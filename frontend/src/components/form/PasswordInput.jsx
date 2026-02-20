import { useState } from 'react'
import { Eye, EyeOff, Lock } from 'lucide-react'
import { StyledInput } from './StyledInput'

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
      suffix={(
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setShow((value) => !value)}
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
      )}
    />
  )
}
