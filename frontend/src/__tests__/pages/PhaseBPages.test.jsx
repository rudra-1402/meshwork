import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('../../utils/api', () => ({
  default: {
    get: (...args) => mockGet(...args),
    post: (...args) => mockPost(...args),
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

import Home from '../../pages/Home'
import Profile from '../../pages/Profile'
import Leaderboard from '../../pages/Leaderboard'
import Questionnaire from '../../pages/Questionnaire'

function renderWithRouter(node) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

describe('Phase B pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders home feed from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          projects: [{ id: 1, title: 'Open Build', description: 'Ship together' }],
        },
      },
    })
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          events: [{ id: 2, title: 'Hack Day', description: 'Build fast' }],
        },
      },
    })
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          communities: [{ id: 3, name: 'Makers', description: 'Weekly demos' }],
        },
      },
    })

    renderWithRouter(<Home />)

    expect(await screen.findByText(/home feed/i)).toBeInTheDocument()
    expect(screen.getByText(/open build/i)).toBeInTheDocument()
  })

  it('renders profile summary from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          user: { first_name: 'Sam', last_name: 'Lee', email: 'sam@meshwork.edu' },
          stats: { level: 5, xp: 1500, streak: 8, motivation: 76 },
        },
      },
    })
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          stats: { level: 5, xp: 1500, streak: 8, projects: 6 },
        },
      },
    })
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          motivation_score: 7.6,
          dominant_roles: ['Builder'],
          all_roles: { Builder: { score: 8.1 } },
          top_interests: [],
        },
      },
    })

    renderWithRouter(<Profile />)

    expect(await screen.findByText(/sam lee/i)).toBeInTheDocument()
    expect(screen.getByText(/sam@meshwork.edu/i)).toBeInTheDocument()
  })

  it('renders leaderboard entries from API', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          entries: [{ id: 1, name: 'Taylor', rank: 1, xp: 2000, role: 'student' }],
        },
      },
    })

    renderWithRouter(<Leaderboard />)

    expect(await screen.findByText(/taylor/i)).toBeInTheDocument()
    expect(screen.getByText(/rank #1/i)).toBeInTheDocument()
  })

  it('loads questionnaire stepper flow', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        questionnaire_completed: false,
      },
    })

    renderWithRouter(<Questionnaire />)

    expect(await screen.findByText(/complete your profile/i)).toBeInTheDocument()
    expect(screen.getByText(/step 1 of 8/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
  })
})
