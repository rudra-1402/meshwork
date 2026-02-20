import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Lock, Eye, EyeOff,
  Building2, GraduationCap, Briefcase, Loader2,
} from 'lucide-react'
import { MORPH_TRANSITION, morphHover } from '../MorphButton'

const ACCENT_RGB = '16, 185, 129'
const EASE = [0.25, 0.1, 0.25, 1]

export function Field({ label, htmlFor, error, children }) {
  return (
    <motion.div layout style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label && (
        <label
          htmlFor={htmlFor}
          style={{
            fontFamily: 'Satoshi, sans-serif',
            fontSize: '13px',
            fontWeight: '500',
            color: 'var(--text-secondary)',
            letterSpacing: '0.02em',
          }}
        >
          {label}
        </label>
      )}
      {children}
      <AnimatePresence initial={false}>
        {error && (
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
        )}
      </AnimatePresence>
    </motion.div>
  )
}

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

  const filled = Boolean(value && value.length > 0)
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
      {Icon && (
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
      )}

      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={(e) => {
          setFocused(false)
          if (onBlur) onBlur(e)
        }}
        placeholder={placeholder}
        readOnly={readOnly}
        autoFocus={autoFocus}
        aria-invalid={!!error}
        style={{
          display: 'block',
          width: '100%',
          padding: `11px ${suffix || loading ? '42px' : '14px'} 11px ${Icon ? '40px' : '14px'}`,
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '15px',
          lineHeight: '24px',
          color: readOnly ? 'var(--text-secondary)' : 'var(--text-primary)',
          backgroundColor: 'var(--bg-surface-elevated)',
          border: `1px solid ${borderColor}`,
          borderRadius: pill ? '999px' : '8px',
          outline: 'none',
          opacity: readOnly ? 0.5 : 1,
          cursor: readOnly ? 'not-allowed' : 'text',
          boxShadow: shadow,
          transition: 'border-color 180ms ease, box-shadow 180ms ease, border-radius 300ms cubic-bezier(0.16,1,0.3,1)',
        }}
      />

      {(loading || suffix) && (
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
      )}
    </div>
  )
}

export function PasswordInput({ id, value, onChange, error, placeholder, autoFocus }) {
  const [show, setShow] = useState(false)

  return (
    <StyledInput
      id={id}
      type={show ? 'text' : 'password'}
      icon={Lock}
      value={value}
      onChange={onChange}
      placeholder={placeholder || '••••••••'}
      error={error}
      autoFocus={autoFocus}
      suffix={
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setShow((s) => !s)}
          aria-label={show ? 'Hide password' : 'Show password'}
          style={{
            display: 'flex',
            alignItems: 'center',
            color: 'var(--text-secondary)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          {show ? <EyeOff size={15} strokeWidth={2} /> : <Eye size={15} strokeWidth={2} />}
        </button>
      }
    />
  )
}

export function FloatingInput({
  id,
  label,
  type = 'text',
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
  const filled = Boolean(value && value.length > 0)
  const floating = focused || filled

  const borderColor = error
    ? 'var(--color-error)'
    : focused
      ? `rgba(${ACCENT_RGB}, 0.55)`
      : 'var(--border-subtle)'

  const shadow = focused && !error
    ? `0 0 0 3px rgba(${ACCENT_RGB}, 0.10)`
    : 'none'

  return (
    <motion.div layout style={{ position: 'relative', paddingTop: '16px' }}>
      <motion.label
        htmlFor={id}
        initial={false}
        animate={{
          top: floating ? 0 : 'calc(50% + 8px)',
          y: floating ? 0 : '-50%',
          left: 14,
          fontSize: floating ? '13px' : '15px',
          color: floating
            ? (error ? 'var(--color-error)' : 'var(--text-secondary)')
            : 'var(--text-secondary)',
          opacity: readOnly ? 0.6 : 1,
        }}
        transition={{ duration: 0.2, ease: EASE }}
        style={{
          position: 'absolute',
          zIndex: 2,
          pointerEvents: 'none',
          fontFamily: 'Satoshi, sans-serif',
          fontWeight: floating ? '500' : '400',
          letterSpacing: floating ? '0.02em' : '0.01em',
        }}
      >
        {label}
      </motion.label>

      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={(e) => {
          setFocused(false)
          if (onBlur) onBlur(e)
        }}
        placeholder={focused ? placeholder : ''}
        readOnly={readOnly}
        autoFocus={autoFocus}
        aria-invalid={!!error}
        style={{
          display: 'block',
          width: '100%',
          minHeight: '56px',
          padding: `22px ${suffix || loading ? '42px' : '14px'} 10px 14px`,
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '15px',
          lineHeight: '24px',
          color: readOnly ? 'var(--text-secondary)' : 'var(--text-primary)',
          backgroundColor: 'var(--bg-surface-elevated)',
          border: `1px solid ${borderColor}`,
          borderRadius: '12px',
          outline: 'none',
          opacity: readOnly ? 0.5 : 1,
          cursor: readOnly ? 'not-allowed' : 'text',
          boxShadow: shadow,
          transition: 'border-color 180ms ease, box-shadow 180ms ease',
        }}
      />

      {(loading || suffix) && (
        <div
          style={{
            position: 'absolute',
            right: 12,
            top: '50%',
            transform: 'translateY(0%)',
            display: 'flex',
            alignItems: 'center',
            zIndex: 2,
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
      )}

      <AnimatePresence initial={false}>
        {error && (
          <motion.span
            key="floating-field-error"
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
              marginTop: '6px',
            }}
          >
            {error}
          </motion.span>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export function FloatingPasswordInput({ id, label, value, onChange, error, placeholder, autoFocus }) {
  const [show, setShow] = useState(false)

  return (
    <FloatingInput
      id={id}
      label={label}
      type={show ? 'text' : 'password'}
      value={value}
      onChange={onChange}
      placeholder={placeholder || '••••••••'}
      error={error}
      autoFocus={autoFocus}
      suffix={
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setShow((s) => !s)}
          aria-label={show ? 'Hide password' : 'Show password'}
          style={{
            display: 'flex',
            alignItems: 'center',
            color: 'var(--text-secondary)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          {show ? <EyeOff size={15} strokeWidth={2} /> : <Eye size={15} strokeWidth={2} />}
        </button>
      }
    />
  )
}

export function SubmitButton({
  loading,
  disabled = false,
  label,
  loadingLabel = 'Processing…',
  type = 'submit',
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
      style={{
        width: fullWidth ? '100%' : 'auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        gap: '8px',
        padding: '13px 24px',
        fontFamily: 'Satoshi, sans-serif',
        fontSize: '15px',
        fontWeight: '600',
        letterSpacing: '0.01em',
        color: '#0E1113',
        backgroundColor: `rgba(${ACCENT_RGB}, ${isDisabled ? 0.55 : 1})`,
        border: '1px solid transparent',
        borderRadius: 12,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        boxShadow: `0 4px 12px rgba(${ACCENT_RGB}, 0.20)`,
        outline: 'none',
        position: 'relative',
      }}
      whileHover={!isDisabled ? morphHover({
        backgroundColor: `rgba(${ACCENT_RGB}, 0.84)`,
        boxShadow: `0 8px 24px rgba(${ACCENT_RGB}, 0.36)`,
      }) : {}}
      whileTap={!isDisabled ? { scale: 0.97, y: -1 } : {}}
      transition={MORPH_TRANSITION}
      aria-label={loading ? 'Processing, please wait' : undefined}
    >
      {loading ? (
        <>
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
            style={{ display: 'flex' }}
          >
            <Loader2 size={16} strokeWidth={2} />
          </motion.span>
          {loadingLabel}
        </>
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
            animate={{ x: hovered ? 0 : 8, opacity: hovered ? 1 : 0 }}
            transition={{ duration: 0.22, ease: EASE }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              fontSize: '15px',
              fontWeight: '700',
              lineHeight: 1,
            }}
          >
            {'→'}
          </motion.span>
        </span>
      )}
    </motion.button>
  )
}

export function ModeToggleLink({ onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        fontFamily: 'Satoshi, sans-serif',
        fontSize: 'inherit',
        fontWeight: '600',
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

const USER_TYPE_CONFIG = {
  student: {
    label: 'Student',
    Icon: GraduationCap,
    color: `rgba(${ACCENT_RGB}, 1)`,
    bg: `rgba(${ACCENT_RGB}, 0.10)`,
    border: `rgba(${ACCENT_RGB}, 0.20)`,
  },
  personnel: {
    label: 'Personnel',
    Icon: Briefcase,
    color: 'rgba(234, 179, 8, 1)',
    bg: 'rgba(234, 179, 8, 0.10)',
    border: 'rgba(234, 179, 8, 0.22)',
  },
}

export function EmailMetaCard({ meta }) {
  const typeConfig = USER_TYPE_CONFIG[meta.user_type] ?? USER_TYPE_CONFIG.student
  const { Icon: TypeIcon } = typeConfig

  return (
    <motion.div
      key="email-meta-card"
      initial={{ opacity: 0, y: -6, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -4, scale: 0.98 }}
      transition={{ duration: 0.26, ease: EASE }}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        padding: '7px 14px',
        borderRadius: '999px',
        backgroundColor: 'var(--bg-surface-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
        <Building2
          size={14}
          strokeWidth={2}
          style={{ flexShrink: 0, color: 'var(--text-secondary)' }}
        />
        <span
          style={{
            fontFamily: 'Satoshi, sans-serif',
            fontSize: '13px',
            fontWeight: '500',
            color: 'var(--text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {meta.college_name}
        </span>
      </div>

      <span
        style={{
          flexShrink: 0,
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          padding: '3px 10px',
          borderRadius: '999px',
          backgroundColor: typeConfig.bg,
          border: `1px solid ${typeConfig.border}`,
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '12px',
          fontWeight: '600',
          color: typeConfig.color,
          letterSpacing: '0.01em',
        }}
      >
        <TypeIcon size={11} strokeWidth={2.5} />
        {typeConfig.label}
      </span>
    </motion.div>
  )
}
