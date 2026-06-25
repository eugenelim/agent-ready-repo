#!/usr/bin/env python3
"""Self-test for tools/lint-catalogue-seeds.py (RFC-0047 Decision 6 / ADR-0037 D4).

Asserts the load-bearing invariant of the opt-in-by-construction gate: the lint
enforces its placeholder/blocklist contract **only** on packs whose `pack.toml`
carries `[pack].lint-seeds = true`, and skips every other pack entirely — so an
organization pack that ships *instance* content is unenforced by construction,
with no edit to the lint and no central first-party pack list.

Runs the lint as a real subprocess against synthetic `packs/` trees (the
documented `python tools/lint-catalogue-seeds.py` file-path invocation), each in
its own git-initialised temp root so the lint's `git rev-parse --show-toplevel`
repo-root discovery resolves to the fixture, not this catalogue.

Run directly: ``python tools/test-lint-catalogue-seeds.py`` (exit 0 = pass).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

_LINT = Path(__file__).resolve().parent / "lint-catalogue-seeds.py"

# A blocklisted catalogue string the lint flags in any enforced seed. The
# `<project-name>` placeholder satisfies AGENTS.md's required-placeholder check,
# so a failure here is unambiguously the blocklist firing (not a missing
# placeholder). Source: lint-catalogue-seeds.py BLOCKLIST_PATTERNS + AGENTS.md
# REQUIRED_PLACEHOLDERS.
_LEAK_SEED = "<project-name> lives in agent-ready-repo\n"
_CLEAN_SEED = "<project-name> goes here\n"
# A known seed (docs/specs/README.md) whose required placeholder is *absent* —
# trips the placeholder-required check (not the blocklist), so it exercises a
# second gated check in the enforced direction. Source: REQUIRED_PLACEHOLDERS.
_MISSING_PLACEHOLDER_SEED = "real content, no scaffold marker\n"

# A pack fixture: (name, body, seeds). `body` is the literal `pack.toml` text, or
# the sentinel None meaning "write no pack.toml at all".
_FLAGGED = '[pack]\nname = "x"\nversion = "0.0.0"\nlint-seeds = true\n'
_NO_FLAG = '[pack]\nname = "x"\nversion = "0.0.0"\n'
_FLAG_FALSE = '[pack]\nname = "x"\nversion = "0.0.0"\nlint-seeds = false\n'
_MALFORMED = '[pack]\nname = "x\nversion =\n'  # syntactically invalid TOML
_NONTABLE = 'pack = "scalar-not-a-table"\n'  # [pack] is not a dict


def _make_pack(root: Path, name: str, body: str | None, seeds: dict[str, str]) -> None:
    pack_dir = root / "packs" / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    if body is not None:
        (pack_dir / "pack.toml").write_text(body, encoding="utf-8")
    for rel, content in seeds.items():
        seed = pack_dir / "seeds" / rel
        seed.parent.mkdir(parents=True, exist_ok=True)
        seed.write_text(content, encoding="utf-8")


def _run(packs: list[tuple[str, str | None, dict[str, str]]]) -> tuple[int, str]:
    """Build a git-initialised synthetic repo with *packs* and run the lint.

    Returns (exit_code, stderr). The `git init` is load-bearing: it is what pins
    the lint's `git rev-parse --show-toplevel` repo-root discovery to this
    fixture rather than falling through to the real catalogue (which would let
    the enforce-fail cases pass for the wrong reason).
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for name, body, seeds in packs:
            _make_pack(root, name, body, seeds)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        proc = subprocess.run(
            [sys.executable, str(_LINT)], cwd=root, capture_output=True, text=True
        )
        return proc.returncode, proc.stderr


# (label, packs, expected_exit, expected_stderr_substring_or_None)
CASES: list[tuple[str, list[tuple[str, str | None, dict[str, str]]], int, str | None]] = [
    # AC2 / AC4: a pack with seeds but NO flag is skipped entirely — even a leak
    # AND an unknown-seed path (normally fail-loud) raise no violation.
    (
        "unflagged pack skipped (leak + unknown-seed path both ignored)",
        [("org-acme", _NO_FLAG, {"AGENTS.md": _LEAK_SEED, "docs/house-style.md": "anything\n"})],
        0,
        None,
    ),
    # AC4: an explicit `lint-seeds = false` is also opt-out.
    (
        "explicit lint-seeds=false is opt-out",
        [("org-beta", _FLAG_FALSE, {"AGENTS.md": _LEAK_SEED})],
        0,
        None,
    ),
    # AC5: a flagged pack with a leak still fails — and the blocklist (not the
    # placeholder check) is what fires, asserted via the stderr message.
    (
        "flagged pack with a leak fails (blocklist fires)",
        [("core", _FLAGGED, {"AGENTS.md": _LEAK_SEED})],
        1,
        "agent-ready-repo",
    ),
    # AC5 (second gated check, enforced direction): a flagged pack whose seed is
    # missing its required placeholder fails the placeholder-required check.
    (
        "flagged pack missing required placeholder fails (placeholder check fires)",
        [("core", _FLAGGED, {"docs/specs/README.md": _MISSING_PLACEHOLDER_SEED})],
        1,
        "required placeholder missing",
    ),
    # A flagged pack with clean placeholder content passes.
    (
        "flagged pack clean passes",
        [("core", _FLAGGED, {"AGENTS.md": _CLEAN_SEED})],
        0,
        None,
    ),
    # AC6: the FLAG drives enforcement, not the pack name. A pack named neither
    # of the four first-party packs but carrying the flag is STILL enforced —
    # proving there is no central first-party-name list as the source of truth.
    (
        "non-first-party pack name + flag is enforced (flag drives it, not a name list)",
        [("org-acme", _FLAGGED, {"AGENTS.md": _LEAK_SEED})],
        1,
        "agent-ready-repo",
    ),
    # The two together: identical instance-shaped seed, enforced iff flagged.
    (
        "same seed: flagged fails, unflagged in same run is skipped",
        [
            ("flagged", _FLAGGED, {"AGENTS.md": _LEAK_SEED}),
            ("unflagged", _NO_FLAG, {"AGENTS.md": _LEAK_SEED}),
        ],
        1,  # the flagged pack's leak fails the whole run; the unflagged one is silent
        "agent-ready-repo",
    ),
    # Fail-closed-to-skip: a pack with seeds but no pack.toml at all is skipped
    # (no flag readable ⇒ unenforced), not crashed or enforced.
    (
        "pack with seeds but no pack.toml is skipped (no crash)",
        [("org-nopack", None, {"AGENTS.md": _LEAK_SEED})],
        0,
        None,
    ),
    # Fail-closed-to-skip: a malformed/unreadable pack.toml is skipped, not a crash.
    (
        "pack with malformed pack.toml is skipped (no crash)",
        [("org-bad", _MALFORMED, {"AGENTS.md": _LEAK_SEED})],
        0,
        None,
    ),
    # Fail-closed-to-skip: a non-table `pack = "scalar"` is skipped, not a crash.
    (
        "pack with non-table [pack] is skipped (no crash)",
        [("org-scalar", _NONTABLE, {"AGENTS.md": _LEAK_SEED})],
        0,
        None,
    ),
]


def main() -> int:
    failures = 0
    for label, packs, expected_exit, expected_stderr in CASES:
        actual_exit, stderr = _run(packs)
        ok = actual_exit == expected_exit
        if ok and expected_stderr is not None:
            ok = expected_stderr in stderr
        if ok:
            print(f"✓ {label}")
        else:
            detail = f"expected exit {expected_exit}, got {actual_exit}"
            if expected_stderr is not None and expected_stderr not in stderr:
                detail += f"; stderr missing {expected_stderr!r}"
            print(f"✖ {label}: {detail}", file=sys.stderr)
            failures += 1
    print()
    if failures:
        print(f"test-lint-catalogue-seeds: {failures} of {len(CASES)} failed", file=sys.stderr)
        return 1
    print(f"test-lint-catalogue-seeds: {len(CASES)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
