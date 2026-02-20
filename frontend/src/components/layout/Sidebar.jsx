import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'

export function Sidebar({
  items = [],
  brand = 'MeshWork',
  brandTo = '/home',
  collapsed = false,
  onToggle,
}) {
  const location = useLocation()
  const [hoverExpanded, setHoverExpanded] = useState(false)

  const shouldOverlayExpand = collapsed && hoverExpanded
  const panelWidth = 264
  const railWidth = 84

  const resolvedItems = useMemo(() => {
    return items.map((item) => {
      const active = item.active || location.pathname === item.to || location.pathname === item.href
      return { ...item, active }
    })
  }, [items, location.pathname])

  const renderItem = (item, showLabel) => {
    const Icon = item.icon
    return (
      <Link
        key={item.to || item.href || item.label}
        to={item.to || item.href || '/home'}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: showLabel ? 'flex-start' : 'center',
          gap: '10px',
          width: '100%',
          borderRadius: '10px',
          padding: showLabel ? '10px 12px' : '10px',
          border: '1px solid',
          borderColor: item.active ? 'rgba(255,255,255,0.14)' : 'transparent',
          backgroundColor: item.active ? 'rgba(255,255,255,0.06)' : 'transparent',
          color: item.active ? 'var(--text-primary)' : 'var(--text-secondary)',
          transition: 'background-color 160ms ease, border-color 160ms ease, color 160ms ease',
        }}
      >
        {Icon ? <Icon size={16} color={item.active ? 'var(--accent-primary)' : 'currentColor'} /> : null}
        {showLabel ? <span className="text-small" style={{ fontWeight: item.active ? 600 : 500 }}>{item.label}</span> : null}
      </Link>
    )
  }

  return (
    <aside
      onMouseEnter={() => setHoverExpanded(true)}
      onMouseLeave={() => setHoverExpanded(false)}
      style={{
        width: collapsed ? `${railWidth}px` : `${panelWidth}px`,
        borderRight: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-surface)',
        padding: '16px 12px',
        transition: 'width 220ms ease',
        position: 'sticky',
        top: '10px',
        height: 'calc(100vh - 78px)',
        zIndex: 60,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', marginBottom: '16px' }}>
        <Link
          to={brandTo}
          style={{
            display: 'block',
            padding: '8px 10px',
            fontFamily: 'Clash Display, sans-serif',
            fontSize: '20px',
            fontWeight: 600,
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)',
            textDecoration: 'none',
          }}
        >
          {collapsed ? 'MW' : brand}
        </Link>

        {!collapsed ? (
          <button
            type="button"
            onClick={onToggle}
            aria-label="Collapse sidebar"
            className="btn-icon"
          >
            <ChevronLeft size={16} />
          </button>
        ) : null}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {resolvedItems.map((item) => renderItem(item, !collapsed))}
      </div>

      {shouldOverlayExpand ? (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: `${panelWidth}px`,
            minHeight: '100%',
            padding: '16px 12px',
            backgroundColor: 'var(--bg-surface)',
            borderRight: '1px solid rgba(255,255,255,0.12)',
            boxShadow: '0 14px 30px rgba(0,0,0,0.35)',
            zIndex: 80,
            animation: 'sidebar-slide-in 220ms ease forwards',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <Link
              to={brandTo}
              style={{
                padding: '8px 10px',
                fontFamily: 'Clash Display, sans-serif',
                fontSize: '20px',
                fontWeight: 600,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
                textDecoration: 'none',
              }}
            >
              {brand}
            </Link>
            <button
              type="button"
              onClick={onToggle}
              aria-label="Expand sidebar"
              className="btn-icon"
            >
              <ChevronRight size={16} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {resolvedItems.map((item) => renderItem(item, true))}
          </div>
        </div>
      ) : null}

      {collapsed ? (
        <button
          type="button"
          onClick={onToggle}
          aria-label="Expand sidebar"
          className="btn-icon"
          style={{
            position: 'absolute',
            bottom: '14px',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          <ChevronRight size={16} />
        </button>
      ) : null}
    </aside>
  )
}
