"""The lifecycle record's optional `parent` field and its derivation on enrol."""
from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_COOLING_PATH = _PACK_ROOT / ".apm/skills/close-work/scripts/cooling.py"
_BRIEF = "docs/product/briefs/example-brief.md"
_SPEC = "docs/specs/example/spec.md"
_ZONE = "Asia/Singapore"


def _load_cooling():
    """Load the cooling source under a test-specific module name."""
    module_name = "core_close_work_cooling_parent"
    spec = importlib.util.spec_from_file_location(module_name, _COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


COOLING = _load_cooling()


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": "spec-example",
        "locator": _SPEC,
        "aliases": [],
        "fingerprint": "sha256:" + "0" * 64,
        "disposition": "cool-30-days",
        "post_closeout_result": "Cooling",
        "completion_event": "merge",
        "completion_evidence_ref": "commit:" + "a" * 40,
        "completed_on": "2026-08-01",
        "timezone": _ZONE,
        "review_on": "2026-08-31",
        "authority": {
            "source": {"status": "repository-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "none"},
        },
        "confirmation_proof": "sha256:" + "1" * 64,
    }
    payload.update(overrides)
    return payload


# ---- validate_payload value cases -------------------------------------------

_ACCEPTED = ["none", _BRIEF, "docs/product/briefs/a.md", "docs/product/briefs/" + "a" * 128 + ".md"]
_REFUSED: list[object] = [
    "brief:example-brief",
    "docs/product/briefs/sub/example.md",
    "docs/product/briefs/../briefs/x.md",
    "../docs/product/briefs/x.md",
    "docs/product/briefs/Example.md",
    "docs/product/briefs/example.md\n",
    "docs/product/briefs/" + "a" * 129 + ".md",
    "docs/product/briefs/-x.md",
    "",
    "None",
    "x" * 5000,
    None,
    7,
    ["none"],
    {"a": "b"},
    True,
]


def test_absent_parent_validates_and_stays_absent() -> None:
    result = COOLING.validate_payload(_payload())
    assert result.code is None
    assert result.record.parent is None
    assert "parent" not in result.record.as_payload()


@pytest.mark.parametrize("value", _ACCEPTED)
def test_accepted_parent_values(value: str) -> None:
    result = COOLING.validate_payload(_payload(parent=value))
    assert result.code is None
    assert result.record.as_payload()["parent"] == value


@pytest.mark.parametrize("value", _REFUSED, ids=repr)
def test_refused_parent_values(value: object) -> None:
    assert COOLING.validate_payload(_payload(parent=value)).code == "record-invalid"


# ---- enrol derivation ---------------------------------------------------------


def _fixtures(root: Path, record):
    close_work = COOLING._close_work()
    resolver = close_work.surface_resolver()
    candidate = resolver.SurfaceCandidate(
        role="runtime-coordination",
        logical_locator="docs/lifecycle",
        physical_locator=resolver.Locator("repository-path", "docs/lifecycle"),
        provenance=(resolver.Evidence("explicit", "request:cooling", "explicit"),),
        availability="available",
        writability="writable",
        authority=resolver.Authority(
            source=resolver.AuthorityFact("repository-owned", "authority:source"),
            write=resolver.AuthorityFact("delegated", "authority:write"),
            delete=resolver.AuthorityFact("none", "authority:delete"),
        ),
        revision_or_fingerprint="lifecycle-v1",
        confirmations=(resolver.Confirmation("destination-selection", "confirmed"),),
    )
    fact = close_work.resolve_mutation_authority(
        grant_record={
            "authorized_actor_role": "release-manager",
            "grant_source": "approval:release",
            "action": "write-lifecycle-record",
            "resource": f"docs/lifecycle/{record.delivery_id}.json",
            "evidence_ref": "authority:write",
            "host_session_provenance": "host-session:pytest",
        },
        authority_evidence_ref="authority-resolution:pytest",
    )
    assert fact is not None
    binding = close_work._mutation_binding(
        authority_fact=fact,
        authorized_actor_role=fact.authorized_actor_role,
        grant_source=fact.grant_source,
        action=fact.action,
        resource=fact.resource,
        evidence_ref=fact.evidence_ref,
        host_session_provenance=fact.host_session_provenance,
        expected_action="write-lifecycle-record",
    )
    assert binding is not None
    (root / "docs/lifecycle").mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "record": record,
        "delivered": True,
        "closed": True,
        "persisted": True,
        "completion_event": "merge",
        "candidates": (candidate,),
        "authority_binding": binding,
    }


def _enrol(root: Path, **payload: object):
    record = COOLING.CoolingRecord.from_payload(_payload(**payload))
    result = COOLING.enrol(**_fixtures(root, record))
    assert result.code == "enrolled", result.code
    path = root / f"docs/lifecycle/{record.delivery_id}.json"
    loaded = COOLING.load_record(root, path)
    assert loaded.code is None
    return loaded.record


def _plant_brief(root: Path, name: str = "example-brief.md") -> None:
    brief = root / "docs/product/briefs" / name
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("# Brief\n", encoding="utf-8")


def _plant_spec(root: Path, brief_line: str | None, locator: str = _SPEC) -> None:
    lines = ["# Spec: Example", "", "- **Status:** Shipped"]
    if brief_line is not None:
        lines.append(brief_line)
    lines += ["- **Owner:** someone", "", "## Overview", "", "- **Brief:** brief:other", ""]
    path = root / locator
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize(
    "header",
    [
        "- **Brief:** brief:example-brief",
        f"- **Brief:** {_BRIEF}",
        "- **Brief:** brief:example-brief <!-- note -->",
    ],
)
def test_enrol_derives_a_brief_path(tmp_path: Path, header: str) -> None:
    _plant_brief(tmp_path)
    _plant_spec(tmp_path, header)
    assert _enrol(tmp_path).parent == _BRIEF


@pytest.mark.parametrize("header", ["- **Brief:** none", "- **Brief:**", "- **Brief:**   ", None])
def test_enrol_derives_none(tmp_path: Path, header: str | None) -> None:
    _plant_spec(tmp_path, header)
    assert _enrol(tmp_path).parent == "none"


@pytest.mark.parametrize(
    "header",
    [
        "- **Brief:** brief:missing-brief",
        "- **Brief:** brief:Example-Brief",
        "- **Brief:** docs/product/briefs/missing.md",
        "- **Brief:** docs/product/briefs/sub/x.md",
        "- **Brief:** example-brief",
        "- **Brief:** https://example.test/brief.md",
        "- **Brief:** brief:example-brief and more",
    ],
)
def test_enrol_leaves_unresolvable_values_without_parent(tmp_path: Path, header: str) -> None:
    _plant_brief(tmp_path)
    _plant_spec(tmp_path, header)
    assert _enrol(tmp_path).parent is None


def test_enrol_refuses_a_brief_name_the_pattern_refuses(tmp_path: Path) -> None:
    _plant_brief(tmp_path, "Upper.md")
    _plant_spec(tmp_path, "- **Brief:** docs/product/briefs/Upper.md")
    assert _enrol(tmp_path).parent is None


def test_enrol_refuses_a_brief_that_is_a_link(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere.md"
    target.write_text("x", encoding="utf-8")
    (tmp_path / "docs/product/briefs").mkdir(parents=True)
    Path(tmp_path / _BRIEF).symlink_to(target)
    _plant_spec(tmp_path, "- **Brief:** brief:example-brief")
    assert _enrol(tmp_path).parent is None


def test_enrol_refuses_a_brief_in_a_linked_directory(tmp_path: Path) -> None:
    real = tmp_path / "real-briefs"
    real.mkdir()
    (real / "example-brief.md").write_text("x", encoding="utf-8")
    (tmp_path / "docs/product").mkdir(parents=True)
    Path(tmp_path / "docs/product/briefs").symlink_to(real)
    _plant_spec(tmp_path, "- **Brief:** brief:example-brief")
    assert _enrol(tmp_path).parent is None


def test_enrol_without_a_spec_file_has_no_parent(tmp_path: Path) -> None:
    assert _enrol(tmp_path).parent is None


def test_enrol_with_a_linked_spec_has_no_parent(tmp_path: Path) -> None:
    _plant_brief(tmp_path)
    real = tmp_path / "real-spec.md"
    real.write_text("- **Brief:** brief:example-brief\n", encoding="utf-8")
    (tmp_path / "docs/specs/example").mkdir(parents=True)
    Path(tmp_path / _SPEC).symlink_to(real)
    assert _enrol(tmp_path).parent is None


def test_enrol_with_an_unreadable_spec_has_no_parent(tmp_path: Path) -> None:
    _plant_brief(tmp_path)
    _plant_spec(tmp_path, "- **Brief:** brief:example-brief")
    path = tmp_path / _SPEC
    path.chmod(0)
    try:
        if os.access(path, os.R_OK):
            pytest.skip("permission bits are not enforced for this user")
        assert _enrol(tmp_path).parent is None
    finally:
        path.chmod(0o644)


def test_enrol_with_a_directory_for_a_spec_has_no_parent(tmp_path: Path) -> None:
    (tmp_path / _SPEC).mkdir(parents=True)
    assert _enrol(tmp_path).parent is None


def test_enrol_with_non_utf8_spec_has_no_parent(tmp_path: Path) -> None:
    (tmp_path / _SPEC).parent.mkdir(parents=True)
    (tmp_path / _SPEC).write_bytes(b"- **Brief:** none\n\xff\xfe\n")
    assert _enrol(tmp_path).parent is None


def test_enrol_with_a_repeated_brief_header_has_no_parent(tmp_path: Path) -> None:
    _plant_brief(tmp_path)
    _plant_spec(tmp_path, "- **Brief:** brief:example-brief\n- **Brief:** none")
    assert _enrol(tmp_path).parent is None


@pytest.mark.parametrize("locator", ["docs/specs/example/plan.md", "docs/product/briefs/x.md", "README.md"])
def test_enrol_writes_a_non_spec_locator_as_given(tmp_path: Path, locator: str) -> None:
    _plant_spec(tmp_path, "- **Brief:** none")
    assert _enrol(tmp_path, locator=locator).parent is None


def test_enrol_keeps_a_supplied_parent(tmp_path: Path) -> None:
    _plant_spec(tmp_path, "- **Brief:** none")
    assert _enrol(tmp_path, parent=_BRIEF).parent == _BRIEF


# ---- AC-0025 round trip ---------------------------------------------------------


def _same(before, after) -> None:
    assert after.parent == before.parent
    assert COOLING.canonical_bytes(after).count(b'"parent"') == 1


@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_parse_load_and_canonical_bytes(tmp_path: Path, parent: str) -> None:
    record = COOLING.CoolingRecord.from_payload(_payload(parent=parent))
    raw = COOLING.canonical_bytes(record)
    parsed = COOLING.parse_record_bytes(raw)
    assert parsed.code is None
    _same(record, parsed.record)
    assert COOLING.canonical_bytes(parsed.record) == raw
    _same(record, _enrol(tmp_path, parent=parent))
    # Without `parent` the bytes carry no such key.
    assert b'"parent"' not in COOLING.canonical_bytes(
        COOLING.CoolingRecord.from_payload(_payload())
    )


@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_rename(parent: str) -> None:
    record = COOLING.CoolingRecord.from_payload(_payload(parent=parent))
    renamed = COOLING.record_rename(record, "docs/specs/renamed/spec.md")
    _same(record, renamed)
    assert COOLING.validate_payload(renamed.as_payload()).code is None


def _write_prior(root: Path, parent: str, **payload: object):
    prior = COOLING.CoolingRecord.from_payload(_payload(parent=parent, **payload))
    fixtures = _fixtures(root, prior)
    result = COOLING._write_record(root, root / "docs/lifecycle", prior, fixtures["authority_binding"])
    assert result.code == "enrolled"
    return prior, fixtures


_NOW = datetime(2026, 8, 31, tzinfo=ZoneInfo(_ZONE))
_EXCEPTION = {"reason": "audit-obligation", "owner_role": "release-manager", "review_on": "2026-12-01"}


def _kw(fixtures: dict[str, object]) -> dict[str, object]:
    return {
        "root": fixtures["root"],
        "candidates": fixtures["candidates"],
        "authority_binding": fixtures["authority_binding"],
    }


@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_update_review_and_exception_paths(tmp_path: Path, parent: str) -> None:
    prior, fx = _write_prior(tmp_path, parent)
    proposed = COOLING.CoolingRecord.from_payload(
        prior.as_payload()
        | {"disposition": "cool-30-days", "post_closeout_result": "Retired"}
    )
    updated = COOLING.update_record(prior=prior, proposed=proposed, **_kw(fx))
    assert updated.code == "accepted"
    _same(prior, updated.record)
    on_disk = COOLING.load_record(tmp_path, tmp_path / "docs/lifecycle/spec-example.json")
    _same(prior, on_disk.record)


@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_review(tmp_path: Path, parent: str) -> None:
    prior, fx = _write_prior(tmp_path, parent)
    checks = dict.fromkeys(("completion", "outputs", "active_use", "obligations", "identity", "authority"), "approve")
    attestation = {
        "answers": dict(checks),
        "proposer_role": "release-manager",
        "approver_role": "delivery-approver",
        "human_evidence_ref": "run:31",
    }
    result = COOLING.review(prior, checks, attestation, _NOW, **_kw(fx))
    assert result.code == "accepted"
    _same(prior, result.record)
    refused = dict(checks, identity="refuse")
    attestation["answers"] = dict(refused)
    (tmp_path / "second").mkdir()
    prior2, fx2 = _write_prior(tmp_path / "second", parent)
    retained = COOLING.review(prior2, refused, attestation, _NOW, exception=_EXCEPTION, **_kw(fx2))
    assert retained.code == "accepted"
    _same(prior2, retained.record)


@pytest.mark.parametrize("outcome", ["renew", "confirm-deletion", "advisory", "choose-cooling"])
@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_review_exception(tmp_path: Path, parent: str, outcome: str) -> None:
    prior, fx = _write_prior(
        tmp_path,
        parent,
        disposition="retain-exception",
        post_closeout_result="Retained",
        exception=_EXCEPTION | {"review_on": "2026-10-01"},
    )
    result = COOLING.review_exception(
        prior, outcome, {"exception": _EXCEPTION}, _NOW, **_kw(fx)
    )
    assert result.code == "accepted", result.code
    _same(prior, result.record)


@pytest.mark.parametrize("parent", ["none", _BRIEF])
def test_parent_survives_reclassify(tmp_path: Path, parent: str) -> None:
    prior, fx = _write_prior(
        tmp_path,
        parent,
        disposition="retain-exception",
        post_closeout_result="Retained",
        exception=_EXCEPTION,
    )
    result = COOLING.reclassify_record(prior, dict(_EXCEPTION), **_kw(fx))
    assert result.code == "accepted", result.code
    _same(prior, result.record)
