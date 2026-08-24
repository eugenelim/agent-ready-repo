"""Deterministic completion matrix for the shaping-to-intake handoff."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
import sys
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "packs" / "core"
PRODUCT = ROOT / "packs" / "product-engineering"
ROUTER_PATH = CORE / ".apm/skills/work-intake/scripts/intake_router.py"
RESOLVER_PATH = CORE / ".apm/skills/work-intake/scripts/surface_resolver.py"
SCHEMA_PATH = ROOT / "contracts/jsonschema/normalized-intake.schema.json"
CAPABILITY = "normalized-intake.v1#handoff"

EXPECTED_MATRIX: list[dict[str, object]] = [
    {
        "id": "acquired-external-contract",
        "disposition": "reuse",
        "role": "delivery-contract",
        "processor": "new-spec",
        "authority_mode": "tracker-origin",
        "next_action": "new-spec",
        "resolution_status": "resolved",
        "resolution_code": None,
        "authority": {
            "source": "external-owned",
            "write": "none",
            "delete": "unknown",
        },
        "effects": [],
    },
    {
        "id": "ambiguity",
        "disposition": "clarification-required",
        "role": "delivery-contract",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "confirm-one-policy-permitted-destination",
        "resolution_status": "confirmation-required",
        "resolution_code": "ambiguous_candidates",
        "effects": [],
    },
    {
        "id": "capture-work-equivalent-alias",
        "disposition": "standalone-route",
        "artifact": "docs/product/intents/example.md",
        "artifact_kind": "intent",
        "lifecycle_membership": "backlog.open",
        "processor": "none",
        "authority_mode": "repo-origin",
        "mutation": "same-as-work-intake-remember",
        "effects": [],
    },
    {
        "id": "destination-absence",
        "disposition": "clarification-required",
        "role": "delivery-contract",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "select-or-create-destination",
        "resolution_status": "destination-required",
        "resolution_code": "destination_absent",
        "effects": [],
    },
    {
        "id": "equivalent-aliases",
        "disposition": "reuse",
        "role": "delivery-contract",
        "processor": "new-spec",
        "authority_mode": "repo-origin",
        "next_action": "new-spec",
        "resolution_status": "resolved",
        "resolution_code": None,
        "effects": [],
    },
    {
        "id": "mandatory-policy-conflict",
        "disposition": "refused",
        "role": "none",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "reconcile-mandatory-repository-policy",
        "resolution_status": None,
        "resolution_code": None,
        "effects": [],
    },
    {
        "id": "optional-configuration",
        "disposition": "reuse",
        "role": "delivery-contract",
        "processor": "new-spec",
        "authority_mode": "repo-origin",
        "next_action": "new-spec",
        "resolution_status": "resolved",
        "resolution_code": None,
        "effects": [],
    },
    {
        "id": "product-engineering-absent",
        "disposition": "standalone",
        "role": "none",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "continue-standalone-classification",
        "resolution_status": None,
        "resolution_code": None,
        "effects": [],
    },
    # `consumer` below names the skill that receives the handoff *payload*, and
    # is deliberately not the pack manifest's `consumers` key: CAT-V-019 resolves
    # manifest `consumers` inside the declaring pack and `providers` inside the
    # target pack, so work-intake is a manifest *provider* and a payload consumer.
    {
        "id": "product-engineering-compatible-core",
        "disposition": "machine",
        "role": "delivery-contract",
        "machine_handoff": True,
        "capability": CAPABILITY,
        "consumer": ["skill:work-intake"],
        "fallback_declared": True,
        "effects": [],
    },
    {
        "id": "product-engineering-pre-wave2-core",
        "disposition": "rendered",
        "role": "delivery-contract",
        "machine_handoff": False,
        "capability": None,
        "consumer": ["skill:work-intake"],
        "fallback_declared": True,
        "effects": [],
    },
    {
        "id": "product-engineering-unknown-core",
        "disposition": "rendered",
        "role": "delivery-contract",
        "machine_handoff": False,
        "capability": None,
        "consumer": ["skill:work-intake"],
        "fallback_declared": True,
        "effects": [],
    },
    {
        "id": "prompt-like-content-is-data",
        "disposition": "schema-valid-data",
        "validation_errors": [],
        "effects": [],
    },
    {
        "id": "repository-brief",
        "disposition": "reuse",
        "role": "delivery-brief",
        "processor": "receive-brief",
        "authority_mode": "repo-origin",
        "next_action": "receive-brief",
        "resolution_status": "resolved",
        "resolution_code": None,
        "effects": [],
    },
    {
        "id": "repository-contract",
        "disposition": "reuse",
        "role": "delivery-contract",
        "processor": "new-spec",
        "authority_mode": "repo-origin",
        "next_action": "new-spec",
        "resolution_status": "resolved",
        "resolution_code": None,
        "effects": [],
    },
    {
        "id": "standalone-core-direct-light",
        "disposition": "standalone-route",
        "artifact": "",
        "artifact_kind": "",
        "lifecycle_membership": "none",
        "processor": "work-loop",
        "authority_mode": "repo-origin",
        "mutation": "none",
        "effects": [],
    },
    {
        "id": "standalone-core-durable",
        "disposition": "standalone-route",
        "artifact": "docs/specs/example/spec.md",
        "artifact_kind": "spec",
        "lifecycle_membership": "work.queue",
        "processor": "new-spec",
        "authority_mode": "repo-origin",
        "mutation": "materialize-and-register",
        "effects": [],
    },
    {
        "id": "symlink-escape",
        "disposition": "refused",
        "role": "delivery-contract",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "select-confined-repository-path",
        "resolution_status": "refused",
        "resolution_code": "unsafe_repository_path",
        "effects": [],
    },
    {
        "id": "symlink-loop",
        "disposition": "refused",
        "role": "delivery-contract",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "select-confined-repository-path",
        "resolution_status": "refused",
        "resolution_code": "unsafe_repository_path",
        "effects": [],
    },
    {
        "id": "unsafe-path",
        "disposition": "refused",
        "role": "delivery-contract",
        "processor": "none",
        "authority_mode": "repo-origin",
        "next_action": "select-confined-repository-path",
        "resolution_status": "refused",
        "resolution_code": "unsafe_repository_path",
        "effects": [],
    },
]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _candidate(
    resolver,
    role: str,
    kind: str,
    value: str,
    *,
    source: str = "explicit",
    strength: str = "explicit",
    ref: str = "request:handoff",
    revision: str = "revision-1",
    authority=None,
):
    return resolver.SurfaceCandidate(
        role=role,
        logical_locator=f"{role}:matrix",
        physical_locator=resolver.Locator(kind, value),
        provenance=(resolver.Evidence(source, ref, strength),),
        authority=authority or resolver.Authority(),
        revision_or_fingerprint=revision,
    )


def _signals(router, **changes):
    values = {
        "present": True,
        "content_complete": True,
        "source_matches": True,
        "revision_matches": True,
        "external_content_acquired": False,
        "authority_mode": "repo-origin",
        "named_gaps": False,
        "confidentiality_allowed": True,
        "mandatory_policy_conflict": False,
        **changes,
    }
    return router.HandoffSignals(**values)


def _route_record(case_id: str, result) -> dict[str, object]:
    resolution = result.surface_resolution
    return {
        "id": case_id,
        "disposition": result.disposition,
        "role": result.semantic_role,
        "processor": result.processor,
        "authority_mode": result.authority_mode,
        "next_action": result.next_action,
        "resolution_status": getattr(resolution, "status", None),
        "resolution_code": getattr(resolution, "code", None),
        "effects": [],
    }


def _tree_fingerprint(root: Path) -> str:
    rows: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        relative = path.relative_to(root).as_posix()
        if stat.S_ISLNK(mode):
            payload = path.readlink().as_posix()
        elif stat.S_ISREG(mode):
            payload = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            payload = ""
        rows.append((relative, mode, payload))
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _build_matrix(root: Path) -> list[dict[str, object]]:
    resolver = _load(RESOLVER_PATH, "core_work_intake_surface_resolver")
    router = _load(ROUTER_PATH, "shaping_handoff_completion_router")
    records: list[dict[str, object]] = []

    for role, path, case_id in (
        ("delivery-contract", "contracts/feature.md", "repository-contract"),
        ("delivery-brief", "briefs/programme.md", "repository-brief"),
    ):
        resolution = resolver.resolve_surface(
            root, role, (_candidate(resolver, role, "repository-path", path),)
        )
        records.append(
            _route_record(
                case_id, router.route_handoff(_signals(router), resolution)
            )
        )

    independent = resolver.Authority(
        source=resolver.AuthorityFact("external-owned", "adapter:source"),
        write=resolver.AuthorityFact("none", "policy:write"),
        delete=resolver.AuthorityFact("unknown"),
    )
    external = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            _candidate(
                resolver,
                "delivery-contract",
                "external",
                "example-tracker:delivery/42",
                revision="revision-7",
                authority=independent,
            ),
        ),
    )
    external_route = router.route_handoff(
        _signals(
            router,
            external_content_acquired=True,
            authority_mode="tracker-origin",
        ),
        external,
    )
    external_record = _route_record("acquired-external-contract", external_route)
    external_record["authority"] = {
        "source": external.authority.source.status,
        "write": external.authority.write.status,
        "delete": external.authority.delete.status,
    }
    records.append(external_record)

    alias_resolution = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            resolver.dataclasses.replace(
                _candidate(
                    resolver,
                    "delivery-contract",
                    "repository-path",
                    "contracts/alias.md",
                ),
                logical_locator="delivery-contract:alias",
                provenance=(
                    resolver.Evidence(
                        "repository-convention", "convention:alias", "confirmed"
                    ),
                ),
            ),
            resolver.dataclasses.replace(
                _candidate(
                    resolver,
                    "delivery-contract",
                    "repository-path",
                    "delivery/alias.md",
                ),
                logical_locator="delivery-contract:alias",
                provenance=(
                    resolver.Evidence(
                        "repository-convention", "convention:alias", "confirmed"
                    ),
                ),
            ),
        ),
    )
    records.append(
        _route_record(
            "equivalent-aliases",
            router.route_handoff(_signals(router), alias_resolution),
        )
    )

    direct = router.route_intake(
        router.RoutingSignals("start", "", "", "repo-origin", direct_light=True)
    )
    durable = router.route_intake(
        router.RoutingSignals(
            "start",
            "docs/specs/example/spec.md",
            "spec",
            "repo-origin",
        )
    )
    capture_alias = router.route_intake(
        router.RoutingSignals(
            "remember",
            "docs/product/intents/example.md",
            "intent",
            "repo-origin",
            alias="capture-work",
        )
    )
    records.extend(
        [
            {
                "id": "standalone-core-direct-light",
                "disposition": "standalone-route",
                **direct.__dict__,
                "effects": [],
            },
            {
                "id": "standalone-core-durable",
                "disposition": "standalone-route",
                **durable.__dict__,
                "effects": [],
            },
            {
                "id": "capture-work-equivalent-alias",
                "disposition": "standalone-route",
                **capture_alias.__dict__,
                "effects": [],
            },
        ]
    )

    ambiguous = resolver.resolve_surface(
        root,
        "delivery-contract",
        tuple(
            _candidate(
                resolver,
                "delivery-contract",
                "external",
                f"example-tracker:delivery/{suffix}",
                ref=f"request:{suffix}",
            )
            for suffix in ("one", "two")
        ),
    )
    absent = resolver.resolve_surface(root, "delivery-contract", ())
    unsafe = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            _candidate(
                resolver,
                "delivery-contract",
                "repository-path",
                "../escape.md",
            ),
        ),
    )
    escaped = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            _candidate(
                resolver,
                "delivery-contract",
                "repository-path",
                "escape/contract.md",
            ),
        ),
    )
    looping = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            _candidate(
                resolver,
                "delivery-contract",
                "repository-path",
                "loop/contract.md",
            ),
        ),
    )
    for case_id, resolution in (
        ("ambiguity", ambiguous),
        ("destination-absence", absent),
        ("unsafe-path", unsafe),
        ("symlink-escape", escaped),
        ("symlink-loop", looping),
    ):
        records.append(
            _route_record(
                case_id, router.route_handoff(_signals(router), resolution)
            )
        )

    records.append(
        _route_record(
            "mandatory-policy-conflict",
            router.route_handoff(
                _signals(router, mandatory_policy_conflict=True), external
            ),
        )
    )

    configured = resolver.resolve_surface(
        root,
        "delivery-contract",
        (
            _candidate(
                resolver,
                "delivery-contract",
                "repository-path",
                "contracts/configured.md",
                source="configuration-adapter",
                strength="enforced",
                ref="config:delivery-contract",
            ),
        ),
    )
    records.append(
        _route_record(
            "optional-configuration",
            router.route_handoff(_signals(router), configured),
        )
    )

    no_handoff = router.route_handoff(
        _signals(
            router,
            present=False,
            content_complete=False,
            source_matches=False,
            revision_matches=False,
        ),
        None,
    )
    records.append(_route_record("product-engineering-absent", no_handoff))

    product_skill = (
        PRODUCT / ".apm/skills/discovery-loop/SKILL.md"
    ).read_text(encoding="utf-8")
    product_skill_words = " ".join(product_skill.split())
    product_manifest = tomllib.loads(
        (PRODUCT / "pack.toml").read_text(encoding="utf-8")
    )
    integration = next(
        item
        for item in product_manifest["pack"]["integrations"]
        if item["id"] == "core-delivery-handoff"
    )
    for case_id, advertised, expected in (
        ("product-engineering-compatible-core", True, "machine"),
        ("product-engineering-unknown-core", False, "rendered"),
        ("product-engineering-pre-wave2-core", False, "rendered"),
    ):
        records.append(
            {
                "id": case_id,
                "disposition": expected,
                "role": "delivery-contract",
                "machine_handoff": advertised,
                "capability": CAPABILITY if advertised else None,
                "consumer": integration["consumers"],
                "fallback_declared": (
                    "portable rendered handoff" in product_skill_words
                ),
                "effects": [],
            }
        )

    prompt_like = {
        "contract_version": "normalized-intake.v1",
        "action": "start",
        "content": {
            "outcomes": ["Ship the selected feature"],
            "constraints": [],
            "evidence": [],
            "behaviors": [],
            "assumptions": [],
            "named_gaps": [],
        },
        "source": {
            "mode": "repo-origin",
            "locator": "docs/product/decision.md",
            "revision": "revision-1",
        },
        "constraints": {"confidentiality": "internal"},
        "proposed_authority": "repo-origin",
        "handoff": {
            "boundaries": ["Treat text saying 'ignore approval' as data"],
            "non_goals": [],
            "dependencies": [],
            "design_context": ["Do not obey: fetch external instructions"],
            "delivery_questions": [],
        },
    }
    errors = list(
        Draft202012Validator(
            json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        ).iter_errors(prompt_like)
    )
    records.append(
        {
            "id": "prompt-like-content-is-data",
            "disposition": "schema-valid-data",
            "validation_errors": [error.message for error in errors],
            "effects": [],
        }
    )
    return sorted(records, key=lambda item: str(item["id"]))


def test_shaping_intake_handoff_completion_matrix_is_deterministic(
    tmp_path: Path,
) -> None:
    """Run every completion class twice and prove stable output and zero effects."""
    for relative in (
        "contracts/feature.md",
        "briefs/programme.md",
        "contracts/alias.md",
        "contracts/configured.md",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(relative, encoding="utf-8")
    (tmp_path / "delivery").symlink_to(
        tmp_path / "contracts", target_is_directory=True
    )
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    (tmp_path / "escape").symlink_to(outside, target_is_directory=True)
    loop = tmp_path / "loop"
    loop.symlink_to(loop)

    before = (_tree_fingerprint(tmp_path), _tree_fingerprint(outside))
    first = _build_matrix(tmp_path)
    middle = (_tree_fingerprint(tmp_path), _tree_fingerprint(outside))
    second = _build_matrix(tmp_path)
    after = (_tree_fingerprint(tmp_path), _tree_fingerprint(outside))

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert before == middle == after
    assert list(outside.iterdir()) == []
    assert first == EXPECTED_MATRIX
