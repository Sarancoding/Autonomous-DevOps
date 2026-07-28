import { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Zap,
  Loader2,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { api, type MetricsResponse } from "../services/api";
import { MetricsCard } from "../components/MetricsCard";
import { useAppStore } from "../stores/appStore";

const COLORS = {
  primary: "#6366f1",
  success: "#10b981",
  danger: "#ef4444",
  warning: "#f59e0b",
  accent: "#8b5cf6",
  surface: "#334155",
};

export function Analytics() {
  const { metrics, setMetrics } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const m = await api.metrics();
        setMetrics(m);
      } catch {
        // Backend might not be ready
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [setMetrics]);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
      </div>
    );
  }

  const pieData = [
    { name: "Success", value: metrics?.success_count ?? 0, color: COLORS.success },
    { name: "Failed", value: metrics?.failed_count ?? 0, color: COLORS.danger },
    { name: "Needs Review", value: metrics?.needs_review_count ?? 0, color: COLORS.warning },
  ].filter((d) => d.value > 0);

  const barData = [
    { name: "Success Rate", value: metrics && metrics.total_jobs > 0 ? (metrics.success_count / metrics.total_jobs) * 100 : 0, fill: COLORS.success },
    { name: "Avg Confidence", value: metrics ? metrics.avg_confidence * 100 : 0, fill: COLORS.primary },
    { name: "Avg Attempts", value: metrics?.avg_attempts_per_job ?? 0, fill: COLORS.accent },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <p className="text-sm text-surface-400 mt-1">
          Token usage, cost metrics, and agent performance
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Jobs"
          value={metrics?.total_jobs ?? 0}
          icon={BarChart3}
          color="primary"
        />
        <MetricsCard
          title="Success Rate"
          value={
            metrics && metrics.total_jobs > 0
              ? `${((metrics.success_count / metrics.total_jobs) * 100).toFixed(1)}%`
              : "—"
          }
          icon={TrendingUp}
          color="success"
        />
        <MetricsCard
          title="Tokens Used"
          value={(metrics?.total_tokens_used ?? 0).toLocaleString()}
          icon={Zap}
          color="warning"
        />
        <MetricsCard
          title="Est. Cost"
          value={`$${(metrics?.total_cost_estimate ?? 0).toFixed(4)}`}
          icon={DollarSign}
          color="accent"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Success Distribution Pie */}
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-surface-200 mb-4">Job Distribution</h2>
          <div className="h-64">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#e2e8f0",
                      fontSize: "12px",
                    }}
                  />
                  <Legend
                    formatter={(value) => (
                      <span className="text-xs text-surface-400">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-surface-500 text-sm">
                No data yet
              </div>
            )}
          </div>
        </div>

        {/* Performance Bar Chart */}
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-surface-200 mb-4">Performance Metrics</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "#334155" }}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "#334155" }}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    color: "#e2e8f0",
                    fontSize: "12px",
                  }}
                  formatter={(value: number) => [`${value.toFixed(1)}%`, ""]}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {barData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Summary table */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-surface-200 mb-4">Summary</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700">
                <th className="text-left py-2 text-surface-400 font-medium text-xs uppercase tracking-wider">Metric</th>
                <th className="text-right py-2 text-surface-400 font-medium text-xs uppercase tracking-wider">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-800">
              <tr>
                <td className="py-2.5 text-surface-300">Total Jobs</td>
                <td className="py-2.5 text-right text-surface-200 font-mono">{metrics?.total_jobs ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Successful</td>
                <td className="py-2.5 text-right text-success font-mono">{metrics?.success_count ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Failed</td>
                <td className="py-2.5 text-right text-danger font-mono">{metrics?.failed_count ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Needs Review</td>
                <td className="py-2.5 text-right text-warning font-mono">{metrics?.needs_review_count ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Avg Attempts / Job</td>
                <td className="py-2.5 text-right text-surface-200 font-mono">{metrics?.avg_attempts_per_job.toFixed(2) ?? "—"}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Avg Confidence</td>
                <td className="py-2.5 text-right text-surface-200 font-mono">{metrics ? `${(metrics.avg_confidence * 100).toFixed(1)}%` : "—"}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Total Tokens Used</td>
                <td className="py-2.5 text-right text-surface-200 font-mono">{metrics?.total_tokens_used.toLocaleString() ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2.5 text-surface-300">Estimated Cost</td>
                <td className="py-2.5 text-right text-surface-200 font-mono">${(metrics?.total_cost_estimate ?? 0).toFixed(4)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
