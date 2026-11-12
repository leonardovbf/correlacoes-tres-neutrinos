# Correlações de dois e três corpos em sistemas de neutrinos

Projeto sobre a precisão da aproximação de espaço de fase em oscilações coletivas de neutrinos e sobre a capacidade de circuitos quânticos de distinguir suas previsões da evolução exata. O estudo adota dois sabores, energias distintas e interações entre todos os pares.

O [artigo em português](ARTIGO.md) foi revisado para a entrega final, com Resultados, Discussão, análise das hipóteses, limitações, Conclusão e trabalhos futuros. A [revisão de 11 de novembro](analysis/REVISAO_FINAL_20261111.md) confronta o texto com o feedback dos professores, distingue as propostas de edição e registra as limitações da inferência. A composição SBC é gerada por `python3 scripts/compilar_artigo.py`; instruções e fontes estão em [artigo/](artigo/README.md).

## Plataforma local de simulação

A aplicação está dividida em [`app/frontend/`](app/frontend/) (**Next.js**, React e
TypeScript) e [`app/backend/`](app/backend/) (**FastAPI**, Python). O backend usa
o motor científico em [`src/neutrinos/`](src/neutrinos/) e grava automaticamente
cada execução em `results/`, com manifesto, configuração, versões das
dependências, hashes do código, momentos e amostras brutas. Cada atualização
cria uma revisão e troca o ponteiro `current` de forma atômica.

A interface tem cinco áreas: **Quadro**, **Clássica**, **Quântica**, **Sistema** e
**Qualidade**. No quadro, cada neutrino acrescentado cria uma variável de Bloch
e um qubit no modelo digital. É possível definir o sabor inicial, o peso da
frequência e o acoplamento de cada par; os pesos são normalizados para média
`ω̄ = 1`. O painel de execução recebe eventos reais do backend e permite abrir
o código Python de cada etapa. O andamento aparece em todas as telas. Ao
terminar, a aplicação mostra a comparação clássica ou quântica solicitada;
quem abriu o painel de execução durante o cálculo permanece nele. O controle
temporal no quadro reproduz os estados salvos, atualizando cartões e gráficos. **Sistema**
mostra rede, vetores de sabor, campos, correlações de pares e cumulantes de
trios. **Qualidade** reúne invariantes, convergência e proveniência.

### Instalação e execução

Requer Python 3.11+ e Node.js 20.9+. Na raiz do repositório:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[qiskit,test]'
npm ci --prefix app/frontend
bash scripts/dev.sh
```

Para usar **hardware IBM Quantum**, preencha `IBM_QUANTUM_API_KEY` no arquivo
`.env` da raiz. `IBM_QUANTUM_INSTANCE` (CRN) é opcional, mas recomendado; você
também pode definir `IBM_QUANTUM_BACKEND` como sugestão de dispositivo. O arquivo
`.env` é ignorado pelo Git e a chave é lida apenas pelo backend Python. Depois
de preencher, reinicie `scripts/dev.sh`. Na tela **Quântica**, execute primeiro
o circuito local, consulte os dispositivos e escolha um instante para enviar
ao hardware. Cada envio cria um job real na IBM e pode consumir créditos. O
resultado e as contagens são gravados em `results/` junto ao experimento.
Jobs pendentes são consultados automaticamente a cada 5 segundos enquanto a
plataforma está aberta. Na tela **Quântica**, use **Atualizar agora** para
consultar o mesmo job manualmente; não é preciso reenviar o circuito. Quando a
IBM informar `DONE`, a plataforma salva as contagens e mostra a estimativa e
o intervalo de confiança no cartão do job.
Consulte a [documentação de credenciais da IBM](https://quantum.cloud.ibm.com/docs/en/guides/initialize-account)
para criar a chave e encontrar o CRN.

Abra `http://127.0.0.1:3000`. O script inicia a API em `127.0.0.1:8000` e o
Next.js em `127.0.0.1:3000`; `Ctrl+C` encerra ambos. A documentação interativa
da API fica em `http://127.0.0.1:8000/docs`. Para iniciar separadamente:

```sh
PYTHONPATH=src .venv/bin/python -m uvicorn app.backend.api:app --host 127.0.0.1 --port 8000
npm run dev --prefix app/frontend
```

Monte o cenário no quadro e execute a clássica. A tela **Clássica** mostra a
comparação com a solução exata e oferece a próxima etapa. Depois execute o
circuito quântico para a mesma configuração (até 8 neutrinos). A referência clássica
aceita de 2 a 16 neutrinos. Use
[`configs/cenario_exemplo.json`](configs/cenario_exemplo.json) como modelo para
carregar parâmetros explícitos de um artigo. O quadro aceita estados iniciais
`νₑ` e `νₓ`; estados produto em superposição podem ser enviados diretamente à
API via `initial_bloch_values`. Ao atualizar a página, a última
execução é recuperada pelo identificador salvo no navegador.

### Verificação

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
npm run typecheck --prefix app/frontend
npm run build --prefix app/frontend
```

**Escopo atual:** a PSA usa a amostragem bi-valuada de Lacroix et al. (2024)
para estados iniciais produto, um neutrino por feixe. A tela quântica
executa um simulador local de estado. A simulação de um instante com ruído de
portas no Qiskit Aer continua disponível pela API. A execução IBM mede um
único instante por job em hardware real; ela ainda não valida H2 sob ruído
calibrado. A reprodução publicada e os controles suplementares constam do pacote concluído. A interpretação dos intervalos bootstrap e os critérios confirmatórios de H1/H2 continuam sujeitos à revisão descrita no artigo.
Para inserir os parâmetros de um benchmark, copie o cenário de exemplo e
carregue o JSON no painel de parâmetros. A matriz `g_values` é simétrica, com diagonal zero; confira a
normalização e a convenção de sabor do artigo antes de comparar curvas.
As frequências `omega_values` devem estar em unidades de `ω̄`, com média 1;
`mu` e o tempo da interface usam a mesma escala adimensional.
`initial_bloch_values` permite estados produto em superposição, usando um vetor
unitário `[x, y, z]` por neutrino. Alguns casos publicados usam termos ou
estados além desse recorte e exigirão ampliar o motor antes de reprodução fiel.

## Arquivos

| Arquivo ou diretório | Conteúdo |
| --- | --- |
| [ARTIGO.md](ARTIGO.md) | Texto principal em português, com contexto astrofísico, fundamentação teórica, revisão bibliográfica e referências unificadas. |
| [ARTIGO.eng.md](ARTIGO.eng.md) | Versão histórica em inglês, anterior à revisão final em português; não é uma tradução sincronizada. |
| [PLANO_TECNICO.md](PLANO_TECNICO.md) | Proposta de arquitetura, etapas do experimento, validações e decisões metodológicas pendentes. |
| [app/frontend/](app/frontend/) | Interface Next.js com gráficos e visualizações interativas. |
| [app/backend/](app/backend/) | API Python, orquestração e armazenamento versionado. |
| [src/neutrinos/](src/neutrinos/) | Motor compartilhado de evolução e observáveis. |
| [app.py](app.py) | Interface Streamlit anterior, mantida temporariamente para consulta. |
| [referencias.bib](referencias.bib) | Base BibTeX preservada, com 33 fontes citadas na revisão final e registros adicionais de apoio. |
| [figuras/](figuras/) | Diagramas em português, em SVG editável e PNG. |
| [figuras/en/](figuras/en/) | Os mesmos diagramas com os rótulos em inglês. |
| [figuras/gerar_diagramas.py](figuras/gerar_diagramas.py) | Código que gera as duas versões das figuras. |

## Contribuições da entrega

A introdução reúne o contexto astrofísico, a lacuna, a pergunta, o objetivo e as hipóteses. A fundamentação teórica apresenta o Hamiltoniano coletivo, os cumulantes conectados, o campo médio, a PSA, a trotterização, as medições, o ruído e a mitigação de leitura. A revisão bibliográfica compara os trabalhos relacionados e delimita a lacuna. A metodologia e os resultados preservam a versão da coleta: comparação com o exato, controle das fontes de erro, avaliação dos cumulantes e limitações da inferência sobre H1 e H2.

## Figuras

O acervo abaixo conserva a numeração original dos arquivos. No artigo, as figuras são 1 (colapso), 2 (correlações conectadas), 3 (PSA), 4 (medições) e 5 (comparação quântica); o protocolo de comparação e o critério de resolução ficam como material de apoio.

1. **Colapso estelar:** cortes esquemáticos do núcleo, do choque e da região de aquecimento por neutrinos.
2. **Correlações conectadas:** decomposição de um momento de três partículas em médias, contribuições dos pares e cumulante do trio.
3. **Protocolo de comparação:** modelo comum, quatro métodos de evolução, observáveis e controles das fontes de erro.
4. **Critério de resolução:** equivalência com o exato e distinção da PSA, em exemplos conceituais.
5. **Resultados PSA:** diferença entre erros normalizados de trios e pares, com os intervalos registrados.
6. **Orçamento de medições:** erro dos circuitos ideais nos três orçamentos avaliados.
7. **Comparação quântica:** exato, PSA, Aer e IBM no caso principal, com e sem mitigação.

Para regenerar os diagramas conceituais (figuras 1–4), executar na raiz do repositório, com Python 3.11 ou superior e `uv` instalado:

```sh
uv run figuras/gerar_diagramas.py
```

Para gerar somente uma língua:

```sh
uv run figuras/gerar_diagramas.py --idioma pt
uv run figuras/gerar_diagramas.py --idioma en
```

O script exporta os diagramas conceituais com largura de 170 mm e PNG a 450 dpi; a composição SBC ajusta-os a 150 mm. As figuras de resultados (5–7) são geradas por `uv run figuras/gerar_resultados.py`, a partir dos CSVs do pacote auditado, já com 150 mm de largura.

## Conferência no modelo SBC

Na conferência de 23 de outubro de 2026, a introdução foi compilada e inspecionada no modelo SBC, com fonte Times de 12 pontos, coluna de 150 mm e altura útil de 237 mm. A extensão foi medida entre o início de cada subseção e o início da seguinte, somando as alturas ocupadas nas páginas sucessivas.

| Versão | Contexto, Figura 1 e legenda | Estado da arte até a lacuna |
| --- | --- | --- |
| Português | 1,45 página equivalente | 1,29 página equivalente |
| Inglês | 1,43 página equivalente | 1,27 página equivalente |

Na versão conferida naquela data, as duas partes atenderam à extensão de 1 a 1,5 página no modelo usado, com o parágrafo final de objetivo e contribuição contado separadamente. Essas medidas são um registro da versão anterior à revisão estrutural e não validam a extensão da versão atual. A nova composição com resultados e sua paginação estão documentadas na seção "Artigo com resultados" abaixo.

## Referências e edição

As listas de referências dos artigos contêm somente as fontes citadas, em ordem alfabética e com apresentação uniforme. A base BibTeX mantém também quatro leituras complementares para o desenvolvimento da pesquisa. Ao acrescentar uma citação, atualizar a lista do artigo e o registro correspondente em `referencias.bib`.

Manter as versões em português e inglês alinhadas quanto ao escopo, às hipóteses, às condições de comparação e às legendas. Para alterar os desenhos, editar o gerador e regenerar as imagens antes de revisar sua leitura no artigo.

## Coleta dos experimentos

O roteiro completo de ambiente, execução das 11 fases, retomada, análises e
extensão IBM está em [EXECUTAR_EXPERIMENTOS.md](EXECUTAR_EXPERIMENTOS.md).

```sh
.venv/bin/python scripts/run_study.py plan
.venv/bin/python scripts/run_study.py smoke --output results/validacao-software
.venv/bin/python scripts/run_study.py run
```

O smoke valida o software e mantém seus resultados separados da coleta oficial.

## Resultados do artigo

O [pacote de resultados para escrita e avaliação](analysis/article_packages/20261106T120036Z-7f9b932d0594/README.md)
reúne tabelas, figuras selecionadas, relatórios completos e hashes das fontes
da coleta local final e dos 80 jobs IBM. O pacote está versionado no repositório;
o arquivo integral `results/` permanece separado por conter todas as tentativas,
contagens e matrizes necessárias para reproduzir cada execução.

A [confirmação com seis e oito qubits](analysis/campaigns/20261110-hardware-confirmation/README.md) foi concluída em 10 de novembro. O plano anterior permanece como registro histórico, e o artigo distingue a confirmação dos pilotos.

Para gerar outro pacote a partir de registros concluídos:

```sh
.venv/bin/python analysis/prepare_article_package.py results/studies/ID/study.json results/protocols/ID/hardware_analysis.json --output analysis/article_packages/NOVO-ID
```


## Artigo para a entrega final

O texto atual em português recebeu uma revisão pontual, preservando a introdução, os gráficos e a organização das tabelas. A Discussão e as partes do encerramento foram identificadas a partir dos parágrafos existentes. A versão integral em inglês permanece histórica; o resumo e o abstract do artigo português estão alinhados.

Os dois gráficos existentes foram mantidos na composição, com seus arquivos vetoriais. A revisão não substitui a validação de autoria e conteúdo pelos autores.

O [registro da revisão pontual](analysis/REVISAO_FINAL_20261111.md) identifica os trechos ajustados e a razão de cada mudança. Os seis ZIPs da campanha `20261109-feedback-v4` foram restaurados dos arquivos locais e coincidem com o manifesto original. Devem acompanhar a entrega do repositório.

O PDF é gerado em `output/pdf/artigo-revisado-sbc.pdf`, diretório ignorado pelo Git. O fonte editorial é `ARTIGO.md`, e `scripts/compilar_artigo.py` gera o LaTeX em `artigo/`. As fontes de composição e a adaptação de compatibilidade do modelo estão documentadas em [artigo/README.md](artigo/README.md).
