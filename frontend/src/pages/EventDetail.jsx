import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, MatchCard, Skeleton } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeEvent(payload, id) {
  const raw = payload?.data?.event || payload?.data || payload || {}
  return {
    id,
    title: raw.title || raw.name || `Event ${id}`,
    description: raw.description || 'No description available.',
    percent: raw.progress ?? 0,
    tags: raw.tags || [raw.status || 'open'],
  }
}

export default function EventDetail() {
  const { eventId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [eventItem, setEventItem] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadEvent() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.events.byId(eventId))
        const payload = ensureApiSuccess(response.data, 'Failed to load event')
        if (!mounted) return
        setEventItem(normalizeEvent(payload, eventId))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load event'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadEvent()
    return () => {
      mounted = false
    }
  }, [eventId])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          {loading ? <Skeleton height={110} /> : null}
          {error ? <Alert tone="error" message={error} /> : null}
          {!loading && !error && !eventItem ? <EmptyState title="Event not found" /> : null}
          {!loading && !error && eventItem ? (
            <MatchCard
              title={eventItem.title}
              description={eventItem.description}
              tags={eventItem.tags}
              percent={eventItem.percent}
            />
          ) : null}
        </Stack>
    </PageShell>
  )
}
