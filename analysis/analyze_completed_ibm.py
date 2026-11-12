#!/usr/bin/env python3
"""Audita contagens IBM concluídas e produz um pacote novo, sem acessar a rede."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'scripts')]
from app.backend.storage import RunStore
from neutrinos.sim import ExperimentConfig, classical_exact, observable_from_counts
from neutrinos.study_analysis import connected
from run_correlation_search import complete_psa
from run_correlation_noise import c3, marginal
from prepare_short_circuit_experiments import _analyze_arm

CAMPAIGN = ROOT/'results/campaigns/20261107-correlacoes-v3'
CONFIRMATION = ROOT/'results/protocols/20261107T233046Z-6d048a1b4b85'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def cumulants(probabilities, cfg):
    """Produtos explícitos de bits; não usa a transformação de Walsh do motor."""
    states = np.arange(1 << cfg.n)
    z = 1 - 2*((states[:, None] >> np.arange(cfg.n)) & 1)
    return connected(probabilities @ z,
        probabilities @ np.prod(z[:, cfg.pair_index], axis=-1),
        probabilities @ np.prod(z[:, cfg.trio_index], axis=-1), cfg.n)[1]


def load_confirmation(destination, source_hashes):
    record = read(CONFIRMATION/'run.json')
    official = read(CONFIRMATION/'short_circuit_hardware_analysis.json')
    if official['status'] != 'analyzed' or official['pending_jobs']:
        raise ValueError('A confirmação não está completa')
    if official['source_protocol_sha256'] != sha(CONFIRMATION/'run.json'):
        raise ValueError('Protocolo da confirmação alterado')
    store = RunStore(ROOT/'results')
    blocks = []
    configs = []
    for step in record['steps']:
        if step['action'] != 'hardware':
            continue
        execution_path = ROOT/'results/executions'/step['execution_id']/'execution.json'
        execution = read(execution_path)
        original = read(ROOT/'results'/execution['result']['path'])['hardware_runs'][-1]
        manifest, summary, arrays = store.load(step['run_id'])
        hw = next(h for h in summary['hardware_runs'] if h['job_id'] == original['job_id'])
        counts = arrays[hw['counts_key']]
        if hw['status'] != 'DONE' or counts.shape != (16,) or counts.sum() != 16384:
            raise ValueError('Job de confirmação incompleto ou orçamento incorreto')
        version = (ROOT/'results'/step['run_id']/'current').read_text().strip()
        moments = ROOT/'results'/step['run_id']/'versions'/version/'moments.npz'
        source_hashes[str(moments.relative_to(ROOT))] = sha(moments)
        blocks.append({'counts': counts.copy(), 'exact': float(arrays['exact_c3'][1, 0]),
            **{key: arrays[f'psa_{key}'][1].copy() for key in ('m1','m2','m3')},
            'seed': manifest['config_input']['seed'], 'job_id': hw['job_id']})
        configs.append(manifest['config_input'])
    if len(blocks) != 20 or len({b['job_id'] for b in blocks}) != 20:
        raise ValueError('Confirmação exige 20 jobs distintos')
    recomputed = _analyze_arm(blocks, repetitions=2000, seed=92001)
    original = official['arms']['principal_2passos/twirled']
    for key in ('ibm','psa','advantage_D','advantage_D_ci95','difference_exact_ci95'):
        np.testing.assert_allclose(recomputed[key], original[key], atol=1e-13, rtol=0)
    cfg = ExperimentConfig.from_dict({**configs[0], 'points': 61})
    exact = classical_exact(cfg)
    full = complete_psa(cfg, substeps=8)
    save(destination/'raw/n4_blocks.json', [{k: v.tolist() if isinstance(v,np.ndarray) else v
        for k,v in b.items()} for b in blocks])
    return {'n':4,'cfg':cfg,'blocks':blocks,'exact':exact.c3[-1], 'psa_full':full.c3[-1],
        'primary_index':0,'primary_psa':original['psa'],'official':original,
        'role':'independent_confirmation', 'psa_numerical':1e-5}


def load_pilot(destination, source_hashes):
    folder = CAMPAIGN/'hardware'
    plan, collection = read(folder/'plan.json'), read(folder/'collection.json')
    if collection['status'] != 'completed' or collection['plan_sha256'] != sha(folder/'plan.json'):
        raise ValueError('Triagem incompleta ou plano alterado')
    selected = read(CAMPAIGN/'search.json')['selected']
    result = []
    for candidate in plan['candidates']:
        cfg = ExperimentConfig.from_dict(candidate['config'])
        if sha(folder/candidate['qpy_path']) != candidate['qpy_sha256']:
            raise ValueError('QPY alterado')
        blocks = []
        for slot in collection['jobs']:
            if slot['n'] != cfg.n:
                continue
            path = folder/(slot['slot']+'_counts.json')
            data = read(path); counts = np.asarray(data['counts'],dtype=np.int64)
            if slot['status'] != 'DONE' or data['job_id'] != slot['job_id'] or sha(path) != slot['counts_sha256']:
                raise ValueError('Contagens ou job incompatíveis')
            if counts.shape != (1 << cfg.n,) or counts.sum() != 4096:
                raise ValueError('Orçamento de shots incorreto')
            source_hashes[str(path.relative_to(ROOT))] = sha(path)
            blocks.append({'job_id':slot['job_id'],'counts':counts})
        if len(blocks)!=5:
            raise ValueError('São necessários os cinco blocos de cada tamanho')
        chosen = next(c for c in selected if c['n']==cfg.n)
        time_index = chosen['candidate']['time_index']
        with np.load(CAMPAIGN/chosen['moments_path']) as arrays:
            exact = arrays['exact_c3'][time_index].copy()
        with np.load(CAMPAIGN/chosen['refined_moments_path']) as arrays:
            psa = arrays['c3'][time_index].copy()
        # Referência independente recalculada no mesmo ponto físico.
        independent = classical_exact(cfg).c3[-1]
        np.testing.assert_allclose(exact,independent,atol=1e-11,rtol=0)
        index = list(map(tuple,cfg.trio_index)).index(tuple(candidate['trio']))
        result.append({'n':cfg.n,'cfg':cfg,'blocks':blocks,'exact':exact,'psa_full':psa,
            'primary_index':index,'primary_psa':candidate['psa'],'role':'exploratory_pilot',
            'psa_numerical':candidate['psa_numerical_sensitivity']})
        for key in ('moments_path','refined_moments_path'):
            source_hashes[str((CAMPAIGN/chosen[key]).relative_to(ROOT))]=sha(CAMPAIGN/chosen[key])
    shutil.copytree(folder,destination/'raw/pilot')
    return result


def analyze(case):
    cfg = case['cfg']; index = case['primary_index']
    counts = np.stack([b['counts'] for b in case['blocks']]); totals=counts.sum(axis=0)
    probability=totals/totals.sum()
    estimates=cumulants(probability,cfg)
    for k,trio in enumerate(cfg.trio_index):
        np.testing.assert_allclose(estimates[k],observable_from_counts(totals,'c3',tuple(trio)),atol=1e-13,rtol=0)
    target=case['exact'];psa=case['psa_full']
    rng=np.random.default_rng(190000+cfg.n)
    weights=rng.multinomial(len(counts),np.ones(len(counts))/len(counts),size=10000)
    draws=weights@counts
    all_boot=cumulants(draws/draws.sum(axis=1,keepdims=True),cfg)
    stationary=rng.multinomial(int(totals.sum()),probability,size=10000)
    all_stationary=cumulants(stationary/stationary.sum(axis=1,keepdims=True),cfg)
    point=float(estimates[index]);reference=float(target[index]);baseline=case['primary_psa']
    official=case.get('official')
    primary={'n':cfg.n,'role':case['role'],'mu':cfg.mu,'tau':cfg.t_max,
        'trio':cfg.trio_index[index].tolist(),'jobs':len(counts),'shots':int(totals.sum()),
        'exact':reference,'psa_protocol':baseline,'psa_full_support':float(psa[index]),'ibm':point,
        'psa_error':abs(baseline-reference),'ibm_error':abs(point-reference),
        'error_reduction_percent':100*(1-abs(point-reference)/abs(baseline-reference)),
        'D':abs(point-reference)-abs(baseline-reference),'signal_fraction_abs':abs(point/reference),
        'per_job_c3':[float(observable_from_counts(row,'c3',tuple(cfg.trio_index[index]))) for row in counts],
        'official_confirmation':official if official else None,'sensitivity':{}}
    for label,values in [('job_blocks_full_psa',all_boot[:,index]),('stationary_full_psa',all_stationary[:,index])]:
        delta=np.abs(values-reference)-abs(psa[index]-reference)
        zero=np.abs(values-reference)-abs(reference)
        low,high=np.quantile(delta,[.025,.975]);num=case['psa_numerical']
        primary['sensitivity'][label]={'C3_ci95':np.quantile(values,[.025,.975]).tolist(),
            'D_ci95':[float(low-num),float(high+num)],
            'error_difference_vs_zero_ci95':np.quantile(zero,[.025,.975]).tolist(),
            'difference_exact_ci95':np.quantile(values-reference,[.025,.975]).tolist()}
    error=np.abs(estimates-target);psa_error=np.abs(psa-target)
    ibm_rmse=float(np.sqrt(np.mean(error**2)));psa_rmse=float(np.sqrt(np.mean(psa_error**2)))
    boot_rmse=np.sqrt(np.mean((all_boot-target)**2,axis=1))-psa_rmse
    secondary={'n':cfg.n,'status':'posthoc_exploratory','trios':len(estimates),
        'point_estimates_better_than_psa':int(np.sum(error<psa_error)),
        'point_estimates_better_than_zero':int(np.sum(error<np.abs(target))),
        'ibm_rmse_over_trios':ibm_rmse,'psa_rmse_over_trios':psa_rmse,
        'rmse_error_reduction_percent':100*(1-ibm_rmse/psa_rmse),
        'rmse_difference_ci95_job_blocks':np.quantile(boot_rmse,[.025,.975]).tolist(),
        'counts_are_not_independent_confirmatory_detections':True,
        'per_trio':[{'trio':list(map(int,trio)),'exact':float(target[k]),'psa':float(psa[k]),
            'ibm':float(estimates[k]),'D':float(error[k]-psa_error[k])} for k,trio in enumerate(cfg.trio_index)]}
    return primary,secondary


def main(destination):
    if destination.exists():
        raise ValueError('Preserve o relatório anterior; escolha outro --output')
    destination.mkdir(parents=True)
    sources={}
    cases=[load_confirmation(destination,sources),*load_pilot(destination,sources)]
    job_ids=[b['job_id'] for c in cases for b in c['blocks']]
    if len(job_ids)!=30 or len(set(job_ids))!=30:
        raise ValueError('Esperados 30 IDs distintos')
    primary=[];secondary=[]
    for case in cases:
        p,s=analyze(case);primary.append(p);secondary.append(s)
        save(destination/f'raw/config_n{case["n"]}.json',case['cfg'].record())
    save(destination/'analysis.json',{'status':'all_30_jobs_complete','ibm_jobs_submitted_by_this_analysis':0,
        'bootstrap_repetitions_sensitivity':10000,'primary':primary,'secondary':secondary,
        'source_counts_sha256':sources})
    for path in [CONFIRMATION/'run.json',CONFIRMATION/'short_circuit_hardware_analysis.json',
        CAMPAIGN/'hardware/plan.json',CAMPAIGN/'hardware/analysis.json']:
        shutil.copy2(path,destination/('original_'+path.name))
    for path in [Path(__file__),ROOT/'src/neutrinos/sim.py',ROOT/'src/neutrinos/study_analysis.py',
        ROOT/'scripts/run_correlation_noise.py',ROOT/'scripts/run_correlation_search.py',ROOT/'scripts/prepare_short_circuit_experiments.py']:
        target=destination/'sources'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    np.savez_compressed(destination/'reference_endpoints.npz',**{f'n{c["n"]}_{key}':c[key] for c in cases for key in ('exact','psa_full')})
    with (destination/'primary.csv').open('w') as stream:
        names=['n','role','mu','tau','trio','jobs','shots','exact','psa_protocol','psa_full_support','ibm','psa_error','ibm_error','error_reduction_percent','D']
        writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
        for row in primary:writer.writerow({key:row[key] for key in names})
    with (destination/'secondary_trios.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['n','trio','exact','psa','ibm','D']);writer.writeheader()
        for row in secondary:
            for trio in row['per_trio']:writer.writerow({'n':row['n'],**trio})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(11.5,3.9),layout='constrained')
    for ax,row in zip(axes,primary):
        values=[row['exact'],row['psa_protocol'],row['ibm']]
        ax.axhspan(row['exact']-.01,row['exact']+.01,color='#167d8d',alpha=.1)
        ax.axhline(0,color='#888888',lw=.8)
        ax.scatter(range(3),values,c=['#242424','#b96330','#167d8d'],s=50)
        lo,hi=row['sensitivity']['job_blocks_full_psa']['C3_ci95'];ax.vlines(2,lo,hi,color='#333333',lw=2)
        ax.set_xticks(range(3),['Exato','PSA','IBM'])
        ax.set_title(f'{row["n"]} qubits · {row["error_reduction_percent"]:.1f}% menos erro')
        ax.grid(axis='y',alpha=.15)
        for x,value in enumerate(values):ax.annotate(f'{value:.4f}',(x,value),xytext=(0,12),textcoords='offset points',ha='center')
        ax.margins(y=.24,x=.18)
    axes[0].set_ylabel('Cumulante conectado C₃')
    fig.savefig(destination/'comparacao_ibm.png',dpi=180);plt.close(fig)
    table='\n'.join(f'| {r["n"]} | {r["exact"]:.6f} | {r["psa_protocol"]:.6f} | {r["ibm"]:.6f} | {r["error_reduction_percent"]:.1f}% |' for r in primary)
    intervals='\n'.join(f'- N={r["n"]}: D={r["D"]:.6f}; IC95 por blocos, usando PSA completa: [{r["sensitivity"]["job_blocks_full_psa"]["D_ci95"][0]:.6f}; {r["sensitivity"]["job_blocks_full_psa"]["D_ci95"][1]:.6f}].' for r in primary)
    broad='\n'.join(f'| {s["n"]} | {s["point_estimates_better_than_psa"]}/{s["trios"]} | {s["ibm_rmse_over_trios"]:.6f} | {s["psa_rmse_over_trios"]:.6f} | {s["rmse_error_reduction_percent"]:.1f}% |' for s in secondary)
    save(destination/'job_ids.json',job_ids)
    (destination/'README.md').write_text(f'''# Resultados IBM concluídos — 8 de novembro de 2026

Os 30 jobs terminaram: vinte de confirmação N=4 e cinco de cada triagem N=6/8. Foram verificadas 368.640 contagens de medição, IDs distintos, orçamento por job e hashes dos circuitos da triagem. Esta análise não enviou novos jobs.

O resultado físico favorece menor erro que a PSA nos três pontos principais. O teste de confirmação de N=4 passou na regra original; N=6/8 permanecem pilotos exploratórios de cinco blocos. Isso demonstra ganho de precisão relativo à PSA nesses pontos, sem estabelecer vantagem computacional quântica.

| Qubits | C₃ exato | C₃ PSA do protocolo | C₃ IBM | Redução do erro absoluto |
| ---: | ---: | ---: | ---: | ---: |
{table}

![Resultados físicos IBM](comparacao_ibm.png)

A faixa sombreada é ±0,01 em torno do exato. As barras IBM são IC95 de reamostragem de jobs. Em N=4 a tabela usa a PSA amostrada do protocolo original; N=6/8 usam a distribuição completa da PSA. Os pontos físicos são distintos: N=4 usa μ=3,τ=1,5 e acoplamento uniforme; N=6/8 usam μ=10, dois feixes e τ=0,55/0,65. Portanto, as diferenças entre linhas não isolam o efeito de N.

## Confirmação e incerteza

A análise original N=4 foi reproduzida a partir das contagens e dos momentos PSA arquivados, com concordância numérica de 10⁻¹³. Sua decisão é `supports_better_than_psa_at_this_endpoint`: D≈−0,044943 e IC95 [−0,052047;−0,037785]. O intervalo de IBM−PSA também exclui zero.

Como sensibilidade, foram usados 10.000 sorteios apenas de blocos independentes de jobs e, separadamente, multinomial estacionário. A PSA completa foi usada como referência clássica sem erro Monte Carlo, inclusive em N=4. Essas sensibilidades não substituem a decisão e os intervalos originalmente definidos:

{intervals}

Todos os intervalos de D dessas duas sensibilidades ficaram abaixo de zero. Os intervalos IBM de C₃ excluem zero e os contrastes de erro contra a previsão C₃=0 também favorecem a IBM. Nos pilotos, cinco jobs permitem apenas uma avaliação limitada de deriva e cobertura dos intervalos.

O sinal N=8 é negativo, como o exato, mas sua amplitude absoluta equivale a aproximadamente {100*primary[2]['signal_fraction_abs']:.1f}% da referência. O circuito preservou um sinal detectável, ainda fortemente atenuado. O erro físico N=8 é maior que o previsto no Aer genérico; os 74% de redução mencionados anteriormente eram da simulação, enquanto a redução física foi {primary[2]['error_reduction_percent']:.1f}%.

Nenhum dos três pontos recuperou o exato dentro da margem ±0,01. Os erros absolutos IBM são {primary[0]['ibm_error']:.6f}, {primary[1]['ibm_error']:.6f} e {primary[2]['ibm_error']:.6f}. Mais precisão que a PSA e equivalência ao exato são afirmações diferentes. As contagens são brutas com gate twirling; não foi aplicada correção de leitura aos novos dados físicos.

## Análise secundária de todos os trios

Após a coleta, foram examinados todos os trios disponíveis no mesmo instante. A tabela compara estimativas pontuais e RMSE entre trios, usando PSA completa. É uma análise posterior e exploratória: as contagens de trios melhores não representam esse número de detecções confirmatórias independentes.

| N | Trios com menor erro pontual IBM que PSA | RMSE IBM | RMSE PSA | Redução do RMSE |
| ---: | ---: | ---: | ---: | ---: |
{broad}

Os dados completos estão em [analysis.json](analysis.json), [primary.csv](primary.csv) e [secondary_trios.csv](secondary_trios.csv). A reamostragem preserva simultaneamente todos os trios de cada job. Não houve exclusão de blocos nem seleção de um novo alvo principal depois de observar os resultados físicos.

## Dados e reprodução

`raw/` contém contagens de N=4, momentos PSA por bloco, dados da triagem N=6/8, circuitos QPY e metadados. `reference_endpoints.npz` preserva as referências por trio. Os relatórios oficiais são copiados sem alterações, e `sources/` contém o analisador e fontes numéricos relevantes. O manifesto registra hashes de todos os arquivos e as origens dos dados.

Para gerar outro pacote sem sobrescrever esta fotografia:

```sh
MPLCONFIGDIR=/private/tmp/neutrinos-matplotlib-cache PYTHONPATH=src .venv/bin/python analysis/analyze_completed_ibm.py --output analysis/campaigns/NOVO-PACOTE
```

O passo científico seguinte é confirmar independentemente os pontos de seis/oito qubits, controlar erros de portas/leitura e comparar custo e precisão com métodos clássicos competitivos. Aumentar o número de qubits isoladamente não constitui evidência de vantagem computacional.
''')
    hashes={str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}
    save(destination/'manifest.json',{'status':'verified_all_jobs_complete','files_sha256':hashes,
        'source_data_sha256':sources,'jobs':30,'shots':368640,'original_reports_preserved':True})
    print(json.dumps({'report':str(destination/'README.md'),'primary':primary,'secondary_summary':[{k:v for k,v in s.items() if k!='per_trio'} for s in secondary]},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'analysis/campaigns/20261108-resultados-ibm')
    main(parser.parse_args().output.resolve())
