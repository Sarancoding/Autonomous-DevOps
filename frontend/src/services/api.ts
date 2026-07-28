/** API client for the Autonomous DevOps backend. */

const BASE_URL = "/api";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = opts;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface JobResponse {
  job_id: string;
  status: "pending" | "running" | "success" | "failed" | "needs_review";
  repo_url: string;
  commit_sha: string;
  error_type: string;
  proposed_fix: string;
  pr_url: string | null;
  confidence_score: number;
  attempts: number;
  max_attempts: number;
  logs: Array<{
    timestamp: string;
    node: string;
    message: string;
    level: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface MetricsResponse {
  total_jobs: number;
  success_count: number;
  failed_count: number;
  needs_review_count: number;
  total_tokens_used: number;
  total_cost_estimate: number;
  avg_attempts_per_job: number;
  avg_confidence: number;
}

export interface TriggerRequest {
  repo_url: string;
  commit_sha?: string;
  failure_log: string;
  max_attempts?: number;
  model?: string;
}

export interface StatusResponse {
  status: string;
  version: string;
  langfuse_enabled: boolean;
  jobs_running: number;
  uptime_seconds: number;
}

export interface SessionKeysResponse {
  session_id: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const api = {
  // Health
  status: () => request<StatusResponse>("/status"),

  // Jobs
  trigger: (data: TriggerRequest, sessionId?: string) =>
    request<{ job_id: string; status: string }>("/trigger", {
      method: "POST",
      body: data,
      headers: sessionId ? { Authorization: `Bearer ${sessionId}` } : {},
    }),

  getJob: (jobId: string) => request<JobResponse>(`/jobs/${jobId}`),

  // Metrics
  metrics: () => request<MetricsResponse>("/metrics"),

  // Session / BYOK
  storeKeys: (llmApiKey: string, githubToken: string) =>
    request<SessionKeysResponse>("/session/keys", {
      method: "POST",
      body: { llm_api_key: llmApiKey, github_token: githubToken },
    }),

  // Config
  updateConfig: (config: {
    max_attempts?: number;
    confidence_threshold?: number;
    model_name?: string;
  }) => request<{ message: string }>("/config", { method: "POST", body: config }),
};
