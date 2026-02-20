import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, SearchInput, Skeleton, Tabs, MatchCard } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeEvents(payload) {
  const raw = payload?.data || payload || {}
  const items = raw.events || raw.items || []
  return items.map((event, index) => ({
    id: event.id || event.event_id || `event-${index + 1}`,
    title: event.title || event.name || `Event ${index + 1}`,
    description: event.description || 'No description available.',
    status: event.status || 'open',
    percent: event.progress ?? 0,
  }))
}

export default function Events() {
  const [tab, setTab] = useState('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [events, setEvents] = useState([])

  useEffect(() => {
    let mounted = true

    async function loadEvents() {
      try {
        setLoading(true)
        setError('')
        const route = tab === 'pending' ? API_ROUTES.events.pending : API_ROUTES.events.list
        const response = await api.get(route)
        const payload = ensureApiSuccess(response.data, 'Failed to load events')
        if (!mounted) return
        setEvents(normalizeEvents(payload))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load events'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadEvents()
    return () => {
      mounted = false
    }
  }, [tab])

  const filtered = useMemo(() => (
    events.filter((item) => item.title.toLowerCase().includes(search.toLowerCase()))
  ), [events, search])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          <div className="card" style={{ display: 'grid', gap: '10px' }}>
            <Tabs
              value={tab}
              onChange={setTab}
              tabs={[
                { label: 'All Events', value: 'all' },
                { label: 'Pending', value: 'pending' },
              ]}
            />
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search events"
              ariaLabel="Search events"
            />
          </div>

          {loading ? (
            <>
              <Skeleton height={90} />
              <Skeleton height={90} />
            </>
          ) : error ? (
            <Alert tone="error" message={error} />
          ) : filtered.length === 0 ? (
            <EmptyState title="No events found" description="No events matched your current view." />
          ) : (
            filtered.map((event) => (
              <MatchCard
                key={event.id}
                title={event.title}
                description={`${event.description} • Status: ${event.status}`}
                percent={event.percent}
                action={<Link className="btn btn-secondary" to={`/events/${event.id}`}>Open Event</Link>}
              />
            ))
          )}
        </Stack>
    </PageShell>
  )
}
