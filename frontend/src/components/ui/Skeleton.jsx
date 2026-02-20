export function Skeleton({ width = '100%', height = 16, radius = 8 }) {
  return (
    <div
      style={{
        width,
        height: `${height}px`,
        borderRadius: `${radius}px`,
        background: 'linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-surface-elevated) 50%, var(--bg-surface) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
      }}
    />
  )
}
