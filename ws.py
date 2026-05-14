#!/usr/bin/env python3
"""
Web Search Skills CLI entry point.

Usage:
    python ws.py <command> <query> [options]

Or install and run:
    uv tool install -e .
    web-search <command> <query> [options]
"""
import sys
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from scripts.cli import main

if __name__ == "__main__":
    main()
