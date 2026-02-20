export function Divider({ vertical = false, style }) {
  return (
    <div
      aria-hidden="true"
      style={{
        width: vertical ? '1px' : '100%',
        height: vertical ? '100%' : '1px',
        backgroundColor: 'var(--border-subtle)',
        ...style,
      }}
    />
  )
}
