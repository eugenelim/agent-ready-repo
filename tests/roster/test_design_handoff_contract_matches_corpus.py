"""Hold the shipped design-handoff contract to the repository's real design tree.

`packs/frontend-engineering/.apm/skills/frontend-engineering/references/
design-handoff.md` tells an agent which files under an adopter's `[design]
output_dir` are the handoff and what to do with each. Nothing mechanical read it
before this module, and six pre-EXECUTE review rounds each found at least one
claim in that contract's authoring chain that the real corpus contradicts:
frontmatter sets, heading literals, a sibling file the read path also matched,
foreign `type:` values under the read paths, files missing keys their template
declares, duplicate H1s.

Hand-transcription is the mechanism, and a review round cannot fix a
transcription process — it can only find the next instance. So this module reads
the contract out of the shipped reference and classifies every file under
`docs/design/` by it, and reds when any file is mishandled.

It asserts nothing about agent behaviour. Whether an agent follows the contract is
what the spec's paired fixture runs observe; this decides only what the contract
*says* about a file, which is a different and mechanically decidable question.

The contract is parsed, never restated. A copy of the table here would pass while
the shipped reference was wrong, which is the defect the module exists to catch.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    REPO_ROOT
    / "packs/frontend-engineering/.apm/skills/frontend-engineering"
    / "references/design-handoff.md"
)
CORPUS = REPO_ROOT / "docs/design"
LEDGER = REPO_ROOT / "docs/specs/design-handoff-read/notes/verification-ledger.md"

# The slugs the real corpus contains. Classification depends on `<slug>`, which an
# operator supplies at runtime and a test has no way to obtain, so the test binds
# the ones this tree actually carries rather than inventing one.
BOUND_SLUGS = ("team-orientation", "tech-site-amendment")

CONSUMED = "consumed"
SKIPPED_NOT_THIS_ARTIFACT = "skipped-not-this-artifact"
OFF_EVERY_READ_PATH = "off-every-read-path"

# A location-bearing value in recorded evidence.
#
# Written as a shape rather than a list of known roots. An earlier version
# enumerated six POSIX prefixes and required the match to follow whitespace or a
# bracket; measured, six of seven known-bad forms evaded it — `/Volumes/...`,
# `/etc/...`, `output_dir=/Users/...`, and both Windows arms, whose `\\\\` in a
# raw string demanded two literal backslashes and could never fire. A guard that
# cannot fail is the thing this module exists to prevent, so
# `test_the_absolute_path_pattern_matches_known_bad_forms` now pins it.
#
# A repository-relative path in prose (`docs/design/...`, `packs/...`) has no
# leading separator and does not match.
ABSOLUTE_PATH_RE = re.compile(
    r"""(?x)
    (?<![A-Za-z0-9._/*-])           # ...at a token boundary, so `docs/design/`
    /(?!/)[A-Za-z0-9._-]+/          # POSIX absolute: /<segment>/   is not a hit
    | ~/                            # home-anchored
    | [A-Za-z]:[\\/]              # Windows drive
    | \\\\[A-Za-z0-9._-]+       # UNC
    | file://                       # file URL
    """
)

# One line per platform form the guard must catch. Kept beside the pattern so a
# future edit that narrows it fails loudly instead of going quiet.
KNOWN_BAD_LINES = (
    "root was /Users/alice/vault/design",
    "output_dir=/Users/alice/vault",
    "|/private/tmp/fixture/design|",
    "resolved to /Volumes/external/design",
    "/etc/something",
    r"C:\\Users\\alice\\design",
    r"\\\\server\\share\\design",
    "~/Documents/vault",
    "file:///Users/alice/vault",
)

# Lines the guard must NOT flag, so it stays usable on ordinary prose.
KNOWN_GOOD_LINES = (
    "the contract lives in packs/frontend-engineering/.apm/skills/",
    "measured over docs/design/ on 2026-09-18",
    "see `references/design-handoff.md`",
    "a ratio of 1/3 and a path shape like direction/<slug>.md",
    "triggered for `packs/**/.apm/skills/**`",
)


def _parse_contract(text: str) -> list[dict[str, str]]:
    """Return one row per artifact from the reference's read-path table.

    The table is the machine-readable half of the contract: a fixed header, then
    one row per artifact giving its read path and the frontmatter `type:` literal
    that identifies it.
    """
    rows: list[dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Artifact | Read path | Required `type:` |"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 3 or set(cells[0]) <= {"-", " "}:
                continue
            path = cells[1].strip("`")
            literal = cells[2].strip("`")
            rows.append({"artifact": cells[0], "read_path": path, "type": literal})
    return rows


def _read_path_to_regex(read_path: str, slug: str) -> re.Pattern[str]:
    """Turn a contract read path into a matcher for one bound slug."""
    pattern = re.escape(read_path)
    pattern = pattern.replace(re.escape("<slug>"), re.escape(slug))
    pattern = pattern.replace(re.escape("<screen>"), r"[^/]+")
    return re.compile(rf"^{pattern}$")


def _frontmatter_type(path: Path) -> str | None:
    """Return the frontmatter `type:` value, or None when there is not one.

    Deliberately a line scan rather than a YAML load: the corpus is
    adopter-authored content, and this module only needs one scalar from it.
    Nothing here deserializes untrusted structure.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    for line in text.split("---", 2)[1].splitlines():
        match = re.match(r"^type:\s*(\S+)\s*$", line)
        if match:
            return match.group(1)
    return None


def _classify(rel: str, path: Path, contract: list[dict[str, str]], slug: str) -> str:
    for row in contract:
        if _read_path_to_regex(row["read_path"], slug).match(rel):
            declared = _frontmatter_type(path)
            if declared == row["type"]:
                return CONSUMED
            return SKIPPED_NOT_THIS_ARTIFACT
    return OFF_EVERY_READ_PATH


@pytest.fixture(scope="module")
def contract() -> list[dict[str, str]]:
    assert REFERENCE.is_file(), f"shipped reference is missing: {REFERENCE}"
    return _parse_contract(REFERENCE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_files() -> list[Path]:
    assert CORPUS.is_dir(), f"design corpus is missing: {CORPUS}"
    return sorted(p for p in CORPUS.rglob("*") if p.is_file())


def test_contract_carries_exactly_the_three_artifact_rows(contract):
    """Structural floor.

    Without this the `token-taxonomy` row is unheld: no file in the corpus carries
    that type, so dropping the row or mistyping its literal changes no
    classification and every other assertion here stays green.
    """
    assert contract, "no rows parsed from the reference's read-path table"
    assert len(contract) == 3, f"expected three artifact rows, parsed {len(contract)}"
    # Paired, not two independent sets. Comparing `{read_path}` and `{type}`
    # separately lets a swap between two rows satisfy both — verified by
    # mutation, it left every classification assertion green.
    assert {(row["read_path"], row["type"]) for row in contract} == {
        ("direction/<slug>.md", "creative-direction"),
        ("screens/<slug>/<screen>.md", "screen-flow-brief"),
        ("tokens/<slug>.md", "token-taxonomy"),
    }


def test_the_corpus_walk_finds_files(corpus_files):
    """Floor: an empty walk would make every classification assertion vacuous."""
    assert len(corpus_files) > 1, f"corpus walk found {len(corpus_files)} file(s)"


@pytest.mark.parametrize("slug", BOUND_SLUGS)
def test_every_corpus_file_lands_in_exactly_one_state(contract, corpus_files, slug):
    states: dict[str, str] = {}
    for path in corpus_files:
        rel = path.relative_to(CORPUS).as_posix()
        states[rel] = _classify(rel, path, contract, slug)

    assert set(states.values()) <= {
        CONSUMED,
        SKIPPED_NOT_THIS_ARTIFACT,
        OFF_EVERY_READ_PATH,
    }
    # Off-path is its own state, never folded into the `type:` skip. Conflating
    # them would let a widened read path classify everything as skipped.
    off_path = [r for r, s in states.items() if s == OFF_EVERY_READ_PATH]
    matched = [r for r, s in states.items() if s != OFF_EVERY_READ_PATH]
    assert off_path, "no file landed off every read path"
    assert matched, f"no file matched any read path under slug {slug!r}"


@pytest.mark.parametrize(
    ("slug", "expected_matched"),
    [
        (
            "team-orientation",
            {
                "screens/team-orientation/guides-index.md",
                "screens/team-orientation/internal-case-route.md",
                "screens/team-orientation/marketing-home.md",
                "screens/team-orientation/operating-model-canvas.md",
                "screens/team-orientation/operating-model-canvas-composition.md",
                "screens/team-orientation/path-page.md",
                "screens/team-orientation/search-results.md",
            },
        ),
        ("tech-site-amendment", {"direction/tech-site-amendment.md"}),
    ],
)
def test_the_matched_set_is_exactly_what_the_read_paths_reach(
    contract, corpus_files, slug, expected_matched
):
    """Assert the matched set by name, and derive off-path from it.

    Pinning a total instead would red whenever anyone adds a design document
    anywhere in the tree — a failure that says nothing about the contract. The
    matched set only changes when a read path or a `type:` literal changes, which
    is what this module is for.
    """
    matched = {
        p.relative_to(CORPUS).as_posix()
        for p in corpus_files
        if _classify(p.relative_to(CORPUS).as_posix(), p, contract, slug)
        != OFF_EVERY_READ_PATH
    }
    assert matched == expected_matched
    off_path = len(corpus_files) - len(matched)
    assert off_path == len(corpus_files) - len(expected_matched)


def test_some_corpus_file_is_consumed(contract, corpus_files):
    """Floor: a contract that consumes nothing would satisfy every other check."""
    consumed = [
        p.relative_to(CORPUS).as_posix()
        for slug in BOUND_SLUGS
        for p in corpus_files
        if _classify(p.relative_to(CORPUS).as_posix(), p, contract, slug) == CONSUMED
    ]
    assert consumed, "the contract consumes no file in the corpus"


def test_a_foreign_type_under_a_read_path_is_skipped_not_consumed(
    contract, corpus_files
):
    """The corpus holds path-matched files whose `type:` is not the artifact's.

    A contract that refused them rather than skipping would refuse this
    repository's own design tree.
    """
    skipped = [
        p.relative_to(CORPUS).as_posix()
        for slug in BOUND_SLUGS
        for p in corpus_files
        if _classify(p.relative_to(CORPUS).as_posix(), p, contract, slug)
        == SKIPPED_NOT_THIS_ARTIFACT
    ]
    assert skipped, (
        "no path-matched file carries a foreign `type:` — the skip rule is "
        "unwitnessed by this corpus and the differential arm below is vacuous"
    )


def test_the_absolute_path_pattern_matches_known_bad_forms():
    """The ledger guard is only as good as its pattern, so pin the pattern.

    Without this, narrowing the regex silently turns the ledger floor into a
    check that passes on everything — which is exactly what the first version of
    it did for six of these nine forms.
    """
    missed = [line for line in KNOWN_BAD_LINES if not ABSOLUTE_PATH_RE.search(line)]
    assert not missed, f"guard does not catch: {missed}"

    flagged = [line for line in KNOWN_GOOD_LINES if ABSOLUTE_PATH_RE.search(line)]
    assert not flagged, f"guard flags ordinary prose: {flagged}"


def test_the_verification_ledger_records_no_absolute_path():
    """The ledger is committed evidence; a fixture root is a real machine path.

    The floor is two-sided on purpose. Asserting only "no absolute path appears"
    passes over an absent or empty file, which is the control-that-cannot-fail
    shape this module exists to prevent.
    """
    assert LEDGER.is_file(), f"verification ledger is missing: {LEDGER}"
    text = LEDGER.read_text(encoding="utf-8")
    assert text.strip(), "verification ledger is empty"
    assert "## " in text, "verification ledger records no observation"

    offenders = [
        line.rstrip()
        for line in text.splitlines()
        if ABSOLUTE_PATH_RE.search(line)
    ]
    assert not offenders, "absolute path(s) recorded in the ledger:\n" + "\n".join(
        offenders
    )
