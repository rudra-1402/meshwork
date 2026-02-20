import { useEffect, useState } from 'react'
import { API_ROUTES } from '../utils/apiRoutes'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import {
  Alert,
  EmptyState,
  SearchInput,
  Tabs,
  UserCard,
  Skeleton,
} from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeEntries(payload) {
  const raw = payload?.data || payload || {}
  const entries = raw.entries || raw.items || raw.leaderboard || []
  return entries.map((entry, index) => ({
    id: entry.id || entry.user_id || `${entry.name || 'user'}-${index}`,
    name: entry.name || entry.username || 'User',
    subtitle: `Rank #${entry.rank ?? index + 1} • ${entry.xp ?? entry.score ?? 0} XP`,
    role: entry.role || 'student',
  }))
}

export default function Leaderboard() {
  const [tab, setTab] = useState('xp')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [entries, setEntries] = useState([])

  useEffect(() => {
    let mounted = true

    async function loadLeaderboard() {
      try {
        setLoading(true)
        setError('')
        const route = tab === 'xp' ? API_ROUTES.leaderboard.xp : API_ROUTES.leaderboard.streak
        const response = await api.get(route)
        const payload = ensureApiSuccess(response.data, 'Failed to load leaderboard')
        if (!mounted) return
        setEntries(normalizeEntries(payload))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load leaderboard'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadLeaderboard()
    return () => {
      mounted = false
    }
  }, [tab])

  const filteredEntries = entries.filter((entry) =>
    entry.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          <div className="card" style={{ display: 'grid', gap: '10px' }}>
            <Tabs
              value={tab}
              onChange={setTab}
              tabs={[
                { label: 'XP', value: 'xp' },
                { label: 'Streak', value: 'streak' },
              ]}
            />
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search users"
              ariaLabel="Search leaderboard users"
            />
          </div>

          {loading ? (
            <>
              <Skeleton height={82} />
              <Skeleton height={82} />
              <Skeleton height={82} />
            </>
          ) : error ? (
            <Alert tone="error" message={error} />
          ) : filteredEntries.length === 0 ? (
            <EmptyState title="No leaderboard entries" description="No users matched your search." />
          ) : (
            filteredEntries.map((entry) => (
              <UserCard
                key={entry.id}
                name={entry.name}
                subtitle={entry.subtitle}
                role={entry.role}
              />
            ))
          )}
        </Stack>
    </PageShell>
  )
}
