# Frontend Component Structure - Unified Auth

## Component Architecture

### Main Component: `Auth.jsx`

```
Auth (Container)
├── AuthHeader (Title + Mode Toggle)
├── EmailValidationBadge (Real-time feedback)
├── LoginForm (mode === 'login')
│   ├── EmailInput (with onBlur validation)
│   ├── PasswordInput
│   └── SubmitButton
└── SignupForm (mode === 'register')
    ├── EmailInput (with onBlur validation)
    ├── DynamicFields (based on userType)
    │   ├── StudentFields
    │   │   ├── UsernameInput
    │   │   ├── FirstNameInput
    │   │   ├── LastNameInput
    │   │   └── PasswordInput
    │   └── PersonnelFields
    │       ├── FirstNameInput
    │       ├── LastNameInput
    │       ├── RoleSelector
    │       ├── PersonnelIDInput (optional)
    │       └── PasswordInput
    └── SubmitButton
```

---

## State Management

```javascript
// Component State
const [mode, setMode] = useState('login') // 'login' | 'register'
const [userType, setUserType] = useState(null) // null | 'student' | 'personnel'
const [emailValidation, setEmailValidation] = useState(null)
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

// Form Data State
const [formData, setFormData] = useState({
  email: '',
  password: '',
  // Student fields
  username: '',
  first_name: '',
  last_name: '',
  // Personnel fields
  role: '',
  personnel_id: ''
})

// Email Validation State Shape
emailValidation = {
  valid: true,
  user_type: 'student',
  college_id: 1,
  college_name: 'Example College',
  detected_role: null,
  is_registered: false,
  whitelisted: true,
  show_role_selector: false
}
```

---

## API Integration

### 1. Email Validation (onBlur)

```javascript
const validateEmail = async (email) => {
  setLoading(true)
  try {
    const response = await fetch('/api/auth/validate-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    })
    
    const data = await response.json()
    
    if (data.valid) {
      setEmailValidation(data)
      setUserType(data.user_type)
      setError(null)
    } else {
      setError(data.error)
      setEmailValidation(null)
      setUserType(null)
    }
  } catch (err) {
    setError('Failed to validate email')
  } finally {
    setLoading(false)
  }
}

// Debounced version
const debouncedValidateEmail = useMemo(
  () => debounce(validateEmail, 300),
  []
)
```

### 2. Unified Login

```javascript
const handleLogin = async (e) => {
  e.preventDefault()
  setLoading(true)
  
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.email,
        password: formData.password
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      // Store token if needed
      // Navigate to dashboard
      navigate(data.dashboard_route)
    } else {
      setError(data.message)
    }
  } catch (err) {
    setError('Login failed. Please try again.')
  } finally {
    setLoading(false)
  }
}
```

### 3. Unified Signup

```javascript
const handleSignup = async (e) => {
  e.preventDefault()
  setLoading(true)
  
  const signupData = {
    user_type: userType,
    email: formData.email,
    password: formData.password,
    first_name: formData.first_name,
    last_name: formData.last_name,
    college_id: emailValidation.college_id
  }
  
  // Add type-specific fields
  if (userType === 'student') {
    signupData.username = formData.username
  } else if (userType === 'personnel') {
    signupData.role = formData.role
    if (formData.personnel_id) {
      signupData.personnel_id = formData.personnel_id
    }
  }
  
  try {
    const response = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signupData)
    })
    
    const data = await response.json()
    
    if (data.success) {
      navigate(data.dashboard_route)
    } else {
      setError(data.message)
    }
  } catch (err) {
    setError('Signup failed. Please try again.')
  } finally {
    setLoading(false)
  }
}
```

---

## Component Breakdown

### EmailValidationBadge Component

```jsx
const EmailValidationBadge = ({ validation, loading }) => {
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-2 text-sm text-text-secondary"
      >
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Validating...</span>
      </motion.div>
    )
  }
  
  if (!validation) return null
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 p-3 rounded-lg bg-accent-soft border border-accent-primary/20"
    >
      <CheckCircle className="w-5 h-5 text-accent-primary" />
      <div>
        <p className="text-sm font-medium text-text-primary">
          {validation.college_name}
        </p>
        <p className="text-xs text-text-secondary">
          {validation.user_type === 'student' ? 'Student Account' : 'Faculty/Staff Account'}
        </p>
      </div>
    </motion.div>
  )
}
```

### DynamicFields Component

```jsx
const DynamicFields = ({ userType, formData, onChange }) => {
  if (!userType) return null
  
  return (
    <AnimatePresence mode="wait">
      {userType === 'student' && (
        <motion.div
          key="student-fields"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="space-y-4"
        >
          <InputField
            label="Username"
            icon={AtSign}
            value={formData.username}
            onChange={(e) => onChange('username', e.target.value)}
            placeholder="johndoe"
            required
          />
          <InputField
            label="First Name"
            icon={User}
            value={formData.first_name}
            onChange={(e) => onChange('first_name', e.target.value)}
            placeholder="John"
            required
          />
          <InputField
            label="Last Name"
            icon={User}
            value={formData.last_name}
            onChange={(e) => onChange('last_name', e.target.value)}
            placeholder="Doe"
            required
          />
        </motion.div>
      )}
      
      {userType === 'personnel' && (
        <motion.div
          key="personnel-fields"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="space-y-4"
        >
          <InputField
            label="First Name"
            icon={User}
            value={formData.first_name}
            onChange={(e) => onChange('first_name', e.target.value)}
            placeholder="Jane"
            required
          />
          <InputField
            label="Last Name"
            icon={User}
            value={formData.last_name}
            onChange={(e) => onChange('last_name', e.target.value)}
            placeholder="Smith"
            required
          />
          <RoleSelector
            value={formData.role}
            onChange={(value) => onChange('role', value)}
            required
          />
          <InputField
            label="Personnel ID (Optional)"
            icon={Hash}
            value={formData.personnel_id}
            onChange={(e) => onChange('personnel_id', e.target.value)}
            placeholder="FAC001"
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

### RoleSelector Component

```jsx
const RoleSelector = ({ value, onChange, required }) => {
  const roles = [
    { value: 'faculty', label: 'Faculty', description: 'Professor, Lecturer' },
    { value: 'hod', label: 'HOD', description: 'Head of Department' },
    { value: 'staff', label: 'Staff', description: 'Administrative Staff' },
    { value: 'assistant', label: 'Assistant', description: 'Teaching/Lab Assistant' },
    { value: 'coordinator', label: 'Coordinator', description: 'Event/Program Coordinator' }
  ]
  
  return (
    <div>
      <label className="label">Role</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className="input"
      >
        <option value="">Select your role</option>
        {roles.map(role => (
          <option key={role.value} value={role.value}>
            {role.label} - {role.description}
          </option>
        ))}
      </select>
    </div>
  )
}
```

---

## Animation Specifications

### Title Animation (Mode Switch)

```jsx
<AnimatePresence mode="wait">
  <motion.h2
    key={mode}
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 10 }}
    transition={{ duration: 0.3 }}
    className="text-heading-2 mb-2"
  >
    {mode === 'login' ? 'Welcome Back' : 'Create Account'}
  </motion.h2>
</AnimatePresence>
```

### Form Fields Expansion

```jsx
<motion.div
  layout
  initial={{ opacity: 0, height: 0 }}
  animate={{ opacity: 1, height: 'auto' }}
  exit={{ opacity: 0, height: 0 }}
  transition={{ 
    duration: 0.35,
    ease: [0.4, 0.0, 0.2, 1]
  }}
>
  {/* Fields */}
</motion.div>
```

### Button Hover Effect (CSS)

```css
.btn-primary {
  border-radius: 12px;
  transition: all 250ms cubic-bezier(0.4, 0.0, 0.2, 1);
}

.btn-primary:hover {
  border-radius: 999px;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: scale(0.97);
}
```

---

## Design System Styling

### Card Container

```jsx
<div className="w-full max-w-md bg-bg-surface border border-border-subtle rounded-[14px] p-8 shadow-[0_4px_24px_rgba(0,0,0,0.25)]">
  {/* Content */}
</div>
```

### Input Field

```jsx
<div className="relative">
  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
  <input
    type="email"
    className="w-full pl-11 pr-4 py-3 bg-bg-surface-elevated border border-border-subtle rounded-[12px] text-text-primary placeholder:text-text-muted focus:border-accent-primary focus:ring focus:ring-accent-primary/20 transition-all"
    placeholder="you@college.edu"
  />
</div>
```

### Primary Button

```jsx
<button
  type="submit"
  disabled={loading}
  className="btn-primary w-full px-6 py-3 bg-accent-primary hover:bg-accent-hover text-white font-medium rounded-[12px] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
>
  {loading ? (
    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
  ) : (
    mode === 'login' ? 'Sign In' : 'Create Account'
  )}
</button>
```

---

## Error Handling

### Display Errors

```jsx
{error && (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    className="p-3 rounded-lg bg-error-500/10 border border-error-500/20 text-error-500 text-sm"
  >
    <div className="flex items-start gap-2">
      <AlertCircle className="w-4 h-4 mt-0.5" />
      <p>{error}</p>
    </div>
  </motion.div>
)}
```

---

## Responsive Design

```jsx
<div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-surface to-accent-primary/5 flex items-center justify-center p-6">
  {/* Back Button */}
  <Link
    to="/"
    className="absolute top-6 left-6 inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
  >
    <ArrowLeft className="w-4 h-4" />
    <span className="text-sm font-medium hidden sm:inline">Back to Home</span>
  </Link>
  
  {/* Auth Card */}
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="w-full max-w-md"
  >
    {/* Content */}
  </motion.div>
</div>
```

---

## Accessibility

```jsx
// Form labels
<label htmlFor="email" className="label">
  Email Address
</label>
<input
  id="email"
  name="email"
  type="email"
  aria-required="true"
  aria-invalid={error ? 'true' : 'false'}
  aria-describedby={error ? 'email-error' : undefined}
/>
{error && (
  <p id="email-error" role="alert" className="text-error-500 text-sm mt-1">
    {error}
  </p>
)}

// Loading states
<button
  disabled={loading}
  aria-busy={loading}
  aria-label={loading ? 'Signing in...' : 'Sign in'}
>
  {loading ? 'Signing in...' : 'Sign In'}
</button>
```

---

## Testing Checklist

### UI Tests
- [ ] Email validation triggers on blur
- [ ] Correct fields shown for student vs personnel
- [ ] Mode toggle works (login ↔ register)
- [ ] Animations are smooth and don't jump
- [ ] Error messages display correctly
- [ ] Loading states work
- [ ] Form validation works

### Integration Tests
- [ ] Student signup flow end-to-end
- [ ] Personnel signup flow end-to-end
- [ ] Student login flow
- [ ] Personnel login flow
- [ ] Invalid email handling
- [ ] Duplicate email handling
- [ ] Weak password handling

### Accessibility Tests
- [ ] Keyboard navigation works
- [ ] Screen reader announces states
- [ ] Focus management is correct
- [ ] Error messages are linked to inputs
- [ ] All interactive elements are focusable

---

## File Structure

```
frontend/src/
├── pages/
│   └── Auth.jsx (main component)
├── components/
│   └── auth/
│       ├── EmailValidationBadge.jsx
│       ├── DynamicFields.jsx
│       ├── RoleSelector.jsx
│       └── InputField.jsx
├── hooks/
│   └── useAuth.js (auth logic hook)
├── services/
│   └── authService.js (API calls)
└── utils/
    └── validation.js (client-side validation)
```

---

## Icons Required (lucide-react)

```javascript
import {
  LogIn,
  UserPlus,
  Mail,
  Lock,
  User,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Loader2,
  AtSign,
  Hash
} from 'lucide-react'
```

---

## Next Steps

1. Implement backend endpoints first
2. Test endpoints with Postman/Thunder Client
3. Build frontend component structure
4. Integrate API calls
5. Add animations
6. Test full flow
7. Add error handling
8. Accessibility audit
9. Performance optimization
10. Documentation
