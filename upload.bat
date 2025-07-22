@echo off
REM MACROCOACH v0.1 - Simple GitHub Upload (Windows CMD)
echo.
echo 🚀 MACROCOACH v0.1 - GitHub Upload Starting...
echo.

REM Check if we're in the right directory
if not exist "src\macrocoach\main.py" (
    echo ❌ Error: Not in MACROCOACH directory
    echo Please run this from: c:\Users\TR\Desktop\Projectsgit\macrocoach
    pause
    exit /b 1
)

echo ✅ Found MACROCOACH project files
echo.

REM Initialize git
echo 📦 Initializing Git repository...
git init

REM Configure git
echo ⚙️ Configuring Git user...
git config user.name "madara88645"
git config user.email "madara88645@users.noreply.github.com"

REM Add remote
echo 🔗 Adding GitHub remote...
git remote add origin https://github.com/madara88645/macrocoach.git

REM Add all files
echo 📁 Adding files...
git add .

REM Commit
echo 💾 Creating commit...
git commit -m "Initial commit: MACROCOACH v0.1 - AI nutrition coaching system"

REM Push
echo 🚀 Pushing to GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% == 0 (
    echo.
    echo 🎉 SUCCESS! Project uploaded to GitHub
    echo 🔗 https://github.com/madara88645/macrocoach
) else (
    echo.
    echo ❌ Upload failed. Try manual commands:
    echo git push -u origin main --force
)

echo.
pause
