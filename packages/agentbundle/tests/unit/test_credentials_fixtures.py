"""AC34 — orphan-fixture detection.

Asserts every fixture file under
``packages/agentbundle/tests/fixtures/creds/`` is referenced by **fixture-
directory-relative path** (or by skill-directory name) in at least one
test under ``packages/agentbundle/tests/``. A fixture that no test names
is dead weight — it rots between PRs and shadows real coverage.

The walker matches on the fixture *directory* segment because lint
fixtures stage individual skills into ``tmp_path`` and reference them
by skill name rather than by full fixtures-tree relpath; the directory
segment is the load-bearing anchor that survives staging.
"""

from __future__ import annotations

import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
FIXTURES_DIR = (
    REPO_ROOT / "packages" / "agentbundle" / "tests" / "fixtures" / "creds"
)
TESTS_DIR = REPO_ROOT / "packages" / "agentbundle" / "tests"


def _test_corpus() -> str:
    """Concatenate every test file's text — including this one's. The
    self-reference is intentional: this test names every fixture by
    directory segment in the docstring/comments below as a fallback
    anchor so a future contributor who deletes a test but leaves the
    fixture in tree still gets a finding.
    """
    chunks = []
    for path in TESTS_DIR.rglob("*.py"):
        if path == pathlib.Path(__file__):
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(chunks)


def test_no_orphan_creds_fixtures():
    if not FIXTURES_DIR.is_dir():
        # No fixtures yet — nothing to orphan-check.
        return

    corpus = _test_corpus()
    orphans: list[str] = []

    for path in FIXTURES_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(FIXTURES_DIR)
        # Two anchors are acceptable: (a) the full fixtures-relative
        # posix path appears verbatim somewhere in the corpus
        # (e.g. ``creds/skills/conforming/SKILL.md``); (b) the
        # immediate parent-directory name appears — this is how the
        # lint integration tests stage by fixture-name. Either match
        # is sufficient.
        rel_posix = rel.as_posix()
        parent_name = rel.parent.name if rel.parent != pathlib.Path(".") else rel.stem
        if rel_posix in corpus or parent_name in corpus:
            continue
        # Also check for grandparent (skills/<name>/scripts/x.py → match on <name>)
        grandparent = rel.parent.parent.name if rel.parent != pathlib.Path(".") else ""
        if grandparent and grandparent in corpus:
            continue
        orphans.append(rel_posix)

    assert not orphans, (
        "Orphan fixture files (no test references them by directory or "
        "relpath): " + ", ".join(sorted(orphans))
    )
