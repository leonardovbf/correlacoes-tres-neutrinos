"""Persistência versionada e atômica de execuções locais."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
from pathlib import Path
from uuid import uuid4

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
RUN_ID = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


class RunNotFound(KeyError):
    pass


class RunStore:
    def __init__(self, root: Path = RESULTS):
        self.root = root
        self.lock = threading.RLock()

    def _path(self, run_id: str) -> Path:
        if not RUN_ID.fullmatch(run_id):
            raise RunNotFound(run_id)
        path = self.root / run_id
        if not path.is_dir():
            raise RunNotFound(run_id)
        return path

    @staticmethod
    def _write_version(path: Path, manifest: dict, summary: dict, arrays: dict[str, np.ndarray]) -> None:
        path.mkdir(parents=True)
        (path / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
        )
        (path / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8"
        )
        np.savez_compressed(path / "moments.npz", **arrays)

    def create(self, manifest: dict, summary: dict, arrays: dict[str, np.ndarray]) -> str:
        from datetime import datetime, timezone

        self.root.mkdir(parents=True, exist_ok=True)
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=self.root))
        try:
            self._write_version(stage / "versions" / "0001", manifest, summary, arrays)
            (stage / "current").write_text("0001", encoding="ascii")
            os.replace(stage, self.root / run_id)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        return run_id

    def _version_path(self, run_id: str) -> Path:
        path = self._path(run_id)
        version = (path / "current").read_text(encoding="ascii").strip()
        if not re.fullmatch(r"[0-9]{4}", version):
            raise ValueError("Ponteiro de revisão inválido")
        return path / "versions" / version

    def load_metadata(self, run_id: str) -> tuple[dict, dict]:
        source = self._version_path(run_id)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((source / "summary.json").read_text(encoding="utf-8"))
        return manifest, summary

    def load(self, run_id: str) -> tuple[dict, dict, dict[str, np.ndarray]]:
        source = self._version_path(run_id)
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((source / "summary.json").read_text(encoding="utf-8"))
        with np.load(source / "moments.npz", allow_pickle=False) as archive:
            arrays = {name: archive[name] for name in archive.files}
        return manifest, summary, arrays

    def update(self, run_id: str, manifest: dict, summary: dict,
               arrays: dict[str, np.ndarray]) -> None:
        path = self._path(run_id)
        current = int((path / "current").read_text(encoding="ascii").strip())
        next_number = current + 1
        while (path / "versions" / f"{next_number:04d}").exists():
            next_number += 1
        next_version = f"{next_number:04d}"
        stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=path / "versions"))
        try:
            self._write_version(stage / "payload", manifest, summary, arrays)
            os.replace(stage / "payload", path / "versions" / next_version)
            pointer = path / "current.tmp"
            pointer.write_text(next_version, encoding="ascii")
            os.replace(pointer, path / "current")
        finally:
            shutil.rmtree(stage, ignore_errors=True)
