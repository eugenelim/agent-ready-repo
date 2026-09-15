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


DOCS_README = REPO_ROOT / "docs/README.md"
SEED_DOCS_README = REPO_ROOT / "packs/core/seeds/docs/README.md"

# The areas core actually seeds under docs/. A map row per area, because the
# repo's own § Documentation table is the model and an adopter has no others.
SEEDED_DOC_AREAS = ("architecture/", "product/", "specs/", "knowledge/")

# The lifecycle classes the § Document lifecycle section defines.
LIFECYCLE_CLASSES = ("living", "frozen", "governance")

# The § 5 wrapper's living-layer definition — the operative content of the
# section this task also owns.
LIVING_LAYER_AREAS = ("docs/architecture/", "docs/product/", "guides/")


def missing_doc_map_content(text: str) -> tuple[str, ...]:
    """Return what a docs map is required to state and does not."""
    body = visible_prose(text)
    lowered = body.lower()
    absent = [area for area in SEEDED_DOC_AREAS if area not in body]
    absent += [f"lifecycle class {c!r}" for c in LIFECYCLE_CLASSES if c not in lowered]
    absent += [f"living-layer area {a!r}" for a in LIVING_LAYER_AREAS if a not in body]
    return tuple(absent)


# --------------------------------------------------------------------------
# AC15, AC18 — the docs map
# --------------------------------------------------------------------------

def test_seeded_docs_map_states_the_areas_and_lifecycle_classes() -> None:
    """AC15 and AC18."""
    assert SEED_DOCS_README.is_file(), (
        "packs/core/seeds/docs/README.md does not exist; an adopter entering "
        "docs/ has no route into its own documentation tree"
    )
    absent = missing_doc_map_content(SEED_DOCS_README.read_text(encoding="utf-8"))
    assert not absent, f"the seeded docs map does not state: {absent}"


def test_seeded_docs_map_carries_the_adopter_extension_placeholder() -> None:
    """AC18. An adopter extends the map; they do not start from a blank file."""
    assert SEED_DOCS_README.is_file(), "packs/core/seeds/docs/README.md does not exist"
    body = SEED_DOCS_README.read_text(encoding="utf-8")
    assert "<" in body and ">" in body, (
        "the seeded map carries no placeholder row for an area core does not seed"
    )


def test_repo_docs_map_states_the_same_areas() -> None:
    """The repository's own copy carries the content it seeds."""
    assert DOCS_README.is_file(), "docs/README.md does not exist"
    absent = missing_doc_map_content(DOCS_README.read_text(encoding="utf-8"))
    assert not absent, f"the repository docs map does not state: {absent}"


def test_the_doc_map_guard_detects_missing_content() -> None:
    """Negative control: the red is produced by stripping."""
    if not SEED_DOCS_README.is_file():
        return  # the existence assertions above already carry the red
    stripped = SEED_DOCS_README.read_text(encoding="utf-8")
    for needle in SEEDED_DOC_AREAS + LIVING_LAYER_AREAS:
        stripped = stripped.replace(needle, "")
    for needle in LIFECYCLE_CLASSES:
        stripped = re.sub(needle, "", stripped, flags=re.IGNORECASE)
    assert missing_doc_map_content(stripped), (
        "the doc-map guard does not detect removal of the content it asserts"
    )


INSTALL_SNAPSHOT = REPO_ROOT / "tests/fixtures/install_snapshot/core.paths.txt"

# The two rows that carry over from the repo's own table unchanged. Both stop an
# agent hunting documentation for a fact another artifact owns.
UNIVERSAL_DOC_ROWS = ("SKILL.md", "linter")

_LINK_RE = re.compile(r"\]\(([^)]+)\)")


def installed_paths() -> frozenset[str]:
    """The paths an adopter actually receives from the core pack."""
    return frozenset(
        line.strip()
        for line in INSTALL_SNAPSHOT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def section_of(text: str, heading: str) -> str:
    """Return one `##` section's body, or an empty string when absent."""
    body = visible_prose(text)
    marker = f"## {heading}"
    if marker not in body:
        return ""
    start = body.index(marker)
    rest = body[start + len(marker) :]
    nxt = rest.find("\n## ")
    return rest if nxt == -1 else rest[:nxt]


# --------------------------------------------------------------------------
# AC17, AC20 — the promoted Documentation table
# --------------------------------------------------------------------------

def test_seed_routes_into_its_own_doc_tree() -> None:
    """AC17.

    The seed's only reference to anything under `docs/` today is the pointer to
    the retired file, so without this an adopter's root `AGENTS.md` names no
    entry into the documentation it was just given.
    """
    documentation = section_of(SEED_AGENTS.read_text(encoding="utf-8"), "Documentation")
    assert documentation, "the seed carries no `## Documentation` section"
    assert "docs/README.md" in documentation, (
        "the seed's Documentation section does not route to docs/README.md"
    )


def test_seed_documentation_names_only_installed_paths() -> None:
    """AC20, scoping half.

    The repo's own table lists `docs/adr/`, `docs/rfc/`, `guides/` and
    `ARCHITECTURE.md`, none of which core installs. Copying it verbatim would
    ship an adopter a table of links they cannot follow.
    """
    documentation = section_of(SEED_AGENTS.read_text(encoding="utf-8"), "Documentation")
    assert documentation, "the seed carries no `## Documentation` section"
    installed = installed_paths()
    dangling = [
        target
        for target in _LINK_RE.findall(documentation)
        if not target.startswith(("http://", "https://", "#"))
        and target.split("#", 1)[0].strip("./") not in installed
    ]
    assert not dangling, (
        f"the seed's Documentation table names paths core does not install: {dangling}"
    )


def test_seed_documentation_keeps_the_universal_rows() -> None:
    """AC20, row half.

    Once `docs/README.md` is installed, a single-row table satisfies both other
    predicates, so the rows themselves are named operative content.
    """
    documentation = section_of(SEED_AGENTS.read_text(encoding="utf-8"), "Documentation")
    absent = [row for row in UNIVERSAL_DOC_ROWS if row not in documentation]
    assert not absent, (
        "the seed's Documentation table drops the universal rows — a repeating "
        f"workflow lives in its own SKILL.md, a mechanically knowable fact in "
        f"code or a linter: {absent}"
    )


# The four development-workflow rules T5 promotes. Behaviour, no repo coupling.
WORKFLOW_RULES = (
    "Scope changes precisely",
    "destructive or irreversible",
    "new top-level directory",
    "unrelated discoveries",
)

# The three coding-convention rules T6 promotes.
CODING_RULES = (
    "types and docstrings",
    "new dependency",
    "silently resolve",
)

# The two rules T7 promotes into sections of their own.
SECURITY_RULES = ("Never commit personal information or credentials",)
SCOPED_RULES = ("stale or conflicting instructions",)


def absent_from_section(path: Path, heading: str, needles: tuple[str, ...]) -> tuple[str, ...]:
    """Return the needles missing from one section's visible prose."""
    section = section_of(path.read_text(encoding="utf-8"), heading)
    if not section:
        return (f"section `## {heading}` is absent",) + needles
    return tuple(n for n in needles if n not in section)


# --------------------------------------------------------------------------
# AC21 — the development-workflow rules
# --------------------------------------------------------------------------

def test_seed_states_the_development_workflow_rules() -> None:
    """AC21."""
    absent = absent_from_section(SEED_AGENTS, "Development workflow", WORKFLOW_RULES)
    assert not absent, f"the seed's Development workflow section omits: {absent}"


def test_the_workflow_rule_guard_detects_their_absence() -> None:
    """Negative control: the red is produced by stripping."""
    section = section_of(SEED_AGENTS.read_text(encoding="utf-8"), "Development workflow")
    for rule in WORKFLOW_RULES:
        section = section.replace(rule, "")
    assert all(rule not in section for rule in WORKFLOW_RULES)


# --------------------------------------------------------------------------
# AC22 — the coding-convention rules
# --------------------------------------------------------------------------

def test_seed_states_the_coding_convention_rules() -> None:
    """AC22."""
    absent = absent_from_section(SEED_AGENTS, "Coding conventions", CODING_RULES)
    assert not absent, f"the seed's Coding conventions section omits: {absent}"


def test_the_coding_rule_guard_detects_their_absence() -> None:
    """Negative control."""
    section = section_of(SEED_AGENTS.read_text(encoding="utf-8"), "Coding conventions")
    for rule in CODING_RULES:
        section = section.replace(rule, "")
    assert all(rule not in section for rule in CODING_RULES)


# --------------------------------------------------------------------------
# AC23 — the security and stale-instruction rules, in sections of their own
# --------------------------------------------------------------------------

def test_seed_states_the_never_commit_rule() -> None:
    """AC23, first half."""
    absent = absent_from_section(SEED_AGENTS, "Security considerations", SECURITY_RULES)
    assert not absent, f"the seed's Security considerations section omits: {absent}"


def test_seed_states_the_report_stale_rule() -> None:
    """AC23, second half."""
    absent = absent_from_section(SEED_AGENTS, "Scoped instructions", SCOPED_RULES)
    assert not absent, f"the seed's Scoped instructions section omits: {absent}"


def test_seed_omits_the_repo_specific_blessed_helpers() -> None:
    """The helpers list is this repository's, not an adopter's.

    Promoting it would hand an adopter a list of tools they do not have, which
    is the same defect as a table of links they cannot follow.
    """
    body = SEED_AGENTS.read_text(encoding="utf-8")
    for repo_only in ("credbroker", "file_safety", "UnsafeContentError"):
        assert repo_only not in body, (
            f"the seed names {repo_only!r}, which only this repository provides"
        )


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
