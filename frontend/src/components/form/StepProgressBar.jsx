export function StepProgressBar({ currentStep, totalSteps, stepLabels = [] }) {
  const safeTotal = Math.max(1, totalSteps || 1)
  const safeCurrent = Math.min(Math.max(0, currentStep || 0), safeTotal - 1)
  const percentage = ((safeCurrent + 1) / safeTotal) * 100

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>

      {stepLabels.length > 0 ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${stepLabels.length}, minmax(0, 1fr))`,
            gap: '8px',
          }}
        >
          {stepLabels.map((label, index) => (
            <span
              key={`${label}-${index}`}
              className="text-small"
              style={{
                color: index <= safeCurrent ? 'var(--text-primary)' : 'var(--text-secondary)',
                opacity: index === safeCurrent ? 1 : 0.72,
              }}
            >
              {label}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  )
}
