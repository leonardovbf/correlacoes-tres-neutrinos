#!/usr/bin/env python3
"""Auditoria local posterior à coleta; não modifica resultados nem acessa a IBM.

Enumera os 4**4 estados iniciais da PSA bi-valuada (não estados quânticos),
confere o RK4 da extensão v2 e resume o viés bootstrap arquivado de H1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from neutrinos.sim import (ExperimentConfig, _evolve_spins, _from_trajectories,
                           _rhs, classical_exact, observable_from_counts)
from neutrinos.study_analysis import connected, metrics
from app.backend.storage import RunStore

PACKAGE = ROOT / "analysis/article_packages/20261106T120036Z-7f9b932d0594"
SCREEN = ROOT / "results/protocols/20261106T203907Z-6f9e3db11fd9/run.json"
LOCAL = ROOT / "results/protocols/20261106T202522Z-13feb0a1bb32/run.json"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def support(config):
    """Mesma base transversal e distribuição inicial de phase_space()."""
    labels = np.arange(4 ** config.n, dtype=np.uint64)
    signs = 2 * ((labels[:, None] >> np.arange(2 * config.n, dtype=np.uint64)) & 1).astype(float) - 1
    signs = signs.reshape(-1, config.n, 2)
    spins = np.empty((len(labels), config.n, 3))
    for i, direction in enumerate(config.initial_bloch):
        anchor = np.array([0., 0., 1.]) if abs(direction[2]) < .9 else np.array([1., 0., 0.])
        u = np.cross(anchor, direction)
        u /= np.linalg.norm(u)
        v = np.cross(direction, u)
        spins[:, i] = direction + signs[:, i, 0, None] * u + signs[:, i, 1, None] * v
    return spins


def enumerate_psa(config, substeps):
    spins = support(config)
    z = _evolve_spins(config, spins, substeps)[..., 2]
    series = _from_trajectories(config, z, "PSA suporte completo", {})
    return series, z


def h1_audit():
    out = []
    for name in ("T03-classica-principal", "T03-classica-extensao"):
        for case in read(PACKAGE / f"reports/{name}.json")["cases"]:
            a = case["psa_analysis"]
            draws = np.asarray(a["r3_minus_r2_bootstrap"])
            center = a["c3"]["normalized_rmse"] - a["c2"]["normalized_rmse"]
            lo, hi = a["r3_minus_r2_ci95"]
            out.append({**case["cell"], "D": center, "ci95": [lo, hi],
                "estimate_outside_percentile_ci": not lo <= center <= hi,
                "bootstrap_mean_minus_estimate": float(draws.mean() - center),
                "bootstrap_sd": float(draws.std(ddof=1)),
                "r3": a["c3"]["normalized_rmse"],
                "c3_signal_rms": a["c3"]["signal_rms"],
                "c3_rmse": a["c3"]["rmse"]})
    return out


def deterministic_h1():
    result = []
    for mu in (.1, .3, 1., 3., 10.):
        cfg = ExperimentConfig(n=4, mu=mu, t_max=10., points=201, flavors=(0, 0, 1, 1))
        ex = classical_exact(cfg)
        coarse, _ = enumerate_psa(cfg, 12)
        fine, _ = enumerate_psa(cfg, 24)
        r2, r3 = metrics(ex.c2, fine.c2), metrics(ex.c3, fine.c3)
        result.append({"n": 4, "mu": mu, "support_size": 256,
            "r2": r2["normalized_rmse"], "r3": r3["normalized_rmse"],
            "D": r3["normalized_rmse"] - r2["normalized_rmse"],
            "rk4_12_vs_24_max_c3": float(np.max(np.abs(coarse.c3 - fine.c3)))})
    return result


def local_convergence():
    cfg = ExperimentConfig(n=4, mu=3., t_max=1.5, points=2, flavors=(0, 0, 1, 1))
    coarse, zc = enumerate_psa(cfg, 12)
    fine, _ = enumerate_psa(cfg, 24)
    initial = support(cfg)
    solution = solve_ivp(lambda t, y: _rhs(cfg, y.reshape(initial.shape)).ravel(),
        (0., 1.5), initial.ravel(), method="DOP853", rtol=1e-11, atol=1e-12,
        t_eval=[0., 1.5])
    if not solution.success:
        raise RuntimeError(solution.message)
    zr = solution.y.T.reshape(2, *initial.shape)[..., 2]
    reference = _from_trajectories(cfg, zr, "PSA suporte completo DOP853", {})
    store = RunStore(ROOT / "results")
    archive_match, seed_differences = [], []
    for state in read(LOCAL)["steps"]:
        if state["action"] != "classical":
            continue
        manifest, _, arrays = store.load(state["run_id"])
        seed = manifest["config_input"]["seed"]
        signs = np.random.default_rng(seed).choice([-1., 1.], size=(4096, 4, 2))
        labels = (((signs.reshape(4096, 8) + 1) / 2).astype(np.int64) @ (1 << np.arange(8)))
        weights = np.bincount(labels, minlength=256)
        def weighted(z):
            v = z[-1]
            m1 = weights @ v / weights.sum()
            m2 = weights @ np.prod(v[:, cfg.pair_index], axis=-1) / weights.sum()
            m3 = weights @ np.prod(v[:, cfg.trio_index], axis=-1) / weights.sum()
            return connected(m1, m2, m3, 4)[1]
        a, b = weighted(zc), weighted(zr)
        archive_match.append(float(np.max(np.abs(a - arrays["psa_c3"][-1]))))
        seed_differences.append(float(np.max(np.abs(a - b))))
    return {"support_size": len(initial), "independent_solver": "DOP853 rtol=1e-11 atol=1e-12",
        "coarse_dt": 1.5 / 12, "fine_dt": 1.5 / 24,
        "coarse_vs_reference_max_c3": float(np.max(np.abs(coarse.c3 - reference.c3))),
        "fine_vs_reference_max_c3": float(np.max(np.abs(fine.c3 - reference.c3))),
        "coarse_vs_reference_trio012": float(coarse.c3[-1, 0] - reference.c3[-1, 0]),
        "reference_psa_trio012": float(reference.c3[-1, 0]),
        "archived_20_seeds_reconstruction_max_error": max(archive_match),
        "archived_seeds_max_c3_integration_difference": max(seed_differences)}


def hardware_diagnostics():
    """Análises de sensibilidade; não substituem os ICs registrados da triagem."""
    store = RunStore(ROOT / "results")
    grouped = {}
    files = {}
    for state in read(SCREEN)["steps"]:
        if state["action"] != "hardware":
            continue
        execution_path = ROOT / "results/executions" / state["execution_id"] / "execution.json"
        execution = read(execution_path)
        original = read(ROOT / "results" / execution["result"]["path"])["hardware_runs"][-1]
        _, summary, arrays = store.load(state["run_id"])
        hw = next(h for h in summary["hardware_runs"] if h["job_id"] == original["job_id"])
        version = (ROOT / "results" / state["run_id"] / "current").read_text().strip()
        moment_path = ROOT / "results" / state["run_id"] / "versions" / version / "moments.npz"
        files[str(moment_path.relative_to(ROOT))] = sha(moment_path)
        arm = f"steps{hw['steps']}/twirling{hw['gate_twirling']}"
        grouped.setdefault(arm, []).append(arrays[hw["counts_key"]])
    result = {}
    for arm, blocks in grouped.items():
        totals = np.sum(blocks, axis=0)
        rng = np.random.default_rng(97001)
        def value(c):
            return float(observable_from_counts(c, "c3", (0, 1, 2)))
        # Duas alternativas explicitam suposições diferentes: estado estacionário
        # ou variação entre jobs. Não se escolhe um IC pelo sinal obtido.
        shot = [value(rng.multinomial(int(totals.sum()), totals / totals.sum())) for _ in range(2000)]
        cluster = [value(np.sum([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))], axis=0))
                   for _ in range(2000)]
        result[arm] = {"blocks": len(blocks), "shots": int(totals.sum()), "pooled_c3": value(totals),
            "per_job_c3": [value(b) for b in blocks],
            "stationary_multinomial_c3_ci95": np.quantile(shot, [.025, .975]).tolist(),
            "job_block_only_c3_ci95": np.quantile(cluster, [.025, .975]).tolist()}
    return {"sensitivity_only": True, "arms": result, "source_moments_sha256": files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
        default=ROOT / "analysis/audits/research_review_20261107.json")
    target = parser.parse_args().output.resolve()
    if target.exists():
        raise SystemExit(f"Auditoria já existe; preserve-a: {target}")
    data = {"schema_version": 1, "status": "post_collection_diagnostics",
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "python": sys.version},
        "changes_original_results": False, "ibm_jobs_submitted": 0,
        "sources_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (
            Path(__file__), ROOT / "src/neutrinos/sim.py", ROOT / "src/neutrinos/study_analysis.py",
            SCREEN, LOCAL, PACKAGE / "reports/T03-classica-principal.json",
            PACKAGE / "reports/T03-classica-extensao.json")},
        "h1_archived_bootstrap": h1_audit(),
        "h1_n4_full_discrete_support": deterministic_h1(),
        "v2_psa_integration": local_convergence(),
        "v2_hardware_uncertainty_sensitivity": hardware_diagnostics()}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(target)
    print(json.dumps({k: v for k, v in data.items() if k in (
        "h1_n4_full_discrete_support", "v2_psa_integration")}, indent=2))


if __name__ == "__main__":
    main()
