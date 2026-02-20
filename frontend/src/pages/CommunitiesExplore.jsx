import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, InterestChip, MatchCard, SearchInput, Skeleton } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeCommunities(payload) {
  const raw = payload?.data || payload || {}
  const items = raw.communities || raw.items || []
  return items.map((community, index) => ({
    id: community.id || community.community_id || `community-${index + 1}`,
    title: community.name || `Community ${index + 1}`,
    description: community.description || 'No description available.',
    tags: community.tags || community.interests || [],
    percent: community.match_percent ?? 0,
  }))
}

export default function CommunitiesExplore() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [activeTag, setActiveTag] = useState('')
  const [communities, setCommunities] = useState([])

  useEffect(() => {
    let mounted = true

    async function loadCommunities() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.communities.explore)
        const payload = ensureApiSuccess(response.data, 'Failed to load communities')
        if (!mounted) return
        setCommunities(normalizeCommunities(payload))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load communities'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadCommunities()
    return () => {
      mounted = false
    }
  }, [])

  const availableTags = useMemo(() => {
    const set = new Set()
    communities.forEach((community) => community.tags.forEach((tag) => set.add(tag)))
    return Array.from(set).slice(0, 6)
  }, [communities])

  const filtered = useMemo(() => (
    communities.filter((item) => {
      const matchesSearch = item.title.toLowerCase().includes(search.toLowerCase())
      const matchesTag = !activeTag || item.tags.includes(activeTag)
      return matchesSearch && matchesTag
    })
  ), [communities, search, activeTag])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          <div className="card" style={{ display: 'grid', gap: '10px' }}>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search communities"
              ariaLabel="Search communities"
            />

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {availableTags.map((tag) => (
                <InterestChip
                  key={tag}
                  label={tag}
                  selected={tag === activeTag}
                  onToggle={(selected) => setActiveTag(selected ? tag : '')}
                />
              ))}
            </div>
          </div>

          {loading ? (
            <>
              <Skeleton height={90} />
              <Skeleton height={90} />
            </>
          ) : error ? (
            <Alert tone="error" message={error} />
          ) : filtered.length === 0 ? (
            <EmptyState title="No communities found" description="Try changing your search or selected tag." />
          ) : (
            filtered.map((community) => (
              <MatchCard
                key={community.id}
                title={community.title}
                description={community.description}
                percent={community.percent}
                tags={community.tags}
                action={<Link className="btn btn-secondary" to={`/communities/${community.id}`}>View Community</Link>}
              />
            ))
          )}
        </Stack>
    </PageShell>
  )
}
