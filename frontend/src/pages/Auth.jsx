/**
 * MESHWORK — Auth Page v2
 *
 * Architecture:
 * - Split layout: left image panel (50%) + right form panel (50%)
 * - Two modes: 'login' | 'signup' — toggled via inline link
 * - Title: overflow-clip mask wipe, y ±100% (AnimatePresence mode="wait")
 * - Signup extra fields: staggered slide-down from Email/Password, AnimatePresence + motion layout
 * - Email: on-blur background validation → college chip + registered hint
 * - Images crossfade between modes (login ↔ signup)
 * - Confirm password: frontend-only (API receives single password field)
 * - Buttons: motion.button pill-morph via MORPH_TRANSITION + morphHover from MorphButton
 * - Tokens: CSS semantic vars only. Zero dark: prefix. Zero raw hex in components.
 */

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import {
  Field,
  StyledInput,
  PasswordInput,
  SubmitButton,
  ModeToggleLink,
  EmailMetaCard,
} from '../components/auth'
import { MultiPaneLayout, PaneSurface } from '../components/layout'

/* ─────────────────────────────────────────────
   CONSTANTS
───────────────────────────────────────────── */
const EASE       = [0.25, 0.1, 0.25, 1]

/* ─────────────────────────────────────────────
   EXTRA FIELD VARIANTS (stagger entrance)
───────────────────────────────────────────── */
const extraContainerVariants = {
  hidden:  { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.055, delayChildren: 0.02 },
  },
  exit: {
    opacity: 0,
    transition: { staggerChildren: 0.03, staggerDirection: -1 },
  },
}

const extraFieldVariants = {
  hidden:  { opacity: 0, y: -14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.26, ease: EASE } },
  exit:    { opacity: 0, y: -10, transition: { duration: 0.18, ease: EASE } },
}

/* ═════════════════════════════════════════════
   ROOT COMPONENT
═════════════════════════════════════════════ */
export default function Auth() {
  const [mode, setMode]               = useState('login')    // 'login' | 'signup'
  const [email, setEmail]             = useState('')
  const [password, setPassword]       = useState('')
  const [confirmPassword, setConfirm] = useState('')
  const [firstName, setFirstName]     = useState('')
  const [lastName, setLastName]       = useState('')
  const [username, setUsername]       = useState('')
  const [role, setRole]               = useState('')

  const [emailMeta, setEmailMeta]   = useState(null)   // {college_name, user_type, college_id, …}
  const [emailChecking, setChecking] = useState(false)
  const [submitting, setSubmitting]  = useState(false)
  const [errors, setErrors]          = useState({})     // field-level
  const [globalError, setGlobal]     = useState('')

  const { validateEmail, login, signup } = useAuth()
  const navigate = useNavigate()

  /* ─── Switch mode ─── */
  const switchMode = useCallback((next) => {
    setMode(next)
    setErrors({})
    setGlobal('')
    setPassword('')
    setConfirm('')
  }, [])

  /* ─── Email on-blur: background validation ─── */
  const handleEmailBlur = useCallback(async () => {
    if (!email) return
    setChecking(true)
    const result = await validateEmail(email)
    setChecking(false)

    if (result.is_registered) {
      setEmailMeta({ ...result, is_registered: true })
      if (mode === 'signup') {
        setErrors(prev => ({ ...prev, email: 'This email already has an account — try Log In.' }))
      } else {
        setErrors(prev => { const n = { ...prev }; delete n.email; return n })
      }
    } else if (result.valid) {
      setEmailMeta(result)
      setErrors(prev => { const n = { ...prev }; delete n.email; return n })
    } else {
      setEmailMeta(null)
      setErrors(prev => ({ ...prev, email: result.error || 'Use your institutional email.' }))
    }
  }, [email, mode, validateEmail])

  /* ─── Client-side validate ─── */
  const validateForm = () => {
    const e = {}
    if (!email)    e.email    = 'Email is required.'
    if (!password) e.password = 'Password is required.'
    if (mode === 'signup') {
      if (!firstName) e.firstName = 'Required.'
      if (!lastName)  e.lastName  = 'Required.'
      if (isPersonnel) {
        if (!role)     e.role     = 'Role is required.'
      } else {
        if (!username) e.username = 'Username is required.'
      }
      if (!confirmPassword) {
        e.confirmPassword = 'Please confirm your password.'
      } else if (password !== confirmPassword) {
        e.confirmPassword = 'Passwords do not match.'
      }
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  /* ─── Submit ─── */
  const handleSubmit = async () => {
    setGlobal('')
    if (!validateForm()) return

    setSubmitting(true)
    if (mode === 'login') {
      const result = await login(email, password)
      setSubmitting(false)
      if (result.success) {
        navigate(result.dashboard_route)
      } else {
        setGlobal(result.error || 'Login failed. Check your credentials.')
      }
    } else {
      const result = await signup({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        user_type:  emailMeta?.user_type  || 'student',
        college_id: emailMeta?.college_id || null,
        ...(isPersonnel ? { role } : { username }),
      })
      setSubmitting(false)
      if (result.success) {
        navigate(result.dashboard_route)
      } else {
        setGlobal(result.error || 'Signup failed. Please try again.')
      }
    }
  }

  const isPersonnel = emailMeta?.user_type === 'personnel'

  /* ═══════════════════════════════════════
     RENDER
  ═══════════════════════════════════════ */

  const leftPane = (
    <div
      style={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: '28px',
        flex: 1,
        backgroundColor: '#080b0d',
      }}
    >
      <AnimatePresence initial={false}>
        <motion.img
          key={mode}
          src={mode === 'login' ? '/auth-login.png' : '/auth-signup.png'}
          alt=""
          initial={{ opacity: 0, scale: 1.04 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.97 }}
          transition={{ duration: 0.85, ease: EASE }}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 30%',
          }}
        />
      </AnimatePresence>

      <motion.div
        animate={{ y: [0, -9, 0], scale: [1, 1.012, 1] }}
        transition={{ duration: 7.5, repeat: Infinity, ease: 'easeInOut' }}
        style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
      />

      <Link
        to="/"
        aria-label="MeshWork — back to home"
        style={{
          position: 'absolute', top: '32px', left: '40px', zIndex: 10,
          fontFamily: 'Clash Display, sans-serif',
          fontSize: '22px', fontWeight: '600', letterSpacing: '-0.02em',
          color: '#E6EDF3', textDecoration: 'none',
        }}
      >
        MeshWork
      </Link>

      <p style={{
        position: 'absolute', bottom: '32px', left: '40px', zIndex: 10,
        margin: 0,
        fontFamily: 'Satoshi, sans-serif', fontSize: '12px',
        letterSpacing: '0.18em', textTransform: 'uppercase',
        color: 'rgba(230,237,243,0.35)',
      }}>
        Engineered, not designed.
      </p>
    </div>
  )

  const rightPane = (
    <PaneSurface
      maxWidth="760px"
      padding="clamp(28px, 4vw, 56px)"
      border="1px solid var(--border-subtle)"
    >
      <div id="auth-form" style={{ width: '100%', maxWidth: '500px' }}>
        {/* ── Title — mask-wipe upward ── */}
        <div style={{ overflow: 'hidden', marginBottom: '8px' }}>
          <AnimatePresence mode="wait" initial={false}>
          <motion.h1
            key={mode}
            initial={{ y: '105%' }}
            animate={{ y: '0%' }}
            exit={{ y: '-105%' }}
            transition={{ duration: 0.32, ease: EASE }}
            style={{
              fontFamily: 'Clash Display, sans-serif',
              fontSize: '72px', lineHeight: '1.05', fontWeight: '700',
              letterSpacing: '-0.03em',
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            {mode === 'login' ? 'Login.' : 'Sign up.'}
          </motion.h1>
        </AnimatePresence>
      </div>

      {/* ── Subtitle ── */}
      <AnimatePresence mode="wait" initial={false}>
        <motion.p
          key={mode + '-sub'}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22, ease: EASE }}
          style={{
            fontFamily: 'Satoshi, sans-serif',
            fontSize: '15px', lineHeight: '24px',
            color: 'var(--text-secondary)',
            margin: '0 0 32px',
          }}
        >
          {mode === 'login'
            ? 'Sign in to continue to MeshWork.'
            : 'Use your institutional email to join.'}
        </motion.p>
      </AnimatePresence>

      {/* ── Global error banner ── */}
      <AnimatePresence initial={false}>
        {globalError && (
          <motion.p
            key="global-err"
            role="alert"
            aria-live="polite"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: EASE }}
            style={{
              overflow: 'hidden',
              fontFamily: 'Satoshi, sans-serif',
              fontSize: '13px',
              color: 'var(--color-error)',
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid rgba(239,68,68,0.18)',
              backgroundColor: 'rgba(239,68,68,0.06)',
              marginBottom: '16px',
            }}
          >
            {globalError}
          </motion.p>
        )}
      </AnimatePresence>

      {/* ── Form ── */}
      <motion.div
        layout
        style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
      >
        {/* EMAIL */}
        <Field label="Institutional Email" htmlFor="email" error={errors.email}>
          <StyledInput
            id="email"
            type="email"
            icon={Mail}
            value={email}
            onChange={e => { setEmail(e.target.value); setEmailMeta(null) }}
            onBlur={handleEmailBlur}
            placeholder="you@college.edu"
            error={errors.email}
            loading={emailChecking}
            autoFocus
          />
          {/* Email meta card — college + role beneath email */}
          <AnimatePresence initial={false}>
            {emailMeta && (emailMeta.college_name || emailMeta.user_type) && (
              <EmailMetaCard meta={emailMeta} />
            )}
          </AnimatePresence>
        </Field>

        {/* SIGNUP-ONLY EXTRA FIELDS — slide in staggered */}
        <AnimatePresence initial={false}>
          {mode === 'signup' && (
            <motion.div
              key="extra-fields"
              variants={extraContainerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
            >
              {/* First + Last name row */}
              <motion.div
                variants={extraFieldVariants}
                style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}
              >
                <Field label="First Name" htmlFor="firstName" error={errors.firstName}>
                  <StyledInput
                    id="firstName"
                    value={firstName}
                    onChange={e => setFirstName(e.target.value)}
                    placeholder="Jane"
                    error={errors.firstName}
                  />
                </Field>
                <Field label="Last Name" htmlFor="lastName" error={errors.lastName}>
                  <StyledInput
                    id="lastName"
                    value={lastName}
                    onChange={e => setLastName(e.target.value)}
                    placeholder="Doe"
                    error={errors.lastName}
                  />
                </Field>
              </motion.div>

              {/* Username (student) or Role (personnel) */}
              <motion.div variants={extraFieldVariants}>
                {isPersonnel ? (
                  <Field label="Role" htmlFor="role" error={errors.role}>
                    <StyledInput
                      id="role"
                      value={role}
                      onChange={e => setRole(e.target.value)}
                      placeholder="e.g. Professor, Advisor"
                      error={errors.role}
                    />
                  </Field>
                ) : (
                  <Field label="Username" htmlFor="username" error={errors.username}>
                    <StyledInput
                      id="username"
                      icon={User}
                      value={username}
                      onChange={e => setUsername(e.target.value)}
                      placeholder="janedoe"
                      error={errors.username}
                    />
                  </Field>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* PASSWORD */}
        <Field label="Password" htmlFor="password" error={errors.password}>
          <PasswordInput
            id="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            error={errors.password}
          />
        </Field>

        {/* CONFIRM PASSWORD — signup only */}
        <AnimatePresence initial={false}>
          {mode === 'signup' && (
            <motion.div
              key="confirm-pw"
              variants={extraFieldVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Field label="Confirm Password" htmlFor="confirmPassword" error={errors.confirmPassword}>
                <PasswordInput
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={e => setConfirm(e.target.value)}
                  placeholder="••••••••"
                  error={errors.confirmPassword}
                />
              </Field>
            </motion.div>
          )}
        </AnimatePresence>

        {/* SUBMIT */}
        <motion.div layout style={{ marginTop: '8px' }}>
          <SubmitButton
            type="button"
            onClick={handleSubmit}
            loading={submitting}
            label={mode === 'login' ? 'LOGIN' : 'Sign up'}
          />
        </motion.div>
      </motion.div>

      {/* ── Mode toggle ── */}
      <motion.p
        layout
        style={{
          marginTop: '24px',
          textAlign: 'center',
          fontFamily: 'Satoshi, sans-serif',
          fontSize: '16px',
          color: 'var(--text-secondary)',
        }}
      >
        {mode === 'login' ? (
          <>
            Don&apos;t have an account?{' '}
            <ModeToggleLink onClick={() => switchMode('signup')}>Sign Up</ModeToggleLink>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <ModeToggleLink onClick={() => switchMode('login')}>Log In</ModeToggleLink>
          </>
        )}
      </motion.p>

      {/* ── Back to home ── */}
      <motion.div layout style={{ marginTop: '40px', textAlign: 'center' }}>
        <Link
          to="/"
          style={{
            fontFamily: 'Satoshi, sans-serif',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            opacity: 0.5,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            transition: 'opacity 180ms ease',
          }}
        >
          ← Back to MeshWork
        </Link>
      </motion.div>
      </div>
    </PaneSurface>
  )

  return (
    <MultiPaneLayout
      panes={[
        {
          key: 'auth-left',
          ariaHidden: true,
          flex: '0 0 55%',
          padding: '28px 16px 28px 28px',
          content: leftPane,
        },
        {
          key: 'auth-right',
          flex: '0 0 45%',
          minWidth: 0,
          padding: '28px 28px 28px 16px',
          content: rightPane,
        },
      ]}
    >
      <a href="#auth-form" className="skip-to-content">Skip to sign-in form</a>
    </MultiPaneLayout>
  )
}