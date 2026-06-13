#!/usr/bin/env python3
"""Self-test for tools/lint-knowledge-surface-parity.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.
Pattern: build a fixture set of knowledge-surface references in a tempdir, point
KS_CANONICAL_FILE / KS_REVIEW_FILE / KS_DIAGRAM_FILE / KS_PE_FILE at them, run the
linter, and assert the exit code (and a diagnostic substring on the failure
cases). Every LAYOUT copy must be overridden here — an un-overridden copy falls
through to its real repo file and breaks the fixture cases.

Cases pin each invariant to a failure mode the linter must catch:

  A — parity: canonical {1..8}, architect-review full {1..8}, architect-diagram
      full {1..8}, frame-intent subset {1,2,4,8}, all byte-identical name+question.
      Must exit 0.
  B — reworded question in the frame-intent copy for a shared area. Must fail.
  C — renamed area in the canonical copy. Must fail (the copies still name the
      old label).
  D — frame-intent carries an extra area (3). Must fail (subset drift).
  E — canonical dropped an area (only 1..7). Must fail (canonical incomplete).
  F — a missing file must surface as an error, not a traceback.
  G — the architect-review copy drifts (reworded question). Must fail (the third
      copy is guarded too).
  I — the architect-diagram copy drifts (reworded question). Must fail (the
      fourth copy is guarded too).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-knowledge-surface-parity.py"

# Canonical area definitions (number -> (name, question)). Fixtures derive from
# these; cases B–G perturb a copy.
CANON: dict[int, tuple[str, str]] = {
    1: ("Business domain & meaning", "What do the terms *mean*?"),
    2: ("Current landscape", "What *exists* today?"),
    3: ("Interfaces & contracts", "On what *terms*?"),
    4: ("Operational reality", "How does it *behave*?"),
    5: ("Constraints & standards", "What *must* I do?"),
    6: ("Patterns & references", "How is this *done well*?"),
    7: ("Decisions & rationale", "*Why* is it this way?"),
    8: ("In-flight & roadmap", "What's *changing*?"),
}
SUBSET = (1, 2, 4, 8)

_FAILURES: list[str] = []
_CASES = 0


def _render(areas: dict[int, tuple[str, str]], *, weight_col: bool) -> str:
    """Render a minimal reference file carrying a taxonomy table."""
    if weight_col:
        head = "| # | Area | The question it answers | Weight | Consult it when… |\n|---|---|---|---|---|\n"
        rows = "".join(
            f"| {n} | {name} | {q} | primary | when… |\n" for n, (name, q) in areas.items()
        )
    else:
        head = "| # | Area | The question it answers | Consult it when… |\n|---|---|---|---|\n"
        rows = "".join(
            f"| {n} | {name} | {q} | when… |\n" for n, (name, q) in areas.items()
        )
    return "# Knowledge surfaces (fixture)\n\n" + head + rows + "\nprose tail.\n"


# Sentinel so an un-passed diagram copy defaults to the full canonical fixture
# (architect-diagram carries the full {1..8} table, like architect-review). It
# *must* be overridden — its LAYOUT row otherwise resolves to the real repo file
# and breaks the fixtures. None still means "don't write the file" (case F).
_DEFAULT_DIAGRAM = object()


def _run(
    canon_text: str | None,
    review_text: str | None,
    pe_text: str | None,
    diagram_text: str | None | object = _DEFAULT_DIAGRAM,
) -> subprocess.CompletedProcess:
    if diagram_text is _DEFAULT_DIAGRAM:
        diagram_text = _render(dict(CANON), weight_col=False)
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ)
        for key, name, text in (
            ("KS_CANONICAL_FILE", "canonical.md", canon_text),
            ("KS_REVIEW_FILE", "review.md", review_text),
            ("KS_DIAGRAM_FILE", "architect-diagram.md", diagram_text),
            ("KS_PE_FILE", "frame-intent.md", pe_text),
        ):
            p = pathlib.Path(d) / name
            if text is not None:
                p.write_text(text, encoding="utf-8")
            env[key] = str(p)
        return subprocess.run(
            [sys.executable, str(LINTER)],
            capture_output=True, text=True, env=env, check=False,
        )


def _expect(label: str, cp: subprocess.CompletedProcess, *, code: int, needle: str = "") -> None:
    global _CASES
    _CASES += 1
    if cp.returncode != code:
        _FAILURES.append(
            f"{label}: expected exit {code}, got {cp.returncode}\n"
            f"  stdout={cp.stdout!r}\n  stderr={cp.stderr!r}"
        )
        return
    if needle and needle not in cp.stderr:
        _FAILURES.append(f"{label}: expected {needle!r} in stderr; stderr={cp.stderr!r}")


def main() -> int:
    full = dict(CANON)
    review = dict(CANON)  # architect-review carries the full set
    subset = {n: CANON[n] for n in SUBSET}

    def canon_md() -> str:
        return _render(full, weight_col=False)

    def review_md(areas=None) -> str:
        return _render(areas if areas is not None else review, weight_col=False)

    def pe_md(areas=None) -> str:
        return _render(areas if areas is not None else subset, weight_col=True)

    # A — parity holds across the review, diagram, and frame-intent copies.
    _expect("A parity", _run(canon_md(), review_md(), pe_md()), code=0)

    # B — reworded question in the frame-intent copy for shared area 1.
    drifted_pe = dict(subset); drifted_pe[1] = (CANON[1][0], "What do the words mean?")
    _expect("B reworded pe", _run(canon_md(), review_md(), pe_md(drifted_pe)),
            code=1, needle="area #1 diverged")

    # C — renamed area in the canonical copy (shared area 2).
    drifted_canon = dict(full); drifted_canon[2] = ("Application landscape", CANON[2][1])
    _expect("C renamed canonical", _run(_render(drifted_canon, weight_col=False), review_md(), pe_md()),
            code=1, needle="area #2 diverged")

    # D — frame-intent carries an extra area (3), breaking the subset.
    extra_pe = {n: CANON[n] for n in (1, 2, 3, 4, 8)}
    _expect("D subset drift", _run(canon_md(), review_md(), pe_md(extra_pe)),
            code=1, needle="frame-intent reference areas")

    # E — canonical dropped an area (only 1..7), breaking the canonical set.
    short = {n: CANON[n] for n in range(1, 8)}
    _expect("E canonical incomplete", _run(_render(short, weight_col=False), review_md(short), pe_md()),
            code=1, needle="canonical) areas")

    # F — a missing file is an error, not a traceback.
    cp = _run(canon_md(), review_md(), None)
    _expect("F missing file", cp, code=1, needle="not found")
    if "Traceback" in cp.stderr:
        _FAILURES.append("F missing file: linter raised a traceback instead of a clean error")

    # G — the architect-review copy drifts (reworded question for shared area 4).
    drifted_review = dict(review); drifted_review[4] = (CANON[4][0], "How does it run in prod?")
    _expect("G review drift", _run(canon_md(), review_md(drifted_review), pe_md()),
            code=1, needle="area #4 diverged")

    # H — a copy carries an area outside the canonical set (a phantom area 9).
    # Caught by invariant (2) (set != expected), not (3) (which only compares
    # shared areas) — pins that out-of-canon areas are guarded.
    out_of_canon = dict(review); out_of_canon[9] = ("Phantom area", "Does this exist?")
    _expect("H out-of-canon area", _run(canon_md(), review_md(out_of_canon), pe_md()),
            code=1, needle="architect-review reference areas")

    # I — the architect-diagram copy drifts (reworded question for shared area 5).
    # Mirrors G: pins that the fourth copy is guarded too.
    drifted_diagram = _render({**CANON, 5: (CANON[5][0], "What rules constrain me?")}, weight_col=False)
    _expect("I diagram drift", _run(canon_md(), review_md(), pe_md(), diagram_text=drifted_diagram),
            code=1, needle="area #5 diverged")

    if _FAILURES:
        for f in _FAILURES:
            print(f"test-lint-knowledge-surface-parity: ✖ {f}", file=sys.stderr)
        print(f"\n{len(_FAILURES)} of {_CASES} case(s) failed.", file=sys.stderr)
        return 1
    print(f"test-lint-knowledge-surface-parity: ✓ all {_CASES} cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
