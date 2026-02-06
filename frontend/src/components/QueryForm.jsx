import { useState } from "react";

export default function QueryForm({ onSubmit, loading, mode, onModeChange }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <>
      <div className="mode-toggle">
        <button
          className={mode === "full" ? "active" : ""}
          onClick={() => onModeChange("full")}
        >
          Full Council (auto)
        </button>
        <button
          className={mode === "step" ? "active" : ""}
          onClick={() => onModeChange("step")}
        >
          Step-by-Step
        </button>
      </div>
      <form className="query-form" onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the council a question..."
          rows={2}
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
          {loading ? "Deliberating..." : "Ask Council"}
        </button>
      </form>
    </>
  );
}
