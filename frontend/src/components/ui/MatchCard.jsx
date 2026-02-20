import { ProgressBar } from './ProgressBar'

export function MatchCard({
  title,
  description,
  percent = 0,
  tags = [],
  action,
}) {
  return (
    <article className="card" style={{ display: 'grid', gap: '10px' }}>
      <div>
        <h3 className="text-subsection">{title}</h3>
        {description ? <p className="text-small text-muted" style={{ marginTop: '4px' }}>{description}</p> : null}
      </div>

      <div style={{ display: 'grid', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span className="text-caption text-muted">Match</span>
          <span className="text-caption" style={{ fontWeight: 600 }}>{percent}%</span>
        </div>
        <ProgressBar value={percent} max={100} />
      </div>

      {tags.length > 0 ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {tags.map((tag) => (
            <span
              key={tag}
              className="text-caption"
              style={{
                border: '1px solid var(--border-subtle)',
                backgroundColor: 'var(--bg-surface-elevated)',
                borderRadius: '999px',
                padding: '3px 8px',
                color: 'var(--text-secondary)',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {action}
    </article>
  )
}
