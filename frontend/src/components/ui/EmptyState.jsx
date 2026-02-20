export function EmptyState({ title = 'No items yet', description, action }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <h3 className="text-subsection" style={{ marginBottom: '8px' }}>{title}</h3>
      {description ? <p className="text-body text-muted" style={{ marginBottom: action ? '14px' : 0 }}>{description}</p> : null}
      {action}
    </div>
  )
}
