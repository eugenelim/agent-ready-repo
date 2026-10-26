# Plan: Dependency edges on the waiting item

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and D3; RFC-0105 D3; RFC-0103 D1; ADR-0103 D6; ADR-0074.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: `_parse_dependency`, `_dependency_is_satisfied`, `_dependency_cycles`, `_brief_child_spec_states`, `evaluate_dispatch`, `run_canonical_reconciliation`, `_parse_preamble_fields`, `_confined_artifact_path`, `canonical_result_identity`, and the legacy `classify_entries` family.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_build_repair_plan_json` and `_apply_operations`, the analogous plan-and-apply pair with a SHA-256 fingerprint and a `tomlkit` write.
  - `tests/roster/test_dependency_scoped_completion_receipts.py` and `tests/roster/test_cooling_scope_closure.py`: the receipt and cooled-dependency suites and their `tmp_path` fixture style.
  - `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py` `_depends_items`: the intent `Depends on:` reading rule this grammar matches.
  - `docs/specs/workspace-retirement/`: the record this slice amends.

## Approach

Freeze the old behavior first. Before any engine change, T1 writes each equivalence case as a typed `needs` fixture and records the unchanged engine's outcome as a committed expectation. Every later task proves itself against those expectations rather than against a reading of today's code. The reader and the switch come next, then the repair. The repair runs on this repository only after it passes on fixtures, and only on a plan the owner has confirmed. The riskiest part is the legacy view and the routing identity: both fold `needs` into outputs that other tools compare, so T3 checks them over the live repository before and after.

## Constraints

- Standard library only in the engine (ADR-0074). `tomlkit` stays inside `repair-apply`, under the Tier 1 declaration in `packs/core/AGENTS.md`.
- Every waiting-item and target read goes through `_confined_artifact_path`, and every brief target also through `_confined_briefs_path`. Every repair write goes through `confine_migration_path(..., require_file=True)` and the identity checks of `_migration_file_bytes`. `repair-plan` reads each waiting item through `_migration_file_bytes`, so a file apply would refuse to write is refused at plan time. Echoed values go through `_bounded_finding_identifier` and the AC-0028 grammars, one part at a time. The plan file itself is never redacted (AC-0031). `_public_needs` keeps serving only the legacy `needs` fields it serves today. A cooled membership's file is never opened.
- `make build-self` reprojects the engine, the prune, and `workspace_status.py` users into `packages/agentbundle/agentbundle/_data/`. The packaged copies are never hand-edited.
- An engine-source commit carries `Engine-Change-RFC: 0106`, as `tools/lint-catalogue-curation-guard.py` enforces.
- `core` takes one patch bump in `pack.toml` and `.claude-plugin/plugin.json` (`packs/AGENTS.md` § Version bump rule). The pack's eval harness under `packs/core/.apm/skills/workspace-status/evals/` gains a header-form case.
- Shipped pack text states its rules directly and cites no internal record (`packs/AGENTS.md`).

## Construction tests

- **Live comparison (T6):** `workspace-status status` is captured over the tree the repair reads and again after it. A scratch script compares the AC-0015 sets and records the comparison in `notes/verification-ledger.md`.
- **Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Header grammar surfaces | T5 | The `new-spec` contract reference, the spec template, and the schema guide name both fields | AC-0018's check passes |
| Adopter repair documentation | T4, T5 | `mutate.md` and `workspace-toml-deps.md` describe `needs-to-header` | The text names the command, its confirmation, and its comparison |
| Equivalence record | T7 | `retirement-record.md` § Equivalence rows | The amended `workspace-retirement` check passes |
| RFC-0106 errata entry | T7 | A dated entry signed by the Approver | The Equivalence row's link resolves |
| ADR superseding ADR-0103 D6 in part | T5 | An Accepted ADR with mirrored supersession fields | `lint-adr-shape.py docs/adr` passes |
| Contracts that name `needs` as the edge | T5 | Each owner-2 inventory row is disposed or re-owned | `test_workspace_retirement_inventory.py` passes |
| `close-work` receipt instruction | T5 | `close-work` SKILL.md text | AC-0018's check passes |
| Release history | T6 | A changelog fragment and the version bump | The changelog gate passes |
| Delivery membership | T6 | The Spec map row and the `workspace.toml` entry | `lint-brief-coverage.py` passes |

## Design (LLD)

### Design decisions

Owned by: T2, T3

- **The reader produces the existing `Dependency` value.** A typed or captured-item item becomes `Dependency(type="local", kind, path)`. A typed reference with no target keeps the path AC-0003 names, so `_dependency_metadata_safety_finding` reports `missing_dependency` and `_completion_receipt_satisfied` settles it exactly as for a pruned `needs` target. A captured item with no membership takes its `kind` from its own `Kind:` line, so a defect reaches the existing probe branch. A captured-item path with neither a file nor a membership keeps its path with no kind and reaches the same `missing_dependency` result. A completion receipt on any captured-item reference is refused, because without a kind a pruned defect could not be told apart. On an existing captured item the old receipt was never read, so only the pruned case drops a behavior, and that is the recorded removal. A completion receipt fills `receipt`. A coordination receipt makes the edge `type="cross-repo"`, with `kind` set to its `<remote_kind>` and with `path` and `containing_brief` both set to the brief's path, which is the shape `_cross_repo_receipt_satisfied` already requires. `_dependency_is_satisfied` and every receipt validator then run unchanged, which is what makes AC-0003 a comparison rather than a reimplementation.
- **Header edges replace `entry.needs` at one point.** `run_canonical_reconciliation` reads every non-cooled membership's header once into a per-path map. `evaluate_dispatch` and `_dependency_cycles` read that map. `_brief_child_spec_states` reads no edge and is unchanged. `WorkspaceEntry.needs` keeps the registry content, used only for the `unmigrated_needs` refusal.
- **One resolution index per run.** Brief slugs and live-intent `(kind, slug)` pairs are built once from confined listings of the two directories. A spec target is opened by its own path, so no spec listing exists to fail. A tombstone is left out, as `navigate-intents` leaves it out. A name matching more than one artifact gives `invalid_dependency`, under RFC-0103 D1, instead of a choice.
- **Receipts sit in a sibling field.** `Depends on:` stays a plain list of RFC-0103 references, so `navigate-intents` reads intent headers unchanged. `Dependency receipts:` keys each receipt by the same reference.
- **The cross-repo pin stays on the waiting item.** `<accepted_revision>` is carried in the coordination receipt line, and the engine still requires it to equal the receipt in the brief's body. The Disposition row `crossRepoNeed.accepted_revision` changes its Home to the waiting item's `Dependency receipts:` line.
- **The legacy view sees a header edge as it saw a typed `needs` edge.** `analyze` and `analyze_bounded` build the legacy lists from `extract_initiatives(workspace)` with `classify_entries` and `classify_shaping_entries`, apart from the canonical run. Today `_parse_needs` turns each typed edge into the string `unsupported-typed-need`, which never resolves. Both entry points read the same per-path header edges, through the same reader, and give each legacy entry whose path is a canonical membership that string once per header edge, so AC-0008 holds for work, shaping, `explain`, and the MCP tools. Making the legacy view resolve header edges would be a behavior change outside this slice.
- **The routing identity takes header edges.** `canonical_repository_identity` serializes `entry.needs` today. It serializes the per-path header edges in the same sorted shape, so an edited header changes the identity just as an edited `needs` array did.

### Data & schema

Owned by: T2, T4

```markdown
- **Status:** Approved
- **Depends on:** spec:payments-ledger, brief:partner-handover, capability:account-management
- **Dependency receipts:** spec:payments-ledger completion payments-ledger-2026 completed merge pr:812, brief:partner-handover coordination spec remote-prereq remote-rev-9
```

- The repair writes items in registry order: a typed reference for a spec, brief, or intent target, and a captured-item path for any other kind. It adds a field after the preamble's last `- **Field:**` line and its continuation lines. When a field is already there, it appends items to it.
- `workspace.toml` keeps `needs = []` on every migrated entry. The field stays required by `contracts/jsonschema/workspace-entry.schema.json`, which the repair reads its input through.

### Interfaces & contracts

Owned by: T4

- `repair-plan` adds operations of type `needs-to-header` to `automatic_operations`, each with `operation_type`, `waiting_path`, `waiting_sha256`, `registry_edges`, `depends_on_items`, and `receipt_items`. The plan ID and `workspace_fingerprint` cover them as they cover today's operations.
- A cooled membership gets an operation of type `needs-drop-cooled`, with `operation_type`, `waiting_path`, a `dropped_cooled` field holding its registry edges, and no `waiting_sha256`. Apply re-checks its cooled state under the lock (AC-0025).
- `_VALID_OPERATION_TYPES` admits both new types. Plan building, `_validate_plan_structure`, and `_apply_operations` dispatch on `operation_type`. Today's queue fields (`spec_path`, `ini_slug`, `spec_status`, `spec_status_fingerprint`) stay required only for `queue-to-shipped` and `queue-remove`.
- `repair-plan` loads the cooled set the way `status` does, for `needs-to-header` classification only. Its Type 2 analysis keeps `cooling_enabled=False`.
- When `canonical_failed` holds, `repair-plan` emits no operation and no manual finding (AC-0029), as `_build_repair_plan_json` already does.
- `repair-apply` returns `header_edges_before`, `registry_edges`, `dropped_cooled`, `header_edges_after`, and `edges_equal`. It exits 1 when `edges_equal` is false.

### Failure, edge cases & resilience

Owned by: T3, T4

- Apply order is the waiting files first, each by an atomic replace, then `workspace.toml` by one atomic replace. After an interruption, a migrated header still has its `needs` content, so `unmigrated_needs` keeps refusing it. A rerun skips items already present and clears `needs`. There is never a moment when an edge is in neither place.
- A waiting file that changed since the plan is refused by its SHA-256, and its entry keeps its `needs`.
- A captured-item file with no canonical membership takes its kind from its own `Kind:` line and reaches the existing probe. With no `Kind:` line it is `invalid_dependency`, so `kind` is never guessed.

## Tasks

### T1: Frozen expectations for every equivalence case

**Depends on:** none

**Mode:** TDD

**Tests:**
- Criteria: AC-0003, AC-0007, AC-0008.
- `packs/core/tests/skills/workspace-status/test_depends_on_headers_equivalence.py` builds one `tmp_path` repository per AC-0003 case, plus one cycle case, with the edge written as a typed `needs` entry.
- A recorder run, kept in the test file behind `--record-expectations`, writes `packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected.json`. That file holds, for each case, the reconciliation's finding codes and paths, `dispatch_by_path` dispatchability, and the legacy ready and blocked lists. It is recorded from the engine before T2 changes it, and committed in a commit of its own.
- Without the flag, the test asserts that the `needs` form still reproduces `expected.json`. That pins the recorder before the engine changes.

**Done when:** `expected.json` is committed from the unchanged engine, and the `needs`-form test passes.

### T2: The header reader

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0004, AC-0027, AC-0028.
- `test_depends_on_headers_reader.py` plants one case per rule. The cases cover:
  - a `none` line, an empty item, repeated lines, and a comment-hidden item;
  - a body-text decoy, and a fenced decoy;
  - a path in place of a spec reference, an ambiguous brief slug, and a kind-mismatched intent reference;
  - a captured-item path with no membership and no `Kind:` line, and one whose `Kind:` line is `defect`;
  - a backticked `Slug:` and `Level:` with a trailing comment, which resolve;
  - an indented continuation line under `Depends on:`;
  - a refused `docs/product/briefs/` listing, and a listed brief file that cannot be read, each giving `unreadable_artifact` for a `brief:` reference and never `missing_dependency`;
  - a valid `spec:`, `brief:<slug>`, and `intent:` reference and a captured-item path, each echoed verbatim;
  - a defect file under `docs/specs/<d>/notes/` named as a captured-item reference;
  - a free-text item, such as `the auth rework`, which gives `invalid_dependency` and not `missing_dependency`;
  - a completion receipt on a captured-item reference;
  - a tombstone and a live intent sharing a slug, where the reference resolves to the live intent alone;
  - a typed reference with no target, and a captured-item path with no file and no membership, each giving `missing_dependency` rather than `invalid_dependency`;
  - each AC-0004 receipt refusal;
  - a receipt value outside the token grammar.

  Each test asserts the one finding it expects, and no other.

**Done when:** each reader test reds before its rule exists and passes after.

### T3: Blocking moves to the header

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0003, AC-0005, AC-0006, AC-0007, AC-0008.
- `test_depends_on_headers_equivalence.py` adds the header form of every T1 case. Each asserts the T1 expectation's finding codes, dispatchability, and legacy lists, and its finding paths except where AC-0003 places a missing brief or intent target at the reference.
- T1's `needs`-form assertion becomes, for each case, an `unmigrated_needs` assertion; `expected.json` stays the frozen record of T1's cases.
- A cooled brief target case, which T1 does not hold, is added with its `needs`-form outcome recorded from the engine at commit `1f9c27342`, run from a `git worktree` of that commit, into the committed file `fixtures/depends-on-headers/expected-cooled-brief.json` beside `expected.json`, and its header form asserts that outcome.
- A shaping-backlog intent case and an `explain` and MCP `blocking_needs` case cover AC-0008 beyond the work lists.
- Editing a header item, a receipt, or a resolved target's `Slug:` changes `canonical_repository_identity`.
- `navigate-intents`' `_KNOWN_FINDINGS` in `intent_readiness.py` gains `invalid_dependency` and `unmigrated_needs` with the engine's sentences, and `test_readiness_vocabulary_matches_workspace_status` passes.
- An `unmigrated_needs` case pairs a satisfied `needs` edge with an empty header, and asserts the refusal and its next action.
- The cooled-waiting-item case makes the waiting file unreadable, and asserts that no `unreadable_artifact` finding and no read occurs.
- The existing suites under `packs/core/tests/skills/workspace-status/`, `tools/test_workspace_status.py`, and the roster suites listed in the anchors are migrated where they plant typed `needs` as dependency evidence. Each kept assertion moves to the header form. An assertion that pins the old reading of `needs` is replaced by an `unmigrated_needs` assertion.
- The eval fixtures that carry typed `needs` move to headers: `packs/core/.apm/skills/workspace-status/evals/files/cooled-child-scope-unknown/`, `.../invalid-completion-receipt/`, and `packs/core/.apm/skills/close-work/evals/files/completion-receipt/`. The legacy string edge in `workspace-status/evals/files/workspace.toml` stays, under the `entry.needs (string form)` follow-on. The skills' eval suites pass.

**Done when:** the equivalence suite and every migrated suite pass.

### T4: The `needs-to-header` repair

**Depends on:** T3

**Mode:** TDD

**Tests:**
- Criteria: AC-0009, AC-0010, AC-0011, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0028, AC-0029, AC-0030, AC-0031.
- `test_depends_on_headers_repair.py` runs `repair-plan` and `repair-apply` over fixture repositories. It asserts:
  - the operation fields, and that `repair-plan` leaves every fixture byte unchanged outside its plan file;
  - a plan holding a Type 2 queue operation, a `needs-to-header` operation, and a `needs-drop-cooled` operation, built, validated, and applied by type;
  - a symlinked waiting item and a multi-linked one, each refused at plan time with a manual finding;
  - a `canonical_failed` workspace holding an edge AC-0020 would refuse, which yields no operation of any type and no manual finding, only the cause;
  - one AC-0020 refusal case each: an intent target whose preamble has a `Tombstone:` field, an intent with no `Slug:`, a kind mismatch, and a cross-repo edge whose `path` differs from its `containing_brief`;
  - the manual findings for each unexpressible edge;
  - a cooled waiting item made unreadable, whose operation clears `needs` and lists `dropped_cooled` without a read;
  - a waiting item whose `Depends on:` already names a reference the registry also holds, which is not added twice;
  - a byte comparison of `workspace.toml` outside the changed `needs` arrays, and of each waiting file outside the added lines;
  - a refusal after a waiting file changes;
  - a registry edge whose path holds a comma or a space, refused at plan time;
  - a `needs-drop-cooled` operation whose lifecycle record is removed between plan and apply, refused with `needs` kept;
  - a plan edited to point an operation at `AGENTS.md`, or to change its items, with `plan_id` recomputed, refused; and a waiting file replaced by a symlink, refused;
  - an oversized item and an item with a control character, each echoed without its content while the rest of its edge still appears;
  - one edge whose waiting item is a spec, verbatim in `header_edges_before`, `registry_edges`, and `header_edges_after`, and one cooled edge verbatim in `dropped_cooled`;
  - a valid coordination receipt longer than 200 characters, carried whole in the plan file and migrated;
  - an interrupted apply (a failure injected after the first waiting file), followed by a clean rerun with no duplicate item;
  - `edges_equal` false when a reader-refused item is planted by hand.

**Done when:** the repair tests pass.

### T5: Instructions, contracts, and errata text

**Depends on:** T3

**Mode:** goal-based

**Tests:**
- Criteria: AC-0016, AC-0018.
- `tests/roster/test_depends_on_headers_instructions.py` applies AC-0016's pattern for a non-empty `needs =` array, with `mutate.md` exempt by exact path, and AC-0018's closed list of files and phrases.
- The `workspace-status` SKILL.md needs-resolution text is reconciled, and the anchor hash in `tools/test_workspace_status.py` is updated in the same commit.
- Draft, with the `new-adr` skill, the ADR that supersedes ADR-0103 D6 in part, and its mirrored `Superseded in part` field on ADR-0103. Ask the Approver to sign its wording and accept it (spec Ask-first). Then run `lint-adr-shape.py docs/adr`.
- Every inventory row with owner 2 is disposed or re-owned. A file whose last registry mention goes has its row removed, and a file still stating a later slice's registry fact moves to that slice. `test_workspace_retirement_inventory.py` passes.

**Done when:** the instruction roster test, the anchor test, `lint-adr-shape.py`, and the inventory test pass, and the new ADR is Accepted with the Approver's sign-off.

### T6: The migration of this repository

**Depends on:** T4, T5

**Mode:** goal-based

**Tests:**
- Criteria: AC-0012, AC-0013, AC-0015, AC-0017.
- Normalize the four Shipped specs' `Depends on:` lines by hand first, so the plan's SHA-256 values cover the normalized files.
- Capture `status` over that tree with the engine at commit `1f9c27342`, run from a `git worktree` of that commit under `.context/`, so its sibling `close-work` and `work-intake` modules are the same commit's. Record the commit and the worktree path in the ledger. Run `repair-plan`, and ask the owner to confirm the exact plan (spec Ask-first). Then run `repair-apply`, and record its edge sets and `edges_equal` in `notes/verification-ledger.md`.
- Compare the AC-0015 sets, and run `navigate-intents query --operation dependencies` over every migrated intent.
- `make build-self`, the `core` version bump, and the changelog fragment. This spec's `workspace.toml` entry and Spec map row are added when the spec is approved, before any capture, so both trees hold them. `lint-brief-coverage.py` passes.

**Done when:** `edges_equal` is true for every edge the repair read, the AC-0015 comparison passes, and the ledger records both.

### T7: The equivalence record and the retirement amendment

**Depends on:** T6

**Mode:** goal-based

**Tests:**
- Criteria: AC-0014.
- Amend `docs/specs/workspace-retirement/spec.md` and `plan.md` through the work-loop controlled-amendment path. Add criteria for § Equivalence: a table with columns Case, Slice, Result, Evidence, and Authority; Result is `reproduced` or `accepted removal`; Evidence names a path `git ls-files` lists; and an `accepted removal` row's Authority meets AC-0014's and AC-0015's link rules with Case text in place of Fact text. Extend `test_workspace_retirement_inventory.py` to enforce them, with one planted-violation fixture per rule.
- Draft the RFC-0106 errata entry for the cooled waiting item, the pruned captured item settled by a completion receipt, and the cooled target named by an unreadable slug (a cooled intent, or a cooled brief whose `Slug:` differs from its file stem), and ask the Approver to sign its wording (spec Ask-first).
- Write the eleven Equivalence rows. Correct the nine Disposition Home cells the spec's Ask-first names (four `crossRepoNeed.*`, five `localNeed.receipt*`), to the waiting item's `Depends on:` and `Dependency receipts:` lines.

**Done when:** the amended check passes against this repository, and the errata entry carries the Approver's sign-off.

## Rollout

- **Delivery:** one pull request. The reader, the refusal, the repair, and this repository's migration ship together, so the repository never has a `needs` edge that blocks nothing.
- **Adopters:** after upgrading `core`, an adopter's typed `needs` entries are refused, and the refusal names `repair-plan`. One confirmed `repair-apply` moves them.
- **Reversal:** revert the pull request. The migration is a tracked-file edit, so the revert restores the registry edges and removes the headers together.

## Risks

- **The suites that plant `needs` are large.** The survey counts about 290 `needs` assertions across five suites. T3 migrates them, and the diff is wide but mechanical. If T3 runs past one review unit, split it by suite, each split leaving the suite green.
- **Fingerprints move.** Every migrated entry's routing identity changes once. A stale `repair-plan` file or a cached identity from before the merge is refused by its fingerprint, which is the intended fail-closed result.
- **The anchor hash in `tools/test_workspace_status.py` pins `workspace-status` SKILL.md §1 to §5.** The needs-resolution text sits in that window, so T5 updates the hash in the same commit as the text.

## Changelog

- 2026-10-25: spec approved by eugenelim
- 2026-10-25: plan approved by eugenelim
- 2026-10-25: spec amendment approved by eugenelim (amendment 1: navigate-intents finding-table copy; cooled target named by an unreadable slug)
- 2026-10-25: plan amendment approved by eugenelim (T3 and T7 tests extended for amendment 1)
