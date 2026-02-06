import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ResponseTabs({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) return null;

  const current = responses[activeTab];

  return (
    <div>
      <div className="tabs">
        {responses.map((r, i) => (
          <button
            key={r.member_id}
            className={`tab ${i === activeTab ? "active" : ""} ${r.error ? "error" : ""}`}
            onClick={() => setActiveTab(i)}
          >
            {r.member_name}
          </button>
        ))}
      </div>
      <div className="card">
        <div className="card-header">
          <h3>{current.member_name}</h3>
          <span className="badge">{current.model}</span>
        </div>
        {current.error ? (
          <div className="error-msg">{current.error}</div>
        ) : (
          <div className="response-content">
            <ReactMarkdown>{current.response}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
