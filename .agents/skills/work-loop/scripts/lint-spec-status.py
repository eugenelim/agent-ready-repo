#!/usr/bin/env python3
"""Spec *metadata* drift lint.

This is a `work-loop` **skill script**: it lives at
`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` and projects to
every adapter's `.../skills/work-loop/scripts/`, the same way `loop-cohort.py`
does. The agent runs it at the work-loop's finish-time checklist — *available
and agent-invoked, not fail-closed* (there is no PR-open hook event in an
adopter repo). It no-ops gracefully where Python is absent.

It can also run as a **fail-closed CI gate** where a PR event and Python both
exist. Do NOT wire it into the projected `pre-pr` hook body: that body projects
to adopter trees and would mis-fire — the finish-time skill checklist and a CI
gate are the two invocation surfaces. (An earlier design shipped this as a
standalone linter; it now ships as a skill script so it projects to adopters
too.)

It checks six invariants over `docs/specs/*/spec.md`, measured against the
contract pinned in `CONVENTIONS.md` § 4 (Spec metadata contract). Only the
header `- **Status:**` field is checked; `plan.md` status is out of v1 scope.

  (i)   status vocabulary — the leading status token is one of
        {Draft, Approved, Implementing, Shipped, Archived}. The token is the
        first word after `Status:`, truncated at the first ` (`, ` →`, or
        `<!--`, so annotated Frozen statuses like `Shipped (2026-05-26)` and
        `Approved → Shipped (…)` pass. HARD (exit non-zero).
  (ii)  ACs at the ship transition (diff-triggered) — a spec whose header
        status *changes to* `Shipped` in the diff against the base ref must
        have every Acceptance Criterion `[x]`. A `(deferred: <anchor>)` marker
        no longer makes a new ship transition valid; separable work leaves the
        final AC list through an approved amendment and a non-AC follow-on.
        Specs already `Shipped` on the base are grandfathered. If no base ref
        resolves, the invariant is skipped with a warning. HARD when it runs.
  (iii) dangling intra-repo references — both **doc** references (markdown
        links to local `.md` paths) and, since v1.1, repo-relative **code**
        references (full paths rooted at a known top-level dir or an explicit
        relative link, ending in `.py`/`.toml`/`.sh`/`.json`, locator suffix
        stripped) that don't resolve to a file. WARN-ONLY (never changes the
        exit code); promoting it to a hard invariant stays deferred pending
        the observed warn rate.
  (iv)  deferral anchors resolve — every real `(deferred: <slug>)` marker
        resolves against `workspace.toml [backlog].open`, in either entry
        shape: a legacy record's `slug`, or a canonical record's `path`
        reduced by `canonical_entry_anchor`. HARD (exit non-zero).
  (v)   spec↔contract traceability — a spec's
        `- **Contract:**` header (forward ref) names contract file(s) under
        `contracts/<type>/`; each must exist and carry a backward pointer — an
        `x-spec` extension (OpenAPI/AsyncAPI YAML/JSON) or a `contracts/REGISTRY.md`
        row (extensionless formats). WARN-ONLY (never changes the exit code;
        mirrors invariant (iii)). No-ops where the spec names no contract
        (non-API features: empty / "none" / the template placeholder) or no
        `contracts/` tree exists — the common case in repos with no API surface.
  (vi)  Acceptance-Criteria section presence (diff-triggered) — a new spec, or
        a spec whose Acceptance-Criteria section was present at the base ref
        and is missing now, must carry the
        `- **Acceptance Criteria:** none — <reason>` opt-out header. Specs whose
        section was already absent at the base ref are grandfathered. If no
        base ref resolves, the invariant is skipped with a warning. HARD when
        it runs; malformed or contradictory markers are always HARD.

Exit codes: 0 = clean (warnings allowed), 1 = one or more HARD violations.
By default, per-spec checks run only for spec directories changed from the base
ref.  In CI, pass ``--all`` to retain the full sweep.  The warn-only dangling
reference pass always reads every spec because its value is repository-wide.

Usage: lint-spec-status.py [--root DIR] [--base-ref REF] [--all]
"""

from __future__ import annotations

import argparse
import bisect
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

CANONICAL_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Approved", "Implementing", "Shipped", "Archived"}
)

# Header status line, e.g. `- **Status:** Shipped (2026-05-26)`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(.+?)\s*$")
# ATX section heading at level ≥2: 0–3 optional spaces, two or more #, then
# a space/tab or end-of-line.  CommonMark (spec §4.2) allows up to three
# leading spaces before the opening #s; four spaces would be a code block.
_SECTION_HEADING_RE = re.compile(r"^ {0,3}#{2,}(?:[ \t]|$)")
# HTML comment span (including multiline).  Applied to the full spec text
# before line iteration so that a commented-out status like:
#   <!--
#   - **Status:** Approved
#   -->
# does not satisfy a lifecycle guard ahead of the real active field.
# re.DOTALL lets the pattern cross newlines.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A real deferral marker carries a slug anchor — NOT the template
# placeholder `(deferred: <anchor>)`, whose `<…>` form is excluded by the
# leading-alphanumeric class.
_DEFERRED_RE = re.compile(r"\(deferred:\s*([A-Za-z0-9][A-Za-z0-9._\-]*)\s*\)")
# Markdown inline link target: [text](target)
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
# Backticked span: `…` — the dominant carrier of code references in specs.
_BACKTICK_RE = re.compile(r"`([^`]+)`")
# Invariant (iii) v1.1: repo-relative *code* references. A reference is only
# resolvable if it's a full repo-relative path — rooted at a known top-level
# directory (or an explicit ../ / ./ relative link target) and ending in a
# recognised code extension. Bare basenames, placeholders, and globs are out.
_CODE_ROOTS = ("packages/", "tools/", "packs/", "apps/", "docs/", ".github/")
_CODE_EXTS = (".py", ".toml", ".sh", ".json")
# Header contract line (invariant v), e.g. `- **Contract:** `contracts/openapi/orders.yaml``.
_CONTRACT_HEADER_RE = re.compile(r"\*\*Contract:\*\*\s*(.+?)\s*$")
# A repo-relative contract path token under the `contracts/` tree.
# Segments may not be `.` or `..`: the token is joined onto `--root` and read,
# so a permissive class containing `.` and `/` let `contracts/../../secret.json`
# escape the tree. `_within()` at the join site is the actual control; this
# rejects the traversal earlier so the warning text stays honest. Each segment
# must therefore start with an alphanumeric.
_CONTRACT_SEGMENT = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_CONTRACT_TOKEN_RE = re.compile(rf"contracts/(?:{_CONTRACT_SEGMENT}/)*{_CONTRACT_SEGMENT}")
# Vendor-extension-bearing contract formats (carry `x-spec` inline); other
# formats (e.g. .proto, .graphql) use the REGISTRY.md back-ref channel.
_XSPEC_FORMATS = (".yaml", ".yml", ".json")
# AC checklist items.
_AC_OPEN_RE = re.compile(r"^\s*-\s*\[ \]\s")
_AC_DONE_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")
# The section-presence invariant and the criterion collector must share this
# matcher: accepting a spelling that the collector cannot read recreates the
# vacuous pass invariant (vi) exists to close.
#
# EXACT on purpose. This was case-insensitive and accepted `###` and up to three
# leading spaces, which is how six specs drifted to `## Acceptance criteria`
# despite the new-spec template emitting the canonical form all along: a
# hand-written variant passed silently, so nothing corrected it. One supported
# shape, read exactly, is what stops the residue reappearing.
_AC_SECTION_HEADING_RE = re.compile(r"^## Acceptance Criteria\b")
# A heading differing only in case, level, or indentation. Not accepted --
# accepting it IS the drift path -- but not silent either: it earns a warning
# naming the exact form. Silence would un-gate an adopter's spec without telling
# anyone, which is the failure this invariant exists to prevent.
_AC_HEADING_NEAR_MISS_RE = re.compile(
    r"^ {0,3}#{2,3}[ \t]+Acceptance Criteria\b", re.IGNORECASE
)
# What the CRITERION COLLECTOR matches. Deliberately looser than
# `_AC_SECTION_HEADING_RE`, and the direction is the whole point.
#
# Invariant (vi) -- "is there a section?" -- uses the EXACT matcher, so the
# canonical heading is enforced and drift cannot reseed. The collector uses this
# one, so invariant (ii) never stops reading criteria it can plainly see.
#
# Measured before this split existed: an adopter shipping a spec with an unmet
# criterion under `## Acceptance criteria` went from
# `invariant (ii) — AC is unchecked and not deferred` (exit 1) to a warning and
# exit 0. Making the collector strict did not break their build; it silently
# stopped catching a real violation, which is worse -- and is the vacuous pass
# invariant (vi) exists to close. Over-reading is the safe direction here;
# under-reading is how a gate goes quiet.
_AC_COLLECTOR_HEADING_RE = _AC_HEADING_NEAR_MISS_RE


def _code_span_ranges(line: str) -> list[tuple[int, int]]:
    """Inline code spans on one line, by a linear scan over backtick runs.

    A run of N backticks opens; the next run of exactly N closes. Deliberately
    not a regex: the obvious ``(`+)(?:(?!\1).)*?\1`` backtracks cubically on a
    long backtick run -- measured, a 12 KB backtick line took 106 s, against a
    file-size cap that admits 8 MB of untrusted repository content.
    """
    runs: list[tuple[int, int]] = []
    index, length = 0, len(line)
    while index < length:
        if line[index] == "`":
            end = index
            while end < length and line[end] == "`":
                end += 1
            runs.append((index, end - index))
            index = end
        else:
            index += 1
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(runs):
        open_at, open_len = runs[cursor]
        probe = cursor + 1
        while probe < len(runs) and runs[probe][1] != open_len:
            probe += 1
        if probe < len(runs):
            spans.append((open_at, runs[probe][0] + runs[probe][1]))
            cursor = probe + 1
        else:
            cursor += 1
    return spans


def _commented_line_numbers(spec_text: str) -> set[int]:
    """Line numbers that fall inside a REAL HTML comment.

    ONE notion of "commented", shared by every caller. An opener inside an
    inline code span does not open a comment: one live spec documents a
    template whose fields carry comment-syntax annotations, writing an opener
    and a closer in backticks 23 lines apart, and a code-span-blind reader
    pairs those two *mentions* into a false span over that spec's real heading
    and all 17 of its criteria. An opener with no closer is literal text.
    """
    lines = spec_text.splitlines()
    offsets: list[int] = []
    position = 0
    for raw in spec_text.splitlines(keepends=True):
        offsets.append(position)
        position += len(raw)

    masked: set[int] = set()
    for index, line in enumerate(lines):
        for span_start, span_end in _code_span_ranges(line):
            masked.update(range(offsets[index] + span_start,
                                offsets[index] + span_end))

    commented: set[int] = set()
    cursor = 0
    while True:
        opener = spec_text.find("<!--", cursor)
        if opener < 0:
            return commented
        if opener in masked:
            cursor = opener + 4
            continue
        closer = spec_text.find("-->", opener + 4)
        if closer < 0:
            return commented  # unterminated opener is literal text
        first = bisect.bisect_right(offsets, opener)
        last = bisect.bisect_right(offsets, closer + 2)
        commented.update(range(first, last + 1))
        cursor = closer + 3


def commented_out_ac_heading(spec_text: str) -> tuple[int, str] | None:
    """Return an Acceptance-Criteria heading that is inside an HTML comment.

    A commented-out Acceptance-Criteria section is not a supported shape, in
    any position. Criteria that no longer apply are DELETED -- git history is
    where superseded ones live, not a comment block the linter has to reason
    about. HTML comments themselves stay welcome in a spec: the template emits
    16 of them and 245 of 407 specs carry one in the metadata preamble. It is
    specifically a commented-out AC SECTION that is rejected.

    Fires wherever one appears -- alone, beside a live section, or beside an
    opt-out marker. Rejecting it in every position is what stops the criterion
    collector ever meeting one, which is why the collector can stay
    comment-blind without that being a latent divergence.

    An earlier version excluded the beside-a-live-section and beside-a-marker
    cases as "the author's business". That let a commented, superseded `- [ ]`
    be collected as a real criterion and block a ship on work nobody intended
    to do.

    An opener inside an inline code span does not open a comment. That is not
    hypothetical: `docs/specs/digital-experience-contract/spec.md` writes
    ``<!-- Required:`` and a matching closer in backticks 23 lines apart, and a
    code-span-blind reader pairs those two *mentions* into a false span over
    that spec's real heading and all 17 of its criteria.
    """
    lines = spec_text.splitlines()
    headings = {n for n, line in _unfenced_lines(spec_text)
                if _AC_COLLECTOR_HEADING_RE.match(line)}
    if not headings:
        return None

    commented = _commented_line_numbers(spec_text) & headings
    if commented:
        lineno = min(commented)
        return lineno, lines[lineno - 1].strip()
    return None

    offsets: list[int] = []
    position = 0
    for raw in spec_text.splitlines(keepends=True):
        offsets.append(position)
        position += len(raw)

    masked: set[int] = set()
    for index, line in enumerate(lines):
        for span_start, span_end in _code_span_ranges(line):
            masked.update(range(offsets[index] + span_start,
                                offsets[index] + span_end))

    commented: set[int] = set()
    cursor = 0
    while True:
        opener = spec_text.find("<!--", cursor)
        if opener < 0:
            break
        if opener in masked:
            cursor = opener + 4
            continue
        closer = spec_text.find("-->", opener + 4)
        if closer < 0:
            break  # an unterminated opener is literal text, not a comment
        first = bisect.bisect_right(offsets, opener)
        last = bisect.bisect_right(offsets, closer + 2)
        commented.update(n for n in headings if first <= n <= last)
        cursor = closer + 3

    # Only when EVERY heading is commented out. A commented draft beside a live
    # section is the author's business, not a defect.
    if commented and commented == headings:
        lineno = min(commented)
        return lineno, lines[lineno - 1].strip()
    return None
# Explicit opt-out for a spec that intentionally has no AC section. The reason
# group is optional so the parser can distinguish a missing marker (None) from
# a present but reasonless marker (an empty string).


_AC_OPT_OUT_HEADER_RE = re.compile(
    r"^- \*\*Acceptance Criteria:\*\*\s*none(?:[ \t]+—[ \t]*(.*?))?[ \t]*$"
)
# Case-insensitive candidate used only to produce a precise diagnostic when an
# author intended the opt-out but missed its exact casing or separator syntax.
# Deliberately WIDER than `_AC_OPT_OUT_HEADER_RE`, which stays exact. This one
# only decides "did the author try to write an opt-out", so it must recognise
# the attempt however it was spelled -- otherwise a visibly attempted marker
# escapes both readers and the spec passes clean with a malformed opt-out on the
# page. Measured before this widened: four of five plausible shapes escaped --
# an indented marker, a `*` bullet, a colon outside the bold, and a double space
# after the bullet. Widening what we DIAGNOSE is not widening what we ACCEPT.
_AC_OPT_OUT_NEAR_MISS_RE = re.compile(
    r"^(?P<indent> {0,3})(?P<bullet>[-*+])(?P<gap>[ \t]+)"
    r"\*\*Acceptance[ \t]+Criteria(?:\*\*[ \t]*:|:\*\*)(?P<value>.*)$",
    re.IGNORECASE,
)
_PLACEHOLDER_REASON_RE = re.compile(r"^<[^<>]*>$")


def _unfenced_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield source lines outside CommonMark fenced code regions."""
    fence_char: str | None = None
    fence_len = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        marker = stripped[:1]
        if marker in ("`", "~"):
            run = len(stripped) - len(stripped.lstrip(marker))
            info = stripped[run:].strip()
            if fence_char is None:
                if run >= 3:
                    fence_char, fence_len = marker, run
                    continue
            elif marker == fence_char and run >= fence_len and not info:
                fence_char = None
                fence_len = 0
                continue
        if fence_char is None:
            yield lineno, line


def extract_status_token(raw: str) -> str:
    """Return the leading status token from a header status value.

    Truncates at the first ` (`, ` →`, or `<!--` so annotated Frozen
    statuses (`Shipped (date)`, `Approved → Shipped (…)`,
    `Draft <!-- ... -->`) reduce to their leading word.
    """
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    return text.strip().split()[0] if text.strip() else ""


def parse_status(spec_text: str) -> str | None:
    """Return the leading status token from a spec's metadata preamble, or None.

    Stops at the first second-level heading (## …) so body text that contains
    **Status:** in examples, task descriptions, or quoted templates cannot
    accidentally satisfy a lifecycle guard.
    """
    # Strip HTML comments from the full text first.  Per-line stripping does
    # not remove multiline comments, so an interior `- **Status:** Approved`
    # inside a block comment would be returned before the live status field.
    cleaned = _HTML_COMMENT_RE.sub("", spec_text)
    for line in cleaned.splitlines():
        if _SECTION_HEADING_RE.match(line):
            break  # preamble ends at the first section heading
        if line.lstrip().startswith("#"):
            continue  # skip ATX heading lines — Status must not live in a heading
        m = _STATUS_RE.search(line)
        if m:
            return extract_status_token(m.group(1))
    return None


def status_uses_list_item_form(spec_text: str) -> bool:
    """Report whether the live status field uses the `- **Status:**` form.

    The workspace-status engine anchors on that list-item form and treats a
    bare `**Status:**` as no status at all, so the two surfaces disagree about
    the same file. Scans the same preamble window as `parse_status`.
    """
    cleaned = _HTML_COMMENT_RE.sub("", spec_text)
    for line in cleaned.splitlines():
        if _SECTION_HEADING_RE.match(line):
            break
        if line.lstrip().startswith("#"):
            continue
        if _STATUS_RE.search(line):
            return line.lstrip().startswith("- **Status:**")
    return False


def canonical_entry_anchor(path: str) -> str | None:
    """Derive a deferral anchor from a canonical entry's `path`.

    A canonical `[backlog].open` entry carries `path`/`kind` and no `slug`, so
    resolving invariant (iv) from the `slug` key alone would oblige every
    deferring spec to write a legacy-shaped record. A spec or plan path
    (`docs/specs/<slug>/spec.md`) anchors on its owning directory; any other
    artifact anchors on its file stem, which is how the shaping slugs these
    entries replaced were already named.
    """
    if not path:
        return None
    parts = [part for part in path.split("/") if part]
    if not parts:
        return None
    name = parts[-1]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    if stem in {"spec", "plan"} and len(parts) >= 2:
        return parts[-2] or None
    return stem or None


def _regex_backlog_slugs(workspace_text: str) -> set[str]:
    """Extract [backlog].open anchors from workspace.toml text via regex fallback.

    Used when tomllib/tomli is unavailable or the TOML is malformed. Scans the
    [backlog] section for both `slug = "..."` (legacy shape) and `path = "..."`
    (canonical shape). Without a parser this cannot separate an entry's own
    `path` from a `needs` target, so it may over-collect; a fallback that is
    too permissive only fails to report an unresolved anchor, whereas one that
    is too strict would fail a correct spec.
    """
    slugs: set[str] = set()
    in_backlog = False
    for line in workspace_text.splitlines():
        if re.match(r"^\s*\[backlog\]", line):
            in_backlog = True
        elif re.match(r"^\s*\[", line) and "[backlog]" not in line:
            in_backlog = False
        if in_backlog:
            m = re.search(r'\bslug\s*=\s*"([^"]+)"', line)
            if m:
                slugs.add(m.group(1))
            for raw_path in re.findall(r'\bpath\s*=\s*"([^"]+)"', line):
                anchor = canonical_entry_anchor(raw_path)
                if anchor:
                    slugs.add(anchor)
    return slugs


def backlog_open_slugs(workspace_path: Path) -> set[str]:
    """Return the set of resolvable deferral anchors from [backlog].open.

    Accepts both entry shapes: a legacy `{slug = ...}` record anchors on its
    `slug`, and a canonical `{path = ..., kind = ...}` record anchors on the
    identifier derived by `canonical_entry_anchor`. Supporting both is what
    stops invariant (iv) from obliging a deferring spec to write a legacy
    record in order to be resolvable.

    Uses tomllib (Python 3.11+ stdlib) or tomli (backport) when available;
    falls back to regex for all other cases including malformed TOML.
    Returns an empty set when workspace.toml is absent.
    """
    if not workspace_path.is_file():
        return set()
    text = workspace_path.read_text(encoding="utf-8", errors="replace")
    try:
        try:
            import tomllib  # type: ignore[import]
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import,no-redef]
            except ImportError:
                return _regex_backlog_slugs(text)
        data = tomllib.loads(text)
        anchors: set[str] = set()
        for entry in data.get("backlog", {}).get("open", []):
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug")
            if isinstance(slug, str) and slug:
                anchors.add(slug)
                continue
            entry_path = entry.get("path")
            if isinstance(entry_path, str):
                derived = canonical_entry_anchor(entry_path)
                if derived:
                    anchors.add(derived)
        return anchors
    except ValueError:
        return _regex_backlog_slugs(text)


def deferred_anchors(spec_text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(spec_text.splitlines(), start=1):
        for m in _DEFERRED_RE.finditer(line):
            out.append((lineno, m.group(1)))
    return out


def _candidate_code_path(token: str) -> str | None:
    """Return the repo-relative code path from a raw reference token, or None
    if the token is not a full repo-relative code reference (invariant iii v1.1).

    Accepts: contains `/`, ends in a recognised code extension (after stripping
    a trailing `:<line>` / `:<range>` / `#<anchor>` locator), and is either
    rooted at a known top-level directory or an explicit `../` / `./` relative
    link target. Rejects bare basenames, placeholders (`<>`), globs (`*`),
    and prose ellipses (`...`).
    """
    # Reject placeholders (`<>`), globs (`*`), brace-expansion shorthand
    # (`{a,b}.py`), and prose ellipses (`...`, e.g. an abbreviated path like
    # `packs/core/...session-start.toml`) — none denote a single literal path.
    if (any(c in token for c in "<>*{}") or "://" in token
            or "..." in token or "/" not in token):
        return None
    path: str | None = None
    for ext in _CODE_EXTS:
        idx = token.find(ext)
        if idx == -1:
            continue
        end = idx + len(ext)
        rest = token[end:]
        # The extension must terminate the path or be followed only by a
        # locator (`:` line/range or `#` anchor) — so `.python` won't match `.py`.
        if rest == "" or rest[0] in ":#":
            path = token[:end]
            break
    if path is None:
        return None
    if not (path.startswith(_CODE_ROOTS) or path.startswith(("../", "./"))):
        return None
    return path


def code_references(text: str) -> list[tuple[int, str]]:
    """Yield (lineno, repo-relative path) for full repo-relative code
    references in backticked spans or markdown links. De-duplicated per path
    so a file referenced many times warns once."""
    out: list[tuple[int, str]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        tokens = [m.group(1) for m in _BACKTICK_RE.finditer(line)]
        tokens += [m.group(1) for m in _LINK_RE.finditer(line)]
        for tok in tokens:
            path = _candidate_code_path(tok.strip())
            if path is not None and path not in seen:
                seen.add(path)
                out.append((lineno, path))
    return out


def contract_header_refs(spec_text: str) -> list[tuple[int, str]]:
    """Return (lineno, contract-path) for each `contracts/...` token on the
    spec's `- **Contract:**` header line. Returns [] for a non-API feature —
    an empty value, `none`, or the template placeholder (an HTML comment)."""
    for lineno, line in enumerate(spec_text.splitlines(), start=1):
        m = _CONTRACT_HEADER_RE.search(line)
        if not m:
            continue
        value = m.group(1).strip()
        if not value or value.lower() == "none" or value.startswith("<!--"):
            return []
        return [(lineno, tm.group(0)) for tm in _CONTRACT_TOKEN_RE.finditer(value)]
    return []


def acceptance_criteria_opt_out(spec_text: str) -> tuple[int, str] | None:
    """Return ``(lineno, reason)`` for the Acceptance-Criteria opt-out.

    ``None`` means the marker is absent; an empty reason means the marker is
    present but reasonless. Only metadata-preamble fields count, and HTML
    comments are removed while preserving line numbers.
    """
    cleaned = _HTML_COMMENT_RE.sub(
        lambda match: "\n" * match.group(0).count("\n"), spec_text
    )
    for lineno, line in _unfenced_lines(cleaned):
        if _SECTION_HEADING_RE.match(line):
            break
        match = _AC_OPT_OUT_HEADER_RE.match(line)
        if match:
            return lineno, (match.group(1) or "").strip()
    return None


def acceptance_criteria_opt_out_near_miss(
    spec_text: str,
) -> tuple[int, str] | None:
    """Return a precise error for an unparsable opt-out-shaped preamble line."""
    cleaned = _HTML_COMMENT_RE.sub(
        lambda match: "\n" * match.group(0).count("\n"), spec_text
    )
    for lineno, line in _unfenced_lines(cleaned):
        if _SECTION_HEADING_RE.match(line):
            break
        if _AC_OPT_OUT_HEADER_RE.match(line):
            continue
        match = _AC_OPT_OUT_NEAR_MISS_RE.match(line)
        if match is None:
            continue
        value = match.group("value").strip()
        # Claim only a `none`-variant value. Prose in this field is not an
        # attempted opt-out, and claiming it would hard-fail a spec that has a
        # perfectly good Acceptance-Criteria section.
        if not re.match(r"^none\b", value, re.IGNORECASE):
            continue
        if match.group("indent"):
            return lineno, "marker must start at column 0, not indented"
        if match.group("bullet") != "-":
            return lineno, (
                f"marker must use a `-` bullet, not "
                f"`{match.group('bullet')}`"
            )
        if match.group("gap") != " ":
            return lineno, "marker must have exactly one space after the `-`"
        if not line.startswith("- **Acceptance Criteria:**"):
            if line.startswith("- **Acceptance Criteria**:"):
                return lineno, (
                    "the colon belongs inside the bold: "
                    "`**Acceptance Criteria:**`, not `**Acceptance Criteria**:`"
                )
            return lineno, "field name must use exact casing `Acceptance Criteria`"
        if value.lower().startswith("none") and not value.startswith("none"):
            return lineno, "marker value must use exact lowercase casing `none`"
        if re.match(r"^none[ \t]+-[ \t]*", value):
            return lineno, (
                "separator must be an em dash (U+2014), not an ASCII hyphen"
            )
        return lineno, (
            "marker must exactly match "
            "`- **Acceptance Criteria:** none — <one-line reason>`"
        )
    return None


def acceptance_criteria_section_present(spec_text: str) -> bool:
    """Return whether a LIVE canonical section heading is present.

    A heading inside an HTML comment is not a section. Counting one made a spec
    that correctly opted out AND kept an abandoned draft in a comment fail the
    "both a section and an opt-out header" contradiction check.

    Deliberately stricter than the collector, which still reads a commented
    heading's criteria. The asymmetry is safe in this direction: the collector
    over-reading can only add criteria to check, never hide one. The reverse --
    presence accepting a shape the collector cannot read -- is the vacuous pass
    this invariant exists to close.
    """
    commented = _commented_line_numbers(spec_text)
    return any(
        _AC_SECTION_HEADING_RE.match(line)
        for lineno, line in _unfenced_lines(spec_text)
        if lineno not in commented
    )


def acceptance_criteria_lines(spec_text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for every checklist item inside the
    `## Acceptance Criteria` section.

    The heading match is case-INSENSITIVE, and that is the whole point. It was
    case-sensitive, so a spec whose heading read `## Acceptance criteria`
    collected zero criteria and its AC-completeness invariant passed
    *vacuously* — the check reported success on a spec it had not read. That
    silently un-gated 18 specs before it was noticed, and the number only grows,
    because nothing tells an author which casing the linter wants.

    A vacuous pass is the worst failure mode a gate has: it is indistinguishable
    from a real one at the call site.
    """
    out: list[tuple[int, str]] = []
    in_ac = False
    opened_level = 0
    for lineno, line in _unfenced_lines(spec_text):
        if _AC_COLLECTOR_HEADING_RE.match(line):
            in_ac = True
            stripped = line.lstrip()
            opened_level = len(stripped) - len(stripped.lstrip("#"))
            continue
        if in_ac and _SECTION_HEADING_RE.match(line):
            stripped = line.lstrip()
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            if heading_level <= opened_level:
                break
        if in_ac and (_AC_OPEN_RE.match(line) or _AC_DONE_RE.match(line)):
            out.append((lineno, line))
    return out


# Local git metadata and object reads must not indefinitely stall a lint run.
# This matches the local-git bound used by the work-loop's engine and cohort.
GIT_TIMEOUT_S = 20.0


class _BaseTextUndetermined:
    """Private sentinel for a base object read that did not complete.

    This is deliberately distinct from ``None``, which means the path was
    absent at an otherwise-resolvable base.  The union return type requires a
    caller to handle this state before using the text in a diff invariant.
    """


_BASE_TEXT_UNDETERMINED = _BaseTextUndetermined()


def resolve_default_base_ref(root: Path) -> str | None:
    """Resolve the diff base ref, preferring `origin/<default-branch>`."""
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "origin/HEAD"],
            capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_S,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None  # git unavailable or timed out
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    # Fall back to origin/main if it exists.
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", "origin/main"],
            capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return None
    return "origin/main" if r.returncode == 0 else None


def base_ref_resolves(root: Path, base_ref: str) -> bool:
    """Whether *base_ref* names a real commit in *root*.

    An explicit `--base-ref` was taken on trust. When it did not resolve,
    `base_spec_text` returned None for EVERY spec, which the diff-triggered
    invariants read as "this spec is new" -- so a typo'd or unfetched ref
    red-lined an entire clean corpus, telling each author to add an opt-out
    marker for a section that was there all along. The module docstring
    promises the opposite: an unresolvable base ref skips with a warning.
    """
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet",
             f"{base_ref}^{{commit}}"],
            capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False  # git unavailable: no base ref is resolvable
    return probe.returncode == 0


def base_spec_text(
    root: Path, relpath: str, base_ref: str
) -> str | None | _BaseTextUndetermined:
    """Return base content, ``None`` when absent, or a timeout sentinel.

    The sentinel cannot be treated as a new spec: callers must skip their
    diff-triggered checks and report the undetermined base read.
    """
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "show", f"{base_ref}:{relpath}"],
            capture_output=True, text=True, errors="replace", check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return _BASE_TEXT_UNDETERMINED
    return r.stdout if r.returncode == 0 else None


def changed_spec_paths(root: Path, base_ref: str) -> list[Path] | None:
    """Return current spec files for directories changed from ``base_ref``.

    ``None`` means Git could not determine the changed set, which callers must
    treat as a full-sweep fallback rather than as an empty, clean selection.
    A change anywhere below ``docs/specs/<slug>/`` selects that directory's
    current ``spec.md`` so plan-only edits retain metadata coverage.
    """
    try:
        result = subprocess.run(
            # `--relative` and `-z`, both load-bearing. Without --relative git
            # reports paths from the REPO root, so a `--root` that is a
            # subdirectory yields `sub/docs/specs/...`, the `docs/specs` prefix
            # filter below drops every entry, and the per-spec pass becomes a
            # silent no-op. Without -z a path needing quoting arrives as
            # `"docs/specs/caf\303\251/spec.md"`, whose first part is `"docs`,
            # and that spec is dropped the same way.
            ["git", "-C", str(root), "diff", "--name-only", "-z", "--relative",
             base_ref, "--", "docs/specs"],
            capture_output=True, text=True, errors="replace", check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    # `git diff` reports TRACKED changes only, so a brand-new spec that has not
    # been committed yet is invisible to it -- and a brand-new spec is exactly
    # what an author has open during a work-loop session. Without this second
    # call the scoped default silently stops linting the file being written,
    # which is worse than the cost the scoping removes.
    try:
        untracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard",
             "-z", "--", "docs/specs"],
            capture_output=True, text=True, errors="replace", check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if untracked.returncode != 0:
        return None

    specs_dir = root / "docs" / "specs"
    changed: set[Path] = set()
    # -z output is NUL-separated with a trailing NUL, so the final split
    # element is empty; the falsy guard drops it.
    reported = result.stdout.split("\0") + untracked.stdout.split("\0")
    for relpath in (entry for entry in reported if entry):
        parts = Path(relpath).parts
        if len(parts) < 3 or parts[:2] != ("docs", "specs"):
            continue
        spec_path = _confined_file(specs_dir / parts[2] / "spec.md", root)
        if spec_path is not None:
            changed.add(spec_path)
    return sorted(changed)


# Skip implausibly large files — an untrusted repo could ship a multi-GB
# spec.md or contract; reading it whole is a memory-exhaustion DoS. Mirrors
# lint-traceability.py's guard of the same name.
_MAX_FILE_BYTES = 8 * 1024 * 1024


def _read(path: Path) -> str | None:
    """Size-guarded read. Returns None when the file is too large or unreadable."""
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _within(path: Path, root: Path) -> bool:
    """True when `path` is inside `root` after symlink resolution.

    Ported from lint-traceability.py, which has carried this confinement since
    it was written. This file did not, and that was a real gap, not a stylistic
    one: `Contract:` header tokens are matched by `_CONTRACT_TOKEN_RE`, whose
    character class contains `.` and `/`, so a header reading
    `contracts/../../secret.json` in an untrusted spec.md resolved outside
    `--root` and was read. That produced both an existence oracle (two distinct
    warnings depending on whether the target existed) and a content-substring
    oracle. `docs/architecture/security.md` declares `filesystem_read_untrusted`
    a boundary, so hostile repo content is in scope.
    """
    return _confined_path(path, root) is not None


def _confined_path(path: Path, root: Path) -> Path | None:
    """Return the canonical path only when it remains below ``root``."""
    try:
        resolved = path.resolve()
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None


def _confined(paths, root: Path) -> list[Path]:
    """Globbed / iterated paths filtered to those within `root`.

    `pathlib.glob` follows symlinked directories, so each result is re-checked
    before it is read — a symlinked `docs/specs/<slug>` cannot pull in a
    spec.md from outside the tree.
    """
    confined: list[Path] = []
    for path in paths:
        canonical = _confined_path(path, root)
        if canonical is not None:
            confined.append(canonical)
    return confined


def _confined_file(path: Path, root: Path) -> Path | None:
    """Return a canonical in-root regular-file candidate, else ``None``."""
    canonical = _confined_path(path, root)
    return canonical if canonical is not None and canonical.is_file() else None


def _validated_root(candidate: Path | None) -> Path:
    """Resolve the CLI-supplied root, or fall back to `_repo_root()`.

    The normalise-then-check is deliberately kept *in one function, adjacent to
    the argv read*, because that is the shape taint analysers recognise. Same
    pattern as `_loop_guards.check_artifact_status`.

    Normalises and asserts directory-ness only — it does not confine the root
    to a fixed prefix, since `--root` is the caller-supplied scan scope. Note
    this also fixes a real usability trap: before the check, a typo'd `--root`
    scanned an empty tree and reported "spec metadata clean".
    """
    raw = candidate if candidate is not None else _repo_root()
    # `_within()` in the sibling script already catches this trio; resolve()
    # raises ValueError on an embedded null and OSError on a Windows reserved
    # name, neither of which is an OSError-only case. Letting them through
    # would produce the traceback this function exists to replace.
    try:
        root = raw.resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"lint-spec-status: --root is not a usable path: {raw!r} ({exc})"
        ) from exc
    if not root.exists():
        raise SystemExit(f"lint-spec-status: --root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"lint-spec-status: --root is not a directory: {root}")
    return root


def _repo_root() -> Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_S,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # `git` may be unavailable on PATH; fall through to the
        # script-relative root, which is the intended fallback.
        pass
    return Path(__file__).resolve().parent.parent


def _repo_wide_findings(
    root: Path, spec_paths: list[Path], anchors: set[str]
) -> tuple[list[str], list[str]]:
    """Return `(hard, warn)` for the invariants that must span every spec.

    Two invariants belong here rather than in the per-spec pass, for different
    reasons:

      (iii) dangling references — warn-only, and its value is repository-wide.
      (iv)  deferral anchors — HARD, and its second input is `workspace.toml`,
            not the spec file. Closing a `[backlog].open` entry invalidates the
            marker in every spec that cites it, none of which need have changed,
            so scoping this to changed specs would let the routine close-work
            operation break anchors with nothing reporting it.

    Both read the same text, so they share one pass over the corpus.
    """
    hard: list[str] = []
    warn: list[str] = []
    for spec_path in spec_paths:
        rel = spec_path.relative_to(root).as_posix()
        text = _read(spec_path)
        if text is None:
            warn.append(
                f"{rel}: could not be read (unreadable, or over the size cap); "
                "invariants (iii) and (iv) were not checked"
            )
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _LINK_RE.finditer(line):
                target = match.group(1).split("#", 1)[0].strip()
                if not target or "://" in target or not target.endswith(".md"):
                    continue
                candidates = [spec_path.parent / target, root / target]
                if not any(_confined_file(candidate, root) is not None
                           for candidate in candidates):
                    warn.append(
                        f"{rel}:{lineno}: invariant (iii) — doc link '{target}' "
                        "does not resolve (warn-only)"
                    )
        for lineno, path in code_references(text):
            candidates = [spec_path.parent / path, root / path]
            if not any(_confined_file(candidate, root) is not None
                       for candidate in candidates):
                warn.append(
                    f"{rel}:{lineno}: invariant (iii) — code reference '{path}' "
                    "does not resolve (warn-only)"
                )
        # (iv) deferral anchors resolve. HARD, and repo-wide: see the docstring.
        for lineno, anchor in deferred_anchors(text):
            if anchor not in anchors:
                hard.append(
                    f"{rel}:{lineno}: invariant (iv) — (deferred: {anchor}) "
                    f"does not resolve in workspace.toml [backlog].open"
                )
    return hard, warn


# What the most recent `check` call gated. A module-level record rather than a
# third return value: `check`'s two-tuple is what every caller and test reads,
# and widening it to carry a reporting detail would churn all of them.
LAST_SCOPE: dict[str, object] = {
    "selected": 0,
    "available": 0,
    "mode": "all",
    "base_ref": None,
}


def check(
    root: Path, base_ref: str | None, all_specs: bool = False
) -> tuple[list[str], list[str]]:
    """Return hard violations and warnings for changed specs or the full sweep.

    Also records the per-spec selection in `LAST_SCOPE`, which `_describe_scope`
    reads to build the summary line. `main` must call them in that order.
    """
    hard: list[str] = []
    warn: list[str] = []

    workspace_path = _confined_file(root / "workspace.toml", root)
    anchors = backlog_open_slugs(workspace_path) if workspace_path is not None else set()

    base_resolvable = base_ref is not None
    if base_resolvable and not base_ref_resolves(root, base_ref):
        # Verified, not assumed. Falls into the same warn-and-skip path as a
        # missing ref rather than reporting every spec as new.
        warn.append(
            f"base ref {base_ref!r} does not resolve to a commit — "
            f"diff-triggered invariants (ii) and (vi) skipped"
        )
        base_resolvable = False
    if not base_resolvable:
        warn.append(
            "invariant (ii): no base ref resolvable — ship-transition AC check "
            "skipped (shallow clone / detached HEAD)"
        )
        warn.append(
            "invariant (vi): no base ref resolvable — Acceptance-Criteria "
            "section-presence check skipped (shallow clone / detached HEAD)"
        )

    specs_dir = root / "docs" / "specs"
    all_spec_paths = sorted(_confined(specs_dir.glob("*/spec.md"), root))
    spec_paths = all_spec_paths
    if not all_specs and base_resolvable:
        changed = changed_spec_paths(root, base_ref)  # type: ignore[arg-type]
        if changed is None:
            warn.append(
                f"base ref {base_ref!r} could not determine changed specs — "
                "running all per-spec invariants"
            )
        else:
            spec_paths = changed

    # Record what this run actually gated. Without it the scoped default prints
    # the same "spec metadata clean." as a full sweep, so a run that selected
    # zero specs is indistinguishable from one that checked all of them -- the
    # failure mode the scoped-run change exists alongside, not one to introduce.
    # `mode` records what actually happened, not what was asked for: an
    # unresolvable base or an undetermined changed set full-sweeps, and calling
    # that a "changed against <base>" run would name a comparison that did not
    # happen.
    swept = all_specs or spec_paths is all_spec_paths
    LAST_SCOPE.update(
        selected=len(spec_paths),
        available=len(all_spec_paths),
        mode="all" if swept else "changed",
        base_ref=None if swept else base_ref,
    )

    for spec_path in spec_paths:
        rel = spec_path.relative_to(root).as_posix()
        text = _read(spec_path)
        if text is None:
            # Never silent. `_read` returns None for an unreadable file or one
            # over the size cap, and skipping quietly reports that spec as
            # clean -- a vacuous pass over an entire file, which is the failure
            # mode every invariant here exists to prevent.
            warn.append(
                f"{rel}: could not be read (unreadable, or over the size cap); "
                f"no invariant was checked against it"
            )
            continue
        base_text = (
            base_spec_text(root, rel, base_ref)  # type: ignore[arg-type]
            if base_resolvable
            else None
        )
        base_text_undetermined = base_text is _BASE_TEXT_UNDETERMINED
        if base_text_undetermined:
            warn.append(
                f"{rel}: git show at base ref {base_ref!r} timed out — "
                "diff-triggered invariants (ii) and (vi) skipped"
            )

        # (i) status vocabulary
        token = parse_status(text)
        if token is None:
            hard.append(f"{rel}: no `- **Status:**` header field found")
        elif token not in CANONICAL_STATUSES:
            hard.append(
                f"{rel}: invariant (i) — status '{token}' not in "
                f"{{{', '.join(sorted(CANONICAL_STATUSES))}}}"
            )
        elif not status_uses_list_item_form(text):
            # This lint accepts a bare `**Status:**`, but the workspace-status
            # engine anchors on the `- **Status:**` list-item form and reads a
            # bare field as absent -- which surfaces later as an
            # `impossible_transition` against the entry's collection instead of
            # a lint error here. Warn-only: 18 specs predate the divergence.
            warn.append(
                f"{rel}: invariant (i) — `**Status:**` is not in the "
                f"`- **Status:**` list-item form the workspace engine reads "
                f"(warn-only)"
            )

        # (vi) diff-triggered Acceptance-Criteria section presence. Existing
        # sectionless specs are grandfathered, but any marker an author writes
        # remains subject to the marker-shape invariants.
        has_ac_section = acceptance_criteria_section_present(text)
        # A commented-out Acceptance-Criteria section is a hard error, not a
        # section. The body readers still read raw text, so without this the
        # heading would count and its criteria would be harvested -- (vi)
        # satisfied and (ii) checking text the author disabled.
        commented_ac = commented_out_ac_heading(text)
        if commented_ac is not None:
            _lineno, _line = commented_ac
            hard.append(
                f"{rel}:{_lineno}: invariant (vi) — an Acceptance-Criteria "
                f"section is commented out ({_line!r}); delete it. Criteria "
                f"that no longer apply are removed, not commented — git "
                f"history is where superseded ones live"
            )

        ac_heading_near_miss = None
        if not has_ac_section:
            # Warn rather than accept or ignore: an adopter whose spec reads
            # `## Acceptance criteria` is told the exact form instead of
            # silently losing its criteria to invariant (ii).
            _commented = _commented_line_numbers(text)
            for _lineno, _line in enumerate(text.splitlines(), start=1):
                if _lineno in _commented:
                    continue  # a commented heading is not a near miss
                if _AC_HEADING_NEAR_MISS_RE.match(_line):
                    ac_heading_near_miss = (_lineno, _line.strip())
                    warn.append(
                        f"{rel}:{_lineno}: Acceptance-Criteria heading should be "
                        f"exactly `## Acceptance Criteria` (found "
                        f"{_line.strip()!r}); its criteria are still checked, "
                        f"but the section does not satisfy invariant (vi)"
                    )
                    break
        ac_opt_out = acceptance_criteria_opt_out(text)
        ac_opt_out_near_miss = acceptance_criteria_opt_out_near_miss(text)
        if ac_opt_out_near_miss is not None:
            lineno, problem = ac_opt_out_near_miss
            hard.append(
                f"{rel}:{lineno}: invariant (vi) — malformed Acceptance "
                f"Criteria opt-out: {problem}"
            )
        if ac_opt_out is not None:
            lineno, reason = ac_opt_out
            if not reason or _PLACEHOLDER_REASON_RE.fullmatch(reason):
                hard.append(
                    f"{rel}:{lineno}: invariant (vi) — Acceptance Criteria "
                    "opt-out requires a non-placeholder one-line reason "
                    "after `none —`"
                )
            if has_ac_section:
                hard.append(
                    f"{rel}:{lineno}: invariant (vi) — spec has both an "
                    "Acceptance-Criteria section and an opt-out header"
                )
        if (
            not has_ac_section
            and ac_opt_out is None
            and ac_opt_out_near_miss is None
            and base_resolvable
            and not base_text_undetermined
            and (
                base_text is None
                or acceptance_criteria_section_present(base_text)
            )
        ):
            hard.append(
                f"{rel}:{ac_heading_near_miss[0]}: invariant (vi) — "
                f"Acceptance-Criteria heading must be exactly "
                f"`## Acceptance Criteria` (found {ac_heading_near_miss[1]!r}); "
                f"fix the heading — do NOT add a `none` opt-out to a spec that "
                f"has criteria"
                if ac_heading_near_miss is not None else
                f"{rel}: invariant (vi) — spec has no `## Acceptance Criteria` "
                "section and no `- **Acceptance Criteria:** none — <reason>` "
                "opt-out header"
            )

        # (ii) ACs at the ship transition (diff-triggered)
        if base_resolvable and not base_text_undetermined and token == "Shipped":
            base_token = parse_status(base_text) if base_text is not None else None
            transitioned = base_token != "Shipped"  # incl. new spec (None)
            if transitioned:
                for lineno, line in acceptance_criteria_lines(text):
                    if _AC_OPEN_RE.match(line):
                        hard.append(
                            f"{rel}:{lineno}: invariant (ii) — spec moved to "
                            f"Shipped but AC is unchecked"
                        )

        # (v) spec↔contract traceability (warn-only). Forward `Contract:` header
        # must point at an existing contract carrying a backward ref. No-ops when
        # the spec names no contract (non-API) or no `contracts/` tree exists.
        contract_refs = contract_header_refs(text)
        if contract_refs:
            feature_dir = spec_path.parent.relative_to(root).as_posix()
            registry_path = _confined_file(root / "contracts" / "REGISTRY.md", root)
            registry_text = _read(registry_path) if registry_path is not None else ""
            registry_text = registry_text or ""
            for lineno, token in contract_refs:
                contract_file = _confined_file(root / token, root)
                # Confinement precedes the existence probe: an unconfined
                # is_file() is itself an existence oracle for files outside root.
                if contract_file is None:
                    warn.append(
                        f"{rel}:{lineno}: invariant (v) — Contract: '{token}' does "
                        f"not resolve to a file (warn-only)"
                    )
                    continue
                backward = False
                if token.endswith(_XSPEC_FORMATS):
                    ctext = _read(contract_file) or ""
                    backward = "x-spec" in ctext and feature_dir in ctext
                if not backward:
                    backward = token in registry_text and feature_dir in registry_text
                if not backward:
                    warn.append(
                        f"{rel}:{lineno}: invariant (v) — contract '{token}' lacks a "
                        f"backward x-spec/REGISTRY.md ref to {feature_dir} (warn-only)"
                    )

    repo_hard, repo_warn = _repo_wide_findings(root, all_spec_paths, anchors)
    hard.extend(repo_hard)
    warn.extend(repo_warn)
    return hard, warn


def _describe_scope() -> str:
    """Describe the last run's per-spec coverage for the summary line.

    The repo-wide invariant (iii) pass always covers every spec; this describes
    only the per-spec coverage, which is what `--all` widens.
    """
    selected = LAST_SCOPE["selected"]
    available = LAST_SCOPE["available"]
    if LAST_SCOPE["mode"] == "all":
        return f"all {available} spec(s)"
    base = LAST_SCOPE["base_ref"] or "no resolvable base"
    return f"{selected} of {available} spec(s) changed against {base}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--base-ref", default=None)
    parser.add_argument(
        "--all", action="store_true",
        help="run per-spec checks for every current spec instead of changed specs",
    )
    args = parser.parse_args(argv)

    root = _validated_root(args.root)
    base_ref = args.base_ref if args.base_ref else resolve_default_base_ref(root)

    hard, warn = check(root, base_ref, all_specs=args.all)
    scope = _describe_scope()

    for w in warn:
        print(f"lint-spec-status: warning: {w}", file=sys.stderr)
    if hard:
        for v in hard:
            print(f"lint-spec-status: {v}", file=sys.stderr)
        print(
            f"lint-spec-status: {len(hard)} hard violation(s) ({scope}).",
            file=sys.stderr,
        )
        return 1
    print(f"lint-spec-status: spec metadata clean ({scope}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
