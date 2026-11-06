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

Além dos oito protocolos acima, estão implementados:

- `00_reproducao_publicada.json`: uma etapa, N=8 e 10000 trajetórias; dados da figura e conversão documentados em `data/benchmarks/lacroix2024/`.
- `04_qiskit.json`: 60 etapas; 15 referências e 45 verificações em τ=1/2/4.
- `07_mitigacao.json`: 2400 etapas; 300 referências, 300 ideais e 1800 casos com calibração incluída no orçamento.

Execute o estudo completo com os gates científicos, análise, CSVs, gráficos e
retomada conforme [EXECUTAR_EXPERIMENTOS.md](../../../EXECUTAR_EXPERIMENTOS.md):

```sh
.venv/bin/python scripts/run_study.py plan
.venv/bin/python scripts/run_study.py smoke --output results/validacao-software
.venv/bin/python scripts/run_study.py run
```

`especificacoes/` descreve conversões, mitigação e extensão IBM; não é um
formato aceito diretamente pelo runner. O comando `hardware-plan` materializa o
protocolo IBM quando os pré-requisitos locais forem satisfeitos. O cache
reaproveita exato/campo médio e evolução ideal sem reutilizar medições aleatórias.

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
descritos em `EXECUTAR_EXPERIMENTOS.md`.
