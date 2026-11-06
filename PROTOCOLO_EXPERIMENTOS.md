# Protocolo dos experimentos do artigo — desenho v1

Data: 5 de novembro de 2026.

Estado: desenho físico v1, revisão operacional 2 implementada antes da coleta principal.
Execução e retomada: [EXECUTAR_EXPERIMENTOS.md](EXECUTAR_EXPERIMENTOS.md).
A grade, as sementes, os testes principais e as metas de precisão já estão
especificados em `configs/estudos/artigo_v1.json`. Os onze arquivos executáveis e
as três especificações detalhadas estão em `configs/protocols/artigo_v1/`.
As verificações iniciais determinam se os controles passam; não adiam o desenho
dos demais experimentos. Mudanças posteriores exigem nova versão e justificativa.
Este documento complementa `PLANO_TECNICO.md` e preserva as hipóteses de `ARTIGO.md`.

O resultado principal é a fidelidade dos cumulantes conectados de três neutrinos,
K³ᶻᶻᶻᵢⱼₖ(τ): comparar a previsão da PSA e a estimativa do circuito com a mesma
referência exata. Probabilidades individuais e correlações de pares são controles
e resultados secundários, que também permitem avaliar a hipótese H1 do artigo.
O benchmark publicado valida a implementação; a contribuição principal é a
comparação dos trios no modelo e nas condições definidos pelo grupo.

Para cada trio e janela previamente escolhidos, comparar os erros RMSE
E_PSA,3 e E_circuito,3 contra o exato, com suas incertezas. Isso mede quanto cada
método captura a correlação. O critério de H2 acrescenta uma pergunta mais
exigente: se o circuito resolve a diferença exato–PSA mantendo concordância com
o exato na margem definida, sob medições e ruído especificados.

## 1. Sequência e entregas

| Etapa | Pergunta | Entrega e condição para avançar |
| --- | --- | --- |
| Reprodução publicada | Nosso código reproduz um caso conhecido? | Configuração do benchmark, conversão de convenções, curvas comparadas à fonte e diferenças quantificadas. |
| Verificação de precisão e custo | A configuração especificada atende às metas e aos recursos disponíveis? | Relatório de convergência, tempo, memória e disco; aprovação ou falha dos controles registrados. |
| Registro do desenho | Quais casos, métricas e decisões serão usados? | Desenho v1 e JSONs já definidos; vincular seu commit antes da coleta principal. |
| Coleta clássica — H1 | Quanto a PSA reproduz K³ e como seu erro se compara aos controles de um e dois corpos? | Curvas de K³ exato e PSA, erros e incertezas por interação e tamanho; controles secundários. |
| Circuito ideal | Qual é o erro introduzido por Trotter? | Curvas e erros contra exato em Qiskit, nos mesmos casos físicos. |
| Medições e ruído — H2 | Quanto o circuito captura K³ e em quais condições resolve a diferença exato–PSA? | K³ exato, PSA e circuito no mesmo gráfico; erros e intervalos, com e sem mitigação e orçamento total igual. |
| Hardware e publicação | O que se mantém em um dispositivo real? | Extensão opcional em IBM; figuras, tabelas, limitações e reprodução integral dos resultados. |

Uma etapa não é aprovada apenas porque o programa terminou sem erro. A reprodução
publicada e a convergência são as primeiras evidências científicas necessárias.

## 2. Primeiro benchmark recomendado

Fonte: [Lacroix et al. (2024), Phase-Space methods for neutrino oscillations:
extension to multi-beams](https://arxiv.org/html/2409.20215v2), seção III.1.1.

O alvo de validação proposto é a Figura 2(c): oito neutrinos, um por feixe, comparando
evolução exata e PSA com amostragem bi-valuada, com observáveis individuais na
base de sabor. A Figura 3(a), para quatro neutrinos, pode ser uma validação
adicional do observável coletivo de flutuações. Ela exige conferir a base, a
normalização e os termos diagonais; não corresponde diretamente à lista de
covariâncias de pares distintos exibida na plataforma.

Essas figuras são controles de reprodução. Elas não substituem os resultados
principais de cumulantes de três corpos do projeto.

Antes de executar:

1. Extrair da publicação Hamiltoniano, matriz de acoplamentos, frequências,
   estados, eixo temporal e definição do observável da figura.
2. Derivar por escrito a conversão entre soma sobre pares ordenados e não
   ordenados, operadores de spin e Pauli, e unidades de tempo/energia do código.
3. Criar uma configuração exclusiva para a reprodução. O cenário próprio atual,
   com frequências distintas e acoplamentos uniformes, não é esse benchmark.
4. Obter dados dos autores/suplemento quando disponíveis; se for necessário
   digitalizar a figura, guardar a origem e a incerteza da digitalização.
5. Comparar a referência exata com a referência publicada e a PSA com a PSA
   publicada, preservando os desvios entre os métodos que a fonte apresenta.
6. Fixar a tolerância da reprodução antes de avaliar sua concordância, com base
   na precisão da fonte, na integração e no erro de amostragem.

A reprodução está implementada em `00_reproducao_publicada.json`, com 10 mil
trajetórias executadas em blocos. A conversão de unidades, os dados vetoriais
extraídos da figura, a origem e as tolerâncias estão em
`data/benchmarks/lacroix2024/`. O runner verifica separadamente exato e PSA.

## 3. Verificação das metas de precisão definidas

Usar inicialmente N = 4 e 8 e μ/ω̄ = 0,1; 1; 10 no modelo próprio. O caso μ = 0
é um controle adicional. Sementes de piloto: 1 a 5.

- Validar H hermitiano, estado inicial, ordem dos bits, momentos iniciais e caso
  sem interação. Para N pequeno, comparar a evolução exata com uma implementação
  independente da exponencial; conservação da norma, sozinha, não basta.
- Refinar RK4 com 2, 4, 8 e 12 subpassos por intervalo, comparando todos os
  observáveis. Verificar que não há trajetórias PSA não finitas.
- Aumentar a PSA com 512, 1.024, 2.048 e 4.096 trajetórias por bloco e sementes
  independentes. Medir o efeito da amostragem em P, C² e K³ separadamente.
- Refinar Trotter com 1, 2, 4, 8 e 16 passos por intervalo. Comparar o emulador
  próprio com o Qiskit também em tempos posteriores; o protocolo `04_qiskit.json` cobre
  τ=1/2/4 com os mesmos passos totais.
- Medir duração, pico de memória e armazenamento antes de aprovar a extensão
  para N = 12 e 16.

O desenho v1 fixa metas operacionais de diferença máxima na integração:
1e-6 para Pₑ, 1e-5 para C² e 1e-5 para K³. A comparação independente do exato
tem meta de 1e-10; o erro máximo de Trotter em K³ tem teto de 1e-3. A margem
de equivalência de H2 é δ=0,01 e o piso RMS para normalização é ε=1e-4.
São escolhas de resolução do estudo, não limiares universais da literatura.
Se um controle falhar, preservar o resultado e registrar uma versão nova antes
de outra coleta; não ajustar os critérios para obter uma hipótese favorável.

## 4. Grade própria definida para H1

| Item | Desenho v1 |
| --- | --- |
| Tamanhos do conjunto principal | N = 4, 6 e 8. |
| Extensão clássica prevista no artigo | N = 12 e 16, após medir viabilidade. Se não couber, revisar explicitamente o escopo do artigo. |
| Interações | μ/ω̄ = 0,1; 0,3; 1; 3; 10. |
| Frequências | `linspace(0.7, 1.3, N)`, média igual a 1. |
| Campo e mistura | θ = 0,2 rad; B = (sen(2θ), 0, −cos(2θ)). |
| Acoplamentos | gᵢⱼ = 1 para i ≠ j e zero na diagonal. |
| Estado inicial | Primeira metade em νₑ; segunda metade em νₓ; associação frequência–sabor mantida. |
| Janela e saídas | τ de 0 a 10, com 201 instantes igualmente espaçados. |
| Observáveis | Todos os Pₑ, todos os pares C²ᶻᶻ e todos os trios K³ᶻᶻᶻ de índices distintos. |
| Recursos PSA | 20 blocos de 4.096 trajetórias por configuração; 12 subpassos RK4. |
| Sementes principais | 10.001 a 10.020, distintas das verificações iniciais. |

O conjunto principal contém 15 configurações físicas. Com 20 sementes, são 300
blocos PSA. As referências exatas e de campo médio são iguais entre sementes e
são reutilizadas por cache com hashes de fontes/dependências e parâmetros
físicos. A PSA e as medições mantêm cada semente declarada.
A extensão para N = 12 e 16 acrescenta dez configurações físicas.

Se os blocos forem combinados, agregar primeiro os momentos m1, m2 e m3 com pesos
proporcionais ao número de trajetórias e depois calcular cumulantes. A média dos
cumulantes de blocos finitos não é, em geral, o cumulante dos momentos agregados.
Guardar blocos/trajetórias e sementes para reamostragem e auditoria.

Para cada grandeza, calcular RMSE absoluto E, maior erro absoluto e amplitude RMS
S da referência sobre os mesmos tempos e índices. Reportar E/S apenas quando
S superar o limiar ε fixado. Não calcular percentuais quando a referência não
estiver resolvida. Usar magnitudes/erros quadráticos para que sinais de trios
diferentes não se cancelem numa média.

H1 será avaliada pela comparação dos erros de indivíduos, pares e trios e pela
tendência com μ. Um resultado em que a PSA reproduz bem K³ também é um resultado
válido; a coleta não depende de encontrar uma falha da aproximação.

## 5. Circuitos e H2

Primeiro, validar Trotter em simulador ideal no conjunto N = 4, 6 e 8. Só depois
adicionar medições e ruído. Aumentar passos reduz o erro de discretização, mas
também pode aumentar o custo e o efeito do ruído; registrar ambos.

O caso primário de H2 fica definido em N=4, μ=3, trio (0,1,2), τ=2, perfil de
ruído moderado e 16.384 medições totais por repetição, com 20 repetições. O total
agregado por método é 327.680 medições. A escolha é um caso intermediário fixado
no desenho, e não uma busca pelo maior sinal observado. Os demais casos são
análises de sensibilidade; não substituirão o teste primário após a coleta.

A grade de sensibilidade usa 1.024, 4.096 e 16.384 medições por repetição, 20
sementes, μ=0,1/0,3/1/3/10 e τ=1/2/4. Os perfis Aer (erro de uma porta, duas
portas, leitura) são: ideal=(0,0,0), leve=(0,0001;0,001;0,01) e
moderado=(0,001;0,01;0,03). Para respeitar o teto atual de 120 subpassos Aer,
cada instante usa uma grade de 8 pontos até τ, com 16 passos por intervalo:
112 subpassos totais. Essa evolução ideal deve passar pelo controle de Trotter
antes de atribuir os desvios ao ruído.

A mitigação definida é tensorial de leitura, com matrizes 2x2 por qubit sob a
hipótese de erros independentes. Usar os estados de calibração 0000 e 1111,
com 12,5% do orçamento para cada um e 75% para sinal. O método sem mitigação usa
100% do mesmo orçamento para sinal. Reamostrar também a calibração e rejeitar a
inversão de matrizes com número de condição acima de 10, registrando o caso como
não resolvido. A implementação em `07_mitigacao.json` preserva as contagens e não corrige,
por definição, todo viés de portas.

Critério proposto para dizer que a diferença foi resolvida:

1. O intervalo para circuito − PSA exclui zero, considerando também a incerteza
   da PSA.
2. O intervalo para circuito − exato fica inteiramente dentro de [−δ, +δ], com
   δ definido previamente. Apenas incluir zero não comprova equivalência.
3. O erro residual de Trotter e da referência está quantificado e cabe no
   orçamento de precisão.
4. Se houver vários testes primários, usar correção previamente definida, como
   Holm, e reportar também casos em que o sinal não foi resolvido.

Se ambos os métodos não resolverem a diferença, a necessidade de mitigação é
inconclusiva. Se apenas o mitigado resolver, há apoio a H2 nessa condição; se o
método sem mitigação resolver, H2 é refutada nessa condição.

Reamostrar trajetórias ou bitstrings completos para preservar as covariâncias
dos momentos usados em cada cumulante. Um mesmo conjunto de medições Z permite
estimar todos os indivíduos, pares e trios naquele instante; não é necessário
enviar um circuito idêntico para cada observável.

Hardware IBM é uma extensão, após demonstrar viabilidade com o circuito
transpilado. Registrar job, dispositivo, data, calibração, layout, profundidade,
portas de dois qubits, shots e opções de Runtime. O limite interativo atual de
subpassos e o custo de roteamento precisam ser avaliados antes de enviar a grade.

## 6. Preparação técnica e estado atual

Já estão disponíveis o runner sequencial `scripts/run_protocol.py`, o piloto
`configs/protocols/piloto_tres_corpos.json`, registros JSON por tentativa,
retomada, replay com comparação numérica, hashes de artefatos, snapshots de
fontes/dependências e `requirements-research.lock`. Cada resultado Aer preserva
contagens com chave própria. O uso está em `EXECUTAR_EXPERIMENTOS.md`.

Os demais testes já estão definidos no catálogo `configs/estudos/artigo_v1.json`.
Para regenerar ou validar as definições, usar `scripts/define_article_protocols.py`
e sua opção `--check`. Isso não executa a coleta. A tabela de arquivos, contagens
e pendências está em `configs/protocols/artigo_v1/README.md`.

A revisão operacional 2 implementa benchmark, PSA em blocos, cache verificável,
Qiskit em tempos posteriores, análise conjunta, mitigação e exportação de curvas.
O estudo completo é iniciado por `scripts/run_study.py run` e preserva cada
controle com aprovação/falha no JSON. Antes da coleta, identificar a versão dos
fontes; depois, arquivar a pasta completa dos resultados junto ao material do artigo.

## 7. Material esperado para o artigo

1. Figura de reprodução publicada, com parâmetros e conversões documentados.
2. Figura de convergência de integração, PSA e Trotter.
3. Curvas de Pₑ, C² e K³ em casos declarados, com incertezas.
4. Mapas/tabelas de erros por N e μ, incluindo cenários sem sinal normalizável.
5. Comparação com e sem mitigação para H2, com orçamento e ruído explícitos.
6. Tabela de recursos: duração, memória, trajetórias, shots e profundidade.

Cada figura deve ser regenerada por um comando a partir de configurações e saídas
arquivadas. Capturas da plataforma podem ilustrar a ferramenta, mas a análise do
artigo deve vir dos dados numéricos exportados.

## 8. Próxima tarefa concreta

Executar `plan`, conferir o ambiente e iniciar `run` conforme
`EXECUTAR_EXPERIMENTOS.md`. O runner começa pela reprodução da Figura 2(c),
verifica os controles e avança somente quando eles passam. O perfil `smoke`
valida o software e não substitui a coleta científica. Eventuais alterações
serão versões documentadas, sem escolhas guiadas pelos resultados.

## Revisão operacional 2 — antes da coleta oficial

A grade física e o ponto principal H2 foram preservados. `run_study` verifica
controles entre fases; H1/H2 não precisam ser favoráveis para concluir a coleta.
A meta adicional de precisão amostral é erro padrão máximo entre sementes de
K3 de 0,01 no orçamento PSA de 4096 durante T02. É uma meta operacional de
resolução e pode reprovar; não é uma afirmação de validade universal da PSA.

A unidade de bootstrap PSA passa a ser o bloco independente de semente de
mesmo tamanho, preservando dentro dele os momentos conjuntos e a trajetória
temporal. São 2000 reamostragens, incluindo os 20 blocos na análise principal.
Cumulantes são calculados depois de agregar momentos. Para H2, as contagens
agregadas de sinal e dos dois estados de calibração são reamostradas como
multinomiais, a resposta é reestimada e a inversão refeita a cada réplica.
A PSA é reamostrada independentemente por blocos. A incerteza não conta duas
vezes a mesma flutuação de shots por reamostrar também as sementes do circuito.
A análise mantém quasiprobabilidades negativas e declara calibração não
resolvida se houver inversão instável, sem descarte seletivo de réplicas.

A margem H2 permanece ±0,01, acrescida do limite de erro Trotter observado
contra exato e do limite numérico 1e-5. Comparações de sensibilidade são
descritivas; não fazemos declarações confirmatórias múltiplas sem uma análise
com correção apropriada. O hardware continua uma extensão separada; um comando
explícito prepara o protocolo e outro autoriza os envios, após a coleta local.
