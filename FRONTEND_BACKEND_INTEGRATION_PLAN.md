# Frontend-Backend Integration Plan
## Complete Analysis & Implementation Roadmap

**Date Created:** February 18, 2026  
**Status:** Action Required  
**Priority:** High

---

## 📊 Executive Summary

The current MeshWork application has:
- ✅ **Frontend:** Fully designed landing page and auth UI (React SPA)
- ✅ **Backend:** Complete unified auth API with gamification features
- ❌ **Integration:** **ZERO** connection between frontend and backend
- ⚠️ **Architecture Conflict:** Backend has both JSON APIs and template-based routes

**Critical Issue:** Frontend displays mock data only. No actual API calls are being made.

---

## 🔍 Current State Analysis

### Frontend Files (All in `frontend/src/`)

| File | Purpose | Status | Issues |
|------|---------|--------|--------|
| `pages/Landing.jsx` | Marketing landing page | ✅ Complete | No backend needed |
| `pages/Auth.jsx` | Login/Signup UI | ⚠️ UI Only | **NOT calling API** |
| `pages/Dashboard.jsx` | User dashboard | ⚠️ Mock Data | Hardcoded values |
| `pages/NotFound.jsx` | 404 page | ✅ Complete | No backend needed |
| `context/AuthContext.jsx` | Auth state management | ⚠️ Unused | **NOT integrated** |
| `utils/api.js` | Axios instance | ✅ Complete | Working correctly |
| `main.jsx` | App entry point | ⚠️ Missing | No AuthProvider wrapper |
| `App.jsx` | Routing | ✅ Complete | Basic routes only |

### Backend Architecture Status

#### ✅ JSON API Routes (SPA-Ready)
```
/api/auth/*            - unified_auth_routes.py (NEW)
/api/profile/*         - profile_routes.py
/api/leaderboard/*     - leaderboards_bp
```

#### ❌ Template Routes (OLD - Server-Side Rendered)
```
/legacy/auth/*         - auth_routes.py (legacy SSR)
/legacy/college-auth/* - college_auth_routes.py (legacy SSR + JSON compatibility)
/api/dashboard/*       - dashboard_routes.py (uses render_template)
/api/communities/*     - community_routes.py (uses render_template)
/api/scoring/*         - scoring_routes.py (uses render_template)
/api/personnel/*       - personnel_dashboard_routes.py (uses render_template)
```

---

## 🚨 Critical Issues Identified

### 1. **Legacy Route Families (No Current Prefix Conflict)**

**Current state:** legacy routes are isolated under `/legacy/*`
```python
# In backend/app/__init__.py
app.register_blueprint(unified_auth_routes)  # /api/auth/* canonical JSON auth
app.register_blueprint(auth_routes, url_prefix="/legacy/auth")
app.register_blueprint(college_auth_routes, url_prefix="/legacy/college-auth")
```

**Impact:** no namespace collision, but developers can still accidentally call legacy endpoints from React if not documented clearly.

---

### 2. **Frontend TODOs**

#### Auth.jsx (Line 59)
```jsx
onSubmit={(e) => {
  e.preventDefault()
  // TODO: Connect to API  ← NOT IMPLEMENTED
  navigate('/dashboard')
}}
```

**Impact:** Form submission bypasses authentication entirely.

#### AuthContext.jsx (Line 14)
```jsx
// TODO: Validate token with backend  ← NOT IMPLEMENTED
```

**Impact:** No token validation on app load. Users can't persist login sessions.

---

### 3. **Route Mismatches**

| Frontend Calls | Backend Expects | Status |
|---------------|-----------------|--------|
| `POST /auth/login` | `POST /auth/login` | ✅ Match |
| `POST /auth/register` | `POST /auth/signup` | ❌ **MISMATCH** |
| - | `POST /auth/validate-email` | Missing in frontend |
| - | `POST /auth/check-username` | Missing in frontend |

---

### 4. **Response Structure Mismatches**

#### Frontend Expectation (AuthContext.jsx:24-25)
```javascript
const response = await api.post('/auth/login', { email, password })
const { token, user } = response.data  // Expects flat structure
```

#### Backend Response (unified_auth_service.py:184-200)
```python
return {
    'success': True,
    'user': {...},
    'dashboard_route': '/dashboard',
    'message': 'Welcome back!',
    'token': '...',
    'xp_awarded': 50
}
```

**Status:** ⚠️ **Compatible but needs adjustment**
- Backend returns extra fields (`success`, `message`, `dashboard_route`, `xp_awarded`)
- Frontend only extracts `token` and `user`
- Should handle `success: false` case

---

### 5. **JWT Configuration Inconsistency**

#### Backend Config (app/__init__.py:24)
```python
app.config['JWT_TOKEN_LOCATION'] = ['headers']  # Expects Authorization header
```

#### But Routes Also Set Cookies (unified_auth_routes.py:57-58)
```python
response = jsonify(result)
set_access_cookies(response, result['token'])  # Sets cookie too!
```

#### Frontend (utils/api.js:13)
```javascript
config.headers.Authorization = `Bearer ${token}`  // Uses headers ✅
```

**Status:** ⚠️ **Dual mode** - Backend supports both but config says headers only.

---

### 6. **AuthProvider Not Wrapped**

#### Current main.jsx
```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />  {/* AuthProvider NOT wrapping! */}
    </BrowserRouter>
  </React.StrictMode>,
)
```

**Impact:** `useAuth()` hook will throw error if called. AuthContext is completely unused.

---

### 7. **Dashboard Mock Data**

All data in Dashboard.jsx is hardcoded:
- "Welcome back, John!" (line 28)
- Stats: 12, 47, 2,450, 128 (line 42)
- User initials: "JD" (line 14)

**Required API Calls:**
```javascript
GET /api/profile/           - User profile with stats
GET /api/leaderboard/xp     - Leaderboard data
GET /api/communities/*      - User communities (NOT IMPLEMENTED)
```

---

## 📋 Required Changes - Complete Checklist

### Phase 1: Authentication Foundation (Critical)

#### 1.1 Backend Cleanup
- [ ] **Remove old auth routes** from `app/__init__.py`
  - Delete line 114: `auth_routes` registration
  - Delete line 115: `college_auth_routes` registration
- [ ] **Decide JWT strategy**
  - Option A: Headers only (current config) - Remove `set_access_cookies()` calls
  - Option B: Cookies + Headers - Update config to `['headers', 'cookies']`
  - **Recommendation:** Headers only for SPA architecture

#### 1.2 Frontend - Fix AuthContext Integration
**File:** `frontend/src/main.jsx`
```jsx
import { AuthProvider } from './context/AuthContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
```

#### 1.3 Frontend - Fix Route Mismatch
**File:** `frontend/src/context/AuthContext.jsx` (Line 35)
```javascript
// Change from:
const response = await api.post('/auth/register', { name, email, password })

// To:
const response = await api.post('/auth/signup', {
  email,
  password,
  first_name: name.split(' ')[0],
  last_name: name.split(' ').slice(1).join(' '),
  user_type: 'student',  // Need to add user type selection
  college_id: 1,  // Need to get from email validation
  username: email.split('@')[0]  // Need username field
})
```

**Problem:** This reveals a deeper issue - signup requires more fields!

#### 1.4 Frontend - Connect Auth.jsx to AuthContext
**File:** `frontend/src/pages/Auth.jsx`

Current (lines 55-62):
```jsx
onSubmit={(e) => {
  e.preventDefault()
  // TODO: Connect to API
  navigate('/dashboard')
}}
```

**Required Changes:**
1. Import `useAuth` hook
2. Add form state management
3. Call `login()` or `register()` from context
4. Handle errors and loading states
5. Add email validation flow

---

### Phase 2: Signup Flow Enhancement (High Priority)

#### 2.1 Backend Signup Requirements
```javascript
// Required fields for student signup
{
  email: string,
  password: string,
  first_name: string,
  last_name: string,
  user_type: 'student' | 'personnel',
  college_id: number,
  username: string  // Only for students
}
```

#### 2.2 Frontend - Add Signup Fields to Auth.jsx
**Changes needed:**
- [ ] Split "Full Name" into `first_name` and `last_name`
- [ ] Add `username` field (students only)
- [ ] Add email validation flow
- [ ] Add college detection UI
- [ ] Add user type selection (student/personnel)
- [ ] Add role field (personnel only)

#### 2.3 Frontend - Implement Email Validation Flow
**New functionality needed in Auth.jsx:**

```javascript
const handleEmailBlur = async (email) => {
  const response = await api.post('/auth/validate-email', { email })
  
  if (response.data.valid) {
    // Show detected college
    // Set user_type from response
    // Show/hide fields based on user_type
    setCollegeId(response.data.college_id)
    setUserType(response.data.user_type)
  } else if (response.data.is_registered) {
    // Show "already registered" error
  } else {
    // Show error message
  }
}
```

---

### Phase 3: Dashboard Integration (High Priority)

#### 3.1 Frontend - Replace Mock Data
**File:** `frontend/src/pages/Dashboard.jsx`

**Current issues:**
- Line 28: Hardcoded "John"
- Line 14: Hardcoded "JD"
- Line 42: Hardcoded stats (12, 47, 2450, 128)
- All sections show "will appear here..." placeholders

**Required API Integration:**
```javascript
// In useEffect on mount:
const fetchDashboardData = async () => {
  const profile = await api.get('/profile/')
  const leaderboard = await api.get('/leaderboard/xp')
  // Note: Communities API not yet converted to JSON
  
  setUser(profile.data.profile)
  setStats({
    communities: profile.data.communities_count || 0,
    tasksCompleted: profile.data.tasks_completed || 0,
    xp: profile.data.profile.xp,
    messages: profile.data.messages_count || 0
  })
}
```

#### 3.2 Backend - Dashboard API Missing
**Problem:** `dashboard_routes.py` uses `render_template()`, not JSON.

**Required new route:**
```python
# In profile_routes.py or new dashboard_routes.py
@profile_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    return jsonify({
        'success': True,
        'user': user.get_profile_summary(),
        'stats': {
            'communities_count': ...,
            'tasks_completed': ...,
            'messages_count': ...
        }
    })
```

**OR** extend existing `/api/profile/` endpoint to include dashboard stats.

---

### Phase 4: Protected Routes & Auth State (Medium Priority)

#### 4.1 Frontend - Add Protected Route Component
**New file:** `frontend/src/components/ProtectedRoute.jsx`

```jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div>Loading...</div>  // Or a spinner component
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />
  }
  
  return children
}
```

#### 4.2 Frontend - Update App.jsx Routes
```jsx
import ProtectedRoute from './components/ProtectedRoute'

<Routes>
  <Route path="/" element={<Landing />} />
  <Route path="/auth" element={<Auth />} />
  <Route 
    path="/dashboard" 
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    } 
  />
  <Route path="*" element={<NotFound />} />
</Routes>
```

#### 4.3 Frontend - Token Validation on Mount
**File:** `frontend/src/context/AuthContext.jsx` (Line 10-18)

```javascript
useEffect(() => {
  const token = localStorage.getItem('token')
  if (token) {
    // TODO: Validate token with backend  ← FIX THIS
    validateToken(token)
  } else {
    setLoading(false)
  }
}, [])

const validateToken = async (token) => {
  try {
    const response = await api.get('/profile/')
    setUser(response.data.profile)
  } catch (error) {
    // Token invalid
    localStorage.removeItem('token')
  } finally {
    setLoading(false)
  }
}
```

---

### Phase 5: Remove Old Template-Based Routes (Low Priority - After Full Migration)

#### 5.1 Routes to Delete (After Converting to JSON APIs)
- [ ] `backend/app/routes/auth_routes.py` - OLD student auth
- [ ] `backend/app/routes/college_auth_routes.py` - OLD personnel auth
- [ ] Convert or delete `dashboard_routes.py` (currently uses templates)
- [ ] Convert or delete `community_routes.py` (currently uses templates)
- [ ] Convert or delete `scoring_routes.py` (currently uses templates)
- [ ] Convert or delete `personnel_dashboard_routes.py` (currently uses templates)

#### 5.2 Templates to Delete (After Full Migration)
```
backend/app/templates/                    # Entire directory
backend/app/static/css/
backend/app/static/styles.css
```

**⚠️ Warning:** Do NOT delete these until:
1. All functionality is migrated to React frontend
2. All template routes are converted to JSON APIs
3. Full integration testing is complete

---

## 🗺️ Implementation Roadmap

### Week 1: Core Authentication
**Goal:** Users can actually log in and sign up

#### Day 1-2: Backend Cleanup & Fixes
1. Remove conflicting auth route registrations
2. Decide JWT strategy (headers vs cookies)
3. Test unified auth endpoints with Postman/curl
4. Document actual response structures

#### Day 3-5: Frontend Auth Integration
1. Wrap App with AuthProvider
2. Implement email validation flow in Auth.jsx
3. Add all required signup fields
4. Connect form to AuthContext
5. Add error handling and loading states
6. Fix `/auth/register` → `/auth/signup` mismatch

#### Day 6-7: Testing & Refinement
1. Test full signup flow
2. Test full login flow
3. Test token persistence
4. Test protected routes
5. Fix bugs

---

### Week 2: Dashboard & Profile
**Goal:** Dashboard shows real user data

#### Day 8-10: Dashboard API
1. Create dashboard stats endpoint (or extend profile)
2. Test with real user data
3. Document response structure

#### Day 11-13: Dashboard Frontend
1. Add API calls to Dashboard.jsx
2. Replace all mock data
3. Add loading states
4. Add error handling
5. Create user avatar from initials or profile pic

#### Day 14: Testing & Polish
1. Test dashboard with different user states
2. Add loading skeletons
3. Handle edge cases (no data, errors)

---

### Week 3: Communities & Leaderboard
**Goal:** Additional features integrated

1. Convert community routes to JSON or create new API
2. Integrate leaderboard data
3. Build community list component
4. Build recent activity feed
5. Test full user flow

---

## 📝 Detailed File Changes

### Files to Modify

#### 1. `backend/app/__init__.py`
**Lines 114-115:** Remove old auth route registrations
```python
# DELETE these lines:
app.register_blueprint(auth_routes, url_prefix="/api/auth")
app.register_blueprint(college_auth_routes, url_prefix="<old-college-auth-prefix>")

# KEEP this:
app.register_blueprint(unified_auth_routes)  # Has its own prefix

# Current isolation for legacy SSR:
app.register_blueprint(auth_routes, url_prefix="/legacy/auth")
app.register_blueprint(college_auth_routes, url_prefix="/legacy/college-auth")
```

**Lines 24-26:** Decide JWT strategy
```python
# Current:
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# If keeping cookies too:
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
```

---

#### 2. `frontend/src/main.jsx`
**Complete file rewrite:**
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'  // ADD THIS
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>  {/* ADD THIS */}
        <App />
      </AuthProvider>  {/* ADD THIS */}
    </BrowserRouter>
  </React.StrictMode>,
)
```

---

#### 3. `frontend/src/context/AuthContext.jsx`
**Changes needed:**

**Line 14-18:** Fix token validation
```javascript
// Current:
// TODO: Validate token with backend
setLoading(false)

// Replace with:
validateToken()
  .then((userData) => setUser(userData))
  .catch(() => localStorage.removeItem('token'))
  .finally(() => setLoading(false))
```

**Line 35:** Fix signup endpoint and payload
```javascript
// Current:
const response = await api.post('/auth/register', { name, email, password })

// Replace with proper signup structure:
const register = async (formData) => {
  // formData should include:
  // { email, password, first_name, last_name, username, user_type, college_id }
  try {
    const response = await api.post('/auth/signup', formData)
    
    if (response.data.success) {
      localStorage.setItem('token', response.data.token)
      setUser(response.data.user)
      return { success: true, message: response.data.message }
    }
    
    return { success: false, error: response.data.message }
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.message || 'Registration failed' 
    }
  }
}
```

**Add new function:**
```javascript
const validateToken = async () => {
  const response = await api.get('/profile/')
  return response.data.profile
}
```

**Update provider value:**
```javascript
return (
  <AuthContext.Provider value={{ 
    user, 
    login, 
    register, 
    logout, 
    loading,
    validateToken  // ADD THIS
  }}>
    {children}
  </AuthContext.Provider>
)
```

---

#### 4. `frontend/src/pages/Auth.jsx`
**Major rewrite needed.** Current file is 135 lines, needs to become ~300+ lines.

**Required additions:**
1. Import `useAuth` hook
2. Add state for all form fields
3. Add email validation handler
4. Add username availability check
5. Add college detection UI
6. Add user type handling
7. Add loading states
8. Add error display
9. Replace TODO with actual form submission

**Pseudo-structure:**
```jsx
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'

export default function Auth() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [username, setUsername] = useState('')
  
  // Auto-detected
  const [userType, setUserType] = useState(null)
  const [collegeId, setCollegeId] = useState(null)
  const [collegeName, setCollegeName] = useState(null)
  
  const handleEmailBlur = async () => {
    if (!email) return
    
    try {
      const response = await api.post('/auth/validate-email', { email })
      
      if (response.data.valid) {
        setUserType(response.data.user_type)
        setCollegeId(response.data.college_id)
        setCollegeName(response.data.college_name)
        setError(null)
      } else {
        setError(response.data.error)
      }
    } catch (err) {
      setError('Email validation failed')
    }
  }
  
  const handleUsernameBlur = async () => {
    if (!username || userType !== 'student') return
    
    try {
      const response = await api.post('/auth/check-username', { username })
      
      if (!response.data.available) {
        setError(`Username "${username}" is already taken`)
      } else {
        setError(null)
      }
    } catch (err) {
      // Handle error
    }
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      let result
      
      if (mode === 'login') {
        result = await login(email, password)
      } else {
        result = await register({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          username,
          user_type: userType,
          college_id: collegeId
        })
      }
      
      if (result.success) {
        navigate('/dashboard')
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError('An error occurred')
    } finally {
      setLoading(false)
    }
  }
  
  // ... rest of JSX with actual controlled inputs
}
```

---

#### 5. `frontend/src/pages/Dashboard.jsx`
**Changes needed:**

**Add imports:**
```jsx
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
```

**Add state and data fetching:**
```jsx
export default function Dashboard() {
  const { user, logout } = useAuth()
  const [stats, setStats] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchDashboardData()
  }, [])
  
  const fetchDashboardData = async () => {
    try {
      const [profileRes, leaderboardRes] = await Promise.all([
        api.get('/profile/'),
        api.get('/leaderboard/xp?limit=10')
      ])
      
      setStats({
        communities: 0, // TODO: Get from communities API
        tasksCompleted: profileRes.data.profile.tasks_completed || 0,
        xp: profileRes.data.profile.xp,
        messages: 0 // TODO: Get from messages API
      })
      
      setLeaderboard(leaderboardRes.data.leaderboard)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return <div>Loading...</div>
  }
  
  return (
    // ... existing JSX but replace:
    // - Line 28: "John" → {user?.name}
    // - Line 14: "JD" → {getInitials(user?.name)}
    // - Line 42: Hardcoded values → {stats.communities}, {stats.tasksCompleted}, etc.
  )
}
```

---

#### 6. Create `frontend/src/components/ProtectedRoute.jsx`
**New file:**
```jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-text-secondary">Loading...</p>
        </div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />
  }
  
  return children
}
```

---

#### 7. `frontend/src/App.jsx`
**Changes needed:**

**Add import:**
```jsx
import ProtectedRoute from './components/ProtectedRoute'
```

**Wrap protected routes:**
```jsx
<Routes>
  <Route path="/" element={<Landing />} />
  <Route path="/auth" element={<Auth />} />
  <Route 
    path="/dashboard" 
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    } 
  />
  <Route path="*" element={<NotFound />} />
</Routes>
```

---

## 🧪 Testing Checklist

### Backend Testing (Before Frontend Integration)
- [ ] Test `POST /api/auth/validate-email` with valid student email
- [ ] Test `POST /api/auth/validate-email` with valid personnel email
- [ ] Test `POST /api/auth/validate-email` with already registered email
- [ ] Test `POST /api/auth/validate-email` with invalid domain
- [ ] Test `POST /api/auth/check-username` with available username
- [ ] Test `POST /api/auth/check-username` with taken username
- [ ] Test `POST /api/auth/signup` student flow
- [ ] Test `POST /api/auth/signup` personnel flow
- [ ] Test `POST /api/auth/login` with valid credentials
- [ ] Test `POST /api/auth/login` with invalid credentials
- [ ] Test `GET /api/profile/` with valid JWT token
- [ ] Test `GET /api/profile/` with invalid JWT token
- [ ] Test `GET /api/profile/` with expired JWT token
- [ ] Test `GET /api/leaderboard/xp`

### Frontend Testing (After Integration)
- [ ] Landing page loads correctly
- [ ] Can navigate to /auth
- [ ] Email validation triggers on blur
- [ ] College name displays after validation
- [ ] User type detected correctly (student/personnel)
- [ ] Username field appears for students
- [ ] Role field appears for personnel
- [ ] Username availability check works
- [ ] Login form submits correctly
- [ ] Signup form submits correctly
- [ ] Error messages display correctly
- [ ] Loading states work
- [ ] Redirect to dashboard after successful auth
- [ ] Dashboard protected route redirects if not logged in
- [ ] Dashboard shows real user data
- [ ] Logout works correctly
- [ ] Token persists across page refresh
- [ ] Token validation on app mount works

---

## 📚 API Documentation Quick Reference

### Unified Auth Endpoints (Ready to Use)

#### 1. Validate Email
```http
POST /api/auth/validate-email
Content-Type: application/json

{
  "email": "student@college.edu"
}

# Response (Success):
{
  "valid": true,
  "user_type": "student",
  "college_id": 1,
  "college_name": "Example University",
  "is_registered": false,
  "whitelisted": true,
  "show_role_selector": false
}

# Response (Already Registered):
{
  "valid": false,
  "is_registered": true,
  "error": "Email already registered"
}
```

#### 2. Check Username
```http
POST /api/auth/check-username
Content-Type: application/json

{
  "username": "johndoe"
}

# Response:
{
  "available": true,
  "message": "Username available"
}
```

#### 3. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "student@college.edu",
  "password": "password123"
}

# Response (Success):
{
  "success": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "username": "johndoe",
    "email": "student@college.edu",
    "role": "student",
    "college_name": "Example University",
    "xp": 150,
    "level": 2,
    "streak": 5
  },
  "dashboard_route": "/dashboard",
  "message": "Welcome back! 🔥 5 day streak!",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "xp_awarded": 10
}

# Response (Failed):
{
  "success": false,
  "message": "Invalid email or password"
}
```

#### 4. Signup
```http
POST /api/auth/signup
Content-Type: application/json

# Student Signup:
{
  "email": "newstudent@college.edu",
  "password": "securepass123",
  "first_name": "Jane",
  "last_name": "Smith",
  "username": "janesmith",
  "user_type": "student",
  "college_id": 1
}

# Personnel Signup:
{
  "email": "professor@college.edu",
  "password": "securepass123",
  "first_name": "Dr. John",
  "last_name": "Professor",
  "user_type": "personnel",
  "college_id": 1,
  "role": "Professor",
  "personnel_id": "EMP001"
}

# Response (Success):
{
  "success": true,
  "user": {
    "id": 2,
    "name": "Jane Smith",
    "username": "janesmith",
    "email": "newstudent@college.edu",
    "role": "student",
    "college_name": "Example University"
  },
  "dashboard_route": "/dashboard",
  "message": "Welcome Jane! +50 bonus XP! 🎉",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 5. Get Profile (Protected)
```http
GET /api/profile/
Authorization: Bearer <token>

# Response:
{
  "success": true,
  "profile": {
    "id": 1,
    "name": "John Doe",
    "username": "johndoe",
    "email": "student@college.edu",
    "college_name": "Example University",
    "xp": 150,
    "level": 2,
    "current_streak": 5,
    "max_streak": 10,
    "role": "student"
  },
  "xp_summary": {...},
  "skills": [...],
  "streak": {...}
}
```

#### 6. Get XP Leaderboard
```http
GET /api/leaderboard/xp?limit=10

# Response:
{
  "success": true,
  "leaderboard_type": "xp",
  "total_entries": 10,
  "leaderboard": [
    {
      "rank": 1,
      "user_id": 5,
      "username": "topuser",
      "name": "Top User",
      "xp": 5000,
      "level": 10
    },
    // ... more users
  ]
}
```

---

## 🎯 Success Criteria

### Phase 1 (Authentication) Complete When:
- ✅ User can sign up with email validation
- ✅ User can log in with email/password
- ✅ JWT token stored in localStorage
- ✅ Protected routes redirect to /auth if not logged in
- ✅ User stays logged in after page refresh
- ✅ Logout clears token and redirects to landing

### Phase 2 (Dashboard) Complete When:
- ✅ Dashboard shows actual user name
- ✅ Dashboard shows real XP, level, streak
- ✅ Stats cards show real data
- ✅ Leaderboard shows top users
- ✅ Loading states display during fetch
- ✅ Error states handled gracefully

### Phase 3 (Full Migration) Complete When:
- ✅ All old template routes deleted
- ✅ All old auth routes deleted
- ✅ `backend/app/templates/` directory deleted
- ✅ All features working through React frontend
- ✅ No more `render_template()` calls in codebase

---

## 🚀 Quick Start Commands

### Backend Testing (Use these first!)
```bash
# Navigate to backend
cd F:\MeshWork\backend

# Activate virtual environment (if using)
# .\venv\Scripts\activate

# Test email validation
curl -X POST http://localhost:5000/api/auth/validate-email \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"student@college.edu\"}"

# Test signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@college.edu\",\"password\":\"test123\",\"first_name\":\"Test\",\"last_name\":\"User\",\"username\":\"testuser\",\"user_type\":\"student\",\"college_id\":1}"

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@college.edu\",\"password\":\"test123\"}"
```

### Frontend Development
```bash
# Navigate to frontend
cd F:\MeshWork\frontend

# Install dependencies (if not done)
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

---

## 📞 Decision Points Requiring Input

### 1. JWT Strategy
**Question:** Headers-only or Headers + Cookies?  
**Current State:** Backend sets cookies but config says headers-only  
**Recommendation:** Headers-only (cleaner for SPA)  
**Impact:** Need to remove `set_access_cookies()` from unified_auth_routes.py

### 2. Dashboard Stats API
**Question:** Extend `/api/profile/` or create new `/api/dashboard/stats`?  
**Current State:** dashboard_routes.py uses templates, not JSON  
**Recommendation:** Extend profile endpoint  
**Impact:** Modify profile_routes.py to include dashboard-specific stats

### 3. Communities API
**Question:** Convert existing community_routes.py or create new?  
**Current State:** Uses `render_template()` for all routes  
**Recommendation:** Create new `/api/communities/*` JSON endpoints  
**Impact:** Significant backend work required

### 4. Personnel Dashboard
**Question:** Same frontend or separate app?  
**Current State:** Backend has separate personnel routes  
**Recommendation:** Same React app with role-based routing  
**Impact:** Need to add personnel dashboard pages to frontend

---

## 📅 Estimated Timeline

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: Core Auth | 5-7 days | High |
| Phase 2: Dashboard | 3-5 days | Medium |
| Phase 3: Communities | 5-7 days | High |
| Phase 4: Testing & Polish | 3-5 days | Medium |
| **Total** | **16-24 days** | **~3-4 weeks** |

*Assumes 1 developer working full-time*

---

## 🔗 Related Documents

- `backend/UNIFIED_AUTH_TEST_COMMANDS.md` - Backend testing examples
- `mesh_work_design_system_v_1.md` - Design system reference
- `FRONTEND_AUTH_COMPONENT_STRUCTURE.md` - Original auth design
- `FRONTEND_PAGES_CHECKLIST.md` - Frontend progress tracker

---

## ✅ Next Immediate Actions (Priority Order)

1. **Backend:** Remove conflicting route registrations in `app/__init__.py`
2. **Backend:** Test all unified_auth endpoints with curl/Postman
3. **Backend:** Decide and implement JWT strategy (headers vs cookies)
4. **Frontend:** Wrap App with AuthProvider in `main.jsx`
5. **Frontend:** Start implementing email validation in Auth.jsx
6. **Frontend:** Fix signup endpoint mismatch and add all required fields
7. **Frontend:** Connect auth form to AuthContext
8. **Frontend:** Test complete auth flow
9. **Frontend:** Implement token validation on mount
10. **Frontend:** Integrate real data in Dashboard.jsx

---

**Document Version:** 1.0  
**Last Updated:** February 18, 2026  
**Status:** Ready for Implementation
