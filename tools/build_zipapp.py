"""Build the agentbundle zipapp into OUTPUT_DIR.

Usage: python tools/build_zipapp.py <output_dir>

Called from the Makefile zipapp target. Using a script (rather than
inline -c snippets) avoids Windows path quoting issues where
$(OUTPUT_DIR) embeds backslashes that Python interprets as escape
sequences in a string literal.
"""
from __future__ import annotations

import shutil
import sys
import zipapp
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <output_dir>", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    stage = output_dir / "_zipapp_stage"

    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(
        "packages/agentbundle/agentbundle",
        stage / "agentbundle",
        ignore=shutil.ignore_patterns("__pycache__", "tests", "*.pyc"),
    )

    zipapp.create_archive(
        stage,
        target=output_dir / "agentbundle.pyz",
        interpreter="/usr/bin/env python3",
        main="agentbundle.cli:main",
    )

    shutil.rmtree(stage, ignore_errors=True)
    print(f"built {output_dir / 'agentbundle.pyz'}")


if __name__ == "__main__":
    main()
