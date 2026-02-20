export function Tabs({
  tabs = [],
  value,
  onChange,
  ariaLabel = 'Tabs',
  fullWidth = false,
}) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      style={{
        display: 'flex',
        gap: '8px',
        width: fullWidth ? '100%' : 'fit-content',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '6px',
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab.value === value

        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange?.(tab.value)}
            className="text-small"
            style={{
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              padding: '6px 10px',
              borderRadius: '999px',
              color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--accent-soft)' : 'transparent',
              width: fullWidth ? '100%' : undefined,
            }}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
