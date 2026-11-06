# Pacote de resultados para o artigo

Este pacote resume o estudo local concluído e os 20 blocos IBM já coletados.
`manifest.json` contém SHA-256 dos relatórios originais e dos arquivos derivados.
O diretório original `results/` completo continua necessário para reproduzir cada execução.

## Ordem de leitura

1. `tables/controls.csv` e `tables/published_reproduction.csv`: validade numérica e reprodução da Figura 2(c).
2. `tables/h1_main.csv`: comparação principal da PSA com o exato para K₂ e K₃, N=4/6/8.
3. `tables/measurement_budget.csv`: efeito de 1.024, 4.096 e 16.384 shots no circuito ideal.
4. `tables/mitigation.csv` e `tables/ibm_primary.csv`: avaliação do caso H2 predefinido.
5. `tables/h1_extension.csv`, `tables/gate_noise.csv` e `tables/sampling_precision.csv`: material suplementar e sensibilidade.
6. `figures/`: curvas originais selecionadas e comparação estática do caso H2.

## Onde usar no artigo

- **Métodos e validação:** reprodução publicada (T00), controles de integração e amostragem (T01/T02), Trotter e equivalência Qiskit (T04), emendas documentadas.
- **Resultado principal H1:** `h1_main.csv` e curvas de N=4/8. Use R₂, R₃ e IC95 de R₃−R₂ por célula; descreva o padrão sem extrapolar o ponto de quebra para N maior.
- **Efeito do orçamento de medição:** `measurement_budget.csv` e curva T05 N=4, μ=3.
- **Resultado principal H2:** `mitigation.csv`, `ibm_primary.csv` e `h2_primary_comparison.pdf`. Separe o circuito ideal, o Aer ruidoso e a QPU real.
- **Suplemento:** extensão N=12/16, grade completa de ruído, precisão de amostragem, arquivos JSON completos e protocolo IBM.

## Resultados que o texto pode afirmar

- Reprodução publicada: maior desvio exato 0.00140755 (limite 0,02) e PSA 0.02992 (limite 0,06). São coordenadas digitalizadas da figura, não dados brutos dos autores.
- H1: o IC95 de R₃−R₂ é positivo em 14/15 células principais; N=4, μ=0,1 não resolve o sinal. A extensão N=12/16 tem 10/10 ICs positivos. Esses resultados são por célula; tendências e multiplicidade exigem interpretação separada.
- O teste principal H2 é N=4, μ=3, τ=2, trio (0,1,2), 20 blocos e 16.384 shots por bloco/método. K₃ exato = -0.315784; PSA local = -0.155768; Aer bruto = -0.000305; Aer mitigado = 0.001301. Decisão: **inconclusivo**.
- Na IBM, K₃ bruto = 0.005847; mitigado = 0.006376; decisão = **inconclusivo**. Há 20 blocos completos e nenhum job pendente no registro. O status textual do arquivo IBM permanece `provisional_pending_T07_and_local_validation` porque ele foi calculado antes da conclusão local; o arquivo original não foi reescrito.

## Interpretação e limites

`passed` nos controles significa que o protocolo e as verificações numéricas passaram; não significa que H2 foi confirmada. No caso principal, as estimativas Aer/IBM ficam perto de zero e os ICs para a diferença ao exato não cabem na margem de equivalência ±0,01. A mitigação de leitura usada aqui não recuperou K₃ exato. Registre essa conclusão, sem afirmar vantagem quântica.

A grade de ruído em μ=10, τ=4 foi refinada para 29 pontos/448 passos Trotter; o limite ideal de erro permaneceu 0,001. A emenda amostral v3 e a emenda temporal v4 estão em `reports/`. A comparação entre células de ruído deve declarar a diferença de profundidade.

A condição inicial de precisão amostral não passou e foi substituída pela emenda v3 após a observação dessa falha. A emenda v4 também foi definida depois da falha de Trotter. Declare ambas como alterações posteriores ao protocolo inicial, com os resultados anteriores preservados.

As inclinações agregadas H1 de N=8/12/16 têm estimativa pontual fora do IC percentil bootstrap registrado. Não use essas inclinações como resultado confirmatório sem revisar o viés/intervalo e a multiplicidade. As tabelas por célula são o ponto de partida para essa auditoria.

O maior desvio Qiskit versus emulador no controle T04 foi 1.09e-11 (limite 1e-10). A coleção IBM é uma aquisição antecipada separada da T07; os relatórios completos em `reports/` guardam ICs, orçamento, sementes e decisões.

## Como regenerar

Na raiz do repositório, execute `python analysis/prepare_article_package.py CAMINHO/study.json CAMINHO/hardware_analysis.json --output NOVO_DIRETORIO`. O destino deve estar vazio. O pacote é um recorte de escrita, não substitui o arquivo científico integral de `results/`.
