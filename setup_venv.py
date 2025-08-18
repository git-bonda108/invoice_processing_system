#!/usr/bin/env python3
"""
Virtual Environment Setup Script for Invoice Processing System
This script creates and configures a virtual environment with all required dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Setup virtual environment and install dependencies"""
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"
    
    print("🚀 Setting up Virtual Environment for Invoice Processing System")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Remove existing virtual environment if it exists
    if venv_path.exists():
        print("🗑️  Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create virtual environment
    if not run_command(f"python -m venv {venv_path}", "Creating virtual environment"):
        return False
    
    # Determine activation script path based on OS
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate"
        pip_path = venv_path / "Scripts" / "pip"
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    # Upgrade pip
    if not run_command(f"{pip_path} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        if not run_command(f"{pip_path} install -r {requirements_file}", "Installing dependencies"):
            return False
    else:
        print("⚠️  requirements.txt not found, skipping dependency installation")
    
    print("\n🎉 Virtual Environment Setup Complete!")
    print("=" * 60)
    print("📋 Next Steps:")
    print()
    
    if platform.system() == "Windows":
        print("1. Activate the virtual environment:")
        print(f"   .venv\\Scripts\\activate")
        print()
        print("2. Run the application:")
        print("   python main.py")
        print()
        print("3. To deactivate when done:")
        print("   deactivate")
    else:
        print("1. Activate the virtual environment:")
        print(f"   source .venv/bin/activate")
        print()
        print("2. Run the application:")
        print("   python main.py")
        print()
        print("3. To deactivate when done:")
        print("   deactivate")
    
    print()
    print("💡 Tip: The virtual environment is now ready and all dependencies are installed!")
    return True

if __name__ == "__main__":
    success = setup_virtual_environment()
    sys.exit(0 if success else 1)