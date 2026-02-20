import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, MatchCard, SearchInput, Skeleton } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeProjects(payload) {
  const raw = payload?.data || payload || {}
  const items = raw.projects || raw.items || []
  return items.map((project, index) => ({
    id: project.id || project.project_id || `project-${index + 1}`,
    title: project.title || project.name || `Project ${index + 1}`,
    description: project.description || 'No description available.',
    percent: project.match_percent ?? project.progress ?? 0,
    tags: project.tags || project.skills || [],
  }))
}

export default function Projects() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [projects, setProjects] = useState([])

  useEffect(() => {
    let mounted = true

    async function loadProjects() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.projects.list)
        const payload = ensureApiSuccess(response.data, 'Failed to load projects')
        if (!mounted) return
        setProjects(normalizeProjects(payload))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load projects'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadProjects()
    return () => {
      mounted = false
    }
  }, [])

  const filtered = useMemo(() => (
    projects.filter((item) => item.title.toLowerCase().includes(search.toLowerCase()))
  ), [projects, search])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          <div className="card" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search projects"
              ariaLabel="Search projects"
            />
            <Link className="btn btn-secondary" to="/projects/new">New Project</Link>
          </div>

          {loading ? (
            <>
              <Skeleton height={90} />
              <Skeleton height={90} />
              <Skeleton height={90} />
            </>
          ) : error ? (
            <Alert tone="error" message={error} />
          ) : filtered.length === 0 ? (
            <EmptyState title="No projects found" description="Try a different search or create a new project." />
          ) : (
            filtered.map((project) => (
              <MatchCard
                key={project.id}
                title={project.title}
                description={project.description}
                percent={project.percent}
                tags={project.tags}
                action={<Link className="btn btn-secondary" to={`/projects/${project.id}`}>View Project</Link>}
              />
            ))
          )}
        </Stack>
    </PageShell>
  )
}
