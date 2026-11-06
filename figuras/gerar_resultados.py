# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Gera as figuras 5–7 dos CSVs auditados, sem alterar o pacote original.

Executar: uv run figuras/gerar_resultados.py
Os intervalos são desenhados independentemente das estimativas: um ponto fora
do intervalo percentil não é deslocado nem tem sua barra truncada.
"""
from pathlib import Path
import csv
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "analysis/article_packages/20261106T120036Z-7f9b932d0594"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read(name):
    with (PACKAGE / "tables" / (name + ".csv")).open() as file:
        return list(csv.DictReader(file))


def save(fig, name, language):
    path = ROOT / "figuras" / ("en" if language == "en" else "") / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=450)
    fig.savefig(path.with_suffix(".svg"), metadata={"Date": None})
    plt.close(fig)


def main():
    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    for name, expected in manifest["package_files_sha256"].items():
        assert hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() == expected, name
    h1, shots, ibm = read("h1_main"), read("measurement_budget"), read("ibm_primary")
    primary = [r for r in read("mitigation") if r["primary"] == "True"]
    assert len(primary) == 1
    aer = primary[0]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.titlesize": 9, "axes.labelsize": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "savefig.facecolor": "white"})
    for lang in ("pt", "en"):
        fig, axes = plt.subplots(1, 3, figsize=(150/25.4, 79/25.4), sharey=True)
        for ax, n in zip(axes, (4, 6, 8)):
            rows = sorted([r for r in h1 if int(r["n"]) == n], key=lambda r: float(r["mu"]))
            for y, row in enumerate(rows):
                point, low, high = (float(row[k]) for k in ("r3_minus_r2", "delta_ci95_low", "delta_ci95_high"))
                ax.hlines(y, low, high, color="#23689b", lw=1.7)
                ax.plot([low, high], [y, y], "|", color="#23689b", ms=6)
                ax.plot(point, y, "o", mfc="#23689b" if low <= point <= high else "white", mec="#23689b", ms=5)
            ax.axvline(0, color=".4", ls="--", lw=.8)
            ax.set(xlim=(-.25, 1.05), ylim=(-.4,4.4), title=f"$N={n}$", xlabel="$D=R_3-R_2$", yticks=range(5), yticklabels=[r["mu"] for r in rows])
            ax.grid(axis="x", alpha=.2)
        axes[0].set_ylabel(r"$\lambda=\mu/\bar{\omega}$")
        fig.subplots_adjust(left=.11, right=.98, bottom=.21, top=.88, wspace=.18)
        save(fig, "figura-5-resultados-psa" if lang == "pt" else "figure-5-psa-results", lang)

        fig, axes = plt.subplots(1,3,figsize=(150/25.4, 88/25.4), sharey=True)
        colors = ["#23689b", "#ca7910", "#368447", "#9360a5", "#414141"]
        for ax, n in zip(axes, (4,6,8)):
            for mu, color, marker, style in zip((.1,.3,1,3,10), colors, ("o","s","^","D","v"), ("-","--","-.",":","-")):
                rows=sorted([r for r in shots if int(r["n"])==n and float(r["mu"])==mu],key=lambda r:int(r["shots_per_block"]))
                ax.plot([int(r["shots_per_block"]) for r in rows], [float(r["k3_rmse"]) for r in rows], color=color, marker=marker, ls=style, ms=3.5, lw=1, label=rf"$\lambda={mu:g}$")
            ax.set(xscale="log", yscale="log", title=f"$N={n}$", xticks=[1024,4096,16384], ylim=(.00025,.009))
            ax.set_xticklabels(["1 024","4 096","16 384"],rotation=25, ha="right",fontsize=7)
            ax.set_xlabel("Medições/bloco" if lang=="pt" else "Shots/block")
            ax.grid(alpha=.2, which="major")
            ax.minorticks_off()
        axes[0].set_ylabel(r"RMSE de $C^{(3)}$" if lang=="pt" else r"RMSE of $C^{(3)}$")
        fig.legend(*axes[0].get_legend_handles_labels(),loc="upper center",ncol=5,frameon=False,fontsize=8,columnspacing=.9)
        fig.subplots_adjust(left=.12,right=.99,bottom=.23,top=.78,wspace=.15)
        save(fig,"figura-6-orcamento-medicoes" if lang=="pt" else "figure-6-measurement-budget",lang)

        exact=float(aer["exact_k3"])
        points=[("Exato" if lang=="pt" else "Exact",exact,None,"D","#20252a"),
                ("PSA local",float(aer["psa_k3"]),None,"^","#23689b"),
                ("PSA IBM",float(ibm[0]["psa_k3"]),None,"^","#23689b")]
        for environment, data in (("Aer",aer),("IBM",None)):
            for method, marker, color in (("raw","o","#ca7910"),("mitigated","s","#9360a5")):
                label=("bruto" if method=="raw" else "mitigado") if lang=="pt" else method
                if data is not None:
                    value=float(data[f"{method}_k3"])
                    low,high=(exact+float(data[f"{method}_minus_exact_ci95_{side}"]) for side in ("low","high"))
                else:
                    row=next(r for r in ibm if r["method"]==method)
                    value=float(row["estimate_k3"])
                    low,high=(float(row["exact_k3"])+float(row[f"minus_exact_ci95_{side}"]) for side in ("low","high"))
                points.append((environment+" "+label,value,(low,high),marker,color))
        fig,ax=plt.subplots(figsize=(150/25.4,92/25.4))
        ax.axvspan(exact-.01,exact+.01,color="#9aa3ad",alpha=.2)
        ax.axvline(exact,color=".4",ls="--",lw=.8)
        for y,(_,value,interval,marker,color) in enumerate(points):
            if interval:
                ax.hlines(y,*interval,color=color,lw=1.5)
                ax.plot(interval,[y,y],"|",color=color,ms=6)
            ax.plot(value,y,marker,color=color,ms=5)
        ax.set(yticks=range(len(points)),yticklabels=[p[0] for p in points],xlabel=r"$C^{(3)}_{012}$",xlim=(-.34,.035),ylim=(6.6,-.6))
        ax.grid(axis="x",alpha=.2)
        fig.subplots_adjust(left=.24,right=.98,bottom=.17,top=.97)
        save(fig,"figura-7-comparacao-quantica" if lang=="pt" else "figure-7-quantum-comparison",lang)
    print("Figuras 5–7 geradas em português e inglês; hashes do pacote conferidos.")


if __name__ == "__main__":
    main()
