import { clsx } from "clsx";
import { CheckCircle2, Circle, XCircle, Loader2, GitPullRequest, AlertTriangle } from "lucide-react";

interface TimelineStep {
  node: string;
  status: "pending" | "running" | "success" | "failed";
  message: string;
  timestamp?: string;
}

interface TimelineProps {
  steps: TimelineStep[];
}

const nodeIcons: Record<string, React.ReactNode> = {
  analyze_failure: <Circle className="w-4 h-4" />,
  retrieve_context: <Circle className="w-4 h-4" />,
  generate_fix: <Circle className="w-4 h-4" />,
  sandbox_verify: <Circle className="w-4 h-4" />,
  submit_pr: <GitPullRequest className="w-4 h-4" />,
  flag_for_human: <AlertTriangle className="w-4 h-4" />,
};

const statusColors: Record<string, string> = {
  pending: "text-surface-500",
  running: "text-primary-400",
  success: "text-success",
  failed: "text-danger",
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <div className="w-4 h-4 rounded-full border-2 border-surface-600" />,
  running: <Loader2 className="w-4 h-4 animate-spin" />,
  success: <CheckCircle2 className="w-4 h-4" />,
  failed: <XCircle className="w-4 h-4" />,
};

const nodeLabels: Record<string, string> = {
  analyze_failure: "Analyze Failure",
  retrieve_context: "Retrieve Context",
  generate_fix: "Generate Fix",
  sandbox_verify: "Sandbox Verify",
  submit_pr: "Submit PR",
  flag_for_human: "Flag for Review",
};

export function Timeline({ steps }: TimelineProps) {
  if (steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-surface-500 gap-2">
        <Loader2 className="w-6 h-6 animate-spin" />
        <p className="text-sm">Waiting for execution to begin...</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-4">
          {/* Timeline line */}
          <div className="flex flex-col items-center">
            <div
              className={clsx(
                "flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors duration-300",
                statusColors[step.status],
                step.status === "running" && "border-primary-400 bg-primary-400/10",
                step.status === "success" && "border-success bg-success/10",
                step.status === "failed" && "border-danger bg-danger/10",
                step.status === "pending" && "border-surface-600 bg-surface-800"
              )}
            >
              {step.status === "running" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : step.status === "success" ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : step.status === "failed" ? (
                <XCircle className="w-4 h-4" />
              ) : (
                <div className="w-2 h-2 rounded-full bg-surface-600" />
              )}
            </div>
            {i < steps.length - 1 && (
              <div
                className={clsx(
                  "w-0.5 h-8",
                  step.status === "success" ? "bg-success/30" : "bg-surface-700"
                )}
              />
            )}
          </div>

          {/* Content */}
          <div className="pb-6 pt-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-surface-200">
                {nodeLabels[step.node] || step.node}
              </span>
              {step.timestamp && (
                <span className="text-[10px] text-surface-500 font-mono">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </span>
              )}
            </div>
            <p className="text-xs text-surface-400 mt-0.5">{step.message}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
