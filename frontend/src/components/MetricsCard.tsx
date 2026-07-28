import { clsx } from "clsx";
import { type LucideIcon } from "lucide-react";

interface MetricsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color?: "primary" | "success" | "warning" | "danger" | "accent";
}

const colorMap: Record<string, string> = {
  primary: "from-primary-500/20 to-primary-600/5 border-primary-500/20",
  success: "from-success/20 to-success/5 border-success/20",
  warning: "from-warning/20 to-warning/5 border-warning/20",
  danger: "from-danger/20 to-danger/5 border-danger/20",
  accent: "from-accent/20 to-accent/5 border-accent/20",
};

const iconColorMap: Record<string, string> = {
  primary: "text-primary-400",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  accent: "text-accent",
};

export function MetricsCard({ title, value, subtitle, icon: Icon, trend, color = "primary" }: MetricsCardProps) {
  return (
    <div
      className={clsx(
        "glass-card p-5 border bg-gradient-to-br",
        colorMap[color]
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">{title}</p>
          <p className="text-3xl font-bold tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-xs text-surface-500">{subtitle}</p>
          )}
        </div>
        <div className={clsx("p-3 rounded-lg bg-surface-800/50", iconColorMap[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1">
          <span
            className={clsx(
              "text-xs font-medium",
              trend === "up" && "text-success",
              trend === "down" && "text-danger",
              trend === "neutral" && "text-surface-400"
            )}
          >
            {trend === "up" && "↑"} {trend === "down" && "↓"} {trend === "neutral" && "—"}
          </span>
        </div>
      )}
    </div>
  );
}
