export default function ReviewPanel({ reviews }) {
  if (!reviews || reviews.length === 0) return null;

  const rankClass = (rank) => {
    if (rank === 1) return "gold";
    if (rank === 2) return "silver";
    if (rank === 3) return "bronze";
    return "";
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>Peer Reviews</h2>
      {reviews.map((review) => (
        <div key={review.reviewer_id} className="review-card">
          <h4>Review by {review.reviewer_name}</h4>
          {review.rankings.map((r, i) => (
            <div key={i} className="ranking-item">
              {r.rank && (
                <span className={`rank-badge ${rankClass(r.rank)}`}>{r.rank}</span>
              )}
              <span>
                <strong>{r.response_label || `#${i + 1}`}</strong>
                {r.reasoning && ` — ${r.reasoning}`}
                {r.error && <span style={{ color: "var(--error)" }}> Error: {r.error}</span>}
              </span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
