"""Release tripwires for the guide callout contract.

**Deliberately not wired into a gate.** Both assertions pin content that has no
mechanical repair — a released changelog section and a shipped spec's handoff
record — so a failure here is worth a human look rather than a red required
check. `build-check.yml` carries no `paths:` filter, and neither of these can be
fixed by re-running a command.

Everything with a mechanical repair lives in a gated file instead. The ledger's
self-consistency is `tools/test_guide_ledger_integrity.py`; the authoring
standard's content, the packaged copy's bytes, its manifest digest, and
`CLI_VERSION` are `tools/test_guide_authoring_standard.py`. Nothing in the
repository compares the conversion ledger against `guides/`: each rendered-output
check derives its expectation from the guide's own source, so editing a guide
cannot redden a record of history.

Run this file directly when touching a release section or a shipped spec's
handoff record:
`python3 -m pytest tools/test_guide_typed_asides.py -q`.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "docs/specs/guide-typed-asides-conversion/spec.md"
#: The agentbundle release that first shipped the guide callout contract. This is a
#: fact about history, not about the current version, so it is not expected to move:
#: `CHANGELOG.md` retains every release section. Pinning the *current* version here
#: instead made this test fail on every release, and bumping it would have required
#: the new release's notes to claim a change that release did not make.
STANDARD_RELEASE = "0.37.1"


def test_standard_release_notes_record_the_conversion() -> None:
    """Archival: the release that shipped the standard still says so.

    A tripwire on immutable history — no legitimate future change touches a frozen
    release section, and if one does, that is worth a human look.
    """
    changelog = (REPO_ROOT / "packages/agentbundle/CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    readme = (REPO_ROOT / "packages/agentbundle/README-pypi.md").read_text(
        encoding="utf-8"
    )

    # Anchored and counted: `"## [0.37.1]" in changelog` is also satisfied by a
    # `### [0.37.1]` subheading, and a duplicated heading would silently take the first.
    headings = re.findall(
        rf"^## \[{re.escape(STANDARD_RELEASE)}\]", changelog, re.MULTILINE
    )
    assert len(headings) == 1, (
        f"expected exactly one '## [{STANDARD_RELEASE}]' release heading, "
        f"found {len(headings)}"
    )

    section = re.split(r"^## \[", changelog, flags=re.MULTILINE)
    body = next(s for s in section if s.startswith(f"{STANDARD_RELEASE}]"))
    # Whitespace-normalised: the raw form pinned an incidental line wrap between
    # "typed" and "Starlight", so a reflow that changes nothing would have failed.
    assert "typed Starlight asides" in " ".join(body.split()), (
        f"the typed-asides wording must stay in {STANDARD_RELEASE}'s changelog section"
    )
    assert "guide callout contract" in " ".join(readme.split()), (
        "README-pypi must keep documenting the callout contract somewhere; this does "
        "not pin it to the Catalogue authoring section"
    )


def test_release_handoff_records_the_completed_change_and_batch_closeout() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    status_match = re.search(r"^- \*\*Status:\*\* (\w+)", spec, re.MULTILINE)
    assert status_match
    status = status_match.group(1)
    assert status == "Shipped"
    assert len(re.findall(r"^- \[x\] \*\*AC\d+", spec, re.MULTILINE)) == 12
    assert not re.search(r"^- \[ \] \*\*AC\d+", spec, re.MULTILINE)

    plan = (
        REPO_ROOT / "docs/specs/guide-typed-asides-conversion/plan.md"
    ).read_text(encoding="utf-8")
    assert re.search(r"^- \*\*Status:\*\* Done\b", plan, re.MULTILINE)

    spec_index = (REPO_ROOT / "docs/specs/README.md").read_text(encoding="utf-8")
    row = next(
        line
        for line in spec_index.splitlines()
        if "guide-typed-asides-conversion/spec.md" in line
    )
    assert "| Shipped |" in row
    assert "12 ACs / 4 tasks" in row

    product_changelog = (REPO_ROOT / "docs/product/changelog.md").read_text(
        encoding="utf-8"
    )
    assert "Guide callouts now say what kind of attention they need." in product_changelog

    workspace = tomllib.loads((REPO_ROOT / "workspace.toml").read_text(encoding="utf-8"))
    assert not any(
        entry.get("slug") == "guide-typed-asides-conversion"
        for entry in workspace["backlog"]["open"]
    )
    spec_path = "docs/specs/guide-typed-asides-conversion/spec.md"
    expected_shipped_entry = {
        "path": spec_path,
        "kind": "spec",
        "source": {"mode": "repo-origin"},
        "summary": (
            "Convert load-bearing guide blockquotes to typed Starlight asides "
            "while preserving genuine quotations"
        ),
        "needs": [],
    }
    shipped_matches = [
        entry
        for entry in workspace["ini-002"]["work"]["shipped"]
        if isinstance(entry, dict) and entry.get("path") == spec_path
    ]
    assert shipped_matches == [expected_shipped_entry]
    prohibited_work_targets = {
        spec_path,
        "spec/guide-typed-asides-conversion",
    }
    assert not any(
        (
            entry in prohibited_work_targets
            if isinstance(entry, str)
            else entry.get("path") in prohibited_work_targets
        )
        for initiative in workspace.values()
        if isinstance(initiative, dict) and isinstance(initiative.get("work"), dict)
        for collection in ("active", "queue")
        for entry in initiative["work"].get(collection, [])
        if isinstance(entry, (str, dict))
    )
