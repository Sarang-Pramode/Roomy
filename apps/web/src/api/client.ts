const base = "";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export type HealthResponse = {
  status: string;
  db_path: string;
  session_count: number;
};

export function fetchHealth() {
  return getJson<HealthResponse>("/health");
}

export type SessionRow = {
  session_id: string;
  agent_name: string;
  environment: string;
  started_at: string;
  ended_at: string | null;
  status: string;
  metadata_json: string;
  total_tokens: number | null;
  total_cost: number | null;
};

export type StepRow = {
  step_id: string;
  session_id: string;
  parent_step_id: string | null;
  step_index: number;
  step_type: string;
  started_at: string;
  ended_at: string | null;
  latency_ms: number | null;
  status: string;
  metadata_json: string;
};

export type SegmentRow = {
  segment_id: string;
  llm_call_id: string;
  order_index: number;
  segment_type: string;
  source_kind?: string | null;
  source_name?: string | null;
  text_preview: string | null;
  token_count: number | null;
  byte_count: number | null;
};

export type FindingRow = {
  finding_id: string;
  session_id: string;
  step_id: string | null;
  severity: string;
  finding_type: string;
  explanation: string;
  evidence_json: string;
};

export function fetchSessions() {
  return getJson<SessionRow[]>("/sessions");
}

export function fetchSession(id: string) {
  return getJson<Record<string, unknown>>(`/sessions/${id}`);
}

export function fetchSteps(sessionId: string) {
  return getJson<StepRow[]>(`/sessions/${sessionId}/steps`);
}

export function fetchStep(stepId: string) {
  return getJson<Record<string, unknown>>(`/steps/${stepId}`);
}

export function fetchSegments(stepId: string) {
  return getJson<SegmentRow[]>(`/steps/${stepId}/segments`);
}

export function fetchRaw(stepId: string) {
  return getJson<{ request: unknown; response: unknown }>(`/steps/${stepId}/raw`);
}

export function fetchFindings(sessionId: string) {
  return getJson<FindingRow[]>(`/sessions/${sessionId}/findings`);
}

export type UpstreamStep = Record<string, unknown> & {
  step_id: string;
  step_type: string;
  step_index: number;
  tool_calls?: Record<string, unknown>[];
  retrieval_events?: Record<string, unknown>[];
};

export function fetchUpstream(stepId: string) {
  return getJson<UpstreamStep[]>(`/steps/${stepId}/upstream`);
}

export type SessionDiffResponse = {
  added_segments: Record<string, unknown>[];
  removed_segments: Record<string, unknown>[];
  token_count_delta: number;
};

export function fetchSessionDiff(sessionId: string, a: string, b: string) {
  const q = new URLSearchParams({ a, b });
  return getJson<SessionDiffResponse>(`/sessions/${sessionId}/diff?${q.toString()}`);
}
