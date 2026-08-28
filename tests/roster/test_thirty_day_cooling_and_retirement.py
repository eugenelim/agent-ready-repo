"""RFC-0096 Wave 5 — cooling engine construction tests."""

import ast
import hashlib
import importlib.util
import json
import shutil
import subprocess
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
def test_input_past_the_byte_ceiling_refuses() -> None:
    """Isolate MAX_RECORD_BYTES from every other validator.

    The earlier fixture padded `aliases` to 400 entries, which the 16-alias cap
    already refuses, so the byte ceiling was deletable with the suite green.
    Insignificant JSON whitespace grows the encoded bytes past the ceiling while
    leaving a payload every field-level validator accepts, which makes the byte
    bound the only thing that can produce the refusal.
    """
    cooling = _load()
    valid = cooling.canonical_bytes(_record(cooling))
    assert cooling.parse_record_bytes(valid).code is None
    assert len(valid) < cooling.MAX_RECORD_BYTES

    padded = b"  " * cooling.MAX_RECORD_BYTES + valid
    assert len(padded) > cooling.MAX_RECORD_BYTES
    assert json.loads(padded.decode()) == json.loads(valid.decode())

    assert cooling.parse_record_bytes(padded).code == "record-invalid"


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
    # Seed the prior on disk. update_record is a compare-and-swap against
    # persisted state, so a transition test that never writes the prior is
    # asserting over its own arguments — which is exactly how `Retired` stopped
    # being terminal without any test noticing.
    (destination / f"{prior_record.delivery_id}.json").write_bytes(
        cooling.canonical_bytes(prior_record)
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


def _well_formed_binding(cooling, *, action: str, resource: str, issued: bool):
    """Build a real MutationBinding, optionally one the seam never registered.

    AC19's earlier fixtures were plain dicts, so every one of them died on the
    `isinstance` guard and none reached the resource comparison or the
    issued-fact loop. A binding has to be genuine to exercise the half of AC19
    that says "for this exact record".
    """
    close_work = cooling._close_work()
    fields = {
        "authorized_actor_role": "release-manager",
        "grant_source": "approval:release",
        "action": action,
        "resource": resource,
        "evidence_ref": "authority:write",
        "host_session_provenance": "host-session:pytest",
    }
    fact = close_work.resolve_mutation_authority(
        grant_record=dict(fields), authority_evidence_ref="authority-resolution:pytest"
    )
    assert fact is not None
    binding = close_work._mutation_binding(
        authority_fact=fact, expected_action=action, **fields
    )
    assert binding is not None
    if not issued:
        # Drop the fact from the registry: the binding object stays well formed
        # while ceasing to be reproducible from an issued authority.
        close_work._ISSUED_COORDINATION_AUTHORITIES.pop(fact.issue_digest, None)
    return binding


# STUB: AC19
@pytest.mark.parametrize(
    "shape",
    ["absent", "never-issued", "wrong-action", "wrong-resource"],
)
def test_the_write_must_be_authorized_for_this_record(tmp_path, shape: str) -> None:
    cooling = _load()
    mine = "docs/lifecycle/spec-example.json"
    binding = {
        "absent": lambda: None,
        "never-issued": lambda: _well_formed_binding(
            cooling, action="write-lifecycle-record", resource=mine, issued=False
        ),
        "wrong-action": lambda: _well_formed_binding(
            cooling, action="write-pause-overlay", resource=mine, issued=True
        ),
        "wrong-resource": lambda: _well_formed_binding(
            cooling, action="write-lifecycle-record",
            resource="docs/lifecycle/spec-other.json", issued=True,
        ),
    }[shape]()

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


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run Git with a generic per-invocation committing identity."""
    return subprocess.run(
        [
            "git", "-c", "user.email=cooling@example.invalid",
            "-c", "user.name=Cooling Fixture", *arguments,
        ],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )


def _build_repository(tmp_path: Path, topology: str):
    """Create an actual history rewrite only after persisting the record."""
    if shutil.which("git") is None:
        pytest.skip("git is unavailable; AC25 requires real Git topology fixtures")

    cooling = _load()
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init")
    base = _git(origin, "branch", "--show-current").stdout.strip()
    artifact = origin / "docs/specs/example/spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Example\n", encoding="utf-8")
    _git(origin, "add", ".")
    _git(origin, "commit", "-m", "base artifact")

    locator = "docs/specs/example/spec.md"
    record = _record(
        cooling,
        locator=locator,
        fingerprint="sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
    )
    lifecycle = origin / "docs/lifecycle/spec-example.json"
    lifecycle.parent.mkdir(parents=True)
    lifecycle.write_bytes(cooling.canonical_bytes(record))
    _git(origin, "add", "docs/lifecycle/spec-example.json")
    _git(origin, "commit", "-m", "persist cooling record")

    if topology == "shallow":
        clone = tmp_path / "shallow"
        _git(tmp_path, "clone", "--depth=1", origin.as_uri(), str(clone))
        return clone, record

    _git(origin, "switch", "-c", "topology-change")
    (origin / "topology.txt").write_text(f"{topology}\n", encoding="utf-8")
    _git(origin, "add", "topology.txt")
    _git(origin, "commit", "-m", "topology-side change")

    if topology == "squash":
        _git(origin, "switch", base)
        _git(origin, "merge", "--squash", "topology-change")
        _git(origin, "commit", "-m", "squash topology change")
    elif topology == "merge":
        _git(origin, "switch", base)
        _git(origin, "merge", "--no-ff", "topology-change", "-m", "merge topology change")
    elif topology == "rebase":
        _git(origin, "switch", base)
        (origin / "base.txt").write_text("moved base\n", encoding="utf-8")
        _git(origin, "add", "base.txt")
        _git(origin, "commit", "-m", "move base")
        _git(origin, "switch", "topology-change")
        _git(origin, "rebase", base)
    elif topology == "no-git":
        shutil.rmtree(origin / ".git")
    else:
        raise ValueError(f"unknown topology: {topology}")
    return origin, record


def _permission_inputs(
    tmp_path: Path, scenario: str, *, live_grant: dict[str, object] | None = "default"
) -> dict[str, object]:
    """Return independently controllable proofs for deletion eligibility tests."""
    cooling = _load()
    artifact = tmp_path / "docs/specs/example/spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Example\n", encoding="utf-8")
    locator = "docs/specs/example/spec.md"
    record = _record(
        cooling,
        locator=locator,
        fingerprint="sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
        authority={
            "source": {"status": "repository-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "delegated", "evidence_ref": "authority:delete"},
        },
    )
    if scenario == "drift":
        artifact.write_text("# Changed\n", encoding="utf-8")
    elif scenario == "missing-locator":
        artifact.unlink()
    elif scenario == "unresolvable-evidence":
        record = _record(
            cooling,
            locator=locator,
            fingerprint="sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
            completion_evidence_ref="commit:" + "b" * 40,
            authority={
                "source": {"status": "repository-owned"},
                "write": {"status": "delegated"},
                "delete": {"status": "delegated", "evidence_ref": "authority:delete"},
            },
        )
    elif scenario == "unknown-authority-status":
        record = _record(
            cooling,
            locator=locator,
            fingerprint="sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
            authority={
                "source": {"status": "repository-owned"},
                "write": {"status": "delegated"},
                "delete": {"status": "banana", "evidence_ref": "authority:delete"},
            },
        )
    elif scenario != "all-proofs":
        raise ValueError(f"unknown permission scenario: {scenario}")

    if live_grant == "default":
        live_grant = {
            "authorized_actor_role": "release-manager",
            "grant_source": "approval:release",
            "action": "delete-confirmed-file-set",
            "resource": locator,
            "evidence_ref": "authority:delete",
            "host_session_provenance": "host-session:pytest",
        }
    return {
        "root": tmp_path,
        "record": record,
        "completion_evidence_resolver": lambda reference: reference == "commit:" + "a" * 40,
        "live_grant": live_grant,
        "authority_evidence_ref": "authority-resolution:pytest",
    }


# STUB: AC25
@pytest.mark.parametrize("topology", ["squash", "merge", "rebase", "shallow", "no-git"])
def test_identity_survives_five_history_shapes(tmp_path, topology: str) -> None:
    cooling = _load()
    root, record = _build_repository(tmp_path, topology)
    assert cooling.verify_identity(root, record).code == "identity-verified"


# STUB: AC26
def test_a_rename_keeps_the_old_locator() -> None:
    cooling = _load()
    original = _record(cooling)
    renamed = cooling.record_rename(original, "docs/specs/renamed/spec.md")
    assert renamed.locator == "docs/specs/renamed/spec.md"
    assert original.locator in renamed.aliases


# STUB: AC27
@pytest.mark.parametrize(
    ("scenario", "code"),
    [
        ("all-proofs", "deletion-permitted"),
        ("drift", "fingerprint-drift"),
        ("missing-locator", "locator-unresolved"),
        ("unresolvable-evidence", "missing-history"),
        ("unknown-authority-status", "authority-uncertain"),
    ],
)
def test_permission_is_granted_never_inferred(tmp_path, scenario: str, code: str) -> None:
    cooling = _load()
    assert cooling.deletion_allowed(**_permission_inputs(tmp_path, scenario)).code == code


# STUB: AC28
def test_missing_history_is_about_evidence_not_git(tmp_path) -> None:
    cooling = _load()
    inputs = _permission_inputs(tmp_path, "all-proofs")
    assert cooling.deletion_allowed(**inputs).code != "missing-history"


# STUB: AC29
def test_persisted_authority_is_a_hint_not_a_grant(tmp_path) -> None:
    cooling = _load()
    inputs = _permission_inputs(tmp_path, "all-proofs", live_grant=None)
    assert cooling.deletion_allowed(**inputs).code == "authority-uncertain"


# STUB: AC30
def test_source_authority_is_not_deletion_authority(tmp_path) -> None:
    cooling = _load()
    inputs = _permission_inputs(tmp_path, "all-proofs")
    payload = inputs["record"].as_payload()
    payload["authority"] = {
        "source": {"status": "external-owned"},
        "write": {"status": "delegated"},
        "delete": {"status": "none"},
    }
    inputs["record"] = cooling.CoolingRecord.from_payload(payload)
    assert cooling.deletion_allowed(**inputs).code == "authority-uncertain"


def _all_approve() -> dict[str, str]:
    """Return a complete approving day-30 review response."""
    return {
        "completion": "approve",
        "outputs": "approve",
        "active_use": "approve",
        "obligations": "approve",
        "identity": "approve",
        "authority": "approve",
    }


def _exception(**overrides: str) -> dict[str, str]:
    """Return a valid exception envelope for retained work."""
    envelope = {
        "reason": "audit-obligation",
        "owner_role": "release-manager",
        "review_on": "2026-10-01",
    }
    envelope.update(overrides)
    return envelope


def _attestation(checks: dict[str, str]) -> dict[str, object]:
    """Return a second party's exact review attestation."""
    return {
        "answers": checks.copy(),
        "proposer_role": "release-manager",
        "approver_role": "delivery-approver",
        "human_evidence_ref": "run:31",
    }


def _review_kwargs(
    root: Path,
    checks: dict[str, str],
    *,
    attestation: str | dict[str, object] = "valid",
    exception: dict[str, str] | None = None,
) -> dict[str, object]:
    """Persist a cooling record and return the inputs for a due review."""
    cooling = _load()
    enrolment = _enrol_kwargs(root)
    assert cooling.enrol(**enrolment).code == "enrolled"
    supplied_attestation = _attestation(checks)
    if attestation == "missing-answers":
        del supplied_attestation["answers"]
    elif attestation == "missing-approver":
        del supplied_attestation["approver_role"]
    elif attestation == "missing-evidence":
        del supplied_attestation["human_evidence_ref"]
    elif attestation == "answers-differ":
        supplied_attestation["answers"] = checks | {"identity": "refuse"}
    elif attestation == "approver-equals-proposer":
        supplied_attestation["approver_role"] = "release-manager"
    elif attestation != "valid":
        raise ValueError(f"unknown attestation fixture: {attestation}")
    return {
        "root": root,
        "record": enrolment["record"],
        "checks": checks,
        "attestation": supplied_attestation,
        "now": datetime(2026, 8, 31, tzinfo=ZoneInfo(SG)),
        "exception": exception,
        "candidates": enrolment["candidates"],
        "authority_binding": enrolment["authority_binding"],
    }


def _exception_kwargs(root: Path, outcome: str) -> dict[str, object]:
    """Persist a retained record and return the inputs for exception review."""
    cooling = _load()
    enrolment = _enrol_kwargs(root)
    prior = cooling.CoolingRecord.from_payload(
        enrolment["record"].as_payload()
        | {
            "disposition": "retain-exception",
            "post_closeout_result": "Retained",
            "exception": _exception(),
        }
    )
    assert cooling._write_record(
        root, _destination(root), prior, enrolment["authority_binding"]
    ).code == "enrolled"
    return {
        "root": root,
        "record": prior,
        "outcome": outcome,
        "attestation": {"exception": _exception(review_on="2026-11-01")},
        "now": datetime(2026, 8, 31, tzinfo=ZoneInfo(SG)),
        "candidates": enrolment["candidates"],
        "authority_binding": enrolment["authority_binding"],
    }


# STUB: AC31
@pytest.mark.parametrize(
    "omitted",
    ["completion", "outputs", "active_use", "obligations", "identity", "authority"],
)
def test_all_six_answers_are_required(tmp_path, omitted: str) -> None:
    cooling = _load()
    checks = _all_approve()
    del checks[omitted]
    assert cooling.review(**_review_kwargs(tmp_path, checks)).code == "review-incomplete"


# STUB: AC32
@pytest.mark.parametrize(
    "attestation",
    ["missing-answers", "missing-approver", "missing-evidence", "answers-differ",
     "approver-equals-proposer"],
)
def test_the_attestation_must_carry_a_humans_own_answers(tmp_path, attestation: str) -> None:
    cooling = _load()
    kwargs = _review_kwargs(tmp_path, _all_approve(), attestation=attestation)
    assert cooling.review(**kwargs).code == "review-incomplete"


# STUB: AC33
def test_approval_retires_and_persists(tmp_path) -> None:
    cooling = _load()
    result = cooling.review(**_review_kwargs(tmp_path, _all_approve()))
    assert result.record.post_closeout_result == "Retired"
    path = _destination(tmp_path) / "spec-example.json"
    assert cooling.load_record(tmp_path, path).record.post_closeout_result == "Retired"


# STUB: AC34
@pytest.mark.parametrize("answer", ["refuse", "uncertain"])
def test_refusal_or_uncertainty_produces_a_complete_exception(tmp_path, answer: str) -> None:
    cooling = _load()
    checks = _all_approve() | {"obligations": answer}
    result = cooling.review(**_review_kwargs(tmp_path, checks, exception=_exception()))
    assert result.record.disposition == "retain-exception"
    assert set(dict(result.record.exception)) >= {"reason", "owner_role", "review_on"}


# STUB: AC34
@pytest.mark.parametrize("missing", ["reason", "owner_role", "review_on"])
def test_an_incomplete_exception_envelope_refuses(tmp_path, missing: str) -> None:
    cooling = _load()
    envelope = _exception()
    del envelope[missing]
    checks = _all_approve() | {"obligations": "refuse"}
    result = cooling.review(**_review_kwargs(tmp_path, checks, exception=envelope))
    assert result.code == "exception-envelope-invalid"


# STUB: AC35
@pytest.mark.parametrize(
    ("outcome", "target"),
    [
        ("confirm-deletion", ("retain-exception", "Retired")),
        ("renew", ("retain-exception", "Retained")),
        ("choose-cooling", ("cool-30-days", "Cooling")),
        ("advisory", ("retain-exception", "ExternalAdvisory")),
    ],
)
def test_exception_review_maps_each_outcome_to_a_table_pair(tmp_path, outcome, target) -> None:
    cooling = _load()
    result = cooling.review_exception(**_exception_kwargs(tmp_path, outcome))
    assert result.code == "accepted"
    assert (result.record.disposition, result.record.post_closeout_result) == target


# STUB: AC35
def test_an_unlisted_exception_outcome_refuses(tmp_path) -> None:
    cooling = _load()
    result = cooling.review_exception(**_exception_kwargs(tmp_path, "delete-now"))
    assert result.code == "exception-envelope-invalid"


# STUB: AC36
def test_cooling_module_removes_nothing_but_its_temp_file() -> None:
    called = _called_attributes(COOLING_PATH)
    for attribute in ("remove", "rmdir", "removedirs", "rmtree"):
        assert ("<any>", attribute) not in called
        assert ("<bare>", attribute) not in called
    source = COOLING_PATH.read_text(encoding="utf-8")
    assert source.count("unlink") == 1, "only the named temp-file cleanup may unlink"
    assert "os.unlink(temporary, dir_fd=" in source


# STUB: AC39
def test_instructional_surfaces_describe_the_shipped_cooling_engine() -> None:
    """Each Wave 5 surface gains its replacement claim and loses the stale one."""
    pairs = (
        (
            "guides/core/how-to/close-and-disposition-work.md",
            "Wave 5 computes the review date and enrols the record",
            "It does not calculate dates, start a timer, or retire anything",
        ),
        (
            "guides/core/reference/work-intake-routing-and-lifecycle.md",
            "| Disposition | Result |",
            "| Disposition | Wave 4 result |",
        ),
        (
            "guides/core/reference/work-intake-routing-and-lifecycle.md",
            "Enrol, compute the review date, and review on day 30",
            "Wave 5 owns dates, clocks, due state, and retirement",
        ),
        (
            "guides/core/reference/workspace-toml-schema.md",
            "workspace.toml may point at cooling state and never owns it",
            "gains no receipt or cooling schema in Wave 4",
        ),
        (
            "packs/core/README.md",
            "cooling records live outside workspace.toml",
            "`cool-30-days` is classification only in this release",
        ),
        (
            "packs/core/.apm/skills/close-work/SKILL.md",
            "Enrol, then answer whether the record is due",
            "Do not start a timer",
        ),
    )
    for relative_path, replacement, superseded in pairs:
        surface = (ROOT / relative_path).read_text(encoding="utf-8")
        assert replacement in surface, relative_path
        assert superseded not in surface, relative_path


def test_enrolment_refuses_to_overwrite_an_existing_record(tmp_path) -> None:
    """AC22 over persisted state, not over arguments.

    A second enrol used to clobber whatever was on disk, silently resetting a
    Retired record to Cooling and discarding a retain-exception retention
    decision. The transition table cannot protect a record the writer never
    reads.
    """
    cooling = _load()
    _destination(tmp_path).mkdir(parents=True)
    assert cooling.enrol(**_enrol_kwargs(tmp_path)).code == "enrolled"

    second = cooling.enrol(**_enrol_kwargs(tmp_path, make_destination=False))

    assert second.code == "record-invalid"
    assert second.mutated == ()


def test_update_refuses_a_prior_that_does_not_match_disk(tmp_path) -> None:
    """A stale or fabricated prior must not drive a forbidden transition.

    With the check over arguments alone, passing prior=(cool-30-days, Cooling)
    against a Retired record on disk returned `accepted` and reopened a terminal
    state.
    """
    cooling = _load()
    destination = _destination(tmp_path)
    destination.mkdir(parents=True)
    retired = _record(cooling, post_closeout_result="Retired")
    (destination / "spec-example.json").write_bytes(cooling.canonical_bytes(retired))

    kwargs = _update_kwargs(
        tmp_path, ("cool-30-days", "Cooling"), ("retain-exception", "Retained")
    )
    # _update_kwargs seeds its own prior; put the terminal record back so the
    # supplied prior genuinely disagrees with disk.
    (destination / "spec-example.json").write_bytes(cooling.canonical_bytes(retired))

    result = cooling.update_record(**kwargs)

    assert result.code == "record-invalid"
    reloaded = cooling.load_record(tmp_path, destination / "spec-example.json")
    assert reloaded.record.post_closeout_result == "Retired"


def test_the_writer_refuses_a_record_the_reader_would_reject(tmp_path) -> None:
    """`enrolled` must never mean "written and permanently unreadable"."""
    cooling = _load()
    _destination(tmp_path).mkdir(parents=True)
    kwargs = _enrol_kwargs(tmp_path, make_destination=False)
    kwargs["record"] = _record(cooling, review_on="2026-12-31")  # not completed_on + 30

    result = cooling.enrol(**kwargs)

    assert result.code == "record-invalid"
    assert not (_destination(tmp_path) / "spec-example.json").exists()


def test_a_deeply_nested_record_refuses_instead_of_raising(tmp_path) -> None:
    """The depth guard must not exhaust the stack it exists to protect.

    This is the integration half. It cannot isolate MAX_RECORD_DEPTH — every
    field of a schema-valid record is constrained, so no valid payload can nest
    past a handful of levels, and a payload deep enough to matter is refused by
    the shape validators too. The bound is therefore exercised directly below;
    what this case pins is that the traversal returns a code rather than
    exhausting the stack, which is the property that actually regressed.
    """
    cooling = _load()
    destination = _destination(tmp_path)
    destination.mkdir(parents=True)
    path = destination / "spec-example.json"
    path.write_bytes(("[" * 2000 + "]" * 2000).encode())

    assert cooling.parse_record_bytes(path.read_bytes()).code == "record-invalid"
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


def test_the_depth_bound_discriminates_at_its_limit(tmp_path) -> None:
    """Exercise MAX_RECORD_DEPTH directly, since no valid record can reach it."""
    cooling = _load()

    def nest(levels: int) -> object:
        node: object = "leaf"
        for _ in range(levels):
            node = {"n": node}
        return node

    assert cooling._exceeds_depth(nest(cooling.MAX_RECORD_DEPTH - 1), cooling.MAX_RECORD_DEPTH) is False
    assert cooling._exceeds_depth(nest(cooling.MAX_RECORD_DEPTH + 1), cooling.MAX_RECORD_DEPTH) is True
    # And it terminates on input that would overflow a recursive implementation.
    assert cooling._exceeds_depth(nest(50_000), cooling.MAX_RECORD_DEPTH) is True
