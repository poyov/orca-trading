#!/usr/bin/env python3
"""
Setup script for Orca Trading environment.
"""
import sys
import subprocess
import pkg_resources
from pathlib import Path

def check_python_version():
    """Check Python version."""
    required = (3, 9)
    current = sys.version_info
    
    if current < required:
        print(f"❌ Python {required[0]}.{required[1]}+ required, found {current[0]}.{current[1]}")
        return False
    else:
        print(f"✅ Python {current[0]}.{current[1]} (>= {required[0]}.{required[1]})")
        return True

def install_requirements():
    """Install required packages."""
    print("\n📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "data",
        "logs",
        "notebooks",
        "tests",
        "docs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def check_imports():
    """Check if key packages can be imported."""
    packages = [
        ("pandas", "pd"),
        ("numpy", "np"),
        ("ccxt", "ccxt"),
        ("yaml", "yaml"),
        ("loguru", "logger")
    ]
    
    print("\n🔍 Checking imports...")
    all_ok = True
    
    for package, alias in packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {package}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Main setup function."""
    print("=" * 50)
    print("🐋 Orca Trading - Environment Setup")
    print("=" * 50)
    
    # Step 1: Check Python
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Install requirements
    if not install_requirements():
        print("⚠️  Continuing with existing packages...")
    
    # Step 4: Check imports
    if not check_imports():
        print("\n⚠️  Some imports failed. You may need to install packages manually.")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Run: python setup_env.py")
    print("2. Run: python src/utils/config_loader.py")
    print("3. Check config/default.yaml")
    print("=" * 50)

if __name__ == "__main__":
    main()