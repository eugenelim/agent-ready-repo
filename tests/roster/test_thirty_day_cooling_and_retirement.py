"""RFC-0096 Wave 5 — cooling engine construction tests."""

import ast
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[2]
COOLING_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
SCHEMA_PATH = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
SG = "Asia/Singapore"
REQUIRED = (
    "schema", "delivery_id", "locator", "aliases", "fingerprint", "disposition",
    "post_closeout_result", "completion_event", "completion_evidence_ref",
    "completed_on", "timezone", "review_on", "authority", "confirmation_proof",
)


def _load():
    spec = importlib.util.spec_from_file_location("wave5_cooling", COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload(**overrides) -> dict:
    payload = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": "spec-example",
        "locator": "docs/specs/example/spec.md",
        "aliases": [],
        "fingerprint": "sha256:" + "0" * 64,
        "disposition": "cool-30-days",
        "post_closeout_result": "Cooling",
        "completion_event": "merge",
        "completion_evidence_ref": "commit:" + "a" * 40,
        "completed_on": "2026-08-01",
        "timezone": SG,
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


def _record(cooling, **overrides):
    return cooling.CoolingRecord.from_payload(_payload(**overrides))


def _called_attributes(path: Path) -> set[tuple[str, str]]:
    """Alias-resolved (receiver, attribute) pairs for every call in a module.

    Receiver-typed calls (`p.unlink()`) are included by attribute name under the
    receiver's local name, so the matcher sees the form a real implementation
    would use. Shared by AC6 and AC36.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            value = func.value
            root = value.id if isinstance(value, ast.Name) else (
                value.attr if isinstance(value, ast.Attribute) else "<expr>"
            )
            seen.add((root, func.attr))
            seen.add(("<any>", func.attr))
        elif isinstance(func, ast.Name):
            seen.add(("<bare>", func.id))
    return seen


# STUB: AC1
@pytest.mark.parametrize(
    ("start", "zone"),
    [
        (date(2027, 2, 25), "America/New_York"),
        (date(2027, 10, 25), "America/New_York"),
        (date(2028, 2, 14), "UTC"),
        (date(2026, 8, 1), SG),
    ],
)
def test_offset_is_always_thirty_calendar_days(start: date, zone: str) -> None:
    cooling = _load()
    assert (cooling.compute_review_on(start, zone) - start).days == 30


# STUB: AC2
@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 8, 30, 23, 59, tzinfo=ZoneInfo(SG)), False),
        (datetime(2026, 8, 31, 0, 0, tzinfo=ZoneInfo(SG)), True),
        (datetime(2026, 9, 1, 0, 0, tzinfo=ZoneInfo(SG)), True),
    ],
)
@pytest.mark.parametrize("reader", ["UTC", "America/New_York", "Australia/Sydney"])
def test_dueness_flips_at_local_midnight_for_every_reader(
    moment: datetime, expected: bool, reader: str
) -> None:
    cooling = _load()
    seen = moment.astimezone(ZoneInfo(reader))
    assert cooling.is_due(_record(cooling), seen).due is expected


# STUB: AC3
def test_late_closeout_keeps_the_supplied_event_date() -> None:
    cooling = _load()
    record = _record(cooling, completed_on="2026-06-01", review_on="2026-07-01")
    result = cooling.is_due(record, datetime(2026, 7, 11, 12, 0, tzinfo=ZoneInfo(SG)))
    assert record.completed_on == date(2026, 6, 1)
    assert result.due is True


# STUB: AC4
def test_a_due_record_carries_no_permission() -> None:
    cooling = _load()
    result = cooling.is_due(_record(cooling), datetime(2026, 9, 30, tzinfo=ZoneInfo(SG)))
    assert (result.due, result.permission_granted, result.mutated) == (True, False, ())


# STUB: AC5
def test_invalid_temporal_input_returns_a_named_code() -> None:
    cooling = _load()
    assert cooling.is_due(_record(cooling), datetime(2026, 9, 30, 12, 0)).code == "naive-clock"
    assert cooling.compute_review_on(date(2026, 8, 1), "Not/AZone").code == "unknown-timezone"


# STUB: AC6
def test_cooling_module_calls_no_clock() -> None:
    called = _called_attributes(COOLING_PATH)
    for receiver, attribute in (
        ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
        ("date", "today"), ("time", "time"), ("time", "monotonic"),
        ("time", "perf_counter"), ("os", "times"),
    ):
        assert (receiver, attribute) not in called
        assert ("<bare>", attribute) not in called
        # The receiver-typed form is the one a real implementation reaches for:
        # `dt = datetime; dt.now()` binds a local name the two checks above
        # never see. Asserting the attribute under any receiver is what makes
        # this guard able to fail; without it a mutant passes.
        assert ("<any>", attribute) not in called


# STUB: AC7
def test_schema_requires_the_rfc_field_set_and_closes_every_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["contract_version"] == "delivery-lifecycle-record.v1"
    assert schema["x-spec"] == ["docs/specs/thirty-day-cooling-and-retirement/"]
    assert set(schema["required"]) == set(REQUIRED)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert node.get("required")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)


# STUB: AC8
def test_a_valid_payload_is_accepted() -> None:
    cooling = _load()
    assert cooling.validate_payload(_payload()).code is None


# STUB: AC8
@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(surprise="x"),
        lambda p: p["authority"]["write"].update(surprise="x"),
        lambda p: p["exception"].update(surprise="x"),
    ],
)
def test_an_undeclared_key_refuses_at_every_level(mutate) -> None:
    cooling = _load()
    payload = _payload(
        disposition="retain-exception",
        post_closeout_result="Retained",
        exception={"reason": "audit-obligation", "owner_role": "release-manager",
                   "review_on": "2026-12-01"},
    )
    mutate(payload)
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC9
@pytest.mark.parametrize("key", REQUIRED)
def test_a_missing_required_key_refuses(key: str) -> None:
    cooling = _load()
    payload = _payload()
    del payload[key]
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC10
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("delivery_id", "a/b"),
        ("delivery_id", ".."),
        ("completion_evidence_ref", "author:jane-doe"),
        ("completion_evidence_ref", "owner:j.doe"),
        ("confirmation_proof", "approved by a.person@example.com"),
    ],
)
def test_a_value_outside_its_pattern_refuses(field: str, value: str) -> None:
    cooling = _load()
    assert cooling.validate_payload(_payload(**{field: value})).code == "record-invalid"


# STUB: AC11
def test_the_filename_must_equal_the_delivery_id(tmp_path) -> None:
    cooling = _load()
    path = tmp_path / "spec-a.json"
    path.write_bytes(json.dumps(_payload(delivery_id="spec-b")).encode() + b"\n")
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


# STUB: AC12
def test_serialization_is_canonical_not_merely_deterministic() -> None:
    cooling = _load()
    ordered = _payload()
    shuffled = dict(reversed(list(ordered.items())))
    assert cooling.canonical_bytes(cooling.CoolingRecord.from_payload(shuffled)) == (
        cooling.canonical_bytes(cooling.CoolingRecord.from_payload(ordered))
    )
    assert cooling.canonical_bytes(_record(cooling)).endswith(b"\n")


# STUB: AC12
def test_a_non_finite_value_refuses() -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(b'{"completed_on": NaN}').code == "record-invalid"


# STUB: AC13
def test_canonical_bytes_are_accepted_by_the_parser() -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(cooling.canonical_bytes(_record(cooling))).code is None


# STUB: AC13
def test_oversized_and_over_nested_input_refuses_without_raising() -> None:
    cooling = _load()
    oversized = _payload(aliases=["docs/specs/x/" + "a" * 200 + ".md"] * 400)
    assert cooling.parse_record_bytes(
        json.dumps(oversized).encode() + b"\n"
    ).code == "record-invalid"

    nested: dict = {"authority": {}}
    cursor = nested["authority"]
    for _ in range(12):
        cursor["source"] = {}
        cursor = cursor["source"]
    assert cooling.parse_record_bytes(
        json.dumps(_payload(**nested)).encode() + b"\n"
    ).code == "record-invalid"


def _destination(root: Path) -> Path:
    """Return the only lifecycle directory used by the write tests."""
    return root / "docs/lifecycle"


_TRANSITION_TABLE = (
    (("cool-30-days", "Cooling"), ("cool-30-days", "Retired")),
    (("cool-30-days", "Cooling"), ("retain-exception", "Retained")),
    (("retain-exception", "Retained"), ("retain-exception", "Retained")),
    (("retain-exception", "Retained"), ("cool-30-days", "Cooling")),
    (("retain-exception", "Retained"), ("retain-exception", "Retired")),
    (("retain-exception", "Retained"), ("retain-exception", "ExternalAdvisory")),
)
_TRANSITION_COMPLEMENT = tuple(
    (prior, proposed)
    for prior in (
        ("cool-30-days", "Cooling"),
        ("cool-30-days", "Retired"),
        ("retain-exception", "Retained"),
        ("retain-exception", "Retired"),
        ("retain-exception", "ExternalAdvisory"),
    )
    for proposed in (
        ("cool-30-days", "Cooling"),
        ("cool-30-days", "Retired"),
        ("retain-exception", "Retained"),
        ("retain-exception", "Retired"),
        ("retain-exception", "ExternalAdvisory"),
    )
    if (prior, proposed) not in _TRANSITION_TABLE
)


def _candidate(cooling, root: Path, *, confirmation: str, declared_writability: str | None):
    close_work = cooling._close_work()
    resolver = close_work.surface_resolver()
    return resolver.SurfaceCandidate(
        role="runtime-coordination",
        logical_locator="docs/lifecycle",
        physical_locator=resolver.Locator("repository-path", "docs/lifecycle"),
        provenance=(resolver.Evidence("explicit", "request:cooling", "explicit"),),
        availability="available",
        writability=declared_writability or "writable",
        authority=resolver.Authority(
            source=resolver.AuthorityFact("repository-owned", "authority:source"),
            write=resolver.AuthorityFact("delegated", "authority:write"),
            delete=resolver.AuthorityFact("none", "authority:delete"),
        ),
        revision_or_fingerprint="lifecycle-v1",
        confirmations=(resolver.Confirmation("destination-selection", confirmation),),
    )


def _binding(cooling, resource: str):
    close_work = cooling._close_work()
    fact = close_work.resolve_mutation_authority(
        grant_record={
            "authorized_actor_role": "release-manager",
            "grant_source": "approval:release",
            "action": "write-lifecycle-record",
            "resource": resource,
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
    return binding


def _enrol_kwargs(
    root: Path,
    *,
    make_destination: bool = True,
    candidates: object = "confirmed",
    declared_writability: str | None = None,
    authority_binding: object = "issued",
) -> dict[str, object]:
    cooling = _load()
    destination = _destination(root)
    if make_destination:
        destination.mkdir(parents=True, exist_ok=True)
    record = _record(cooling)
    resolved_candidates: object
    if candidates == "confirmed":
        resolved_candidates = (_candidate(
            cooling, root, confirmation="confirmed", declared_writability=declared_writability
        ),)
    elif candidates == "unconfirmed":
        resolved_candidates = (_candidate(
            cooling, root, confirmation="required", declared_writability=declared_writability
        ),)
    else:
        resolved_candidates = candidates
    resource = "docs/lifecycle/spec-example.json"
    return {
        "root": root,
        "record": record,
        "delivered": True,
        "closed": True,
        "persisted": True,
        "completion_event": "merge",
        "candidates": resolved_candidates,
        "authority_binding": (
            _binding(cooling, resource) if authority_binding == "issued" else authority_binding
        ),
    }


def _update_kwargs(root: Path, prior: tuple[str, str], proposed: tuple[str, str]) -> dict[str, object]:
    cooling = _load()
    destination = _destination(root)
    destination.mkdir(parents=True, exist_ok=True)
    prior_record = _record(
        cooling, disposition=prior[0], post_closeout_result=prior[1],
        exception=(
            {"reason": "audit-obligation", "owner_role": "release-manager", "review_on": "2026-12-01"}
            if prior[0] == "retain-exception" else None
        ),
    )
    proposed_record = _record(
        cooling, disposition=proposed[0], post_closeout_result=proposed[1],
        exception=(
            {"reason": "audit-obligation", "owner_role": "release-manager", "review_on": "2026-12-01"}
            if proposed[0] == "retain-exception" else None
        ),
    )
    return {
        "root": root,
        "prior": prior_record,
        "proposed": proposed_record,
        "candidates": (_candidate(cooling, root, confirmation="confirmed", declared_writability=None),),
        "authority_binding": _binding(cooling, "docs/lifecycle/spec-example.json"),
    }


# STUB: AC14
@pytest.mark.parametrize(
    ("facts", "code"),
    [
        ({"delivered": False}, "not-delivered"),
        ({"closed": False}, "not-closed"),
        ({"persisted": False}, "no-persistent-record"),
        ({"completion_event": None}, "completion-event-required"),
        ({"completion_event": "creation"}, "completion-event-required"),
        ({"completion_event": "ready"}, "completion-event-required"),
        ({"completion_event": "edit"}, "completion-event-required"),
        ({"completion_event": "session-end"}, "completion-event-required"),
    ],
)
def test_each_enrolment_precondition_has_its_own_code(tmp_path, facts, code) -> None:
    cooling = _load()
    result = cooling.enrol(**_enrol_kwargs(tmp_path) | facts)
    assert result.code == code
    assert result.mutated == ()


# STUB: AC15
@pytest.mark.parametrize("candidates", [(), "unconfirmed"])
def test_an_unconfirmed_destination_refuses(tmp_path, candidates) -> None:
    cooling = _load()
    result = cooling.enrol(**_enrol_kwargs(tmp_path, candidates=candidates))
    assert result.code == "destination-unconfirmed"
    assert list(_destination(tmp_path).iterdir()) == []


# STUB: AC16
def test_absent_destination_refuses_and_present_destination_enrols(tmp_path) -> None:
    cooling = _load()
    absent = cooling.enrol(**_enrol_kwargs(tmp_path, make_destination=False))
    assert absent.code == "lifecycle-state-unwritable"
    assert not _destination(tmp_path).exists()

    created = cooling.enrol(**_enrol_kwargs(tmp_path))
    assert created.code == "enrolled"
    assert (_destination(tmp_path) / "spec-example.json").is_file()


# STUB: AC17
@pytest.mark.parametrize("declared", [None, "writable"])
def test_a_declared_attribute_cannot_make_a_destination_writable(tmp_path, declared) -> None:
    import os as _os

    if _os.geteuid() == 0:
        pytest.skip("root writes through mode 0o555; the case cannot fail here")
    cooling = _load()
    destination = _destination(tmp_path)
    destination.mkdir(parents=True)
    destination.chmod(0o555)
    try:
        result = cooling.enrol(
            **_enrol_kwargs(tmp_path, make_destination=False, declared_writability=declared)
        )
        assert result.code == "lifecycle-state-unwritable"
        assert list(destination.iterdir()) == []
    finally:
        destination.chmod(0o755)


# STUB: AC18
def test_a_swapped_parent_leaves_no_bytes_anywhere(tmp_path) -> None:
    """The escape target must be outside the repository root, not merely elsewhere.

    A symlink pointing at a sibling *inside* the root is not an escape: the
    resolver realpath-resolves it and the write legitimately follows to the real
    directory. Nesting the root under tmp_path is what makes `outside` genuinely
    outside it, so this fixture exercises AC18 rather than passing on a refusal
    raised for an unrelated reason.
    """
    cooling = _load()
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = _destination(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(outside, target_is_directory=True)
    result = cooling.enrol(**_enrol_kwargs(root, make_destination=False))
    assert result.code == "unsafe-target"
    assert list(outside.iterdir()) == []
    assert result.mutated == ()


# STUB: AC19
@pytest.mark.parametrize(
    "binding",
    [
        None,
        "never-issued",
        {"action": "write-pause-overlay"},
        {"resource": "docs/lifecycle/spec-other.json"},
    ],
)
def test_the_write_must_be_authorized_for_this_record(tmp_path, binding) -> None:
    cooling = _load()
    result = cooling.enrol(**_enrol_kwargs(tmp_path, authority_binding=binding))
    assert result.code == "authority-uncertain"
    assert list(_destination(tmp_path).iterdir()) == []


# STUB: AC20
def test_refusals_carry_a_code_and_leak_nothing(tmp_path) -> None:
    cooling = _load()
    result = cooling.enrol(**_enrol_kwargs(tmp_path, make_destination=False))
    assert result.code in cooling.REFUSAL_CODES
    rendered = repr(result.as_dict())
    assert str(tmp_path) not in rendered
    for leak in ("Traceback", "errno", "Errno"):
        assert leak not in rendered


# STUB: AC21
def test_a_stale_review_on_refuses(tmp_path) -> None:
    cooling = _load()
    path = _destination(tmp_path) / "spec-example.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(json.dumps(_payload(review_on="2026-12-31")).encode() + b"\n")
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


# STUB: AC22
@pytest.mark.parametrize(("prior", "proposed"), _TRANSITION_TABLE)
def test_every_listed_transition_is_accepted(tmp_path, prior, proposed) -> None:
    cooling = _load()
    assert cooling.update_record(**_update_kwargs(tmp_path, prior, proposed)).code == "accepted"


# STUB: AC22
@pytest.mark.parametrize(("prior", "proposed"), _TRANSITION_COMPLEMENT)
def test_every_unlisted_transition_refuses(tmp_path, prior, proposed) -> None:
    cooling = _load()
    result = cooling.update_record(**_update_kwargs(tmp_path, prior, proposed))
    assert result.code == "record-invalid"


# STUB: AC23
def test_an_update_survives_the_process(tmp_path) -> None:
    import subprocess
    import sys

    cooling = _load()
    cooling.enrol(**_enrol_kwargs(tmp_path))
    cooling.update_record(
        **_update_kwargs(tmp_path, ("cool-30-days", "Cooling"), ("cool-30-days", "Retired"))
    )
    path = _destination(tmp_path) / "spec-example.json"
    program = (
        "import importlib.util,sys;"
        "s=importlib.util.spec_from_file_location('c', sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "r=m.load_record(sys.argv[2], sys.argv[3]);"
        "sys.stdout.buffer.write(m.canonical_bytes(r.record))"
    )
    proof = subprocess.run(
        [sys.executable, "-c", program, str(COOLING_PATH), str(tmp_path), str(path)],
        capture_output=True, check=True,
    )
    assert proof.stdout == path.read_bytes()


# STUB: AC24
def test_workspace_toml_holds_no_cooling_state() -> None:
    import tomllib

    data = tomllib.loads((ROOT / "workspace.toml").read_text(encoding="utf-8"))
    forbidden = {"cooling", "review_on", "completed_on", "lifecycle_record"}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            assert forbidden.isdisjoint(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)


def test_the_destination_comes_from_the_validated_physical_locator(tmp_path) -> None:
    """The resolver path-validates only the physical locator.

    `_validate_logical_locator` checks bounded safe text; `_validate_repository_path`
    is what rejects a leading separator, a drive letter, a backslash, and any
    empty, "." or ".." segment — and it runs on the physical locator alone. A
    candidate may therefore resolve with an escaping logical locator, so the
    write path must derive its destination from the physical one. Building it
    from the logical locator instead only fails closed because the descriptor
    walk rejects ".." afterwards, which makes the confinement depend on a second
    guard rather than on using the value that was checked.
    """
    cooling = _load()
    close_work = cooling._close_work()
    resolver = close_work.surface_resolver()
    destination = _destination(tmp_path)
    destination.mkdir(parents=True, exist_ok=True)

    escaping = resolver.SurfaceCandidate(
        role="runtime-coordination",
        logical_locator="../ESCAPED",
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
    assert resolver.resolve_surface(tmp_path, "runtime-coordination", (escaping,)).status == (
        "resolved"
    ), "precondition: the resolver admits an escaping logical locator"

    result = cooling.enrol(**_enrol_kwargs(tmp_path, candidates=(escaping,)))

    assert result.code == "enrolled"
    assert (destination / "spec-example.json").is_file()
    assert not (tmp_path.parent / "ESCAPED").exists()
