# Além do campo médio: a aproximação de espaço de fase captura as correlações de três corpos entre neutrinos?

## Abstract

The phase-space approximation was evaluated for two- and three-body cumulants in a two-flavor neutrino model. Comparison with exact evolution indicated larger normalized triple errors in 14 of 15 main configurations, according to the recorded intervals. More measurements reduced ideal-circuit error; in the primary noisy case, readout mitigation did not recover the exact cumulant in simulation or on IBM hardware. Parameters, controls, and reproducibility materials are presented. Statistical review and noise-threshold evaluation remain necessary for confirmatory conclusions.

## Resumo

Avaliou-se a aproximação de espaço de fase para cumulantes de dois e três corpos em um modelo de neutrinos com dois sabores. A comparação com a evolução exata indicou maior erro normalizado dos trios em 14 de 15 configurações principais, segundo os intervalos registrados. Nos circuitos ideais, mais medições reduziram o erro; no caso ruidoso principal, a mitigação de leitura não recuperou o cumulante exato, no simulador e na IBM. Apresentam-se parâmetros, controles e materiais de reprodução. A revisão estatística e a avaliação de limiares de ruído permanecem necessárias às conclusões confirmatórias.

## Introdução

### Contexto astrofísico e motivação

Estrelas com massa inicial acima de aproximadamente oito massas solares podem sofrer colapso gravitacional do núcleo. No cenário típico, um núcleo rico em ferro perde sustentação, contrai-se e sofre um rebote, originando um choque. Esse choque pode estagnar por perdas com dissociação nuclear e emissão de neutrinos. A absorção de neutrinos e os movimentos da matéria podem reativá-lo durante a acreção, isto é, a queda de matéria sobre o remanescente (Figura 1) (JANKA, 2012; ABI et al., 2020).

![Três painéis mostram o núcleo estelar em contração, o aquecimento por neutrinos atrás do choque e os possíveis desfechos de explosão ou formação de buraco negro.](figuras/figura-1-colapso-estelar.png)

*Figura 1 - Colapso estelar, sem escala física. (a) Contração e rebote do núcleo. (b) Choque estagnado e aquecimento por neutrinos ao redor da protoestrela de nêutrons (PN). (c) Explosão ou formação de um buraco negro, inclusive após uma explosão. Fonte: elaboração própria com base em Janka (2012).*

Neutrinos são partículas elementares eletricamente neutras que interagem fracamente com a matéria. Uma supernova típica emite cerca de $10^{58}$ neutrinos, com energias características de $10\,\mathrm{MeV}$, em aproximadamente dez segundos, transportando mais de 99% da energia gravitacional liberada pelo núcleo colapsado (ABI et al., 2020). Seus estados de sabor são superposições dos estados de massa, cujas fases de propagação alteram as probabilidades de detecção, produzindo oscilações (DUAN; FULLER; QIAN, 2010).

A evolução de sabor pode alterar o aquecimento atrás do choque e a composição de nêutrons e prótons, relevante para a nucleossíntese. Seus efeitos dependem da configuração estelar, como mostram os estudos de Nagakura (2023) e Akaho et al. (2026); a relação entre matéria rica em nêutrons e formação de elementos pesados é discutida por Cowan et al. (2021). Os eventos da SN 1987A e as perspectivas de detecção em DUNE, Hyper-Kamiokande e JUNO reforçam a importância de prever os sabores emitidos (VISSANI et al., 2010; BAUM; CAPOZZI; HORIUCHI, 2022; SARMAH et al., 2026). Perto do núcleo, a interação coerente entre neutrinos acopla sua evolução, gerando oscilações coletivas e o problema de muitos corpos discutido a seguir (DUAN; FULLER; QIAN, 2010).

### Estado da arte e lacuna de pesquisa

A dinâmica coletiva descrita acima constitui um problema quântico de muitos corpos, no qual podem surgir correlações e emaranhamento entre neutrinos, associado à não separabilidade do estado quântico conjunto. Na representação geral de dois sabores, um estado puro de $N$ neutrinos possui $2^N$ amplitudes complexas. Esse crescimento limita a evolução exata de sistemas grandes em computadores clássicos quando não se exploram simetrias ou compressões específicas (DUAN; FULLER; QIAN, 2010; CERVIA et al., 2019).

Uma estratégia para reduzir esse custo é a aproximação de campo médio, que substitui os efeitos das outras partículas por um campo efetivo determinado por suas médias. Ao fatorizar os valores esperados de operadores de partículas distintas, essa descrição despreza suas correlações conectadas e, para estados inicialmente fatorizados, não acompanha a formação de emaranhamento entre neutrinos. [Cervia et al. (2019)](https://doi.org/10.1103/PhysRevD.100.083001) relacionaram diferenças entre a evolução exata e a de campo médio ao desenvolvimento de emaranhamento, com dependência das condições iniciais. Em um modelo de três sabores, [Mangin-Brinet, Bauge e Lacroix (2026)](https://doi.org/10.1103/yr2g-1g2g) também observaram desvios em tempos curtos nas configurações examinadas. A validade da aproximação deve, portanto, ser avaliada em função do modelo, das condições iniciais e do regime dinâmico.

A aproximação de espaço de fase, denominada *phase-space approximation* (PSA), procura incorporar efeitos além do campo médio mediante um conjunto de trajetórias independentes. As condições iniciais são amostradas para reproduzir momentos quânticos selecionados, e cada trajetória evolui segundo equações de campo médio; os observáveis são estimados por médias estatísticas sobre o conjunto. [Lacroix et al. (2022)](https://doi.org/10.1103/PhysRevD.106.123006) obtiveram boa concordância com valores médios e entropias dos estados reduzidos de um e dois neutrinos, calculadas a partir das respectivas matrizes densidade, em um modelo de dois feixes, embora não reproduzissem oscilações de longo tempo das flutuações. A extensão para múltiplos feixes também incluiu comparações de correlações coletivas de dois corpos por meio do observável $C_{ZZ}$, construído a partir de covariâncias. Essa validação coletiva não equivale à avaliação individual de todos os pares nem estabelece a precisão dos cumulantes de terceira ordem ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027)). Posteriormente, a extensão para três sabores foi comparada com soluções exatas de até oito neutrinos ([MANGIN-BRINET; BAUGE; LACROIX, 2026](https://doi.org/10.1103/yr2g-1g2g)).

Outra abordagem além do campo médio consiste em truncar a hierarquia de Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY), que relaciona a evolução de observáveis de uma partícula a correlações de ordens superiores. No preprint de [Riccio e Balantekin (2026)](https://arxiv.org/abs/2607.28619), o fechamento de segunda ordem mantém contribuições de pares e anula os cumulantes conectados de três corpos para fechar as equações. Essa condição não anula necessariamente o valor esperado de um produto de três operadores, pois permanecem contribuições construídas a partir de médias individuais e de pares. A PSA, por sua vez, incorpora momentos superiores sem impor esse mesmo fechamento; sua precisão para cumulantes de terceira ordem precisa ser examinada diretamente ([LACROIX et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

As simulações quânticas oferecem uma via complementar para investigar essas correlações. [Hall et al. (2021)](https://doi.org/10.1103/PhysRevD.104.063009) demonstraram a simulação de pequenos sistemas de neutrinos em dispositivos ruidosos, empregando mitigação de erros, isto é, técnicas para reduzir os efeitos do ruído nas estimativas dos observáveis, para extrair medidas de emaranhamento. [Illa e Savage (2023)](https://doi.org/10.1103/PhysRevLett.130.221003) investigaram sistemas de até doze neutrinos no processador de íons aprisionados Quantinuum H1-1, incluindo correlações de dois e três corpos e indicadores de emaranhamento multipartite. Em escala maior, [Kiss et al. (2026)](https://doi.org/10.1038/s42005-026-02697-2) estudaram a termalização com circuitos aleatórios em processadores IBM com mais de cem qubits. Nesse estudo, o desempenho foi avaliado por observáveis de termalização; a fidelidade de cumulantes específicos durante a evolução demanda validação própria.

Na literatura explorada, não foi identificada uma comparação sistemática dos cumulantes de três corpos da PSA com a solução exata que controle tamanho do sistema, intensidade da interação e incertezas computacionais e de medição. A concordância em médias de sabor, correlações coletivas de pares ou entropias reduzidas não garante a precisão dos cumulantes de terceira ordem. Essa lacuna exige observáveis consistentes e a separação entre erro da aproximação, amostragem finita, discretização temporal e ruído.

A precisão dos cumulantes de terceira ordem é relevante porque, em um Hamiltoniano com interações entre pares, a hierarquia de evolução acopla observáveis de uma partícula a correlações de dois corpos, cujas equações dependem de momentos de terceira ordem. Assim, desvios na descrição dos trios podem afetar observáveis de ordens inferiores ao longo da evolução ([LACROIX et al., 2024](https://doi.org/10.1103/PhysRevD.110.103027); [RICCIO; BALANTEKIN, 2026](https://arxiv.org/abs/2607.28619)). As limitações de longo tempo relatadas para a PSA motivam examinar essa relação, sem atribuir previamente todos os desvios de sabor a uma única componente dos cumulantes ([LACROIX et al., 2022](https://doi.org/10.1103/PhysRevD.106.123006)).

Para quatro a oito neutrinos, o cálculo exato é acessível em computadores clássicos. A etapa quântica busca determinar com que precisão os circuitos distinguem desvios da PSA. Em sistemas maiores, sem solução exata acessível, esses circuitos poderiam servir de referência para validar aproximações. Os sistemas pequenos permitem avaliar essa possibilidade separando discretização, amostragem e ruído, sem pressupor vantagem computacional ou extrapolar os resultados para sistemas maiores.

Diante disso, este trabalho busca responder em quais regimes de intensidade de interação, tamanho do sistema e tempo de evolução a PSA reproduz as correlações conectadas de dois e três corpos e, quando há desvios, sob quais condições de ruído e número de medições circuitos quânticos conseguem distingui-los dos resultados exatos.

Para isso, propõe-se avaliar os cumulantes conectados de dois e três corpos da PSA frente ao cálculo exato, com o campo médio como referência adicional, delimitando os regimes de validade da aproximação. Serão usados Python para sistemas de quatro até cerca de dezesseis neutrinos e Qiskit para circuitos de quatro a oito, em um modelo de dois sabores com estados iniciais de sabor puro fatorizados. A razão $\mu/\bar{\omega}$ variará de 0,1 a 10, em que $\mu$ é a escala de interação neutrino-neutrino e $\bar{\omega}$, a frequência média de oscilação no vácuo. O contexto de supernovas motiva o modelo; as conclusões ficarão restritas às configurações simplificadas examinadas.

O aumento da interação amplia os coeficientes dos termos que acoplam as ordens da hierarquia, motivando a expectativa de maior sensibilidade dos trios aos efeitos além das trajetórias de campo médio. Essa é uma conjectura dependente do estado inicial e da janela temporal, não uma consequência de a PSA anular cumulantes superiores. A hipótese **H1** é que a PSA reproduz com maior precisão as probabilidades individuais de sabor e os cumulantes de dois corpos do que os de três corpos. Nos casos em que a referência permite normalização, o erro normalizado nos trios tende a crescer com a intensidade da interação. A hipótese **H2** prevê que a mitigação amplia o limiar de ruído que permite distinguir a PSA da solução exata sob o mesmo orçamento total de medições. Seus critérios de refutação serão definidos no desenho da pesquisa.

A Seção 2 apresenta o modelo, os observáveis, as etapas de comparação e os critérios de avaliação das hipóteses. A Seção 3 descreve a organização prevista dos resultados. O presente texto apresenta o desenho da pesquisa; os resultados experimentais serão incorporados após a execução e a validação do protocolo.

## Metodologia

Comparam-se campo médio, PSA e circuitos com a evolução exata. O [protocolo](PROTOCOLO_EXPERIMENTOS.md) reúne configurações, sementes e controles.

Cada neutrino corresponde a um qubit, com $|\nu_e\rangle=|0\rangle$ e $|\nu_x\rangle=|1\rangle$. Com $\hbar=1$, $\tau=\bar{\omega}t$, $\lambda=\mu/\bar{\omega}$ e $\widetilde{\omega}_i=\omega_i/\bar{\omega}$,

$$
\frac{H}{\bar{\omega}}=\frac{1}{2}\sum_{i=0}^{N-1}\widetilde{\omega}_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\lambda}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j.
$$

em que $\mathbf{B}=(\sin2\theta,0,-\cos2\theta)$, $\boldsymbol{\sigma}_i$ reúne os operadores de Pauli e $g_{ij}$ define o acoplamento. Cada par aparece uma vez. O modelo exclui transporte, colisões e hidrodinâmica; a janela fixa em $\tau$ corresponde a $\mu t=\lambda\tau$.

A referência usa `expm_multiply` (SciPy), verificado por exponenciação densa em um sistema pequeno. Campo médio e PSA usam RK4. Na PSA, amostram-se componentes transversais independentes em $\pm1$, com a longitudinal fixada pelo sabor (LACROIX et al., 2024).

Os circuitos usam Trotter simétrico de segunda ordem. A comparação Qiskit–emulador verifica a implementação; a comparação com o exato isola a discretização da amostragem e do ruído.

Para $m_i(t)=\langle Z_i\rangle_t$, a probabilidade de sabor eletrônico é $P_{e,i}(t)=[1+m_i(t)]/2$. Os cumulantes de partículas distintas são

$$
\begin{aligned}
C^{(2)}_{ij}(t)&=\langle Z_i Z_j\rangle_t-m_i(t)m_j(t),\\
C^{(3)}_{ijk}(t)&=\langle Z_i Z_j Z_k\rangle_t-m_i(t)m_j(t)m_k(t)\\
&\quad-C^{(2)}_{ij}(t)m_k(t)-C^{(2)}_{ik}(t)m_j(t)-C^{(2)}_{jk}(t)m_i(t).
\end{aligned}
$$

A análise restringe-se a $Z$, $ZZ$ e $ZZZ$; cumulantes não nulos não certificam, isoladamente, emaranhamento.

Os controles cobrem reprodução publicada, ausência de interação, integração, amostragem e Trotter. Falhas exigem emendas documentadas, sem exclusão de resultados desfavoráveis.

## Experimentos e parâmetros

A grade reúne quinze configurações principais e dez na extensão (Tabela 1), com associação fixa entre frequência e sabor inicial.

*Tabela 1 - Parâmetros da grade clássica original.*

| Parâmetro | Definição |
| --- | --- |
| Tamanhos e interação | $N=4,6,8$; extensão: $12,16$. $\lambda=0,1;0,3;1;3;10$. |
| Frequências e mistura | $\widetilde{\omega}_i=0,7+0,6i/(N-1)$, $i=0,\ldots,N-1$; $\theta=0,2$ rad. |
| Acoplamentos | $g_{ij}=1$ para $i\ne j$; $g_{ii}=0$. |
| Estado inicial | Primeira metade dos índices em $\nu_e$; segunda em $\nu_x$. |
| Tempo e integração | $0\leq\tau\leq10$, 201 instantes; 12 subpassos RK4 por intervalo. |
| Observáveis | Todos os indivíduos, pares e trios distintos. |
| PSA e sementes | 20 blocos independentes de 4.096 trajetórias (81.920 no total); sementes 10.001–10.020. |

A reprodução de Lacroix et al. (2024) usa a Figura 2(c) daquele estudo, em configuração distinta da Tabela 1, com oito neutrinos e 10.000 trajetórias. As coordenadas foram extraídas da figura; parâmetros e conversões estão na [documentação da referência](data/benchmarks/lacroix2024/README.md).

A convergência em $N=4,8$ e $\lambda=0,1;1;10$ varia trajetórias, subpassos RK4 e passos de Trotter. A Tabela 3 limita os desvios absolutos máximos, o refinamento de 8 para 12 subpassos e o maior erro-padrão entre sementes, sobre tempos e trios.

Os circuitos ideais usam $N=4,6,8$ e vinte blocos de 1.024, 4.096 ou 16.384 medições por instante. A etapa ruidosa restringe-se a $N=4$, ao trio $(0,1,2)$ e a $\tau=1,2,4$, mantendo as cinco interações e os três orçamentos. A discretização original totaliza 112 passos de Trotter.

*Tabela 2 - Perfis de ruído definidos para o simulador Aer.*

| Perfil | Despolarização: um qubit | Despolarização: dois qubits | Erro de leitura |
| --- | ---: | ---: | ---: |
| Ideal | 0 | 0 | 0 |
| Leve | 0,0001 | 0,001 | 0,01 |
| Moderado | 0,001 | 0,01 | 0,03 |

O Aer usa matriz densidade, base `rz`, `sx`, `x`, `cx` e otimização de nível 1. Os perfis sintéticos da Tabela 2 aplicam despolarização em `sx`, `x`, `cx` e inversões de leitura simétricas independentes.

A mitigação inverte o produto tensorial das matrizes de resposta calibradas com $|0000\rangle$ e $|1111\rangle$, preservando quasiprobabilidades negativas. Por bloco, usa $3m/4$ medições no sinal e $m/8$ em cada calibração; o método bruto usa $m$ no sinal. Ambos recebem $M=20m$. A correção não elimina erros de portas.

O caso principal usa $N=4$, $\lambda=3$, $\tau=2$, ruído moderado e $m=16.384$, com execução adicional no `ibm_kingston`.

A emenda v3 respondeu à identificação de um controle amostral omitido e à sua reprovação em três de seis configurações. Acrescentou vinte blocos de 4.096 trajetórias por configuração, aprovados sob o mesmo limite. A reanálise preservou a reprovação original.

Após a falha de Trotter, a v4 adotou 29 pontos e 448 passos em $N=4$, $\lambda=10$, $\tau=4$; em $\lambda=10$, $\tau=2$, elevou a PSA de 12 para 24 subpassos RK4. O caso principal não mudou. As profundidades distintas limitam comparações entre interações.

## Métricas de avaliação

Para $T$ instantes e $n_q$ conjuntos de partículas, sejam $O^{\mathrm{ex}}_{q,\alpha}$ a referência e $\widehat O_{q,\alpha}$ a estimativa de $P_e$, $C^{(2)}$ ou $C^{(3)}$. Definem-se

$$
\begin{aligned}
E_q&=\sqrt{\frac{1}{Tn_q}\sum_{\ell=1}^{T}\sum_{\alpha=1}^{n_q}
\left[\widehat{O}_{q,\alpha}(\tau_\ell)-O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2},\\
S_q&=\sqrt{\frac{1}{Tn_q}\sum_{\ell=1}^{T}\sum_{\alpha=1}^{n_q}
\left[O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2}.
\end{aligned}
$$

Usa-se $R_q=E_q/S_q$ para $S_q\geq10^{-4}$ e apenas erro absoluto abaixo desse piso. Para H1, $D=R_3-R_2$ recebe 2.000 réplicas bootstrap de blocos independentes. Agregam-se momentos antes dos cumulantes, preservando a dependência temporal; os percentis 2,5 e 97,5 definem o intervalo de 95%.

Os circuitos usam 2.000 réplicas multinomiais das contagens agregadas, reestimando a calibração e reamostrando independentemente os blocos PSA, sem correção de viés. Para $C^{(3)}$, sejam $I_{\mathrm{PSA}}$ o intervalo de circuito menos PSA e $[L,U]$ o de circuito menos exato. Exige-se

$$
0\notin I_{\mathrm{PSA}}
\quad\text{e}\quad
[L-r,U+r]\subseteq[-\delta,\delta],
\qquad \delta=0,01,
$$

em que $r$ soma o desvio ideal–exato a $10^{-5}$. Calibrações com número de condição não finito ou superior a 10 tornam o caso não resolvido.

Para H2, $p_{\max}(M)$ é o maior ruído avaliado que satisfaz o critério sob orçamento $M$. Comparar os limiares com e sem mitigação exige fixar família de ruído, varredura e margem relevante; a grade atual não estima essa diferença.

*Tabela 3 - Tolerâncias e verificações selecionadas. Máximos nas configurações de cada controle; traços indicam valores não reproduzidos nesta síntese.*

| Controle | Limite | Observado |
| --- | ---: | ---: |
| Reprodução publicada: exato | $2\times10^{-2}$ | $1,41\times10^{-3}$ |
| Reprodução publicada: PSA | $6\times10^{-2}$ | $2,99\times10^{-2}$ |
| Exato independente | $10^{-10}$ | — |
| Qiskit versus emulador | $10^{-10}$ | $2,80\times10^{-12}$ |
| Refinamento RK4: $P_e$ | $10^{-6}$ | — |
| Refinamento RK4: cumulantes | $10^{-5}$ | — |
| Erro-padrão PSA suplementar: $C^{(3)}$ | $10^{-2}$ | $5,11\times10^{-3}$ |
| Trotter ideal: $C^{(3)}$ | $10^{-3}$ | — |

## Resultados experimentais

### Validação e precisão da PSA

As onze fases locais, incluindo $N=12,16$, passaram nos controles após as emendas (Tabela 3). Os desvios da reprodução publicada incluem a incerteza de extração da figura.

O intervalo de 95% de $D$ foi positivo em 14 de 15 configurações principais (Figura 2). Em $N=4$, $\lambda=0,1$, o sinal ficou indefinido: $D=-0,132$, intervalo $[-0,209;0,048]$. Em $N=4$, $\lambda=3$, obtiveram-se $R_2=0,419$, $R_3=0,948$ e $D=0,529$, intervalo $[0,524;0,535]$.

![Três painéis apresentam a diferença entre erros normalizados de trios e pares, com as estimativas pontuais e os intervalos percentis da grade principal.](figuras/figura-5-resultados-psa.png)

*Figura 2 - $D=R_3-R_2$ para $0\leq\tau\leq10$: estimativas com vinte blocos PSA e intervalos percentis de 95% com 2.000 réplicas. O círculo aberto marca a estimativa fora do próprio intervalo. Fonte: elaboração própria a partir do pacote de resultados.*

Os dez intervalos da extensão foram positivos. Contudo, cinco estimativas ficaram fora dos próprios intervalos: $N=8$, $\lambda=0,1$, e $N=12,16$, $\lambda=0,1$ e $0,3$. Elas e as inclinações agregadas de $N=8,12,16$ exigem revisão do viés bootstrap. Uma conclusão global de H1 requer critérios de agregação, relevância e multiplicidade.

O maior erro dos trios não cresce monotonicamente com a interação: em $N=8$, $D$ cai de $0,485$ para $0,363$ entre $\lambda=0,1$ e $1$, antes de aumentar.

### Orçamento de medições

Nos circuitos ideais, o RMSE de $C^{(3)}$ diminuiu com cada aumento de orçamento nas quinze configurações. De 1.024 para 16.384 medições por bloco, a redução de 3,75 a 4,19 vezes (Figura 3) aproxima-se do fator quatro esperado da dependência $1/\sqrt{m}$. Três orçamentos não estabelecem uma lei de escala nem avaliam erros de portas.

![Três painéis mostram o RMSE dos cumulantes de trios em função do número de medições por bloco, para os três tamanhos principais e cinco intensidades de interação.](figuras/figura-6-orcamento-medicoes.png)

*Figura 3 - RMSE dos trios em relação ao exato, agregado sobre tempos e trios. Cada ponto usa vinte blocos de $m$ medições por instante; linhas conectam os orçamentos, sem intervalos de confiança. Fonte: elaboração própria a partir do pacote de resultados.*

### Ruído, mitigação e hardware

No caso principal, o cumulante exato foi $-0,315784$; a PSA estimou $-0,155768$ nos blocos locais e $-0,151947$ nos associados à IBM, amostras distintas. Os circuitos ruidosos ficaram próximos de zero, com e sem mitigação (Tabela 4 e Figura 4).

*Tabela 4 - Caso principal: estimativas de $C^{(3)}$ e intervalos de 95% para circuito menos exato, ampliados pelo resíduo numérico. Cada método recebe $M=327.680$ medições; a calibração integra o orçamento mitigado.*

| Ambiente | Método | Estimativa | IC95 da diferença |
| --- | --- | ---: | --- |
| Aer | Bruto | $-0,000305$ | $[0,312040;0,318866]$ |
| Aer | Mitigado | $0,001301$ | $[0,312190;0,322029]$ |
| IBM | Bruto | $0,005847$ | $[0,317702;0,325733]$ |
| IBM | Mitigado | $0,006376$ | $[0,317486;0,327007]$ |

![Comparação do cumulante exato, das duas estimativas PSA e dos circuitos Aer e IBM, sem e com mitigação, no caso principal.](figuras/figura-7-comparacao-quantica.png)

*Figura 4 - Caso principal: faixa de $\pm0,01$ ao redor do exato; intervalos dos circuitos ampliados pelo resíduo e transladados para $C^{(3)}$. PSA sem intervalo individual; círculos e quadrados representam métodos brutos e mitigados. Fonte: elaboração própria a partir do pacote de resultados.*

Os quatro intervalos de circuito menos PSA excluem zero, mas nenhum de circuito menos exato cabe em $[-0,01;0,01]$. A mitigação não recuperou o cumulante nessa margem. A decisão pontual é inconclusiva e não testa o limiar de ruído de H2.

A IBM completou vinte blocos, quatro qubits, oitenta trabalhos e 655.360 medições, incluindo calibrações, em 72,87 minutos. O relatório mantém o status científico provisório, embora todos os trabalhos tenham terminado; os tempos detalhados estão no pacote de resultados.

As conclusões restringem-se ao modelo, estado inicial e componentes estudados. O [repositório](https://github.com/leonardovbf/correlacoes-tres-neutrinos) reúne códigos, protocolos, workloads, referência e resultados auditáveis. O arquivo integral de trajetórias e contagens em `results/`, necessário à reanálise completa, não integra o pacote.

## Referências

Abi, B. et al. (2020). Deep Underground Neutrino Experiment (DUNE), Far Detector Technical Design Report, Volume II: DUNE Physics. Technical Report FERMILAB-PUB-20-025-ND, DUNE Collaboration. <https://arxiv.org/abs/2002.03005>.

Akaho, R., Nagakura, H., Iwakami, W., Furusawa, S., Harada, A., Okawa, H., Matsufuru, H., Sumiyoshi, K., and Yamada, S. (2026). Bifurcated Impact of Neutrino Fast Flavor Conversion on Core-Collapse Supernovae Informed by Multiangle Neutrino Radiation Hydrodynamics. *Physical Review Letters*, 136(19):191002. <https://doi.org/10.1103/fksy-1jtw>.

Baum, S., Capozzi, F., and Horiuchi, S. (2022). Rocks, water, and noble liquids: Unfolding the flavor contents of supernova neutrinos. *Physical Review D*, 106(12):123008. <https://doi.org/10.1103/PhysRevD.106.123008>.

Cervia, M. J., Patwardhan, A. V., Balantekin, A. B., Coppersmith, S. N., and Johnson, C. W. (2019). Entanglement and collective flavor oscillations in a dense neutrino gas. *Physical Review D*, 100(8):083001. <https://doi.org/10.1103/PhysRevD.100.083001>.

Cowan, J. J., Sneden, C., Lawler, J. E., Aprahamian, A., Wiescher, M., Langanke, K., Martínez-Pinedo, G., and Thielemann, F.-K. (2021). Origin of the heaviest elements: The rapid neutron-capture process. *Reviews of Modern Physics*, 93(1):015002. <https://doi.org/10.1103/RevModPhys.93.015002>.

Duan, H., Fuller, G. M., and Qian, Y.-Z. (2010). Collective Neutrino Oscillations. *Annual Review of Nuclear and Particle Science*, 60(1):569--594. <https://doi.org/10.1146/annurev.nucl.012809.104524>.

Hall, B., Roggero, A., Baroni, A., and Carlson, J. (2021). Simulation of collective neutrino oscillations on a quantum computer. *Physical Review D*, 104(6):063009. <https://doi.org/10.1103/PhysRevD.104.063009>.

Illa, M. and Savage, M. J. (2023). Multi-Neutrino Entanglement and Correlations in Dense Neutrino Systems. *Physical Review Letters*, 130:221003. <https://doi.org/10.1103/PhysRevLett.130.221003>.

Janka, H.-T. (2012). Explosion Mechanisms of Core-Collapse Supernovae. *Annual Review of Nuclear and Particle Science*, 62:407--451. <https://doi.org/10.1146/annurev-nucl-102711-094901>.

Kiss, O., Tavernelli, I., Tacchino, F., Lacroix, D., and Roggero, A. (2026). Neutrino thermalization via randomization on a quantum processor. *Communications Physics*, 9(1):282. <https://doi.org/10.1038/s42005-026-02697-2>.

Lacroix, D., Balantekin, A. B., Cervia, M. J., Patwardhan, A. V., and Siwach, P. (2022). Role of non-Gaussian quantum fluctuations in neutrino entanglement. *Physical Review D*, 106(12):123006. <https://doi.org/10.1103/PhysRevD.106.123006>.

Lacroix, D., Bauge, A., Yilmaz, B., Mangin-Brinet, M., Roggero, A., and Balantekin, A. B. (2024). Phase-space methods for neutrino oscillations: Extension to multibeams. *Physical Review D*, 110:103027. <https://doi.org/10.1103/PhysRevD.110.103027>.

Mangin-Brinet, M., Bauge, A., and Lacroix, D. (2026). Three-flavor neutrino oscillations using the phase space approach. *Physical Review D*, 113:036026. <https://doi.org/10.1103/yr2g-1g2g>.

Nagakura, H. (2023). Roles of Fast Neutrino-Flavor Conversion on the Neutrino-Heating Mechanism of Core-Collapse Supernova. *Physical Review Letters*, 130(21):211401. <https://doi.org/10.1103/PhysRevLett.130.211401>.

Riccio, M. and Balantekin, A. B. (2026). Improved Approximations for Collective Neutrino Oscillations. Preprint, version 2. <https://doi.org/10.48550/arXiv.2607.28619>.

Sarmah, P., Chakraborty, S., Medhi, A., Bose, D., and Devi, M. M. (2026). Neutrino mass ordering from the next Galactic supernova at DUNE, HK, and JUNO. Preprint. <https://arxiv.org/abs/2606.06580>.

Vissani, F., Costantini, M. L., Fulgione, W., Ianni, A., and Pagliaroli, G. (2010). What is the issue with SN1987A neutrinos? Preprint. <https://arxiv.org/abs/1008.4726>.
