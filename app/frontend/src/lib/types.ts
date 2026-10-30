export type Observable = "pe" | "c2" | "c3";
export type Area = "board" | "classical" | "quantum" | "system" | "quality";
export type Method = "exact" | "mean" | "psa" | "ideal" | "measured";

export interface Series {
  method: string;
  diagnostics: Record<string, number | string>;
  m1: number[][];
  m2: number[][];
  m3: number[][];
  pe: number[][];
  c2: number[][];
  c3: number[][];
  bloch?: number[][][];
}

export interface ErrorMetrics {
  rmse: number;
  max_abs: number;
  signal_rms: number;
}

export interface QualityControl {
  name: string;
  value: number;
  limit: number;
  pass: boolean;
}

export interface Experiment {
  run_id: string;
  config: {
    n: number;
    mu: number;
    theta: number;
    omega_spread: number;
    t_max: number;
    points: number;
    seed: number;
    omega: number[];
    b_field: number[];
    g_matrix: number[][];
    initial_bloch: number[][];
    hamiltonian: string;
  };
  times: number[];
  pairs: number[][];
  trios: number[][];
  classical: { exact: Series; mean: Series; psa: Series };
  metrics: Partial<Record<"mean" | "psa" | "ideal" | "measured", Partial<Record<Observable, ErrorMetrics>>>>;
  quantum: { ideal: Series; measured: Series; options: QuantumOptions } | null;
  aer: AerResult | null;
  hardware_runs?: HardwareRun[];
  trace?: ExecutionEvent[];
  quality: {
    controls: QualityControl[];
    psa_initial_spin_mean_error_max: number;
    trajectories: number;
    seed: number;
    convergence: Record<string, number> | null;
  };
}

export interface ExecutionEvent {
  order: number;
  elapsed_ms: number;
  stage: string;
  status: "running" | "done";
  message: string;
  source: string;
}

export interface Job {
  job_id: string;
  kind: "classical" | "quantum" | "hardware";
  status: "queued" | "running" | "completed" | "failed";
  events: ExecutionEvent[];
  run_id: string | null;
  error: string | null;
}

export interface NeutrinoSpec {
  id: string;
  flavor: 0 | 1;
  weight: number;
  x: number;
  y: number;
}

export interface QuantumOptions { steps: number; shots: number; readout_error: number }
export interface IbmStatus { configured: boolean; sdk_installed: boolean; instance_configured: boolean; preferred_backend: string | null }
export interface IbmBackend { name: string; num_qubits: number }
export interface HardwareRun {
  job_id: string;
  backend: string;
  interval_index: number;
  tau: number;
  steps: number;
  shots: number;
  kind: Observable;
  index: number;
  indices: number[];
  status: string;
  checked_utc?: string;
  estimate: number | null;
  lower: number | null;
  upper: number | null;
  references: { exact: number; ideal: number };
  transpiled_depth: number;
  two_qubit_gates: number;
}
export interface Band { lower: number[]; upper: number[]; confidence: number; scope: string }
export interface CircuitResult { size: number; diagram: string; max_probability_difference: number }
export interface AerResult {
  kind: Observable;
  index: number;
  indices: number[];
  estimate: number;
  lower: number;
  upper: number;
  references: Record<string, number>;
  metadata: { tau: number; transpiled_depth: number; cx_count: number; shots: number; noise_scope: string };
}

export const observableLabels: Record<Observable, string> = {
  pe: "Probabilidade νₑ",
  c2: "Correlação de pares C²ᶻᶻ",
  c3: "Cumulante de trios K³ᶻᶻᶻ",
};

export function numberLabel(value: number, digits = 3) {
  if (!Number.isFinite(value)) return "—";
  if (value !== 0 && Math.abs(value) < 0.001) return value.toExponential(1);
  return value.toFixed(digits);
}
