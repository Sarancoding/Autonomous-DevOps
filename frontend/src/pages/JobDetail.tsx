import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ExternalLink,
  GitPullRequest,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { clsx } from "clsx";
import { api, type JobResponse } from "../services/api";
import { useWebSocket } from "../hooks/useWebSocket";
import { StatusBadge } from "../components/StatusBadge";
import { LiveLogs } from "../components/LiveLogs";
import { DiffViewer } from "../components/DiffViewer";
import { Timeline } from "../components/Timeline";

interface TimelineStep {
  node: string;
  status: "pending" | "running" | "success" | "failed";
  message: string;
  timestamp?: string;
}

export function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [timelineSteps, setTimelineSteps] = useState<TimelineStep[]>([]);

  // WebSocket for live logs
  const { connected, logs } = useWebSocket({
    jobId: jobId ?? null,
    onLog: (entry) => {
      // Update timeline based on log entries
      const nodeName = entry.node;
      setTimelineSteps((prev) => {
        const existing = prev.find((s) => s.node === nodeName);
        if (existing) {
          return prev.map((s) =>
            s.node === nodeName
              ? {
                  ...s,
                  status: entry.level === "error" ? "failed" : "success",
                  message: entry.message,
                  timestamp: entry.timestamp,
                }
              : s
          );
        }
        return [
          ...prev,
          {
            node: nodeName,
            status: entry.level === "error" ? "failed" : "success",
            message: entry.message,
            timestamp: entry.timestamp,
          },
        ];
      });
    },
  });

  // Fetch job details
  useEffect(() => {
    if (!jobId) return;

    const fetchJob = async () => {
      try {
        const data = await api.getJob(jobId);
        setJob(data);
      } catch {
        // Job may still be running
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
    const interval = setInterval(fetchJob, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  // Set initial timeline from job status
  useEffect(() => {
    if (!job) return;

    const statusMap: Record<string, "pending" | "running" | "success" | "failed"> = {
      pending: "pending",
      running: "running",
      success: "success",
      failed: "failed",
      needs_review: "failed",
    };

    setTimelineSteps([
      {
        node: "analyze_failure",
        status: job.status !== "pending" ? "success" : "running",
        message: job.error_type
          ? `Detected: ${job.error_type}`
          : "Analyzing failure logs...",
        timestamp: job.updated_at,
      },
      {
        node: "retrieve_context",
        status: job.status === "success" ? "success" : job.status === "running" ? "running" : "pending",
        message: job.repo_url ? `Context from ${job.repo_url}` : "Retrieving code context...",
      },
      {
        node: "generate_fix",
        status: job.proposed_fix ? "success" : job.status === "running" ? "running" : "pending",
        message: job.proposed_fix
          ? `Fix generated (${(job.confidence_score * 100).toFixed(0)}% confidence)`
          : "Generating fix...",
      },
      {
        node: "sandbox_verify",
        status: job.status === "success" ? "success" : job.status === "running" ? "running" : "pending",
        message: job.status === "success" ? "All tests passed ✓" : "Running sandbox tests...",
      },
      {
        node: "submit_pr",
        status: job.pr_url ? "success" : job.status === "failed" ? "failed" : "pending",
        message: job.pr_url
          ? "PR submitted successfully"
          : job.status === "failed"
          ? "Submission failed"
          : "Awaiting verification...",
      },
    ]);
  }, [job]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-surface-500 gap-4">
        <AlertTriangle className="w-12 h-12" />
        <p className="text-lg">Job not found</p>
        <Link to="/" className="text-primary-400 hover:text-primary-300 text-sm">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back & Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-sm text-surface-400 hover:text-surface-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Link>
        <StatusBadge status={job.status} size="lg" />
      </div>

      <div>
        <h1 className="text-xl font-bold gradient-text">
          Job <span className="font-mono text-surface-300">{job.job_id}</span>
        </h1>
        <p className="text-sm text-surface-400 mt-1 truncate">{job.repo_url}</p>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Timeline - left column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-5">
            <h2 className="text-sm font-semibold text-surface-200 mb-4">Execution Timeline</h2>
            <Timeline steps={timelineSteps} />
          </div>

          {/* Quick Info */}
          <div className="glass-card p-5 space-y-3">
            <h2 className="text-sm font-semibold text-surface-200">Details</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-surface-500">Attempts</span>
                <span className="text-surface-300 font-mono">
                  {job.attempts}/{job.max_attempts}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Confidence</span>
                <span className={clsx(
                  "font-mono",
                  job.confidence_score >= 0.7 ? "text-success" : job.confidence_score >= 0.4 ? "text-warning" : "text-danger"
                )}>
                  {(job.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-surface-500">Created</span>
                <span className="text-surface-300">{new Date(job.created_at).toLocaleString()}</span>
              </div>
              {job.pr_url && (
                <a
                  href={job.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-primary-400 hover:text-primary-300 pt-2"
                >
                  <GitPullRequest className="w-3.5 h-3.5" />
                  View Pull Request
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Right column - Logs & Diff */}
        <div className="lg:col-span-3 space-y-6">
          {/* Live Logs */}
          <LiveLogs logs={logs.map((l) => ({
            timestamp: l.timestamp,
            node: l.node,
            message: l.message,
            level: l.level,
          }))} connected={connected} />

          {/* Diff Viewer */}
          <div>
            <h2 className="text-sm font-semibold text-surface-200 mb-3">Proposed Fix</h2>
            <DiffViewer diff={job.proposed_fix} filename={job.error_type ? `fix: ${job.error_type}` : undefined} />
          </div>
        </div>
      </div>
    </div>
  );
}
