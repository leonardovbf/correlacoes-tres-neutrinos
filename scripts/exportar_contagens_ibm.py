"""Exporta as contagens brutas dos 80 jobs IBM do caso principal para dados/ibm/.

Só consulta jobs já concluídos; não envia circuitos nem consome créditos.
Requer IBM_QUANTUM_API_KEY (e, de preferência, IBM_QUANTUM_INSTANCE) no .env da raiz.

Uso: PYTHONPATH=src:. python scripts/exportar_contagens_ibm.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
TEMPOS = next((RAIZ / "analysis" / "article_packages").glob("*/tables/ibm_job_timing.csv"))
SAIDA = RAIZ / "dados" / "ibm" / "contagens_caso_principal.json"


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    from app.backend.ibm_runtime import fetch

    jobs = list(csv.DictReader(TEMPOS.open(encoding="utf-8")))
    registros = []
    for numero, job in enumerate(jobs, 1):
        estado, contagens = fetch(job["job_id"], 4)
        if contagens is None:
            raise SystemExit(f"Job {job['job_id']} em estado {estado}; nada foi gravado.")
        if int(contagens.sum()) != int(job["shots"]):
            raise SystemExit(f"Job {job['job_id']}: {contagens.sum()} contagens, esperado {job['shots']}.")
        registros.append({"job_id": job["job_id"], "papel": job["role"], "medicoes": int(job["shots"]),
                          "inicio": job["running"], "fim": job["finished"],
                          "contagens": {format(i, "04b"): int(c) for i, c in enumerate(contagens) if c}})
        print(f"[{numero}/{len(jobs)}] {job['role']:<16} {job['job_id']}", flush=True)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({
        "backend": "ibm_kingston",
        "caso": {"n": 4, "lambda": 3.0, "tau": 2.0, "trio": [0, 1, 2], "passos_trotter": 112},
        "ordem_dos_bits": "cadeia de bits Qiskit; o caractere mais à direita é o qubit 0",
        "papeis": {"raw": "sinal, método bruto (m medições)", "signal": "sinal, método mitigado (3m/4)",
                   "calibration_zero": "calibração |0000⟩ (m/8)", "calibration_one": "calibração |1111⟩ (m/8)"},
        "jobs": registros}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
