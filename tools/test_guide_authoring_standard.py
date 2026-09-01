"""Gated invariants of the guide authoring standard.

Two assertions, deliberately only two: the authoring standard defines the fixed aside
contract, and the archival conversion record stays out of the gate chain.

Everything else this file briefly held was already covered by a gated test, in a
stronger form, and was deleted rather than duplicated:

- byte-equality of the packaged scaffold copy → `tools/test_scaffold_projection.py`'s
  `test_projection_byte_identical_to_repo_root`, which covers all `_SYNC_PAIRS` rather
  than this one file.
- the manifest digest → moved *into* that same file as
  `test_manifest_records_every_projected_file_digest`, so it covers every projected
  file instead of only this one. That was the one genuinely missing check, and the
  wider home is where it belongs.
- `CLI_VERSION` ↔ `pyproject.toml` → `packages/agentbundle/tests/unit/test_version.py`,
  which *imports* `CLI_VERSION` rather than substring-matching the source, and is wired
  explicitly in `build-check.yml` as the version-drift guard.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORING_STANDARD = (
    REPO_ROOT / "guides/_shared/reference/catalogue-authoring-standards.md"
)
ARCHIVAL_RECORD = "tools/test_guide_typed_asides.py"
GATED_LISTS = ("Makefile", ".github/workflows/build-check.yml")


def test_authoring_standard_defines_the_fixed_aside_contract() -> None:
    """The four aside types, and the quotation-vs-aside distinction, are documented.

    Prose is compared whitespace-normalised. An earlier form asserted
    `"do not turn genuine quoted wording into an\\naside"`, which pinned an incidental
    line wrap — a pure markdown reflow would have reddened a required check. The two
    regexes are deliberately *not* normalised: a table row and a fenced example are
    markdown structure, not prose wrapping, and their line boundaries are the assertion.
    """
    standard = AUTHORING_STANDARD.read_text(encoding="utf-8")
    prose = " ".join(standard.split())

    for aside_type in ("note", "tip", "caution", "danger"):
        assert re.search(rf"^\| `{aside_type}` \| .+ \|$", standard, re.MULTILINE), (
            f"the standard must keep a table row defining the `{aside_type}` aside"
        )
    assert re.search(r"```md\n:::caution\n.+\n:::\n```", standard, re.DOTALL), (
        "the standard must keep a fenced example of the aside syntax"
    )
    for phrase in (
        "Use only those four types.",
        "A blockquote has a different job",
        "Leave those passages as `>` blockquotes.",
        "do not turn genuine quoted wording into an aside",
    ):
        assert phrase in prose, f"the standard must keep the guidance: {phrase!r}"


def test_the_archival_conversion_record_stays_unwired() -> None:
    """The release-tripwire file must not be added to a gated pytest list.

    Its two assertions pin a released changelog section and a shipped spec's
    handoff record. Neither has a mechanical repair, so a failure is worth a
    human look rather than a red required check. Asserted rather than left to a
    hand-run grep, so re-wiring it is detected rather than discovered.

    The ledger's own self-consistency is `tools/test_guide_ledger_integrity.py`,
    which *is* gated: nothing compares that ledger to `guides/` any more, so no
    guide edit can redden it.
    """
    for relative in GATED_LISTS:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        hits = [
            n
            for n, line in enumerate(text.splitlines(), 1)
            if ARCHIVAL_RECORD in line and not line.lstrip().startswith("#")
        ]
        assert not hits, (
            f"{relative}:{hits} wires {ARCHIVAL_RECORD} into a gate. It is deliberately "
            f"unwired — its two assertions have no mechanical repair; see its module "
            f"docstring. Gate tools/test_guide_ledger_integrity.py instead."
        )
