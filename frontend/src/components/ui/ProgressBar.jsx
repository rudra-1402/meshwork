export function ProgressBar({ value = 0, max = 100 }) {
  const safeValue = Math.min(max, Math.max(0, value))
  const pct = max > 0 ? (safeValue / max) * 100 : 0

  return (
    <div className="progress-track">
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}
