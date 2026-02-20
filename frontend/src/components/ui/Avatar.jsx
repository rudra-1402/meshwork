export function Avatar({ src, alt, name = '', size = 40 }) {
  const initials = name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((value) => value[0]?.toUpperCase())
    .join('')

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '999px',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-surface-elevated)',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {src ? (
        <img src={src} alt={alt || name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      ) : (
        <span className="text-small" style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>
          {initials || 'U'}
        </span>
      )}
    </div>
  )
}
