#!/usr/bin/env python3
"""NHANES to Lancet - Run the server."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.server import run_server

if __name__ == "__main__":
    run_server()
