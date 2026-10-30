"use client";

import { useRef } from "react";
import type { PointerEvent } from "react";
import type { Experiment, NeutrinoSpec } from "@/lib/types";
import { numberLabel } from "@/lib/types";

export type BoardMode = "classical" | "quantum";

function boardSize(count: number) {
  const columns = count <= 4 ? 2 : count <= 9 ? 3 : 4;
  return { columns, rows: Math.ceil(count / columns) };
}

export function arrangeNeutrinos(items: NeutrinoSpec[]): NeutrinoSpec[] {
  const { columns, rows } = boardSize(items.length);
  const columnSpacing = (100 - 80 / columns) / (columns - 1);
  return items.map((item, index) => {
    const row = Math.floor(index / columns);
    const rowSize = Math.min(columns, items.length - row * columns);
    return { ...item,
      x: 50 + (index % columns - (rowSize - 1) / 2) * columnSpacing,
      y: 100 * (row + .5) / rows,
    };
  });
}

export function normalizedFrequencies(items: NeutrinoSpec[]): number[] {
  const mean = items.reduce((sum, item) => sum + item.weight, 0) / items.length;
  return items.map((item) => item.weight / mean);
}

interface Props {
  items: NeutrinoSpec[];
  couplings: number[][];
  mode: BoardMode;
  onMode: (mode: BoardMode) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  onChange: (index: number, update: Partial<NeutrinoSpec>) => void;
  onArrange: () => void;
  onCoupling: (i: number, j: number, value: number) => void;
  selectedPair: [number, number] | null;
  onPair: (pair: [number, number] | null) => void;
  data: Experiment | null;
  dirty: boolean;
  step: number;
}

export default function NeutrinoBoard({ items, couplings, mode, onMode, onAdd, onRemove, onChange,
  onArrange, onCoupling, selectedPair, onPair, data, dirty, step }: Props) {
  const boardRef = useRef<HTMLDivElement>(null);
  const dragging = useRef<string | null>(null);
  const { columns, rows } = boardSize(items.length);
  const omega = normalizedFrequencies(items);
  const result = !dirty && data?.config.n === items.length ? (mode === "quantum" ? data.quantum?.ideal : data.classical.exact) : null;
  const pairList = items.flatMap((_, i) => items.slice(i + 1).map((_, offset) => [i, i + offset + 1] as [number, number]));

  function move(event: PointerEvent<HTMLDivElement>, index: number) {
    if (dragging.current !== items[index].id || !boardRef.current) return;
    const rect = boardRef.current.getBoundingClientRect();
    const card = event.currentTarget.parentElement;
    const xMargin = 100 * ((card?.offsetWidth ?? 148) / 2 + 10) / rect.width;
    const yMargin = 100 * ((card?.offsetHeight ?? 170) / 2 + 10) / rect.height;
    onChange(index, { x: Math.max(xMargin, Math.min(100 - xMargin, 100 * (event.clientX - rect.left) / rect.width)),
      y: Math.max(yMargin, Math.min(100 - yMargin, 100 * (event.clientY - rect.top) / rect.height)) });
  }

  return <section className="nb-board-shell" aria-label="Quadro interativo de neutrinos">
    <div className="nb-board-toolbar"><div><span className="nb-kicker">01 / CONSTRUÇÃO DO MODELO</span><h2>Quadro de neutrinos</h2><p>Adicione partículas, ajuste o sabor e a frequência, e escolha os acoplamentos.</p></div>
      <div className="nb-board-actions"><div className="nb-segment" role="group" aria-label="Visualização da evolução"><button className={mode === "classical" ? "selected" : ""} onClick={() => onMode("classical")}>Clássico</button><button className={mode === "quantum" ? "selected" : ""} onClick={() => onMode("quantum")}>Quântico</button></div><button className="nb-button nb-button-outline" onClick={onArrange}>Organizar</button><button className="nb-button nb-button-primary" onClick={onAdd} disabled={items.length >= 16}>+ Adicionar neutrino</button></div></div>
    <div className="nb-board-status"><span><b>{items.length}</b> neutrinos</span><span><b>{items.length}</b> variáveis de Bloch</span><span><b>{items.length}</b> qubits</span><span>dimensão <b>2^{items.length} = {2 ** items.length}</b></span><span className="nb-board-model">{dirty ? "Configuração alterada · execute novamente" : result ? `Evolução em τ = ${numberLabel(data?.times[step] ?? 0, 2)}` : mode === "quantum" ? "Execute o circuito para ver a evolução" : "Pronto para simular"}</span></div>
    <div className="nb-board-viewport"><div className="nb-board-canvas" ref={boardRef}
      style={{ minHeight: Math.max(450, rows * 230), minWidth: columns * 220 }}>
      <div className="nb-board-grid" />
      <svg className="nb-board-edges" aria-label="Acoplamentos entre neutrinos">
        {pairList.map(([i, j]) => {
          const g = couplings[i][j];
          const active = selectedPair?.[0] === i && selectedPair?.[1] === j;
          return <g key={`${items[i].id}-${items[j].id}`}>
            {g !== 0 && <line x1={`${items[i].x}%`} y1={`${items[i].y}%`} x2={`${items[j].x}%`} y2={`${items[j].y}%`}
              stroke={g > 0 ? "#9f78f3" : "#d493af"} strokeWidth={active ? 3 : 1.4 + Math.abs(g)} opacity={active ? .9 : .42} />}
            <line x1={`${items[i].x}%`} y1={`${items[i].y}%`} x2={`${items[j].x}%`} y2={`${items[j].y}%`}
              stroke="transparent" strokeWidth="14" className="nb-edge-hit" onClick={() => onPair([i, j])}>
              <title>{`Acoplamento g${i}${j} = ${g}. Clique para editar.`}</title>
            </line>
          </g>;
        })}
      </svg>
      {items.map((item, index) => {
        const pe = result?.pe[step]?.[index];
        return <div key={item.id} className={`nb-particle ${mode === "quantum" ? "nb-quantum" : ""}`}
          style={{ left: `${item.x}%`, top: `${item.y}%` }}>
          <div className="nb-particle-top" onPointerDown={(event) => { dragging.current = item.id; event.currentTarget.setPointerCapture(event.pointerId); }}
            onPointerMove={(event) => move(event, index)} onPointerUp={() => { dragging.current = null; }} onPointerCancel={() => { dragging.current = null; }}>
            <span className="nb-particle-index">ν<sub>{index}</sub></span><span className="nb-qubit-tag">q<sub>{index}</sub></span>
            <button type="button" aria-label={`Remover neutrino ${index}`} disabled={items.length <= 2} onPointerDown={(event) => event.stopPropagation()} onClick={() => onRemove(index)}>×</button>
          </div>
          <div className="nb-particle-body"><label>Estado inicial<select aria-label={`Sabor inicial do neutrino ${index}`} value={item.flavor} onChange={(event) => onChange(index, { flavor: Number(event.target.value) as 0 | 1 })}><option value={0}>νₑ · |0⟩</option><option value={1}>νₓ · |1⟩</option></select></label>
            <label>Peso da frequência<input aria-label={`Frequência relativa do neutrino ${index}`} type="number" min="0.1" max="5" step="0.1" value={item.weight} onChange={(event) => onChange(index, { weight: Number(event.target.value) })} /></label></div>
          <div className="nb-particle-foot"><span>ω<sub>{index}</sub>/ω̄ = <b>{numberLabel(omega[index], 2)}</b></span><span>{pe === undefined ? "Pₑ —" : `Pₑ ${numberLabel(pe, 2)}`}</span></div>
          {pe !== undefined && <div className="nb-pe-track"><i style={{ width: `${Math.max(0, Math.min(100, pe * 100))}%` }} /></div>}
        </div>;
      })}
    </div></div>
    <div className="nb-board-bottom"><div><strong>Ligação selecionada</strong>{selectedPair ? <span>ν{selectedPair[0]} ↔ ν{selectedPair[1]} · g<sub>{selectedPair[0]}{selectedPair[1]}</sub> = {numberLabel(couplings[selectedPair[0]][selectedPair[1]], 1)}</span> : <span>Clique em uma linha para ajustar o acoplamento entre duas partículas.</span>}</div>
      {selectedPair && <div className="nb-coupling-control"><input aria-label="Intensidade do acoplamento" type="range" min="-2" max="2" step="0.1" value={couplings[selectedPair[0]][selectedPair[1]]} onChange={(event) => onCoupling(...selectedPair, Number(event.target.value))} /><button onClick={() => onCoupling(...selectedPair, 0)}>Desligar</button></div>}
    </div>
    {mode === "quantum" && items.length > 8 && <div className="nb-inline-note">O motor interativo de circuito aceita até 8 qubits. A evolução clássica continua disponível até 16 neutrinos.</div>}
  </section>;
}
