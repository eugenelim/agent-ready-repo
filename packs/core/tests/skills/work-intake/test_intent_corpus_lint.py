"""Construction tests for the intent corpus lint.

Covers T4 of the intent metadata shape contract's plan: reporting,
exit behaviour, and the two-contract partition. These need a real directory
rather than a text fixture, so they live apart from the packet-decidable suite
in `test_intent_shape.py` while reusing its notion of a conforming preamble.

The partition rule and the tombstone field contract are
`intent-renumber-and-reissue`'s; this suite asserts that the lint routes by the
rule and validates the tombstone branch, not what the rule should be.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
)

MODULE_NAME = "core_work_intake_intent_corpus_lint"


def _load_module():
    """Load the lint by path under a pack-and-skill-qualified name."""
    path = SCRIPTS / "intent_corpus_lint.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


lint = _load_module()


CONFORMING = "\n".join(
    [
        "# Intent: a conforming fixture",
        "",
        "- **Owner:** eugenelim",
        "- **Slug:** `{slug}` <!-- canonical identity -->",
        "- **Level:** feature",
        "- **Status:** Draft",
        "",
        "## Outcome",
        "",
        "An outcome sentence.",
        "",
    ]
)

TOMBSTONE = "\n".join(
    [
        "# Retired: a tombstone fixture",
        "",
        "- **Slug:** `{slug}`",
        "- **Tombstone:** 2026-09-21",
        "- **{edge}:** {target}",
        "",
    ]
)


def _corpus(tmp_path: Path, files: dict[str, str]) -> Path:
    directory = tmp_path / "intents"
    directory.mkdir()
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8")
    return directory


def _run(tmp_path: Path, files: dict[str, str]):
    directory = _corpus(tmp_path, files)
    return lint.lint_corpus(tmp_path, directory)


def _live(slug: str) -> str:
    return CONFORMING.format(slug=slug)


def _broken(slug: str, *, status: str = "Draft", extra: str = "") -> str:
    text = _live(slug).replace("- **Status:** Draft", f"- **Status:** {status}")
    if extra:
        text = text.replace("## Outcome", f"{extra}\n\n## Outcome")
    return text


# ── AC-0014: exit behaviour ───────────────────────────────────────────────────


def test_ac0014_exits_zero_for_a_clean_corpus(tmp_path: Path) -> None:
    result = _run(tmp_path, {"FEAT-0001-a.md": _live("a"), "FEAT-0002-b.md": _live("b")})
    assert result.violations == []
    assert result.exit_code == 0


def test_ac0014_exits_non_zero_for_any_violation(tmp_path: Path) -> None:
    result = _run(tmp_path, {"FEAT-0001-a.md": _broken("a", status="Shipped")})
    assert result.violations
    assert result.exit_code != 0


def test_ac0014_one_violation_among_many_clean_files_still_fails(
    tmp_path: Path,
) -> None:
    """A single fault decides the exit code; a majority-clean corpus is not
    clean."""
    files = {f"FEAT-000{n}-ok{n}.md": _live(f"ok{n}") for n in range(1, 5)}
    files["FEAT-0009-bad.md"] = _broken("bad", status="Shipped")
    result = _run(tmp_path, files)
    assert result.exit_code != 0
    assert {v.path for v in result.violations} == {"FEAT-0009-bad.md"}


# ── AC-0013: every non-conforming intent is named, with its field ─────────────


def test_ac0013_names_the_intent_and_the_field_at_fault(tmp_path: Path) -> None:
    result = _run(tmp_path, {"FEAT-0001-a.md": _broken("a", status="Shipped")})
    (violation,) = result.violations
    assert violation.path == "FEAT-0001-a.md"
    assert violation.field == "Status"


def test_ac0013_reports_both_faults_rather_than_the_first(tmp_path: Path) -> None:
    """Two faulted files, not one: a lint that stops at the first refusal makes
    a migration an unbounded number of runs."""
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _broken("a", status="Shipped"),
            "FEAT-0002-b.md": _broken("b", extra="- **Authority:** adr:0033"),
        },
    )
    assert {v.path for v in result.violations} == {
        "FEAT-0001-a.md",
        "FEAT-0002-b.md",
    }
    assert {v.field for v in result.violations} == {"Status", "Authority"}


def test_ac0013_reports_every_fault_within_one_file(tmp_path: Path) -> None:
    text = _broken("a", status="Shipped", extra="- **Stage:** shaping")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert {v.field for v in result.violations} == {"Status", "Stage"}


# ── AC-0017: every file is routed to exactly one contract ─────────────────────


def test_ac0017_routes_every_file_to_exactly_one_contract(tmp_path: Path) -> None:
    files = {
        "FEAT-0001-a.md": _live("a"),
        "FEAT-0002-gone.md": TOMBSTONE.format(
            slug="gone", edge="Reissued as", target="FEAT-0003-again.md"
        ),
        "FEAT-0003-again.md": _live("again"),
    }
    result = _run(tmp_path, files)
    assert set(result.routed) == set(files)
    assert result.routed["FEAT-0001-a.md"] == lint.CONTRACT_LIVE
    assert result.routed["FEAT-0002-gone.md"] == lint.CONTRACT_TOMBSTONE
    assert result.routed["FEAT-0003-again.md"] == lint.CONTRACT_LIVE


def test_ac0017_no_file_is_skipped(tmp_path: Path) -> None:
    """The routed set is compared against the directory, so a file the lint
    silently ignored fails here rather than passing as clean."""
    files = {f"FEAT-000{n}-f{n}.md": _live(f"f{n}") for n in range(1, 7)}
    directory = _corpus(tmp_path, files)
    result = lint.lint_corpus(tmp_path, directory)
    on_disk = {p.name for p in directory.iterdir() if p.is_file()}
    assert set(result.routed) == on_disk


def test_ac0017_a_tombstone_is_validated_not_skipped(tmp_path: Path) -> None:
    """A tombstone missing its third field is refused, which is what proves the
    branch validates rather than waves the file through."""
    bad = "\n".join(
        [
            "# Retired: a tombstone fixture",
            "",
            "- **Slug:** `gone`",
            "- **Tombstone:** 2026-09-21",
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0002-gone.md": bad})
    assert result.violations
    assert result.routed["FEAT-0002-gone.md"] == lint.CONTRACT_TOMBSTONE


def test_ac0017_a_tombstone_carrying_both_edges_is_refused(tmp_path: Path) -> None:
    """`exactly one of` is a biconditional, so both is as wrong as neither."""
    both = "\n".join(
        [
            "# Retired: a tombstone fixture",
            "",
            "- **Slug:** `gone`",
            "- **Tombstone:** 2026-09-21",
            "- **Reissued as:** FEAT-0003-again.md",
            "- **Retired:** superseded by nothing",
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0002-gone.md": both})
    assert result.violations


@pytest.mark.parametrize("edge", ["Reissued as", "Retired"])
def test_ac0017_a_conforming_tombstone_is_accepted(tmp_path: Path, edge: str) -> None:
    text = TOMBSTONE.format(slug="gone", edge=edge, target="a value")
    result = _run(tmp_path, {"FEAT-0002-gone.md": text})
    assert result.violations == [], result.violations
    assert result.exit_code == 0


def test_ac0017_a_tombstone_carrying_a_fourth_field_is_refused(
    tmp_path: Path,
) -> None:
    text = TOMBSTONE.format(
        slug="gone", edge="Retired", target="a value"
    ).replace("- **Tombstone:**", "- **Owner:** eugenelim\n- **Tombstone:**")
    result = _run(tmp_path, {"FEAT-0002-gone.md": text})
    assert result.violations


def test_ac0017_a_live_intent_is_not_held_to_the_tombstone_contract(
    tmp_path: Path,
) -> None:
    """The partition is exclusive: a live intent carries four fields and more,
    which the three-field contract would refuse."""
    result = _run(tmp_path, {"FEAT-0001-a.md": _live("a")})
    assert result.violations == []


def test_ac0017_the_partition_reads_only_the_preamble(tmp_path: Path) -> None:
    """A body-level `Tombstone:` line does not make a live intent a tombstone."""
    text = _live("a").replace(
        "An outcome sentence.",
        "An outcome sentence.\n\n- **Tombstone:** 2026-09-21",
    )
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.routed["FEAT-0001-a.md"] == lint.CONTRACT_LIVE
    assert result.violations == []


# ── AC-0005 at corpus scope ───────────────────────────────────────────────────


def _superseded(slug: str, *, by: str) -> str:
    """A live intent superseded by ``by``, in the split two-field form."""
    return _broken(slug, status="Superseded", extra=f"- **Superseded by:** {by}")


def test_ac0005_refuses_a_supersession_naming_no_live_slug(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _superseded("a", by="a-ghost"),
            "FEAT-0002-b.md": _live("b"),
        },
    )
    assert result.exit_code != 0
    assert any("a-ghost" in v.reason for v in result.violations)


def test_ac0005_names_the_intent_and_the_pointer_field(tmp_path: Path) -> None:
    """The lint supplies the intent; the reason supplies the slug; the field
    names the line an author edits to fix it."""
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _superseded("a", by="a-ghost"),
            "FEAT-0002-b.md": _live("b"),
        },
    )
    (violation,) = [v for v in result.violations if "a-ghost" in v.reason]
    assert violation.path == "FEAT-0001-a.md"
    assert violation.field == "Superseded by"


def test_ac0005_accepts_a_supersession_naming_a_live_slug(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _superseded("a", by="b"),
            "FEAT-0002-b.md": _live("b"),
        },
    )
    assert result.violations == [], result.violations


def test_ac0005_a_tombstone_slug_does_not_satisfy_a_supersession(
    tmp_path: Path,
) -> None:
    """`Superseded by:` resolves against a *live* intent's slug, so a retired
    artifact carrying the same slug does not answer it."""
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _superseded("a", by="gone"),
            "FEAT-0002-gone.md": TOMBSTONE.format(
                slug="gone", edge="Retired", target="a value"
            ),
        },
    )
    assert result.exit_code != 0


def test_ac0002_refuses_superseded_with_no_pointer_at_corpus_scope(
    tmp_path: Path,
) -> None:
    """The pairing rule is corpus-lint-only, so this is its end-to-end control
    rather than a second copy of a unit case."""
    result = _run(
        tmp_path,
        {"FEAT-0001-a.md": _broken("a", status="Superseded"), "FEAT-0002-b.md": _live("b")},
    )
    assert result.exit_code != 0
    assert any(v.field == "Superseded by" for v in result.violations)


def test_ac0003_refuses_a_stranded_pointer_at_corpus_scope(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _broken(
                "a", extra="- **Superseded by:** b"
            ),
            "FEAT-0002-b.md": _live("b"),
        },
    )
    assert result.exit_code != 0
    assert any(v.field == "Superseded by" for v in result.violations)


def test_ac0005_refuses_a_chain_through_a_superseded_intent(tmp_path: Path) -> None:
    """One hop, asserted where the partition is actually decided.

    `a` points at `b`, which is itself `Superseded`. The unit suite cannot
    settle this: it would have to hand `validate_supersession` a slug set built
    by the test, which asserts what the test believes the lint passes. Only the
    lint knows, so the control lives here.
    """
    result = _run(
        tmp_path,
        {
            "FEAT-0001-a.md": _superseded("a", by="b"),
            "FEAT-0002-b.md": _superseded("b", by="c"),
            "FEAT-0003-c.md": _live("c"),
        },
    )
    assert result.exit_code != 0
    assert any(
        v.path == "FEAT-0001-a.md" and "'b'" in v.reason for v in result.violations
    ), result.violations


def test_ac0005_a_two_intent_supersession_still_resolves(tmp_path: Path) -> None:
    """The accept case the chain rule must not swallow: `b` is live, so `a`
    resolves. Without this, refusing every pointer passes the case above."""
    result = _run(
        tmp_path,
        {"FEAT-0001-a.md": _superseded("a", by="b"), "FEAT-0002-b.md": _live("b")},
    )
    assert result.violations == [], result.violations


def test_ac0004_refuses_a_dated_record_without_evidence_at_corpus_scope(
    tmp_path: Path,
) -> None:
    result = _run(
        tmp_path,
        {"FEAT-0001-a.md": _broken("a", extra="- **Accepted:** 2026-09-20")},
    )
    assert result.exit_code != 0
    assert any(v.field == "Accepted" for v in result.violations)


# ── AC-0023: the progress report ──────────────────────────────────────────────


def test_ac0023_reports_one_line_per_intent(tmp_path: Path) -> None:
    files = {"FEAT-0001-a.md": _live("a"), "FEAT-0002-b.md": _live("b")}
    result = _run(tmp_path, files)
    assert set(result.progress) == set(files)


def test_ac0023_each_line_states_all_three_progress_fields(tmp_path: Path) -> None:
    result = _run(tmp_path, {"FEAT-0001-a.md": _live("a")})
    state = result.progress["FEAT-0001-a.md"]
    assert set(state) == {"De-risked", "Shaping-reviewed", "Decomposed"}


def test_ac0023_absence_alone_does_not_change_the_exit_code(tmp_path: Path) -> None:
    result = _run(tmp_path, {"FEAT-0001-a.md": _live("a")})
    assert all(v == "absent" for v in result.progress["FEAT-0001-a.md"].values())
    assert result.exit_code == 0


def test_ac0023_a_tombstone_carries_no_progress_line(tmp_path: Path) -> None:
    """The progress fields are the live contract's; a tombstone has none."""
    result = _run(
        tmp_path,
        {
            "FEAT-0002-gone.md": TOMBSTONE.format(
                slug="gone", edge="Retired", target="a value"
            )
        },
    )
    assert result.progress == {}


# ── AC-0015: a corpus it could not fully read is not clean ────────────────────


def test_ac0015_a_symlinked_entry_is_unreadable_and_not_clean(
    tmp_path: Path,
) -> None:
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    (directory / "FEAT-0002-link.md").symlink_to(directory / "FEAT-0001-a.md")

    result = lint.lint_corpus(tmp_path, directory)
    assert result.unreadable, "a link-like entry must be reported unreadable"
    assert result.exit_code != 0


def test_ac0015_an_unreadable_corpus_does_not_report_clean(tmp_path: Path) -> None:
    """The distinction AC-0015 draws is between `no violations` and `clean`."""
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    (directory / "FEAT-0002-link.md").symlink_to(directory / "FEAT-0001-a.md")

    result = lint.lint_corpus(tmp_path, directory)
    assert result.exit_code != 0
    assert not result.is_clean


def test_ac0015_a_missing_directory_is_not_clean(tmp_path: Path) -> None:
    result = lint.lint_corpus(tmp_path, tmp_path / "absent")
    assert result.exit_code != 0
    assert not result.is_clean


def test_ac0015_a_clean_corpus_is_clean(tmp_path: Path) -> None:
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    result = lint.lint_corpus(tmp_path, directory)
    assert result.is_clean
    assert result.unreadable == []


# ── The CLI ───────────────────────────────────────────────────────────────────


def test_the_cli_exits_zero_on_a_clean_corpus(tmp_path: Path, capsys) -> None:
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    code = lint.main(["--dir", str(directory.relative_to(tmp_path)),
                      "--root", str(tmp_path)])
    assert code == 0


def test_the_cli_exits_non_zero_and_names_the_fault(tmp_path: Path, capsys) -> None:
    directory = _corpus(
        tmp_path, {"FEAT-0001-a.md": _broken("a", status="Shipped")}
    )
    code = lint.main(["--dir", str(directory.relative_to(tmp_path)),
                      "--root", str(tmp_path)])
    assert code != 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "FEAT-0001-a.md" in combined
    assert "Status" in combined


# The two cases above fail during the directory *walk*, so they never reach the
# per-file read. These reach it: the walk lists the entry and opening or
# decoding it fails. Found by mutation — gutting the per-file `unreadable`
# record left every other test in this file green.


def test_ac0015_a_file_that_is_not_utf8_is_unreadable(tmp_path: Path) -> None:
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    (directory / "FEAT-0002-binary.md").write_bytes(b"# Intent\n\xff\xfe not utf-8\n")

    result = lint.lint_corpus(tmp_path, directory)
    assert any("FEAT-0002-binary.md" in entry for entry in result.unreadable)
    assert result.exit_code != 0
    assert not result.is_clean


def test_ac0015_a_file_past_the_byte_bound_is_unreadable(tmp_path: Path) -> None:
    directory = _corpus(tmp_path, {"FEAT-0001-a.md": _live("a")})
    oversize = directory / "FEAT-0003-huge.md"
    oversize.write_text("x" * (lint._MAX_BYTES + 1), encoding="utf-8")

    result = lint.lint_corpus(tmp_path, directory)
    assert any("FEAT-0003-huge.md" in entry for entry in result.unreadable)
    assert result.exit_code != 0


def test_ac0015_one_unreadable_file_does_not_stop_the_others(tmp_path: Path) -> None:
    """The run continues, so a single bad file does not hide every other fault.

    A lint that aborted here would report one problem per run, and a migration
    would take as many runs as it has faults.
    """
    directory = _corpus(
        tmp_path,
        {
            "FEAT-0001-a.md": _live("a"),
            "FEAT-0004-bad.md": _broken("bad", status="Shipped"),
        },
    )
    (directory / "FEAT-0002-binary.md").write_bytes(b"\xff\xfe")

    result = lint.lint_corpus(tmp_path, directory)
    assert result.unreadable
    assert {v.path for v in result.violations} == {"FEAT-0004-bad.md"}
    assert result.routed["FEAT-0001-a.md"] == lint.CONTRACT_LIVE
    # The unreadable file is not routed, because nothing could be read to route.
    assert "FEAT-0002-binary.md" not in result.routed


# ── Raised by adversarial review ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "item",
    [
        "- [ ] An unindented hyphen item",
        "  - [ ] An indented hyphen item",
        "* [ ] A star item",
        "+ [ ] A plus item",
        "- [x] A checked item",
    ],
)
def test_a_decomposition_item_is_recognized_in_every_markdown_spelling(
    tmp_path: Path, item: str
) -> None:
    """AC-0007 refuses a `direct-light` intent with no item, so a spelling the
    reader sees as an item and the check does not is a refused conforming
    intent."""
    text = "\n".join(
        [
            "# Intent: a fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** `a-fixture`",
            "- **Level:** feature",
            "- **Status:** Draft",
            "- **Decomposed:** 2026-09-22 direct-light",
            "",
            "## Outcome",
            "",
            "Text.",
            "",
            "## Decomposition",
            "",
            item,
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.violations == [], [f"{v.field}: {v.reason}" for v in result.violations]


@pytest.mark.parametrize("item", ["  - [ ]   ", "* [ ] ", "+ [ ]"])
def test_an_empty_item_is_refused_in_every_spelling(tmp_path: Path, item: str) -> None:
    """The mirror of the case above: widening what counts as an item must
    widen AC-0008's reach too, or an empty item hides behind its spelling."""
    text = "\n".join(
        [
            "# Intent: a fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** `a-fixture`",
            "- **Level:** feature",
            "- **Status:** Draft",
            "- **Decomposed:** 2026-09-22 direct-light",
            "",
            "## Outcome",
            "",
            "Text.",
            "",
            "## Decomposition",
            "",
            "- [ ] A real item",
            item,
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert "Decomposed" in {v.field for v in result.violations}


def test_every_directory_entry_is_accounted_for(tmp_path: Path) -> None:
    """Routed plus unreadable covers the directory, so no entry goes unmentioned.

    `routed` alone cannot carry this: a file that could not be read cannot be
    routed to a contract, so it is absent from `routed` by construction.
    """
    directory = _corpus(
        tmp_path,
        {"FEAT-0001-a.md": _live("a"), "FEAT-0004-bad.md": _broken("bad", status="Shipped")},
    )
    (directory / "FEAT-0002-binary.md").write_bytes(b"\xff\xfe")

    result = lint.lint_corpus(tmp_path, directory)
    on_disk = {p.name for p in directory.iterdir() if p.is_file()}
    assert result.accounted == on_disk
    assert "FEAT-0002-binary.md" not in result.routed


def test_the_traversal_bounds_reach_the_confinement_helper(
    tmp_path: Path, monkeypatch
) -> None:
    """Declaring a bound and not passing it would be a control that cannot fire.

    The real bounds sit far above any corpus, so the only way to observe that
    they are threaded through is to lower one and watch the walk refuse.
    """
    directory = _corpus(
        tmp_path, {"FEAT-0001-a.md": _live("a"), "FEAT-0002-b.md": _live("b")}
    )
    assert lint.lint_corpus(tmp_path, directory).is_clean

    monkeypatch.setattr(lint, "_MAX_FILES", 1)
    bounded = lint.lint_corpus(tmp_path, directory)
    assert bounded.unreadable, "a bound below the file count must refuse the walk"
    assert bounded.exit_code != 0
    assert not bounded.is_clean


# ── Raised by review round 2 ──────────────────────────────────────────────────


def test_two_nested_files_sharing_a_basename_are_both_validated(
    tmp_path: Path,
) -> None:
    """Keying by basename let one overwrite the other and vanish silently.

    The walk admits nesting, so this is reachable: one file was validated, the
    other was never routed, and the run could still report clean.
    """
    directory = _corpus(tmp_path, {})
    for sub in ("first", "second"):
        (directory / sub).mkdir()
    (directory / "first" / "FEAT-0001-a.md").write_text(_live("a"), encoding="utf-8")
    (directory / "second" / "FEAT-0001-a.md").write_text(
        _broken("b", status="Shipped"), encoding="utf-8"
    )

    result = lint.lint_corpus(tmp_path, directory)
    assert len(result.routed) == 2, result.routed
    assert result.exit_code != 0, "the nested non-conforming file must be seen"
    assert any("second" in v.path for v in result.violations), result.violations


@pytest.mark.parametrize("value", ["", " ", "<!-- retired, date to follow -->"])
def test_a_tombstone_field_with_no_value_still_partitions_as_a_tombstone(
    tmp_path: Path, value: str
) -> None:
    """The partition is a rule about a field's name.

    This module's own rule is that a value emptied by normalization makes the
    value absent, not the line, and a name rule still sees the field. An empty
    `Tombstone:` was routing as a live intent, which then held it to the wrong
    contract entirely.
    """
    text = "\n".join(
        [
            "# Retired: a fixture",
            "",
            "- **Slug:** `gone`",
            f"- **Tombstone:** {value}",
            "- **Retired:** a reason",
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0002-gone.md": text})
    assert result.routed["FEAT-0002-gone.md"] == lint.CONTRACT_TOMBSTONE


def test_the_summary_count_covers_every_entry(tmp_path: Path) -> None:
    """Live plus tombstone plus unreadable equals the reported file count.

    The how-to tells a reader to check exactly that sum, so a summary counting
    only routed files made the documented check fail on a correct run.
    """
    directory = _corpus(
        tmp_path,
        {
            "FEAT-0001-a.md": _live("a"),
            "FEAT-0002-gone.md": TOMBSTONE.format(
                slug="gone", edge="Retired", target="a reason"
            ),
        },
    )
    (directory / "FEAT-0003-binary.md").write_bytes(b"\xff\xfe")

    result = lint.lint_corpus(tmp_path, directory)
    live = sum(1 for c in result.routed.values() if c == lint.CONTRACT_LIVE)
    tombstone = sum(1 for c in result.routed.values() if c == lint.CONTRACT_TOMBSTONE)
    assert live + tombstone + len(result.unreadable) == len(result.accounted)
    assert len(result.accounted) == 3


# ── AC-0012: declared refusal registry ───────────────────────────────────────


def test_ac0012_lifecycle_refusal_classes_registry_exists() -> None:
    """The module declares its refusal classes in one enumerable place.

    A module-level tuple is the single authoritative enumeration; a rule added
    without a corresponding class name can be caught by asserting membership
    against this tuple rather than by substring-matching a reason.
    """
    shape = lint._shape
    assert hasattr(shape, "LIFECYCLE_REFUSAL_CLASSES"), (
        "intent_shape must expose LIFECYCLE_REFUSAL_CLASSES"
    )
    assert isinstance(shape.LIFECYCLE_REFUSAL_CLASSES, tuple)
    assert len(shape.LIFECYCLE_REFUSAL_CLASSES) > 0, (
        "LIFECYCLE_REFUSAL_CLASSES must name at least one refusal class"
    )


def test_ac0012_violation_carries_a_refusal_class_field_with_default() -> None:
    """Violation has a third field defaulting to the empty string.

    All seven existing construction sites pass just field and reason; the
    default must keep every one of them working unchanged.
    """
    shape = lint._shape
    v = shape.Violation("Status", "some reason")
    assert hasattr(v, "refusal_class"), "Violation must have a refusal_class field"
    assert v.refusal_class == "", (
        "refusal_class must default to '' so existing sites need no change"
    )


def test_ac0012_a_violation_may_carry_a_registry_member_as_its_class() -> None:
    """A Violation constructed with a class drawn from the registry carries it."""
    shape = lint._shape
    registry = shape.LIFECYCLE_REFUSAL_CLASSES
    cls = registry[0]
    v = shape.Violation("Status", "some reason", refusal_class=cls)
    assert v.refusal_class == cls
    assert v.refusal_class in registry


# ── State-coherence rules ─────────────────────────────────────────────────────
# AC-0001, AC-0002, AC-0003, AC-0004: delivered-terminal rules.
# AC-0005, AC-0006: positive paths — own fixtures so an implementation that
#   refuses every Fulfilled intent cannot pass them.
# AC-0007, AC-0008, AC-0009: records beside a state that did not earn them.
# AC-0011: each refusal names the file and the record.
# AC-0012: each refusal carries a class from LIFECYCLE_REFUSAL_CLASSES.

_VALID_ACCEPTED = "2026-09-20 by eugenelim"
_VALID_FULFILLED = "2026-09-22 by eugenelim"


def test_state_coherence_refuses_fulfilled_without_accepted_record(
    tmp_path: Path,
) -> None:
    """AC-0001: a Fulfilled intent requires an Accepted: record."""
    text = _broken("a", status="Fulfilled", extra=f"- **Fulfilled:** {_VALID_FULFILLED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Accepted" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Fulfilled without Accepted: must produce an Accepted violation"


def test_state_coherence_refuses_cancelled_without_accepted_record(
    tmp_path: Path,
) -> None:
    """AC-0002: a Cancelled intent requires an Accepted: record."""
    result = _run(tmp_path, {"FEAT-0001-a.md": _broken("a", status="Cancelled")})
    assert result.exit_code != 0
    assert any(
        v.field == "Accepted" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Cancelled without Accepted: must produce an Accepted violation"


def test_state_coherence_accepts_withdrawn_without_accepted_record(
    tmp_path: Path,
) -> None:
    """AC-0003: Withdrawn needs no Accepted: record — abandoning an unratified
    bet needs no ratification."""
    result = _run(tmp_path, {"FEAT-0001-a.md": _broken("a", status="Withdrawn")})
    assert result.violations == [], result.violations


def test_state_coherence_refuses_fulfilled_without_fulfilled_record(
    tmp_path: Path,
) -> None:
    """AC-0004: a Fulfilled intent requires a Fulfilled: record."""
    text = _broken("a", status="Fulfilled", extra=f"- **Accepted:** {_VALID_ACCEPTED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Fulfilled" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Fulfilled without Fulfilled: must produce a Fulfilled violation"


def test_state_coherence_accepts_fulfilled_with_both_records(tmp_path: Path) -> None:
    """AC-0005: own fixture — a Fulfilled intent carrying both records is accepted.

    Without its own fixture, an implementation that refuses every Fulfilled
    intent satisfies every refusal criterion; this case catches it.
    """
    extra = f"- **Accepted:** {_VALID_ACCEPTED}\n- **Fulfilled:** {_VALID_FULFILLED}"
    text = _broken("a", status="Fulfilled", extra=extra)
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.violations == [], result.violations


def test_state_coherence_accepts_cancelled_with_accepted_record(
    tmp_path: Path,
) -> None:
    """AC-0006: own fixture — a Cancelled intent carrying Accepted: is accepted."""
    text = _broken("a", status="Cancelled", extra=f"- **Accepted:** {_VALID_ACCEPTED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.violations == [], result.violations


def test_state_coherence_refuses_draft_with_accepted_record(tmp_path: Path) -> None:
    """AC-0007: Draft means open — an Accepted: record is not allowed."""
    text = _broken("a", extra=f"- **Accepted:** {_VALID_ACCEPTED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Accepted" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Draft with Accepted: must produce an Accepted violation"


def test_state_coherence_refuses_draft_with_fulfilled_record(tmp_path: Path) -> None:
    """AC-0007: Draft means open — a Fulfilled: record is not allowed."""
    text = _broken("a", extra=f"- **Fulfilled:** {_VALID_FULFILLED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Fulfilled" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Draft with Fulfilled: must produce a Fulfilled violation"


def test_state_coherence_refuses_accepted_with_fulfilled_record(
    tmp_path: Path,
) -> None:
    """AC-0008: Accepted has not yet delivered — a Fulfilled: record is not allowed."""
    text = _broken("a", status="Accepted", extra=f"- **Fulfilled:** {_VALID_FULFILLED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Fulfilled" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Accepted with Fulfilled: must produce a Fulfilled violation"


def test_state_coherence_refuses_cancelled_with_fulfilled_record(
    tmp_path: Path,
) -> None:
    """AC-0009: Cancelled did not deliver — a Fulfilled: record is not allowed."""
    extra = f"- **Accepted:** {_VALID_ACCEPTED}\n- **Fulfilled:** {_VALID_FULFILLED}"
    text = _broken("a", status="Cancelled", extra=extra)
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Fulfilled" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Cancelled with Fulfilled: must produce a Fulfilled violation"


def test_state_coherence_refuses_withdrawn_with_fulfilled_record(
    tmp_path: Path,
) -> None:
    """AC-0009: Withdrawn did not deliver — a Fulfilled: record is not allowed."""
    text = _broken("a", status="Withdrawn", extra=f"- **Fulfilled:** {_VALID_FULFILLED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert result.exit_code != 0
    assert any(
        v.field == "Fulfilled" and v.path == "FEAT-0001-a.md"
        for v in result.violations
    ), "Withdrawn with Fulfilled: must produce a Fulfilled violation"


def test_state_coherence_violation_names_the_path_and_the_record(
    tmp_path: Path,
) -> None:
    """AC-0011: each refusal names the corpus-relative file and the record at fault."""
    text = _broken("a", status="Fulfilled", extra=f"- **Fulfilled:** {_VALID_FULFILLED}")
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    # Only the Accepted: violation: Fulfilled: is present, so only Accepted: is missing.
    accepted_violations = [v for v in result.violations if v.field == "Accepted"]
    assert len(accepted_violations) == 1
    (violation,) = accepted_violations
    assert violation.path == "FEAT-0001-a.md"
    assert violation.field == "Accepted"


def test_state_coherence_violation_carries_a_registry_refusal_class() -> None:
    """AC-0012: every state-coherence refusal sets refusal_class to a registry member."""
    shape = lint._shape
    # Fulfilled without either record: two violations, both must carry a class.
    text = _broken("a", status="Fulfilled")
    violations = shape.validate_corpus_scoped(text, set())
    assert violations
    registry = shape.LIFECYCLE_REFUSAL_CLASSES
    for v in violations:
        assert v.refusal_class in registry, (
            f"violation for {v.field!r} carries refusal_class {v.refusal_class!r} "
            f"which is not in {registry}"
        )


def test_validate_corpus_scoped_delegates_to_both_rule_sets() -> None:
    """validate_corpus_scoped reaches both supersession and state-coherence rules.

    One fixture violates only supersession; one violates only state coherence.
    A delegation dropped from the aggregator reds for the affected side.
    """
    shape = lint._shape

    # Supersession only: Status: Superseded with no Superseded by:
    supersession_only = _broken("a", status="Superseded")
    assert shape.validate_corpus_scoped(supersession_only, set()), (
        "supersession violation must reach validate_corpus_scoped"
    )

    # State coherence only: Status: Fulfilled with no records
    # (no Superseded status, no Superseded by: — supersession is quiet)
    state_only = _broken("a", status="Fulfilled")
    assert shape.validate_corpus_scoped(state_only, set()), (
        "state-coherence violation must reach validate_corpus_scoped"
    )


def test_a_four_space_indented_checkbox_is_not_an_item(tmp_path: Path) -> None:
    """CommonMark renders four-space indentation as a code block.

    Counting it would credit an item no reader can see, which is the opposite
    of what requiring an item is for.
    """
    text = "\n".join(
        [
            "# Intent: a fixture",
            "",
            "- **Owner:** eugenelim",
            "- **Slug:** `a-fixture`",
            "- **Level:** feature",
            "- **Status:** Draft",
            "- **Decomposed:** 2026-09-22 direct-light",
            "",
            "## Outcome",
            "",
            "Text.",
            "",
            "## Decomposition",
            "",
            "    - [ ] This is a code block, not an item",
            "",
        ]
    )
    result = _run(tmp_path, {"FEAT-0001-a.md": text})
    assert "Decomposed" in {v.field for v in result.violations}
