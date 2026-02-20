import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../../context/AuthContext'

// Mock the api module so we don't make real HTTP calls
vi.mock('../../utils/api', () => ({
  default: {
    post: vi.fn(),
  },
  ensureApiSuccess: (payload) => {
    if (!payload || payload.success !== true) {
      const error = new Error(payload?.message || payload?.error || 'Request failed')
      error.payload = payload
      throw error
    }
    return payload
  },
  getApiErrorMessage: (error, fallback = 'Request failed') => (
    error?.response?.data?.message || error?.response?.data?.error || error?.message || fallback
  ),
  setApiAuthToken: vi.fn(),
  clearApiAuthToken: vi.fn(),
}))

import api from '../../utils/api'

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts with no user in memory', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('does not restore persisted state across fresh mounts', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('login sets user and token in memory', async () => {
    const mockUser = { id: 1, email: 'user@student.edu' }
    api.post.mockResolvedValueOnce({
      data: { success: true, token: 'jwt-abc', user: mockUser, dashboard_route: '/dashboard' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    let loginResult
    await act(async () => {
      loginResult = await result.current.login('user@student.edu', 'Pass123!')
    })

    expect(loginResult.success).toBe(true)
    expect(loginResult.dashboard_route).toBe('/dashboard')
    expect(result.current.user).toEqual(mockUser)
    expect(result.current.token).toBe('jwt-abc')
  })

  it('login returns error on API failure', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { message: 'Invalid credentials' } },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    let loginResult
    await act(async () => {
      loginResult = await result.current.login('bad@student.edu', 'wrong')
    })

    expect(loginResult.success).toBe(false)
    expect(loginResult.error).toBe('Invalid credentials')
    expect(result.current.user).toBeNull()
  })

  it('logout clears user and token in memory', async () => {
    const mockUser = { id: 1, email: 'user@student.edu' }
    api.post.mockResolvedValueOnce({
      data: { success: true, token: 'jwt-abc', user: mockUser, dashboard_route: '/dashboard' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.login('user@student.edu', 'Pass123!')
    })

    act(() => {
      result.current.logout()
    })

    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('signup sets user and token in memory', async () => {
    const mockUser = { id: 2, email: 'new@student.edu' }
    api.post.mockResolvedValueOnce({
      data: { success: true, token: 'jwt-new', user: mockUser, dashboard_route: '/dashboard' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    let signupResult
    await act(async () => {
      signupResult = await result.current.signup({
        email: 'new@student.edu',
        password: 'Pass123!',
        username: 'newuser',
        first_name: 'New',
        last_name: 'User',
      })
    })

    expect(signupResult.success).toBe(true)
    expect(result.current.user).toEqual(mockUser)
    expect(result.current.token).toBe('jwt-new')
  })
})
