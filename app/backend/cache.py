"""Cache verificável de cálculos determinísticos; medições/sementes não são reutilizadas."""
from dataclasses import asdict
import hashlib
import json
import os
import tempfile
from pathlib import Path
import numpy as np
from neutrinos.sim import MomentSeries
from . import audit


def arrays(root: Path, kind: str, config, options: dict, compute):
    physical = asdict(config)
    physical.pop('seed')
    identity = {'kind': kind, 'config': physical, 'options': options,
                'environment': audit.environment()['fingerprint']}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    folder = root/'_cache'/key
    folder.mkdir(parents=True, exist_ok=True)
    path, index = folder/'arrays.npz', folder/'cache.json'
    if index.exists():
        meta = json.loads(index.read_text())
        if audit.file_hash(path) != meta['sha256']:
            raise ValueError(f'Cache alterado: {path}')
        with np.load(path, allow_pickle=False) as data:
            return {k: data[k] for k in data.files}, True
    values = compute()
    fd, temporary = tempfile.mkstemp(suffix='.npz', dir=folder)
    os.close(fd)
    try:
        np.savez_compressed(temporary, **values)
        os.replace(temporary, path)
        audit.atomic_json(index, {'identity': identity, 'sha256': audit.file_hash(path)})
    finally:
        Path(temporary).unlink(missing_ok=True)
    return values, False


def series(root, kind, config, options, compute):
    def encode():
        result = compute()
        return {**{k: getattr(result, k) for k in ('m1','m2','m3','bloch')
                   if getattr(result, k) is not None},
                'meta': np.array(json.dumps({'method': result.method, 'diagnostics': result.diagnostics}))}
    values, hit = arrays(root, kind, config, options, encode)
    meta = json.loads(str(values.pop('meta')))
    return MomentSeries(config.times, values['m1'], values['m2'], values['m3'],
                        config.pair_index, config.trio_index, meta['method'],
                        meta['diagnostics'], bloch=values.get('bloch')), hit
