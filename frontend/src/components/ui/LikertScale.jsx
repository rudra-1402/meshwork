export function LikertScale({
  value,
  onChange,
  options = [
    { value: 1, label: 'Strongly Disagree' },
    { value: 2, label: 'Disagree' },
    { value: 3, label: 'Neutral' },
    { value: 4, label: 'Agree' },
    { value: 5, label: 'Strongly Agree' },
  ],
  ariaLabel = 'Likert Scale',
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      style={{ display: 'grid', gap: '8px' }}
    >
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            className="text-small"
            onClick={() => onChange?.(option.value)}
            style={{
              textAlign: 'left',
              border: '1px solid',
              borderColor: selected ? 'var(--accent-primary)' : 'var(--border-subtle)',
              backgroundColor: selected ? 'var(--accent-soft)' : 'var(--bg-surface)',
              color: selected ? 'var(--accent-primary)' : 'var(--text-secondary)',
              borderRadius: '10px',
              padding: '10px 12px',
            }}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
