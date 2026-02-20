import { http, HttpResponse } from 'msw'

export const handlers = [
  http.post('/api/auth/validate-email', async ({ request }) => {
    const body = await request.json()
    const email = body?.email ?? ''
    if (!email.includes('@')) {
      return HttpResponse.json({ success: false, message: 'Invalid email' }, { status: 400 })
    }
    return HttpResponse.json({ valid: true, is_registered: false, user_type: 'student', college_id: 1 })
  }),

  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json()
    if (body?.password === 'wrong') {
      return HttpResponse.json({ success: false, message: 'Invalid credentials' }, { status: 401 })
    }
    return HttpResponse.json({ success: true, token: 'mock-jwt-token', user: { id: 1, email: body?.email } })
  }),

  http.post('/api/auth/signup', async ({ request }) => {
    const body = await request.json()
    if (!body?.email || !body?.password) {
      return HttpResponse.json({ success: false, message: 'Missing required fields' }, { status: 400 })
    }
    return HttpResponse.json({ success: true, token: 'mock-jwt-token', user: { id: 2, email: body?.email } })
  }),
]
