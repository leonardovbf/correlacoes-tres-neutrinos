#!/usr/bin/env python3
"""Publica uma fotografia local da comparação Aer–IBM pareada já concluída."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package(source,destination):
    if destination.exists():raise ValueError('Preserve o pacote anterior; escolha outro --output')
    result=read(source/'analysis.json');capture=read(source/'capture_manifest.json')
    if result['status']!='paired_replay_complete':raise ValueError('Replay incompleto')
    destination.mkdir(parents=True)
    validation=read(source/'validation.json')
    if validation['status']!='passed' or sha(source/'test_output.txt')!=validation['log_sha256']:
        raise ValueError('Validação ausente ou log alterado')
    for name in ('analysis.json','comparison.csv','capture_manifest.json','replay_plan.json','validation.json','test_output.txt'):
        shutil.copy2(source/name,destination/name)
    controls=[]
    for entry in capture['jobs']:
        folder=source/'replay'/entry['job_id'];report=read(folder/'result.json')
        if sha(folder/'arrays.npz')!=report['arrays_sha256'] or sha(folder/'compact_template.qpy')!=report['template_sha256']:
            raise ValueError('Artefato do replay foi alterado')
        controls.append(report)
    if len(controls)!=30:raise ValueError('Esperados 30 replays completos')
    with zipfile.ZipFile(destination/'replay_data.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for directory in ('inputs','replay','attempts'):
            for path in sorted((source/directory).rglob('*')):
                if path.is_file():archive.write(path,str(path.relative_to(source)))
    for path in [ROOT/'analysis/capture_paired_aer_inputs.py',ROOT/'analysis/paired_aer_common.py',
        ROOT/'analysis/run_paired_aer.py',Path(__file__),ROOT/'tests/test_paired_aer_replay.py',ROOT/'requirements-research.lock']:
        target=destination/'sources'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    with (destination/'matching_controls.csv').open('w') as stream:
        names=['n','job_id','shots','num_randomizations','shots_per_randomization','physical_to_compact',
            'max_ideal_probability_error','max_ideal_c3_error','max_trace_error','elapsed_seconds']
        writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
        for control in controls:writer.writerow({key:control[key] for key in names})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    rows=result['comparisons'];primary=[r for r in rows if r['model']=='full_calibrated']
    fig,axes=plt.subplots(1,3,figsize=(12,3.9),layout='constrained')
    for ax,row in zip(axes,primary):
        idle=next(r for r in rows if r['n']==row['n'] and r['model']=='full_asap_idle')
        values=[row['exact'],row['psa'],row['aer'],idle['aer'],row['ibm']]
        ax.axhline(0,color='#888888',lw=.8);ax.axhspan(row['exact']-.01,row['exact']+.01,color='#167d8d',alpha=.08)
        ax.scatter(range(5),values,c=['#252525','#be6b37','#526aab','#88759c','#167d8d'],s=45)
        for index,r,key in [(2,row,'aer_ci95_job_blocks'),(3,idle,'aer_ci95_job_blocks'),(4,row,'ibm_ci95_job_blocks')]:
            low,high=r[key];ax.vlines(index,low,high,color='#444444',lw=2)
        ax.set_xticks(range(5),['Exato','PSA','Aer cal.','Aer + ócio','IBM'],rotation=25)
        ax.set_title(f'{row["n"]} qubits · {row["shots_per_environment"]:,} shots'.replace(',','.'))
        ax.grid(axis='y',alpha=.15);ax.margins(y=.14)
    axes[0].set_ylabel('Cumulante conectado C₃')
    fig.savefig(destination/'paired_comparison.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.9),layout='constrained')
    labels=['Ideal','Leitura','Portas','Completo','+ ócio']
    for ax,n in zip(axes,(4,6,8)):
        subset=[r for r in rows if r['n']==n]
        ax.axhline(subset[0]['exact'],color='#333333',ls='--',lw=1,label='Exato')
        ax.axhline(subset[0]['ibm'],color='#167d8d',lw=1.5,label='IBM')
        for index,row in enumerate(subset):
            ax.scatter(index,row['aer'],color='#526aab',s=35)
            ax.vlines(index,*row['aer_ci95_job_blocks'],color='#526aab')
            ax.scatter(index,row['aer_expected'],color='#be6b37',marker='D',s=22,
                label='Previsão sem shots' if index==0 else None)
        ax.set_xticks(range(5),labels,rotation=25);ax.set_title(f'{n} qubits');ax.grid(axis='y',alpha=.15);ax.margins(y=.2)
    axes[0].set_ylabel('C₃ no replay pareado');axes[0].legend(fontsize=9)
    fig.savefig(destination/'noise_ablation.png',dpi=180);plt.close(fig)
    table='\n'.join(f'| {r["n"]} | {r["exact"]:.6f} | {r["aer"]:.6f} | {next(x for x in rows if x["n"]==r["n"] and x["model"]=="full_asap_idle")["aer"]:.6f} | {r["ibm"]:.6f} |' for r in primary)
    residuals='\n'.join(f'- N={r["n"]}: IBM−Aer={r["ibm_minus_aer"]:.6f}, IC95 por blocos [{r["ibm_minus_aer_ci95"][0]:.6f}; {r["ibm_minus_aer_ci95"][1]:.6f}].' for r in primary)
    max_c3=max(c['max_ideal_c3_error'] for c in controls)
    max_p=max(c['max_ideal_probability_error'] for c in controls)
    ideal_control='\n'.join(f'- N={r["n"]}: circuito ideal com dois passos C₃={r["aer_expected"]:.6f}; referência exata={r["exact"]:.6f}; diferença de discretização={r["aer_expected"]-r["exact"]:+.6f}.' for r in rows if r['model']=='ideal')
    expected_table='\n'.join('| '+str(n)+' | '+' | '.join(f'{r["aer_expected"]:.6f}' for r in rows if r['n']==n)+' |' for n in (4,6,8))
    gate_table=[]
    for n in (4,6,8):
        c=next(x for x in controls if x['n']==n)
        gate_table.append(f'| {n} | {c["original_gate_counts"].get("cz",0)} | {c["original_gate_counts"].get("sx",0)} | {c["template_gate_counts"].get("sx",0)} |')
    gate_table='\n'.join(gate_table)
    (destination/'README.md').write_text(f'''# Comparação Aer–IBM pareada — 8 de novembro de 2026

O Aer foi reexecutado localmente a partir dos programas dos 30 jobs IBM concluídos. Foram mantidos os pontos físicos, circuitos nativos arquivados, mapeamento físico e clássico, gerador e política de twirling, shots por randomização, blocos e processamento bruto. Nenhum novo job IBM foi enviado.

| N | Exato | Aer calibrado | Aer calibrado + ócio ASAP | IBM existente |
| ---: | ---: | ---: | ---: | ---: |
{table}

![Comparação pareada](paired_comparison.png)

A faixa sombreada é ±0,01 do exato. Os intervalos são reamostragens dos blocos de jobs, com medições Aer e IBM independentes. Não incluem incerteza dos parâmetros de calibração nem viés do modelo de ruído. N=6/8 têm apenas cinco blocos cada, o que limita a avaliação de variabilidade. O cenário com ócio é uma sensibilidade de escalonamento, não uma recuperação do cronograma real de pulsos.

## O que foi efetivamente igualado

- Os 20 jobs N=4 usam o ponto μ=3,τ=1,5, acoplamento uniforme e estado de domínio; N=6/8 usam seus pontos de dois feixes, μ=10,τ=0,55/0,65 e estado alternado. A comparação não mistura o exemplo local v3 de N=4 com a confirmação v2.
- Cada job N=4 tem 32 randomizações × 512 shots; cada job N=6/8 tem 32 × 128. Totais por cenário: 327.680, 20.480 e 20.480, os mesmos da IBM. Cinco cenários locais perfazem 1.843.200 shots simulados.
- Foram baixados, por leitura dos jobs existentes, os próprios QuantumPrograms e Samplex do Runtime. Assim, são reproduzidas também as rotações de um qubit introduzidas pelo mecanismo de twirling. O programa nativo executável pode ter mais operações que o QPY base.
- Não houve nova transpilação do circuito lógico. A remoção de fios ociosos do registrador de 156 posições conserva as portas, qubits físicos ativos e permutação dos bits medidos. Os arquivos originais e seus hashes são mantidos.
- Os dois ambientes são comparados sem correção de leitura e com gate twirling. Não se coloca um Aer mitigado contra um IBM bruto.
- As calibrações são as arquivadas com os jobs/preparação original. Não foram escolhidos parâmetros para ajustar a simulação aos resultados físicos.

O programa com twirling recuperado contém mais rotações físicas de um qubit que o circuito base. Estas são contagens de operações nos arquivos, antes de eventuais simplificações internas de pulsos não registradas:

| N | CZ, base e template | SX no QPY base | SX no template Runtime |
| ---: | ---: | ---: | ---: |
{gate_table}

O replay inclui o template completo; simular apenas o QPY base com ruído não representaria a mesma sequência programada.

## Limites do pareamento

As opções e os programas recuperados não informam a semente aleatória interna usada pelo servidor para sortear cada instância de twirling. O replay usa o mesmo Samplex, política, número de variantes e orçamento, com novas sementes locais registradas e parâmetros amostrados arquivados. Portanto, pareia-se a distribuição do procedimento, não se afirma repetir a mesma sequência aleatória física.

O ruído real também não é copiável integralmente de um snapshot. O modelo calibrado usa erros de portas derivados por `basic_device_gate_errors` do Aer, relaxação T₁/T₂ durante as portas, erro independente de inicialização e matriz de leitura assimétrica por qubit. Assume temperatura de equilíbrio zero. A frequência física não consta do snapshot e não foi inventada: nessa hipótese a população térmica excitada é zero independentemente dela.

Os canais de inicialização/leitura são tratados como independentes, uma aproximação de SPAM. Não há um modelo completo de erros coerentes, vazamento, crosstalk ou deriva entre a calibração e a execução. A data da calibração e os tempos dos jobs estão nos dados arquivados.

O modelo principal aplica relaxação durante portas. Foi acrescentada uma sensibilidade com relaxação nos tempos ociosos calculados por um cronograma ASAP hipotético, com durações de portas e barreiras arquivadas. O cronograma real de pulsos do hardware não está nos programas; esse cenário não deve ser tratado como uma reprodução medida dos tempos ociosos.

## Separação das fontes de erro

![Ablation de ruído](noise_ablation.png)

Os cinco cenários usam as mesmas 32 variantes locais em cada bloco: ideal; apenas leitura; erros de portas com relaxação; modelo completo incluindo inicialização/leitura; completo com ócio ASAP. As contagens de cada cenário são amostradas independentemente, mantendo o orçamento físico. A ablação é uma interpretação do modelo calibrado, não prova causal de cada erro do chip.

Os pontos azuis e seus intervalos usam contagens finitas, comparáveis ao orçamento IBM. Os diamantes laranja usam as probabilidades simuladas antes da amostragem de shots. Para interpretar o efeito sistemático dos canais, estas últimas previsões são:

| N | Ideal | Apenas leitura | Portas/relaxação | Completo | Completo + ócio ASAP |
| ---: | ---: | ---: | ---: | ---: | ---: |
{expected_table}

Em N=8 com ócio ASAP, o sinal da estimativa amostrada muda para positivo, enquanto a previsão probabilística permanece negativa. Essa diferença é flutuação dos shots locais fixados no plano; não é uma inversão determinística causada pelo canal de relaxação. As sementes e as contagens foram mantidas, sem repetir o sorteio para aproximar a IBM. As previsões sem shots também preservam apenas as 32 variantes de twirling por job, não uma média sobre todas as randomizações possíveis.

Mesmo sem ruído, o circuito de dois passos aproxima a evolução exata. Usando as probabilidades ideais, sem flutuação de shots:

{ideal_control}

Diferenças residuais do modelo completo para o hardware:

{residuals}

O objetivo deste replay é validar e qualificar a previsão do simulador. Não é um novo teste confirmatório de superioridade, nem altera os dados físicos ou a decisão original IBM–PSA.

O modelo aponta as portas e a relaxação como a principal perda prevista de sinal, acima da leitura isolada. A prioridade técnica é reduzir operações físicas/profundidade e validar o modelo com calibrações próximas da execução; ampliar shots melhora a incerteza estatística, mas não corrige esse viés. A sensibilidade ASAP não foi escolhida como modelo vencedor a partir da proximidade dos dados IBM.

## Controles e reprodutibilidade

O maior desvio entre as probabilidades ideais do template Runtime e o QPY base foi {max_p:.3g}; entre C₃ de todos os trios, {max_c3:.3g}. O controle inicial mais estrito de 10⁻⁹ falhou no primeiro template com diferença de 1,39×10⁻⁷ e foi preservado em `attempts/ideal_control_v1`. Como o objetivo é reproduzir o programa Runtime efetivamente enviado, não o resintetizar, validou-se adicionalmente C₃ no limite numérico de 10⁻⁵ já adotado no estudo, 0,1% da margem de equivalência de 0,01. O histórico dessa emenda está no plano e no arquivo de dados.

Os seis testes novos verificam o mapeamento de bits após compactação, a assimetria da leitura, canais calibrados sem frequência, relaxação ociosa analítica, inicialização e rejeição de medições não terminais. A suíte completa passou: 76 testes (`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`). Durante o replay, cada orçamento e cada equivalência são checados em todos os jobs e variantes.

- [comparison.csv](comparison.csv): valores, erros e diferenças para cada cenário.
- [analysis.json](analysis.json): intervalos e metadados da comparação.
- [matching_controls.csv](matching_controls.csv): orçamento, índices físicos e controles por job.
- [validation.json](validation.json) e [test_output.txt](test_output.txt): resultado e saída da suíte de testes.
- `replay_data.zip`: programas recuperados, QPY base e templates compactos, calibrações, contagens físicas, sementes/parâmetros locais, probabilidades simuladas e tentativas preservadas.
- `sources/`: código e ambiente de referência; `manifest.json`: hashes dos arquivos.

Para retomar o replay local completo, sem rede e sem novos jobs:

```sh
PYTHONPATH=src .venv/bin/python analysis/run_paired_aer.py
```

Para exportar outro pacote, preservando este:

```sh
MPLCONFIGDIR=/private/tmp/neutrinos-matplotlib-cache .venv/bin/python analysis/package_paired_aer.py --output analysis/campaigns/NOVO-PACOTE
```

Referências técnicas: [modelo de ruído Aer](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.NoiseModel.html) e [opções de twirling IBM](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-twirling-options).
''')
    hashes={str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}
    (destination/'manifest.json').write_text(json.dumps({'status':'paired_local_replay_complete','ibm_jobs_submitted':0,
        'capture_manifest_sha256':sha(source/'capture_manifest.json'),'files_sha256':hashes},indent=2)+'\n')
    print(destination/'README.md')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'results/paired-aer-ibm-20261108')
    parser.add_argument('--output',type=Path,default=ROOT/'analysis/campaigns/20261108-aer-ibm-pareado')
    args=parser.parse_args();package(args.source.resolve(),args.output.resolve())
