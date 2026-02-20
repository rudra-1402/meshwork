import { useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { ACCENT_RGB } from './formConstants'

export function StyledInput({
  id,
  type = 'text',
  icon: Icon,
  value,
  onChange,
  onBlur,
  placeholder,
  suffix,
  readOnly,
  error,
  autoFocus,
  loading,
}) {
  const [focused, setFocused] = useState(false)

  const filled = Boolean(value && String(value).length > 0)
  const pill = focused || filled

  const borderColor = error
    ? 'var(--color-error)'
    : focused
      ? `rgba(${ACCENT_RGB}, 0.55)`
      : 'var(--border-subtle)'

  const shadow = focused && !error
    ? `0 0 0 3px rgba(${ACCENT_RGB}, 0.10)`
    : 'none'

  return (
    <div style={{ position: 'relative' }}>
      {Icon ? (
        <Icon
          size={15}
          strokeWidth={2}
          style={{
            position: 'absolute',
            left: 14,
            top: '50%',
            transform: 'translateY(-50%)',
            color: focused ? `rgba(${ACCENT_RGB}, 0.85)` : 'var(--text-secondary)',
            transition: 'color 180ms ease',
            pointerEvents: 'none',
            zIndex: 1,
          }}
        />
      ) : null}

      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={(event) => {
          setFocused(false)
          if (onBlur) onBlur(event)
        }}
        placeholder={placeholder}
        readOnly={readOnly}
        autoFocus={autoFocus}
        aria-invalid={Boolean(error)}
        className="input"
        style={{
          padding: `11px ${suffix || loading ? '42px' : '14px'} 11px ${Icon ? '40px' : '14px'}`,
          lineHeight: '24px',
          color: readOnly ? 'var(--text-secondary)' : 'var(--text-primary)',
          borderColor,
          borderRadius: pill ? '999px' : '8px',
          opacity: readOnly ? 0.5 : 1,
          cursor: readOnly ? 'not-allowed' : 'text',
          boxShadow: shadow,
          transition: 'border-color 180ms ease, box-shadow 180ms ease, border-radius 300ms cubic-bezier(0.16,1,0.3,1)',
        }}
      />

      {loading || suffix ? (
        <div
          style={{
            position: 'absolute',
            right: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            display: 'flex',
            alignItems: 'center',
            zIndex: 1,
          }}
        >
          {loading ? (
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ duration: 0.85, repeat: Infinity, ease: 'linear' }}
              style={{ display: 'flex', color: `rgba(${ACCENT_RGB}, 0.6)` }}
            >
              <Loader2 size={14} strokeWidth={2} />
            </motion.span>
          ) : suffix}
        </div>
      ) : null}
    </div>
  )
}
