#!/usr/bin/env python3
"""Brief-coverage auto-rollup lint.

This is an `author-delivery-brief` **skill script**: it lives at
`packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py`
and projects to every adapter's `.../skills/author-delivery-brief/scripts/`, the same way
the work-loop's `lint-spec-status.py` does. The agent runs it after a slice's
status changes; it can also run as a **fail-closed CI gate** where a PR event
and Python both exist. It no-ops gracefully where Python is absent.

What it does: reads every brief and mapped spec `Status:` field, follows the
`Brief:` back-links, and checks the brief lifecycle against its child specs.
It reports delivery only after the brief is explicitly `Shipped`; it introduces
no new state and never mutates a status.

Rollup rules:
  - A brief is *delivered* only when its own status is `Shipped`, its Spec map
    is non-empty, and every mapped spec is `Shipped`.
  - `Draft`, `Ready`, and `Withdrawn` have no `Implementing` or `Shipped`
    child. `Executing` and `Cancelled` have at least one. `Shipped` has only
    `Shipped` children and cannot have an empty map.
  - A spec that back-links a brief but is absent from that brief's Spec map is
    reported **untracked** — informational, never an error. The canonical
    back-link is the path form pinned by the owning guide § Spec metadata
    contract; the bare `Slug:` spelling is still matched here for backward
    compatibility only.
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
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

# Header status / brief lines for spec files, e.g. `- **Status:** Shipped (2026-05-26)`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+?)\s*$")
_BRIEF_RE = re.compile(r"\*\*Brief:\*\*\s*(.+?)\s*$")
# Recorded-status cells that mean "not yet derived" — reported, never drift.
_UNSET_CELLS = frozenset({"", "<auto>", "—", "-", "tbd", "todo"})
_GOVERNANCE_REFERENCE_RE = re.compile(
    r"(?i)^(?:docs/(?:rfc|adr)/|(?:rfc|adr)-?\d{3,})"
)
_GOVERNANCE_PATH_RE = re.compile(r"(?i)(?:^|/)(?:rfc|adr)/")
_MARKDOWN_LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")


def _load_sibling(name: str, module_name: str):
    """Load a sibling script by its path under a pack-and-skill-qualified name.

    Skills are independent and several may ship a same-named script.  A bare
    ``import`` would bind whichever directory reached the path first and cache
    it for every later importer.  Loading by path avoids that collision and
    works whether the lint is run as a script or loaded in-process.
    """
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling module {name!r} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_bs = _load_sibling("brief_shape", "core_author_delivery_brief_brief_shape")


def parse_spec(spec_text: str) -> tuple[str | None, str | None]:
    """Return (status-token, brief-back-link) from a spec's header.

    `brief:<slug>` is the canonical back-link form; the
    repository-relative path and a bare slug are both accepted fallbacks. A
    leading `./` is stripped so the path spelling compares equal to the
    brief's own repository-relative path.

    A `Brief:` value that is empty, `none`, or the template HTML-comment
    placeholder counts as no back-link (None).
    """
    status: str | None = None
    brief: str | None = None
    for line in spec_text.splitlines():
        if status is None:
            m = _STATUS_RE.search(line)
            if m:
                status = _bs.extract_token(m.group(1))
        if brief is None:
            m = _BRIEF_RE.search(line)
            if m:
                value = m.group(1).strip()
                if not _bs.is_placeholder(value):
                    brief = _bs.extract_token(value).strip("`")
                    if brief.startswith("./"):
                        brief = brief[2:]
    return status, brief


def parse_spec_map(brief_text: str) -> list[tuple[int, str, str]]:
    """Return (lineno, spec-slug, recorded-status) for each Spec map row.

    Parses the markdown table under the ``## Spec map`` heading, with HTML
    comment awareness.  The first table column is the spec slug; the LAST
    column is the recorded status (so a Shape-B map with a middle ``Story``
    column parses the same way).  The header row and the ``| --- |`` separator
    row are skipped.

    Comment handling rules:

    - A ``## Spec map`` heading inside a comment does not open the section:
      the live text of such a line is empty or does not start with
      ``## Spec map``.
    - A ``## `` heading inside a comment does not close the section:
      the live-prefix check uses ``live.startswith("## ")``, not stripped text,
      so a heading whose ``## `` is preceded by a ``-->`` closer is not a
      terminator.
    - A repeated ``## Spec map`` heading re-opens the section rather than
      closing it, preserving the prior handling where the opener matched
      unconditionally.
    - A row inside a comment is not parsed: the line is skipped when
      ``in_comment_before`` or ``in_comment`` (after processing) is True.
    - A comment that opens and closes within one line leaves the row parsed
      and the recorded status unchanged: the raw ``line`` is parsed so that
      ``extract_token`` can truncate the inline comment as it does everywhere
      else.
    """
    rows: list[tuple[int, str, str]] = []
    in_section = False
    in_comment = False
    for lineno, line in enumerate(brief_text.splitlines(), start=1):
        in_comment_before = in_comment
        live, in_comment = _bs.process_line(line, in_comment)

        if not in_section:
            # A '## Spec map' heading inside a comment does not open the
            # section.  live is the non-comment portion of the line; it will
            # be empty or lack the '## Spec map' prefix when the heading is
            # inside a comment.
            if re.match(r"^##\s+Spec map\b", live, re.IGNORECASE):
                in_section = True
            continue

        # A repeated '## Spec map' heading re-opens the section rather than
        # closing it — same behaviour as the unconditional opener in the
        # old parser.  Check this before the generic terminator so that a
        # second '## Spec map' does not break the section.
        if re.match(r"^##\s+Spec map\b", live, re.IGNORECASE):
            continue

        # A '## ' heading inside a comment does not end the section.
        # live.startswith checks the live prefix before any leading whitespace
        # is removed, so '--> ## Other' (whose live text starts with ' ##')
        # is not a terminator.
        if live.startswith("## "):
            break

        # Skip lines that are inside a comment or on which comment state
        # changes (opened without being closed on the same line, or closed
        # after being opened on a previous line).
        if in_comment_before or in_comment:
            continue

        # Only a markdown table row counts — it must start with `|`. This
        # ignores explanatory prose under the heading that happens to contain a
        # pipe (which would otherwise parse as a phantom row and trip drift).
        if not line.lstrip().startswith("|"):
            continue

        # Parse from the original line so that inline annotations such as
        # '| Shipped <!-- re-derived 2026-06-01 --> |' are preserved for
        # extract_token to truncate at '<!--' (inline comment preserved).
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


def _is_governance_reference(value: str) -> bool:
    """Return whether a Spec-map cell names an RFC or ADR identity."""

    normalized = value.strip("` ")
    candidates = [normalized]
    link = _MARKDOWN_LINK_RE.match(normalized)
    if link:
        candidates.extend(link.groups())
    return any(
        _GOVERNANCE_REFERENCE_RE.match(candidate.strip("` "))
        or _GOVERNANCE_PATH_RE.search(candidate.strip("` "))
        for candidate in candidates
    )


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
        # identity a spec's `Brief:` back-link names.  The bounded accessor
        # falls back to the filename stem when no usable `Slug:` field is
        # present.
        brief_slug = _bs.get_slug(text, brief_path.stem)
        brief_status = _bs.get_status(text)
        cut_closed = _bs.get_cut_closed(text)
        rel = brief_path.relative_to(root).as_posix()
        rows = parse_spec_map(text)

        mapped = {slug for _, slug, _ in rows if slug}
        derived: list[str] = []
        for lineno, spec_slug, recorded in rows:
            if not spec_slug:
                continue
            if _is_governance_reference(spec_slug):
                hard.append(
                    f"{rel}:{lineno}: governance reference '{spec_slug}' is in "
                    "the Spec map — move it to Governance references"
                )
                derived.append("governance-reference")
                continue
            status = specs.get(spec_slug, (None, None))[0]
            actual = status if status else "missing"
            derived.append(actual)
            # Normalise the recorded cell the same way as the actual status
            # (leading token) so an annotated cell like `Shipped (2026-06-01)`
            # isn't misreported as drift against a derived `Shipped`.
            recorded_norm = _bs.extract_token(recorded).strip("`").lower()
            if recorded_norm not in _UNSET_CELLS and recorded_norm != actual.lower():
                hard.append(
                    f"{rel}:{lineno}: spec '{spec_slug}' recorded '{recorded}' "
                    f"but its Status is '{actual}' — the Spec map is stale "
                    f"(auto-derived; do not hand-edit the Status column)"
                )

        # A back-link makes a spec a child even when the Spec map has not yet
        # been reconciled. Keep the coverage omission informational, but do not
        # let it hide execution evidence from lifecycle validation.
        # `brief:<slug>` (canonical), the repository-relative path, and the
        # bare slug all join here — the typed form must survive
        # alongside the two compatibility forms already recognised.
        untracked = sorted(
            slug for slug, (_, back) in specs.items()
            if back in (brief_slug, rel, f"brief:{brief_slug}") and slug not in mapped
        )
        child_states = set(derived)
        child_states.update(
            status if status else "missing"
            for slug in untracked
            for status in (specs[slug][0],)
        )

        # Absent status: refused with a missing-status message.
        # Status not in the vocabulary: refused with a vocabulary message.
        # Child execution evidence contradicts the state table: refused.
        lifecycle_valid = False
        if brief_status is None:
            hard.append(f"{rel}: brief status is absent")
        elif brief_status not in _bs.BRIEF_STATUSES:
            hard.append(
                f"{rel}: brief status '{brief_status}' is not in the vocabulary"
            )
        elif not _bs.is_lifecycle_valid(brief_status, child_states):
            hard.append(
                f"{rel}: brief lifecycle '{brief_status}' contradicts its child scope"
            )
        else:
            lifecycle_valid = True

        # Cut-closed: value that is present but malformed: refused and named.
        if cut_closed is not None:
            cut_err = _bs.validate_cut_closed(cut_closed)
            if cut_err:
                hard.append(f"{rel}: Cut-closed: {cut_err}")

        # Declaration matrix: Shipped requires Cut-closed:; Draft refuses it.
        decl_err = _bs.validate_declaration(brief_status, cut_closed is not None)
        if decl_err:
            hard.append(f"{rel}: {decl_err}")

        # Case-insensitive so lowercase spec status tokens agree with drift.
        delivered = (
            brief_status == "Shipped"
            and lifecycle_valid
            and bool(mapped)
            and all(state.lower() == "shipped" for state in derived)
        )
        out.append(
            f"lint-brief-coverage: brief '{brief_slug}': "
            f"{'delivered' if delivered else 'not delivered'}"
        )
        for _, spec_slug, _ in rows:
            if spec_slug:
                status = specs.get(spec_slug, (None, None))[0]
                out.append(f"  - {spec_slug}: {status if status else 'missing'}")

        # Untracked: specs that back-link this brief but aren't in its map.
        # A back-link names the brief by `brief:<slug>` (canonical), by its
        # `Slug:` identity (bare slug), or by its repository-relative path;
        # all three resolve to this brief, so every spelling is recognised
        # here.
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
        # `git` may be unavailable on PATH; fall through to the
        # script-relative root, which is the intended fallback.
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
            f"lint-brief-coverage: {len(hard)} Spec-map violation(s).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
