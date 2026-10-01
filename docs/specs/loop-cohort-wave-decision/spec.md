# Spec: loop-cohort wave decision

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0005 D1–D6; ADR-0061 D5; RFC-0015 Proposal decisions 1–3
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/loop-cohort-wave-decision.schema.json`
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects
> them in place as the work teaches, without an amendment and without a review
> round. A review finding against working material is advisory — it cannot block,
> because nothing gates the text it cites.

## Outcome

A work-loop controller can ask which unfinished tasks in one scheduled wave are
candidates for concurrent dispatch and read the reasons from one JSON result.
Success is that the screen can serialize work early but cannot authorize or
perform parallel writes.

## What Changes

- A read-only `loop-cohort wave-decision` verb and parser entry live in the existing work-loop cohort script.
- A versioned JSON Schema pins verdict and refusal envelopes under `contracts/jsonschema/`.
- Supervisor guidance explains the pre-dispatch screen separately from the post-write dispatch gate.
- Core pack evaluation and release records cover the new public primitive and its safety boundary.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — agents consume a versioned JSON verdict or refusal | `contracts/jsonschema/loop-cohort-wave-decision.schema.json`, this spec | this spec's implementer | schema validation of every emitted success and refusal fixture; bidirectional `x-spec` trace | the schema, CLI payloads, and final acceptance criteria agree |
| Current architecture | Applicable — § 4 records the Owner-approved delivery for this read-only verb | `docs/architecture/loop-parallelism.md` § 4 | this spec's implementer | § 4 names the approved delivery and no longer says the decision is untaken | the section keeps ADR-0005 D4 and ADR-0061 D5 unchanged |
| Maintainer and user procedure | Applicable — supervisors gain a public read-only verb | `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, `contracts/README.md` | this spec's implementer | the verb, its refusal channel, and the screen/gate boundary are findable from both surfaces | neither surface reuses `dispatch-decision` vocabulary or implies dispatch authority |
| Release history and user promise | Applicable — the core pack gains a primitive | scaffold source `packs/core/seeds/docs/product/changelog.md`, repository release history `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | this spec's implementer | one freshly derived core minor version and outcome-led release entries in both separately maintained changelogs | pack and plugin versions agree with the topmost core heading in both changelogs; the repository history and newly scaffolded repos expose the capability |
| Reusable learning | Applicable — `packs/AGENTS.md` requires an honest eval record | `packs/core/.apm/skills/work-loop/evals/evals.json` | this spec's implementer | an eval asks an agent to distinguish `parallel-capable` from the authoritative gate | the entry parses and is not counted as implementation verification |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read cohort state and `plan.md` through the exported guard-layer readers, validate identity before schedule currency, and leave cohort state byte-identical on every exit path.
- Report admission only on task rows, pairwise overlap only on pair rows, and `admission_pending: true` on every verdict envelope.
- Keep reason codes and refusal codes closed to the sets pinned by this spec and its JSON Schema.
- Refuse malformed state before verdict construction: `run_id` is a non-empty string, the selected unfinished wave has unique valid task IDs, and no more than 64 tasks proceed.
- Enforce the effective `Touches:` budgets owned by AC-0018 before overlap or pair construction; fold a breach into `plan-status-illegal` without adding a refusal code.
- Emit only the fixed public-safe message for each refusal code in JSON `detail`, capped at 96 characters; keep raw guard and exception diagnostics on the human stderr path only.
- Edit `.apm/` sources, then regenerate and verify the `.claude/` and `.agents/` projections.

### Ask first

- Changing a verdict field, a reason or refusal code, a code's required detail fields, or `payload_version` after approval.
- Changing `_DANGER_PATH_RE`; it is shared by the post-write classifier and this pre-dispatch screen.
- Letting any `wave-decision` output dispatch work, bypass a post-write check, assert a safe category, or otherwise influence ADR-0005's greenlight beyond selecting candidates for later admission.

### Never do

- Rename the verb to `dispatch-decision`, change `cmd_dispatch_decision`, or change that verb's parser.
- Emit `parallel` as a pre-dispatch verdict, put a disposition on a pair row, or omit `admission_pending` from a verdict.
- Build plan-width selection from `loop-parallelism.md` § 3, lift ADR-0061 D5, or enable concurrent execution.
- Add a module, runtime dependency, or second implementation of glob overlap or danger-path classification.

## Testing Strategy

- **V-001 — Verdict construction (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0016): TDD at pure-function and CLI surfaces.** Parameterized fixtures cover wave selection, completed-task subtraction, both `--force-sequential` forms, all five reason codes, accumulation, overlap short-circuiting, plan-order greediness, every disposition, and the exact pair-count formula through the 64-task limit.
- **V-002 — Refusal contract (AC-0007, AC-0008, AC-0012, AC-0015, AC-0017, AC-0018): TDD through the real CLI.** Every closed refusal code is reached with a distinct fixture; repository escape, a non-directory spec path, invalid and unreadable state, malformed success-envelope state, and each AC-0018 boundary exercise their folded codes. Each case is asserted for exit status, stdout/stderr channel, fixed public-safe JSON detail, and byte-identical state where a state file exists.
- **V-003 — Safety separation (AC-0009, AC-0010, AC-0018): TDD plus mutation proof.** Source-shape assertions pin `cmd_dispatch_decision` and its parser. Edited-source mutants prove the `run_id`, duplicate task-ID, per-task glob-count, per-wave glob-count, and glob-length guards are each reached and necessary before the original bytes are restored by editing.
- **V-004 — Published JSON contract (AC-0011, AC-0017, AC-0018): TDD against Draft 2020-12 JSON Schema from a repository-owned roster test.** Representative verdicts and all refusal envelopes validate; forbidden vocabulary, pair dispositions, invalid or overlong task IDs, AC-0018 violations, a one-member cohort, missing admission state, open-ended reason fields, unknown codes, and refusal details over 96 characters fail validation. Pack-local tests exercise CLI behavior without reading above `packs/core/`.
- **V-005 — Durable outputs and release integrity (AC-0012, AC-0013, AC-0014): goal-based checks plus manual CLI QA.** Content checks cover guidance, architecture, eval, versions, changelogs, and danger-path coupling; the built verb is invoked once on a real temporary cohort fixture and its observed JSON and exit code are recorded.

## Acceptance Criteria

- [x] **AC-0001.** `loop-cohort wave-decision <spec-dir> --json` exits 0 with one verdict envelope whose `schema_version` echoes cohort state; `payload_version` is `1`; and non-empty `run_id`, scheduled `plan_hash`, selected `wave_index`, `wave`, `wave_disposition`, `cohort`, `serialized`, `tasks`, `pairs`, and `admission_pending: true` agree with the selected unfinished wave.
- [x] **AC-0002.** With no `--wave`, the selected index is `current_wave_index`; an explicit non-negative `--wave <n>` selects that schedule entry; and the decided `wave` is `schedule_waves[wave_index]` in plan order with every `completed_task_ids` member removed.
- [x] **AC-0003.** A decided wave of width `n` emits exactly `n(n-1)/2` pair rows in plan-combination order; each row contains only its two task IDs and `touches_relation: disjoint|overlapping|unknown`, with no disposition or admission field.
- [x] **AC-0004.** The task reason vocabulary is exactly `touches-undeclared`, `danger-path-declared` with `glob`, `override-forced-sequential` with `source: cli`, `touches-overlap` with `with` and the two `globs`, and `no-admitted-peer`; every task row reports all applicable unary reasons.
- [x] **AC-0005.** Cohort selection walks tasks in plan order and admits a task only when it declares touches, names no danger path, is not forced sequential, and overlaps no task already admitted; the first admitted overlap short-circuits further overlap checks and names that peer, while a unary-refused but pairwise-disjoint task keeps `disjoint` pair rows.
- [x] **AC-0006.** A task that passes every other check but has no admitted peer is `sequential` with `no-admitted-peer`; `cohort` never has one member; width one yields `single-task`; and wider waves yield exactly `all-parallel-capable`, `all-sequential`, or `partially-parallel-capable` from the final task admissions.
- [x] **AC-0007.** The refusal vocabulary is exactly `unsupported-state-schema-version`, `state-unreadable`, `no-schedule`, `state-malformed`, `plan-missing`, `plan-status-illegal`, `plan-hash-stale`, `wave-index-out-of-range`, and `empty-wave`, with the precedence and folded conditions defined by `loop-parallelism.md` § 4 and this amendment: repository-confinement and state-read failures fold under `state-unreadable`; malformed success-envelope state folds under `state-malformed`; and an AC-0018 breach folds under `plan-status-illegal`.
- [x] **AC-0008.** Under `--json`, each refusal exits 1, writes one `{"payload_version": 1, "refusal": "<code>", "detail": "<fixed public-safe message for code>"}` object to stdout, and writes nothing to stderr; without `--json`, the same condition exits 1 through `stop()` with the richer guard diagnostic on stderr and writes nothing to stdout.
- [x] **AC-0009.** Verdicts use `parallel-capable` or `sequential` only; no output contains a pre-dispatch `parallel` disposition or safe-category claim; and neither success nor refusal invokes dispatch, worktree, merge-tree, or cohort-write behavior.
- [x] **AC-0010.** `cmd_dispatch_decision` and the existing `dispatch-decision` parser remain byte-identical to their pre-change forms, and no `wave-decision` call path reaches `dispatch_decision` or `wave_is_disjoint`.
- [x] **AC-0011.** `contracts/jsonschema/loop-cohort-wave-decision.schema.json` is a valid Draft 2020-12 schema with an `x-spec` back-pointer to this directory; it accepts every emitted verdict and refusal fixture and rejects unknown fields or codes, open-ended reason shapes, over-limit wave/task/pair/touch arrays, overlong globs, a pair-level disposition, a one-member `cohort`, a missing `admission_pending`, and any pre-dispatch `parallel` disposition. The schema mirrors AC-0018's per-value bounds and records its selected-wave aggregate as an extension annotation because Draft 2020-12 cannot sum lengths of nested arrays.
- [x] **AC-0012.** Cohort `state.json` is byte-identical before and after every exercised success and refusal path, including unsupported schema, invalid or unreadable state, malformed state fields, missing or illegal plans, stale hashes, out-of-range waves, empty remaining waves, and every `Touches:` resource-limit refusal.
- [x] **AC-0013.** Supervisor guidance documents `wave-decision`, keeps `dispatch-decision` unchanged, states that `_DANGER_PATH_RE` moves both consumers, and keeps ADR-0005 D4 as the sole file-disjointness greenlight; `loop-parallelism.md` § 4 records the Owner-approved delivery, resolves its D5 applicability question as outside parallel-wave orchestration, and does not lift ADR-0061 D5.
- [x] **AC-0014.** The core eval record, separately maintained pack-source changelog seed and repository product changelog, freshly derived minor version, and `.apm` source/projection parity all describe the new primitive. The pack and plugin versions equal the topmost core heading in each changelog. `make lint-ruff lint-mypy`, the targeted pack suite, the pack-boundary lint, repository-owned JSON Schema coverage, and `FORCE=1 make build-self` pass; a real built-verb smoke pass records passing exit status, stdout/stderr channels, and byte-identical cohort state. The repository-owned schema test is wired into CI but is not run locally because `tests/roster/` is dispatch-only for this delivery.
- [x] **AC-0015.** Before reading state or plan bytes, the verb uses `_resolve_spec_dir` to confine the resolved path to the current repository; absolute outside paths, `..`, and symlink or reparse-point escapes refuse as `state-unreadable`. Before verdict construction, `run_id` is a non-empty string and, after completed-task subtraction, every task ID is unique, matches `T[0-9]+[a-z]?` within 64 characters, and belongs to a wave of at most 64 tasks. A missing/empty `run_id`, duplicate ID, invalid/overlong ID, or 65 or more tasks refuses as `state-malformed` before any pair row is built. These controls preserve the JSON/human refusal channels and byte-identical cohort state.
- [x] **AC-0016.** `--force-sequential <task-id>` adds `override-forced-sequential` only to that named wave task, while bare `--force-sequential` adds it to every wave task; both forms preserve reason accumulation and produce the normal JSON or human verdict rather than a refusal.
- [x] **AC-0017.** Every JSON refusal uses the fixed public-safe `detail` assigned to its refusal code, never raw exception text, absolute paths, secrets, or caller-controlled prose; every such detail is non-empty and at most 96 characters, the JSON Schema enforces that bound, and the non-JSON `stop()` path retains the richer guard diagnostic on stderr.
- [x] **AC-0018.** For the selected unfinished wave, each task has at most 64 effective, de-duplicated `Touches:` globs, each effective glob is at most 256 characters, and their wave-wide sum is at most 256. A breach refuses as `plan-status-illegal` before danger-path, overlap, admission, or pair construction; the JSON Schema caps each emitted task touch array and every emitted glob string and records the aggregate limit as `x-max-total-touches: 256`.

## Follow-ons

- Owner of a future decision record: supersede RFC-0015's standalone-worktree safety premise; outside this delivery.
- Owner of a future decision record: supersede ADR-0005 D7 before binding a worktree layout constraint; outside this delivery.

## Assumptions

none
