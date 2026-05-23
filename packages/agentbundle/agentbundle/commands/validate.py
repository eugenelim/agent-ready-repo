"""`agentbundle validate` subcommand.

Validates a pack directory's ``pack.toml`` against ``pack.schema.json``,
enforces the six-recipe enumeration, and applies the spec-version gate.
With ``--strict``, runs conformance fixtures via the F-build render
pipeline when they are present; warns and exits 0 when absent (v1 ship
state — F-conformance deferred to v1.1 per RFC-0003).

Exit codes:
  0 — pack is schema-valid (and conformance fixtures pass if --strict).
  1 — any schema error, unknown recipe, version mismatch, or conformance
      failure; one-line stderr reason printed for each failure.

Usage (wired by cli.py):
    args.pack_path  — path to a pack directory containing pack.toml.
    args.strict     — bool; run conformance fixtures when present.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from agentbundle.commands._common import check_spec_version_gate

# Stdlib only — no third-party deps.

# Six-recipe enumerated set from the sibling distribution-adapters spec.
VALID_RECIPES: frozenset[str] = frozenset(
    {
        "per-pack-claude-plugin",
        "per-pack-apm-package",
        "marketplace",
        "per-pack-overlay",
        "composite-agents-md",
        "composite-marketplace",
    }
)

# Location of pack.schema.json relative to the repo root.  The schema is
# bundled in docs/contracts/ and is also bundled at
# agentbundle/_data/pack.schema.json for zipapp use.
_HERE = Path(__file__).resolve().parent


def _schema_path() -> Path:
    """Locate pack.schema.json — bundled copy preferred, dev fallback."""
    bundled = _HERE.parent / "_data" / "pack.schema.json"
    if bundled.exists():
        return bundled
    # Dev fallback: walk up from agentbundle/ package to repo root.
    repo_root = _HERE.parent.parent.parent.parent
    return repo_root / "docs" / "contracts" / "pack.schema.json"


def _conformance_fixtures_dir() -> Path:
    """Return the expected path for conformance fixtures."""
    # packages/agentbundle/tests/fixtures/conformance/
    pkg_root = _HERE.parent.parent.parent
    return pkg_root / "tests" / "fixtures" / "conformance"


def run(args) -> int:
    """Entry point called by the CLI dispatcher. Returns exit code."""
    pack_path = Path(args.pack_path)
    strict: bool = getattr(args, "strict", False)

    # ── 1. Locate and load pack.toml ──────────────────────────────────────
    pack_toml_path = pack_path / "pack.toml"
    if not pack_toml_path.exists():
        print(
            f"validate: pack.toml not found at {pack_toml_path}",
            file=sys.stderr,
        )
        return 1

    try:
        raw_toml = pack_toml_path.read_text(encoding="utf-8")
        pack_data = tomllib.loads(raw_toml)
    except tomllib.TOMLDecodeError as exc:
        print(
            f"validate: pack.toml is not valid TOML: {exc}",
            file=sys.stderr,
        )
        return 1

    # ── 2. Spec-version gate ──────────────────────────────────────────────
    gate = check_spec_version_gate(pack_data)
    if gate is not None:
        return gate

    # ── 3. Schema validation ──────────────────────────────────────────────
    schema_path = _schema_path()
    if not schema_path.exists():
        print(
            f"validate: pack.schema.json not found at {schema_path}",
            file=sys.stderr,
        )
        return 1

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Import validate_instance from F-build (library-first).
    from agentbundle.build.validate import validate as validate_instance

    errors = validate_instance(pack_data, schema)
    if errors:
        # One-line stderr: first error only (spec says "one-line reason").
        print(
            f"validate: schema error — {errors[0]}",
            file=sys.stderr,
        )
        return 1

    # ── 4. Recipe gate ────────────────────────────────────────────────────
    recipes = _extract_recipes(pack_data)
    for recipe in recipes:
        if recipe not in VALID_RECIPES:
            print(
                f"validate: unknown recipe {recipe!r}; "
                f"valid recipes are {sorted(VALID_RECIPES)}",
                file=sys.stderr,
            )
            return 1

    # ── 5. Strict / conformance mode ─────────────────────────────────────
    if strict:
        conformance_dir = _conformance_fixtures_dir()
        if not conformance_dir.exists():
            print(
                "--strict conformance fixtures not present — skipping",
                file=sys.stderr,
            )
            # Exit 0 on schema portion (v1 carve-out).
            return 0
        # Conformance fixtures present — run them.
        rc = _run_conformance(pack_path, conformance_dir)
        if rc != 0:
            return rc

    return 0


def _extract_recipes(pack_data: dict) -> list[str]:
    """Return the list of recipe names the pack declares, if any.

    The schema allows a pack to declare recipes at ``[pack].recipes``
    (a list of strings).  Returns an empty list if the field is absent or
    the pack table is missing.
    """
    pack_table = pack_data.get("pack", {})
    if not isinstance(pack_table, dict):
        return []
    recipes = pack_table.get("recipes", [])
    if not isinstance(recipes, list):
        return []
    return [str(r) for r in recipes if isinstance(r, str)]


def _run_conformance(pack_path: Path, conformance_dir: Path) -> int:
    """Run each conformance fixture and assert the expected output tree.

    Each fixture is a subdirectory under ``conformance_dir`` containing:
      - ``expected/``  — the expected rendered output tree.

    We call ``render.render_pack_to_dir`` and compare file trees.
    Returns 0 if all fixtures pass; 1 on first mismatch (with stderr).
    """
    import tempfile

    from agentbundle.render import render_pack_to_dir

    fixture_dirs = sorted(
        d for d in conformance_dir.iterdir() if d.is_dir()
    )
    if not fixture_dirs:
        print(
            "--strict: conformance directory present but empty — skipping",
            file=sys.stderr,
        )
        return 0

    for fixture in fixture_dirs:
        expected_dir = fixture / "expected"
        if not expected_dir.exists():
            print(
                f"--strict: fixture {fixture.name!r} has no expected/ tree; skipping",
                file=sys.stderr,
            )
            continue

        with tempfile.TemporaryDirectory() as raw:
            actual_dir = Path(raw)
            try:
                render_pack_to_dir(pack_path, actual_dir)
            except Exception as exc:
                print(
                    f"--strict: render failed for fixture {fixture.name!r}: {exc}",
                    file=sys.stderr,
                )
                return 1

            mismatch = _diff_trees(expected_dir, actual_dir)
            if mismatch:
                print(
                    f"--strict: conformance failure in fixture {fixture.name!r}: "
                    + mismatch,
                    file=sys.stderr,
                )
                return 1

    return 0


def _diff_trees(expected: Path, actual: Path) -> str:
    """Return a one-line description of the first difference, or '' if identical."""
    expected_files = _tree_files(expected)
    actual_files = _tree_files(actual)

    only_in_expected = expected_files.keys() - actual_files.keys()
    if only_in_expected:
        first = sorted(only_in_expected)[0]
        return f"file missing from actual: {first}"

    only_in_actual = actual_files.keys() - expected_files.keys()
    if only_in_actual:
        first = sorted(only_in_actual)[0]
        return f"unexpected file in actual: {first}"

    for relpath in sorted(expected_files):
        if expected_files[relpath] != actual_files[relpath]:
            return f"content differs: {relpath}"

    return ""


def _tree_files(root: Path) -> dict[str, bytes]:
    """Return all files under ``root`` as a dict of relpath → bytes."""
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relpath = path.relative_to(root).as_posix()
            out[relpath] = path.read_bytes()
    return out
