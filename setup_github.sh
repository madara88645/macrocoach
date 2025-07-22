#!/bin/bash
# GitHub Repository Setup Script for MACROCOACH v0.1

echo "🚀 Setting up MACROCOACH v0.1 for GitHub..."

# Initialize git repository
git init

# Configure git (update with your details)
git config user.name "madara88645"
git config user.email "madara88645@users.noreply.github.com"

# Add all files
git add .

# Initial commit
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

echo "✅ Git repository initialized!"
echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub - ✅ DONE!"
echo "2. Run: git remote add origin https://github.com/madara88645/macrocoach.git"
echo "3. Run: git branch -M main"
echo "4. Run: git push -u origin main"
echo ""
echo "🎯 Your MACROCOACH project is ready for GitHub!"
