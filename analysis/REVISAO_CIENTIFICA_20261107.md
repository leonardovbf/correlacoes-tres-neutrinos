# Revisão científica e experimental — 7 de novembro de 2026

A linha de pesquisa é boa e merece continuidade. A contribuição mais sustentada é delimitar a fidelidade da PSA para cumulantes conectados de terceira ordem, com referência exata e controle das fontes de erro. A extensão em hardware fica mais convincente como investigação das condições para resolver esses desvios. Os resultados disponíveis ainda não estabelecem vantagem computacional quântica nem confirmação global de H1/H2.

Examinei o artigo, protocolos, implementação científica, relatórios do pacote final, contagens da triagem IBM de circuitos curtos e literatura relacionada. Executei os 64 testes automatizados: todos passaram. Também conferi os 42 arquivos e as 28 fontes listados no manifesto do pacote: todos os hashes coincidiram. A auditoria adicional está em [research_review_20261107.json](audits/research_review_20261107.json), com código em [review_research.py](review_research.py). Os resultados e protocolos da coleta foram preservados; os cálculos desta revisão foram locais.

**Posicionamento na literatura.** Lacroix et al. validaram a PSA multifeixes e examinaram médias e correlações coletivas; a comparação individual dos trios é uma extensão pertinente. Illa e Savage já mediram correlações de dois e três corpos em hardware, portanto essa medição isolada não constitui a novidade. O foco defensável é a comparação PSA–exato por trio, com regimes de validade e orçamento de erro. A busca realizada sustenta esse posicionamento, mas não equivale a uma revisão sistemática que prove prioridade absoluta. Fontes: [Lacroix et al. (2024)](https://arxiv.org/html/2409.20215v2), [Illa e Savage (2023)](https://arxiv.org/abs/2210.08656).

O fechamento BBGKY recente é um comparador adicional interessante: nele os cumulantes de terceira ordem são anulados, embora médias e pares possam melhorar. Compará-lo com a PSA ajudaria a distinguir a qualidade das previsões de ordens diferentes; implementá-lo exige adaptar e validar as equações no mesmo modelo de dois sabores. Fonte: [Riccio e Balantekin, preprint v2 (2026)](https://arxiv.org/html/2607.28619v2).

**O que os experimentos já sustentam.**

| Parte | Evidência disponível | Interpretação sustentada |
| --- | --- | --- |
| Validação | Reprodução publicada, referência densa independente, refinamento RK4 e equivalência Qiskit–emulador; emendas preservadas. | Boa base de verificação numérica. A reprodução publicada é de médias de sabor extraídas de uma figura. |
| H1 | IC percentil de R₃−R₂ positivo em 14/15 células principais e 10/10 na extensão. | Padrão descritivo consistente de maior erro **relativo ao sinal** dos trios; a inferência global precisa de auditoria. |
| Medições ideais | Redução do RMSE de aproximadamente quatro vezes ao multiplicar os shots por dezesseis. | Compatível com predominância de flutuação de medição nessa faixa. |
| H2 v1 | Aer/IBM próximos de zero no caso cujo exato é −0,315784. | O procedimento usado não recupera o cumulante na margem ±0,01. O limiar de ruído não foi estimado. |
| Circuitos curtos v2 | Triagem IBM concluída, 20 jobs, 81.920 shots, quatro braços. | Sinal exploratório favorável ao circuito de dois passos; confirmação independente ainda não aparece nos registros locais examinados. |

**Melhoria imediata: retirar o erro Monte Carlo dos casos pequenos da PSA.** Cada neutrino tem duas componentes transversais com dois valores possíveis. A distribuição inicial tem exatamente 4ᴺ configurações equiprováveis: 256 para N=4, 4.096 para N=6 e 65.536 para N=8. É possível integrar cada configuração uma vez e agregar seus momentos com pesos iguais. Isso calcula a média da distribuição discreta completa da PSA; não transforma a PSA em evolução quântica exata e continua tendo custo exponencial para N grande.

Fiz essa enumeração para as cinco interações em N=4. A tabela usa RK4 refinado, mantendo a janela 0≤τ≤10:

| μ | R₂, suporte completo | R₃, suporte completo | D=R₃−R₂ |
| ---: | ---: | ---: | ---: |
| 0,1 | 0,674341 | 0,588748 | −0,085593 |
| 0,3 | 0,541085 | 0,807830 | 0,266745 |
| 1 | 0,722221 | 1,159391 | 0,437170 |
| 3 | 0,417774 | 0,946854 | 0,529080 |
| 10 | 0,485249 | 1,086357 | 0,601108 |

O padrão principal de N=4 persiste sem amostragem: quatro diferenças positivas e uma negativa. O maior desvio em C₃ entre 12 e 24 subpassos foi 2,70×10⁻⁸. Para N=6/8, o suporte completo é menor que as 81.920 trajetórias já usadas por célula, tornando essa estratégia especialmente atraente como controle adicional. Esta revisão não executou a enumeração nesses dois tamanhos. Em N=12/16, manter Monte Carlo e controles específicos de precisão é mais realista.

**Prioridade estatística de H1.** A reamostragem atual preserva corretamente momentos, tempos e dependência dentro dos blocos. Entretanto, cinco estimativas ficam fora dos próprios ICs percentis: N=8, μ=0,1; N=12/16, μ=0,1 e 0,3. Isso não prova, por si só, erro de programação: intervalos percentis podem excluir a estimativa quando a distribuição bootstrap é enviesada. O problema prático é a cobertura não demonstrada de uma estatística não linear com sinal pequeno.

Em N=8, μ=0,1, D=0,484820, o IC é [0,509705; 0,800133] e a média bootstrap desloca-se +0,151347. Em N=16, μ=0,1, o deslocamento é +0,735729, cerca de 3,34 desvios-padrão bootstrap. O piso de normalização 10⁻⁴ evita divisão por sinais quase nulos em termos absolutos, mas não assegura resolução em relação ao erro Monte Carlo.

Recomendo validar a cobertura usando o suporte completo como população conhecida em N=4 e, se viável, N=6/8: gerar campanhas independentes com os mesmos tamanhos de bloco, aplicar os intervalos candidatos e medir cobertura e viés. Comparar percentil, basic e BCa é uma análise de sensibilidade; escolher automaticamente BCa não resolve a questão. A [documentação do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) descreve essas alternativas e o pareamento. Manter os intervalos originais arquivados e versionar a reanálise.

Há três ajustes adicionais para a interpretação de H1:

- O estimador `h1()` compara C₂ e C₃; ele não fornece um teste completo da parte de H1 que envolve probabilidades individuais. Acrescentar avaliação explícita de Pₑ ou restringir a conclusão à comparação realmente analisada.
- Maior erro normalizado não significa sempre maior erro absoluto. Em N=8, μ=3, E₃≈0,0551 é menor que E₂≈0,0690, embora R₃≈0,732 seja maior que R₂≈0,226.
- Incluir a referência C₃=0, cujo R₃ é exatamente 1. A PSA tem R₃≥1 em cinco células principais registradas. Para N=4, μ=1 e 10, isso persiste na enumeração completa: nesses casos ela é pior, pela métrica usada, que prever cumulante nulo.

Os 201 tempos e os vários trios não são replicações independentes. Para afirmações simultâneas nas células, usar um procedimento definido para multiplicidade, como intervalos simultâneos ou testes com ajuste de Holm. Uma conclusão agregada deve declarar a população de configurações e a relevância prática; contar ICs positivos não demonstra validade geral da hipótese.

**Fragilidade concreta do critério de H2 v1.** Em [study_analysis.py](../src/neutrinos/study_analysis.py), o critério exige distinção estatística circuito–PSA e equivalência circuito–exato em ±0,01. Ele não exige que a PSA esteja fora dessa margem nem que o circuito seja mais preciso que a PSA.

Na célula μ=0,1, τ=1, m=16.384, o exato é aproximadamente +0,00005097, a PSA −0,00003954 e o circuito bruto −0,00364575. O relatório marca `raw_resolves=True`, embora o erro absoluto do circuito seja aproximadamente 0,00369672, contra apenas 0,00009050 da PSA: o circuito é cerca de 41 vezes pior nesse ponto. A regra permite isso porque o circuito ainda cabe na margem relativamente larga de equivalência. As duas classificações `refutada_nesta_condicao` da tabela são análises secundárias; esse problema não muda o fracasso de recuperação do caso principal.

Para novos desenhos, exigir uma diferença PSA–exato de relevância previamente fixada e comparar diretamente os erros:

> D = |C₃_circuito − C₃_exato| − |C₃_PSA − C₃_exato|.

Superioridade pontual corresponde a D<0 com incerteza controlada. Equivalência ao exato é um objetivo adicional, mais forte. A v2 já adota D, o que melhora o desenho. Não reclassificar retrospectivamente o teste original com uma regra escolhida após seus resultados.

**Ruído: o limitante atual é o viés de portas.** A auditoria anterior verificou circuitos Aer com 4.032 CX e saída praticamente maximamente mista. A repetição de contagens entre células com a mesma semente é compatível com essa saturação; não oferece replicações independentes entre células. Aumentar shots estreita o intervalo em torno de um valor errado. A mitigação de leitura não reconstitui a informação destruída durante as portas.

H2 trata de limiar de ruído, mas os perfis leve e moderado alteram simultaneamente erros de uma porta, de duas portas e de leitura. A grade ainda usa profundidades diferentes em algumas células. Para medir um limiar, fixar o caso físico, o circuito e o orçamento; variar separadamente leitura e portas, com vários níveis próximos da transição. No Aer, calcular primeiro os valores esperados pela matriz densidade, sem flutuação de shots, e depois estudar a capacidade de decisão com medições finitas. Isso separa viés físico e poder estatístico e evita repetir grandes grades já saturadas.

**A triagem v2 é a direção experimental mais promissora.** Os valores abaixo vêm do relatório concluído em 6 de novembro, horário de São Paulo. Cada braço tem cinco jobs e 20.480 shots. No mesmo ponto, C₃_exato=−0,1586845 e C₃_PSA=−0,0512157:

| Circuito / condição | Estimativa IBM | Erro absoluto | IC95 registrado de D |
| --- | ---: | ---: | --- |
| 2 passos, sem twirling | −0,0830471 | 0,0756374 | [−0,049865; −0,014922] |
| 2 passos, com twirling | −0,0972654 | 0,0614191 | [−0,069113; −0,026220] |
| 6 passos, sem twirling | −0,0398082 | 0,1188763 | [−0,004752; 0,026936] |
| 6 passos, com twirling | −0,0580590 | 0,1006255 | [−0,032125; 0,014757] |

O braço selecionado reduz o erro pontual em aproximadamente 43% frente à PSA dessa triagem. Ainda está a aproximadamente 0,0614 do exato, acima da margem original de 0,01. Trata-se de melhora relativa exploratória, sem demonstração de recuperação exata ou de vantagem computacional. Tampouco foi estabelecida uma diferença estatística entre twirling e ausência de twirling.

O plano de compilação registra 78 portas de dois qubits e profundidade 294 no candidato de dois passos, contra 219 e 801 no de seis. Os layouts diferem entre candidatos, de modo que o efeito observado não isola exclusivamente a profundidade. A [documentação IBM](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques) explica que twirling altera a estrutura do ruído e pode ajudar com erros coerentes; não garante recuperação de sinal. O resultado mais preciso do circuito mais curto ilustra a necessidade de otimizar o erro total, não apenas o erro ideal de Trotter.

Conferi também a precisão da PSA v2: reduzir a grade a dois pontos faz o RK4 usar Δτ=0,125. Comparando o suporte completo com DOP853 independente, o maior desvio de C₃ foi 6,45×10⁻⁶; nos vinte blocos efetivamente arquivados, o máximo foi 9,47×10⁻⁶. A reconstrução dos blocos pela distribuição discreta coincidiu com os dados a 1,71×10⁻¹⁵. Assim, esse erro de integração não explica a vantagem observada. A PSA sem erro de amostragem nesse ponto vale −0,0543949, ainda bem mais distante do exato que a estimativa IBM selecionada.

**A incerteza do hardware precisa de uma escolha explícita de modelo.** A v1 agrega contagens e usa multinomial, supondo uma distribuição estacionária entre jobs. Já `_analyze_arm()` da v2 reamostra jobs e, dentro deles, novas contagens multinomiais; também usa os mesmos índices para PSA e IBM, embora o número de semente PSA não crie um pareamento físico com o dispositivo. Em um cenário estacionário, a combinação pode contar duas vezes parte da flutuação de shots. Se há deriva, a agregação pura pode subestimá-la. Nenhuma das duas opções deve ser adotada apenas por produzir o intervalo desejado.

Na revisão, comparei as contagens com multinomial agregado e com reamostragem apenas de jobs. Para dois passos com twirling, os ICs de C₃ foram, respectivamente, [−0,10982; −0,08422] e [−0,11282; −0,08135]. São sensibilidades com apenas cinco jobs, não novos intervalos confirmatórios de D. Validar cobertura com dados simulados, modelar deriva e registrar a análise antes da confirmação. Na coleta futura, distribuir os blocos em janelas de calibração e intercalar ou aleatorizar condições quando houver comparação entre braços.

**Ordem recomendada de trabalho.**

| Prioridade | Ação | O que resolve |
| --- | --- | --- |
| 1 | Enumerar a PSA em N=6/8; validar a cobertura dos ICs de H1; incluir erros absolutos, C₃=0 e Pₑ. | Distingue falha da aproximação de erro de amostragem e fecha a principal pendência do artigo. |
| 2 | Fixar a análise de incerteza v2 e manter o candidato selecionado para confirmação independente. | Testa se a melhora pontual sobre a PSA se repete, sem reutilizar dados da seleção. |
| 3 | Redesenhar localmente a varredura de ruído com circuito fixo e leitura/portas separadas. | Permite investigar o limiar de H2 com custo controlado. |
| 4 | Testar robustez a estado inicial e geometria angular antes de ampliar N no hardware. | Verifica se a conclusão depende da ordenação frequência–sabor e do caso de ângulo único. |
| 5 | Adicionar mecanismo e custo à análise: tempos de perda de precisão, componentes mistas dos cumulantes e tempo/memória clássicos. | Aumenta o conteúdo físico e permite comparar utilidade e recursos. |

Para a robustez física, uma grade pequena pode combinar estado de domínio e alternado, mantendo as mesmas frequências, e uma geometria multiangular com gᵢⱼ=1−vᵢ·vⱼ. Declarar a normalização dos acoplamentos para comparar μ. Examinar tanto janelas fixas em ω̄t quanto em μt: na grade atual, variar μ com τ final fixo também varia o número de tempos de interação observados. Isso não invalida a grade, mas limita atribuir a tendência somente à intensidade do acoplamento.

Como resultado físico adicional, definir antecipadamente um tempo de perda de precisão com tolerância absoluta e persistência mínima, evitando cruzamentos espúrios perto dos zeros de C₃. Mostrar distribuições por trio e separar trios por composição inicial. Se o objetivo for explicar a propagação de erros pela hierarquia, C₃ᶻᶻᶻ isolado não basta: examinar componentes mistas que entram nas equações e sua relação temporal com erros de pares e de sabor. Uma associação não demonstra causalidade.

**Ajustes de escrita.** O texto já distingue correlação de emaranhamento e reconhece as emendas e as limitações estatísticas. Manter essa cautela. Na descrição da amostragem, especificar que os segundos momentos locais reproduzidos são os **simetrizados**: em geral ⟨σᵃσᵇ⟩=δₐᵦ+iεₐᵦ𝚌nᶜ, enquanto o produto das variáveis clássicas é comutativo. Evitar a leitura de que um par inteiro está necessariamente emaranhado com o restante quando C₂≠0: um par de Bell fatorizado do restante é um contraexemplo. No estado global puro, a correlação não nula impede que cada um dos dois neutrinos esteja individualmente fatorizado do resto.

O README do pacote ainda contém o máximo Qiskit–emulador atribuído incorretamente ao controle de comprimento dos spins; o artigo já informa o valor correto 2,8021×10⁻¹². Corrigir isso em nova revisão identificada do pacote, preservando seu histórico. Para publicação, disponibilizar o arquivo científico necessário à reanálise, incluindo contagens, fontes e metadados, com identificador persistente. Um pacote de tabelas e hashes não substitui os dados ausentes.

Para reproduzir esta auditoria sem sobrescrever o registro:

```sh
PYTHONPATH=src .venv/bin/python analysis/review_research.py --output /private/tmp/nova-revisao-neutrinos.json
```

Essas verificações complementam a coleta existente; não repetem integralmente as onze fases, não estabelecem cobertura estatística por simulação e não verificam calibrações atuais do dispositivo. A recomendação científica é consolidar primeiro a comparação PSA–exato e a confirmação dos circuitos curtos. A expansão para mais qubits ganha valor depois que houver controle do viés e uma pergunta de escala que os dados consigam responder.
