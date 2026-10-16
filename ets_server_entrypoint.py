#!/usr/bin/python3
"""Backwards-compatible thin wrapper around the ``server_entrypoint`` package.

The container's ``entrypoint.sh`` invokes this script directly; all logic now
lives in the ``server_entrypoint`` package (config / server / main modules).
"""

import os
import sys

# Allow running as a plain script from anywhere inside the container.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server_entrypoint.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
