"""Modelo comum, solvers e observáveis Z para o piloto de neutrinos.

Convenção: qubit i ocupa o bit i (menos significativo para i=0), |0>=nu_e,
|1>=nu_x. As frequências são expressas em unidades de omega_bar=1.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import cos, sin

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import expm_multiply


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class ExperimentConfig:
    n: int = 4
    mu: float = 1.0
    theta: float = 0.2
    omega_spread: float = 0.3
    t_max: float = 8.0
    points: int = 81
    flavors: tuple[int, ...] = (0, 0, 1, 1)
    seed: int = 42
    omega_values: tuple[float, ...] | None = None
    b_values: tuple[float, float, float] | None = None
    g_values: tuple[tuple[float, ...], ...] | None = None
    initial_bloch_values: tuple[tuple[float, float, float], ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.n, int) or not 2 <= self.n <= 16:
            raise ValueError("n deve estar entre 2 e 16")
        if len(self.flavors) != self.n or any(bit not in (0, 1) for bit in self.flavors):
            raise ValueError("flavors deve ter n valores 0 (nu_e) ou 1 (nu_x)")
        if not all(np.isfinite(value) for value in (self.mu, self.theta, self.omega_spread, self.t_max)):
            raise ValueError("Parâmetros escalares devem ser finitos")
        if not 0 <= self.omega_spread < 1:
            raise ValueError("omega_spread deve estar em [0, 1)")
        if self.mu < 0 or self.t_max <= 0 or not isinstance(self.points, int) or not 2 <= self.points <= 201:
            raise ValueError("mu, t_max ou points fora do intervalo permitido")
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed deve ser inteiro não negativo")
        if self.omega_values is not None:
            if (len(self.omega_values) != self.n or not np.all(np.isfinite(self.omega_values))
                    or not np.isclose(np.mean(self.omega_values), 1.0, rtol=1e-6, atol=1e-8)):
                raise ValueError("omega_values deve conter n frequências finitas normalizadas com média 1")
        if self.b_values is not None:
            if len(self.b_values) != 3 or not np.all(np.isfinite(self.b_values)) or not np.isclose(np.linalg.norm(self.b_values), 1):
                raise ValueError("b_values deve ser um vetor unitário de três componentes")
        if self.g_values is not None:
            g = np.asarray(self.g_values, dtype=float)
            if g.shape != (self.n, self.n) or not np.all(np.isfinite(g)) or not np.allclose(g, g.T) or not np.allclose(np.diag(g), 0):
                raise ValueError("g_values deve ser matriz n×n finita, simétrica e com diagonal zero")
        if self.initial_bloch_values is not None:
            spins = np.asarray(self.initial_bloch_values, dtype=float)
            if spins.shape != (self.n, 3) or not np.all(np.isfinite(spins)) or not np.allclose(np.linalg.norm(spins, axis=1), 1):
                raise ValueError("initial_bloch_values deve conter n vetores unitários")

    @classmethod
    def from_dict(cls, values: dict) -> "ExperimentConfig":
        allowed = set(cls.__dataclass_fields__)
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Campos desconhecidos: {', '.join(sorted(unknown))}")
        data = dict(values)
        for key in ("flavors", "omega_values", "b_values"):
            if key in data and data[key] is not None:
                data[key] = tuple(data[key])
        if data.get("g_values") is not None:
            data["g_values"] = tuple(tuple(row) for row in data["g_values"])
        if data.get("initial_bloch_values") is not None:
            data["initial_bloch_values"] = tuple(tuple(row) for row in data["initial_bloch_values"])
            if "flavors" not in data:
                data["flavors"] = (0,) * data.get("n", 4)
        return cls(**data)

    @property
    def omega(self) -> FloatArray:
        return (np.asarray(self.omega_values, dtype=float) if self.omega_values is not None
                else np.linspace(1 - self.omega_spread, 1 + self.omega_spread, self.n))

    @property
    def b_field(self) -> FloatArray:
        return (np.asarray(self.b_values, dtype=float) if self.b_values is not None
                else np.array([sin(2 * self.theta), 0.0, -cos(2 * self.theta)]))

    @property
    def g_matrix(self) -> FloatArray:
        return (np.asarray(self.g_values, dtype=float) if self.g_values is not None
                else np.ones((self.n, self.n)) - np.eye(self.n))

    @property
    def initial_bloch(self) -> FloatArray:
        if self.initial_bloch_values is not None:
            return np.asarray(self.initial_bloch_values, dtype=float)
        spins = np.zeros((self.n, 3), dtype=float)
        spins[:, 2] = 1 - 2 * np.asarray(self.flavors)
        return spins

    @property
    def times(self) -> FloatArray:
        return np.linspace(0.0, self.t_max, self.points)

    @property
    def pair_index(self) -> NDArray[np.int64]:
        return np.array(list(combinations(range(self.n), 2)), dtype=np.int64)

    @property
    def trio_index(self) -> NDArray[np.int64]:
        return np.array(list(combinations(range(self.n), 3)), dtype=np.int64).reshape(-1, 3)

    def record(self) -> dict:
        return {**asdict(self), "omega": self.omega.tolist(), "b_field": self.b_field.tolist(),
                "g_matrix": self.g_matrix.tolist(), "initial_bloch": self.initial_bloch.tolist(),
                "hamiltonian": "sum_i omega_i B.sigma_i/2 + mu/(4N) sum_i<j g_ij(XX+YY+ZZ)",
                "sampling": "bi-valued x/y for flavor product states; one neutrino per beam"}


@dataclass
class MomentSeries:
    times: FloatArray
    m1: FloatArray
    m2: FloatArray
    m3: FloatArray
    pairs: NDArray[np.int64]
    trios: NDArray[np.int64]
    method: str
    diagnostics: dict
    bloch: FloatArray | None = None
    sample_z: FloatArray | None = None
    raw_counts: NDArray[np.int64] | None = None

    @property
    def pe(self) -> FloatArray:
        return (1 + self.m1) / 2

    @property
    def c2(self) -> FloatArray:
        i, j = self.pairs.T
        return self.m2 - self.m1[:, i] * self.m1[:, j]

    @property
    def c3(self) -> FloatArray:
        if not len(self.trios):
            return np.empty((len(self.times), 0))
        i, j, k = self.trios.T
        pair_lookup = {tuple(pair): idx for idx, pair in enumerate(self.pairs)}
        ij = np.array([pair_lookup[(a, b)] for a, b in zip(i, j)])
        ik = np.array([pair_lookup[(a, b)] for a, b in zip(i, k)])
        jk = np.array([pair_lookup[(a, b)] for a, b in zip(j, k)])
        return (self.m3 - self.m1[:, i] * self.m2[:, jk]
                - self.m1[:, j] * self.m2[:, ik]
                - self.m1[:, k] * self.m2[:, ij]
                + 2 * self.m1[:, i] * self.m1[:, j] * self.m1[:, k])


def _moments_from_probabilities(config: ExperimentConfig, probabilities: FloatArray,
                                method: str, diagnostics: dict,
                                raw_counts: NDArray[np.int64] | None = None) -> MomentSeries:
    """Walsh transform: coefficient at mask is <product_i Z_i>."""
    values = np.asarray(probabilities, dtype=np.float64).copy()
    if values.ndim == 1:
        values = values[None, :]
    if values.shape[1] != 1 << config.n:
        raise ValueError("Distribuição com dimensão incompatível")
    for bit in range(config.n):
        block = values.reshape(len(values), -1, 2, 1 << bit)
        left, right = block[:, :, 0, :].copy(), block[:, :, 1, :].copy()
        block[:, :, 0, :] = left + right
        block[:, :, 1, :] = left - right
    pairs, trios = config.pair_index, config.trio_index
    one_masks = 1 << np.arange(config.n)
    pair_masks = (1 << pairs[:, 0]) | (1 << pairs[:, 1])
    trio_masks = (1 << trios[:, 0]) | (1 << trios[:, 1]) | (1 << trios[:, 2]) if len(trios) else []
    return MomentSeries(config.times, values[:, one_masks], values[:, pair_masks],
                        values[:, trio_masks], pairs, trios, method, diagnostics,
                        raw_counts=raw_counts)


def hamiltonian_sparse(config: ExperimentConfig) -> csr_matrix:
    """H = sum omega B.sigma/2 + mu/(4N) sum_{i<j} g_ij sigma_i.sigma_j."""
    n, dim = config.n, 1 << config.n
    basis = np.arange(dim, dtype=np.int64)
    z = 1 - 2 * ((basis[:, None] >> np.arange(n)) & 1)
    omega, bx, by, bz = config.omega, *config.b_field
    pair_coef = config.mu / (4 * n)
    diagonal = z @ (0.5 * omega * bz)
    rows: list[NDArray] = [basis]
    cols: list[NDArray] = [basis]
    data: list[NDArray] = []
    g = config.g_matrix
    for i, j in config.pair_index:
        diagonal += pair_coef * g[i, j] * z[:, i] * z[:, j]
    data.append(diagonal.astype(np.complex128))
    for i in range(n):
        rows.append(basis ^ (1 << i))
        cols.append(basis)
        data.append(0.5 * omega[i] * (bx + 1j * by * z[:, i]))
    if pair_coef:
        for i, j in config.pair_index:
            opposite = z[:, i] != z[:, j]
            source = basis[opposite]
            rows.append(source ^ ((1 << i) | (1 << j)))
            cols.append(source)
            data.append(np.full(len(source), 2 * pair_coef * g[i, j], dtype=np.complex128))
    return coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                      shape=(dim, dim)).tocsr()


def initial_state(config: ExperimentConfig) -> ComplexArray:
    state = np.array([1.0 + 0j])
    for x, y, z in config.initial_bloch:
        theta = np.arccos(np.clip(z, -1, 1))
        phi = np.arctan2(y, x)
        local = np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])
        state = np.kron(local, state)
    return state


def classical_exact(config: ExperimentConfig) -> MomentSeries:
    h = hamiltonian_sparse(config)
    states = expm_multiply(-1j * h, initial_state(config), start=0,
                           stop=config.t_max, num=config.points, endpoint=True)
    norms = np.sum(np.abs(states) ** 2, axis=1)
    return _moments_from_probabilities(config, np.abs(states) ** 2, "Exato",
                                       {"max_norm_error": float(np.max(np.abs(norms - 1))),
                                        "hilbert_dim": 1 << config.n,
                                        "hamiltonian_nnz": int(h.nnz)})


def _rhs(config: ExperimentConfig, spins: FloatArray) -> FloatArray:
    # spins: (trajetorias, neutrinos, xyz).
    others = (spins.sum(axis=1, keepdims=True) - spins if config.g_values is None
              else np.einsum("ij,mjk->mik", config.g_matrix, spins))
    field = config.omega[None, :, None] * config.b_field[None, None, :]
    field = field + (config.mu / (2 * config.n)) * others
    return np.cross(field, spins)


def _evolve_spins(config: ExperimentConfig, spins: FloatArray, substeps: int) -> FloatArray:
    if not 1 <= substeps <= 30:
        raise ValueError("substeps deve estar entre 1 e 30")
    result = np.empty((config.points, len(spins), config.n, 3), dtype=np.float64)
    result[0] = spins
    dt = (config.times[1] - config.times[0]) / substeps
    for t in range(1, config.points):
        for _ in range(substeps):
            k1 = _rhs(config, spins)
            k2 = _rhs(config, spins + dt * k1 / 2)
            k3 = _rhs(config, spins + dt * k2 / 2)
            k4 = _rhs(config, spins + dt * k3)
            spins = spins + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        result[t] = spins
    return result


def _from_trajectories(config: ExperimentConfig, z_values: FloatArray,
                       method: str, diagnostics: dict,
                       bloch: FloatArray | None = None,
                       retain_samples: bool = False) -> MomentSeries:
    pairs, trios = config.pair_index, config.trio_index
    m1 = z_values.mean(axis=1)
    m2 = (z_values[:, :, pairs[:, 0]] * z_values[:, :, pairs[:, 1]]).mean(axis=1)
    m3 = ((z_values[:, :, trios[:, 0]] * z_values[:, :, trios[:, 1]]
           * z_values[:, :, trios[:, 2]]).mean(axis=1) if len(trios)
          else np.empty((config.points, 0)))
    return MomentSeries(config.times, m1, m2, m3, pairs, trios, method, diagnostics,
                        bloch, z_values.copy() if retain_samples else None)


def mean_field(config: ExperimentConfig, substeps: int = 4) -> MomentSeries:
    spins = config.initial_bloch[None, :, :].copy()
    evolved = _evolve_spins(config, spins, substeps)
    lengths = np.linalg.norm(evolved, axis=-1)
    return _from_trajectories(config, evolved[:, :, :, 2], "Campo médio",
                              {"max_spin_length_error": float(np.max(np.abs(lengths - 1))),
                               "substeps_per_interval": substeps}, evolved[:, 0])


def phase_space(config: ExperimentConfig, trajectories: int = 256,
                substeps: int = 4) -> MomentSeries:
    """Amostragem bi-valuada para estados produto de sabor, um neutrino/feixe.

    Lacroix et al., Phys. Rev. D 110, 103027 (2024), Sec. II.1.3: cada
    componente transversal inicial toma valores +/-1 independentemente.
    """
    if not 16 <= trajectories <= 4096:
        raise ValueError("trajectories deve estar entre 16 e 4096")
    rng = np.random.default_rng(config.seed)
    spins = np.empty((trajectories, config.n, 3), dtype=np.float64)
    transverse = rng.choice(np.array([-1.0, 1.0]), size=(trajectories, config.n, 2))
    for i, direction in enumerate(config.initial_bloch):
        anchor = np.array([0., 0., 1.]) if abs(direction[2]) < .9 else np.array([1., 0., 0.])
        u = np.cross(anchor, direction)
        u /= np.linalg.norm(u)
        v = np.cross(direction, u)
        spins[:, i, :] = direction + transverse[:, i, 0, None] * u + transverse[:, i, 1, None] * v
    evolved = _evolve_spins(config, spins, substeps)
    return _from_trajectories(config, evolved[:, :, :, 2], "PSA bi-valuada",
                              {"trajectories": trajectories, "seed": config.seed,
                               "substeps_per_interval": substeps,
                               "initial_spin_mean_error_max": float(np.max(np.abs(spins.mean(axis=0) - config.initial_bloch)))},
                              evolved.mean(axis=1), retain_samples=True)


def _single_qubit_gate(state: ComplexArray, n: int, i: int, omega: float,
                       b_field: FloatArray, dt: float) -> None:
    basis0 = np.arange(1 << n, dtype=np.int64)
    basis0 = basis0[(basis0 & (1 << i)) == 0]
    basis1 = basis0 | (1 << i)
    a, b = state[basis0].copy(), state[basis1].copy()
    angle = omega * dt / 2
    c, s = cos(angle), sin(angle)
    bx, by, bz = b_field
    state[basis0] = (c - 1j * s * bz) * a - 1j * s * (bx - 1j * by) * b
    state[basis1] = -1j * s * (bx + 1j * by) * a + (c + 1j * s * bz) * b


def _pair_gate(state: ComplexArray, n: int, i: int, j: int, mu: float, g: float, dt: float) -> None:
    angle = mu * g * dt / (4 * n)
    if angle == 0:
        return
    basis = np.arange(1 << n, dtype=np.int64)
    bit_i, bit_j = 1 << i, 1 << j
    same = ((basis & bit_i) == 0) == ((basis & bit_j) == 0)
    state[same] *= np.exp(-1j * angle)
    basis01 = basis[((basis & bit_i) == 0) & ((basis & bit_j) != 0)]
    basis10 = basis01 ^ (bit_i | bit_j)
    a, b = state[basis01].copy(), state[basis10].copy()
    c = np.exp(1j * angle) * cos(2 * angle)
    s = -1j * np.exp(1j * angle) * sin(2 * angle)
    state[basis01] = c * a + s * b
    state[basis10] = s * a + c * b


def _symmetric_trotter_step(state: ComplexArray, config: ExperimentConfig, dt: float) -> None:
    pairs = config.pair_index
    g = config.g_matrix
    for i in range(config.n):
        _single_qubit_gate(state, config.n, i, config.omega[i], config.b_field, dt / 2)
    for i, j in pairs:
        _pair_gate(state, config.n, int(i), int(j), config.mu, g[i, j], dt / 2)
    for i, j in pairs[::-1]:
        _pair_gate(state, config.n, int(i), int(j), config.mu, g[i, j], dt / 2)
    for i in range(config.n - 1, -1, -1):
        _single_qubit_gate(state, config.n, i, config.omega[i], config.b_field, dt / 2)


def quantum_trotter(config: ExperimentConfig, steps_per_interval: int = 2,
                    shots: int = 1024, readout_error: float = 0.0
                    ) -> tuple[MomentSeries, MomentSeries]:
    """Simulador de estado do circuito e medições com ruído de leitura independente.

    Não é execução em QPU nem modelo completo de ruído de portas.
    """
    if config.n > 8:
        raise ValueError("O simulador interativo de circuito aceita até 8 qubits")
    if not 1 <= steps_per_interval <= 16 or not 32 <= shots <= 20000:
        raise ValueError("Passos ou número de medições fora dos limites")
    if not 0 <= readout_error <= 0.25:
        raise ValueError("readout_error deve estar em [0, 0.25]")
    state = initial_state(config)
    probabilities = np.empty((config.points, 1 << config.n))
    probabilities[0] = np.abs(state) ** 2
    dt = (config.times[1] - config.times[0]) / steps_per_interval
    max_norm_error = 0.0
    for t in range(1, config.points):
        for _ in range(steps_per_interval):
            _symmetric_trotter_step(state, config, dt)
        probabilities[t] = np.abs(state) ** 2
        max_norm_error = max(max_norm_error, abs(float(probabilities[t].sum()) - 1.0))
    ideal = _moments_from_probabilities(config, probabilities, "Circuito ideal",
                                        {"trotter_order": 2, "steps_per_interval": steps_per_interval,
                                         "total_steps": (config.points - 1) * steps_per_interval,
                                         "max_norm_error": max_norm_error})
    rng = np.random.default_rng(config.seed + 100_000)
    measured_probabilities = np.empty_like(probabilities)
    counts_by_time = np.empty((config.points, 1 << config.n), dtype=np.int64)
    for t, probs in enumerate(probabilities):
        samples = rng.choice(len(probs), p=probs / probs.sum(), size=shots)
        for i in range(config.n):
            flips = rng.random(shots) < readout_error
            samples ^= flips.astype(np.int64) << i
        counts_by_time[t] = np.bincount(samples, minlength=len(probs))
        measured_probabilities[t] = counts_by_time[t] / shots
    measured = _moments_from_probabilities(config, measured_probabilities, "Medições simuladas",
                                           {"shots_per_time": shots, "seed": config.seed + 100_000,
                                            "readout_bit_flip_probability": readout_error,
                                            "noise_scope": "somente leitura; sem ruído de portas"},
                                           raw_counts=counts_by_time)
    return ideal, measured


def bootstrap_interval(series: MomentSeries, kind: str, index: int,
                       repetitions: int = 200, seed: int = 1234) -> tuple[FloatArray, FloatArray]:
    """IC percentil pontual, reamostrando trajetórias ou contagens completas.

    Preserva a dependência entre momentos usados em cada cumulante. Não corrige
    comparações múltiplas entre tempos/índices.
    """
    if kind not in ("pe", "c2", "c3") or not 20 <= repetitions <= 2000:
        raise ValueError("Observável ou número de reamostragens inválido")
    indices = (np.arange(series.m1.shape[1])[:, None] if kind == "pe"
               else series.pairs if kind == "c2" else series.trios)
    selected = np.asarray(indices[index], dtype=np.int64)
    rng = np.random.default_rng(seed)
    draws = np.empty((repetitions, len(series.times)), dtype=np.float64)

    if series.sample_z is not None:
        selected_z = series.sample_z[:, :, selected]
        count = selected_z.shape[1]
        for b in range(repetitions):
            sampled = selected_z[:, rng.integers(0, count, count), :]
            m = sampled.mean(axis=1)
            if kind == "pe":
                draws[b] = (1 + m[:, 0]) / 2
            elif kind == "c2":
                draws[b] = (sampled[:, :, 0] * sampled[:, :, 1]).mean(axis=1) - m[:, 0] * m[:, 1]
            else:
                pair01 = (sampled[:, :, 0] * sampled[:, :, 1]).mean(axis=1)
                pair02 = (sampled[:, :, 0] * sampled[:, :, 2]).mean(axis=1)
                pair12 = (sampled[:, :, 1] * sampled[:, :, 2]).mean(axis=1)
                triple = np.prod(sampled, axis=2).mean(axis=1)
                draws[b] = (triple - m[:, 0] * pair12 - m[:, 1] * pair02
                            - m[:, 2] * pair01 + 2 * np.prod(m, axis=1))
    elif series.raw_counts is not None:
        counts = series.raw_counts
        shots = int(counts[0].sum())
        states = np.arange(counts.shape[1], dtype=np.int64)
        signs = 1 - 2 * ((states[:, None] >> selected) & 1)
        for t, row in enumerate(counts):
            sampled_counts = rng.multinomial(shots, row / shots, size=repetitions)
            m = sampled_counts @ signs / shots
            if kind == "pe":
                draws[:, t] = (1 + m[:, 0]) / 2
            elif kind == "c2":
                pair = sampled_counts @ (signs[:, 0] * signs[:, 1]) / shots
                draws[:, t] = pair - m[:, 0] * m[:, 1]
            else:
                p01 = sampled_counts @ (signs[:, 0] * signs[:, 1]) / shots
                p02 = sampled_counts @ (signs[:, 0] * signs[:, 2]) / shots
                p12 = sampled_counts @ (signs[:, 1] * signs[:, 2]) / shots
                triple = sampled_counts @ np.prod(signs, axis=1) / shots
                draws[:, t] = (triple - m[:, 0] * p12 - m[:, 1] * p02
                                - m[:, 2] * p01 + 2 * np.prod(m, axis=1))
    else:
        raise ValueError("Série sem trajetórias ou contagens brutas")
    return np.quantile(draws, .025, axis=0), np.quantile(draws, .975, axis=0)


def observable_from_counts(counts: NDArray[np.int64], kind: str,
                           indices: tuple[int, ...]) -> float:
    """Estima P_e, C2 ou C3 a partir das mesmas contagens de bits."""
    counts = np.asarray(counts)
    if counts.ndim != 1 or counts.sum() <= 0 or kind not in ("pe", "c2", "c3"):
        raise ValueError("Contagens ou observável inválido")
    states = np.arange(len(counts), dtype=np.int64)
    probabilities = counts / counts.sum()

    def moment(*qubits: int) -> float:
        parity = ((states[:, None] >> np.asarray(qubits)) & 1).sum(axis=1) % 2
        return float(probabilities @ (1 - 2 * parity))

    if kind == "pe":
        return (1 + moment(indices[0])) / 2
    if kind == "c2":
        i, j = indices
        return moment(i, j) - moment(i) * moment(j)
    i, j, k = indices
    mi, mj, mk = moment(i), moment(j), moment(k)
    return (moment(i, j, k) - mi * moment(j, k) - mj * moment(i, k)
            - mk * moment(i, j) + 2 * mi * mj * mk)


def bootstrap_counts_interval(counts: NDArray[np.int64], kind: str,
                              indices: tuple[int, ...], repetitions: int = 200,
                              seed: int = 1234) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    shots = int(np.sum(counts))
    estimates = [observable_from_counts(rng.multinomial(shots, counts / shots), kind, indices)
                 for _ in range(repetitions)]
    return tuple(float(x) for x in np.quantile(estimates, [.025, .975]))


def summarize_errors(reference: MomentSeries, other: MomentSeries) -> dict[str, dict[str, float]]:
    if not np.array_equal(reference.times, other.times):
        raise ValueError("Malhas temporais diferentes")
    result = {}
    for key in ("pe", "c2", "c3"):
        ref = getattr(reference, key)
        value = getattr(other, key)
        if ref.shape != value.shape or not ref.size:
            continue
        delta = value - ref
        result[key] = {"rmse": float(np.sqrt(np.mean(delta ** 2))),
                       "max_abs": float(np.max(np.abs(delta))),
                       "signal_rms": float(np.sqrt(np.mean(ref ** 2)))}
    return result
