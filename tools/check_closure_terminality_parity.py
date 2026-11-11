#!/usr/bin/env python3
"""Check terminality projections against their upstreams.

`close-work` decides closure verdicts on whether a status is terminal, and the
surfaces owning that answer sit in sibling skills it may not import. It
therefore carries projections, and this gate is what keeps them honest: it runs
on every pull request through `build_gate_chain.py`, reads both upstreams
first-hand, and fails when either has moved.

`navigate-intents` carries a parity-checked copy of the same terminality rule
in `intent_terminality.py`. This tool checks that copy too: its intent, brief,
and spec terminal sets against `closure_terminality`'s upstreams, its spec
terminal subset against `closure_terminality` directly, and its
leading-word extraction against `lint-spec-status.py`'s `extract_status_token`
over a fixed probe set.

It lives here rather than in `packs/core/tests/` for two reasons. It reads the
repository's governance corpus, which no portable pack test does — coupling a
pack to repository-private content is what the pack tests deliberately avoid.
And it imports two sibling skills at once, which only a repository-side tool
may do.

Exit 0 when all projections agree with their upstreams, 1 on any disagreement.

Remediation: if a failure is reported, update the projection in
`close-work/scripts/closure_terminality.py` or
`navigate-intents/scripts/intent_terminality.py` to match its upstream, never
the other way round.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

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

    ``re.DOTALL`` matters and is not decoration: without it ``.`` stops at a
    newline, so a comment spanning lines is left in the value and every later
    comparison runs against text that still carries markup. It also keeps this
    in step with the shipped normalizers this tool exists to check against —
    ``intent_shape._COMMENT_SUFFIX`` and its counterpart in ``closure_index``
    both set it, and a parity tool that normalises differently from its
    subject can report a disagreement that is its own.
    """
    value = re.sub(r"<!--.*?-->\s*$", "", raw, flags=re.DOTALL).strip()
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
        try:
            found = closure_index._build_descendant_closure(
                root=root, ancestor_slug=slug, ancestor_terminus=terminus
            )
        except closure_index._ClosureDeliveryRefusal:
            # A refused ancestor (an unresolved delivery mapping) resolves no
            # descendant here; the per-terminus count still needs one that does.
            found = {}
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


# ── Navigator terminality seam functions ──────────────────────────────────────
# These are extracted so tests can import and call them directly against a
# mutated nav_terminality module, rather than re-implementing the checks locally.

_EXTRACT_PROBES: list[str] = [
    "Fulfilled",
    "Shipped",
    "Draft",
    "Accepted",
    # ' (' cases: delimiter comes after the status word (most common form)
    "Fulfilled (2026-01-01)",
    "Shipped (date)",
    "Draft (something)",
    "Approved (review)",
    # ' (' case: delimiter at position 0 — the only case where truncation
    # changes the first word (exercises the delimiter detection path)
    " (Fulfilled)",
    # ' →' cases
    "Fulfilled → next",
    "Shipped → archived",
    # '<!--' cases
    "Draft<!-- comment -->",
    "Accepted<!-- inline -->",
    "Superseded <!-- trailing -->",
    "Archived <!-- trailing -->",
    "",
    "  ",
    "Withdrawn",
]


def _check_nav_intent_parity(
    nav_terminality: Any,
    terminal_col: Mapping[str, bool],
) -> list[str]:
    """Compare the navigator's intent terminal set against the upstream Terminal column.

    Checks both directions: statuses the upstream marks terminal that the
    navigator disagrees on, and statuses the navigator marks terminal that are
    absent from the upstream column altogether.
    """
    failures: list[str] = []
    nav_set = nav_terminality.TERMINAL_INTENT_STATUSES
    for status, upstream_terminal in terminal_col.items():
        nav_says = status in nav_set
        if nav_says != upstream_terminal:
            failures.append(
                f"navigator intent status {status!r}: intent_terminality.py says "
                f"terminal={nav_says}, upstream Terminal column says "
                f"terminal={upstream_terminal}"
            )
    for status in nav_set:
        if status not in terminal_col:
            failures.append(
                f"navigator intent status {status!r}: marked terminal by "
                f"intent_terminality.py but absent from the upstream Terminal column"
            )
    return failures


def _check_nav_brief_parity(
    nav_terminality: Any,
    brief_transitions: Iterable[tuple[str, str]],
) -> list[str]:
    """Compare the navigator's brief terminality against brief_shape.BRIEF_TRANSITIONS.

    Derives the upstream terminal set from the no-outgoing-edge property of
    the transition table.  Checks both directions: the upstream vocabulary and
    the navigator's own brief vocabulary, so an extra status the navigator marks
    terminal is caught even if it does not appear in the upstream table.
    """
    failures: list[str] = []
    edges = frozenset(brief_transitions)
    upstream_vocab = frozenset(s for pair in edges for s in pair)
    # Navigator derives its brief terminality from its own _BRIEF_TRANSITIONS.
    # Access that to build the full check vocabulary.
    try:
        nav_edges: frozenset[tuple[str, str]] = frozenset(nav_terminality._BRIEF_TRANSITIONS)
    except AttributeError:
        nav_edges = frozenset()
    nav_vocab = frozenset(s for pair in nav_edges for s in pair)
    all_vocab = upstream_vocab | nav_vocab
    for status in sorted(all_vocab):
        upstream_terminal = (status in upstream_vocab) and not any(
            src == status for src, _ in edges
        )
        nav_says = nav_terminality.is_brief_terminal(status)
        if nav_says != upstream_terminal:
            failures.append(
                f"navigator brief status {status!r}: intent_terminality.py says "
                f"terminal={nav_says}, brief_shape.BRIEF_TRANSITIONS says "
                f"terminal={upstream_terminal}"
            )
    return failures


def _check_nav_spec_parity(
    nav_terminality: Any,
    closure_terminality: Any,
) -> list[str]:
    """Compare the navigator's spec terminal set against closure_terminality directly.

    The spec terminal subset has no upstream table, so closure_terminality is
    the authoritative source for this check.  Checks both directions.
    """
    failures: list[str] = []
    nav_spec_terminal = nav_terminality.TERMINAL_SPEC_STATUSES
    closure_spec_terminal = closure_terminality.TERMINAL_SPEC_STATUSES
    for status in closure_terminality.SPEC_STATUS_VOCABULARY:
        nav_says = status in nav_spec_terminal
        closure_says = status in closure_spec_terminal
        if nav_says != closure_says:
            failures.append(
                f"navigator spec status {status!r}: intent_terminality.py says "
                f"terminal={nav_says}, closure_terminality.py disagrees"
            )
    for status in nav_spec_terminal:
        if status not in closure_terminality.SPEC_STATUS_VOCABULARY:
            failures.append(
                f"navigator spec status {status!r}: marked terminal by "
                f"intent_terminality.py but absent from closure_terminality.py vocabulary"
            )
    return failures


def _check_nav_extraction(
    nav_terminality: Any,
    lint_spec_status: Any,
    probes: list[str] | None = None,
) -> list[str]:
    """Compare the navigator's _extract_status_token against lint-spec-status.py.

    Uses _EXTRACT_PROBES by default; pass a custom list for targeted tests.
    """
    failures: list[str] = []
    probe_set = probes if probes is not None else _EXTRACT_PROBES
    for probe in probe_set:
        nav_result = nav_terminality._extract_status_token(probe)
        lint_result = lint_spec_status.extract_status_token(probe)
        if nav_result != lint_result:
            failures.append(
                f"leading-word extraction probe {probe!r}: "
                f"intent_terminality._extract_status_token returns {nav_result!r}, "
                f"lint-spec-status.extract_status_token returns {lint_result!r}"
            )
    return failures


def _check_parent_kind_parity(resolver: Any, intent_shape: Any) -> list[str]:
    """Compare the resolver's parent-intent kinds to ``OUTCOME_CO_OWNER_KINDS``.

    Both directions: a kind upstream adds that the resolver lacks makes every
    parent edge carrying it unreadable, and a kind the resolver adds that
    upstream lacks accepts an edge the shipped grammar rejects.
    """
    resolver_kinds = frozenset(resolver._PARENT_INTENT_KINDS)
    upstream = frozenset(intent_shape.OUTCOME_CO_OWNER_KINDS)
    failures = [
        f"parent-intent kind {kind!r}: in intent_shape.OUTCOME_CO_OWNER_KINDS "
        f"but missing from intent_delivery_relations._PARENT_INTENT_KINDS"
        for kind in sorted(upstream - resolver_kinds)
    ]
    failures.extend(
        f"parent-intent kind {kind!r}: in intent_delivery_relations."
        f"_PARENT_INTENT_KINDS but absent from intent_shape.OUTCOME_CO_OWNER_KINDS"
        for kind in sorted(resolver_kinds - upstream)
    )
    return failures


def main(argv: list[str] | None = None, resolver_path: Path | None = None) -> int:
    """Run the parity checks; ``resolver_path`` lets tests point at a resolver copy."""
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
    resolver = _load(
        "intent_delivery_relations_parity",
        resolver_path
        or root / "packs/core/.apm/skills/close-work/scripts/intent_delivery_relations.py",
    )
    intent_shape = _load(
        "intent_shape",
        root / "packs/core/.apm/skills/work-intake/scripts/intent_shape.py",
    )
    nav_terminality = _load(
        "nav_intent_terminality",
        root / "packs/core/.apm/skills/navigate-intents/scripts/intent_terminality.py",
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
    terminal_col = _terminal_column(text, path)
    for status in projection.intent_parity_disagreements(terminal_col):
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
    failures.extend(_check_parent_kind_parity(resolver, intent_shape))
    failures.extend(_walk_is_not_vacuous(root, closure_index))

    # ── Navigator terminality copy checks (intent_terminality.py) ─────────────
    # Intent: compare against the lifecycle intent's Terminal column (the upstream
    # AC-0067 names), in both directions.
    for line in _check_nav_intent_parity(nav_terminality, terminal_col):
        failures.append(line)

    # Brief: compare against brief_shape.BRIEF_TRANSITIONS (the upstream
    # AC-0067 names), in both directions.
    for line in _check_nav_brief_parity(nav_terminality, brief_shape.BRIEF_TRANSITIONS):
        failures.append(line)

    # Spec: compare against closure_terminality directly (no upstream table for
    # the terminal subset; vocabulary is already pinned via spec_parity_disagreements).
    for line in _check_nav_spec_parity(nav_terminality, projection):
        failures.append(line)

    # Leading-word extraction: compare navigator's _extract_status_token against
    # lint-spec-status.py's extract_status_token over the fixed probe set.
    for line in _check_nav_extraction(nav_terminality, lint_spec_status):
        failures.append(line)

    if failures:
        for line in failures:
            print(f"check-closure-terminality-parity: {line}", file=sys.stderr)
        print(
            "check-closure-terminality-parity: "
            f"{len(failures)} disagreement(s) — update the projection to match "
            "its upstream, never the other way round. Status projections live "
            "in close-work/scripts/closure_terminality.py and "
            "navigate-intents/scripts/intent_terminality.py; the terminus "
            "projection lives in close-work/scripts/closure_index.py and the "
            "parent-intent kinds in close-work/scripts/intent_delivery_relations.py",
            file=sys.stderr,
        )
        return 1

    print(
        "check-closure-terminality-parity: clean — "
        f"{len(projection.INTENT_STATUS_VOCABULARY)} intent, "
        f"{len(projection.BRIEF_STATUS_VOCABULARY)} brief and "
        f"{len(projection.SPEC_STATUS_VOCABULARY)} spec status(es) and "
        f"{len(closure_index.TERMINUS_VOCABULARY)} terminus(es) and "
        f"{len(resolver._PARENT_INTENT_KINDS)} parent-intent kind(s) agree with upstream; "
        "navigator terminality copy agrees; "
        "the live-corpus walk is not vacuous"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
