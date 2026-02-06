import { useState, useCallback } from "react";
import QueryForm from "./components/QueryForm.jsx";
import ProgressBar from "./components/ProgressBar.jsx";
import ResponseTabs from "./components/ResponseTabs.jsx";
import ReviewPanel from "./components/ReviewPanel.jsx";
import SynthesisPanel from "./components/SynthesisPanel.jsx";
import SessionHistory from "./components/SessionHistory.jsx";
import {
  runFullCouncil,
  startSession,
  runReview,
  runSynthesis,
} from "./api/council.js";

export default function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("full"); // "full" or "step"
  const [loadingStage, setLoadingStage] = useState(null);

  const handleFullRun = useCallback(async (query) => {
    setLoading(true);
    setError(null);
    setSession(null);
    setLoadingStage("responses");
    try {
      const result = await runFullCouncil(query);
      setSession(result);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
    setLoadingStage(null);
  }, []);

  const handleStepStart = useCallback(async (query) => {
    setLoading(true);
    setError(null);
    setSession(null);
    setLoadingStage("responses");
    try {
      const result = await startSession(query);
      setSession(result);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
    setLoadingStage(null);
  }, []);

  const handleNextStep = useCallback(async () => {
    if (!session) return;
    setLoading(true);
    setError(null);

    try {
      if (session.stage === "review") {
        setLoadingStage("review");
        const result = await runReview(session.session_id);
        setSession(result);
      } else if (session.stage === "synthesis") {
        setLoadingStage("synthesis");
        const result = await runSynthesis(session.session_id);
        setSession(result);
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
    setLoadingStage(null);
  }, [session]);

  const handleSubmit = mode === "full" ? handleFullRun : handleStepStart;

  const handleLoadSession = (s) => {
    setSession(s);
    setError(null);
  };

  const stageLabel = {
    responses: "Gathering responses from council members...",
    review: "Council members are reviewing each other's responses...",
    synthesis: "Chairman is synthesizing the final answer...",
  };

  return (
    <div>
      <header className="header">
        <h1>AIChairmain</h1>
        <p>A council of LLMs deliberates on your question</p>
      </header>

      <QueryForm
        onSubmit={handleSubmit}
        loading={loading}
        mode={mode}
        onModeChange={setMode}
      />

      {error && <div className="error-msg">{error}</div>}

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>{stageLabel[loadingStage] || "Processing..."}</span>
        </div>
      )}

      {session && (
        <>
          <ProgressBar currentStage={session.stage} />

          {session.responses.length > 0 && (
            <section style={{ marginBottom: "1.5rem" }}>
              <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
                Individual Responses
              </h2>
              <ResponseTabs responses={session.responses} />
            </section>
          )}

          {session.reviews.length > 0 && (
            <section style={{ marginBottom: "1.5rem" }}>
              <ReviewPanel reviews={session.reviews} />
            </section>
          )}

          {session.synthesis && (
            <section style={{ marginBottom: "1.5rem" }}>
              <SynthesisPanel synthesis={session.synthesis} />
            </section>
          )}

          {mode === "step" && !loading && session.stage !== "complete" && (
            <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
              <button className="btn-primary" onClick={handleNextStep}>
                {session.stage === "review"
                  ? "Run Peer Review"
                  : session.stage === "synthesis"
                  ? "Run Synthesis"
                  : "Next Step"}
              </button>
            </div>
          )}
        </>
      )}

      <SessionHistory onLoadSession={handleLoadSession} />
    </div>
  );
}
