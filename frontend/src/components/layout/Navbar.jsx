import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function Navbar({ brand = 'MeshWork', navItems = [], rightSlot, sticky = true, brandTo }) {
  let user = null
  try {
    const auth = useAuth()
    user = auth?.user || null
  } catch {
    user = null
  }
  const [scrolled, setScrolled] = useState(false)
  const [hovered, setHovered] = useState(null)

  const resolvedBrandTo = brandTo || (user?.user_type === 'personnel' ? '/personnel/dashboard' : '/home')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      role="banner"
      style={{
        position: sticky ? 'sticky' : 'relative',
        top: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '68px',
        paddingInline: '24px',
        backgroundColor: scrolled ? 'color-mix(in srgb, var(--bg-primary) 88%, transparent)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid var(--border-subtle)' : 'none',
        transition: 'background-color 300ms ease, border-color 300ms ease, backdrop-filter 300ms ease',
      }}
    >
      <Link
        to={resolvedBrandTo}
        aria-label="MeshWork home"
        style={{
          fontFamily: 'Clash Display, sans-serif',
          fontSize: '24px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: 'var(--text-primary)',
          textDecoration: 'none',
        }}
      >
        {brand}
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <nav aria-label="Primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '4px',
              borderRadius: '12px',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'rgba(255,255,255,0.015)',
              gap: '2px',
            }}
          >
            {navItems.map((item) => {
              const isHovered = hovered === item.label
              const Icon = item.icon

              return (
                <Link
                  key={item.label}
                  to={item.to || item.href || '/home'}
                  onMouseEnter={() => setHovered(item.label)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: '6px 9px',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    backgroundColor: isHovered ? 'var(--bg-surface-elevated)' : 'transparent',
                    transition: 'background-color 160ms ease',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {Icon ? (
                    <Icon
                      size={14}
                      style={{
                        color: isHovered ? 'var(--accent-primary)' : 'var(--text-secondary)',
                        transition: 'color 160ms ease',
                        flexShrink: 0,
                      }}
                    />
                  ) : null}

                  <span
                    style={{
                      fontFamily: 'Satoshi, sans-serif',
                      fontSize: '13px',
                      fontWeight: 500,
                      color: 'var(--text-primary)',
                      maxWidth: isHovered ? '90px' : '0px',
                      opacity: isHovered ? 1 : 0,
                      overflow: 'hidden',
                      transition: 'max-width 240ms ease, opacity 180ms ease',
                    }}
                  >
                    {item.label}
                  </span>
                </Link>
              )
            })}
          </div>
        </nav>

        {rightSlot ? rightSlot : null}
      </div>
    </header>
  )
}
