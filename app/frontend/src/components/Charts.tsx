"use client";

import { numberLabel } from "@/lib/types";

export interface PlotLine {
  name: string;
  values: number[];
  color: string;
  dash?: string;
  band?: { lower: number[]; upper: number[] };
}

interface PlotProps {
  times: number[];
  lines: PlotLine[];
  ylabel: string;
  fixedProbability?: boolean;
  compact?: boolean;
  playhead?: number;
}

export function LinePlot({ times, lines, ylabel, fixedProbability = false, compact = false, playhead }: PlotProps) {
  const width = 760;
  const height = compact ? 248 : 328;
  const p = { left: 56, right: 24, top: 20, bottom: 42 };
  const all = lines.flatMap((line) => [
    ...line.values,
    ...(line.band?.lower ?? []),
    ...(line.band?.upper ?? []),
  ]).filter(Number.isFinite);
  const actualMin = all.length ? Math.min(...all) : 0;
  const actualMax = all.length ? Math.max(...all) : 1;
  const span = Math.max(actualMax - actualMin, 0.03);
  const ymin = fixedProbability ? -0.04 : Math.min(0, actualMin - span * 0.14);
  const ymax = fixedProbability ? 1.04 : Math.max(0.02, actualMax + span * 0.14);
  const xmin = times[0] ?? 0;
  const xmax = times[times.length - 1] ?? 1;
  const x = (value: number) => p.left + ((value - xmin) / Math.max(xmax - xmin, 1e-9)) * (width - p.left - p.right);
  const y = (value: number) => height - p.bottom - ((value - ymin) / (ymax - ymin)) * (height - p.top - p.bottom);
  const path = (values: number[]) => values.map((value, i) => `${i ? "L" : "M"}${x(times[i]).toFixed(2)},${y(value).toFixed(2)}`).join(" ");
  const area = (lower: number[], upper: number[]) => {
    if (lower.length !== times.length || upper.length !== times.length) return "";
    const top = upper.map((value, i) => `${i ? "L" : "M"}${x(times[i]).toFixed(2)},${y(value).toFixed(2)}`).join(" ");
    const bottom = [...lower].reverse().map((value, reverseIndex) => {
      const i = lower.length - 1 - reverseIndex;
      return `L${x(times[i]).toFixed(2)},${y(value).toFixed(2)}`;
    }).join(" ");
    return `${top} ${bottom} Z`;
  };

  return <div className="plot-wrap">
    <svg className="plot" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Gráfico de ${ylabel} ao longo do tempo`}>
      {[0, 1, 2, 3, 4].map((i) => {
        const value = ymin + (ymax - ymin) * i / 4;
        const yy = y(value);
        return <g key={`y${i}`}><line x1={p.left} x2={width - p.right} y1={yy} y2={yy} stroke="#404040" strokeDasharray="3 5" />
          <text x={p.left - 10} y={yy + 4} textAnchor="end" fill="#aaa6b0" fontSize="12">{numberLabel(value, 2)}</text></g>;
      })}
      {[0, 1, 2, 3, 4].map((i) => {
        const value = xmin + (xmax - xmin) * i / 4;
        const xx = x(value);
        return <g key={`x${i}`}><line x1={xx} x2={xx} y1={p.top} y2={height - p.bottom} stroke="#404040" strokeDasharray="3 6" />
          <text x={xx} y={height - 13} textAnchor="middle" fill="#aaa6b0" fontSize="12">{numberLabel(value, 1)}</text></g>;
      })}
      <text x={width / 2} y={height - 2} textAnchor="middle" fill="#bcb8c2" fontSize="12">Tempo adimensional ω̄t</text>
      <text x="17" y={height / 2} textAnchor="middle" fill="#bcb8c2" fontSize="12" transform={`rotate(-90 17 ${height / 2})`}>{ylabel}</text>
      {lines.map((line) => <g key={line.name}>
        {line.band && <path d={area(line.band.lower, line.band.upper)} fill={line.color} opacity="0.14" />}
        <path d={path(line.values)} fill="none" stroke={line.color} strokeWidth="2.5" strokeDasharray={line.dash} strokeLinecap="round" strokeLinejoin="round" />
      </g>)}
      {playhead !== undefined && <g><line x1={x(times[Math.min(playhead, times.length - 1)])} x2={x(times[Math.min(playhead, times.length - 1)])}
        y1={p.top} y2={height - p.bottom} stroke="#c5b0fa" strokeWidth="1.5" strokeDasharray="5 4" />
        <circle cx={x(times[Math.min(playhead, times.length - 1)])} cy={p.top + 2} r="4" fill="#c5b0fa" /></g>}
    </svg>
    <div className="plot-legend">{lines.map((line) => <span key={line.name}><i style={{ background: line.color }} />{line.name}</span>)}</div>
  </div>;
}
