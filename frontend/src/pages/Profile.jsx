import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { RefreshCcw } from 'lucide-react'
import { API_ROUTES } from '../utils/apiRoutes'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { Alert, EmptyState, Skeleton } from '../components/ui'
import { Grid, PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function mapProfile(payload) {
  const raw = payload?.data || payload || {}
  const user = raw.user || raw.profile || {}
  const stats = raw.stats || {}

  return {
    name: user.username || user.name || [user.first_name, user.last_name].filter(Boolean).join(' ') || 'MeshWork User',
    email: user.email || 'Not available',
    createdAt: user.created_at,
    level: stats.level ?? raw.level ?? 1,
    xp: stats.xp ?? raw.total_xp ?? 0,
    streak: stats.streak ?? raw.current_streak ?? 0,
  }
}

function mapDashboard(payload) {
  const raw = payload?.data || payload || {}
  const stats = raw.stats || {}

  return {
    xp: stats.xp ?? raw.total_xp ?? 0,
    streak: stats.streak ?? raw.current_streak ?? 0,
    level: stats.level ?? raw.level ?? 1,
    projects: stats.projects ?? raw.project_count ?? 0,
  }
}

function mapScoring(payload) {
  const raw = payload?.data || payload || {}
  return {
    motivationScore: raw.motivation_score ?? 0,
    dominantRoles: raw.dominant_roles || [],
    allRoles: raw.all_roles || {},
    topInterests: raw.top_interests || [],
  }
}

export default function Profile() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState(null)
  const [dashboardStats, setDashboardStats] = useState(null)
  const [scoring, setScoring] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadProfileData() {
      try {
        setLoading(true)
        setError('')

        const profileRequest = api.get(API_ROUTES.profile.me)
        const dashboardRequest = (async () => {
          try {
            return await api.get(API_ROUTES.dashboard.home)
          } catch (err) {
            if (err?.response?.status === 404) {
              return api.get('/api/dashboard/dashboard')
            }
            throw err
          }
        })()
        const scoringRequest = api.get(API_ROUTES.scoring.profile)

        const [profileResult, dashboardResult, scoringResult] = await Promise.allSettled([
          profileRequest,
          dashboardRequest,
          scoringRequest,
        ])

        if (!mounted) return

        if (profileResult.status === 'rejected') {
          throw profileResult.reason
        }

        const profilePayload = ensureApiSuccess(profileResult.value.data, 'Failed to load profile')
        setProfile(mapProfile(profilePayload))

        if (dashboardResult.status === 'fulfilled') {
          const dashboardPayload = ensureApiSuccess(dashboardResult.value.data, 'Failed to load dashboard summary')
          setDashboardStats(mapDashboard(dashboardPayload))
        }

        if (scoringResult.status === 'fulfilled') {
          const scoringPayload = ensureApiSuccess(scoringResult.value.data, 'Failed to load scoring profile')
          setScoring(mapScoring(scoringPayload))
        } else if (scoringResult.reason?.response?.status !== 404) {
          throw scoringResult.reason
        }
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load profile'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadProfileData()

    return () => {
      mounted = false
    }
  }, [])

  const topRoles = useMemo(() => {
    if (!scoring) return []
    return scoring.dominantRoles.map((role) => ({
      label: role,
      score: scoring.allRoles?.[role]?.score,
    }))
  }, [scoring])

  const profileInitial = profile?.name?.charAt(0)?.toUpperCase() || 'M'

  return (
    <PageShell
      brand="MeshWork"
      brandTo="/home"
      navItems={STUDENT_NAV_ITEMS}
      topItems={STUDENT_TOP_ITEMS}
    >
      {loading ? (
        <Stack gap={12}>
          <Skeleton height={180} />
          <Skeleton height={110} />
          <Skeleton height={110} />
        </Stack>
      ) : error ? (
        <Alert tone="error" message={error} />
      ) : !profile ? (
        <EmptyState title="No profile data" description="Profile details are not available yet." />
      ) : (
        <Stack gap={14}>
          <section className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '20px', flexWrap: 'wrap' }}>
              <div
                style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '999px',
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: '40px',
                  fontWeight: 700,
                  color: 'white',
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-hover))',
                }}
              >
                {profileInitial}
              </div>
              <div style={{ flex: 1, minWidth: '260px' }}>
                <h1 className="text-subsection">{profile.name}</h1>
                <p className="text-small text-muted" style={{ marginTop: '4px' }}>{profile.email}</p>
                <p className="text-small text-muted" style={{ marginTop: '6px' }}>
                  Dashboard has been merged into profile as requested.
                </p>
              </div>
            </div>
          </section>

          <Grid columns="repeat(4, minmax(0, 1fr))" gap={12}>
            <section className="card"><p className="text-small text-muted">Level</p><h3 className="text-subsection">{dashboardStats?.level ?? profile.level}</h3></section>
            <section className="card"><p className="text-small text-muted">XP</p><h3 className="text-subsection">{dashboardStats?.xp ?? profile.xp}</h3></section>
            <section className="card"><p className="text-small text-muted">Streak</p><h3 className="text-subsection">{dashboardStats?.streak ?? profile.streak} days</h3></section>
            <section className="card"><p className="text-small text-muted">Projects</p><h3 className="text-subsection">{dashboardStats?.projects ?? 0}</h3></section>
          </Grid>

          {scoring ? (
            <Grid columns="minmax(0, 1fr) minmax(0, 1fr)" gap={12}>
              <section className="card" style={{ display: 'grid', gap: '10px' }}>
                <h3 className="text-body" style={{ fontWeight: 600 }}>Overall Motivation Score</h3>
                <h2 className="text-subsection">{Number(scoring.motivationScore || 0).toFixed(1)} / 10.0</h2>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${Math.max(0, Math.min(100, (Number(scoring.motivationScore || 0) / 10) * 100))}%` }} />
                </div>
              </section>

              <section className="card" style={{ display: 'grid', gap: '10px' }}>
                <h3 className="text-body" style={{ fontWeight: 600 }}>Dominant Roles</h3>
                {topRoles.length === 0 ? (
                  <p className="text-small text-muted">No role breakdown available.</p>
                ) : topRoles.map((roleItem) => (
                  <div key={roleItem.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="text-small">{roleItem.label}</span>
                    <strong>{roleItem.score != null ? Number(roleItem.score).toFixed(1) : '--'}</strong>
                  </div>
                ))}
              </section>
            </Grid>
          ) : (
            <section className="card" style={{ display: 'grid', gap: '10px' }}>
              <h3 className="text-body" style={{ fontWeight: 600 }}>Questionnaire Not Yet Completed</h3>
              <p className="text-small text-muted">Complete your questionnaire to unlock role and interest insights.</p>
              <div>
                <Link className="btn btn-primary" to="/questionnaire">Start Questionnaire</Link>
              </div>
            </section>
          )}

          <section className="card" style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
            <div>
              <h3 className="text-body" style={{ fontWeight: 600 }}>Need to retake?</h3>
              <p className="text-small text-muted">You can retake the questionnaire to refresh recommendations.</p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={async () => {
                try {
                  await api.post(API_ROUTES.scoring.retake)
                  navigate('/questionnaire')
                } catch (err) {
                  setError(getApiErrorMessage(err, 'Failed to reset questionnaire'))
                }
              }}
            >
              <RefreshCcw size={16} /> Retake Questionnaire
            </button>
          </section>
        </Stack>
      )}
    </PageShell>
  )
}
