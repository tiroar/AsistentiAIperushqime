#!/usr/bin/env python3
"""
Test script to verify AI Meal Planner setup
"""

import sys
import os
import sqlite3
from pathlib import Path

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Streamlit: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Pandas: {e}")
        return False
    
    try:
        import plotly
        print("✅ Plotly imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Plotly: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PIL: {e}")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("🗄️  Testing database...")
    
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database manager created successfully")
        
        # Test creating a user
        user = db.create_user(
            email="test@example.com",
            username="testuser",
            auth_provider="email",
            password="testpass123"
        )
        
        if user:
            print("✅ User creation test passed")
        else:
            print("❌ User creation test failed")
            return False
        
        # Test getting user
        retrieved_user = db.get_user_by_id(user.id)
        if retrieved_user and retrieved_user.email == "test@example.com":
            print("✅ User retrieval test passed")
        else:
            print("❌ User retrieval test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_auth():
    """Test authentication functionality"""
    print("🔐 Testing authentication...")
    
    try:
        from auth import AuthManager
        from database import DatabaseManager
        
        db = DatabaseManager()
        auth = AuthManager(db)
        
        print("✅ Auth manager created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        return False

def test_meal_planning():
    """Test meal planning functionality"""
    print("🍽️  Testing meal planning...")
    
    try:
        from planner import Recipe, make_week_plan, DAYS
        from database import DatabaseManager
        
        # Test Recipe model
        recipe = Recipe(
            name="Test Recipe",
            meal_type="breakfast",
            kcal=300,
            protein=15,
            carbs=30,
            fat=10,
            tags=["test"],
            ingredients=["test ingredient"],
            steps=["test step"]
        )
        
        if recipe.name == "Test Recipe":
            print("✅ Recipe model test passed")
        else:
            print("❌ Recipe model test failed")
            return False
        
        # Test meal planning
        recipes = [recipe]
        plan = make_week_plan(recipes, 2000, [], [], "30/40/30")
        
        if plan and len(plan) == len(DAYS):
            print("✅ Meal planning test passed")
        else:
            print("❌ Meal planning test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Meal planning test failed: {e}")
        return False

def test_ai_features():
    """Test AI features"""
    print("🤖 Testing AI features...")
    
    try:
        from ai_helpers import suggest_substitutions, expand_recipe_request, translate_to_albanian
        
        # Test substitutions
        subs = suggest_substitutions(["chicken"], ["turkey"])
        if subs:
            print("✅ Substitutions test passed")
        else:
            print("❌ Substitutions test failed")
            return False
        
        # Test recipe expansion
        recipe = expand_recipe_request("breakfast", 300, ["test"], [])
        if recipe and "name" in recipe:
            print("✅ Recipe expansion test passed")
        else:
            print("❌ Recipe expansion test failed")
            return False
        
        # Test translation
        translation = translate_to_albanian("Hello")
        if translation:
            print("✅ Translation test passed")
        else:
            print("❌ Translation test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ AI features test failed: {e}")
        return False

def test_file_structure():
    """Test file structure"""
    print("📁 Testing file structure...")
    
    required_files = [
        "app_enhanced.py",
        "database.py",
        "auth.py",
        "planner.py",
        "ai_helpers.py",
        "nutrition_reports.py",
        "preference_learning.py",
        "cooking_skills.py",
        "social_features.py",
        "analytics_dashboard.py",
        "image_recognition.py",
        "config.py",
        "requirements.txt",
        "recipes.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_config():
    """Test configuration"""
    print("⚙️  Testing configuration...")
    
    try:
        from config import Config
        
        # Test basic config values
        if hasattr(Config, 'APP_NAME') and hasattr(Config, 'APP_VERSION'):
            print("✅ Configuration loaded successfully")
            return True
        else:
            print("❌ Configuration test failed")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 AI Meal Planner - Enhanced Edition Test Suite")
    print("================================================")
    print()
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_config),
        ("Imports", test_imports),
        ("Database", test_database),
        ("Authentication", test_auth),
        ("Meal Planning", test_meal_planning),
        ("AI Features", test_ai_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nTo start the application, run:")
        print("  streamlit run app_enhanced.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("Make sure you have run setup.py and installed all dependencies.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
