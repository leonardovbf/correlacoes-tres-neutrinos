#!/usr/bin/env python3
"""Extrai vetores da Fig. 2(c), sem ajustar coordenadas aos nossos resultados.
Requer o PDF v2 e Poppler (pdftocairo). Não baixa nem altera a publicação.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLORS = ['rgb(0%, 0%, 0%)', 'rgb(100%, 0%, 0%)',
          'rgb(0%, 0%, 100%)', 'rgb(0%, 50.195312%, 0%)']
# Eixos do painel c no sistema de coordenadas vetorial da página 7.
X0, X1 = 353.7773436488, 554.4335937268
Y_ONE, Y_ZERO = 290.23437497, 361.833593858


def extract(pdf, output):
    with tempfile.TemporaryDirectory() as temp:
        svg = Path(temp) / 'page7.svg'
        subprocess.run(['pdftocairo', '-f', '7', '-l', '7', '-svg', str(pdf), str(svg)], check=True)
        rows = []
        for e in ET.parse(svg).iter():
            if not e.tag.endswith('path'):
                continue
            color = e.get('fill')
            if color in COLORS and not e.get('transform'):
                coords = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', e.get('d', ''))]
                xs, ys = coords[::2], coords[1::2]
                if not xs:
                    continue
                x, y = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
                if X0-1 < x < X1+1 and Y_ONE-2 < y < 399:
                    rows.append(('exact', COLORS.index(color), 200*(x-X0)/(X1-X0),
                                 (Y_ZERO-y)/(Y_ZERO-Y_ONE)))
            if (e.get('fill') == 'none' and e.get('stroke') in COLORS
                    and len(e.get('d', '')) > 800):
                coords = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', e.get('d', ''))]
                if not 379 < coords[1] < 382:
                    continue
                for u, v in zip(coords[::2], coords[1::2]):
                    x, y = .3404*u + 317.014, -.3404*v + 419.698
                    rows.append(('psa', COLORS.index(e.get('stroke')),
                                 200*(x-X0)/(X1-X0), (Y_ZERO-y)/(Y_ZERO-Y_ONE)))
        rows.sort()
        counts = {f'{method}_{i}': sum(row[:2] == (method, i) for row in rows)
                  for method in ('exact', 'psa') for i in range(4)}
        if any(v < 50 for v in counts.values()):
            raise ValueError(f'Extração incompleta: {counts}')
        output.mkdir(parents=True, exist_ok=True)
        with (output/'figure2c.csv').open('w') as f:
            writer = csv.writer(f)
            writer.writerow(['method', 'neutrino', 't_paper', 'z'])
            writer.writerows((m, i, f'{t:.7f}', f'{z:.7f}') for m,i,t,z in rows)
        metadata = {'source': 'https://arxiv.org/pdf/2409.20215v2',
            'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(), 'page': 7,
            'figure': '2(c)', 'method': 'símbolos: centro da caixa vetorial; PSA: vértices da linha',
            'colors_neutrinos': dict(zip(COLORS, range(4))), 'counts': counts,
            'axes_page_points': {'x_t0': X0, 'x_t200': X1, 'y_z1': Y_ONE, 'y_z0': Y_ZERO},
            'digitization_absolute_uncertainty_z': .02,
            'acceptance_predeclared': {'exact_max_abs': .02, 'psa_max_abs': .06},
            'acceptance_rationale': 'Exato: resolução dos símbolos. PSA: 0.02 de extração mais 0.04 de variação Monte Carlo entre amostras independentes de 10000; critério operacional, não inferência de K3.',
            'scope': 'Referência extraída da figura; não são dados brutos disponibilizados pelos autores.'}
        metadata['csv_sha256'] = hashlib.sha256((output/'figure2c.csv').read_bytes()).hexdigest()
        (output/'source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
        print(counts)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'data/benchmarks/lacroix2024')
    args = parser.parse_args()
    extract(args.pdf, args.output)
