import { motion } from 'framer-motion'

const VARIANT_CLASS_MAP = {
  primary: 'btn btn-primary',
  secondary: 'btn btn-secondary',
  ghost: 'btn btn-ghost',
  danger: 'btn btn-secondary',
}

export function Button({
  children,
  variant = 'primary',
  type = 'button',
  onClick,
  disabled = false,
  fullWidth = false,
  ariaLabel,
  style,
}) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={VARIANT_CLASS_MAP[variant] || VARIANT_CLASS_MAP.primary}
      whileHover={!disabled ? { y: -1 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      transition={{ duration: 0.18 }}
      style={{
        width: fullWidth ? '100%' : undefined,
        ...(variant === 'danger'
          ? { borderColor: 'var(--color-error)', color: 'var(--color-error)' }
          : {}),
        ...style,
      }}
    >
      {children}
    </motion.button>
  )
}
