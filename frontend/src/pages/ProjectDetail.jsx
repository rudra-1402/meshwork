import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, EmptyState, MatchCard, Skeleton } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

function normalizeProject(payload, id) {
  const raw = payload?.data?.project || payload?.data || payload || {}
  return {
    id,
    title: raw.title || raw.name || `Project ${id}`,
    description: raw.description || 'No description available.',
    tags: raw.tags || raw.skills || [],
    percent: raw.match_percent ?? raw.progress ?? 0,
  }
}

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [project, setProject] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadProject() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.projects.byId(projectId))
        const payload = ensureApiSuccess(response.data, 'Failed to load project')
        if (!mounted) return
        setProject(normalizeProject(payload, projectId))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load project'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadProject()
    return () => {
      mounted = false
    }
  }, [projectId])

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          {loading ? <Skeleton height={110} /> : null}
          {error ? <Alert tone="error" message={error} /> : null}
          {!loading && !error && !project ? <EmptyState title="Project not found" /> : null}
          {!loading && !error && project ? (
            <MatchCard
              title={project.title}
              description={project.description}
              tags={project.tags}
              percent={project.percent}
            />
          ) : null}
        </Stack>
    </PageShell>
  )
}
