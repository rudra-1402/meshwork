import { useEffect, useMemo, useState } from 'react'
import { Building2, Shield } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import {
  AuthPageShell,
  AuthLeftVisual,
  Field,
  StyledInput,
  PasswordInput,
  SubmitButton,
  SkeletonBlock,
  InlineErrorState,
  ToastMessage,
} from '../components/auth'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'

export default function AdminLoginPage({ token = '' }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)
  const [recentAdmins, setRecentAdmins] = useState([])

  const [credentials, setCredentials] = useState({
    email: '',
    password: '',
  })

  const canSubmit = useMemo(() => {
    return Boolean(credentials.email.trim() && credentials.password && !submitting)
  }, [credentials, submitting])

  useEffect(() => {
    setLoading(false)
  }, [token])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(timer)
  }, [toast])

  const updateField = (field, value) => {
    setCredentials((prev) => ({ ...prev, [field]: value }))
  }

  const submitLogin = async () => {
    if (submitting) return

    const email = credentials.email.trim()
    const password = credentials.password

    if (!email || !password) {
      setToast({ type: 'error', message: 'Email and password are required.' })
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const response = await api.post(API_ROUTES.collegeAuth.login, { email, password })
      const result = ensureApiSuccess(response.data, 'Admin login failed')

      setRecentAdmins((prev) => [
        {
          id: Date.now(),
          email,
          at: new Date().toLocaleTimeString(),
        },
        ...prev,
      ])

      setToast({ type: 'success', message: result.message || 'Admin logged in successfully.' })
      navigate(result.data?.dashboard_route || '/dashboard')
    } catch (err) {
      setToast({ type: 'error', message: getApiErrorMessage(err, 'Unexpected error during login.') })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <style>{`@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }`}</style>
      <AuthPageShell title="Admin Login" icon={Shield} leftPane={<AuthLeftVisual mode="login" />}>
        {loading ? (
          <div className="card p-8 space-y-4">
            <SkeletonBlock height={24} />
            <SkeletonBlock height={20} />
            <SkeletonBlock height={48} />
            <SkeletonBlock height={48} />
          </div>
        ) : error ? (
          <InlineErrorState message={error} onRetry={() => navigate(0)} />
        ) : (
          <div className="space-y-5">
            <p className="text-body text-muted">
              Sign in as college administrator to access the college dashboard.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Admin Email" htmlFor="admin-email">
                <StyledInput
                  id="admin-email"
                  type="email"
                  value={credentials.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  placeholder="admin@college.edu"
                />
              </Field>
              <Field label="Password" htmlFor="admin-password">
                <PasswordInput
                  id="admin-password"
                  value={credentials.password}
                  onChange={(e) => updateField('password', e.target.value)}
                />
              </Field>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <SubmitButton
                type="button"
                onClick={submitLogin}
                loading={submitting}
                disabled={!canSubmit}
                label="Admin Login"
                loadingLabel="Signing in..."
                fullWidth={false}
              />

              <Link className="btn btn-secondary" to="/college/register">
                Register College
              </Link>
            </div>

            <div className="card p-6">
              <div className="flex items-center gap-2 mb-3">
                <Building2 size={16} style={{ color: 'var(--text-secondary)' }} />
                <h2 className="text-body">Recent admin sessions</h2>
              </div>

              {recentAdmins.length === 0 ? (
                <p className="text-small text-muted">No admin session in this browser session yet.</p>
              ) : (
                <div className="space-y-3">
                  {recentAdmins.map((item) => (
                    <div key={item.id} className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-surface-elevated)', border: '1px solid var(--border-subtle)' }}>
                      <p className="text-small" style={{ color: 'var(--text-primary)' }}>{item.email}</p>
                      <p className="text-small text-muted">{item.at}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </AuthPageShell>

      <ToastMessage toast={toast} />
    </>
  )
}
