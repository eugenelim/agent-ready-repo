"""Roster test: containment-attestation.v1 schema parity and DELIVERY_CONTROL_PATHS pin.

For the containment-attestation.v1 record this suite:

1. Validates a record produced by _containment.py against the canonical
   contracts/delivery/containment-attestation.v1.schema.json schema using
   jsonschema Draft202012Validator, so schema drift is caught before merge.

2. Feeds four classes of schema-invalid record to validate_attestation_dict()
   and asserts refusal with a stable denial code:
   - unknown authority-shaped field (not declared in the schema).
   - missing required field.
   - unknown schema_version (a version the module does not recognise).
   - out-of-enum value (read_enforcement set to an unrecognised value).

3. Pins DELIVERY_CONTROL_PATHS to the work-loop skill projections that
   contracts/adapter.toml declares for the Core pack's surfaces:
   every unique ``target-path`` under the ``skill`` primitive has
   ``{target_path}work-loop/`` in the constant, plus the pack source path.

Both reads are anchored at the repo root via
``Path(__file__).resolve().parents[2]``.  No schema or contract file is read
at runtime by the scripts under test; this suite is the only place that does
the schema comparison.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_SCRIPTS = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)

_CONTRACTS = REPO_ROOT / "contracts" / "delivery"
_ADAPTER_TOML = REPO_ROOT / "contracts" / "adapter.toml"

_ATTESTATION_SCHEMA_PATH = _CONTRACTS / "containment-attestation.v1.schema.json"

# ── Module loader ─────────────────────────────────────────────────────────────


def _load_script(name: str, path: Path) -> ModuleType:
    """Load a work-loop script by path, unregistered, using the standard loader pattern."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None, (
            f"cannot create import spec for {path}"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(name, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def containment() -> ModuleType:
    """_containment.py loaded by path."""
    return _load_script("cn_roster_parity", _SCRIPTS / "_containment.py")


@pytest.fixture(scope="module")
def attestation_schema() -> dict:
    """containment-attestation.v1 schema loaded from contracts/delivery/."""
    assert _ATTESTATION_SCHEMA_PATH.is_file(), (
        f"attestation schema not found: {_ATTESTATION_SCHEMA_PATH}"
    )
    return json.loads(_ATTESTATION_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def adapter_toml() -> dict:
    """contracts/adapter.toml loaded from the repository root."""
    assert _ADAPTER_TOML.is_file(), f"adapter.toml not found: {_ADAPTER_TOML}"
    return tomllib.loads(_ADAPTER_TOML.read_text(encoding="utf-8"))


# ── Schema validation fixtures ────────────────────────────────────────────────


def _validate_against_schema(instance: object, schema: dict) -> list[str]:
    """Validate *instance* against *schema* and return a list of error messages."""
    if importlib.util.find_spec("jsonschema") is None:
        pytest.skip("jsonschema not installed; skipping schema-validation check")
    from jsonschema import Draft202012Validator  # type: ignore[import-not-found]
    validator = Draft202012Validator(schema)
    return [str(e) for e in validator.iter_errors(instance)]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Schema parity: emitted record validates against canonical schema
# ═══════════════════════════════════════════════════════════════════════════════


class TestAttestationSchemaConformance:
    """ContainmentAttestation.as_dict() must satisfy containment-attestation.v1.schema.json."""

    def test_minimal_attestation_validates(
        self,
        containment: ModuleType,
        attestation_schema: dict,
    ) -> None:
        """A minimal valid ContainmentAttestation serializes to a schema-valid dict."""
        cn = containment
        attestation = cn.ContainmentAttestation(
            schema_version=1,
            host_mechanism="os-sandbox",
            principal_or_sandbox="sandbox-001",
            roots=("/work",),
            limits={},
        )
        errors = _validate_against_schema(attestation.as_dict(), attestation_schema)
        assert not errors, (
            "Minimal attestation dict did not validate against schema:\n"
            + "\n".join(errors)
        )

    def test_full_attestation_validates(
        self,
        containment: ModuleType,
        attestation_schema: dict,
    ) -> None:
        """A full ContainmentAttestation with all optional fields serializes correctly."""
        cn = containment
        attestation = cn.ContainmentAttestation(
            schema_version=1,
            host_mechanism="os-sandbox",
            principal_or_sandbox="sandbox-001",
            roots=("/work",),
            limits={"max_bytes": 1000, "timeout_s": 60},
            read_enforcement="allowlist",
            trace_coverage="full-trace",
            network={"allowed": False},
            children={"allowed": False},
        )
        errors = _validate_against_schema(attestation.as_dict(), attestation_schema)
        assert not errors, (
            "Full attestation dict did not validate against schema:\n"
            + "\n".join(errors)
        )

    def test_empty_roots_validates(
        self,
        containment: ModuleType,
        attestation_schema: dict,
    ) -> None:
        """Attestation with empty roots validates (roots is not required to be non-empty)."""
        cn = containment
        attestation = cn.ContainmentAttestation(
            schema_version=1,
            host_mechanism="restricted-principal",
            principal_or_sandbox="principal-002",
            roots=(),
            limits={},
        )
        errors = _validate_against_schema(attestation.as_dict(), attestation_schema)
        assert not errors, (
            "Empty-roots attestation did not validate:\n" + "\n".join(errors)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. validate_attestation_dict: four schema-invalid classes
# ═══════════════════════════════════════════════════════════════════════════════


class TestAttestationDictInvalidCases:
    """validate_attestation_dict refuses four classes of schema-invalid input."""

    def test_unknown_authority_field_refused(self, containment: ModuleType) -> None:
        """An unknown authority-shaped field is refused (additionalProperties: false)."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": ["/work"],
            "limits": {},
            "inject_escalation": "bypass",  # unknown authority field
        })
        assert not ok, "Unknown authority field must be refused"
        assert code == "denied-unknown-authority-field", (
            f"expected denied-unknown-authority-field; got {code!r}"
        )

    def test_missing_required_field_refused(self, containment: ModuleType) -> None:
        """A missing required field is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            # host_mechanism is missing
            "principal_or_sandbox": "sandbox-001",
            "roots": ["/work"],
            "limits": {},
        })
        assert not ok, "Missing required field must be refused"
        assert code == "denied-missing-required-field", (
            f"expected denied-missing-required-field; got {code!r}"
        )

    def test_unknown_schema_version_refused(self, containment: ModuleType) -> None:
        """An unknown schema_version major is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 99,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": [],
            "limits": {},
        })
        assert not ok, "Unknown schema_version must be refused"
        assert code == "denied-unknown-schema-version", (
            f"expected denied-unknown-schema-version; got {code!r}"
        )

    def test_out_of_enum_read_enforcement_refused(self, containment: ModuleType) -> None:
        """An out-of-enum value for read_enforcement is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": [],
            "limits": {},
            "read_enforcement": "completely-unrestricted",  # not in enum
        })
        assert not ok, "Out-of-enum read_enforcement must be refused"
        # The exact code depends on how the module classifies it;
        # either denied-unknown-authority-field or another stable code.
        assert code in (
            "denied-unknown-authority-field",
            "denied-out-of-enum-value",
        ), f"Expected a stable denial code for out-of-enum; got {code!r}"

    def test_same_process_isolation_refused(self, containment: ModuleType) -> None:
        """A same-process isolation claim is refused with a stable code."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            "host_mechanism": "same-process",
            "principal_or_sandbox": "no-sandbox",
            "roots": [],
            "limits": {},
        })
        assert not ok, "Same-process isolation claim must be refused"
        assert code == "denied-same-process-isolation-claim", (
            f"expected denied-same-process-isolation-claim; got {code!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DELIVERY_CONTROL_PATHS pin to contracts/adapter.toml
# ═══════════════════════════════════════════════════════════════════════════════


def _extract_skill_target_paths(toml_data: dict) -> set[str]:
    """Extract all unique skill target-path values from the adapter.toml data.

    adapter.toml declares projections for each adapter as a list under
    ``adapter.<name>.projection``.  Each entry has a ``primitive`` key
    (e.g. "skill", "agent") and a ``target-path`` key.

    Returns relative path prefixes as strings (e.g., ".claude/skills/").
    """
    skill_paths: set[str] = set()
    adapter_data = toml_data.get("adapter", {})
    for _adapter_name, adapter_config in adapter_data.items():
        if not isinstance(adapter_config, dict):
            continue
        for proj in adapter_config.get("projection", []):
            if not isinstance(proj, dict):
                continue
            if proj.get("primitive") == "skill":
                tp = proj.get("target-path")
                if isinstance(tp, str) and tp:
                    skill_paths.add(tp)
    return skill_paths


class TestDeliveryControlPathsPin:
    """DELIVERY_CONTROL_PATHS must cover every work-loop skill projection declared in adapter.toml."""

    def test_pack_source_present(self, containment: ModuleType) -> None:
        """The Core pack's work-loop source tree is in DELIVERY_CONTROL_PATHS."""
        cn = containment
        pack_source = "packs/core/.apm/skills/work-loop/"
        assert pack_source in cn.DELIVERY_CONTROL_PATHS, (
            f"Pack source {pack_source!r} missing from DELIVERY_CONTROL_PATHS; "
            f"got: {list(cn.DELIVERY_CONTROL_PATHS)!r}"
        )

    def test_claude_code_projection_present(self, containment: ModuleType) -> None:
        """The claude-code adapter's .claude/skills/work-loop/ path is in DELIVERY_CONTROL_PATHS."""
        cn = containment
        expected = ".claude/skills/work-loop/"
        assert expected in cn.DELIVERY_CONTROL_PATHS, (
            f"claude-code projection {expected!r} missing from DELIVERY_CONTROL_PATHS"
        )

    def test_kiro_projection_present(self, containment: ModuleType) -> None:
        """The kiro adapter's .kiro/skills/work-loop/ path is in DELIVERY_CONTROL_PATHS."""
        cn = containment
        expected = ".kiro/skills/work-loop/"
        assert expected in cn.DELIVERY_CONTROL_PATHS, (
            f"kiro projection {expected!r} missing from DELIVERY_CONTROL_PATHS"
        )

    def test_cohort_projection_present(self, containment: ModuleType) -> None:
        """The cohort shared .agents/skills/work-loop/ path is in DELIVERY_CONTROL_PATHS."""
        cn = containment
        expected = ".agents/skills/work-loop/"
        assert expected in cn.DELIVERY_CONTROL_PATHS, (
            f"cohort projection {expected!r} missing from DELIVERY_CONTROL_PATHS"
        )

    def test_all_adapter_skill_projections_pinned(
        self,
        containment: ModuleType,
        adapter_toml: dict,
    ) -> None:
        """Every unique skill target-path in adapter.toml has a work-loop entry in DELIVERY_CONTROL_PATHS.

        This is the binding pin: when a new adapter projecting skills to a new
        target-path is added to contracts/adapter.toml, this test will fail
        until DELIVERY_CONTROL_PATHS is updated.
        """
        cn = containment
        skill_target_paths = _extract_skill_target_paths(adapter_toml)
        assert skill_target_paths, (
            "No skill target-paths found in adapter.toml; check _extract_skill_target_paths"
        )
        dcp = cn.DELIVERY_CONTROL_PATHS
        missing: list[str] = []
        for tp in sorted(skill_target_paths):
            expected = f"{tp}work-loop/"
            if expected not in dcp:
                missing.append(expected)
        assert not missing, (
            "The following adapter.toml skill projection paths are not in "
            "DELIVERY_CONTROL_PATHS:\n  " + "\n  ".join(missing)
            + "\n\nCurrent DELIVERY_CONTROL_PATHS:\n  "
            + "\n  ".join(dcp)
        )

    def test_delivery_control_paths_is_tuple_of_strings(
        self, containment: ModuleType
    ) -> None:
        """DELIVERY_CONTROL_PATHS is a tuple of non-empty strings."""
        cn = containment
        dcp = cn.DELIVERY_CONTROL_PATHS
        assert isinstance(dcp, tuple), (
            f"DELIVERY_CONTROL_PATHS must be a tuple; got {type(dcp)!r}"
        )
        assert dcp, "DELIVERY_CONTROL_PATHS must be non-empty"
        for entry in dcp:
            assert isinstance(entry, str) and entry, (
                f"DELIVERY_CONTROL_PATHS entries must be non-empty strings; got {entry!r}"
            )

    def test_delivery_control_paths_schema_version(
        self, containment: ModuleType
    ) -> None:
        """SUPPORTED_ATTESTATION_SCHEMA_VERSION is the expected integer."""
        cn = containment
        assert cn.SUPPORTED_ATTESTATION_SCHEMA_VERSION == 1, (
            f"expected schema version 1; got {cn.SUPPORTED_ATTESTATION_SCHEMA_VERSION!r}"
        )
