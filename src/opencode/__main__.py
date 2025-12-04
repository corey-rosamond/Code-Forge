"""Enable running OpenCode as a module: python -m OpenCode."""

from __future__ import annotations

import sys

from opencode.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
