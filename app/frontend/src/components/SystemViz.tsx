"use client";

import type { Experiment } from "@/lib/types";
import { numberLabel } from "@/lib/types";

const CYAN = "#8f62f3";
const CORAL = "#d493af";
const GOLD = "#a6e0d7";

function blend(value: number) {
  const ratio = Math.max(0, Math.min(1, value));
  return `hsl(${268 - ratio * 112} 43% ${56 + ratio * 10}%)`;
}

function Network({ data, step }: { data: Experiment; step: number }) {
  const n = data.config.n;
  const positions = Array.from({ length: n }, (_, i) => {
    const angle = 2 * Math.PI * i / n - Math.PI / 2;
    return { x: 160 + 105 * Math.cos(angle), y: 148 + 105 * Math.sin(angle) };
  });
  const g = data.config.g_matrix;
  const maxG = Math.max(1, ...g.flat().map(Math.abs));
  return <svg viewBox="0 0 320 295" className="system-svg" role="img" aria-label="Rede de interações entre neutrinos">
    {data.pairs.map(([i, j]) => {
      const strength = Math.abs(g[i][j]) / maxG;
      return strength ? <line key={`${i}-${j}`} x1={positions[i].x} y1={positions[i].y} x2={positions[j].x} y2={positions[j].y}
        stroke={g[i][j] >= 0 ? CYAN : CORAL} strokeWidth={1 + strength * 2.5} opacity={0.15 + strength * 0.5} /> : null;
    })}
    {positions.map((position, i) => <g key={i}>
      <circle cx={position.x} cy={position.y} r={n > 10 ? 17 : 22} fill={blend(data.classical.exact.pe[step][i])} stroke="#e2edf5" strokeWidth="2" />
      <text x={position.x} y={position.y + 5} textAnchor="middle" fill="#091725" fontSize="14" fontWeight="700">{i}</text>
    </g>)}
  </svg>;
}

function VectorPanel({ data, step, field = false }: { data: Experiment; step: number; field?: boolean }) {
  const bloch = data.classical.mean.bloch?.[step] ?? [];
  const selected = 0;
  const vacuum = data.config.b_field.map((v) => data.config.omega[selected] * v);
  const effective = [...vacuum];
  if (field) {
    bloch.forEach((spin, j) => {
      effective.forEach((_, axis) => { effective[axis] += data.config.mu / (2 * data.config.n) * data.config.g_matrix[selected][j] * spin[axis]; });
    });
  }
  const vectors = field ? [
    { x: vacuum[0], z: vacuum[2], color: "#c4b3ed", label: "B" },
    { x: effective[0], z: effective[2], color: GOLD, label: "h₀" },
  ] : bloch.map((spin, i) => ({ x: spin[0], z: spin[2], color: i % 2 ? GOLD : CYAN, label: String(i) }));
  const scale = field ? 62 : 96;
  return <svg viewBox="0 0 320 295" className="system-svg" role="img" aria-label={field ? "Campos de vácuo e efetivo" : "Vetores de sabor no plano XZ"}>
    <line x1="45" y1="148" x2="285" y2="148" stroke="#35516b" />
    <line x1="160" y1="27" x2="160" y2="267" stroke="#35516b" />
    {!field && <circle cx="160" cy="148" r="96" fill="none" stroke="#385573" strokeDasharray="4 5" />}
    {vectors.map((vector, i) => {
      const endX = 160 + vector.x * scale;
      const endY = 148 - vector.z * scale;
      const angle = Math.atan2(endY - 148, endX - 160);
      return <g key={i}>
        <line x1="160" y1="148" x2={endX} y2={endY} stroke={vector.color} strokeWidth="3" strokeLinecap="round" />
        <path d={`M${endX},${endY} l${-11 * Math.cos(angle - .45)},${-11 * Math.sin(angle - .45)} M${endX},${endY} l${-11 * Math.cos(angle + .45)},${-11 * Math.sin(angle + .45)}`}
          fill="none" stroke={vector.color} strokeWidth="3" />
        <text x={endX + 10} y={endY - 8} fill={vector.color} fontSize="13" fontWeight="700">{vector.label}</text>
      </g>;
    })}
    <text x="284" y="140" fill="#8ca3b9" fontSize="13">X</text>
    <text x="169" y="34" fill="#8ca3b9" fontSize="13">Z</text>
  </svg>;
}

export default function SystemViz({ data, step, onStep }: { data: Experiment; step: number; onStep: (step: number) => void }) {
  const c2 = data.classical.exact.c2[step];
  const pairMap = new Map(data.pairs.map((pair, index) => [`${pair[0]}-${pair[1]}`, c2[index]]));
  const maxPair = Math.max(0.05, ...c2.map(Math.abs));
  const trios = data.trios.map((indices, i) => ({ label: indices.join("·"), value: data.classical.exact.c3[step][i] }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 6);
  const maxTrio = Math.max(0.05, ...trios.map((x) => Math.abs(x.value)));
  return <>
    <div className="time-control panel"><div><span className="eyebrow">EXPLORAR A DINÂMICA</span><h3>Instante da simulação</h3></div>
      <div className="time-slider"><div className="time-labels"><span>τ 0.00</span><strong>τ {numberLabel(data.times[step], 2)}</strong><span>τ {numberLabel(data.times.at(-1) ?? 0, 2)}</span></div>
      <input aria-label="Instante da simulação" type="range" min="0" max={data.times.length - 1} value={step} onChange={(event) => onStep(Number(event.target.value))} /></div>
      <span className="step-badge">{step + 1} / {data.times.length}</span>
    </div>
    <div className="system-grid">
      <div className="panel viz-panel"><div className="panel-head"><div><span className="eyebrow">TOPOLOGIA</span><h3>Rede de interações</h3></div><span className="legend-dot cyan" /></div><Network data={data} step={step} /><p>Arestas: intensidade |gᵢⱼ|. Cor dos nós: P(νₑ) exata.</p></div>
      <div className="panel viz-panel"><div className="panel-head"><div><span className="eyebrow">CAMPO MÉDIO</span><h3>Vetores de sabor</h3></div><span className="legend-dot gold" /></div><VectorPanel data={data} step={step} /><p>Projeção dos vetores de Bloch no plano XZ.</p></div>
      <div className="panel viz-panel"><div className="panel-head"><div><span className="eyebrow">HAMILTONIANO</span><h3>Campos em ν₀</h3></div><span className="legend-dot blue" /></div><VectorPanel data={data} step={step} field /><p>B: termo de vácuo. h₀: campo efetivo com interações.</p></div>
    </div>
    <div className="system-grid lower">
      <div className="panel correlation-panel"><div className="panel-head"><div><span className="eyebrow">DOIS CORPOS</span><h3>Correlações conectadas C²ᶻᶻ</h3></div></div>
        <div className="matrix" style={{ gridTemplateColumns: `repeat(${data.config.n}, 1fr)` }}>
          {Array.from({ length: data.config.n * data.config.n }, (_, index) => {
            const i = Math.floor(index / data.config.n), j = index % data.config.n;
            const value = i === j ? null : pairMap.get(`${Math.min(i, j)}-${Math.max(i, j)}`) ?? 0;
            const alpha = value === null ? 0 : Math.min(.85, .12 + .7 * Math.abs(value) / maxPair);
            return <span key={index} title={value === null ? `ν${i}` : `ν${i} · ν${j}: ${numberLabel(value, 4)}`}
              style={{ background: value === null ? "#343039" : value >= 0 ? `rgba(143,98,243,${alpha})` : `rgba(212,147,175,${alpha})` }} />;
          })}
        </div><div className="matrix-caption"><span>negativa</span><span>positiva</span></div>
      </div>
      <div className="panel correlation-panel trio-panel"><div className="panel-head"><div><span className="eyebrow">TRÊS CORPOS</span><h3>Cumulantes conectados K³ᶻᶻᶻ</h3></div></div>
        {trios.length ? trios.map((trio) => <div className="trio-row" key={trio.label}><span>ν {trio.label}</span><div className="trio-track"><i style={{ width: `${Math.abs(trio.value) / maxTrio * 100}%`, background: trio.value >= 0 ? CYAN : CORAL }} /></div><strong>{numberLabel(trio.value, 4)}</strong></div>)
          : <p>São necessários pelo menos três neutrinos.</p>}
        <p className="note">A intensidade das arestas representa acoplamento; estes painéis mostram correlações produzidas pela evolução exata.</p>
      </div>
    </div>
  </>;
}
