# Revisão da Sprint 1

Esta revisão foi reconstruída a partir do texto entregue, preservado no commit `39279cf`, e reavaliou as mudanças iniciais do PR #5 (`e4cf765`). As fontes de revisão foram o parecer completo de oito páginas fornecido pelos autores e os comentários de Giovanna no PR. A linguagem e os argumentos da entrega foram preservados sempre que a correção não exigia mudança. As figuras originais foram mantidas.

## Correspondência com os pareceres

| Apontamento | Tratamento na revisão |
| --- | --- |
| Título no plural e promessa ampla de aplicação em supernovas | Título centrado na PSA e nas correlações de três corpos; supernovas permanecem como motivação do modelo simplificado. |
| Introdução depois dos elementos de pesquisa; redundâncias | Introdução como Seção 1, incorporando problema, pergunta, objetivo e hipóteses em texto corrido. Refutação e pré-registro na Seção 2. |
| Contexto astrofísico longo | Condensados os trechos sobre SN 1987A e detectores; preservada a Figura 1. |
| Ordem da argumentação | Lacuna e relevância dos trios antecedem pergunta e proposta; o encerramento indica as Seções 2 e 3. |
| Justificativa da etapa quântica | Estudo de precisão e recursos com referência clássica acessível, preparando avaliações futuras em tamanhos maiores. Sem alegação de vantagem quântica nos tamanhos examinados. |
| Pergunta binária | Pergunta formulada em regimes de interação, tamanho e tempo, incluindo condições de ruído e medições. |
| H1 sem justificativa da tendência | Mantida a tendência com a interação, motivada pelo acoplamento da hierarquia; explicitado seu caráter de conjectura e a dependência do estado e da janela temporal. |
| H2 dependente de escolhas arbitrárias de ruído e shots | Comparação do limiar de ruído com e sem mitigação sob o mesmo orçamento total; reporte também do menor orçamento avaliado e dos limites da varredura. |
| Resumo e abstract reestruturados excessivamente no primeiro PR | Retomada a sequência contexto, problema, objetivo, métodos e contribuição; condensação para o limite de dez linhas. “Este trabalho”/“This work”; detalhe operacional de hardware fora dos resumos. |
| Qubits no contexto astrofísico | Mapeamento dos sabores transferido para o modelo na Seção 2.1. |
| Citação do press release do Nobel | Removida; a revisão de Duan, Fuller e Qian fundamenta a explicação das oscilações. |
| Citações separadas e palavras coladas no PDF | Citações agrupadas; bibliografia composta via BibTeX; idiomas de hifenização definidos separadamente para resumo e abstract. |
| Referências de 2026 ainda como preprints | Consultadas as páginas de Riccio e Balantekin e de Sarmah em 6/11/2026. Sem referência de periódico indicada nessas páginas, mantido o status de preprint; Riccio explicitamente identificado no texto. Isso não constitui busca exaustiva por publicação em outros índices. |
| Estados iniciais não especificados | Estados fatorizados de sabor puro, com comparação principal em sistemas pares e metade dos neutrinos em cada sabor; distribuição e parâmetros registrados por cenário. |
| Extensão de N e hipótese de escala | Faixa principal 4–16; extensão a 20/22 condicionada ao custo medido. Dependência com N explorada sem impor uma lei de escala sem justificativa. |
| Erro normalizado quando a referência se aproxima de zero | Definidos RMS da referência e piso dependente do refinamento numérico; erros absolutos preservados nos casos excluídos e análise de sensibilidade do piso. |
| Cumulantes e incertezas | Definições de Z, ZZ e ZZZ; reamostragem conjunta preservando a dependência entre os termos; cumulante não apresentado como certificado de emaranhamento. |
| Trajetórias, convergência, Trotter e shots | Valores iniciais e refinamentos propostos para o piloto, com tolerâncias e limites registrados antes da análise confirmatória. |
| Técnicas de mitigação e critério de distinção | Modelo principal de erro de leitura e matriz de calibração; orçamento inclui calibração, com sua incerteza. Critério combina equivalência com o exato e separação da PSA. Ruído de portas e extrapolação a ruído zero ficam como extensão separada. |
| E-mails no cabeçalho | Configuração preparada em `emails.json`; campos vazios por decisão do autor, que os preencherá depois. |

Comentários específicos do PR: [resumo](https://github.com/leonardovbf/correlacoes-tres-neutrinos/pull/5#discussion_r4492943385), [abstract](https://github.com/leonardovbf/correlacoes-tres-neutrinos/pull/5#discussion_r4492960999) e [pedido de reavaliação integral](https://github.com/leonardovbf/correlacoes-tres-neutrinos/pull/5#pullrequestreview-5800763982).

## Decisões para a próxima etapa

Os valores de 1.024 trajetórias iniciais, cinco sementes, passo de Trotter 0,05 e orçamentos de 1.024 a 8.192 medições são propostas de planejamento, não resultados nem configurações já validadas. O piso de normalização também é uma escolha operacional, com análise de sensibilidade prevista. O piloto deverá verificar viabilidade e precisão antes do pré-registro confirmatório.

Continuam a ser definidos no protocolo executável: Hamiltoniano e configuração publicada de referência, distribuição das frequências e sabores, malhas e janelas, conjuntos de observáveis, tolerâncias, margens de equivalência, nível de confiança, medida de tendência de H1, frequência mínima de sucesso de H2 e tratamento de comparações múltiplas. A ausência de resolução estatística será reportada como inconclusiva. Esta revisão não incorpora resultados ou alterações do desenvolvimento paralelo em `feat/system`.

A revisão textual e as propostas metodológicas devem passar pela leitura final dos autores, conforme a responsabilidade autoral indicada no parecer. A declaração de assistência de IA permanece explícita nos manuscritos.

## Composição e verificação

O gerador `scripts/gerar_revisao_sbc.py` compõe os dois manuscritos com Pandoc e Tectonic. Os arquivos em `sbc/` preservam o estilo histórico SBC identificado no próprio cabeçalho como criado em 2001 e atualizado em março de 2005; não são apresentados como uma edição recente do template. Mantêm A4, margens superior de 3,5 cm, inferior de 2,5 cm e laterais de 3 cm, e corpo Times de 12 pontos. Foram preservados os avisos dos arquivos de estilo; apenas os finais de linha e espaços finais foram normalizados.

O limite de dez linhas segue a orientação do parecer e as [instruções do template SBC](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr). Os dois resumos são compostos na primeira página. As medidas de extensão da introdução registradas para a entrega anterior não foram reutilizadas como validação desta revisão.

Referências consultadas para a revisão: [Riccio e Balantekin](https://arxiv.org/abs/2607.28619), [Sarmah et al.](https://arxiv.org/abs/2606.06580) e [Lacroix et al.](https://arxiv.org/html/2409.20215v2).

Verificação em 6/11/2026: ambos os PDFs têm dez páginas. Resumo e abstract ocupam dez linhas cada na primeira página, em ambas as versões. As vinte páginas foram renderizadas e inspecionadas; os logs finais não contêm citações indefinidas, glifos ausentes ou avisos de caixas excedendo as margens. Os PDFs contêm as três figuras e as 17 referências citadas. Os e-mails vazios não aparecem no cabeçalho.
