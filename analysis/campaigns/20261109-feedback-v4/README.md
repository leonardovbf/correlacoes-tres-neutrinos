# Experimentos para revisão da Entrega 2 — 9 de novembro de 2026

Foram reanalisadas as 25 células originais de H1, executadas 400 campanhas de validação de intervalos, calculadas 15 configurações controladas com suporte completo da PSA e avaliadas 44 condições de ruído com 100 campanhas sintéticas de medição em cada uma. Os resultados anteriores foram preservados. Esta revisão local não enviou jobs IBM; a confirmação em hardware descrita na seção 4 foi executada depois, em 10 de novembro, e seus dados e resultados estão em [20261110-hardware-confirmation](../20261110-hardware-confirmation/README.md). Os arquivos deste pacote (incluindo `summary.json` e o plano) descrevem o estado de 9 de novembro e não foram alterados, para manter os hashes do manifesto.

O [repositório configurado no projeto](https://github.com/leonardovbf/correlacoes-tres-neutrinos) contém o código, o [desenho desta revisão](../../../configs/protocols/revisao_feedback_v4/design.json), os testes e os arquivos necessários à reanálise. Este desenho foi definido após os resultados anteriores e antes dos novos cálculos locais; não é o pré-registro original.

## 1. Auditoria do bootstrap

Os sorteios originais foram reproduzidos nas 25 células. O maior desvio numérico na reconstrução de suas distribuições bootstrap foi 2,27×10⁻¹⁴. As cinco estimativas fora dos próprios intervalos foram reproduzidas. Portanto, a ocorrência não decorre de uma divergência entre os dados arquivados e o estimador implementado.

Foram comparados percentil, basic e BCa. A implementação de BCa também foi conferida contra o SciPy em um teste independente. Para avaliar cobertura, foram simuladas 200 campanhas em cada um de dois regimes N=4, preservando 20 blocos × 4.096 trajetórias e a janela original 0≤τ≤10. A população conhecida é o suporte completo de 256 estados iniciais da PSA.

| μ | Cobertura percentil | Cobertura basic | Cobertura BCa |
| ---: | ---: | ---: | ---: |
| 0,1 | 82,0% | 91,0% | 85,5% |
| 3 | 96,0% | 95,0% | 94,5% |

Os intervalos têm nível nominal de 95%. A cobertura empírica também tem incerteza Monte Carlo, registrada nos dados. No regime fraco, trocar automaticamente para BCa não resolve a subcobertura. Essas validações são específicas de N=4 e não demonstram cobertura em N=8/12/16. Os intervalos reanalisados dos tamanhos maiores são sensibilidades, sem confirmação global de H1. Não se selecionou um método por ele conter a estimativa ou favorecer uma hipótese.

O [resumo da auditoria](h1_audit_summary.csv) mantém as estimativas, os três intervalos e o viés estimado. Os sorteios e jackknifes completos estão nos ZIPs. A [documentação do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) descreve os três métodos.

## 2. H1 com distribuição completa e configuração controlada

Foram mantidos estado de domínio, geometria uniforme, θ=0,2 e frequências de 0,7 a 1,3. A grade tem N=4/6/8 e μ=0,1/0,3/1/3/10. Cada caso usa todos os 4ᴺ estados iniciais da PSA. Compararam-se 8 e 16 subpassos RK4, com limites de 10⁻⁶ para Pₑ e 10⁻⁵ para C₂/C₃; todos passaram.

Esta nova grade usa **0≤τ≤3, com 61 tempos**. A análise original acima usa 0≤τ≤10; os dois resultados não são intercambiáveis. A média da PSA é determinística nessa enumeração, portanto não recebe um intervalo de Monte Carlo artificial.

| N | Inclinação de R₃ contra log₁₀μ | Crescimento estritamente monotônico? |
| ---: | ---: | --- |
| 4 | +0,090622 | Não |
| 6 | +0,006017 | Não |
| 8 | −0,114605 | Não |

R₃−R₂ foi positivo nas 15 configurações desta grade. Isso sustenta maior erro **normalizado pelo sinal** nos trios para esses casos. Não significa maior erro absoluto em todos eles. O crescimento com μ não se sustenta como uma regra geral nesta grade, e N=8 tem inclinação negativa. O [arquivo de métricas](h1_controlled_summary.csv) inclui erros de Pₑ, C₂ e C₃, normalização e comparação com C₃=0. Em N=4, μ=10, a PSA tem R₃≈1,031 e perde para essa previsão nula.

As inclinações descrevem uma grade finita, sem p-valor de uma população de modelos. A sensibilidade observada ao refinamento numérico foi propagada às inclinações e é muito menor que seus valores. Isso não é uma prova rigorosa de erro numérico para todo o espaço de parâmetros.

## 3. H2 com circuito fixo e orçamento igual

O ponto principal é N=4, μ=3, τ=1,5, estado de domínio e trio (0,1,2). Foram usados o QPY IBM arquivado e seu template Runtime de twirling, com 32 novas variantes locais. São 2 passos Trotter e 78 CZ. O template contém 614 SX; o replay inclui essas rotações. O erro ideal no C₃ é aproximadamente 0,000825, dentro da margem primária de 0,01.

As famílias separam apenas leitura, apenas erro de dois qubits, erro de dois qubits com p₁ fixo e portas sem erro de leitura. O modelo é despolarizante independente nas portas nativas e leitura simétrica independente. É um estudo de mecanismo, sem ajustar parâmetros aos resultados IBM. O parâmetro p₂ não deve ser identificado diretamente com a infidelidade média publicada do dispositivo.

Cada método recebe **327.680 shots**. O bruto usa todo o orçamento no sinal. O mitigado usa 245.760 no sinal e 40.960 em cada calibração. Preservam-se os 32 estratos de twirling; o bootstrap reamostra esses estratos e reestima as calibrações. A análise mantém as covariâncias dos bits.

O desfecho primário é o intervalo de C₃−C₃_exato inteiramente contido em ±0,01. Superar a PSA e superar C₃=0 são desfechos secundários distintos. O viés de Trotter permanece no erro do circuito; não é removido para facilitar a equivalência.

| Condição, apenas erro de leitura | Recuperação pelo bruto | Recuperação pelo mitigado |
| --- | ---: | ---: |
| pᵣ=0 | 100/100 | 100/100 |
| pᵣ=0,01 | 2/100 | 99/100 |
| pᵣ=0,03 | 0/100 | 97/100 |
| pᵣ=0,10 | 0/100 | 59/100 |
| pᵣ=0,20 | 0/100 | 0/100 |

Para pᵣ=0,03, os IC95 Monte Carlo dessas probabilidades são aproximadamente [0%;3,7%] para o bruto e [91,5%;99,0%] para o mitigado. São campanhas sintéticas sob o modelo declarado, não novos experimentos físicos. A cobertura do intervalo bootstrap interno de H2 não foi demonstrada para toda essa grade; a repetição mede a probabilidade de sua regra operacional de decisão.

Sem flutuação de shots, o limiar bruto de leitura fica entre 0,009375 e 0,01; a média corrigida ainda satisfaz a margem em pᵣ=0,20. Com shots finitos, a amplificação da incerteza limita a correção, como mostra a tabela. Para erro apenas de CZ e leitura zero, o limiar esperado fica entre p₂=0,000475 e 0,0005625 para ambos os métodos. A mitigação de leitura não corrige esse erro de porta. Com p₁=0,0001 por SX/X, ambos já falham na equivalência no início da varredura de p₂ desse circuito.

Os limiares são colchetes da grade, **não intervalos de confiança de uma diferença global de limiares**. O relatório completo preserva também reentradas de sucesso por flutuação de shots. Não se toma o último sucesso isolado como um limiar monotônico. As 44 condições e probabilidades de decisão estão em [h2_summary.csv](h2_summary.csv); os ZIPs contêm intervalos, campanhas, sementes, contagens e probabilidades completas.

## 4. Confirmação IBM preparada

> **Atualização (10 de novembro):** este plano foi executado integralmente, com 20 jobs e 163.840 shots. As quatro comparações passaram; os dados e o resultado estão em [20261110-hardware-confirmation](../20261110-hardware-confirmation/README.md). O texto abaixo é o plano, como estava antes do envio.

O [plano de confirmação](hardware_confirmation_plan.json) conserva os dois pontos físicos exploratórios de N=6/8 e seus QPYs. Ele prevê:

- 20 jobs, com dois PUBs por job, um de cada tamanho.
- 4.096 shots por PUB, 32 randomizações × 128 shots.
- Total máximo de 163.840 shots de sinal, distribuídos em cinco janelas de calibração.
- Ordem N6/N8 alternada por bloco e registro da calibração próxima da execução.
- Bootstrap apenas dos blocos de jobs, sem adicionar uma segunda reamostragem multinomial dos mesmos shots.
- Quatro comparações de erro, contra PSA completa e C₃=0 em cada tamanho, com intervalos simultâneos por Bonferroni.

O plano está **preparado, não submetido**. Antes de qualquer envio, são obrigatórias a validação do alvo atual, dos hashes, do agrupamento de dois PUBs e dos limites. Se o agrupamento não for suportado, o processo deve parar em vez de aumentar os jobs automaticamente. O plano não contém uma função de submissão.

A sensibilidade de planejamento encontrou sucesso conjunto em 95,8% de 500 cenários do modelo estacionário com incerteza de probabilidades e em 100% no cenário de heterogeneidade empírica dos pilotos. Essas projeções dependem de apenas cinco jobs anteriores por tamanho, não garantem poder ou calibração futura. O objetivo é confirmar menor erro nos pontos fixados. O N=8 de dois passos tem erro ideal≈0,01285 e não foi declarado uma promessa de equivalência em ±0,01. Os tamanhos também têm outros parâmetros diferentes, portanto esse plano não é um teste controlado de escala em N.

## 5. Parâmetros, dados e verificação

- [table4_controls.csv](table4_controls.csv): todos os valores observados para completar a tabela de controles, com proveniência e escopo. Nenhuma célula foi preenchida com um valor inventado.
- [hardware_parameters.csv](hardware_parameters.csv): parâmetros dos **130 jobs históricos concluídos**, incluindo contagens/calibrações do artigo original, triagem, confirmação e pilotos. São 120 jobs RunStore e 10 pilotos diretos; os 30 da campanha mais recente são um subconjunto.
- [classical_parameters.csv](classical_parameters.csv): as 25 células originais, blocos, trajetórias, frequências e subpassos.
- Os dados completos incluem ainda as mudanças originais de discretização, separando passos por intervalo de passos totais. O hardware original usa 14 passos totais no caso principal, enquanto o Aer original usa 112; não são o mesmo circuito.
- Os 85 testes do projeto passaram na data desta revisão, incluindo 9 controles novos. Com a execução em hardware, a suíte tem 97 testes. Foi verificada a reanálise portátil de 214 casos/jobs e a reconstrução dos 20 blocos originais N=4/μ=0,1 a partir dos rótulos iniciais brutos.

Os ZIPs contêm os momentos não centrados float64 de cada bloco original, suficientes para recalcular H1; os rótulos brutos de amostragem inicial, sementes e opções permitem regenerar as trajetórias. As grandes matrizes temporais `sample_z` originais continuam preservadas localmente e não foram duplicadas no pacote. Não se afirma que esses arquivos temporais integrais estejam publicados. As contagens completas dos 130 jobs, circuitos e calibrações arquivadas relevantes foram incluídas.

Os ZIPs são partes independentes, com menos de 45 MiB cada, para evitar centenas de arquivos expostos no Git. O [manifesto](archives.json) registra SHA-256 de cada parte e arquivo extraído.

## Reproduzir sem IBM ou acesso aos resultados originais

Use o ambiente fixado em `requirements-research.lock` (CPython 3.14.3 no ambiente de referência). Na raiz do repositório, extraia e valide todas as partes:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, zipfile
release = Path('analysis/campaigns/20261109-feedback-v4')
target = Path('results/feedback-revision-20261109')
manifest = json.loads((release/'archives.json').read_text())
target.mkdir(parents=True, exist_ok=True)
for part in manifest['parts']:
    path = release/part['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == part['sha256']
    with zipfile.ZipFile(path) as archive:
        archive.extractall(target)
for name, digest in manifest['files_sha256'].items():
    assert hashlib.sha256((target/name).read_bytes()).hexdigest() == digest
print('Todos os dados extraídos e verificados.')
PY

PYTHONPATH=src .venv/bin/python analysis/feedback_delivery.py verify
```

O verificador recalcula as estimativas H1 dos momentos, os intervalos arquivados, as decisões H2 a partir das contagens e os controles de orçamento/hashes dos jobs. Não consulta a IBM. O teste em uma cópia limpa, com conexão de rede bloqueada, está registrado em `reproduction_check.json`.

Para repetir os cálculos da nova grade controlada ou a validação de cobertura, use outra pasta de saída e os comandos `run_feedback_revision.py h1` e `coverage`. A captura dos dados originais e a geração inicial da varredura H2 usam os arquivos históricos locais; após a extração acima, toda a reanálise publicada funciona sem esse RunStore. Os 4.400 experimentos sintéticos de medição são amostragens das distribuições locais, não jobs de QPU.
