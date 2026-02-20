import { AnimatePresence, motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react'
import { MultiPaneLayout, PaneSurface } from '../layout'

export function SkeletonBlock({ height = 20 }) {
  return (
    <div
      style={{
        background:
          'linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-surface-elevated) 50%, var(--bg-surface) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
        borderRadius: '8px',
        height: `${height}px`,
      }}
    />
  )
}

export function AuthPageShell({
  title,
  icon,
  backTo = '/',
  leftPane,
  children,
}) {
  const HeaderIcon = icon

  return (
    <MultiPaneLayout
      panes={[
        {
          key: 'left-pane',
          ariaHidden: true,
          flex: '0 0 50%',
          padding: '28px 16px 28px 28px',
          content: leftPane,
        },
        {
          key: 'right-pane',
          flex: '0 0 50%',
          minWidth: 0,
          padding: '28px 28px 28px 16px',
          content: (
            <PaneSurface
              maxWidth="760px"
              padding="clamp(28px, 4vw, 56px)"
              border="1px solid var(--border-subtle)"
            >
              <div style={{ width: '100%', maxWidth: '500px' }}>
                <div className="flex items-center justify-between gap-4 mb-8">
                  <div className="flex items-center gap-3">
                    {HeaderIcon ? <HeaderIcon size={24} style={{ color: 'var(--accent-primary)' }} /> : null}
                    <h1 className="text-section-title">{title}</h1>
                  </div>

                  <Link to={backTo} className="btn btn-secondary inline-flex items-center gap-2">
                    <ArrowLeft size={16} /> Back to Landing
                  </Link>
                </div>

                {children}
              </div>
            </PaneSurface>
          ),
        },
      ]}
      style={{ minHeight: '100vh' }}
    />
  )
}

export function AuthLeftVisual({ mode = 'register' }) {
  return (
    <div
      style={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: '28px',
        flex: 1,
        backgroundColor: '#080b0d',
      }}
    >
      <motion.img
        key={mode}
        src={mode === 'login' ? '/auth-login.png' : '/auth-signup.png'}
        alt=""
        initial={{ opacity: 0, scale: 1.04 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.85, ease: [0.25, 0.1, 0.25, 1] }}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center 30%',
        }}
      />

      <motion.div
        animate={{ y: [0, -9, 0], scale: [1, 1.012, 1] }}
        transition={{ duration: 7.5, repeat: Infinity, ease: 'easeInOut' }}
        style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
      />

      <Link
        to="/"
        aria-label="MeshWork — back to home"
        style={{
          position: 'absolute',
          top: '32px',
          left: '40px',
          zIndex: 10,
          fontFamily: 'Clash Display, sans-serif',
          fontSize: '22px',
          fontWeight: '600',
          letterSpacing: '-0.02em',
          color: '#E6EDF3',
          textDecoration: 'none',
        }}
      >
        MeshWork
      </Link>

      <p
        style={{
          position: 'absolute',
          bottom: '32px',
          left: '40px',
          zIndex: 10,
          margin: 0,
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '12px',
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: 'rgba(230,237,243,0.35)',
        }}
      >
        Engineered, not designed.
      </p>
    </div>
  )
}

export function InlineErrorState({ message, onRetry }) {
  return (
    <div className="card p-8">
      <p className="text-body" style={{ color: 'var(--color-error)' }}>{message}</p>
      <div className="mt-6 flex gap-3">
        <button className="btn btn-primary" onClick={onRetry}>Retry</button>
        <Link to="/" className="btn btn-secondary">Go Home</Link>
      </div>
    </div>
  )
}

export function ToastMessage({ toast }) {
  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          key={toast.message}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          className="fixed bottom-6 right-6 card p-4 max-w-sm"
          style={{
            zIndex: 600,
            borderLeft: `4px solid ${toast.type === 'success' ? 'var(--accent-primary)' : 'var(--color-error)'}`,
          }}
        >
          <div className="flex items-start gap-3">
            {toast.type === 'success' ? (
              <CheckCircle2 size={18} style={{ color: 'var(--accent-primary)', marginTop: 2 }} />
            ) : (
              <AlertCircle size={18} style={{ color: 'var(--color-error)', marginTop: 2 }} />
            )}
            <p className="text-small" style={{ color: 'var(--text-primary)' }}>{toast.message}</p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
