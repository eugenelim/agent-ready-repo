#!/usr/bin/env python3
"""Pytest coverage for the brief-coverage rollup.

Builds fixture brief + spec trees in a tempdir and runs the linter as a
subprocess against the documented `python <skill>/scripts/lint-brief-coverage.py
--root <dir>` invocation — the same shape the CI gate uses (not a
synthesised import, so the real `from .X import Y`-free entry point is
exercised). Covers each acceptance case red-and-green: rollup of a mixed map,
all-Shipped → delivered, empty map → not delivered, no-brief no-op, untracked
back-link as informational, and a hand-edited stale cell as the fail-closed
drift case.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "author-delivery-brief"
LINTER = _SKILL_DIR / "scripts" / "lint-brief-coverage.py"
if not LINTER.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {LINTER} — check the parents[] depth")


def expect(cond: bool, msg: str) -> None:
    """Assert a condition through pytest instead of aggregate state."""
    assert cond, msg


def write_spec(root: Path, slug: str, status: str, brief: str | None = None) -> None:
    p = root / "docs" / "specs" / slug / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    header = f"# Spec: {slug}\n\n- **Status:** {status}\n"
    if brief is not None:
        header += f"- **Brief:** {brief}\n"
    header += "\n## Acceptance Criteria\n\n- [ ] AC1\n"
    p.write_text(header, encoding="utf-8")


def write_brief(
    root: Path,
    slug: str,
    rows: list[tuple[str, str]],
    stem: str | None = None,
    status: str = "Ready",
) -> None:
    """Write a brief with a two-column Spec map. `rows` is (spec-slug, recorded-status).

    A ``Shipped`` brief automatically includes a ``Cut-closed:`` record so that
    existing tests are not refused by AC-0013; pass raw brief text to
    ``write_brief_raw`` when precise preamble control is needed.
    """
    name = stem if stem is not None else slug
    p = root / "docs" / "product" / "briefs" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# Brief: {slug}\n\n- **Status:** {status}\n"
        f"- **Slug:** `{slug}`\n"
    )
    if status == "Shipped":
        body += "- **Cut-closed:** 2026-01-01 all mapped specs shipped.\n"
    body += "\n## Spec map\n\n"
    body += "| Spec | Status |\n| --- | --- |\n"
    for spec_slug, recorded in rows:
        body += f"| `{spec_slug}` | {recorded} |\n"
    p.write_text(body, encoding="utf-8")


def write_brief_raw(root: Path, stem: str, body: str) -> Path:
    """Write a brief with exact content. Returns the path written."""
    p = root / "docs" / "product" / "briefs" / f"{stem}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def run_lint(root: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_mixed_map_not_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Implementing", brief="myb")
        write_brief(
            root,
            "myb",
            [("alpha", "Shipped"), ("beta", "Implementing")],
            status="Executing",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"mixed map should exit 0, got {rc}: {err}")
        expect("shipped" in out.lower(), f"alpha should roll up shipped: {out}")
        expect("implementing" in out.lower(), f"beta should roll up implementing: {out}")
        expect("not delivered" in out.lower(), f"mixed map → not delivered: {out}")


def test_explicitly_shipped_all_shipped_map_is_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Shipped", brief="myb")
        write_brief(
            root,
            "myb",
            [("alpha", "Shipped"), ("beta", "Shipped")],
            status="Shipped",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"all-shipped should exit 0, got {rc}: {err}")
        # "': delivered" disambiguates from "': not delivered".
        expect("': delivered" in out, f"all-shipped brief → delivered: {out}")


def test_all_shipped_map_requires_explicit_shipped_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped")], status="Executing")
        rc, out, err = run_lint(root)
        expect(rc == 0, f"executing all-shipped map remains valid: {err}")
        expect("': not delivered" in out, f"open brief must not auto-close: {out}")


def test_statusless_all_shipped_map_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped")], status="Executing")
        brief = root / "docs/product/briefs/myb.md"
        brief.write_text(
            brief.read_text(encoding="utf-8").replace("- **Status:** Executing\n", ""),
            encoding="utf-8",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"missing lifecycle must fail closed: {out}")
        # AC-0011: absent status reports "brief status is absent", not "contradicts".
        expect("brief status" in err.lower() and "absent" in err.lower(), err)
        expect("': not delivered" in out, out)


def test_shipped_requires_nonempty_all_shipped_map() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "myb", [], status="Shipped")
        rc, out, err = run_lint(root)
        expect(rc == 1, f"empty Shipped map must fail: {out}")
        expect("': not delivered" in out, out)
        expect("brief lifecycle" in err.lower(), err)
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: lifecycle refusal must name 'docs/product/briefs/myb.md': {err}",
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Approved", brief="myb")
        write_brief(root, "myb", [("alpha", "Approved")], status="Shipped")
        rc, out, err = run_lint(root)
        expect(rc == 1, f"non-shipped child must block Shipped brief: {out}")
        expect("': not delivered" in out, out)
        expect("brief lifecycle" in err.lower(), err)
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: lifecycle refusal must name 'docs/product/briefs/myb.md': {err}",
        )


@pytest.mark.parametrize(
    ("brief_status", "child_status", "expected_rc"),
    [
        ("Withdrawn", "Approved", 0),
        ("Withdrawn", "Implementing", 1),
        ("Withdrawn", "Shipped", 1),
        ("Cancelled", "Approved", 1),
        ("Cancelled", "Implementing", 0),
        ("Cancelled", "Shipped", 0),
    ],
    ids=[
        "withdrawn-approved",
        "withdrawn-implementing",
        "withdrawn-shipped",
        "cancelled-approved",
        "cancelled-implementing",
        "cancelled-shipped",
    ],
)
def test_terminated_brief_child_scope(
    brief_status: str,
    child_status: str,
    expected_rc: int,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", child_status, brief="myb")
        write_brief(root, "myb", [("alpha", child_status)], status=brief_status)
        rc, out, err = run_lint(root)
        expect(rc == expected_rc, f"{brief_status}/{child_status}: {out}{err}")
        expect("': not delivered" in out, out)


def test_empty_map_not_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "emptyb", [])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"empty map should exit 0, got {rc}: {err}")
        expect("not delivered" in out.lower(),
               f"empty map is never vacuously delivered: {out}")
        expect("': delivered" not in out,
               f"empty map must NOT report delivered: {out}")


def test_governance_reference_is_rejected_from_spec_map() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(
            root,
            "myb",
            [
                ("docs/rfc/0099-razor.md", "<auto>"),
                ("[ADR-0098](../../adr/0098-artifact-admission.md)", "<auto>"),
            ],
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"governance row must fail closed, got {rc}: {out}")
        expect("governance reference" in err.lower(), err)
        expect("Governance references" in err, err)
        expect("ADR-0098" in err, err)
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: governance refusal must name 'docs/product/briefs/myb.md': {err}",
        )


def test_no_brief_noop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # spec but no brief
        rc, out, err = run_lint(root)
        expect(rc == 0, f"no brief should exit 0, got {rc}: {err}")
        expect(err.strip() == "", f"no brief → no diagnostic on stderr: {err!r}")
        expect(out.strip() == "", f"no brief → no diagnostic on stdout: {out!r}")


def test_template_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A `_template.md` placeholder in the briefs dir must NOT be treated
        # as a real brief (it ships with the pack and projects into repos).
        write_brief(root, "<one-line outcome>", [("<feature-slug>", "<auto>")],
                    stem="_template")
        rc, out, err = run_lint(root)
        expect(rc == 0, f"template-only briefs dir should exit 0, got {rc}: {err}")
        expect(out.strip() == "" and err.strip() == "",
               f"_template.md must be skipped (no diagnostic): out={out!r} err={err!r}")


def test_untracked_backlink_informational() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # gamma back-links myb but is NOT in myb's Spec map → untracked.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "gamma", "Draft", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped")], status="Executing")
        rc, out, err = run_lint(root)
        combined = (out + err).lower()
        expect(rc == 0, f"untracked back-link must NOT be an error, got {rc}: {err}")
        expect("untracked" in combined, f"gamma should be reported untracked: {out}{err}")
        expect("gamma" in combined, f"untracked spec named: {out}{err}")


@pytest.mark.parametrize(
    "brief_status",
    ["Ready", "Withdrawn"],
    ids=["ready", "withdrawn"],
)
def test_untracked_backlink_contributes_execution_evidence(
    brief_status: str,
) -> None:
    """A missing Spec-map row cannot hide a back-linked shipped child."""

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief(root, "myb", [], status=brief_status)
        rc, out, err = run_lint(root)
        expect(rc == 1, f"{brief_status} must reject shipped child evidence: {out}")
        expect("brief lifecycle" in err.lower(), err)
        expect("untracked" in out.lower(), out)


def test_stale_cell_drifts_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # beta is actually Shipped, but the brief's Spec map still records
        # Implementing — a hand-edited stale cell. Fail closed.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Shipped", brief="myb")
        write_brief(
            root,
            "myb",
            [("alpha", "Shipped"), ("beta", "Implementing")],
            status="Shipped",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"stale recorded cell should exit 1, got {rc}: {out}")
        expect("stale" in err.lower(), f"drift message should name staleness: {err}")
        expect("beta" in err, f"drift message should name the spec: {err}")
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: drift refusal must name 'docs/product/briefs/myb.md': {err}",
        )


def test_unset_cell_is_not_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # An `<auto>` / unset cell means "not yet derived" — report, don't fail.
        write_spec(root, "alpha", "Implementing", brief="myb")
        write_brief(root, "myb", [("alpha", "<auto>")], status="Executing")
        rc, out, err = run_lint(root)
        expect(rc == 0, f"unset <auto> cell must not be drift, got {rc}: {err}")
        expect("implementing" in out.lower(), f"derived status still reported: {out}")


def test_slug_differs_from_filename() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The brief's Slug field (real-slug) differs from its filename stem
        # (shape-a) — the shipped examples do exactly this. A spec back-links
        # the SLUG; untracked detection must join on the slug, not the stem.
        write_spec(root, "gamma", "Draft", brief="real-slug")
        write_brief(root, "real-slug", [("alpha", "<auto>")], stem="shape-a")
        rc, out, err = run_lint(root)
        combined = (out + err).lower()
        expect(rc == 0, f"untracked is informational, got {rc}: {err}")
        expect("gamma" in combined and "untracked" in combined,
               f"gamma back-links by slug, must be untracked: {out}{err}")


def test_path_form_backlink_joins_to_brief() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The canonical `Brief:` spelling is the brief's repository-relative
        # path — the form the spec template, the owning guide, and
        # workspace-status provenance all require. It must resolve to the same
        # brief as the bare slug, or untracked detection silently stops firing
        # for every path-form spec.
        write_spec(root, "gamma", "Draft", brief="docs/product/briefs/myb.md")
        write_brief(root, "myb", [("alpha", "<auto>")])
        rc, out, err = run_lint(root)
        combined = (out + err).lower()
        expect(rc == 0, f"untracked is informational, got {rc}: {err}")
        expect("gamma" in combined and "untracked" in combined,
               f"path-form back-link must resolve to the brief: {out}{err}")


def test_path_form_backlink_attributes_to_the_named_brief() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Two real briefs, and a spec naming the SECOND one's path. The path
        # form must attribute gamma to `other` and to `other` only — a join
        # that ignored the path (or matched loosely) would either drop gamma
        # entirely or report it under both briefs.
        write_spec(root, "gamma", "Draft", brief="docs/product/briefs/other.md")
        write_brief(root, "myb", [("alpha", "<auto>")])
        write_brief(root, "other", [("beta", "<auto>")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"untracked is informational, got {rc}: {err}")

        # Split the report into per-brief sections so attribution is checked,
        # not just presence somewhere in the output.
        sections: dict[str, list[str]] = {}
        current = None
        for line in (out + err).splitlines():
            marker = "lint-brief-coverage: brief '"
            if marker in line:
                current = line.split(marker, 1)[1].split("'", 1)[0]
                sections[current] = []
            elif current is not None:
                sections[current].append(line)

        expect("other" in sections and "myb" in sections,
               f"both briefs should be reported: {out}{err}")
        expect(any("gamma" in ln and "untracked" in ln for ln in sections["other"]),
               f"gamma names other's path, must be untracked under it: {out}{err}")
        expect(not any("gamma" in ln for ln in sections["myb"]),
               f"gamma must not be attributed to myb: {out}{err}")


def test_typed_form_backlink_joins_to_brief() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # `brief:<slug>` is the canonical `Brief:` spelling (RFC-0103 D3). It
        # must resolve to the brief exactly as the path and bare-slug forms
        # do, or the coverage join does not converge on the canonical form —
        # AC-0010.
        write_spec(root, "gamma", "Draft", brief="brief:myb")
        write_brief(root, "myb", [("alpha", "<auto>")])
        rc, out, err = run_lint(root)
        combined = (out + err).lower()
        expect(rc == 0, f"untracked is informational, got {rc}: {err}")
        expect("gamma" in combined and "untracked" in combined,
               f"typed-form back-link must resolve to the brief: {out}{err}")


def test_prose_pipe_after_table_is_not_a_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        p = root / "docs" / "product" / "briefs" / "myb.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n## Spec map\n\n"
            "| Spec | Status |\n| --- | --- |\n| `alpha` | Shipped |\n\n"
            "Note: rows are added as slices ship | one per spec.\n",
            encoding="utf-8",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"prose pipe must not trip drift exit 1, got {rc}: {err}")
        expect("stale" not in err.lower(), f"no phantom drift row: {err}")


def test_lowercase_status_token_still_delivers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "shipped", brief="myb")  # lowercase token
        write_brief(root, "myb", [("alpha", "Shipped")], status="Shipped")
        rc, out, err = run_lint(root)
        expect(rc == 0, f"no drift expected, got {rc}: {err}")
        expect("': delivered" in out,
               f"lowercase 'shipped' must still count as delivered: {out}")


def test_placeholder_brief_value_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Draft", brief="<slug>")  # template placeholder
        write_brief(root, "myb", [("beta", "<auto>")])
        rc, out, err = run_lint(root)
        combined = out + err
        expect(rc == 0, f"placeholder back-link must not error, got {rc}: {err}")
        expect("<slug>" not in combined,
               f"placeholder must not surface as a tracked/untracked slug: {combined}")


def test_annotated_recorded_cell_not_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A recorded cell annotated the same way a spec's own Status field may
        # be (`Shipped (2026-06-01)`) must not misreport as drift against a
        # derived `Shipped` — the recorded side is normalized symmetrically.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief(
            root,
            "myb",
            [("alpha", "Shipped (2026-06-01)")],
            status="Shipped",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"annotated recorded cell must not drift, got {rc}: {err}")
        expect("stale" not in err.lower(), f"no false drift on annotated cell: {err}")
        expect("': delivered" in out, f"annotated-cell brief still delivered: {out}")


# ── AC-0013: Shipped brief without Cut-closed: is refused ────────────────────


def test_shipped_brief_without_cut_closed_refused() -> None:
    """AC-0013: a Shipped brief with no Cut-closed: record is refused."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        # Write Shipped brief manually WITHOUT Cut-closed:.
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n| `alpha` | Shipped |\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"Shipped without Cut-closed: must fail, got {rc}: {err}")
        expect("cut-closed" in err.lower(), f"refusal must name Cut-closed: {err}")
        expect("shipped" in err.lower(), f"refusal must name Shipped status: {err}")
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: declaration-matrix refusal must name 'docs/product/briefs/myb.md': {err}",
        )


# ── AC-0024: no second scan of any brief preamble field ─────────────────────


def test_no_second_brief_field_scan_ac0024() -> None:
    """AC-0024: no second scan of any brief preamble field survives in the lint."""
    source = LINTER.read_text(encoding="utf-8")
    # No surviving second readers for brief preamble fields.
    assert "def parse_brief_status" not in source, (
        "parse_brief_status still defined — use brief_shape.get_status"
    )
    assert "def parse_brief_slug" not in source, (
        "parse_brief_slug still defined — use brief_shape.get_slug"
    )
    # No surviving second vocabulary copy.
    assert "_BRIEF_STATUSES" not in source, (
        "_BRIEF_STATUSES still defined — use brief_shape.BRIEF_STATUSES"
    )
    # No surviving second predicate copy.
    assert "def _brief_lifecycle_is_valid" not in source, (
        "_brief_lifecycle_is_valid still defined — use brief_shape.is_lifecycle_valid"
    )
    # No surviving second tokenizer definition (it is loaded from brief_shape).
    assert "def extract_token" not in source, (
        "extract_token still defined locally — load it from brief_shape"
    )


# ── AC-0007: bounded reader at the consumer ──────────────────────────────────
# Each fixture is a differential: the lint's output differs between a bounded
# and an unbounded read.  Five suppressing rules hide the field; AC-0003 puts
# a decoy in the comment and a live value after -->.

# ── Status: under suppressing rules ─────────────────────────────────────────

@pytest.mark.parametrize(
    ("rule_id", "body"),
    [
        # AC-0001: Status: only below the first ## heading.
        (
            "ac0001",
            "# Brief: myb\n\n- **Slug:** `myb`\n\n## Section\n\n- **Status:** Draft\n",
        ),
        # AC-0002: Status: only inside a spanning HTML comment.
        (
            "ac0002",
            "# Brief: myb\n\n- **Slug:** `myb`\n<!--\n- **Status:** Draft\n-->\n",
        ),
        # AC-0004: Status: as an ATX heading line.
        (
            "ac0004",
            "# Brief: myb\n\n- **Slug:** `myb`\n# - **Status:** Draft\n",
        ),
        # AC-0005: Status: inside a blockquote.
        (
            "ac0005",
            "# Brief: myb\n\n- **Slug:** `myb`\n> - **Status:** Draft\n",
        ),
        # AC-0006: Status: inside an unclosed HTML comment.
        (
            "ac0006",
            "# Brief: myb\n\n- **Slug:** `myb`\n<!--\n- **Status:** Draft\n",
        ),
    ],
    ids=["ac0001", "ac0002", "ac0004", "ac0005", "ac0006"],
)
def test_ac0007_status_hidden_by_suppressing_rule(rule_id: str, body: str) -> None:
    """AC-0007: bounded reader hides Status: placed in a forbidden location.

    Each fixture is differential: an unbounded scan would read the Status:
    and not fire AC-0011.  The bounded reader does not, so AC-0011 fires.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(root, "myb", body)
        rc, out, err = run_lint(root)
        expect(rc == 1, f"{rule_id}: hidden Status: must cause AC-0011: rc={rc} err={err}")
        expect(
            "brief status" in err.lower() and "absent" in err.lower(),
            f"{rule_id}: AC-0011 message must say 'brief status ... absent': {err}",
        )


# ── Cut-closed: under suppressing rules ─────────────────────────────────────

@pytest.mark.parametrize(
    ("rule_id", "body"),
    [
        # AC-0001: Cut-closed: only below the first ## heading.
        (
            "ac0001",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n\n"
            "## Section\n\n- **Cut-closed:** 2026-01-01 some evidence\n",
        ),
        # AC-0002: Cut-closed: only inside a spanning HTML comment.
        (
            "ac0002",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n"
            "<!--\n- **Cut-closed:** 2026-01-01 some evidence\n-->\n",
        ),
        # AC-0004: Cut-closed: as an ATX heading line.
        (
            "ac0004",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n"
            "# - **Cut-closed:** 2026-01-01 some evidence\n",
        ),
        # AC-0005: Cut-closed: inside a blockquote.
        (
            "ac0005",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n"
            "> - **Cut-closed:** 2026-01-01 some evidence\n",
        ),
    ],
    ids=["ac0001", "ac0002", "ac0004", "ac0005"],
)
def test_ac0007_cut_closed_hidden_by_suppressing_rule(rule_id: str, body: str) -> None:
    """AC-0007: bounded reader hides Cut-closed: placed in a forbidden location.

    Fixture is a Draft brief.  Bounded: Cut-closed: absent → no AC-0016
    refusal → rc=0.  Unbounded would read Cut-closed: → AC-0016 fires → rc=1.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(root, "myb", body)
        rc, out, err = run_lint(root)
        expect(
            rc == 0,
            f"{rule_id}: bounded hides Cut-closed: → no AC-0016 refusal: rc={rc} err={err}",
        )
        expect(
            "cut-closed" not in err.lower(),
            f"{rule_id}: no Cut-closed: refusal expected: {err}",
        )


def test_ac0007_cut_closed_hidden_by_ac0006() -> None:
    """AC-0007/AC-0006: unclosed comment invalidates all fields including Cut-closed:.

    Bounded: preamble = [] (unclosed comment) → status absent (AC-0011) and
    Cut-closed: absent (no AC-0016).  Unbounded would read Draft status and
    Cut-closed: → AC-0016 fires with a different message.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n"
            "<!--\n- **Cut-closed:** 2026-01-01 some evidence\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"unclosed comment causes AC-0011, got rc={rc}: {err}")
        # Bounded fires AC-0011 ("brief status is absent"), NOT AC-0016.
        expect(
            "absent" in err.lower(),
            f"AC-0006: bounded must report status absent, not Cut-closed: error: {err}",
        )
        expect(
            "cut-closed" not in err.lower(),
            f"AC-0006: no Cut-closed: refusal when preamble is invalidated: {err}",
        )


# ── Slug: under suppressing rules ────────────────────────────────────────────

@pytest.mark.parametrize(
    ("rule_id", "body"),
    [
        # AC-0001: Slug: only below the first ## heading.
        (
            "ac0001",
            "# Brief: myb\n\n- **Status:** Ready\n\n"
            "## Section\n\n- **Slug:** `different-slug`\n",
        ),
        # AC-0002: Slug: only inside a spanning HTML comment.
        (
            "ac0002",
            "# Brief: myb\n\n- **Status:** Ready\n"
            "<!--\n- **Slug:** `different-slug`\n-->\n",
        ),
        # AC-0004: Slug: as an ATX heading line.
        (
            "ac0004",
            "# Brief: myb\n\n- **Status:** Ready\n# - **Slug:** `different-slug`\n",
        ),
        # AC-0005: Slug: inside a blockquote.
        (
            "ac0005",
            "# Brief: myb\n\n- **Status:** Ready\n> - **Slug:** `different-slug`\n",
        ),
        # AC-0006: Slug: inside an unclosed HTML comment.
        (
            "ac0006",
            "# Brief: myb\n\n<!--\n- **Status:** Ready\n- **Slug:** `different-slug`\n",
        ),
    ],
    ids=["ac0001", "ac0002", "ac0004", "ac0005", "ac0006"],
)
def test_ac0007_slug_hidden_by_suppressing_rule(rule_id: str, body: str) -> None:
    """AC-0007: bounded reader hides Slug: placed in a forbidden location.

    Slug: value differs from the filename stem ('myb') so the stem fallback
    cannot mask the fix.  Bounded: Slug absent → fallback slug = 'myb'.
    Unbounded would read 'different-slug'.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(root, "myb", body)
        rc, out, err = run_lint(root)
        # Regardless of rc (ac0006 fires AC-0011), the slug in the output
        # line must be the fallback stem, not the hidden value.
        expect(
            "brief 'myb'" in out,
            f"{rule_id}: bounded slug must fall back to stem 'myb': {out}",
        )
        expect(
            "brief 'different-slug'" not in out,
            f"{rule_id}: hidden Slug: 'different-slug' must not appear: {out}",
        )


# ── AC-0003: accepting rule — decoy in comment, live value after --> ─────────


def test_ac0007_ac0003_status_live_wins_over_commented_decoy() -> None:
    """AC-0007/AC-0003: live Status: after --> wins over commented-out decoy.

    Decoy token is out-of-vocabulary so unbounded read fires AC-0010.
    Bounded reads the live valid token → no refusal from this check.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # BADTOKEN is out-of-vocabulary; unbounded would read it and fire AC-0010.
        # The live value 'Ready' is after the closing -->.
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Slug:** `myb`\n"
            "<!--\n- **Status:** BADTOKEN\n-->\n"
            "- **Status:** Ready\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"bounded reads live 'Ready' → no refusal: rc={rc} err={err}")
        expect("vocabulary" not in err.lower(), f"no AC-0010 error expected: {err}")


def test_ac0007_ac0003_cut_closed_live_wins_over_commented_decoy() -> None:
    """AC-0007/AC-0003: live Cut-closed: after --> wins over commented-out malformed decoy.

    Bounded: reads valid live value → no AC-0008 refusal.
    Unbounded: reads malformed decoy → AC-0008 fires.
    Ready brief is child-coherent with no children.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Ready\n- **Slug:** `myb`\n"
            "<!--\n- **Cut-closed:** not-a-date malformed\n-->\n"
            "- **Cut-closed:** 2026-01-01 valid evidence text\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"bounded reads valid Cut-closed: → no AC-0008: rc={rc} err={err}")
        expect("cut-closed" not in err.lower(), f"no Cut-closed: error expected: {err}")


def test_ac0007_ac0003_slug_live_wins_over_commented_decoy() -> None:
    """AC-0007/AC-0003: live Slug: after --> wins over commented-out decoy.

    Bounded: reads live slug → output line shows 'live-slug'.
    Unbounded: reads decoy slug → output line shows 'decoy-slug'.
    Both slugs differ from the stem 'myb' so the stem fallback cannot mask it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Ready\n"
            "<!--\n- **Slug:** `decoy-slug`\n-->\n"
            "- **Slug:** `live-slug`\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"Ready with no children is valid: rc={rc} err={err}")
        expect("brief 'live-slug'" in out, f"bounded slug is live-slug: {out}")
        expect("brief 'decoy-slug'" not in out, f"decoy slug must not appear: {out}")


# ── AC-0025: ## Spec map inside comment does not open the section ─────────────


def test_ac0025_specmap_heading_in_comment_does_not_open() -> None:
    """AC-0025: a ## Spec map heading inside a comment does not open the section.

    Without the fix: rows below the commented heading are parsed and alpha
    (Shipped) is a child of a Ready brief → lifecycle invalid → rc=1.
    With the fix: section never opens → no rows → Ready with no children → rc=0.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no back-link
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Ready\n- **Slug:** `myb`\n\n"
            "<!--\n## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| `alpha` | Shipped |\n-->\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"commented ## Spec map must not open section: rc={rc} err={err}")
        expect("brief lifecycle" not in err.lower(), err)


# ── AC-0026: row inside comment is not a Spec-map row (two arms) ─────────────


def test_ac0026_commented_row_no_backlink_leaves_child_set() -> None:
    """AC-0026 (no-back-link arm): spec in commented row leaves child set entirely.

    A Shipped brief with one real Shipped mapped spec and one ghost spec in a
    comment.  Bounded: ghost excluded → child_states = {shipped} → delivered.
    Unbounded: ghost counted → child_states = {shipped, missing} → refused.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no back-link
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| `alpha` | Shipped |\n"
            "<!--\n| `no-such-slug` | <auto> |\n-->\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"ghost row in comment must be excluded: rc={rc} err={err}")
        expect("': delivered" in out, f"brief must be delivered: {out}")


def test_ac0026_commented_row_with_backlink_moves_to_untracked() -> None:
    """AC-0026 (back-link arm): spec in commented row moves to untracked arm.

    The spec back-links the brief, so its status still reaches child_states
    through the untracked path — it is additionally reported as untracked.
    Bounded: alpha in untracked (row not in mapped) → 'untracked' in output.
    Unbounded: alpha in mapped (row counted) → not untracked, 'Shipped' row.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="brief:myb")
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Ready\n- **Slug:** `myb`\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "<!--\n| `alpha` | Shipped |\n-->\n",
        )
        rc, out, err = run_lint(root)
        # Bounded: alpha's Shipped status reaches child_states via untracked arm.
        # Ready + Shipped child = lifecycle invalid → rc=1.
        expect(rc == 1, f"Shipped child (via untracked) invalidates Ready brief: rc={rc}")
        expect("untracked" in out.lower(), f"alpha must be reported untracked: {out}")


# ── AC-0027: ## heading inside comment does not end the Spec-map section ─────


def test_ac0027_commented_heading_does_not_end_section_measured_fixture() -> None:
    """AC-0027: ## heading inside comment does not end the Spec-map section.

    This is the measured fixture from the plan (2026-09-25).  Three conditions
    each defeated an earlier attempt; all three are load-bearing:

    1. The ghost row names a slug with no spec file — the untracked arm cannot
       restore it.
    2. A live Shipped row survives above the comment — so the child set is not
       empty when the ghost row is excluded.
    3. The comment is multi-line with ## on its own line — a single-line
       <!-- ## Governance references --> begins with <!--, never matches the
       terminator check, and tests nothing.

    Unrepaired: terminator fires on ## Governance references → only alpha
    parses → child_states = {shipped} → Shipped brief validates and delivers.
    Repaired: both rows parse → child_states = {shipped, missing} → refused.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no back-link; no spec for no-such-slug
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 The Spec map was closed when alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped |\n"
            "<!--\n## Governance references\n-->\n"
            "| no-such-slug | <auto> |\n",
        )
        rc, out, err = run_lint(root)
        # Repaired: both rows parsed; no-such-slug is missing → Shipped brief
        # with a missing child → lifecycle invalid → rc=1.
        expect(
            rc == 1,
            f"AC-0027: ghost row after commented heading must be parsed: rc={rc} err={err}",
        )
        expect("brief lifecycle" in err.lower(), err)


# ── AC-0028: unterminated comment yields rows above, none after ───────────────


def test_ac0028_unterminated_comment_rows_above_only() -> None:
    """AC-0028: a comment opened inside the Spec-map section and never closed
    yields the rows above it and none after it.

    Alpha row is above the opening <!--; beta row (Status: Draft) is inside
    the unclosed comment.  Bounded: only alpha counted → child_states = {shipped}
    → Shipped brief valid → delivered.  Unbounded: beta also counted →
    child_states = {shipped, draft} → refused.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")
        write_spec(root, "beta", "Draft")
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped |\n"
            "<!--\n| beta | Draft |\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"beta in unclosed comment must be excluded: rc={rc} err={err}")
        expect("': delivered" in out, f"brief must be delivered: {out}")


# ── AC-0029: line where comment state changes is not a row ───────────────────


def test_ac0029_row_where_comment_opens_is_excluded() -> None:
    """AC-0029: a line on which a comment opens (but does not close) is not a row.

    The alpha row opens a comment that is not closed on the same line; it is
    excluded.  The --> that closes the comment is also excluded (in_comment_before).
    The gamma row, in clean comment state, is parsed normally.

    Bounded: only gamma counts → Shipped brief with all Shipped children →
    delivered → rc=0.  Unbounded: alpha (no spec file) also counted → missing
    child → refused → rc=1.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "gamma", "Shipped")
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 gamma shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | <auto> <!--\n"
            "-->\n"
            "| gamma | Shipped |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 0,
            f"partial-comment row must be excluded: rc={rc} err={err}",
        )
        expect("': delivered" in out, f"brief must be delivered: {out}")


# ── AC-0030: inline comment preserves the row and its recorded status ─────────


def test_ac0030_inline_comment_row_is_parsed_and_status_preserved() -> None:
    """AC-0030: a comment that opens and closes within one line leaves the row
    parsed and extract_token returns the status before the inline comment.

    The mapped spec's Status is Draft; the recorded cell is
    'Shipped <!-- re-derived 2026-06-01 -->'.  A correct implementation:
    - admits the row (comment state unchanged on this line),
    - extracts 'Shipped' via extract_token (truncates at <!--),
    - compares to actual 'draft' → drift fires.

    A cell-destroying implementation would return '' for the cell; extract_token('')
    returns '' which _UNSET_CELLS exempts → drift silent.  The test asserts
    drift fires, proving the annotation was preserved.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Spec is Draft; cell records Shipped → drift unless cell is destroyed.
        write_spec(root, "alpha", "Draft")
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 test.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped <!-- re-derived 2026-06-01 --> |\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"drift must be detected (inline comment preserved): rc={rc}")
        expect("stale" in err.lower(), f"drift message expected: {err}")
        expect("alpha" in err, f"drift message must name alpha: {err}")
        # The drift message names the recorded value — 'Shipped' must appear.
        expect("Shipped" in err or "shipped" in err.lower(), f"recorded 'Shipped' in message: {err}")


# ── AC-0021: refusal names the offending brief by its full relative path ──────


def test_refusal_names_brief_relative_path() -> None:
    """AC-0021: every refusal names the offending brief by its path relative to --root.

    The brief is at docs/product/briefs/myb.md relative to the root.  The full
    relative path 'docs/product/briefs/myb.md' must appear in the diagnostic,
    not merely the stem 'myb' — the directory component makes it distinguishable.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # No Status: field → fires the absent-status refusal.
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Slug:** `myb`\n\n## Spec map\n\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"absent status must exit 1, got {rc}: {err}")
        expect(
            "docs/product/briefs/myb.md" in err,
            f"refusal must name full relative path 'docs/product/briefs/myb.md': {err}",
        )


# ── AC-0010 / AC-0022: out-of-vocabulary token exits 1 with vocabulary diagnostic


def test_out_of_vocabulary_status_exits_1_with_vocabulary_diagnostic() -> None:
    """AC-0010/AC-0022: an out-of-vocabulary token exits 1 and names the offending token.

    The vocabulary-refusal branch must be driven through the entry point so
    its exit code is verified independently of the lifecycle check.  A deleted
    branch would silently fall through to the lifecycle check which also exits 1,
    but with a different diagnostic — this test asserts the vocabulary message.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** FLIBBERTIGIBBET\n- **Slug:** `myb`\n\n"
            "## Spec map\n\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"OOV status must exit 1, got {rc}: {err}")
        expect(
            "vocabulary" in err.lower(),
            f"refusal must say 'vocabulary': {err}",
        )
        expect(
            "FLIBBERTIGIBBET" in err,
            f"refusal must name the offending token 'FLIBBERTIGIBBET': {err}",
        )
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: vocabulary refusal must name 'docs/product/briefs/myb.md': {err}",
        )


# ── AC-0008 / AC-0021 / AC-0022: malformed Cut-closed: exits 1 and names value


def test_malformed_cut_closed_exits_1_and_names_value() -> None:
    """AC-0008/AC-0021/AC-0022: malformed Cut-closed: exits 1, names the field, names the value.

    The malformed-value branch must be driven through the entry point.  The
    diagnostic must name the offending value and identify the Cut-closed: field,
    so a maintainer can act without reading the code.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # '20260101 some evidence' has a non-ISO date part (no dashes).
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Ready\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 20260101 some evidence\n\n"
            "## Spec map\n\n",
        )
        rc, out, err = run_lint(root)
        expect(rc == 1, f"malformed Cut-closed: must exit 1, got {rc}: {err}")
        expect(
            "cut-closed" in err.lower(),
            f"refusal must name the Cut-closed: field: {err}",
        )
        expect(
            "20260101 some evidence" in err,
            f"refusal must name the offending value '20260101 some evidence': {err}",
        )
        # AC-0021: the full relative path must appear, not just the stem.
        expect(
            "docs/product/briefs/myb.md" in err,
            f"AC-0021: malformed Cut-closed refusal must name 'docs/product/briefs/myb.md': {err}",
        )


# ── AC-0029 (second direction): a row on which a comment closes is excluded ───


def test_ac0029_row_where_comment_closes_is_excluded() -> None:
    """AC-0029 (closed-on-line direction): a row on which a comment closes is not a row.

    A comment opened on a previous line and closed embedded inside a row line
    means in_comment_before=True, so the line is excluded even though the raw
    line starts with '|'.  The fixture '| alpha | Shipped --> |' has
    in_comment_before=True (comment from the previous '<!--' line) and
    in_comment=False (the '-->' closes it); without the in_comment_before guard
    the raw '| alpha | ...' line would be parsed as a valid row.

    Bounded: only gamma (a real Shipped child) counts → Shipped brief all-Shipped
    → delivered → rc=0.  Without the in_comment_before guard, alpha (no spec file
    → missing) would be counted → lifecycle invalid → rc=1.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "gamma", "Shipped")
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 gamma shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "<!--\n"
            "| alpha | Shipped --> |\n"
            "| gamma | Shipped |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 0,
            f"closed-comment row must be excluded: rc={rc} err={err}",
        )
        expect("': delivered" in out, f"brief must be delivered: {out}")


# ── Section-reopen: a second ## Spec map heading keeps the section open ───────


def test_repeated_spec_map_heading_rows_all_parsed() -> None:
    """A second '## Spec map' heading re-opens the section; rows below it are parsed.

    Without the fix the second heading terminates the section, so only the
    row above it is parsed: alpha (Shipped) makes the Shipped brief look
    delivered.  With the fix, no-such-slug (missing) is also counted, the
    child set is {shipped, missing}, and the lifecycle check fails.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no spec for no-such-slug
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped |\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| no-such-slug | <auto> |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 1,
            f"rows under both headings must be parsed; no-such-slug is missing "
            f"→ lifecycle invalid: rc={rc} err={err}",
        )
        expect("brief lifecycle" in err.lower(), err)


# ── Indented ## heading terminates Spec-map section ───────────────────────────


def test_indented_heading_terminates_spec_map() -> None:
    """An indented ## heading (up to three leading spaces) ends the Spec-map section.

    CommonMark allows up to three leading spaces on a heading.  The Spec-map
    parser must not parse rows that appear below an indented heading as though
    the section were still open.

    Without termination: no-such-slug is also counted → missing child →
    lifecycle invalid → rc=1.  With correct termination: only alpha counts →
    Shipped brief all-Shipped → delivered → rc=0.

    Mutation: remove the ``.lstrip()`` call in the section-terminator check so
    that ``  ## Other`` is not recognised as a heading.  no-such-slug would then
    be parsed, the lifecycle check would fail, and rc becomes 1 — this test reds.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no spec for no-such-slug
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped |\n"
            "  ## Other\n"  # indented heading — must end the section
            "| no-such-slug | <auto> |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 0,
            f"indented ## heading must end the Spec-map section: rc={rc} err={err}",
        )
        expect("': delivered" in out, f"brief must be delivered: {out}")


# ── Comment-closer-then-heading does NOT terminate Spec-map section ────────────


def test_comment_closer_heading_does_not_terminate_spec_map() -> None:
    """A line that closes a comment and then carries a heading does not end the section.

    ``-->  ## Other`` began inside a comment and closed it; the heading text is
    a live *suffix* rather than a prefix, so it must not terminate the
    Spec-map section.  The preamble reader draws the same line for the same
    reason — both readers must agree.

    Without the ``in_comment_before`` guard: the section terminates at
    ``-->  ## Other`` → only alpha is counted → Shipped brief with one
    Shipped child → delivered → rc=0.
    With the guard (correct): the section does not terminate → no-such-slug is
    also counted (no spec file → missing child) → lifecycle invalid → rc=1.

    Mutation: remove the ``not in_comment_before`` part of the terminator check
    so that any live ``## `` suffix terminates.  The section would then close at
    ``-->  ## Other`` and no-such-slug would not be counted → rc becomes 0 —
    this test reds.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # no spec for no-such-slug
        write_brief_raw(
            root, "myb",
            "# Brief: myb\n\n- **Status:** Shipped\n- **Slug:** `myb`\n"
            "- **Cut-closed:** 2026-01-01 alpha shipped.\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Shipped |\n"
            "<!--\n"
            "-->  ## Other\n"  # comment-closer-then-heading — must NOT end the section
            "| no-such-slug | <auto> |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 1,
            f"comment-closer-then-heading must not end the Spec-map section: rc={rc} err={err}",
        )
        expect("brief lifecycle" in err.lower(), err)


def test_tab_separated_heading_terminates_spec_map() -> None:
    """A tab-separated heading ends the Spec map, as a space-separated one does.

    Measured before the fix: `##\tGovernance references` left the section
    open, so that table's header row parsed as a spec row and produced a
    stale-cell refusal naming a spec called 'Ref'. The opener and the
    terminator now ask the same whitespace question.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief_raw(
            root,
            "myb",
            "# Brief: myb\n\n- **Status:** Executing\n- **Slug:** `myb`\n\n"
            "## Spec map\n\n| Spec | Status |\n| --- | --- |\n| alpha | Shipped |\n"
            "##\tGovernance references\n\n| Ref | Status |\n| --- | --- |\n"
            "| ADR-0001 | n/a |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            "'Ref'" not in err,
            f"a row below a tab-separated heading parsed as a spec row: {err}",
        )
        expect(rc == 0, f"expected a clean run, got rc={rc}: {err}")


def test_indented_spec_map_heading_still_opens_the_section() -> None:
    """An indented Spec-map heading opens the section, so a child is not hidden.

    The silent direction: if the heading does not open, the map yields an
    empty child set, so a Draft brief listing an Implementing child conceals
    that execution evidence and validates. All three heading decisions --
    open, re-open, close -- ask one question so this cannot differ.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # No Brief: back-link. The Spec map must be the spec's ONLY route
        # into the child set, or the untracked back-link arm restores it and
        # the fixture passes whether the heading opened the section or not.
        write_spec(root, "alpha", "Implementing")
        write_brief_raw(
            root,
            "myb",
            "# Brief: myb\n\n- **Status:** Draft\n- **Slug:** `myb`\n\n"
            "  ## Spec map\n\n| Spec | Status |\n| --- | --- |\n"
            "| alpha | Implementing |\n",
        )
        rc, out, err = run_lint(root)
        expect(
            rc == 1,
            f"a Draft brief with an Implementing child must be refused, got rc={rc}: {out}",
        )
        expect(
            "child scope" in err,
            f"the concealed child should surface as a lifecycle refusal: {err}",
        )
