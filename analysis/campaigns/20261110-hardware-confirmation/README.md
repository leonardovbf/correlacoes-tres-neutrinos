# Confirmação IBM N=6/8 — 10 de novembro de 2026

Execução do [plano de confirmação](../20261109-feedback-v4/hardware_confirmation_plan.json) em `ibm_kingston`: 20 jobs, dois PUBs por job (N6 e N8), 4.096 shots por PUB e 32 randomizações × 128 shots. Total de 163.840 shots, exatamente o teto autorizado. Todos os jobs terminaram (`DONE`), nenhum foi reenviado ou substituído. Os IDs, as janelas e o procedimento de execução estão no [registro da execução](../../HARDWARE_CONFIRMACAO_20261110.md).

Os dados são independentes dos pilotos: os mesmos dois pontos físicos e QPYs arquivados, sem seleção a partir dos novos resultados.

## Resultado

Bootstrap conjunto dos 20 jobs (10.000 reamostragens), com quatro intervalos bilaterais simultâneos de 98,75% (Bonferroni, α familiar = 0,05). O critério de sucesso exige que o limite superior da diferença de erro absoluto fique abaixo de zero nas quatro comparações.

| N | C₃ no hardware | IC 98,75% | C₃ exato | C₃ da PSA | Δ erro vs PSA | Δ erro vs C₃=0 |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| 6 | 0,1837 | [0,1733; 0,1931] | 0,4145 | 0,1367 | −0,0470 [−0,0564; −0,0365] | −0,1837 [−0,1932; −0,1733] |
| 8 | −0,0281 | [−0,0377; −0,0180] | −0,1308 | 0,0502 | −0,0783 [−0,0879; −0,0682] | −0,0281 [−0,0377; −0,0180] |

As quatro comparações passam: nos dois pontos, o hardware erra menos que a PSA completa e menos que a previsão C₃=0.

## Como ler

- **Menor erro não é reprodução do exato.** O hardware recupera cerca de 44% do C₃ exato em N=6 e cerca de 21% em N=8, com o sinal correto. O N=8 de dois passos não foi declarado equivalente ao exato em ±0,01.
- **A comparação com C₃=0 em N=8 equivale a testar o sinal de C₃.** Para um exato negativo, estar mais perto do exato que o zero significa C₃<0.
- **Cinco janelas não são cinco repetições independentes.** As médias por janela derivam (N6: 0,190; 0,193; 0,195; 0,167; 0,172. N8: −0,029; −0,045; −0,034; −0,022; −0,012). O bootstrap sobre os 20 jobs inclui essa variação entre blocos, mas não a modela. Uma média simples com intervalo t sobre os 20 blocos é um pouco mais larga e leva às mesmas quatro conclusões.
- **Janelas e identificação de calibração.** Uma janela é nova quando os parâmetros calibrados dos qubits e portas realmente usados mudam. A janela 0 foi capturada com a primeira definição dessa identificação, que incluía carimbos operacionais. Após os quatro primeiros jobs, a definição passou a ignorar esses carimbos e a ordem dos registros; plano físico, circuitos, IDs e orçamentos não mudaram. O estado preserva `legacy_fingerprint` e `implementation_update`, e os arquivos anteriores estão em `bookkeeping_history/` dentro do ZIP.
- **Escopo.** Dois pontos fixos, sem mitigação de leitura nem desacoplamento dinâmico. Não é teste controlado de escala em N nem vantagem quântica computacional.

## Arquivos

- [data.zip](data.zip): pasta completa da execução (97 arquivos): contagens por PUB, programas enviados e recuperados, metadados Runtime, as cinco calibrações, estado, plano de execução, análise e log.
- [archives.json](archives.json): SHA-256 do ZIP e de cada arquivo interno.
- [analysis.json](analysis.json): resultado acima, cópia do arquivo gerado pelo executor.

## Verificar sem IBM

Na raiz do repositório, extraia e confira os hashes:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, zipfile
release = Path('analysis/campaigns/20261110-hardware-confirmation')
target = Path('results/hardware-confirmation-20261110')
manifest = json.loads((release/'archives.json').read_text())
assert hashlib.sha256((release/manifest['file']).read_bytes()).hexdigest() == manifest['sha256']
target.mkdir(parents=True, exist_ok=True)
zipfile.ZipFile(release/manifest['file']).extractall(target)
for name, digest in manifest['files_sha256'].items():
    assert hashlib.sha256((target/name).read_bytes()).hexdigest() == digest
print('Dados extraídos e verificados.')
PY

PYTHONPATH=src .venv/bin/python scripts/run_feedback_hardware.py verify
```

`verify` confere 20 IDs distintos, orçamento, ordem dos PUBs, shots por PUB, hashes das contagens e das calibrações, cinco janelas distintas, e recalcula a análise a partir das contagens, comparando com `analysis.json`. Não consulta a IBM.
