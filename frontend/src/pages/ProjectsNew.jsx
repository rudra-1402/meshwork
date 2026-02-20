import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'
import { Alert, Button } from '../components/ui'
import { PageShell, Stack } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

export default function ProjectsNew() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const canSubmit = Boolean(title.trim()) && !saving

  const createProject = async () => {
    if (!canSubmit) return

    try {
      setSaving(true)
      setError('')
      const response = await api.post(API_ROUTES.projects.create, {
        title: title.trim(),
        description: description.trim(),
      })
      const payload = ensureApiSuccess(response.data, 'Failed to create project')
      const createdId = payload?.data?.project?.id || payload?.data?.id
      navigate(createdId ? `/projects/${createdId}` : '/projects')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to create project'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageShell brand="MeshWork" brandTo="/home" navItems={STUDENT_NAV_ITEMS} topItems={STUDENT_TOP_ITEMS}>
        <Stack gap={12}>
          <section className="card">
            <h1 className="text-subsection" style={{ marginBottom: '10px' }}>Create Project</h1>
            <div style={{ display: 'grid', gap: '10px' }}>
              <input
                className="input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Project title"
                aria-label="Project title"
              />
              <textarea
                className="input"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Project description"
                aria-label="Project description"
                rows={5}
                style={{ resize: 'vertical' }}
              />
              <div style={{ display: 'flex', gap: '10px' }}>
                <Button onClick={createProject} disabled={!canSubmit}>
                  {saving ? 'Creating...' : 'Create Project'}
                </Button>
                <Button variant="secondary" onClick={() => navigate('/projects')}>Cancel</Button>
              </div>
            </div>
          </section>
          {error ? <Alert message={error} tone="error" /> : null}
        </Stack>
    </PageShell>
  )
}
