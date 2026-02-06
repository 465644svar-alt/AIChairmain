import ReactMarkdown from "react-markdown";

export default function SynthesisPanel({ synthesis }) {
  if (!synthesis) return null;

  return (
    <div className="synthesis-card">
      <div className="card-header">
        <h3>Chairman's Synthesis</h3>
        <span className="badge">{synthesis.chairman_model}</span>
      </div>
      <div className="response-content">
        <ReactMarkdown>{synthesis.synthesis}</ReactMarkdown>
      </div>
    </div>
  );
}
