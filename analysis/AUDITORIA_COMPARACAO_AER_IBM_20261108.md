# Comparabilidade Aer–IBM e prioridades — 8 de novembro de 2026

**Atualização após esta auditoria:** foi executado o [replay Aer pareado aos 30 jobs IBM](campaigns/README.md#20261108-aer-ibm-pareado), sem novas submissões. Ele usa os programas Runtime recuperados, QPY, mapeamento, política de twirling, orçamento e calibrações arquivadas de cada job. A sequência aleatória interna do servidor e o cronograma real de pulsos não foram disponibilizados; o relatório distingue esse limite do que foi efetivamente igualado. A comparação abaixo documenta a varredura Aer original, preservada como histórico.

Na varredura original em N=6/8 foram mantidos o Hamiltoniano, estado inicial, frequências, acoplamentos, tempo, trio principal e circuito lógico de dois passos. A cadeia de execução e o modelo de ruído eram diferentes. Assim, a coleta testava o mesmo problema físico nesses dois tamanhos, mas aquela comparação entre simulador e dispositivo não era integralmente pareada.

| Aspecto | Aer da extensão v3 | IBM da extensão v3 |
| --- | --- | --- |
| Modelo e parâmetros N=6/8 | Mesmos pontos físicos da IBM | Mesmos pontos físicos do Aer |
| Passos do circuito curto | 2 | 2 |
| Compilação | Base genérica RZ/SX/X/CX, nível 1, sem conectividade IBM | Alvo `ibm_kingston`, nível 1, layout e roteamento físicos |
| N=6: portas de dois qubits / profundidade | 108 CX / 173 | 204 CZ / 540 |
| N=8: portas de dois qubits / profundidade | 192 CX / 237 | 429 CZ / 927 |
| Ruído | Despolarização uniforme sintética e inversões independentes de leitura | Ruído físico do dispositivo |
| Twirling | Não aplicado nessa varredura Aer | Ativado; 32 randomizações × 128 shots por job |
| Shots brutos por ponto | 81.920 | 20.480, em cinco jobs |
| Correção de leitura | Avaliada com calibrações simuladas | Não aplicada aos novos dados físicos |

As quantidades de CX e CZ descrevem os circuitos respectivos; não são taxas de erro diretamente equivalentes. A profundidade indica camadas do circuito, não tempo físico diretamente comparável sem duração das portas e escalonamento.

No perfil selecionado do Aer, p₂=0,001, p₁=0,0001 e probabilidade de inversão de leitura=0,03. Esses parâmetros não foram ajustados à calibração IBM. O parâmetro despolarizante também não deve ser igualado automaticamente à infidelidade média de porta publicada pelo backend.

O Aer primeiro calcula a distribuição final ruidosa via matriz densidade; os shots e as calibrações são então amostrados localmente dessa distribuição. Na IBM, as contagens vêm de execuções físicas. Portanto, a linha `shots=1` na simulação de matriz densidade não é o orçamento estatístico final de 81.920 medições do estimador local.

## O caso de quatro qubits exige outra associação

A confirmação IBM N=4 usa μ=3, τ=1,5, estado de domínio e acoplamento uniforme. O caso N=4 do gráfico local v3 usa μ=10, τ=0,55 e dois feixes. Esses dois pontos não devem ser colocados numa comparação direta Aer–IBM como se tivessem os mesmos parâmetros. Existe uma triagem Aer v2 do ponto μ=3,τ=1,5; o pareamento deve partir dela e de seus próprios shots e opções.

## O que as diferenças permitem concluir

Comparar IBM e PSA com a mesma referência exata no mesmo ponto físico continua válido. A falta de pareamento integral Aer–IBM limita explicar a diferença entre a previsão Aer e o resultado do chip e atribuir sua causa exclusivamente ao ruído físico.

Por exemplo, em N=8, C₃ Aer bruto≈−0,08377 e C₃ IBM≈−0,02250, para exato≈−0,13079. A IBM preserva um sinal menor que o previsto pelo perfil genérico. Não é possível separar retrospectivamente, com essa comparação isolada, os efeitos de roteamento, canais de ruído, twirling, leitura e deriva.

Menos shots aumentam a flutuação estatística; ampliar o orçamento não remove o viés de portas. Nessa etapa, a atenuação observada justifica priorizar a fidelidade da evolução e da leitura, além da confirmação estatística.

## Prioridades propostas

1. **Parear a simulação ao circuito físico já executado — concluído.** O replay mantém os 20 blocos ×16.384 shots de N=4 e cinco blocos ×4.096 shots para cada N=6/8. Além do QPY, recupera o próprio gerador Samplex e o template Runtime de twirling. Os controles ideais, sementes locais, contagens e hashes estão no pacote novo.
2. **Separar as fontes de perda — concluído no modelo.** Foram avaliados ideal, apenas leitura, portas/relaxação, combinação com inicialização/leitura e sensibilidade a tempos ociosos ASAP. A calibração arquivada permite uma aproximação mais informada; ela não garante reproduzir deriva ou todos os canais de erro presentes durante os jobs. Os resultados não foram usados para ajustar o ruído ao chip.
3. **Confirmar os pilotos N=6/8.** Fixar antecipadamente os mesmos pontos físicos, trio, margem relevante, orçamento e regra de análise. Distribuir repetições em períodos de calibração distintos e declarar multiplicidade. Cinco blocos atuais não equivalem a uma confirmação ampla de validade.
4. **Avaliar correção de leitura física com orçamento comparável.** Coletar calibrações dos qubits realmente usados e incluir seu custo e sua incerteza. Conservar o resultado bruto e verificar as suposições do modelo de leitura.
5. **Fazer uma comparação de escala controlada.** Manter a mesma regra de frequências, estado inicial, geometria, μ e τ ao variar N. Os três grupos IBM atuais mudam outros parâmetros além do tamanho.
6. **Fortalecer a comparação clássica e o custo.** Reportar precisão, tempo, memória, shots, portas, tempo de QPU e custos de calibração. Comparar com a referência nula e métodos clássicos competitivos, além da PSA. A evolução exata ainda é acessível nos tamanhos usados.

O Aer oferece modelos aproximados construídos a partir de propriedades de dispositivos, incluindo erros de portas, relaxação térmica e leitura. O mecanismo está documentado em [NoiseModel](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.NoiseModel.html) e [AerSimulator](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html). Reproduzir a política de supressão também requer considerar as [opções de twirling](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques).

Fontes locais: `scripts/run_correlation_short_noise.py`, `scripts/run_correlation_noise.py`, `scripts/run_correlation_hardware.py`, `results/campaigns/20261107-correlacoes-v3/hardware/plan.json` e os pacotes de resultados de 7 e 8 de novembro. Esta auditoria não enviou novos jobs nem alterou os resultados anteriores.
