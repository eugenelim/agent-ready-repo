#!/usr/bin/env python3
"""Brief-coverage auto-rollup lint.

This is a `receive-brief` **skill script**: it lives at
`packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py` and
projects to every adapter's `.../skills/receive-brief/scripts/`, the same way
the work-loop's `lint-spec-status.py` does. The agent runs it after a slice's
status changes; it can also run as a **fail-closed CI gate** where a PR event
and Python both exist. It no-ops gracefully where Python is absent.

What it does: reads every `docs/specs/*/spec.md` `Status:` field, follows the
`Brief:` back-links, and rolls each brief's Spec map up from its child specs —
so "is this brief delivered?" stays answerable with no hand-maintenance. It
reads only existing `Status:` fields and the brief's Spec map; it introduces no
new state.

Rollup rules:
  - A brief is *delivered* only when its Spec map is non-empty AND every mapped
    spec is `Shipped`. An empty map is never vacuously delivered.
  - A spec that back-links a brief (`Brief: <slug>`) but is absent from that
    brief's Spec map is reported **untracked** — informational, never an error.
  - A `docs/product/briefs/_template.md` (or any `_`-prefixed file) is the
    shipped template, not a brief; it is skipped.

Exit codes:
  0 = clean (coverage reported; warnings/untracked allowed).
  1 = drift: a brief's Spec map records a status that contradicts the spec's
      actual `Status:` (a hand-edited, now-stale cell). The Status column is
      auto-derived and must not be hand-maintained — drift is the failure this
      lint exists to catch. An unset cell (`<auto>`, `—`, `-`, or empty) means
      "not yet derived" and is reported, not failed.

No briefs found → exit 0 with no diagnostic output (the common case in a repo
that ships no brief). Usage: lint-brief-coverage.py [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Header status / brief / slug lines, e.g. `- **Status:** Shipped (2026-05-26)`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+?)\s*$")
_BRIEF_RE = re.compile(r"\*\*Brief:\*\*\s*(.+?)\s*$")
_SLUG_RE = re.compile(r"\*\*Slug:\*\*\s*(.+?)\s*$")
# Recorded-status cells that mean "not yet derived" — reported, never drift.
_UNSET_CELLS = frozenset({"", "<auto>", "—", "-", "tbd", "todo"})


def _is_placeholder(value: str) -> bool:
    """True for an unset/template value: empty, `none`, an HTML comment, or a
    bare angle-bracket placeholder (`<slug>`)."""
    v = value.strip()
    return (
        not v
        or v.lower() == "none"
        or v.startswith("<!--")
        or (v.startswith("<") and v.endswith(">"))
    )


def extract_token(raw: str) -> str:
    """Leading token from a header value, truncating at ` (`, ` →`, or `<!--`.

    Intentionally mirrors lint-spec-status.py's `extract_status_token` (same
    delimiters) — cross-skill import is banned by this spec's Boundaries, so
    the two must be kept in lockstep by hand. Reduces annotated statuses
    (`Shipped (2026-05-26)`, `Approved → Shipped (…)`, `Draft <!-- ... -->`) to
    their leading word.
    """
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    parts = text.strip().split()
    return parts[0] if parts else ""


def parse_spec(spec_text: str) -> tuple[str | None, str | None]:
    """Return (status-token, brief-back-link-slug) from a spec's header.

    A `Brief:` value that is empty, `none`, or the template HTML-comment
    placeholder counts as no back-link (None).
    """
    status: str | None = None
    brief: str | None = None
    for line in spec_text.splitlines():
        if status is None:
            m = _STATUS_RE.search(line)
            if m:
                status = extract_token(m.group(1))
        if brief is None:
            m = _BRIEF_RE.search(line)
            if m:
                value = m.group(1).strip()
                if not _is_placeholder(value):
                    brief = extract_token(value).strip("`")
    return status, brief


def parse_brief_slug(brief_text: str, fallback: str) -> str:
    """Return the brief's canonical slug from its `- **Slug:**` field.

    A derived spec's `Brief:` back-link names this slug, which need not equal
    the brief's filename stem — so the slug, not the stem, is the join key for
    coverage and untracked detection. Falls back to `fallback` (the filename
    stem) only when no usable `Slug:` field is present.
    """
    for line in brief_text.splitlines():
        m = _SLUG_RE.search(line)
        if m:
            value = m.group(1).strip().strip("`")
            if not _is_placeholder(value):
                return extract_token(value).strip("`")
    return fallback


def parse_spec_map(brief_text: str) -> list[tuple[int, str, str]]:
    """Return (lineno, spec-slug, recorded-status) for each Spec map row.

    Parses the markdown table under the `## Spec map` heading. The first
    table column is the spec slug; the LAST column is the recorded status
    (so a Shape-B map with a middle `Story` column parses the same way).
    The header row and the `| --- |` separator row are skipped.
    """
    rows: list[tuple[int, str, str]] = []
    in_section = False
    for lineno, line in enumerate(brief_text.splitlines(), start=1):
        if re.match(r"^##\s+Spec map\b", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^##\s+", line):
            break
        # Only a markdown table row counts — it must start with `|`. This
        # ignores explanatory prose under the heading that happens to contain a
        # pipe (which would otherwise parse as a phantom row and trip drift).
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        first = cells[0].strip("` ")
        last = cells[-1].strip("` ")
        # Skip the header row and the `| --- | --- |` separator row.
        if first.lower() == "spec" or set(first) <= set("-: "):
            continue
        rows.append((lineno, first, last))
    return rows


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (lines_to_print, hard_violations)."""
    briefs_dir = root / "docs" / "product" / "briefs"
    if not briefs_dir.is_dir():
        return [], []

    brief_files = [
        p for p in sorted(briefs_dir.glob("*.md")) if not p.name.startswith("_")
    ]
    if not brief_files:
        return [], []

    # Index specs by slug → (status, brief-back-link).
    specs: dict[str, tuple[str | None, str | None]] = {}
    specs_dir = root / "docs" / "specs"
    for spec_path in sorted(specs_dir.glob("*/spec.md")):
        slug = spec_path.parent.name
        specs[slug] = parse_spec(
            spec_path.read_text(encoding="utf-8", errors="replace")
        )

    out: list[str] = []
    hard: list[str] = []

    for brief_path in brief_files:
        text = brief_path.read_text(encoding="utf-8", errors="replace")
        # The slug (from the `Slug:` field), not the filename stem, is the
        # identity a spec's `Brief:` back-link names — see parse_brief_slug.
        brief_slug = parse_brief_slug(text, brief_path.stem)
        rel = brief_path.relative_to(root).as_posix()
        rows = parse_spec_map(text)

        mapped = {slug for _, slug, _ in rows if slug}
        derived: list[str] = []
        for lineno, spec_slug, recorded in rows:
            if not spec_slug:
                continue
            status = specs.get(spec_slug, (None, None))[0]
            actual = status if status else "missing"
            derived.append(actual)
            # Normalise the recorded cell the same way as the actual status
            # (leading token) so an annotated cell like `Shipped (2026-06-01)`
            # isn't misreported as drift against a derived `Shipped`.
            recorded_norm = extract_token(recorded).strip("`").lower()
            if recorded_norm not in _UNSET_CELLS and recorded_norm != actual.lower():
                hard.append(
                    f"{rel}:{lineno}: spec '{spec_slug}' recorded '{recorded}' "
                    f"but its Status is '{actual}' — the Spec map is stale "
                    f"(auto-derived; do not hand-edit the Status column)"
                )

        # Case-insensitive so a lowercase `shipped` token agrees with the drift
        # check (which is also case-insensitive) on the delivered verdict.
        delivered = bool(mapped) and all(s.lower() == "shipped" for s in derived)
        out.append(
            f"lint-brief-coverage: brief '{brief_slug}': "
            f"{'delivered' if delivered else 'not delivered'}"
        )
        for _, spec_slug, _ in rows:
            if spec_slug:
                status = specs.get(spec_slug, (None, None))[0]
                out.append(f"  - {spec_slug}: {status if status else 'missing'}")

        # Untracked: specs that back-link this brief but aren't in its map.
        untracked = sorted(
            slug for slug, (_, back) in specs.items()
            if back == brief_slug and slug not in mapped
        )
        for slug in untracked:
            out.append(
                f"  - {slug}: untracked (back-links this brief, not in Spec map)"
            )

    out.append(f"lint-brief-coverage: {len(brief_files)} brief(s) checked.")
    return out, hard


def _repo_root() -> Path:
    # Best-effort discovery for a bare manual run. The CI gate
    # and every self-test pass `--root` explicitly, so this only fires for a
    # hand-run with no `--root`; prefer git's toplevel when available.
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except FileNotFoundError:
        pass
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else _repo_root()

    out, hard = check(root)

    for line in out:
        print(line)
    if hard:
        for v in hard:
            print(f"lint-brief-coverage: {v}", file=sys.stderr)
        print(
            f"lint-brief-coverage: {len(hard)} stale Spec-map cell(s).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
