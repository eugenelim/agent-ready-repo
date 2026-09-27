#!/usr/bin/env python3
"""Check the closure check's terminality projections against their upstreams.

`close-work` decides closure verdicts on whether a status is terminal, and the
surfaces owning that answer sit in sibling skills it may not import. It
therefore carries projections, and this gate is what keeps them honest: it runs
on every pull request through `build_gate_chain.py`, reads both upstreams
first-hand, and fails when either has moved.

It lives here rather than in `packs/core/tests/` for two reasons. It reads the
repository's governance corpus, which no portable pack test does — coupling a
pack to repository-private content is what the pack tests deliberately avoid.
And it imports two sibling skills at once, which only a repository-side tool
may do.

Exit 0 when both projections agree with their upstreams, 1 on any disagreement.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Iterator

_SLUG_RE = re.compile(r"^- \*\*Slug:\*\*\s*(.+?)\s*$", re.M)
_INTENT_STATES_HEADING = re.compile(r"^###\s+Intent states\s*$", re.M)
_ROW = re.compile(r"^\|\s*`?([A-Za-z]+)`?\s*\|.*\|\s*(yes|no)\s*\|\s*$", re.M)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise SystemExit(f"{path}: not importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _normalise_slug(raw: str) -> str:
    """Strip a trailing HTML comment, then surrounding backticks — in that order.

    The corpus's dominant shape is ``- **Slug:** `value` <!-- ... -->``. Stripping
    backticks first no-ops on it, because the line does not end in a backtick.
    """
    value = re.sub(r"<!--.*?-->\s*$", "", raw).strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def _intents(root: Path) -> Iterator[tuple[str, Path, str]]:
    for path in sorted((root / "docs" / "product" / "intents").glob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        match = _SLUG_RE.search(text)
        if match:
            yield _normalise_slug(match.group(1)), path, text


def _terminal_column(text: str, path: Path) -> dict[str, bool]:
    """Parse the Intent states table's Terminal column into status -> bool."""
    heading = _INTENT_STATES_HEADING.search(text)
    if heading is None:
        raise SystemExit(f"{path}: no '### Intent states' section to parse")
    section = text[heading.end():]
    next_heading = re.search(r"^###\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    table = {status: verdict == "yes" for status, verdict in _ROW.findall(section)}
    if not table:
        raise SystemExit(f"{path}: the Intent states table parsed to no rows")
    return table


def _walk_is_not_vacuous(root: Path, closure_index) -> list[str]:
    """Refuse a terminus whose inversion resolves nothing across the corpus.

    This is the control the unit suites structurally cannot provide. Every
    fixture states its own parent edges, so a walk and its fixtures can agree
    on a reference grammar the corpus does not use, and each side confirms the
    other while the walk returns nothing on real data.

    Checked **per terminus**, which is the part that makes it work. Each
    terminus inverts a different edge — ``children`` and ``brief`` invert
    ``Parent intent:``, ``spec`` inverts ``Discovery:`` — so a corpus-wide
    "something resolved somewhere" passes while one inversion is entirely
    dead. That is not hypothetical: matching ``Parent intent:`` against
    ``intent:<slug>`` alone read 5 of 49 declared edges, every
    ``children``-terminus ancestor resolved to an empty set, and a
    corpus-wide check still passed on the strength of the ``spec`` terminus.

    A terminus with no ancestors using it is skipped rather than failed.
    """
    dec_re = re.compile(r"^- \*\*Decomposed:\*\*\s*(.+?)\s*$", re.M)
    seen: dict[str, int] = {}
    resolved: dict[str, int] = {}
    for slug, _path, text in _intents(root):
        match = dec_re.search(text)
        if not match:
            continue
        value = _normalise_slug(match.group(1))
        parts = value.split()
        if len(parts) < 2 or parts[-1] not in ("children", "brief", "spec"):
            continue
        terminus = parts[-1]
        seen[terminus] = seen.get(terminus, 0) + 1
        found = closure_index._build_descendant_closure(
            root=root, ancestor_slug=slug, ancestor_terminus=terminus
        )
        if found:
            resolved[terminus] = resolved.get(terminus, 0) + 1
    failures: list[str] = []
    for terminus, count in sorted(seen.items()):
        if resolved.get(terminus, 0) == 0:
            failures.append(
                f"terminus {terminus!r}: its inversion resolved no descendant "
                f"beneath any of {count} ancestor(s) using it in the live "
                f"corpus — the edge it inverts does not match the grammar the "
                f"corpus writes"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    projection = _load(
        "closure_terminality",
        root / "packs/core/.apm/skills/close-work/scripts/closure_terminality.py",
    )
    brief_shape = _load(
        "brief_shape",
        root / "packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py",
    )
    lint_spec_status = _load(
        "lint_spec_status",
        root / "packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py",
    )
    closure_index = _load(
        "closure_index",
        root / "packs/core/.apm/skills/close-work/scripts/closure_index.py",
    )
    intent_shape = _load(
        "intent_shape",
        root / "packs/core/.apm/skills/work-intake/scripts/intent_shape.py",
    )

    wanted = projection.INTENT_TERMINALITY_UPSTREAM.slug
    source = next(((p, t) for slug, p, t in _intents(root) if slug == wanted), None)
    if source is None:
        print(
            f"check-closure-terminality-parity: no intent carries "
            f"Slug: {wanted} — the projection's upstream pin does not resolve",
            file=sys.stderr,
        )
        return 1
    path, text = source

    failures: list[str] = []
    for status in projection.intent_parity_disagreements(_terminal_column(text, path)):
        failures.append(
            f"intent status {status!r}: projection says "
            f"terminal={projection.is_intent_terminal(status)}, "
            f"{path.relative_to(root).as_posix()} disagrees or omits it"
        )
    for status in projection.brief_parity_disagreements(brief_shape.BRIEF_TRANSITIONS):
        failures.append(
            f"brief status {status!r}: projection says "
            f"terminal={projection.is_brief_terminal(status)}, "
            f"brief_shape.BRIEF_TRANSITIONS disagrees"
        )
    for status in projection.spec_parity_disagreements(lint_spec_status.CANONICAL_STATUSES):
        failures.append(
            f"spec status {status!r}: SPEC_STATUS_VOCABULARY and "
            f"lint-spec-status.py::CANONICAL_STATUSES disagree on membership"
        )
    for terminus in closure_index.terminus_parity_disagreements(
        intent_shape.DECOMPOSITION_TERMINI
    ):
        failures.append(
            f"terminus {terminus!r}: TERMINUS_VOCABULARY and "
            f"intent_shape.py::DECOMPOSITION_TERMINI disagree on membership"
        )
    for kind in closure_index.reference_kind_parity_disagreements(
        intent_shape.OUTCOME_CO_OWNER_KINDS
    ):
        failures.append(
            f"reference kind {kind!r}: REFERENCE_KIND_VOCABULARY and "
            f"intent_shape.py::OUTCOME_CO_OWNER_KINDS disagree on membership"
        )
    failures.extend(_walk_is_not_vacuous(root, closure_index))

    if failures:
        for line in failures:
            print(f"check-closure-terminality-parity: {line}", file=sys.stderr)
        print(
            "check-closure-terminality-parity: "
            f"{len(failures)} disagreement(s) — update the projection to match "
            "its upstream, never the other way round. Status projections live "
            "in close-work/scripts/closure_terminality.py; the terminus "
            "projection lives in close-work/scripts/closure_index.py",
            file=sys.stderr,
        )
        return 1

    print(
        "check-closure-terminality-parity: clean — "
        f"{len(projection.INTENT_STATUS_VOCABULARY)} intent, "
        f"{len(projection.BRIEF_STATUS_VOCABULARY)} brief and "
        f"{len(projection.SPEC_STATUS_VOCABULARY)} spec status(es) and "
        f"{len(closure_index.TERMINUS_VOCABULARY)} terminus(es) and "
        f"{len(closure_index.REFERENCE_KIND_VOCABULARY)} reference kind(s) agree with upstream; "
        "the live-corpus walk is not vacuous"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
