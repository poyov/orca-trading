#!/usr/bin/env python3
"""
Setup script for Orca Trading Bot.
"""
import os
import sys
import subprocess
from pathlib import Path
import platform

def print_step(step: str):
    """Print a step header."""
    print(f"\n{'='*60}")
    print(f"🐋 {step}")
    print(f"{'='*60}")

def run_command(cmd: str, check: bool = True) -> bool:
    """Run a shell command."""
    print(f"  → {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"  📝 {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr.strip() if e.stderr else e}")
        return False

def main():
    """Main setup function."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print_step("ORCA TRADING BOT - SETUP")
    
    # Step 1: Check Python
    print_step("1. Checking Python installation")
    if not run_command(f"{sys.executable} --version"):
        print("  ⚠️  Please install Python 3.9 or higher")
        return False
    
    # Step 2: Create virtual environment
    print_step("2. Creating virtual environment")
    venv_path = project_root / "venv"
    
    if not venv_path.exists():
        if not run_command(f"{sys.executable} -m venv venv"):
            print("  ⚠️  Failed to create virtual environment")
            return False
    else:
        print("  ✅ Virtual environment already exists")
    
    # Step 3: Determine activation command
    system = platform.system()
    if system == "Windows":
        python_cmd = "venv\\Scripts\\python"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        python_cmd = "venv/bin/python"
        pip_cmd = "venv/bin/pip"
    
    # Step 4: Upgrade pip
    print_step("3. Upgrading pip")
    run_command(f"{pip_cmd} install --upgrade pip")
    
    # Step 5: Install requirements
    print_step("4. Installing dependencies")
    if not run_command(f"{pip_cmd} install -r requirements.txt"):
        print("  ⚠️  Some dependencies failed to install")
        print("  ℹ️  Trying with pip install --no-deps")
        run_command(f"{pip_cmd} install -r requirements.txt --no-deps")
    
    # Step 6: Install package in development mode
    print_step("5. Installing orca package")
    run_command(f"{pip_cmd} install -e .")
    
    # Step 7: Test imports
    print_step("6. Testing imports")
    test_code = """
import pandas as pd
import numpy as np
import ccxt
import orca
print("✅ All core packages imported successfully!")
print(f"Pandas: {pd.__version__}")
print(f"Numpy: {np.__version__}")
"""
    
    with open("_test_imports.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    run_command(f"{python_cmd} _test_imports.py")
    os.remove("_test_imports.py")
    
    # Step 8: Create initial config
    print_step("7. Creating initial configuration")
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_content = """# Orca Trading Configuration

# Data collection
symbols: ["BTC/USDT"]
timeframes: ["5m", "15m", "1h"]
exchange: "binance"

# Trading parameters
initial_balance: 10000.0
commission: 0.001  # 0.1%
max_position_size: 0.1  # 10%

# Model training
training_episodes: 1000
validation_split: 0.2

# Risk management
max_drawdown: 0.10  # 10%
stop_loss: 0.02  # 2%
"""
    
    config_file = config_dir / "default.yaml"
    if not config_file.exists():
        with open(config_file, "w") as f:
            f.write(config_content)
        print("  ✅ Created config/default.yaml")
    else:
        print("  ✅ Configuration already exists")
    
    print_step("SETUP COMPLETE! 🎉")
    print("\nNext steps:")
    print("1. Open VSCode command palette (Ctrl+Shift+P)")
    print("2. Type 'Python: Select Interpreter'")
    print("3. Choose: ./venv/bin/python")
    print("4. Open a notebook or Python file to start coding")
    print("\nFor Git in VSCode:")
    print("- Source Control icon in left sidebar (Ctrl+Shift+G)")
    print("- Stage changes, commit, and push")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)