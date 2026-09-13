# Plan: loop-event-schema-version

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`
  (`_cmd_transition`'s `pending_data` literal at 1608-1623 is the one write site;
  the outbox replay at 626 is the second path); `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`
  (the existing envelope suite, whose `test_event_schema_field_names` already
  asserts a key *superset* and therefore admits a new field without amendment);
  `contracts/README.md` (authored-source authority model and the file table);
  `contracts/jsonschema/*.schema.json` (naming and shape precedent).
  No named uncertainty: both write paths and both readers are already located.

## Approach

One field, two write paths, one schema. The field is added to the dict literal
in `_cmd_transition`; the outbox replay path is deliberately *not* touched, which
is what makes a record written by an older engine replay unchanged.

The schema and its corpus come second because the corpus is recorded from the
engine after the field exists — synthesising it first would let the schema pass
against a line shape the engine never emits.

## Constraints

- The first seven fields keep their names, order and values (`telemetry.md` § 8).
- Absent means version 1. No reader this repository owns may require the key.
- Recording stays graceful: no failure here may cost a transition.

## Construction tests

The envelope suite already asserts a key superset, so admitting the new field
needs no change to an existing assertion — the new cases are additive. The case
that cannot be inferred is the replay passthrough: it is the only one that
distinguishes "stamp every line" from "stamp what this writer produces", and a
build that retro-stamps passes every other test in the suite.

The corpus is recorded from a real engine run rather than written by hand, so the
schema is validated against emitted shapes rather than intended ones.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `contracts/jsonschema/loop-run-event.schema.json` | T2 | Schema validates the recorded corpus | Registry row in `contracts/README.md` |
| `docs/architecture/telemetry.md` § 5.1 | T3 | Field inventory matches the emitted line | No count contradicts the emitted line |
| `docs/product/changelog.md` + `packs/core` version | T3 | Version bump with entry | Entry present, versions match |
| `project-knowledge` | closeout | Capture receipt | Receipt or `project-knowledge unavailable` |

## Design (LLD)

### Data & schema

`schema` is an integer, value 1, added to the `pending_data` dict literal above
the `_lifecycle_fields` spread so the first seven fields keep their position.
Absent means version 1; that rule is what the replay passthrough preserves.

### State & control flow

Two paths reach `_append_events_jsonl`. The transition path builds a fresh dict
and gains the field. The recovery path at `loop-engine.py:626` replays a
`events.pending` record as it found it — a record written before this change has
no `schema` key and must keep none.

## Tasks

### T1: Stamp the version on the written line

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`

**Tests:**
- `stub: true` — one compilable red contract-surface assertion for AC-0001,
  validated in disposable scratch (compile: `python -m py_compile` OK;
  intended red: `KeyError: 'schema'`, 1 failed / 3 passed, the 3 passing being
  the harness's own copied cases, which proves the red is the assertion and not
  a broken fixture). Disposable copy removed.

```python
class TestSchemaVersionStub:
    def test_event_line_carries_schema_version_one(self, tmp_path) -> None:
        # STUB: AC-0001
        repo = _init_git_repo(tmp_path)
        spec_dir = _make_spec_dir(repo)
        _engine_init(repo, spec_dir)
        _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
        event = json.loads((repo / ".loop-run" / "events.jsonl").read_text().strip())
        assert event["schema"] == 1
```

- A pending record carrying no `schema` key replays unchanged. Verifies AC-0002.
  This is the case the rest of the suite cannot see: a retro-stamping build
  passes everything else.

**Approach:**
- Add the key to the `pending_data` literal; leave the replay path alone.

**Done when:** both new cases pass in
`packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`, and the
pre-existing cases in that file still pass unchanged.

### T2: Record the corpus and author the contract schema

**Depends on:** T1

**Touches:** `contracts/jsonschema/loop-run-event.schema.json`, `contracts/README.md`, `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl`

**Tests:**
- The corpus holds both a versioned and a legacy record, and the schema
  validates every line. Verifies AC-0003.
- The schema rejects a bad `schema` value and a record missing an identity
  field. Verifies AC-0006.
- `contracts/README.md`'s file table names the schema. Verifies AC-0004.

**Approach:**
- Record the corpus by driving real transitions, not by authoring lines.
- `contracts/` is the authored source; no `agentbundle/_data/` mirror.

**Done when:** the corpus validates and the registry row is present.

### T3: Make the architecture and the release true

**Depends on:** T1

**Touches:** `docs/architecture/telemetry.md`, `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`

**Tests:**
- `telemetry.md` § 5.1's stated field count equals the emitted key count.
  Verifies AC-0005.
- The events poller yields the same parsed result for a legacy record and an
  explicit `schema: 1` record. Verifies AC-0007.

**Approach:**
- Bump `pack.toml` and `.claude-plugin/plugin.json` together per
  `packs/AGENTS.md`, and write the changelog entry.

**Done when:** the stated count matches a line the engine emits, and both
version files agree.

## Rollout

Additive and reversible. Both known readers tolerate the field — the suite
asserts a superset and the MCP bridge polls by byte offset. Reversal is removing
one key.

## Risks

- **A build retro-stamps the replayed record**, which passes every test except
  AC-0002's. That single case is the whole defence, which is why it is called
  out in Construction tests rather than left as one bullet among many.

## Changelog

- 2026-09-12 — Split out of `loop-telemetry-export` so the format gains its
  version before any exporter consumes it, and so a `packs/core` version bump
  does not wait on a PyPI release. The exporter spec retains no criterion for
  the version field and cites this one as a dependency.
