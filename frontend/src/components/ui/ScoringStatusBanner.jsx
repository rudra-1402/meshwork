const STATUS_STYLES = {
  pending: {
    borderColor: 'var(--color-warning)',
    backgroundColor: 'color-mix(in srgb, var(--color-warning) 12%, transparent)',
    textColor: 'var(--color-warning)',
  },
  complete: {
    borderColor: 'var(--accent-primary)',
    backgroundColor: 'var(--accent-soft)',
    textColor: 'var(--accent-primary)',
  },
  blocked: {
    borderColor: 'var(--color-error)',
    backgroundColor: 'color-mix(in srgb, var(--color-error) 10%, transparent)',
    textColor: 'var(--color-error)',
  },
}

export function ScoringStatusBanner({
  status = 'pending',
  title = 'Scoring Status',
  description,
}) {
  const tone = STATUS_STYLES[status] || STATUS_STYLES.pending

  return (
    <section
      role="status"
      className="card"
      style={{
        border: '1px solid',
        borderColor: tone.borderColor,
        backgroundColor: tone.backgroundColor,
      }}
    >
      <h3 className="text-subsection" style={{ color: tone.textColor, marginBottom: description ? '6px' : 0 }}>
        {title}
      </h3>
      {description ? <p className="text-small" style={{ color: 'var(--text-secondary)' }}>{description}</p> : null}
    </section>
  )
}
