"""The retired engine's names appear only at the sites this test pins.

The supervisor replaced the old full-mode engine. Outside history paths, no file
in the searched trees names a retired script, its state file, or its reference,
except at the pinned sites below. Each site is one of three kinds:

* ``digest-input``: a value hashed into recorded approval digests, so its bytes
  can never change;
* ``deny-list``: a containment deny-list entry, kept so a worker cannot plant the
  file for a rollback to read;
* ``absence-assertion``: the line of a test that asserts the name is absent. The
  file may name the term on that line only.

A hit outside the list fails, and so does a listed site that no longer matches.
This module is outside the search, because it must spell the terms to search
for them. The workspace file and the briefs are outside it too, and so is every
file named for history (a changelog). The intents listed under
``PAST_DELIVERY_INTENTS`` describe delivery that already happened, so they are
history; the list pins which terms each still carries.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

SEARCHED = (
    "packs", "tools", "packages", "tests", "guides", "contracts", ".github",
    "docs/product/intents", "Makefile", ".snyk",
)
SKIPPED_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".vlx-worktrees", ".pytest_cache"}
HISTORY_FILENAMES = {"CHANGELOG.md", "changelog.md"}

TERMS = {
    "loop-engine": re.compile(r"loop-engine"),
    "loop-cohort": re.compile(r"loop-cohort"),
    "engine-state.json": re.compile(r"engine-state\.json"),
    "full-mode-engine": re.compile(r"full-mode-engine"),
    "cohort state.json": re.compile(r"cohort[ `'\"-]{1,3}state\.json"),
}

# (path, term, kind, the exact stripped line)
PINNED_SITES = (
    (
        "packs/core/.apm/skills/work-loop/scripts/_loop_guards.py",
        "loop-cohort", "digest-input",
        '_STATUS_PLACEHOLDER = "<loop-cohort:status>"',
    ),
    (
        "packs/core/.apm/skills/work-loop/scripts/_containment.py",
        "engine-state.json", "deny-list",
        '"engine-state.json",',
    ),
    (
        "packs/core/tests/skills/work-loop/test_supervisor_admission.py",
        "engine-state.json", "absence-assertion",
        'legacy = ("engine-state.json", "state.json")',
    ),
    (
        "packages/agentbundle/tests/unit/test_workspace_mcp_supervisor_run.py",
        "engine-state.json", "absence-assertion",
        'LEFTOVER_STATE_FILE = "engine-state.json"',
    ),
    (
        "packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py",
        "loop-engine", "absence-assertion",
        'for retired in ("loop-engine", "loop-cohort", "dispatch-receipt", "wave-passed"):',
    ),
    (
        "packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py",
        "loop-cohort", "absence-assertion",
        'for retired in ("loop-engine", "loop-cohort", "dispatch-receipt", "wave-passed"):',
    ),
    (
        "packs/frontend-engineering/tests/skills/frontend-engineering/"
        "test_rendered_page_shipped_content_limits.py",
        "loop-engine", "absence-assertion",
        '"loop-engine",',
    ),
    (
        "packs/frontend-engineering/tests/skills/frontend-engineering/"
        "test_rendered_page_shipped_content_limits.py",
        "loop-cohort", "absence-assertion",
        '"loop-cohort",',
    ),
)
ALLOWED_KINDS = {"digest-input", "deny-list", "absence-assertion"}

# Intents whose remaining mentions are dated accounts of delivery that happened.
PAST_DELIVERY_INTENTS = {
    "docs/product/intents/FEAT-0011-intent-backed-working-view.md": {"engine-state.json"},
    "docs/product/intents/work-loop-delivery-efficiency.md": {"loop-engine", "loop-cohort"},
    "docs/product/intents/contract-amendment-pre-wave-window.md": {"loop-engine", "loop-cohort"},
}


def _searched_files() -> list[Path]:
    found: list[Path] = []
    for entry in SEARCHED:
        base = REPO_ROOT / entry
        if base.is_file():
            found.append(base)
            continue
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIPPED_DIRS]
            found.extend(Path(current) / name for name in files)
    return [p for p in found if p.resolve() != SELF and p.name not in HISTORY_FILENAMES]


# A reference into a spec directory points into a history path (``docs/specs/``), so it
# is not a mention of the name: the slug of a spec that governed the old engine stays.
# Only ``docs/specs/<slug>`` or a ``../``-relative ``specs/<slug>`` reference matches, the
# slug carries no dot, and it must end at ``/`` or a delimiter, so a script path such as
# ``tools/specs/<name>.py`` is never stripped.
SPEC_REFERENCE = re.compile(
    r"(?:docs/specs/|(?:\.\./)+specs/)[a-z0-9][a-z0-9-]*(?=/|[\s`)\]'\",:;#]|$)"
)


def _hits() -> list[tuple[str, str, str]]:
    hits: list[tuple[str, str, str]] = []
    for path in _searched_files():
        if path.is_symlink():
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for line in raw.decode("utf-8", errors="replace").splitlines():
            searched = SPEC_REFERENCE.sub("", line)
            for term, pattern in TERMS.items():
                if pattern.search(searched):
                    hits.append((rel, term, line.strip()))
    return hits


def test_the_pinned_kinds_are_the_admitted_three() -> None:
    assert {kind for _p, _t, kind, _l in PINNED_SITES} <= ALLOWED_KINDS
    assert len(set(PINNED_SITES)) == len(PINNED_SITES)


def test_a_retired_name_appears_only_at_a_pinned_site() -> None:
    pinned = {(path, term, line) for path, term, _kind, line in PINNED_SITES}
    stray = [
        hit for hit in _hits()
        if hit not in pinned and hit[0] not in PAST_DELIVERY_INTENTS
    ]
    assert stray == [], f"retired names outside the pinned sites: {stray}"


def test_every_pinned_site_still_matches() -> None:
    hits = _hits()
    for path, term, _kind, line in PINNED_SITES:
        assert hits.count((path, term, line)) == 1, (path, term, line)
    for path in {p for p, *_ in PINNED_SITES}:
        for term in TERMS:
            on_file = [h for h in hits if h[0] == path and h[1] == term]
            expected = [(path, t, line) for p, t, _k, line in PINNED_SITES if p == path and t == term]
            assert on_file == expected, (path, term, on_file)


def test_the_past_delivery_intents_carry_exactly_the_pinned_terms() -> None:
    hits = _hits()
    for path, terms in PAST_DELIVERY_INTENTS.items():
        assert {t for p, t, _l in hits if p == path} == terms, path


# The files the switch removed, relative to the skill, and the skill's three copies.
REMOVED_SKILL_FILES = (
    "scripts/loop-engine.py",
    "scripts/loop-cohort.py",
    "scripts/_compat_facade.py",
    "scripts/_review_compat.py",
    "assets/state.json",
    "references/full-mode-engine.md",
)
SKILL_COPIES = (
    "packs/core/.apm/skills/work-loop",
    ".claude/skills/work-loop",
    ".agents/skills/work-loop",
)
REMOVED_SCHEMA = "contracts/jsonschema/loop-cohort-wave-decision.schema.json"


def test_the_removed_files_are_absent_from_the_source_and_its_generated_copies() -> None:
    present = [
        f"{copy}/{name}"
        for copy in SKILL_COPIES
        for name in REMOVED_SKILL_FILES
        if (REPO_ROOT / copy / name).exists()
    ]
    present += [REMOVED_SCHEMA] if (REPO_ROOT / REMOVED_SCHEMA).exists() else []
    assert present == []
    assert (REPO_ROOT / SKILL_COPIES[0] / "scripts" / "work-supervisor.py").is_file()


def test_the_spec_reference_exemption_does_not_hide_a_script_caller() -> None:
    """Control: a caller of a retired script under any ``specs/`` directory is still a hit."""
    for text in (
        "run python3 tools/specs/loop-cohort.py check",
        "python3 specs/loop-cohort.py status",
        "see specs/loop-engine-notes/ for details",
    ):
        assert re.search("loop-engine|loop-cohort", SPEC_REFERENCE.sub("", text)), text
    for text in (
        "[spec](../../specs/loop-cohort-wave-decision-retirement/spec.md)",
        "[spec](../../specs/loop-engine-guards/spec.md)",
    ):
        assert not re.search("loop-engine|loop-cohort", SPEC_REFERENCE.sub("", text)), text
