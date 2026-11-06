"use client";

import type { ExecutionEvent, Job } from "@/lib/types";
import { numberLabel } from "@/lib/types";

interface Props { job: Job | null; trace: ExecutionEvent[]; }

const stageLabels: Record<string, string> = {
  config: "Preparar modelo", exact: "Evolução exata", mean: "Campo médio",
  psa: "Espaço de fase", quality: "Verificar invariantes", persist: "Registrar dados",
  quantum: "Circuito Trotter", compare: "Comparar com exato",
  ibm: "Enviar à IBM Quantum",
};
export default function ExecutionPanel({ job, trace }: Props) {
  const events = job?.events.length ? job.events : trace;

  return <section className="nb-execution nb-panel" aria-label="Etapas da execução">
    <div className="nb-panel-title"><div><span className="nb-kicker">02 / EXECUÇÃO</span><h2>Motor Python</h2></div>
      <span className={`nb-job-state ${job?.status ?? "idle"}`}>{job?.status === "running" ? "Calculando" : job?.status === "queued" ? "Na fila" : job?.status === "failed" ? "Falhou" : job?.status === "completed" || trace.length ? "Concluído" : "Aguardando"}</span></div>
    <p className="nb-panel-description">Etapas registradas pelo backend durante o cálculo.</p>
    {events.length ? <ol className="nb-event-list">{events.map((event) => <li key={`${event.order}-${event.stage}-${event.status}`}>
      <div className="nb-event">
        <span className={`nb-event-dot ${event.status}`} /><span className="nb-event-main"><strong>{stageLabels[event.stage] ?? event.stage}</strong><small>{event.message}</small></span>
        <time>{numberLabel(event.elapsed_ms / 1000, 2)} s</time>
      </div></li>)}</ol> : <div className="nb-log-empty">A execução aparece aqui depois de iniciar a simulação.</div>}
    {job?.status === "failed" && <div className="nb-error" role="alert">{job.error}</div>}
  </section>;
}
