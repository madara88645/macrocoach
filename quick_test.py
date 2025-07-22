#!/usr/bin/env python3
"""
Quick test to verify the project setup
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports"""
    try:
        print("✅ Testing basic Python imports...")
        import json
        import datetime
        import asyncio
        print("✅ Basic imports successful")
        
        print("✅ Testing project structure...")
        # Check if src directory exists
        src_dir = os.path.join(os.path.dirname(__file__), 'src', 'macrocoach')
        if os.path.exists(src_dir):
            print(f"✅ Source directory found: {src_dir}")
        else:
            print(f"❌ Source directory not found: {src_dir}")
            return False
            
        # Check main files
        main_file = os.path.join(src_dir, 'main.py')
        if os.path.exists(main_file):
            print(f"✅ Main file found: {main_file}")
        else:
            print(f"❌ Main file not found: {main_file}")
            return False
            
        print("✅ Project structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_project_imports():
    """Test project-specific imports"""
    try:
        print("✅ Testing project imports...")
        
        # Test core models
        from macrocoach.core.models import (
            UserProfile, HealthMetric, DailyPlan, 
            Meal, ChatMessage
        )
        print("✅ Core models imported successfully")
        
        # Test context
        from macrocoach.core.context import ApplicationContext
        print("✅ Context imported successfully")
        
        # Test agent imports
        from macrocoach.agents.state_store_agent import StateStoreAgent
        from macrocoach.agents.planner_agent import PlannerAgent
        from macrocoach.agents.meal_gen_agent import MealGenAgent
        from macrocoach.agents.chat_ui_agent import ChatUIAgent
        print("✅ All agents imported successfully")
        
        print("✅ All project imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Project import test failed: {e}")
        print(f"Error details: {type(e).__name__}: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 MACROCOACH v0.1 - Quick Test")
    print("=" * 50)
    
    # Test basic functionality
    basic_ok = test_imports()
    if not basic_ok:
        print("❌ Basic tests failed")
        return False
    
    print()
    
    # Test project imports
    project_ok = test_project_imports()
    if not project_ok:
        print("❌ Project import tests failed")
        return False
    
    print()
    print("🎉 All tests passed!")
    print("✅ MACROCOACH project is ready for development")
    
    # Show next steps
    print("\n📋 Next Steps:")
    print("1. Set up your .env file with OpenAI API key")
    print("2. Run: uvicorn src.macrocoach.main:app --reload")
    print("3. Visit: http://localhost:8000")
    print("4. Test the chat interface: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
