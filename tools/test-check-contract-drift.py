#!/usr/bin/env python3
"""Self-test for tools/check-contract-drift.py (spec/digital-experience-contract, AC7).

Pattern: build fixture trees in a tempdir, run the drift-check via subprocess
against each tree (``--root <tmp>``), assert exit code and output substrings.
Real invocation — not synthesised import. Follows tools/test-lint-profiles.py.

Trees:
  A — four identical copies: exit 0
  B — schema-version mismatch in one copy: exit 1, names the pack
  C — tier annotation value changed (explore+ → pilot+) in one copy: exit 1, names field
  D — Required annotation missing on one field in one copy: exit 1, names field
  E — extra h3 header in one copy: exit 1, names extra header
  F — h3 header missing from one copy: exit 1, names missing field
  G — one file missing from disk: exit 1, names missing path
  H — h3 headers in different order in one copy: exit 1, names position mismatch
  I — one copy has no parseable frontmatter: exit 1, clean error (no uncaught exception)
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "tools" / "check-contract-drift.py"

ANCHOR_PATHS = {
    "product-strategy": pathlib.Path(
        "packs/product-strategy/.apm/skills/"
        "synthesize-stakeholder-research/references/digital-experience-contract.md"
    ),
    "product-engineering": pathlib.Path(
        "packs/product-engineering/.apm/skills/"
        "frame-intent/references/digital-experience-contract.md"
    ),
    "experience-design": pathlib.Path(
        "packs/experience-design/.apm/skills/"
        "design-review/references/digital-experience-contract.md"
    ),
    "core": pathlib.Path(
        "packs/core/.apm/skills/"
        "frontend-engineering/references/digital-experience-contract.md"
    ),
}

CANONICAL = """\
---
schema-version: "1.0"
risk-tier: explore     # explore | pilot | production
product-slug: <replace-with-product-slug>
---

# Digital Experience Contract: <replace-with-product-slug>

## Strategy [owner: product-strategy]

### Target User and Context
<!-- Required: explore+ -->

### Assumptions and Kill Criteria
<!-- Required: explore+ -->

## Product Engineering [owner: product-engineering]

### Opportunity and Bet
<!-- Required: explore+ -->

### Thin Slice
<!-- Required: pilot+ -->

## Experience Design [owner: experience-design]

### Primary Journey
<!-- Required: explore+ -->

## Frontend Engineering [owner: core]

### Prototype or Representation
<!-- Required: explore+ -->
"""


def _write_tree(root: pathlib.Path, contents: dict[str, str]) -> None:
    """Write contract copies to fixture tree; ``contents`` maps pack name to text."""
    for pack, rel_path in ANCHOR_PATHS.items():
        if pack not in contents:
            continue
        full = root / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(contents[pack], encoding="utf-8")


def _run(root: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def fail(label: str, msg: str, output: str = "") -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    if output:
        print("---", file=sys.stderr)
        print(output[:800], file=sys.stderr)
        print("---", file=sys.stderr)
    sys.exit(1)


def test_a_identical() -> None:
    label = "A (four identical copies → exit 0)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_tree(root, {p: CANONICAL for p in ANCHOR_PATHS})
        code, out = _run(root)
        if code != 0:
            fail(label, f"expected exit 0, got {code}", out)
    print(f"✓ {label}")


def test_b_schema_version_mismatch() -> None:
    label = "B (schema-version mismatch in one copy → exit 1, names pack)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        contents["core"] = CANONICAL.replace('schema-version: "1.0"', 'schema-version: "2.0"')
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
        if "schema-version" not in out.lower() and "core" not in out.lower():
            fail(label, "output does not name the mismatch pack or field", out)
    print(f"✓ {label}")


def test_c_tier_annotation_value_changed() -> None:
    label = "C (tier annotation value changed explore+ → pilot+ in one copy → exit 1, names drifting pack)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Change "Target User and Context" annotation from explore+ to pilot+ in PS copy
        contents["product-strategy"] = CANONICAL.replace(
            "### Target User and Context\n<!-- Required: explore+ -->",
            "### Target User and Context\n<!-- Required: pilot+ -->",
        )
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
        if "product-strategy" not in out.lower():
            fail(label, "output does not name product-strategy as the drifting pack", out)
        if "pilot" not in out.lower() and "explore" not in out.lower():
            fail(label, "output does not mention the tier mismatch", out)
    print(f"✓ {label}")


def test_d_required_annotation_missing() -> None:
    label = "D (Required annotation missing on one field → exit 1)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Remove the Required annotation for Thin Slice in the PE copy
        contents["product-engineering"] = CANONICAL.replace(
            "### Thin Slice\n<!-- Required: pilot+ -->",
            "### Thin Slice",
        )
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
    print(f"✓ {label}")


def test_e_extra_h3_in_one_copy() -> None:
    label = "E (extra h3 header in one copy → exit 1, names extra header)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Insert an extra field in the XD copy
        contents["experience-design"] = CANONICAL.replace(
            "## Frontend Engineering [owner: core]",
            "### Extra Invented Field\n<!-- Required: explore+ -->\n\n"
            "## Frontend Engineering [owner: core]",
        )
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
        if "extra" not in out.lower() and "extra invented field" not in out.lower():
            fail(label, "output does not name the extra header", out)
    print(f"✓ {label}")


def test_f_missing_h3_in_one_copy() -> None:
    label = "F (h3 header missing from one copy → exit 1)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Remove Primary Journey from XD copy
        contents["experience-design"] = CANONICAL.replace(
            "\n### Primary Journey\n<!-- Required: explore+ -->",
            "",
        )
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
    print(f"✓ {label}")


def test_g_file_missing() -> None:
    label = "G (one file missing from disk → exit 1, names path)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        # Only write three copies; omit 'core'
        contents = {p: CANONICAL for p in ANCHOR_PATHS if p != "core"}
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
        if "core" not in out.lower() and "frontend-engineering" not in out.lower():
            fail(label, "output does not name the missing pack path", out)
    print(f"✓ {label}")


def test_h_different_order() -> None:
    label = "H (h3 headers in different order in one copy → exit 1)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Swap order of Opportunity and Bet + Thin Slice in PE copy
        contents["product-engineering"] = CANONICAL.replace(
            "### Opportunity and Bet\n<!-- Required: explore+ -->\n\n"
            "### Thin Slice\n<!-- Required: pilot+ -->",
            "### Thin Slice\n<!-- Required: pilot+ -->\n\n"
            "### Opportunity and Bet\n<!-- Required: explore+ -->",
        )
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
    print(f"✓ {label}")


def test_i_no_parseable_frontmatter() -> None:
    label = "I (one copy has no frontmatter → exit 1, clean error not AttributeError)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        contents = {p: CANONICAL for p in ANCHOR_PATHS}
        # Strip frontmatter from PS copy
        contents["product-strategy"] = "# Digital Experience Contract: no-frontmatter\n\nJust content."
        _write_tree(root, contents)
        code, out = _run(root)
        if code == 0:
            fail(label, "expected exit 1, got 0")
        if "AttributeError" in out or "Traceback" in out:
            fail(label, "uncaught exception in output", out)
        if "frontmatter" not in out.lower() and "schema-version" not in out.lower():
            fail(label, "output does not describe the parse failure", out)
    print(f"✓ {label}")


if __name__ == "__main__":
    print(f"Running drift-check self-tests against {CHECKER}")
    test_a_identical()
    test_b_schema_version_mismatch()
    test_c_tier_annotation_value_changed()
    test_d_required_annotation_missing()
    test_e_extra_h3_in_one_copy()
    test_f_missing_h3_in_one_copy()
    test_g_file_missing()
    test_h_different_order()
    test_i_no_parseable_frontmatter()
    print("\nAll drift-check self-tests passed.")
