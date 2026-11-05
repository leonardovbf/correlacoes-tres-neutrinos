#!/usr/bin/env python3
"""Executa ou reproduz protocolos a partir da raiz ou de outro diretório."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from app.backend import protocol, service
from app.backend.storage import RunStore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Executar um protocolo JSON")
    run.add_argument("protocol", type=Path)
    run.add_argument("--resume", type=Path, help="run.json de uma tentativa anterior")
    replay = commands.add_parser("replay", help="Repetir execution.json e comparar os resultados")
    replay.add_argument("execution", type=Path)
    replay.add_argument("--atol", type=float, default=1e-10)
    replay.add_argument("--rtol", type=float, default=1e-8)
    for command in (run, replay):
        command.add_argument("--output", type=Path, default=ROOT / "results")
        command.add_argument("--allow-environment-drift", action="store_true",
                             help="Permitir diferenças de fontes/dependências e registrá-las")
        command.add_argument("--allow-hardware", action="store_true",
                             help="Autorizar novos jobs IBM que podem consumir créditos")
    args = parser.parse_args()
    service.store = RunStore(args.output.resolve())
    options = {"allow_environment_drift": args.allow_environment_drift,
               "allow_hardware": args.allow_hardware,
               "progress": lambda message: print(message, flush=True)}
    try:
        if args.command == "run":
            result = protocol.run_protocol(protocol.read_protocol(args.protocol), resume=args.resume, **options)
        else:
            if args.atol < 0 or args.rtol < 0:
                raise ValueError("Tolerâncias devem ser não negativas")
            result = protocol.replay_execution(args.execution, atol=args.atol, rtol=args.rtol, **options)
    except (ValueError, OSError, protocol.ProtocolFailed) as exc:
        print(f"Falha: {exc}", file=sys.stderr)
        if isinstance(exc, protocol.ProtocolFailed):
            print(f"Registro: {exc.record_path}", file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"], "record_path": result["record_path"],
                      "steps": [{key: step[key] for key in ("id", "run_id", "execution_id")}
                                for step in result["steps"]],
                      "comparison": result.get("comparison")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
