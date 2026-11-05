"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Area, CircuitResult, Experiment, HardwareRun, IbmBackend, IbmStatus, Job, NeutrinoSpec, Observable, QuantumOptions, Series } from "@/lib/types";
import { numberLabel, observableLabels } from "@/lib/types";
import { LinePlot, type PlotLine } from "./Charts";
import NeutrinoBoard, { arrangeNeutrinos, normalizedFrequencies, type BoardMode } from "./NeutrinoBoard";
import ExecutionPanel from "./ExecutionPanel";
import SystemViz from "./SystemViz";

type Settings = { mu: number; theta: number; tMax: number; points: number; seed: number; trajectories: number; substeps: number };
const defaults: Settings = { mu: 1, theta: .2, tMax: 8, points: 81, seed: 42, trajectories: 256, substeps: 4 };
const initialItems = arrangeNeutrinos([.7, .9, 1.1, 1.3].map((weight, i) => ({ id: `nu-${i}`, flavor: (i < 2 ? 0 : 1) as 0 | 1, weight, x: 0, y: 0 })));
const initialCouplings = Array.from({ length: 4 }, (_, i) => Array.from({ length: 4 }, (_, j) => i === j ? 0 : 1));
const palette = { exact: "#e9e7ed", mean: "#96929f", psa: "#8f62f3", ideal: "#a6e0d7", measured: "#c5b0fa" };
const hardwareStatusLabels: Record<string, string> = {
  INITIALIZING: "Preparando na IBM", QUEUED: "Na fila da IBM", RUNNING: "Executando na IBM",
  DONE: "Concluído", ERROR: "Falhou", CANCELLED: "Cancelado",
};
const navigation: { area: Area; label: string; subtitle: string }[] = [
  { area: "board", label: "Quadro", subtitle: "Partículas e evolução" },
  { area: "classical", label: "Clássica", subtitle: "Exato · campo médio · PSA" },
  { area: "quantum", label: "Quântica", subtitle: "Trotter · IBM Quantum" },
  { area: "system", label: "Sistema", subtitle: "Campos · correlações" },
];

function Field({ label, value, onChange, min, max, step, hint }: { label: string; value: number; onChange: (value: number) => void; min: number; max: number; step: number; hint?: string }) {
  return <label className="nb-field"><span>{label}</span><input type="number" value={value} min={min} max={max} step={step} onChange={(event) => onChange(Number(event.target.value))} />{hint && <small>{hint}</small>}</label>;
}

function ResultPlot({ data, kind, index, quantum = false, playhead }: { data: Experiment; kind: Observable; index: number; quantum?: boolean; playhead?: number }) {
  const series: { label: string; value: Series | undefined; color: string; dash?: string }[] = quantum ? [
    { label: "Exato", value: data.classical.exact, color: palette.exact },
    { label: "Circuito ideal", value: data.quantum?.ideal, color: palette.ideal },
    { label: "Medições", value: data.quantum?.measured, color: palette.measured, dash: "5 4" },
  ] : [
    { label: "Exato", value: data.classical.exact, color: palette.exact },
    { label: "Campo médio", value: data.classical.mean, color: palette.mean, dash: "5 5" },
    { label: "PSA", value: data.classical.psa, color: palette.psa },
  ];
  const lines: PlotLine[] = series.filter((item) => item.value).map((item) => ({ name: item.label, values: item.value![kind].map((row) => row[index]), color: item.color, dash: item.dash }));
  return <LinePlot times={data.times} lines={lines} ylabel={kind === "pe" ? "P(νₑ)" : kind === "c2" ? "C²ᶻᶻ" : "K³ᶻᶻᶻ"} fixedProbability={kind === "pe"} playhead={playhead} />;
}

function Metrics({ data, quantum }: { data: Experiment; quantum: boolean }) {
  const methods = quantum ? (["ideal", "measured"] as const) : (["mean", "psa"] as const);
  const labels = { mean: "Campo médio", psa: "PSA", ideal: "Circuito ideal", measured: "Medições" };
  return <div className="nb-table-wrap"><table><thead><tr><th>Método</th><th>Observável</th><th>RMSE</th><th>Erro máximo</th><th>Sinal RMS</th></tr></thead><tbody>{methods.flatMap((method) => (["pe", "c2", "c3"] as Observable[]).map((kind) => {
    const metric = data.metrics[method]?.[kind];
    return metric ? <tr key={`${method}-${kind}`}><td>{labels[method]}</td><td>{observableLabels[kind]}</td><td>{numberLabel(metric.rmse, 5)}</td><td>{numberLabel(metric.max_abs, 5)}</td><td>{numberLabel(metric.signal_rms, 5)}</td></tr> : null;
  }))}</tbody></table></div>;
}

export default function Workbench() {
  const [area, setArea] = useState<Area>("board");
  const [mode, setMode] = useState<BoardMode>("classical");
  const [items, setItems] = useState<NeutrinoSpec[]>(initialItems);
  const [couplings, setCouplings] = useState<number[][]>(initialCouplings);
  const [selectedPair, setSelectedPair] = useState<[number, number] | null>(null);
  const [settings, setSettings] = useState<Settings>(defaults);
  const [bValues, setBValues] = useState<number[] | null>(null);
  const [data, setData] = useState<Experiment | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [dirty, setDirty] = useState(false);
  const [kind, setKind] = useState<Observable>("pe");
  const [index, setIndex] = useState(0);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [quantumOptions, setQuantumOptions] = useState<QuantumOptions>({ steps: 2, shots: 1024, readout_error: .02 });
  const [circuit, setCircuit] = useState<CircuitResult | null>(null);
  const [ibmStatus, setIbmStatus] = useState<IbmStatus | null>(null);
  const [ibmBackends, setIbmBackends] = useState<IbmBackend[]>([]);
  const [ibmBackend, setIbmBackend] = useState("");
  const [ibmIndex, setIbmIndex] = useState(1);
  const [hardwareError, setHardwareError] = useState("");
  const [hardwareChecking, setHardwareChecking] = useState("");
  const loaded = useRef(false);
  const nextId = useRef(4);
  const navigationVersion = useRef(0);
  const navigate = (target: Area) => { navigationVersion.current += 1; setArea(target); };

  const hydrate = useCallback((result: Experiment) => {
    setData(result);
    setItems(arrangeNeutrinos(result.config.omega.map((weight, i) => ({ id: `nu-${nextId.current++}`, weight, flavor: (result.config.initial_bloch[i][2] < 0 ? 1 : 0) as 0 | 1, x: 0, y: 0 }))));
    setCouplings(result.config.g_matrix);
    setSettings((current) => ({ ...current, mu: result.config.mu, theta: result.config.theta, tMax: result.config.t_max, points: result.config.points, seed: result.config.seed, trajectories: result.quality.trajectories, substeps: Number(result.classical.mean.diagnostics.substeps_per_interval ?? current.substeps) }));
    const expected = [Math.sin(2 * result.config.theta), 0, -Math.cos(2 * result.config.theta)];
    setBValues(result.config.b_field.some((value, i) => Math.abs(value - expected[i]) > 1e-6) ? result.config.b_field : null);
    setQuantumOptions(result.quantum?.options ?? { steps: 2, shots: 1024, readout_error: .02 });
    setDirty(false);
  }, []);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    api.health().then(() => setOnline(true)).catch(() => setOnline(false));
    const saved = window.localStorage.getItem("neutrino-lab.run");
    if (saved) api.get<Experiment>(saved).then(hydrate).catch(() => window.localStorage.removeItem("neutrino-lab.run"));
  }, [hydrate]);

  useEffect(() => {
    if (area !== "quantum") return;
    api.ibmStatus<IbmStatus>().then((result) => {
      setIbmStatus(result);
      if (result.preferred_backend) setIbmBackend(result.preferred_backend);
    }).catch(() => setIbmStatus(null));
  }, [area]);

  useEffect(() => { setIbmBackends([]); setIbmBackend(""); }, [items.length]);

  const pendingHardwareIds = data?.hardware_runs?.filter((run) => !["DONE", "ERROR", "CANCELLED"].includes(run.status)).map((run) => run.job_id).join(",") ?? "";
  useEffect(() => {
    if (!data || !pendingHardwareIds) return;
    const runId = data.run_id;
    const ids = pendingHardwareIds.split(",");
    let cancelled = false;
    let polling = false;
    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        for (const id of ids) {
          const result = await api.hardwareJob<HardwareRun>(runId, id);
          if (cancelled) return;
          setData((current) => current?.run_id === runId ? { ...current,
            hardware_runs: (current.hardware_runs ?? []).map((run) => run.job_id === id ? result : run) } : current);
        }
        setHardwareError("");
      } catch (cause) {
        if (!cancelled) setHardwareError(cause instanceof Error ? cause.message : "Falha ao consultar o job IBM.");
      } finally { polling = false; }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [data?.run_id, pendingHardwareIds]);

  useEffect(() => {
    if (!playing || !data || dirty) return;
    const timer = window.setInterval(() => setStep((current) => {
      if (current >= data.times.length - 1) { setPlaying(false); return current; }
      return current + 1;
    }), 130 / speed);
    return () => window.clearInterval(timer);
  }, [playing, data, dirty, speed]);

  const patchSettings = <K extends keyof Settings,>(key: K, value: Settings[K]) => {
    setSettings((current) => ({ ...current, [key]: value }));
    if (key === "theta") setBValues(null);
    setDirty(true); setPlaying(false);
  };
  const patchQuantumOptions = (update: Partial<QuantumOptions>) => {
    setQuantumOptions((current) => ({ ...current, ...update }));
    setCircuit(null);
  };
  const changeItem = (itemIndex: number, update: Partial<NeutrinoSpec>) => {
    setItems((current) => current.map((item, i) => i === itemIndex ? { ...item, ...update } : item));
    if ("flavor" in update || "weight" in update) { setDirty(true); setPlaying(false); }
  };
  const addItem = () => {
    if (items.length >= 16) return;
    setItems(arrangeNeutrinos([...items, { id: `nu-${nextId.current++}`, flavor: 0, weight: 1, x: 0, y: 0 }]));
    setCouplings((current) => [...current.map((row) => [...row, 1]), [...Array(current.length).fill(1), 0]]);
    setSelectedPair(null); setDirty(true); setPlaying(false);
  };
  const removeItem = (itemIndex: number) => {
    if (items.length <= 2) return;
    setItems(arrangeNeutrinos(items.filter((_, i) => i !== itemIndex)));
    setCouplings((current) => current.filter((_, i) => i !== itemIndex).map((row) => row.filter((_, j) => j !== itemIndex)));
    setSelectedPair(null); setDirty(true); setPlaying(false);
  };
  const changeCoupling = (i: number, j: number, value: number) => {
    setCouplings((current) => current.map((row, a) => row.map((entry, b) => (a === i && b === j) || (a === j && b === i) ? value : entry)));
    setDirty(true); setPlaying(false);
  };

  async function follow(start: () => Promise<Job>): Promise<Experiment> {
    const first = await start(); setJob(first);
    let current = first;
    while (current.status === "queued" || current.status === "running") {
      await new Promise((resolve) => window.setTimeout(resolve, 180));
      current = await api.job<Job>(first.job_id);
      setJob(current);
    }
    if (current.status === "failed") throw new Error(current.error ?? "Execução falhou.");
    if (!current.run_id) throw new Error("A execução terminou sem identificador.");
    return api.get<Experiment>(current.run_id);
  }

  const runClassical = async () => {
    const navigationAtStart = navigationVersion.current;
    setBusy("Calculando modelo clássico"); setError(""); setJob(null); setPlaying(false); setStep(0);
    try {
      if (items.some((item) => !Number.isFinite(item.weight) || item.weight <= 0)) throw new Error("Defina um peso de frequência positivo para cada neutrino.");
      if (!Number.isInteger(settings.points) || settings.points < 2 || settings.points > 201) throw new Error("Use entre 2 e 201 pontos temporais.");
      if (!Number.isInteger(settings.trajectories) || settings.trajectories < 16 || settings.trajectories > 4096) throw new Error("Use entre 16 e 4096 trajetórias PSA.");
      const result = await follow(() => api.startClassical<Job>({ config: {
        n: items.length, mu: settings.mu, theta: settings.theta, omega_spread: 0,
        t_max: settings.tMax, points: settings.points, seed: settings.seed,
        flavors: items.map((item) => item.flavor), omega_values: normalizedFrequencies(items),
        g_values: couplings, ...(bValues ? { b_values: bValues } : {}),
      }, trajectories: settings.trajectories, substeps: settings.substeps }));
      setData(result); setDirty(false); setOnline(true); setKind("pe"); setIndex(0);
      setCircuit(null); setMode("classical"); setPlaying(false);
      if (navigationVersion.current === navigationAtStart) setArea("classical");
      window.localStorage.setItem("neutrino-lab.run", result.run_id);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha na simulação clássica."); }
    finally { setBusy(""); }
  };

  const runQuantum = async () => {
    if (!data || dirty || items.length > 8) { setError("Execute primeiro a referência clássica para a configuração atual (até 8 neutrinos)."); return; }
    const navigationAtStart = navigationVersion.current;
    setBusy("Calculando circuito quântico"); setError(""); setJob(null); setPlaying(false); setStep(0);
    try {
      const result = await follow(() => api.startQuantum<Job>(data.run_id, quantumOptions));
      setData(result); setMode("quantum"); setCircuit(null); setPlaying(false);
      if (navigationVersion.current === navigationAtStart) setArea("quantum");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha no circuito quântico."); }
    finally { setBusy(""); }
  };

  async function runAuxiliary<T>(label: string, operation: () => Promise<T>, complete: (result: T) => void) {
    setBusy(label); setError("");
    try { complete(await operation()); } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha na operação."); }
    finally { setBusy(""); }
  }

  const loadIbmBackends = () => runAuxiliary("Consultando dispositivos IBM Quantum",
    () => api.ibmBackends<IbmBackend[]>(items.length), (backends) => {
      setIbmBackends(backends);
      setIbmBackend((current) => backends.some((backend) => backend.name === current)
        ? current : backends[0]?.name ?? "");
    });

  const runHardware = async () => {
    if (!available?.quantum || quantumDirty || !ibmBackend) return;
    setBusy("Enviando circuito à IBM Quantum"); setError(""); setJob(null); setHardwareError("");
    try {
      const result = await follow(() => api.startHardware<Job>(available.run_id, {
        backend: ibmBackend, interval_index: Math.min(ibmIndex, maxHardwareIndex),
        steps: quantumOptions.steps, shots: quantumOptions.shots, kind, index: clampedIndex,
      }));
      setData(result);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Falha ao enviar circuito à IBM Quantum."); }
    finally { setBusy(""); }
  };

  const refreshHardwareNow = async (jobId: string) => {
    if (!available) return;
    setHardwareChecking(jobId); setHardwareError("");
    try {
      const refreshed = await api.hardwareJob<HardwareRun>(available.run_id, jobId);
      setData((current) => current?.run_id === available.run_id ? { ...current,
        hardware_runs: (current.hardware_runs ?? []).map((run) => run.job_id === jobId ? refreshed : run) } : current);
    } catch (cause) {
      setHardwareError(cause instanceof Error ? cause.message : "Falha ao consultar o job IBM.");
    } finally { setHardwareChecking(""); }
  };

  const importScenario = async (file: File) => {
    try {
      const parsed = JSON.parse(await file.text());
      const config = parsed.config ?? parsed;
      const n = Number(config.n);
      if (!Number.isInteger(n) || n < 2 || n > 16) throw new Error("O cenário precisa de n entre 2 e 16.");
      if (config.initial_bloch_values) throw new Error("O quadro aceita estados iniciais νₑ ou νₓ. Vetores de Bloch arbitrários devem ser executados pela API.");
      const flavors = config.flavors ?? Array.from({ length: n }, (_, i) => i < n / 2 ? 0 : 1);
      const omega = config.omega_values ?? Array.from({ length: n }, (_, i) => 1 - (config.omega_spread ?? .3) + 2 * (config.omega_spread ?? .3) * i / (n - 1));
      const g = config.g_values ?? Array.from({ length: n }, (_: unknown, i: number) => Array.from({ length: n }, (_: unknown, j: number) => i === j ? 0 : 1));
      if (flavors.length !== n || omega.length !== n || g.length !== n || g.some((row: number[]) => row.length !== n)) throw new Error("O tamanho de flavors, omega ou g não corresponde a n.");
      setItems(arrangeNeutrinos(omega.map((weight: number, i: number) => ({ id: `nu-${nextId.current++}`, flavor: flavors[i] as 0 | 1, weight, x: 0, y: 0 }))));
      setCouplings(g);
      setBValues(config.b_values ?? null);
      setSettings((current) => ({ ...current, mu: config.mu ?? current.mu, theta: config.theta ?? current.theta, tMax: config.t_max ?? current.tMax, points: config.points ?? current.points, seed: config.seed ?? current.seed, trajectories: parsed.trajectories ?? current.trajectories, substeps: parsed.substeps ?? current.substeps }));
      setSelectedPair(null); setDirty(true); setPlaying(false); setError(""); navigate("board");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "JSON inválido."); }
  };

  const available = !dirty && data?.config.n === items.length ? data : null;
  const quantumDirty = Boolean(available?.quantum && (available.quantum.options.steps !== quantumOptions.steps || available.quantum.options.shots !== quantumOptions.shots || available.quantum.options.readout_error !== quantumOptions.readout_error));
  const selected = available ? (kind === "pe" ? Array.from({ length: available.config.n }, (_, i) => [i]) : kind === "c2" ? available.pairs : available.trios) : [];
  const clampedIndex = Math.min(index, Math.max(0, selected.length - 1));
  const maxHardwareIndex = Math.max(1, Math.min((available?.times.length ?? 2) - 1, Math.floor(16 / quantumOptions.steps)));
  const hardwarePending = Boolean(available?.hardware_runs?.some((run) => !["DONE", "ERROR", "CANCELLED"].includes(run.status)));
  const activeJob = job?.status === "queued" || job?.status === "running" ? job : null;

  return <div className="nb-shell">
    <main className="nb-main">
      <header className="nb-topbar">
        <div className="nb-brand"><span className="nb-brand-mark">ν</span><div><strong>Neutrino<span>Lab</span></strong><small>LABORATÓRIO COMPUTACIONAL</small></div></div>
        <div className="nb-top-actions"><span className="nb-connection"><i className={online ? "online" : online === false ? "offline" : ""} />{online === null ? "Conectando" : online ? "Python conectado" : "Python offline"}</span>{data && <code>RUN {data.run_id.slice(-8)}</code>}<button className="nb-button nb-button-primary" disabled={Boolean(busy)} onClick={runClassical}>{busy ? "Calculando…" : "▶ Executar clássica"}</button></div>
      </header>
      <div className="nb-tabbar"><nav aria-label="Áreas do laboratório">{navigation.map((item) => <button key={item.area} title={item.subtitle} className={`nb-nav ${area === item.area ? "active" : ""}`} onClick={() => navigate(item.area)}>{item.label}</button>)}</nav></div>
      <div className="nb-content">
        <div className="nb-page-title"><div><h1>{area === "board" ? "Quadro de neutrinos" : area === "classical" ? "Evolução clássica" : area === "quantum" ? "Circuito quântico" : "Visualizar sistema"}</h1><p>{area === "board" ? "Monte o cenário e acompanhe a evolução." : area === "classical" ? "Compare a referência exata com campo médio e PSA." : area === "quantum" ? "Compare o circuito de Trotter com a referência exata." : "Inspecione campos e correlações ao longo do tempo."}</p></div></div>
        <section className="nb-setup nb-panel" inert={Boolean(busy)}><div className="nb-setup-head"><div><span className="nb-setup-icon">⚗</span><div><span className="nb-kicker">CONFIGURAÇÃO DO CENÁRIO</span><h2>Parâmetros globais</h2></div></div><label className="nb-import">↑ Importar JSON<input type="file" accept=".json,application/json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importScenario(file); event.target.value = ""; }} /></label></div>
          <div className="nb-fields"><Field label="Interação μ / ω̄" value={settings.mu} onChange={(value) => patchSettings("mu", value)} min={0} max={10} step={.1} /><Field label="Ângulo de mistura θ" value={settings.theta} onChange={(value) => patchSettings("theta", value)} min={0} max={.78} step={.01} /><Field label="Tempo final τ" value={settings.tMax} onChange={(value) => patchSettings("tMax", value)} min={.1} max={20} step={.5} /><Field label="Pontos temporais" value={settings.points} onChange={(value) => patchSettings("points", value)} min={2} max={201} step={1} /></div>
          <p className="nb-scenario-note">Entradas definidas no quadro ou em JSON. A reprodução de um benchmark publicado ainda está pendente.</p>
          <details className="nb-advanced"><summary>Configuração numérica <span>+</span></summary><div className="nb-fields"><Field label="Trajetórias PSA" value={settings.trajectories} onChange={(value) => patchSettings("trajectories", value)} min={16} max={4096} step={16} /><Field label="Subpassos RK4" value={settings.substeps} onChange={(value) => patchSettings("substeps", value)} min={1} max={12} step={1} /><Field label="Semente" value={settings.seed} onChange={(value) => patchSettings("seed", value)} min={0} max={10000000} step={1} /></div></details>
        </section>
      {error && <div className="nb-error" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="Fechar erro">×</button></div>}
      {busy && <div className="nb-run-progress" role="status" aria-live="polite"><span className="nb-run-spinner" aria-hidden="true" /><div><strong>{busy}</strong><span>{activeJob?.events.at(-1)?.message ?? (activeJob ? "Preparando execução…" : "Aguarde a conclusão da verificação.")}</span></div>{activeJob && <button className="nb-button nb-button-outline" onClick={() => navigate("board")}>Acompanhar execução</button>}</div>}
      {dirty && data && <div className="nb-notice">Configuração alterada. Execute a clássica para atualizar as curvas e o quadro.</div>}
      {area === "board" && <><div className="nb-workspace-grid"><div inert={Boolean(busy)}><NeutrinoBoard items={items} couplings={couplings} mode={mode} onMode={setMode} onAdd={addItem} onRemove={removeItem} onChange={changeItem} onArrange={() => setItems(arrangeNeutrinos(items))} onCoupling={changeCoupling} selectedPair={selectedPair} onPair={setSelectedPair} data={quantumDirty && mode === "quantum" ? null : available} dirty={dirty} step={step} /></div><div className="nb-execution-slot"><ExecutionPanel key={job?.job_id ?? available?.run_id ?? "none"} job={job} trace={available?.trace ?? []} /></div></div>
        <div className="nb-playback nb-panel"><div><span className="nb-kicker">03 / REPRODUÇÃO DA EVOLUÇÃO CALCULADA</span><h2>Tempo da simulação</h2><p>O cursor percorre os estados já calculados; cada quadro usa os dados salvos da execução.</p></div><div className="nb-play-controls"><button className="nb-button nb-button-outline" disabled={!available} onClick={() => { if (step >= (available?.times.length ?? 0) - 1) setStep(0); setPlaying(!playing); }}>{playing ? "Ⅱ Pausar" : "▶ Reproduzir"}</button><button className="nb-icon-button" disabled={!available} onClick={() => { setPlaying(false); setStep(0); }} aria-label="Voltar ao início">↺</button><select aria-label="Velocidade de reprodução" value={speed} onChange={(event) => setSpeed(Number(event.target.value))}><option value={.5}>0,5×</option><option value={1}>1×</option><option value={2}>2×</option></select><strong>τ {numberLabel(available?.times[step] ?? 0, 2)}</strong></div><input aria-label="Posição no tempo" type="range" min={0} max={Math.max(0, (available?.times.length ?? 1) - 1)} value={Math.min(step, Math.max(0, (available?.times.length ?? 1) - 1))} disabled={!available} onChange={(event) => { setPlaying(false); setStep(Number(event.target.value)); }} /></div>
        <section className="nb-panel nb-board-chart"><div className="nb-panel-title"><div><span className="nb-kicker">PROBABILIDADE NO TEMPO</span><h2>Neutrino ν₀</h2></div><span className="nb-muted">{mode === "quantum" ? "Exato · circuito · medição" : "Exato · campo médio · PSA"}</span></div>{available && !(mode === "quantum" && quantumDirty) ? <ResultPlot data={available} kind="pe" index={0} quantum={mode === "quantum" && Boolean(available.quantum)} playhead={step} /> : <div className="nb-empty-chart">{quantumDirty && mode === "quantum" ? "Execute o circuito com os parâmetros atuais." : "Execute a simulação para visualizar as trajetórias."}</div>}</section></>}
      {area === "classical" && (available ? <><div className="nb-next-step"><span>Referência clássica calculada para {available.config.n} neutrinos.</span>{available.config.n <= 8 && <button className="nb-button nb-button-outline" onClick={() => navigate("quantum")}>Próxima etapa: circuito quântico →</button>}</div><Selector data={available} kind={kind} index={clampedIndex} onKind={(value) => { setKind(value); setIndex(0); }} onIndex={setIndex} /><section className="nb-panel nb-full-chart"><h2>{observableLabels[kind]}</h2><ResultPlot data={available} kind={kind} index={clampedIndex} /></section><section className="nb-panel nb-table-panel"><h2>Desvio em relação à solução exata</h2><Metrics data={available} quantum={false} /></section></> : <Empty text="Execute a simulação clássica para comparar os métodos." />)}
      {area === "quantum" && <>
        <div className="nb-panel nb-quantum-settings" inert={Boolean(busy)}><div><strong>SUZUKI–TROTTER DE SEGUNDA ORDEM</strong><p>Usa a mesma configuração da execução clássica, até 8 qubits.</p></div><label>Passos / intervalo<select value={quantumOptions.steps} onChange={(event) => patchQuantumOptions({ steps: Number(event.target.value) })}>{[1, 2, 4, 8, 16].map((value) => <option key={value}>{value}</option>)}</select></label><label>Medições / tempo<select value={quantumOptions.shots} onChange={(event) => patchQuantumOptions({ shots: Number(event.target.value) })}>{[128, 256, 512, 1024, 2048, 4096, 8192].map((value) => <option key={value}>{value}</option>)}</select></label><Field label="Erro de leitura simulado" value={quantumOptions.readout_error} onChange={(value) => patchQuantumOptions({ readout_error: value })} min={0} max={.25} step={.005} /><button className="nb-button nb-button-primary" disabled={!available || items.length > 8 || Boolean(busy)} onClick={runQuantum}>{busy ? "Calculando…" : "Executar circuito"}</button></div>
        {!available && <div className="nb-notice">Execute primeiro a simulação clássica da configuração atual.</div>}
        {items.length > 8 && <div className="nb-notice">O circuito aceita até 8 qubits. Reduza o número de neutrinos no quadro.</div>}
        {quantumDirty && <div className="nb-notice">Parâmetros alterados. Execute o circuito novamente para atualizar as curvas.</div>}
        {available?.quantum && !quantumDirty && <><Selector data={available} kind={kind} index={clampedIndex} onKind={(value) => { setKind(value); setIndex(0); }} onIndex={setIndex} /><section className="nb-panel nb-full-chart"><h2>{observableLabels[kind]}</h2><ResultPlot data={available} kind={kind} index={clampedIndex} quantum /></section><section className="nb-panel nb-table-panel"><h2>Desvio em relação à solução exata</h2><Metrics data={available} quantum /></section></>}
        {available && items.length <= 8 && <details className="nb-advanced-tool nb-panel"><summary>Verificação independente com Qiskit</summary><div className="nb-tool-panel"><p>Compare o primeiro intervalo com uma implementação independente do circuito.</p><button className="nb-button nb-button-outline" disabled={Boolean(busy)} onClick={() => runAuxiliary("Verificando circuito Qiskit", () => api.circuit<CircuitResult>(available.run_id, { steps: quantumOptions.steps }), setCircuit)}>Verificar circuito</button>{circuit && <><p>{circuit.size} portas · diferença máxima {numberLabel(circuit.max_probability_difference)}</p><pre className="nb-circuit-code">{circuit.diagram}</pre></>}</div></details>}
        <section className="nb-panel nb-hardware">
          <div className="nb-panel-title"><div><span className="nb-kicker">HARDWARE REAL · QISKIT RUNTIME</span><h2>IBM Quantum</h2></div><span className="nb-job-state">{ibmStatus === null ? "Status indisponível" : ibmStatus.configured ? "Chave configurada" : "Chave ausente"}</span></div>
          <p>Envie um instante do circuito a um dispositivo IBM. O job pode entrar em fila e consumir créditos da sua conta.</p>
          {ibmStatus === null ? <p>Inicie o backend Python para consultar a configuração da IBM Quantum.</p>
            : !ibmStatus.configured ? <p>Preencha <code>IBM_QUANTUM_API_KEY</code> no arquivo <code>.env</code> da raiz e reinicie o backend. A chave permanece no Python.</p>
            : !ibmStatus.sdk_installed ? <p>Instale <code>qiskit-ibm-runtime</code> com <code>pip install -e &apos;.[qiskit]&apos;</code>.</p>
              : <><div className="nb-hardware-controls"><button className="nb-button nb-button-outline" disabled={items.length > 8 || Boolean(busy)} onClick={loadIbmBackends}>Consultar dispositivos</button><label>Dispositivo<select aria-label="Dispositivo IBM Quantum" value={ibmBackends.some((item) => item.name === ibmBackend) ? ibmBackend : ""} onChange={(event) => setIbmBackend(event.target.value)} disabled={!ibmBackends.length || Boolean(busy)}><option value="">Selecione</option>{ibmBackends.map((item) => <option key={item.name} value={item.name}>{item.name} · {item.num_qubits} qubits</option>)}</select></label><label>Instante<select aria-label="Instante para hardware" value={Math.min(ibmIndex, maxHardwareIndex)} onChange={(event) => setIbmIndex(Number(event.target.value))} disabled={!available || Boolean(busy)}>{Array.from({ length: maxHardwareIndex }, (_, i) => i + 1).map((point) => <option key={point} value={point}>τ {numberLabel(available?.times[point] ?? 0, 2)}</option>)}</select></label><button className="nb-button nb-button-primary" disabled={!available?.quantum || quantumDirty || !ibmBackends.some((item) => item.name === ibmBackend) || hardwarePending || Boolean(busy)} onClick={runHardware}>Enviar ao hardware</button></div><p>Uma execução mede {observableLabels[kind]} em {selected[clampedIndex]?.map((i) => `ν${i}`).join(" · ") ?? "—"}, com {quantumOptions.shots} medições.</p></>}
          {hardwareError && <div className="nb-error" role="alert">{hardwareError}</div>}
          <p>Jobs pendentes são consultados automaticamente enquanto a plataforma está aberta.</p>
          {(available?.hardware_runs ?? []).slice().reverse().map((run) => <div className="nb-hardware-run" key={run.job_id}><div><strong>{run.backend}</strong><span>{observableLabels[run.kind]} · {run.indices.map((i) => `ν${i}`).join(" · ")}</span><span>τ {numberLabel(run.tau, 2)} · {run.shots} medições · {hardwareStatusLabels[run.status] ?? run.status}</span><code>Job {run.job_id}</code>{run.checked_utc && <span>Consultado às {new Date(run.checked_utc).toLocaleTimeString("pt-BR")}</span>}{!["DONE", "ERROR", "CANCELLED"].includes(run.status) && <button className="nb-button nb-button-outline nb-hardware-refresh" disabled={hardwareChecking === run.job_id || Boolean(busy)} onClick={() => refreshHardwareNow(run.job_id)}>{hardwareChecking === run.job_id ? "Consultando…" : "Atualizar agora"}</button>}</div>{run.estimate !== null && <div><strong>{numberLabel(run.estimate, 4)}</strong><span>IC 95% [{numberLabel(run.lower ?? NaN, 4)}, {numberLabel(run.upper ?? NaN, 4)}]</span><span>Exato {numberLabel(run.references.exact, 4)} · circuito ideal {numberLabel(run.references.ideal, 4)}</span></div>}</div>)}
        </section>
      </>}
      {area === "system" && (available ? <SystemViz data={available} step={Math.min(step, available.times.length - 1)} onStep={(value) => { setPlaying(false); setStep(value); }} /> : <Empty text="Execute o cenário para visualizar campos e correlações." />)}
      <footer className="nb-footer"><span>NEUTRINO LAB / SIMULAÇÃO LOCAL</span><span>Dois sabores · τ em unidades de ω̄⁻¹</span></footer></div>
    </main>
  </div>;
}

function Empty({ text }: { text: string }) { return <section className="nb-panel nb-empty"><span className="nb-kicker">AGUARDANDO EXECUÇÃO</span><h2>Sem resultados ainda</h2><p>{text} Use “Executar clássica” na barra superior.</p></section>; }
function Selector({ data, kind, index, onKind, onIndex }: { data: Experiment; kind: Observable; index: number; onKind: (value: Observable) => void; onIndex: (value: number) => void }) {
  const groups = kind === "pe" ? Array.from({ length: data.config.n }, (_, i) => [i]) : kind === "c2" ? data.pairs : data.trios;
  return <div className="nb-panel nb-selector"><div><span className="nb-kicker">OBSERVÁVEL</span><h2>Escolha o que comparar</h2></div><label>Grandeza<select aria-label="Observável" value={kind} onChange={(event) => onKind(event.target.value as Observable)}>{(["pe", "c2", "c3"] as Observable[]).map((value) => <option key={value} value={value} disabled={value === "c3" && data.trios.length === 0}>{observableLabels[value]}</option>)}</select></label><label>Partículas<select aria-label="Partículas" value={index} onChange={(event) => onIndex(Number(event.target.value))}>{groups.map((group, i) => <option key={i} value={i}>{group.map((n) => `ν${n}`).join(" · ")}</option>)}</select></label></div>;
}
