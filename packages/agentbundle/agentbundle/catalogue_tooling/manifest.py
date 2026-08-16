"""Where a pack's Claude plugin manifest lives.

One convention, one literal. Both the catalogue linter and the catalogue
verifier need the manifest path, and they disagreed for as long as each
carried its own copy: `verify.py` read `.claude-plugin/plugin.json` while
`lint.py` read `<pack>/plugin.json`, so three of lint's diagnostic codes
(CAT-L007, CAT-L008, CAT-L009) could never fire against a real pack.

A pack root is deliberately *not* a manifest location. A `plugin.json` there
is invisible to every consumer while looking present in the tree; catalogue
verify reports that case as CAT-V-004, and catalogue lint stays silent about
it rather than growing a second opinion.

Python 3.11 stdlib only.
"""

from __future__ import annotations

from pathlib import Path

MANIFEST_DIR = ".claude-plugin"
MANIFEST_NAME = "plugin.json"


def plugin_json_path(pack_dir: Path) -> Path:
    """Manifest location for a pack — the only one the build pipeline reads."""
    return pack_dir / MANIFEST_DIR / MANIFEST_NAME
