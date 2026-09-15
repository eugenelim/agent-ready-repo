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


def test_scan_reports_in_domain_and_excludes_historical_records() -> None:
    """Positive and negative control on the predicate itself."""
    reported = run_scan()
    assert any(p == "AGENTS.md" for p in reported), (
        "the scan reports no in-domain path; its exclusions have swallowed the domain"
    )
    for excluded in ("docs/knowledge/observations/", "docs/adr/", "docs/rfc/"):
        assert not any(p.startswith(excluded) for p in reported), (
            f"historical records under {excluded} leaked into the scan domain"
        )


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
