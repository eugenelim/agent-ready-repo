"""Construction checks for the guide blockquote classification ledger."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDES_ROOT = REPO_ROOT / "guides"
SPEC_PATH = REPO_ROOT / "docs/specs/guide-typed-asides-conversion/spec.md"
LEDGER_PATH = (
    REPO_ROOT
    / "docs/specs/guide-typed-asides-conversion/notes/blockquote-classification.jsonl"
)
BASELINE_PATH = (
    REPO_ROOT
    / "docs/specs/guide-typed-asides-conversion/notes/blockquote-baseline-identities.jsonl"
)
ALLOWED_CLASSIFICATIONS = {"quotation", "note", "tip", "caution", "danger"}
REQUIRED_FIELDS = {
    "item",
    "path",
    "line",
    "content_sha256",
    "anchor",
    "classification",
    "status",
    "reason",
}
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
SHA256 = re.compile(r"[0-9a-f]{64}")
ASIDE_OPEN = re.compile(r"^:::(note|tip|caution|danger)(?:\[[^\]]+\])?\s*$")
AUTHORING_STANDARD = GUIDES_ROOT / "_shared/reference/catalogue-authoring-standards.md"
SCAFFOLD_ROOT = (
    REPO_ROOT / "packages/agentbundle/agentbundle/_data/catalogue-scaffold"
)


def _expected_baseline_count() -> int:
    match = re.search(
        r"one row for each of the (\d+) parser-visible contiguous blockquote blocks",
        SPEC_PATH.read_text(encoding="utf-8"),
    )
    assert match, "spec AC1 must define the parser-visible baseline count"
    return int(match.group(1))


def _load_ledger() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_baseline() -> list[dict[str, object]]:
    """Load the frozen inventory captured before the wrapper conversion."""
    return [
        json.loads(line)
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _blockquote_blocks(lines: list[str]) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    start: int | None = None
    fence_char: str | None = None
    fence_length = 0

    for index, line in enumerate(lines):
        fence = FENCE_OPEN.match(line)
        if fence_char is None and fence:
            marker = fence.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            is_quote = False
        elif fence_char is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                line,
            )
            if closing:
                fence_char = None
                fence_length = 0
            is_quote = False
        else:
            is_quote = line.startswith(">")

        if is_quote and start is None:
            start = index
        if not is_quote and start is not None:
            blocks.append((start + 1, "".join(lines[start:index]).rstrip("\n")))
            start = None

    if start is not None:
        blocks.append((start + 1, "".join(lines[start:]).rstrip("\n")))
    return blocks


def _blockquote_body(content: str) -> str:
    """Remove Markdown quote markers while preserving the authored body."""
    return re.sub(r"^> ?", "", content, flags=re.MULTILINE)


def _aside_blocks(lines: list[str]) -> list[tuple[int, str, str]]:
    """Return typed asides outside code fences as line, type, and body."""
    blocks: list[tuple[int, str, str]] = []
    aside_start: int | None = None
    aside_type: str | None = None
    fence_char: str | None = None
    fence_length = 0

    for index, line in enumerate(lines):
        fence = FENCE_OPEN.match(line)
        if fence_char is None and fence:
            marker = fence.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            continue
        if fence_char is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                line,
            )
            if closing:
                fence_char = None
                fence_length = 0
            continue

        if aside_start is None:
            match = ASIDE_OPEN.match(line)
            if match:
                aside_start = index
                aside_type = match.group(1)
            continue

        if line.rstrip("\n") == ":::":
            body = "".join(lines[aside_start + 1 : index]).rstrip("\n")
            assert aside_type is not None
            blocks.append((aside_start + 1, aside_type, body))
            aside_start = None
            aside_type = None

    assert aside_start is None, "unclosed typed aside"
    return blocks


def test_ledger_has_complete_terminal_classifications() -> None:
    ledger = _load_ledger()
    baseline = _load_baseline()
    expected_count = _expected_baseline_count()

    assert len(ledger) == expected_count
    assert len(baseline) == expected_count
    assert [row["item"] for row in ledger] == list(range(1, expected_count + 1))
    assert [row["item"] for row in baseline] == list(range(1, expected_count + 1))
    assert all(set(row) == REQUIRED_FIELDS for row in ledger)
    assert all(row["status"] == "done" for row in ledger)
    assert all(row["classification"] in ALLOWED_CLASSIFICATIONS for row in ledger)
    assert all(isinstance(row["reason"], str) and row["reason"].strip() for row in ledger)
    assert all(isinstance(row["anchor"], str) and row["anchor"].strip() for row in ledger)
    assert all(SHA256.fullmatch(str(row["content_sha256"])) for row in ledger)

    identities = [
        (row["path"], row["line"], row["content_sha256"]) for row in ledger
    ]
    assert len(identities) == len(set(identities)), "duplicate ledger identities"
    baseline_identities = [
        (row["path"], row["line"], row["content_sha256"]) for row in baseline
    ]
    assert identities == baseline_identities, "ledger drifted from frozen baseline"

    anchors = [(row["path"], row["anchor"]) for row in ledger]
    assert len(anchors) == len(set(anchors)), "anchors must be unique within a guide"


def test_ledger_matches_converted_asides_and_unchanged_quotations() -> None:
    ledger = _load_ledger()
    failures: list[str] = []

    for path in sorted(GUIDES_ROOT.rglob("*.md")):
        source_path = path.relative_to(REPO_ROOT).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        rows = [row for row in ledger if row["path"] == source_path]
        quotation_rows = [row for row in rows if row["classification"] == "quotation"]
        typed_rows = [row for row in rows if row["classification"] != "quotation"]

        blockquotes = _blockquote_blocks(lines)
        blockquote_hashes = [
            hashlib.sha256(_blockquote_body(content).encode()).hexdigest()
            for _, content in blockquotes
        ]
        expected_quote_hashes = [str(row["content_sha256"]) for row in quotation_rows]
        if sorted(blockquote_hashes) != sorted(expected_quote_hashes):
            failures.append(f"{source_path}: quotation content or container drift")

        asides = _aside_blocks(lines)
        for row in typed_rows:
            matches = [
                (aside_type, body)
                for _, aside_type, body in asides
                if aside_type == row["classification"]
                and hashlib.sha256(body.encode()).hexdigest() == row["content_sha256"]
            ]
            if len(matches) != 1:
                failures.append(
                    f"{source_path}:{row['item']}: expected one {row['classification']} "
                    "with unchanged body"
                )

        expected_sequence = [
            (str(row["classification"]), str(row["content_sha256"]))
            for row in rows
        ]
        expected_containers = set(expected_sequence)
        current_containers = [
            (
                line,
                "quotation",
                hashlib.sha256(_blockquote_body(content).encode()).hexdigest(),
            )
            for line, content in blockquotes
        ] + [
            (line, aside_type, hashlib.sha256(body.encode()).hexdigest())
            for line, aside_type, body in asides
        ]
        observed_sequence = [
            (container, content_hash)
            for _, container, content_hash in sorted(current_containers)
            if (container, content_hash) in expected_containers
        ]
        if observed_sequence != expected_sequence:
            failures.append(
                f"{source_path}: classified container order drifted from ledger"
            )

    assert failures == [], "\n".join(failures)


def test_authoring_standard_defines_the_fixed_aside_contract() -> None:
    standard = AUTHORING_STANDARD.read_text(encoding="utf-8")

    for aside_type in ("note", "tip", "caution", "danger"):
        assert re.search(rf"^\| `{aside_type}` \| .+ \|$", standard, re.MULTILINE)
    assert "Use only those four types." in standard
    assert re.search(r"```md\n:::caution\n.+\n:::\n```", standard, re.DOTALL)
    assert "A blockquote has a different job" in standard
    assert "Leave those passages as `>` blockquotes." in standard
    assert "do not turn genuine quoted wording into an\naside" in standard


def test_agentbundle_release_carries_the_authoring_standard() -> None:
    source = AUTHORING_STANDARD.read_bytes()
    projected_path = (
        SCAFFOLD_ROOT / "guides/_shared/reference/catalogue-authoring-standards.md"
    )
    assert projected_path.read_bytes() == source

    manifest = json.loads((SCAFFOLD_ROOT / "manifest.json").read_text(encoding="utf-8"))
    relative_path = "guides/_shared/reference/catalogue-authoring-standards.md"
    assert manifest["files"][relative_path] == hashlib.sha256(source).hexdigest()

    pyproject = tomllib.loads(
        (REPO_ROOT / "packages/agentbundle/pyproject.toml").read_text(encoding="utf-8")
    )
    version_source = (
        REPO_ROOT / "packages/agentbundle/agentbundle/version.py"
    ).read_text(encoding="utf-8")
    version = pyproject["project"]["version"]
    assert version == "0.37.1"
    assert f'CLI_VERSION = "{version}"' in version_source

    changelog = (REPO_ROOT / "packages/agentbundle/CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    readme = (REPO_ROOT / "packages/agentbundle/README-pypi.md").read_text(
        encoding="utf-8"
    )
    assert f"## [{version}]" in changelog
    assert "typed\n  Starlight asides" in changelog
    assert f"## What's new in {version}" in readme
    assert "guide callout contract" in " ".join(readme.split())


def test_release_handoff_records_the_completed_change_and_batch_closeout() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    status_match = re.search(r"^- \*\*Status:\*\* (\w+)", spec, re.MULTILINE)
    assert status_match
    status = status_match.group(1)
    assert status == "Shipped"
    assert len(re.findall(r"^- \[x\] \*\*AC\d+", spec, re.MULTILINE)) == 12
    assert not re.search(r"^- \[ \] \*\*AC\d+", spec, re.MULTILINE)

    plan = (
        REPO_ROOT / "docs/specs/guide-typed-asides-conversion/plan.md"
    ).read_text(encoding="utf-8")
    assert re.search(r"^- \*\*Status:\*\* Done\b", plan, re.MULTILINE)

    spec_index = (REPO_ROOT / "docs/specs/README.md").read_text(encoding="utf-8")
    row = next(
        line
        for line in spec_index.splitlines()
        if "guide-typed-asides-conversion/spec.md" in line
    )
    assert "| Shipped |" in row
    assert "12 ACs / 4 tasks" in row

    product_changelog = (REPO_ROOT / "docs/product/changelog.md").read_text(
        encoding="utf-8"
    )
    assert "Guide callouts now say what kind of attention they need." in product_changelog

    workspace = tomllib.loads((REPO_ROOT / "workspace.toml").read_text(encoding="utf-8"))
    assert not any(
        entry.get("slug") == "guide-typed-asides-conversion"
        for entry in workspace["backlog"]["open"]
    )
    spec_path = "docs/specs/guide-typed-asides-conversion/spec.md"
    expected_shipped_entry = {
        "path": spec_path,
        "kind": "spec",
        "source": {"mode": "repo-origin"},
        "summary": (
            "Convert load-bearing guide blockquotes to typed Starlight asides "
            "while preserving genuine quotations"
        ),
        "needs": [],
    }
    shipped_matches = [
        entry
        for entry in workspace["ini-002"]["work"]["shipped"]
        if isinstance(entry, dict) and entry.get("path") == spec_path
    ]
    assert shipped_matches == [expected_shipped_entry]
    prohibited_work_targets = {
        spec_path,
        "spec/guide-typed-asides-conversion",
    }
    assert not any(
        (
            entry in prohibited_work_targets
            if isinstance(entry, str)
            else entry.get("path") in prohibited_work_targets
        )
        for initiative in workspace.values()
        if isinstance(initiative, dict) and isinstance(initiative.get("work"), dict)
        for collection in ("active", "queue")
        for entry in initiative["work"].get(collection, [])
        if isinstance(entry, (str, dict))
    )
