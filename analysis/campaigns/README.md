# Pacotes científicos das campanhas

Os três pacotes completos são versionados em ZIP, mantendo contagens, probabilidades, circuitos, calibrações, fontes e manifestos originais. As pastas extraídas permanecem locais e são ignoradas pelo Git. O arquivo [archives.json](archives.json) registra hashes SHA-256 dos ZIPs e dos manifestos internos.

## 20261107-correlacoes-v3

[Baixar o pacote completo](20261107-correlacoes-v3.zip).

Fotografia da busca exploratória: 36 configurações com 4, 6 e 8 qubits, 61 tempos por configuração e PSA com suporte discreto completo. Inclui a varredura de ruído genérico, as emendas e o registro dos envios IBM. O estado dos jobs nesse pacote é histórico; os resultados concluídos estão no pacote seguinte.

## 20261108-resultados-ibm

[Baixar o pacote completo](20261108-resultados-ibm.zip).

Contém os resultados dos 30 jobs concluídos em `ibm_kingston`: 20 blocos de confirmação N=4 e cinco blocos para cada piloto N=6/8, totalizando 368.640 shots. A confirmação N=4 passou no critério original; N=6/8 continuam exploratórios. Os resultados favoreceram menor erro que a PSA nos pontos avaliados, sem demonstrar superioridade computacional.

## 20261108-aer-ibm-pareado

[Baixar o pacote completo](20261108-aer-ibm-pareado.zip).

Replay local dos programas dos 30 jobs, com os mesmos pontos físicos, mapeamento, gerador/política de twirling e orçamento de shots, usando as calibrações arquivadas. Nenhum novo job IBM foi enviado. Os cinco cenários locais usam 1.843.200 shots simulados no total.

Estimativas de C₃ com shots finitos, usando o modelo Aer calibrado completo:

| Qubits | Exato | Aer calibrado | IBM |
| ---: | ---: | ---: | ---: |
| 4 | −0,158685 | −0,081481 | −0,097087 |
| 6 | +0,414548 | +0,172019 | +0,194897 |
| 8 | −0,130788 | −0,012498 | −0,022495 |

O modelo de ruído é aproximado. O sorteio interno de twirling do servidor e o cronograma real de pulsos não estão disponíveis; são usados novos sorteios locais sob a mesma política. O relatório completo inclui intervalos, previsões sem flutuação de shots, limites do pareamento e a sensibilidade a tempos ociosos. Os 76 testes do projeto passaram na validação arquivada.

## Abrir os relatórios e reproduzir a análise

Na raiz do repositório, extraia os pacotes preservando a estrutura original:

```sh
python3 -m zipfile -e analysis/campaigns/20261107-correlacoes-v3.zip analysis/campaigns/
python3 -m zipfile -e analysis/campaigns/20261108-resultados-ibm.zip analysis/campaigns/
python3 -m zipfile -e analysis/campaigns/20261108-aer-ibm-pareado.zip analysis/campaigns/
```

Cada pasta extraída contém seu `README.md` completo, gráficos, dados e `manifest.json` original. Os arquivos descompactados não entram no Git. Os hashes dos arquivos internos podem ser conferidos pelo manifesto de cada pacote.

Para reanalisar o replay pareado já calculado, sem rede, após preparar o ambiente científico com `requirements-research.lock`:

```sh
mkdir -p results/paired-aer-ibm-20261108
cp analysis/campaigns/20261108-aer-ibm-pareado/capture_manifest.json results/paired-aer-ibm-20261108/
cp analysis/campaigns/20261108-aer-ibm-pareado/replay_plan.json results/paired-aer-ibm-20261108/
python3 -m zipfile -e analysis/campaigns/20261108-aer-ibm-pareado/replay_data.zip results/paired-aer-ibm-20261108/
PYTHONPATH=src .venv/bin/python analysis/run_paired_aer.py
```

Esse comando reutiliza os replays completos e refaz a análise local. Não envia jobs à IBM.
