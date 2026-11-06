# Executar os experimentos do artigo

O ponto de entrada é `scripts/run_study.py`. A revisão operacional 2 implementa
o desenho físico v1: reprodução publicada, controles, convergência, H1, Trotter,
Qiskit em tempos posteriores, medições, ruído e mitigação. São **7.800 etapas em
11 fases locais**, incluindo N=12/16. O programa prepara e avalia experimentos;
a aprovação científica dos controles depende dos resultados.

## 1. Ambiente

A coleta de referência usa CPython **3.14.3** e versões fixas. A partir da raiz:

```sh
python3.14 -m venv .venv-research
.venv-research/bin/python -m pip install -r requirements-research.lock
.venv-research/bin/python -m pip install --no-deps -e .
.venv-research/bin/python scripts/define_article_protocols.py --check
PYTHONPATH=src .venv-research/bin/python -m unittest discover -s tests -v
```

Se a `.venv` existente já possui exatamente essas versões, pode substituir
`.venv-research/bin/python` por `.venv/bin/python`. O preflight verifica Python,
dependências, dados da referência, RAM/disco e uma construção independente de H.
A interface Next.js e o servidor FastAPI podem ficar fechados durante a coleta.
Evite editar os fontes/protocolos durante a execução: a retomada exige as mesmas
fontes e dependências. O snapshot arquiva inclusive alterações ainda sem commit.

## 2. Conferir recursos e testar o fluxo

```sh
.venv-research/bin/python scripts/run_study.py plan
.venv-research/bin/python scripts/run_study.py smoke --output results/validacao-software
```

`plan` grava `results/study_preflight.json`, sem executar a coleta.
A estimativa inclui margens e revisões que preservam as amostras; os valores
variam com o perfil. A coleta completa pode levar horas ou dias.

`smoke` executa todas as rotas locais com grade reduzida, incluindo Aer real,
calibração, análise e gráficos. Seus registros são marcados `software-smoke` e
**não servem como resultados oficiais**, aprovação do benchmark ou teste de H1/H2.
As APIs IBM nos testes unitários usam objetos de teste; os experimentos locais
usam os simuladores numéricos e Qiskit/Aer, sem contagens fabricadas.

## 3. Executar tudo localmente

```sh
.venv-research/bin/python scripts/run_study.py run
```

Inclui a extensão N=12/16. Para uma coleta explicitamente limitada ao conjunto
principal, use `--without-extension`; o escopo ficará registrado. Não omite
outras etapas silenciosamente. O comando para se um controle falhar, preserva
os dados e explica a falha no JSON. Resultados negativos/inconclusivos de H1/H2
são resultados válidos e não impedem a conclusão da coleta.

Os controles incluem reprodução exata e PSA da publicação, integrador 8 versus
12 subpassos, erro padrão da PSA de até 0,01 no maior orçamento, Trotter ideal
até 0,001 em K3 e concordância entre Qiskit e emulador até 1e-10. O circuito ideal
da grade específica de ruído é verificado **antes** de executar Aer/mitigação.
Falhar não autoriza afrouxar os critérios; é necessário registrar uma emenda ao
protocolo antes de uma nova coleta.

### Recuperação da falha de discretização na T06 (emenda v4)

Se o estudo com a emenda amostral v3 parar com `Grade de ruído não resolve
Trotter: erro K3=0.00400071 > 0.001`, prepare a continuação versionada:

```sh
.venv/bin/python scripts/run_study.py prepare-trotter-recovery results/studies/ID-ORIGINAL/study.json
```

O preparo verifica 120 comparações de referências PSA, os resultados
concluídos e a convergência ideal. Se você já tiver o diagnóstico
`tmp/trotter/reference_checks.json` do mesmo estudo e ambiente, use
`--reference-checks tmp/trotter/reference_checks.json` para reaproveitá-lo;
ele é copiado e autenticado no novo estudo. O comando imprime um **novo**
`record_path`. Retome com ele:

```sh
.venv/bin/python scripts/run_study.py resume results/studies/ID-NOVO/study.json --next-phase
.venv/bin/python scripts/run_study.py resume results/studies/ID-NOVO/study.json --next-phase
```

A primeira retomada conclui T06; a segunda executa T07. Sem `--next-phase`,
executa ambas. A emenda mantém o limite ideal `|ΔK3| ≤ 0,001`, usa 29 pontos
em N=4, μ=10, τ=4 e 24 subpassos RK4 na referência PSA de μ=10, τ=2.
Contagens T06 já obtidas em τ=2 são preservadas; somente as referências
clássicas correspondentes são refinadas. O ponto confirmatório H2 em μ=3,
τ=2 e todas as contagens IBM permanecem os mesmos. A célula μ=10, τ=4
passa a usar 448 passos Trotter totais, fato declarado nas comparações de
sensibilidade. O diário da falha e seus resultados não são apagados.

## 4. Interromper e retomar

Para executar **uma fase por vez**, preservando os controles e análises do estudo:

```sh
.venv-research/bin/python scripts/run_study.py run --next-phase
```

O comando executa somente a primeira fase (reprodução publicada), grava a análise
e termina. O terminal mostra `record_path`, com o caminho do `study.json`, e
`next_phase`, com a próxima fase. Para executar a seguinte quando desejar:

```sh
.venv-research/bin/python scripts/run_study.py resume results/studies/ID/study.json --next-phase
```

Repita esse comando para cada fase seguinte. Use sempre o **mesmo registro**;
`run` inicia outro estudo. O estado `awaiting_next_phase` indica uma parada normal
entre fases; um controle reprovado continua sendo registrado como falha e impede
o avanço. Retomar sem `--next-phase` executa todas as fases restantes. A opção
também está disponível em `smoke`, para testar esse fluxo com a grade reduzida.
Uma fase pode conter várias simulações/sementes; Ctrl+C permite interromper
dentro dela e a retomada reaproveita as etapas completas.

Pode interromper com Ctrl+C. O terminal imprime o caminho do registro, também
identificado em `results/studies/LATEST.json`:

```sh
.venv-research/bin/python scripts/run_study.py resume results/studies/ID/study.json
```

Etapas já completas são verificadas por SHA-256 e reaproveitadas. Uma tentativa
interrompida é registrada e refeita; fases anteriores não são descartadas. Use o
mesmo `--output` da execução inicial. Uma trava impede duas retomadas simultâneas
do mesmo estudo. Fontes/dados/dependências diferentes exigem outra coleta ou o
snapshot original; `run_study` não oferece uma opção para ignorar essa diferença.

## 5. Resultados

| Local | Conteúdo |
| --- | --- |
| `results/studies/ID/study.json` | Estado de cada fase, tentativas, fontes, referências aos protocolos e hashes dos relatórios. |
| `results/studies/ID/FASE/analysis.json` | Critérios, métricas, IC95 e decisão estatística quando aplicável. |
| `results/studies/ID/FASE/*.csv` e `*.png` | Curvas K3 de exato/PSA/campo médio e erros, nas fases de coleta clássica/medições. |
| `results/protocols/ID/run.json` | Todas as etapas e execuções do protocolo, inclusive falhas. |
| `results/executions/ID/` | Entrada, receita reproduzível, passos, erros e resultado JSON de cada tentativa. |
| `results/RUN_ID/versions/` | Revisões imutáveis de manifestos, resumos e matrizes/amostras/contagens NPZ. |
| `results/_sources/` | Snapshot do código, dados da referência, protocolos e dependências. |
| `results/_cache/` | Exato, campo médio e probabilidades ideais reaproveitados por chave física e ambiente; nunca substitui sementes/medições independentes. |

Os JSONs referenciam os NPZ por hashes, formato, tipo e dimensões. As matrizes
volumosas permanecem binárias para evitar duplicá-las em listas JSON. Não apague
NPZ/snapshots antes de arquivar a coleta. `results/` está no `.gitignore`; copiar
o diretório completo para o arquivo científico/depósito de dados é uma etapa
separada do commit dos fontes.

Recalcular análises sem substituir o relatório original:

```sh
.venv-research/bin/python scripts/run_study.py analyze results/studies/ID/study.json
.venv-research/bin/python scripts/run_protocol.py replay results/executions/ID/execution.json
```

## 6. Hardware IBM (extensão separada)

Depois da coleta oficial local, prepare o caso primário no backend escolhido:

```sh
.venv-research/bin/python scripts/run_study.py hardware-plan results/studies/ID/study.json --backend ibm_kingston
```

Esse comando não acessa a fila nem envia jobs. Grava `08_hardware.json` e seu
orçamento: **80 jobs, 655.360 shots**, 327.680 por método. Backend é um parâmetro;
a disponibilidade de `ibm_kingston` deve ser conferida na conta. A chave fica no
`.env` da raiz (`IBM_QUANTUM_API_KEY`, `IBM_QUANTUM_INSTANCE`); nunca nos protocolos.
A calibração usa os qubits físicos finais do sinal correspondente. QPY, layout,
calibração do backend, opções, job ID e contagens são arquivados. `max_depth`
é verificado depois da transpiração e antes do envio.

Para iniciar os envios explicitamente:

```sh
.venv-research/bin/python scripts/run_protocol.py run results/studies/ID/08_hardware.json --allow-hardware
```

Consultar e arquivar resultados, repetindo enquanto houver jobs na fila:

```sh
.venv-research/bin/python scripts/run_study.py collect-hardware results/protocols/ID/run.json
```

Essa consulta não reenvia jobs. A análise conjunta IBM só ocorre com os 20 blocos
completos, incluindo as duas calibrações de cada bloco. Uma interrupção no exato
momento de um envio requer conferir o job na IBM; o runner impede reenviar
silenciosamente a mesma etapa com estado ambíguo.

## 7. Continuação com o integrador otimizado

O RK4 usa a identidade `sum_j g_ij P_j = sum_j P_j - P_i` quando a matriz é
exatamente uniforme fora da diagonal. Matrizes não uniformes usam multiplicação
matricial NumPy. Os campos constantes são preparados uma vez por integração.
A grade, as trajetórias, as sementes e os subpassos permanecem os mesmos.
Diferenças de arredondamento são verificadas contra o solver original arquivado.

Para aproveitar fases já concluídas sob a versão anterior:

```sh
.venv/bin/python scripts/run_study.py prepare-fast results/studies/ID_ORIGINAL/study.json
```

Execute entre fases, depois que a coleta parar normalmente. O comando confere
os hashes dos resultados e rejeita mudanças nos parâmetros dos protocolos ou
nas dependências. Compara PSA/campo médio nas células físicas oficiais, com
sondagens de 64 trajetórias, casos não uniformes e um caso de desempenho com
4096 trajetórias, 201 tempos e 12 subpassos. Exige diferença absoluta até 1e-10
nas amostras, Bloch, momentos e cumulantes. Essa tolerância é de equivalência
numérica da implementação; os critérios científicos do estudo não mudam.

A verificação fica em `optimization_verification.json`, com entradas, sementes,
tempos e desvios por caso. Só depois de aprovada, o comando cria **outro registro
de estudo**, ligado ao original, com os resultados concluídos reaproveitados.
O estudo original e seus snapshots ficam intactos. Os protocolos/revisões
originais continuam sendo a origem de cada fase herdada. Os relatórios são
copiados e seus hashes conferidos; as matrizes brutas não são duplicadas.

Use o **novo `record_path`** mostrado pelo comando:

```sh
.venv/bin/python scripts/run_study.py resume results/studies/ID_NOVO/study.json --next-phase
```

Sem `--next-phase`, continua todas as fases locais restantes. A aceleração
medida se refere ao integrador da PSA/campo médio, não ao tempo total das fases,
à análise estatística, à gravação dos dados ou à execução/fila IBM.

## 8. Revalidação dos relatórios oficiais

Foi corrigido um erro de encaminhamento: os nomes públicos como
`T03-classica-principal` não coincidiam com os identificadores internos como
`03_classica_principal`. Os relatórios anteriores a essa correção registravam
controles gerais, mas omitiam análises específicas, inclusive a meta amostral.
Os cálculos e artefatos brutos continuam disponíveis nas revisões originais.

Depois de interromper a coleta, reavalie os controles sem novas simulações:

```sh
.venv/bin/python scripts/run_study.py revalidate results/studies/ID/study.json
```

O comando exige o mesmo Python/dependências e aceita apenas alterações nos
arquivos responsáveis pelo encaminhamento das análises. Confere os artefatos
originais e grava novos relatórios em `results/revalidations/ID/`, mantendo os
anteriores. Código de saída 2 significa reprovação/incompletude científica,
mesmo que a execução da análise tenha terminado normalmente.

Se algum controle reprovar, a coleta oficial deve permanecer interrompida.
É necessário definir previamente uma coleta suplementar que cumpra a meta de
precisão, preservando os resultados anteriores e a justificativa da emenda.
Não diminuir o limite para transformar uma reprovação em aprovação.

Uma prévia descritiva independente, com CSVs e figura do caso N=4/μ=3, foi salva
em `results/previews/`. Ela não contém IC95 nem estabelece conclusão sobre H1/H2.
A receita e o código usados nessa prévia são copiados para a mesma pasta e
identificados por SHA-256 no JSON. Os arquivos de prévia não substituem a
revalidação nem autorizam continuar a coleta.

## 9. Recuperar a coleta com a emenda amostral v3

A emenda está em `configs/protocols/artigo_v1/especificacoes/emenda_amostragem_v3.json`.
O protocolo suplementar fixa **20 sementes novas (70001…70020), com 4096 trajetórias
por bloco**, nas seis células N=4/8 e μ=0,1/1/10. São 120 execuções; a meta de erro
padrão máximo 0,01 é preservada. O resultado com cinco sementes permanece
arquivado como condição reprovada, substituída por uma condição de maior orçamento.
Esta emenda foi definida após a falha e a visualização de uma prévia; essa história
é registrada e não se altera o ponto principal H2 nem as hipóteses para obter sucesso.

Prepare uma continuação, sem executar novas simulações:

```sh
.venv/bin/python scripts/run_study.py prepare-recovery results/studies/ID_INTERROMPIDO/study.json
```

O comando revalida os controles, verifica os hashes e imprime um **novo record_path**.
Preserva os diários originais. No novo estudo, a validação suplementar vem antes de
qualquer avanço; se reprovar, o executor para, sem ampliar a amostra automaticamente.
Os dados T03 são reanalisados com o encaminhamento corrigido, sem repetir sua coleta.
O diário T05 é derivado do anterior e reutiliza as quatro etapas completas; uma
tentativa interrompida pode ser refeita. A origem de cada etapa continua registrada.

Execute primeiro somente a validação suplementar:

```sh
.venv/bin/python scripts/run_study.py resume results/studies/ID_NOVO/study.json --next-phase
```

Após aprovação, repita para avançar uma fase por vez. Sem `--next-phase`, executa
as reanálises e as fases locais restantes, respeitando os controles. O novo estudo
contém a emenda e os protocolos completos, permitindo reproduzir a sequência.

## 10. Colocar o hardware IBM na fila antes de concluir a coleta local

A aquisição antecipada foi solicitada explicitamente durante a recuperação. Ela
usa o ponto principal já fixado e mantém as contagens **provisórias**, sem conclusão
H2 antes da validação amostral e da T07. As fases locais T04–T07 já constam da
continuação; a fila IBM é um fluxo independente, com seus próprios registros.

```sh
.venv/bin/python scripts/run_study.py prepare-hardware-queue results/studies/ID/study.json --backend ibm_kingston
.venv/bin/python scripts/run_study.py queue-hardware results/hardware-queues/ID/queue.json --allow-hardware
```

A preparação não envia jobs. Confere disponibilidade do backend, precisão ideal
de K3 <=0,001 e profundidade após transpilar, e registra um QPY de prévia.
O orçamento é **80 jobs e 655360 shots totais**, incluindo os dois estados de
calibração por repetição. Cada envio registra QPY efetivo, layout, propriedades,
opções e job ID. A transpilação e o teto de profundidade são conferidos novamente
antes de cada envio. Não há alteração automática dos passos para caber na máquina.

Consultar resultados usa o run.json indicado pela fila, sem novos envios:

```sh
.venv/bin/python scripts/run_study.py collect-hardware results/protocols/ID/run.json
```

Enquanto os controles locais não forem aprovados, a análise de hardware permanece
exploratória. O estágio de aquisição antecipada e seu orçamento não demonstram
validade científica ou sucesso de mitigação.

Na aquisição antecipada, o número de passos é escolhido **antes das contagens IBM**:
o menor entre 1/2/4/8/16 por intervalo que satisfaça erro ideal máximo K3 <=0,001
em todos os tempos e trios da grade primária. As cinco checagens e a escolha ficam
no queue.json. No cenário primário, foram selecionados 2 por intervalo (14 totais),
com erro 0,0007155; a tentativa com 112 totais excedeu o teto de profundidade.
O hardware usa essa discretização própria validada. Os perfis locais T06/T07
mantêm seus 112 passos e não são rotulados como o mesmo circuito do hardware.
Layout inicial e semente de transpilação ficam fixos entre repetições; as sementes
PSA continuam independentes e as calibrações usam o layout físico final do sinal.
