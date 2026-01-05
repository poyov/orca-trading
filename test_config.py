#!/usr/bin/env python3
"""Test the configuration."""
import sys
sys.path.append('.')

from orca.core.config import config

if __name__ == "__main__":
    config.show()
    
    # Test data directories
    import os
    print("\n📁 Checking directories:")
    print(f"  Project root: {config.project_root}")
    print(f"  Data dir exists: {os.path.exists('data')}")
    print(f"  Logs dir exists: {os.path.exists('logs')}")
    
    print("\n✅ All good! Ready to start Phase 1.")