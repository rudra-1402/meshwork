export function StatRow({ items = [] }) {
  return (
    <div
      className="card"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${Math.max(items.length, 1)}, minmax(0, 1fr))`,
        gap: '10px',
      }}
    >
      {items.map((item) => (
        <div key={item.label}>
          <p className="text-caption text-muted" style={{ marginBottom: '4px' }}>
            {item.label}
          </p>
          <p className="text-body" style={{ fontWeight: 600 }}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  )
}
