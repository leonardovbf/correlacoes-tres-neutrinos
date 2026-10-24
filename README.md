# Correlações de dois e três corpos em sistemas de neutrinos

Projeto sobre a precisão da aproximação de espaço de fase em oscilações coletivas de neutrinos e sobre a capacidade de circuitos quânticos de distinguir suas previsões da evolução exata. O estudo adota dois sabores, energias distintas e interações entre todos os pares.

A Entrega 1 reúne o problema, a pergunta, os objetivos, as hipóteses, os resumos e a introdução. A estratégia de avaliação apresenta o planejamento dos cálculos e das comparações que serão desenvolvidos nas próximas etapas.

## Arquivos

| Arquivo ou diretório | Conteúdo |
| --- | --- |
| [ARTIGO.md](ARTIGO.md) | Texto principal em português, com contexto astrofísico, estado da arte e referências unificadas. |
| [ARTIGO.eng.md](ARTIGO.eng.md) | Versão correspondente em inglês, com resumo em português e abstract em inglês. |
| [referencias.bib](referencias.bib) | Base BibTeX com as 18 fontes citadas e quatro leituras complementares identificadas por comentários. |
| [figuras/](figuras/) | Diagramas em português, em SVG editável e PNG. |
| [figuras/en/](figuras/en/) | Os mesmos diagramas com os rótulos em inglês. |
| [figuras/gerar_diagramas.py](figuras/gerar_diagramas.py) | Código que gera as duas versões das figuras. |

## Contribuições da entrega

O núcleo da pesquisa define a pergunta, os objetivos e as hipóteses. O contexto da introdução apresenta supernovas, neutrinos, sabor, nucleossíntese e detecção; essa frente também reúne e padroniza as referências. O estado da arte discute campo médio, espaço de fase, BBGKY e simulações quânticas, delimitando a lacuna do estudo. O parágrafo final da introdução conecta essas contribuições ao plano de pesquisa.

## Figuras

1. **Colapso estelar:** cortes esquemáticos do núcleo, do choque e da região de aquecimento por neutrinos.
2. **Correlações conectadas:** decomposição de um momento de três partículas em médias, contribuições dos pares e cumulante do trio.
3. **Protocolo de comparação:** modelo comum, quatro métodos de evolução, observáveis e controles das fontes de erro.

Para regenerar todas as figuras, executar na raiz do repositório, com Python 3.11 ou superior e `uv` instalado:

```sh
uv run figuras/gerar_diagramas.py
```

Para gerar somente uma língua:

```sh
uv run figuras/gerar_diagramas.py --idioma pt
uv run figuras/gerar_diagramas.py --idioma en
```

O script declara a dependência de Matplotlib e exporta os desenhos com largura de 170 mm e PNG a 450 dpi. Os diagramas são conceituais; as curvas de evolução, os mapas de erro e os circuitos de portas serão produzidos com os cálculos e a implementação.

## Conferência no modelo SBC

Na conferência de 23 de outubro de 2026, a introdução foi compilada e inspecionada no modelo SBC, com fonte Times de 12 pontos, coluna de 150 mm e altura útil de 237 mm. A extensão foi medida entre o início de cada subseção e o início da seguinte, somando as alturas ocupadas nas páginas sucessivas.

| Versão | Contexto, Figura 1 e legenda | Estado da arte até a lacuna |
| --- | --- | --- |
| Português | 1,45 página equivalente | 1,29 página equivalente |
| Inglês | 1,43 página equivalente | 1,27 página equivalente |

As duas partes atenderam à extensão de 1 a 1,5 página no modelo usado. O parágrafo final de objetivo e contribuição foi contado separadamente. Alterações no texto, na figura, na legenda ou no modelo exigem nova composição e medição; a paginação do artigo completo será determinada quando todas as seções forem compostas juntas.

## Referências e edição

As listas de referências dos artigos contêm somente as fontes citadas, em ordem alfabética e com apresentação uniforme. A base BibTeX mantém também quatro leituras complementares para o desenvolvimento da pesquisa. Ao acrescentar uma citação, atualizar a lista do artigo e o registro correspondente em `referencias.bib`.

Manter as versões em português e inglês alinhadas quanto ao escopo, às hipóteses, às condições de comparação e às legendas. Para alterar os desenhos, editar o gerador e regenerar as imagens antes de revisar sua leitura no artigo.
