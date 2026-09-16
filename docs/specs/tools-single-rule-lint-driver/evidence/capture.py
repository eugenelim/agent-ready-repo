#!/usr/bin/env python3
"""T1 capture instrument for tools-single-rule-lint-driver.

Records raw stdout, stderr and exit status for each in-scope rule across the
input modes the spec's first criterion names. Not committed: this is a
measurement device, and the spec confines committed changes to tools/ and the
spec directory.

Modes
  clean   the real repository tree
  empty   a root where the rule's target directory exists but holds no targets
  absent  a root where that directory does not exist
(the `violation` mode is authored separately, per rule)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import fixtures

# These two resolve their scan root from their own file location
# (REPO_ROOT = Path(__file__).resolve().parent.parent) and run `git ls-files`
# with cwd=REPO_ROOT, so argv cannot move them off the real repository. Every
# fixture mode therefore records the same "outside repository" refusal rather
# than the mode it names. Recorded, not silently dropped: exit 2 on an
# out-of-tree argv IS their behaviour, and the refactor must preserve it.
ROOT_PINNED_TO_REPO = {"lint-nosec-form", "lint-nosemgrep-form"}

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
TOOLS = REPO / "tools"

# name -> (script, target-dir relative to a root, argv builder, env builder)
# argv builder takes the root and returns args AFTER the script path.
RULES: dict[str, tuple[str, str, object, object]] = {
    # argv builder takes (root, clean). `clean` reproduces the default
    # invocation CI runs; the fixture modes point at a throwaway root.
    "lint-conformance-portability": (
        "lint-conformance-portability.py", "tests/conformance",
        lambda r, clean: ["--root", str(r)], lambda r: {}),
    "lint-experience-agnostic": (
        "lint-experience-agnostic.py", "packs/experience-design",
        lambda r, clean: [], lambda r: {"EXPERIENCE_ROOT": str(r / "packs/experience-design")}),
    "lint-guides-no-repo-only-refs": (
        "lint-guides-no-repo-only-refs.py", "guides",
        lambda r, clean: ["--guides-root", str(r / "guides")], lambda r: {}),
    # Default (no argv) reads SAST_DIRS out of the Makefile — what CI runs.
    "lint-nosec-form": (
        "lint-nosec-form.py", "tools",
        lambda r, clean: [] if clean else [str(r / "tools")], lambda r: {}),
    "lint-nosemgrep-form": (
        "lint-nosemgrep-form.py", "tools",
        lambda r, clean: [] if clean else [str(r / "tools")], lambda r: {}),
    "lint_zone_violations": (
        "lint_zone_violations.py", "web/src",
        lambda r, clean: [] if clean else [str(r / "web/src")], lambda r: {}),
    # --root here is the guides DIRECTORY, not the repo root: it defaults to
    # REPO_ROOT / "guides". The flag name is overloaded across these scripts.
    "lint-guide-titles": (
        "lint-guide-titles.py", "guides",
        lambda r, clean: ["--root", str(r / "guides")], lambda r: {}),
    "lint-journey-contract": (
        "lint-journey-contract.py", "web/src/content/journeys",
        lambda r, clean: [], lambda r: {"LJC_JOURNEY_DIR": str(r / "web/src/content/journeys")}),
    "lint-pack-descriptions": (
        "lint-pack-descriptions.py", "packs",
        lambda r, clean: ["--root", str(r)], lambda r: {}),
    "lint-pack-journeys": (
        "lint-pack-journeys.py", "packs",
        lambda r, clean: [], lambda r: {"LPJ_PACKS_DIR": str(r / "packs"),
                                        "LPJ_JOURNEY_DIR": str(r / "web/src/content/journeys")}),
    "lint-pack-maintainer-emails": (
        "lint-pack-maintainer-emails.py", "packs",
        lambda r, clean: ["--root", str(r)], lambda r: {}),
    "lint-sso-config": (
        "lint-sso-config.py", "packs",
        lambda r, clean: [] if clean else sorted(
            str(p) for p in (r / "packs").glob("*/.apm/skills/*/references/sso-config.toml")),
        lambda r: {}),
}


def invoke(rule: str, root: Path, cwd: Path, clean: bool = False) -> dict:
    script, _target, argv_of, env_of = RULES[rule]
    env = dict(os.environ)
    env.update(env_of(root))
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [sys.executable, str(TOOLS / script), *argv_of(root, clean)],
        capture_output=True, text=True, cwd=str(cwd), env=env,
    )
    return {
        "exit": proc.returncode,
        "stdout": _normalise(proc.stdout, root),
        "stderr": _normalise(proc.stderr, root),
    }


def _normalise(text: str, root: Path) -> str:
    """Replace the throwaway fixture path with a placeholder.

    One normalisation class, applied identically to the before and after sides.
    A fixture root is a fresh mkdtemp each run, and several rules echo it, so
    without this an unchanged rule reads as changed. Both spellings are
    substituted because macOS resolves /var to /private/var and the scripts
    disagree about which one they print.
    """
    # Longest form first, and sorted rather than a set: /var/... is a prefix of
    # /private/var/... on macOS, so replacing the short one first leaves a
    # "/private<ROOT>" stub, and set iteration order made that intermittent.
    for form in sorted({str(root), str(root.resolve())}, key=len, reverse=True):
        text = text.replace(form, "<ROOT>")
    return text


def fixture_root(rule: str, present: bool) -> Path:
    """Build a throwaway root; target dir present-but-empty, or absent."""
    tmp = Path(tempfile.mkdtemp(prefix=f"cap-{rule}-"))
    subprocess.run(
        ["git", "init", "-q"], cwd=tmp, check=False, capture_output=True
    )
    if present:
        (tmp / RULES[rule][1]).mkdir(parents=True, exist_ok=True)
    return tmp


def main() -> int:
    out: dict[str, dict] = {}
    for rule in RULES:
        out[rule] = {}
        out[rule]["clean"] = invoke(rule, REPO, REPO, clean=True)
        for mode, present in (("empty", True), ("absent", False)):
            root = fixture_root(rule, present)
            # cwd stays the real repo: nosec/nosemgrep read SAST_DIRS from the
            # Makefile, and lint-guide-titles resolves relative paths from cwd.
            out[rule][mode] = invoke(rule, root, REPO)
        root = fixture_root(rule, True)
        fixtures.build(rule, root)
        out[rule]["violation"] = invoke(rule, root, REPO)
        if rule in ROOT_PINNED_TO_REPO:
            for mode in ("empty", "absent", "violation"):
                out[rule][mode]["unreachable"] = (
                    "scan root is pinned to the real repository; argv cannot "
                    "reach this mode"
                )
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
