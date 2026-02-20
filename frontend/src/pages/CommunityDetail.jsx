import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, MatchCard, Skeleton } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeCommunity(payload, id) {
  const raw = payload?.data?.community || payload?.data || payload || {}
  return {
    id,
    title: raw.name || `Community ${id}`,
    description: raw.description || 'No description available.',
    tags: raw.tags || raw.interests || [],
    percent: raw.match_percent ?? 0,
  }
}

export default function CommunityDetail() {
  const { communityId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [community, setCommunity] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadCommunity() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.communities.byId(communityId))
        const payload = ensureApiSuccess(response.data, 'Failed to load community')
        if (!mounted) return
        setCommunity(normalizeCommunity(payload, communityId))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load community'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadCommunity()
    return () => {
      mounted = false
    }
  }, [communityId])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          {loading ? <Skeleton height={110} /> : null}
          {error ? <Alert tone="error" message={error} /> : null}
          {!loading && !error && !community ? <EmptyState title="Community not found" /> : null}
          {!loading && !error && community ? (
            <MatchCard
              title={community.title}
              description={community.description}
              tags={community.tags}
              percent={community.percent}
            />
          ) : null}
        </Stack>
    </PageShell>
  )
}
