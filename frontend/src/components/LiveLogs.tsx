import { useEffect, useRef } from "react";
import { clsx } from "clsx";
import { Terminal, AlertCircle, CheckCircle, Loader2 } from "lucide-react";

interface LogEntry {
  timestamp: string;
  node: string;
  message: string;
  level: string;
}

interface LiveLogsProps {
  logs: LogEntry[];
  connected?: boolean;
}

const levelStyles: Record<string, string> = {
  info: "text-surface-300",
  warn: "text-warning",
  warning: "text-warning",
  error: "text-danger",
  success: "text-success",
};

const levelIcons: Record<string, React.ReactNode> = {
  info: <Terminal className="w-3.5 h-3.5" />,
  warn: <AlertCircle className="w-3.5 h-3.5" />,
  warning: <AlertCircle className="w-3.5 h-3.5" />,
  error: <AlertCircle className="w-3.5 h-3.5" />,
  success: <CheckCircle className="w-3.5 h-3.5" />,
};

export function LiveLogs({ logs, connected }: LiveLogsProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-700 bg-surface-900/80">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary-400" />
          <span className="text-sm font-medium text-surface-200">Agent Logs</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              "inline-block w-1.5 h-1.5 rounded-full",
              connected ? "bg-success animate-pulse" : "bg-surface-500"
            )}
          />
          <span className="text-xs text-surface-400">
            {connected ? "Live" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Log entries */}
      <div className="h-80 overflow-y-auto p-4 space-y-1 font-mono text-xs">
        {logs.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-surface-500 gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Waiting for agent logs...</span>
          </div>
        )}
        {logs.map((log, i) => (
          <div
            key={i}
            className={clsx(
              "flex items-start gap-2 py-0.5 hover:bg-surface-800/40 rounded px-1 transition-colors",
              levelStyles[log.level] ?? "text-surface-300"
            )}
          >
            <span className="mt-0.5 shrink-0">
              {levelIcons[log.level] ?? levelIcons.info}
            </span>
            <span className="text-surface-500 shrink-0">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className="text-surface-600 shrink-0">[{log.node}]</span>
            <span className="break-words">{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
