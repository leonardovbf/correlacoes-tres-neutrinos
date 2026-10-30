const BASE = "/api/backend";

async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new Error("Não foi possível conectar ao backend Python em 127.0.0.1:8000.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (Array.isArray(detail)) {
      const messages = detail.map((item) => `${(item.loc ?? []).slice(1).join(".")}: ${item.msg ?? "valor inválido"}`);
      throw new Error(messages.join("; "));
    }
    throw new Error(`Requisição falhou (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  startClassical: <T>(body: unknown) => request<T>("/jobs/classical", body),
  startQuantum: <T>(id: string, body: unknown) => request<T>(`/jobs/${id}/quantum`, body),
  startHardware: <T>(id: string, body: unknown) => request<T>(`/jobs/${id}/hardware`, body),
  ibmStatus: <T>() => request<T>("/ibm/status"),
  ibmBackends: <T>(minQubits: number) => request<T>(`/ibm/backends?min_qubits=${minQubits}`),
  hardwareJob: <T>(id: string, jobId: string) => request<T>(`/experiments/${id}/hardware/${encodeURIComponent(jobId)}`),
  job: <T>(id: string) => request<T>(`/jobs/${id}`),
  create: <T>(body: unknown) => request<T>("/experiments", body),
  get: <T>(id: string) => request<T>(`/experiments/${id}`),
  quantum: <T>(id: string, body: unknown) => request<T>(`/experiments/${id}/quantum`, body),
  interval: <T>(id: string, body: unknown) => request<T>(`/experiments/${id}/interval`, body),
  circuit: <T>(id: string, body: unknown) => request<T>(`/experiments/${id}/circuit`, body),
  aer: <T>(id: string, body: unknown) => request<T>(`/experiments/${id}/aer`, body),
  convergence: <T>(id: string) => request<T>(`/experiments/${id}/convergence`, {}),
  manifest: <T>(id: string) => request<T>(`/experiments/${id}/manifest`),
};
