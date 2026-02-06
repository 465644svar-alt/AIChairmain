import { useState, useEffect } from "react";
import { listSessions, getSession } from "../api/council.js";

export default function SessionHistory({ onLoadSession }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await listSessions();
      setSessions(data);
    } catch {
      // silently fail — history is optional
    }
  };

  const handleClick = async (sessionId) => {
    setLoading(true);
    try {
      const session = await getSession(sessionId);
      onLoadSession(session);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  if (sessions.length === 0) return null;

  return (
    <div style={{ marginTop: "2rem" }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>Previous Sessions</h2>
      {loading && (
        <div className="loading">
          <div className="spinner" />
        </div>
      )}
      <ul className="history-list">
        {sessions.map((s) => (
          <li
            key={s.session_id}
            className="history-item"
            onClick={() => handleClick(s.session_id)}
          >
            <span className="history-query">{s.query}</span>
            <span className="history-stage">{s.stage}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
