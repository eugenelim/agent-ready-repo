"""Roster suite for spec/agent-skill-engineering-consumer-integrations.

`work-loop` and `architect-design` each gain a bounded step that inlines its own
request to the installed agent-skill-engineering provider. This module is that
slice's construction test.

Every assertion carries an `external-comparison`, `same-slice` or
`authored-statement` label matching the spec's three criterion classes. AC3
carries two, because its task-kind set is external while its per-consumer
assignment is authored.

T0 records the merge-base version literals below; T1 adds the assertions.
"""

# --- T0: merge-base version literals -----------------------------------------
#
# AC10 requires each pack's version to be *strictly greater* than its literal
# here, so these are a floor, not an equality. They are literals rather than a
# read of `origin/main` because a test that read the remote would depend on
# fetch state and would not hold in a shallow clone or in CI, where
# `origin/main` may not be a local ref. Both roster precedents record the same
# reason: `test_cooling_scope_closure.py:1053-1058` and
# `test_thirty_day_cooling_and_retirement.py:1626-1629`.
#
# `core` moved twice while this contract was in review (2.21.0 -> 2.22.0 ->
# 2.23.0). Re-record all three if the branch is ever rebased past the pinned
# baseline; a stale floor lets an unbumped pack satisfy AC10.

MERGE_BASE_CORE_VERSION = "2.23.0"  # packs/core/pack.toml at merge base 236ae549c
MERGE_BASE_ARCHITECT_VERSION = "0.15.5"  # packs/architect/pack.toml at merge base 236ae549c
MERGE_BASE_ASE_VERSION = "0.4.0"  # packs/agent-skill-engineering/pack.toml at merge base 236ae549c

import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import tomllib  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml  # noqa: E402
from agentbundle.catalogue_tooling.verify import verify_catalogue  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "docs" / "specs" / "agent-skill-engineering-consumer-integrations"
SPEC_PATH = "docs/specs/agent-skill-engineering-consumer-integrations/spec.md"
SPEC = SPEC_DIR / "spec.md"
PLAN = SPEC_DIR / "plan.md"
QA = SPEC_DIR / "qa.md"

CORE_PACK = ROOT / "packs" / "core"
ARCHITECT_PACK = ROOT / "packs" / "architect"
ASE_PACK = ROOT / "packs" / "agent-skill-engineering"
CORE_BODY = CORE_PACK / ".apm" / "skills" / "work-loop" / "SKILL.md"
ARCHITECT_BODY = (
    ARCHITECT_PACK / ".apm" / "skills" / "architect-design" / "SKILL.md"
)
CORE_MANIFEST = CORE_PACK / "pack.toml"
ARCHITECT_MANIFEST = ARCHITECT_PACK / "pack.toml"
ASE_MANIFEST = ASE_PACK / "pack.toml"
PROVIDER_CONTRACT = (
    ASE_PACK
    / ".apm"
    / "skills"
    / "author-or-update-agent-skill"
    / "references"
    / "provider-contract.md"
)
PROVIDER_CASES = ASE_PACK / "tests" / "fixtures" / "provider-cases.json"

ARCHITECTURE = ROOT / "docs" / "architecture" / "agent-skill-engineering.md"
GUIDES = ROOT / "guides" / "_shared" / "reference" / "catalogue-authoring-standards.md"
GUIDES_TWIN = (
    ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "catalogue-scaffold"
    / "guides"
    / "_shared"
    / "reference"
    / "catalogue-authoring-standards.md"
)
CLAUDE_WORK_LOOP = ROOT / ".claude" / "skills" / "work-loop" / "SKILL.md"
AGENTS_WORK_LOOP = ROOT / ".agents" / "skills" / "work-loop" / "SKILL.md"
WORKSPACE = ROOT / "workspace.toml"
SPECS_README = ROOT / "docs" / "specs" / "README.md"
BRIEF = ROOT / "docs" / "product" / "briefs" / "agent-skill-engineering.md"
CHANGELOG = ROOT / "docs" / "product" / "changelog.md"

CONTRACT_VERSION = "agent-skill-engineering-reference/v1"
HOSTILE_DIAGNOSTIC = "token=secret-value"
TASK_KINDS = frozenset(
    {"skill-authoring", "skill-review", "skill-eval-ci", "agent-extension-design"}
)
CONSUMER_ASSIGNMENTS = (
    (CORE_BODY, frozenset({"skill-authoring", "skill-eval-ci"})),
    (ARCHITECT_BODY, frozenset({"agent-extension-design", "skill-eval-ci"})),
)
BOUND_SURFACES = (
    CORE_BODY,
    ARCHITECT_BODY,
    CORE_MANIFEST,
    ARCHITECT_MANIFEST,
    PROVIDER_CONTRACT,
    ARCHITECTURE,
    CLAUDE_WORK_LOOP,
    AGENTS_WORK_LOOP,
    GUIDES,
    GUIDES_TWIN,
    WORKSPACE,
    SPECS_README,
    BRIEF,
    CHANGELOG,
    PROVIDER_CASES,
)
# A published diagnostic is a backticked multi-word lowercase phrase. The domain
# is the *shape* of a diagnostic, deliberately not the seven answers' own leading
# words: a `(?:knowledge|provider) ...` pattern collects all seven and still
# misses an invented eighth such as `capability seam missing`, so AC1's set
# equality could not fail for the case it exists to catch. Every single-token
# literal in this section is a field name or a status (`ok`, `stale-profile`,
# `topic_ids`), so requiring one internal space excludes them without naming
# them either.
DIAGNOSTIC_LITERAL = re.compile(r"`([a-z][a-z0-9_.-]*(?: [a-z0-9_.-]+)+)`")
PACK_PATH = re.compile(r"(?:packs/|/)agent-skill-engineering(?:/|`)")
# One released changelog section: `[<artifact>][<version>]` segments joined by
# ` / `, then the em dash and the date. Excludes `## [Unreleased]` and the
# `## [1.0.0] — YYYY-MM-DD` template in the file's own header guidance, neither
# of which names an artifact.
RELEASE_HEADING = re.compile(
    r"## \[[^\]]+\]\[[^\]]+\](?: / \[[^\]]+\]\[[^\]]+\])* — \d{4}-\d{2}-\d{2}"
)
STAGE_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def _read_bound_surfaces() -> dict[Path, bytes]:
    """Open every existing surface named by the anti-vacuity bound."""
    return {path: path.read_bytes() for path in BOUND_SURFACES if path.is_file()}


def _section(text: str, heading: str) -> str:
    """Return one level-two Markdown section without later peer sections."""
    marker = f"## {heading}"
    _, found, remainder = text.partition(marker)
    if not found:
        return ""
    return remainder.split("\n## ", 1)[0]


def _provider_cases() -> list[dict[str, object]]:
    """Load the provider fixture's case objects from its top-level list."""
    value = json.loads(PROVIDER_CASES.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        return []
    return [case for case in value if isinstance(case, dict)]


def _fixture_expected_diagnostics() -> set[str]:
    """Load only distinct non-null expected diagnostics from the fixture."""
    diagnostics: set[str] = set()
    for case in _provider_cases():
        expected = case.get("expected")
        if not isinstance(expected, dict):
            continue
        diagnostic = expected.get("diagnostic")
        if isinstance(diagnostic, str):
            diagnostics.add(diagnostic)
    return diagnostics


def _all_diagnostic_values(value: object) -> set[str]:
    """Recursively collect string values stored under any diagnostic key."""
    diagnostics: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "diagnostic" and isinstance(nested, str):
                diagnostics.add(nested)
            diagnostics.update(_all_diagnostic_values(nested))
    elif isinstance(value, list):
        for nested in value:
            diagnostics.update(_all_diagnostic_values(nested))
    return diagnostics


def _published_diagnostics(text: str) -> set[str]:
    """Load diagnostic literals from the provider response section only."""
    provider_response = _section(text, "Provider response")
    fixture = json.loads(PROVIDER_CASES.read_text(encoding="utf-8"))
    fixture_diagnostics = _all_diagnostic_values(fixture)
    published_fixture_values = {
        diagnostic
        for diagnostic in fixture_diagnostics
        if f"`{diagnostic}`" in provider_response
    }
    return set(DIAGNOSTIC_LITERAL.findall(provider_response)) | published_fixture_values


def _task_kinds(text: str) -> set[str]:
    """Parse the wrapped task-kind bullet in the Consumer request section."""
    consumer_request = _section(text, "Consumer request")
    match = re.search(r"^- `task_kind`:(.*?);$", consumer_request, re.MULTILINE | re.DOTALL)
    if match is None:
        return set()
    return set(re.findall(r"`([a-z][a-z0-9-]+)`", match.group(1)))


def _expected_diagnostic(case: dict[str, object]) -> str | None:
    """Return one case's expected diagnostic when it is a string."""
    expected = case.get("expected")
    if not isinstance(expected, dict):
        return None
    diagnostic = expected.get("diagnostic")
    return diagnostic if isinstance(diagnostic, str) else None


def _manifest(path: Path) -> dict[str, object]:
    """Parse a pack manifest with the standard-library TOML reader."""
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _integration_entries(path: Path) -> list[dict[str, object]]:
    """Return well-shaped pack integration entries from a manifest."""
    pack = _manifest(path).get("pack")
    if not isinstance(pack, dict):
        return []
    integrations = pack.get("integrations")
    if not isinstance(integrations, list):
        return []
    return [entry for entry in integrations if isinstance(entry, dict)]


def _carries_integration(path: Path, consumer: str, fallback: str) -> bool:
    """Report whether a manifest carries the consumer's required handoff."""
    for entry in _integration_entries(path):
        consumers = entry.get("consumers")
        declared_consumers = consumers if isinstance(consumers, list) else []
        declared_fallback = entry.get("fallback")
        if (
            entry.get("pack") == "agent-skill-engineering"
            and entry.get("kind") == "handoff"
            and consumer in declared_consumers
            and isinstance(declared_fallback, str)
            and fallback in declared_fallback
        ):
            return True
    return False


def _stage(pack_names: tuple[str, ...], dest: Path) -> Path:
    """Stage only the named packs, plus what lint was measured to require.

    Measured over the three-pack stage: omitting `guides/` or
    `.claude-plugin/marketplace.json` each yields `ok=False` with `CAT-V-002`,
    because `packs/architect/pack.toml` carries a `tutorial` path resolved
    against the catalogue root and lint reads the marketplace manifest.
    `contracts/` is not read and is deliberately not copied. Emitting a
    catalogue config rather than copying the repository's own also matters: the
    real one declares `profiles/`, whose packs are absent here, which produced
    nine spurious `CAT-V-002` diagnostics.
    """
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "catalogue.toml").write_text(
        emit_catalogue_toml(
            name="staged-catalogue",
            display_name="Staged Catalogue",
            description="Staged catalogue for the consumer-integration criterion.",
            minimum_agentbundle_version="0.33.0",
            owner_name="Example Maintainer",
            preferred_adapter="claude-code",
        ),
        encoding="utf-8",
        newline="\n",
    )
    (dest / "packs").mkdir()
    for name in pack_names:
        shutil.copytree(ROOT / "packs" / name, dest / "packs" / name, ignore=STAGE_IGNORE)
    shutil.copytree(ROOT / "guides", dest / "guides", ignore=STAGE_IGNORE)
    (dest / ".claude-plugin").mkdir()
    shutil.copy2(
        ROOT / ".claude-plugin" / "marketplace.json",
        dest / ".claude-plugin" / "marketplace.json",
    )
    return dest


def _version(path: Path) -> str:
    """Read a pack's declared version."""
    pack = _manifest(path).get("pack")
    if not isinstance(pack, dict):
        return ""
    version = pack.get("version")
    return version if isinstance(version, str) else ""


def _version_tuple(version: str) -> tuple[int, ...]:
    """Convert a dotted numeric version into an ordering tuple."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return ()


def _topmost_changelog_version(artifact: str) -> str:
    """Return an artifact's version from the newest release heading naming it.

    A release heading may cover several artifacts at once — `## [core][2.15.2]
    / [governance-extras][0.10.2] / ... — <date>`. `docs/CONVENTIONS.md:701-703`
    makes that the format ("one section per release, naming every artifact that
    release covers") and nine shipped headings use it, two of them combining
    packs this slice releases. Since this slice releases three packs in one PR,
    the combined form is the likely one here.

    Anchoring the em dash straight after this artifact's own segment therefore
    skips such a heading and falls through to an *older* standalone one. That is
    not hypothetical: it is already wrong for 18 of the 24 artifacts in the
    shipped file, and the precedent this module follows records having been
    caught by it once already
    (`tests/roster/test_thirty_day_cooling_and_retirement.py:1640-1646`). That
    precedent's own pattern only handles the artifact *leading* a heading, so it
    cannot be copied for `architect` or `agent-skill-engineering` here.

    Returns the empty string when no release heading names the artifact, which
    AC10 asserts against rather than comparing silently.
    """
    return _newest_release_version(
        artifact, CHANGELOG.read_text(encoding="utf-8").splitlines()
    )


def _newest_release_version(artifact: str, lines: list[str]) -> str:
    """Scan release headings newest-first for one naming the artifact."""
    segment = re.compile(rf"\[{re.escape(artifact)}\]\[([^\]]+)\]")
    for line in lines:
        if RELEASE_HEADING.fullmatch(line) is None:
            continue
        named = segment.search(line)
        if named is not None:
            return named.group(1)
    return ""


def _workspace() -> dict[str, object]:
    """Parse the repository workspace registry."""
    return tomllib.loads(WORKSPACE.read_text(encoding="utf-8"))


def _shape_and_counts() -> tuple[str, int, int]:
    """Derive the spec shape, acceptance-criterion count, and task count."""
    spec_text = SPEC.read_text(encoding="utf-8")
    plan_text = PLAN.read_text(encoding="utf-8")
    shape_match = re.search(r"^- \*\*Shape:\*\*\s+([^\s]+)$", spec_text, re.MULTILINE)
    shape = shape_match.group(1) if shape_match else ""
    criteria = len(re.findall(r"^- \[[ x]\] \*\*AC\d+\*\*", spec_text, re.MULTILINE))
    tasks = len(re.findall(r"^### T\d+[a-z]?:", plan_text, re.MULTILINE))
    return shape, criteria, tasks


def test_bound_roots_reach_every_named_surface() -> None:
    """T1 turns green by binding every existing surface named by AC1-AC16."""
    opened = _read_bound_surfaces()
    assert set(opened) == set(BOUND_SURFACES)  # external-comparison
    assert all(opened.values())  # external-comparison


def test_ac1_provider_contract_publishes_exactly_the_fixture_diagnostics() -> None:
    """T2 turns AC1 green by publishing the fixture's expected diagnostics."""
    fixture = json.loads(PROVIDER_CASES.read_text(encoding="utf-8"))
    expected = _fixture_expected_diagnostics()
    published = _published_diagnostics(PROVIDER_CONTRACT.read_text(encoding="utf-8"))
    assert expected  # external-comparison
    assert len(expected) == 7  # external-comparison
    assert HOSTILE_DIAGNOSTIC not in expected  # external-comparison
    assert HOSTILE_DIAGNOSTIC not in published  # external-comparison
    assert published == expected, (published, expected)  # external-comparison
    assert (_all_diagnostic_values(fixture) - expected).isdisjoint(published)  # external-comparison


@pytest.mark.parametrize("diagnostic", sorted(_fixture_expected_diagnostics()))
def test_ac1_each_fixture_diagnostic_is_individually_recognized(diagnostic: str) -> None:
    """T1 turns this parser control green; T2 turns the publication check green."""
    planted = f"## Provider response\n\n- diagnostic `{diagnostic}`.\n"
    assert _published_diagnostics(planted) == {diagnostic}  # external-comparison


def test_ac1_rejects_a_published_diagnostic_the_fixture_does_not_expect() -> None:
    """A control on AC1's domain: an invented literal must break set equality.

    The mutation this catches is narrowing the loader's domain to the answers'
    own leading words. `capability seam missing` starts with neither
    `knowledge` nor `provider`, so a `(?:knowledge|provider) ...` pattern
    returns exactly the expected set over this input and AC1 passes while the
    shipped file publishes a value no adopter ever receives.
    """
    expected = _fixture_expected_diagnostics()
    planted = "## Provider response\n\n" + "".join(
        f"- `{diagnostic}`\n" for diagnostic in sorted(expected)
    )
    assert _published_diagnostics(planted) == expected  # external-comparison
    invented = planted + "- `capability seam missing`\n"
    assert _published_diagnostics(invented) != expected  # external-comparison


def test_ac1_rejects_the_fixtures_hostile_diagnostic_literal() -> None:
    """A control on AC1's hostile-literal guard.

    `token=secret-value` is a single token, so the shape-based domain cannot
    see it; the fixture-value scan in `_published_diagnostics` is what does.
    Removing that scan must fail here rather than silently permitting the
    fixture's planted credential to reach an installed surface.
    """
    assert HOSTILE_DIAGNOSTIC in _all_diagnostic_values(  # external-comparison
        json.loads(PROVIDER_CASES.read_text(encoding="utf-8"))
    )
    planted = f"## Provider response\n\n- `{HOSTILE_DIAGNOSTIC}`\n"
    assert HOSTILE_DIAGNOSTIC in _published_diagnostics(planted)  # external-comparison


@pytest.mark.parametrize("consumer", (CORE_BODY, ARCHITECT_BODY), ids=("work-loop", "architect-design"))
def test_ac2_each_consumer_names_the_contract_version(consumer: Path) -> None:
    """T3 and T4 turn AC2 green by naming the capability contract version."""
    assert CONTRACT_VERSION in consumer.read_text(encoding="utf-8")  # external-comparison


@pytest.mark.parametrize(
    ("consumer", "assigned"),
    CONSUMER_ASSIGNMENTS,
    ids=("work-loop", "architect-design"),
)
def test_ac3_each_consumer_sends_only_its_assigned_task_kinds(
    consumer: Path,
    assigned: frozenset[str],
) -> None:
    """T3 and T4 turn AC3 green with the two reviewed task-kind assignments."""
    provider_text = PROVIDER_CONTRACT.read_text(encoding="utf-8")
    task_kinds = _task_kinds(provider_text)
    assert len(task_kinds) == 4  # external-comparison
    assert task_kinds >= TASK_KINDS  # external-comparison
    present = {task_kind for task_kind in task_kinds if task_kind in consumer.read_text(encoding="utf-8")}
    assert present == assigned  # external-comparison; authored-statement


@pytest.mark.parametrize("consumer", (CORE_BODY, ARCHITECT_BODY), ids=("work-loop", "architect-design"))
def test_ac4_each_consumer_names_the_absent_case_diagnostic(consumer: Path) -> None:
    """T3 and T4 turn AC4 green by recording the absent case's diagnostic."""
    cases = _provider_cases()
    absent = next((case for case in cases if case.get("id") == "absent"), {})
    absent_diagnostic = _expected_diagnostic(absent)
    zero_candidate_cases = [case for case in cases if case.get("candidates") == []]
    assert absent.get("candidates") == []  # external-comparison
    assert absent_diagnostic is not None  # external-comparison
    assert {_expected_diagnostic(case) for case in zero_candidate_cases} == {absent_diagnostic}  # external-comparison
    assert absent_diagnostic in consumer.read_text(encoding="utf-8")  # external-comparison


@pytest.mark.parametrize("consumer", (CORE_BODY, ARCHITECT_BODY), ids=("work-loop", "architect-design"))
def test_ac5_consumers_do_not_depend_on_the_provider_pack_layout(consumer: Path) -> None:
    """T1 turns AC5's base-green guard on; T3 and T4 must preserve it."""
    body = consumer.read_text(encoding="utf-8")
    # The contract version is excised before the product-name scan because
    # `agent-skill-engineering-reference/v1` carries the product name as a
    # substring. AC2 requires that literal and AC5 forbids the bare product
    # name, so a plain substring scan makes the two criteria unsatisfiable
    # together. Addressing the capability by contract version is the one
    # deviation ADR-0097:97-99 obliges, not a weakening of this guard.
    without_contract_version = body.replace(CONTRACT_VERSION, "")
    assert "agent-skill-engineering" not in without_contract_version  # external-comparison
    assert "ase-okf-reference" not in body  # external-comparison
    assert PACK_PATH.search(body) is None  # external-comparison


def test_ac6_core_manifest_declares_the_work_loop_handoff() -> None:
    """T3 turns AC6 green by declaring work-loop's provider handoff."""
    absent = next((case for case in _provider_cases() if case.get("id") == "absent"), {})
    diagnostic = _expected_diagnostic(absent)
    assert diagnostic is not None  # external-comparison
    assert _carries_integration(CORE_MANIFEST, "skill:work-loop", diagnostic)  # external-comparison


def test_ac7_architect_manifest_declares_the_architect_design_handoff() -> None:
    """T4 turns AC7 green by declaring architect-design's provider handoff."""
    absent = next((case for case in _provider_cases() if case.get("id") == "absent"), {})
    diagnostic = _expected_diagnostic(absent)
    assert diagnostic is not None  # external-comparison
    assert _carries_integration(ARCHITECT_MANIFEST, "skill:architect-design", diagnostic)  # external-comparison


def test_ac8_catalogue_verifies_with_provider_present_and_absent(tmp_path: Path) -> None:
    """T3 and T4 turn AC8 green once both staged manifests carry their entries."""
    absent = next((case for case in _provider_cases() if case.get("id") == "absent"), {})
    diagnostic = _expected_diagnostic(absent)
    assert diagnostic is not None  # external-comparison
    stages = (
        _stage(("core", "architect", "agent-skill-engineering"), tmp_path / "provider-present"),
        _stage(("core", "architect"), tmp_path / "provider-absent"),
    )
    for staged_root in stages:
        staged_core = staged_root / "packs" / "core" / "pack.toml"
        staged_architect = staged_root / "packs" / "architect" / "pack.toml"
        assert _carries_integration(staged_core, "skill:work-loop", diagnostic)  # external-comparison
        assert _carries_integration(staged_architect, "skill:architect-design", diagnostic)  # external-comparison
        result = verify_catalogue(staged_root)
        assert result.ok, result.diagnostics  # external-comparison
        assert not result.diagnostics, result.diagnostics  # external-comparison


def test_ac9_guidance_requires_verbatim_published_fallbacks() -> None:
    """T5 turns AC9 green by adding the diagnostic-vocabulary obligation."""
    section = _section(GUIDES.read_text(encoding="utf-8"), "11. Optional pack integrations")
    paragraphs = re.split(r"\n\s*\n", section.lower())
    required = (
        "target pack",
        "publish",
        "diagnostic vocabulary",
        "fallback",
        "repeat",
        "verbatim",
    )
    assert any(all(token in paragraph for token in required) for paragraph in paragraphs)  # authored-statement


@pytest.mark.parametrize(
    "artifact",
    ("core", "architect", "agent-skill-engineering"),
)
def test_ac10_reads_a_release_heading_that_covers_several_artifacts(
    artifact: str,
) -> None:
    """A control on AC10's changelog half, for the heading this slice will write.

    The mutation this catches is anchoring the em dash straight after the
    artifact's own segment. Under that form every assertion below reads the
    *older* standalone heading, so `current == topmost` and `current > floor`
    become mutually unsatisfiable and AC10 can never go green — while the
    failure message blames the version rather than the parse.
    """
    combined = (
        "## [core][2.24.0] / [architect][0.15.6] "
        "/ [agent-skill-engineering][0.4.1] — 2026-09-03"
    )
    stale = ["## [core][2.23.0] — 2026-09-03"]
    expected = {"core": "2.24.0", "architect": "0.15.6", "agent-skill-engineering": "0.4.1"}
    assert _newest_release_version(artifact, [combined, *stale]) == expected[artifact]  # external-comparison
    # Newest-first ordering, and a heading that names no artifact is skipped.
    assert _newest_release_version(artifact, ["## [Unreleased]", combined]) == expected[artifact]  # external-comparison
    assert _newest_release_version("desk-research", [combined]) == ""  # external-comparison


@pytest.mark.parametrize(
    ("artifact", "manifest", "floor"),
    (
        ("core", CORE_MANIFEST, MERGE_BASE_CORE_VERSION),
        ("architect", ARCHITECT_MANIFEST, MERGE_BASE_ARCHITECT_VERSION),
        ("agent-skill-engineering", ASE_MANIFEST, MERGE_BASE_ASE_VERSION),
    ),
)
def test_ac10_pack_versions_exceed_the_floor_and_match_the_changelog(
    artifact: str,
    manifest: Path,
    floor: str,
) -> None:
    """T6b turns AC10 green by releasing all three packs above their T0 floors."""
    current = _version(manifest)
    topmost = _topmost_changelog_version(artifact)
    assert topmost, f"no release heading in the changelog names {artifact!r}"
    assert current == topmost, (artifact, current, topmost)  # external-comparison
    assert _version_tuple(current) > _version_tuple(floor), (  # external-comparison
        f"{artifact} {current} does not advance past the merge-base floor {floor}"
    )


def test_ac11_work_loop_projections_are_byte_identical_to_the_source() -> None:
    """T1 turns AC11's base-green guard on; T6b restores it after T3."""
    source = CORE_BODY.read_bytes()
    assert CLAUDE_WORK_LOOP.read_bytes() == source  # same-slice
    assert AGENTS_WORK_LOOP.read_bytes() == source  # same-slice


def test_ac12_catalogue_guidance_twin_is_byte_identical() -> None:
    """T1 turns AC12's base-green guard on; T5 updates both copies together."""
    assert GUIDES_TWIN.read_bytes() == GUIDES.read_bytes()  # same-slice


def test_ac13_architecture_last_verified_names_both_consumers() -> None:
    """T6a turns AC13 green by recording this slice and its wired consumers."""
    section = _section(ARCHITECTURE.read_text(encoding="utf-8"), "11. Last verified")
    paragraphs = re.split(r"\n\s*\n", section)
    # The slice is identified by the contract version rather than by its spec
    # slug: none of the 2a, 2b or composition-floors entries carries a slug, so
    # requiring one would push this paragraph out of the very form AC13 names.
    # The contract version is fixed outside this slice, which keeps the
    # identifying token external even though the sentence is authored here.
    required = {CONTRACT_VERSION, "work-loop", "architect-design"}
    assert any(all(token in paragraph for token in required) for paragraph in paragraphs)  # authored-statement


def test_ac14_spec_is_registered_with_derived_shape_and_counts() -> None:
    """T6a turns AC14 green by adding the queue, index, and brief registrations."""
    shape, criteria, tasks = _shape_and_counts()
    assert shape and criteria > 0 and tasks > 0  # same-slice

    workspace = _workspace()
    initiative = workspace.get("ini-009")
    work = initiative.get("work") if isinstance(initiative, dict) else None
    queue = work.get("queue") if isinstance(work, dict) else None
    assert isinstance(queue, list)  # same-slice
    # Membership is matched on a canonical entry's `path` key. `SPEC_PATH in
    # queue` would compare a string against inline tables and be False for
    # every valid record, so the criterion could only have been satisfied by a
    # bare string this file's own authoring rules reject as non-dispatchable.
    assert [entry for entry in queue if isinstance(entry, dict) and entry.get("path") == SPEC_PATH]  # same-slice

    # The row is found by its link target, not by a bare-slug match. The README
    # records a hard predecessor as a backticked slug in the *Constrained by*
    # column, so `agent-skill-engineering-corpus` already appears on three lines
    # (its own row at :26 and two successors citing it). A later sibling citing
    # this slug the same way would otherwise redden AC14 on a Shipped spec that
    # in fact satisfies it.
    link = f"]({SPEC_DIR.name}/spec.md)"
    rows = [line for line in SPECS_README.read_text(encoding="utf-8").splitlines() if link in line]
    assert len(rows) == 1, rows  # same-slice
    row = rows[0]
    assert shape.lower() in row.lower()  # same-slice
    assert re.search(rf"\b{criteria}\s+ACs?\b", row) is not None  # same-slice
    assert re.search(rf"\b{tasks}\s+tasks?\b", row) is not None  # same-slice

    spec_map = _section(BRIEF.read_text(encoding="utf-8"), "Spec map")
    assert SPEC_DIR.name in spec_map  # same-slice


def test_ac15_qa_records_each_review_walk_item_and_session() -> None:
    """T3 and T4 turn AC15 green by recording both manual review walks."""
    assert QA.is_file()  # same-slice
    ledger = _section(QA.read_text(encoding="utf-8"), "Review ledger")
    assert ledger  # same-slice
    # The reviewing session is named once for the ledger, not repeated on all
    # six item rows: AC15 requires a result per item and names the session for
    # the record, so a per-row session token would be a stricter obligation
    # than the criterion it checks.
    assert re.search(r"\bsession\b", ledger, re.IGNORECASE)  # same-slice
    for consumer in ("work-loop", "architect-design"):
        consumer_lines = [line for line in ledger.splitlines() if consumer in line]
        assert consumer_lines  # same-slice
        for item in ("always do", "invocation condition", "surrounding workflow"):
            item_lines = [line for line in consumer_lines if item in line.lower()]
            assert item_lines  # same-slice
            assert any(re.search(r"\b(?:pass(?:ed)?|fail(?:ed)?)\b", line, re.IGNORECASE) for line in item_lines)  # same-slice


def test_ac16_provider_absence_follow_on_is_registered() -> None:
    """T6a turns AC16 green by registering the provider-absence follow-on."""
    backlog = _workspace().get("backlog")
    open_entries = backlog.get("open") if isinstance(backlog, dict) else None
    entries = open_entries if isinstance(open_entries, list) else []
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("slug") == "agent-skill-engineering-provider-absence-behaviour"
        and entry.get("source") == f"{SPEC_PATH}#follow-ons"
    ]
    assert len(matches) == 1  # same-slice
    summary = matches[0].get("summary")
    assert isinstance(summary, str) and summary.strip()  # same-slice
