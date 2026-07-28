import { clsx } from "clsx";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
}

const statusConfig: Record<string, { dot: string; label: string; bg: string }> = {
  pending: {
    dot: "status-dot--pending",
    label: "Pending",
    bg: "bg-warning/10 text-warning border-warning/20",
  },
  running: {
    dot: "status-dot--running",
    label: "Running",
    bg: "bg-primary-400/10 text-primary-400 border-primary-400/20",
  },
  success: {
    dot: "status-dot--success",
    label: "Success",
    bg: "bg-success/10 text-success border-success/20",
  },
  failed: {
    dot: "status-dot--failed",
    label: "Failed",
    bg: "bg-danger/10 text-danger border-danger/20",
  },
  needs_review: {
    dot: "status-dot--pending",
    label: "Needs Review",
    bg: "bg-accent/10 text-accent border-accent/20",
  },
};

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.pending;
  const sizeClasses = size === "sm" ? "text-xs px-2 py-0.5" : size === "lg" ? "text-sm px-4 py-1.5" : "text-xs px-3 py-1";

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border font-medium",
        config.bg,
        sizeClasses
      )}
    >
      <span className={clsx("status-dot", config.dot)} />
      {config.label}
    </span>
  );
}
