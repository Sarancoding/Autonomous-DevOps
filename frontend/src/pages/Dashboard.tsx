import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Play,
  GitBranch,
  Bug,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Plus,
  Loader2,
} from "lucide-react";
import { clsx } from "clsx";
import { api, type JobResponse, type MetricsResponse } from "../services/api";
import { useAppStore } from "../stores/appStore";
import { StatusBadge } from "../components/StatusBadge";
import { MetricsCard } from "../components/MetricsCard";

export function Dashboard() {
  const navigate = useNavigate();
  const { jobs, setJobs, metrics, setMetrics, sessionId } = useAppStore();

  // Trigger form state
  const [repoUrl, setRepoUrl] = useState("");
  const [failureLog, setFailureLog] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState("");

  // Poll metrics every 5s
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const m = await api.metrics();
        setMetrics(m);
      } catch {
        // Backend may not be ready yet
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [setMetrics]);

  // Poll jobs list
  useEffect(() => {
    // The backend doesn't have a list endpoint in our current impl,
    // so we rely on metrics + the individual jobs we've created.
    // For now, we trigger refresh when a new job is added.
  }, []);

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!repoUrl || !failureLog) {
      setError("Repository URL and failure log are required.");
      return;
    }

    setTriggering(true);
    try {
      const result = await api.trigger(
        { repo_url: repoUrl, failure_log: failureLog },
        sessionId ?? undefined
      );
      // Add a placeholder job to the list
      const newJob: JobResponse = {
        job_id: result.job_id,
        status: "pending",
        repo_url: repoUrl,
        commit_sha: "",
        error_type: "",
        proposed_fix: "",
        pr_url: null,
        confidence_score: 0,
        attempts: 0,
        max_attempts: 3,
        logs: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setJobs([newJob, ...jobs]);
      navigate(`/jobs/${result.job_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to trigger job");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Dashboard</h1>
        <p className="text-sm text-surface-400 mt-1">
          Monitor and manage your self-healing CI/CD agents
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Jobs"
          value={metrics?.total_jobs ?? 0}
          icon={GitBranch}
          color="primary"
        />
        <MetricsCard
          title="Success Rate"
          value={
            metrics && metrics.total_jobs > 0
              ? `${Math.round((metrics.success_count / metrics.total_jobs) * 100)}%`
              : "0%"
          }
          icon={CheckCircle2}
          color="success"
          trend={metrics && metrics.success_count > metrics.failed_count ? "up" : "neutral"}
        />
        <MetricsCard
          title="Failed"
          value={metrics?.failed_count ?? 0}
          icon={Bug}
          color="danger"
        />
        <MetricsCard
          title="Avg Confidence"
          value={
            metrics?.avg_confidence
              ? `${(metrics.avg_confidence * 100).toFixed(0)}%`
              : "—"
          }
          icon={AlertTriangle}
          color="accent"
        />
      </div>

      {/* Trigger Form & Job List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trigger Form */}
        <div className="glass-card p-5 lg:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <Play className="w-4 h-4 text-primary-400" />
            <h2 className="text-sm font-semibold text-surface-200">Trigger Agent</h2>
          </div>

          <form onSubmit={handleTrigger} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-surface-400 mb-1.5">
                Repository URL
              </label>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full bg-surface-800 border border-surface-700 rounded-lg px-3 py-2 text-sm text-surface-200 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:border-primary-500/50 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-surface-400 mb-1.5">
                Failure Log / Stack Trace
              </label>
              <textarea
                value={failureLog}
                onChange={(e) => setFailureLog(e.target.value)}
                rows={6}
                placeholder="Paste the CI/CD failure log or stack trace..."
                className="w-full bg-surface-800 border border-surface-700 rounded-lg px-3 py-2 text-sm text-surface-200 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:border-primary-500/50 transition-all font-mono"
              />
            </div>

            {error && (
              <p className="text-xs text-danger">{error}</p>
            )}

            <button
              type="submit"
              disabled={triggering}
              className={clsx(
                "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200",
                triggering
                  ? "bg-surface-700 text-surface-400 cursor-not-allowed"
                  : "bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-500/20"
              )}
            >
              {triggering ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Triggering...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Agent
                </>
              )}
            </button>
          </form>
        </div>

        {/* Job List */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-surface-200">Recent Jobs</h2>
            <span className="text-xs text-surface-500">{jobs.length} total</span>
          </div>

          {jobs.length === 0 && (
            <div className="glass-card p-8 text-center">
              <div className="flex flex-col items-center gap-3 text-surface-500">
                <Clock className="w-10 h-10" />
                <p className="text-sm">No jobs yet. Trigger an agent run to get started.</p>
              </div>
            </div>
          )}

          {jobs.map((job) => (
            <button
              key={job.job_id}
              onClick={() => navigate(`/jobs/${job.job_id}`)}
              className="w-full glass-card-hover p-4 text-left cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <StatusBadge status={job.status} />
                  <span className="text-sm font-mono text-surface-400">
                    {job.job_id.slice(0, 12)}...
                  </span>
                </div>
                <span className="text-xs text-surface-500">
                  {new Date(job.created_at).toLocaleString()}
                </span>
              </div>
              <div className="mt-2 flex items-center gap-4 text-xs text-surface-400">
                <span className="truncate max-w-md">{job.repo_url}</span>
                {job.error_type && (
                  <span className="text-danger">{job.error_type}</span>
                )}
                {job.confidence_score > 0 && (
                  <span className="text-success">
                    {(job.confidence_score * 100).toFixed(0)}% confidence
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
