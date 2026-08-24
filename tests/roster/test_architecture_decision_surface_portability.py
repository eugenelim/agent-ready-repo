"""RFC-0096 Wave 3 portability matrix around the shipped Wave 1 resolver."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RESOLVER_PATH = (
    ROOT
    / "packs/core/.apm/skills/work-intake/scripts/surface_resolver.py"
)
INSTALLED_RESOLVER_PATH = (
    ROOT / ".agents/skills/work-intake/scripts/surface_resolver.py"
)
SCHEMA_PATH = ROOT / "contracts/jsonschema/semantic-surface-resolution.schema.json"
MATRIX_PATH = (
    ROOT
    / "tests/roster/fixtures/architecture-decision-surface-portability"
    / "completion-matrix.json"
)

EXPECTED_RESOLVER_SHA256 = (
    "b341f10478e8db8c03c0ff187648d3e9d3daa5b9e860f48504d13d025ab8a5d4"
)
EXPECTED_SCHEMA_SHA256 = (
    "df66ac4455316a9b9edf1664a9966415afaed2048ffa415a7db95bafce0c28d8"
)
WAVE3_ROLES = ("architecture-design", "current-architecture", "decision-record")

ARCHITECT_SOURCES = {
    "architect-design": ROOT / "packs/architect/.apm/skills/architect-design/SKILL.md",
    "architect-assess": ROOT / "packs/architect/.apm/skills/architect-assess/SKILL.md",
    "architect-diagram": ROOT / "packs/architect/.apm/skills/architect-diagram/SKILL.md",
}
ARCHITECT_EVALS = {
    "architect-design": (
        ROOT / "packs/architect/.apm/skills/architect-design/evals/evals.json"
    ),
    "architect-assess": (
        ROOT / "packs/architect/.apm/skills/architect-assess/evals/evals.json"
    ),
    "architect-diagram": (
        ROOT / "packs/architect/.apm/skills/architect-diagram/evals/evals.json"
    ),
}
NEW_ADR_SOURCE = ROOT / "packs/governance-extras/.apm/skills/new-adr/SKILL.md"
PORTABLE_CONSUMER_SOURCES = {
    "work-intake": ROOT / "packs/core/.apm/skills/work-intake/SKILL.md",
    "init-project": ROOT / "packs/core/.apm/skills/init-project/SKILL.md",
    "adapt-to-project": ROOT / "packs/core/.apm/skills/adapt-to-project/SKILL.md",
    "new-package": ROOT / "packs/monorepo-extras/.apm/skills/new-package/SKILL.md",
    "generate-iac": ROOT / "packs/iac-terraform/.apm/skills/generate-iac/SKILL.md",
}


def _sha256(path: Path) -> str:
    """Return the byte digest for an immutable Wave 1 authority."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_resolver(
    path: Path = RESOLVER_PATH,
    module_name: str = "wave3_real_surface_resolver",
):
    """Load the portable Wave 1 source without an installed package dependency."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def resolver():
    """Return a fresh real resolver module for each behavior test."""
    return _load_resolver()


def _candidate(module, case_id: str, role: str, raw: dict[str, str]):
    """Construct one closed candidate from committed inert fixture data."""
    return module.SurfaceCandidate(
        role=role,
        logical_locator=raw["logical_locator"],
        physical_locator=module.Locator(raw["kind"], raw["value"]),
        provenance=(
            module.Evidence(
                raw["source"], raw.get("ref", f"fixture:{case_id}"), raw["strength"]
            ),
        ),
    )


def _fingerprint(root: Path) -> dict[str, bytes]:
    """Return the complete regular-file state below a fixture root."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_wave3_consumes_the_exact_wave1_authorities() -> None:
    """Wave 3 cannot widen the role enum or modify the resolver/schema bytes."""
    resolver = _load_resolver()

    assert _sha256(RESOLVER_PATH) == EXPECTED_RESOLVER_SHA256
    assert _sha256(SCHEMA_PATH) == EXPECTED_SCHEMA_SHA256
    assert all(role in resolver.SURFACE_ROLES for role in WAVE3_ROLES)
    assert "design-artifact" not in resolver.SURFACE_ROLES


def test_portable_destination_matrix_uses_the_real_resolver(
    resolver, tmp_path: Path
) -> None:
    """Custom destinations and terminal outcomes retain Wave 1 semantics."""
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

    observed: list[dict[str, str | None]] = []
    for case in matrix:
        case_root = tmp_path / case["id"]
        case_root.mkdir()
        candidates = [
            _candidate(resolver, case["id"], case["role"], item)
            for item in case["candidates"]
        ]
        before = _fingerprint(case_root)
        result = resolver.resolve_surface(case_root, case["role"], candidates)
        after = _fingerprint(case_root)
        assert before == after, case["id"]
        payload = result.as_dict()
        assert {
            "contract_version",
            "status",
            "role",
            "provenance",
            "availability",
            "writability",
            "confinement",
            "authority",
            "confirmations",
        }.issubset(payload), case["id"]
        if result.status == "resolved":
            winner = next(
                candidate
                for candidate in candidates
                if candidate.physical_locator.value == case["selected"]
            )
            assert result.logical_locator == winner.logical_locator, case["id"]
            assert result.physical_locator == winner.physical_locator, case["id"]
            assert result.provenance == winner.provenance, case["id"]
            assert result.availability in {
                "available",
                "unavailable",
                "unknown",
            }, case["id"]
            assert result.writability in {"writable", "read-only", "unknown"}, case[
                "id"
            ]
            assert result.confinement == (
                "external"
                if winner.physical_locator.kind == "external"
                else "repository-confined"
            ), case["id"]
            assert result.authority == winner.authority, case["id"]
            assert result.confirmations == winner.confirmations, case["id"]
            assert (
                result.revision_or_fingerprint == winner.revision_or_fingerprint
            ), case["id"]
        observed.append(
            {
                "id": case["id"],
                "role": result.role,
                "status": result.status,
                "code": result.code,
                "selected": (
                    result.physical_locator.value
                    if result.physical_locator is not None
                    else None
                ),
            }
        )

    assert observed == [
        {
            "id": case["id"],
            "role": case["role"],
            "status": case["status"],
            "code": case["code"],
            "selected": case["selected"],
        }
        for case in matrix
    ]


def test_installed_agents_projection_executes_the_same_boundary_contract() -> None:
    """The built Core projection must execute Wave 3 roles, not just mention them."""
    assert _sha256(INSTALLED_RESOLVER_PATH) == EXPECTED_RESOLVER_SHA256
    installed = _load_resolver(
        INSTALLED_RESOLVER_PATH, "wave3_installed_surface_resolver"
    )
    destinations = {
        "current-architecture": "engineering/system/current",
        "decision-record": "decisions/records",
    }

    results = {
        role: installed.resolve_surface(
            ROOT,
            role,
            [
                installed.SurfaceCandidate(
                    role=role,
                    logical_locator=f"{role}:installed",
                    physical_locator=installed.Locator("repository-path", value),
                    provenance=(
                        installed.Evidence(
                            "repository-policy",
                            f"installed:{role}",
                            "enforced",
                        ),
                    ),
                )
            ],
        )
        for role, value in destinations.items()
    }

    assert all(result.status == "resolved" for result in results.values())
    assert {
        result.physical_locator.value
        for result in results.values()
        if result.physical_locator is not None
    } == set(destinations.values())
    projection_pairs = (
        (
            ROOT / "packs/core/.apm/skills/work-intake/SKILL.md",
            ROOT / ".agents/skills/work-intake/SKILL.md",
        ),
        (
            ROOT / "packs/core/.apm/skills/adapt-to-project/SKILL.md",
            ROOT / ".agents/skills/adapt-to-project/SKILL.md",
        ),
        (
            ROOT / "packs/governance-extras/.apm/skills/new-adr/SKILL.md",
            ROOT / ".agents/skills/new-adr/SKILL.md",
        ),
    )
    for source, installed_projection in projection_pairs:
        assert installed_projection.read_bytes() == source.read_bytes()


def test_architect_package_projection_preserves_all_four_modes(
    tmp_path: Path,
) -> None:
    """The real installable Architect package must carry source and eval bytes."""
    output = tmp_path / "architect-package"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(ROOT / "packages/agentbundle")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "build",
            "--root",
            str(ROOT),
            "--recipe",
            "per-pack-apm-package",
            "--pack",
            "architect",
            "--output",
            str(output),
            "--format",
            "json",
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    built_root = output / "apm/architect/.apm/skills"

    for skill_name, source_skill in ARCHITECT_SOURCES.items():
        source_root = source_skill.parent
        built_skill_root = built_root / skill_name
        source_files = {
            path.relative_to(source_root): path.read_bytes()
            for path in source_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        built_files = {
            path.relative_to(built_skill_root): path.read_bytes()
            for path in built_skill_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        assert built_files == source_files, skill_name
        built_skill = (built_skill_root / "SKILL.md").read_text(encoding="utf-8")
        for mode in (
            "chat-only",
            "personal-workspace",
            "repository-resolved",
            "repository-handoff",
        ):
            assert mode in built_skill, (skill_name, mode)

    built_design_evals = json.loads(
        (built_root / "architect-design/evals/evals.json").read_text(
            encoding="utf-8"
        )
    )["evals"]
    built_assess_evals = json.loads(
        (built_root / "architect-assess/evals/evals.json").read_text(
            encoding="utf-8"
        )
    )["evals"]
    built_diagram_evals = json.loads(
        (built_root / "architect-diagram/evals/evals.json").read_text(
            encoding="utf-8"
        )
    )["evals"]
    assert {item["id"] for item in built_design_evals}.issuperset({3, 4, 5, 6, 7})
    assert {item["id"] for item in built_assess_evals}.issuperset(
        {8, 9, 10, 11, 12}
    )
    assert {item["id"] for item in built_diagram_evals}.issuperset({2, 3, 4})


def test_architect_mode_evals_close_write_authority_edges() -> None:
    """Deterministic eval contracts cover all four modes and exact-file branches."""
    evals = {
        skill: {
            item["id"]: item
            for item in json.loads(path.read_text(encoding="utf-8"))["evals"]
        }
        for skill, path in ARCHITECT_EVALS.items()
    }

    chat = evals["architect-design"][3]
    assert "chat only; no file was created" in chat["expected_output"]

    personal_root = evals["architect-design"][5]
    assert "personal-workspace" in personal_root["expected_output"]
    assert "Does not claim a semantic-surface-resolution.v1 result" in personal_root[
        "assertions"
    ]

    for skill, eval_id in (("architect-design", 7), ("architect-assess", 12)):
        exact_file = evals[skill][eval_id]
        assert "refusal with zero effects" in exact_file["expected_output"]
        assert "Invokes no write" in exact_file["assertions"]

    diagram_file = evals["architect-diagram"][4]
    assert "personal-workspace single-file save" in diagram_file["expected_output"]
    assert "Treats the exact confirmed file as the sole target" in diagram_file[
        "assertions"
    ]

    for skill, eval_id in (
        ("architect-design", 4),
        ("architect-assess", 8),
        ("architect-diagram", 2),
    ):
        repository_resolved = evals[skill][eval_id]
        assert "repository-resolved" in repository_resolved["expected_output"]
        assert (
            "semantic-surface-resolution.v1"
            in " ".join(
                [
                    repository_resolved["expected_output"],
                    *repository_resolved["assertions"],
                ]
            )
        )

    for skill, eval_id in (
        ("architect-design", 6),
        ("architect-assess", 11),
        ("architect-diagram", 3),
    ):
        handoff = evals[skill][eval_id]
        assert "zero-write" in handoff["expected_output"]
        assert "semantic-surface-resolution.v1" in " ".join(
            [handoff["expected_output"], *handoff["assertions"]]
        )
        assert any(
            "no repository write" in assertion.lower()
            or "invokes no repository write" in assertion.lower()
            or "writes no report" in assertion.lower()
            for assertion in handoff["assertions"]
        )


def test_complete_external_facts_remain_independent_and_offline(
    resolver, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A consumer receives capability and authority facts without probing."""

    def unexpected_path_access(*_args, **_kwargs):
        raise AssertionError("external locator entered filesystem resolution")

    monkeypatch.setattr(resolver.Path, "resolve", unexpected_path_access)
    authority = resolver.Authority(
        source=resolver.AuthorityFact("external-owned", "policy:source"),
        write=resolver.AuthorityFact("delegated", "policy:write"),
        delete=resolver.AuthorityFact("none", "policy:delete"),
    )
    result = resolver.resolve_surface(
        tmp_path,
        "decision-record",
        [
            resolver.SurfaceCandidate(
                role="decision-record",
                logical_locator="decision-record:external",
                physical_locator=resolver.Locator(
                    "external", "example-wiki:architecture/decisions"
                ),
                provenance=(
                    resolver.Evidence(
                        "external-destination", "policy:decisions", "confirmed"
                    ),
                ),
                availability="available",
                writability="writable",
                authority=authority,
                revision_or_fingerprint="revision-9",
                confirmations=(
                    resolver.Confirmation(
                        "authority", "confirmed", "approval:external-write"
                    ),
                ),
            )
        ],
    )

    assert result.contract_version == "semantic-surface-resolution.v1"
    assert result.role == "decision-record"
    assert result.physical_locator == resolver.Locator(
        "external", "example-wiki:architecture/decisions"
    )
    assert result.confinement == "external"
    assert result.availability == "available"
    assert result.writability == "writable"
    assert result.authority == authority
    assert result.revision_or_fingerprint == "revision-9"
    assert result.confirmations == (
        resolver.Confirmation("authority", "confirmed", "approval:external-write"),
    )


def test_boundary_change_resolves_architecture_and_decision_without_product_prose(
    resolver, tmp_path: Path
) -> None:
    """The RFC representative boundary case has exactly two durable roles."""
    destinations = {
        "current-architecture": "engineering/system/current",
        "decision-record": "decisions/records",
    }

    results = {
        role: resolver.resolve_surface(
            tmp_path,
            role,
            [
                resolver.SurfaceCandidate(
                    role=role,
                    logical_locator=f"{role}:boundary-change",
                    physical_locator=resolver.Locator("repository-path", locator),
                    provenance=(
                        resolver.Evidence(
                            "repository-policy",
                            f"fixture:boundary-change:{role}",
                            "enforced",
                        ),
                    ),
                )
            ],
        )
        for role, locator in destinations.items()
    }

    assert set(results) == {"current-architecture", "decision-record"}
    assert all(result.status == "resolved" for result in results.values())
    assert {
        result.physical_locator.value
        for result in results.values()
        if result.physical_locator is not None
    } == set(destinations.values())
    assert set(results).isdisjoint(
        {
            "current-product-truth",
            "user-documentation",
            "product-history",
            "release-history",
        }
    )


def test_architecture_consumers_declare_portable_roles_and_modes() -> None:
    """Prompt owners must consume roles without claiming a catalogue path."""
    for skill_name, path in ARCHITECT_SOURCES.items():
        source = path.read_text(encoding="utf-8")
        assert "semantic-surface-resolution.v1" in source, skill_name
        assert "chat-only" in source, skill_name
        assert "personal-workspace" in source, skill_name
        assert "repository-resolved" in source, skill_name
        assert "repository-handoff" in source, skill_name

    design = ARCHITECT_SOURCES["architect-design"].read_text(encoding="utf-8")
    assessment = ARCHITECT_SOURCES["architect-assess"].read_text(encoding="utf-8")
    diagram = ARCHITECT_SOURCES["architect-diagram"].read_text(encoding="utf-8")
    adr = NEW_ADR_SOURCE.read_text(encoding="utf-8")

    assert "architecture-design" in design
    assert "current-architecture" in assessment
    assert "architecture-design" in assessment
    assert "current-architecture" in diagram
    assert "architecture-design" in diagram
    assert "decision-record" in adr
    assert "semantic-surface-resolution.v1" in adr


def test_bounded_consumers_delegate_roles_without_reimplementing_resolution() -> None:
    """Orchestrators name roles while Wave 1 remains the sole resolver."""
    sources = {
        name: path.read_text(encoding="utf-8")
        for name, path in PORTABLE_CONSUMER_SOURCES.items()
    }

    assert "architecture-design" in sources["work-intake"]
    assert "current-architecture" in sources["work-intake"]
    assert "decision-record" in sources["work-intake"]

    for name in ("init-project", "adapt-to-project", "new-package", "generate-iac"):
        assert "work-intake" in sources[name], name
        assert "semantic-surface-resolution.v1" in sources[name], name

    assert "current-architecture" in sources["init-project"]
    assert "decision-record" in sources["init-project"]
    assert "current-architecture" in sources["adapt-to-project"]
    assert "current-architecture" in sources["new-package"]
    assert "decision-record" in sources["generate-iac"]
    assert "docs/architecture/overview.md` is only the catalogue fallback" in sources[
        "new-package"
    ]
    assert "do not assume `docs/adr/`" in sources["generate-iac"]

    resolver_copies = list(ROOT.glob("packs/**/surface_resolver.py"))
    assert resolver_copies == [RESOLVER_PATH]


def test_touched_skill_boundaries_are_declared_in_canonical_sources() -> None:
    """Filesystem and untrusted-content metadata must survive from `.apm`."""
    touched_sources = {
        **ARCHITECT_SOURCES,
        "new-adr": NEW_ADR_SOURCE,
        **PORTABLE_CONSUMER_SOURCES,
    }
    for skill_name, path in touched_sources.items():
        source = path.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        assert "metadata:" in frontmatter, skill_name
        assert "filesystem_read_untrusted" in frontmatter, skill_name
        assert "filesystem_write" in frontmatter, skill_name
