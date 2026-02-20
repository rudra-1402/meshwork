export function Grid({ columns = 'repeat(12, minmax(0, 1fr))', gap = 16, children, style }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: columns,
        gap: `${gap}px`,
        ...style,
      }}
    >
      {children}
    </div>
  )
}
