"""Hermetic validation of generated claude-plugin manifests.

Validates all generated plugin.json files and marketplace.json against the
pinned internal schemas (plugin-manifest.derived.schema.json and the
marketplace structure). Fails with a non-zero exit code if any manifest has
schema errors, so publishing is blocked when artifacts are malformed.

Run after `make build`:
  python3 tools/validate-claude-plugin-manifests.py

Used by .github/workflows/publish-claude-plugins.yml before publishing to
claude-plugins-dist. This is the hermetic CI gate; real-client validation
(`claude plugin validate`, Claude Code 2.1.209+) should be run locally.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist" / "claude-plugins"

# Add agentbundle to path for schema validation.
sys.path.insert(0, str(REPO_ROOT / "packages" / "agentbundle"))
from agentbundle.build.main import _read_bundled  # noqa: E402
from agentbundle.build.validate import validate as validate_instance  # noqa: E402


def _load_derived_schema() -> dict:
    return json.loads(_read_bundled("plugin-manifest.derived.schema.json"))


def main() -> int:
    if not DIST_DIR.exists():
        print(f"error: {DIST_DIR} not found — run `make build` first.", file=sys.stderr)
        return 1

    schema = _load_derived_schema()
    failed: list[str] = []

    # Validate every per-pack plugin.json.
    plugin_manifests = sorted(DIST_DIR.rglob("*.claude-plugin/plugin.json"))
    if not plugin_manifests:
        print("warning: no plugin.json files found in dist/claude-plugins/", file=sys.stderr)

    for manifest_path in plugin_manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        errors = validate_instance(manifest, schema)
        if errors:
            rel = manifest_path.relative_to(REPO_ROOT)
            print(f"FAIL {rel}:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            failed.append(str(rel))
        else:
            print(f"ok   {manifest_path.relative_to(REPO_ROOT)}")

    # Validate marketplace.json structure: no hooks in plugin entries.
    marketplace_path = DIST_DIR / "marketplace.json"
    if marketplace_path.exists():
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        for plugin in marketplace.get("plugins", []):
            if "hooks" in plugin:
                rel = marketplace_path.relative_to(REPO_ROOT)
                msg = (
                    f"FAIL {rel}: plugin '{plugin.get('name')}' contains 'hooks' — "
                    "hooks must not appear in marketplace entries"
                )
                print(msg, file=sys.stderr)
                failed.append(str(rel))
                break
        else:
            print(f"ok   {marketplace_path.relative_to(REPO_ROOT)}")

    if failed:
        print(f"\n{len(failed)} manifest(s) failed validation:", file=sys.stderr)
        for f in failed:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"\nAll {len(plugin_manifests) + 1} manifests passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
