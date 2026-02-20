import { useEffect, useState } from 'react'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, Skeleton, Stat } from '../components/ui'
import { Grid, PageShell, Stack } from '../components/layout'
import { PERSONNEL_NAV_ITEMS } from '../utils/appNavigation'

function normalizePersonnel(payload) {
  const raw = payload?.data || payload || {}
  return {
    userCount: raw.user_count ?? raw.total_students ?? 0,
    collegeName: raw.college?.name || raw.college_name || 'College',
    students: raw.users || [],
  }
}

export default function PersonnelDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [view, setView] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadPersonnelDashboard() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.personnel.dashboard)
        const payload = ensureApiSuccess(response.data, 'Failed to load personnel dashboard')
        if (!mounted) return
        setView(normalizePersonnel(payload))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load personnel dashboard'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadPersonnelDashboard()
    return () => {
      mounted = false
    }
  }, [])

  return (
    <PageShell
      brand="MeshWork"
      brandTo="/personnel/dashboard"
      navItems={PERSONNEL_NAV_ITEMS}
      topItems={PERSONNEL_NAV_ITEMS}
    >
        {loading ? (
          <Stack gap={12}>
            <Skeleton height={72} />
            <Grid columns="repeat(2, minmax(0, 1fr))" gap={12}>
              <Skeleton height={110} />
              <Skeleton height={110} />
            </Grid>
          </Stack>
        ) : error ? (
          <Alert tone="error" message={error} />
        ) : !view ? (
          <EmptyState title="No personnel dashboard data" description="Try refreshing in a moment." />
        ) : (
          <Stack gap={14}>
            <section className="card">
              <h1 className="text-subsection">{view.collegeName} Dashboard</h1>
              <p className="text-small text-muted" style={{ marginTop: '4px' }}>
                Personnel overview and student management entry point.
              </p>
            </section>

            <Grid columns="repeat(2, minmax(0, 1fr))" gap={12}>
              <Stat label="Total Students" value={view.userCount} />
              <Stat label="Loaded Users" value={view.students.length} />
            </Grid>
          </Stack>
        )}
    </PageShell>
  )
}
