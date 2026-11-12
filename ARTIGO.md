# Investigando correlações de três corpos entre neutrinos além da aproximação de espaço de fase com hardware quântico

_Probing Three-Body Neutrino Correlations Beyond the Phase-Space Approximation with Quantum Hardware_

**Giovanna Fátima de Britto Vieira¹, Marco Ruas Sales Peixoto¹, Leonardo Villas Boas Fischel¹**

¹Instituto de Tecnologia e Liderança – Inteli, São Paulo – SP – Brasil

Orientadores: Jose Erinaldo da Fonseca e Bryan Kano Ferreira

## Resumo

O sabor dos neutrinos em supernovas pode influenciar a explosão e a produção de elementos pesados. Este trabalho comparou a aproximação de espaço de fase (PSA) com a evolução exata em um modelo de dois sabores, com 4 a 16 neutrinos. O erro normalizado dos trios superou o dos pares nas 15 configurações com enumeração completa da PSA; sua tendência com a interação dependeu da janela temporal. No caso principal, a PSA recuperou 48% do cumulante exato. A mitigação ampliou a tolerância ao erro de leitura nas simulações. Circuitos IBM recuperaram 61%, 44% e 21% dos cumulantes em três pontos com 4, 6 e 8 qubits, superando a PSA, mas fora da margem de 0,01.

**Palavras-chave:** Neutrinos. Oscilações coletivas. Correlações de três corpos. Computação quântica. Aproximação de espaço de fase.

## Abstract

Neutrino flavor in supernovae can influence the explosion and heavy-element production. This work compared the phase-space approximation (PSA) with exact evolution in a two-flavor model with 4 to 16 neutrinos. Normalized triple errors exceeded pair errors in all 15 configurations with complete PSA enumeration; their interaction trend depended on the time window. In the primary case, PSA recovered 48% of the exact cumulant. Mitigation increased readout-error tolerance in simulations. IBM circuits recovered 61%, 44%, and 21% of the cumulants at three points with 4, 6, and 8 qubits, outperforming PSA but remaining outside the 0.01 margin.

**Keywords:** Neutrinos. Collective oscillations. Three-body correlations. Quantum computing. Phase-space approximation.

## Introdução

### Contexto astrofísico e motivação

Estrelas com massa inicial acima de cerca de oito massas solares podem sofrer colapso gravitacional do núcleo, cujo rebote origina um choque que tende a estagnar e que a absorção de neutrinos e os movimentos da matéria podem reativar [Janka 2012, Abi et al. 2020]. Uma supernova típica emite cerca de $10^{58}$ neutrinos, partículas eletricamente neutras que interagem fracamente com a matéria, com energias características de $10\,\mathrm{MeV}$, que transportam mais de 99% da energia gravitacional liberada [Abi et al. 2020]. A evolução de sabor desses neutrinos altera o aquecimento atrás do choque e a razão entre nêutrons e prótons, relevante para a nucleossíntese, com efeitos que dependem da configuração estelar [Nagakura 2023, Akaho et al. 2026, Cowan et al. 2021]. A detecção da SN 1987A e as perspectivas de DUNE, Hyper-Kamiokande e JUNO reforçam a importância de prever os sabores emitidos [Vissani et al. 2010, Baum et al. 2022, Sarmah et al. 2026]. Perto do núcleo, a interação coerente entre neutrinos acopla suas evoluções e gera oscilações coletivas de sabor, um problema quântico de muitos corpos [Duan et al. 2010].

### Problema, lacuna e objetivo

O custo da evolução exata cresce exponencialmente com o número de neutrinos. A aproximação de campo médio reduz esse custo ao desprezar as correlações conectadas entre partículas [Cervia et al. 2019]. A aproximação de espaço de fase, denominada _phase-space approximation_ (PSA), incorpora efeitos além do campo médio por meio de um conjunto de trajetórias com condições iniciais aleatórias [Lacroix et al. 2022] e foi validada em neutrinos por meio de médias de sabor, correlações coletivas de pares e entropias reduzidas [Lacroix et al. 2024, Mangin-Brinet et al. 2026]. Cumulantes de três corpos de neutrinos já foram medidos em hardware, sem comparação com a PSA [Illa e Savage 2023]. Na literatura examinada, não se encontrou uma comparação, par a par e trio a trio, dos cumulantes conectados de três corpos da PSA com a evolução exata.

Os cumulantes de terceira ordem importam porque, em um Hamiltoniano com interações entre pares, a evolução dos observáveis de uma partícula depende das correlações de dois corpos, e a destas, de momentos de terceira ordem, de modo que desvios nos trios podem afetar observáveis de ordem inferior [Lacroix et al. 2024, Riccio e Balantekin 2026]. Com até dezesseis neutrinos, o cálculo exato é acessível em computadores clássicos. A etapa quântica avalia se circuitos distinguem os desvios da PSA, o que seria útil para validar aproximações em sistemas sem solução exata, sem pressupor vantagem computacional nem extrapolar os resultados para sistemas maiores.

Este trabalho busca responder em quais regimes de intensidade de interação, tamanho do sistema e tempo de evolução a PSA reproduz as correlações conectadas de dois e três corpos e, quando há desvios, sob quais condições de ruído e número de medições circuitos quânticos conseguem distingui-los dos resultados exatos. O modelo tem dois sabores e estados iniciais de sabor puro fatorizados, e o campo médio serve de referência adicional. As simulações clássicas cobrem de quatro a dezesseis neutrinos, e os circuitos, de quatro a oito. A razão $\lambda=\mu/\bar{\omega}$ variou de 0,1 a 10, em que $\mu$ é a escala efetiva da interação neutrino-neutrino e $\bar{\omega}$ é a frequência média de oscilação no vácuo. O contexto de supernovas motiva o modelo, e as conclusões restringem-se às configurações simplificadas examinadas.

A hipótese **H1** é que a PSA reproduz com maior precisão as probabilidades individuais de sabor e os cumulantes de dois corpos do que os de três corpos. Nos casos em que a referência permite normalização, o erro normalizado nos trios tende a crescer com a intensidade da interação. A hipótese **H2** é que a mitigação de leitura amplia o nível de ruído sob o qual um circuito ainda distingue a PSA da solução exata, com o mesmo orçamento total de medições. A Seção 6 define as métricas usadas para avaliá-las.

## Fundamentação teórica

### Oscilações de sabor e o Hamiltoniano coletivo

Em dois sabores, os estados $|\nu_e\rangle$ e $|\nu_x\rangle$, em que $\nu_x$ representa uma combinação efetiva de $\nu_\mu$ e $\nu_\tau$, relacionam-se aos estados de massa por um ângulo de mistura $\theta$, e cada neutrino pode ser descrito como um spin-1/2 em um campo efetivo [Duan et al. 2010]. Em ambientes densos, o espalhamento frontal coerente entre neutrinos acrescenta uma troca de sabor entre pares, na forma de um produto escalar entre os _spins_ de sabor [Duan et al. 2010, Balantekin e Pehlivan 2007]. Para $N$ neutrinos com momentos discretizados, com $\hbar=c=1$ e na base de sabor,

$$
H=\frac{1}{2}\sum_{i=0}^{N-1}\omega_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\mu}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j,
\qquad
\omega_i=\frac{\Delta m^2}{2E_i},\qquad
\mathbf{B}=(\sin2\theta,0,-\cos2\theta),
\tag{1}
$$

em que $\boldsymbol{\sigma}_i=(X_i,Y_i,Z_i)$ reúne as matrizes de Pauli do neutrino $i$, $\Delta m^2$ é a diferença entre os quadrados das massas, $E_i$ é a energia, $\mu$ é uma escala efetiva da interação, proporcional a $\sqrt{2}G_Fn_\nu$, com $G_F$ a constante de Fermi e $n_\nu$ a densidade de neutrinos, e $g_{ij}$ incorpora a dependência angular $1-\cos\vartheta_{ij}$ entre as direções de propagação. O fator $1/N$ mantém finita a energia de interação por neutrino. Com $g_{ij}$ uniforme, a Equação (1) corresponde à aproximação de ângulo único [Pehlivan et al. 2011, Cervia et al. 2019], e a grade clássica deste trabalho usa $g_{ij}=1$.

O estado de cada neutrino é resumido pelo vetor de polarização $\mathbf{P}_i=\langle\boldsymbol{\sigma}_i\rangle$, que no vácuo precessa em torno de $\mathbf{B}$ com frequência $\omega_i$. A probabilidade de sabor eletrônico é $P_{e,i}=(1+m_i)/2$, com $m_i=\langle Z_i\rangle$ [Duan et al. 2010, Cervia et al. 2019]. Com $|\nu_e\rangle=|0\rangle$ e $|\nu_x\rangle=|1\rangle$, cada neutrino corresponde a um qubit, e a medição de $Z_i$ distingue os dois sabores. O espaço de estados tem dimensão $2^N$, o que limita a evolução exata de sistemas grandes quando não se exploram simetrias [Cervia et al. 2019], e a Equação (1) descreve um sistema fechado simplificado, sem matéria, antineutrinos nem colisões.

### Correlações conectadas e emaranhamento

Um estado puro de $N$ neutrinos é separável quando se escreve como produto de estados individuais, e emaranhado no caso contrário. Partindo de um estado produto, o termo de interação da Equação (1) gera emaranhamento, enquanto o termo de vácuo, isoladamente, preserva a fatorização. As correlações entre resultados de medição na base de sabor são descritas por cumulantes conectados, que isolam a parcela de um momento conjunto não explicada por momentos de ordem inferior [Riccio e Balantekin 2026]. Para partículas distintas,

$$
\begin{aligned}
C^{(2)}_{ij}(t)&=\langle Z_i Z_j\rangle_t-m_i(t)m_j(t),\\
C^{(3)}_{ijk}(t)&=\langle Z_i Z_j Z_k\rangle_t-m_i(t)m_j(t)m_k(t)\\
&\quad-C^{(2)}_{ij}(t)m_k(t)-C^{(2)}_{ik}(t)m_j(t)-C^{(2)}_{jk}(t)m_i(t).
\end{aligned}
\tag{2}
$$

Anular $C^{(3)}_{ijk}$ não equivale, portanto, a anular $\langle Z_iZ_jZ_k\rangle$, e para um estado produto todos os cumulantes de partículas distintas são nulos. Como dependem apenas da distribuição dos resultados de medição na base de sabor, esses cumulantes não certificam, isoladamente, emaranhamento, e o interesse nos de terceira ordem está, sobretudo, em seu papel na dinâmica.

### Campo médio e hierarquia BBGKY

A aproximação de campo médio substitui, no termo de interação, o operador de cada parceiro por sua média, $\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j\approx\boldsymbol{\sigma}_i\cdot\mathbf{P}_j+\mathbf{P}_i\cdot\boldsymbol{\sigma}_j-\mathbf{P}_i\cdot\mathbf{P}_j$ [Balantekin e Pehlivan 2007, Cervia et al. 2019]. Cada vetor de polarização passa a precessar em um campo que reúne o termo de vácuo e a média dos demais,

$$
\frac{d\mathbf{P}_i}{dt}=\Big[\omega_i\,\mathbf{B}+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\,\mathbf{P}_j\Big]\times\mathbf{P}_i .
\tag{3}
$$

O problema reduz-se a $3N$ equações acopladas, e um estado produto permanece produto, sem emaranhamento nem correlações conectadas. Os desvios em relação à evolução exata surgem à medida que as correlações crescem [Lacroix et al. 2022].

Na evolução exata, as equações de Ehrenfest não se fecham. Para a componente $b$ do vetor de polarização,

$$
\frac{dP_i^{b}}{dt}=\Big(\Big[\omega_i\mathbf{B}+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\mathbf{P}_j\Big]\times\mathbf{P}_i\Big)^{b}
+\frac{\mu}{2N}\sum_{j\neq i}g_{ij}\,\epsilon_{bac}\,C^{ac}_{ji},
\qquad C^{ac}_{ji}=\langle\sigma_j^a\sigma_i^c\rangle-P_j^aP_i^c,
\tag{4}
$$

em que $\epsilon_{bac}$ é o símbolo de Levi-Civita e há soma sobre os índices repetidos $a$ e $c$. O campo médio corresponde a anular os cumulantes de dois corpos $C^{ac}_{ji}$, cujas equações dependem, por sua vez, de cumulantes de três corpos, e assim sucessivamente, em uma hierarquia do tipo Bogoliubov–Born–Green–Kirkwood–Yvon (BBGKY) [Volpe et al. 2013, Lacroix e Ayik 2014]. Um fechamento de ordem $m$ anula os cumulantes de ordem $m+1$. O campo médio corresponde a $m=1$, e o fechamento de segunda ordem de Riccio e Balantekin (2026) anula todas as componentes dos cumulantes de três corpos. Na Equação (4), cada par contribui com coeficiente $\mu/(2N)$, somado sobre os $N-1$ parceiros, de modo que o peso dos termos de correlação cresce com a interação. Essa estrutura motiva a hipótese H1, sem demonstrá-la, pois a expectativa depende do estado inicial e da janela temporal e não decorre de a PSA anular cumulantes superiores.

### Aproximação de espaço de fase

A PSA transforma a evolução quântica em um problema estatístico [Lacroix et al. 2022, Lacroix et al. 2024]. Sorteiam-se condições iniciais clássicas $\mathbf{s}_i^{(\ell)}(0)$ cujas médias e flutuações reproduzem as do estado quântico inicial. Cada trajetória $\ell$ evolui independentemente segundo a Equação (3), com $\mathbf{P}_i$ substituído por $\mathbf{s}_i^{(\ell)}$, e os observáveis são estimados por médias de produtos das componentes $s^{z,(\ell)}_i(t)$ sobre as $N_{\mathrm{traj}}$ trajetórias. A ideia provém do campo médio estocástico da física nuclear [Lacroix e Ayik 2014]. O custo por trajetória é polinomial em $N$, e o erro estatístico das médias decresce com $1/\sqrt{N_{\mathrm{traj}}}$.

Para estados produto com um neutrino por feixe, Lacroix et al. (2024) propuseram uma amostragem bivaluada, em que a componente de $\mathbf{s}_i$ ao longo do sabor inicial é fixada e as duas componentes transversais assumem, independentemente, os valores $\pm1$ com igual probabilidade,

$$
\mathbf{s}_i^{(\ell)}(0)=\mathbf{n}_i+x_i^{(\ell)}\mathbf{u}_i+y_i^{(\ell)}\mathbf{v}_i,\qquad x_i^{(\ell)},\,y_i^{(\ell)}\in\{-1,+1\},
\tag{5}
$$

em que $\mathbf{n}_i=\pm\hat{z}$ indica o sabor inicial e $\mathbf{u}_i$, $\mathbf{v}_i$ completam uma base ortonormal. Essa escolha reproduz $\overline{\mathbf{s}_i}=\mathbf{n}_i$ e $\overline{s_i^a s_i^b}=\delta_{ab}$, como os segundos momentos quânticos simetrizados de $\boldsymbol{\sigma}_i$, e inicia a distribuição completa sem cumulantes entre partículas distintas.

Embora cada trajetória seja representada por vetores clássicos, o conjunto desenvolve correlações entre partículas, porque trajetórias com condições iniciais distintas se separam ao longo da evolução. Segundo Lacroix et al. (2024), a PSA equivale a uma hierarquia BBGKY não truncada, que difere da exata apenas no nível de dois corpos. Diferentemente do fechamento de segunda ordem, que anula os cumulantes de três corpos, a PSA não impõe $C^{(3)}=0$. A concordância dos cumulantes da PSA com os exatos é o que este trabalho examina.

### Simulação quântica digital e trotterização

Na simulação quântica digital, o operador de evolução $U(t)=e^{-iHt}$ é aproximado por uma sequência de portas de um e dois qubits [Lloyd 1996, Nielsen e Chuang 2010]. A Equação (1) separa-se em termos de um corpo, que geram rotações de um qubit em torno de $\mathbf{B}$, e termos de pares, $H_{ij}=\tfrac{\mu g_{ij}}{4N}\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j$. Como $\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j=2\,\mathrm{SWAP}_{ij}-\mathbb{1}$, $e^{-iH_{ij}\delta}$ é uma única porta de dois qubits, equivalente a uma troca parcial de sabor, e exige no máximo três CNOTs [Vatan e Williams 2004]. Como todos os pares interagem, o número de portas de dois qubits por passo cresce com $N^2$, e processadores com conectividade limitada exigem ainda portas SWAP de roteamento [Hall et al. 2021, Amitrano et al. 2023].

Como os termos não comutam entre si, a evolução é dividida em $r$ passos de duração $\delta=t/r$. Para $H=\sum_{\gamma=1}^{\Gamma}H_\gamma$, a fórmula simétrica de Suzuki de segunda ordem é

$$
S_2(\delta)=e^{-iH_1\delta/2}\cdots e^{-iH_\Gamma\delta/2}\,e^{-iH_\Gamma\delta/2}\cdots e^{-iH_1\delta/2},
\qquad U(t)\approx S_2(t/r)^r,
\tag{6}
$$

com erro $O(t^3/r^2)$ no intervalo total [Childs et al. 2021]. Termos de pares que compartilham uma partícula têm comutadores que envolvem operadores de três corpos, o que torna o erro de discretização relevante para os trios. Aumentar $r$ reduz esse erro, mas aprofunda o circuito e amplia a exposição ao ruído.

### Medição, ruído e mitigação de leitura

A medição na base computacional produz cadeias de bits, e o valor esperado de $Z_S=\prod_{i\in S}Z_i$, para um conjunto de qubits $S$, é estimado pela paridade média dos bits de $S$ em $m$ repetições [Nielsen e Chuang 2010]. As mesmas contagens fornecem $m_i$, $\langle Z_iZ_j\rangle$ e $\langle Z_iZ_jZ_k\rangle$, com erro estatístico proporcional a $1/\sqrt{m}$, e as incertezas dos cumulantes dependem das covariâncias entre esses momentos [Hall et al. 2021, Cai et al. 2023].

Nos processadores atuais, sem correção de erros, o ruído limita a profundidade útil dos circuitos [Preskill 2018]. Um modelo usual de erro de porta é o canal despolarizante de probabilidade $p$, que multiplica por $1-p$ o valor esperado de qualquer operador de Pauli não trivial [Nielsen e Chuang 2010]. Na leitura, cada bit pode ser invertido com probabilidade $\varepsilon$, independente entre qubits, o que resulta em $\langle Z_S\rangle_{\mathrm{med}}=(1-2\varepsilon)^{|S|}\langle Z_S\rangle$, e o mesmo fator $(1-2\varepsilon)^3$ atenua $C^{(3)}$. Correlações de ordem maior sofrem, assim, atenuação mais forte.

Na mitigação de leitura, a relação entre as distribuições ideal e medida é descrita por uma matriz de resposta que, supondo erros independentes entre qubits, fatoriza-se em matrizes de um qubit, estimadas por circuitos de calibração e invertidas sobre as frequências medidas [Bravyi et al. 2021]. O resultado pode conter quasiprobabilidades negativas, que fornecem estimativas não enviesadas de momentos lineares quando a matriz de resposta é conhecida exatamente. A estimação dessa matriz e o cálculo dos cumulantes podem introduzir viés finito. A inversão amplia a variância, e a calibração consome parte do orçamento de medições [Bravyi et al. 2021, Cai et al. 2023]. A mitigação de leitura não corrige erros de porta, que exigem técnicas como a extrapolação a ruído zero [Cai et al. 2023].

## Revisão bibliográfica

### O problema de muitos corpos e os limites do campo médio

Com soluções exatas de até nove neutrinos, Cervia et al. (2019) relacionaram as diferenças entre campo médio e evolução exata ao desenvolvimento de emaranhamento, com forte dependência das condições iniciais. Rrapaj (2020) comparou soluções exatas multiangulares ao campo médio, incluindo correlações conectadas de pares, e indicou que o desacordo esperado é máximo quando a polarização de sabor líquida é nula, como no estado com metade dos neutrinos em cada sabor adotado nesta pesquisa. Há, porém, limites para extrapolar esses resultados. Em um modelo de dois feixes, o campo médio recupera observáveis de um corpo no limite de muitos neutrinos [Martin et al. 2022], e sistemas fechados com poucos neutrinos não bastam para validá-lo ou invalidá-lo em fontes astrofísicas abertas [Shalgar e Tamborra 2023]. Esses trabalhos justificam o foco em correlações, que o campo médio despreza por construção, e a restrição das conclusões a sistemas fechados pequenos.

### Métodos além do campo médio

A PSA oferece uma alternativa de custo polinomial à evolução exata. Lacroix et al. (2022) aplicaram-na a um modelo de dois feixes, em que o método reproduziu médias, flutuações e entropias de um e dois neutrinos, mas não as oscilações de longo tempo das flutuações. A extensão para múltiplos feixes usou um arranjo semelhante ao deste trabalho, com quatro, oito e doze neutrinos, metade em cada sabor e interação entre todos os pares. Nela, as médias individuais de sabor foram sobreamortecidas em tempos longos, enquanto a correlação coletiva $C_{ZZ}$, que soma as covariâncias de todos os pares, e a entropia média de um neutrino foram bem reproduzidas [Lacroix et al. 2024]. Não se avaliaram covariâncias par a par, cumulantes de três corpos nem a dependência com a intensidade da interação. A versão de três sabores reproduziu populações de sabor e entropias de soluções exatas de até oito neutrinos [Mangin-Brinet et al. 2026].

Fora de neutrinos, de Correc et al. (2026) aplicaram a PSA a registradores de qubits em modelos de Ising e observaram perda de precisão em correlações de dois qubits e em entropias de subsistemas maiores, sobretudo em acoplamento forte, o que antecipa qualitativamente a hipótese H1, sem envolver cumulantes conectados de três corpos nem o Hamiltoniano de neutrinos. Na linha da hierarquia BBGKY, o fechamento de segunda ordem de Riccio e Balantekin (2026) trata cerca de cem neutrinos com custo polinomial, mas sua comparação com a evolução exata restringiu-se a quatro neutrinos em três sabores.

### Simulação quântica de oscilações coletivas

Hall et al. (2021) simularam quatro neutrinos em um processador IBM, com mitigação de leitura e extrapolação a ruído zero, e Amitrano et al. (2023) mostraram que a conectividade total de íons aprisionados reduz a profundidade dos circuitos de Trotter de segunda ordem, com execuções de até oito neutrinos. Illa e Savage (2023) mediram correlações conectadas de dois e três corpos em sistemas de até doze neutrinos, com a mesma definição de cumulantes da Equação (2) e o mesmo estado inicial com metade em cada sabor. Com 240 medições no processador de íons aprisionados e 1.200 no emulador, a maioria dos cumulantes de três corpos ficou compatível com zero, o que indica que o orçamento de medições limita a resolução desses observáveis. Kiss et al. (2026) usaram processadores IBM com até 112 qubits para estudar a termalização e compararam os resultados com a PSA, mas apenas em observáveis de um qubit.

### Síntese e posicionamento

_Tabela 1 - Trabalhos relacionados e observáveis comparados. CM: campo médio; "coletivo": grandeza agregada, com definição própria em cada estudo; "anulado": cumulante igualado a zero pelo fechamento. Todos tratam dois sabores, exceto Mangin-Brinet et al. (três), Riccio e Balantekin (dois e três) e de Correc et al. (qubits em modelos de Ising). Fonte: elaboração própria._

| Trabalho                    | Métodos                  | $N$ máximo |  $P_e$   | $C^{(2)}$ | $C^{(3)}$ | Plataforma        |
| --------------------------- | ------------------------ | ---------: | :------: | :-------: | :-------: | ----------------- |
| Rrapaj (2020)               | Exato, CM                |         20 |   Sim    |   Pares   |     —     | Clássica          |
| Lacroix et al. (2022)       | Exato, CM, PSA           |        100 |   Sim    | Coletivo  |     —     | Clássica          |
| Lacroix et al. (2024)       | Exato, PSA               |         12 |   Sim    | Coletivo  |     —     | Clássica          |
| Mangin-Brinet et al. (2026) | Exato, CM, PSA           |          8 |   Sim    |     —     |     —     | Clássica          |
| de Correc et al. (2026)     | Exato, CM, PSA           |         10 |   Sim    |   Média   |     —     | Clássica          |
| Riccio e Balantekin (2026)  | BBGKY, CM, exato         |  4 (exato) |   Sim    |    Sim    |  Anulado  | Clássica          |
| Illa e Savage (2023)        | Exato, circuito          |         12 |   Sim    |    Sim    |    Sim    | Íons aprisionados |
| Kiss et al. (2026)          | Circuito, PSA            |        112 | Um qubit |     —     |     —     | IBM               |
| Este trabalho               | Exato, CM, PSA, circuito |         16 |   Sim    |   Pares   |   Trios   | Aer, IBM          |

A Tabela 1 mostra que os cumulantes de três corpos aparecem apenas em medições em hardware sem comparação com aproximações [Illa e Savage 2023] ou anulados por construção em um fechamento da hierarquia [Riccio e Balantekin 2026], e na literatura localizada não foi identificado trabalho que compare os cumulantes conectados de três corpos da PSA com a evolução exata. Este trabalho faz essa comparação por par e por trio, controlando o tamanho do sistema, a razão $\lambda$ e as incertezas de amostragem, discretização e medição, e avalia se circuitos quânticos com ruído e mitigação de leitura distinguem os desvios da PSA.

## Metodologia

O estudo compara quatro descrições da mesma dinâmica. A evolução exata serve de referência. O campo médio e a PSA são as aproximações avaliadas, e os circuitos trotterizados representam a alternativa quântica. Todas usam a forma adimensional da Equação (1), com $\tau=\bar{\omega}t$, $\lambda=\mu/\bar{\omega}$ e $\widetilde{\omega}_i=\omega_i/\bar{\omega}$,

$$
\frac{H}{\bar{\omega}}=\frac{1}{2}\sum_{i=0}^{N-1}\widetilde{\omega}_i\,\mathbf{B}\cdot\boldsymbol{\sigma}_i
+\frac{\lambda}{4N}\sum_{i<j}g_{ij}\,\boldsymbol{\sigma}_i\cdot\boldsymbol{\sigma}_j .
\tag{7}
$$

**Evolução exata.** O estado de $2^N$ amplitudes é propagado pela ação da exponencial da matriz esparsa do Hamiltoniano sobre o vetor de estado (`expm_multiply`, SciPy). Para verificar a construção dessa matriz, um Hamiltoniano denso montado de forma independente, por produtos de Kronecker, foi comparado a ela em um sistema de quatro neutrinos com acoplamentos e estados genéricos.

**Campo médio e PSA.** As Equações (3) e (5) são integradas por Runge–Kutta de quarta ordem (RK4) com subpassos fixos entre instantes consecutivos. A PSA é organizada em blocos de 4.096 trajetórias, cada um com semente própria. Os momentos $m_i$, $\langle Z_iZ_j\rangle$ e $\langle Z_iZ_jZ_k\rangle$ são somados entre os blocos antes do cálculo dos cumulantes, porque cumulantes calculados em cada bloco e depois promediados teriam viés de ordem $1/N_{\mathrm{traj}}$.

**Circuitos.** Os circuitos aplicam a fórmula de Suzuki de segunda ordem da Equação (6), com uma porta de dois qubits por par e por meio passo. A implementação em Qiskit foi comparada a um emulador independente de vetor de estado. As medições ideais são amostradas da distribuição exata do circuito. As execuções ruidosas usam o simulador Qiskit Aer com matriz densidade e o processador `ibm_kingston`. A mitigação de leitura segue Bravyi et al. (2021), com matrizes calibradas pelos estados $|0000\rangle$ e $|1111\rangle$, e preserva quasiprobabilidades negativas.

**Observáveis.** Avaliam-se as probabilidades $P_{e,i}$ e os cumulantes $C^{(2)}_{ij}$ e $C^{(3)}_{ijk}$ da Equação (2) para todos os indivíduos, pares e trios distintos. Tempos e conjuntos de partículas da mesma evolução não são réplicas independentes. As unidades de reamostragem são os blocos de PSA ou os trabalhos em hardware, conforme a análise.

**Controles.** Antes da comparação, cada etapa passou por verificações com limites fixados previamente (Tabela 5). Os controles incluem a reprodução de um resultado publicado da PSA, a ausência de cumulantes sem interação, a coincidência entre exato e campo médio sem interação, a convergência do RK4, o erro-padrão da PSA entre sementes e o erro de Trotter dos circuitos ideais. Dois controles falharam na primeira execução. No primeiro, o erro-padrão de $C^{(3)}$ entre cinco blocos de PSA superou $10^{-2}$ em três de seis configurações testadas, e o número de blocos foi elevado para vinte em todas as configurações, o que reduziu o maior erro-padrão para $5{,}11\times10^{-3}$. No segundo, o circuito ideal com 112 passos errou $C^{(3)}$ em $4{,}0\times10^{-3}$ em $\lambda=10$, $\tau=4$, acima do limite de $10^{-3}$, e essa configuração passou a usar 448 passos. Na mesma interação, a referência PSA em $\tau=2$ passou de 12 para 24 subpassos RK4. Nenhum resultado foi descartado, e os controles repetidos passaram após essas mudanças. Esses limites se referem às configurações verificadas; os resíduos dos pontos adicionais em hardware são informados separadamente.

## Experimentos e parâmetros

### Grade clássica

A Tabela 2 resume a grade usada para H1. A associação entre frequência e sabor inicial é fixa, com as frequências mais baixas no sabor eletrônico.

_Tabela 2 - Parâmetros da grade clássica._

| Parâmetro             | Valores                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------- |
| Tamanho               | $N=4,6,8$ (principal) e $N=12,16$ (extensão)                                                |
| Interação             | $\lambda=0{,}1;\ 0{,}3;\ 1;\ 3;\ 10$                                                        |
| Frequências e mistura | $\widetilde{\omega}_i=0{,}7+0{,}6\,i/(N-1)$; $\theta=0{,}2$ rad                             |
| Acoplamentos          | $g_{ij}=1$ para $i\neq j$                                                                   |
| Estado inicial        | Primeira metade dos neutrinos em $\nu_e$ e a segunda em $\nu_x$                             |
| Tempo                 | $0\leq\tau\leq10$, 201 instantes, 12 subpassos RK4 por intervalo                            |
| PSA                   | 20 blocos de 4.096 trajetórias (81.920 no total), sementes 10.001 a 10.020                  |

A reprodução de Lacroix et al. (2024) usa a Figura 2(c) daquele estudo, com oito neutrinos e 10.000 trajetórias, em configuração distinta da Tabela 2. As coordenadas foram extraídas da figura publicada, o que acrescenta uma incerteza de leitura aos desvios.

### Circuitos e ruído

Os circuitos ideais usam $N=4,6,8$, as cinco interações e vinte blocos de $m=1.024$, $4.096$ ou $16.384$ medições por instante. As execuções ruidosas no Aer restringem-se a $N=4$, ao trio $(0,1,2)$ e a $\tau=1,2,4$, com sete intervalos de tempo e 16 passos de Trotter por intervalo. O caso principal é $N=4$, $\lambda=3$, $\tau=2$, em que o cumulante exato é grande e a PSA se afasta dele.

A Tabela 3 apresenta a profundidade dos circuitos usados no simulador e o menor número de passos que mantém o erro de Trotter de $C^{(3)}$ abaixo de $10^{-3}$. Os 112 passos das execuções no Aer resultam em 4.032 CNOTs no simulador, sem restrição de conectividade, e em 6.048 após a compilação para uma cadeia linear de qubits, próxima da conectividade do hardware. No caso principal, 12 passos bastam e reduzem o circuito a 648 CNOTs. A primeira execução em hardware já usou uma discretização mais curta, com 2 passos por intervalo, 14 no total, e erro de Trotter de $7{,}2\times10^{-4}$. Compilado no processador, esse circuito tem 672 portas CZ e profundidade 2.918, com mapeamento lógico para os qubits físicos $(109,110,118,108)$.

_Tabela 3 - Circuitos do trio $(0,1,2)$ com $N=4$, compilados para portas `rz`, `sx`, `x` e `cx` em cadeia linear (Qiskit, otimização de nível 1). As três primeiras colunas numéricas referem-se à discretização usada no Aer e as duas últimas, ao menor número de passos com erro de Trotter em $C^{(3)}$ abaixo de $10^{-3}$._

| $\lambda$ | $\tau$ | Passos | Profundidade | CNOTs  | Passos mín. | CNOTs (mín.) |
| --------: | -----: | -----: | -----------: | -----: | ----------: | -----------: |
|   0,1–0,3 |  1–4   |    112 | 11.989–15.909 |  6.048 |         1–2 |       54–108 |
|         1 |      1 |    112 |       11.989 |  6.048 |           1 |           54 |
|         1 |      2 |    112 |       11.989 |  6.048 |           3 |          162 |
|         1 |      4 |    112 |       11.989 |  6.048 |           6 |          324 |
|         3 |      1 |    112 |       11.989 |  6.048 |           5 |          270 |
|     **3** |  **2** |**112** |   **11.989** |**6.048**|      **12** |      **648** |
|         3 |      4 |    112 |       11.989 |  6.048 |          22 |        1.188 |
|        10 |      1 |    112 |       11.989 |  6.048 |          20 |        1.080 |
|        10 |      2 |    112 |       11.989 |  6.048 |          37 |        1.998 |
|        10 |      4 |    448 |       47.941 | 24.192 |         224 |       12.096 |

A Tabela 4 lista os modelos de ruído. Os perfis leve e moderado reproduzem as execuções originais com 112 passos. A varredura usa o circuito de 12 passos do caso principal e varia separadamente a despolarização das portas de dois qubits, $p$, e o erro de leitura, $\varepsilon$, para testar H2.

_Tabela 4 - Modelos de ruído no Qiskit Aer. A despolarização de um qubit vale $p/10$ e atua em `sx` e `x`; a de dois qubits atua em `cx`._

| Modelo     | Passos | Despolarização $p$                                  | Erro de leitura $\varepsilon$                  |
| ---------- | -----: | --------------------------------------------------- | ---------------------------------------------- |
| Leve       |    112 | $10^{-3}$                                           | 0,01                                           |
| Moderado   |    112 | $10^{-2}$                                           | 0,03                                           |
| Varredura  |     12 | $0;\ 10^{-5};\ 3\times10^{-5};\ 10^{-4};\ 3\times10^{-4};\ 10^{-3}$ | $0;\ 0{,}005;\ 0{,}01;\ 0{,}02;\ 0{,}03;\ 0{,}05$ |

O orçamento por método é $M=20m$, com $m=16.384$. O método bruto usa todas as medições no circuito do sinal. O mitigado usa $3m/4$ medições no sinal e $m/8$ em cada calibração, de modo que a calibração consome parte do mesmo orçamento. Na varredura, o Aer calcula a distribuição de probabilidades com ruído de portas, o erro de leitura é aplicado como produto tensorial de matrizes de inversão de bit, e as contagens são sorteadas dessa distribuição. A primeira execução no `ibm_kingston` usou o caso principal com 14 passos, vinte blocos e o mesmo orçamento. Em seguida, o experimento em hardware foi refeito com um circuito mais curto. O instante $\tau=1{,}5$ foi escolhido depois da primeira execução, porque nele o cumulante exato do trio $(0,1,2)$ ainda vale $-0{,}159$, a PSA recupera apenas 34% dele, e o menor número de passos com erro de Trotter abaixo de $10^{-3}$ é 2, com erro de $8{,}2\times10^{-4}$. Compilado no processador, esse circuito tem 78 portas CZ e profundidade 294, com mapeamento $(142,143,144,136)$, cerca de nove vezes menos portas de dois qubits que o da primeira execução. Como a escolha do instante foi posterior aos primeiros resultados, uma triagem exploratória no processador precedeu a confirmação, feita com vinte trabalhos de 16.384 medições e sementes novas, com _twirling_ de portas e sem mitigação de leitura. Nesse caso, a PSA de referência é calculada com as 256 condições iniciais da amostragem bivaluada, o que elimina seu erro de Monte Carlo.

Dois pontos com seis e oito qubits foram executados no mesmo processador, em configuração diferente da grade. Neles, os neutrinos formam dois feixes, com acoplamento apenas entre feixes, de $g_{ij}=5/3$ em $N=6$ e $7/4$ em $N=8$, de modo que a média sobre todos os pares vale 1. Os sabores iniciais alternam-se, $\lambda=10$, e os circuitos têm dois passos de Trotter, com $\tau=0{,}55$ e o trio $(0,1,2)$ em $N=6$ e $\tau=0{,}65$ e o trio $(1,3,5)$ em $N=8$. Compilados, somam 204 e 429 portas CZ, com profundidades 540 e 927 e mapeamentos $(136,123,122,124,143,144)$ e $(123,136,124,122,143,142,144,141)$, respectivamente. O erro de Trotter de $C^{(3)}$ vale $1{,}3\times10^{-3}$ e $1{,}3\times10^{-2}$. Os pontos foram escolhidos por cálculos clássicos, antes de qualquer execução nesses tamanhos, em uma busca de 36 combinações de tamanho, interação, estado inicial e geometria que favoreceu sinais exatos e desvios da PSA grandes em circuitos curtos. Cinco trabalhos piloto de 4.096 medições por tamanho precederam uma confirmação com os mesmos circuitos, feita em vinte trabalhos com os dois circuitos, 4.096 medições por circuito, ordem alternada e cinco janelas de calibração. A confirmação compara o erro absoluto do hardware com o da PSA, calculada com todas as $4^N$ condições iniciais, e com o da previsão $C^{(3)}=0$, com quatro intervalos simultâneos de 98,75%, pela correção de Bonferroni.

_Tabela 5 - Controles numéricos. Valores máximos observados sobre todas as configurações de cada controle._

| Controle                                  | Limite              | Máximo observado          |
| :---------------------------------------- | ------------------: | ------------------------: |
| Reprodução publicada: exato               | $2\times10^{-2}$    | $1{,}41\times10^{-3}$     |
| Reprodução publicada: PSA                 | $6\times10^{-2}$    | $2{,}99\times10^{-2}$     |
| Exato: Hamiltoniano denso independente    | $10^{-10}$          | $2{,}26\times10^{-16}$    |
| Sem interação: $C^{(3)}$ exato            | $10^{-10}$          | $1{,}33\times10^{-15}$    |
| Qiskit versus emulador                    | $10^{-10}$          | $2{,}80\times10^{-12}$    |
| Refinamento RK4: $P_e$                    | $10^{-6}$           | $5{,}16\times10^{-8}$     |
| Refinamento RK4: cumulantes               | $10^{-5}$           | $1{,}26\times10^{-7}$     |
| Erro-padrão da PSA: $C^{(3)}$             | $10^{-2}$           | $5{,}11\times10^{-3}$     |
| Trotter ideal: $C^{(3)}$                  | $10^{-3}$           | $8{,}91\times10^{-5}$     |

## Métricas de avaliação

### Erro normalizado e hipótese H1

Para $T$ instantes e $n_q$ conjuntos de partículas de ordem $q$, sejam $O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)$ a referência exata e $\widehat O_{q,\alpha}(\tau_\ell)$ a estimativa da PSA. O erro e a escala do sinal são

$$
E_q^2=\max\!\left\{0,\ \frac{1}{Tn_q}\sum_{\ell,\alpha}\left[\widehat{O}_{q,\alpha}(\tau_\ell)-O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2-\overline{\sigma^2_q}\right\},\qquad
S_q^2=\frac{1}{Tn_q}\sum_{\ell,\alpha}\left[O^{\mathrm{ex}}_{q,\alpha}(\tau_\ell)\right]^2,
\tag{8}
$$

em que $\overline{\sigma^2_q}$ é a variância média do estimador da PSA, estimada pela dispersão entre os vinte blocos dividida por vinte. Sem esse termo, o erro quadrático incluiria o ruído de Monte Carlo da própria PSA, que é comparável ao sinal quando a interação é fraca e inflaria $E_q$ justamente onde os cumulantes são pequenos. O erro normalizado é $R_q=E_q/S_q$, com $q=1,2,3$, para $S_q\geq10^{-4}$; abaixo desse piso, usa-se o erro absoluto. Maior erro normalizado não implica necessariamente maior erro absoluto. Para as probabilidades de sabor, usa-se $m_i=2P_{e,i}-1$, de modo que $S_1$ mede o afastamento de $P_e$ em relação a $1/2$. A primeira parte de H1 é avaliada por $D=R_3-R_2$ e por $D_1=R_3-R_1$, com valores positivos indicando que a PSA erra mais nos trios.

Os intervalos de 95% vêm de 2.000 réplicas bootstrap dos vinte blocos. Como a estatística corrigida estima o erro sistemático da PSA, e no mundo bootstrap a média dos blocos não tem ruído próprio, usa-se o intervalo básico $[\widehat D-q_{97{,}5},\ \widehat D-q_{2{,}5}]$, em que $q_{2{,}5}$ e $q_{97{,}5}$ são percentis da diferença entre cada réplica corrigida e o valor sem correção calculado na média dos blocos, que é a referência do mundo bootstrap. O mesmo procedimento vale para $D_1$ e para as inclinações. Quando o ruído da PSA supera 1,5 vez o erro sistemático estimado, a configuração é sinalizada como dominada por ruído.

A segunda parte de H1, o crescimento do erro dos trios com a interação, é medida pela inclinação $b_N$ da regressão linear de $R_3$ em $\log_{10}\lambda$, para cada $N$. O intervalo de $b_N$ usa as mesmas réplicas bootstrap, com sementes pareadas entre as interações, e essa parte de H1 recebe apoio local quando o intervalo nominal de 95% de $b_N$ fica acima de zero. Uma inclinação positiva não exige crescimento monotônico. Os intervalos são pontuais, sem ajuste simultâneo entre configurações, e sua contagem não confirma H1 globalmente.

### Critério para os circuitos e hipótese H2

Para um circuito ruidoso, sejam $I_{\mathrm{PSA}}$ o intervalo de 95% de circuito menos PSA e $[L,U]$ o de circuito menos exato, ambos obtidos de 2.000 réplicas multinomiais das contagens agregadas, com a calibração reestimada a cada réplica e os blocos da PSA reamostrados. O circuito distingue a PSA do exato quando

$$
0\notin I_{\mathrm{PSA}}
\quad\text{e}\quad
[L-r,U+r]\subseteq[-0{,}01;\ 0{,}01],
\tag{9}
$$

em que $r$ soma o erro de Trotter do circuito ideal a uma tolerância numérica de $10^{-5}$. Calibrações com número de condição superior a 10 tornam o caso não resolvido. Como critério complementar, que não exige recuperar o valor exato, compara-se o erro absoluto do circuito com o da PSA por $\Delta=|\widehat C^{(3)}_{\mathrm{circ}}-C^{(3)}_{\mathrm{ex}}|-|C^{(3)}_{\mathrm{PSA}}-C^{(3)}_{\mathrm{ex}}|$, com intervalo obtido pela reamostragem dos trabalhos. O valor $\Delta<0$ indica que o circuito ficou mais perto do exato do que a aproximação. Na varredura inicial, o maior nível aprovado descreve os pontos avaliados, sem garantir um limiar monotônico. Na análise adicional com 78 CZ, o limiar é delimitado pela primeira falha, preservando eventuais sucessos posteriores como flutuações. H2 recebe apoio quando a região de recuperação do método mitigado supera a do bruto.

A análise adicional com 78 CZ usa 32 variantes de twirling e 100 campanhas sintéticas por condição. Seu desfecho primário é o intervalo circuito menos exato contido em $\pm0{,}01$, sem a ampliação adicional por $r$ da Equação (9), pois o viés de Trotter já permanece no erro. Na confirmação com seis e oito qubits, 10.000 réplicas reamostram conjuntamente os vinte trabalhos, preservando os dois circuitos de cada trabalho, sem nova amostragem multinomial interna.

## Resultados experimentais

### A PSA recupera metade do cumulante de trio no caso principal

No caso principal ($N=4$, $\lambda=3$, $\tau=2$), o cumulante exato do trio $(0,1,2)$ é $C^{(3)}=-0{,}316$. A PSA, com três conjuntos de 81.920 trajetórias, forneceu $-0{,}156$, $-0{,}152$ e $-0{,}147$, e sua média é $-0{,}151\pm0{,}002$. A aproximação recupera, portanto, 48% do cumulante exato, um desvio de 0,165, mais de oitenta vezes o erro-padrão. Na janela $0\leq\tau\leq10$ dessa configuração, o erro normalizado dos pares é $R_2=0{,}419$, contra $R_3=0{,}948$ dos trios. O desvio não decorre da amostragem da PSA nem da discretização, porque o erro-padrão é cerca de oitenta vezes menor que o desvio e os controles de integração também ficam abaixo dele (Tabela 5).

### Precisão da PSA em pares e trios

A Tabela 6 apresenta $D$ para as 25 configurações, com o ruído amostral da PSA descontado.

_Tabela 6 - Diferença $D=R_3-R_2$ entre os erros normalizados de trios e pares da PSA, com intervalo de 95%. Valores positivos indicam erro maior nos trios. O asterisco marca as configurações em que o ruído amostral da PSA supera 1,5 vez o erro sistemático estimado._

| $N$ | $\lambda=0{,}1$ | $\lambda=0{,}3$ | $\lambda=1$ | $\lambda=3$ | $\lambda=10$ |
| ---: | :---: | :---: | :---: | :---: | :---: |
| 4 | −0,180 [−0,326; −0,048] | 0,267 [0,237; 0,293] | 0,430 [0,417; 0,443] | 0,529 [0,524; 0,535] | 0,602 [0,599; 0,605] |
| 6 | 0,109 [−0,052; 0,257] | 0,306 [0,270; 0,346] | 0,359 [0,347; 0,370] | 0,625 [0,617; 0,632] | 0,752 [0,747; 0,756] |
| 8 | 0,264 [0,062; 0,430] | 0,358 [0,294; 0,405] | 0,362 [0,351; 0,373] | 0,505 [0,495; 0,513] | 0,936 [0,933; 0,939] |
| 12 | 0,347 [−0,007; 0,664]$^{*}$ | 0,445 [0,376; 0,501] | 0,311 [0,297; 0,323] | 0,371 [0,361; 0,379] | 0,720 [0,710; 0,729] |
| 16 | 0,695 [0,041; 1,282]$^{*}$ | 0,583 [0,476; 0,669] | 0,239 [0,228; 0,250] | 0,174 [0,163; 0,184] | 0,517 [0,508; 0,526] |

O intervalo nominal de 95% de $D$ ficou acima de zero em 22 das 25 configurações. As exceções ocorreram todas com a interação mais fraca, $\lambda=0{,}1$. Em $N=4$, o intervalo ficou abaixo de zero, com $D=-0{,}180$ $[-0{,}326;\ -0{,}048]$, de modo que nessa configuração a PSA errou mais nos pares do que nos trios. Em $N=6$ e $N=12$, o sinal ficou indefinido. Nessa interação, os cumulantes exatos são pequenos, com escala de $10^{-3}$ nos trios, e em $N=12$ e $N=16$ o ruído amostral da PSA superou o erro sistemático, o que torna esses dois valores pouco informativos com 81.920 trajetórias.

A correção do ruído amostral alterou de forma relevante apenas as configurações com $\lambda\leq0{,}3$. Sem ela, o erro quadrático incluía a variância de Monte Carlo da PSA, e cinco estimativas de $D$ ficavam fora dos próprios intervalos bootstrap, porque cada réplica, ao repetir blocos, acrescentava ruído e deslocava a distribuição para cima. Em $N=16$, $\lambda=0{,}1$, por exemplo, o valor sem correção era $2{,}062$, fora do intervalo $[2{,}425;\ 3{,}280]$, e o valor corrigido é $0{,}695$. Para $\lambda\geq1$, o ruído amostral é pequeno diante do erro sistemático, e os valores corrigidos diferem dos originais em no máximo 0,002.

Os trios também foram reproduzidos com menos precisão do que as probabilidades de sabor. O intervalo de $D_1=R_3-R_1$ ficou acima de zero nas 25 configurações. Com $\lambda\leq0{,}3$, o erro normalizado das probabilidades não passou de 0,011, enquanto o dos trios ficou entre 0,50 e 1,15. Com $\lambda=10$, porém, $R_1$ chegou a valores entre 0,53 e 1,01, porque a PSA amortece as oscilações das probabilidades individuais em acoplamento forte, como relataram Lacroix et al. (2024), e a vantagem das probabilidades sobre os trios caiu para 0,09 a 0,24.

O erro normalizado dos trios cresceu com a interação nos sistemas menores. A inclinação de $R_3$ por década de $\lambda$ foi $b_{4}=0{,}264$ $[0{,}215;\ 0{,}319]$, $b_{6}=0{,}162$ $[0{,}101;\ 0{,}229]$ e $b_{8}=0{,}150$ $[0{,}061;\ 0{,}260]$. Em $N=12$, a inclinação foi $b_{12}=0{,}042$ $[-0{,}144;\ 0{,}264]$, e em $N=16$, $b_{16}=-0{,}260$ $[-0{,}587;\ 0{,}101]$, ambas sem tendência definida. Nesses dois tamanhos, $R_3$ caiu de 0,70 a 1,15 com $\lambda\leq0{,}3$ para 0,24 a 0,44 com $\lambda$ entre 1 e 3 e voltou a subir em $\lambda=10$.

Como controle, a grade com $N=4,6,8$ foi recalculada com a PSA avaliada em todas as $4^N$ condições iniciais, sem erro de Monte Carlo, em uma janela mais curta, $0\leq\tau\leq3$, com 61 instantes. Nessa grade, $D$ foi positivo nas 15 configurações, o que sustenta a comparação entre trios e pares nessa janela sem depender da correção do ruído amostral. As inclinações de $R_3$, porém, foram $b_4=0{,}091$, $b_6=0{,}006$ e $b_8=-0{,}115$, e em nenhum tamanho $R_3$ cresceu de forma monotônica com $\lambda$. Em $N=4$, $\lambda=10$, a PSA errou mais do que a previsão $C^{(3)}=0$. O crescimento observado na janela completa depende, portanto, da inclusão dos tempos longos. A primeira parte de H1 recebe apoio local nas comparações descritas. A tendência crescente da segunda parte aparece para $N\leq8$ na janela $0\leq\tau\leq10$, mas não se mantém como regra nos tempos iniciais.

### Orçamento de medições

Nos circuitos ideais, o RMSE de $C^{(3)}$ em relação ao exato diminuiu a cada aumento de orçamento nas quinze configurações (Figura 1). De 1.024 para 16.384 medições por bloco, a redução foi de 3,75 a 4,19 vezes, próxima do fator quatro esperado da dependência $m^{-1/2}$. O erro dos circuitos ideais é, portanto, dominado pela estatística das medições. Com o maior orçamento, o RMSE ficou entre $3{,}4\times10^{-4}$ e $1{,}8\times10^{-3}$, bem abaixo do desvio da PSA no caso principal.

![RMSE de C3 dos circuitos ideais em função das medições por bloco, para N = 4, 6 e 8 e cinco intensidades de interação.](figuras/figura-orcamento-medicoes.svg)

_Figura 1 - RMSE de $C^{(3)}$ dos circuitos ideais em relação ao exato, sobre todos os instantes e trios, com vinte blocos de $m$ medições. As barras indicam a faixa de 95% em 500 repetições independentes do experimento._

### Ruído, mitigação e hardware

A Figura 2 mostra a estimativa de $C^{(3)}$ no caso principal sob a varredura de ruído. Sem ruído de porta, o método bruto distinguiu a PSA do exato apenas com leitura perfeita, porque a atenuação $(1-2\varepsilon)^3$ já desloca a estimativa para fora da margem de 0,01 com $\varepsilon=0{,}005$. A mitigação de leitura manteve a estimativa dentro da margem até $\varepsilon=0{,}03$, e em $\varepsilon=0{,}05$ o resultado oscilou entre os níveis de ruído de porta, sinal de que o aumento da variância da inversão aproxima o intervalo do limite da margem. Para o ruído de leitura, portanto, a mitigação ampliou o limiar, como prevê H2.

O ruído de porta produziu outro quadro. Sem erro de leitura, o maior nível de despolarização que satisfez o critério foi $p=10^{-5}$ para o método bruto e $p=3\times10^{-5}$ para o mitigado, e com $p=10^{-4}$ os dois métodos já ficaram fora da margem. A diferença em $3\times10^{-5}$ está no limite da resolução da varredura, porque nesse nível o método mitigado passou em apenas três dos seis erros de leitura. Com $\varepsilon=0{,}03$, o método bruto não atingiu a margem em nenhum nível, e o mitigado, até $p=10^{-5}$. A mitigação de leitura não trata o ruído de porta, e o apoio a H2 restringe-se ao erro de leitura. Com $p=10^{-3}$ no modelo despolarizante adotado, e $\varepsilon=0{,}03$, o circuito mitigado estimou $C^{(3)}=-0{,}156$. Esse valor é próximo da previsão da PSA, mas resulta da atenuação do sinal pelo ruído, o que mostra que um circuito ruidoso pode parecer concordar com a aproximação sem resolver a diferença.

![Estimativas de C3 no caso principal sob erro de leitura e despolarização de dois qubits, com e sem mitigação.](figuras/figura-varredura-ruido.svg)

_Figura 2 - Estimativas de $C^{(3)}_{012}$ no caso principal ($N=4$, $\lambda=3$, $\tau=2$) com o circuito de 12 passos e $M=327.680$ medições por método. (a) Sem ruído de porta, em função do erro de leitura. (b) Com erro de leitura de 0,03, em função da despolarização de dois qubits. As barras são intervalos de 95% ampliados pelo erro de Trotter, a linha contínua é o valor exato com a margem de $\pm0{,}01$ pontilhada, e a tracejada é a PSA._

A profundidade dos circuitos explica os resultados da Tabela 7, em que as quatro estimativas ficaram entre $-0{,}0003$ e $0{,}0064$, com ou sem mitigação. No Aer, os 112 passos somam 4.032 CNOTs, e uma auditoria das contagens mostrou que a matriz densidade antes da leitura ficou a menos de $8\times10^{-11}$ do estado maximamente misto, de modo que o ruído de portas apagou o sinal. No hardware, o circuito de 14 passos tem 672 portas CZ, mais do que as 648 CNOTs do circuito de 12 passos da Figura 2, cuja varredura já falha em $p=10^{-4}$ para resolver o cumulante em $\tau=2$. O parâmetro despolarizante sintético não é diretamente a infidelidade física de CNOT ou CZ. A execução no `ibm_kingston` completou vinte blocos e oitenta trabalhos, com 655.360 medições incluindo calibrações, em 72,87 minutos. Por isso, o experimento em hardware foi refeito com o circuito curto de $\tau=1{,}5$.

_Tabela 7 - Estimativas de $C^{(3)}$ no caso principal ($\tau=2$) e intervalo de 95% da diferença circuito menos exato, ampliado pelo erro de Trotter. Cada método recebe $M=327.680$ medições, e a calibração integra o orçamento mitigado. As portas de dois qubits são CNOTs no Aer e CZ no processador. O valor exato é $-0{,}316$, e o da PSA, $-0{,}151$._

| Ambiente | Passos | Portas de dois qubits | Método   | Estimativa  | IC95 da diferença        |
| -------- | -----: | --------------------: | -------- | ----------: | ------------------------ |
| Aer      |    112 |                 4.032 | Bruto    | $-0{,}0003$ | $[0{,}312;\ 0{,}319]$    |
| Aer      |    112 |                 4.032 | Mitigado |  $0{,}0013$ | $[0{,}312;\ 0{,}322]$    |
| IBM      |     14 |                   672 | Bruto    |  $0{,}0058$ | $[0{,}318;\ 0{,}326]$    |
| IBM      |     14 |                   672 | Mitigado |  $0{,}0064$ | $[0{,}317;\ 0{,}327]$    |

Com o circuito curto, o processador preservou um sinal mensurável. A estimativa da IBM foi $C^{(3)}=-0{,}097$, contra $-0{,}159$ do exato e $-0{,}054$ da PSA, de modo que o circuito recuperou 61% do cumulante e a aproximação, 34%. O erro absoluto do circuito foi 0,062, e o da PSA, 0,104, com $\Delta=-0{,}043$ $[-0{,}046;\ -0{,}039]$. O intervalo da diferença circuito menos PSA também excluiu zero. Uma simulação do mesmo circuito no Aer, com o modelo de ruído calibrado do processador e o mesmo número de medições, previu $C^{(3)}=-0{,}081$, próximo do valor medido. Já o intervalo da diferença circuito menos exato, $[0{,}058;\ 0{,}065]$, ficou fora da margem de $\pm0{,}01$, e o critério da Equação (9) não foi satisfeito. O hardware distinguiu, portanto, a previsão da PSA e ficou mais perto do exato do que ela, mas a atenuação total de cerca de 40% ainda impede recuperar o valor exato nessa execução. As simulações apontam a relevância do ruído de portas, sem atribuir toda a perda exclusivamente às CZ. Uma varredura de ruído no Aer sobre o próprio circuito executado, com 100 campanhas sintéticas de medição por condição, situou o limiar de despolarização de dois qubits entre $4{,}8\times10^{-4}$ e $5{,}6\times10^{-4}$ para os dois métodos, numericamente acima dos níveis aprovados no circuito de 648 CNOTs. A diferença não isola o efeito da profundidade, pois os pontos físicos, as portas e os critérios diferem. Nessa varredura, sem ruído de porta e com erro de leitura de 0,03, o método mitigado satisfez o critério em 97 de 100 campanhas e o bruto em nenhuma, o que reforça o benefício da mitigação de leitura nesse modelo, com o critério adicional descrito na seção de métricas.

Os pontos com seis e oito qubits também preservaram sinais mensuráveis (Tabela 8). Na confirmação, o hardware estimou $C^{(3)}=0{,}184$ em $N=6$, contra $0{,}415$ do exato e $0{,}137$ da PSA, e $C^{(3)}=-0{,}028$ em $N=8$, contra $-0{,}131$ do exato e $0{,}050$ da PSA. Em $N=8$, a PSA previu o sinal errado do cumulante, e o hardware recuperou o sinal correto. As quatro comparações de erro absoluto, contra a PSA e contra a previsão $C^{(3)}=0$ em cada tamanho, favoreceram o hardware com intervalos simultâneos de 98,75%, e os pilotos de cinco trabalhos já indicavam o mesmo resultado. Ainda assim, o hardware recuperou apenas 44% do cumulante exato em $N=6$ e 21% em $N=8$, e nenhum ponto ficou dentro da margem de $\pm0{,}01$. Em $N=8$, o próprio erro de Trotter, de $1{,}3\times10^{-2}$, já excede essa margem. As médias por janela de calibração variaram de 0,167 a 0,195 em $N=6$ e de $-0{,}045$ a $-0{,}012$ em $N=8$, uma deriva que o intervalo por reamostragem dos trabalhos inclui, mas não modela. Uma simulação no Aer com o modelo de ruído calibrado do processador previu $0{,}172$ e $-0{,}012$ para os pilotos, na mesma direção dos valores medidos. Como os pontos diferem em geometria, estado inicial, interação e tempo, as diferenças entre tamanhos não isolam o efeito de $N$.

_Tabela 8 - Execuções no `ibm_kingston` com circuitos de dois passos de Trotter. $\Delta$ é a diferença entre os erros absolutos do hardware e da PSA, e valores negativos indicam o hardware mais perto do exato. Os intervalos são de 95% nos pilotos e no caso $N=4$, e simultâneos de 98,75% na confirmação com seis e oito qubits. A PSA usa todas as condições iniciais._

| Execução         | $N$ | CZ  | Trabalhos × medições | Hardware    | Exato       | PSA         | $\Delta$                         |
| ---------------- | --: | --: | -------------------: | ----------: | ----------: | ----------: | -------------------------------- |
| Confirmação      |   4 |  78 |          20 × 16.384 | $-0{,}097$  | $-0{,}159$  | $-0{,}054$  | $-0{,}043$ $[-0{,}046;\ -0{,}039]$ |
| Piloto           |   6 | 204 |           5 × 4.096 |  $0{,}195$  |  $0{,}415$  |  $0{,}137$  | $-0{,}058$ $[-0{,}074;\ -0{,}043]$ |
| Piloto           |   8 | 429 |           5 × 4.096 | $-0{,}022$  | $-0{,}131$  |  $0{,}050$  | $-0{,}073$ $[-0{,}081;\ -0{,}065]$ |
| Confirmação      |   6 | 204 |          20 × 4.096 |  $0{,}184$  |  $0{,}415$  |  $0{,}137$  | $-0{,}047$ $[-0{,}056;\ -0{,}037]$ |
| Confirmação      |   8 | 429 |          20 × 4.096 | $-0{,}028$  | $-0{,}131$  |  $0{,}050$  | $-0{,}078$ $[-0{,}088;\ -0{,}068]$ |

## Discussão

### Comparação com trabalhos relacionados

A Tabela 9 compara os métodos, as grandezas e as condições de teste deste trabalho com os dois estudos mais próximos, Lacroix et al. (2024) para a PSA e Illa e Savage (2023) para a medição de cumulantes em hardware.

_Tabela 9 - Condições de teste deste trabalho e dos estudos mais próximos. Fonte: elaboração própria, com base nos trabalhos citados._

| Aspecto           | Lacroix et al. (2024)          | Illa e Savage (2023)                     | Este trabalho                                       |
| ----------------- | ------------------------------ | ---------------------------------------- | --------------------------------------------------- |
| Métodos           | Exato, PSA                     | Exato, circuito                          | Exato, campo médio, PSA, circuito                   |
| $N$               | 4, 8 e 12                      | Até 12                                   | 4 a 16 (clássico); 4 a 8 (hardware)                 |
| Estado inicial    | Metade em cada sabor           | Metade em cada sabor                     | Metade em cada sabor                                |
| Correlações       | $C_{ZZ}$ coletivo              | $C^{(2)}$ e $C^{(3)}$                    | $C^{(2)}$ por par e $C^{(3)}$ por trio              |
| Aproximação       | PSA comparada ao exato         | Nenhuma                                  | PSA comparada ao exato e aos circuitos              |
| Medições          | Não se aplica                  | 240 (processador) e 1.200 (emulador)     | 81.920 a 327.680 por circuito                       |
| Plataforma        | Clássica                       | Íons aprisionados                        | Clássica, Aer e `ibm_kingston`                      |

No arranjo de Lacroix et al. (2024), a PSA reproduziu bem a correlação coletiva $C_{ZZ}$, enquanto os resultados deste trabalho indicam erros altos em pares e trios. As duas observações são compatíveis. A grandeza publicada $C_{ZZ}$ inclui termos locais $i=j$; aqui, a soma $K_{ZZ}=\sum_{i<j}C^{(2)}_{ij}$ considera apenas pares distintos. Calculada sobre os mesmos dados da Tabela 6, essa soma teve erro normalizado entre 0,06 e 0,37 e ficou abaixo do erro par a par $R_2$ em 21 das 25 configurações. No caso principal, esse erro foi 0,17, contra $R_2=0{,}42$ e $R_3=0{,}95$. Os desvios dos pares individuais compensam-se em parte na soma, de modo que uma grandeza coletiva pode ser bem reproduzida mesmo quando as correlações de cada par e de cada trio não são. O sobreamortecimento das médias de sabor relatado por esses autores também aparece aqui, como o aumento do erro de $P_e$ com a interação, que chega a $R_1$ entre 0,53 e 1,01 em $\lambda=10$. A principal diferença está na grandeza comparada. A validação anterior não examinou cumulantes de três corpos, em que a PSA mais se afasta da evolução exata, nem a dependência com $\lambda$.

Illa e Savage (2023) usaram a mesma definição de cumulante conectado e o mesmo estado inicial, mas a maioria dos cumulantes de três corpos medidos ficou compatível com zero. Os resultados deste trabalho ilustram a relevância do orçamento de medições, sem identificar a causa única das incertezas daquele estudo. No circuito curto, o intervalo de 95% da diferença entre a IBM e o exato teve meia largura de 0,0035 com 327.680 medições, o que corresponde a um erro-padrão de cerca de 0,0018. Pela dependência $M^{-1/2}$ observada na Figura 1, o mesmo circuito, mantendo hipoteticamente sua distribuição e usando 240 medições, teria erro-padrão próximo de 0,07, comparável ao próprio cumulante exato, de $-0{,}159$. Com o orçamento ampliado, o hardware resolveu um cumulante não nulo e ainda o distinguiu da previsão da PSA. Com 81.920 medições, os circuitos de seis e oito qubits também resolveram cumulantes não nulos, inclusive o sinal negativo em $N=8$, que a PSA erra. Também se acrescenta a comparação com uma aproximação, ausente naquele estudo. A atenuação observada, de cerca de 40% em $N=4$ e de 56% e 79% em $N=6$ e $N=8$, mostra, porém, que aumentar o orçamento não basta e que, além da estatística, o ruído de porta limita a recuperação do valor exato.

### Análise das hipóteses e dos objetivos

Os intervalos nominais indicaram maior erro normalizado dos trios do que das probabilidades de sabor nas 25 configurações, e do que dos pares em 22 delas. A grade de controle sem erro de Monte Carlo sustentou o maior erro normalizado dos trios em todas as 15 configurações dessa janela. O erro dos trios cresceu com a interação em sistemas de quatro a oito neutrinos na janela $0\leq\tau\leq10$, mas não nos tempos iniciais, $\tau\leq3$, de modo que essa parte de H1 depende da janela temporal. No caso principal, com $N=4$, $\lambda=3$ e $\tau=2$, a aproximação recuperou 48% do cumulante de trio exato, um desvio muito acima das incertezas de amostragem e de integração. Em sistemas de doze e dezesseis neutrinos, o erro dos trios continuou maior, mas não cresceu de forma monotônica com a interação. Em acoplamento forte, a PSA também perdeu precisão nas probabilidades de sabor, o que reduz a vantagem dos observáveis de uma partícula sobre os trios. Com acoplamento fraco, os cumulantes são pequenos e o ruído de Monte Carlo da própria PSA precisa ser descontado, sob pena de produzir diferenças espúrias entre trios e pares.

Circuitos quânticos ideais distinguiram esse desvio com folga, com erro que decresce como $m^{-1/2}$ e fica abaixo de $2\times10^{-3}$ com 16.384 medições por bloco. Com ruído, a mitigação de leitura ampliou de menos de 0,5% para 3% o erro de leitura tolerável, o que apoia H2 nesse tipo de ruído. Para o ruído de porta, nenhum dos métodos tolerou despolarização acima de $3\times10^{-5}$ por porta de dois qubits no circuito de 648 CNOTs e sob o canal sintético adotado. Isso explica as estimativas próximas de zero obtidas no `ibm_kingston` com o circuito original e mostra que, com ruído de porta realista, a atenuação pode levar o circuito a valores próximos aos da PSA sem resolver a diferença. Com um circuito redesenhado de 78 portas CZ, o processador recuperou 61% do cumulante exato e ficou mais perto dele do que a PSA, que recupera 34%, mas ainda fora da margem exigida. Em dois pontos com seis e oito qubits e dois feixes, o hardware também errou menos que a PSA e que a previsão $C^{(3)}=0$, e em oito qubits recuperou o sinal do cumulante que a PSA inverte, mas recuperou apenas 44% e 21% do valor exato. Nos pontos examinados, o hardware distingue, portanto, a previsão da PSA em circuitos curtos, sem ainda servir de referência quantitativa para os trios.

### Limitações

As conclusões restringem-se a um modelo de dois sabores, a estados iniciais com metade dos neutrinos em cada sabor e à componente $zzz$ dos cumulantes. A grade clássica usa acoplamento uniforme. Os pontos em hardware foram escolhidos por cálculos prévios, diferem entre si em vários parâmetros e não constituem um estudo de escala em $N$ nem uma demonstração de vantagem computacional, já que a evolução exata ainda é viável nesses tamanhos.

Os intervalos da grade amostral são pontuais e sua cobertura não foi demonstrada para toda a grade. A validação arquivada do estimador original encontrou subcobertura no regime fraco; ela não valida automaticamente o estimador corrigido. Por isso, a contagem de intervalos positivos é descritiva, e a enumeração completa sustenta a comparação apenas nos regimes em que foi calculada. As execuções IBM sem comparação entre braços bruto e mitigado não constituem um teste de H2 no dispositivo.

## Conclusão

Nas configurações examinadas, a PSA apresentou maior erro normalizado nos trios do que nas probabilidades de sabor e, na maioria dos casos, nos pares. Circuitos quânticos distinguiram esse desvio quando o ruído de porta era pequeno ou o circuito era curto, mas não recuperaram o valor exato no hardware atual.

Os objetivos de comparar as ordens dos observáveis e avaliar interação, medições e ruído foram atendidos nas configurações definidas. A tendência com a interação depende da janela temporal, e o benefício da mitigação restringe-se ao mecanismo de leitura avaliado.

## Trabalhos futuros

Trabalhos futuros podem estender a comparação a acoplamentos angulares não uniformes e a três sabores, aumentar o número de trajetórias com acoplamento fraco e combinar a mitigação de leitura com a extrapolação a ruído zero, para avaliar se a execução em hardware alcança a margem de resolução exigida.

## Código e dados

O código, os protocolos e os dados derivados estão em <https://github.com/leonardovbf/correlacoes-tres-neutrinos>. O motor numérico (exato, campo médio, PSA e circuitos) fica em `src/neutrinos/`, os protocolos de cada fase em `configs/protocols/artigo_v1/`, e a análise estatística em `src/neutrinos/study_analysis.py`. Os resultados deste artigo são reproduzidos, nesta ordem, por `scripts/grade_psa.py gerar`, `scripts/grade_psa.py analisar`, `scripts/grade_psa.py ordens` e `scripts/grade_psa.py coletivo` (grade de H1 e comparação com a correlação coletiva), `scripts/varredura_ruido.py` (H2), `figuras/dados_orcamento.py` (orçamento de medições), e por `figuras/gerar_tabelas.py`, `figuras/figura_orcamento.py` e `figuras/figura_ruido.py` (tabelas e figuras). O ambiente científico de referência usa CPython 3.14.3, NumPy 2.4.3, SciPy 1.17.1, Qiskit 2.5.2, Qiskit Aer 0.18.2, Qiskit IBM Runtime 0.51.0 e Matplotlib 3.10.8, com as versões fixadas em `requirements-research.lock`. Todas as sementes são fixas, e a reprodução das medições ideais coincide com os valores originais em todas as 45 configurações. As contagens brutas, os circuitos compilados e as calibrações das execuções em hardware de 7 a 10 de novembro estão em `analysis/campaigns/`, nos pacotes `20261108-resultados-ibm` (confirmação com quatro qubits e pilotos), `20261108-aer-ibm-pareado` (simulação com ruído calibrado) e `20261110-hardware-confirmation` (confirmação com seis e oito qubits), com hashes SHA-256 de cada arquivo. As contagens do circuito curto também estão em `dados/ibm/circuito_curto_n4.json`, e `scripts/run_feedback_hardware.py verify` recalcula a confirmação com seis e oito qubits a partir das contagens, sem acesso à IBM. A grade de controle com $\tau\leq3$ e a varredura de ruído no circuito executado estão resumidas em `analysis/campaigns/20261109-feedback-v4/`. As contagens dos 80 trabalhos da primeira execução também estão preservadas no arquivo `existing_ibm_jobs.json` dos ZIPs de `20261109-feedback-v4`, que reúne 130 trabalhos históricos. Após a extração descrita no pacote, `analysis/feedback_delivery.py verify` verifica a reanálise sem acesso à IBM. Os blocos de trajetórias da PSA são regenerados de forma determinística pelos scripts acima.

## Referências

Abi, B. et al. (2020). Deep Underground Neutrino Experiment (DUNE), Far Detector Technical Design Report, Volume II: DUNE Physics. Technical Report FERMILAB-PUB-20-025-ND, DUNE Collaboration. <https://arxiv.org/abs/2002.03005>.

Akaho, R., Nagakura, H., Iwakami, W., Furusawa, S., Harada, A., Okawa, H., Matsufuru, H., Sumiyoshi, K., and Yamada, S. (2026). Bifurcated Impact of Neutrino Fast Flavor Conversion on Core-Collapse Supernovae Informed by Multiangle Neutrino Radiation Hydrodynamics. _Physical Review Letters_, 136(19):191002. <https://doi.org/10.1103/fksy-1jtw>.

Amitrano, V., Roggero, A., Luchi, P., Turro, F., Vespucci, L., and Pederiva, F. (2023). Trapped-ion quantum simulation of collective neutrino oscillations. _Physical Review D_, 107(2):023007. <https://doi.org/10.1103/PhysRevD.107.023007>.

Balantekin, A. B. and Pehlivan, Y. (2007). Neutrino–neutrino interactions and flavour mixing in dense matter. _Journal of Physics G: Nuclear and Particle Physics_, 34(1):47--65. <https://doi.org/10.1088/0954-3899/34/1/004>.

Baum, S., Capozzi, F., and Horiuchi, S. (2022). Rocks, water, and noble liquids: Unfolding the flavor contents of supernova neutrinos. _Physical Review D_, 106(12):123008. <https://doi.org/10.1103/PhysRevD.106.123008>.

Bravyi, S., Sheldon, S., Kandala, A., Mckay, D. C., and Gambetta, J. M. (2021). Mitigating measurement errors in multiqubit experiments. _Physical Review A_, 103(4):042605. <https://doi.org/10.1103/PhysRevA.103.042605>.

Cai, Z., Babbush, R., Benjamin, S. C., Endo, S., Huggins, W. J., Li, Y., McClean, J. R., and O'Brien, T. E. (2023). Quantum error mitigation. _Reviews of Modern Physics_, 95(4):045005. <https://doi.org/10.1103/RevModPhys.95.045005>.

Cervia, M. J., Patwardhan, A. V., Balantekin, A. B., Coppersmith, S. N., and Johnson, C. W. (2019). Entanglement and collective flavor oscillations in a dense neutrino gas. _Physical Review D_, 100(8):083001. <https://doi.org/10.1103/PhysRevD.100.083001>.

Childs, A. M., Su, Y., Tran, M. C., Wiebe, N., and Zhu, S. (2021). Theory of Trotter Error with Commutator Scaling. _Physical Review X_, 11(1):011020. <https://doi.org/10.1103/PhysRevX.11.011020>.

Cowan, J. J., Sneden, C., Lawler, J. E., Aprahamian, A., Wiescher, M., Langanke, K., Martínez-Pinedo, G., and Thielemann, F.-K. (2021). Origin of the heaviest elements: The rapid neutron-capture process. _Reviews of Modern Physics_, 93(1):015002. <https://doi.org/10.1103/RevModPhys.93.015002>.

de Correc, C., Lacroix, D., and Bertrand, C. (2026). Emulation of large-scale qubit registers with a phase-space approach. _APS Open Science_, 1:000017. <https://doi.org/10.1103/swn6-s387>.

Duan, H., Fuller, G. M., and Qian, Y.-Z. (2010). Collective Neutrino Oscillations. _Annual Review of Nuclear and Particle Science_, 60(1):569--594. <https://doi.org/10.1146/annurev.nucl.012809.104524>.

Hall, B., Roggero, A., Baroni, A., and Carlson, J. (2021). Simulation of collective neutrino oscillations on a quantum computer. _Physical Review D_, 104(6):063009. <https://doi.org/10.1103/PhysRevD.104.063009>.

Illa, M. and Savage, M. J. (2023). Multi-Neutrino Entanglement and Correlations in Dense Neutrino Systems. _Physical Review Letters_, 130:221003. <https://doi.org/10.1103/PhysRevLett.130.221003>.

Janka, H.-T. (2012). Explosion Mechanisms of Core-Collapse Supernovae. _Annual Review of Nuclear and Particle Science_, 62:407--451. <https://doi.org/10.1146/annurev-nucl-102711-094901>.

Kiss, O., Tavernelli, I., Tacchino, F., Lacroix, D., and Roggero, A. (2026). Neutrino thermalization via randomization on a quantum processor. _Communications Physics_, 9(1):282. <https://doi.org/10.1038/s42005-026-02697-2>.

Lacroix, D. and Ayik, S. (2014). Stochastic quantum dynamics beyond mean field. _The European Physical Journal A_, 50(6):95. <https://doi.org/10.1140/epja/i2014-14095-8>.

Lacroix, D., Balantekin, A. B., Cervia, M. J., Patwardhan, A. V., and Siwach, P. (2022). Role of non-Gaussian quantum fluctuations in neutrino entanglement. _Physical Review D_, 106(12):123006. <https://doi.org/10.1103/PhysRevD.106.123006>.

Lacroix, D., Bauge, A., Yilmaz, B., Mangin-Brinet, M., Roggero, A., and Balantekin, A. B. (2024). Phase-space methods for neutrino oscillations: Extension to multibeams. _Physical Review D_, 110:103027. <https://doi.org/10.1103/PhysRevD.110.103027>.

Lloyd, S. (1996). Universal Quantum Simulators. _Science_, 273(5278):1073--1078. <https://doi.org/10.1126/science.273.5278.1073>.

Mangin-Brinet, M., Bauge, A., and Lacroix, D. (2026). Three-flavor neutrino oscillations using the phase space approach. _Physical Review D_, 113:036026. <https://doi.org/10.1103/yr2g-1g2g>.

Martin, J. D., Roggero, A., Duan, H., Carlson, J., and Cirigliano, V. (2022). Classical and quantum evolution in a simple coherent neutrino problem. _Physical Review D_, 105(8):083020. <https://doi.org/10.1103/PhysRevD.105.083020>.

Nagakura, H. (2023). Roles of Fast Neutrino-Flavor Conversion on the Neutrino-Heating Mechanism of Core-Collapse Supernova. _Physical Review Letters_, 130(21):211401. <https://doi.org/10.1103/PhysRevLett.130.211401>.

Nielsen, M. A. and Chuang, I. L. (2010). _Quantum Computation and Quantum Information: 10th Anniversary Edition_. Cambridge University Press, Cambridge. <https://doi.org/10.1017/CBO9780511976667>.

Pehlivan, Y., Balantekin, A. B., Kajino, T., and Yoshida, T. (2011). Invariants of collective neutrino oscillations. _Physical Review D_, 84(6):065008. <https://doi.org/10.1103/PhysRevD.84.065008>.

Preskill, J. (2018). Quantum Computing in the NISQ era and beyond. _Quantum_, 2:79. <https://doi.org/10.22331/q-2018-08-06-79>.

Riccio, M. and Balantekin, A. B. (2026). Improved Approximations for Collective Neutrino Oscillations. Preprint arXiv:2607.28619, versão 2. <https://doi.org/10.48550/arXiv.2607.28619>.

Rrapaj, E. (2020). Exact solution of multiangle quantum many-body collective neutrino-flavor oscillations. _Physical Review C_, 101(6):065805. <https://doi.org/10.1103/PhysRevC.101.065805>.

Sarmah, P., Chakraborty, S., Medhi, A., Bose, D., and Devi, M. M. (2026). Neutrino mass ordering from the next Galactic supernova at DUNE, HK, and JUNO. Preprint arXiv:2606.06580. <https://arxiv.org/abs/2606.06580>.

Shalgar, S. and Tamborra, I. (2023). Do we have enough evidence to invalidate the mean-field approximation adopted to model collective neutrino oscillations? _Physical Review D_, 107(12):123004. <https://doi.org/10.1103/PhysRevD.107.123004>.

Vatan, F. and Williams, C. (2004). Optimal quantum circuits for general two-qubit gates. _Physical Review A_, 69(3):032315. <https://doi.org/10.1103/PhysRevA.69.032315>.

Vissani, F., Costantini, M. L., Fulgione, W., Ianni, A., and Pagliaroli, G. (2010). What is the issue with SN1987A neutrinos? Preprint arXiv:1008.4726. <https://arxiv.org/abs/1008.4726>.

Volpe, C., Väänänen, D., and Espinoza, C. (2013). Extended evolution equations for neutrino propagation in astrophysical and cosmological environments. _Physical Review D_, 87(11):113010. <https://doi.org/10.1103/PhysRevD.87.113010>.
