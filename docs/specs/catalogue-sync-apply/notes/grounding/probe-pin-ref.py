#!/usr/bin/env python3
"""Probe: what pin values each source form affords once a pin is WRITTEN.

Phase 2 recorded the pin only in the plan it printed. Phase 3 writes it, so the
`git+https://` ref that `_resolve_https` computes and discards becomes the one
missing value. Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-pin-ref.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages" / "agentbundle"))

from agentbundle import catalogue  # noqa: E402

print("1. resolve_catalogue's return type — what a caller can learn")
print(f"   {inspect.signature(catalogue.resolve_catalogue)}")
print("   -> a Path. The ref is not returned.")

print("\n2. Where the ref is computed inside _resolve_https")
for line in inspect.getsource(catalogue._resolve_https).splitlines():
    if "ref" in line and "tarball" not in line:
        print(f"   {line.strip()}")
print("   -> the ref is parsed from the URI and defaulted to 'main'; nothing")
print("      resolves it to a commit SHA, so 'resolved ref' means the ref the")
print("      URI names, which the URI itself already carries.")

print("\n3. Is the parse reusable without touching _resolve_https?")
print(f"   module-level regex: {catalogue._GIT_HTTPS_RE.pattern}"
      if hasattr(catalogue, "_GIT_HTTPS_RE") else
      "   the pattern is inline in _resolve_https; no module-level name")
names = [n for n in dir(catalogue) if "RE" in n or "_re" in n]
print(f"   regex-shaped module names: {names}")
