"""Mitigação tensorial de leitura; preserva quasiprobabilidades negativas."""
import numpy as np


def response_matrix(zero, one, condition_max=10.):
    zero, one = np.asarray(zero), np.asarray(one)
    if zero.shape != one.shape or zero.ndim != 1 or zero.size & (zero.size-1):
        raise ValueError('Contagens de calibração incompatíveis')
    if np.any(zero < 0) or np.any(one < 0) or min(zero.sum(), one.sum()) <= 0:
        raise ValueError('Calibração sem medições válidas')
    n = zero.size.bit_length()-1
    states = np.arange(zero.size)
    matrices = []
    for q in reversed(range(n)):
        bits = (states >> q) & 1
        matrix = np.array([[zero[bits==0].sum()/zero.sum(), one[bits==0].sum()/one.sum()],
                           [zero[bits==1].sum()/zero.sum(), one[bits==1].sum()/one.sum()]])
        matrices.append(matrix)
    full = np.array([[1.]])
    for matrix in matrices:
        full = np.kron(full, matrix)
    condition = float(np.linalg.cond(full))
    if not np.isfinite(condition) or condition > condition_max:
        return None, condition
    return full, condition


def correct(signal, zero, one, condition_max=10.):
    response, condition = response_matrix(zero, one, condition_max)
    if response is None:
        return None, condition
    signal = np.asarray(signal)
    if signal.shape != np.asarray(zero).shape or np.any(signal < 0) or signal.sum() <= 0:
        raise ValueError('Contagens de sinal inválidas')
    return np.linalg.solve(response, signal/signal.sum()), condition


def observable(probabilities, kind, indices):
    # O estimador é polinomial em momentos; não impõe positividade artificial.
    p = np.asarray(probabilities, dtype=float)
    if p.ndim != 1 or not np.isclose(p.sum(), 1):
        raise ValueError('Distribuição normalizada necessária')
    states = np.arange(len(p))
    def moment(*qs):
        return p @ np.prod(1-2*((states[:,None] >> np.asarray(qs)) & 1), axis=1)
    if kind == 'pe':
        return float((1+moment(indices[0]))/2)
    if kind == 'c2':
        i,j=indices
        return float(moment(i,j)-moment(i)*moment(j))
    i,j,k=indices
    return float(moment(i,j,k)-moment(i)*moment(j,k)-moment(j)*moment(i,k)
                 -moment(k)*moment(i,j)+2*moment(i)*moment(j)*moment(k))
