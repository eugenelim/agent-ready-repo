#!/usr/bin/env python3
"""Umbrella runner for the hand-run self-tests in `TESTS` below. Run it
when a linter, hook, or loop-cohort.py changes.

It is a *curated* list, not a sweep: it does not discover every
`tools/test-*` script, and several tool self-tests are gated elsewhere
(`tools/catalogue/pre_pr_catalogue.py` runs a different set, and
`tools/repo/build_gate_chain.py` runs the projected skill linters). An
earlier docstring here claimed it ran "every self-test in tools/"; it
never did, and the claim made two dangling entries easy to ignore.

Pure Python so the umbrella runs on Windows without an MSYS shell or
WSL.

Distinct from tools/hooks/pre-pr.py — that's a *gate* against the
working tree (does the diff pass the linters?); this is a *suite*
of self-tests against the linters and hooks themselves (do the
tools still do what they claim?). Both have a place; both green is
the contract.

Exit codes — three outcomes, deliberately distinguishable:

  0  every entry ran and passed.
  1  every entry resolved to a real file; at least one test failed.
  2  the manifest itself is broken — an entry in `TESTS` names a file
     that does not exist. Nothing is run. `2` is separate from `1`
     because "2 of 9 failed" and "2 entries never resolved to a file"
     are different facts, and reporting the second as the first is how
     this runner sat red for weeks without anyone reading it as broken
     (spec/local-gate-ci-parity, workstream B).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _utf8_streams() -> None:
    """Windows cp1252 guard — UTF-8 streams before any print.

    Called from `main`, not at import: a suite that imports this module to drive
    its pure functions should not have its own streams reconfigured as a side
    effect of loading the subject.
    """
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


# Each entry: (label, argv). Order is alphabetical for stability;
# nothing in the chain depends on a particular order. New `.py`
# self-tests prefer `sys.executable` over a bare `python3` so the
# child runs with the same interpreter as the umbrella.
#
# Two entries were removed here because their target files are absent
# from `main` and always were — they arrived on PRs #673 / #684, which the
# 2026-07-24 history rewrite left unreachable, and the rewritten commit
# 96232e62 carried the list entries into a tree that never held the
# scripts. `git log --diff-filter=D` finds no deletion for either.
#
#   check-xd-chain (was tools/test-check-xd-chain.py)
#     Dropped. The checker and its .github/workflows/xd-chain-gate.yml are
#     both absent from main; the chain map they enforced is readable only
#     from the unreachable commit 321c825c, so it cannot be verified
#     against main at all. Two of the five skills that map named no longer
#     exist under those names: `design-system-foundations` was renamed to
#     `design-system` (ADR-0052), and `design-token-taxonomy` — RFC-0071's
#     intended new name for `design-system` — is nowhere in the tree.
#     (`design-principles` is a separate new skill from RFC-0066 D3, not a
#     rename of either.) So restoring the checker verbatim would restore a
#     gate that fails on its own stale chain definition.
#     Of its five invariants, description length is covered by
#     `agentbundle catalogue lint` (see the lint-skill-spec entry below)
#     and Digital-Experience-Contract copy parity by
#     tools/catalogue/check_contract_parity.py. The other three — chain
#     completeness, phantom-handoff resolution, boundary-guard adjacency —
#     have no successor; recorded in workspace.toml [backlog].open as
#     `xd-chain-structural-invariants-uncovered` rather than dropped in
#     silence.
#
#   llm-judge-cross-pack-eval (was tools/test-llm-judge-cross-pack-eval.py)
#     Dropped because the check moved, not because it was lost. The judge
#     now lives in packages/agentbundle/agentbundle/commands/pack_evals.py
#     and its self-test is tools/test-run-pack-evals.py, which covers
#     build_judge_prompt / parse_judge_verdict / get_judge /
#     load_judge_config / grade_judge. That file is already run by
#     tools/catalogue/pre_pr_catalogue.py, so it gates on every
#     `make pre-pr`, `make build-check`, and `make ci`. Re-listing it here
#     would duplicate a gated check.
TESTS: list[tuple[str, list[str]]] = [
    ("lint-knowledge", [sys.executable,
                        "packs/core/tests/skills/work-loop/test-lint-knowledge.py"]),
    ("lint-sso-config", [sys.executable, "tools/test-lint-sso-config.py"]),
    ("lint-skill-spec", [sys.executable, "-m", "pytest",
                              "packages/agentbundle/tests/unit/test_catalogue_skill_spec_lint.py",
                              "-v"]),
    ("loop-cohort", ["bash", "packs/core/tests/skills/work-loop/test-loop-cohort.sh"]),
    ("pack-runtime-boundary", [sys.executable,
                               "packs/core/tests/pack/test-runtime-boundary.py"]),
    ("pre-pr", ["bash", "tools/test-pre-pr.sh"]),
    ("session-start", ["bash", "packs/core/tests/hooks/test_session_start_projection.sh"]),
    ("session-start-source", ["bash", "packs/core/tests/hooks/test_session_start_bash.sh"]),
]


def _entry_targets(cmd: list[str]) -> list[str]:
    """The repo-relative files *cmd* names. Pure — no filesystem.

    Every entry's argv is an interpreter plus flags plus one or more script /
    pytest paths, so "the tokens that end in .py or .sh" identifies the targets
    without knowing which interpreter is in front. `sys.executable` is excluded
    explicitly: on Windows it ends in `.exe`, but a source build or a wrapper
    script can put a `.py` on the end of it.
    """
    return [
        tok for tok in cmd
        if tok != sys.executable and tok.endswith((".py", ".sh"))
    ]


def _missing_targets(
    tests: list[tuple[str, list[str]]], root: Path,
) -> list[tuple[str, str, str]]:
    """(label, kind, detail) for every `TESTS` entry whose target does not check
    out. *kind* is ``"absent"`` or ``"unverifiable"``.

    Separated from `main` so it is testable without spawning anything — the
    manifest can be wrong in a checkout where every real test would pass. *kind*
    is returned rather than re-derived from the message, so the caller never has
    to sniff prose to know which fact it is holding.

    An entry that yields *no* target is a manifest error too, not a pass. It
    means the argv names nothing this function can verify (a bare `-m pytest`, a
    module rather than a path), so reporting it clean would be the same
    false-assurance this preflight exists to end.
    """
    problems: list[tuple[str, str, str]] = []
    for label, cmd in tests:
        targets = _entry_targets(cmd)
        if not targets:
            problems.append(
                (label, "unverifiable", f"no verifiable target in {' '.join(cmd)!r}")
            )
            continue
        problems += [
            (label, "absent", target)
            for target in targets
            if not (root / target).is_file()
        ]
    return problems


def main() -> int:
    _utf8_streams()
    root = _repo_root()
    os.chdir(root)

    # Preflight, before anything runs. A missing entry is a broken manifest,
    # not a failing test: reporting it as "N of M failed" describes a test run
    # that never happened.
    problems = _missing_targets(TESTS, root)
    if problems:
        print("test-all: BROKEN MANIFEST — no tests were run.", file=sys.stderr)
        for label, kind, detail in problems:
            shown = detail if kind == "unverifiable" else f"names {detail} — no such file"
            print(f"  ✖ entry {label!r} {shown}", file=sys.stderr)
        # Distinct labels, not problems: `_missing_targets` emits one per
        # target, so an entry naming two would break a count comparison.
        if len({label for label, _kind, _detail in problems}) == len(TESTS):
            # Everything missing almost never means everything was deleted. It
            # means the root resolved somewhere else — `_repo_root` reads
            # `git rev-parse --show-toplevel` in the *caller's* cwd, so running
            # this script by absolute path from another checkout lands there.
            # Advising "restore the script, or remove the entry" would be advice
            # to delete a correct manifest.
            print(
                f"test-all: every entry is missing under {root} — that is almost "
                "certainly the wrong repository root, not a deleted manifest. Run "
                "this from inside the repo you meant.",
                file=sys.stderr,
            )
        else:
            print(
                f"test-all: {len(problems)} TESTS entr"
                f"{'y' if len(problems) == 1 else 'ies'} do not resolve to a file. "
                "Restore the script, or remove the entry and record where its "
                "check now lives.",
                file=sys.stderr,
            )
        return 2

    failures = 0
    ran = 0
    for label, cmd in TESTS:
        ran += 1
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✓ {label}")
        else:
            cmd_str = " ".join(cmd)
            print(f"✖ {label} — re-run `{cmd_str}` for output", file=sys.stderr)
            failures += 1

    print()
    if failures > 0:
        print(f"test-all: {failures} of {ran} failed", file=sys.stderr)
        return 1
    print(f"test-all: {ran} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
