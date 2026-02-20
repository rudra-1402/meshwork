import { Link } from 'react-router-dom'

export function MobileDrawer({ open, onClose, items = [] }) {
  if (!open) return null

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 400 }}>
      <button
        type="button"
        aria-label="Close navigation drawer"
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          border: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          height: '100%',
          width: 'min(340px, 84vw)',
          backgroundColor: 'var(--bg-surface)',
          borderLeft: '1px solid var(--border-subtle)',
          padding: '18px 14px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {items.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to}
                className="btn btn-ghost"
                onClick={onClose}
                style={{ justifyContent: 'flex-start', width: '100%' }}
              >
                {Icon ? <Icon size={16} /> : null}
                <span>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
