# Plan: Capture a loop's leftover work as an actionable record

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` (version-bump rule; the
  portable-content rule forbidding repository-only paths in shipped packs; the
  self-hosting projection rule). `packs/core/AGENTS.md` (core-pack deltas).
  Analogous implementations: `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`
  is the precedent for a strict request validator paired with a JSON Schema in
  `contracts/jsonschema/`; its construction path is
  `packs/core/tests/skills/project-knowledge/test_contracts.py` and the roster
  suite `tests/roster/test_project_knowledge_capture_contract.py`. No named
  uncertainty is open: the store's write path was settled during PLAN by
  running it rather than reading it, giving two facts. the partition parse is version-blind, so no versioned partition is
  needed; and the same validator allowlists the kind directory, so a
  `work-item` partition is refused with `confinement` until it is widened. An
  earlier draft drew only the first and concluded no partition change was
  needed. T4 owns the widening.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/work-item-capture/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding
> for a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure.

## Approach

The change is a contract version bump with a new trust boundary attached, and
the order is forced by it. The schema and the version-selecting validator land
first, because every later task writes or reads records through them. The argv trust boundary lands next, because `AC-0046` binds the `work_item`
shape rules to the validator it builds and both tasks edit the same four
files — so T2 depends on T3 rather than running beside it. The kind-vocabulary sweep is
mechanical and touches the most files, so it lands after the validators that
give a `work-item` record meaning, not before. The close-time behavior — the
branch, the outcome list, the printed rationale, the 12-item cap — sits on top
and is the only part a person sees, so it is verified by exercising a real
close rather than by a unit gate. Documentation and the version bump close it.

The riskiest part is the kind-vocabulary sweep. Running the write path during
PLAN showed two layers refuse a `work-item` record and a third makes its
partition invisible, while three other literal sets holding the same three
values belong to different vocabularies and must not move. A partial sweep
leaves the store able to read the new kind and unable to write it; an
over-broad one admits a work item to the knowledge corpus it is defined as the
complement of.

## Constraints

- **`contract_version` is a `const` and `additionalProperties` is `false`.**
  Any new kind or field is a version bump, not an additive change. This is what
  makes v2 unavoidable and is the ground for spec § D8.
- **The kind enum is pinned at many sites, and T4's check is their only
  inventory.** A partial sweep leaves the store readable but unwritable for
  the new kind, which is why T4 is one task. The site list appears in prose here and in the
  spec, but T4's check is what governs: it parses the enum at every site and
  compares them, so it fails on a site the prose misses. Read the check, not
  the prose, when the two disagree — T4 edits every one of those lines, so a
  written-down inventory decays during the task that reads it.
- **The packaged mirror must stay byte-identical to the canonical contract.**
  `tools/catalogue/check_contract_parity.py` compares them and `make
  build-check` runs it, so a schema edit that does not copy through reds the
  PR. The mirror is a plain copy. The packaged inventory
  `public-contracts.txt` does list this contract, but it is keyed on filenames
  and this change adds no file, so it needs no regeneration; a future change
  adding a second `contracts/jsonschema/knowledge-*.schema.json` would.
- **`work-loop/SKILL.md` sits under CAT-S003's 1000-body-line error.**
  `skill_spec_lint.py` counts `body.splitlines()` after the frontmatter split,
  and emits `CAT-S003` as a *warning* above 500 lines as well, so the file
  already carries the code and only the error severity is actionable. No line
  count is recorded here: T6 edits this file, so any figure would be stale by
  the time the task it governs lands. T6 reads the count from the linter and
  keeps its delta small by putting detail in a reference.
- **`.agents/` and `.claude/` copies are projections.** Edit only
  `packs/core/.apm/`; `make build-self` regenerates the rest.
- **The store is append-only.** No task migrates, rewrites, or deletes a record.
- **No new store**, per CAP-0005. A refusal has no durable home.

## Construction tests

Per-task tests carry the acceptance criteria. Two cross-cutting obligations:

**Integration tests:** one replay over the real corpus — every record in
`docs/knowledge/observations/` read through the version-selecting validator,
partitioned on whether `request.contract_version` is present: the present
partition reads under the validator that field selects, the absent partition
reads through the `observation-event.v1` envelope without reaching version
selection, and every file's bytes are unchanged (`AC-0015`, `AC-0016`,
`AC-0017`). **The partition is the assertion and no record count appears
anywhere** — the store is append-only and this feature's own close writes into
it, so a literal count reds the replay for a reason unrelated to the contract.
This is the replay's only home. It spans T1's validator and T4's widened
enum, so **T4 schedules and owns it** — the later of the two, and the first
point at which it can pass. T1's `Tests` covers single-record cases only.
Describing a test here without an owning task is how `AC-0017` went
unscheduled in an earlier draft.

**Manual verification:** one real work-loop close that declines at least one
item of each shape, with its output recorded — the outcome list, the printed
rationale, and a refusal with its reason code. This is the spec's Visual /
manual QA mode and no unit gate substitutes for it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — the schema and its packaged mirror | T1, T2 | `AC-0015` to `AC-0018` green; the store replay; `check_contract_parity.py` exits zero | Each payload version validates its own records and the mirror is byte-identical |
| Current architecture — the record class and its tier state | T8 | The guide and architecture entry land | **The spec's Durable Outputs row is canonical**; discharge against it, not against this cell |
| Current architecture (security) — the single home for the gap list | T8 | `docs/architecture/security.md` updated | **The spec's Durable Outputs row is canonical**; discharge against it. It requires the full gap list, not a subset, and no count |
| Maintainer procedure — the close branch and the reasoning-tier dispatch | T6, T7 | `AC-0001`, `AC-0002`, `AC-0014`, `AC-0036`, `AC-0038` to `AC-0041`, **`AC-0068`** and **`AC-0069`** green. `AC-0068` is the delivery's only floor, so this cell is where a dropped fail-closed test stops being invisible | The branch reads without the spec. Tier *ordering* is `docs/specs/work-item-mechanical-tier/spec.md`'s — there is one tier until it lands |
| Current product truth — the adopter guide | T8 | A cold adopter writes a valid record | `docs/guides/reference/` names the three shapes |
| Release history — the version bump | T8 | The changelog entry leads the release | The bump is recorded |
| Decision rationale | T3, T5, T7 | The gate approval; `AC-0044`, `AC-0045`, and § D6 cases green | See the spec's Durable Outputs row, which is canonical for this role |

## Design (LLD)

### Design decisions
<!-- Traces to: AC-0003..AC-0009, AC-0018 · contracts/jsonschema/knowledge-captured-observation.schema.json -->
<!-- Owned by: T1, T2, T4. -->

**Version selection is a dispatch, not a migration.** A record names its own
`contract_version`; the reader looks the validator up by that value. Two
validators coexist and neither knows about the other. The alternative —
upcasting a v1 record to v2 on read — was rejected because it makes "no record
is rewritten" true only in the file and false in memory, and the spec's AC-0017
is about what the reader sees.

**Shape rules are a table, not a branch per shape.** Required fields per shape
live in one mapping that both the validator and the error message read, so a
shape added later cannot be validated in one place and unmentioned in the
other.

**The kind vocabulary widens at five sites and must not widen at four.**
Running the write path during PLAN, not reading it, established which is
which: the request validator and the partition allowlist each refuse a
`work-item` record, and the kind enumerator makes its partition invisible to
any caller that walks kinds. The topic and proposal synthesis kinds and the
legacy `patterns.jsonl` row kind in `knowledge_store.py`, and
`lint-knowledge.py`'s own `ALLOWED_KINDS` — a fourth, distinct set — hold the
same three values and are different vocabularies; § D1 defines a work item as generalisable practice's complement,
so admitting it there would contradict the contract. T4 carries both the sweep
and a negative control over the three that stay.

### Data & schema
<!-- Traces to: AC-0003..AC-0009, AC-0015..AC-0018 · contracts/jsonschema/knowledge-captured-observation.schema.json -->
<!-- Owned by: T1, T2, T3, T4. -->

`knowledge-captured-observation.v2` adds `work_item` (an object) and changes
`verification_route.command` from a string to a bounded argv array, the latter
under § D6. T3 owns that argv change. The `work_item` object gains **no path
field** for a mechanical tier: that tier is
`docs/specs/work-item-mechanical-tier/spec.md`'s, and this delivery ships
without it. It adds no `authorship` field: § D6 withdrew the authorship claim and routes attribution
to git history instead, so a field carrying no refusal and no criterion would
be permanent published surface whose later removal costs a v3. `lesson` moves from unconditionally required to required
only when `kind` is not `work-item`; `work_item` is required only when `kind`
is `work-item`. Both are `if`/`then` blocks, which the draft-2020-12 schema
already uses for the git-blob digest.

Storage partitions by kind directory, so `work-item` records land in
`docs/knowledge/observations/work-item/<YYYY-MM>.jsonl`. That directory is allowlisted by
`knowledge_store.py`'s `_validate_partition_name` and enumerated by its
kind-iteration loop, both of which T4 widens — cited by identifier because
T4 moves the offsets; the parse is version-blind, so no versioned partition is needed.
Both facts come from running the write path during PLAN, recorded in the
verification ledger — neither is open.

### Interfaces & contracts
<!-- Traces to: AC-0015..AC-0018, AC-0037 · contracts/jsonschema/knowledge-captured-observation.schema.json -->
<!-- Owned by: T1, T5. -->

The producer seam is unchanged in shape: a strict JSON request in, a capture id
or a diagnostic out. The diagnostic stays inside `SAFE_DIAGNOSTIC_FIELDS`, so
the codes § D4 adds carry no new field. Test seam for the crossed
boundary: the request validator is called directly with a constructed record,
never through the CLI, so a refusal is observed as a raised
`KnowledgeStoreError` with its reason code.

### Behavior & rules
<!-- Traces to: AC-0001, AC-0002, AC-0007, AC-0008, AC-0009, AC-0038, AC-0039, AC-0040 -->
<!-- Owned by: T2, T6, T7. -->

The close's outcome accounting is a set difference: the declined set minus the
set carrying an outcome must be empty, checked before the close reports
success. The one-correction rule is per item identity within a close, so the
close holds a small map from item to refusal count and refuses a second time
terminally.

### Failure, edge cases & resilience
<!-- Traces to: AC-0031, AC-0032, AC-0034, AC-0037, AC-0044, AC-0045 -->
<!-- Owned by: T2, T5, T7. -->

Tier ordering is `docs/specs/work-item-mechanical-tier/spec.md`'s: this
delivery ships the reasoning tier alone, so there is no ordering to settle
here and no mechanical floor beneath it. That spec's `AC-0003` and `AC-0004`
are the fail-closed controls, and they land with it.

### Quality attributes (NFRs)
<!-- Traces to: AC-0035, AC-0036, AC-0041, AC-0068, AC-0069 -->
<!-- Owned by: T3, T5, T7. -->

Security posture here is the privacy scan over the six free-text fields in
T5 and the instruction-shape refusal before dispatch. The argv boundary is T3's, under § D6. Cold-context isolation
(`AC-0041`) is observable: the validating context is given the record and the
committed tree only, and the test asserts the transcript path is not among its
inputs.

### Dependencies & integration
<!-- Traces to: AC-0015..AC-0017 -->
<!-- Owned by: T1, T4. -->

No new dependency. Everything lands in the standard library plus the existing
`jsonschema` surface the contract tests already use.

## Tasks

### T1: v2 schema exists and a record is validated by the version it names

**Depends on:** none

**Touches:** contracts/jsonschema/knowledge-captured-observation.schema.json, packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json, packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py, tests/roster/test_project_knowledge_capture_contract.py

<!-- Amendment 001 (notes/amendment-001.md) added knowledge_test_support.py:
     the non-writable-version refusal must bind at the write path, and that
     module's legacy fixtures are what the wiring reds. -->

**Tests:**
- `select_validator(..., require_writable=True)` refuses a non-writable
  version, and `validate_capture_request` stays **version-agnostic**
  (`AC-0048`, selector half). Do not make that function require-writable:
  `knowledge_store.py` calls it from the read path too, so requiring
  writability refuses every stored legacy record — see
  `notes/amendment-002.md`, where that regression was found against the real
  corpus. Binding the selector to the write path is **T4's**, which owns
  `knowledge_store.py`. Migrate `knowledge_test_support.py`'s fixtures to v2
  so the suite's default submission is the writable version.
- `tests/roster/test_project_knowledge_capture_contract.py` is green. It pins
  the schema's **top-level** `contract_version` — a second version site § D11
  names — and validates a fixture whose `verification_route.command` is a
  string carrying an option, which § D6 refuses; both move
  with the bump. The fixture's `command` stays a **string** here — T3
  migrates it to an array when it changes the type, so the conversion
  happens exactly once.
- A record carrying `request.contract_version = …v1` validates under the v1
  validator and is unchanged by it (`AC-0015`).
- A record carrying `…v2` validates under the v2 validator (`AC-0015`).
- A payload tagged `…v3` is refused with a catalog code and nothing is
  stored, and a payload tagged `…v1` submitted at the write path is refused
  rather than re-stamped (`AC-0047`, `AC-0048`). The version map has no
  default and no fallback, so both cases are driven at the selector directly.
- A payload written **through the writer** carries `…v2`; the assertion reads
  the emitted record, not a constructed one, so it fails if the writer still
  emits v1 (`AC-0018`).
- A record carrying no `request` object is read through the
  `observation-event.v1` envelope and never reaches capture version selection
  (`AC-0016`).
- A record carrying a `request` object with **no** `contract_version` is
  refused with a `REQUIRED_DIAGNOSTIC_CODES` code, not admitted as an
  envelope-only event (`AC-0062`). The schema made this fail by construction;
  moving selection into a map removed that, so the case is driven at the
  selector.
<!-- The store replay covering AC-0015..AC-0017 lives once, under
     `## Construction tests`; T1 owns only these single-record cases. -->
- Goal-based: `python3 tools/catalogue/check_contract_parity.py` exits zero
  after the mirror is copied.
- `stub: true` — `test_version_selection_dispatches_on_payload_field` asserting
  `select_validator({"request": {"contract_version": "knowledge-captured-observation.v1"}})`
  returns the v1 validator, and that a record with no `request` raises no
  selection error.

**Approach:**
- Copy the canonical schema to the `_data` mirror in the same commit as the
  schema edit; the parity gate is byte equality and `make build-check` runs it.
- **Version selection lives in the validator, not the schema document.** The
  contract file describes the writable version only, so its `const` becomes
  v2 and no second schema file is created — which is what keeps the packaged
  inventory unchanged. `project_knowledge.py` gains a version-to-validator
  map keyed on the record's own `request.contract_version`.

**Done when:** `python3 -m pytest packs/core/tests/skills/project-knowledge/test_contracts.py -q`
is green and the parity check exits zero. The corpus replay is the
cross-cutting test under `## Construction tests`, not this task's.

### T2: a `work_item` record is admitted only when its shape's fields are present

**Depends on:** T3 (`AC-0046` invokes the argv validator T3 builds, and both
tasks name the same four paths — a local edge is the only ordering the
scheduler reads)

**Touches:** contracts/jsonschema/knowledge-captured-observation.schema.json, packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json, packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py

**Tests:**
- For each of the three shapes, a record missing one required field is refused
  (`AC-0003`); a complete record of each shape is written (`AC-0004`).
- A `defect` with no `verification_route` but both `observed` and `intended`
  is written; a `question` and a `decision` with no `verification_route` are
  written (`AC-0005`, `AC-0006`).
- An absent `blocker` refuses with `work_item_incomplete`; an out-of-set
  `blocker` refuses with `work_item_not_blocked`. The two codes are asserted
  distinct (`AC-0007`, `AC-0008`).
- A `decision` with an empty `significance` is refused (`AC-0009`).
- A written record carries a non-empty `necessity_rationale` (`AC-0013`).
- A record carrying a `verification_route` is validated against § D6 at
  write time, and one whose command fails those rules is refused with the
  matching § D4 code (`AC-0046`). Driven for a `work-item`
  **and** for a non-`work-item` kind — a `gotcha` carrying
  `["bash", "-c", "…"]` — because the field is kind-agnostic and a validator
  wiring the rules into the `work-item` branch alone would pass a
  work-item-only test. The rules
  are invoked, not reimplemented — T3 owns them.
- The shape table is walked against every fixture case — a loop over the
  closed set, so a shape added later fails loudly rather than going
  unchecked.
- `stub: true` — `test_defect_missing_finished_state_is_refused`.

**Done when:** every shape's required-field case is red before the validator
lands and green after, and the two blocker refusals return different codes.

### T3: an argv that is not read-only is refused at write time

**Depends on:** T1

**Touches:** contracts/jsonschema/knowledge-captured-observation.schema.json, packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json, packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/argv_cases.py, tests/roster/test_project_knowledge_capture_contract.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py

**Tests:**
- `tests/roster/test_project_knowledge_capture_contract.py`'s
  `verification_route.command` fixture is migrated from the string form to an
  argv array, in this task, because this is the task that changes the type.
  T1 leaves it as a string; T1's bump does not invalidate it and this does.
- Every row of § D6 cases is a case, driven from
  `packs/core/tests/skills/project-knowledge/argv_cases.py`, which is
  **generated** by `notes/spike-argv-boundary.py` and not retyped from the
  spec table (`AC-0049`–`AC-0060`). A hand-transcribed fixture would be a
  control derived from the artifact it checks. The table is the derivation's
  own output; a row whose verdict changes is a contract change.
- An admitted argv is **written through the store and read back**, and the
  read-back list equals the submitted list element for element (`AC-0049`).
  The row-driven cases exercise a pure validator; only this one exercises the
  array serialization v2 introduces, so without it a dropped, reordered or
  coerced element ships untested.
- Every refusal path leaves the store's bytes unchanged, asserted
  differentially rather than by "no id returned".
- `argv_cases.py` is importable by another spec's suite, which is what the
  handoff spec's re-check criterion reads, and regenerating it from the spike
  produces no diff. This bullet carries no criterion.
- `verification_route.path` is refused for `.ssh/id_rsa`, `.env` and
  `.git/config` (`AC-0065`). The dot rule moves from the argv loop to the
  whole stored-path set § D6 defines: `_validate_verification_route` applies
  the component check to the value `_expect_repo_path` returns, which also
  catches the `"."` early return. All three pass `_expect_repo_path` today, so
  these cases are red before the change. **Take the narrow route, on both
  enforcement layers: apply the dot rule to the § D6 stored-path set only —
  leaving `_expect_repo_path` unchanged for its other callers, and leaving
  the schema's shared `$defs/repositoryPath` untouched.** Six fields `$ref`
  that definition, including `project_scope.paths` and
  `destination_hint.path`, which are the fields carrying the live dot values
  below; narrowing the shared pattern satisfies the Python half of this
  constraint and breaks the store just the same. The wide route is not available, and
  the live store is why — scanning `docs/knowledge/**/*.jsonl` finds **17
  distinct dot-containing `path` values across 41 occurrences** (for example
  `.claude/skills/work-loop/SKILL.md` and
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`) plus four
  dot-containing `scope` values, and `_expect_repo_path` has 20 call sites
  in `knowledge_store.py` including the committed-blob readers behind
  `read_confined_source`. Widening it in place would make already-stored
  records **unreadable**, not merely refuse new ones, and the cheapest exit
  from a store that no longer reads is to loosen the dot rule — destroying
  the control this task adds.
- `stub: true` — `test_element_beginning_with_dash_is_refused`.

**Done when:** every § D6 case row reproduces its recorded verdict, the
read-back assertion passes, `verification_route.path` refuses a
dot-leading component, and every refusal path leaves the store byte-equal.

### T4: every site pinning the kind vocabulary admits `work-item` together

**Depends on:** T2

**Touches:** packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py, contracts/jsonschema/knowledge-captured-observation.schema.json, packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py

<!-- Amendment 002 (notes/amendment-002.md) moved the write-path refusal here
     and added test_contracts.py: this is the only task that can reach both
     knowledge_store.py call sites and prove the split with the replay. -->

**Tests:**
- A `work-item` record round-trips: written through the capture path, then
  read back. Running the write path during PLAN showed the request validator
  refuses the kind first and the partition validator refuses the directory
  second, so both must widen before this passes.
- Goal-based, and the single home for the site inventory: a check over the
  **capture-kind** sites only — the two schema copies plus
  `project_knowledge.py`'s request validator, `knowledge_store.py`'s partition
  allowlist, and `knowledge_store.py`'s kind enumerator — asserting all five
  hold exactly the same four values. It fails if it finds fewer sites than on
  the previous run, so a site added later cannot be silently missed. A `grep`
  for the old three cannot decide this, because a site holding the old set and
  one holding the new set both match it.
- A negative control over the **four** sets the spec's `Never do` rail fixes,
  quantified over the same membership so the two cannot disagree: the topic
  synthesis kind, the proposal synthesis kind, `knowledge_store.py`'s legacy
  row kind, and `lint-knowledge.py`'s `ALLOWED_KINDS` — a separate set from
  the legacy row kind, not the same one. All four still hold exactly the old
  three values after the sweep. Widening
  them would admit `work-item` into the distillation corpus and
  `patterns.jsonl`, which § D1's complement argument forbids.
- **The write path refuses a non-writable version and the read path does
  not** (`AC-0048` with `AC-0015`). Wire `_check_pre_admission` to
  `select_validator(..., require_writable=True)` and leave `_validate_event`
  on the version-agnostic call. Both assertions in one task because one
  function served both sites and binding it in the wrong place refused every
  stored legacy record at read — the regression `notes/amendment-002.md`
  records. Drive a v1 submission through `capture_observation` (refused,
  catalog code, nothing written) and a stored v1 record through the replay
  (reads clean).
- The corpus replay under `## Construction tests` runs here, once both the
  validator and the enum are in place: every record read, partitioned on
  capture-payload presence, and **every file's bytes unchanged**
  (`AC-0015`, `AC-0016`, `AC-0017`). T4 is the first task at which it can
  pass, so T4 schedules it.
- `tests/roster/test_work_loop_lint_knowledge.py::test_schema_drift` passes.

**Approach:**
- **Four non-capture sets stay fixed.** `lint-knowledge.py`'s `ALLOWED_KINDS`
  is its own set, distinct from `knowledge_store.py`'s legacy row kind, and
  both serve `patterns.jsonl`; the two synthesis kinds are the other two. All
  four are generalisable practice — a work item's complement by § D1 — so
  touching any of them reds the negative control, and leaving them alone
  costs nothing, because no capture-kind site depends on them. The two
  `docs/knowledge/README.md` copies and the roster guard `test_schema_drift`
  describe the legacy vocabulary and are likewise untouched.

**Done when:** the five capture-kind sites agree on the same four values, all
four non-capture sets still hold the old three, a `work-item` record round
trips through the store, and the corpus replay passes with every file's bytes
unchanged.

### T5: a refusal returns a code from the closed catalog

**Depends on:** T4 (both edit `project_knowledge.py`; a local edge is the
only ordering the scheduler reads, so the same-module rail is carried by the
DAG rather than by prose)

**Touches:** packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py

**Tests:**
- Every code § D4's table adds is returned by the refusal that raises it,
  quantified over the table rather than a literal count so a code added there
  adds a case here (`AC-0037`).
- Every free-text field a `work-item` carries is passed to the scan,
  driven one field at a time with a known violating string, over the six
  fields `AC-0031` derives — the rule lives in that criterion and is not
  restated here (`AC-0031`). A separate assertion
  compares the scanned set to that derivation computed from the schema at
  test time; that comparison, not the loop, is what makes a field added
  later fail the suite.
- A record with no `lesson` is scanned without error (`AC-0032`).
- An induced privacy-scan failure returns a catalog code rather than an
  unhandled `KeyError` or `TypeError` (`AC-0034`).
- Every element of a stored command after `argv[0]` reaches
  `assert_persistable_text`, driven one element at a time with a violating
  string from the two scans' symmetric difference — a bare hostname, which the
  text scan refuses and the path scan admits (`AC-0061`). A secret-shaped
  string does not discriminate, because both scans carry `_SECRET_SHAPE`.
  Index 0 is covered by the four-member allowlist and is refused before the
  scan runs.
- `stub: true` — `test_work_item_statement_reaches_privacy_scan`, asserting
  `_deterministic_privacy_scan` raises on a `work_item.statement` carrying a
  known violating string.
- Every returned diagnostic's field set is within `SAFE_DIAGNOSTIC_FIELDS`.
- `REQUIRED_DIAGNOSTIC_CODES` contains every code § D4's table adds.

**Approach:**
- `_deterministic_privacy_scan` builds its `prose` and `paths` lists from
  literally named keys, so any field not enumerated there is never scanned.
  Two defects for this task: it reads `lesson` unconditionally, and it names
  none of the six `work_item` free-text fields. `AC-0061` — routing every
  command element to `assert_persistable_text` — is this task's; the argv
  rules those elements must satisfy are T3's. Skipping non-strings
  would silently stop scanning the command rather than fix it.

**Done when:** no refusal path in T2 or the privacy scan returns a code
outside the catalog or raises an uncaught exception, and removing any one field from the
scan's enumeration turns the suite red.

### T6: the close-time rule branches for specific blocked work

**Depends on:** T4

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/, packs/core/tests/skills/work-loop/

<!-- Amendment 004 (notes/amendment-004.md): T6 must prove its branch
     table matches the spec's and owned no test location to prove it in. -->

**Tests:**
- Goal-based: `skill_spec_lint` reports no **error-severity** body-length
  finding for `work-loop/SKILL.md` — that is, the body stays at or below 1000
  lines. The `CAT-S003` code itself is already emitted as a >500-line warning
  and is not the signal.
- The new reference's anchor resolves under
  `packs/core/tests/skills/work-loop/test_reference_routing.py`.
- The four-row branch table's rows are compared against § D9's table and
  asserted equal, so a SKILL.md branch that diverges from the spec fails.
  T6 carries no acceptance criterion of its own — it is a documentation task,
  and this test is what keeps its prose honest against the contract.

**Approach:**
- Measure the body line count from the linter before and after. The budget is
  the 1000-line error threshold as the linter reports it at edit time.
  Detail goes in the
  reference, so the SKILL.md delta stays a table and a pointer.

**Done when:** the linter reports no error-severity body-length finding and
the routing suite is green.

### T7: a close accounts for every declined item and fails closed when validation cannot run

**Depends on:** T5, T6

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/, packs/core/tests/skills/work-loop/, packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py, packs/core/tests/skills/project-knowledge/test_contracts.py, packs/core/tests/skills/project-knowledge/knowledge_test_support.py

**Tests:**
- A declined item with a suppressed outcome fails the close (`AC-0001`, `AC-0002`).
- The outcome vocabulary is exactly the three values, and the declined set is
  asserted to contain D9's rows two to four and not the generalisable-practice
  row (`AC-0001`, `AC-0002`).
- Each captured item's `necessity_rationale` appears in the close output
  (`AC-0014`).
- An item refused, corrected so its statement text changes, and re-submitted
  is matched by its declined-set ordinal and admitted; a second refusal ends
  the close (`AC-0038`, `AC-0039`).
- `stub: true` — `test_second_refusal_of_the_same_item_ends_the_close`.
- A close declining 13 items refuses before the first validation dispatch,
  asserted by a dispatch spy recording zero calls (`AC-0040`).
- The reasoning check's input set excludes the transcript path (`AC-0041`).
- Every input the reasoning dispatch can receive is enumerated and placed in
  exactly one bin — refused beforehand, or unscreened (`AC-0069`). **The
  domain is the dispatch's own parameter set**, not the record schema: the
  schema **document** is one source — walked, not a record instance, which
  drops unset optional fields — and `AC-0041` shows the dispatch also receives
  close-level context a schema walk cannot reach. **The schema-sourced part
  is derived by walking nested objects from the record root**, so
  `verification_route.command` is a member — a top-level walk, or a walk
  over a record instance rather than the schema document, yields
  `verification_route` opaque and misses it. Pin the minimum yield —
  including **at least one input the schema cannot supply**, or every pinned
  name is schema-sourced and the widened half has no failing case — so a
  partial or empty derivation fails. Adding a dispatch input without placing
  it must fail. Both bins are total by construction, so
  the domain's completeness is the whole check.
- An item whose prose matches the existing instruction-shape pattern is
  refused before any reasoning dispatch, driven one field at a time across
  the same six fields `AC-0031` derives (`AC-0035`). `significance` is not
  among them: it is a closed enum, so its case would pass with no
  instruction-shape scan at all.
- An item the razor refuses is not written and returns `work_item_unnecessary`;
  a `decision` whose declared grounds fail the § D1 three-ground test is not
  written and returns `work_item_threshold` (`AC-0044`, `AC-0045`). Both are
  the reasoning tier's calls, so both are driven through it rather than
  through the field validator.
<!-- Amendment 005 (notes/amendment-005.md) moved the three bullets above
     from T5: all three assert against the reasoning dispatch, which this
     task builds and T5 has no work-loop file to reach. -->
- The reasoning dispatch wraps item content in its data delimiter, and no item
  field is interpolated into instruction position (`AC-0036`).
- **The write path refuses any submission without a recognized verdict for
  that item** (`AC-0068`). The gate is in `project_knowledge.py` at the
  write, **not** in the skill prose that obtains the verdict: every existing
  test under `packs/core/tests/skills/work-loop/` is a source-text assertion
  over `SKILL.md`, and a source-text pin over a reference is the
  hand-written list `AC-0069` names as catching nothing. Put the refusal
  where a test can drive it, and every failure mode — unreachable endpoint,
  unconfigured tier, raise, expiry, an agent that never dispatched —
  collapses into "no verdict supplied" at one seam. Four cases: absent,
  outside the recognized set, item-identity mismatch (a count of verdicts
  cannot catch this; the binding is per-item correspondence), and a
  corrected re-submission under `AC-0038` reusing its pre-correction
  verdict. This is the delivery's only floor.
- Goal-based: `skill_spec_lint` reports no error-severity body-length finding
  for `work-loop/SKILL.md`. T6 and T7 both edit that file and share its
  headroom, so the task that could breach the 1000-line error carries the
  check too. Read the count from the linter at edit time.
- Manual QA: one real close declining at least one item of each shape, output
  recorded.

**Approach:**
- The new `work-loop` reference performs one dispatch: the per-item cold
reasoning check. There is no mechanical tier in this delivery — that is
`docs/specs/work-item-mechanical-tier/spec.md`'s — so there is no ordering to
hold here. What the reference must hold instead is the fail-closed rule: an
unavailable dispatch refuses, never admits.

**Done when:** the real close's recorded output shows one outcome per
declined item, a printed rationale per captured item, and a refusal with its
code.

### T8: the contract change is documented and released

**Depends on:** T7

**Touches:** docs/guides/reference/, docs/architecture/knowledge-capture.md, docs/architecture/security.md, packs/core/CHANGELOG.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, packs/core/.apm/skills/project-knowledge/evals/eval_queries.json

**Tests:**
- Goal-based: the guide names all three shapes and their thresholds.
- Goal-based: `docs/architecture/knowledge-capture.md` describes the
  `work-item` record class, its validation, and the unchecked merge path
  § D10 discloses. The entry describes a **single** reasoning tier and says
  the mechanical tier is not built, pointing at
  `docs/specs/work-item-mechanical-tier/spec.md`.
- Goal-based: `docs/architecture/security.md` describes the write-time argv
  rules and the complete gap list. **The spec's Durable Outputs security row
  is canonical for that list's membership, its classification and its
  ordering** — this bullet carries no enumeration, no ordinal and no count of
  its own, because a second copy here is what drifts. Read the row and
  discharge against it. One substantive note the row assumes: § D6's
  dot-component residual must be stated as reaching dot-leading names only,
  or the document reads as though the argv rules refuse credential-bearing
  paths as a class, which § D6 disclaims.
- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry
  matching bumped versions, per `packs/AGENTS.md`. One bump, one topmost
  changelog entry, for the whole delivery.
- The `project-knowledge` eval harness covers the new kind and at least one
  command refusal. `packs/AGENTS.md` requires a non-cosmetic pack update to
  update that pack's eval harness, and `project-knowledge` is in
  `pack.toml`'s `[pack.evals] skills` list.
- The changelog entry is the topmost release heading.
- `agentbundle catalogue self-host --check` is clean after `make build-self`.
- No false-or-already-fixed count is derived here. The spec withdrew it to the
  registered freshness owner, because both instruments that could produce it
  are closed to this delivery.

**Done when:** both documentation outcomes hold **against the spec's Durable
Outputs rows, which are canonical for them** — the architecture entry
describes the single delivered tier, and `docs/architecture/security.md`
carries the gap list the canonical row requires, in full and with no member
named here — `make lint-ruff lint-mypy` is green,
the projections are
regenerated, both version files carry the same bumped version, and the eval
harness covers the new kind.

## Rollout

- **Delivery:** big bang within the pack; no flag. Reversible in code — the v2
  validator can be withdrawn. **Irreversible:** any v2 record written before a
  withdrawal stays in the append-only store, so the v1 reader must keep
  tolerating an unknown kind directory. T4 covers that read path.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** schema and validator (T1) before anything that
  writes; vocabulary sweep (T4) before the close branch (T6) can emit a record;
  projections regenerated last (T8), because `make build-self` refuses a dirty
  tree.

## Risks

- **The sweep is partial, or too wide.** Five capture-kind sites must move
  together and four non-capture sets must stay fixed. T4's control parses the
  enum at every capture site and compares them, and a negative control asserts
  the four others are unchanged; a `grep` for the old values decides neither,
  because a stale site and a migrated one both match it.
- **`work-loop/SKILL.md` is close to the 1000-body-line error.** T6 can
  breach it late. Mitigated by measuring from the
  linter at edit time and by putting detail in a reference.
- **The 12-item cap is chosen, not observed.** No close has ever declined a
  work item, so the cap may be wrong in either direction. It is recorded as an
  open Assumption in the spec rather than presented as a measured bound.
- **The razor has no mechanical test.** `AC-0044` and `AC-0045` are the
  reasoning tier's calls, so their tests drive a real cold dispatch rather
  than a pure function, and a degraded tier makes them unfalsifiable. That is
  why the fail direction needs its own control — which is
  `docs/specs/work-item-mechanical-tier/spec.md`'s `AC-0004`, so this risk
  stays live until that spec lands.

## Changelog
