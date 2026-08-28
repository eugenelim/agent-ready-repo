# Plan: Thirty-day cooling and retirement

- **Spec:** [spec.md](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0096-portable-delivery-artifact-lifecycle.md`
  at `6e984d67b583b36798efddbb2717ce5784572a49` owns cooling policy;
  `docs/architecture/work-intake-and-artifact-routing.md` owns implemented phase
  boundaries and `docs/architecture/overview.md` owns the repository tree;
  `packs/core/.apm/skills/close-work/scripts/close_work.py` is the analogous
  production implementation for bounded records, authority bindings, and
  confirmed effects, with `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
  and `packs/core/tests/skills/close-work/test_close_work.py` as its analogous
  tests; `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py` and
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` own the
  shipped resolution and confinement primitives and are unchanged here;
  `contracts/jsonschema/semantic-surface-resolution.schema.json` is the analogous
  published contract. Named deviation: no repository surface owns
  delivery-lifecycle state, so RFC §4 rung 6 applied and the owner selected
  `docs/lifecycle/` after the first choice, `docs/specs/<slug>/lifecycle.json`,
  was withdrawn for conflicting with the frozen-spec-directory rule.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Land Wave 5 as five dependency-ordered review units: record shape and dates,
then the guarded write seam, then identity, then review, then surfaces.

The whole engine is three operations — compute a date, persist a bounded record,
answer whether a record is due — and everything else is a refusal with a named
code. There is no scheduler, daemon, background job, or wake-up hook: a human
invokes `close-work` and asks. Deletion is not implemented here; an approved
retirement calls Wave 4's `preview_deletion`, `confirm_deletion`, and
`apply_confirmed_deletion` unchanged.

Two rules carry most of the correctness. The clock is always an argument, so DST,
foreign readers, leap days, and day boundaries are table rows rather than
timing-dependent tests. And `review_on` is date arithmetic
(`completed_on + timedelta(days=30)`), not interval arithmetic, so a DST
transition inside the window cannot move it.

Identity is the logical delivery ID plus the content fingerprint from
`file_safety.sha256_confined_regular_file`. Nothing in this wave reads Git, so
the identity fixtures build real repositories and perform a real squash merge,
merge commit, rebase, and shallow clone, plus a `.git` deletion. Each fixture
writes the record *before* the topology operation and verifies *after* it, so an
implementation that derived identity from commit topology cannot self-verify.

`cooling.py` is a sibling of `close_work.py` inside the `close-work` skill, not
an addition to that 2,400-line module, so Wave 4's clock-absence guard — which
parses `close_work.py`'s own imports and date-shaped tokens — stays both green
and meaningful.

`surface_resolver.py` and `file_safety.py` are byte-unchanged (AC37).
`close_work.py` gains exactly two public aliases and no other change: its private
`_open_validated_parent` and `_load_regular_sibling`, both of which `cooling.py`
must call to avoid a second confinement walk and a second sibling loader. Neither
alias adds a clock or a date-shaped token, so Wave 4's guards stay green.

Anchor tests, with the reason each is expected to redden:

| Anchor | Why it moves |
| --- | --- |
| `tests/roster/test_wave4_durable_outputs_and_release.py` | three pack-version literals; two Wave-5-owned doctrine sentences |
| `packs/core/tests/skills/close-work/test_close_work.py` | pins "Do not start a timer" in the shipped skill, which Task 5 rewrites |
| `tests/roster/test_close_work_extraction_and_immediate_disposition.py` | scans every file under `tests/roster/`; the new roster file must not name `action-not-authorized`, `grant-not-authoritative`, or `session-provenance-invalid` |
| `tools/test_local_ci_shared_test_deduplication.py` | pins node-ID digests for three core lint files — untouched, listed so a surprise is visible |
| `tools/test_workspace_status.py` | pins a work-loop `SKILL.md` hash — untouched, listed for the same reason |

Two authoring constraints govern Task 5's prose.
`packs/core/.apm/skills/close-work/SKILL.md` is projected into `.claude/` and
`.agents/`, so it must cite no `contracts/`, `docs/`, or other repository-only
path. `tools/lint-guides-no-repo-only-refs.py` rejects any `RFC-NNNN` or
`ADR-NNNN` token in `guides/**`, any reference to a real `docs/specs/<slug>`
directory, and link targets containing an `adr`, `rfc`, or `specs` segment;
`.github/workflows/docs.yml` gates it. New assertion strings must not wrap across
a line. Projections are regenerated with `env FORCE=1 make build-self`.

## Design (LLD)

### Data and schema

`docs/lifecycle/<delivery_id>.json`, one record per delivery artifact.
**The filename is the delivery ID with no transformation** — `delivery_id` is
constrained so that it is already a safe basename, which removes the id→path
mapping entirely rather than specifying it. `docs/lifecycle/` is created once in
Task 5 with a `README.md` naming its single writer; enrolment never creates it.

**Records are Git-tracked.** They must survive across sessions and machines,
`workspace.toml` may point at them, and Wave 6 projects them. A record written
during a session is an ordinary working-tree change the maintainer commits; no
`.gitignore` entry is added.

The contract is `contracts/jsonschema/delivery-lifecycle-record.schema.json`,
carrying `$schema` (draft 2020-12), `"contract_version": "delivery-lifecycle-record.v1"`
matching every other file under `contracts/jsonschema/`, and
`"x-spec": ["docs/specs/thirty-day-cooling-and-retirement/"]`. Every object node
sets `additionalProperties: false` and a non-empty `required`.

| Field | Constraint |
| --- | --- |
| `schema` | const `delivery-lifecycle-record.v1` |
| `delivery_id` | `^[a-z0-9][a-z0-9-]{0,127}$` — no `/`, no `.`, so no traversal and no collision |
| `locator` | repository-relative POSIX path, no `..` segment |
| `aliases` | array of `locator`, `maxItems: 16` |
| `fingerprint` | `^sha256:[0-9a-f]{64}$` |
| `disposition` | enum `cool-30-days`, `retain-exception` (RFC §5 intents) |
| `post_closeout_result` | enum `Cooling`, `Retained`, `Retired`, `ExternalAdvisory` (subset of `close_work.POST_CLOSEOUT_RESULTS`) |
| `completion_event` | enum `merge`, `release`, `acceptance` |
| `completion_evidence_ref` | one of `commit:<40 hex>`, `pr:<digits>`, `run:<digits>` |
| `completed_on`, `review_on` | `^\d{4}-\d{2}-\d{2}$` |
| `timezone` | IANA key resolvable by `ZoneInfo` |
| `authority` | closed object of `source`/`write`/`delete`, each `{status, evidence_ref?}` |
| `confirmation_proof` | `^sha256:[0-9a-f]{64}$` — opaque by construction |
| `exception` | required iff `disposition == retain-exception`: `reason` (enum of obligation kinds), `owner_role` (`^[a-z][a-z0-9-]{1,63}$`, reusing `close_work._ACTOR_ROLE_RE`), `review_on`, optional `evidence_ref` |

`reason` is an enumerated obligation kind, not free text, so persisted rationale
and personal identity are unrepresentable rather than screened for (AC10).

Canonical serialization is `json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=True, allow_nan=False)` plus a trailing
newline — copying `surface_resolver.py`'s existing canonical form, not
`close_work.py`'s two inconsistent ones.

Bounds: `MAX_RECORD_BYTES = 64 * 1024`, `MAX_RECORD_DEPTH = 8`,
`MAX_ARTIFACT_BYTES = 8 * 1024 * 1024`. The record is read through
`file_safety.read_confined_regular_file(..., max_bytes=MAX_RECORD_BYTES)`. Depth
is checked on the parsed object, because `json.loads` raises `RecursionError`,
which is not a `ValueError`. `sha256_confined_regular_file` accepts no bound and
`file_safety.py` is byte-pinned, so the artifact-size check is a caller-side
`stat` in `cooling.py` before hashing.

### The transition table

`update_record(prior, proposed)` accepts exactly these ordered pairs and returns
`record-invalid` for anything else. `Retired` appears only as a target.

| From `(disposition, post_closeout_result)` | To | Occasion |
| --- | --- | --- |
| `(cool-30-days, Cooling)` | `(cool-30-days, Retired)` | AC33 approval |
| `(cool-30-days, Cooling)` | `(retain-exception, Retained)` | AC34 refusal or uncertainty |
| `(retain-exception, Retained)` | `(retain-exception, Retained)` | AC35 `renew`, with a new `exception.review_on` |
| `(retain-exception, Retained)` | `(cool-30-days, Cooling)` | AC35 `choose-cooling` |
| `(retain-exception, Retained)` | `(retain-exception, Retired)` | AC35 `confirm-deletion` |
| `(retain-exception, Retained)` | `(retain-exception, ExternalAdvisory)` | AC35 `advisory` |

### State and control flow

`enrol()` evaluates in this precedence, and each step's refusal is terminal:

1. `delivered` / `closed` / `persisted` → `not-delivered` / `not-closed` / `no-persistent-record`
2. selected completion event → `completion-event-required`
3. candidate present and `destination-selection` confirmed → `destination-unconfirmed`
4. resolve the surface through the Wave 1 resolver → `lifecycle-state-unwritable`
5. authority binding — the object `close_work._mutation_binding` returned for an authority fact registered in `_ISSUED_COORDINATION_AUTHORITIES`, with `resource` equal to this record's locator; a well-formed literal the seam never issued refuses → `authority-uncertain`
6. `_open_validated_parent(root, destination)` → `unsafe-target`
7. exclusive create, write canonical bytes, `os.replace` through the same descriptor → `enrolled`

`enrol_into()` does not exist as a public seam; steps 4–7 are one private
`_write_record(root, destination, record, binding)` that every write path —
`enrol` and `update_record` — funnels through, so no entry point bypasses the
candidate confirmation (AC15) or the authority binding (AC19).

`load_record()` evaluates: confined bounded read → strict parse → depth check →
schema validation → `delivery_id` equals the file's stem (AC11) → `review_on`
re-derived and compared (AC21). It performs no transition check, because it holds
no prior state; transitions belong to `update_record`.

**Error-to-code mapping** for the write seam, so AC20's "refusals carry a code"
is implementable rather than aspirational. The descriptor is closed in a
`finally`.

| Raised | Code |
| --- | --- |
| `ValueError` from `_open_validated_parent` or `relative_to` | `unsafe-target` |
| `OSError` with `ELOOP`, `ENOTDIR` | `unsafe-target` |
| `OSError` with `EACCES`, `EPERM`, `EROFS`, `ENOENT` | `lifecycle-state-unwritable` |

No `errno`, absolute path, or exception text enters the returned payload.

**Platform capability gate.** Copying `close_work.secure_effect_supported()`
(close_work.py:1281), the write refuses `lifecycle-state-unwritable` unless
`{os.open, os.stat, os.rename} <= os.supports_dir_fd` and `O_NOFOLLOW` and
`O_DIRECTORY` are both non-zero. Note for the implementer, verified on this
platform: **`os.replace` is absent from `os.supports_dir_fd` even though it
honours `src_dir_fd`/`dst_dir_fd` at runtime**; both it and `os.rename` are
`renameat`-backed, and `os.rename` cannot be substituted because it refuses an
existing destination on Windows. Gate on `os.rename`'s truthfully-reported
membership and call `os.replace`. Do not read `os.supports_dir_fd` for
`os.replace` and conclude the platform is unsupported, and never drop `dir_fd`
to make a write succeed.

**Temp-file cleanup** is the single `os.unlink(temp_name, dir_fd=descriptor)` in
`_write_record`'s failure path — the one call AC36 exempts, by line. The
target-kind check runs *before* the exclusive create, so the ordinary refusal
paths never reach it.

### Failure, edge cases, and resilience

Published refusal codes: `not-delivered`, `not-closed`, `no-persistent-record`,
`completion-event-required`, `destination-unconfirmed`,
`lifecycle-state-unwritable`, `unsafe-target`, `authority-uncertain`,
`record-invalid`, `naive-clock`, `unknown-timezone`, `not-due`,
`review-incomplete`, `fingerprint-drift`, `locator-unresolved`,
`missing-history`, `exception-envelope-invalid`. Success codes: `enrolled`,
`identity-verified`, `deletion-permitted`, `accepted`.

`missing-history` means **the completion-evidence reference cannot be
resolved** — an unreachable `commit:`/`pr:`/`run:` target. It is not about the
presence of a `.git` directory, which AC25 requires to be irrelevant.

`ZoneInfo` raises `ZoneInfoNotFoundError` from the same call as an unknown key,
so one `unknown-timezone` code covers a malformed key and an absent platform tz
database (slim containers, Windows without `tzdata`). There is no UTC fallback.

`deletion_allowed()` is affirmative: it returns `deletion-permitted` only when
all four proofs are present, so an unrecognized state can never read as
permission.

The AC32 attestation copies Wave 4's shipped human-confirmation shape
(`close_work.confirm_deletion`, close_work.py:1837-1875): it restates all six
answers exactly, names an approver role distinct from the proposing role, and
carries a human evidence reference, all validated at the deterministic seam.
It deliberately does **not** claim a cross-session single-use guarantee:
`_ISSUED_HUMAN_PROOFS` is a process-local set (close_work.py:44), so a
replay guarantee spanning the thirty-day gap would need persistence this wave
does not add. The claim is bounded to what is checkable — the answers came from
a party other than the one proposing them, in this turn.

The persisted `confirmation_proof` records that enrolment was confirmed and is
never re-matched later; nothing treats it as standing authority. Deletion
authority is never read from the record: Wave 4's seams reacquire it from named
evidence immediately before any mutation.

No lock is introduced: distinct records never share a file, and a same-record
concurrent write is whole-record last-writer-wins rather than a torn read. The
claim is bounded to torn reads and is not exercised against simultaneous writers.

## Tasks

### Task 1 — Contract, record shape, and dates

**ACs:** AC1–AC13.
**Verification mode:** TDD.
**Depends on:** none.

**Tests:** stub: true. Every row below is (input → observable).

| AC | Input | Observable |
| --- | --- | --- |
| AC1 | `(2027-02-25, America/New_York)` spring-forward; `(2027-10-25, America/New_York)` fall-back; `(2028-02-14, UTC)` leap day; `(2026-08-01, Asia/Singapore)` plain | `(result - completed_on).days == 30` |
| AC2 | `review_on=2026-08-31`, instants 08-30T23:59, 08-31T00:00, 09-01T00:00 SGT, each re-expressed in 3 reader zones | `due` = False, True, True — identical across readers |
| AC3 | `completed_on` = injected instant − 40 days | `record.completed_on` is that date; `due is True` |
| AC4 | any due record | `permission_granted is False`, `mutated == ()` |
| AC5 | naive datetime; `"Not/AZone"` | `naive-clock`; `unknown-timezone` |
| AC6 | `cooling.py` AST, alias-resolved | 8 clock symbols absent |
| AC7 | the schema file | top-level `required` == the 14 names; every object node closed |
| AC8 | extra key at top / in `authority.write` / in a complete `exception` | `record-invalid` ×3; valid payload → `None` |
| AC9 | delete each required key in turn | `record-invalid` |
| AC10 | `a/b`, `..`, `author:jane-doe`, `owner:j.doe`, `approved by a.person@example.com` | `record-invalid` |
| AC11 | file `spec-a.json` carrying `delivery_id: spec-b` | `record-invalid` |
| AC12 | shuffled-key payload; canonical bytes; `NaN` | equal bytes, trailing `\n`; `record-invalid` |
| AC13 | valid record padded past 64 KiB via `aliases`; valid object nested past depth 8 | `record-invalid`, no raise |

```python
# tests/roster/test_thirty_day_cooling_and_retirement.py
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
```

**Approach:** author the schema, then `CoolingRecord`, `validate_payload`,
`parse_record_bytes`, `canonical_bytes`, `compute_review_on`, and `is_due` in
`packs/core/.apm/skills/close-work/scripts/cooling.py`.

### Task 2 — Enrolment, the guarded write seam, and updates

**ACs:** AC14–AC24.
**Verification mode:** TDD.
**Depends on:** Task 1.

**Tests:** stub: true.

| AC | Input | Observable |
| --- | --- | --- |
| AC14 | each of 3 precondition failures; unset event; 4 non-completion events | 3 distinct codes; `completion-event-required` ×5 |
| AC15 | no candidate; candidate with confirmation `required` | `destination-unconfirmed`, no file |
| AC16 | absent destination dir; present dir + valid inputs | `lifecycle-state-unwritable`, no dir; `enrolled`, file exists |
| AC17 | `chmod 0o555` dir, candidate silent; same dir, candidate declares `writable` | `lifecycle-state-unwritable` both times |
| AC18 | parent replaced by symlink to outside root | `unsafe-target`; link target and repo both unchanged |
| AC19 | binding `None`; wrong `action`; `resource` of a different record | `authority-uncertain` ×3, no file |
| AC20 | each refusal above | code in the published set; payload has no `/`-rooted path, no errno, no exception text |
| AC21 | stored `review_on` = `2026-12-31` | `record-invalid` |
| AC22 | every pair in the transition table; the complement | accepted; `record-invalid` |
| AC23 | enrol then `update_record`, reload in a subprocess | identical `canonical_bytes` |
| AC24 | `tomllib.load(workspace.toml)` | no `cooling`/`review_on`/`completed_on`/`lifecycle_record` key at any depth |

The AC17 fixture skips loudly when `os.geteuid() == 0`, because a root container
can write through mode `0o555` and the case would pass vacuously.

```python
# tests/roster/test_thirty_day_cooling_and_retirement.py (continued)

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
    cooling = _load()
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = _destination(tmp_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(outside, target_is_directory=True)
    result = cooling.enrol(**_enrol_kwargs(tmp_path, make_destination=False))
    assert result.code == "unsafe-target"
    assert list(outside.iterdir()) == []


# STUB: AC19
@pytest.mark.parametrize(
    "binding",
    [
        None,
        "never-issued",  # well-formed literal the seam never registered
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
```

**Approach:** implement `enrol()` in the documented precedence, the private
`_write_record()` that every write funnels through, `update_record()` driven by
the transition table, and `load_record()`. Expose `close_work._open_validated_parent`
and `close_work._load_regular_sibling` under public names and call them. The
helpers `_enrol_kwargs`, `_destination`, `_update_kwargs`, `_TRANSITION_TABLE`,
and `_TRANSITION_COMPLEMENT` are built in this task from the transition table
above; `_TRANSITION_COMPLEMENT` is the full pair product minus the table.

### Task 3 — Identity and deletion permission

**ACs:** AC25–AC30.
**Verification mode:** TDD with real Git fixtures.
**Depends on:** Task 2.

**Tests:** stub: true.

| AC | Input | Observable |
| --- | --- | --- |
| AC25 | 5 repos: squash, merge, rebase, `--depth=1` clone, `.git` deleted — record written **before**, verified **after** (clone: written in origin, verified in clone) | `identity-verified` |
| AC26 | `record_rename(r, new)` | `locator == new`; old locator in `aliases` |
| AC27 | all proofs; drift; unresolvable locator; unresolvable evidence ref; `delete.status = "banana"` | `deletion-permitted`; `fingerprint-drift`; `locator-unresolved`; `missing-history`; `authority-uncertain` |
| AC28 | resolvable evidence ref in a tree with no `.git` | not `missing-history` |
| AC29 | stored `delete.status = "delegated"`, no live grant | `authority-uncertain` |
| AC30 | `source = external-owned`, `delete = none` | `authority-uncertain` |

`_build_repository(tmp_path, topology)` is built in this task: it `git init`s,
commits the artifact, writes the record, then performs the real topology
operation, returning the root to verify in. It skips loudly if `git` is absent.

```python
# tests/roster/test_thirty_day_cooling_and_retirement.py (continued)

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
    record = _record(
        cooling,
        authority={
            "source": {"status": "external-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "none"},
        },
    )
    inputs = _permission_inputs(tmp_path, "all-proofs") | {"record": record}
    assert cooling.deletion_allowed(**inputs).code == "authority-uncertain"
```

**Approach:** `verify_identity()` re-resolves the locator or an alias, checks the
artifact size caller-side, and recomputes the fingerprint via
`file_safety.sha256_confined_regular_file`. `deletion_allowed()` is affirmative.
Nothing in `cooling.py` imports `subprocess`; only the fixtures shell out.

### Task 4 — Day-30 review, retirement, and exceptions

**ACs:** AC31–AC36.
**Verification mode:** TDD.
**Depends on:** Task 3.

**Tests:** stub: true.

| AC | Input | Observable |
| --- | --- | --- |
| AC31 | omit each of the six answers | `review-incomplete` ×6 |
| AC32 | attestation never issued; issued then replayed | `review-incomplete` ×2 |
| AC33 | six approvals | `post_closeout_result == "Retired"`, readable after reload |
| AC34 | one `refuse`; one `uncertain`; each with one of the three exception fields missing | `retain-exception` complete ×2; `exception-envelope-invalid` ×3 |
| AC35 | the four outcomes; `delete-now` | `accepted` ×4 mapping to table pairs; `exception-envelope-invalid` |
| AC36 | `cooling.py` AST, alias-resolved, receiver-typed | 7 removal symbols absent except the named temp cleanup |

```python
# tests/roster/test_thirty_day_cooling_and_retirement.py (continued)

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
    ["missing-answers", "missing-approver", "missing-evidence",
     "answers-differ", "approver-equals-proposer"],
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
    assert set(result.record.exception) >= {"reason", "owner_role", "review_on"}


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
    assert "os.unlink(temp_name, dir_fd=" in source
```

**Approach:** `review()` and `review_exception()` take the record, a closed
checks mapping, an issued attestation, and the injected instant, and route every
state change through `update_record()`. Neither performs a deletion.

### Task 5 — Doctrine, instructional surfaces, release, projections

**ACs:** AC37–AC40.
**Verification mode:** Goal-based plus visual/manual QA.
**Tests:** `no stub (mode)`.
**Depends on:** Task 4.

AC39's enumerated pairs — each file must gain the first string and lose the second:

| File | Must contain | Must not contain |
| --- | --- | --- |
| `guides/core/how-to/close-and-disposition-work.md` | "Wave 5 computes the review date and enrols the record" | "It does not calculate dates, start a timer, or retire anything" |
| `guides/core/reference/work-intake-routing-and-lifecycle.md` | "Result" (table header) | "Wave 4 result" |
| `guides/core/reference/work-intake-routing-and-lifecycle.md` | "Enrol, compute the review date, and review on day 30" | "Wave 5 owns dates, clocks, due state, and retirement" |
| `guides/core/reference/workspace-toml-schema.md` | "workspace.toml may point at cooling state and never owns it" | "gains no receipt or cooling schema in Wave 4" |
| `packs/core/README.md` | "cooling records live outside workspace.toml" | "`cool-30-days` is classification only in this release" |
| `packs/core/.apm/skills/close-work/SKILL.md` | "Enrol, then answer whether the record is due" | "Do not start a timer" |

**Approach:** create `docs/lifecycle/README.md` naming `close-work` as its single
writer; add `docs/lifecycle/` to `docs/architecture/overview.md`'s tree and a row
to `contracts/README.md`'s inventory; update the six surfaces above and
`docs/architecture/work-intake-and-artifact-routing.md` (including its "Last
verified surface" section, the Core version, and the Windows tz-database note);
amend the two anchor tests rather than deleting them; bump `packs/core/pack.toml`
and `packs/core/.claude-plugin/plugin.json` to `2.14.0` with the topmost dated
`## [core][2.14.0]` changelog heading; regenerate with `env FORCE=1 make build-self`.

**Manual QA** drives a fixture record with a backdated `completed_on` so a day-30
review is reachable on the day of the PR, and records three artifacts: the
enrolment result, the due answer, and one review outcome. Stop point: Wave 4's
deletion seams are exercised only to the `preview_deletion` call; no confirmation
is issued and nothing is deleted.

## Verification

`make lint-ruff`, `make lint-mypy`, `SKIP_SAST=1 make build-check`, `make test`,
`make sast`, `make site-link-check`, `npm test --prefix web`, and — for the
emitted-changelog test — `python3 tools/build-site.py && npm run build --prefix web
&& npm run build --prefix docs-site`.

Every new guard carries a mutation proof: the property is made false in the
source, the guard is run and observed to fail, the source is restored, and the
restoration is confirmed byte-identical. The AC6 and AC36 AST guards are mutated
with a *receiver-variable* form (`p.unlink()`, `dt.now()`), not the literal form
the matcher already sees, because that is the form a real implementation would
use and the form a weaker matcher would miss.

## Risks

- A pack version bump reddens three literals in the Wave 4 roster test, and the
  SKILL.md rewrite reddens the "Do not start a timer" pin in the pack suite. Both
  are updated in Task 5, not weakened.
- `close_work.py` gains two public aliases and nothing else. If any further edit
  to that file becomes necessary, surface it rather than absorbing it.
- The no-lock decision is bounded to torn reads and is not exercised against two
  simultaneous enrolments. A concurrency defect found later is a new finding, not
  a silent fix here.
- The pre-EXECUTE review closed at owner direction after round 2 returned 43
  findings of which 33 were caused by round 1's own fixes. Eight contract-level
  defects were fixed; the remainder were judged mechanism detail that the tests
  above settle. Post-GATES adversarial, security, and quality review still run
  against real code.
