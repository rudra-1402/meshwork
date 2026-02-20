import axios from 'axios'
import { API_ROUTES } from './apiRoutes'

const configuredBaseURL = (import.meta.env.VITE_API_URL || '').trim()
const resolvedBaseURL = import.meta.env.DEV ? '' : configuredBaseURL

const api = axios.create({
  baseURL: resolvedBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

let authToken = null

export function setApiAuthToken(token) {
  authToken = token || null
}

export function clearApiAuthToken() {
  authToken = null
}

export function ensureApiSuccess(payload, fallbackMessage = 'Request failed') {
  const isSuccess = payload?.success === true || payload?.status === 'success'

  if (!payload || !isSuccess) {
    const error = new Error(payload?.message || payload?.error || fallbackMessage)
    error.payload = payload
    throw error
  }

  return payload
}

export function getApiErrorMessage(error, fallbackMessage = 'Request failed') {
  if (error?.code === 'ERR_NETWORK' || (!error?.response && error?.message === 'Network Error')) {
    return 'Cannot reach backend. Check backend on :5000 and restart frontend dev server.'
  }

  return (
    error?.response?.data?.message
    || error?.response?.data?.error
    || error?.message
    || fallbackMessage
  )
}

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

const AUTH_PATHS = [
  API_ROUTES.auth.login,
  API_ROUTES.auth.signup,
  API_ROUTES.auth.validateEmail,
  API_ROUTES.collegeAuth.login,
  API_ROUTES.collegeAuth.signup,
]

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      const isAuthEndpoint = AUTH_PATHS.some((path) => url.includes(path))
      if (!isAuthEndpoint) {
        clearApiAuthToken()
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)

export default api
