"""RFC-0096 Wave 4 closeout and immediate-disposition contract matrix."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    ROOT
    / "tests/roster/fixtures/close-work-extraction-and-immediate-disposition"
)
RESOLVER_PATH = ROOT / "packs/core/.apm/skills/work-intake/scripts/surface_resolver.py"
SCHEMA_PATH = ROOT / "contracts/jsonschema/semantic-surface-resolution.schema.json"
FILE_SAFETY_PATH = (
    ROOT / "packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py"
)
CLOSE_WORK_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/close_work.py"
SOURCE_SKILL_PATH = ROOT / "packs/core/.apm/skills/close-work/SKILL.md"

EXPECTED_RESOLVER_SHA256 = (
    "b341f10478e8db8c03c0ff187648d3e9d3daa5b9e860f48504d13d025ab8a5d4"
)
EXPECTED_SCHEMA_SHA256 = (
    "df66ac4455316a9b9edf1664a9966415afaed2048ffa415a7db95bafce0c28d8"
)
# This digest is the only guard that the pack's projected duplicate of the
# blessed helper is byte-identical to the canonical one, so its provenance is an
# audit trail: state what moved the bytes, and nothing else.
#
# Two widenings have moved it, both keyword-only and both defaulting to None, so
# each was backward compatible and the duplicate was re-synced rather than
# diverged:
#
#   1. main's `feat(agentbundle): add portable Agent Plugin projection` added
#      `max_files` and `max_depth`.
#   2. RFC-0096 Wave 4's `fix(agentbundle,core): close the enumeration bound
#      asymmetry` added `max_entries`, because `max_files` alone leaves a
#      directory-only tree unbounded between close-work's preflight and its
#      materialising walk.
#
# close-work's single call site now passes `max_files` and `max_entries` by
# keyword (`_confined_target_set` in close_work.py), asserted structurally by
# `test_materialising_walk_carries_both_preflight_bounds` in the pack suite.
EXPECTED_FILE_SAFETY_SHA256 = (
    "bf4294f9dd19798709713d37f7c088e8b490c9ebe1df3f0e6f879e39a2bc0bb6"
)


def _sha256(path: Path) -> str:
    """Return the byte digest for one pinned authority."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, name: str):
    """Load one repository module without requiring an installed package."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_close_work():
    """Load the Wave 4 deterministic seam once it exists."""
    assert CLOSE_WORK_PATH.is_file(), "close-work deterministic seam is absent"
    return _load_module(CLOSE_WORK_PATH, "wave4_close_work_matrix")


def _fixture(name: str):
    """Read one inert committed matrix."""
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _inputs(raw: dict[str, object], *excluded: str) -> dict[str, object]:
    """Keep assertion metadata out of the behavior seam inputs."""
    omitted = {"id", "expected", "expected_phase", "expected_blocker", *excluded}
    return {key: value for key, value in raw.items() if key not in omitted}


def _tree_state(root: Path) -> tuple[tuple[str, str, bytes | str], ...]:
    """Return a no-follow snapshot that is safe for special-file fixtures."""
    state: list[tuple[str, str, bytes | str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        inspected = path.lstat()
        if path.is_symlink():
            state.append((relative, "symlink", os.readlink(path)))
        elif path.is_file():
            state.append((relative, f"regular:{inspected.st_nlink}", path.read_bytes()))
        elif path.is_dir():
            state.append((relative, "directory", b""))
        else:
            state.append((relative, "non-regular", b""))
    return tuple(state)


def _surface_candidate(close_work, root: Path, case_root: Path, logical: str):
    resolver = close_work.surface_resolver()
    return resolver.SurfaceCandidate(
        role="delivery-contract",
        logical_locator=logical,
        physical_locator=resolver.Locator(
            "repository-path", case_root.relative_to(root).as_posix()
        ),
        provenance=(
            resolver.Evidence("explicit", "request:close-work", "explicit"),
        ),
        availability="available",
        writability="writable",
        authority=resolver.Authority(
            source=resolver.AuthorityFact(
                "repository-owned", "authority:source-preview"
            ),
            write=resolver.AuthorityFact(
                "delegated", "authority:write-preview"
            ),
            delete=resolver.AuthorityFact(
                "delegated", "authority:delete-preview"
            ),
        ),
        revision_or_fingerprint="fixture-revision-v1",
    )


def _human_confirmation(close_work, preview, confirmation_id: str):
    return close_work.HumanConfirmation(
        confirmation_id=confirmation_id,
        human_evidence_ref=f"human:{confirmation_id}",
        confirmation_challenge=preview.confirmation_challenge,
        enumeration_mode=preview.enumeration_mode,
        surface_role=preview.surface_role,
        logical_locator=preview.logical_locator,
        physical_locator=preview.physical_locator,
        revision_or_fingerprint=preview.revision_or_fingerprint,
        surface_resolution_fingerprint=preview.surface_resolution_fingerprint,
        resource_file_set=tuple(
            target.relative_to(preview.repository_root).as_posix()
            for target in preview.targets
        ),
        target_fingerprints=preview.target_fingerprints,
        target_fingerprint=preview.target_fingerprint,
        disposition=preview.disposition,
        disposition_eligibility_fingerprint=(
            preview.disposition_eligibility_fingerprint
        ),
        completion_evidence_ref=preview.completion_evidence_ref,
        durable_output_evidence_refs=preview.durable_output_evidence_refs,
        pushed=preview.pushed,
        removal_integrated=preview.removal_integrated,
        source_state_evidence_ref=preview.source_state_evidence_ref,
        source_authority=preview.source_authority,
        source_authority_evidence_ref=preview.source_authority_evidence_ref,
        write_authority=preview.write_authority,
        write_authority_evidence_ref=preview.write_authority_evidence_ref,
        deletion_authority=preview.deletion_authority,
        deletion_authority_evidence_ref=preview.deletion_authority_evidence_ref,
        authorized_actor_role=preview.authorized_actor_role,
        proposer_role=preview.proposer_role,
        proposer_evidence_ref=preview.proposer_evidence_ref,
        approver_role="repository-maintainer",
        approver_evidence_ref="human-gate:current",
        grant_source=preview.grant_source,
        action=preview.action,
        host_session_provenance=preview.host_session_provenance,
        authority_resource=preview.authority_resource,
        authority_resolution_evidence_ref=(
            preview.authority_resolution_evidence_ref
        ),
        authority_issue_digest=preview.authority_issue_digest,
        proposed_mutation="ordinary-file-removal",
    )


def _effect_authority(close_work, preview) -> dict[str, object]:
    """Return freshly reacquired authority and session facts for one effect."""
    authority_fact = close_work.resolve_mutation_authority(
        grant_record={
            "authorized_actor_role": preview.authorized_actor_role,
            "grant_source": preview.grant_source,
            "action": preview.action,
            "resource": preview.authority_resource,
            "evidence_ref": preview.deletion_authority_evidence_ref,
            "host_session_provenance": preview.host_session_provenance,
        },
        authority_evidence_ref=preview.authority_resolution_evidence_ref,
    )
    assert authority_fact is not None
    return {
        "current_authority_fact": authority_fact,
        "current_surface_candidates": preview.surface_candidates,
        "current_disposition_candidate": preview.disposition_candidate,
    }


def test_wave4_pins_and_executes_shipped_resolver_and_file_safety() -> None:
    """Wave 4 reuses the exact Wave 1 resolver and blessed file helpers."""
    resolver = _load_module(RESOLVER_PATH, "wave4_pinned_resolver")
    file_safety = _load_module(FILE_SAFETY_PATH, "wave4_pinned_file_safety")

    assert _sha256(RESOLVER_PATH) == EXPECTED_RESOLVER_SHA256
    assert _sha256(SCHEMA_PATH) == EXPECTED_SCHEMA_SHA256
    assert _sha256(FILE_SAFETY_PATH) == EXPECTED_FILE_SAFETY_SHA256
    assert "research-evidence" not in resolver.SURFACE_ROLES
    assert {
        "validate_confined_directory",
        "list_confined_regular_files",
        "read_confined_regular_file",
        "sha256_confined_regular_file",
    }.issubset(vars(file_safety))

    files = file_safety.list_confined_regular_files(FIXTURE_ROOT, FIXTURE_ROOT)
    assert {path.name for path in files} == {
        "context-matrix.json",
        "disposition-matrix.json",
        "lifecycle-matrix.json",
        "refusal-matrix.json",
    }
    for path in files:
        assert file_safety.read_confined_regular_file(FIXTURE_ROOT, path)
        assert file_safety.sha256_confined_regular_file(
            FIXTURE_ROOT, path
        ) == _sha256(path)


def test_lifecycle_projection_matrix_is_exact_and_read_only() -> None:
    """Lifecycle projection is deterministic and never exposes mutation."""
    close_work = _load_close_work()

    for case in _fixture("lifecycle-matrix.json"):
        result = close_work.project_lifecycle(**_inputs(case))
        assert result.lifecycle_phase == case["expected_phase"], case["id"]
        assert result.blocker == case["expected_blocker"], case["id"]
        assert result.permission_granted is False, case["id"]
        assert result.mutated == (), case["id"]


def test_disposition_matrix_separates_intent_from_permission() -> None:
    """All six disposition intents and blockers remain mutation-free."""
    close_work = _load_close_work()

    for raw in _fixture("disposition-matrix.json"):
        candidate = close_work.DispositionCandidate(
            lifecycle_outcome=raw.get(
                "lifecycle_outcome", "completed" if raw["delivered"] else "abandoned"
            ),
            persisted=raw["persisted"],
            delivered=raw["delivered"],
            pushed=raw["pushed"],
            removal_change=raw["removal_change"],
            removal_integrated=raw["removal_integrated"],
            lasting_facts_settled=raw["lasting_facts_settled"],
            obligations_settled=raw["obligations_settled"],
            live_dependencies=raw["live_dependencies"],
            retain_exception=raw["retain_exception"],
            source_authority=raw["source_authority"],
            write_authority=raw["write_authority"],
            deletion_authority=raw["deletion_authority"],
        )
        result = close_work.classify_disposition(candidate)
        assert result.disposition == raw["expected"], raw["id"]
        assert result.blocker == raw.get("blocker"), raw["id"]
        assert result.permission_granted is False, raw["id"]
        assert result.mutated == (), raw["id"]
        assert result.history_rewrite is False, raw["id"]


def test_durable_output_and_lld_extraction_matrix_blocks_lost_intent() -> None:
    """Non-inferable facts must reach semantic owners before disposition."""
    close_work = _load_close_work()
    matrix = _fixture("context-matrix.json")

    for raw in matrix["durable_outputs"]:
        result = close_work.assess_durable_output(**_inputs(raw))
        assert result.status == raw["expected"], raw["id"]
    for raw in matrix["lld_facts"]:
        result = close_work.classify_lld_fact(**_inputs(raw))
        assert result.status == raw["expected"], raw["id"]


def test_workspace_capture_matrix_accepts_only_terse_live_state() -> None:
    """Workspace capture points to context instead of narrating history."""
    close_work = _load_close_work()

    for raw in _fixture("context-matrix.json")["workspace_entries"]:
        result = close_work.validate_workspace_capture(**_inputs(raw))
        assert result.status == raw["expected"], raw["id"]
        assert result.mutated == (), raw["id"]


def test_refusal_matrix_proves_reported_and_physical_zero_effect(
    tmp_path: Path,
) -> None:
    """Every declined, drifted, reused, or unsafe effect leaves bytes unchanged."""
    close_work = _load_close_work()

    for raw in _fixture("refusal-matrix.json"):
        case_root = tmp_path / raw["id"]
        case_root.mkdir()
        target = case_root / "delivery.md"
        event = raw["event"]
        if event == "symlink":
            real = case_root / "real.md"
            real.write_text("temporary\n", encoding="utf-8")
            target.symlink_to(real.name)
        elif event == "hard-link":
            target.write_text("temporary\n", encoding="utf-8")
            os.link(target, case_root / "alias.md")
        elif event == "non-regular":
            if not hasattr(os, "mkfifo"):
                pytest.skip("FIFO refusal fixture is unsupported on this platform")
            os.mkfifo(target)
        else:
            target.write_text("temporary\n", encoding="utf-8")

        before = _tree_state(case_root)
        logical_locator = f"delivery-contract:{raw['id']}"
        disposition_candidate = close_work.DispositionCandidate(
            lifecycle_outcome="completed",
            persisted=True,
            delivered=False,
            pushed=False,
            lasting_facts_settled=True,
            obligations_settled=True,
            source_authority="repository-origin",
            write_authority="repository-maintainer",
            deletion_authority="repository-owned",
        )
        authority_fact = close_work.resolve_mutation_authority(
            grant_record={
                "authorized_actor_role": "repository-maintainer",
                "grant_source": "policy:maintainer-delete",
                "action": "delete-confirmed-file-set",
                "resource": logical_locator,
                "evidence_ref": "authority:delete-preview",
                "host_session_provenance": "session:current",
            },
            authority_evidence_ref="authority:resolved-delete-policy",
        )
        assert authority_fact is not None
        preview = close_work.preview_deletion(
            repository_root=tmp_path,
            enumeration_root=case_root,
            surface_role="delivery-contract",
            surface_candidates=(
                _surface_candidate(
                    close_work, tmp_path, case_root, logical_locator
                ),
            ),
            logical_locator=logical_locator,
            targets=(target,),
            disposition="delete-before-push",
            disposition_candidate=disposition_candidate,
            completion_evidence_ref="evidence:completion",
            durable_output_evidence_refs=("evidence:docs",),
            pushed=False,
            removal_integrated=False,
            source_state_evidence_ref="git-state:preview",
            source_authority="repository-origin",
            source_authority_evidence_ref="authority:source-preview",
            write_authority="repository-maintainer",
            write_authority_evidence_ref="authority:write-preview",
            deletion_authority="repository-owned",
            deletion_authority_evidence_ref="authority:delete-preview",
            authorized_actor_role="repository-maintainer",
            proposer_role="delivery-agent",
            proposer_evidence_ref="workflow:close-work-preview",
            grant_source="policy:maintainer-delete",
            action="delete-confirmed-file-set",
            host_session_provenance="session:current",
            authority_fact=authority_fact,
        )

        if event in {"symlink", "hard-link", "non-regular"}:
            result = preview
        elif event == "decline":
            result = close_work.decline_deletion(preview)
        else:
            confirmation = close_work.confirm_deletion(
                preview,
                human_confirmation=_human_confirmation(
                    close_work, preview, f"confirm:{raw['id']}"
                ),
            )
            if event == "confirmation-mismatch":
                confirmation = replace(confirmation, disposition="cool-30-days")
            elif event == "content-drift":
                target.write_text("changed\n", encoding="utf-8")
            elif event == "rename":
                target.rename(case_root / "renamed.md")
            elif event == "added-target":
                (case_root / "added.md").write_text("added\n", encoding="utf-8")
            elif event == "confirmation-reuse":
                first = close_work.apply_confirmed_deletion(
                    repository_root=tmp_path,
                    preview=preview,
                    confirmation=confirmation,
                    current_source_state={
                        "pushed": False,
                        "removal_integrated": False,
                    },
                    source_state_evidence_ref="git-state:preview",
                    **_effect_authority(close_work, preview),
                )
                assert first.mutated == (target,)
                target.write_text("temporary\n", encoding="utf-8")
            before = _tree_state(case_root)
            current_state = {
                "pushed": event == "source-state-drift",
                "removal_integrated": False,
            }
            result = close_work.apply_confirmed_deletion(
                repository_root=tmp_path,
                preview=preview,
                confirmation=confirmation,
                current_source_state=current_state,
                source_state_evidence_ref="git-state:preview",
                **_effect_authority(close_work, preview),
            )

        assert result.code == raw["expected_code"], raw["id"]
        assert result.mutated == (), raw["id"]
        assert _tree_state(case_root) == before, raw["id"]


def test_wave4_excludes_later_wave_and_history_rewrite_behaviour() -> None:
    """Wave 4 classifies only and never grows timed or history-rewrite effects.

    The declared-capability equality below is a self-report: it mirrors the
    literal `wave4_capabilities()` returns, so on its own it would stay green
    while a date engine was added beside it. The source-level assertions after it
    are the ones that can actually fail on that change (AC13, AC21).
    """
    close_work = _load_close_work()

    capabilities = close_work.wave4_capabilities()

    assert capabilities == {
        "timed_retirement": False,
        "migration_or_pruning": False,
        "workspace_context_exclusion": False,
        "history_rewrite": False,
        "second_resolver": False,
    }

    tree = ast.parse(CLOSE_WORK_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    # A clock is the mechanism every later-wave capability would need first.
    assert imported.isdisjoint({"datetime", "time", "calendar", "zoneinfo"})

    # Date-shaped state field names only. `cooling_started: bool` is deliberately
    # NOT in this list: it is a boundary marker the pause path asserts is False,
    # so it is evidence for the boundary rather than a violation of it.
    source = CLOSE_WORK_PATH.read_text(encoding="utf-8")
    for token in (
        "completed_on",
        "review_on",
        "review_date",
        "due_at",
        "due_date",
        "enrolled_at",
        "retire_at",
        "expires_at",
        "cooling_started_at",
    ):
        assert token not in source, token


def _declared_boundaries(frontmatter: str) -> set[str]:
    """Parse `metadata.boundaries` in either flow or block sequence form.

    close-work writes the flow form (`[a, b]`); most core skills write the block
    form. An exact-set assertion has to read both, or it silently passes on the
    shape it cannot parse.
    """
    flow = re.search(r"^\s*boundaries:\s*\[(.+?)\]\s*$", frontmatter, re.MULTILINE)
    if flow is not None:
        return {item.strip() for item in flow.group(1).split(",") if item.strip()}
    block = re.search(
        r"^\s*boundaries:\s*\n((?:\s*-\s*\S+\s*\n)+)", frontmatter, re.MULTILINE
    )
    assert block is not None, "no parsable boundaries declaration"
    return {
        line.strip().removeprefix("-").strip()
        for line in block.group(1).splitlines()
        if line.strip()
    }


_RESULT_TYPES = frozenset({
    "DeletionResult",
    "PauseResult",
    "ReceiptResult",
    "InitiativeCloseoutResult",
    "ArtifactCloseoutResult",
    "Assessment",
    "DispositionDecision",
    "LifecycleProjection",
})
_TERMINAL_MUTATED_CODES = frozenset({"rollback-failed", "residual-hardlink"})
# Provably unreachable emitters, retained as defence in depth behind
# `_mutation_binding`'s identical checks on the identical values. No fixture can
# reach them, so an assertion would have to fake the call rather than drive the
# seam. Each carries an inline subsumption note at its site.
_UNREACHABLE_BY_SUBSUMPTION = frozenset({
    "action-not-authorized",
    "grant-not-authoritative",
    "session-provenance-invalid",
})


def _result_codes(source: str) -> set[str]:
    """Every string literal close_work.py hands to a result constructor."""
    codes: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _RESULT_TYPES
        ):
            continue
        for value in list(node.args) + [kw.value for kw in node.keywords]:
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and re.fullmatch(r"[a-z][a-z0-9-]{3,}", value.value)
            ):
                codes.add(value.value)
    return codes


# The fixture keys the drivers actually assert a result against. Measured from
# the drivers, not guessed: `expected_phase`/`expected_blocker` (lifecycle),
# `expected` and `blocker` (disposition and context), `expected_code`
# (refusal). Every other key in these matrices is *input* — `id` is a failure
# label and `event` selects a driver behaviour — so a code named only there is
# not asserted by anything.
_ASSERTION_KEYS = (
    "expected",
    "expected_code",
    "expected_phase",
    "expected_blocker",
    "blocker",
)


def _json_asserted_codes(text: str) -> set[str]:
    """Return code-shaped values a fixture asserts, ignoring input fields."""
    codes: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if (
                    key in _ASSERTION_KEYS
                    and isinstance(value, str)
                    and re.fullmatch(r"[a-z][a-z0-9-]{3,}", value)
                ):
                    codes.add(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    try:
        walk(json.loads(text))
    except json.JSONDecodeError:  # pragma: no cover - corpus is valid JSON
        return codes
    return codes


def test_committed_matrices_are_byte_identical_on_a_second_run() -> None:
    """AC19: two runs over the committed matrices produce equal results.

    Lives here rather than in the pack suite because it reads this directory's
    fixtures; a pack test may not reach above its owning pack. `preview_deletion`
    is excluded on purpose — it embeds a fresh `secrets.token_hex` challenge and
    is required to differ between runs.
    """
    close_work = _load_close_work()

    def run() -> str:
        rendered: list[str] = []
        for raw in _fixture("disposition-matrix.json"):
            candidate = close_work.DispositionCandidate(
                lifecycle_outcome=raw.get(
                    "lifecycle_outcome",
                    "completed" if raw["delivered"] else "abandoned",
                ),
                persisted=raw["persisted"],
                delivered=raw["delivered"],
                pushed=raw["pushed"],
                removal_change=raw["removal_change"],
                removal_integrated=raw["removal_integrated"],
                lasting_facts_settled=raw["lasting_facts_settled"],
                obligations_settled=raw["obligations_settled"],
                live_dependencies=raw["live_dependencies"],
                retain_exception=raw["retain_exception"],
                source_authority=raw["source_authority"],
                write_authority=raw["write_authority"],
                deletion_authority=raw["deletion_authority"],
            )
            decision = close_work.classify_disposition(candidate)
            rendered.append(f"{raw['id']}|{dataclasses.asdict(decision)}")
        for raw in _fixture("lifecycle-matrix.json"):
            projection = close_work.project_lifecycle(**_inputs(raw))
            rendered.append(f"{raw['id']}|{dataclasses.asdict(projection)}")
        return "\n".join(rendered)

    first = run()
    second = run()
    assert first == second
    # A non-trivial corpus, so the equality is not vacuous.
    assert first.count("\n") >= 20, first.count("\n")


def test_every_result_code_has_an_asserted_trace() -> None:
    """No close-work outcome ships without a test that names it.

    Plan T1's Done-when clause requires every refusal to have an asserted
    zero-effect trace, and AC19 requires every case to assert the exact result.
    Reviewers kept re-discovering this one code at a time, so the invariant is
    mechanised here: a newly added result code fails this test until something
    asserts it, and the only permitted exceptions are the provably unreachable
    emitters named above.
    """
    codes = _result_codes(CLOSE_WORK_PATH.read_text(encoding="utf-8"))
    assert len(codes) > 80, f"code extraction looks broken: found {len(codes)}"

    searched = [
        ROOT / "packs/core/tests/skills/close-work",
        ROOT / "packs/core/tests/skills/work-loop",
        ROOT / "tests/roster",
        ROOT / "packs/core/.apm/skills/close-work/evals",
    ]
    # Three weaknesses this loop must not have. (1) This module is inside the
    # searched tree and names live codes in its own constants and comments, so
    # including its text would let the guard satisfy itself. It is excluded
    # entirely rather than by stripping one declaration. (2) A whole-file
    # substring test is satisfied by a bare comment, so membership is decided by
    # string *constants* recovered from the parsed source, never by prose.
    # (3) A fixture row's *input* fields are not evidence that anything asserts
    # the code they happen to spell. A sweep of every quoted token counted
    # `confirmation-mismatch` as covered purely because refusal-matrix.json
    # names a row `"id"`/`"event"` after it while asserting a different
    # `expected_code`, so both of its emitters shipped undriven. JSON membership
    # is therefore read only from the keys the drivers actually assert on.
    asserted: set[str] = set()
    scanned = 0
    for base in searched:
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".json"}:
                continue
            if path.resolve() == pathlib.Path(__file__).resolve():
                continue
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix == ".json":
                asserted |= _json_asserted_codes(text)
                continue
            try:
                parsed = ast.parse(text)
            except SyntaxError:  # pragma: no cover - corpus is syntactically valid
                continue
            for node in ast.walk(parsed):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    asserted.add(node.value)
    assert scanned > 40, f"corpus looks broken: scanned {scanned} files"

    # Two checks with different jobs; only the second is a control.
    #
    # The loop proves each exempt or terminal code is still *emitted* by the
    # module. That is a staleness check on this file's own constants — it would
    # pass whatever the corpus contained — not a control.
    #
    # The disjointness assertion after it is the actual positive control, and it
    # covers `_UNREACHABLE_BY_SUBSUMPTION` only. `_TERMINAL_MUTATED_CODES` cannot
    # serve as controls: they are legitimately asserted by the pack suite, so
    # their presence in `asserted` proves nothing about self-seeding.
    for seeded in _UNREACHABLE_BY_SUBSUMPTION | _TERMINAL_MUTATED_CODES:
        assert seeded in _result_codes(
            CLOSE_WORK_PATH.read_text(encoding="utf-8")
        ), f"{seeded} is not emitted by the module at all"
    assert _UNREACHABLE_BY_SUBSUMPTION.isdisjoint(asserted), (
        "corpus still seeds an exempt code: "
        f"{sorted(_UNREACHABLE_BY_SUBSUMPTION & asserted)}"
    )

    unasserted = sorted(c for c in codes if c not in asserted)
    assert unasserted == sorted(_UNREACHABLE_BY_SUBSUMPTION), unasserted

    # The allowlist must stay honest: each entry must still be emitted by the
    # module, so a deleted branch cannot leave a stale exemption behind.
    assert codes >= _UNREACHABLE_BY_SUBSUMPTION


def _declared_residue_vocabulary(source: str) -> set[str]:
    """Read the closed vocabulary from the module's own declaration.

    Coupled to the source rather than restated here, so renaming a token in
    `close_work.py` cannot leave this guard checking a stale set.
    """
    block = re.search(
        r"residual_evidence: ResidualHardlinkEvidence \| None = None\n(.*?)"
        r"    residue_state: str \| None = None",
        source,
        re.DOTALL,
    )
    assert block is not None, "residue_state declaration not found"
    tokens = set(re.findall(r'#\s+"([a-z-]+)"', block.group(1)))
    assert len(tokens) == 3, f"expected 3 declared tokens, found {sorted(tokens)}"
    return tokens


def test_every_result_reporting_residue_names_its_identity() -> None:
    """AC11: if a result reports recovery residue, it must say whose inode it is.

    Keyed on *reporting residue*, not on a list of code names. A terminal
    mutated failure added later under a new name is therefore still caught,
    which a name-filtered guard would skip. `recovery_residue` presence is
    statically decidable from the call site; the emptiness of a conditional
    tuple like `(target,) if original_removed else ()` is not, so this
    deliberately does not test that.
    """
    source = CLOSE_WORK_PATH.read_text(encoding="utf-8")
    vocabulary = _declared_residue_vocabulary(source)
    seen = 0
    for node in ast.walk(ast.parse(source)):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "DeletionResult"
        ):
            continue
        keywords = {kw.arg: kw.value for kw in node.keywords}
        # A call reports residue when it passes recovery_residue (4th
        # positional or keyword) or residual_evidence, which this module only
        # ever passes by keyword. A `len(node.args) >= 5` term would be dead:
        # it is strictly subsumed by the `>= 4` test below.
        reports_residue = (
            len(node.args) >= 4
            or "recovery_residue" in keywords
            or "residual_evidence" in keywords
        )
        if not reports_residue:
            continue
        seen += 1
        state = keywords.get("residue_state")
        assert state is not None, (
            f"line {node.lineno}: reports residue but names no residue_state"
        )
        assert isinstance(state, ast.Constant), f"line {node.lineno}: not a literal"
        assert state.value in vocabulary, (
            f"line {node.lineno}: {state.value!r} outside the declared vocabulary "
            f"{sorted(vocabulary)}"
        )
    # Floor guards against the matcher silently matching nothing; the per-site
    # assertions above are the contract.
    assert seen >= 8, f"expected at least 8 residue-reporting sites, found {seen}"


def test_close_work_declares_only_filesystem_boundaries() -> None:
    """AC20a's declared boundaries are pinned as an exact set, not a substring.

    A substring check passes when a boundary is added, and passes vacuously when
    the declaration is deleted. Both are the failure this pins: widening to
    `network_fetch` or dropping line 6 must redden.
    """
    expected = {"filesystem_read_untrusted", "filesystem_write"}
    paths = {
        "canonical": SOURCE_SKILL_PATH,
        ".claude": ROOT / ".claude/skills/close-work/SKILL.md",
        ".agents": ROOT / ".agents/skills/close-work/SKILL.md",
    }
    for label, path in paths.items():
        assert path.is_file(), label
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        assert "metadata:" in frontmatter, label
        assert _declared_boundaries(frontmatter) == expected, label


def test_close_work_source_and_adapter_contract_declare_minimal_authority() -> None:
    """Canonical tool authority plus the codex adapter-contract stanza.

    Projected-frontmatter parity is the self-host drift gate's job, not this
    test's; the canonical `boundaries` set is pinned by
    `test_close_work_declares_only_filesystem_boundaries`.
    """
    expected = {"Read", "Write", "Edit", "Bash"}
    forbidden = {
        "Agent",
        "WebFetch",
        "WebSearch",
        "Browser",
        "MCP",
        "Credential",
        "ExternalAdapter",
    }

    body = SOURCE_SKILL_PATH.read_text(encoding="utf-8")
    frontmatter = body.split("---", 2)[1]
    match = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, re.MULTILINE)
    assert match is not None
    declared = set(match.group(1).split())
    assert declared == expected
    assert declared.isdisjoint(forbidden)

    pack = tomllib.loads((ROOT / "packs/core/pack.toml").read_text(encoding="utf-8"))
    assert "close-work" in pack["pack"]["evals"]["skills"]
    contract = tomllib.loads(
        (ROOT / "contracts/adapter.toml").read_text(encoding="utf-8")
    )
    codex_skill = next(
        projection
        for projection in contract["adapter"]["codex"]["projection"]
        if projection["primitive"] == "skill"
    )
    assert codex_skill == {
        "primitive": "skill",
        "mode": "direct-directory",
        "target-path": ".agents/skills/",
        "on-conflict": "prompt-then-preserve",
    }


def test_close_work_construction_suite_is_in_local_and_ci_pack_gates() -> None:
    """The destructive-boundary suite remains live in both normal pack gates."""
    suite = "packs/core/tests/skills/close-work/"
    assert suite in (ROOT / "Makefile").read_text(encoding="utf-8")
    assert suite in (
        ROOT / ".github/workflows/catalogue-tooling-ci-gates.yml"
    ).read_text(encoding="utf-8")


def test_projected_file_safety_matches_the_agentbundle_canonical() -> None:
    """Cross-tree parity: the pack copy is byte-identical to the engine helper."""
    projected = ROOT / "packs/core/.apm/skills/close-work/scripts/file_safety.py"
    assert projected.read_bytes() == FILE_SAFETY_PATH.read_bytes()


def test_wave4_spec_index_plan_and_workspace_lifecycle_are_aligned() -> None:
    spec_path = (
        ROOT / "docs/specs/close-work-extraction-and-immediate-disposition/spec.md"
    )
    plan_path = spec_path.with_name("plan.md")
    spec_status = next(
        line.removeprefix("- **Status:** ")
        for line in spec_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- **Status:** ")
    )
    plan_status = next(
        line.removeprefix("- **Status:** ")
        for line in plan_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("- **Status:** ")
    )
    index_row = next(
        line
        for line in (ROOT / "docs/specs/README.md")
        .read_text(encoding="utf-8")
        .splitlines()
        if "close-work-extraction-and-immediate-disposition/" in line
    )
    workspace = tomllib.loads((ROOT / "workspace.toml").read_text(encoding="utf-8"))
    work = workspace["ini-002"]["work"]
    locator = "docs/specs/close-work-extraction-and-immediate-disposition/spec.md"
    memberships = {
        state
        for state in ("active", "queue", "shipped")
        if any(
            isinstance(item, dict) and item.get("path") == locator
            for item in work[state]
        )
    }

    expected = {
        "Draft": ("Drafting", {"queue"}),
        "Approved": ("Approved", {"queue"}),
        "Implementing": ("Executing", {"active"}),
        "Shipped": ("Done", {"shipped"}),
    }
    assert spec_status in expected
    assert plan_status == expected[spec_status][0]
    assert (
        f"| {spec_status} | RFC-0096; Waves 1–3 (Shipped); "
        "Waves 5–7 (live dependencies) |"
    ) in index_row
    assert memberships == expected[spec_status][1]

    # A shipped spec carries no unchecked acceptance criterion; a separable
    # follow-on lives outside the AC list with its own owner.
    if spec_status == "Shipped":
        assert "- [ ] **AC" not in spec_path.read_text(encoding="utf-8")

    # Exactly one membership row, RFC-pinned, with no hard dependency.
    rows = [
        item
        for item in work[next(iter(expected[spec_status][1]))]
        if isinstance(item, dict) and item.get("path") == locator
    ]
    assert len(rows) == 1
    assert rows[0]["source"] == {
        "mode": "repo-origin",
        "ref": "docs/rfc/0096-portable-delivery-artifact-lifecycle.md",
        "revision": "6e984d67b583b36798efddbb2717ce5784572a49",
    }
    assert rows[0]["needs"] == []
