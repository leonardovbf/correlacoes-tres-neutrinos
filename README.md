# Correlações de dois e três corpos em sistemas de neutrinos

Estudo sobre os regimes de validade da aproximação de espaço de fase (PSA) em um modelo de oscilações coletivas de dois sabores, com energias distintas e interações entre todos os pares. A comparação usa evolução exata, campo médio, PSA e circuitos quânticos, com atenção aos cumulantes conectados de três corpos.

Esta branch contém a revisão do desenho da pesquisa da Sprint 1. O texto apresenta o protocolo proposto e a organização futura dos resultados; não relata experimentos já executados. Os resumos foram condensados a partir da redação da entrega, mantendo sua sequência de argumentação. Os dois PDFs revisados têm dez páginas, com resumo e abstract de dez linhas cada. A revisão considera o parecer completo dos professores e os comentários do [PR #5](https://github.com/leonardovbf/correlacoes-tres-neutrinos/pull/5).

## Artigo e pareceres

| Arquivo | Conteúdo |
| --- | --- |
| [ARTIGO.md](ARTIGO.md) | Manuscrito em português. |
| [ARTIGO.eng.md](ARTIGO.eng.md) | Versão correspondente em inglês. |
| [PDF em português](output/pdf/artigo-neutrinos-revisao-s1.pdf) | Revisão composta no estilo SBC. |
| [PDF em inglês](output/pdf/artigo-neutrinos-revisao-s1-en.pdf) | Revisão composta no estilo SBC. |
| [Registro da revisão](artigo/revisao-s1/README.md) | Correspondência entre os pareceres e as alterações, decisões metodológicas e pendências. |
| [referencias.bib](referencias.bib) | 17 fontes citadas e quatro leituras complementares identificadas por comentários. |
| [Entrega original](artigo-neutrinos-entrega-1-sbc.pdf) | Registro histórico da versão avaliada; não corresponde ao texto revisado. |

A Introdução reúne contexto, estado da arte, lacuna, pergunta, objetivo e hipóteses. A Seção 2 apresenta o desenho da pesquisa e os critérios de avaliação; a Seção 3 descreve a apresentação prevista dos resultados. H1 mantém a expectativa de maior erro nos trios e sua tendência com a interação, com justificativa e critérios de refutação. H2 compara limiares de ruído com e sem mitigação sob o mesmo orçamento total de medições. A etapa quântica avalia precisão e recursos em sistemas que permitem referência clássica conhecida.

## Gerar os PDFs

Requisitos: Python 3, [Pandoc](https://pandoc.org/) e [Tectonic](https://tectonic-typesetting.github.io/), disponíveis no `PATH`. Na raiz do repositório:

```sh
python3 scripts/gerar_revisao_sbc.py
```

Para gerar uma única versão:

```sh
python3 scripts/gerar_revisao_sbc.py --idioma pt
python3 scripts/gerar_revisao_sbc.py --idioma en
```

O gerador lê os manuscritos e a base BibTeX. Os arquivos finais ficam em `output/pdf/`; o LaTeX, a bibliografia compilada e os logs ficam em `tmp/pdfs/revisao-s1/`. O Tectonic pode baixar seus pacotes na primeira execução. O preâmbulo e os arquivos do estilo estão em `artigo/revisao-s1/`.

Os e-mails serão preenchidos pelos autores em [emails.json](artigo/revisao-s1/emails.json). Campos vazios são omitidos do cabeçalho. Após preenchê-los, regenerar os PDFs e conferir a primeira página.

## Figuras e edição

As três figuras conceituais da entrega foram preservadas: colapso estelar, decomposição das correlações conectadas e protocolo de comparação. As versões em português estão em [figuras/](figuras/), e as traduções em [figuras/en/](figuras/en/), em SVG e PNG.

Para regenerá-las, com Python 3.11 ou superior e `uv` instalado:

```sh
uv run figuras/gerar_diagramas.py
```

O gerador aceita `--idioma pt` e `--idioma en`. Os desenhos têm largura de 170 mm e PNG a 450 dpi. São diagramas conceituais; curvas de evolução e circuitos de portas dependem da execução do protocolo.

Manter os dois manuscritos alinhados quanto a hipóteses, parâmetros, observáveis, critérios e referências. Alterações no texto exigem nova composição e inspeção dos PDFs; a contagem de linhas dos resumos depende da composição, não apenas do número de palavras.
