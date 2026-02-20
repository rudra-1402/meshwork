import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockGet = vi.fn()

vi.mock('../../utils/api', () => ({
  default: {
    get: (...args) => mockGet(...args),
  },
  ensureApiSuccess: (payload, fallback = 'Request failed') => {
    if (!payload || payload.success !== true) {
      throw new Error(payload?.message || payload?.error || fallback)
    }
    return payload
  },
  getApiErrorMessage: (error, fallback = 'Request failed') => (
    error?.response?.data?.message || error?.response?.data?.error || error?.message || fallback
  ),
}))

import Projects from '../../pages/Projects'
import Events from '../../pages/Events'
import CommunitiesExplore from '../../pages/CommunitiesExplore'

function renderWithRouter(node) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

describe('Phase C pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders projects list from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          projects: [{ id: 1, title: 'Mesh AI', description: 'AI collaboration', match_percent: 88, tags: ['AI'] }],
        },
      },
    })

    renderWithRouter(<Projects />)

    expect(await screen.findByText(/mesh ai/i)).toBeInTheDocument()
    expect(screen.getByText(/ai collaboration/i)).toBeInTheDocument()
  })

  it('renders events list from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          events: [{ id: 11, title: 'Hack Day', description: 'Build and present', status: 'open', progress: 35 }],
        },
      },
    })

    renderWithRouter(<Events />)

    expect(await screen.findByText(/hack day/i)).toBeInTheDocument()
    expect(screen.getByText(/status: open/i)).toBeInTheDocument()
  })

  it('renders communities list from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          communities: [{ id: 20, name: 'Python Circle', description: 'Weekly challenges', tags: ['Python'], match_percent: 91 }],
        },
      },
    })

    renderWithRouter(<CommunitiesExplore />)

    expect(await screen.findByText(/python circle/i)).toBeInTheDocument()
    expect(screen.getByText(/weekly challenges/i)).toBeInTheDocument()
  })
})
