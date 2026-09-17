"""Guards for the conventions-retirement spec.

Every guard this spec adds lands here. The module deliberately invokes
``notes/ac2-scan.sh`` rather than restating its pathspecs: a second copy of the
exclusion predicate is how the guard and the criterion drift apart.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "docs/specs/conventions-retirement"
NOTES = SPEC_DIR / "notes"
SCAN = NOTES / "ac2-scan.sh"

# Assembled, never written literally: this module is inside the scan's domain, so
# a literal here would make the guard report itself and never pass. Same reason
# the pathspec needle below is built at runtime.
RETIRED_TOKEN = "CONVEN" + "TIONS"
ANCHOR_MAP = NOTES / "anchor-map.txt"
ANCHOR_INVENTORY = NOTES / "anchor-inventory.txt"

# AC2c canary. Pins the approved *form* of the scan predicate, not its
# pathspecs. A class-by-class check cannot see an exclusion added after it was
# written, and one added exclusion shrinks every task's discovery domain.
APPROVED_SCAN_DIGEST = "a8ec4080227bab0b8caa78cb46f1cba91cd1bae4a832f115e827840020723794"

_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*$", re.MULTILINE)

# Inert spans: text no reader follows, and so text no assertion in this module
# should read. Three constructs qualify — a fenced block, an HTML comment, and
# an inline code span — and they are found by one left-to-right scan rather
# than by three regexes run in sequence.
#
# The scan exists because the sequential version was wrong three times, each
# time in a way a passing suite did not show. Masking inline code first blanked
# bare ``` fence delimiters, because a delimiter line reads as an empty code
# span, so the fence pattern lost its opener. Masking fences first let a fence
# marker *inside* a comment consume that comment's `-->`, leaving the comment
# pass to swallow the file. And a fixed three-character delimiter closed a
# four-backtick fence on the first inner three-backtick line — live in this
# repository at `guides/_shared/how-to/author-a-skill.md`, where a ````markdown
# fence wraps ```bash examples.
#
# One pass has no ordering to get wrong: whichever construct opens first at the
# current position wins, and the scan resumes after it closes. A construct left
# unterminated runs to end of file, which is what a renderer does with it.
_FENCE_OPEN_RE = re.compile(r"^(?P<indent> {0,3})(?P<delim>`{3,}|~{3,})[^\n]*$")

_BLOCK, _CODE = "block", "code"


def _fence_close(text: str, search_from: int, delim: str, run: int) -> int:
    """Offset just past the line that closes this fence, or end of text.

    CommonMark closes a fence with the same character, at least as long as the
    opener, alone on its line. "At least as long" is what keeps a ````
    fence open across the ``` lines it is quoting.
    """
    closer = re.compile(rf"^ {{0,3}}{re.escape(delim)}{{{run},}}\s*$")
    position = search_from
    while position < len(text):
        line_end = text.find("\n", position)
        line_end = len(text) if line_end == -1 else line_end
        if closer.match(text[position:line_end]):
            return min(line_end + 1, len(text))
        position = line_end + 1
    return len(text)


def _inert_spans(text: str) -> list[tuple[int, int, str]]:
    """Return `(start, end, kind)` for every inert span, in document order."""
    spans: list[tuple[int, int, str]] = []
    position, length = 0, len(text)
    at_line_start = True
    while position < length:
        if at_line_start:
            line_end = text.find("\n", position)
            line_end = length if line_end == -1 else line_end
            opener = _FENCE_OPEN_RE.match(text[position:line_end])
            if opener is not None:
                delim = opener.group("delim")
                close = _fence_close(
                    text, min(line_end + 1, length), delim[0], len(delim)
                )
                spans.append((position, close, _BLOCK))
                position, at_line_start = close, True
                continue
        if text.startswith("<!--", position):
            close = text.find("-->", position + 4)
            close = length if close == -1 else close + 3
            spans.append((position, close, _BLOCK))
            position, at_line_start = close, False
            continue
        if text[position] == "`":
            run = len(text) - len(text.lstrip("`")) if False else 0
            run = 0
            while position + run < length and text[position + run] == "`":
                run += 1
            closer = re.compile(rf"(?<!`){'`' * run}(?!`)")
            found = closer.search(text, position + run)
            if found is not None:
                spans.append((position, found.end(), _CODE))
                position, at_line_start = found.end(), False
                continue
        at_line_start = text[position] == "\n"
        position += 1
    return spans


def _blank(text: str, kinds: tuple[str, ...]) -> str:
    """Blank the named span kinds, preserving every offset and newline."""
    masked = list(text)
    for begin, finish, kind in _inert_spans(text):
        if kind not in kinds:
            continue
        for i in range(begin, finish):
            if masked[i] != "\n":
                masked[i] = " "
    return "".join(masked)


def _inert_masked(text: str) -> str:
    """Blank every inert span. Offsets are preserved, so a match here indexes
    the original text unchanged."""
    return _blank(text, (_BLOCK, _CODE))


def _mask_inert(text: str) -> str:
    """Alias for the section and link readers, which want full masking."""
    return _inert_masked(text)


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
    # Headings are *located* on masked text, because one inside a comment or a
    # fenced example exposes no anchor a link can reach. Each is then slugged
    # from the original line: a heading like `## Use \`foo\`` anchors as
    # `use-foo`, and slugging the masked line drops the blanked code span —
    # and trailing blanks fall to `\s*$` — leaving `use`, which nothing links to.
    masked_lines = _mask_inert(body).splitlines()
    return frozenset(
        _slug(raw_line[m.start("text"):])
        for raw_line, masked_line in zip(body.splitlines(), masked_lines, strict=True)
        if (m := _HEADING_RE.match(masked_line)) is not None
    )


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


# AC6 names this figure, so it is part of the criterion rather than an
# incidental property of the file. Without it a dropped or corrupted inventory
# row leaves the guard green while its replacement link disappears: the domain
# would shrink to fit whatever survived.
RECORDED_USE_COUNT = 30

_INVENTORY_ROW_RE = re.compile(
    r"^(?P<consumer>[^:]+):(?P<line>\d+):" + RETIRED_TOKEN + r"\.md(?P<anchor>#\S+)$"
)


def recorded_uses() -> tuple[tuple[str, str], ...]:
    """Return ``(consuming_file, anchor)`` for every use in the inventory.

    Parsed strictly. A row that does not match is an error, not a row to skip,
    because silently skipping is how the criterion's domain shrinks.
    """
    uses: list[tuple[str, str]] = []
    malformed: list[str] = []
    for number, line in enumerate(
        ANCHOR_INVENTORY.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        row = _INVENTORY_ROW_RE.match(line)
        if row is None:
            malformed.append(f"{ANCHOR_INVENTORY.name}:{number}: {line!r}")
            continue
        uses.append((row.group("consumer"), row.group("anchor")))
    assert not malformed, "unparseable anchor-inventory row(s):\n  " + "\n  ".join(
        malformed
    )
    assert len(uses) == RECORDED_USE_COUNT, (
        f"the inventory records {len(uses)} uses; AC6 names "
        f"{RECORDED_USE_COUNT}. A row was added or dropped, which moves the "
        f"criterion's domain."
    )
    return tuple(uses)


def unresolved_uses() -> tuple[str, ...]:
    """Return a diagnostic line per recorded use that does not resolve.

    A use resolves when its anchor maps to a destination, that destination names
    a concrete Markdown file, the row records the heading the content landed
    under, and that heading exists in the file.
    """
    mapping = anchor_map()
    # One inventory line is one use, so a consumer citing an anchor twice owes
    # two replacements. Iterate the distinct pairs and carry the count.
    use_counts = Counter(recorded_uses())
    failures: list[str] = []
    for consumer, anchor in use_counts:
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
            continue
        failures.extend(
            _replacement_failures(
                consumer, anchor, destination, heading, use_counts[(consumer, anchor)]
            )
        )
    return tuple(failures)


# The label is matched so the lookbehind can sit before the opening bracket,
# which is where an image's `!` and an escaped bracket's backslash live. Testing
# a guard placed before the closing bracket instead let `![alt](dest)` through:
# the character before `]` there is ordinary label text.
_LINK_TARGET_RE = re.compile(r"(?<![!\\])\[[^\]]*\]\(([^)\s]+)")

# A seed page's relative links resolve inside the scaffold it becomes, not inside
# this repository, so a seed twin pointing at its own twin is correct.
SEED_ROOTS = ("packs/core/seeds/",)

# A use whose replacement cannot be a resolvable in-tree link to the mapped
# destination. Each disposition is owner-confirmed in the spec's Assumptions and
# records what to assert instead, because only a human can say what a
# non-Markdown reader — or a scaffold that never installs `packs/` — resolves.
#   `deleted` — the guidance is not adopter-facing, so the note is removed.
#   `literal` — the pointer is adapter-relative, so its exact spelling is pinned.
#   `local`   — the content landed in the citing file, which now cites a heading
#               of its own instead of linking out.
RECORDED_DISPOSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("packs/core/seeds/docs/architecture/README.md", "#pack-source-of-truth-split"): (
        "deleted",
        "an adopter scaffold installs no `packs/`, so the note is deleted",
    ),
    ("packs/core/seeds/docs/specs/README.md", "#4-specs-and-plans--docsspecsfeature"): (
        "local",
        "Spec and plan",
    ),
    (
        "packages/agentbundle/agentbundle/catalogue_tooling/verify.py",
        "#model-selection",
    ): (
        "literal",
        "the work-loop skill's references/model-selection.md",
    ),
    ("tools/lint-agents-md.py", "#supervisor-mode"): (
        "literal",
        "work-loop/references/supervisor-mode.md",
    ),
    ("tools/test-lint-agents-md-gitignore-probes.py", "#supervisor-mode"): (
        "literal",
        "work-loop/references/supervisor-mode.md",
    ),
}


def _matching_link_count(
    source: Path, consumer: str, destination: str, heading: str
) -> int:
    """Count the consumer's links that reach the mapped destination *heading*.

    Three things this proves that a path comparison does not.

    The fragment is load-bearing: comparing paths alone passes whenever the
    consumer happens to hold any bare link to the destination file, and several
    consumers do, so the fragment-bearing replacement could be deleted outright
    and the check would stay green. The fragment is compared exactly rather
    than through `_slug`, because slugging the fragment normalises punctuation
    away and `#the-source-of-truth-split!` would compare equal to a heading it
    does not address.

    The heading is verified in whichever target the link actually reached. A
    seed page may reach the destination's seed twin — its links resolve inside
    the scaffold it becomes, where no `packs/` prefix exists — and the twin is
    a different file, so proving the heading in the repository copy says
    nothing about the adopter's link.

    Comments and fences are removed first, for the reason `visible_prose`
    gives: a link parked in either governs nothing a reader can follow.

    Returns a count rather than a boolean so a consumer citing one anchor
    twice must carry two replacements. The inventory is one line per use.
    """
    seed_root = next((r for r in SEED_ROOTS if consumer.startswith(r)), None)
    if seed_root is None:
        candidates = [REPO_ROOT / destination]
    else:
        # The twin is the only candidate. Accepting the repository copy as well
        # let a seed link spelled with enough `..` to escape the installed tree
        # count, because those segments still reach a real file in this
        # repository — a namespace the adopter never has.
        candidates = [REPO_ROOT / seed_root / destination]
    wanted = _slug(heading)
    targets = {
        path.resolve()
        for path in candidates
        if path.is_file() and wanted in anchors_in(path)
    }
    if not targets:
        return 0
    body = _inert_masked(source.read_text(encoding="utf-8"))
    hits = 0
    for raw in _LINK_TARGET_RE.findall(body):
        path_part, _, fragment = raw.partition("#")
        if not path_part or fragment != wanted:
            continue
        if (source.parent / path_part).resolve() in targets:
            hits += 1
    return hits


def _replacement_failures(
    consumer: str, anchor: str, destination: str, heading: str, required: int
) -> tuple[str, ...]:
    """Return a diagnostic when the consumer holds no working replacement.

    The mapped destination existing proves the content landed; it does not prove
    the consumer was re-pointed at it. Round 9 found a diagnostic re-pointed at a
    path that exists in no tree while AC6 stayed green, because the resolver read
    only the destination and never opened the consumer.
    """
    source = REPO_ROOT / consumer
    if not source.is_file():
        return (f"{consumer} -> {anchor}: recorded consumer is missing",)
    if consumer == destination:
        # The content landed in the citing file, so the heading check above is
        # already the proof: there is nothing left to link to.
        return ()
    text = source.read_text(encoding="utf-8")
    disposition = RECORDED_DISPOSITIONS.get((consumer, anchor))
    if disposition is not None:
        kind, value = disposition
        if kind == "deleted":
            if RETIRED_TOKEN in text:
                return (
                    f"{consumer} -> {anchor}: recorded as deleted ({value}) but the "
                    f"retired document is still named here",
                )
            return ()
        if kind == "local":
            if _slug(value) not in anchors_in(source):
                return (
                    f"{consumer} -> {anchor}: content was recorded as landing here "
                    f"under heading {value!r}, which this file does not expose",
                )
            return ()
        if value not in text:
            return (
                f"{consumer} -> {anchor}: pinned replacement {value!r} is absent; "
                f"the pointer must resolve for a reader of an installed tree",
            )
        return ()
    found = _matching_link_count(source, consumer, destination, heading)
    if found >= required:
        return ()
    return (
        f"{consumer} -> {anchor}: the inventory records {required} use(s) but "
        f"only {found} link(s) here resolve to {destination}#{_slug(heading)}; "
        f"each recorded use needs its own replacement pointer (or a recorded "
        f"disposition)",
    )


CHANGELOG = REPO_ROOT / "docs/product/changelog.md"


def test_the_changelog_header_names_no_retired_document() -> None:
    """The living half of a file whose entries are historical.

    `docs/product/changelog.md` is excluded from the AC2 scan because its dated
    entries name the retired document and stay untouched. Its maintenance header
    is not an entry: it is live guidance, and the exclusion cannot tell the two
    apart because a pathspec is file-granular. Round 9 found a dangling pointer
    there. Blind spot, named: this checks only the text above the first `##`
    heading, so a live pointer introduced lower in the file is not detected.
    """
    body = CHANGELOG.read_text(encoding="utf-8")
    header = body.split("\n## ", 1)[0]
    assert RETIRED_TOKEN not in header, (
        "the changelog's maintenance header names the retired document; it is "
        "live guidance, not a dated entry, so it is repaired normally"
    )


def run_scan(pattern: str | None = None) -> tuple[str, ...]:
    """Invoke the recorded scan predicate and return the paths it reports."""
    argv = ["sh", str(SCAN)] + ([pattern] if pattern else [])
    completed = subprocess.run(
        argv, cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
SEED_AGENTS = REPO_ROOT / "packs/core/seeds/AGENTS.md"


def visible_prose(text: str) -> str:
    """Strip HTML comments and fenced blocks, then normalise whitespace.

    A token parked in a comment, a fence, a heading or a link title satisfies a
    naive substring check while governing nothing — hence the stripping.

    Whitespace is collapsed because a needle spanning two words fails whenever
    the prose happens to wrap between them, which makes the guard report a
    missing rule that is present. Found in T19: the Finish-checklist obligation
    wrapped between "not done" and "until those are updated".
    """
    # Only the block spans are cut. A backticked token is ordinary content
    # here — several assertions name one — so inline code stays, while the
    # single scan still prevents a quoted `<!--` from opening a comment.
    keep, cursor = [], 0
    spans = [(b, e) for b, e, kind in _inert_spans(text) if kind == _BLOCK]
    for start, end in spans:
        if start >= cursor:
            keep.append(text[cursor:start])
            cursor = end
    keep.append(text[cursor:])
    return " ".join("".join(keep).split())


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
    """Return one `##` section's body, or an empty string when absent.

    The boundary is found on text that keeps its line breaks, because
    `visible_prose` collapses newlines and a newline-anchored `## ` needle can
    never match once it has. Round 9 found every window running to end of file,
    which made the placement half of each "rule X sits under § Y" criterion
    unenforceable.

    The heading match is anchored to a whole line, so `## Documentation extras`
    does not answer a lookup for `Documentation`, and it runs on masked text,
    so a heading commented out or shown inside a fenced example does not
    either. Both were live weaknesses: the first let a rename keep the
    assertion green, the second let a section no reader renders satisfy it.
    """
    masked = _mask_inert(text)
    marker = re.compile(rf"^## {re.escape(heading)}$", re.MULTILINE)
    found = marker.search(masked)
    if found is None:
        return ""
    # Both boundaries come from the masked string. Finding the start there and
    # the end in the raw text let a commented-out `## Fake` truncate the
    # section, so content after it — a dangling link included — was never read.
    nxt = masked.find("\n## ", found.end())
    end = len(text) if nxt == -1 else nxt
    return visible_prose(text[found.end():end])


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


PROMOTED_SECTIONS = ("Documentation", "Security considerations", "Scoped instructions")


def optional_guidance_comment() -> str:
    """The seed's trailing recommended-additional-guidance comment."""
    body = SEED_AGENTS.read_text(encoding="utf-8")
    marker = "Recommended additional guidance"
    if marker not in body:
        return ""
    start = body.rindex("<!--", 0, body.index(marker))
    return body[start : body.index("-->", start) + 3]


# --------------------------------------------------------------------------
# AC24 — the optional-guidance comment stops offering what the seed now has
# --------------------------------------------------------------------------

def test_comment_no_longer_offers_the_promoted_sections() -> None:
    """AC24.

    Each promoted section stops being an offered option in the task that makes
    it real. Leaving the offer would invite an adopter to add what they have.
    """
    comment = optional_guidance_comment()
    assert comment, "the seed's optional-guidance comment is absent entirely"
    still_offered = [s for s in PROMOTED_SECTIONS if f"`{s}`" in comment]
    assert not still_offered, (
        f"the comment still offers sections the seed already carries: {still_offered}"
    )


def test_comment_still_offers_what_the_seed_lacks() -> None:
    """AC24, the other direction.

    Deleting the comment outright would satisfy the assertion above while
    removing guidance an adopter still needs, so the surviving offer is asserted
    too.
    """
    comment = optional_guidance_comment()
    assert "`Repository structure`" in comment, (
        "the comment no longer offers Repository structure, which the seed does "
        "not carry — the comment was trimmed too far, or deleted"
    )
    assert "trigger" in comment.lower() and "benefit" in comment.lower(), (
        "the surviving offer lost its trigger-and-benefit shape"
    )


def test_seed_is_within_its_cap_with_every_promotion_present() -> None:
    """The headroom condition, checked where the accumulated content exists.

    At T1 the content T2-T8 add did not exist, so any cap above the file's
    length passed and the rest was the implementer's estimate.
    """
    import subprocess

    completed = subprocess.run(
        ["python3", "tools/lint-agents-md.py"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert completed.returncode == 0, (
        "the AGENTS.md linter fails with every promotion present:\n"
        + completed.stdout[-1500:]
    )


ARCH_README = REPO_ROOT / "docs/architecture/README.md"
SEED_ARCH_README = REPO_ROOT / "packs/core/seeds/docs/architecture/README.md"

# § 5a's operative content. Round 8 found T9's original test guarded the
# `reference.md` seating, which belongs to § Document hierarchy and so to T3.
ARCH_RULES = ("STATUS: PLANNED", "Last verified against commit", "current state")


def test_architecture_readme_states_the_current_state_rules() -> None:
    """§ 5a's own operative content, in both copies."""
    for path in (ARCH_README, SEED_ARCH_README):
        body = visible_prose(path.read_text(encoding="utf-8"))
        absent = [r for r in ARCH_RULES if r not in body]
        assert not absent, f"{path.relative_to(REPO_ROOT)} omits: {absent}"


PRODUCT_README = REPO_ROOT / "docs/product/README.md"
SEED_PRODUCT_README = REPO_ROOT / "packs/core/seeds/docs/product/README.md"

# § 5b's ownership list. Round 8 found the living-docs rule this section also
# carries is already in the seed, so the assertion names content the seed lacks.
PRODUCT_AREAS = (
    "roadmap",
    "changelog",
    "intents",
    "briefs",
    "shaping",
    "findings",
    "initiatives",
    "research",
)


def test_product_readme_states_the_area_ownership() -> None:
    """§ 5b's operative content, in both copies."""
    for path in (PRODUCT_README, SEED_PRODUCT_README):
        body = visible_prose(path.read_text(encoding="utf-8")).lower()
        absent = [a for a in PRODUCT_AREAS if a not in body]
        assert not absent, f"{path.relative_to(REPO_ROOT)} omits: {absent}"


def test_product_readme_states_the_changelog_heading_rule() -> None:
    """The load-bearing half: a released section is never nested."""
    for path in (PRODUCT_README, SEED_PRODUCT_README):
        body = visible_prose(path.read_text(encoding="utf-8"))
        assert "Unreleased" in body, (
            f"{path.relative_to(REPO_ROOT)} omits the changelog heading rule"
        )


PACK_LAYOUT = REPO_ROOT / "docs/architecture/pack-layout.md"

# § Pack source-of-truth split's operative content: the Projected-versus-Manual
# classification, and the edit-the-upstream-then-regenerate rule.
PACK_LAYOUT_RULES = ("Projected", "Manual", "make build-self", "EXCLUDED_PATTERNS")


def test_pack_layout_states_the_source_of_truth_split() -> None:
    """§ Pack source-of-truth split's operative content."""
    body = visible_prose(PACK_LAYOUT.read_text(encoding="utf-8"))
    absent = [r for r in PACK_LAYOUT_RULES if r not in body]
    assert not absent, f"docs/architecture/pack-layout.md omits: {absent}"


NEW_ADR_GUIDE = REPO_ROOT / "guides/governance-extras/how-to/new-adr.md"
NEW_RFC_GUIDE = REPO_ROOT / "guides/governance-extras/how-to/new-rfc.md"
SEED_CHARTER = REPO_ROOT / "packs/core/seeds/docs/CHARTER.md"

RFC_LIFECYCLE_STATES = ("Draft", "Open", "Final Comment Period", "Accepted", "Withdrawn")


def test_adr_guide_states_what_an_adr_records() -> None:
    body = visible_prose(NEW_ADR_GUIDE.read_text(encoding="utf-8"))
    for needle in ("immutable", "supersed"):
        assert needle in body.lower(), f"the ADR guide omits {needle!r}"


def test_rfc_guide_states_the_lifecycle_the_skill_cites() -> None:
    """`rfc-status` cited § 3 for the valid states; the guide now owns them."""
    body = visible_prose(NEW_RFC_GUIDE.read_text(encoding="utf-8"))
    absent = [s for s in RFC_LIFECYCLE_STATES if s not in body]
    assert not absent, f"the RFC guide omits lifecycle states: {absent}"


def test_seeded_charter_states_its_revision_rule() -> None:
    """The reserved-versus-normal distinction, which the seed lacked."""
    body = visible_prose(SEED_CHARTER.read_text(encoding="utf-8"))
    assert "typo" in body.lower() and "broken link" in body.lower(), (
        "the seeded charter omits the revision rule's normal-change list, so an "
        "adopter cannot tell a reserved change from a wording fix"
    )


SPEC_CONTRACT_REF = REPO_ROOT / "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md"
SEED_SPECS_README = REPO_ROOT / "packs/core/seeds/docs/specs/README.md"

# § 4's four subsections. A prose move can silently drop one, so each is named.
SPEC_CONTRACT_RULES = (
    "Spec metadata contract",
    "Low-level design lives in the plan",
    "construction tests",
    "contracts/<type>/",
    # Round 9 found § Spec metadata contract pointing at this subsection while no
    # live artifact carried it. These four tokens are its operative rules, not
    # its title, so the assertion cannot pass on a heading alone.
    "Superseding a frozen document",
    "superseded in part by ADR-NNNN",
    "meaning-preserving mechanical rewrites are allowed",
    "not a supersession",
)


def test_spec_contract_reference_carries_all_four_subsections() -> None:
    body = visible_prose(SPEC_CONTRACT_REF.read_text(encoding="utf-8"))
    absent = [r for r in SPEC_CONTRACT_RULES if r not in body]
    assert not absent, f"the spec-and-plan contract reference omits: {absent}"


def test_seeded_specs_readme_states_the_distinction_and_vocabulary() -> None:
    """The adopter half. A seed cannot link to an adapter-specific skill path."""
    body = visible_prose(SEED_SPECS_README.read_text(encoding="utf-8"))
    for needle in ("Implementing", "Shipped", "Executing", "lifecycle index"):
        assert needle in body, f"the seeded specs README omits {needle!r}"


RELOCATED_OWNERS = {
    "packs/core/.apm/skills/work-intake/references/lifecycle-index.md":
        ("path", "kind", "source", "summary", "needs"),
    "guides/_shared/explanation/documentation-contracts.md":
        ("tutorial", "how-to", "reference", "explanation"),
    "packs/core/.apm/skills/work-loop/references/knowledge-base.md":
        ("pattern", "gotcha", "antipattern", "show-knowledge"),
    "packs/core/.apm/skills/work-loop/SKILL.md":
        ("not done until those are updated",),
    "CONTRIBUTING.md": ("Profile A", "Profile B", "Profile C"),
    "guides/_shared/how-to/author-a-skill.md": ("three times", "speculatively"),
}


def test_relocated_sections_landed_with_their_operative_content() -> None:
    """One assertion per destination, naming what each section actually carries."""
    for rel, needles in RELOCATED_OWNERS.items():
        path = REPO_ROOT / rel
        assert path.is_file(), f"{rel} does not exist"
        body = visible_prose(path.read_text(encoding="utf-8")).lower()
        absent = [n for n in needles if n.lower() not in body]
        assert not absent, f"{rel} omits: {absent}"


CHANGELOG = REPO_ROOT / "docs/product/changelog.md"
PACK_TOML = REPO_ROOT / "packs/core/pack.toml"
PLUGIN_JSON = REPO_ROOT / "packs/core/.claude-plugin/plugin.json"

# AC12 names one version, so the control asserts that value rather than an
# ordering. Round 9 found a `greater than the predecessor` comparison accepted
# both a patch and a major bump, which is the whole substance of the decision
# to take a minor. Pinning the target also survives the baseline moving: core
# released several patches on `main` while this change was in flight, and an
# ordering expressed against a predecessor would have silently re-based on
# each one.
RELEASE_VERSION = "2.27.0"

_CORE_HEADING_RE = re.compile(r"^## \[core\]\[(?P<version>[^\]]+)\] — ", re.MULTILINE)


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


# --------------------------------------------------------------------------
# AC11, AC12 — the release
# --------------------------------------------------------------------------

def test_changelog_names_the_seed_withdrawal() -> None:
    """AC11. A heading check cannot observe this; the body is read."""
    body = CHANGELOG.read_text(encoding="utf-8")
    match = _CORE_HEADING_RE.search(body)
    assert match, "the changelog carries no free-standing `core` entry"
    start = match.end()
    end = _CORE_HEADING_RE.search(body, start)
    entry = body[start : end.start() if end else len(body)]
    for needle in ("retired", "no longer seeded"):
        assert needle in entry, f"the topmost core entry does not name the withdrawal: {needle!r}"


def test_both_manifests_carry_the_same_bumped_version() -> None:
    """AC12, pinned against the version this change started from."""
    pack = re.search(r'version = "([^"]+)"', PACK_TOML.read_text(encoding="utf-8"))
    plugin = re.search(r'"version": "([^"]+)"', PLUGIN_JSON.read_text(encoding="utf-8"))
    assert pack and plugin, "a manifest carries no version"
    assert pack.group(1) == plugin.group(1), (
        f"manifests disagree: pack.toml={pack.group(1)} plugin.json={plugin.group(1)}"
    )
    assert pack.group(1) == RELEASE_VERSION, (
        f"AC12 names {RELEASE_VERSION} exactly; found {pack.group(1)}. "
        f"A patch or major bump satisfies any looser comparison, so the "
        f"criterion pins the value."
    )


def test_changelog_version_matches_the_manifests() -> None:
    """The repository's own coupling check lives outside `build-check`.

    Without this, an entry headed with any other version satisfies AC11 and
    AC12 together while nothing in the required gate notices.
    """
    match = _CORE_HEADING_RE.search(CHANGELOG.read_text(encoding="utf-8"))
    assert match, "the changelog carries no free-standing `core` entry"
    pack = re.search(r'version = "([^"]+)"', PACK_TOML.read_text(encoding="utf-8"))
    assert pack and match.group("version") == pack.group(1), (
        f"changelog heading is {match.group('version')!r} but pack.toml is "
        f"{pack.group(1) if pack else None!r}"
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


# --------------------------------------------------------------------------
# The inert-span scanner, pinned case by case
#
# Round 13 found the previous round's "behaviours verified" claim was false:
# those checks were run ad hoc and never committed, and worse, they
# called `_mask_inert` directly while `_matching_link_count` took a different
# path entirely — so the proof ratified the intent rather than the code. These
# cases run against the real readers wherever one exists. Add to them freely;
# nothing states how many there are.
# --------------------------------------------------------------------------

_DEST = "docs/README.md"
_FRAG = "#the-three-lifecycle-classes"


@pytest.mark.parametrize(
    ("label", "markup", "operative"),
    [
        ("plain link", f"[x]({_DEST}{_FRAG})", True),
        ("image", f"![x]({_DEST}{_FRAG})", False),
        ("escaped bracket", f"\\[x]({_DEST}{_FRAG})", False),
        ("inline code", f"`[x]({_DEST}{_FRAG})`", False),
        ("backtick fence", f"```\n[x]({_DEST}{_FRAG})\n```", False),
        ("tilde fence", f"~~~\n[x]({_DEST}{_FRAG})\n~~~", False),
        ("indented fence", f"   ```\n   [x]({_DEST}{_FRAG})\n   ```", False),
        ("html comment", f"<!--\n[x]({_DEST}{_FRAG})\n-->", False),
        ("unterminated comment", f"<!--\n[x]({_DEST}{_FRAG})\n", False),
        # A four-backtick fence stays open across the three-backtick lines it
        # quotes. Live in this repository at `guides/_shared/how-to/
        # author-a-skill.md`, where a ````markdown fence wraps ```bash.
        ("nested fence", f"````\n```\n[x]({_DEST}{_FRAG})\n```\n````", False),
        # A `<!--` shown as inline code is a sample, not an opener. Live at
        # `spec-and-plan-contract.md`, which quotes it with no closing `-->`.
        ("quoted comment opener", f"a `<!--` b\n[x]({_DEST}{_FRAG})", True),
    ],
)
def test_only_an_operative_link_counts(label: str, markup: str, operative: bool) -> None:
    """A link a reader cannot follow must not satisfy AC6."""
    found = _LINK_TARGET_RE.findall(_inert_masked(markup))
    assert bool(found) == operative, f"{label}: expected operative={operative}"


@pytest.mark.parametrize(
    ("label", "body", "reaches"),
    [
        ("plain body", "## D\nkeep\n\n## Next\ntail\n", True),
        ("fenced fake heading", "## D\nkeep\n```\n## Fake\n```\nkeep2\n\n## Next\ntail\n", True),
        ("commented fake heading", "## D\nkeep\n<!--\n## Fake\n-->\nkeep2\n\n## Next\ntail\n", True),
    ],
)
def test_an_inert_heading_does_not_end_a_section(label: str, body: str, reaches: bool) -> None:
    """A commented or fenced `## Fake` must not truncate the section.

    Truncation is a false green: content after the fake boundary — a dangling
    link included — is never examined by the placement assertions.
    """
    section = section_of(body, "D")
    assert ("keep" in section) is reaches, label
    assert "tail" not in section, f"{label}: a real heading must still end it"


def test_an_inert_heading_exposes_no_anchor(tmp_path: Path) -> None:
    """`anchors_in` must ignore a heading no reader renders."""
    page = tmp_path / "page.md"
    page.write_text("# Real\n\n<!--\n## Commented\n-->\n\n```\n## Fenced\n```\n", encoding="utf-8")
    assert anchors_in(page) == frozenset({"real"})


def test_a_heading_keeps_its_inline_code_in_the_anchor(tmp_path: Path) -> None:
    """Masking locates a heading; the slug still comes from the real text.

    `## Use \\`foo\\`` anchors as `use-foo`. Slugging the masked line would
    blank the code span and yield `use`, so every link to it would miss.
    """
    page = tmp_path / "page.md"
    page.write_text("## Use `foo`\n", encoding="utf-8")
    assert anchors_in(page) == frozenset({"use-foo"})


def test_visible_prose_keeps_backticked_tokens_and_drops_blocks() -> None:
    """Inline code is content here; several assertions name a backticked token."""
    text = "a `kept-token` b\n\n```\nfenced-out\n```\n\n<!-- commented-out -->\n"
    prose = visible_prose(text)
    assert "kept-token" in prose
    assert "fenced-out" not in prose
    assert "commented-out" not in prose
