import { ACCENT_RGB } from './formConstants'

export function ModeToggleLink({ onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        fontFamily: 'Satoshi, sans-serif',
        fontSize: 'inherit',
        fontWeight: 600,
        color: `rgba(${ACCENT_RGB}, 1)`,
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: 0,
        transition: 'opacity 180ms ease',
      }}
    >
      {children}
    </button>
  )
}
