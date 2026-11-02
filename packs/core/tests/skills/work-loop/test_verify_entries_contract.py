"""Construction tests for the work-loop verify-entry doctrine."""

import re
from pathlib import Path

_PACK = Path(__file__).resolve().parents[3]
_WORK_LOOP = _PACK / ".apm" / "skills" / "work-loop"
_MODES = _WORK_LOOP / "references" / "verification-modes.md"
_TEMPLATE = _WORK_LOOP / "assets" / "verify-entry.md"

_FIELDS = [
    "Surface",
    "Launch",
    "Ready",
    "Doctor",
    "Isolation",
    "Drive",
    "Features",
    "Evidence",
    "Proof limits",
    "Cleanup",
    "Helpers",
    "Stand-in gap",
]


def _flat(text: str) -> str:
    return " ".join(text.split())


def _section(heading: str) -> str:
    """Return one `### ` sub-section of `## Verify entries`, whitespace-flattened."""
    raw = _MODES.read_text(encoding="utf-8")
    top = raw.index("\n## Verify entries\n")
    body = raw[top + 1 :]
    end = re.search(r"^## ", body[3:], re.M)
    body = body[: end.start() + 3] if end else body
    marker = f"\n### {heading}\n"
    assert marker in body, f"missing sub-section: {heading}"
    start = body.index(marker) + len(marker)
    stop = re.search(r"^#{2,3} ", body[start:], re.M)
    return _flat(body[start : start + stop.start()] if stop else body[start:])


def test_t1_sub_headings_in_order_between_neighbours() -> None:
    raw = _MODES.read_text(encoding="utf-8")
    heads = re.findall(r"^## .*$", raw, re.M)
    i = heads.index("## Verify entries")
    assert heads[i - 1] == "## Exploratory / visual fuzz (a third flavor)"
    assert heads[i + 1] == "## Behavior pin"
    block = raw[raw.index("\n## Verify entries\n") :]
    block = block[: block.index("\n## Behavior pin")]
    assert re.findall(r"^### (.*)$", block, re.M) == [
        "When an entry is needed",
        "Where entries live",
        "Building an entry",
        "Proving an entry",
        "Recording and promoting",
        "Drift",
        "Fields",
        "Rules",
        "Grades",
        "Receipt mapping",
        "Placeholders and trust",
    ]
    assert "`assets/verify-entry.md`" in _flat(block)


def test_t1_when_an_entry_is_needed() -> None:
    s = _section("When an entry is needed")
    assert "visual / manual QA, behavior pin, or measurement" in s
    assert "each surface the task changes or must drive" in s
    assert "creating it is the task's first step" in s
    assert "neither touches nor must drive is recorded as uncovered" in s
    assert "Do not map, draft, or fix it" in s


def test_t1_where_entries_live() -> None:
    s = _section("Where entries live")
    order = [
        "A verify file an `AGENT_RULES.md` row already routes to",
        "`CONTRIBUTING.md` in `.github/`, the root, or `docs/`",
        "`DEVELOPMENT.md`",
        "`docs/DEVELOPMENT.md`",
        "`docs/development/`",
        "`contribute/`",
        "`BUILD.md`",
        "`BUILDING.md`",
        "`TESTING.md`",
        "`HACKING.md`",
        "`VERIFICATION.md`",
        "README sections on running or building locally",
        "`AGENTS.md`",
        "`.github/copilot-instructions.md`",
        "`GEMINI.md`",
        "`.claude/skills/verify/`",
    ]
    positions = [s.index(p) for p in order]
    assert positions == sorted(positions)
    assert "offer to add the entry there" in s
    assert "Create `docs/VERIFICATION.md` only when no file covers the surface" in s
    assert "or the adopter declines" in s
    assert "An unanswered or ambiguous offer writes nothing" in s
    assert "the surface's grade is `blocked`" in s
    assert "names the pending offer and records no receipt, because no command ran" in s
    assert "The task does not claim its mode" in s
    assert "under the same adopter acceptance as the entry" in s
    assert "Its `read` cell is that file's repository-relative path" in s
    assert "Its `when` is limited to verifying the surfaces that file covers" in s
    assert "`RUNBOOK.md` and `docs/runbooks/` are not extended with launch steps" in s


def test_t1_building_an_entry() -> None:
    s = _section("Building an entry")
    assert "points at that tooling" in s
    assert (
        "the exact invocation, the ready signal, which output is the evidence, and cleanup" in s
    )
    assert "manifests, scripts, CI, and docs only where no tooling covers the surface" in s


def test_t1_proving_an_entry() -> None:
    s = _section("Proving an entry")
    assert "draft until it has run once from start to finish" in s
    assert "one recorded failing run" in s
    assert "`mutation-proof.md`" in s
    assert "evidence check as its catching test" in s
    assert "one deliberate break of the driven subject as its exact mutation" in s
    assert "stands in for that reference's revert to the pre-fix implementation" in s
    assert "does not claim its mode before both runs exist" in s


def test_t1_recording_and_promoting() -> None:
    s = _section("Recording and promoting")
    assert "Record drive commands in the verification ledger" in s
    assert "second run drives the same surface by hand" in s
    assert "the verify file, a test, or the repository's own tooling" in s


def test_t1_drift() -> None:
    s = _section("Drift")
    assert "fails at run start" in s
    for kind in ("Doc drift", "Harness gap", "Product bug"):
        assert f"**{kind}:**" in s
    assert "Fix a gap in mapped tooling in that tooling" in s
    assert "Report it. Never write it into the entry as expected behavior" in s


def test_t1_fields() -> None:
    raw = _MODES.read_text(encoding="utf-8")
    block = raw[raw.index("\n### Fields\n") :]
    block = block[: block.index("\n### Rules\n")]
    names = re.findall(r"^- \*\*(.+?):\*\*", block, re.M)
    assert names == _FIELDS
    assert "twelve fields" in _flat(block)
    assert "**Doctor:** one read-only check" in _flat(block)


def test_t1_rules() -> None:
    s = _section("Rules")
    assert "Ready means usable, not that the process answers" in s
    assert "Never drive an instance this run did not start" in s
    assert "stable handles such as roles, labels, and prompt strings, never coordinates" in s
    assert "Evidence survives cleanup, and the run checks that it did" in s
    assert "Test-only endpoints and internal setters are not proof" in s
    assert "A dry-run is checked by observing what it skips" in s
    assert "only processes, containers, and directories this run started or created" in s
    assert "by the handle the run recorded, never by process name or pattern" in s


def test_t1_grades() -> None:
    s = _section("Grades")
    grades = re.findall(r"^- `([a-z-]+)`:", _MODES.read_text(encoding="utf-8").split("### Grades")[1], re.M)
    assert grades == ["live-verified", "test-verified", "build-only", "blocked", "failed"]
    assert "exactly one of five grades" in s
    assert "other than the failing proof run" in s
    assert "A grade its recorded commands and output do not support is reported as `blocked`" in s
    assert (
        "comes from the task and the criterion's approved evidence policy, "
        "never from the verify entry" in s
    )


def test_t1_receipt_mapping() -> None:
    raw = _MODES.read_text(encoding="utf-8")
    block = raw[raw.index("\n### Receipt mapping\n") :]
    block = block[: block.index("\n### Placeholders and trust\n")]
    rows = re.findall(r"^\| `([a-z-]+)` \| `([a-z-]+)` \| `([a-z-]+)` \|$", block, re.M)
    assert "| Grade | observation.type | outcome |" in block
    assert sorted(rows) == sorted(
        [
            ("live-verified", "command-result", "live-verified"),
            ("build-only", "command-result", "build-only"),
            ("blocked", "command-result", "blocked"),
            ("failed", "command-result", "failed"),
            ("test-verified", "test-result", "test-verified"),
            ("failed", "test-result", "failed"),
        ]
    )
    assert all(grade == outcome for grade, _, outcome in rows)
    spans = re.findall(r"`([^`]+)`", _flat(block))
    for value in (
        "1",
        "verify:<surface>:<run-id>",
        "exact-subject",
        '{"class": "verify-entry", "identity": "verify:<surface>"}',
    ):
        assert value in spans
    assert "`schema_version` is `1`" in _flat(block)
    assert "`receipt_id` is `verify:<surface>:<run-id>`" in _flat(block)
    assert "`freshness_mode` is `exact-subject`" in _flat(block)


def test_t1_placeholders_and_trust() -> None:
    s = _section("Placeholders and trust")
    assert "use placeholders such as `<checkout>`, `<scratch>`, and `<evidence-dir>`" in s
    assert "paths, hostnames, and usernames" in s
    assert "any output copied into the verification ledger or another committed record" in s
    assert "Never include a credential value" in s
    assert "Name a credential only by its environment variable" in s
    assert "A verify entry is agent guidance. Editing it changes a tool surface" in s
    assert "run only under the host's permission mode" in s
    assert "never widens network, credential, or write scope" in s
    assert "beyond what the task's verification needs" in s


def test_t1_template_headings_and_placeholders() -> None:
    lines = _TEMPLATE.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "## Verify: <surface>"
    assert [ln[4:] for ln in lines if ln.startswith("### ")] == _FIELDS
    values = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    assert len(values) == len(_FIELDS)
    assert all(re.fullmatch(r"<[^>]+>", ln) for ln in values)


_SKILL = _WORK_LOOP / "SKILL.md"


def _skill_region(start: str, end: str) -> str:
    raw = _SKILL.read_text(encoding="utf-8")
    i = raw.index(start)
    return _flat(raw[i : raw.index(end, i)])


def test_t2_plan_step_7_links_verify_entries() -> None:
    region = _skill_region(
        "**Confirm the mechanism exists before claiming the mode",
        "8. **Design construction tests up front.",
    )
    assert "references/verification-modes.md#verify-entries" in region
    assert "verify entry for each surface the task drives" in region


def test_t2_finish_checklist_asks_uncovered_surface() -> None:
    region = _skill_region(
        "- [ ] **Verification passed.**",
        "- [ ] **Review passed, residuals surfaced.**",
    )
    assert "its verify entry does not cover" in region
    assert "record or promote it" in region
