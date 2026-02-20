export function Alert({ tone = 'info', message }) {
  const toneStyle = {
    info: {
      borderColor: 'var(--border-subtle)',
      color: 'var(--text-secondary)',
      backgroundColor: 'var(--bg-surface-elevated)',
    },
    success: {
      borderColor: 'var(--accent-primary)',
      color: 'var(--accent-primary)',
      backgroundColor: 'var(--accent-soft)',
    },
    warning: {
      borderColor: 'var(--color-warning)',
      color: 'var(--color-warning)',
      backgroundColor: 'color-mix(in srgb, var(--color-warning) 14%, transparent)',
    },
    error: {
      borderColor: 'var(--color-error)',
      color: 'var(--color-error)',
      backgroundColor: 'color-mix(in srgb, var(--color-error) 10%, transparent)',
    },
  }

  return (
    <div
      role="alert"
      className="text-small"
      style={{
        border: '1px solid',
        borderRadius: '8px',
        padding: '10px 12px',
        ...toneStyle[tone],
      }}
    >
      {message}
    </div>
  )
}
