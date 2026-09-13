# Plan: loop-telemetry-export

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/pack.toml` (where the optional dependency is
  declared); `packages/agentbundle/agentbundle/_data/pack.schema.json:217-246`
  (the dormant `[[pack.runtime-dependencies]]` shape this activates);
  `Makefile:515-516`, `pyproject.toml:16`, `pyproject.toml:94-96`,
  `Makefile:361-366` (the four literal enumerations a new distribution must join);
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
| ADR-0111 (decision rationale) | T5 | Accepted ADR file | Cited by `telemetry.md` § 9 |
| `docs/architecture/telemetry.md` | T5 | §§ 2, 5.2, 5.3, 8 diff | Anchors resolve |
| `guides/core/how-to/export-loop-telemetry.md` | T5 | Guide with the disclosure sentence | `check-guide-index.py` green |
| `packs/core/pack.toml` + lint reporting | T3 | Lint naming the unsatisfied dependency | AC-0039 green |
| `docs/product/changelog.md` | T5 | Version bump with entry | Entry present |
| `docs/specs/README.md` | T5 | Active-list row | Row present |
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

**Depends on:** none (the package's profile interface is a published contract)

**Touches:** the package's `mappings/work_loop.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the profile
  interface is published in the package's `docs/profiles.md`, but the module
  path is fixed only once the package exists. Constraint: declaration only, no
  logic. Required outcome: the three declarations match `telemetry.md` § 5.1.
  Verification mode: TDD. Proof obligation: the profile's declared fields are
  asserted against the envelope the engine actually emits, not against a
  restated list.
- The profile declares `at`, `result`, `run_id` with `seq`, and its allowlist.
  Verifies AC-0040.
- The documented invocation selects the registered profile and a real emitted
  line reaches a live Collector at the declared destinations. Verifies AC-0044.

**Done when:** the profile's declarations are asserted against a real emitted line.

### T2: Configuration wiring

**Depends on:** none

**Touches:** `guides/core/how-to/export-loop-telemetry.md`, the wiring tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the wiring seam is
  the documented invocation plus the package's `--config` and `--input` flags,
  whose exact form is fixed only once `jsonl-otlp-exporter` ships. Constraint:
  the package reads one config path; precedence is this catalogue's wiring, not
  the package's behaviour. Required outcome: repository file before user file,
  and `--input` resolved to the repository event log. Verification mode: TDD.
  Proof obligation: the precedence assertion runs over two fixture layout files
  that differ only in their endpoint, so a build reading the wrong one fails.
- The documented invocation resolves `--config` to the repository
  `agentbundle-layout.toml` before the user one. Verifies AC-0041.
- It resolves `--input` to the repository root's `.loop-run/events.jsonl`.
  Verifies AC-0043.

**Approach:**
- The package reads one `--config` path; repository-before-user precedence is
  this catalogue's wiring, not the package's behaviour.

**Done when:** the precedence is asserted over two fixture layout files.

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

- A pending record carrying no `schema` key replays unchanged. Verifies AC-0047.
  This is the case the rest of the suite cannot see: a retro-stamping build
  passes everything else.

**Approach:**
- Add the key to `_cmd_transition`'s `pending_data` literal; leave the replay
  path at `loop-engine.py:626` alone.

**Done when:** both new cases pass and the pre-existing cases in that file still
pass unchanged.

### T7: Record the corpus and author the contract schema

**Depends on:** T6

**Touches:** `contracts/jsonschema/loop-run-event.schema.json`, `contracts/README.md`, `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl`

**Tests:**
- The corpus holds a versioned and a legacy record, and the schema validates
  every line. Verifies AC-0048.
- The schema rejects a bad `schema` value and a record missing an identity field.
  Verifies AC-0049.
- `contracts/README.md`'s table names the schema. Verifies AC-0050.
- The events poller yields the same parsed result for a legacy record and an
  explicit `schema: 1` record. Verifies AC-0052.

**Approach:**
- Record the corpus by driving real transitions, not by authoring lines.

**Done when:** the corpus validates and the registry row is present.

### T5: Records, architecture and disclosure

**Depends on:** T1, T2, T3, T4

**Touches:** `docs/architecture/telemetry.md`, `guides/core/how-to/export-loop-telemetry.md`, `docs/specs/README.md`, `docs/product/changelog.md`

**Tests:**
- The guide states the capability, payload and destination. Verifies AC-0020.
- § 5.3 carries no stale claim and every `agentbundle.md` anchor resolves. Verifies AC-0021.
- § 2 carries neither retired string. Verifies AC-0022.
- Every `agentbundle.md` anchor resolves. Verifies AC-0045.
- The field count in § 5.1 equals the emitted key count. Verifies AC-0051.
- No documented exit code falls in the 2–9 reserved band. Verifies AC-0042.

**Done when:** `check-guide-index.py` is green and no dead anchor remains.

## Rollout

Depends on `jsonl-otlp-exporter` shipping first; the event-line version (T6, T7)
is internal to this spec and sequenced ahead of the integration tasks.
Nothing here changes existing behaviour: the declaration is optional and the
documentation describes a tool the adopter installs deliberately.

## Risks

- **The gate enumeration is four separate literal lists.** Adding the package to
  three of four leaves a hole that `make test` reports green. T4's `Done when`
  is deliberately a deliberate-failure probe rather than a grep.

## Changelog

- 2026-09-13 — The separate event-line-version spec was folded back in on the
  owner's ruling: both it and this spec are catalogue-scoped, and their
  separation was a sequencing constraint that task order expresses. Its seven
  criteria return as AC-0046 through AC-0052.
- 2026-09-12 — Reduced to this catalogue's integration when the sender's contract
  was split into `jsonl-otlp-exporter`. Thirty-four criteria were retired to that
  spec; identity is append-only, so none is
  reused here.
