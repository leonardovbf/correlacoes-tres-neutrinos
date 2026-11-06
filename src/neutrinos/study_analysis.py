"""Estimadores do artigo: momentos agregados antes dos cumulantes, blocos de sementes."""
from itertools import combinations
import numpy as np
from scipy.linalg import expm
from .sim import ExperimentConfig, MomentSeries, hamiltonian_sparse, initial_state
from .mitigation import correct, observable


def connected(m1, m2, m3, n):
    # Aceita dimensões iniciais arbitrárias (tempo ou réplica bootstrap).
    pairs = list(combinations(range(n), 2))
    trios = list(combinations(range(n), 3))
    lookup = {p:i for i,p in enumerate(pairs)}
    c2 = np.stack([m2[...,p]-m1[...,i]*m1[...,j] for p,(i,j) in enumerate(pairs)], axis=-1)
    c3 = np.stack([m3[...,q]-m1[...,i]*m2[...,lookup[j,k]]
        -m1[...,j]*m2[...,lookup[i,k]]-m1[...,k]*m2[...,lookup[i,j]]
        +2*m1[...,i]*m1[...,j]*m1[...,k] for q,(i,j,k) in enumerate(trios)], axis=-1)
    return c2, c3


def metrics(reference, estimate, floor=1e-4):
    signal = float(np.sqrt(np.mean(np.asarray(reference)**2)))
    error = float(np.sqrt(np.mean((np.asarray(reference)-estimate)**2)))
    return {'rmse': error, 'max_abs': float(np.max(np.abs(np.asarray(reference)-estimate))),
        'signal_rms': signal, 'normalized_rmse': error/signal if signal >= floor else None,
        'normalization_resolved': signal >= floor}


def pooled(blocks, n):
    values = [np.mean([b[k] for b in blocks], axis=0) for k in ('m1','m2','m3')]
    return connected(*values, n)


def h1(blocks, reference2, reference3, n, repetitions=2000, seed=71001):
    """Bootstrap de blocos independentes de igual tamanho; preserva trajetórias/tempos internos."""
    c2,c3=pooled(blocks,n)
    r2,r3=metrics(reference2,c2),metrics(reference3,c3)
    rng=np.random.default_rng(seed)
    # Comprime apenas somas de momentos; cada bloco contém todas as suas trajetórias.
    moments=[np.stack([b[k] for b in blocks]) for k in ('m1','m2','m3')]
    delta=[]
    for _ in range(repetitions):
        index=rng.integers(0,len(blocks),len(blocks))
        b2,b3=connected(*(m[index].mean(axis=0) for m in moments),n)
        a,b=metrics(reference2,b2),metrics(reference3,b3)
        if a['normalization_resolved'] and b['normalization_resolved']:
            delta.append(b['normalized_rmse']-a['normalized_rmse'])
    return {'c2':r2,'c3':r3,'r3_minus_r2_ci95':list(map(float,np.quantile(delta,[.025,.975]))) if delta else None,
            'repetitions':len(blocks),'bootstrap_repetitions':repetitions,'seed':seed,
            'bootstrap_unit':'bloco independente de semente; momentos agregados antes do cumulante',
            'r3_minus_r2_bootstrap':delta,
            'c3_per_trio':[metrics(reference3[:,i],c3[:,i]) for i in range(c3.shape[-1])]}


def h2(count_blocks, psa_blocks, exact, residual, *, repetitions=2000, seed=72001,
       margin=.01, condition_max=10.):
    """Bootstrap conjunto: contagens completas e calibração; blocos PSA independentes.

    PSA: bootstrap dos blocos independentes de trajetórias de igual tamanho.
    Circuito: reamostra contagens multinomiais agregadas de cada orçamento.
    """
    rng=np.random.default_rng(seed)
    def estimate(counts):
        q,condition=correct(counts['signal'],counts['zero'],counts['one'],condition_max)
        return {'raw':observable(counts['raw']/counts['raw'].sum(),'c3',(0,1,2)),
                'mitigated':None if q is None else observable(q,'c3',(0,1,2))}
    def aggregate(blocks):
        return {k:np.sum([b[k] for b in blocks],axis=0) for k in blocks[0]}
    def psa_value(blocks):
        m1,m2,m3=(np.mean([b[k] for b in blocks],axis=0) for k in ('m1','m2','m3'))
        return float(connected(m1,m2,m3,4)[1][0])
    central=estimate(aggregate(count_blocks))
    central_psa=psa_value(psa_blocks)
    draws={k:[] for k in central}
    if any(estimate(b)['mitigated'] is None for b in count_blocks):
        return {'status':'unresolved_calibration','reason':'Pelo menos uma calibração ultrapassou o limite; nenhum bloco foi descartado.'}
    totals=aggregate(count_blocks)
    for _ in range(repetitions):
        # Contagens multinomiais agregadas de igual configuração: não somar
        # uma segunda variância de sementes à mesma flutuação de shots.
        counts={k:rng.multinomial(int(row.sum()),row/row.sum()) for k,row in totals.items()}
        q=estimate(counts)
        ps=psa_value([psa_blocks[i] for i in rng.integers(0,len(psa_blocks),len(psa_blocks))])
        for method,value in q.items():
            if value is None:
                return {'status':'unresolved_calibration','reason':'Inversão instável em réplica bootstrap; sem descarte seletivo.'}
            draws[method].append([value-ps,value-exact])
    result={'status':'analyzed','exact':exact,'psa':central_psa,'bounded_numerical_residual':residual,
            'margin':margin,'bootstrap_repetitions':repetitions,'bootstrap_seed':seed,
            'bootstrap_unit':'blocos PSA e contagens completas agregadas; calibração reestimada em cada réplica',
            'methods':{}}
    for method in draws:
        ci=np.quantile(draws[method],[.025,.975],axis=0)
        # Soma limites de discretização; nunca os trata como ruído amostral.
        eq=[float(ci[0,1]-residual),float(ci[1,1]+residual)]
        diff=list(map(float,ci[:,0]))
        result['methods'][method]={'estimate':central[method],'difference_psa_ci95':diff,
            'difference_exact_ci95_with_residual':eq,
            'bootstrap_bias_estimate':float(np.mean(np.asarray(draws[method])[:,1])-(central[method]-exact)),
            'bias_correction_applied':False,
            'resolves': bool((diff[0]>0 or diff[1]<0) and eq[0]>=-margin and eq[1]<=margin)}
    raw,mit=(result['methods'][m]['resolves'] for m in ('raw','mitigated'))
    result['h2_decision']='refutada_nesta_condicao' if raw else ('apoio_nesta_condicao' if mit else 'inconclusivo')
    return result


def independent_exact_check():
    """H denso por produtos de Kronecker, independente da construção esparsa por bits."""
    config=ExperimentConfig(n=4,mu=3.,points=3,t_max=.7,
        omega_values=(.7,.9,1.1,1.3),g_values=((0,1,.2,0),(1,0,.4,.7),(.2,.4,0,1.2),(0,.7,1.2,0)),
        b_values=(.6,.8,0), initial_bloch_values=((.6,0,.8),(0,.6,.8),(-.6,0,-.8),(0,-.6,-.8)))
    paulis=[np.array([[0,1],[1,0]]),np.array([[0,-1j],[1j,0]]),np.diag([1,-1])]
    def embed(terms):
        result=np.array([[1.]])
        for q in reversed(range(config.n)):
            result=np.kron(result,terms.get(q,np.eye(2)))
        return result
    dense=np.zeros((16,16),complex)
    for i in range(4):
        for p,coefficient in zip(paulis,config.b_field):
            dense+=config.omega[i]*coefficient/2*embed({i:p})
    for i,j in config.pair_index:
        for p in paulis:
            dense+=config.mu*config.g_matrix[i,j]/(4*config.n)*embed({i:p,j:p})
    sparse=hamiltonian_sparse(config).toarray()
    from scipy.sparse.linalg import expm_multiply
    state=initial_state(config)
    error=np.max(np.abs(expm(-1j*dense*config.t_max)@state-expm_multiply(-1j*sparse*config.t_max,state)))
    return {'hamiltonian_max_abs':float(np.max(np.abs(dense-sparse))), 'state_max_abs':float(error)}
