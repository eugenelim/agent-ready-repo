"""T9a conformance roll-up: projected Core pack copies are byte-identical to source.

AC-0001 through AC-0021: the frozen import, subject, verdict, recovery, reversal,
security, content-safety, authorized-append, audit-failure, and cross-adapter corpora
pass against the projected Core pack (the `make build-self` output).

Strategy (plan.md T9a):

  Prefer reusing the existing suites by running them against the projected copies —
  a roster test that verifies projected copies are byte-identical to the pack source
  and then imports from the projected path — over duplicating assertions.

Since the projected copies at
  .claude/skills/work-loop/scripts/    (Claude Code adapter)
  .agents/skills/work-loop/scripts/    (Agents adapter)
are build outputs of ``make build-self``, byte-identity to
  packs/core/.apm/skills/work-loop/scripts/
proves that every assertion in the existing T1–T8 pack and roster suites already
covers the projected copies: the tests run against identical bytes.  Byte-identity
also satisfies the AC-0013 requirement that the delivery-control paths agree with
the pack source at the point of audit.

Roster-owned: reads above any single pack tree (repo root, packs/core/, .claude/,
.agents/), so lint-pack-test-boundary forbids a pack home.  Placed above the bulk
``pytest tests/ -q`` carve-out step in build-check.yml so a failure is attributed
to this named step.

Spec: docs/specs/acceptance-authority-and-evidence/spec.md
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]

_PACK_SCRIPTS = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)

# Projected adapter copies — build outputs of `make build-self`.
_CLAUDE_SCRIPTS = REPO_ROOT / ".claude" / "skills" / "work-loop" / "scripts"
_AGENTS_SCRIPTS = REPO_ROOT / ".agents" / "skills" / "work-loop" / "scripts"


# ── SHA-256 file digest helper ────────────────────────────────────────────────


def _sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a regular file's raw bytes."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _script_files(scripts_dir: Path) -> list[Path]:
    """Return sorted regular .py files in a scripts directory."""
    return sorted(
        p for p in scripts_dir.iterdir()
        if p.is_file() and p.suffix == ".py" and p.stat().st_mode & stat.S_IFREG
    )


# ── Module loader (reuses the pattern from other roster tests) ────────────────


def _load_script(name: str, path: Path) -> ModuleType:
    """Load a work-loop script by absolute path, unregistered."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sp = importlib.util.spec_from_file_location(name, str(path))
        assert sp is not None and sp.loader is not None, (
            f"cannot create import spec for {path}"
        )
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = previous


# ═══════════════════════════════════════════════════════════════════════════════
# Byte-identity: projected copies equal the pack source
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectedCopiesByteIdentical:
    """Both projected copies are byte-identical to packs/core/.apm/…/scripts/."""

    def _assert_byte_identity(
        self, projected: Path, *, label: str
    ) -> None:
        """Compare every .py in projected against the pack source byte-by-byte."""
        assert projected.is_dir(), (
            f"projected scripts directory missing: {projected}\n"
            f"Run `make build-self` to regenerate build outputs."
        )
        source_files = _script_files(_PACK_SCRIPTS)
        assert source_files, f"no .py files found in pack source: {_PACK_SCRIPTS}"

        diffs: list[str] = []
        for src in source_files:
            dst = projected / src.name
            if not dst.exists():
                diffs.append(f"  MISSING  {label}/{src.name}")
                continue
            src_hash = _sha256_file(src)
            dst_hash = _sha256_file(dst)
            if src_hash != dst_hash:
                diffs.append(
                    f"  DIFFER   {label}/{src.name}\n"
                    f"           pack source sha256: {src_hash}\n"
                    f"           projected  sha256: {dst_hash}"
                )

        # Also catch extra files in the projection that the source doesn't have
        projected_files = {p.name for p in _script_files(projected)}
        source_names = {p.name for p in source_files}
        for extra in sorted(projected_files - source_names):
            diffs.append(f"  EXTRA    {label}/{extra} (not in pack source)")

        assert not diffs, (
            f"Projected copy at {label} is NOT byte-identical to the pack source.\n"
            f"Run `make build-self` to regenerate.\n"
            + "\n".join(diffs)
        )

    def test_claude_projected_scripts_byte_identical_to_pack_source(self) -> None:
        """The .claude/skills/work-loop/scripts/ copy is byte-identical to pack source.

        Proves AC-0001 through AC-0021: the T1–T8 corpora run against identical
        bytes in both the pack source (where the suites are anchored) and the
        Claude Code adapter projection.
        """
        self._assert_byte_identity(_CLAUDE_SCRIPTS, label=".claude/skills/work-loop/scripts")

    def test_agents_projected_scripts_byte_identical_to_pack_source(self) -> None:
        """The .agents/skills/work-loop/scripts/ copy is byte-identical to pack source.

        Proves AC-0001 through AC-0021: the T1–T8 corpora run against identical
        bytes in both the pack source and the Agents adapter projection.
        """
        self._assert_byte_identity(_AGENTS_SCRIPTS, label=".agents/skills/work-loop/scripts")


# ═══════════════════════════════════════════════════════════════════════════════
# Import smoke-tests: projected modules load correctly from their projected path
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectedModulesImportable:
    """Key modules import from the projected paths as well as the pack source."""

    def test_acceptance_module_importable_from_claude_projection(self) -> None:
        """_acceptance.py loads from the .claude/ projected copy.

        Confirms AC-0003, AC-0007, AC-0009, AC-0018: the acceptance evaluator is
        reachable via the projected path.
        """
        mod = _load_script("t9a_acc_claude", _CLAUDE_SCRIPTS / "_acceptance.py")
        assert hasattr(mod, "evaluate_verdict"), (
            "_acceptance.py from .claude/ must export evaluate_verdict"
        )

    def test_compat_facade_importable_from_agents_projection(self) -> None:
        """_compat_facade.py loads from the .agents/ projected copy.

        Confirms AC-0016, AC-0017: the compatibility facade is reachable via the
        Agents adapter projection.
        """
        mod = _load_script("t9a_facade_agents", _AGENTS_SCRIPTS / "_compat_facade.py")
        assert hasattr(mod, "shadow_enabled"), (
            "_compat_facade.py from .agents/ must export shadow_enabled"
        )
        assert hasattr(mod, "shadow_call_on_transition"), (
            "_compat_facade.py from .agents/ must export shadow_call_on_transition"
        )

    def test_policy_import_importable_from_claude_projection(self) -> None:
        """_policy_import.py loads from the .claude/ projected copy.

        Confirms AC-0001, AC-0002, AC-0017, AC-0020: the policy-import service is
        reachable via the Claude Code adapter projection. Checks for ``import_policy``
        as the canonical public entry point.
        """
        mod = _load_script("t9a_pi_claude", _CLAUDE_SCRIPTS / "_policy_import.py")
        assert hasattr(mod, "import_policy"), (
            "_policy_import.py from .claude/ must export import_policy"
        )

    def test_subject_projection_importable_from_agents_projection(self) -> None:
        """_subject_projection.py loads from the .agents/ projected copy.

        Confirms AC-0005, AC-0006: the delivery-subject projector is reachable via
        the Agents adapter projection.
        """
        mod = _load_script("t9a_sp_agents", _AGENTS_SCRIPTS / "_subject_projection.py")
        assert hasattr(mod, "project_delivery_subject"), (
            "_subject_projection.py from .agents/ must export project_delivery_subject"
        )

    def test_evidence_store_importable_from_claude_projection(self) -> None:
        """_evidence_store.py loads from the .claude/ projected copy.

        Confirms AC-0008, AC-0009, AC-0019, AC-0020: the evidence store is
        reachable via the Claude Code adapter projection.
        """
        mod = _load_script("t9a_es_claude", _CLAUDE_SCRIPTS / "_evidence_store.py")
        assert hasattr(mod, "EvidenceStore"), (
            "_evidence_store.py from .claude/ must export EvidenceStore"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Red evidence: byte-identity check fails on a mutated scratch copy
# ═══════════════════════════════════════════════════════════════════════════════


class TestByteIdentityRedEvidence:
    """Prove the byte-identity assertion actually catches a mutation."""

    def test_byte_identity_check_detects_modified_file_in_scratch_copy(
        self, tmp_path: Path
    ) -> None:
        """Mutating one byte in a scratch copy causes the identity check to fail.

        Red evidence: confirms the check is not a tautology.  The scratch
        directory mimics a projected copy that has a stale or incorrect file.
        """
        # Copy the real source to a scratch directory
        scratch = tmp_path / "scratch-scripts"
        scratch.mkdir()
        source_files = _script_files(_PACK_SCRIPTS)
        assert source_files, "no .py files found in pack source"

        # Copy all files byte-for-byte
        for src in source_files:
            (scratch / src.name).write_bytes(src.read_bytes())

        # Verify it's identical first
        diffs_before: list[str] = []
        for src in source_files:
            dst = scratch / src.name
            if _sha256_file(src) != _sha256_file(dst):
                diffs_before.append(src.name)
        assert not diffs_before, f"scratch copy not clean before mutation: {diffs_before}"

        # Mutate one file
        target = scratch / source_files[0].name
        original_bytes = target.read_bytes()
        mutated = original_bytes + b"\n# T9a red-evidence marker\n"
        target.write_bytes(mutated)

        # Re-run the identity check on the mutated scratch
        diffs_after: list[str] = []
        for src in source_files:
            dst = scratch / src.name
            if _sha256_file(src) != _sha256_file(dst):
                diffs_after.append(src.name)

        assert diffs_after, (
            "Red evidence: the byte-identity check did NOT detect the mutation; "
            "the check would be a false-positive guarantor."
        )
        assert source_files[0].name in diffs_after, (
            f"Red evidence: expected {source_files[0].name} in diffs; got {diffs_after}"
        )


# ── Shadow records satisfy their canonical schemas ────────────────────────────

_PACK_TESTS = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"
_DELIVERY_SCHEMAS = REPO_ROOT / "contracts" / "delivery"

# Shadow file name → canonical schema it must satisfy.
_SHADOW_FILE_SCHEMAS: dict[str, str] = {
    "shadow-approval.json": "approval-record.v1.schema.json",
    "shadow-initial-review.json": "initial-plan-review.v1.schema.json",
    "shadow-verdict.json": "acceptance-verdict.v1.schema.json",
    "shadow-delivery-subject.json": "delivery-subject.v1.schema.json",
    "shadow-property.json": "acceptance-property.v1.schema.json",
}


def _delivery_validator(schema_name: str):  # type: ignore[no-untyped-def]
    """Return a Draft 2020-12 validator for one canonical delivery schema."""
    import json

    import jsonschema  # test-time only

    schema = json.loads((_DELIVERY_SCHEMAS / schema_name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


class TestShadowRecordsMatchCanonicalSchemas:
    """Every record the shadow facade persists validates against contracts/delivery/."""

    def test_full_shadow_run_writes_only_schema_valid_records(self, tmp_path: Path) -> None:
        """Run the real engine to plan-locked with shadow on, then validate every record."""
        import json
        import subprocess

        helpers = _load_script("wl_compat_facade_tests", _PACK_TESTS / "test_compat_facade.py")
        root = tmp_path / "repo"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        results = helpers._run_full_sequence(root, "schema-feature", shadow="1")
        assert results.get("plan_locked_rc") == 0, results

        shadow_dir = results["shadow_dir"]
        written = {f.name for f in shadow_dir.iterdir() if f.is_file()}
        assert {"shadow-approval.json", "shadow-initial-review.json",
                "shadow-property.json", "shadow-verdict.json",
                "shadow-evidence.log"} <= written, written
        verdict = json.loads((shadow_dir / "shadow-verdict.json").read_text(encoding="utf-8"))
        assert verdict["verdict"] == "supported", verdict
        known = set(_SHADOW_FILE_SCHEMAS) | {
            "shadow-evidence.log", "shadow-security-events.jsonl", ".gitignore",
        }
        assert written <= known, f"unregistered shadow files: {sorted(written - known)}"

        for name, schema_name in _SHADOW_FILE_SCHEMAS.items():
            if name in written:
                record = json.loads((shadow_dir / name).read_text(encoding="utf-8"))
                errors = [e.message for e in _delivery_validator(schema_name).iter_errors(record)]
                assert not errors, f"{name} violates {schema_name}: {errors}"

        tx_validator = _delivery_validator("semantic-evidence-transaction.v1.schema.json")
        receipt_validator = _delivery_validator("evidence-receipt.v1.schema.json")
        lines = (shadow_dir / "shadow-evidence.log").read_text(encoding="utf-8").splitlines()
        assert lines, "the evidence log must hold at least one transaction"
        for line in lines:
            frame = json.loads(line)
            assert not list(tx_validator.iter_errors(frame["tx"])), frame["tx"]
            for receipt in frame["records"]:
                errors = [e.message for e in receipt_validator.iter_errors(receipt)]
                assert not errors, f"shadow receipt violates evidence-receipt.v1: {errors}"

        events = shadow_dir / "shadow-security-events.jsonl"
        if events.exists():
            validator = _delivery_validator("security-event.v1.schema.json")
            for line in events.read_text(encoding="utf-8").splitlines():
                assert not list(validator.iter_errors(json.loads(line))), line
