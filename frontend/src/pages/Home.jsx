import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Flame, Megaphone, TrendingUp } from 'lucide-react'
import api, { getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, Skeleton } from '../components/ui'
import { Grid, PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function mapProjects(payload) {
  const raw = payload?.data || payload || {}
  return (raw.projects || raw.items || []).slice(0, 6).map((item, index) => ({
    id: item.id || item.project_id || `project-${index + 1}`,
    title: item.title || item.name || `Project ${index + 1}`,
    body: item.description || 'No description available.',
    link: `/projects/${item.id || item.project_id || ''}`,
  }))
}

function mapEvents(payload) {
  const raw = payload?.data || payload || {}
  return (raw.events || raw.items || []).slice(0, 4).map((item, index) => ({
    id: item.id || item.event_id || `event-${index + 1}`,
    title: item.title || item.name || `Event ${index + 1}`,
    body: item.description || 'No description available.',
    link: `/events/${item.id || item.event_id || ''}`,
  }))
}

function mapCommunities(payload) {
  const raw = payload?.data || payload || {}
  return (raw.communities || raw.items || []).slice(0, 4).map((item, index) => ({
    id: item.id || item.community_id || `community-${index + 1}`,
    title: item.name || `Community ${index + 1}`,
    body: item.description || 'No description available.',
    link: `/communities/${item.id || item.community_id || ''}`,
  }))
}

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [projects, setProjects] = useState([])
  const [events, setEvents] = useState([])
  const [communities, setCommunities] = useState([])

  useEffect(() => {
    let mounted = true

    async function loadHome() {
      try {
        setLoading(true)
        setError('')

        const [projectsResult, eventsResult, communitiesResult] = await Promise.allSettled([
          api.get(API_ROUTES.projects.list),
          api.get(API_ROUTES.events.list),
          api.get(API_ROUTES.communities.explore),
        ])

        if (!mounted) return

        if (projectsResult.status === 'fulfilled') {
          setProjects(mapProjects(projectsResult.value.data))
        }

        if (eventsResult.status === 'fulfilled') {
          setEvents(mapEvents(eventsResult.value.data))
        }

        if (communitiesResult.status === 'fulfilled') {
          setCommunities(mapCommunities(communitiesResult.value.data))
        }

        if (
          projectsResult.status === 'rejected' &&
          eventsResult.status === 'rejected' &&
          communitiesResult.status === 'rejected'
        ) {
          throw projectsResult.reason
        }
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load home feed'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadHome()

    return () => {
      mounted = false
    }
  }, [])

  return (
    <PageShell
      brand="MeshWork"
      brandTo="/home"
      navItems={STUDENT_NAV_ITEMS}
      topItems={STUDENT_TOP_ITEMS}
    >
      {loading ? (
        <Stack gap={12}>
          <Skeleton height={76} />
          <Skeleton height={110} />
          <Skeleton height={110} />
        </Stack>
      ) : error ? (
        <Alert tone="error" message={error} />
      ) : (
        <Grid columns="minmax(0, 2fr) minmax(320px, 1fr)" gap={14}>
          <Stack gap={12}>
            <section className="card">
              <h1 className="text-subsection" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Flame size={18} color="var(--accent-primary)" /> Home Feed
              </h1>
              <p className="text-small text-muted" style={{ marginTop: '4px' }}>
                Reddit-style stream of active projects and community updates.
              </p>
            </section>

            {projects.length === 0 ? <EmptyState title="No projects yet" /> : projects.map((item) => (
              <section key={item.id} className="card" style={{ display: 'grid', gap: '10px' }}>
                <h3 className="text-body" style={{ fontWeight: 600 }}>{item.title}</h3>
                <p className="text-small text-muted">{item.body}</p>
                <div>
                  <Link className="btn btn-secondary" to={item.link}>Open Thread</Link>
                </div>
              </section>
            ))}
          </Stack>

          <Stack gap={12}>
            <section className="card" style={{ display: 'grid', gap: '8px' }}>
              <h3 className="text-body" style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={16} color="var(--accent-primary)" /> Trending Events
              </h3>
              {events.length === 0 ? <p className="text-small text-muted">No active events.</p> : events.map((eventItem) => (
                <Link key={eventItem.id} to={eventItem.link} className="btn btn-secondary" style={{ textAlign: 'left' }}>
                  {eventItem.title}
                </Link>
              ))}
            </section>

            <section className="card" style={{ display: 'grid', gap: '8px' }}>
              <h3 className="text-body" style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Megaphone size={16} color="var(--accent-primary)" /> Community Highlights
              </h3>
              {communities.length === 0 ? <p className="text-small text-muted">No communities found.</p> : communities.map((communityItem) => (
                <Link key={communityItem.id} to={communityItem.link} className="btn btn-secondary" style={{ textAlign: 'left' }}>
                  {communityItem.title}
                </Link>
              ))}
            </section>
          </Stack>
        </Grid>
      )}
    </PageShell>
  )
}
