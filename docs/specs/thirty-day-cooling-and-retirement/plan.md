# Plan: Thirty-day cooling and retirement

- **Spec:** [spec.md](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0096-portable-delivery-artifact-lifecycle.md`
  at `6e984d67b583b36798efddbb2717ce5784572a49` owns cooling policy;
  `docs/architecture/work-intake-and-artifact-routing.md` owns implemented phase
  boundaries; `packs/core/.apm/skills/close-work/scripts/close_work.py` is the
  analogous production implementation for bounded records, authority bindings,
  and confirmed effects, with `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
  and `packs/core/tests/skills/close-work/test_close_work.py` as its analogous
  tests; `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py`
  and `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` own the
  shipped resolution and confinement primitives and are unchanged here;
  `contracts/jsonschema/semantic-surface-resolution.schema.json` is the analogous
  published contract. Named deviation: no repository surface owns
  delivery-lifecycle state, so RFC §4 rung 6 applied and the owner selected
  `docs/lifecycle/` as the destination after the first choice,
  `docs/specs/<slug>/lifecycle.json`, was withdrawn for conflicting with the
  frozen-spec-directory rule.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Land Wave 5 as five dependency-ordered review units. The first three build the
engine bottom-up — pure date arithmetic and record shape, then the guarded write
path, then identity — so each unit is independently reviewable and leaves the
repository working. The fourth composes them into the day-30 review decision.
The fifth closes doctrine, the instructional surfaces, release metadata, and
every projection.

The whole engine is three operations: compute a date, persist a bounded record,
answer whether a record is due. Everything else is refusal. There is no
scheduler, no daemon, no background job, and no wake-up hook: a human invokes
`close-work` and asks. Deletion is not implemented here at all — an approved
retirement calls Wave 4's `preview_deletion`, `confirm_deletion`, and
`apply_confirmed_deletion` with no change to those seams.

Two design rules carry most of the correctness. First, the clock is always an
argument: no module in this wave calls a wall-clock function, so DST, foreign
readers, leap days, and day-boundary cases are ordinary table tests rather than
timing-dependent ones. Second, `review_on` is date arithmetic
(`completed_on + timedelta(days=30)`), not interval arithmetic, so a DST
transition inside the window cannot move it — the tests assert that property
rather than a wall-clock offset.

Identity is the logical delivery ID plus the content fingerprint from
`file_safety.sha256_confined_regular_file`. Nothing in this wave reads Git.
The identity fixtures therefore build real repositories and perform a real
squash merge, merge commit, rebase, and shallow clone, and a fifth fixture
deletes `.git` outright — a mocked Git could not testify to the property being
claimed.

The new module is `cooling.py`, a sibling of `close_work.py` inside the
`close-work` skill rather than an addition to that 2,400-line module, so the
wave's seams are independently importable and testable. It reuses
`close_work.py`'s existing `file_safety()` and `surface_resolver()` sibling
loaders, its authority-binding shape, and its validated-parent walk; it
introduces no second resolver, no second fingerprint helper, and no third safety
primitive.

`surface_resolver.py` and `file_safety.py` are byte-unchanged, so
`EXPECTED_RESOLVER_SHA256` and `EXPECTED_FILE_SAFETY_SHA256` in the Wave 4
roster test must still pass without edits. If either digest moves, that is a
defect in this wave, not a pin to re-cut. `close_work.py` gains exactly one
change: its existing private `_open_validated_parent` is exposed under a public
name so `cooling.py` can call it instead of writing a second confinement walk.
That edit adds no clock and no date-shaped field, so Wave 4's import and token
guards stay green and stay meaningful.

Anchor tests identified before EXECUTE:
`tests/roster/test_wave4_durable_outputs_and_release.py` pins the core pack
version literal in three places and asserts three whitespace-normalised Wave 4
doctrine sentences; `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
pins the resolver, schema, and file-safety digests and parses `close_work.py`'s
imports and date-shaped tokens; `packs/core/tests/skills/close-work/test_close_work.py`
pins the whitespace-normalised phrase "Do not start a timer" in the shipped
skill, which Task 5 rewrites; `tools/test_local_ci_shared_test_deduplication.py`
pins node-ID digests for three core lint files, none of which this wave touches;
`tools/test_workspace_status.py` pins a work-loop `SKILL.md` contract hash, and
this wave does not edit that file.

Two authoring constraints govern Task 5's prose.
`packs/core/.apm/skills/close-work/SKILL.md` is projected into `.claude/` and
`.agents/`, so it must not cite `contracts/`, `docs/`, or any other
repository-only path. Separately, `tools/lint-guides-no-repo-only-refs.py`
rejects any `RFC-NNNN` or `ADR-NNNN` token in `guides/**`, any reference to a
real `docs/specs/<slug>` directory, and link targets containing an `adr`, `rfc`,
or `specs` path segment; `.github/workflows/docs.yml` gates it in CI. New guide
wording is authored under that prohibition rather than repaired afterwards.
New assertion strings added to doctrine surfaces must not wrap across a line,
because the roster checks are whitespace-normalised but the per-pointer checks
are not. Projections are regenerated with `env FORCE=1 make build-self` and
never hand-authored.

## Design (LLD)

### Data and schema

`docs/lifecycle/<delivery-id>.json`, one record per delivery artifact, resolved
through the Wave 1 resolver for the `runtime-coordination` role from a
caller-supplied candidate. `docs/lifecycle/` is created once in Task 5 with a
`README.md` naming its single writer; enrolment never creates it. The published
field set lives in `contracts/jsonschema/delivery-lifecycle-record.schema.json`,
which carries `"x-spec": ["docs/specs/thirty-day-cooling-and-retirement/"]` and
sets `additionalProperties: false` with an explicit `required` list at *every*
object level.

| Field | Meaning |
| --- | --- |
| `schema` | `delivery-lifecycle-record.v1` |
| `delivery_id` | Logical ID; never a commit, branch, or tag |
| `locator` | Current repository-relative locator |
| `aliases` | Prior locators retained across renames; `maxItems: 16` |
| `fingerprint` | `sha256:<64 hex>` of the artifact's content |
| `disposition` | RFC §5 intent token: `cool-30-days` or `retain-exception` |
| `post_closeout_result` | `close_work.POST_CLOSEOUT_RESULTS` token: `Cooling`, `Retained`, or `Retired` |
| `completion_event` | Selected delivery-completion event kind |
| `completion_evidence_ref` | Bounded non-personal reference |
| `completed_on` | ISO date of the selected event |
| `timezone` | IANA key recorded with the event |
| `review_on` | ISO date, `completed_on` plus thirty days |
| `authority` | Closed object of `source`, `write`, `delete` facts |
| `confirmation_proof` | `sha256:<64 hex>`, opaque by construction |
| `exception` | Present only for `retain-exception`: `reason`, `owner_role`, `review_on` |

`owner_role` reuses `close_work.py`'s shipped actor-role pattern
`^[a-z][a-z0-9-]{1,63}$`. `confirmation_proof` is a digest, so a name or address
cannot be expressed in it. Every `*_evidence_ref` is bounded and matches the
non-personal reference pattern. Together these make the spec's exclusion rule a
schema property rather than a string screen.

Canonical serialization is
`json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
allow_nan=False)` plus a trailing newline, copying `surface_resolver.py`'s
existing canonical form rather than `close_work.py`'s two inconsistent ones.

Bounds: `MAX_RECORD_BYTES = 64 * 1024`, `MAX_RECORD_DEPTH = 8`,
`MAX_ARTIFACT_BYTES = 8 * 1024 * 1024`. The record is read through
`file_safety.read_confined_regular_file(..., max_bytes=MAX_RECORD_BYTES)`.
Because `sha256_confined_regular_file` accepts no bound and `file_safety.py` is
byte-pinned, the artifact-size check is a caller-side `stat` in `cooling.py`
before the hash. Depth is checked on the parsed object rather than relying on
`json.loads`, whose `RecursionError` is not a `ValueError`.

### State and control flow

`enrol()` order is: validate the supplied candidate and its confirmation →
resolve the surface → validate the write-scoped authority binding → open the
validated parent → re-confine → exclusive temp create → write canonical bytes →
`os.replace` through the same directory handle. Every refusal before the replace
returns an empty mutation trace.

`load_record()` order is: confined bounded read → strict parse → depth check →
schema-shaped closed-key validation → re-derive `review_on` and compare →
disposition-transition check. Legal transitions are `cool-30-days →
retain-exception`, and `post_closeout_result` may move `Cooling → Retained` or
`Cooling → Retired`. Any backward move refuses.

### Failure, edge cases, and resilience

Refusal codes: `completion-event-required`, `not-delivered`,
`destination-unconfirmed`, `lifecycle-state-unwritable`, `unsafe-target`,
`record-invalid`, `naive-clock`, `unknown-timezone`, `not-due`,
`review-incomplete`, `fingerprint-drift`, `locator-unresolved`,
`missing-history`, `authority-uncertain`, `exception-envelope-invalid`.

`ZoneInfo` raises `ZoneInfoNotFoundError` from the same call as an unknown key,
so one `unknown-timezone` refusal covers both an invalid IANA key and an absent
platform tz database (slim containers, Windows without `tzdata`). There is no
UTC fallback. Task 5 records the platform condition in the architecture
document.

No lock is introduced: distinct records never share a file, and a same-record
concurrent write is a whole-record last-writer-wins rather than a torn read, so
no lock is needed to prevent data loss. Cross-worktree simultaneity is not
exercised by a test; the claim is bounded to torn reads.

### Concurrency and idempotence

`os.replace` is atomic within a filesystem, and the temp file is created in the
destination directory through the same validated descriptor, so no cross-device
rename occurs. Re-enrolling an already-enrolled record is refused by the
disposition-transition check rather than silently rewriting it.

## Tasks

### Task 1 — Contract, record shape, and date arithmetic

**ACs:** AC1–AC11.
**Verification mode:** TDD.
**Depends on:** none.

**Tests:**

- stub: true
- Table rows beyond the stub: a window spanning 29 February; a spring-forward and
  a fall-back window in the recorded zone; the forty-days-in-the-past row also
  asserting `completed_on` is not clamped to the enrolment day.
- The AC7 clock check names its path set (`packs/core/.apm/skills/close-work/scripts/cooling.py`)
  and its exhaustive symbol set (`datetime.now`, `datetime.utcnow`,
  `datetime.today`, `date.today`, `time.time`, `time.monotonic`,
  `time.perf_counter`, `os.times`) and resolves them by AST import and attribute
  analysis, not substring — `cooling.py` legitimately imports `datetime` and
  `zoneinfo`, so the Wave 4 module-name idiom cannot be copied.

```python
# tests/roster/test_thirty_day_cooling_and_retirement.py
"""RFC-0096 Wave 5 — cooling engine construction tests."""

import ast
import importlib.util
import json
from datetime import date, datetime, timezone as _tz
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[2]
COOLING_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
SCHEMA_PATH = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
SG = "Asia/Singapore"


def _load():
    spec = importlib.util.spec_from_file_location("wave5_cooling", COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(cooling, **overrides):
    """Minimal valid in-memory record; overrides drive the negative cases."""
    payload = {
        "schema": "delivery-lifecycle-record.v1",
        "delivery_id": "spec/example",
        "locator": "docs/specs/example/spec.md",
        "aliases": [],
        "fingerprint": "sha256:" + "0" * 64,
        "disposition": "cool-30-days",
        "post_closeout_result": "Cooling",
        "completion_event": "merge",
        "completion_evidence_ref": "commit:0123456789abcdef",
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
    return cooling.CoolingRecord.from_payload(payload)


# STUB: AC1
def test_review_on_is_thirty_calendar_days() -> None:
    cooling = _load()
    assert cooling.compute_review_on(date(2026, 8, 1), SG) == date(2026, 8, 31)


# STUB: AC2
@pytest.mark.parametrize(
    ("zone", "start"),
    [
        ("America/New_York", date(2027, 2, 25)),   # spring forward inside window
        ("America/New_York", date(2027, 10, 25)),  # fall back inside window
        ("Asia/Singapore", date(2027, 2, 25)),     # no transition at all
    ],
)
def test_dst_transition_does_not_move_review_on(zone: str, start: date) -> None:
    cooling = _load()
    assert (cooling.compute_review_on(start, zone) - start).days == 30


# STUB: AC3
def test_dueness_is_evaluated_in_the_recorded_zone() -> None:
    cooling = _load()
    record = _record(cooling)
    instant = datetime(2026, 8, 31, 1, 0, tzinfo=ZoneInfo(SG))
    answers = {
        cooling.is_due(record, instant.astimezone(ZoneInfo(reader))).due
        for reader in ("UTC", "America/New_York", "Australia/Sydney")
    }
    assert answers == {True}


# STUB: AC4
@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 8, 30, 23, 59, tzinfo=ZoneInfo(SG)), False),
        (datetime(2026, 8, 31, 0, 0, tzinfo=ZoneInfo(SG)), True),
        (datetime(2026, 9, 1, 0, 0, tzinfo=ZoneInfo(SG)), True),
    ],
)
def test_dueness_flips_at_local_midnight(moment: datetime, expected: bool) -> None:
    cooling = _load()
    assert cooling.is_due(_record(cooling), moment).due is expected


# STUB: AC5
def test_late_closeout_preserves_the_event_date() -> None:
    cooling = _load()
    record = _record(cooling, completed_on="2026-06-01", review_on="2026-07-01")
    now = datetime(2026, 8, 27, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.is_due(record, now)
    assert result.due is True
    assert record.completed_on == date(2026, 6, 1)


# STUB: AC6
def test_due_grants_no_permission() -> None:
    cooling = _load()
    now = datetime(2026, 9, 30, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.is_due(_record(cooling), now)
    assert result.due is True
    assert result.permission_granted is False
    assert result.mutated == ()


# STUB: AC7
def test_naive_clock_refuses() -> None:
    cooling = _load()
    result = cooling.is_due(_record(cooling), datetime(2026, 9, 30, 12, 0))
    assert result.code == "naive-clock"


# STUB: AC7
def test_no_wave5_module_reads_the_system_clock() -> None:
    forbidden = {
        ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
        ("date", "today"), ("time", "time"), ("time", "monotonic"),
        ("time", "perf_counter"), ("os", "times"),
    }
    tree = ast.parse(COOLING_PATH.read_text(encoding="utf-8"))
    seen = {
        (node.func.value.id, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }
    assert seen.isdisjoint(forbidden)


# STUB: AC8
def test_schema_closes_every_object_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["x-spec"] == ["docs/specs/thirty-day-cooling-and-retirement/"]

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert "required" in node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)


# STUB: AC8
@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(surprise="x"),
        lambda p: p["authority"]["write"].update(surprise="x"),
        lambda p: p.setdefault("exception", {}).update(surprise="x"),
    ],
)
def test_undeclared_key_refuses_at_every_level(mutate) -> None:
    cooling = _load()
    payload = _record(cooling).as_payload()
    mutate(payload)
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC9
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confirmation_proof", "approved by a.person@example.com"),
        ("completion_evidence_ref", "reviewed by A. Person"),
    ],
)
def test_exclusion_is_structural(field: str, value: str) -> None:
    cooling = _load()
    payload = _record(cooling).as_payload()
    payload[field] = value
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC10
def test_canonical_serialization_round_trips_byte_identically() -> None:
    cooling = _load()
    first = cooling.canonical_bytes(_record(cooling))
    again = cooling.canonical_bytes(cooling.CoolingRecord.from_payload(json.loads(first)))
    assert first == again
    assert first.endswith(b"\n")


# STUB: AC10
def test_non_finite_value_refuses() -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(b'{"completed_on": NaN}').code == "record-invalid"


# STUB: AC11
@pytest.mark.parametrize(
    "blob",
    [
        b'{"a":' + b'"x"' * 40000 + b"}",
        b"[" * 64 + b"]" * 64,
    ],
)
def test_oversized_and_over_nested_input_refuses(blob: bytes) -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(blob).code == "record-invalid"
```

**Approach:** write `contracts/jsonschema/delivery-lifecycle-record.schema.json`
with `x-spec` and level-wise closure, then the `CoolingRecord` dataclass, strict
parse, bounds, canonical serialise, and `compute_review_on` / `is_due` in
`packs/core/.apm/skills/close-work/scripts/cooling.py`.

### Task 2 — Enrolment, the guarded write seam, and fail-closed state

**ACs:** AC12–AC23.
**Verification mode:** TDD.
**Depends on:** Task 1.

**Tests:**

- stub: true
- The candidate destination and its `destination-selection` confirmation come
  from `close-work/SKILL.md`'s enrolment step in this repository — the skill
  supplies `docs/lifecycle/` as a `repository-convention` candidate once
  `docs/lifecycle/README.md` exists — and, in an adopter repository, from the
  same RFC §4 precedence walk the skill already runs for every other surface.
  No repository-only path is written into the projected skill body; the skill
  resolves the directory by role and records the human's selection.
- The unwritable fixture is a real `chmod 0o555` destination whose candidate does
  **not** declare its own `writability`, so the refusal cannot come from an
  echoed attribute.
- Additional rows: re-enrolling an existing record; a record whose stored
  `review_on` disagrees with `completed_on + 30d`; a `retain-exception` record
  rewritten back to `cool-30-days`.

```python
# STUB: AC12
@pytest.mark.parametrize(
    "facts",
    [
        {"delivered": False, "closed": True, "persisted": True},
        {"delivered": True, "closed": False, "persisted": True},
        {"delivered": True, "closed": True, "persisted": False},
    ],
)
def test_only_delivered_closed_persistent_work_enrols(tmp_path, facts) -> None:
    cooling = _load()
    result = cooling.enrol(repository_root=tmp_path, completion_event="merge", **facts)
    assert result.code == "not-delivered"
    assert result.mutated == ()


# STUB: AC13
def test_enrolment_without_a_selected_event_refuses(tmp_path) -> None:
    cooling = _load()
    result = cooling.enrol(
        repository_root=tmp_path, delivered=True, closed=True,
        persisted=True, completion_event=None,
    )
    assert result.code == "completion-event-required"


# STUB: AC14
@pytest.mark.parametrize("event", ["creation", "ready", "edit", "session-end"])
def test_non_completion_events_never_start_the_clock(tmp_path, event: str) -> None:
    cooling = _load()
    result = cooling.enrol(
        repository_root=tmp_path, delivered=True, closed=True,
        persisted=True, completion_event=event,
    )
    assert result.code == "completion-event-required"


# STUB: AC15
def test_enrolment_without_a_confirmed_candidate_refuses(tmp_path) -> None:
    cooling = _load()
    result = cooling.enrol(
        repository_root=tmp_path, delivered=True, closed=True, persisted=True,
        completion_event="merge", candidates=(),
    )
    assert result.code == "destination-unconfirmed"


# STUB: AC16
def test_absent_destination_refuses_but_absent_record_is_normal(tmp_path) -> None:
    cooling = _load()
    missing = cooling.enrol_into(tmp_path, tmp_path / "docs" / "lifecycle")
    assert missing.code == "lifecycle-state-unwritable"

    (tmp_path / "docs" / "lifecycle").mkdir(parents=True)
    created = cooling.enrol_into(tmp_path, tmp_path / "docs" / "lifecycle")
    assert created.code == "enrolled"
    assert created.mutated != ()


# STUB: AC17
def test_writability_comes_from_the_filesystem_not_the_candidate(tmp_path) -> None:
    destination = tmp_path / "docs" / "lifecycle"
    destination.mkdir(parents=True)
    destination.chmod(0o555)
    try:
        cooling = _load()
        result = cooling.enrol_into(tmp_path, destination, declared_writability="writable")
        assert result.code == "lifecycle-state-unwritable"
        assert result.mutated == ()
    finally:
        destination.chmod(0o755)


# STUB: AC18
def test_swapped_parent_refuses_with_zero_effects(tmp_path) -> None:
    cooling = _load()
    real = tmp_path / "elsewhere"
    real.mkdir()
    link = tmp_path / "docs" / "lifecycle"
    link.parent.mkdir(parents=True)
    link.symlink_to(real, target_is_directory=True)
    result = cooling.enrol_into(tmp_path, link)
    assert result.code == "unsafe-target"
    assert result.mutated == ()
    assert list(real.iterdir()) == []


# STUB: AC19
@pytest.mark.parametrize(
    "binding",
    [None, {"action": "write-something-else"}, {"resource": "docs/other"}],
)
def test_record_mutation_requires_a_write_scoped_binding(tmp_path, binding) -> None:
    cooling = _load()
    result = cooling.enrol_into(tmp_path, tmp_path, authority_binding=binding)
    assert result.code == "authority-uncertain"
    assert result.mutated == ()


# STUB: AC20
def test_every_loaded_field_is_revalidated(tmp_path) -> None:
    cooling = _load()
    payload = _record(cooling).as_payload()
    payload["locator"] = "../outside/spec.md"
    path = tmp_path / "spec-example.json"
    path.write_bytes(json.dumps(payload).encode() + b"\n")
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


# STUB: AC21
@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(review_on="2026-12-31"),
        lambda p: p.update(disposition="cool-30-days", post_closeout_result="Cooling"),
    ],
)
def test_inconsistent_or_backward_state_refuses(tmp_path, mutate) -> None:
    cooling = _load()
    payload = _record(cooling, disposition="retain-exception").as_payload()
    mutate(payload)
    path = tmp_path / "spec-example.json"
    path.write_bytes(json.dumps(payload).encode() + b"\n")
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


# STUB: AC22
def test_record_survives_a_separate_process(tmp_path) -> None:
    import subprocess
    import sys

    cooling = _load()
    path = tmp_path / "spec-example.json"
    path.write_bytes(cooling.canonical_bytes(_record(cooling)))
    proof = subprocess.run(
        [sys.executable, "-c",
         "import importlib.util,sys,json;"
         f"s=importlib.util.spec_from_file_location('c', r'{COOLING_PATH}');"
         "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
         f"print(m.load_record(r'{tmp_path}', r'{path}').record.delivery_id)"],
        capture_output=True, text=True, check=True,
    )
    assert proof.stdout.strip() == "spec/example"


# STUB: AC23
def test_workspace_toml_gains_no_cooling_schema() -> None:
    text = (ROOT / "workspace.toml").read_text(encoding="utf-8")
    for token in ("review_on", "completed_on", "cooling", "lifecycle_record"):
        assert token not in text
```

**Approach:** `enrol()` validates the candidate and confirmation, resolves the
surface through the Wave 1 resolver as `close_work._resolved_surface` does,
validates a write-scoped binding with the existing binding shape, then writes
through the validated parent descriptor: exclusive temp create, canonical bytes,
`os.replace`. Expose `close_work._open_validated_parent` under a public name and
call it; do not write a second walk. `load_record()` reads through
`file_safety.read_confined_regular_file` with `max_bytes`, then runs the
Task 1 validation chain plus the re-derivation and transition checks.

### Task 3 — Identity across history shapes and deletion blockers

**ACs:** AC24–AC27.
**Verification mode:** TDD with real Git fixtures.
**Depends on:** Task 2.

**Tests:**

- stub: true
- The record is written **before** each topology operation and verified **after**
  it in the same repository; the shallow-clone case writes in the origin and
  verifies in the clone. A topology-derived implementation therefore cannot
  self-verify.
- Fixtures skip loudly, never silently, when `git` is unavailable.

```python
# STUB: AC24
@pytest.mark.parametrize(
    "topology", ["squash", "merge", "rebase", "shallow", "no-git"],
)
def test_identity_survives_every_history_shape(tmp_path, topology: str) -> None:
    cooling = _load()
    repo, record = _seed_repository_and_record(tmp_path, cooling)  # writes first
    verified_root = _apply_topology(repo, topology)                # then rewrites history
    result = cooling.verify_identity(verified_root, record)
    assert result.code == "identity-verified"


# STUB: AC25
def test_rename_updates_the_locator_and_keeps_the_alias() -> None:
    cooling = _load()
    original = _record(cooling)
    renamed = cooling.record_rename(original, "docs/specs/renamed/spec.md")
    assert renamed.locator == "docs/specs/renamed/spec.md"
    assert original.locator in renamed.aliases


# STUB: AC26
@pytest.mark.parametrize(
    ("condition", "code"),
    [
        ("missing-history", "missing-history"),
        ("fingerprint-drift", "fingerprint-drift"),
        ("unresolved-reference", "locator-unresolved"),
        ("uncertain-authority", "authority-uncertain"),
    ],
)
def test_four_conditions_block_deletion(condition: str, code: str) -> None:
    cooling = _load()
    assert cooling.deletion_blocked(*_blocker_inputs(condition)) == code


# STUB: AC27
def test_source_authority_never_implies_deletion_authority() -> None:
    cooling = _load()
    record = _record(
        cooling,
        authority={
            "source": {"status": "external-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "none"},
        },
    )
    assert cooling.deletion_blocked(record, _verified_identity(), None) == "authority-uncertain"
```

**Approach:** `verify_identity()` re-resolves the locator or an alias and
recomputes the fingerprint via `file_safety.sha256_confined_regular_file` after
a caller-side size check. `record_rename()` returns a new record with the prior
locator appended to `aliases`. `deletion_blocked()` returns the first applicable
code or `None`. Nothing imports `subprocess` for Git; the fixtures shell out,
the module does not.

### Task 4 — Day-30 review, retirement, and exceptions

**ACs:** AC28–AC33.
**Verification mode:** TDD.
**Depends on:** Task 3.

**Tests:**

- stub: true
- The AC33 no-deletion proof states the exhaustive removal-API set
  (`os.unlink`, `os.remove`, `os.rmdir`, `os.removedirs`, `Path.unlink`,
  `Path.rmdir`, `shutil.rmtree`) and resolves it by AST call-target analysis,
  reusing the Task 1 helper so one implementation serves both checks. No
  by-name carve-out is added for `os.replace`, which is not in the set.

```python
# STUB: AC28
@pytest.mark.parametrize(
    "omitted",
    ["completion", "outputs", "active_use", "obligations", "identity", "authority"],
)
def test_review_requires_all_six_answers(omitted: str) -> None:
    cooling = _load()
    checks = {k: "approve" for k in
              ("completion", "outputs", "active_use", "obligations", "identity", "authority")}
    del checks[omitted]
    now = datetime(2026, 9, 30, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.review(_record(cooling), checks, _attestation(), now)
    assert result.code == "review-incomplete"


# STUB: AC29
def test_model_sourced_answers_refuse() -> None:
    cooling = _load()
    now = datetime(2026, 9, 30, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.review(_record(cooling), _all_approve(), _model_attestation(), now)
    assert result.code == "review-incomplete"


# STUB: AC30
def test_approval_retires() -> None:
    cooling = _load()
    now = datetime(2026, 9, 30, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.review(_record(cooling), _all_approve(), _attestation(), now)
    assert result.record.post_closeout_result == "Retired"
    assert result.mutated == ()


# STUB: AC31
@pytest.mark.parametrize("answer", ["refuse", "uncertain"])
def test_refusal_or_uncertainty_creates_a_reasoned_owned_dated_exception(answer: str) -> None:
    cooling = _load()
    checks = _all_approve() | {"obligations": answer}
    now = datetime(2026, 9, 30, 12, 0, tzinfo=ZoneInfo(SG))
    result = cooling.review(
        _record(cooling), checks, _attestation(),
        now, exception={"reason": "audit obligation open",
                        "owner_role": "release-manager",
                        "review_on": "2026-12-01"},
    )
    assert result.record.disposition == "retain-exception"
    assert result.record.exception["owner_role"] == "release-manager"


# STUB: AC32
@pytest.mark.parametrize(
    "outcome", ["confirm-deletion", "renew", "choose-cooling", "advisory"],
)
def test_exception_review_offers_exactly_four_outcomes(outcome: str) -> None:
    cooling = _load()
    now = datetime(2026, 12, 1, 12, 0, tzinfo=ZoneInfo(SG))
    record = _exception_record(cooling)
    assert cooling.review_exception(record, outcome, _attestation(), now).code == "accepted"
    assert cooling.review_exception(record, "delete-now", _attestation(), now).code == (
        "exception-envelope-invalid"
    )


# STUB: AC33
def test_no_wave5_seam_removes_a_file() -> None:
    forbidden = {
        ("os", "unlink"), ("os", "remove"), ("os", "rmdir"), ("os", "removedirs"),
        ("Path", "unlink"), ("Path", "rmdir"), ("shutil", "rmtree"),
    }
    tree = ast.parse(COOLING_PATH.read_text(encoding="utf-8"))
    seen = {
        (node.func.value.id, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }
    assert seen.isdisjoint(forbidden)
```

**Approach:** `review()` takes the record, a closed `ReviewChecks` mapping, a
human attestation, and the injected instant, and returns one outcome. It
performs no effect. `review_exception()` accepts exactly the four RFC §6
outcomes and refuses anything else.

### Task 5 — Doctrine, instructional surfaces, release, and projections

**ACs:** AC34–AC37.
**Verification mode:** Goal-based plus visual/manual QA.
**Depends on:** Task 4.

**Tests:** `no stub (mode)`.

- `EXPECTED_RESOLVER_SHA256` and `EXPECTED_FILE_SAFETY_SHA256` still pass
  unedited; a check that no runtime dependency was added; the amended
  `test_wave4_docs_do_not_claim_later_wave_engines`, which drops the two
  Wave-5-owned sentences, keeps the Wave 4-scoped architecture sentence, and
  adds the Wave 5 statement; per-pointer assertions for the five documents and
  the three `close-work/SKILL.md` lines. Manual QA: invoke `close-work` on one
  shipped artifact and record the enrolment, the due answer, and one day-30
  review outcome.

**Approach:** create `docs/lifecycle/` with a `README.md` naming `close-work` as
its single writer; update `packs/core/.apm/skills/close-work/SKILL.md`,
`docs/architecture/work-intake-and-artifact-routing.md` (including its "Last
verified surface" section and the Windows tz-database condition), and the five
pointers; amend `tests/roster/test_wave4_durable_outputs_and_release.py` (three
version literals and the doctrine-sentence set) and
`packs/core/tests/skills/close-work/test_close_work.py`'s "Do not start a timer"
pin rather than deleting either; bump `packs/core/pack.toml` and
`packs/core/.claude-plugin/plugin.json` to `2.14.0` and add the topmost dated
`## [core][2.14.0]` changelog heading; regenerate with `env FORCE=1 make build-self`.

## Verification

`make lint-ruff`, `make lint-mypy`, `SKIP_SAST=1 make build-check`, `make test`,
`make sast`, `make site-link-check`, `npm test --prefix web`, and — for the
emitted-changelog test — `python3 tools/build-site.py && npm run build --prefix web
&& npm run build --prefix docs-site`.

Every new guard in this wave carries a mutation proof: the property is made
false in the source, the guard is run and observed to fail, the source is
restored, and the restoration is confirmed byte-identical.

## Risks

- A pack version bump reddens three literals in the Wave 4 roster test, and the
  SKILL.md rewrite reddens the "Do not start a timer" pin in the pack suite.
  Both are updated in Task 5, not weakened.
- `close_work.py` gains one public alias for its validated-parent walk. That is
  the only edit; it adds no clock and no date-shaped token, so Wave 4's import
  and token guards stay green. If any other edit to that file becomes necessary,
  surface it rather than absorbing it.
- The no-lock decision is bounded to torn reads and is not exercised against two
  simultaneous enrolments. If a concurrency defect is found later, it is a new
  finding, not a silent fix here.
