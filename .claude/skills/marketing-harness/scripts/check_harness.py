#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REQUIRED_FILES = [
    "pyproject.toml",
    "workspace/brand/brand.lock.yaml",
    "workspace/campaigns/example.campaign.yaml",
    "src/cli.py",
    "src/harness/config.py",
    "src/harness/render.py",
    "src/harness/publish.py",
    "src/harness/style.py",
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    status = {
        "root": str(root),
        "missing": missing,
        "uv_available": shutil.which("uv") is not None,
        "env_exists": (root / ".env").exists(),
        "outputs_exists": (root / "outputs").exists(),
        "published_exists": (root / "published").exists(),
        "skill_dir": str(Path(__file__).resolve().parents[1]),
    }
    print(json.dumps(status, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
