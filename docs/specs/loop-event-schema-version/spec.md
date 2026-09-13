# Spec: loop-event-schema-version

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — the field is additive and `docs/architecture/telemetry.md` § 8 already permits it
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/loop-run-event.schema.json`](../../../contracts/jsonschema/loop-run-event.schema.json)
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Objective

The work-loop's event line carries a version, so the format can change later
without breaking a reader that is already consuming it. Today every line in
`.loop-run/events.jsonl` is unversioned, which is tolerable only while the file
never leaves the machine. The moment anything exports it the cost of adding a
version rises sharply, because the readers are then outside this repository and
outside its release cadence.

This ships ahead of any exporter for exactly that reason. A consumer that starts
reading these lines finds a version already present rather than having one
appear underneath it.

Two facts make the change small. `telemetry.md` § 8 already guarantees that the
first seven fields keep their names, order and values so that adding a field
never breaks an existing reader — so the field is additive by construction. And
an absent version means version 1, which is what lets a line written by an older
engine replay unchanged instead of being stamped with a version it was not
written under.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the line becomes a versioned wire format with readers outside this repository | `contracts/jsonschema/loop-run-event.schema.json` + a row in `contracts/README.md` | spec owner | Schema validates a recorded corpus of real lines | Schema committed, registry row present |
| Current architecture | Applicable — § 5.1's field inventory states a count the new field changes | `docs/architecture/telemetry.md` § 5.1 | spec owner | Inventory matches what the engine emits | No count contradicts the emitted line |
| Release history | Applicable — a `packs/core` content change | `docs/product/changelog.md` | release workflow | Version bump with entry | Entry present, versions match |
| Reusable learning | Applicable — absent-means-v1 and the replay-passthrough trap generalise | `project-knowledge` public seam | work-loop closeout | Capture receipt | Receipt or `project-knowledge unavailable` |
| Decision rationale | Not applicable — the field is additive and § 8 already permits it, so no decision is reversed | — | — | — | — |

## Boundaries

### Always do

- Keep the first seven fields' names, order and values unchanged, per § 8.
- Treat an absent version as version 1, in every reader this repository owns.
- Keep recording graceful: a failure in the version path warns and the phase
  state is still written.

### Ask first

- Emitting any version other than 1.
- Changing the meaning of an existing field rather than adding one.
- Making the version a required field for any reader.

### Never do

- Stamp a version onto a record written by an earlier writer.
- Add a new module boundary inside `packs/core` for this.
- Make a transition fail because the version could not be written.

## Testing Strategy

- **VI-0001 — the writer stamps the version (AC-0001, AC-0002):** TDD, in the
  existing envelope suite at
  `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`. Both are
  functions over a written file, so the cases compress into assertions. The two
  criteria share a group because they are one predicate over the writer's two
  paths — the fresh transition and the outbox replay — and a single fixture
  exercises both.
- **VI-0002 — the contract schema is real and registered (AC-0003, AC-0004):**
  goal-based check. The schema is validated against a recorded corpus of lines
  the engine actually emitted rather than a synthesised one, so a shape the
  engine produces cannot pass by construction.
- **VI-0003 — the architecture states what is emitted (AC-0005):** goal-based
  check over the authored file. Mechanical: the stated count is compared against
  the emitted key count.

## Acceptance Criteria

- [ ] **AC-0001.** Every event line `loop-engine` appends to
  `.loop-run/events.jsonl` on a transition carries `schema` with integer value 1.
- [ ] **AC-0002.** An `events.pending` record that carries no `schema` key is
  appended to `events.jsonl` unchanged, still carrying no `schema` key.
- [ ] **AC-0003.** `contracts/jsonschema/loop-run-event.schema.json` validates
  every line of the recorded corpus at
  `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl`.
- [ ] **AC-0004.** `contracts/README.md`'s file table carries a row naming
  `contracts/jsonschema/loop-run-event.schema.json` and what it pins.
- [ ] **AC-0005.** `docs/architecture/telemetry.md` § 5.1 states a field count
  equal to the number of keys on a line the engine emits.

## Retired identifiers

<!-- Identity is append-only: a retired identifier is never reused. -->

None.

## Follow-ons

- spec owner: [`docs/specs/loop-telemetry-export/spec.md`](../loop-telemetry-export/spec.md)
  — the exporter that consumes these lines. It depends on this spec shipping
  first, and carries no criterion of its own for the version field.

## Assumptions

- Technical: adding a field breaks neither known reader — `test_loop_engine_events_jsonl.py:125` asserts a key superset, and `packages/agentbundle/agentbundle/workspace_mcp.py:304` polls by byte offset (source: both paths read 2026-09-12)
- Technical: the line is assembled as a dict literal in `_cmd_transition`, so field order is stable and the addition is one key (source: `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:1608-1623`)
- Technical: the outbox replays `events.pending` through `_append_events_jsonl` without re-deriving fields, which is why a versionless pending record passes through unchanged (source: `loop-engine.py:626`)
- Technical: `contracts/` is the authored source for repository-public contracts, with no CLI data copy required (source: `contracts/README.md` authority model)
- Process: a `packs/core` content change bumps `pack.toml` and `.claude-plugin/plugin.json` together (source: `packs/AGENTS.md` § Version bump rule)
- Product: this ships ahead of the exporter so a consumer never sees a version appear underneath it (source: user confirmation 2026-09-12)
