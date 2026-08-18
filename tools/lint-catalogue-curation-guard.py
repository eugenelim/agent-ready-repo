#!/usr/bin/env python3
"""Guard lint for the ``catalogue-curation`` pack (RFC-0059 D6, spec AC group
"D6 guard").

The ``catalogue-curation`` skills ingest external code from outside this repo.
RFC-0059's hard constraint: **they must never change this repo's
``agentbundle`` engine behaviour or the ``credential-brokers`` pack.** A skill
body is LLM-executed prose, so a lint cannot decide whether prose "sanctions a
write" (the credentialed-lint substring trap is the cautionary case). This guard
is therefore **two honest layers**, neither of them intent-detection:

  1. **Presence layer (pure tree check).** Every ``catalogue-curation`` skill
     carries an explicit refusal clause. Legacy skills name the two protected
     trees in the running catalogue; adopter-facing skills instead confine writes
     to their declared pack surface and reserve other protected trees for an
     authorized change path. This lint asserts a recognized clause is *present*
     — a structural fact — not that the prose is obeyed.

  2. **Path-gate layer (changeset check).** A changeset that touches the engine's
     *behavioural* code (``packages/agentbundle/**``) or ``packs/credential-brokers/**``
     hard-fails **unless** it carries the declared engine/credbroker-scoped
     exemption reference (a commit trailer / in-diff marker readable by both a
     local hook and CI). Two engine-tree carve-outs, neither engine behaviour:
     the declarative build recipes
     (``packages/agentbundle/agentbundle/build/recipes/**``, config every pack
     addition edits) and any ``.../tests/...`` path (additive test coverage —
     e.g. a pack's dependency-gate regression test). ``packs/credential-brokers/**``
     has **no** carve-out.

     This protects the trees *regardless of what wrote the change* — the honest
     guarantee is barrier-plus-visibility, not cryptographic impossibility. The
     exemption is **changeset-scoped, not per-commit**: the trailer appearing in
     any commit of the range exempts the whole changeset (consistent with the
     barrier-not-cryptographic bound; gate per-commit if finer precision is ever
     wanted).

  3. **Parity layer (pure tree check).** Security-critical helpers duplicated
     across skills (the pack model has no cross-skill shared-code location) must
     stay **byte-identical**; a drifted copy fails the lint (edit one, edit all).
     See ``DUP_GROUPS``.

Together these make this the ``catalogue-curation`` pack lint.

**Residual (D6, spec AC99).** The path-gate contains *changesets*. An assimilated
**hook executes at session/commit time** and could write a protected tree
*before* a diff is ever gated — outside this barrier. The compensating control
for that path is the **ingest-time hook confirm** (an ingested hook is a
higher-scrutiny class requiring explicit human confirm before it lands; see
``assimilate-primitive``'s ``ingest-safety`` reference), **not** this path-gate.

The path-classification and exemption-detection logic are pure functions
(``classify_paths`` / ``has_exemption``) so they unit-test without git; a thin
``git diff`` wrapper feeds them in CI. Pure-stdlib, ``--root`` flagged, exit
0=pass / 1=violation — matching the other ``tools/`` lints. Runs in
``build-check.yml`` (this repo's own-lint home), never in the projected
``pre-pr.py`` hook (which deliberately runs no repo linters).

Usage:
    python tools/lint-catalogue-curation-guard.py [--root .] [--base <ref>]
    python tools/lint-catalogue-curation-guard.py --local-skip-path-gate

``--base`` names the ref to diff against for the path-gate (default:
``origin/main``). Git or base-ref unavailability fails closed. Local operators
who intentionally lack the base may pass ``--local-skip-path-gate``; presence
and parity still run. CI must never use that flag. Exit codes: 0 = pass, 1 = one
or more violations.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Fully-protected tree: the credential brokers pack (no carve-out).
CREDBROKER_PREFIX = "packs/credential-brokers/"
# The engine: protect *behavioral* code only. Two carve-outs, neither of which is
# engine behaviour: the declarative build recipes (config every pack addition
# edits) and the test suite (additive coverage, e.g. a pack's dependency-gate
# regression test, does not change engine behaviour).
ENGINE_PREFIX = "packages/agentbundle/"
RECIPE_CARVE_OUT = "packages/agentbundle/agentbundle/build/recipes/"

# The exemption carrier: a commit trailer / in-diff marker naming an
# engine/credbroker-scoped RFC. Readable by both a local hook and CI.
EXEMPTION_MARKER = "Engine-Change-RFC:"

PACK_SKILLS_DIR = "packs/catalogue-curation/.apm/skills"
# A legacy refusal names both checkout-local protected trees. A portable,
# adopter-facing refusal instead names the selected pack boundary and reserves
# protected trees for a separate authorized change path. This remains a
# structural presence check, not prose intent detection.
LEGACY_REFUSAL_TOKENS = ("packages/agentbundle/", "packs/credential-brokers/")
PORTABLE_REFUSAL_TOKENS = (
    "selected pack's declared",
    "protected trees",
    "authorized change path",
)

# Duplicated-helper parity (RFC-0059 D-scripts, option (a) "with pack lint"):
# the pack model has no cross-skill shared-code location, so security-critical
# helpers are duplicated per skill and MUST stay byte-identical. Each group is a
# helper filename + the skill dirs whose scripts/ carry a copy.
DUP_GROUPS = {
    "ssrf_check.py": ["assimilate-primitive", "assimilate-repo"],
    "write_jail.py": ["assimilate-primitive", "assimilate-repo"],
}


def classify_paths(changed: list[str]) -> list[str]:
    """Return the subset of ``changed`` that hits a protected tree *and* is not
    carved out. Pure — no git, no filesystem."""
    hits = []
    for p in changed:
        norm = p.replace("\\", "/").removeprefix("./")
        if norm.startswith(CREDBROKER_PREFIX):
            hits.append(norm)  # credential-brokers: whole pack, no carve-out
            continue
        if norm.startswith(ENGINE_PREFIX):
            if norm.startswith(RECIPE_CARVE_OUT):
                continue  # declarative recipe — config, not engine behaviour
            if "/tests/" in norm:
                continue  # test suite — additive coverage, not engine behaviour
            hits.append(norm)
    return hits


def has_exemption(commit_messages: str) -> bool:
    """True if the exemption carrier appears in the changeset's commit messages
    (or an in-diff marker passed in the same blob). Pure."""
    return EXEMPTION_MARKER in commit_messages


def check_presence(root: Path) -> list[str]:
    """Return skills without a recognized legacy or portable refusal clause."""
    violations: list[str] = []
    skills_dir = root / PACK_SKILLS_DIR
    if not skills_dir.is_dir():
        return violations  # pack not present in this tree — nothing to check
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        body = skill_md.read_text(encoding="utf-8")
        has_legacy_refusal = all(token in body for token in LEGACY_REFUSAL_TOKENS)
        has_portable_refusal = all(token in body for token in PORTABLE_REFUSAL_TOKENS)
        if not (has_legacy_refusal or has_portable_refusal):
            rel = skill_md.relative_to(root)
            violations.append(
                f"{rel}: missing refusal clause — expected both legacy protected-tree "
                "paths or the portable selected-pack/protected-tree/authorized-path clause"
            )
    return violations


def check_dup_sync(root: Path) -> list[str]:
    """Parity layer: every duplicated helper copy is byte-identical across the
    skills that carry it. A drifted copy is a violation (edit one, edit all)."""
    violations: list[str] = []
    base = root / PACK_SKILLS_DIR
    if not base.is_dir():
        return violations
    for filename, skills in DUP_GROUPS.items():
        blobs: dict[str, bytes] = {}
        for skill in skills:
            p = base / skill / "scripts" / filename
            if not p.exists():
                violations.append(f"dup-sync: missing copy {skill}/scripts/{filename}")
                continue
            blobs[skill] = p.read_bytes()
        uniq = set(blobs.values())
        if len(uniq) > 1:
            violations.append(
                f"dup-sync: '{filename}' copies have drifted across "
                f"{sorted(blobs)} — edit one, edit all (they must be byte-identical)"
            )
    return violations


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, FileNotFoundError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def check_path_gate(root: Path, base: str) -> tuple[list[str], bool]:
    """Path-gate layer: read the diff vs ``base`` and the changeset's commit
    messages; a protected-tree touch without the exemption carrier is a
    violation. Returns (violations, ran) — ``ran`` is False when git/base was
    unavailable (the gate is skipped, not failed)."""
    names = _git(root, "diff", "--name-only", f"{base}...HEAD")
    if names is None:
        return [], False
    changed = [line for line in names.splitlines() if line.strip()]
    hits = classify_paths(changed)
    if not hits:
        return [], True
    messages = _git(root, "log", f"{base}..HEAD", "--format=%B") or ""
    if has_exemption(messages):
        return [], True
    violations = [
        "path-gate: changeset touches a protected tree without the "
        f"'{EXEMPTION_MARKER}' exemption trailer:"
    ] + [f"    {h}" for h in hits]
    return violations, True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repo root (default: .)")
    ap.add_argument("--base", default="origin/main", help="diff base ref for the path-gate")
    ap.add_argument(
        "--local-skip-path-gate",
        action="store_true",
        help="explicitly skip git path-gate for a local checkout without the diff base",
    )
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    violations = check_presence(root)
    violations.extend(check_dup_sync(root))
    if args.local_skip_path_gate:
        print(
            "lint-catalogue-curation-guard: path-gate explicitly skipped for local run; "
            "presence and parity layers ran.",
            file=sys.stderr,
        )
    else:
        gate_violations, ran = check_path_gate(root, args.base)
        violations.extend(gate_violations)
        if not ran:
            violations.append(
                "path-gate: cannot evaluate changes because git or diff base "
                f"'{args.base}' is unavailable"
            )

    if violations:
        for v in violations:
            print(f"lint-catalogue-curation-guard: {v}", file=sys.stderr)
        return 1
    print("lint-catalogue-curation-guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
