#!/usr/bin/env python3
"""
Launch Script for AlignPress v2

Runs the complete AlignPress v2 application with CustomTkinter UI
"""
import sys
import os

# Add alignpress_v2 to Python path
sys.path.insert(0, os.path.abspath('.'))

if __name__ == "__main__":
    from alignpress_v2.ui import main
    main()