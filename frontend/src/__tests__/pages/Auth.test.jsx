import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const original = await importOriginal()
  return { ...original, useNavigate: () => mockNavigate }
})

const mockValidateEmail = vi.fn()
const mockLogin = vi.fn()
const mockSignup = vi.fn()

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    validateEmail: mockValidateEmail,
    login: mockLogin,
    signup: mockSignup,
  }),
}))

import Auth from '../../pages/Auth'

function renderAuth() {
  return render(
    <MemoryRouter>
      <Auth />
    </MemoryRouter>
  )
}

describe('Auth page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockValidateEmail.mockResolvedValue({ valid: true, user_type: 'student', college_id: 1 })
  })

  it('renders email and submit action', () => {
    renderAuth()
    expect(screen.getByRole('textbox', { name: /institutional email/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('validates email on blur', async () => {
    mockValidateEmail.mockResolvedValueOnce({ valid: false, error: 'Invalid domain' })
    renderAuth()

    const emailInput = screen.getByRole('textbox', { name: /institutional email/i })
    await userEvent.type(emailInput, 'bad@example.com')
    fireEvent.blur(emailInput)

    await waitFor(() => {
      expect(mockValidateEmail).toHaveBeenCalledWith('bad@example.com')
      expect(screen.getByText(/invalid domain/i)).toBeInTheDocument()
    })
  })

  it('calls login and navigates on success', async () => {
    mockLogin.mockResolvedValueOnce({ success: true, dashboard_route: '/dashboard' })
    renderAuth()

    await userEvent.type(screen.getByRole('textbox', { name: /institutional email/i }), 'user@student.edu')
    await userEvent.type(screen.getAllByLabelText(/password/i)[0], 'Pass123!')
    await userEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('user@student.edu', 'Pass123!')
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('calls signup in signup mode', async () => {
    mockSignup.mockResolvedValueOnce({ success: true, dashboard_route: '/dashboard' })

    renderAuth()

    await userEvent.click(screen.getByRole('button', { name: /sign up/i }))

    const emailInput = screen.getByRole('textbox', { name: /institutional email/i })
    await userEvent.type(emailInput, 'new@student.edu')
    fireEvent.blur(emailInput)

    await userEvent.type(screen.getByLabelText(/first name/i), 'New')
    await userEvent.type(screen.getByLabelText(/last name/i), 'User')
    await userEvent.type(screen.getByLabelText(/username/i), 'newuser')

    const passwordInputs = screen.getAllByLabelText(/password/i)
    await userEvent.type(passwordInputs[0], 'Pass123!')
    await userEvent.type(passwordInputs[1], 'Pass123!')

    await userEvent.click(screen.getByRole('button', { name: /sign up/i }))

    await waitFor(() => {
      expect(mockSignup).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })
})
