import { createContext, useContext, useState } from 'react'
import api, {
  clearApiAuthToken,
  ensureApiSuccess,
  getApiErrorMessage,
  setApiAuthToken,
} from '../utils/api'
import { API_ROUTES } from '../utils/apiRoutes'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading] = useState(false)

  const validateEmail = async (email) => {
    try {
      const response = await api.post(API_ROUTES.auth.validateEmail, { email })
      const payload = ensureApiSuccess(response.data, 'Email validation failed')
      return { success: true, ...payload }
    } catch (error) {
      const data = error.response?.data || error.payload || {}
      // is_registered means the email exists — treat as login, not an error
      if (data.is_registered) {
        return { success: false, is_registered: true, ...data }
      }
      return { success: false, error: getApiErrorMessage(error, 'Email validation failed') }
    }
  }

  const login = async (email, password) => {
    try {
      const response = await api.post(API_ROUTES.auth.login, { email, password })
      const payload = ensureApiSuccess(response.data, 'Login failed')
      const { token: jwtToken, user: userData, dashboard_route } = payload

      setToken(jwtToken || null)
      setApiAuthToken(jwtToken)
      setUser(userData)
      return { success: true, dashboard_route: dashboard_route || '/dashboard' }
    } catch (error) {
      return { success: false, error: getApiErrorMessage(error, 'Login failed') }
    }
  }

  const signup = async (data) => {
    try {
      const response = await api.post(API_ROUTES.auth.signup, data)
      const payload = ensureApiSuccess(response.data, 'Registration failed')
      const { token: jwtToken, user: userData, dashboard_route } = payload

      setToken(jwtToken || null)
      setApiAuthToken(jwtToken)
      setUser(userData)
      return { success: true, dashboard_route: dashboard_route || '/dashboard' }
    } catch (error) {
      return { success: false, error: getApiErrorMessage(error, 'Registration failed') }
    }
  }

  const logout = () => {
    clearApiAuthToken()
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, validateEmail, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
