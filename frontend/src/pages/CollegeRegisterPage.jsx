import { useEffect, useMemo, useState } from 'react'
import { Building2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import {
  AuthPageShell,
  AuthLeftVisual,
  FloatingInput,
  FloatingPasswordInput,
  SubmitButton,
  SkeletonBlock,
  InlineErrorState,
  ToastMessage,
} from '../components/auth'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'

export default function CollegeRegisterPage({ token = '' }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [registrations, setRegistrations] = useState([])
  const [toast, setToast] = useState(null)

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirm_password: '',
    city: '',
    state: '',
  })

  const canSubmit = useMemo(() => {
    return (
      form.name.trim() &&
      form.email.trim() &&
      form.password.trim() &&
      form.confirm_password.trim() &&
      !submitting
    )
  }, [form, submitting])

  useEffect(() => {
    setLoading(false)
  }, [token])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(timer)
  }, [toast])

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const submitCollege = async () => {
    if (!canSubmit) return

    if (form.password !== form.confirm_password) {
      setToast({ type: 'error', message: 'Passwords do not match.' })
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const response = await api.post(API_ROUTES.collegeAuth.signup, {
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
          confirm_password: form.confirm_password,
          city: form.city.trim(),
          state: form.state.trim(),
      })
      const result = ensureApiSuccess(response.data, 'Registration failed')

      const newItem = {
        id: Date.now(),
        name: result.data?.college?.name || form.name.trim(),
        email: result.data?.college?.email || form.email.trim(),
        city: result.data?.college?.city || form.city.trim(),
        state: result.data?.college?.state || form.state.trim(),
      }

      setRegistrations((prev) => [newItem, ...prev])
      setForm({
        name: '',
        email: '',
        password: '',
        confirm_password: '',
        city: '',
        state: '',
      })
      setToast({ type: 'success', message: result.message || 'College registered successfully. You can now log in.' })
    } catch (err) {
      setToast({ type: 'error', message: getApiErrorMessage(err, 'Unexpected error during registration.') })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <style>{`@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }`}</style>
      <AuthPageShell title="Register Your College" icon={Building2} leftPane={<AuthLeftVisual mode="register" />}>
        {loading ? (
          <div className="card p-8 space-y-4">
            <SkeletonBlock height={24} />
            <SkeletonBlock height={20} />
            <SkeletonBlock height={48} />
            <SkeletonBlock height={48} />
            <SkeletonBlock height={48} />
            <SkeletonBlock height={48} />
          </div>
        ) : error ? (
          <InlineErrorState message={error} onRetry={() => navigate(0)} />
        ) : (
          <div className="space-y-5">
            <p className="text-body text-muted">
              Create a college account first. Personnel signup can be done after the college exists.
            </p>

            <div className="space-y-4">
              <FloatingInput
                id="college-name"
                label="College Name"
                value={form.name}
                onChange={(e) => updateField('name', e.target.value)}
                placeholder="MeshWork Institute"
              />
              <FloatingInput
                id="college-email"
                label="Official College Email"
                type="email"
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                placeholder="admin@college.edu"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FloatingPasswordInput
                  id="college-password"
                  label="Password"
                  value={form.password}
                  onChange={(e) => updateField('password', e.target.value)}
                />
                <FloatingPasswordInput
                  id="college-confirm-password"
                  label="Confirm Password"
                  value={form.confirm_password}
                  onChange={(e) => updateField('confirm_password', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FloatingInput
                  id="college-city"
                  label="City (Optional)"
                  value={form.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  placeholder="Chennai"
                />
                <FloatingInput
                  id="college-state"
                  label="State (Optional)"
                  value={form.state}
                  onChange={(e) => updateField('state', e.target.value)}
                  placeholder="Tamil Nadu"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <SubmitButton
                type="button"
                onClick={submitCollege}
                loading={submitting}
                disabled={!canSubmit}
                label="Register College"
                loadingLabel="Registering..."
                fullWidth={false}
              />
              <Link className="btn btn-secondary" to="/college/admin-login">Go to Admin Login</Link>
            </div>

            <div className="card p-6">
              <h2 className="text-body mb-3">Recent registrations</h2>
              {registrations.length === 0 ? (
                <p className="text-small text-muted">No registration attempts yet in this session.</p>
              ) : (
                <div className="space-y-3">
                  {registrations.map((item) => (
                    <div key={item.id} className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-surface-elevated)', border: '1px solid var(--border-subtle)' }}>
                      <p className="text-small" style={{ color: 'var(--text-primary)' }}>{item.name}</p>
                      <p className="text-small text-muted">{item.email}</p>
                      <p className="text-small text-muted">{[item.city, item.state].filter(Boolean).join(', ') || 'Location not provided'}</p>
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
