const ROLE_STYLES = {
  student: {
    color: 'var(--accent-primary)',
    backgroundColor: 'var(--accent-soft)',
    borderColor: 'var(--accent-primary)',
  },
  personnel: {
    color: 'var(--text-primary)',
    backgroundColor: 'var(--bg-surface-elevated)',
    borderColor: 'var(--border-strong)',
  },
  admin: {
    color: 'var(--color-warning)',
    backgroundColor: 'color-mix(in srgb, var(--color-warning) 12%, transparent)',
    borderColor: 'var(--color-warning)',
  },
}

export function RoleBadge({ role = 'student', label }) {
  const tone = ROLE_STYLES[role] || ROLE_STYLES.student

  return (
    <span
      className="text-caption"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        border: '1px solid',
        borderRadius: '999px',
        padding: '3px 8px',
        textTransform: 'capitalize',
        ...tone,
      }}
    >
      {label || role}
    </span>
  )
}
