import { Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'

export function Spinner({ size = 16, label = 'Loading' }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
      <motion.span
        animate={{ rotate: 360 }}
        transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
        style={{ display: 'inline-flex' }}
      >
        <Loader2 size={size} />
      </motion.span>
      <span className="text-small">{label}</span>
    </span>
  )
}
