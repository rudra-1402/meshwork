export function KbdShortcut({ children }) {
  return (
    <kbd
      className="text-small"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '6px',
        border: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-surface-elevated)',
        color: 'var(--text-secondary)',
        fontFamily: 'JetBrains Mono, monospace',
      }}
    >
      {children}
    </kbd>
  )
}
