#!/usr/bin/env python3
"""
GestureAgent - Touchless AI Interface
Main launcher script for the application
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from src.main import main
    sys.exit(main())