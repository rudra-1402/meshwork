import { X } from 'lucide-react'

export function Chip({ label, selected = false, removable = false, onClick, onRemove }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-small"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        borderRadius: '999px',
        border: '1px solid',
        borderColor: selected ? 'var(--accent-primary)' : 'var(--border-subtle)',
        color: selected ? 'var(--accent-primary)' : 'var(--text-secondary)',
        backgroundColor: selected ? 'var(--accent-soft)' : 'var(--bg-surface)',
        padding: '4px 10px',
      }}
    >
      <span>{label}</span>
      {removable ? (
        <span
          role="button"
          aria-label={`Remove ${label}`}
          onClick={(event) => {
            event.stopPropagation()
            if (onRemove) onRemove()
          }}
          style={{ display: 'inline-flex' }}
        >
          <X size={12} />
        </span>
      ) : null}
    </button>
  )
}
