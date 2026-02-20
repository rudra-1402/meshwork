export function MotivationMeter({
  value = 0,
  max = 100,
  label = 'Motivation',
}) {
  const safeValue = Math.max(0, Math.min(value, max))
  const percentage = max > 0 ? Math.round((safeValue / max) * 100) : 0

  return (
    <section className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <p className="text-small text-muted">{label}</p>
        <p className="text-small" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
          {percentage}%
        </p>
      </div>
      <div className="progress-track" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={safeValue} role="progressbar">
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
    </section>
  )
}
