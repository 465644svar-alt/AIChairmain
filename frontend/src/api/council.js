const API_BASE = "/api";

export async function getMembers() {
  const res = await fetch(`${API_BASE}/council/members`);
  if (!res.ok) throw new Error("Failed to fetch council members");
  return res.json();
}

export async function runFullCouncil(query) {
  const res = await fetch(`${API_BASE}/council/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Council request failed");
  }
  return res.json();
}

export async function startSession(query) {
  const res = await fetch(`${API_BASE}/council/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to start session");
  }
  return res.json();
}

export async function runReview(sessionId) {
  const res = await fetch(`${API_BASE}/council/${sessionId}/review`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Review failed");
  }
  return res.json();
}

export async function runSynthesis(sessionId) {
  const res = await fetch(`${API_BASE}/council/${sessionId}/synthesize`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Synthesis failed");
  }
  return res.json();
}

export async function getSession(sessionId) {
  const res = await fetch(`${API_BASE}/council/${sessionId}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}

export async function listSessions() {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error("Failed to list sessions");
  return res.json();
}
