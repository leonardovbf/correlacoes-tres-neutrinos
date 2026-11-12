#!/usr/bin/env python3
"""Empacota uma fotografia dos resultados locais e dos jobs IBM, sem rede."""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from app.backend.storage import RunStore


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(source, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if destination.exists():
        raise ValueError('Preserve o pacote existente; escolha outro --output')
    destination.mkdir(parents=True)
    shutil.copytree(source, destination/'data')
    root = destination/'data'
    search = json.loads((root/'search.json').read_text())
    observations = sum([json.loads((root/name).read_text())['observations']
        for name in ('noise.json', 'short_noise.json')], [])
    pilot = json.loads((root/'hardware/collection.json').read_text())
    plan = json.loads((root/'hardware/plan.json').read_text())
    confirmation = ROOT/'results/protocols/20261107T233046Z-6d048a1b4b85/run.json'
    record = json.loads(confirmation.read_text())
    store = RunStore(ROOT/'results')
    jobs = []
    for step in record['steps']:
        if step['action'] != 'hardware':
            continue
        _, summary = store.load_metadata(step['run_id'])
        job = summary['hardware_runs'][-1]
        jobs.append({'n': 4, 'role': 'independent_confirmation_v2', 'job_id': job['job_id'],
            'status': job['status'], 'shots': job['shots']})
    jobs.extend({'n': j['n'], 'role': 'exploratory_pilot_v3', 'job_id': j['job_id'],
        'status': j['status'], 'shots': 4096} for j in pilot['jobs'])
    (destination/'ibm_jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
    shutil.copy2(confirmation,destination/'ibm_confirmation_protocol_record.json')
    report_path = confirmation.parent/'short_circuit_hardware_analysis.json'
    if report_path.exists():
        shutil.copy2(report_path,destination/'ibm_confirmation_analysis.json')
    files = [ROOT/'scripts'/name for name in ('run_correlation_search.py','run_correlation_noise.py',
        'run_correlation_short_noise.py','run_correlation_hardware.py','prepare_short_circuit_experiments.py')]
    files += list((ROOT/'configs/protocols/correlacoes_v3').glob('*.json'))
    files += [Path(__file__), ROOT/'tests/test_correlation_campaign.py', ROOT/'requirements-research.lock',ROOT/'pyproject.toml']
    for source_path in files:
        target = destination/'sources'/source_path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source_path,target)
    with (destination/'comparacao_ruido.csv').open('w') as stream:
        names = ['n','case_id','mu','tau','steps','factor','p2','readout_error','cx_count','method',
            'exact','psa','estimate','absolute_error','D','D_low','D_high','better_than_psa','equivalent']
        writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
        for row in observations:
            for method,value in row['methods'].items():
                writer.writerow({**{k:row[k] for k in names[:9]},'method':method,'exact':row['exact'],'psa':row['psa'],
                    **{k:value[k] for k in ('estimate','absolute_error','D')},
                    'D_low':value['D_ci95'][0],'D_high':value['D_ci95'][1],
                    'better_than_psa':value['better_than_psa_pointwise'],'equivalent':value['equivalent_to_exact_pointwise']})
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),layout='constrained')
    for ax,n in zip(axes,(4,6,8)):
        for factor,label,color in [(0,'Curto','#167d8d'),(1,'Tolerância ideal 0,001','#c36b36'),(2,'Dobro de passos','#817386')]:
            rows=sorted([r for r in observations if r['n']==n and r['factor']==factor and r['readout_error']==.03],key=lambda r:r['p2'])
            x=np.array([r['p2'] for r in rows]); y=np.array([r['methods']['raw']['D'] for r in rows])
            low=[r['methods']['raw']['D_ci95'][0] for r in rows];high=[r['methods']['raw']['D_ci95'][1] for r in rows]
            ax.plot(x,y,'o-',label=label,color=color,ms=4);ax.fill_between(x,low,high,color=color,alpha=.16)
        ax.axhline(0,color='#555555',lw=1);ax.set_xscale('symlog',linthresh=1e-4)
        reference=next(r for r in observations if r['n']==n)
        zero_baseline=abs(reference['exact'])-abs(reference['psa']-reference['exact'])
        ax.axhline(zero_baseline,color='#555555',ls=':',lw=1,label='Previsão C₃=0')
        ax.set_xlim(0,.012)
        ax.set_title(f'{n} qubits');ax.set_xlabel('Despolarização por porta de 2 qubits')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('D: diferença de erro absoluto frente à PSA')
    axes[0].legend(fontsize=8)
    fig.savefig(destination/'erro_por_ruido.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.5),layout='constrained')
    chosen=[]
    for ax,n in zip(axes,(4,6,8)):
        row=next(r for r in observations if r['n']==n and r['factor']==0 and r['p2']==.001 and r['readout_error']==.03)
        chosen.append(row)
        values=[row['exact'],row['psa'],row['methods']['raw']['estimate'],row['methods']['mitigated']['estimate']]
        ax.scatter(range(4),values,c=['#252525','#c36b36','#167d8d','#8161a1'],s=45)
        for x,key in [(2,'raw'),(3,'mitigated')]:
            low,high=np.array(row['methods'][key]['difference_exact_ci95'])+row['exact']
            ax.vlines(x,low,high,color='#444444',lw=2)
        ax.axhline(0,color='#888888',lw=.8)
        ax.set_xticks(range(4),['Exato','PSA','Aer bruto','Aer mitigado'],rotation=20)
        ax.set_title(f'{n} qubits, μ={row["mu"]:g}, τ={row["tau"]:g}')
        ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Cumulante conectado C₃')
    fig.savefig(destination/'comparacao_local.png',dpi=180);plt.close(fig)
    table='\n'.join(f'| {r["n"]} | {r["tau"]:.2f} | {r["exact"]:.6f} | {r["psa"]:.6f} | {r["methods"]["raw"]["estimate"]:.6f} | {100*(1-r["methods"]["raw"]["absolute_error"]/abs(r["psa"]-r["exact"])):.1f}% |' for r in chosen)
    resource_table='\n'.join(f'| {c["n"]} | {c["steps"]} | {c["depth"]} | {c["two_qubit_gates"]} | 5 |' for c in plan['candidates'])
    statuses={s:sum(j['status']==s for j in jobs) for s in sorted({j['status'] for j in jobs})}
    (destination/'README.md').write_text(f'''# Experimentos ampliados de correlações — 7 de novembro de 2026

Foram concluídas 36 configurações locais com 4, 6 e 8 qubits: três interações, dois estados iniciais e duas geometrias. A PSA usa a distribuição discreta completa, sem erro Monte Carlo. Cada configuração inclui 61 tempos e todos os pares e trios. Os três candidatos selecionados passaram por refinamento RK4 e comparação Qiskit–emulador.

Foram calculadas 54 matrizes densidade com ruído de portas e 108 condições de medição/leitura, cada uma com método bruto e mitigado sob orçamento igual de 81.920 shots por método. São 216 avaliações de métodos em condições exploratórias, não replicações independentes de hardware.

No perfil genérico p₂=0,001, p₁=0,0001 e leitura=0,03, os circuitos de dois passos apresentaram:

| Qubits | τ | Exato | PSA completa | Aer bruto | Redução do erro frente à PSA |
| ---: | ---: | ---: | ---: | ---: | ---: |
{table}

Todos esses pontos usam μ=10 e dois feixes antiparalelos, com acoplamentos normalizados para média fora da diagonal igual a 1. Em N=4, o estado inicial é de domínio; em N=6/8, alternado. Não são o mesmo ponto físico da confirmação v2 de quatro qubits.

![Comparação local](comparacao_local.png)

![Erro frente à PSA em função do ruído](erro_por_ruido.png)

D é o erro absoluto do circuito menos o erro absoluto da PSA. Valores negativos favorecem o circuito. A linha pontilhada mostra a previsão C₃=0: em N=8, até essa previsão supera a PSA, portanto D<0 isoladamente não demonstra recuperação da correlação. As faixas são IC95 pontuais e exploratórios, sob modelo estacionário de medições. O Aer usa despolarização genérica, não calibração IBM; a compilação genérica tem conectividade distinta da física. Os números não predizem a precisão no dispositivo nem estabelecem vantagem computacional.

## Execução IBM

Foram enviados 30 jobs, todos no `ibm_kingston`, com 368.640 shots: 20 blocos de confirmação v2 de quatro qubits, com 327.680 shots, e cinco blocos de cada tamanho N=6/8, com 40.960 shots no total. Os IDs e o estado nesta fotografia estão em [ibm_jobs.json](ibm_jobs.json). Estado resumido: `{statuses}`.

| Qubits da triagem v3 | Passos | Profundidade física | Portas de 2 qubits | Jobs |
| ---: | ---: | ---: | ---: | ---: |
{resource_table}

Os circuitos QPY preparados são os enviados, com hashes e qubits físicos arquivados. A triagem v3 usa gate twirling com 32 randomizações × 128 shots por job. Os resultados físicos ainda dependem da conclusão dos jobs. A confirmação v2 conserva o ponto, a seleção e a regra originais; a triagem v3 é uma nova exploração.

## Controles e emendas

- Os 70 testes automatizados passaram. Novos controles verificam evolução livre, marginalização de bits, correção assimétrica de leitura, comparação de erros e prevenção de reenvio ambíguo.
- O maior desvio de C₃ no refinamento dos candidatos foi {max(c['refinement_max_c3'] for c in search['selected']):.3g}. A maior diferença de probabilidades Qiskit–emulador foi {max(c['qiskit_probability_error'] for c in search['selected']):.3g}.
- A tolerância ideal original 0,001 selecionou circuitos mais longos. Uma emenda posterior à busca ideal definiu circuitos curtos com erro ideal ≤min(0,02; 10% da diferença PSA–exato), mantendo os candidatos originais. Os três casos selecionaram dois passos. O erro ideal de N=8 é aproximadamente 0,01285; não se afirma equivalência ao exato em ±0,01.
- O compilador de nível 3 falhou no controle estrito de equivalência com desvio de probabilidade 3,43×10⁻⁶. A tentativa e os fontes foram preservados em `data/compiler_level3_attempt/`. Outra emenda fixou nível 1, que passou no controle ideal de 10⁻¹⁰. A confirmação v2 mantém sua compilação original.
- Os critérios de seleção e o orçamento físico estão nos fontes dos protocolos. A seleção física usou os valores esperados locais e exigiu também distinguir C₃ de zero e superar a previsão nula no modelo. Não houve seleção a partir dos novos resultados IBM.

O objetivo alcançado localmente é maior precisão que a PSA em pontos selecionados. A evolução exata continua viável nesses tamanhos. Para demonstrar vantagem computacional, será preciso comparar tempo, memória e precisão com métodos clássicos competitivos numa escala maior, incluindo todos os custos quânticos. Ampliar qubits sem preservar o sinal não atende a esse objetivo.

## Reproduzir e acompanhar

Na raiz do repositório, os comandos locais retomam resultados completos sem recalculá-los:

```sh
.venv/bin/python scripts/run_correlation_search.py run
.venv/bin/python scripts/run_correlation_noise.py
.venv/bin/python scripts/run_correlation_short_noise.py run
```

Consultar os jobs já enviados não cria novos jobs:

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py collect-hardware --record results/protocols/20261107T233046Z-6d048a1b4b85/run.json
.venv/bin/python scripts/run_correlation_hardware.py collect
```

O diretório `data/` contém os momentos agregados, contagens simuladas, probabilidades ruidosas, circuitos, metadados físicos e relatórios desta campanha. `sources/` preserva os novos scripts e protocolos; o motor usado pela busca está em `data/sources/`. O manifesto registra hashes dos arquivos desta fotografia. O registro completo dos 20 jobs v2 continua em `results/`.
''')
    hashes={str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}
    (destination/'manifest.json').write_text(json.dumps({'schema_version':1,'status':'local_complete_hardware_snapshot',
        'original_results_unchanged':True,'files_sha256':hashes,'ibm_jobs':len(jobs),'total_ibm_shots':sum(j['shots'] for j in jobs)},indent=2)+'\n')
    print(destination/'README.md')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'results/campaigns/20261107-correlacoes-v3')
    parser.add_argument('--output',type=Path,default=ROOT/'analysis/campaigns/20261107-correlacoes-v3')
    args=parser.parse_args();package(args.source.resolve(),args.output.resolve())
