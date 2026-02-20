import { AnimatePresence, motion } from 'framer-motion'
import { EASE } from './formConstants'

export function Field({ label, htmlFor, error, children }) {
  return (
    <motion.div layout style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label ? (
        <label
          htmlFor={htmlFor}
          style={{
            fontFamily: 'Satoshi, sans-serif',
            fontSize: '13px',
            fontWeight: 500,
            color: 'var(--text-secondary)',
            letterSpacing: '0.02em',
          }}
        >
          {label}
        </label>
      ) : null}

      {children}

      <AnimatePresence initial={false}>
        {error ? (
          <motion.span
            key="field-error"
            role="alert"
            initial={{ opacity: 0, height: 0, y: -3 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -3 }}
            transition={{ duration: 0.17, ease: EASE }}
            style={{
              overflow: 'hidden',
              fontFamily: 'Satoshi, sans-serif',
              fontSize: '12px',
              color: 'var(--color-error)',
            }}
          >
            {error}
          </motion.span>
        ) : null}
      </AnimatePresence>
    </motion.div>
  )
}
