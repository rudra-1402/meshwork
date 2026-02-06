#!/usr/bin/env python
"""Main entry point for CLI management tool

Usage:
    python manage.py check-scoring 12
    python manage.py reset-questionnaire 12
    python manage.py mark-completed 12
    python manage.py list-users
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run CLI
from cli.manage import cli

if __name__ == '__main__':
    cli()
