"""Run the full programmatic SEO pipeline (currently: planner)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    script = ROOT / "scripts" / "planner" / "pseo_planner.py"
    cmd = [sys.executable, str(script)] + sys.argv[1:]
    print("=== Programmatic SEO Master ===")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print("\nDone. See reports/pseo/")


if __name__ == "__main__":
    main()
