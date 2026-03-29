# this_file: vexy-lines-py/tests/conftest.py
"""Pytest configuration for vexy-lines-py tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src directory is on sys.path so that `import vexy_lines` works
# even when running tests outside of a proper editable install.
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
