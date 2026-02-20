# 🧪 COMPREHENSIVE TESTING INSTRUCTIONS
## Enhanced Authentication System - MeshWork

**Last Updated:** February 10, 2026  
**Version:** 2.0  
**Tested On:** Flask 2.3.x, Python 3.11+

> ⚠️ Route Migration Note
> 
> Legacy SSR auth pages are mounted under `/legacy/*`:
> - `/legacy/auth/*`
> - `/legacy/college-auth/*`
> 
> Unified JSON auth for React remains under `/api/auth/*`.

---

## 📋 TABLE OF CONTENTS

1. [Pre-Testing Setup](#pre-testing-setup)
2. [Critical Path Testing](#critical-path-testing)
3. [Navigation Testing](#navigation-testing)
4. [Authentication Flow Testing](#authentication-flow-testing)
5. [Personnel Management Testing](#personnel-management-testing)
6. [Student Registration Testing](#student-registration-testing)
7. [Edge Cases & Error Handling](#edge-cases--error-handling)
8. [Security Testing](#security-testing)
9. [Performance Testing](#performance-testing)
10. [Browser Compatibility](#browser-compatibility)
11. [Regression Testing](#regression-testing)
12. [Test Data Reference](#test-data-reference)

---

## 🚀 PRE-TESTING SETUP

### 1. Environment Check

```powershell
# Activate virtual environment
F:/MeshWork/venv/Scripts/Activate.ps1

# Verify Flask is running
cd F:\MeshWork\backend
$env:FLASK_APP="run.py"
flask run --host=0.0.0.0 --port=5000
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### 2. Database Verification

```powershell
# Check database migration status
flask db current

# Expected: 9b69ae95562e (enhanced_auth_system)
```

### 3. Demo Data Setup

```powershell
# Run demo data setup script
python setup_demo_data.py
```

**Expected Output:**
```
✓ College created/updated: MIT India
✓ Personnel created: HOD (hod001-hod@mitindia.edu)
✓ Whitelist populated: 5 student emails
✓ Demo data setup complete!
```

### 4. Clear Browser Data

- Clear cookies for localhost:5000
- Clear localStorage
- Open Incognito/Private window (recommended)

---

## 🎯 CRITICAL PATH TESTING

### Test Suite 1: New User Journey (MUST PASS)

#### Test 1.1: Landing Page Access
**Priority:** CRITICAL

1. Navigate to `http://localhost:5000/`
2. Verify page loads without errors

**Expected Results:**
- ✅ Page displays "Welcome to MeshWork"
- ✅ Three cards visible: Students, Personnel, Colleges
- ✅ Navigation bar shows: Home, Login (dropdown), Signup
- ✅ No JavaScript console errors

**Pass/Fail Criteria:**
- ALL expected results must be true
- Page load time < 2 seconds

---

#### Test 1.2: Personnel Login Navigation
**Priority:** CRITICAL

1. From landing page, click navigation bar "Login" dropdown
2. Verify "Personnel Login" option is visible
3. Click "Personnel Login"

**Expected Results:**
- ✅ Redirects to `/login/personnel`
- ✅ Form displays: Email, Password fields
- ✅ Header shows "College Personnel Login"
- ✅ Subtext: "For HODs, Faculty, Staff, and Administrators"
- ✅ Cross-links visible: "Student Login", "College Login"

**Pass/Fail Criteria:**
- ALL links functional
- No 404 errors
- Form renders correctly

---

#### Test 1.3: Personnel Login Success
**Priority:** CRITICAL

**Test Data:**
- Email: `hod001-hod@mitindia.edu`
- Password: `hod123`

**Steps:**
1. Enter test credentials
2. Click "Login" button
3. Observe redirect and flash message

**Expected Results:**
- ✅ Redirects to `/personnel/dashboard` (NOT `/dashboard/college`)
- ✅ Flash message: "Welcome [Name]! Logged in as [Role]."
- ✅ Dashboard loads successfully
- ✅ Navigation bar shows: Dashboard, Students, Whitelist, Profile, Logout
- ✅ Statistics cards display: Total, Registered, Pending, Rate
- ✅ "Quick Stats" section shows whitelist data

**Pass/Fail Criteria:**
- Login completes in < 3 seconds
- NO redirect to college login page
- JWT cookie set (check DevTools → Application → Cookies)
- Dashboard displays without errors

**CRITICAL BUG CHECK:**
- ❌ FAIL if redirected to "/login/college" after login
- ❌ FAIL if shows "Access denied" message
- ❌ FAIL if JWT cookie not set

---

#### Test 1.4: Personnel Dashboard Navigation
**Priority:** HIGH

**Precondition:** Logged in as personnel (Test 1.3)

**Steps:**
1. Click "Students" in navigation bar
2. Verify students page loads
3. Click "Whitelist" in navigation bar
4. Verify whitelist page loads
5. Click "Dashboard" in navigation bar
6. Verify dashboard reloads

**Expected Results:**
- ✅ All navigation links functional
- ✅ Each page loads without errors
- ✅ Navigation bar persists on all pages
- ✅ Active page highlighted in nav (optional)
- ✅ No 404 errors

**Pass/Fail Criteria:**
- ALL navigation links work
- Page load time < 2 seconds per page
- User remains authenticated

---

#### Test 1.5: Personnel Logout
**Priority:** HIGH

**Precondition:** Logged in as personnel

**Steps:**
1. Click "Logout" button in navigation bar
2. Observe redirect and flash message

**Expected Results:**
- ✅ Redirects to `/` (landing page)
- ✅ Flash message: "Logged out successfully."
- ✅ JWT cookie cleared
- ✅ Navigation bar shows public menu (Home, Login, Signup)

**Pass/Fail Criteria:**
- Cannot access `/personnel/dashboard` after logout (redirects to login)
- JWT cookie removed (check DevTools)

---

#### Test 1.6: Whitelist Management - Add Single Email
**Priority:** CRITICAL

**Precondition:** Logged in as personnel

**Steps:**
1. Navigate to `/personnel/whitelist`
2. Fill "Add Single Email" form:
   - Email: `2024010@mitindia.edu`
   - Enrollment: `2024010`
   - Name: `Test Student`
3. Click "Add Email"

**Expected Results:**
- ✅ Flash message: "Email added to whitelist successfully."
- ✅ Email appears in whitelist table
- ✅ Status badge: "Pending" (orange)
- ✅ Stats updated: Total count +1

**Pass/Fail Criteria:**
- Email saved to database
- No duplicate entries allowed
- Form validation works

---

#### Test 1.7: Student Signup with Whitelisted Email
**Priority:** CRITICAL

**Precondition:** Email `2024001@mitindia.edu` is whitelisted

**Steps:**
1. Logout personnel
2. Navigate to `/signup/user`
3. Fill form:
   - First Name: `Amit`
   - Last Name: `Sharma`
   - Username: `amitkumar` (type slowly to trigger availability check)
   - Email: `2024001@mitindia.edu`
   - Password: `password123`
   - Confirm Password: `password123`
4. Observe live validation feedback
5. Submit form

**Expected Results:**
- ✅ Username availability shows ✓ "Available" (green)
- ✅ College auto-detected: "MIT India" or similar
- ✅ Email validation: ✓ "Email is whitelisted" (green)
- ✅ Form submits successfully
- ✅ Flash message includes welcome + XP bonus
- ✅ Redirects to questionnaire or dashboard

**Pass/Fail Criteria:**
- AJAX validation works (500ms debounce)
- Cannot signup with non-whitelisted email
- Username uniqueness enforced

---

#### Test 1.8: Verify Registration in Personnel Dashboard
**Priority:** HIGH

**Precondition:** Student registered in Test 1.7

**Steps:**
1. Login as personnel (`hod001-hod@mitindia.edu`)
2. Navigate to `/personnel/whitelist`
3. Find entry for `2024001@mitindia.edu`

**Expected Results:**
- ✅ Status badge changed to "Registered" (green)
- ✅ Dashboard stats updated: Registered count +1, Pending count -1
- ✅ Registration timestamp recorded

**Pass/Fail Criteria:**
- Whitelist entry marked as registered
- Stats calculation accurate

---

## 🧭 NAVIGATION TESTING

### Test Suite 2: Cross-Navigation Testing

#### Test 2.1: Public Navigation Menu
**Priority:** HIGH

**Precondition:** Not logged in

**Steps:**
1. Navigate to `/`
2. Check navigation bar

**Expected Results:**
- ✅ Brand logo/text: "MeshWork" links to `/`
- ✅ "Home" link present
- ✅ "Login" dropdown with 3 options:
  - Student Login → `/login/user`
  - Personnel Login → `/login/personnel`
  - College Login → `/login/college`
- ✅ "Signup" link → `/signup/user`

**Test Each Link:**
| Link | Expected URL | Status |
|------|--------------|--------|
| MeshWork (brand) | `/` | [ ] |
| Home | `/` | [ ] |
| Student Login | `/login/user` | [ ] |
| Personnel Login | `/login/personnel` | [ ] |
| College Login | `/login/college` | [ ] |
| Signup | `/signup/user` | [ ] |

---

#### Test 2.2: Student Navigation (Authenticated)
**Priority:** MEDIUM

**Precondition:** Logged in as student

**Steps:**
1. Login as student
2. Verify navigation bar

**Expected Results:**
- ✅ Dashboard link
- ✅ Profile link
- ✅ Communities link
- ✅ Logout button (styled differently)

**Pass/Fail:** All links functional, logout works

---

#### Test 2.3: Personnel Navigation (Authenticated)
**Priority:** HIGH

**Precondition:** Logged in as personnel

**Expected Results:**
- ✅ Dashboard link → `/personnel/dashboard`
- ✅ Students link → `/personnel/students`
- ✅ Whitelist link → `/personnel/whitelist`
- ✅ Profile link → `/personnel/profile`
- ✅ Logout button → `/logout/personnel`

**Pass/Fail:** All links functional, correct URLs

---

#### Test 2.4: College Navigation (Authenticated)
**Priority:** LOW

**Precondition:** Logged in as college

**Expected Results:**
- ✅ Dashboard link → `/dashboard/college`
- ✅ Logout button → `/logout/college`

---

#### Test 2.5: Login Page Cross-Links
**Priority:** MEDIUM

**Test all login pages have cross-links:**

**Student Login Page (`/login/user`):**
- ✅ Link to signup: `/signup/user`
- ✅ "Personnel Login" button → `/login/personnel`
- ✅ "College Login" button → `/login/college`

**Personnel Login Page (`/login/personnel`):**
- ✅ "Student Login" button → `/login/user`
- ✅ "College Login" button → `/login/college`

**College Login Page (`/login/college`):**
- ✅ Link to signup: `/signup/college`
- ✅ "Student Login" button → `/login/user`
- ✅ "Personnel Login" button → `/login/personnel`

---

## 🔐 AUTHENTICATION FLOW TESTING

### Test Suite 3: Login/Logout Flows

#### Test 3.1: Personnel Login - Invalid Credentials
**Priority:** HIGH

**Test Cases:**

| Email | Password | Expected Result |
|-------|----------|-----------------|
| `hod001-hod@mitindia.edu` | `wrongpass` | "Invalid email or password." |
| `nonexistent@mit.edu` | `hod123` | "Invalid email or password." |
| `` (empty) | `hod123` | "Email and password are required." |
| `hod001-hod@mitindia.edu` | `` (empty) | "Email and password are required." |

**Pass/Fail:** Proper error messages, no server errors

---

#### Test 3.2: Personnel Login - Inactive Account
**Priority:** MEDIUM

**Precondition:** Create inactive personnel account

**Steps:**
1. Set `is_active = false` for test personnel
2. Attempt login

**Expected Result:**
- ✅ Error: "Invalid or inactive personnel account."
- ✅ Redirect to login page

---

#### Test 3.3: JWT Session Persistence
**Priority:** HIGH

**Steps:**
1. Login as personnel
2. Navigate to `/personnel/students`
3. Copy URL
4. Close browser
5. Open new browser window
6. Paste URL (if JWT stored as cookie)

**Expected Results:**
- ✅ If cookie exists and valid: Page loads directly
- ✅ If cookie expired/missing: Redirects to `/login/personnel`

**Pass/Fail:** JWT validation works correctly

---

#### Test 3.4: Multiple Role Login (Session Isolation)
**Priority:** MEDIUM

**Steps:**
1. Login as personnel in Browser A
2. Login as student in Browser B (Incognito)
3. Verify both sessions work independently

**Expected Results:**
- ✅ Browser A can access `/personnel/dashboard`
- ✅ Browser B can access `/dashboard`
- ✅ Neither can access each other's routes

---

#### Test 3.5: Logout Clears JWT for All Roles
**Priority:** HIGH

**Test each role:**
1. Login as [role]
2. Click logout
3. Attempt to access protected route directly

**Test Matrix:**

| Role | Login URL | Protected Route | Logout URL | Should Redirect To |
|------|-----------|-----------------|------------|-------------------|
| Student | `/login/user` | `/dashboard` | `/logout/user` | `/login/user` |
| Personnel | `/login/personnel` | `/personnel/dashboard` | `/logout/personnel` | `/login/personnel` |
| College | `/login/college` | `/dashboard/college` | `/logout/college` | `/login/college` |

---

## 👥 PERSONNEL MANAGEMENT TESTING

### Test Suite 4: Whitelist Operations

#### Test 4.1: Add Single Email - Valid Data
**Priority:** HIGH

**Test Cases:**

| Email | Enrollment | Name | Expected |
|-------|------------|------|----------|
| `2024020@mitindia.edu` | `2024020` | `Valid Student` | ✓ Success |
| `2024021@mitindia.edu` | `` | `No Enrollment` | ✓ Success (optional field) |
| `new.student@mitindia.edu` | `2024022` | `Dot Email` | ✓ Success |

**Verification:**
- Entry appears in whitelist table
- Status: "Pending"
- Stats updated

---

#### Test 4.2: Add Single Email - Invalid Data
**Priority:** HIGH

**Test Cases:**

| Email | Expected Error |
|-------|----------------|
| `invalid-email` | "Invalid email format" |
| `student@wrongdomain.com` | "Email must be from college domain" |
| `` (empty) | "Email is required" |
| `2024020@mitindia.edu` (duplicate) | "Email already whitelisted" |

---

#### Test 4.3: Bulk Upload CSV - Valid File
**Priority:** HIGH

**Prepare CSV File:** `test_bulk.csv`
```csv
email,enrollment,name
2024030@mitindia.edu,2024030,Bulk Student 1
2024031@mitindia.edu,2024031,Bulk Student 2
2024032@mitindia.edu,2024032,Bulk Student 3
```

**Steps:**
1. Navigate to `/personnel/whitelist`
2. Choose file: `test_bulk.csv`
3. Click "Upload CSV"

**Expected Results:**
- ✅ Flash message: "Successfully added X emails to whitelist."
- ✅ All 3 emails appear in table
- ✅ Stats updated: Total +3

---

#### Test 4.4: Bulk Upload CSV - Invalid File
**Priority:** MEDIUM

**Test Cases:**

| File Content | Expected Error |
|--------------|----------------|
| Missing header row | "Invalid CSV format" |
| Wrong headers | "CSV must have 'email' column" |
| Empty file | "No data in CSV" |
| Duplicate emails | "X duplicates skipped" |
| Mixed valid/invalid | "Added X, skipped Y invalid" |

---

#### Test 4.5: Remove Email from Whitelist
**Priority:** HIGH

**Precondition:** Whitelist contains unregistered email

**Steps:**
1. Navigate to `/personnel/whitelist`
2. Find entry with "Pending" status
3. Click "Remove" button
4. Confirm in alert dialog

**Expected Results:**
- ✅ Entry removed from table
- ✅ Flash message: "Email removed from whitelist."
- ✅ Stats updated: Total -1, Pending -1

**Restriction Test:**
- ❌ Registered emails should NOT have "Remove" button

---

#### Test 4.6: Filter Whitelist - Pending Only
**Priority:** MEDIUM

**Steps:**
1. Navigate to `/personnel/whitelist`
2. Click "Pending Only" filter button

**Expected Results:**
- ✅ Only "Pending" (orange) entries shown
- ✅ "Registered" (green) entries hidden
- ✅ Stats still show total count
- ✅ Button highlighted/active

---

#### Test 4.7: Filter Whitelist - Show All
**Priority:** MEDIUM

**Steps:**
1. With "Pending Only" filter active
2. Click "Show All" button

**Expected Results:**
- ✅ All entries visible (Pending + Registered)
- ✅ "Show All" button highlighted/active

---

#### Test 4.8: View Students List
**Priority:** HIGH

**Precondition:** At least 1 student registered

**Steps:**
1. Navigate to `/personnel/students`

**Expected Results:**
- ✅ Table displays: Name, Username, Email, Level, XP, Joined
- ✅ All registered students visible
- ✅ "Back to Dashboard" link works
- ✅ Stats show: "Total Students: X"

---

#### Test 4.9: Personnel Dashboard Statistics
**Priority:** MEDIUM

**Verification:**

**Manual Calculation:**
1. Count whitelisted emails: `SELECT COUNT(*) FROM whitelisted_emails WHERE college_id = X`
2. Count registered: `SELECT COUNT(*) FROM whitelisted_emails WHERE is_registered = true`
3. Calculate pending: Total - Registered
4. Calculate rate: (Registered / Total) * 100

**Dashboard Display:**
- ✅ Total matches count
- ✅ Registered matches count
- ✅ Pending = Total - Registered
- ✅ Registration Rate formula correct

---

## 🎓 STUDENT REGISTRATION TESTING

### Test Suite 5: Student Signup Flow

#### Test 5.1: Live Username Availability Check
**Priority:** HIGH

**Steps:**
1. Navigate to `/signup/user`
2. Type username slowly (trigger debounce)
3. Observe feedback messages

**Test Cases:**

| Username | Expected Feedback | Color |
|----------|-------------------|-------|
| (New unique) | "✓ Username is available" | Green |
| (Existing in DB) | "✗ Username already taken" | Red |
| `ab` (< 3 chars) | "Username too short" | Red |
| `user@name` (special chars) | "Invalid characters" | Red |

**Performance Check:**
- AJAX request delay: 500ms after typing stops
- Response time: < 1 second

---

#### Test 5.2: College Auto-Detection from Email
**Priority:** HIGH

**Steps:**
1. Navigate to `/signup/user`
2. Enter email matching college domain
3. Observe college field auto-fill

**Test Cases:**

| Email | Expected College | Status |
|-------|------------------|--------|
| `test@mitindia.edu` | "MIT India" | Auto-detected |
| `test@unknowndomain.com` | (Empty or error) | Not found |

**API Endpoint Test:**
```bash
curl -X POST http://localhost:5000/api/detect-college \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mitindia.edu"}'
```

**Expected Response:**
```json
{
  "found": true,
  "college_id": 1,
  "college_name": "MIT India"
}
```

---

#### Test 5.3: Email Whitelist Validation
**Priority:** CRITICAL

**Test Cases:**

| Email | Whitelisted? | Expected Behavior |
|-------|--------------|-------------------|
| `2024001@mitindia.edu` | Yes | ✓ Signup allowed |
| `notwhitelisted@mitindia.edu` | No | ✗ Error: "Email not whitelisted" |
| `student@wrongdomain.com` | No | ✗ Error: "Invalid college domain" |

---

#### Test 5.4: Password Validation
**Priority:** MEDIUM

**Test Cases:**

| Password | Confirm | Expected |
|----------|---------|----------|
| `password123` | `password123` | ✓ Match |
| `pass` | `pass` | ✗ Too short (if min length set) |
| `password123` | `password321` | ✗ Passwords don't match |

---

#### Test 5.5: Complete Signup Flow (Success)
**Priority:** CRITICAL

**Full End-to-End Test:**

**Preparation:**
1. Ensure email is whitelisted: `2024002@mitindia.edu`

**Steps:**
1. Navigate to `/signup/user`
2. Fill form:
   - First Name: `Priya`
   - Last Name: `Patel`
   - Username: `priyap2024` (check availability)
   - Email: `2024002@mitindia.edu`
   - Password: `securepass123`
   - Confirm Password: `securepass123`
3. Submit form

**Expected Results:**
- ✅ Flash message: Welcome message with XP bonus
- ✅ User created in database
- ✅ Whitelist entry marked as registered
- ✅ Redirects to questionnaire or dashboard
- ✅ Auto-login with JWT

**Database Verification:**
```sql
SELECT * FROM users WHERE email = '2024002@mitindia.edu';
-- Should return 1 row

SELECT is_registered FROM whitelisted_emails WHERE email = '2024002@mitindia.edu';
-- Should return: true
```

---

#### Test 5.6: Duplicate Username Prevention
**Priority:** HIGH

**Steps:**
1. Attempt signup with username that exists
2. Submit form

**Expected:**
- ✗ Error: "Username already taken"
- No database entry created

---

#### Test 5.7: Duplicate Email Prevention
**Priority:** HIGH

**Steps:**
1. Attempt signup with already registered email
2. Submit form

**Expected:**
- ✗ Error: "Email already registered"
- No duplicate user created

---

## 🐛 EDGE CASES & ERROR HANDLING

### Test Suite 6: Edge Cases

#### Test 6.1: Direct URL Access (Unauthorized)
**Priority:** HIGH

**Test Matrix:**

| URL | When Logged Out | Expected |
|-----|-----------------|----------|
| `/personnel/dashboard` | Not authenticated | Redirect to `/login/personnel` |
| `/personnel/students` | Not authenticated | Redirect to `/login/personnel` |
| `/personnel/whitelist` | Not authenticated | Redirect to `/login/personnel` |
| `/dashboard` | Not authenticated | Redirect to `/login/user` |
| `/dashboard/college` | Not authenticated | Redirect to `/login/college` |

**Pass/Fail:** All protected routes redirect properly

---

#### Test 6.2: Cross-Role Access Attempts
**Priority:** HIGH

**Scenario: Student tries to access personnel routes**

**Steps:**
1. Login as student
2. Navigate to `/personnel/dashboard` directly

**Expected:**
- ✗ Flash message: "Access denied. Personnel login required."
- Redirect to `/login/personnel`

**Test all combinations:**

| Logged In As | Accessing | Should |
|--------------|-----------|--------|
| Student | `/personnel/*` | Deny |
| Student | `/dashboard/college` | Deny |
| Personnel | `/dashboard` (student) | Allow (or deny based on policy) |
| College | `/personnel/*` | Deny |

---

#### Test 6.3: Expired JWT Handling
**Priority:** MEDIUM

**Steps:**
1. Login as personnel
2. Manually set JWT expiration (or wait for expiration)
3. Attempt to access `/personnel/dashboard`

**Expected:**
- ✗ Flash message: "Your session has expired. Please log in again."
- Redirect to login page
- JWT cookie cleared

---

#### Test 6.4: Special Characters in Input Fields
**Priority:** MEDIUM

**Test SQL injection & XSS:**

| Field | Input | Expected Behavior |
|-------|-------|-------------------|
| Username | `admin'; DROP TABLE users;--` | Sanitized/rejected |
| Email | `<script>alert('xss')</script>@mit.edu` | Sanitized/rejected |
| Name | `O'Brien` | Properly escaped, saved |
| Password | `'; OR '1'='1` | Hashed safely |

**Pass/Fail:** No SQL errors, no script execution

---

#### Test 6.5: Large File Upload (CSV)
**Priority:** LOW

**Test Cases:**
- File size: 10MB+ (should reject or limit)
- 10,000+ rows (performance test)
- Malformed CSV (extra columns, missing commas)

---

#### Test 6.6: Concurrent Actions
**Priority:** MEDIUM

**Scenario: Two personnel add same email simultaneously**

**Expected:**
- First request: Success
- Second request: Error "Email already whitelisted"

---

#### Test 6.7: Browser Back Button After Logout
**Priority:** MEDIUM

**Steps:**
1. Login as personnel
2. Navigate to `/personnel/dashboard`
3. Logout
4. Click browser back button

**Expected:**
- Page attempts to load
- JWT validation fails
- Redirects to login page (should NOT show cached dashboard)

---

## 🔒 SECURITY TESTING

### Test Suite 7: Security Validation

#### Test 7.1: Password Hashing
**Priority:** CRITICAL

**Verification:**
```sql
SELECT password FROM college_personnel WHERE email = 'hod001-hod@mitindia.edu';
-- Should return hashed value (e.g., pbkdf2:sha256:...)
-- Should NOT be plaintext "hod123"
```

**Pass/Fail:** Password is hashed using Werkzeug

---

#### Test 7.2: JWT Cookie Security Attributes
**Priority:** HIGH

**Check DevTools → Application → Cookies:**

**Required Attributes:**
- ✅ `HttpOnly`: true (prevents JavaScript access)
- ✅ `Secure`: true (if HTTPS, false for localhost is OK)
- ✅ `SameSite`: Lax or Strict

---

#### Test 7.3: Permission-Based UI (RBAC)
**Priority:** MEDIUM

**Test role-based permissions:**

**HOD (can_manage_students = true):**
- ✅ "Manage Whitelist" button visible
- ✅ "Add Email" form accessible

**Faculty (can_manage_students = false):**
- ✗ "Manage Whitelist" button hidden or disabled
- ✗ "Add Email" form inaccessible (or shows error)

---

#### Test 7.4: CSRF Protection (if enabled)
**Priority:** LOW (depends on Flask-WTF setup)

**Test POST requests without CSRF token:**
- Should return 400 Bad Request

---

#### Test 7.5: Rate Limiting (if implemented)
**Priority:** LOW

**Test rapid-fire requests:**
- 100 login attempts in 1 minute
- Should trigger rate limit (if configured)

---

## ⚡ PERFORMANCE TESTING

### Test Suite 8: Performance Benchmarks

#### Test 8.1: Page Load Times
**Priority:** MEDIUM

**Measure with DevTools Network tab:**

| Page | Target Time | Acceptable |
|------|-------------|------------|
| Landing page | < 1s | < 2s |
| Login pages | < 1s | < 2s |
| Personnel dashboard | < 2s | < 3s |
| Whitelist table (100 entries) | < 2s | < 4s |
| Students table (500 students) | < 3s | < 5s |

---

#### Test 8.2: AJAX Response Times
**Priority:** MEDIUM

**Measure API endpoints:**

| Endpoint | Action | Target | Acceptable |
|----------|--------|--------|------------|
| `/api/check-username` | Check availability | < 500ms | < 1s |
| `/api/detect-college` | Detect from email | < 300ms | < 1s |

---

#### Test 8.3: Database Query Performance
**Priority:** LOW

**Enable Flask-SQLAlchemy logging:**
```python
app.config['SQLALCHEMY_ECHO'] = True
```

**Review logs for:**
- N+1 query problems
- Missing indexes
- Full table scans

---

## 🌐 BROWSER COMPATIBILITY

### Test Suite 9: Cross-Browser Testing

**Test on multiple browsers:**

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | [ ] |
| Firefox | Latest | [ ] |
| Edge | Latest | [ ] |
| Safari | Latest (Mac) | [ ] |

**Test critical features:**
- ✅ Login forms
- ✅ Navigation dropdown
- ✅ AJAX username check
- ✅ CSV file upload
- ✅ Bootstrap modal (if any)

---

## 🔄 REGRESSION TESTING

### Test Suite 10: Existing Features

**Ensure new changes didn't break old features:**

#### Test 10.1: Student Login (Original Flow)
**Priority:** CRITICAL

1. Navigate to `/login/user`
2. Login with existing student credentials
3. Verify redirects to `/dashboard`

**Pass/Fail:** Original student flow intact

---

#### Test 10.2: College Login (Original Flow)
**Priority:** HIGH

1. Navigate to `/login/college`
2. Login with college credentials
3. Verify redirects to `/dashboard/college`

**Pass/Fail:** College dashboard still accessible

---

#### Test 10.3: Questionnaire Flow
**Priority:** MEDIUM

**After student signup:**
1. Verify redirects to questionnaire
2. Complete questionnaire
3. Verify results saved

---

#### Test 10.4: Communities Feature
**Priority:** LOW

**Verify existing features:**
- Create community
- Join community
- Post in community

---

## 📊 TEST DATA REFERENCE

### Pre-Seeded Test Accounts

#### Personnel Accounts:
```
Email: hod001-hod@mitindia.edu
Password: hod123
Role: HOD
Can Manage Students: Yes
```

#### Whitelisted Student Emails:
```
2024001@mitindia.edu (Amit Sharma)
2024002@mitindia.edu (Priya Patel)
2024003@mitindia.edu (Rahul Verma)
2024004@mitindia.edu (Sneha Reddy)
2024005@mitindia.edu (Vikram Singh)
```

#### College Info:
```
Name: MIT India
Domain: mitindia.edu
Student Email Pattern: {enrollment}@mitindia.edu
Personnel Email Pattern: {id}-{role}@mitindia.edu
```

---

## ✅ TEST COMPLETION CHECKLIST

### Before Demo:
- [ ] All CRITICAL tests passed
- [ ] All HIGH priority tests passed
- [ ] At least 80% MEDIUM tests passed
- [ ] No server errors in console
- [ ] Database migration up-to-date
- [ ] Demo data loaded
- [ ] Browser cache cleared

### Documentation:
- [ ] All test results recorded
- [ ] Bugs logged with severity
- [ ] Performance metrics documented
- [ ] Screenshots of key flows captured

---

## 🐛 BUG REPORTING TEMPLATE

**Use this format when reporting issues:**

```markdown
## Bug Report

**Severity:** [CRITICAL | HIGH | MEDIUM | LOW]
**Test ID:** [e.g., Test 1.3]

**Description:**
[Brief description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Screenshots:**
[Attach if applicable]

**Environment:**
- Browser: [e.g., Chrome 120]
- OS: [e.g., Windows 11]
- Date: [Test date]

**Logs/Errors:**
```
[Paste console errors or stack traces]
```
```

---

## 📈 SUCCESS CRITERIA

### Minimum Pass Thresholds:
- **CRITICAL tests:** 100% pass
- **HIGH tests:** 95% pass
- **MEDIUM tests:** 80% pass
- **LOW tests:** 70% pass

### Demo Ready Criteria:
✅ Personnel can login without issues  
✅ Personnel can access all dashboard pages  
✅ Personnel can add emails to whitelist  
✅ Students can signup with whitelisted emails  
✅ Live validation (username, email) works  
✅ Navigation between pages seamless  
✅ No console errors during normal flow  
✅ All critical security checks pass  

---

## 🎓 TESTING BEST PRACTICES

1. **Test in Order:** Follow critical path first
2. **Document Everything:** Record all pass/fail results
3. **Use Fresh Data:** Reset demo data between test runs
4. **Clear State:** Logout between role-switching tests
5. **Check DevTools:** Monitor console for errors
6. **Verify Database:** Check DB state for critical operations
7. **Test Negative Cases:** Don't just test happy paths
8. **Performance Matters:** Note slow operations
9. **Mobile Testing:** Test responsive design (optional)
10. **Ask Questions:** If behavior unclear, investigate

---

## 📞 SUPPORT DURING TESTING

**If tests fail:**
1. Check server is running
2. Verify database migration current
3. Clear browser cache/cookies
4. Check console for errors
5. Review demo data setup
6. Consult implementation docs

**Common Issues:**
- **401 Unauthorized:** JWT not set or expired
- **403 Forbidden:** Wrong role trying to access route
- **404 Not Found:** Route not registered or typo in URL
- **500 Server Error:** Check Flask console for stack trace

---

## 🎉 FINAL VERIFICATION

**Before declaring "Testing Complete":**

✅ All critical bugs fixed  
✅ Regression tests passed  
✅ Performance acceptable  
✅ Security checks passed  
✅ Documentation updated  
✅ Demo script prepared  
✅ Backup created  

---

**Last Updated:** February 10, 2026  
**Version:** 2.0  
**Total Test Cases:** 100+  
**Estimated Testing Time:** 4-6 hours (full suite)

**Good luck with your testing! 🚀**
