"""Construction tests for portable decision-record destination ordering."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs/repo-governance"
SKILL = PACK / ".apm/skills/new-adr/SKILL.md"
RFC_SKILL = PACK / ".apm/skills/new-rfc/SKILL.md"
RFC_TEMPLATE = PACK / ".apm/skills/new-rfc/assets/rfc.md"
ADR_EVALS = PACK / ".apm/skills/new-adr/evals/evals.json"
RFC_EVALS = PACK / ".apm/skills/new-rfc/evals/evals.json"
MANIFEST = PACK / "pack.toml"


def _flat(text: str) -> str:
    """Collapse whitespace so wrapped prose compares as one line."""
    return " ".join(text.split())


def _step_one() -> str:
    source = SKILL.read_text(encoding="utf-8")
    return _flat(
        source[
            source.index("1. **Resolve the `decision-record`") : source.index(
                "2. Find the next number"
            )
        ]
    )


def _step_eight() -> str:
    source = SKILL.read_text(encoding="utf-8")
    return _flat(
        source[source.index("8. **On confirmation, write.**") : source.index("9. **Return a completion receipt.**")]
    )


def test_decision_record_resolution_precedes_ordinal_and_filename() -> None:
    """No ADR identity or index read is selected before the destination."""
    source = SKILL.read_text(encoding="utf-8")

    resolve_at = source.index(
        "1. **Resolve the `decision-record` destination before identity or reads.**"
    )
    ordinal_at = source.index("2. Find the next number **inside the resolved destination**")
    filename_at = source.index("3. Pick a kebab-case filename title")

    assert resolve_at < ordinal_at < filename_at
    assert "python3 <skill-dir>/scripts/next-ordinal.py <resolved-decision-record-directory>" in source
    assert "passing the directory line step 1 printed, verbatim" in _flat(source)


def test_ac5_step_one_applies_the_order_without_core() -> None:
    """AC5: the six-step order, fail-closed rules, and no core call."""
    step = _step_one()

    for phrase in (
        "`GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` and `GIT_INDEX_FILE` removed",
        "With no Git top-level, refuse with zero effects",
        "`[adr] output_dir`",
        "all other content in that file is data",
        "handed in by a calling workflow",
        "Repeated examples are inference until the user confirms them",
        "one example is never a convention",
        "mandatory policy is refused, not an override",
        "Contradictory evidence fails closed and asks",
        "declared `[adr] output_dir` that holds no ADR-shaped record while another searched location holds one",
        "`docs/adr/`, `docs/decisions/`, `adr/`, `decisions/`",
        "starts with four or more digits, a hyphen, and ends `.md`",
        "`docs/adr/` is a fallback offered only with the user's confirmation",
        "No confirmation overrides a refusal",
        "An external locator stays external",
        "zero ordinal, index, directory, configuration, or file effects",
        "never claims a `semantic-surface-resolution.v1` result",
        "references/agentbundle-layout.md",
    ):
        assert phrase in step, phrase
    for forbidden in ("Ask compatible Core", "Consume the Wave 1", "Wave 1 result", "compatible Core is absent"):
        assert forbidden not in step, forbidden
    # Six precedence entries, in order.
    positions = [
        step.index(marker)
        for marker in (
            "An explicit destination",
            "Declared configuration or repository policy",
            "An established in-repository convention",
            "An established external destination",
            "Ambiguity: ask for confirmation",
            "Absence: offer to select or create",
        )
    ]
    assert positions == sorted(positions)


def test_ac12_every_path_is_proven_and_used_verbatim() -> None:
    """AC12: each read and write path passes the check and is used as printed."""
    step = _step_one()
    source = SKILL.read_text(encoding="utf-8")

    for phrase in (
        "confine-destination.py <root> --root-file agentbundle-layout.toml",
        "confine-destination.py <root> <relative-dir> --read-file <record.md>",
        "used only as the single absolute line the check printed, verbatim",
        "Exit 3 with empty stdout means the named file is absent",
        "Any other non-zero exit, and any exit 0 whose stdout is not exactly one line, is a refusal",
        "An absent layout file is no step-2 evidence",
        "A refused layout file, declared folder, guidance-named location, or search location stops resolution with zero effects",
        "No lower-precedence candidate and no absence offer follows it",
        "A refused record file is skipped and never read",
        "This skill opens no guidance file itself",
        "Confine each with the directory form before listing it",
    ):
        assert phrase in step, phrase
    flat = _flat(source)
    assert "`<skill-dir>` is the canonicalized directory containing this `SKILL.md`" in flat
    assert "Never resolve a script against the working directory" in flat
    assert "python3 scripts/confine-destination.py" not in source
    bare = re.findall(r"python3?\s+(?!<skill-dir>/)\S*scripts/\S+", source)
    assert not bare, bare
    for line in source.splitlines():
        if "confine-destination.py <root>" in line:
            assert "python3 <skill-dir>/scripts/confine-destination.py <root>" in line, line
    for phrase in (
        "reaches the script as exactly one literal argument",
        "discrete argument vector",
        "single-quoted literal",
        "A value the adapter cannot represent safely is refused with zero effects",
    ):
        assert phrase in flat, phrase
    scan = _flat(source[source.index("7. **Preview and confirm") : source.index("8. **On confirmation")])
    assert "only after `confine-destination.py --read-file` passes" in scan
    assert "skipped, never read" in scan


def test_ac10_write_reproves_confinement_and_uses_printed_lines() -> None:
    """AC10: step 8 re-runs both forms and writes only to the printed lines."""
    step = _step_eight()

    assert step.index("--new-file <NNNN-title.md>") < step.index("Create the directory")
    for phrase in (
        "Immediately before creating any directory or file",
        "confine-destination.py <root> <relative-dir> --new-file <NNNN-title.md>",
        "A refusal of either has zero effects",
        "directory line, verbatim",
        "`--new-file` line, verbatim",
        "index-records.py <directory-line-printed-by-the-check>",
        "Any change to the folder or title after the check re-runs both checks",
    ):
        assert phrase in step, phrase
    source = _flat(SKILL.read_text(encoding="utf-8"))
    assert "re-run both step-7 checks for the final folder and title" in step
    preview = _flat(
        SKILL.read_text(encoding="utf-8")[
            SKILL.read_text(encoding="utf-8").index("7. **Preview and confirm") :
            SKILL.read_text(encoding="utf-8").index("8. **On confirmation")
        ]
    )
    # Step 7 runs both checks before it shows the preview, and shows their lines.
    assert preview.index("--new-file <NNNN-title.md>") < preview.index("Then show the author")
    assert preview.index("run both checks") < preview.index("Then show the author")
    assert "printed lines of the directory check and the `--new-file` check below, verbatim" in preview
    assert "A refusal of either has zero effects and no preview" in preview
    assert "step 8's check" not in source
    assert "the `--new-file` line written, verbatim" in source


def test_ac6_new_rfc_core_references_are_conditional_with_fallbacks() -> None:
    """AC6: every core-owned reference in new-rfc names its condition and fallback."""
    skill = _flat(RFC_SKILL.read_text(encoding="utf-8"))
    template = _flat(RFC_TEMPLATE.read_text(encoding="utf-8"))

    for phrase in (
        "core's `new-spec` when core is installed, otherwise a spec in the repository's own spec format",
        "core's `work-loop` risk triggers when core is installed",
        "the template's own `light` / `standard` / `heavy` definitions",
        "Dispatch `adversarial-reviewer` when core is installed",
        "When core is installed, dispatch `security-reviewer` for a security boundary or trust model",
        "a fresh-context reviewer given only the RFC text and the same adversarial",
        "record it in the receipt as self-review",
        "When core is installed, hand follow-on work to its `work-intake` / `workspace-status`",
        "Without core, list the follow-ons in the completion receipt",
    ):
        assert phrase in skill, phrase
    assert "owning core workflow" not in skill
    assert ". Dispatch `security-reviewer`" not in skill
    assert "Use core's work-loop risk triggers when core is installed, otherwise these definitions" in template
    assert "Consult work-loop's risk triggers" not in template


def test_ac7_evals_match_the_in_skill_resolution() -> None:
    """AC7: no core-resolver eval; absent-core preview, unsafe refusal, rfc review."""
    adr = json.loads(ADR_EVALS.read_text(encoding="utf-8"))["evals"]
    text = json.dumps(adr)
    for stale in (
        "compatible Core resolver",
        "asks compatible Core",
        "Wave 1 destination",
        "Preserves the Wave 1 refusal",
        "zero-write decision-record repository handoff",
        "routes the handoff to compatible Core",
    ):
        assert stale not in text, stale
    by_id = {e["id"]: e for e in adr}
    assert "Core is not installed" in by_id[13]["prompt"]
    assert "preview" in by_id[13]["expected_output"]
    assert "Proceeds without core" in " ".join(by_id[13]["assertions"])
    unsafe = [e for e in adr if "zero-effect refusal" in e["expected_output"] and "confine-destination.py" in e["expected_output"]]
    assert unsafe, "no unsafe-destination refusal eval"
    rfc = json.loads(RFC_EVALS.read_text(encoding="utf-8"))["evals"]
    assert any("Core is not installed" in e["prompt"] and "self-review" in e["expected_output"] for e in rfc)


def test_ac11_core_handoffs_are_declared_integrations() -> None:
    """AC11: weights, queue and review hand-offs are optional core integrations."""
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    core = {i["id"]: i for i in manifest["pack"]["integrations"] if i["pack"] == "core"}

    expected = {
        "decision-weight-triggers": "skill:work-loop",
        "follow-on-queue-registration": "skill:work-intake",
        "rfc-review": "agent:adversarial-reviewer",
    }
    for integration_id, provider in expected.items():
        entry = core[integration_id]
        assert entry["consumers"] == ["skill:new-rfc"], integration_id
        assert provider in entry["providers"], integration_id
        assert entry["fallback"].startswith("If core is absent"), integration_id
    weight_fallback = core["decision-weight-triggers"]["fallback"]
    assert "listing" not in weight_fallback
    assert "template's own light, standard and heavy definitions" in weight_fallback
    assert "completion receipt" in core["follow-on-queue-registration"]["fallback"]
    assert "self-review" in core["rfc-review"]["fallback"]


def test_existing_adr_method_and_write_gate_remain() -> None:
    """Wave 3 moves the destination gate, not the ADR method."""
    source = SKILL.read_text(encoding="utf-8")

    for marker in (
        "Frame the decision before drafting",
        "Decision summary",
        "Decision drivers",
        "Preview and confirm — the write gate",
        "wait for explicit confirmation",
        "Leave the status `Proposed`",
        "## Lifecycle after acceptance",
    ):
        assert marker in source


AC8_SURFACES = (
    PACK / "README.md",
    PACK / "DESIGN.md",
    PACK / "JOURNEY.md",
    PACK / "docs/index.md",
    ROOT / "web/src/content/journeys/repo-governance.md",
    ROOT / "profiles/full-ceremony.toml",
    ROOT / "packs/core/docs/index.md",
    *sorted((ROOT / "guides/repo-governance").rglob("*.md")),
)


def test_ac8_no_surface_states_governance_extras_requires_core() -> None:
    """AC8 (a): no pack doc, journey or guide calls core required."""
    forbidden = (
        "requires `core`",
        "requires core",
        "depends on core",
        "depends on it",
        "install core first",
        "dependency on `core` is required",
        "core is a required dependency",
        "repo-governance` and `catalogue-curation` list core as a required",
        "compatible `core` installed",
    )
    for path in AC8_SURFACES:
        text = _flat(path.read_text(encoding="utf-8")).lower()
        if path.name == "index.md" and path.parent.name == "docs" and path.parent.parent.name == "repo-governance":
            # catalogue-curation legitimately requires core and repo-governance
            text = text.replace("`catalogue-curation` requires both `core`", "")
        for phrase in forbidden:
            assert phrase.lower() not in text, f"{path.relative_to(ROOT)}: {phrase!r}"


def test_ac8_no_surface_describes_new_adr_consulting_core_or_stopping() -> None:
    """AC8 (b): new-adr is not described as asking core or handing off."""
    forbidden = (
        "asks core where",
        "through core before numbering",
        "through compatible core",
        "compatible core returns",
        "portable `decision-record` handoff",
        "portable handoff rather than simulated resolution",
        "without compatible core",
        "core offers the catalogue fallback",
    )
    for path in AC8_SURFACES:
        text = _flat(path.read_text(encoding="utf-8")).lower()
        for phrase in forbidden:
            assert phrase not in text, f"{path.relative_to(ROOT)}: {phrase!r}"


def test_ac8_new_rfc_guide_presents_core_pieces_as_conditional() -> None:
    """AC8 (c): the how-to names core-installed use and the fallbacks."""
    text = _flat((ROOT / "guides/repo-governance/how-to/new-rfc.md").read_text(encoding="utf-8"))

    assert "risk triggers when `core` is installed" in text
    assert "weight definitions in the RFC template itself" in text
    assert "When `core` is installed, a fresh-context `adversarial-reviewer`" in text
    assert "Without `core`, a fresh-context reviewer given only the RFC text" in text
    assert "recorded in the receipt as self-review" in text


def test_ac8_web_journey_no_longer_lists_core_as_prerequisite() -> None:
    """AC8 (d): prerequisitePacks is empty in the journey and its site copy."""
    for path in (PACK / "JOURNEY.md", ROOT / "web/src/content/journeys/repo-governance.md"):
        front = path.read_text(encoding="utf-8").split("---")[1]
        assert "prerequisitePacks: []" in front, path
        assert "prerequisitePacks:\n  - core" not in front, path


def test_ac8_first_value_prerequisites_do_not_name_core() -> None:
    """AC8: pack.toml first-value metadata does not make core a prerequisite."""
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    prerequisites = manifest["pack"]["first-value"]["prerequisites"]
    assert prerequisites
    assert all("core" not in item.lower() for item in prerequisites), prerequisites


def test_hostile_values_eval_requires_one_literal_argument() -> None:
    """A new-adr eval covers a hostile output_dir or filename."""
    evals = json.loads(ADR_EVALS.read_text(encoding="utf-8"))["evals"]
    hostile = [e for e in evals if "$(" in e["prompt"] and "output_dir" in e["prompt"]]
    assert hostile, "no hostile output_dir eval"
    text = json.dumps(hostile)
    assert "exactly one literal argument" in text
    assert "command substitution" in text
