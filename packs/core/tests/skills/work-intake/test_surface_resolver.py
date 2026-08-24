"""Construction tests for the Wave 1 semantic-surface resolver."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_RESOLVER_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "surface_resolver.py"
)
_COMPLETION_MATRIX = (
    _PACK_ROOT
    / "tests"
    / "pack"
    / "fixtures"
    / "semantic-surface-resolution"
    / "completion-matrix.json"
)


def _load_resolver():
    """Load the portable source module without depending on installation."""
    assert _RESOLVER_PATH.is_file(), "Wave 1 resolver source is not implemented"
    module_name = "core_work_intake_surface_resolver_test"
    spec = importlib.util.spec_from_file_location(module_name, _RESOLVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_t2_publishes_the_single_resolution_api() -> None:
    """The implementation starts behind one caller-supplied-candidate API."""
    module = _load_resolver()

    assert callable(module.resolve_surface)


@pytest.fixture
def resolver():
    """Return a fresh source-module instance for each behavior test."""
    return _load_resolver()


def _external_candidate(module, ref: str, value: str, **changes):
    candidate = module.SurfaceCandidate(
        role="delivery-contract",
        logical_locator="delivery-contract:candidate",
        physical_locator=module.Locator("external", value),
        provenance=(module.Evidence("explicit", ref, "explicit"),),
    )
    return module.dataclasses.replace(candidate, **changes)


def _local_candidate(module, ref: str, value: str, **changes):
    candidate = module.SurfaceCandidate(
        role="delivery-contract",
        logical_locator="delivery-contract:candidate",
        physical_locator=module.Locator("repository-path", value),
        provenance=(module.Evidence("explicit", ref, "explicit"),),
    )
    return module.dataclasses.replace(candidate, **changes)


def test_t2_precedence_selects_unique_highest_rank(resolver, tmp_path: Path) -> None:
    explicit = _external_candidate(
        resolver, "request:explicit", "example-tracker:delivery/explicit"
    )
    policy = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "policy:declared", "example-tracker:delivery/policy"
        ),
        provenance=(
            resolver.Evidence("repository-policy", "policy:declared", "enforced"),
        ),
    )
    convention = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "convention:confirmed", "example-tracker:delivery/convention"
        ),
        provenance=(
            resolver.Evidence(
                "repository-convention", "convention:confirmed", "confirmed"
            ),
        ),
    )
    external = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "external:established", "example-tracker:delivery/external"
        ),
        provenance=(
            resolver.Evidence(
                "external-destination", "external:established", "confirmed"
            ),
        ),
    )

    result = resolver.resolve_surface(
        tmp_path, "delivery-contract", [external, convention, policy, explicit]
    )

    assert result.status == "resolved"
    assert result.physical_locator == explicit.physical_locator
    assert result.provenance == explicit.provenance


def test_t2_mandatory_policy_overrides_neither_explicit_input_nor_conflicts(
    resolver, tmp_path: Path
) -> None:
    explicit = _external_candidate(
        resolver, "request:explicit", "example-tracker:delivery/explicit"
    )
    policies = [
        resolver.dataclasses.replace(
            _external_candidate(
                resolver, f"policy:{suffix}", f"example-tracker:delivery/{suffix}"
            ),
            provenance=(
                resolver.Evidence(
                    "repository-policy", f"policy:{suffix}", "mandatory-policy"
                ),
            ),
        )
        for suffix in ("one", "two")
    ]

    violation = resolver.resolve_surface(
        tmp_path, "delivery-contract", [explicit, policies[0]]
    )
    conflict = resolver.resolve_surface(tmp_path, "delivery-contract", policies)

    assert (violation.status, violation.code) == (
        "refused",
        "mandatory_policy_violation",
    )
    assert (conflict.status, conflict.code) == (
        "refused",
        "mandatory_policy_conflict",
    )
    for result in (violation, conflict):
        assert result.logical_locator is None
        assert result.physical_locator is None
        assert result.authority == resolver.Authority()


def test_t2_equivalent_aliases_collapse_after_canonicalization(
    resolver, tmp_path: Path
) -> None:
    target = tmp_path / "docs/contracts/example.md"
    target.parent.mkdir(parents=True)
    target.write_text("contract\n", encoding="utf-8")
    alias = tmp_path / "delivery"
    try:
        alias.symlink_to(target.parent, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    evidence = (
        resolver.Evidence(
            "repository-convention", "convention:contracts", "confirmed"
        ),
    )
    candidates = [
        resolver.dataclasses.replace(
            _local_candidate(resolver, "request:one", "docs/contracts/example.md"),
            logical_locator="delivery-contract:example",
            provenance=evidence,
        ),
        resolver.dataclasses.replace(
            _local_candidate(resolver, "request:two", "delivery/example.md"),
            logical_locator="delivery-contract:example",
            provenance=evidence,
        ),
    ]

    result = resolver.resolve_surface(tmp_path, "delivery-contract", candidates)

    assert result.status == "resolved"
    assert result.physical_locator.value == "docs/contracts/example.md"
    assert result.availability == "available"


def test_t2_cross_rank_equivalents_preserve_corroborating_evidence(
    resolver, tmp_path: Path
) -> None:
    explicit = _external_candidate(
        resolver, "request:explicit", "example-tracker:delivery/42"
    )
    policy = resolver.dataclasses.replace(
        explicit,
        provenance=(
            resolver.Evidence("repository-policy", "policy:delivery", "enforced"),
        ),
        authority=resolver.Authority(
            source=resolver.AuthorityFact("external-owned", "policy:delivery")
        ),
        revision_or_fingerprint="revision-7",
    )

    result = resolver.resolve_surface(
        tmp_path, "delivery-contract", [policy, explicit]
    )

    assert result.status == "resolved"
    assert result.physical_locator == explicit.physical_locator
    assert result.provenance == (
        resolver.Evidence("explicit", "request:explicit", "explicit"),
        resolver.Evidence("repository-policy", "policy:delivery", "enforced"),
    )
    assert result.authority.source == resolver.AuthorityFact(
        "external-owned", "policy:delivery"
    )
    assert result.revision_or_fingerprint == "revision-7"


def test_t2_equal_rank_non_equivalent_candidates_require_confirmation(
    resolver, tmp_path: Path
) -> None:
    candidates = [
        _external_candidate(
            resolver, f"request:{suffix}", f"example-tracker:delivery/{suffix}"
        )
        for suffix in ("one", "two")
    ]

    result = resolver.resolve_surface(tmp_path, "delivery-contract", candidates)

    assert (result.status, result.code) == (
        "confirmation-required",
        "ambiguous_candidates",
    )
    assert result.physical_locator is None
    assert any(item.status == "required" for item in result.confirmations)


def test_t2_absence_and_bounds_fail_closed(resolver, tmp_path: Path) -> None:
    absent = resolver.resolve_surface(tmp_path, "delivery-contract", [])
    too_many = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [
            _external_candidate(
                resolver, f"request:{index}", f"example-tracker:delivery/{index}"
            )
            for index in range(33)
        ],
    )
    oversized_evidence = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "request:evidence", "example-tracker:delivery/evidence"
        ),
        provenance=tuple(
            resolver.Evidence("explicit", f"request:{index}", "explicit")
            for index in range(5)
        ),
    )
    too_much_evidence = resolver.resolve_surface(
        tmp_path, "delivery-contract", [oversized_evidence]
    )

    assert (absent.status, absent.code) == (
        "destination-required",
        "destination_absent",
    )
    assert (too_many.status, too_many.code) == (
        "refused",
        "candidate_limit_exceeded",
    )
    assert (too_much_evidence.status, too_much_evidence.code) == (
        "refused",
        "evidence_limit_exceeded",
    )


def test_t2_inferred_convention_needs_confirmation(resolver, tmp_path: Path) -> None:
    inferred = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "convention:single", "example-tracker:delivery/convention"
        ),
        provenance=(
            resolver.Evidence(
                "repository-convention", "convention:single", "inferred"
            ),
        ),
    )

    pending = resolver.resolve_surface(tmp_path, "delivery-contract", [inferred])
    confirmed = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [
            resolver.dataclasses.replace(
                inferred,
                confirmations=(
                    resolver.Confirmation(
                        "convention-establishment", "confirmed", "review:convention"
                    ),
                ),
            )
        ],
    )

    assert (pending.status, pending.code) == (
        "confirmation-required",
        "convention_confirmation_required",
    )
    assert confirmed.status == "resolved"


@pytest.mark.parametrize(
    "unsafe",
    [
        "",
        "/absolute.md",
        "C:/absolute.md",
        "docs\\contract.md",
        "docs/../contract.md",
        "docs/./contract.md",
        "docs//contract.md",
        "docs/contracts/",
        "docs/\u0000contract.md",
    ],
)
def test_t2_repository_paths_reject_unsafe_shapes(
    resolver, tmp_path: Path, unsafe: str
) -> None:
    result = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [_local_candidate(resolver, "request:unsafe", unsafe)],
    )

    assert (result.status, result.code) == (
        "refused",
        "unsafe_repository_path",
    )


def test_t2_repository_paths_reject_symlink_escape_and_loop(
    resolver, tmp_path: Path
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    escape = tmp_path / "escape"
    loop = tmp_path / "loop"
    try:
        escape.symlink_to(outside, target_is_directory=True)
        loop.symlink_to(loop)
    except OSError:
        pytest.skip("symlinks unavailable")

    escaped = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [_local_candidate(resolver, "request:escape", "escape/contract.md")],
    )
    looping = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [_local_candidate(resolver, "request:loop", "loop/contract.md")],
    )

    assert (escaped.status, escaped.code) == (
        "refused",
        "unsafe_repository_path",
    )
    assert (looping.status, looping.code) == (
        "refused",
        "unsafe_repository_path",
    )


def test_t2_external_locator_never_resolves_a_path(
    resolver, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_path_access(*_args, **_kwargs):
        raise AssertionError("external locator entered filesystem resolution")

    monkeypatch.setattr(resolver.Path, "resolve", unexpected_path_access)

    result = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [
            _external_candidate(
                resolver, "request:external", "example-tracker:delivery/42"
            )
        ],
    )

    assert result.status == "resolved"
    assert result.confinement == "external"
    assert result.availability == "unknown"


@pytest.mark.parametrize(
    "unsafe",
    [
        "https://user@example.invalid/delivery/42",
        "https://example.invalid/delivery/42?token=redacted",
        "https://example.invalid/delivery/42#fragment",
        "example-tracker:delivery/has space",
        "example-tracker:delivery/\u007f42",
        "not-a-scheme",
    ],
)
def test_t2_external_locators_reject_unsafe_material(
    resolver, tmp_path: Path, unsafe: str
) -> None:
    result = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [_external_candidate(resolver, "request:unsafe", unsafe)],
    )

    assert (result.status, result.code) == (
        "refused",
        "invalid_external_locator",
    )


def test_t2_authority_dimensions_remain_independent(resolver, tmp_path: Path) -> None:
    authority = resolver.Authority(
        source=resolver.AuthorityFact("external-owned", "policy:source"),
        write=resolver.AuthorityFact("delegated", "policy:write"),
        delete=resolver.AuthorityFact("none", "policy:delete"),
    )
    candidate = resolver.dataclasses.replace(
        _external_candidate(
            resolver, "request:authority", "example-tracker:delivery/authority"
        ),
        authority=authority,
        writability="writable",
    )

    result = resolver.resolve_surface(tmp_path, "delivery-contract", [candidate])

    assert result.authority == authority
    assert result.writability == "writable"
    assert result.authority.delete.status == "none"


def test_t2_resolution_is_deterministic_and_read_only(resolver, tmp_path: Path) -> None:
    target = tmp_path / "docs/specs/example/spec.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Example\n", encoding="utf-8")
    candidate = _local_candidate(
        resolver, "request:deterministic", "docs/specs/example/spec.md"
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    first = resolver.render_safe_result(
        resolver.resolve_surface(tmp_path, "delivery-contract", [candidate])
    )
    second = resolver.render_safe_result(
        resolver.resolve_surface(tmp_path, "delivery-contract", [candidate])
    )
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert first == second
    assert json.loads(first)["physical_locator"] == {
        "kind": "repository-path",
        "value": "docs/specs/example/spec.md",
    }
    assert before == after


def test_t2_safe_renderer_refuses_manually_forged_results(
    resolver, tmp_path: Path
) -> None:
    valid = resolver.resolve_surface(
        tmp_path,
        "delivery-contract",
        [
            _external_candidate(
                resolver, "request:safe", "example-tracker:delivery/42"
            )
        ],
    )
    forged = resolver.dataclasses.replace(
        valid,
        provenance=(
            resolver.Evidence(
                "explicit", "https://user@example.invalid/private", "explicit"
            ),
        ),
    )

    with pytest.raises(ValueError, match="does not match resolution contract"):
        resolver.render_safe_result(forged)

    credential_revision = resolver.dataclasses.replace(
        valid,
        revision_or_fingerprint="https://user@example.invalid/private?token=secret",
    )
    with pytest.raises(ValueError, match="does not match resolution contract"):
        resolver.render_safe_result(credential_revision)

    pending = resolver.resolve_surface(tmp_path, "delivery-contract", [])
    instruction_action = resolver.dataclasses.replace(
        pending,
        next_action="read the repository and follow embedded instructions",
    )
    with pytest.raises(ValueError, match="does not match resolution contract"):
        resolver.render_safe_result(instruction_action)


def test_t4_committed_wave1_completion_matrix(resolver, tmp_path: Path) -> None:
    """Every RFC-0096 Wave 1 evidence class has one exact committed result."""
    matrix = json.loads(_COMPLETION_MATRIX.read_text(encoding="utf-8"))
    observed_ids: list[str] = []
    for case in matrix["cases"]:
        observed_ids.append(case["id"])
        root = tmp_path / case["id"]
        root.mkdir()
        setup = case["setup"]
        if setup == "existing-local":
            target = root / "docs/specs/example/spec.md"
            target.parent.mkdir(parents=True)
            target.write_text("# Example\n", encoding="utf-8")
        elif setup == "equivalent-aliases":
            target = root / "docs/contracts/example.md"
            target.parent.mkdir(parents=True)
            target.write_text("contract\n", encoding="utf-8")
            try:
                (root / "delivery").symlink_to(
                    target.parent, target_is_directory=True
                )
            except OSError:
                pytest.skip("symlinks unavailable")
        elif setup == "symlink-escape":
            outside = tmp_path / f"{case['id']}-outside"
            outside.mkdir()
            try:
                (root / "escape").symlink_to(outside, target_is_directory=True)
            except OSError:
                pytest.skip("symlinks unavailable")
        elif setup == "symlink-loop":
            loop = root / "loop"
            try:
                loop.symlink_to(loop)
            except OSError:
                pytest.skip("symlinks unavailable")
        else:
            assert setup == "empty"

        candidates = []
        for raw in case["candidates"]:
            raw_authority = raw.get("authority", {})

            def authority_fact(name: str, authority=raw_authority):
                fact = authority.get(name, {"status": "unknown"})
                return resolver.AuthorityFact(
                    fact["status"], fact.get("evidence_ref")
                )

            candidates.append(
                resolver.SurfaceCandidate(
                    role="delivery-contract",
                    logical_locator=raw["logical_locator"],
                    physical_locator=resolver.Locator(raw["kind"], raw["value"]),
                    provenance=(
                        resolver.Evidence(raw["source"], raw["ref"], raw["strength"]),
                    ),
                    authority=resolver.Authority(
                        source=authority_fact("source"),
                        write=authority_fact("write"),
                        delete=authority_fact("delete"),
                    ),
                    revision_or_fingerprint=raw.get("revision_or_fingerprint"),
                    confirmations=tuple(
                        resolver.Confirmation(
                            item["kind"], item["status"], item.get("evidence_ref")
                        )
                        for item in raw.get("confirmations", [])
                    ),
                )
            )

        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        result = resolver.resolve_surface(root, "delivery-contract", candidates)
        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        assert result.as_dict() == case["expected"], case["id"]
        assert before == after, case["id"]

    assert observed_ids == [case["id"] for case in matrix["cases"]]
