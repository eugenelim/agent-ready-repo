"""Guards for the conventions-retirement spec.

Every guard this spec adds lands here. The module deliberately invokes
``notes/ac2-scan.sh`` rather than restating its pathspecs: a second copy of the
exclusion predicate is how the guard and the criterion drift apart.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "docs/specs/conventions-retirement"
NOTES = SPEC_DIR / "notes"
SCAN = NOTES / "ac2-scan.sh"
ANCHOR_MAP = NOTES / "anchor-map.txt"
ANCHOR_INVENTORY = NOTES / "anchor-inventory.txt"

# AC2c canary. Pins the approved *form* of the scan predicate, not its
# pathspecs. A class-by-class check cannot see an exclusion added after it was
# written, and one added exclusion shrinks every task's discovery domain.
APPROVED_SCAN_DIGEST = "b6945c823706931546cda3a95f5c827f566d106a8c209d341d7e6f767757579e"

_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*$", re.MULTILINE)


def _slug(heading_text: str) -> str:
    """GitHub-style anchor slug for a Markdown heading."""
    lowered = heading_text.strip().lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered.replace("`", ""))
    return re.sub(r"\s+", "-", stripped).strip("-")


def anchors_in(path: Path) -> frozenset[str]:
    """Return every anchor slug a Markdown file exposes."""
    if not path.is_file():
        return frozenset()
    body = path.read_text(encoding="utf-8")
    return frozenset(_slug(m.group("text")) for m in _HEADING_RE.finditer(body))


def anchor_map() -> dict[str, dict[str, str]]:
    """Parse ``anchor-map.txt`` into ``{anchor: {destination, task, heading}}``.

    The heading column is absent until an owning task writes back the heading it
    chose against the real destination file. Until then the row cannot resolve,
    which is what makes the resolver red before the work lands.
    """
    rows: dict[str, dict[str, str]] = {}
    for line in ANCHOR_MAP.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#") or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        rows[parts[0]] = {
            "destination": parts[1],
            "task": parts[2],
            "heading": parts[3] if len(parts) > 3 else "",
        }
    return rows


def recorded_uses() -> tuple[tuple[str, str], ...]:
    """Return ``(consuming_file, anchor)`` for every use in the inventory."""
    uses: list[tuple[str, str]] = []
    for line in ANCHOR_INVENTORY.read_text(encoding="utf-8").splitlines():
        if ":" not in line or "CONVENTIONS.md#" not in line:
            continue
        consumer = line.split(":", 1)[0]
        anchor = "#" + line.split("CONVENTIONS.md#", 1)[1].strip()
        uses.append((consumer, anchor))
    return tuple(uses)


def unresolved_uses() -> tuple[str, ...]:
    """Return a diagnostic line per recorded use that does not resolve.

    A use resolves when its anchor maps to a destination, that destination names
    a concrete Markdown file, the row records the heading the content landed
    under, and that heading exists in the file.
    """
    mapping = anchor_map()
    failures: list[str] = []
    for consumer, anchor in recorded_uses():
        row = mapping.get(anchor)
        if row is None:
            failures.append(f"{consumer} -> {anchor}: no anchor-map row")
            continue
        destination = row["destination"]
        heading = row["heading"]
        if not heading:
            failures.append(
                f"{consumer} -> {anchor}: row records no destination heading "
                f"(destination {destination!r})"
            )
            continue
        target = REPO_ROOT / destination
        if not target.is_file():
            failures.append(
                f"{consumer} -> {anchor}: destination {destination!r} is not a file"
            )
            continue
        if _slug(heading) not in anchors_in(target):
            failures.append(
                f"{consumer} -> {anchor}: heading {heading!r} absent from {destination}"
            )
    return tuple(failures)


def run_scan(pattern: str | None = None) -> tuple[str, ...]:
    """Invoke the recorded scan predicate and return the paths it reports."""
    argv = ["sh", str(SCAN)] + ([pattern] if pattern else [])
    completed = subprocess.run(
        argv, cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
SEED_AGENTS = REPO_ROOT / "packs/core/seeds/AGENTS.md"

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_RE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)


def visible_prose(text: str) -> str:
    """Strip HTML comments and fenced blocks before matching.

    A token parked in a comment, a fence, a heading or a link title satisfies a
    naive substring check while governing nothing.
    """
    return _FENCE_RE.sub("", _COMMENT_RE.sub("", text))


# The three session-priming rules T2 seats in both AGENTS.md files, each named by
# a token distinctive enough that a paraphrase does not accidentally satisfy it.
PRIMING_TOKENS = (
    "Conventional Commits",
    "`feat`",
    "what did you not change that you",
    "Never commit personal information or credentials",
    "generic placeholders",
)


def missing_priming_rules(text: str) -> tuple[str, ...]:
    """Return the priming tokens absent from a file's visible prose."""
    body = visible_prose(text)
    return tuple(token for token in PRIMING_TOKENS if token not in body)


# --------------------------------------------------------------------------
# AC4, AC5 — the session-priming rules, with a negative control
# --------------------------------------------------------------------------

def test_both_agents_files_state_the_priming_rules() -> None:
    """AC4 and AC5."""
    for path in (ROOT_AGENTS, SEED_AGENTS):
        absent = missing_priming_rules(path.read_text(encoding="utf-8"))
        assert not absent, f"{path.relative_to(REPO_ROOT)} is missing: {absent}"


def test_the_priming_guard_detects_their_absence() -> None:
    """Negative control: the red is produced by stripping, not by timing.

    A destination is usually the topic's natural owner and may already state a
    rule, so requiring the assertion to have been red before the edit is not a
    usable proof. Stripping the content and watching the same predicate fail is.
    """
    stripped = SEED_AGENTS.read_text(encoding="utf-8")
    for token in PRIMING_TOKENS:
        stripped = stripped.replace(token, "")
    absent = missing_priming_rules(stripped)
    assert set(absent) == set(PRIMING_TOKENS), (
        "the priming guard does not detect removal of the rules it asserts; "
        f"it reported only {absent}"
    )


def test_the_priming_guard_ignores_commented_out_content() -> None:
    """A token in an HTML comment or a fenced block governs nothing."""
    faked = "<!--\n" + "\n".join(PRIMING_TOKENS) + "\n-->\n"
    assert set(missing_priming_rules(faked)) == set(PRIMING_TOKENS)


# --------------------------------------------------------------------------
# AC2c — the canary
# --------------------------------------------------------------------------

def test_scan_predicate_matches_its_approved_form() -> None:
    """A widened pathspec shrinks every task's discovery domain silently."""
    live = hashlib.sha256(SCAN.read_bytes()).hexdigest()
    assert live == APPROVED_SCAN_DIGEST, (
        "notes/ac2-scan.sh differs from its approved form. If the change is "
        "intended, update APPROVED_SCAN_DIGEST in the same commit and say why; "
        f"live digest is {live}"
    )


def test_guard_invokes_the_scan_rather_than_restating_it() -> None:
    """Two copies of the exclusion predicate drift apart."""
    body = Path(__file__).read_text(encoding="utf-8")
    # Built rather than written literally: a guard that searches its own source
    # for a needle cannot contain that needle, or it always finds itself.
    pathspec_marker = ":(" + "glob,exclude" + ")"
    assert pathspec_marker not in body, (
        "this module restates the scan's pathspecs; invoke notes/ac2-scan.sh instead"
    )
    assert "ac2-scan.sh" in body


def test_scan_admits_an_in_domain_tree() -> None:
    """Positive control on the predicate's reach.

    Deliberately not anchored on the retirement's own pattern: the retired path
    leaves every file as the work lands, and by the deletion task the default
    scan returns nothing by design. A witness on that pattern would therefore
    report a swallowed domain the moment the work succeeded. `MAX_SEED_LINES`
    lives in `tools/`, which no exclusion covers and this change does not move.
    """
    assert "tools/lint-agents-md.py" in run_scan("MAX_SEED_LINES"), (
        "the scan no longer reaches tools/; its exclusions have widened"
    )


def test_scan_excludes_the_historical_record_trees() -> None:
    """Negative control, one witness per excluded class.

    `## Decision` occurs inside `docs/adr/`, so a scan that reaches it would
    report those files. Their absence is the exclusion working rather than the
    pattern simply missing.
    """
    reported = run_scan("## Decision")
    assert reported, "the witness pattern matches nothing; the control is vacuous"
    for excluded in ("docs/adr/", "docs/rfc/", "docs/knowledge/observations/"):
        leaked = [p for p in reported if p.startswith(excluded)]
        assert not leaked, f"historical records leaked into the domain: {leaked}"


# --------------------------------------------------------------------------
# AC6 — the anchor resolver, with its positive control
# --------------------------------------------------------------------------

def test_resolver_accepts_a_heading_that_exists() -> None:
    """Positive control.

    Without it, a resolver red because it crashes is indistinguishable from one
    red because the work is undone.
    """
    assert "documentation" in anchors_in(REPO_ROOT / "AGENTS.md")
    assert _slug("## Rule lookups") == "rule-lookups"


def test_every_recorded_anchor_use_resolves() -> None:
    """AC6. Ranges over the recorded pre-relocation uses.

    The live set empties as the work lands, so a criterion over it could not
    fail once the retirement completed.
    """
    failures = unresolved_uses()
    assert not failures, "unresolved anchor uses:\n" + "\n".join(failures)
