# Unified Auth API - Test Commands (Bash/PowerShell)

## Health Check
```bash
curl -X GET http://localhost:5000/api/health
```

## 1. Email Validation

### Valid Student Email
```bash
curl -X POST http://localhost:5000/api/auth/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email":"student@college.edu"}'
```

### Valid Personnel Email
```bash
curl -X POST http://localhost:5000/api/auth/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email":"faculty@college.edu"}'
```

### Invalid Domain
```bash
curl -X POST http://localhost:5000/api/auth/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@invalid.com"}'
```

## 2. Student Signup

```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "user_type": "student",
    "email": "teststudent@college.edu",
    "password": "TestPass123!",
    "username": "teststudent",
    "first_name": "Test",
    "last_name": "Student",
    "college_id": 1
  }'
```

## 3. Personnel Signup

```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "user_type": "personnel",
    "email": "testfaculty@college.edu",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "Faculty",
    "role": "faculty",
    "college_id": 1
  }'
```

## 4. Student Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teststudent@college.edu",
    "password": "TestPass123!"
  }'
```

## 5. Personnel Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testfaculty@college.edu",
    "password": "TestPass123!"
  }'
```

## 6. Check Username Availability

### Available Username
```bash
curl -X POST http://localhost:5000/api/auth/check-username \
  -H "Content-Type: application/json" \
  -d '{"username":"availableuser123"}'
```

### Taken Username
```bash
curl -X POST http://localhost:5000/api/auth/check-username \
  -H "Content-Type: application/json" \
  -d '{"username":"teststudent"}'
```

---

## PowerShell Versions

### Email Validation
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/validate-email" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"student@college.edu"}'
```

### Student Signup
```powershell
$body = @{
  user_type = "student"
  email = "teststudent@college.edu"
  password = "TestPass123!"
  username = "teststudent"
  first_name = "Test"
  last_name = "Student"
  college_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/auth/signup" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### Login
```powershell
$body = @{
  email = "teststudent@college.edu"
  password = "TestPass123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```
