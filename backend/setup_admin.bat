@echo off
echo ========================================
echo MeshWork Admin Features Setup
echo ========================================
echo.

echo Step 1: Running database migration...
cd backend
flask db upgrade

if %errorlevel% neq 0 (
    echo ERROR: Migration failed!
    echo Make sure Flask is installed and database is configured.
    pause
    exit /b 1
)

echo.
echo ✅ Migration completed successfully!
echo.

echo Step 2: Creating first admin user
echo.
set /p EMAIL="Enter email address for admin user: "

python set_admin.py %EMAIL%

if %errorlevel% neq 0 (
    echo ERROR: Failed to set admin privileges!
    echo Make sure the user exists in the database.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Setup Complete!
echo ========================================
echo.
echo Your admin user is ready. You can now:
echo   1. Login with the admin account
echo   2. See XP, level, and streak on dashboard
echo   3. Access the Admin Panel
echo   4. Create tasks in communities
echo.
pause
