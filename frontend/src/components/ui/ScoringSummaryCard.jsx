export function ScoringSummaryCard({
  title = 'Scoring Summary',
  score,
  level,
  nextLevelHint,
}) {
  return (
    <section className="card">
      <h3 className="text-subsection" style={{ marginBottom: '10px' }}>
        {title}
      </h3>

      <div style={{ display: 'grid', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span className="text-small text-muted">Score</span>
          <span className="text-small" style={{ fontWeight: 600 }}>{score}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span className="text-small text-muted">Level</span>
          <span className="text-small" style={{ fontWeight: 600 }}>{level}</span>
        </div>
      </div>

      {nextLevelHint ? (
        <p className="text-caption text-muted" style={{ marginTop: '10px' }}>
          {nextLevelHint}
        </p>
      ) : null}
    </section>
  )
}
