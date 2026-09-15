# Plan: loop-telemetry-export

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/pack.toml` (where the optional dependency is
  declared); `packages/agentbundle/agentbundle/_data/pack.schema.json:217-246`
  (the dormant `[[pack.runtime-dependencies]]` shape this activates);
  `pyproject.toml` `pythonpath` and `[tool.mypy] files`, the `Makefile`'s
  `PYTHONPATH` assignment and its test-suite invocations, the pip-audit
  `--build-system` leg, and `tools/lint-mypy.py`'s `TYPED_PACKAGES`
  (**six** literal enumerations a new distribution must join — AC-0031 names
  four of them, and four do not achieve its own purpose clause; see the
  verification ledger);
  `docs/architecture/telemetry.md` (the architecture this reconciles);
  `packages/agentbundle/agentbundle/workspace_mcp.py:1576-1620` (the existing
  layout-file reader, for precedence precedent). Named uncertainty: nothing reads
  `[[pack.runtime-dependencies]]` today, so its reporting shape is set here.

## Approach

Four small integrations and a documentation reconciliation. None of this
specifies how the sender behaves — that is `jsonl-otlp-exporter`'s contract, and
restating it here would create a second home that drifts.

The mapping profile is the only code this delivery contributes to the package,
and it is data plus a three-field declaration.

## Constraints

- No pack gains a network path.
- Reporting only. Tier 1 is detect and fail clean; the installer never acquires.
- The sender's behaviour is never specified here.

## Construction tests

The gate enumeration is the case that cannot be inferred: each site is a literal
list, so a package absent from one is checked by nothing while `make test` still
reports green. The test reads each site rather than trusting that adding the
package to one added it to all.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| ADR-0115 (decision rationale) | T5 | Accepted ADR file | Cited by `telemetry.md` § 9 |
| `docs/architecture/telemetry.md` | T5 | §§ 2, 5.2, 5.3, 8 diff | Anchors resolve |
| `guides/core/how-to/export-loop-telemetry.md` | T5 | Guide with the disclosure sentence | `check-guide-index.py` green |
| `packs/core/pack.toml` + lint reporting | T3 | Lint naming the unsatisfied dependency | AC-0039 green |
| `docs/product/changelog.md` | T5 | Version bump with entry | Entry present |
| `project-knowledge` | closeout | Capture receipt | Receipt or `project-knowledge unavailable` |

## Design (LLD)

### Interfaces & contracts

The `work_loop` profile declares three things against the envelope in
`telemetry.md` § 5.1: `at` is the timestamp, `result` is the severity, and
`run_id` with `seq` are the record identity. Everything else becomes an
attribute by default, so the profile stays four lines of declaration.

### Dependencies & integration

`[[pack.runtime-dependencies]]` is declared in `packs/core/pack.toml` with
`optional = true`. This delivery writes the first reader of that schema, and it
reports only — naming an unsatisfied optional dependency and exiting 0.

## Tasks

### T1: The work-loop mapping profile

**Depends on:** T6 (this task's pinned assertion compares the profile's
`allowlist` against the keys of a line the engine emits, and T6 adds `schema` to
that envelope. Run first, it ships a profile one field short and its own
assertion turns red the moment T6 lands. The package's profile interface is a
published contract and imposes no ordering; the envelope does. The rationale sits
inside parentheses deliberately: the scheduler reads task identifiers out of the
prose before the first `(`, so an identifier named there becomes a dependency.)

**Touches:** `packs/core/.apm/skills/work-loop/profiles/work-loop.toml`,
`packs/core/tests/skills/work-loop/test_work_loop_profile.py`

**Tests:**
- `stub: true` — three compilable assertions for AC-0040, validated in disposable
  scratch. **The profile is data, not code** (ADR-0115): it is a TOML file at a
  path AC-0040 fixes, with keys AC-0040 fixes, so the assertion needs no symbol
  from the unshipped package and the earlier `no stub
  (implementation-discovered)` record was wrong. Compile: `python -m py_compile`
  OK. Intended red: all three fail with `FileNotFoundError` on the profile path,
  because the file does not exist yet (3 failed). Proof the red is the assertion
  rather than a broken harness: pointed at a profile generated from a line the
  engine actually emitted and carrying the pinned `success = 9` / `failure = 17`
  map, the same three pass (3 passed), and changing `success` to 10 fails one of
  them — so the pinned pairs are asserted, not merely present. That run also measured
  the envelope — **13 keys today**: `at`, `awaiting_input`, `budgets`, `event`,
  `from`, `phase_s`, `phase_started_at`, `result`, `run_id`, `seq`, `spec`, `to`,
  `waived`, becoming 14 once T6 adds `schema`, which is why T5 now depends on T6.
  Disposable copies removed.

```python
def _engine_module():
    """The engine loaded by path — the same recipe the envelope suite uses."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "core_work_loop_loop_engine_profile_under_test",
        _REPO / "packs/core/.apm/skills/work-loop/scripts/loop-engine.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _one_emitted_line(tmp_path: Path) -> dict:
    """Drive one real transition and return the line it appended."""
    from test_loop_engine_events_jsonl import (
        _engine_init, _init_git_repo, _make_spec_dir, _run, _LOOP_ENGINE,
    )

    repo = _init_git_repo(tmp_path)
    spec_dir = _make_spec_dir(repo)
    _engine_init(repo, spec_dir)
    _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
    return json.loads((repo / ".loop-run" / "events.jsonl").read_text().splitlines()[-1])


class TestWorkLoopProfile:
    def test_profile_declares_the_envelope_fields(self) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["timestamp_field"] == "at"
        assert profile["timestamp_format"] == "rfc3339"
        assert profile["severity_field"] == "result"
        assert profile["identity"] == ["run_id", "seq"]

    def test_severity_map_is_the_pinned_pairs_and_covers_every_gate_result(self, tmp_path) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["severity_map"] == {"success": 9, "failure": 17}
        # The pinned pairs and the engine's own values are asserted together on
        # purpose: pinning literals alone would silently stop covering the engine
        # the day a third gate result is added.
        missing = set(_engine_module()._GATE_RESULTS.values()) - set(profile["severity_map"])
        assert not missing, f"severity_map omits {sorted(missing)}"

    def test_allowlist_is_exactly_the_unrouted_emitted_keys(self, tmp_path) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        emitted = set(_one_emitted_line(tmp_path))
        routed = {"at", "result", "run_id", "seq"}
        assert set(profile["allowlist"]) == emitted - routed
```

- `no stub (implementation-discovered)` for AC-0044. Discovery predicate: the
  invocation's flag spelling is fixed only once `jsonl-otlp-exporter` ships.
  Constraint: the profile is passed as a file through `--profile`; nothing is
  registered inside the package. Required outcome: a line the engine emitted
  reaches a live Collector with each declared field at its declared destination.
  Verification mode: TDD. Proof obligation: the assertion reads the Collector's
  received record, not the sender's own log of what it intended to send.

**Done when:** the three AC-0040 assertions pass against the shipped profile, and
a real emitted line is observed at the Collector.

### T2: Configuration wiring

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/telemetry_layout.py` (new — the
per-setting resolver and the invocation it renders),
`guides/core/how-to/export-loop-telemetry.md`, the wiring tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the wiring seam is
  the documented invocation plus the package's `--config` and `--input` flags,
  whose exact form is fixed only once `jsonl-otlp-exporter` ships. Constraint:
  the package reads one config path; precedence is this catalogue's wiring, not
  the package's behaviour. Required outcome: repository file before user file,
  and `--input` resolved to the repository event log. Verification mode: TDD.
  Proof obligation: the precedence assertion runs over two fixture layout files
  that differ only in their endpoint, so a build reading the wrong one fails.
- Per-setting resolution over two fixture layout files: a setting the repository
  file declares comes from there; a setting it omits while the user file declares
  it comes from the user file. A whole-file-wins implementation fails the second
  case. Verifies AC-0041.
- It resolves `--input` to the repository root's `.loop-run/events.jsonl`.
  Verifies AC-0043.

**Approach:**
- The package reads one `--config` path; repository-before-user precedence is
  this catalogue's wiring, not the package's behaviour. So the precedence needs a
  caller that can be asserted: `telemetry_layout.resolve(repo_root, user_path)`
  reads both `agentbundle-layout.toml` files and returns the merged `[telemetry]`
  settings plus the `--config`/`--input` arguments the documented invocation uses.
- The merge is **per setting**, not per file. `workspace_mcp.py:1576-1620` is the
  precedent for reading these files but not for merging them: its
  `_read_layout_bases` picks a whole scope per section, so reusing it would pass
  the first fixture case and fail the second. The guide documents the resolver's
  output; it does not restate the precedence rule.

**Done when:** the precedence is asserted over two fixture layout files, through
the resolver rather than through prose.

### T3: Declare and report the optional runtime dependency

**Depends on:** none

**Touches:** `packs/core/pack.toml`, the catalogue lint's reporting path, its tests

**Tests:**
- With the distribution absent, `agentbundle catalogue lint` names it as an
  optional unsatisfied runtime dependency of `core`, exits 0, and invokes no
  package manager. Verifies AC-0039.

**Done when:** a lint run reports the dependency without failing and without
invoking pip, npm, uv or pipx.

### T4: Put the distribution inside the gates

**Depends on:** none

**Touches:** `pyproject.toml`, `Makefile`

**Tests:**
- The package name appears in the root `pythonpath`, mypy's `files`, the
  `Makefile` test-suite invocations, and the pip-audit build-system leg. Each is
  read and asserted, because each is a literal list. Verifies AC-0031.

**Done when:** a deliberate failing test inside the package is reported by
`make test` — proving the suite is reached rather than merely listed.

### T6: The event line carries its version

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`

**Tests:**
- `stub: true` — one compilable red contract-surface assertion for AC-0046,
  validated in disposable scratch (compile: `python -m py_compile` OK; intended
  red: `KeyError: 'schema'`, 1 failed / 3 passed, the three passing being the
  harness's own copied cases, which proves the red is the assertion and not a
  broken fixture). Disposable copy removed.

```python
class TestSchemaVersionStub:
    def test_event_line_carries_schema_version_one(self, tmp_path) -> None:
        # STUB: AC-0046
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        event = json.loads((repo / ".loop-run" / "events.jsonl").read_text().strip())
        assert event["schema"] == 1
```

- `stub: true` — one compilable assertion for AC-0047, validated in disposable
  scratch. This is the case the rest of the suite cannot see: a retro-stamping
  build passes everything else.

  **Its red is a mutation, not an absence, and that is deliberate.** AC-0047
  preserves a property that already holds at HEAD, so no feature-absence red
  exists: run against the current engine the assertion is green (4 passed).
Non-vacuity was proved instead by two mutations of the
  replay branch at `loop-engine.py:626`, each inserted before the append:

  - `pending["schema"] = 1` (retro-stamping) fails the key-absence assertion.
  - `pending["spec"] = "docs/specs/other"` (rewriting any other field) fails
    **only** `replayed == legacy`, which is what earns that assertion its place.
    AC-0047 says the record is appended *unchanged*, and a key-absence check
    alone passes a build that rewrote every other field.

  The `len(lines) == 2` assertion is load-bearing too: without it a pending
  record the engine *discards* rather than replays still satisfies the key check,
  and the retro-stamp mutant passes — which is how the first draft of this stub
  failed its own mutation run. At HEAD the whole file is green (44 passed,
  5 skipped). Compile: `python -m py_compile` OK. Disposable copies removed.

```python
class TestReplayPreservesLegacyRecord:
    def test_replayed_pending_without_schema_stays_without_schema(self, tmp_path) -> None:
        # STUB: AC-0047
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        run_id = _engine_init(repo, spec_dir)
        state = json.loads((spec_dir / "engine-state.json").read_text())
        legacy = {
            "seq": state["transition_sequence"], "run_id": run_id,
            "spec": "docs/specs/test-spec", "from": "INIT", "event": "init",
            "to": state["state"], "at": "2026-01-01T00:00:00Z",
        }
        (repo / ".loop-run" / "events.pending").write_text(json.dumps(legacy))
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        lines = (repo / ".loop-run" / "events.jsonl").read_text().splitlines()
        assert len(lines) == 2, f"replay must precede the new record: {lines}"
        replayed = json.loads(lines[0])
        assert "schema" not in replayed
        assert replayed == legacy, "the replayed record must be unchanged, not merely unstamped"
```

**Approach:**
- Add the key to `_cmd_transition`'s `pending_data` literal; leave the replay
  path at `loop-engine.py:626` alone.

**Done when:** both new cases pass and the pre-existing cases in that file still
pass unchanged.

### T7: Record the corpus and author the contract schema

**Depends on:** T6

**Touches:** `contracts/jsonschema/loop-run-event.schema.json`, `contracts/README.md`, `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl`, `packages/agentbundle/tests/unit/test_workspace_mcp_events_poller.py`

**Tests:**
- The corpus holds a versioned and a legacy record, and the schema validates
  every line. Verifies AC-0048.
- The schema rejects a bad `schema` value and a record missing an identity field.
  Verifies AC-0049.
- `contracts/README.md`'s table names the schema. Verifies AC-0050.
- The events poller yields the same parsed result for a legacy record and an
  explicit `schema: 1` record. Verifies AC-0052. The two records are fed to
  `workspace_mcp.py`'s poller and its two parsed results compared to each other,
  so the assertion fails if the poller ever branches on the key's presence.
- The schema's `$comment` names this spec's path. Verifies AC-0053.

**Approach:**
- Record the corpus by driving real transitions, not by authoring lines.

**Done when:** the corpus validates, the registry row is present, and the poller
returns equal parsed results for the legacy and versioned records.

### T5: Records, architecture and disclosure

**Depends on:** T1, T2, T3, T4, T6, T7 (T6 creates the `schema` key that
AC-0051's field count measures, and T7 records the corpus the count is read from,
so running this task first would pin § 5.1 to a field count one short of what
ships.)

**Touches:** `docs/architecture/telemetry.md`,
`guides/core/how-to/export-loop-telemetry.md`, `docs/product/changelog.md`,
`packs/core/tests/skills/work-loop/test_telemetry_disclosure_contract.py`
(new — the goal-based checks for this task's criteria).
`docs/specs/README.md` was removed by amendment 1: it carries a section
headed "Why there is no index", and ADR-0112 decides that an index over a
document corpus is generated or absent. The obligation was impossible as
written.

**Tests:**
- The guide states the capability, payload and destination. Verifies AC-0020.
- § 5.3 carries no stale claim and every `agentbundle.md` anchor resolves. Verifies AC-0021.
- § 2 carries neither retired string. Verifies AC-0022.
- Every `agentbundle.md` anchor resolves. Verifies AC-0045.
- The field count in § 5.1 equals the emitted key count. Verifies AC-0051.
- No exit code named in `guides/core/how-to/export-loop-telemetry.md` falls in
  the 2–9 reserved band. Verifies AC-0042. The guide is the named set: an
  assertion over "documented" codes has no file to read.
- § 2 names the sender, states that it is separately installed, and states that
  nothing is sent until an endpoint is configured. Verifies AC-0054. This is the
  positive half: AC-0021 and AC-0022 only delete stale claims, and a § 2 reduced
  to a bare heading satisfies both of them.

**Done when:** `check-guide-index.py` is green and no dead anchor remains.

## Rollout

Depends on `jsonl-otlp-exporter` shipping first; the event-line version (T6, T7)
is internal to this spec and sequenced ahead of the integration tasks.
Nothing here changes existing behaviour: the declaration is optional and the
documentation describes a tool the adopter installs deliberately.

## Risks

- **The gate enumeration is six separate literal lists.** Adding the package to
  five of six leaves a hole that `make test` reports green — and two of the six
  are not the surfaces the criterion names, so satisfying AC-0031 literally is
  not sufficient. T4's `Done when` is deliberately a deliberate-failure probe
  rather than a grep, because a grep would have passed at four.

## Changelog

- 2026-09-13 — The separate event-line-version spec was folded back in on the
  owner's ruling: both it and this spec are catalogue-scoped, and their
  separation was a sequencing constraint that task order expresses. Its seven
  criteria return as AC-0046 through AC-0052.
- 2026-09-12 — Reduced to this catalogue's integration when the sender's contract
  was split into `jsonl-otlp-exporter`. Thirty-four criteria were retired to that
  spec; identity is append-only, so none is
  reused here.
