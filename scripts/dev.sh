#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ ! -x .venv/bin/python ]]; then
  echo "Ambiente Python ausente. Crie .venv e instale o projeto conforme README.md." >&2
  exit 1
fi
if [[ ! -d app/frontend/node_modules ]]; then
  echo "Dependências Next.js ausentes. Execute: npm ci --prefix app/frontend" >&2
  exit 1
fi

PYTHONPATH=src .venv/bin/python -m uvicorn app.backend.api:app --host 127.0.0.1 --port 8000 \
  --reload --reload-dir app/backend --reload-dir src &
backend_pid=$!
cleanup() {
  kill "$backend_pid" 2>/dev/null || true
  wait "$backend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

npm run dev --prefix app/frontend
