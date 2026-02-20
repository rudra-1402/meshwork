import { useEffect, useMemo, useState } from 'react'
import { API_ROUTES } from '../utils/apiRoutes'
import api, { ensureApiSuccess, getApiErrorMessage } from '../utils/api'
import { Alert, EmptyState, Spinner } from '../components/ui'
import { PageShell } from '../components/layout'
import { STUDENT_NAV_ITEMS, STUDENT_TOP_ITEMS } from '../utils/appNavigation'

const TEAM_ROLE_OPTIONS = [
  'Building core features',
  'Designing architecture',
  'Working on UI/UX',
  'Experimenting with new ideas',
  'Optimizing or fixing things',
  'Leading or coordinating the team',
  'Learning while contributing',
]

const TECHNOLOGY_OPTIONS = [
  'Web (Frontend)',
  'Web (Backend)',
  'Mobile',
  'Cloud / DevOps',
  'AI / ML',
  'Data',
  'Systems / Low-level',
  'Security',
  'Game development',
  'APIs & integrations',
]

const COLLAB_OPTIONS = [
  'I prefer working solo and contributing specific pieces',
  'I enjoy tight collaboration with a small team',
  'I like large, active communities',
  'I enjoy mentoring or helping others grow',
]

const steps = [
  {
    key: 'q1_project_excitement',
    title: 'Project Excitement',
    description: 'Describe a coding project that would genuinely excite you to work on for weeks or months. What problem does it solve, and what part excites you most?',
    type: 'textarea',
    required: true,
    minLength: 30,
    placeholder: 'Example: I want to build a collaborative code editor because...',
  },
  {
    key: 'q2',
    title: 'Team Roles',
    description: 'Which role do you naturally gravitate toward in a team? (Choose up to 2)',
    type: 'roles',
    required: true,
  },
  {
    key: 'q3',
    title: 'Technical Depth vs Breadth',
    description: 'On a scale of 1–5, where do you fall? 1 = Deeply specialize in one area, 5 = Explore many areas broadly.',
    type: 'depth',
    required: true,
  },
  {
    key: 'q4_problem_solving',
    title: 'Problem Solving Style',
    description: 'Describe your approach to solving a complex technical problem.',
    type: 'textarea',
    required: true,
    minLength: 20,
    placeholder: 'My approach is...',
  },
  {
    key: 'q5',
    title: 'Your Experience',
    description: 'Rate each area from 1 to 5, where 5 = very experienced.',
    type: 'experience',
    required: true,
  },
  {
    key: 'q6',
    title: 'Technical Areas',
    description: 'Which technical areas interest you most? (Choose 1–6)',
    type: 'technologies',
    required: true,
  },
  {
    key: 'q7',
    title: 'Collaboration Style',
    description: 'How do you prefer to work with others?',
    type: 'collaboration',
    required: true,
  },
  {
    key: 'q8_learning_motivation',
    title: 'What Drives You?',
    description: 'What motivates you most in a project or job?',
    type: 'textarea',
    required: true,
    minLength: 20,
    placeholder: 'Right now, I am most motivated by...',
  },
]

const initialValues = {
  q1_project_excitement: '',
  q2_team_roles: [],
  q2_explanation: '',
  q3_depth_vs_breadth: '',
  q3_explanation: '',
  q4_problem_solving: '',
  q5_hackathons: '',
  q5_competitions: '',
  q5_team_projects: '',
  q5_open_source: '',
  q5_research: '',
  q6_technologies: [],
  q6_explanation: '',
  q7_collaboration_style: '',
  q7_explanation: '',
  q8_learning_motivation: '',
}

function SelectScaleField({ id, label, value, onChange }) {
  return (
    <label style={{ display: 'grid', gap: '6px' }}>
      <span className="text-small" style={{ fontWeight: 600 }}>{label}</span>
      <select className="input" aria-label={label} id={id} value={value} onChange={onChange}>
        <option value="">-- Select --</option>
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
        <option value="4">4</option>
        <option value="5">5</option>
      </select>
    </label>
  )
}

export default function Questionnaire() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [submitMessage, setSubmitMessage] = useState('')
  const [alreadyCompleted, setAlreadyCompleted] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [values, setValues] = useState(initialValues)

  useEffect(() => {
    let mounted = true

    async function loadStatus() {
      try {
        setLoading(true)
        setError('')
        const response = await api.get(API_ROUTES.scoring.questionnaire)
        const payload = ensureApiSuccess(response.data, 'Failed to load questionnaire')
        if (!mounted) return
        setAlreadyCompleted(Boolean(payload.questionnaire_completed))
      } catch (err) {
        if (!mounted) return
        setError(getApiErrorMessage(err, 'Failed to load questionnaire'))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadStatus()
    return () => {
      mounted = false
    }
  }, [])

  const activeStep = steps[stepIndex]
  const progress = ((stepIndex + 1) / steps.length) * 100

  const stepError = useMemo(() => {
    if (!activeStep) return ''

    if (activeStep.key === 'q2') {
      if (values.q2_team_roles.length < 1 || values.q2_team_roles.length > 2) {
        return 'Please select 1-2 team roles.'
      }
      if ((values.q2_explanation || '').trim().length < 20) {
        return 'Please explain your role choices in at least 20 characters.'
      }
      return ''
    }

    if (activeStep.key === 'q3') {
      if (!values.q3_depth_vs_breadth) {
        return 'Please choose your depth vs breadth value.'
      }
      if ((values.q3_explanation || '').trim().length < 20) {
        return 'Please explain your choice in at least 20 characters.'
      }
      return ''
    }

    if (activeStep.key === 'q5') {
      const scoreFields = ['q5_hackathons', 'q5_competitions', 'q5_team_projects', 'q5_open_source', 'q5_research']
      const invalid = scoreFields.some((field) => !values[field])
      return invalid ? 'Please rate all experience fields from 1 to 5.' : ''
    }

    if (activeStep.key === 'q6') {
      if (values.q6_technologies.length < 1 || values.q6_technologies.length > 6) {
        return 'Please select between 1 and 6 technology areas.'
      }
      return ''
    }

    if (activeStep.key === 'q7') {
      if (!values.q7_collaboration_style) {
        return 'Please select one collaboration style.'
      }
      if ((values.q7_explanation || '').trim().length < 15) {
        return 'Please add a short explanation (at least 15 characters).'
      }
      return ''
    }

    const value = values[activeStep.key]
    if (activeStep.required && typeof value === 'string' && !value.trim()) {
      return 'Please complete this question before continuing.'
    }
    if (activeStep.minLength && (value || '').trim().length < activeStep.minLength) {
      return `Please enter at least ${activeStep.minLength} characters.`
    }
    return ''
  }, [activeStep, values])

  const canContinue = !stepError
  const atLastStep = stepIndex === steps.length - 1

  const updateValue = (key, nextValue) => {
    setValues((prev) => ({ ...prev, [key]: nextValue }))
    setError('')
  }

  const toggleArrayValue = (key, option, max) => {
    setValues((prev) => {
      const current = prev[key]
      const exists = current.includes(option)
      if (exists) {
        return { ...prev, [key]: current.filter((item) => item !== option) }
      }
      if (current.length >= max) {
        return prev
      }
      return { ...prev, [key]: [...current, option] }
    })
  }

  const submitQuestionnaire = async () => {
    if (!atLastStep || !canContinue || saving) return

    const responses = {
      ...values,
      q3_depth_vs_breadth: Number(values.q3_depth_vs_breadth),
      q5_hackathons: Number(values.q5_hackathons),
      q5_competitions: Number(values.q5_competitions),
      q5_team_projects: Number(values.q5_team_projects),
      q5_open_source: Number(values.q5_open_source),
      q5_research: Number(values.q5_research),
    }

    try {
      setSaving(true)
      setError('')
      setSubmitMessage('')
      const response = await api.post(API_ROUTES.scoring.submit, { responses })
      const payload = ensureApiSuccess(response.data, 'Failed to submit questionnaire')
      setSubmitMessage(payload.message || 'Questionnaire submitted successfully.')
      setAlreadyCompleted(true)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to submit questionnaire'))
    } finally {
      setSaving(false)
    }
  }

  const renderStep = () => {
    if (!activeStep) return null

    if (activeStep.key === 'q2') {
      return (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'grid', gap: '8px' }}>
            {TEAM_ROLE_OPTIONS.map((option) => (
              <label key={option} className="card" style={{ padding: '10px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={values.q2_team_roles.includes(option)}
                  onChange={() => toggleArrayValue('q2_team_roles', option, 2)}
                  aria-label={option}
                />
                <span className="text-small">{option}</span>
              </label>
            ))}
          </div>
          <textarea
            className="input"
            rows={4}
            value={values.q2_explanation}
            onChange={(event) => updateValue('q2_explanation', event.target.value)}
            placeholder="I chose these roles because..."
            aria-label="Explain team role choices"
          />
        </div>
      )
    }

    if (activeStep.key === 'q3') {
      return (
        <div style={{ display: 'grid', gap: '12px' }}>
          <select
            className="input"
            value={values.q3_depth_vs_breadth}
            onChange={(event) => updateValue('q3_depth_vs_breadth', event.target.value)}
            aria-label="Depth vs breadth"
          >
            <option value="">-- Select --</option>
            <option value="1">1 - Deep specialization</option>
            <option value="2">2 - Mostly deep, some breadth</option>
            <option value="3">3 - Balanced</option>
            <option value="4">4 - Mostly broad, some depth</option>
            <option value="5">5 - Broad exploration</option>
          </select>
          <textarea
            className="input"
            rows={4}
            value={values.q3_explanation}
            onChange={(event) => updateValue('q3_explanation', event.target.value)}
            placeholder="I chose this because..."
            aria-label="Explain depth and breadth"
          />
        </div>
      )
    }

    if (activeStep.key === 'q5') {
      return (
        <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
          <SelectScaleField id="q5_hackathons" label="Hackathons" value={values.q5_hackathons} onChange={(event) => updateValue('q5_hackathons', event.target.value)} />
          <SelectScaleField id="q5_competitions" label="Competitions" value={values.q5_competitions} onChange={(event) => updateValue('q5_competitions', event.target.value)} />
          <SelectScaleField id="q5_team_projects" label="Team Projects" value={values.q5_team_projects} onChange={(event) => updateValue('q5_team_projects', event.target.value)} />
          <SelectScaleField id="q5_open_source" label="Open Source" value={values.q5_open_source} onChange={(event) => updateValue('q5_open_source', event.target.value)} />
          <div style={{ gridColumn: '1 / -1' }}>
            <SelectScaleField id="q5_research" label="Research Projects" value={values.q5_research} onChange={(event) => updateValue('q5_research', event.target.value)} />
          </div>
        </div>
      )
    }

    if (activeStep.key === 'q6') {
      return (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'grid', gap: '8px' }}>
            {TECHNOLOGY_OPTIONS.map((option) => (
              <label key={option} className="card" style={{ padding: '10px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={values.q6_technologies.includes(option)}
                  onChange={() => toggleArrayValue('q6_technologies', option, 6)}
                  aria-label={option}
                />
                <span className="text-small">{option}</span>
              </label>
            ))}
          </div>
          <textarea
            className="input"
            rows={3}
            value={values.q6_explanation}
            onChange={(event) => updateValue('q6_explanation', event.target.value)}
            placeholder="Tell us about your favorite project or technology"
            aria-label="Technology explanation"
          />
        </div>
      )
    }

    if (activeStep.key === 'q7') {
      return (
        <div style={{ display: 'grid', gap: '12px' }}>
          <select
            className="input"
            value={values.q7_collaboration_style}
            onChange={(event) => updateValue('q7_collaboration_style', event.target.value)}
            aria-label="Collaboration style"
          >
            <option value="">-- Select --</option>
            {COLLAB_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <textarea
            className="input"
            rows={4}
            value={values.q7_explanation}
            onChange={(event) => updateValue('q7_explanation', event.target.value)}
            placeholder="What is important to you in a team environment?"
            aria-label="Collaboration explanation"
          />
        </div>
      )
    }

    return (
      <textarea
        className="input"
        rows={5}
        value={values[activeStep.key] || ''}
        onChange={(event) => updateValue(activeStep.key, event.target.value)}
        placeholder={activeStep.placeholder || 'Type your answer...'}
        aria-label={activeStep.title}
      />
    )
  }

  return (
    <PageShell
      brand="MeshWork"
      brandTo="/home"
      navItems={STUDENT_NAV_ITEMS}
      topItems={STUDENT_TOP_ITEMS}
    >
      {loading ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Spinner />
          <span className="text-small text-muted">Loading questionnaire...</span>
        </div>
      ) : error ? (
        <Alert tone="error" message={error} />
      ) : alreadyCompleted ? (
        <Alert tone="success" message={submitMessage || 'Questionnaire already completed. You can retake it from your profile.'} />
      ) : !activeStep ? (
        <EmptyState title="Questionnaire unavailable" description="Please refresh and try again." />
      ) : (
        <section className="card" style={{ maxWidth: '960px', marginInline: 'auto', display: 'grid', gap: '16px' }}>
          <div>
            <h1 className="text-subsection">Complete Your Profile</h1>
            <p className="text-small text-muted" style={{ marginTop: '4px' }}>
              Help us understand your skills and interests by answering these questions.
            </p>
          </div>

          <div style={{ display: 'grid', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="text-small" style={{ fontWeight: 600 }}>Progress</span>
              <span className="text-small text-muted">Step {stepIndex + 1} of {steps.length}</span>
            </div>
            <div className="progress-track" style={{ height: '8px' }}>
              <div className="progress-fill" style={{ width: `${progress}%`, height: '8px' }} />
            </div>
          </div>

          <div className="card" style={{ display: 'grid', gap: '12px' }}>
            <h2 className="text-body" style={{ fontWeight: 700 }}>{stepIndex + 1}. {activeStep.title}</h2>
            <p className="text-small text-muted">{activeStep.description}</p>
            {renderStep()}
            {stepError ? <p className="text-small" style={{ color: 'var(--color-warning)', margin: 0 }}>{stepError}</p> : null}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setStepIndex((prev) => Math.max(prev - 1, 0))}
              disabled={stepIndex === 0 || saving}
            >
              Previous
            </button>

            {!atLastStep ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  if (!canContinue) return
                  setStepIndex((prev) => Math.min(prev + 1, steps.length - 1))
                }}
                disabled={!canContinue || saving}
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-primary"
                onClick={submitQuestionnaire}
                disabled={!canContinue || saving}
              >
                {saving ? 'Processing...' : 'Submit Questionnaire'}
              </button>
            )}
          </div>

          {saving ? (
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Spinner />
              <span className="text-small text-muted">Processing your profile. This may take 30-60 seconds.</span>
            </div>
          ) : null}

          {submitMessage ? <Alert tone="success" message={submitMessage} /> : null}
        </section>
      )}
    </PageShell>
  )
}
