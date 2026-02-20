export function Stat({ label, value, hint, trend }) {
  return (
    <article className="card" style={{ padding: '14px' }}>
      <p className="text-caption text-muted" style={{ marginBottom: '6px' }}>
        {label}
      </p>
      <p className="text-subsection" style={{ marginBottom: hint || trend ? '6px' : 0 }}>
        {value}
      </p>
      {hint ? <p className="text-small text-muted">{hint}</p> : null}
      {trend ? (
        <p className="text-small" style={{ color: 'var(--accent-primary)', marginTop: hint ? '4px' : 0 }}>
          {trend}
        </p>
      ) : null}
    </article>
  )
}
