# Guia de leitura dos experimentos e dos circuitos

Este guia descreve a campanha de 7 de novembro de 2026 e conserva os exemplos locais usados para explicar os métodos. **Atualização de 8 de novembro:** os 30 jobs IBM terminaram. A confirmação N=4 passou no critério original e os pilotos N=6/8 favoreceram menor erro que a PSA nos pontos avaliados. Os resultados físicos completos estão no [relatório IBM concluído](campaigns/README.md#20261108-resultados-ibm). Os números identificados abaixo como Aer continuam sendo simulações locais.

Para comparar diretamente o simulador com os jobs físicos, consulte o [novo replay Aer pareado](campaigns/README.md#20261108-aer-ibm-pareado). Ele usa os programas IBM recuperados, o mesmo orçamento de medições e política de twirling, e ruído calibrado. Os exemplos Aer históricos deste guia usam o modelo genérico anterior e não foram substituídos pelos novos números.

**A pergunta experimental.** Queremos estimar uma correlação conectada de três neutrinos e comparar sua precisão entre PSA e circuito, usando a evolução exata como referência. Cada neutrino tem dois sabores no modelo: νₑ e νₓ. O termo “três corpos” se refere a três partículas. A computação quântica usa um qubit para o sabor de cada neutrino; não há neutrinos reais dentro do processador IBM.

**Quais modelos foram enviados à IBM.**

| Parâmetro | Confirmação com 4 qubits | Triagem com 6 qubits | Triagem com 8 qubits |
| --- | --- | --- | --- |
| Objetivo | Repetir independentemente um caso já selecionado | Explorar um sistema maior | Explorar um sistema maior |
| μ, interação em unidades da frequência média | 3 | 10 | 10 |
| θ, mistura de sabores | 0,2 rad | 0,2 rad | 0,2 rad |
| Tempo adimensional τ | 1,5 | 0,55 | 0,65 |
| Sabores iniciais, na ordem q₀,q₁,… | 0,0,1,1 | 0,1,0,1,0,1 | 0,1,0,1,0,1,0,1 |
| Geometria | Acoplamento uniforme entre todos os pares | Dois feixes antiparalelos | Dois feixes antiparalelos |
| Pares com interação não nula | 6 | 9 | 16 |
| Trio principal, índices começando em zero | (0,1,2) | (0,1,2) | (1,3,5) |
| Passos Trotter totais | 2 | 2 | 2 |
| Jobs × shots por job | 20 × 16.384 | 5 × 4.096 | 5 × 4.096 |
| Portas de dois qubits compiladas | 78 | 204 | 429 |
| Profundidade compilada | 294 | 540 | 927 |

Todos foram enviados ao `ibm_kingston`, com gate twirling. Em 6/8 qubits, foram fixadas 32 randomizações × 128 shots por job. A confirmação de quatro qubits conserva as opções do protocolo v2. Não foi adicionada calibração de leitura aos novos jobs dessas três coletas; os valores físicos serão inicialmente brutos, com supressão por twirling.

Frequências individuais ωᵢ:

- N=4: [0,7; 0,9; 1,1; 1,3].
- N=6: [0,7; 0,82; 0,94; 1,06; 1,18; 1,3].
- N=8: [0,7; 0,785714; 0,871429; 0,957143; 1,042857; 1,128571; 1,214286; 1,3].

As frequências têm média 1. μ controla a intensidade da interação em relação a essa escala; θ controla a mistura no termo de vácuo; τ é o tempo da evolução física simulada, e não segundos de execução ou tempo em fila. Frequências distintas representam energias distintas no modelo.

Na geometria de dois feixes, os índices da primeira metade pertencem ao feixe A e os da segunda, ao B. Há interação A–B; o acoplamento dentro de A e dentro de B é zero. Os valores não nulos de gᵢⱼ são 5/3 para N=6 e 7/4 para N=8. Essa normalização mantém a média sobre todos os pares distintos em 1. Em quatro qubits, gᵢⱼ=1 para todo par distinto.

Os três grupos físicos variam vários parâmetros ao mesmo tempo. Comparar diretamente os seus erros não isola o efeito de aumentar N. Para investigar escala, precisamos também de comparações com os demais parâmetros controlados.

**O que foi calculado localmente.** A busca exploratória combinou 3 tamanhos × 3 interações (1,3,10) × 2 estados iniciais (domínio e alternado) × 2 geometrias (uniforme e dois feixes): 36 configurações. Cada uma contém 61 tempos entre 0 e 3, todos os indivíduos, pares e trios.

Nos estados de domínio, a primeira metade começa em νₑ e a segunda em νₓ; nos alternados, os sabores se alternam. Essa escolha de sabores é independente da divisão dos índices entre os feixes angulares.

Foram selecionados pontos em que o sinal exato e o desvio PSA–exato fossem resolvidos, com uma regra que também penalizasse circuitos caros. A seleção ocorreu com cálculos locais, antes dos novos resultados físicos. Portanto, os candidatos de N=6/8 são exploratórios. A confirmação N=4 é outra linha, definida a partir da triagem v2 anterior.

| Nome nos resultados | Como é calculado | O que controla |
| --- | --- | --- |
| Exato | Evolução clássica das 2ᴺ amplitudes quânticas | Referência numérica convergida |
| PSA | Evolução de um conjunto de condições clássicas iniciais | Erro da aproximação, além do erro numérico |
| Circuito ideal | Simulação clássica das portas quânticas aproximando a evolução | Erro da discretização Trotter |
| Aer bruto | Simulação local de portas ruidosas, leitura e shots finitos | Viés de ruído e flutuação de medição |
| Aer mitigado | Correção de leitura com calibrações simuladas | Ganho e custo estatístico da correção |
| IBM | Circuito executado no processador físico | Ruído real, compilação e variação entre execuções |

A PSA desta campanha usa todas as configurações possíveis de sua distribuição inicial bi-valuada: 256, 4.096 e 65.536 para N=4,6,8. Isso elimina sua flutuação Monte Carlo nesses cálculos; permanece o erro da aproximação e da integração. Esses 4ᴺ pontos pertencem ao conjunto clássico da PSA. O espaço quântico tem 2ᴺ amplitudes.

**Como o circuito representa o modelo.** O Hamiltoniano é

H = Σᵢ (ωᵢ/2) B·σᵢ + μ/(4N) Σᵢ<ⱼ gᵢⱼ σᵢ·σⱼ,

com B=(sin 2θ,0,−cos 2θ). A primeira soma faz cada sabor precessionar; a segunda descreve interações entre pares. A evolução pretendida é U(τ)=exp(−iHτ).

Um circuito é uma sequência de operações nos qubits. Neste projeto, ele segue:

1. Preparar os sabores iniciais.
2. Aplicar um bloco de evolução aproximada.
3. Aplicar outro bloco de evolução aproximada.
4. Medir todos os qubits na base de sabor.

No preparo, todos começam em 0. Aplicar X coloca em 1 os índices cujo sabor inicial é νₓ. Para seis qubits, são q₁,q₃,q₅; para oito, q₁,q₃,q₅,q₇.

Cada passo Trotter tem quatro partes, em ordem temporal:

> Meia evolução individual → meia evolução dos pares em ordem direta → meia evolução dos pares em ordem inversa → meia evolução individual.

Essa composição simétrica é de segunda ordem. Na confirmação N=4, cada passo representa Δτ=0,75; nos casos N=6/8, Δτ=0,275 e 0,325, respectivamente. As rotações individuais são portas de um qubit. Os fatores de interação são portas de dois qubits.

Uma porta de interação de um par tem a forma G(α)=exp[−iα(XX+YY+ZZ)]. Ela mistura as amplitudes de 01 e 10. Para um par inicialmente em 01, as probabilidades de permanecer em 01 e aparecer em 10 são cos²(2α) e sin²(2α). O estado antes de medir também contém fases, que importam quando combinamos várias portas. O parâmetro α dessa porta é diferente do θ de mistura de sabores.

No código, a meia evolução de um par usa α=μgᵢⱼΔτ/(8N). No meio de um passo, o último par da ordem direta aparece novamente como o primeiro da ordem inversa. A compilação pode combinar operações equivalentes. A figura didática representa uma porta isolada; no sistema completo, ela é intercalada com outras rotações e interações.

Correlações de três corpos podem surgir da composição dessas interações entre pares. Em N=6, o trio principal (0,1,2) pertence ao mesmo feixe e não tem interação direta interna; seus membros interagem com o outro feixe, que pode mediar correlações.

**Por que dois passos produzem centenas de portas.** “Passo Trotter” é um bloco matemático. Cada bloco contém operações de todos os pares relevantes e de todos os qubits. Depois, a compilação traduz essas operações para as portas e conexões disponíveis no chip.

Nos QPY enviados, as portas nativas principais são `rz` e `sx`, de um qubit, e `cz`, de dois qubits. N=6 contém 204 CZ, 489 SX e 485 RZ; N=8 contém 429 CZ, 999 SX e 862 RZ. Profundidade é o número de camadas de operações, considerando o paralelismo possível. Assim, dois passos Trotter e profundidade 927 descrevem coisas diferentes.

O backend tem 156 posições físicas, mas os circuitos verificados usam seis ou oito delas ativamente. O mapeamento final de N=6 é [136,123,122,124,143,144]; o de N=8 é [123,136,124,122,143,142,144,141], na ordem dos qubits lógicos. Números como 143 são identificadores de posição no chip.

Mais passos costumam melhorar a aproximação ideal, mas acrescentam portas e exposição ao ruído. Por isso comparamos o erro final, incluindo o ruído. Os circuitos curtos selecionados têm erros ideais de C₃ aproximadamente 0,006981, 0,001286 e 0,012848 em N=4,6,8 na exploração v3. A confirmação N=4 v2 usa outro ponto, com erro ideal aproximado de 0,000824.

**O papel do twirling.** Ele usa variantes do circuito com operações de Pauli compensadas: idealmente, todas realizam a mesma evolução. A combinação dos resultados busca tornar certos erros coerentes mais tratáveis. A correção de leitura é outro procedimento, aplicado depois de medir e dependente de calibrações. Na tabela local, “mitigado” refere-se à correção de leitura; nos novos jobs IBM, usamos twirling e ainda não há correção de leitura desses dados.

**O que sai de uma medição.** Um shot prepara o estado novamente, executa o circuito inteiro e mede uma vez. Com oito qubits, ele retorna oito bits. Milhares de shots produzem uma tabela de frequências dos resultados, e não uma cópia completa da função de onda.

Usamos a convenção Z=+1 para bit 0 e Z=−1 para bit 1. Cada shot fornece produtos de um, dois e três desses valores. Por exemplo, os resultados [0,1,0] de um trio dão valores [+1,−1,+1] e produto −1. A média desses produtos nos shots estima ⟨ZᵢZⱼZₖ⟩.

No texto e nas configurações, listamos os qubits na ordem q₀,q₁,… . Nos bitstrings exibidos pelo Qiskit, q₀ fica à direita. Para interpretar um trio, use seus índices lógicos e essa convenção, não a posição visual contada da esquerda.

**Momento e cumulante são diferentes.** Escrevendo mᵢ=⟨Zᵢ⟩, mᵢⱼ=⟨ZᵢZⱼ⟩ e mᵢⱼₖ=⟨ZᵢZⱼZₖ⟩,

C₃ᵢⱼₖ = mᵢⱼₖ − mᵢmⱼₖ − mⱼmᵢₖ − mₖmᵢⱼ + 2mᵢmⱼmₖ.

O cumulante remove do momento de três partículas as contribuições explicadas pelas médias e pelos pares. Ele é um número com sinal, não uma probabilidade. Mais negativo não significa mais preciso: precisamos compará-lo com a referência. C₃ não nulo indica uma correlação conectada nessa componente, mas, sozinho, não certifica emaranhamento nem identifica uma interação fundamental de três partículas.

As mesmas contagens de todos os qubits fornecem todos os observáveis em Z: por exemplo, seis qubits têm 20 trios e oito têm 56. O trio escolhido previamente é o alvo principal; os demais são resultados secundários, com dependência estatística e multiplicidade a considerar.

**Exemplo real de como comparar os números.** No caso local N=8, μ=10, τ=0,65, trio (1,3,5), com p₂=0,001, p₁=0,0001 e leitura=0,03:

| Método | C₃ | Erro absoluto frente ao exato |
| --- | ---: | ---: |
| Exato | −0,130788 | — |
| PSA completa | +0,050202 | 0,180990 |
| Aer bruto, dois passos | −0,083768 | 0,047020 |
| Aer mitigado | −0,101864 | 0,028925 |

Para o método bruto, a redução de erro é 100×(1−0,047020/0,180990)≈74%. Isso significa redução do erro desse observável nesse ponto. Não significa probabilidade de acerto de 74%, fidelidade quântica de 74% ou aceleração computacional de 74%.

O orçamento local é 81.920 shots por método: o bruto usa todos no sinal; o mitigado usa 61.440 no sinal e 10.240 em cada uma das duas calibrações. A triagem física N=8 tem 20.480 shots no total, portanto não deve reproduzir a mesma precisão estatística do orçamento local. O ruído real também é diferente do modelo Aer.

**Como ler D e os intervalos.** Definimos

> D = |C₃_circuito−C₃_exato| − |C₃_PSA−C₃_exato|.

- D<0: o circuito tem menor erro que a PSA.
- D>0: a PSA tem menor erro.
- IC95 de D inteiramente abaixo de zero: evidência pontual de menor erro do circuito, sob as suposições da análise.
- IC95 contendo zero: os dados não resolvem a comparação nesse nível de incerteza.

No exemplo bruto, D≈−0,133970 e o IC95 é [−0,140378;−0,127523]. O resultado favorece o circuito no simulador. Esse é um intervalo exploratório pontual; a busca em muitos casos não o transforma automaticamente em uma conclusão global.

O intervalo é obtido repetindo o cálculo com reamostragens das contagens, preservando a dependência dos bits. Na análise local, calibrações também são reestimadas. Na triagem física, os jobs independentes serão usados para avaliar a variação entre execuções, com análise alternativa sob hipótese estacionária. IC95 não elimina viés de portas nem demonstra que o modelo de ruído seja adequado ao dispositivo.

Também devemos comparar com C₃=0. Em N=8, essa previsão tem erro 0,130788, menor que o da PSA. Assim, uma saída totalmente sem sinal poderia superar a PSA sem recuperar a correlação. Por isso exigimos evidência de sinal não nulo e melhora sobre a referência nula na seleção dos novos candidatos físicos.

Para afirmar equivalência ao exato em ±0,01, o intervalo de circuito menos exato precisa caber inteiro nessa faixa. No exemplo bruto ele é [0,040612;0,053466]; no mitigado, [0,020416;0,038130]. Ambos melhoram sobre a PSA, mas nenhum atende à equivalência definida.

**Quatro conclusões com forças diferentes.**

1. Detectar sinal de correlação: C₃ distinguível de zero.
2. Ganhar em precisão sobre a PSA: erro menor, com incerteza controlada.
3. Recuperar o exato dentro de uma margem previamente definida.
4. Demonstrar vantagem computacional: atingir uma precisão relevante com recursos melhores que métodos clássicos competitivos.

Os cálculos locais sustentaram a segunda conclusão em pontos selecionados. Os dados físicos concluídos em 8 de novembro também favoreceram menor erro que a PSA: confirmação independente em N=4 e pilotos exploratórios em N=6/8. Nenhum desses pontos físicos recuperou o exato na margem ±0,01. A quarta conclusão exige outro estudo de escala e custo: a evolução exata ainda é viável em N=8. Ter mais qubits, isoladamente, não demonstra essa vantagem.

**Em que ordem abrir os arquivos.**

1. [README da campanha](campaigns/README.md#20261107-correlacoes-v3): visão geral e figuras.
2. [Configuração executada no hardware](../results/campaigns/20261107-correlacoes-v3/hardware/plan.json): parâmetros, trio, portas, layout e hashes dos circuitos N=6/8.
3. [Busca clássica](campaigns/20261107-correlacoes-v3/data/search.csv): uma linha por configuração; erros sobre toda a janela de 61 tempos e todos os trios.
4. [Comparação de ruído](campaigns/20261107-correlacoes-v3/comparacao_ruido.csv): uma linha por método, circuito e condição de ruído em um trio e tempo selecionados. Esses erros instantâneos não são a mesma métrica agregada da busca.
5. [IDs IBM na fotografia publicada](campaigns/20261107-correlacoes-v3/ibm_jobs.json) e [estado corrente da triagem](../results/campaigns/20261107-correlacoes-v3/hardware/collection.json).
6. [Análise física corrente](../results/campaigns/20261107-correlacoes-v3/hardware/analysis.json): receberá estimativas quando houver jobs concluídos.

No CSV de ruído, `factor=0` é o circuito curto da emenda, `factor=1` é o circuito escolhido pela tolerância ideal original de 0,001 e `factor=2` dobra os passos desse último. `raw` significa bruto e `mitigated`, leitura corrigida. `p2` é o parâmetro do canal despolarizante de dois qubits; ele não é, em geral, uma taxa de infidelidade de porta diretamente intercambiável com a publicada pelo dispositivo. `readout_error=0.03` é a probabilidade sintética de inversão de cada bit na leitura.

Um `run.json` com status `completed` pode indicar que o protocolo terminou de enviar os jobs. O estado remoto precisa ser lido separadamente: `QUEUED` aguarda, `RUNNING` executa e `DONE` concluiu. Um `plan.json` é um plano preservado e pode continuar escrito `prepared_not_submitted`, mesmo quando o registro de submissão posterior já contém os IDs. Para saber o que realmente aconteceu, confira os IDs e os registros de coleta.

Para atualizar os jobs existentes, sem novos envios:

```sh
.venv/bin/python scripts/run_correlation_hardware.py collect
.venv/bin/python scripts/prepare_short_circuit_experiments.py collect-hardware --record results/protocols/20261107T233046Z-6d048a1b4b85/run.json
```

Referências didáticas: [circuitos no Qiskit](https://quantum.cloud.ibm.com/docs/en/guides/construct-circuits), [twirling e mitigação na documentação IBM](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques). A definição física dos parâmetros e dos cumulantes segue o código e o artigo deste repositório.
