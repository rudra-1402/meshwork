import { useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { ACCENT_RGB, EASE, MORPH_TRANSITION } from './formConstants'

export function SubmitButton({
  loading,
  disabled = false,
  label,
  loadingLabel = 'Processing…',
  type = 'button',
  onClick,
  fullWidth = true,
}) {
  const [hovered, setHovered] = useState(false)
  const isDisabled = loading || disabled

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      className="btn btn-primary"
      style={{
        width: fullWidth ? '100%' : 'auto',
        overflow: 'hidden',
        borderRadius: '999px',
        position: 'relative',
        opacity: isDisabled ? 0.55 : 1,
        boxShadow: `0 4px 12px rgba(${ACCENT_RGB}, 0.20)`,
      }}
      whileHover={!isDisabled ? {
        backgroundColor: 'var(--accent-hover)',
        boxShadow: `0 8px 24px rgba(${ACCENT_RGB}, 0.36)`,
      } : {}}
      whileTap={!isDisabled ? { scale: 0.97, y: -1 } : {}}
      transition={MORPH_TRANSITION}
      aria-label={loading ? 'Processing, please wait' : undefined}
    >
      {loading ? (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
            style={{ display: 'flex' }}
          >
            <Loader2 size={16} strokeWidth={2} />
          </motion.span>
          {loadingLabel}
        </span>
      ) : (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <motion.span
            animate={{ x: hovered ? -6 : 0 }}
            transition={{ duration: 0.22, ease: EASE }}
            style={{ display: 'inline-block' }}
          >
            {label}
          </motion.span>
          <motion.span
            animate={{ x: hovered ? 6 : 24, opacity: hovered ? 1 : 0 }}
            transition={{ duration: 0.22, ease: EASE }}
            style={{ display: 'inline-flex', alignItems: 'center', lineHeight: 1 }}
          >
            →
          </motion.span>
        </span>
      )}
    </motion.button>
  )
}
