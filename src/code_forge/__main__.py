"""Enable running Code-Forge as a module: python -m Code-Forge."""

from __future__ import annotations

import sys

from code_forge.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
