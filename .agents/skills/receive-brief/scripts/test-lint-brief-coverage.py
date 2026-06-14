#!/usr/bin/env python3
"""Self-test for the sibling lint-brief-coverage.py (the brief-coverage rollup).

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

LINTER = Path(__file__).resolve().parent / "lint-brief-coverage.py"

FAILURES: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def write_spec(root: Path, slug: str, status: str, brief: str | None = None) -> None:
    p = root / "docs" / "specs" / slug / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    header = f"# Spec: {slug}\n\n- **Status:** {status}\n"
    if brief is not None:
        header += f"- **Brief:** {brief}\n"
    header += "\n## Acceptance Criteria\n\n- [ ] AC1\n"
    p.write_text(header, encoding="utf-8")


def write_brief(root: Path, slug: str, rows: list[tuple[str, str]], stem: str | None = None) -> None:
    """Write a brief with a two-column Spec map. `rows` is (spec-slug, recorded-status)."""
    name = stem if stem is not None else slug
    p = root / "docs" / "product" / "briefs" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = f"# Brief: {slug}\n\n- **Slug:** `{slug}`\n\n## Spec map\n\n"
    body += "| Spec | Status |\n| --- | --- |\n"
    for spec_slug, recorded in rows:
        body += f"| `{spec_slug}` | {recorded} |\n"
    p.write_text(body, encoding="utf-8")


def run_lint(root: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def case_mixed_map_not_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Implementing", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped"), ("beta", "Implementing")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"mixed map should exit 0, got {rc}: {err}")
        expect("shipped" in out.lower(), f"alpha should roll up shipped: {out}")
        expect("implementing" in out.lower(), f"beta should roll up implementing: {out}")
        expect("not delivered" in out.lower(), f"mixed map → not delivered: {out}")


def case_all_shipped_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Shipped", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped"), ("beta", "Shipped")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"all-shipped should exit 0, got {rc}: {err}")
        # "': delivered" disambiguates from "': not delivered".
        expect("': delivered" in out, f"all-shipped brief → delivered: {out}")


def case_empty_map_not_delivered() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "emptyb", [])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"empty map should exit 0, got {rc}: {err}")
        expect("not delivered" in out.lower(),
               f"empty map is never vacuously delivered: {out}")
        expect("': delivered" not in out,
               f"empty map must NOT report delivered: {out}")


def case_no_brief_noop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped")  # spec but no brief
        rc, out, err = run_lint(root)
        expect(rc == 0, f"no brief should exit 0, got {rc}: {err}")
        expect(err.strip() == "", f"no brief → no diagnostic on stderr: {err!r}")
        expect(out.strip() == "", f"no brief → no diagnostic on stdout: {out!r}")


def case_template_skipped() -> None:
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


def case_untracked_backlink_informational() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # gamma back-links myb but is NOT in myb's Spec map → untracked.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "gamma", "Draft", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped")])
        rc, out, err = run_lint(root)
        combined = (out + err).lower()
        expect(rc == 0, f"untracked back-link must NOT be an error, got {rc}: {err}")
        expect("untracked" in combined, f"gamma should be reported untracked: {out}{err}")
        expect("gamma" in combined, f"untracked spec named: {out}{err}")


def case_stale_cell_drifts_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # beta is actually Shipped, but the brief's Spec map still records
        # Implementing — a hand-edited stale cell. Fail closed.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_spec(root, "beta", "Shipped", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped"), ("beta", "Implementing")])
        rc, out, err = run_lint(root)
        expect(rc == 1, f"stale recorded cell should exit 1, got {rc}: {out}")
        expect("stale" in err.lower(), f"drift message should name staleness: {err}")
        expect("beta" in err, f"drift message should name the spec: {err}")


def case_unset_cell_is_not_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # An `<auto>` / unset cell means "not yet derived" — report, don't fail.
        write_spec(root, "alpha", "Implementing", brief="myb")
        write_brief(root, "myb", [("alpha", "<auto>")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"unset <auto> cell must not be drift, got {rc}: {err}")
        expect("implementing" in out.lower(), f"derived status still reported: {out}")


def case_slug_differs_from_filename() -> None:
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


def case_prose_pipe_after_table_is_not_a_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Shipped", brief="myb")
        p = root / "docs" / "product" / "briefs" / "myb.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# Brief: myb\n\n- **Slug:** `myb`\n\n## Spec map\n\n"
            "| Spec | Status |\n| --- | --- |\n| `alpha` | Shipped |\n\n"
            "Note: rows are added as slices ship | one per spec.\n",
            encoding="utf-8",
        )
        rc, out, err = run_lint(root)
        expect(rc == 0, f"prose pipe must not trip drift exit 1, got {rc}: {err}")
        expect("stale" not in err.lower(), f"no phantom drift row: {err}")


def case_lowercase_status_token_still_delivers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "shipped", brief="myb")  # lowercase token
        write_brief(root, "myb", [("alpha", "Shipped")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"no drift expected, got {rc}: {err}")
        expect("': delivered" in out,
               f"lowercase 'shipped' must still count as delivered: {out}")


def case_placeholder_brief_value_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", "Draft", brief="<slug>")  # template placeholder
        write_brief(root, "myb", [("beta", "<auto>")])
        rc, out, err = run_lint(root)
        combined = out + err
        expect(rc == 0, f"placeholder back-link must not error, got {rc}: {err}")
        expect("<slug>" not in combined,
               f"placeholder must not surface as a tracked/untracked slug: {combined}")


def case_annotated_recorded_cell_not_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A recorded cell annotated the same way a spec's own Status field may
        # be (`Shipped (2026-06-01)`) must not misreport as drift against a
        # derived `Shipped` — the recorded side is normalized symmetrically.
        write_spec(root, "alpha", "Shipped", brief="myb")
        write_brief(root, "myb", [("alpha", "Shipped (2026-06-01)")])
        rc, out, err = run_lint(root)
        expect(rc == 0, f"annotated recorded cell must not drift, got {rc}: {err}")
        expect("stale" not in err.lower(), f"no false drift on annotated cell: {err}")
        expect("': delivered" in out, f"annotated-cell brief still delivered: {out}")


def main() -> int:
    for case in (
        case_mixed_map_not_delivered,
        case_annotated_recorded_cell_not_drift,
        case_all_shipped_delivered,
        case_empty_map_not_delivered,
        case_no_brief_noop,
        case_template_skipped,
        case_untracked_backlink_informational,
        case_stale_cell_drifts_fail_closed,
        case_unset_cell_is_not_drift,
        case_slug_differs_from_filename,
        case_prose_pipe_after_table_is_not_a_row,
        case_lowercase_status_token_still_delivers,
        case_placeholder_brief_value_ignored,
    ):
        case()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"test-lint-brief-coverage: {len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("test-lint-brief-coverage: all cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
