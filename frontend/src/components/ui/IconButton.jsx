import { motion } from 'framer-motion'

export function IconButton({ icon: Icon, ariaLabel, onClick, disabled = false, size = 18, style }) {
  return (
    <motion.button
      type="button"
      className="btn-icon"
      aria-label={ariaLabel}
      onClick={onClick}
      disabled={disabled}
      whileHover={!disabled ? { y: -1 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      transition={{ duration: 0.18 }}
      style={style}
    >
      <Icon size={size} />
    </motion.button>
  )
}
