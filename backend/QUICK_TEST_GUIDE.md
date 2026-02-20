# Quick Test Guide - Phase 1 Endpoints

## ✅ Server is Running!

Your Flask API server is now accessible at `http://127.0.0.1:5000`

## 📋 Root Endpoint
Visit in browser: http://127.0.0.1:5000/
This shows all available endpoints.

## 🧪 Test the Unified Auth Endpoints

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health"
```

### 2. Email Validation (Change email to match your college domain)
```powershell
$body = @{ 
    email = "2025004@mitindia.edu" 
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/validate-email" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Expected Response:**
```json
{
  "valid": true,
  "user_type": "student",  // or "personnel"
  "college_id": 1,
  "college_name": "Your College Name",
  "is_registered": false,
  "whitelisted": true,
  "show_role_selector": false
}
```

### 3. Check Username Availability
```powershell
$body = @{ 
    username = "newuser123" 
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/check-username" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 4. Student Signup (Update email to match your college)
```powershell
$body = @{
    user_type = "student"
    email = "newstudent@yourcollege.edu"
    password = "TestPass123!"
    username = "newstudent"
    first_name = "Test"
    last_name = "Student"
    college_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/signup" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 5. Login
```powershell
$body = @{
    email = "2024004@mitindia.edu"
    password = "sneha123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

## ⚠️ Important Notes

### Before Testing Signup:

1. **Check your database has:**
   - A college with configured email patterns
   - The college's domain set correctly
   - For students: email must be whitelisted in `whitelisted_emails` table

2. **Update the test emails** to match your actual college domain

3. **Check college patterns** in your database:
   ```sql
   SELECT id, name, domain, student_email_pattern, personnel_email_pattern 
   FROM colleges;
   ```

### Common Issues:

**"College not found for this email domain"**
- The email domain doesn't match any college in your database
- Check the `domain` field in the `colleges` table

**"Email not whitelisted"** (for students)
- Student email must be in `whitelisted_emails` table
- Add it manually or via college admin panel

**"Email does not match pattern"**
- The email doesn't match the `student_email_pattern` or `personnel_email_pattern`
- Check the pattern configuration in your college record

## 🎯 Next Step: Database Check

Run this to see your colleges and patterns:

```powershell
# Navigate to backend folder
cd backend

# Open Python shell
python

# In Python:
from app import create_app, db
from app.models.college import College

app = create_app()
with app.app_context():
    colleges = College.query.all()
    for c in colleges:
        print(f"College: {c.name}")
        print(f"  Domain: {c.domain}")
        print(f"  Student Pattern: {c.student_email_pattern}")
        print(f"  Personnel Pattern: {c.personnel_email_pattern}")
        print()
```

## 📖 Full Test Commands

See [UNIFIED_AUTH_TEST_COMMANDS.md](UNIFIED_AUTH_TEST_COMMANDS.md) for complete test examples.

---

**Phase 1 Backend:** ✅ Fully Functional
**Ready for Phase 2:** ✅ Yes (awaiting your confirmation)
