# MACROCOACH v0.1 - GitHub Setup Script (PowerShell)
# Run this script to prepare your project for GitHub

Write-Host "🚀 Setting up MACROCOACH v0.1 for GitHub..." -ForegroundColor Green

# Check if git is installed
try {
    git --version | Out-Null
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Initialize git repository
Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
git init

# Configure git (you should update these)
Write-Host "⚙️ Configuring Git..." -ForegroundColor Yellow
git config user.name "madara88645"
git config user.email "madara88645@users.noreply.github.com"

# Add all files
Write-Host "📁 Adding files to Git..." -ForegroundColor Yellow
git add .

# Create initial commit
Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
git commit -m "🎉 Initial commit: MACROCOACH v0.1 - AI-powered nutrition coaching system

Features:
- 🤖 5-agent architecture (StateStore, Planner, MealGen, ChatUI, DataConnector)  
- 🍽️ Turkish cuisine-focused meal generation
- 📊 Health metrics integration (HealthKit, Health Connect, Mi Band)
- 🔒 Privacy-first local SQLite storage
- ⚡ FastAPI REST API + Streamlit dashboard
- 🐳 Docker containerization
- 🧪 Comprehensive test suite
- 📚 Full documentation

Stack: Python 3.12, FastAPI, SQLite, OpenAI GPT-4, Streamlit, Docker"

Write-Host ""
Write-Host "✅ Git repository successfully initialized!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps to push to GitHub:" -ForegroundColor Cyan
Write-Host "1. ✅ Repository created: https://github.com/madara88645/macrocoach"
Write-Host "2. Run: git remote add origin https://github.com/madara88645/macrocoach.git"
Write-Host "3. Run: git branch -M main"
Write-Host "4. Run: git push -u origin main"
Write-Host ""
Write-Host "🎯 Your MACROCOACH project is ready for GitHub!" -ForegroundColor Green

# Show current status
Write-Host ""
Write-Host "📊 Current Git Status:" -ForegroundColor Yellow
git status --short
