# Circuitos curtos: nova extensão exploratória

Esta extensão investiga se um circuito mais curto permite medir o cumulante
conectado de três corpos em N=4, μ=3, τ=1,5. Ela foi definida **depois** de
examinar os resultados v1. Não substitui o teste original em τ=2 nem permite
reinterpretar sua conclusão. O [desenho fixado](design.json) e o
[protocolo local executável](local_protocol.json) ficam versionados aqui.

## Comparações

| Candidato | Passos Trotter totais | Critério ideal de K₃ |
| --- | ---: | --- |
| `principal_2passos` | 2 | Erro ≤ 0,001 no trio (0,1,2) em τ=1,5. |
| `todos_6passos` | 6 | Erro ≤ 0,001 em todos os quatro trios em τ=1,5. |

Os dois usam o mesmo Hamiltoniano, estado inicial e instante. A fase local usa
20 sementes PSA novas (70001–70020), circuitos ideais e medições finitas com
4096 shots por semente. Cinco sementes também passam por dois perfis genéricos
de ruído Aer. O Aer desta fase **não** é uma previsão calibrada da IBM.

## 1. Conferir e executar a fase local

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py define --check
.venv/bin/python scripts/prepare_short_circuit_experiments.py preflight
.venv/bin/python scripts/run_protocol.py run configs/protocols/circuitos_curtos_v2/local_protocol.json
```

O `preflight` verifica exato, Trotter e Qiskit sem acesso à IBM. O último
comando executa apenas cálculos locais e imprime o caminho `run.json`. Para
retomar uma interrupção, use o mesmo protocolo e o mesmo diretório de saída:

```sh
.venv/bin/python scripts/run_protocol.py run configs/protocols/circuitos_curtos_v2/local_protocol.json --resume results/protocols/ID/run.json
```

Depois da execução, agregue os 20 blocos e os perfis de ruído em um relatório:

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py analyze-local \
  --record results/protocols/ID/run.json
```

O relatório fica ao lado de `run.json` como `short_circuit_local_analysis.json`.
Na primeira execução local, o perfil Aer moderado não separou de modo confiável
o circuito de 2 passos da PSA; o de 6 passos ficou mais distante do exato.
Isto é um sinal de cautela para a triagem física, não uma previsão calibrada da
IBM nem uma mudança da regra de seleção.

Cada etapa grava entradas, passos, ambiente e artefatos em `results/`. O runner
não executa jobs IBM sem `--allow-hardware`.

## 2. Preparar a triagem IBM

Após concluir o protocolo local, prepare a fila para um backend disponível na
conta. O comando consulta a IBM e transpila circuitos; **não envia jobs**:

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py prepare-hardware \
  --local-record results/protocols/ID-LOCAL/run.json --backend ibm_kingston
```

O resultado contém `plan.json`, dois QPY, SHA-256, layout, profundidade,
contagem de portas e `hardware_screen_protocol.json`. São 2 circuitos × 2
condições (sem supressão e *gate twirling*) × 5 sementes novas (80001–80005):
**20 jobs e 81.920 shots**. A preparação falha se a compilação atingir 672
portas de dois qubits ou ultrapassar `max_depth` (padrão 5000). Como não há
calibração de leitura nessa triagem, nenhuma correção de leitura é inferida.

O envio é uma operação separada e explícita, que consome créditos:

```sh
.venv/bin/python scripts/run_protocol.py run results/short-circuit-preparations/ID/hardware_screen_protocol.json --allow-hardware
```

Consultar os jobs já enviados e analisar a triagem não cria outros jobs:

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py collect-hardware \
  --record results/protocols/ID-TRIAGEM/run.json
```

Repita a consulta enquanto houver jobs pendentes. A escolha do candidato e da
condição usa apenas a distância absoluta da estimativa ao exato na triagem.
Empates favorecem menos passos e ausência de twirling. Esta escolha não é uma
conclusão estatística.

## 3. Confirmação independente

Quando todos os jobs da triagem estiverem concluídos e analisados:

```sh
.venv/bin/python scripts/prepare_short_circuit_experiments.py prepare-confirmation \
  --record results/protocols/ID-TRIAGEM/run.json
```

O comando fixa um único circuito e condição em `confirmation_protocol.json`,
com **20 sementes inéditas (90001–90020), 20 jobs e 327.680 shots**. O envio
também exige `scripts/run_protocol.py run CAMINHO --allow-hardware`. Depois,
`collect-hardware --record results/protocols/ID-CONFIRMACAO/run.json` calcula
IC95 de bootstrap conjunto para IBM, PSA e a vantagem
`D = |K₃_IBM−K₃_exato| − |K₃_PSA−K₃_exato|`. Só há suporte à superioridade
**nesse ponto do modelo** quando o limite superior do IC95 de D é negativo e o
IC95 de IBM−PSA exclui zero. O resultado v1 permanece separado.

Todos os caminhos `results/` são ignorados pelo Git. Preserve o diretório
integral e seus snapshots em um arquivo científico antes de divulgar os dados.
