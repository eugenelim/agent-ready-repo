import ast
import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
COOLING_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
ENGINE_PATH = (
    ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
)
SCHEMA_PATH = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
RESULTS = ["Cooling", "Retained", "Retired", "Reclassified", "ExternalAdvisory"]

_HELPERS_PATH = Path(__file__).with_name(
    "test_status_projection_and_context_exclusion.py"
)
_helpers_spec = importlib.util.spec_from_file_location(
    "reclassified_lifecycle_status_helpers", _HELPERS_PATH
)
assert _helpers_spec is not None and _helpers_spec.loader is not None
_helpers_module = importlib.util.module_from_spec(_helpers_spec)
sys.modules[_helpers_spec.name] = _helpers_module
try:
    _helpers_spec.loader.exec_module(_helpers_module)
finally:
    sys.modules.pop(_helpers_spec.name, None)

_entry = _helpers_module._entry
_reconcile_json = _helpers_module._reconcile_json
_record = _helpers_module._record
_spec = _helpers_module._spec
_tree = _helpers_module._tree
_workspace = _helpers_module._workspace


def _load():
    spec = importlib.util.spec_from_file_location("wave7c_cooling", COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_engine():
    spec = importlib.util.spec_from_file_location(
        "workspace_status_engine", ENGINE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # The module carries postponed dataclass annotations that resolve against
    # its own name, so it must be in sys.modules before exec_module runs.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_the_contract_admits_exactly_five_results() -> None:  # AC1
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["post_closeout_result"]["enum"] == RESULTS


def test_validator_admits_exactly_the_contract_results() -> None:  # AC2
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    contract_results = set(schema["properties"]["post_closeout_result"]["enum"])
    tree = ast.parse(COOLING_PATH.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_is_one_of"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Subscript)
        and isinstance(node.args[0].value, ast.Name)
        and node.args[0].value.id == "payload"
        and isinstance(node.args[0].slice, ast.Constant)
        and node.args[0].slice.value == "post_closeout_result"
    ]
    assert len(calls) == 1
    accepted_literal = calls[0].args[1]
    assert isinstance(accepted_literal, ast.Set)
    validator_results = ast.literal_eval(accepted_literal)
    assert isinstance(validator_results, set)
    assert validator_results == contract_results


def test_the_validator_behaviourally_admits_the_contract_results() -> None:  # AC2
    """The validator's behaviour, not just its literal, matches the contract.

    The AST case above is the exhaustive half — it captures the whole membership
    set, which a probe cannot. This is the other half the plan names: a probe
    that includes a value outside the published set, so a second acceptance path
    added elsewhere in `validate_payload` fails here even though the inspected
    literal is untouched. Neither case subsumes the other.
    """
    cooling = _load()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    published = schema["properties"]["post_closeout_result"]["enum"]

    for result in published:
        payload = _valid_payload(post_closeout_result=result)
        assert cooling.validate_payload(payload).code is None, result

    for outside in ("Reclassifed", "Archived", "Cooling ", "", "reclassified"):
        payload = _valid_payload(post_closeout_result=outside)
        assert cooling.validate_payload(payload).code == "record-invalid", outside

    # Sampling refusals cannot close the general case: a branch admitting some
    # *other* unlisted value early would pass both this loop and the AST case
    # above. What closes it is that `validate_payload` has exactly ONE success
    # exit, reached only after the membership guard. An early success return
    # added anywhere in the function is a second one, and fails here.
    source = ast.parse(COOLING_PATH.read_text(encoding="utf-8"))
    validator = next(
        node
        for node in ast.walk(source)
        if isinstance(node, ast.FunctionDef) and node.name == "validate_payload"
    )
    success_exits = [
        node
        for node in ast.walk(validator)
        if isinstance(node, ast.Return)
        and not any(
            isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "record-invalid"
            for keyword in getattr(node.value, "keywords", [])
        )
    ]
    assert len(success_exits) == 1, [node.lineno for node in success_exits]
    assert success_exits[0] is validator.body[-1]


def _valid_payload(**overrides: object) -> dict[str, object]:
    """Return a schema-valid record payload, overridden field by field."""
    payload: dict[str, object] = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": "spec-example",
        "locator": "docs/specs/example/spec.md",
        "aliases": [],
        "fingerprint": "sha256:" + "0" * 64,
        "disposition": "retain-exception",
        "post_closeout_result": "Retained",
        "completion_event": "merge",
        "completion_evidence_ref": "commit:" + "a" * 40,
        "completed_on": "2026-08-01",
        "timezone": "Asia/Singapore",
        "review_on": "2026-08-31",
        "authority": {
            "source": {"status": "repository-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "none"},
        },
        "confirmation_proof": "sha256:" + "1" * 64,
        "exception": {
            "reason": "audit-obligation",
            "owner_role": "records-owner",
            "review_on": "2027-01-31",
        },
    }
    payload.update(overrides)
    return payload


def _acceptance(**overrides: str) -> dict[str, str]:
    """Return a valid durable-owner acceptance envelope."""
    acceptance = {
        "reason": "audit-obligation",
        "owner_role": "records-owner",
        "review_on": "2027-01-31",
        "evidence_ref": "run:72",
    }
    acceptance.update(overrides)
    return acceptance


def _candidate(cooling: Any, root: Path) -> object:
    """Build the confirmed lifecycle destination used by the cooling suite."""
    resolver = cooling._close_work().surface_resolver()
    return resolver.SurfaceCandidate(
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
        confirmations=(
            resolver.Confirmation("destination-selection", "confirmed"),
        ),
    )


def _binding(cooling: Any, resource: str) -> object:
    """Build an issued lifecycle-record mutation binding."""
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


def _reclassification_kwargs(
    cooling: Any,
    root: Path,
    *,
    completed_on: str = "2026-08-01",
    review_on: str = "2026-08-31",
) -> dict[str, object]:
    """Persist a retained record and return its reclassification inputs."""
    destination = root / "docs/lifecycle"
    destination.mkdir(parents=True)
    prior_exception = {
        "reason": "legal-obligation",
        "owner_role": "delivery-owner",
        "review_on": "2026-12-31",
    }
    prior = cooling.CoolingRecord.from_payload(
        {
            "schema": "delivery-lifecycle-record.v1",
            "delivery_id": "spec-example",
            "locator": "docs/specs/example/spec.md",
            "aliases": [],
            "fingerprint": "sha256:" + "0" * 64,
            "disposition": "retain-exception",
            "post_closeout_result": "Retained",
            "completion_event": "merge",
            "completion_evidence_ref": "commit:" + "a" * 40,
            "completed_on": completed_on,
            "timezone": "Asia/Singapore",
            "review_on": review_on,
            "authority": {
                "source": {"status": "repository-owned"},
                "write": {"status": "delegated"},
                "delete": {"status": "none"},
            },
            "confirmation_proof": "sha256:" + "1" * 64,
            "exception": prior_exception,
        }
    )
    resource = "docs/lifecycle/spec-example.json"
    authority_binding = _binding(cooling, resource)
    assert cooling._write_record(
        root, destination, prior, authority_binding
    ).code == "enrolled"
    return {
        "root": root,
        "record": prior,
        "candidates": (_candidate(cooling, root),),
        "authority_binding": authority_binding,
    }


def _record_digest(root: Path) -> str:
    """Return the persisted lifecycle record's SHA-256 digest."""
    record_path = root / "docs/lifecycle/spec-example.json"
    return hashlib.sha256(record_path.read_bytes()).hexdigest()


def test_the_transition_table_admits_reclassification() -> None:  # AC6
    cooling = _load()
    assert (
        ("retain-exception", "Retained"),
        ("retain-exception", "Reclassified"),
    ) in cooling._TRANSITIONS


def test_the_engine_cools_a_reclassified_record() -> None:  # AC9
    assert ("retain-exception", "Reclassified") in _load_engine()._COOLING_PAIRS


def test_reclassification_persists_the_supplied_acceptance(
    tmp_path: Path,
) -> None:  # AC4
    cooling = _load()
    inputs = _reclassification_kwargs(cooling, tmp_path)
    prior = inputs["record"]
    supplied = _acceptance()

    result = cooling.reclassify_record(acceptance=supplied, **inputs)

    persisted = cooling.load_record(
        tmp_path, tmp_path / "docs/lifecycle/spec-example.json"
    ).record
    assert result.code == "accepted"
    assert persisted is not None
    assert dict(persisted.exception) == supplied
    assert persisted.exception != prior.exception


@pytest.mark.parametrize(
    "acceptance",
    [
        None,
        "accepted",
        _acceptance() | {"unexpected": "field"},
        _acceptance(reason="business-preference"),
        # The carrier shape `review_exception` accepts for `renew`. Reading the
        # nested value would validate the block and ignore `unexpected`, so this
        # case is what holds the producer to the acceptance being the block
        # itself rather than something unwrapped from a carrier.
        {"exception": _acceptance(), "unexpected": "field"},
    ],
)
def test_malformed_acceptance_leaves_the_record_unchanged(
    tmp_path: Path, acceptance: object
) -> None:  # AC5
    cooling = _load()
    inputs = _reclassification_kwargs(cooling, tmp_path)
    before = _record_digest(tmp_path)

    result = cooling.reclassify_record(acceptance=acceptance, **inputs)

    assert result.code == "exception-envelope-invalid"
    assert _record_digest(tmp_path) == before


def test_reclassification_is_not_gated_by_the_review_date(
    tmp_path: Path,
) -> None:  # AC3
    cooling = _load()
    inputs = _reclassification_kwargs(
        cooling,
        tmp_path,
        completed_on="2999-01-01",
        review_on="2999-01-31",
    )
    prior = inputs["record"]
    assert datetime.now(UTC).date() < prior.review_on

    result = cooling.reclassify_record(
        acceptance=_acceptance(review_on="2999-06-01"),
        **inputs,
    )

    assert result.code == "accepted"
    assert result.record.post_closeout_result == "Reclassified"


def test_reclassification_preserves_the_artifact(tmp_path: Path) -> None:  # AC8
    cooling = _load()
    inputs = _reclassification_kwargs(cooling, tmp_path)
    artifact = tmp_path / "docs/specs/example/spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Example\n", encoding="utf-8")

    result = cooling.reclassify_record(
        acceptance=_acceptance(), **inputs
    )

    assert result.code == "accepted"
    assert artifact.is_file()


def test_reclassification_delegates_on_the_success_path(tmp_path: Path) -> None:
    """A SUCCEEDING reclassification must also reach disk through `update_record`.

    The removed-edge case below proves delegation only on the refusal path, and
    that is not enough on its own: a producer that checks `_TRANSITIONS` itself
    and delegates *only* when the check fails satisfies it while writing through
    `_write_record` on every real reclassification. That producer passes every
    other case in this file, because they all observe the persisted record and
    the persisted record is correct. This case is what makes it fail — the
    invariant is that reclassification reaches disk only through transition
    enforcement, on both paths.

    Observing the call is still not enough on its own either: a producer could
    write directly FIRST and call `update_record` afterwards, discarding its
    stale-record refusal. So the spy also asserts that the record on disk is
    still the PRIOR record at the moment it is invoked. That makes the delegated
    call the thing that performed the write, not merely something that ran.
    """
    cooling = _load()
    inputs = _reclassification_kwargs(cooling, tmp_path)
    delegated: list[dict[str, object]] = []
    state_at_call: list[str] = []
    update_record = cooling.update_record

    def recording_update(**kwargs: object) -> object:
        """Record the delegated call, and what was on disk when it was made."""
        delegated.append(kwargs)
        on_disk = cooling.load_record(
            tmp_path, tmp_path / "docs/lifecycle/spec-example.json"
        ).record
        state_at_call.append(on_disk.post_closeout_result)
        return update_record(**kwargs)

    cooling.update_record = recording_update

    result = cooling.reclassify_record(acceptance=_acceptance(), **inputs)

    assert result.code == "accepted"
    assert len(delegated) == 1
    assert delegated[0]["prior"] == inputs["record"]
    assert delegated[0]["proposed"].post_closeout_result == "Reclassified"
    # The write had not happened yet when the delegated call was made, so that
    # call is what performed it. A producer that wrote first and delegated
    # afterwards would show "Reclassified" here.
    assert state_at_call == ["Retained"]
    persisted = cooling.load_record(
        tmp_path, tmp_path / "docs/lifecycle/spec-example.json"
    ).record
    assert persisted.post_closeout_result == "Reclassified"


def test_reclassification_delegates_transition_enforcement(tmp_path: Path) -> None:
    """A removed edge must reach the guarded updater once and leave no write."""
    cooling = _load()
    inputs = _reclassification_kwargs(cooling, tmp_path)
    prior = inputs["record"]
    supplied = _acceptance()
    expected_proposed = cooling._proposed_record(
        prior,
        disposition="retain-exception",
        post_closeout_result="Reclassified",
        exception=supplied,
    )
    edge = (
        ("retain-exception", "Retained"),
        ("retain-exception", "Reclassified"),
    )
    cooling._TRANSITIONS = frozenset(
        transition for transition in cooling._TRANSITIONS if transition != edge
    )
    delegated: list[dict[str, object]] = []
    update_record = cooling.update_record

    def recording_update(**kwargs: object) -> object:
        """Record the proposed transition before enforcing it."""
        delegated.append(kwargs)
        return update_record(**kwargs)

    cooling.update_record = recording_update
    before = _record_digest(tmp_path)

    result = cooling.reclassify_record(acceptance=supplied, **inputs)

    assert len(delegated) == 1
    assert delegated[0]["prior"] == prior
    assert delegated[0]["proposed"] == expected_proposed
    assert result.code == "record-invalid"
    assert _record_digest(tmp_path) == before


def test_reclassified_artifact_leaves_orientation_without_a_body_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # AC9, AC10
    engine = _load_engine()
    root = _tree(
        tmp_path,
        records=[_record(disposition="retain-exception", result="Reclassified")],
        specs=(),
    )
    _spec(root, "alpha")
    _workspace(root, queue=_entry("alpha"))
    artifact = root / "docs/specs/alpha/spec.md"
    opened: list[Path] = []
    real_open = Path.open

    def recording_open(path: Path, *args: object, **kwargs: object):
        """Record any attempt to open the reclassified artifact body."""
        if path == artifact:
            opened.append(path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", recording_open)

    projection = _reconcile_json(root, engine)

    assert projection["canonical"]["ready"] == []
    assert projection["scan"]["declared_spec_files_read"] == 0
    assert opened == []


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 1, 31, tzinfo=UTC),
        datetime(2026, 8, 30, tzinfo=UTC),
    ],
)
def test_reclassified_record_is_never_due(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    now: datetime,
) -> None:  # AC11
    engine = _load_engine()
    root = _tree(
        tmp_path,
        records=[_record(disposition="retain-exception", result="Reclassified")],
        specs=(),
    )
    _workspace(root, queue="")
    real = engine._load_cooling_module()

    class _NoDateComparison:
        def is_due(self, record: object, at: datetime) -> object:
            raise AssertionError("reclassified records must be excluded first")

        def __getattr__(self, name: str) -> object:
            return getattr(real, name)

    monkeypatch.setattr(engine, "_load_cooling_module", lambda: _NoDateComparison())

    projection = _reconcile_json(root, engine, now=now)
    record = projection["cooling"]["records"][0]

    assert record["due"] is False
    assert projection["cooling"]["due"] == []
    assert projection["closeout"]["cooling_context_visible"] is False


def test_reclassified_record_is_not_a_retention_exception(tmp_path: Path) -> None:
    """AC12: the existing live-obligation predicate excludes reclassification."""
    engine = _load_engine()
    root = _tree(
        tmp_path,
        records=[_record(disposition="retain-exception", result="Reclassified")],
        specs=(),
    )
    _workspace(root, queue="")

    assert _reconcile_json(root, engine)["cooling"]["exceptions"] == []


def test_older_cooling_module_rejection_is_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # AC13
    engine = _load_engine()
    root = _tree(
        tmp_path,
        records=[_record(disposition="retain-exception", result="Reclassified")],
        specs=(),
    )
    _workspace(root, queue="")
    real = engine._load_cooling_module()

    class _OlderCoolingModule:
        def load_record(self, record_root: Path, record_path: Path) -> object:
            result = real.load_record(record_root, record_path)
            if (
                result.record is not None
                and result.record.post_closeout_result == "Reclassified"
            ):
                raise ValueError("unsupported post-closeout result")
            return result

        def __getattr__(self, name: str) -> object:
            return getattr(real, name)

    monkeypatch.setattr(engine, "_load_cooling_module", lambda: _OlderCoolingModule())

    projection = _reconcile_json(root, engine)

    assert ("invalid_lifecycle_record", "docs/lifecycle/alpha.json") in {
        (finding["code"], finding["path"])
        for finding in projection["canonical"]["findings"]
    }
    assert projection["closeout"]["cooling_context_visible"] is True
