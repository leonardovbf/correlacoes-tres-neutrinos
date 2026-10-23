# Além do campo médio: aproximações de baixo custo capturam as correlações entre neutrinos em supernovas?

_Beyond the average field: do low cost approximations capture the correlations between neutrinos in supernovae?_

## Abstract

Collective neutrino oscillations in core-collapse supernovae motivate the development of computational methods capable of describing quantum many-body effects. Exact evolution has an exponential cost in the general representation, whereas the mean-field approximation neglects connected correlations between particles. The phase-space approximation offers a computationally cheaper alternative, but its accuracy for three-body correlations requires specific assessment. This project aims to evaluate whether this approximation accurately reproduces two- and three-body correlations in collective neutrino oscillations, using exact calculations as benchmarks, and to determine whether quantum simulations can measure discrepancies between the methods. A two-flavor model with all-to-all interactions and distinct neutrino energies will be studied. Exact evolution, mean-field evolution, and the phase-space approximation will be compared for systems of up to sixteen neutrinos, varying the ratio of interaction strength to mean vacuum oscillation frequency from 0.1 to 10. Trotterized circuits implemented in Qiskit will be assessed for four to eight neutrinos under ideal conditions and simulated noise, with execution on IBM hardware subject to availability. Absolute and normalized errors in flavor probabilities and connected two- and three-body cumulants will be quantified, controlling for sampling uncertainty, numerical integration, and Trotterization. The expected contribution is to establish the approximation's range of validity and the precision required for quantum circuits to distinguish its predictions from exact results.

**Keywords:** Neutrinos. Collective oscillations. Three-body correlations. Quantum computing. Phase-space approximation.

## Problema de pesquisa

No processo de simulações de supernovas, é necessário prever como os neutrinos trocam de sabor, tendo em vista o impacto das trocas no aquecimento da onda choque da estrela, na produção de metais pesados, e consequentemente o sinal registrado por detectores no planeta Terra. Próximo ao núcleo da estrela, os neutrinos interagem entre si e se emaranham. Logo, o custo de cálculo do sabor dos neutrinos cresce de forma exponencial com o número de partículas analisadas, requerindo o uso de aproximações para medição. A aproximação de campo médio, até pouco tempo utilizada, ja provou-se falha em tempos curtos. Abordagens além do campo médio, como a aproximação de espaço de fase (PSA) e fechamentos da hierarquia BBGKY, buscam incorporar efeitos de correlações a menor custo computacional. As validações da PSA incluem observáveis de sabor, entropias reduzidas e correlações coletivas de dois corpos. Em particular, [Lacroix et al. (2024)](https://arxiv.org/html/2409.20215v3#S3.SS1.SSS1) comparam o observável coletivo $C_{ZZ}$, construído a partir de covariâncias, com o resultado exato na equação 47 e na Figura 3. Essa comparação não equivale à validação individual de todos os pares nem estabelece a precisão dos cumulantes conectados de terceira ordem. O fechamento de segunda ordem da hierarquia BBGKY considerado por [Riccio e Balantekin (2026)](https://arxiv.org/html/2607.28619v2#S3.SS2) despreza os cumulantes conectados de três corpos para fechar as equações. Essa condição decorre do truncamento adotado; a hierarquia completa mantém o acoplamento a correlações de ordens superiores. Ao mesmo tempo, experimentos conduzidos com computadores quânticos indicam emaranhamento evidente entre muitos neutrinos em um sistema, com baixa capacidade de detecção de ruídos vindos da estrutura computacional. Portanto, permanece necessário avaliar em quais condições a PSA reproduz os cumulantes conectados de terceira ordem e se simulações quânticas sujeitas a ruído conseguem distinguir suas previsões dos resultados exatos.

## Pergunta de pesquisa

A aproximação de espaço de fase reproduz precisamente as correlações entre três ou mais neutrinos, e se não reproduz, um computador quântico tem as capacidades para medir esta falha?

## Objetivos

Os objetivos do corpo de pesquisa se apresentam a partir da linha da experimentação, teste e entendimento das capacidades dos métodos autais de aproximação de baixo custo, especificamente o método de aproximação de espaço de fase, em reproduzir o ambiente, levando em consideração a capacidade de um computador quântico com seu devido poder computacional atual de medir a existência desta falha.

### Geral

O objetivo geral da pesquisa se demonstra como avaliar se a aproximação do espaço de fase consegue reproduzir com precisão a correlação de dois e três corpos em oscilações coletivas de neutrinos, usando cálculos exatos como gabarito, e verificar se simulações em computador quântico conseguem medir essas correlações.

### Específicos

Frente a construção do objetivo geral de pesquisa, o processo é dividido em 5 objetivos específicos principais que buscam estruturar e guiar os métodos de pesquisa.

Primeiramente, posiciona-se implementar os três diferentes modelos clássicos de oscilações coletivas, a exata (viável em uma quantidade baixa de neutrinos), a de campo médio e a de fase de espaço.

Em seguida, quantificar o erro de cada solução em cada sabor de neutrino e nas correlações para dois e para três neutrinos emaranhados, variando a intensidade das interações, de uma interação fraca com razão μ/ω̄ (razão do ritmo de oscilação do neutrino causado pelos neutrinos próximos, μ, sob o ritmo de oscilção entre diferentes sabores do próprio neutrino, ω̄) de 0,1, até uma interação forte com razão 10.

Próximo, verificar como este erro varia de acordo com a quantidade de neutrinos no sistema (mantendo a análise de correlações em corpos de dois e três neutrinos), a partir do crescimento do sistema de dois e três neutrinos para ambientes com até dezesseis neutrinos.

De forma subsequente, construir e validar um circuito quântico trotterizado, um sistema em que o tempo ocorre em passos pequenos para para poder-se primeiro aplicar a rotação inicial que representa o ritmo próprio do neutrino e em seguida o a interação, para 4 a 8 neutrinos e medir as mesmas correlações, em simulador ideal (confirmação que circuito replica os resultados exatos) e com ruído simulado.

Por último, estimar o nível de ruído a partir do qual o computador quântico não distingue mais o resultado exato do resultado da aproximação.

## Hipóteses

Como a pergunta de pesquisa é estruturada em duas frentes, a da precisão dos métodos atuais e a das capacidades dos equipamentos quânticos existentes, são estruturadas duas principais hipóteses:

### H1

A aproximação de espaço de fase reproduz bem o sabor de cada neutrino e as correlações entre pares, mas falha nas correlações entre trios, e essa falha cresce com a intensidade da interação.

_Refutação: o erro relativo nos trios fica comparável ao erro nos pares em todas as intensidades testadas._

### H2

As correlações entre trios são pequenas, da ordem de 0,001 a 0,01, então só são mensuráveis em hardware com mitigação de erro e para poucos neutrinos.

_Refutação: o hardware distingue o resultado exato do resultado da aproximação nos trios sem mitigação._

## Resumo

As oscilações coletivas de neutrinos em supernovas de colapso de núcleo motivam o desenvolvimento de métodos computacionais capazes de descrever efeitos quânticos de muitos corpos. A evolução exata apresenta custo exponencial na representação geral, enquanto a aproximação de campo médio despreza correlações conectadas entre partículas. A aproximação de espaço de fase oferece uma alternativa de menor custo computacional, mas sua precisão para correlações de três corpos requer avaliação específica. Este projeto tem como objetivo avaliar se essa aproximação reproduz com precisão as correlações de dois e três corpos em oscilações coletivas de neutrinos, usando cálculos exatos como referência, e verificar se simulações quânticas conseguem medir as diferenças entre os métodos. Será estudado um modelo de dois sabores, com interações entre todos os pares e energias distintas para os neutrinos. Serão comparadas a evolução exata, a de campo médio e a aproximação de espaço de fase para sistemas de até dezesseis neutrinos, variando a razão entre intensidade de interação e frequência média de oscilação no vácuo de 0,1 a 10. Circuitos trotterizados implementados em Qiskit serão avaliados para quatro a oito neutrinos, em condições ideais e com ruído simulado, com execução em hardware IBM condicionada à disponibilidade. Serão quantificados erros absolutos e normalizados nas probabilidades de sabor e nos cumulantes conectados de dois e três corpos, controlando incertezas de amostragem, integração numérica e trotterização. Espera-se estabelecer o domínio de validade da aproximação e a precisão necessária para que circuitos quânticos distingam suas previsões dos resultados exatos.

**Palavras-chave:** Neutrinos. Oscilações coletivas. Correlações de três corpos. Computação quântica. Aproximação de espaço de fase.

## Introdução

### Parte 2: estado da arte e lacuna de pesquisa

A descrição das oscilações coletivas considera que a evolução do sabor de um neutrino pode depender do estado dos demais por meio do espalhamento coerente neutrino–neutrino. Nesse regime, a dinâmica constitui um problema quântico de muitos corpos, no qual podem surgir correlações e emaranhamento entre partículas. Na aproximação de dois sabores, cada modo de neutrino é representado por um sistema de dois níveis, equivalente a um qubit. Sem explorar simetrias ou compressões específicas, um estado puro de $N$ neutrinos possui $2^N$ amplitudes complexas, o que limita a evolução exata de sistemas grandes em computadores clássicos ([Duan; Fuller; Qian, 2010](https://doi.org/10.1146/annurev.nucl.012809.104524); [Cervia et al., 2019](https://doi.org/10.1103/PhysRevD.100.083001)).

Uma estratégia para reduzir esse custo é a aproximação de campo médio, que substitui os efeitos das outras partículas por um campo efetivo determinado por suas médias. Ao fatorizar os valores esperados de operadores de partículas distintas, essa descrição despreza suas correlações conectadas e, para estados inicialmente fatorizados, não acompanha a formação de emaranhamento entre neutrinos. [Cervia et al. (2019)](https://doi.org/10.1103/PhysRevD.100.083001) relacionaram diferenças entre a evolução exata e a de campo médio ao desenvolvimento de emaranhamento, com dependência das condições iniciais. Em um modelo de três sabores, [Mangin-Brinet, Bauge e Lacroix (2026)](https://doi.org/10.1103/yr2g-1g2g) também observaram desvios em tempos curtos nas configurações examinadas. A validade da aproximação deve, portanto, ser avaliada em função do modelo, das condições iniciais e do regime dinâmico.

A aproximação de espaço de fase, denominada *phase-space approximation* (PSA), procura incorporar efeitos além do campo médio mediante um conjunto de trajetórias independentes. As condições iniciais são amostradas para reproduzir momentos quânticos selecionados, e cada trajetória evolui segundo equações de campo médio; os observáveis são estimados por médias estatísticas sobre o conjunto. [Lacroix et al. (2022)](https://doi.org/10.1103/PhysRevD.106.123006) obtiveram boa concordância com valores médios e entropias reduzidas de um e dois neutrinos em um modelo de dois feixes, embora não reproduzissem oscilações de longo tempo das flutuações. A extensão para múltiplos feixes também incluiu comparações de correlações coletivas de dois corpos, ampliando a validação para além dos observáveis individuais ([Lacroix et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027)). Posteriormente, a extensão para três sabores foi comparada com soluções exatas de até oito neutrinos ([Mangin-Brinet; Bauge; Lacroix, 2026](https://doi.org/10.1103/yr2g-1g2g)).

Outra abordagem além do campo médio consiste em truncar a hierarquia de Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY), que relaciona a evolução de observáveis de uma partícula a correlações de ordens superiores. No preprint de [Riccio e Balantekin (2026)](https://arxiv.org/abs/2607.28619), o fechamento de segunda ordem mantém contribuições de pares e anula os cumulantes conectados de três corpos para fechar as equações. Essa condição não anula necessariamente o valor esperado de um produto de três operadores, pois permanecem contribuições construídas a partir de médias individuais e de pares. A PSA, por sua vez, incorpora momentos superiores sem impor esse mesmo fechamento; sua precisão para cumulantes de terceira ordem precisa ser examinada diretamente ([Lacroix et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

As simulações quânticas oferecem uma via complementar para investigar essas correlações. [Hall et al. (2021)](https://doi.org/10.1103/PhysRevD.104.063009) demonstraram a simulação de pequenos sistemas de neutrinos em dispositivos ruidosos, destacando a importância da mitigação de erros para extrair medidas de emaranhamento. [Illa e Savage (2023)](https://doi.org/10.1103/PhysRevLett.130.221003) investigaram sistemas de até doze neutrinos no processador de íons aprisionados Quantinuum H1-1, incluindo correlações de dois e três corpos e indicadores de emaranhamento multipartite. Em escala maior, [Kiss et al. (2026)](https://doi.org/10.1038/s42005-026-02697-2) estudaram a termalização com circuitos aleatórios em processadores IBM com mais de cem qubits. Nesse estudo, o desempenho foi avaliado por observáveis de termalização; a fidelidade de cumulantes específicos durante a evolução demanda validação própria.

Esses avanços demonstram uma lacuna mais específica: estabelecer em quais condições a PSA reproduz as correlações conectadas de três corpos em oscilações coletivas de neutrinos e se circuitos quânticos acessíveis conseguem distinguir suas previsões dos resultados exatos. Na literatura explorada, não foi identificada uma avaliação sistemática dessa comparação que controle simultaneamente tamanho do sistema, intensidade da interação e incertezas computacionais e de medição. A concordância em médias de sabor, correlações coletivas de pares ou entropias reduzidas não garante a precisão de cumulantes de terceira ordem. Por isso, a comparação exige observáveis definidos de forma consistente e a separação entre erro da aproximação, amostragem finita, discretização temporal e ruído do circuito.

### Parágrafo final da introdução

## Referências citadas na parte do membro 3

CERVIA, M. J.; PATWARDHAN, A. V.; BALANTEKIN, A. B.; COPPERSMITH, S. N.; JOHNSON, C. W. Entanglement and collective flavor oscillations in a dense neutrino gas. **Physical Review D**, v. 100, art. 083001, 2019. DOI: [10.1103/PhysRevD.100.083001](https://doi.org/10.1103/PhysRevD.100.083001).

DUAN, H.; FULLER, G. M.; QIAN, Y.-Z. Collective neutrino oscillations. **Annual Review of Nuclear and Particle Science**, v. 60, p. 569–594, 2010. DOI: [10.1146/annurev.nucl.012809.104524](https://doi.org/10.1146/annurev.nucl.012809.104524).

HALL, B.; ROGGERO, A.; BARONI, A.; CARLSON, J. Simulation of collective neutrino oscillations on a quantum computer. **Physical Review D**, v. 104, art. 063009, 2021. DOI: [10.1103/PhysRevD.104.063009](https://doi.org/10.1103/PhysRevD.104.063009).

ILLA, M.; SAVAGE, M. J. Multi-neutrino entanglement and correlations in dense neutrino systems. **Physical Review Letters**, v. 130, art. 221003, 2023. DOI: [10.1103/PhysRevLett.130.221003](https://doi.org/10.1103/PhysRevLett.130.221003).

KISS, O.; TAVERNELLI, I.; TACCHINO, F.; LACROIX, D.; ROGGERO, A. Neutrino thermalization via randomization on a quantum processor. **Communications Physics**, v. 9, art. 282, 2026. DOI: [10.1038/s42005-026-02697-2](https://doi.org/10.1038/s42005-026-02697-2).

LACROIX, D.; BALANTEKIN, A. B.; CERVIA, M. J.; PATWARDHAN, A. V.; SIWACH, P. Role of non-gaussian quantum fluctuations in neutrino entanglement. **Physical Review D**, v. 106, art. 123006, 2022. DOI: [10.1103/PhysRevD.106.123006](https://doi.org/10.1103/PhysRevD.106.123006).

LACROIX, D.; BAUGE, A.; YILMAZ, B.; MANGIN-BRINET, M.; ROGGERO, A.; BALANTEKIN, A. B. Phase-space methods for neutrino oscillations: extension to multibeams. **Physical Review D**, v. 110, art. 103027, 2024. DOI: [10.1103/PhysRevD.110.103027](https://doi.org/10.1103/PhysRevD.110.103027).

MANGIN-BRINET, M.; BAUGE, A.; LACROIX, D. Three-flavor neutrino oscillations using the phase space approach. **Physical Review D**, v. 113, art. 036026, 2026. DOI: [10.1103/yr2g-1g2g](https://doi.org/10.1103/yr2g-1g2g).

RICCIO, M.; BALANTEKIN, A. B. Improved approximations for collective neutrino oscillations. **arXiv**, 2026. Preprint, arXiv:2607.28619, versão 2. DOI: [10.48550/arXiv.2607.28619](https://doi.org/10.48550/arXiv.2607.28619). Disponível em: [arXiv](https://arxiv.org/abs/2607.28619). Acesso em: 23 out. 2026.
