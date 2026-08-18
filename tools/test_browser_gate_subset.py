#!/usr/bin/env python3
"""The deterministic browser subset must exclude every screenshot-writing spec.

`site-browser-quality-gate` AC10/AC11. The subset is wired into `pages.yml` after
the combined build, and it must leave the tracked tree clean — two of the existing
e2e specs write PNGs into `docs/specs/**/notes/screenshots/`, which is tracked.

Asserted as an ALLOWLIST in both directions:

- nothing in the subset writes; and
- every spec outside the subset is a writer, so a read-only spec cannot be
  quietly dropped from the gate and left running nowhere.

Run: `python3 -m pytest tools/test_browser_gate_subset.py`
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
E2E_DIR = REPO_ROOT / "web" / "src" / "test" / "e2e"
PACKAGE_JSON = REPO_ROOT / "web" / "package.json"
PAGES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pages.yml"

GATE_SCRIPT = "test:e2e:gate"

# A call that puts bytes on disk. Comments mentioning the word do not count, which
# is why this matches call syntax rather than the bare noun.
_WRITE_CALL_RE = re.compile(r"\.screenshot\s*\(|mkdirSync\s*\(|writeFileSync\s*\(|writeFile\s*\(")


def _subset_files() -> list[str]:
    scripts = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["scripts"]
    assert GATE_SCRIPT in scripts, f"web/package.json has no {GATE_SCRIPT!r} script"
    return [tok for tok in scripts[GATE_SCRIPT].split() if tok.endswith(".spec.ts")]


def _writes(path: Path) -> bool:
    return _WRITE_CALL_RE.search(path.read_text(encoding="utf-8")) is not None


def test_the_gate_script_exists_and_names_only_spec_files() -> None:
    files = _subset_files()
    assert files, "the gate script names no spec files"
    for name in files:
        assert (E2E_DIR / name).is_file(), f"{name} is not an e2e spec"


def test_no_spec_in_the_required_subset_writes_files() -> None:
    """AC11: required CI writes no tracked files."""
    writers = [name for name in _subset_files() if _writes(E2E_DIR / name)]
    assert not writers, (
        "these specs write files and must not be in the required subset: "
        f"{writers}"
    )


def test_every_excluded_spec_is_excluded_because_it_writes() -> None:
    """The other direction: a read-only spec must not be silently dropped.

    Without this, removing a spec from the gate script would look like tidying
    rather than like deleting coverage.
    """
    subset = set(_subset_files())
    excluded = sorted(
        p.name for p in E2E_DIR.glob("*.spec.ts") if p.name not in subset
    )
    non_writers = [name for name in excluded if not _writes(E2E_DIR / name)]
    assert not non_writers, (
        "these specs are read-only but excluded from the required subset — "
        f"add them to {GATE_SCRIPT} or say why here: {non_writers}"
    )


def test_the_workflow_runs_the_gate_after_both_builds_and_blocks_on_it() -> None:
    """AC10: ordering is load-bearing and the step must be able to fail the job."""
    text = PAGES_WORKFLOW.read_text(encoding="utf-8")
    assert f"run: npm run {GATE_SCRIPT} --prefix web" in text, (
        "pages.yml does not invoke the deterministic browser subset"
    )
    # The gate exercises the emitted artifact, so both builds must precede it.
    web_build = text.index("npm run build --prefix web")
    docs_build = text.index("npm run build --prefix docs-site")
    gate = text.index(f"npm run {GATE_SCRIPT} --prefix web")
    assert web_build < gate, "the browser gate runs before the marketing build"
    assert docs_build < gate, "the browser gate runs before the docs build"
    # And before the artifact is published, so a failure cannot deploy.
    upload = text.index("upload-pages-artifact")
    assert gate < upload, "the browser gate runs after the artifact upload"
    # No `continue-on-error` anywhere near it would make the gate advisory.
    window = text[text.rindex("- name:", 0, gate):upload]
    assert "continue-on-error" not in window, (
        "the browser gate step is marked continue-on-error, so it cannot block"
    )


def test_the_workflow_triggers_on_the_paths_the_gate_depends_on() -> None:
    """AC10's path-filter clause: the gate must run when its inputs change."""
    text = PAGES_WORKFLOW.read_text(encoding="utf-8")
    for needed in (
        "'web/**'",            # the specs, the config, the marketing renderer
        "'docs-site/**'",      # the docs renderer the matrix exercises
        "'guides/**'",         # guide content reaching the docs routes
        "'site.toml'",
        "'tools/build-site.py'",
        "'.github/workflows/pages.yml'",
    ):
        assert needed in text, f"pages.yml has no path filter for {needed}"
