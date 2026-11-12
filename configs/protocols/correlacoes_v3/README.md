# Extensão exploratória v3 — correlações em 4, 6 e 8 qubits

Os [resultados locais, gráficos e IDs dos jobs IBM](../../../analysis/campaigns/README.md#20261107-correlacoes-v3) estão preservados em um pacote com hashes. A busca executou 36 configurações e a análise de ruído avaliou 108 condições, com métodos bruto e mitigado sob orçamento igual. A PSA usa todas as configurações de sua distribuição discreta inicial.

**Atualização de 8 de novembro de 2026:** os 30 jobs terminaram. O [pacote de resultados físicos IBM](../../../analysis/campaigns/README.md#20261108-resultados-ibm) contém a confirmação de N=4, os pilotos N=6/8, as contagens verificadas, as análises de sensibilidade e os gráficos. O pacote anterior permanece como fotografia da fase local e dos envios.

O [replay Aer pareado à IBM](../../../analysis/campaigns/README.md#20261108-aer-ibm-pareado) reexecuta os programas Runtime arquivados com o mesmo orçamento por bloco, mapeamento e política de twirling, usando ruído derivado das calibrações originais. Foi feito localmente, sem novos jobs. Esse pacote deve ser usado para a comparação Aer–IBM; a varredura genérica anterior permanece preservada.

O [desenho](design.json) foi fixado antes da busca. A [emenda de circuitos curtos](emenda_circuitos_curtos.json) foi definida após a busca ideal, para avaliar o compromisso entre discretização e ruído. A [emenda de compilação](emenda_compilacao.json) respondeu à falha do controle numérico com otimização de nível 3. As tentativas anteriores foram preservadas.

Foram enviados dez jobs físicos desta extensão: cinco com seis qubits e cinco com oito, todos no `ibm_kingston`, totalizando 40.960 shots. Separadamente, a confirmação v2 de quatro qubits recebeu vinte jobs e 327.680 shots. Os novos pontos de seis/oito qubits usam μ=10 e dois feixes; a confirmação v2 conserva o ponto μ=3, τ=1,5 e seus critérios originais.

Para retomar os cálculos locais, na raiz do repositório:

```sh
.venv/bin/python scripts/run_correlation_search.py run
.venv/bin/python scripts/run_correlation_noise.py
.venv/bin/python scripts/run_correlation_short_noise.py run
```

Para consultar os jobs já enviados, sem novos envios:

```sh
.venv/bin/python scripts/run_correlation_hardware.py collect
.venv/bin/python scripts/prepare_short_circuit_experiments.py collect-hardware --record results/protocols/20261107T233046Z-6d048a1b4b85/run.json
```

Os dados correntes ficam em `results/campaigns/20261107-correlacoes-v3/`. A triagem física envia os próprios QPY arquivados, registra os IDs após cada submissão e impede repetir automaticamente uma submissão de estado ambíguo. O orçamento é limitado a dez jobs de 4.096 shots; a retomada pula os IDs já registrados.

Os resultados locais demonstram maior precisão que a PSA em pontos selecionados sob ruído genérico. Os dados físicos também favoreceram menor erro nos alvos avaliados; a confirmação N=4 passou na regra original, enquanto N=6/8 continuam pilotos de cinco blocos. Superioridade computacional exige comparação de recursos com métodos clássicos competitivos em escala maior.
