# Confirmação IBM N=6/8 — registro da execução, 10 de novembro de 2026

A execução do plano de confirmação foi autorizada e concluída em `ibm_kingston`: **20 jobs, 40 PUBs e 163.840 shots**, o teto autorizado, sem reenvios nem substituições. Os resultados estão no [pacote da campanha](campaigns/20261110-hardware-confirmation/README.md); este arquivo registra o que foi executado e como.

## Jobs

Cada job tem dois PUBs (N6 e N8) de 4.096 shots, com twirling de 32 randomizações × 128 shots. A ordem dos circuitos alterna por bloco.

| Bloco | Janela | Ordem dos PUBs | Job IBM |
| ---: | ---: | --- | --- |
| 0 | 0 | N6, N8 | `dbpgs2lt7fqc7389dpl0` |
| 1 | 0 | N8, N6 | `dbpgs30ou4as73ctlcf0` |
| 2 | 0 | N6, N8 | `dbpgs3gou4as73ctlcg0` |
| 3 | 0 | N8, N6 | `dbpgs4c4148s739ujlng` |
| 4 | 1 | N6, N8 | `dbph1ioqtr0c738edj3g` |
| 5 | 1 | N8, N6 | `dbph1j8ou4as73ctlilg` |
| 6 | 1 | N6, N8 | `dbph1jtt7fqc7389dvmg` |
| 7 | 1 | N8, N6 | `dbph1k8qtr0c738edj60` |
| 8 | 2 | N6, N8 | `dbphdioou4as73ctm0a0` |
| 9 | 2 | N8, N6 | `dbphdjc4148s739uk940` |
| 10 | 2 | N6, N8 | `dbphdjoou4as73ctm0bg` |
| 11 | 2 | N8, N6 | `dbphdk8qtr0c738ee0s0` |
| 12 | 3 | N6, N8 | `dbphs7dt7fqc7389f0fg` |
| 13 | 3 | N8, N6 | `dbphs7tt7fqc7389f0h0` |
| 14 | 3 | N6, N8 | `dbphs8gqtr0c738eekcg` |
| 15 | 3 | N8, N6 | `dbphs90qtr0c738eekdg` |
| 16 | 4 | N6, N8 | `dbpi87dt7fqc7389fsjg` |
| 17 | 4 | N8, N6 | `dbpi8844148s739ulogg` |
| 18 | 4 | N6, N8 | `dbpi88lt7fqc7389fsn0` |
| 19 | 4 | N8, N6 | `dbpi8944148s739ulok0` |

## Janelas de calibração

Cada janela tem quatro jobs. A seguinte só foi liberada depois que os quatro jobs anteriores terminaram e a calibração dos qubits e portas realmente usados mudou. A identificação considera parâmetros calibrados e suas datas; ignora mudanças de status operacional e a ordem dos registros. Cada calibração está arquivada.

| Janela | Última atualização IBM (UTC−3) | Capturada (UTC) | Identificação |
| ---: | --- | --- | --- |
| 0 | 09:15 | 12:28 | `670b24c906ea` |
| 1 | 09:34 | 12:40 | `edfcffc51cd3` |
| 2 | 09:48 | 13:06 | `85b3d870bae5` |
| 3 | 10:20 | 13:37 | `9d6495a4d7b5` |
| 4 | 10:53 | 14:03 | `007931fae141` |

A janela 0 foi capturada com a primeira definição dessa identificação, que incluía carimbos operacionais. Depois dos quatro primeiros jobs, a definição passou a ignorá-los; plano físico, circuitos, IDs e orçamentos não mudaram. Os arquivos anteriores estão em `bookkeeping_history/`, e o snapshot [hardware_execution_20261110.json](../configs/protocols/revisao_feedback_v4/hardware_execution_20261110.json) preserva, sem alterações, o estado do início (4 jobs, 12:35 UTC).

## Limites e política de execução

Mantêm-se os QPYs arquivados, os pontos físicos e o twirling. Não há nova transpilation, mitigação de leitura nem desacoplamento dinâmico. O executor registra cada ID imediatamente; uma resposta de submissão ambígua bloqueia novos envios e jobs com erro não são substituídos automaticamente. Os limites não aumentaram após observar resultados. Jobs de 12:28 a 14:03 UTC; avisos de DNS ao serviço de identidade da IBM no log não afetaram os dados, e nenhum job foi reenviado.

## Consultar e verificar

Na raiz do repositório:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_feedback_hardware.py status
PYTHONPATH=src .venv/bin/python scripts/run_feedback_hardware.py verify
```

O diário local é `results/hardware-confirmation-20261110/` (não versionado), e o log é `watch.log`. Com a campanha completa, `verify` confere orçamento, IDs, hashes e recalcula a análise a partir das contagens, sem consultar a IBM. Os dados completos estão versionados no [pacote da campanha](campaigns/20261110-hardware-confirmation/README.md), com instruções de extração.

## Testes

Os 12 testes de [test_feedback_hardware.py](../tests/test_feedback_hardware.py) cobrem o orçamento real do SDK para dois PUBs, a ordem alternada, os limites de jobs e shots, o bloqueio de reenvio após falha de comunicação, a distinção de calibrações reais e a verificação offline da campanha concluída.
