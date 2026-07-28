import { create } from "zustand";
import type { JobResponse, MetricsResponse } from "../services/api";

interface AppState {
  // Theme
  darkMode: boolean;
  toggleDarkMode: () => void;

  // Jobs
  jobs: JobResponse[];
  setJobs: (jobs: JobResponse[]) => void;
  addJob: (job: JobResponse) => void;
  updateJob: (jobId: string, updates: Partial<JobResponse>) => void;

  // Metrics
  metrics: MetricsResponse | null;
  setMetrics: (m: MetricsResponse | null) => void;

  // Session
  sessionId: string | null;
  setSessionId: (id: string | null) => void;

  // API Keys (ephemeral — never persisted)
  llmApiKey: string;
  githubToken: string;
  setLLMApiKey: (key: string) => void;
  setGithubToken: (token: string) => void;

  // Active job for detail view
  activeJobId: string | null;
  setActiveJobId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Theme
  darkMode: true,
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),

  // Jobs
  jobs: [],
  setJobs: (jobs) => set({ jobs }),
  addJob: (job) => set((s) => ({ jobs: [job, ...s.jobs] })),
  updateJob: (jobId, updates) =>
    set((s) => ({
      jobs: s.jobs.map((j) => (j.job_id === jobId ? { ...j, ...updates } : j)),
    })),

  // Metrics
  metrics: null,
  setMetrics: (metrics) => set({ metrics }),

  // Session
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),

  // API Keys
  llmApiKey: "",
  githubToken: "",
  setLLMApiKey: (key) => set({ llmApiKey: key }),
  setGithubToken: (token) => set({ githubToken: token }),

  // Active job
  activeJobId: null,
  setActiveJobId: (id) => set({ activeJobId: id }),
}));
