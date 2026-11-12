# Extensão futura: 6 e 8 neutrinos na IBM

**Estado:** proposta para uma etapa posterior. Nenhum job IBM de N=6 ou N=8 foi enviado.

## Por que considerar a extensão

No modelo de dois sabores, cada neutrino ocupa um qubit. A coleta IBM concluída
representa **N=4** e mede o cumulante conectado K₃ do trio (0,1,2), com o
quarto neutrino interagindo com o trio. Isso responde ao caso principal H2
predefinido, mas não testa a escala de tamanho no hardware. O resultado H2
da coleta N=4 foi inconclusivo; a mitigação de leitura não recuperou K₃ exato.

As fases clássicas principais cobrem N=4, 6 e 8, com extensão N=12 e 16.
Os circuitos ideais e a medição finita cobrem N=4, 6 e 8. As grades locais de
ruído e mitigação T06/T07, assim como a IBM, cobrem apenas N=4. O resumo atual
de `ARTIGO.md` menciona circuitos de 4 a 8 neutrinos com ruído simulado:
antes da submissão, completar essa faixa ou ajustar o texto ao escopo medido.

## Prévia técnica, sem envio à IBM

Ponto comparado: μ=3, τ=2, 8 pontos temporais, 2 passos de Trotter por intervalo
(14 no total), estado inicial com metade νe/metade νx e frequências de 0,7 a
1,3. A comparação ideal usa o maior erro absoluto de K₃ entre tempos e trios.
Compilação preliminar no `ibm_kingston`, nível de otimização 1 e semente de
transpilação 60001. Os números de N=6/8 são estimativas de recursos, não
execuções físicas nem registros do protocolo oficial.

| N / qubits lógicos | Pares que interagem | Erro ideal máximo de K₃ | Profundidade compilada | Portas de 2 qubits |
| ---: | ---: | ---: | ---: | ---: |
| 4, coleta existente | 6 | 0,0007155 | 2.882 | 672 |
| 6, prévia | 15 | 0,0004707 | 5.986 | 1.947 |
| 8, prévia | 28 | 0,0003815 | 9.415 | 4.029 |

As três grades ideais ficaram abaixo da meta de erro 0,001, e as prévias de
profundidade ficaram abaixo do teto operacional 20.000. A calibração do backend
pode mudar; transpilar novamente antes de decidir a coleta. Mais portas e
qubits podem aumentar o efeito do ruído. O caso N=4 já não resolveu H2, de
modo que a expansão requer avaliação de viabilidade antes de consumir shots.

## Próxima sequência de trabalho

1. Definir uma **nova extensão exploratória**, separada da coleta oficial N=4.
   Fixar antecipadamente N, μ, τ, trio, sementes, shots, backend, versão do
   compilador, critérios de precisão e condição de parada. Preservar os dados
   e decisões originais.
2. Repetir o controle ideal e a prévia de recursos para N=6/8 com as
   calibrações do dia; arquivar circuitos QPY, layout, profundidade, portas e
   hashes. Testar primeiro N=6 com ruído local e avaliar se K₃ ainda é
   distinguível dentro das incertezas.
3. Decidir sobre uma pequena coleta física N=6 com orçamento declarado.
   Avaliar N=8 somente depois de analisar fidelidade, custo e interpretação
   do resultado N=6. Não tratar essa extensão como confirmação retroativa de H2.
4. Atualizar os resumos em português e inglês e as limitações do artigo para
   distinguir claramente simulação ideal, ruído local e hardware IBM.

Os resultados existentes e as emendas estão no
[pacote do artigo](article_packages/20261106T120036Z-7f9b932d0594/README.md).
O arquivo integral `results/` deve continuar preservado separadamente.
