# Além do campo médio: aproximações de baixo custo capturam as correlações entre neutrinos em supernovas?

_Beyond the average field: do low cost approximations capture the correlations between neutrinos in supernovae?_

## Abstract

## Problema de pesquisa

No processo de simulações de supernovas, é necessário prever como os neutrinos trocam de sabor, tendo em vista o impacto das trocas no aquecimento da onda choque da estrela, na produção de metais pesados, e consequentemente o sinal registrado por detectores no planeta Terra. Próximo ao núcleo da estrela, os neutrinos interagem entre si e se emaranham. Logo, o custo de cálculo do sabor dos neutrinos cresce de forma exponencial com o número de partículas analisadas, requerindo o uso de aproximações para medição. A aproximação de campo médio, até pouco tempo utilizada, ja provou-se falha em tempos curtos. Na bibliografia recente, atalhos como a aproximação de fase e o fechamento BBGKY corrigem a maior parte da falha provada nos atalhos de campo médio, contudo a validação destes foi feita principalmente no sabor de cada neutrino (sem considerar pares de sabores) e em modelos de entropia de apenas um e dois neutrinos. O fechamento BBGKY por exemplo, assume por construção que as correlações entre três ou mais neutrinos são nulas. Ao mesmo tempo, experimentos conduzidos com computadores quânticos indicam emaranhamento evidente entre muitos neutrinos em um sistema, com baixa capacidade de detecção de ruídos vindos da estrutura computacional. Portanto, não se sabe se os atalhos de baixo custo capturam as correlações entre três ou mais neutrinos e nem se o hardware quântico existente apresenta as capacidades para medi-las com precisão.

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

## Parágrafo final da introdução
