import { Avatar } from './Avatar'
import { RoleBadge } from './RoleBadge'

export function UserCard({
  name,
  subtitle,
  role = 'student',
  rightSlot,
}) {
  return (
    <article className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
        <Avatar name={name} />
        <div style={{ minWidth: 0 }}>
          <p className="text-body" style={{ fontWeight: 600 }}>{name}</p>
          {subtitle ? <p className="text-caption text-muted">{subtitle}</p> : null}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <RoleBadge role={role} />
        {rightSlot}
      </div>
    </article>
  )
}
