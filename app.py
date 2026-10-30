"""Interface local do laboratório de oscilações coletivas de neutrinos.

Executar com: streamlit run app.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from neutrinos import (  # noqa: E402
    ExperimentConfig,
    bootstrap_counts_interval,
    bootstrap_interval,
    classical_exact,
    mean_field,
    observable_from_counts,
    phase_space,
    quantum_trotter,
    summarize_errors,
)


INK = "#e9f4ff"
MUTED = "#9ab1c7"
CYAN = "#58d7dc"
BLUE = "#6e9aff"
GOLD = "#ffca71"
PINK = "#f184b4"
BG = "#0c1930"

st.set_page_config(page_title="Laboratório de Neutrinos", page_icon="◉", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background: radial-gradient(circle at 85% 0%, #172c49 0%, #07111f 54%); color: #e9f4ff;}
    [data-testid="stSidebar"] {background: #0b1b30; border-right: 1px solid #24415d;}
    h1, h2, h3 {color: #e9f4ff !important; letter-spacing: -.025em;}
    .hero {padding: 1.35rem 1.65rem; margin: .4rem 0 1.4rem; border: 1px solid #2c5269;
           border-radius: 20px; background: linear-gradient(110deg,#143048,#101e37 65%,#102b36);}
    .hero .eyebrow {color:#58d7dc;font-size:.74rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;}
    .hero h1 {font-size:2.15rem;margin:.35rem 0 .4rem;}
    .hero p {color:#c2d5e5;margin:0;max-width:850px;}
    .stButton button[kind="primary"] {background: #41bfc6; color:#061622; border:0; font-weight:800;}
    [data-testid="stMetric"] {background:#11253b;border:1px solid #24435d;border-radius:14px;padding:12px;}
    [data-testid="stMetricLabel"] {color:#a9c2d7;}
    .small-note {color:#9ab1c7;font-size:.84rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def run_classical(config: ExperimentConfig, trajectories: int, substeps: int):
    return {
        "exact": classical_exact(config),
        "mean": mean_field(config, substeps),
        "psa": phase_space(config, trajectories, substeps),
    }


@st.cache_data(show_spinner=False)
def run_quantum(config: ExperimentConfig, steps: int, shots: int, readout_error: float):
    return quantum_trotter(config, steps, shots, readout_error)


def styled_axes(title: str, ylabel: str = ""):
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_title(title, color=INK, loc="left", fontsize=14, pad=12, weight="bold")
    ax.set_xlabel(r"Tempo adimensional $\bar\omega t$", color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_color("#38536d")
    ax.grid(color="#29415c", alpha=.55, linewidth=.65)
    return fig, ax


def item_label(kind: str, item: tuple[int, ...]) -> str:
    if kind == "pe":
        return f"Neutrino {item[0]}"
    if kind == "c2":
        return f"Par ({item[0]}, {item[1]})"
    return f"Trio ({item[0]}, {item[1]}, {item[2]})"


def pick_observable(config: ExperimentConfig, key_prefix: str):
    labels = {"pe": "Probabilidade νₑ", "c2": "Cumulante de pares C²ᶻᶻ", "c3": "Cumulante de trios K³ᶻᶻᶻ"}
    kind = st.selectbox("Observável", list(labels), format_func=lambda k: labels[k], key=f"{key_prefix}_kind")
    indices = ([(i,) for i in range(config.n)] if kind == "pe" else
               [tuple(x) for x in (config.pair_index if kind == "c2" else config.trio_index)])
    item = st.selectbox("Partículas", indices, format_func=lambda x: item_label(kind, x), key=f"{key_prefix}_{kind}_item")
    return kind, indices.index(item), item


def line_chart(series, kind: str, index: int, title: str):
    fig, ax = styled_axes(title, {"pe": "P(νₑ)", "c2": "C²ᶻᶻ", "c3": "K³ᶻᶻᶻ"}[kind])
    colors = {"Exato": INK, "Campo médio": MUTED, "PSA bi-valuada": CYAN,
              "Circuito ideal": GOLD, "Medições simuladas": PINK}
    styles = {"Exato": "-", "Campo médio": ":", "PSA bi-valuada": "--",
              "Circuito ideal": "-.", "Medições simuladas": ""}
    for s in series:
        y = getattr(s, kind)[:, index]
        if s.sample_z is not None or s.raw_counts is not None:
            lower, upper = bootstrap_interval(s, kind, index, repetitions=100)
            ax.fill_between(s.times, lower, upper, color=colors[s.method], alpha=.13)
        if s.method == "Medições simuladas":
            ax.plot(s.times, y, "o", color=PINK, ms=3, alpha=.78, label=s.method)
        else:
            ax.plot(s.times, y, styles[s.method], color=colors[s.method],
                    linewidth=2 if s.method == "Exato" else 1.8, label=s.method)
    ax.legend(facecolor="#14283d", edgecolor="#35516d", labelcolor=INK, fontsize=8,
              ncol=2, loc="best")
    fig.tight_layout()
    return fig


def error_chart(reference, candidates, kind: str, index: int):
    fig, ax = styled_axes("Desvio absoluto em relação ao exato", "|Δ observável|")
    for s, color in candidates:
        ax.plot(s.times, np.abs(getattr(s, kind)[:, index] - getattr(reference, kind)[:, index]),
                color=color, linewidth=1.9, label=s.method)
    ax.legend(facecolor="#14283d", edgecolor="#35516d", labelcolor=INK, fontsize=8)
    fig.tight_layout()
    return fig


def metric_table(reference, series):
    rows = []
    for s in series:
        for key, label in (("pe", "P(νₑ)"), ("c2", "Pares"), ("c3", "Trios")):
            data = summarize_errors(reference, s).get(key)
            if data:
                rows.append({"Método": s.method, "Observável": label,
                             "RMSE": data["rmse"], "Erro máximo": data["max_abs"],
                             "Sinal exato RMS": data["signal_rms"]})
    return rows


def system_figure(config, exact, mean, moment_index):
    fig, (ax_network, ax_bloch, ax_field) = plt.subplots(1, 3, figsize=(13.5, 4.1), dpi=120)
    fig.patch.set_facecolor(BG)
    for ax in (ax_network, ax_bloch, ax_field):
        ax.set_facecolor(BG)
        ax.tick_params(colors=MUTED)
        for spine in ax.spines.values():
            spine.set_color("#38536d")
    angles = np.linspace(0, 2 * np.pi, config.n, endpoint=False) + np.pi / 2
    xy = np.column_stack((np.cos(angles), np.sin(angles)))
    g = config.g_matrix
    scale = max(float(np.max(np.abs(g))), 1.0)
    for i, j in config.pair_index:
        strength = abs(g[i, j]) / scale
        if strength:
            ax_network.plot(xy[[i, j], 0], xy[[i, j], 1], color=CYAN if g[i, j] >= 0 else PINK,
                            alpha=.16 + .52 * strength, linewidth=.7 + 2 * strength * min(config.mu / 5, 1), zorder=1)
    pe = exact.pe[moment_index]
    dots = ax_network.scatter(xy[:, 0], xy[:, 1], c=pe, cmap="coolwarm_r", vmin=0, vmax=1,
                              s=680, edgecolors=INK, linewidths=1.4, zorder=3)
    for i, (x, y) in enumerate(xy):
        ax_network.text(x, y, str(i), ha="center", va="center", fontsize=11, weight="bold", color="#07111f", zorder=4)
    ax_network.set_title("Rede de interações", color=INK, fontsize=12, weight="bold")
    ax_network.set_xlim(-1.45, 1.45)
    ax_network.set_ylim(-1.45, 1.45)
    ax_network.set_aspect("equal")
    ax_network.axis("off")
    bar = fig.colorbar(dots, ax=ax_network, fraction=.045, pad=.02)
    bar.set_label("P(νₑ) exata", color=MUTED)
    bar.ax.tick_params(colors=MUTED)

    bloch = mean.bloch[moment_index]
    ax_bloch.add_patch(plt.Circle((0, 0), 1, fill=False, color="#45637d", linestyle="--"))
    palette = plt.cm.plasma(np.linspace(.15, .85, config.n))
    for i, spin in enumerate(bloch):
        ax_bloch.arrow(0, 0, spin[0], spin[2], color=palette[i], width=.008,
                       head_width=.055, length_includes_head=True)
        ax_bloch.text(spin[0] * 1.11, spin[2] * 1.11, str(i), color=palette[i], ha="center", va="center")
    ax_bloch.axhline(0, color="#37516c", linewidth=.6)
    ax_bloch.axvline(0, color="#37516c", linewidth=.6)
    ax_bloch.set(xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), xlabel="⟨X⟩", ylabel="⟨Z⟩")
    ax_bloch.set_aspect("equal")
    ax_bloch.set_title("Vetores de sabor · campo médio", color=INK, fontsize=12, weight="bold")
    ax_bloch.xaxis.label.set_color(MUTED)
    ax_bloch.yaxis.label.set_color(MUTED)

    selected = 0
    effective = config.omega[selected] * config.b_field + config.mu / (2 * config.n) * (g[selected, :, None] * bloch).sum(axis=0)
    for vector, color, label in ((config.b_field, BLUE, "Campo de vácuo B"),
                                  (effective, GOLD, "Campo efetivo h₀")):
        ax_field.arrow(0, 0, vector[0], vector[2], color=color, width=.017,
                       head_width=.09, length_includes_head=True, label=label)
    ax_field.axhline(0, color="#37516c", linewidth=.6)
    ax_field.axvline(0, color="#37516c", linewidth=.6)
    ax_field.set(xlim=(-2.3, 2.3), ylim=(-2.3, 2.3), xlabel="componente X", ylabel="componente Z")
    ax_field.set_aspect("equal")
    ax_field.set_title("Campos atuando em ν₀", color=INK, fontsize=12, weight="bold")
    ax_field.xaxis.label.set_color(MUTED)
    ax_field.yaxis.label.set_color(MUTED)
    ax_field.legend(facecolor="#14283d", edgecolor="#35516d", labelcolor=INK, fontsize=7, loc="lower left")
    fig.tight_layout()
    return fig


def correlation_figure(config, exact, moment_index):
    """Mostra correlações exatas produzidas pela dinâmica no instante escolhido."""
    fig, (ax_pairs, ax_trios) = plt.subplots(1, 2, figsize=(11.5, 3.8), dpi=120)
    fig.patch.set_facecolor(BG)
    for ax in (ax_pairs, ax_trios):
        ax.set_facecolor(BG)
        ax.tick_params(colors=MUTED)
        for spine in ax.spines.values():
            spine.set_color("#38536d")

    c2 = np.full((config.n, config.n), np.nan)
    for value, (i, j) in zip(exact.c2[moment_index], config.pair_index):
        c2[i, j] = c2[j, i] = value
    amplitude = max(float(np.nanmax(np.abs(c2))), .05)
    heatmap = ax_pairs.imshow(c2, cmap="coolwarm", vmin=-amplitude, vmax=amplitude)
    ax_pairs.set_xticks(range(config.n))
    ax_pairs.set_yticks(range(config.n))
    ax_pairs.set_xlabel("Neutrino j", color=MUTED)
    ax_pairs.set_ylabel("Neutrino i", color=MUTED)
    ax_pairs.set_title("Correlação conectada dos pares", color=INK, fontsize=12, weight="bold")
    colorbar = fig.colorbar(heatmap, ax=ax_pairs, fraction=.046, pad=.04)
    colorbar.set_label("C²ᶻᶻ exato", color=MUTED)
    colorbar.ax.tick_params(colors=MUTED)

    trios = exact.c3[moment_index]
    if len(trios):
        largest = np.argsort(np.abs(trios))[-min(8, len(trios)):]
        largest = largest[np.argsort(np.abs(trios[largest]))]
        labels = ["(" + ",".join(str(i) for i in config.trio_index[index]) + ")" for index in largest]
        values = trios[largest]
        ax_trios.barh(labels, values, color=[CYAN if value >= 0 else PINK for value in values])
        span = max(float(np.max(np.abs(values))), .05)
        ax_trios.set_xlim(-span * 1.2, span * 1.2)
        ax_trios.axvline(0, color=MUTED, linewidth=.7)
    else:
        ax_trios.text(.5, .5, "Requer pelo menos 3 neutrinos", transform=ax_trios.transAxes,
                      color=MUTED, ha="center", va="center")
    ax_trios.set_title("Cumulantes conectados dos trios", color=INK, fontsize=12, weight="bold")
    ax_trios.set_xlabel("K³ᶻᶻᶻ exato", color=MUTED)
    ax_trios.grid(axis="x", color="#29415c", alpha=.5)
    fig.tight_layout()
    return fig


def save_results(config, classical, quantum, quality, gate_noise=None):
    from datetime import datetime, timezone
    import hashlib
    import importlib.metadata
    import os
    import shutil
    import subprocess
    import tempfile
    import uuid

    root = Path(__file__).resolve().parent
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cfg = json.dumps(config.record(), sort_keys=True)
    run_id = f"{stamp}-{hashlib.sha256(cfg.encode()).hexdigest()[:10]}-{uuid.uuid4().hex[:6]}"
    results_root = root / "results"
    results_root.mkdir(parents=True, exist_ok=True)
    dest = results_root / run_id
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_sha = "unknown"
    source_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in (root / "app.py", *sorted((root / "src" / "neutrinos").glob("*.py")))}
    dependencies = {}
    for name in ("numpy", "scipy", "matplotlib", "streamlit", "qiskit", "qiskit-aer"):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    manifest = {"run_id": run_id, "created_utc": stamp, "git_commit": git_sha,
                "source_sha256": source_hashes,
                "model": config.record(), "quality": quality,
                "methods": [s.method for s in classical.values()] + ([s.method for s in quantum] if quantum else []),
                "method_diagnostics": {name: s.diagnostics for name, s in classical.items()} |
                                      ({name: s.diagnostics for name, s in zip(("circuit_ideal", "measured"), quantum)} if quantum else {}),
                "dependencies": dependencies,
                "gate_noise": gate_noise[1] if gate_noise else None,
                "limitations": ["Modelo de ruído de portas exploratório, sem calibração de hardware", "PSA requer convergência para análise confirmatória"]}
    arrays = {"times": config.times, "pairs": config.pair_index, "trios": config.trio_index}
    for name, s in classical.items():
        for field in ("m1", "m2", "m3", "pe", "c2", "c3"):
            arrays[f"{name}_{field}"] = getattr(s, field)
        if s.sample_z is not None:
            arrays[f"{name}_sample_z"] = s.sample_z
    if quantum:
        for name, s in zip(("circuit_ideal", "measured"), quantum):
            for field in ("m1", "m2", "m3", "pe", "c2", "c3"):
                arrays[f"{name}_{field}"] = getattr(s, field)
            if s.raw_counts is not None:
                arrays[f"{name}_counts"] = s.raw_counts
    if gate_noise:
        arrays["gate_noise_counts"] = gate_noise[0]
    staged = Path(tempfile.mkdtemp(prefix=".staging-", dir=results_root))
    try:
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        np.savez_compressed(staged / "moments.npz", **arrays)
        os.replace(staged, dest)
    except Exception:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return dest


def run_qiskit_isolated(config, action, steps, **parameters):
    """Isola as bibliotecas nativas do Qiskit do processo da interface."""
    import os
    root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    payload = {"action": action, "config": {"n": config.n, "mu": config.mu, "theta": config.theta,
                          "omega_spread": config.omega_spread, "t_max": config.t_max,
                          "points": config.points, "flavors": config.flavors, "seed": config.seed,
                          "omega_values": config.omega_values, "b_values": config.b_values,
                          "g_values": config.g_values,
                          "initial_bloch_values": config.initial_bloch_values},
               "steps_per_interval": steps, **parameters}
    result = subprocess.run([sys.executable, "-m", "neutrinos.aer_worker"],
                            input=json.dumps(payload), text=True, capture_output=True,
                            cwd=root, env=env, timeout=120, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Qiskit Aer terminou com código {result.returncode}: {result.stderr[-800:]}")
    response = json.loads(result.stdout)
    return response


@st.cache_data(show_spinner=False)
def verify_qiskit(config, steps):
    return run_qiskit_isolated(config, "first_interval", steps)


st.markdown(
    """<div class="hero"><div class="eyebrow">Laboratório computacional · dois sabores</div>
    <h1>Oscilações coletivas de neutrinos</h1>
    <p>Execute o mesmo modelo por evolução exata, campo médio, PSA e circuito Trotter.
    Explore campos, interações e cumulantes com parâmetros rastreáveis.</p></div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Experimento")
    screen = st.radio("Área", ["Clássica", "Quântica", "Sistema", "Qualidade"], label_visibility="collapsed")
    st.divider()
    n = st.select_slider("Neutrinos N", options=[4, 6, 8, 10, 12, 14, 16], value=4)
    mu = st.slider("Interação μ / ω̄", 0.0, 10.0, 1.0, .1)
    theta = st.slider("Ângulo de mistura θ (rad)", 0.0, .78, .20, .01)
    spread = st.slider("Dispersão das frequências", 0.0, .8, .30, .05)
    pattern = st.selectbox("Estado inicial", ["Blocos νₑ / νₓ", "Alternado", "Todos νₑ", "Personalizado"])
    if pattern == "Blocos νₑ / νₓ":
        flavors = (0,) * (n // 2) + (1,) * (n - n // 2)
    elif pattern == "Alternado":
        flavors = tuple(i % 2 for i in range(n))
    elif pattern == "Todos νₑ":
        flavors = (0,) * n
    else:
        entry = st.text_input("Sequência 0=νₑ, 1=νₓ", value="0" * (n // 2) + "1" * (n - n // 2))
        flavors = tuple(int(x) for x in entry) if len(entry) == n and set(entry) <= {"0", "1"} else ()
        if len(flavors) != n:
            st.error(f"Informe exatamente {n} caracteres 0 ou 1.")
            st.stop()
    t_max = st.slider("Tempo máximo ω̄t", 2.0, 20.0, 8.0, .5)
    points = st.select_slider("Pontos no tempo", options=[21, 41, 61, 81, 101], value=81)
    st.divider()
    trajectories = st.select_slider("Trajetórias PSA", options=[64, 128, 256, 512, 1024, 2048], value=256)
    substeps = st.slider("Subpassos do integrador", 1, 12, 4)
    seed = st.number_input("Semente", 0, 10_000_000, 42, 1)
    with st.expander("Carregar cenário próprio / publicado"):
        uploaded_config = st.file_uploader("Configuração JSON", type="json", help="Permite definir ωᵢ, B e gᵢⱼ explicitamente.")
        st.caption("Use configs/cenario_exemplo.json como modelo. Confirme os fatores e a base de sabor ao reproduzir uma publicação.")
    run_button = st.button("Executar parte clássica", type="primary", width="stretch")
    st.caption("ωᵢ/ω̄ igualmente espaçados em [1−dispersão, 1+dispersão]; gᵢⱼ=1.")
    if n >= 12 and trajectories >= 1024:
        st.warning("Esta configuração pode consumir centenas de MB e levar mais tempo. Salve os resultados após a execução.")

config = ExperimentConfig(n=n, mu=mu, theta=theta, omega_spread=spread,
                          t_max=t_max, points=points, flavors=flavors, seed=int(seed))
if uploaded_config is not None:
    try:
        config = ExperimentConfig.from_dict(json.loads(uploaded_config.getvalue().decode("utf-8")))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        st.error(f"Configuração JSON inválida: {exc}")
        st.stop()
    n, mu, points, seed = config.n, config.mu, config.points, config.seed
    st.sidebar.info("Cenário carregado. Os controles físicos acima foram substituídos pelo JSON; trajetórias e subpassos continuam ativos.")
classical_key = (config, trajectories, substeps)
if run_button or ("classical" not in st.session_state and n == 4):
    with st.spinner("Calculando referência exata, campo médio e PSA..."):
        st.session_state.classical = run_classical(config, trajectories, substeps)
        st.session_state.classical_key = classical_key
classical = st.session_state.get("classical") if st.session_state.get("classical_key") == classical_key else None

if screen == "Clássica":
    st.subheader("Evolução clássica")
    st.caption("Referência exata, aproximação de campo médio e PSA bi-valuada. O caso configurado é um cenário piloto, não uma reprodução publicada.")
    if classical is None:
        st.info("Os parâmetros mudaram. Execute a parte clássica pela barra lateral.")
    else:
        exact, mean, psa = classical["exact"], classical["mean"], classical["psa"]
        err = summarize_errors(exact, psa)
        a, b, c, d = st.columns(4)
        a.metric("Dimensão exata", f"2^{n} = {1 << n:,}")
        b.metric("Trajetórias PSA", f"{trajectories:,}")
        c.metric("RMSE PSA · trios", f"{err['c3']['rmse']:.3g}")
        d.metric("Erro de norma", f"{exact.diagnostics['max_norm_error']:.2g}")
        kind, idx, item = pick_observable(config, "classical")
        st.pyplot(line_chart((exact, mean, psa), kind, idx, item_label(kind, item)), clear_figure=True)
        left, right = st.columns([1.15, .85])
        with left:
            st.pyplot(error_chart(exact, ((mean, MUTED), (psa, CYAN)), kind, idx), clear_figure=True)
        with right:
            st.markdown("#### Comparação agregada")
            st.dataframe(metric_table(exact, (mean, psa)), width="stretch", hide_index=True)
            st.caption("RMSE calculado em todos os tempos e índices da ordem correspondente. Faixa colorida: IC percentil pontual de 95% por reamostragem das trajetórias; não corrige múltiplas comparações.")

elif screen == "Quântica":
    st.subheader("Circuito Trotter e medições")
    st.caption("Circuito de 2ª ordem com medições locais. O painel Aer aplica ruído sintético de portas e leitura em um instante; não representa hardware IBM.")
    if n > 8:
        st.warning("Escolha N ≤ 8 para o circuito interativo. O cálculo clássico aceita até N=16.")
    elif classical is None:
        st.info("Execute primeiro a parte clássica com estes parâmetros para obter a referência.")
    else:
        c1, c2, c3 = st.columns(3)
        steps = c1.select_slider("Passos Trotter por intervalo", options=[1, 2, 4, 8, 16], value=2)
        shots = c2.select_slider("Medições por tempo", options=[128, 256, 512, 1024, 2048, 4096, 8192], value=1024)
        readout = c3.slider("Erro de leitura por qubit", 0.0, .2, .02, .005)
        quantum_key = (config, steps, shots, readout)
        if st.button("Executar circuito", type="primary") or ("quantum" not in st.session_state and n == 4):
            with st.spinner("Aplicando portas Trotter e amostrando medições..."):
                st.session_state.quantum = run_quantum(config, steps, shots, readout)
                st.session_state.quantum_key = quantum_key
        quantum = st.session_state.get("quantum") if st.session_state.get("quantum_key") == quantum_key else None
        if quantum:
            ideal, measured = quantum
            exact, psa = classical["exact"], classical["psa"]
            err = summarize_errors(exact, ideal)
            a, b, c, d = st.columns(4)
            a.metric("Passos até τ máximo", ideal.diagnostics["total_steps"])
            b.metric("Medições totais", f"{shots * points:,}")
            c.metric("RMSE Trotter · trios", f"{err['c3']['rmse']:.3g}")
            d.metric("Erro de norma", f"{ideal.diagnostics['max_norm_error']:.2g}")
            kind, idx, item = pick_observable(config, "quantum")
            st.pyplot(line_chart((exact, psa, ideal, measured), kind, idx, item_label(kind, item)), clear_figure=True)
            left, right = st.columns([1.1, .9])
            with left:
                st.pyplot(error_chart(exact, ((psa, CYAN), (ideal, GOLD), (measured, PINK)), kind, idx), clear_figure=True)
            with right:
                st.markdown("#### Erros agregados")
                st.dataframe(metric_table(exact, (psa, ideal, measured)), width="stretch", hide_index=True)
                st.caption("Faixas coloridas: IC percentil pontual de 95% por reamostragem das trajetórias ou contagens completas. O ruído de portas fica disponível para um instante no painel Aer; H2 ainda exige varredura de cenários e correção por testes múltiplos.")
            with st.expander("Circuito Qiskit e verificação independente", expanded=False):
                try:
                    from neutrinos.sim import _symmetric_trotter_step, initial_state

                    verification = verify_qiskit(config, steps)
                    qiskit_probs = np.asarray(verification["probabilities"])
                    manual_state = initial_state(config)
                    interval_dt = float(config.times[1] - config.times[0]) / steps
                    for _ in range(steps):
                        _symmetric_trotter_step(manual_state, config, interval_dt)
                    discrepancy = float(np.max(np.abs(qiskit_probs - np.abs(manual_state) ** 2)))
                    x, y = st.columns(2)
                    x.metric("Diferença máxima Qiskit × motor", f"{discrepancy:.2g}")
                    y.metric("Portas no primeiro intervalo", verification["size"])
                    st.caption("O diagrama mostra apenas o primeiro intervalo temporal; os demais repetem a sequência de portas. Portas νν representam a interação Heisenberg de um par.")
                    st.code(verification["diagram"], language="text")
                except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                    st.info(f"Verificação Qiskit indisponível: {exc}")
            if steps < 16 and st.button("Verificar convergência de Trotter (passos ×2)"):
                with st.spinner("Calculando circuito ideal com passo temporal menor..."):
                    finer, _ = run_quantum(config, steps * 2, 32, 0.0)
                current_error = summarize_errors(exact, ideal)["c3"]["rmse"]
                finer_error = summarize_errors(exact, finer)["c3"]["rmse"]
                st.dataframe([
                    {"Passos por intervalo": steps, "RMSE nos trios": current_error},
                    {"Passos por intervalo": steps * 2, "RMSE nos trios": finer_error},
                ], width="stretch", hide_index=True)
                st.caption("Critério de aceitabilidade deve ser definido em relação à diferença exato–PSA do cenário estudado.")
            with st.expander("Ruído de portas em um instante · Qiskit Aer", expanded=False):
                max_index = min(points - 1, 120 // steps)
                chosen_index = st.slider("Índice temporal para ruído de portas", 1, max_index,
                                         min(5, max_index))
                p1_col, p2_col = st.columns(2)
                p1 = p1_col.slider("Erro despolarizante · porta de 1 qubit", 0.0, .05, .001, .001)
                p2 = p2_col.slider("Erro despolarizante · CX", 0.0, .15, .01, .005)
                gate_key = (config, steps, shots, readout, chosen_index, p1, p2)
                if st.button("Simular ruído de portas"):
                    try:
                        with st.spinner("Transpilando e amostrando o circuito no Qiskit Aer..."):
                            response = run_qiskit_isolated(
                                config, "gate_noise", steps, interval_index=chosen_index,
                                shots=shots, single_qubit_error=p1,
                                two_qubit_error=p2, readout_error=readout)
                            st.session_state.gate_noise = (np.asarray(response["counts"], dtype=np.int64),
                                                           response["metadata"])
                            st.session_state.gate_noise_key = gate_key
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                        st.error(f"Falha controlada na simulação Aer: {exc}")
                gate_result = (st.session_state.get("gate_noise")
                               if st.session_state.get("gate_noise_key") == gate_key else None)
                if gate_result:
                    counts, meta = gate_result
                    noisy_value = observable_from_counts(counts, kind, item)
                    low, high = bootstrap_counts_interval(counts, kind, item, repetitions=200)
                    ref_value = float(getattr(exact, kind)[chosen_index, idx])
                    psa_value = float(getattr(psa, kind)[chosen_index, idx])
                    ideal_value = float(getattr(ideal, kind)[chosen_index, idx])
                    st.metric(f"Estimativa Aer em τ={meta['tau']:.2f}", f"{noisy_value:.4f}")
                    st.write(f"IC de 95% das medições: **[{low:.4f}, {high:.4f}]** · "
                             f"exato **{ref_value:.4f}** · PSA **{psa_value:.4f}** · "
                             f"circuito ideal **{ideal_value:.4f}**")
                    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
                    fig.patch.set_facecolor(BG)
                    ax.set_facecolor(BG)
                    values = [ref_value, psa_value, ideal_value, noisy_value]
                    ax.bar(["Exato", "PSA", "Ideal", "Aer ruidoso"], values,
                           color=[INK, CYAN, GOLD, PINK], alpha=.88)
                    ax.errorbar([3], [noisy_value], yerr=[[max(0, noisy_value-low)], [max(0, high-noisy_value)]],
                                fmt="none", ecolor=INK, capsize=5, linewidth=1.5)
                    ax.tick_params(colors=MUTED)
                    ax.grid(axis="y", color="#29415c", alpha=.5)
                    for spine in ax.spines.values():
                        spine.set_color("#38536d")
                    fig.tight_layout()
                    st.pyplot(fig, clear_figure=True)
                    st.caption(f"Profundidade após transpilação: {meta['transpiled_depth']} · portas CX: {meta['cx_count']}. Ruído sintético despolarizante em sx/x/cx e leitura; não é calibração IBM nem teste confirmatório de H2.")
        else:
            st.info("Execute o circuito com os controles acima.")

elif screen == "Sistema":
    st.subheader("Visualização do sistema")
    st.caption("A cor da rede mostra P(νₑ) exata. Setas de sabor e campo efetivo usam a solução de campo médio; a intensidade das conexões representa |gᵢⱼ|.")
    if classical is None:
        st.info("Execute a parte clássica para visualizar a dinâmica.")
    else:
        idx = st.slider("Instante da simulação", 0, points - 1, 0,
                        format="passo %d")
        st.markdown(f"**τ = {config.times[idx]:.3f}** · {n} neutrinos · μ/ω̄ = {mu:.2f}")
        st.pyplot(system_figure(config, classical["exact"], classical["mean"], idx), clear_figure=True)
        st.pyplot(correlation_figure(config, classical["exact"], idx), clear_figure=True)
        x, y = st.columns(2)
        x.info("Rede: cada aresta é uma interação entre dois neutrinos. A espessura representa μ|gᵢⱼ|; não indica correlação medida.")
        y.info("Campo efetivo em ν₀: termo de vácuo mais contribuição média dos demais neutrinos. Os vetores variam com o tempo.")
        st.markdown("#### Parâmetros físicos")
        st.dataframe([{"i": i, "ωᵢ/ω̄": float(w), "⟨Z⟩ inicial": float(config.initial_bloch[i, 2]),
                       "P(νₑ) agora": float(classical["exact"].pe[idx, i])}
                      for i, w in enumerate(config.omega)],
                     width="stretch", hide_index=True)

else:
    st.subheader("Qualidade e reprodutibilidade")
    st.caption("Verificações automáticas identificam problemas numéricos. Elas não substituem reprodução de um benchmark publicado nem estudo de convergência.")
    if classical is None:
        st.info("Execute a parte clássica para gerar o relatório de qualidade.")
    else:
        exact, mean, psa = classical["exact"], classical["mean"], classical["psa"]
        initial_moment_error = max(float(np.max(np.abs(getattr(exact, key)[0] - getattr(psa, key)[0])))
                                   for key in ("m1", "m2", "m3") if getattr(exact, key).shape[1])
        quality = {
            "exact_norm_error": exact.diagnostics["max_norm_error"],
            "mean_spin_length_error": mean.diagnostics["max_spin_length_error"],
            "psa_initial_z_moment_error": initial_moment_error,
            "psa_initial_spin_mean_error_max": psa.diagnostics["initial_spin_mean_error_max"],
            "psa_trajectories": trajectories,
            "seed": int(seed),
        }
        rows = [
            {"Controle": "Norma da referência exata", "Medida": quality["exact_norm_error"],
             "Limite": 1e-8, "Estado": "✓" if quality["exact_norm_error"] < 1e-8 else "REVER"},
            {"Controle": "Comprimento dos spins · campo médio", "Medida": quality["mean_spin_length_error"],
             "Limite": 1e-4, "Estado": "✓" if quality["mean_spin_length_error"] < 1e-4 else "REVER"},
            {"Controle": "Momentos Z da PSA em τ=0", "Medida": initial_moment_error,
             "Limite": 4 / np.sqrt(trajectories), "Estado": "✓" if initial_moment_error < 4 / np.sqrt(trajectories) else "REVER"},
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
        st.markdown("#### Rastreabilidade")
        st.json(config.record(), expanded=False)
        st.caption("A PSA usa amostragem bi-valuada rotacionada para estados produto, um neutrino por feixe, conforme Lacroix et al. (2024), seção II.1.3. O limite 4/√M para os momentos iniciais é apenas uma checagem de engenharia, não um teste estatístico formal.")
        st.write(f"Desvio máximo da média inicial de Bloch na PSA: **{quality['psa_initial_spin_mean_error_max']:.3g}**")
        st.markdown("#### Convergência numérica")
        convergence_key = (config, trajectories, substeps)
        if st.button("Comparar resolução e amostragem"):
            with st.spinner("Refinando o integrador e a amostragem da PSA..."):
                fine_steps = substeps * 2
                fine_mean = mean_field(config, fine_steps)
                fine_psa = phase_space(config, trajectories, fine_steps)
                more_psa = phase_space(config, min(trajectories * 2, 4096), substeps)
                independent_psa = phase_space(replace(config, seed=config.seed + 1), trajectories, substeps)
                def rms_gap(a, b):
                    return float(np.sqrt(np.mean((a.c3 - b.c3) ** 2)))
                st.session_state.convergence = {
                    "Campo médio: subpassos ×2": rms_gap(mean, fine_mean),
                    "PSA: subpassos ×2, mesma semente": rms_gap(psa, fine_psa),
                    "PSA: trajetórias ×2": rms_gap(psa, more_psa),
                    "PSA: semente independente": rms_gap(psa, independent_psa),
                }
                st.session_state.convergence_key = convergence_key
        if st.session_state.get("convergence_key") == convergence_key:
            quality["convergence_c3_rms"] = st.session_state.convergence
            st.dataframe([{"Comparação": name, "RMS da mudança nos trios": value}
                          for name, value in st.session_state.convergence.items()],
                         width="stretch", hide_index=True)
            st.caption("Estas diferenças quantificam sensibilidade numérica e de amostragem. A interpretação física requer tolerâncias e critérios fixados no protocolo.")
        st.markdown("#### Salvar experimento")
        quantum = st.session_state.get("quantum") if st.session_state.get("quantum_key", (None,))[0] == config else None
        gate_noise = (st.session_state.get("gate_noise")
                      if st.session_state.get("gate_noise_key", (None,))[0] == config else None)
        if st.button("Salvar manifesto e momentos em results/"):
            try:
                dest = save_results(config, classical, quantum, quality, gate_noise)
                st.success(f"Experimento salvo em {dest.relative_to(Path(__file__).resolve().parent)}")
            except FileExistsError:
                st.error("Já existe uma execução com o mesmo identificador nesta segundo. Tente novamente.")
        st.markdown("**Próximos controles para H1/H2:** fechar o benchmark publicado, estudar a convergência da PSA em várias sementes, varrer ruído de portas e orçamento de medições, definir margens de equivalência e corrigir testes múltiplos.")

st.divider()
st.markdown('<div class="small-note">Protótipo local · resultados gerados por modelo de dois sabores · tempos em unidades de ω̄⁻¹</div>', unsafe_allow_html=True)
