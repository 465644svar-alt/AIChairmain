import { useState, useEffect, useRef, useCallback } from "react";

const DIRECTION_ICONS = {
  request: "\u2192",   // →
  response: "\u2190",  // ←
  error: "\u2716",     // ✖
  info: "\u2022",      // •
};

const DIRECTION_CLASS = {
  request: "log-request",
  response: "log-response",
  error: "log-error",
  info: "log-info",
};

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString("en-GB", { hour12: false }) +
    "." + String(d.getMilliseconds()).padStart(3, "0");
}

export default function LogViewer() {
  const [entries, setEntries] = useState([]);
  const [connected, setConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState("all"); // all | request | response | error | info
  const logEndRef = useRef(null);
  const containerRef = useRef(null);

  // Load existing logs on mount, then connect to SSE stream
  useEffect(() => {
    // Fetch history
    fetch("/api/logs")
      .then((r) => r.json())
      .then((data) => setEntries(data))
      .catch(() => {});

    // SSE real-time stream
    const es = new EventSource("/api/logs/stream");

    es.onopen = () => setConnected(true);

    es.onmessage = (event) => {
      try {
        const entry = JSON.parse(event.data);
        setEntries((prev) => {
          const next = [...prev, entry];
          // Cap at 500 entries in UI
          if (next.length > 500) next.splice(0, next.length - 500);
          return next;
        });
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      setConnected(false);
    };

    return () => es.close();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [entries, autoScroll]);

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  }, []);

  const clearLogs = () => setEntries([]);

  const filtered = filter === "all"
    ? entries
    : entries.filter((e) => e.direction === filter);

  return (
    <div className="log-viewer">
      <div className="log-toolbar">
        <div className="log-toolbar-left">
          <span className={`log-status ${connected ? "connected" : "disconnected"}`}>
            {connected ? "Live" : "Disconnected"}
          </span>
          <span className="log-count">{filtered.length} events</span>
        </div>
        <div className="log-toolbar-right">
          <select
            className="log-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All</option>
            <option value="request">Requests</option>
            <option value="response">Responses</option>
            <option value="error">Errors</option>
            <option value="info">Info</option>
          </select>
          <button className="log-clear" onClick={clearLogs}>
            Clear
          </button>
        </div>
      </div>

      <div
        className="log-container"
        ref={containerRef}
        onScroll={handleScroll}
      >
        {filtered.length === 0 && (
          <div className="log-empty">
            No log events yet. Run a council query to see requests and responses here.
          </div>
        )}
        {filtered.map((entry, i) => (
          <div key={i} className={`log-entry ${DIRECTION_CLASS[entry.direction] || ""}`}>
            <span className="log-time">{formatTime(entry.timestamp)}</span>
            <span className="log-icon">{DIRECTION_ICONS[entry.direction] || "?"}</span>
            <span className="log-stage">[{entry.stage}]</span>
            {entry.provider && (
              <span className="log-provider">{entry.provider}/{entry.model}</span>
            )}
            {entry.duration_ms != null && (
              <span className="log-duration">{entry.duration_ms}ms</span>
            )}
            <span className="log-content">{entry.content}</span>
            {entry.error && <span className="log-error-text">{entry.error}</span>}
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
