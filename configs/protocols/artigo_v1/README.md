# Desenho dos experimentos do artigo — versão 1

O desenho científico está definido antes da coleta. A verificação inicial valida
precisão e custo; não é necessário esperar seus resultados para especificar os
demais testes. Se um controle falhar, registrar uma nova versão e a justificativa,
preservando os resultados anteriores.

O foco primário é Kzzz: medir quanto PSA e circuito reproduzem os cumulantes
conectados de três neutrinos, usando o exato como referência. Probabilidades e
pares são controles secundários.

| Arquivo executável | Conteúdo | Etapas |
| --- | --- | ---: |
| `01_controles.json` | N=4,6,8 sem interação; referência, circuito local e verificação Qiskit. | 9 |
| `02_integracao.json` | N=4,8; μ=0,1/1/10; 5 sementes; RK4 com 2/4/8/12 subpassos. | 120 |
| `02_amostragem.json` | Mesmos casos; PSA com 512/1024/2048/4096 trajetórias. | 120 |
| `03_classica_principal.json` | N=4,6,8; cinco μ; 20 sementes e 4096 trajetórias. | 300 |
| `03_classica_extensao.json` | Extensão para N=12,16, condicionada a recursos. | 200 |
| `04_trotter.json` | 15 referências e 75 circuitos com 1/2/4/8/16 passos. | 90 |
| `05_medicoes.json` | 300 referências; 900 circuitos com 1024/4096/16384 shots, sem ruído. | 1200 |
| `06_ruido.json` | N=4; cinco μ; τ=1/2/4; 20 sementes; três perfis de ruído e três orçamentos. | 3300 |

Esses arquivos são compatíveis com o runner. Gerar os dados não implementa, por
si só, a análise estatística conjunta: critérios, pré-requisitos científicos e
pendências estão no catálogo `configs/estudos/artigo_v1.json`.

Exemplo de execução do primeiro protocolo:

```sh
.venv/bin/python scripts/run_protocol.py run configs/protocols/artigo_v1/01_controles.json
```

As coletas extensas devem começar após reprodução publicada, verificações de
precisão e medição dos recursos necessários. Os pré-requisitos do catálogo são
condições científicas; o runner ainda não aprova esses critérios automaticamente.
O código atual recalcula exato/campo médio para cada semente e repete a evolução
ideal ao mudar shots. Esse reaproveitamento deve ser melhorado antes das grades
extensas, sem mudar seu desenho físico.

## Especificações com implementação pendente

`especificacoes/` contém definições científicas JSON, e não arquivos aceitos pelo
runner:

- `reproducao_publicada.json`: alvo, conversões e evidência necessária para o
  benchmark de Lacroix et al. (2024).
- `mitigacao.json`: método tensorial de leitura, estados de calibração, divisão
  do orçamento, incertezas e decisão da H2.
- `hardware_ibm.json`: caso candidato, pré-requisitos e informações a arquivar;
  o dispositivo e orçamento físico dependem do acesso disponível.

O teste primário H2 fica fixado em N=4, μ=3, trio (0,1,2), τ=2, perfil moderado e
16384 medições totais por repetição, com 20 repetições. O orçamento agregado é
327680 medições por método. Na mitigação, 75% de cada orçamento vai para sinal e
12,5% para cada um dos dois estados de calibração. Os demais casos são análises
de sensibilidade, sem seleção posterior de um novo teste primário.

Os limiares v1 são metas operacionais declaradas: erro numérico de K3 até 1e-5,
erro máximo de Trotter até 1e-3, piso de sinal RMS para normalização de 1e-4 e
margem de equivalência H2 de 0,01. São escolhas de resolução do estudo, não
constantes da literatura. Falhar em atingir uma meta é resultado a registrar;
não autoriza mudar silenciosamente o critério.

Para regenerar os JSONs ou conferir se correspondem ao desenho versionado:

```sh
.venv/bin/python scripts/define_article_protocols.py
.venv/bin/python scripts/define_article_protocols.py --check
```

Esses dois comandos apenas geram/conferem definições. Não executam cálculos nem
enviam jobs IBM. A execução de qualquer protocolo continua produzindo os registros
descritos em `REPRODUTIBILIDADE.md`.
