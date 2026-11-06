# Referência publicada: Lacroix et al. (2024)

Origem: https://arxiv.org/pdf/2409.20215v2, página 7, Figura 2(c).
`figure2c.csv` contém coordenadas extraídas dos vetores do PDF: centros dos
símbolos exatos e vértices das curvas PSA. Não são dados brutos dos autores.
`source.json` registra SHA-256 do PDF/CSV, eixos, método e incerteza. As quatro
cores correspondem aos neutrinos 0–3; os demais têm a simetria indicada na figura.

Para repetir a extração com Poppler:

```sh
curl -L --fail https://arxiv.org/pdf/2409.20215v2 -o /tmp/lacroix-2024.pdf
.venv/bin/python scripts/extract_lacroix_reference.py /tmp/lacroix-2024.pdf --output /tmp/lacroix-reference
```

Conversão: o artigo escreve H com J=σ/2, soma de pares ordenados e
ω=2μ_paper/N, Gij=(2μ_paper/N) fij. A contribuição de um par não ordenado é
Gij σi·σj/2=(μ_paper/N)fij σi·σj. Dividindo todo H por ω̄=2μ_paper/N, o
coeficiente do par é fij/2. No código ele é μ_codigo gij/(4N), portanto usamos
**μ_codigo=2N=16**, gij=fij=1−cos(|i−j| arccos(0,9)/7), ωi=1 e θ=0,195.
O tempo é **τ=t_paper/4** para N=8; t_paper=0…200 corresponde a τ=0…50.
Primeira metade νe, segunda νx; base de sabor; comparamos m1=⟨Z⟩, e não Pe.
Não se aplicou ajuste às curvas para definir essas constantes.

O protocolo usa 10.000 trajetórias bi-valuadas, semente 50001 e RK4 com
20 subpassos por intervalo: Δτ=0,0125 (Δt_paper=0,05). O artigo usa RK2;
o integrador pode diferir desde que convergido. A meta máxima para a extração
exata é 0,02 em Z e para PSA 0,06, incluindo variação entre amostras Monte Carlo
independentes. São tolerâncias operacionais de reprodução de uma figura,
fixadas antes da comparação; não margens de equivalência dos testes de K3.
Este controle preserva a diferença PSA–exato que o artigo apresenta.
