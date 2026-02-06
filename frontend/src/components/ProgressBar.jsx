const STAGES = [
  { key: "responses", label: "Responses" },
  { key: "review", label: "Peer Review" },
  { key: "synthesis", label: "Synthesis" },
  { key: "complete", label: "Complete" },
];

const STAGE_ORDER = ["responses", "review", "synthesis", "complete"];

export default function ProgressBar({ currentStage }) {
  const currentIdx = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className="progress-bar">
      {STAGES.map((stage, i) => (
        <div key={stage.key} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div
            className={`progress-step ${
              i < currentIdx ? "done" : i === currentIdx ? "active" : ""
            }`}
          >
            {i < currentIdx ? "\u2713" : i + 1} {stage.label}
          </div>
          {i < STAGES.length - 1 && (
            <div className={`progress-connector ${i < currentIdx ? "done" : ""}`} />
          )}
        </div>
      ))}
    </div>
  );
}
