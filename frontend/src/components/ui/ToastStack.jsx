import { useEffect, useState } from 'react'

function ToastItem({ toast, onDismiss }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const inTimer = setTimeout(() => setVisible(true), 12)
    const outTimer = setTimeout(() => {
      setVisible(false)
      setTimeout(() => onDismiss(toast.id), 220)
    }, toast.duration || 4000)

    return () => {
      clearTimeout(inTimer)
      clearTimeout(outTimer)
    }
  }, [toast, onDismiss])

  const borderColor = toast.type === 'error' ? 'var(--color-error)' : 'var(--accent-primary)'

  return (
    <div
      role="status"
      className="card"
      style={{
        padding: '12px 14px',
        borderLeft: `4px solid ${borderColor}`,
        transform: visible ? 'translateY(0)' : 'translateY(16px)',
        opacity: visible ? 1 : 0,
        transition: 'transform 180ms ease, opacity 180ms ease',
      }}
    >
      <p className="text-small" style={{ color: 'var(--text-primary)', margin: 0 }}>
        {toast.message}
      </p>
    </div>
  )
}

export function ToastStack({ toasts = [], onDismiss }) {
  if (!toasts.length) return null

  return (
    <div
      style={{
        position: 'fixed',
        right: '24px',
        bottom: '24px',
        zIndex: 600,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        width: 'min(360px, calc(100vw - 32px))',
      }}
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
