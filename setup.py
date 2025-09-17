#!/usr/bin/env python3
"""
Setup script for AI Meal Planner - Enhanced Edition
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        "uploads",
        "logs",
        "backups",
        "exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_PATH=meal_planner.db

# Social Login Configuration (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret

# App Configuration
APP_NAME=AI Meal Planner
APP_VERSION=2.0.0
DEBUG=False
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("⚠️  Please edit .env file and add your API keys")
    else:
        print("✅ .env file already exists")

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if recipes.json exists
    if not Path("recipes.json").exists():
        print("❌ recipes.json not found")
        print("Please ensure recipes.json is in the project directory")
        sys.exit(1)
    print("✅ recipes.json found")
    
    # Check if images directory exists
    if not Path("images").exists():
        print("⚠️  images directory not found")
        print("Creating images directory...")
        Path("images").mkdir(exist_ok=True)
        print("✅ Created images directory")
    else:
        print("✅ images directory found")
    
    # Check if icon.png exists
    if not Path("images/icon.png").exists():
        print("⚠️  icon.png not found in images directory")
        print("Please add an icon.png file to the images directory")
    else:
        print("✅ icon.png found")

def create_startup_script():
    """Create startup script"""
    print("🚀 Creating startup script...")
    
    startup_script = """#!/bin/bash
# AI Meal Planner - Enhanced Edition Startup Script

echo "🍽️  Starting AI Meal Planner - Enhanced Edition"
echo "================================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please run setup.py first"
    exit 1
fi

# Start the application
echo "Starting Streamlit application..."
streamlit run app_enhanced.py
"""
    
    with open("start.sh", "w") as f:
        f.write(startup_script)
    
    # Make it executable
    os.chmod("start.sh", 0o755)
    print("✅ Created start.sh script")

def create_windows_startup_script():
    """Create Windows startup script"""
    print("🪟 Creating Windows startup script...")
    
    startup_script = """@echo off
REM AI Meal Planner - Enhanced Edition Startup Script

echo 🍽️  Starting AI Meal Planner - Enhanced Edition
echo ================================================

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\\Scripts\\activate
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Please run setup.py first
    pause
    exit /b 1
)

REM Start the application
echo Starting Streamlit application...
streamlit run app_enhanced.py
pause
"""
    
    with open("start.bat", "w") as f:
        f.write(startup_script)
    
    print("✅ Created start.bat script")

def main():
    """Main setup function"""
    print("🍽️  AI Meal Planner - Enhanced Edition Setup")
    print("=============================================")
    print()
    
    # Check Python version
    check_python_version()
    
    # Check requirements
    check_requirements()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    # Initialize database
    initialize_database()
    
    # Create startup scripts
    create_startup_script()
    create_windows_startup_script()
    
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run the application:")
    print("   - Linux/Mac: ./start.sh")
    print("   - Windows: start.bat")
    print("   - Or manually: streamlit run app_enhanced.py")
    print()
    print("For more information, see README_ENHANCED.md")

if __name__ == "__main__":
    main()
