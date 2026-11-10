"""Statistical helpers for the feedback revision; immutable previous estimators."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr, ndtri


def cumulants(moments, n):
    from neutrinos.study_analysis import connected
    return connected(*moments, n)


def statistics(moments, reference2, reference3, n):
    """Last axis: R3-R2, R3, R2. Leading axes may include bootstrap draws."""
    c2, c3 = cumulants(moments, n)
    signal2=np.sqrt(np.mean(reference2**2));signal3=np.sqrt(np.mean(reference3**2))
    if min(signal2,signal3)<1e-4:raise ValueError('Unresolved normalization')
    r2=np.sqrt(np.mean((c2-reference2)**2,axis=(-2,-1)))/signal2
    r3=np.sqrt(np.mean((c3-reference3)**2,axis=(-2,-1)))/signal3
    return np.stack((r3-r2,r3,r2),axis=-1)


def weighted_statistics(blocks, weights, reference2, reference3, n, batch=32):
    weights=np.atleast_2d(weights);result=[]
    for start in range(0,len(weights),batch):
        w=weights[start:start+batch];w=w/w.sum(axis=1,keepdims=True)
        moments=[(w@b.reshape(len(b),-1)).reshape(len(w),*b.shape[1:]) for b in blocks]
        result.append(statistics(moments,reference2,reference3,n))
    return np.concatenate(result)


def bootstrap_statistics(blocks, reference2, reference3, n, repetitions=2000, seed=71001):
    count=len(blocks[0]);rng=np.random.default_rng(seed)
    # Same integer-index draws as the original h1(), then compress to counts.
    indices=rng.integers(0,count,size=(repetitions,count))
    weights=np.zeros((repetitions,count),dtype=float)
    np.add.at(weights,(np.arange(repetitions)[:,None],indices),1)
    central=weighted_statistics(blocks,np.ones((1,count)),reference2,reference3,n)[0]
    draws=weighted_statistics(blocks,weights,reference2,reference3,n)
    jack=weighted_statistics(blocks,np.ones((count,count))-np.eye(count),reference2,reference3,n)
    return central,draws,jack


def intervals(estimate, draws, jackknife, confidence=.95):
    """Percentile, basic and BCa, including finite-B and jackknife diagnostics."""
    estimate=float(estimate);draws=np.asarray(draws);jackknife=np.asarray(jackknife)
    alpha=(1-confidence)/2;quantiles=np.quantile(draws,[alpha,1-alpha])
    proportion=(np.sum(draws<estimate)+.5*np.sum(draws==estimate))/len(draws)
    clipped=np.clip(proportion,.5/len(draws),1-.5/len(draws))
    z0=ndtri(clipped);u=jackknife.mean()-jackknife
    denominator=6*np.sum(u*u)**1.5
    acceleration=float(np.sum(u**3)/denominator) if denominator>0 else 0.
    z=ndtri([alpha,1-alpha]);adjusted=ndtr(z0+(z0+z)/(1-acceleration*(z0+z)))
    valid=bool(np.all(np.isfinite(adjusted)) and adjusted[0]<adjusted[1])
    bca=np.quantile(draws,adjusted).tolist() if valid else None
    return {'percentile':quantiles.tolist(),'basic':(2*estimate-quantiles[::-1]).tolist(),
        'BCa':bca,'bias_correction_z0':float(z0),'acceleration':acceleration,
        'bias_fraction_at_boundary':bool(proportion==0 or proportion==1),
        'BCa_quantiles':adjusted.tolist(),'BCa_tail_below_resolution':bool(np.min(adjusted)<1/(len(draws)+1) or np.max(adjusted)>len(draws)/(len(draws)+1)),
        'jackknife_degenerate':bool(denominator==0)}


def wilson(successes, total, confidence=.95):
    z=ndtri((1+confidence)/2);p=successes/total;d=1+z*z/total
    center=(p+z*z/(2*total))/d
    radius=z*np.sqrt(p*(1-p)/total+z*z/(4*total**2))/d
    return [float(max(0,center-radius)),float(min(1,center+radius))]


def slope(x, values):
    centered=np.asarray(x)-np.mean(x)
    if not np.any(centered):raise ValueError('At least two distinct x values required')
    return np.asarray(values)@centered/(centered@centered)


def first_loss(levels, success):
    """Bracket first failure; no false threshold from last isolated success."""
    order=np.argsort(levels);levels=np.asarray(levels)[order];success=np.asarray(success,dtype=bool)[order]
    if not success[0]:return {'status':'failure_at_zero','bracket':[None,float(levels[0])],
        'later_reentry':bool(np.any(success[1:]))}
    failed=np.flatnonzero(~success)
    if not len(failed):return {'status':'lower_bound_only','bracket':[float(levels[-1]),None],'later_reentry':False}
    i=int(failed[0]);return {'status':'bracketed','bracket':[float(levels[i-1]),float(levels[i])],
        'later_reentry':bool(np.any(success[i+1:]))}
