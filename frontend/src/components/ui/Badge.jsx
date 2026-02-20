export function Badge({ children, tone = 'neutral' }) {
  const styleByTone = {
    neutral: {
      color: 'var(--text-secondary)',
      backgroundColor: 'var(--bg-surface-elevated)',
      borderColor: 'var(--border-subtle)',
    },
    success: {
      color: 'var(--accent-primary)',
      backgroundColor: 'var(--accent-soft)',
      borderColor: 'var(--accent-primary)',
    },
    warning: {
      color: 'var(--color-warning)',
      backgroundColor: 'color-mix(in srgb, var(--color-warning) 16%, transparent)',
      borderColor: 'var(--color-warning)',
    },
    error: {
      color: 'var(--color-error)',
      backgroundColor: 'color-mix(in srgb, var(--color-error) 12%, transparent)',
      borderColor: 'var(--color-error)',
    },
  }

  return (
    <span
      className="text-small"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        border: '1px solid',
        borderRadius: '999px',
        padding: '2px 10px',
        fontWeight: 600,
        ...styleByTone[tone],
      }}
    >
      {children}
    </span>
  )
}
