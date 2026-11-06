"""Processo isolado para circuitos Qiskit e simulação de ruído Aer.

Recebe JSON por stdin e devolve JSON por stdout. Uma falha nativa do Aer não
encerra o processo da interface Streamlit.
"""

from __future__ import annotations

import json
import sys

from .qiskit_backend import first_interval_probabilities, simulate_gate_noise
from .sim import ExperimentConfig


def main() -> None:
    request = json.load(sys.stdin)
    config = ExperimentConfig.from_dict(request["config"])
    if request["action"] == "first_interval":
        circuit, probabilities = first_interval_probabilities(config, request["steps_per_interval"], request.get("interval_index", 1))
        response = {"probabilities": probabilities.tolist(), "size": circuit.size(),
                    "diagram": str(circuit.draw(output="text", fold=110)) if request.get("interval_index",1)==1 else "Circuito completo arquivado pela receita; diagrama extenso omitido"}
    elif request["action"] == "gate_noise":
        counts, metadata = simulate_gate_noise(
            config,
            interval_index=request["interval_index"],
            steps_per_interval=request["steps_per_interval"],
            shots=request["shots"],
            single_qubit_error=request["single_qubit_error"],
            two_qubit_error=request["two_qubit_error"],
            readout_error=request["readout_error"],
        )
        response = {"counts": counts.tolist(), "metadata": metadata}
    elif request["action"] == "mitigation":
        response = {"counts": {}, "metadata": {}}
        budget = request["shots"]
        for offset, (label, shots, calibration) in enumerate((
                ("raw", budget, None), ("signal", 3*budget//4, None),
                ("zero", budget//8, 0), ("one", budget//8, 1))):
            counts, metadata = simulate_gate_noise(config, request["interval_index"],
                request["steps_per_interval"], shots, request["single_qubit_error"],
                request["two_qubit_error"], request["readout_error"],
                calibration_state=calibration, seed_offset=offset*1000000)
            response["counts"][label] = counts.tolist()
            response["metadata"][label] = metadata
    else:
        raise ValueError("Ação Qiskit desconhecida")
    json.dump(response, sys.stdout)


if __name__ == "__main__":
    main()
