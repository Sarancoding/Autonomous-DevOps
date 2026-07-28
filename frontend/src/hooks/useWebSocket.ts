import { useCallback, useEffect, useRef, useState } from "react";

interface LogEntry {
  type: "log";
  job_id: string;
  node: string;
  message: string;
  level: string;
  timestamp: string;
}

interface UseWebSocketOptions {
  jobId: string | null;
  onLog?: (entry: LogEntry) => void;
}

export function useWebSocket({ jobId, onLog }: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (!jobId) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/jobs/${jobId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Attempt reconnect after 3s
      reconnectTimer.current = setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "log") {
          setLogs((prev) => [...prev, data]);
          onLog?.(data);
        }
      } catch {
        // Ignore non-JSON messages
      }
    };
  }, [jobId, onLog]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      wsRef.current = null;
      setConnected(false);
      setLogs([]);
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    wsRef.current?.send("ping");
  }, []);

  return { connected, logs, sendPing };
}
