#!/usr/bin/env python3
"""Self-test for tools/check-xd-chain.py (spec/cross-pack-experience-eval, AC8/AC11).

Pattern: build fixture trees in a tempdir, run the checker via subprocess
against each tree, assert exit code and output marker substrings. Follows the
pattern in tools/test-check-contract-drift.py.

The minimal fixture tree writes all five chain skills PLUS their non-chain
pack neighbors (content-design, tone-of-voice, creative-direction, etc.) so
that the baseline passes --gate cleanly before each injection is applied.
This ensures each failure-path test is discriminating: the assertion fails
only when the specific injected fault causes the specific expected finding.

Trees:
  A — real repo in report-only mode (no --gate) → exit 0
  B — real repo with --gate → exit 0 (all checks pass)
  C — missing chain skill → --gate exits 1, [chain-completeness] in output
  D — phantom skill reference → --gate exits 1, [phantom-handoff] in output
  E — missing boundary guard → --gate exits 1, [boundary-guards] in output
  F — missing DEC contract copy → --gate exits 1, [contract-copies] in output
  G — description over 1024 chars → --gate exits 1, [description-length] in output
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "tools" / "check-xd-chain.py"

CONTRACT_ANCHORS = {
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

DUMMY_CONTRACT = "---\nschema-version: \"1.0\"\n---\n# Digital Experience Contract\n"

# Descriptions for the five chain skills that satisfy the adjacency map.
CHAIN_DESCRIPTIONS: dict[str, str] = {
    "design-token-taxonomy": (
        "Name the token taxonomy. Do NOT use to set up the token foundation — "
        "use `design-system-foundations` for that. Do NOT use to lay out hierarchy "
        "(use `information-architecture`). Do NOT use to evaluate (use `design-review`)."
    ),
    "design-system-foundations": (
        "Apply the token foundation. Do NOT use to derive the taxonomy (use `design-token-taxonomy`). "
        "Do NOT use to structure hierarchy (use `information-architecture`). "
        "Do NOT use to evaluate (use `design-review`)."
    ),
    "information-architecture": (
        "Structure a screen or flow. Do NOT use to name copy voice goals — "
        "use `copy-direction` for a specific surface."
    ),
    "copy-direction": (
        "Name copy goals. Do NOT use for content structure — use `content-design`. "
        "Do NOT use for general brand tone — use `tone-of-voice`."
    ),
    "design-review": (
        "Evaluate a screen. Do NOT use to name copy voice goals — use `copy-direction`. "
        "Do NOT use to name a felt direction — use `creative-direction`."
    ),
}

# Non-chain skills referenced in the chain descriptions above.
# These must exist in the fixture tree so the phantom-handoff check passes.
NEIGHBOR_STUBS: list[str] = [
    "content-design",
    "tone-of-voice",
    "creative-direction",
]


def _run(root: pathlib.Path, gate: bool = False) -> tuple[int, str]:
    cmd = [sys.executable, str(CHECKER), "--root", str(root)]
    if gate:
        cmd.append("--gate")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _write_minimal_skill(
    root: pathlib.Path, pack: str, skill: str, description: str
) -> None:
    """Write a minimal SKILL.md with the given description."""
    path = root / "packs" / pack / ".apm" / "skills" / skill / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nname: {skill}\ndescription: "{description}"\n---\n\n# Skill: {skill}\n',
        encoding="utf-8",
    )


def _write_contracts(root: pathlib.Path) -> None:
    """Write all four DEC contract copies to the fixture tree."""
    for rel_path in CONTRACT_ANCHORS.values():
        full = root / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(DUMMY_CONTRACT, encoding="utf-8")


def _write_minimal_chain(root: pathlib.Path) -> None:
    """Write all chain skills plus neighbor stubs so the baseline passes --gate."""
    for skill, desc in CHAIN_DESCRIPTIONS.items():
        _write_minimal_skill(root, "experience-design", skill, desc)
    # Write neighbor stubs — referenced in chain descriptions; must exist in pack
    # so the phantom-handoff check doesn't flag them as phantoms.
    for stub in NEIGHBOR_STUBS:
        _write_minimal_skill(root, "experience-design", stub, f"Stub for {stub}.")


def fail(label: str, msg: str, output: str = "") -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    if output:
        print("---", file=sys.stderr)
        print(output[:800], file=sys.stderr)
        print("---", file=sys.stderr)
    sys.exit(1)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_a_real_repo_report_only() -> None:
    label = "A (real repo, report-only → exit 0)"
    code, out = _run(REPO_ROOT, gate=False)
    if code != 0:
        fail(label, f"expected exit 0, got {code}", out)
    if "All checks passed" not in out:
        fail(label, "expected 'All checks passed' in output", out)
    print(f"✓ {label}")


def test_b_real_repo_gate() -> None:
    label = "B (real repo, --gate → exit 0)"
    code, out = _run(REPO_ROOT, gate=True)
    if code != 0:
        fail(label, f"expected exit 0, got {code}", out)
    if "All checks passed" not in out:
        fail(label, "expected 'All checks passed' in output", out)
    print(f"✓ {label}")


def test_c_missing_chain_skill() -> None:
    label = "C (missing chain skill → --gate exits 1, [chain-completeness] in output)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_minimal_chain(root)
        _write_contracts(root)
        # Pre-check: baseline should pass --gate cleanly.
        code0, out0 = _run(root, gate=True)
        if code0 != 0:
            fail(label, f"baseline unexpectedly failed --gate (pre-injection): exit {code0}", out0)
        # Inject: remove design-system-foundations.
        import shutil
        shutil.rmtree(root / "packs" / "experience-design" / ".apm" / "skills" / "design-system-foundations")
        code, out = _run(root, gate=True)
        if code != 1:
            fail(label, f"expected exit 1, got {code}", out)
        if "::error ::[chain-completeness]" not in out:
            fail(label, "expected '::error ::[chain-completeness]' marker in output", out)
    print(f"✓ {label}")


def test_d_phantom_skill_reference() -> None:
    label = "D (phantom skill reference → --gate exits 1, [phantom-handoff] in output)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_minimal_chain(root)
        _write_contracts(root)
        # Pre-check: baseline should pass --gate cleanly.
        code0, out0 = _run(root, gate=True)
        if code0 != 0:
            fail(label, f"baseline unexpectedly failed --gate (pre-injection): exit {code0}", out0)
        # Inject: overwrite design-token-taxonomy with a phantom reference.
        phantom_desc = (
            "Name the token taxonomy. Do NOT use to set up the token foundation — "
            "use `nonexistent-phantom-skill` for that. Do NOT use to lay out hierarchy "
            "(use `information-architecture`). Do NOT use to evaluate (use `design-review`)."
        )
        _write_minimal_skill(root, "experience-design", "design-token-taxonomy", phantom_desc)
        code, out = _run(root, gate=True)
        if code != 1:
            fail(label, f"expected exit 1, got {code}", out)
        if "::error ::[phantom-handoff]" not in out:
            fail(label, "expected '::error ::[phantom-handoff]' marker in output", out)
        if "nonexistent-phantom-skill" not in out:
            fail(label, "expected phantom skill name in output", out)
    print(f"✓ {label}")


def test_e_missing_boundary_guard() -> None:
    label = "E (missing boundary guard → --gate exits 1, [boundary-guards] in output)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_minimal_chain(root)
        _write_contracts(root)
        # Pre-check: baseline should pass --gate cleanly.
        code0, out0 = _run(root, gate=True)
        if code0 != 0:
            fail(label, f"baseline unexpectedly failed --gate (pre-injection): exit {code0}", out0)
        # Inject: overwrite information-architecture without the copy-direction guard.
        no_guard_desc = (
            "Structure a screen or flow. Do NOT use to choose mood (use `creative-direction`). "
            "Do NOT use to evaluate (use `design-review`)."
            # Intentionally omits `copy-direction` reference.
        )
        _write_minimal_skill(root, "experience-design", "information-architecture", no_guard_desc)
        code, out = _run(root, gate=True)
        if code != 1:
            fail(label, f"expected exit 1, got {code}", out)
        if "::error ::[boundary-guards]" not in out:
            fail(label, "expected '::error ::[boundary-guards]' marker in output", out)
    print(f"✓ {label}")


def test_f_missing_contract_copy() -> None:
    label = "F (missing DEC contract copy → --gate exits 1, [contract-copies] in output)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_minimal_chain(root)
        _write_contracts(root)
        # Pre-check: baseline should pass --gate cleanly.
        code0, out0 = _run(root, gate=True)
        if code0 != 0:
            fail(label, f"baseline unexpectedly failed --gate (pre-injection): exit {code0}", out0)
        # Inject: remove the core contract copy.
        (root / CONTRACT_ANCHORS["core"]).unlink()
        code, out = _run(root, gate=True)
        if code != 1:
            fail(label, f"expected exit 1, got {code}", out)
        if "::error ::[contract-copies]" not in out:
            fail(label, "expected '::error ::[contract-copies]' marker in output", out)
    print(f"✓ {label}")


def test_g_description_over_cap() -> None:
    label = "G (description over 1024 chars → --gate exits 1, [description-length] in output)"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_minimal_chain(root)
        _write_contracts(root)
        # Pre-check: baseline should pass --gate cleanly.
        code0, out0 = _run(root, gate=True)
        if code0 != 0:
            fail(label, f"baseline unexpectedly failed --gate (pre-injection): exit {code0}", out0)
        # Inject: overwrite copy-direction with a description over 1024 chars.
        long_desc = (
            "Name copy goals. Do NOT use for content structure — use `content-design`. "
            "Do NOT use for general brand tone — use `tone-of-voice`. "
            + ("Extra filler text to exceed the cap. " * 30)
        )
        assert len(long_desc) > 1024, f"test setup error: desc is {len(long_desc)} chars"
        _write_minimal_skill(root, "experience-design", "copy-direction", long_desc)
        code, out = _run(root, gate=True)
        if code != 1:
            fail(label, f"expected exit 1, got {code}", out)
        if "::error ::[description-length]" not in out:
            fail(label, "expected '::error ::[description-length]' marker in output", out)
    print(f"✓ {label}")


def main() -> int:
    print("Running test-check-xd-chain.py...")
    test_a_real_repo_report_only()
    test_b_real_repo_gate()
    test_c_missing_chain_skill()
    test_d_phantom_skill_reference()
    test_e_missing_boundary_guard()
    test_f_missing_contract_copy()
    test_g_description_over_cap()
    print("\n✓ All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
