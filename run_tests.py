#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runs all tests in the tests directory.
"""

import unittest
import sys
from pathlib import Path

# Windows Unicode 인코딩 문제 근본 해결
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

def main():
    """Runs all tests."""
    # Add the src directory to the Python path
    sys.path.append(str(Path(__file__).parent / "src"))

    # Discover and run all tests in the tests directory
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    main()
