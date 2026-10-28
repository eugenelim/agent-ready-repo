# Spec: Intents and briefs stop being registered

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-27 by eugenelim, spec and plan; re-approved the same day after the pre-EXECUTE security review tightened the brief-file confinement, the repair's drop re-check, and the rename criteria; review records under `.context/reviews/intent-brief-registration-stop-spec-r1/` to `-r8/` and `.context/reviews/dc8372f0-018b-4a56-8fdf-a950dd1597ae/`. Re-approved 2026-10-28 by eugenelim after a controlled amendment during T3: the repair drops only intent entries under `docs/product/intents/` and brief entries under `docs/product/briefs/`, so every captured item keeps its entry; records under the same run directory, `6-amendment-*` and `7-amendment-*`. Re-approved 2026-10-28 by eugenelim after a second controlled amendment after T7: AC-0035 has the spec-status lint resolve a deferral anchor through an open intent or brief file; records `8-amendment-*` to `10-amendment-*`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, a type's registration stops in the release that ships the replacement for every responsibility its entries feed, and the contracts requiring it change in that release through their own errata or amendment; that amendment supersedes ADR-0119 D4 in part), RFC-0105 (D3, the behavioral-equivalence gate and accepted authority for a removal), RFC-0064 (its `receive-brief` and `author-brief` writer rows), RFC-0083 (§ 6 and § 8, intake registration and brief claim moves), ADR-0134 (D4, the rename's registry step), ADR-0110 (D2, D4, D7, and D9, cooled child scope resolved against a brief membership), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:depends-on-headers, spec:captured-item-registration-stop, spec:registry-comparison, spec:next-item-suggestions-removal
- **Contract:** none — the registry schema is published in the `workspace.toml` schema guide, and the criteria below change which entries a writer adds to it.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer or agent who creates, readies, renames, or closes a repo-origin intent or delivery brief edits that artifact and its citations and never adds, moves, or deletes a `workspace.toml` entry for it. Success is that this repository's registry holds no repo-origin intent or brief entry, that an adopter removes theirs with the `workspace-status` repair, and that every spec is blocked or dispatchable as before, apart from the removals and intended changes the retirement record names.

## What Changes

- A `workspace-status` repair step, `intent-brief-drop`, that removes every repo-origin intent and brief entry, run once on this repository. A legacy intent or brief entry is migrated as today and then removed by the next run. Its plan and apply live in `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, with `references/mutate.md` and SKILL.md describing it.
- The engine, `workspace_status_engine.py` and its packaged copy:
  - a cooled spec's declared `source.parent` that names a brief file attributes the child to that brief whether or not the brief has an entry;
  - a dependency on a brief that has no entry is refused when the brief breaks the child-state rule, as a registered one is today; a brief that never had an entry gains this check and the cooled-child attribution, two intended changes.
- `work-intake`'s router: the `start` and `remember` routes for a repo-origin intent or brief, and the repo-origin ready-brief route, return no membership and no registration — `scripts/intake_router.py` and four cases of the core routing eval matrix. Tracker-origin routes, and the tracker brief-intake matrices, are unchanged.
- The intent rename treats a `workspace.toml` entry path like any other citation: it renames an intent with or without an entry, and repoints whatever `workspace.toml` text names the old path — `scripts/intent_rename_request.py` and `scripts/intent_rename.py`.
- The instructions that add or move repo-origin intent and brief entries: `work-intake`, `intake-intent`, `author-delivery-brief` create and continue, `close-work`'s brief closeout, and the guides, architecture page, maintainer reference, and pack pages that repeat them. The `cooled_child_scope_unknown` definition in `workspace-status` SKILL.md and the schema guide.
- The spec-status lint's deferral-anchor check, `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` invariant (iv), also resolves an anchor naming an intent or brief file, through that file's non-terminal `Status:`, because a removed intent entry no longer carries it.
- Errata or amendments, each citing RFC-0106 D1: ADR-0119 (with `Superseded in part:` set), ADR-0134, ADR-0110, RFC-0064, RFC-0083, and RFC-0106 (three accepted removals, two intended changes, and the tracker-origin limit); dated owner amendments on FEAT-0001, FEAT-0005, and FEAT-0007.
- The slice-7 rows of `docs/specs/workspace-retirement/retirement-record.md` § Equivalence and the re-owned Disposition rows, admitted by a controlled amendment of the `workspace-retirement` spec; the inventory rows this stop disposes or re-owns; and the brief's slice 7 and slice 9 text, amended for the tracker-origin limit.
- Unchanged: tracker-origin intents and briefs, which keep their entries and writers because refresh binds the tracker profile through the entry alone; refresh; spec registration and every writer of spec entries; captured items; `close-work`'s spec moves and its dormant closure-packet registration field, which production never fills; the `place-bet`, `map-capabilities`, and `lean-canvas` suggestions, which only print text and never write `workspace.toml`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: which entries the registry holds, and the repair that removes the rest | Applicable: adopters' writers and the repair share the schema | `guides/core/reference/workspace-toml-schema.md`, `packs/core/.apm/skills/workspace-status/references/mutate.md`, and `packs/core/.apm/skills/workspace-status/SKILL.md` | Platform Core maintainer | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0023, and AC-0024 pass; the wording follows plan T3's and T5's design decisions and is checked in review | Each names the `intent-brief-drop` step and says new repo-origin intents and briefs get no entry |
| Decision rationale: the contracts that required registration | Applicable: RFC-0106 D1 requires each to change in the stop's release | ADR-0119, ADR-0134, ADR-0110, RFC-0064, RFC-0083, and RFC-0106, each § Errata; FEAT-0001, FEAT-0005, and FEAT-0007, each as a dated amendment | eugenelim, Decision-maker, Approver, and intent owner | AC-0025 and AC-0026 pass | Each entry carries owner-approved wording |
| Decision rationale: equivalence evidence and the authority for each removal | Applicable: RFC-0105 D3 gate 3 | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence | Platform Core maintainer; eugenelim as RFC-0106 Approver | AC-0027 and the amended `workspace-retirement` check pass | Each case AC-0027 lists has a row |
| Current product truth: which consumers still depend on the registry | Applicable: the stop changes what many inventory rows describe | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0028 and the inventory check pass | No row outside this spec's directory names slice 7 |
| User documentation: how to create, ready, rename, and close an intent or brief | Applicable: adopters do these by hand or through the skills | the guides and pack pages AC-0024 lists | Platform Core maintainer; the `github` and `linear` pack owners for their pages | AC-0024 passes; the rewritten paragraphs follow plan T5's design decisions and are checked in review | No listed page tells a reader to register or move a repo-origin intent or brief entry |
| Architecture and maintainer guidance | Applicable: both describe the brief lockstep | `docs/architecture/work-intake-and-artifact-routing.md` and `docs/guides/reference/work-intake-maintenance.md` | Platform Core maintainer | AC-0024 passes | Both say a repo-origin brief's lifecycle is its `Status:` alone |
| Verification record: the registry comparison before the stop, and the repair run | Applicable: FEAT-0034's validation hook | `docs/specs/intent-brief-registration-stop/notes/verification-ledger.md` | Platform Core maintainer | AC-0029 and AC-0031 pass | The ledger holds both runs and no failing row |
| Release history | Applicable: shipped content changes in `core`, and the site's `github` and `linear` pack pages change | a `docs/product/changelog.d/` fragment; `core`'s `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog and version gates pass | The fragment names the stop and the repair step |
| Delivery plan: the brief's slice 7 and slice 9 text | Applicable: the tracker-origin limit moves part of slice 7 to slice 9 | `docs/product/briefs/workspace-registry-retirement-delivery.md` § Delivery slices | eugenelim, brief owner, through `author-delivery-brief` | The amended slice text, approved by the owner | Slice 7 says repo-origin; slice 9 names ending tracker-origin registration |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Run `python3 tools/compare-registry.py --root .` on the implementing branch before any writer instruction or entry changes, and stop for the owner if it exits non-zero.
- Decide whether a declared parent is a brief file by the Brief file term alone, and never open a brief's body or a cooled file's body to decide it.
- Regenerate the packaged and projected copies with `make build-self`, bump `core`'s version, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits a file under `packages/agentbundle/`.

### Ask first

- The wording of each errata entry and intent amendment AC-0025 and AC-0026 list. The owner approves each before it is committed.
- Running `repair-apply` on this repository's `workspace.toml`. The owner sees the whole plan file first.
- The list of spec-result differences AC-0032 records. The owner approves it before closeout.
- The amended text of the brief's slices 7 and 9.
- Any change to a tracker-origin route, to refresh, or to a skill in the `atlassian`, `github`, or `linear` pack.

### Never do

- Remove, move, or rewrite any `workspace.toml` entry by hand, apart from adding and moving this spec's own entry and moving the parent brief's entry together with its `Status:` line before the repair runs. The repair alone removes intent and brief entries.
- Change spec registration, the `remember` route for a spec, or `close-work`'s spec moves, or change how a dependency on an intent or brief is settled beyond what AC-0007, AC-0010, AC-0011, and the retirement record's slice-7 rows name.
- Add a finding code, or change any `navigate-intents` file.
- Add a dependency, a skill, a module, or a top-level directory, or add any reader of the old `workspace.toml` shape outside the repair.

## Testing Strategy

- **The repair step (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006): TDD.** Each rule is a plan or apply result over a fixture `workspace.toml`, so one planted entry per case reds each test before the step exists.
- **Cooled child scope (AC-0007): TDD.** One planted cooled spec membership per case reds before the rule changes.
- **Cooled child scope kept unknown (AC-0008): goal-based.** Regression guards that pass at `ff33d0dcc` and must still pass.
- **Existing equivalence fixtures (AC-0009): goal-based.** The frozen fixtures and their suites run unchanged.
- **The child-state refusal (AC-0010): TDD.** A waiter on one planted brief per case reds before the rule changes.
- **Unregistered intents and findings (AC-0011, AC-0012): goal-based.** Regression guards that pass at `ff33d0dcc` and must still pass; AC-0011's expected settlement is computed once by the engine at that commit and captured as literals.
- **Router (AC-0013, AC-0014): TDD.** `route_intake` is a pure function, so each route reds against its expected membership and mutation.
- **Routing evals (AC-0015): goal-based.** The existing matrix comparisons run against the edited core matrix and the unchanged tracker matrices.
- **Rename (AC-0016, AC-0017, AC-0018, AC-0019, AC-0020): TDD.** Each reds on a fixture repository whose `workspace.toml` bytes and result code are compared.
- **Writer and guide text (AC-0021, AC-0022, AC-0023, AC-0024): goal-based.** A roster check over closed lists of files and phrases, each phrase present at `ff33d0dcc`.
- **The spec-status lint (AC-0035): TDD.** Each planted case whose result changes reds before the lint changes: an open intent file and an open brief file that resolve, and a file whose preamble is `Draft` and body `Fulfilled`. The cases whose result does not change are regression guards: an entry that resolves, and a symbolic link, a closed file in each terminal status, a tombstone, a file whose only `Status:` line follows a `## ` heading, and an anchor with nothing behind it, none of which resolve.
- **Governance (AC-0025, AC-0026): goal-based.** The same roster check reads each errata entry and amendment; the owner's approval of each wording is an Ask-first gate, recorded in the ledger.
- **Equivalence, inventory, and the ledger (AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0034): goal-based.** The amended `workspace-retirement` check and this spec's roster check run against this repository.
- **This repository (AC-0032): manual QA.** The two engines run over the head tree and every spec-result difference is listed with its cause; the owner judges the list, because no rule written ahead can say which differences on real data are acceptable.

## Acceptance Criteria

Terms used below. Canonical membership, cooled, and dependency item are as the [`depends-on-headers`](../depends-on-headers/spec.md) spec's Acceptance Criteria define them. A cooled child, a declared `source.parent`, and child scope are as [ADR-0110](../../adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md) defines them.

- **Repo-origin intent or brief entry.** A canonical membership whose `source.mode` is `repo-origin` and that is either `kind = "intent"` with a `path` under `docs/product/intents/`, or `kind = "brief"` with a `path` under `docs/product/briefs/`. An entry that points at a captured item is never one, whatever its `kind`.
- **Unregistered target.** An intent or brief path that no canonical membership names.
- **Brief file.** A declared `source.parent` value that, as the engine's provenance normalizer `_resolved_provenance_parent(value, require_local_brief=True)` at commit `ff33d0dcc` returns it, is byte-identical to `docs/product/briefs/` joined with the name of an entry of that directory as listed, where that entry is a regular file and not a symbolic link, and where `docs/product/briefs/`, `docs/product/`, and `docs/` are each a real directory, not a symbolic link, resolving beneath the resolved repository root; the root itself and the directories above it are not checked. Nothing is resolved through the filesystem to decide the match, and a directory that fails these conditions lists no brief file.
- **Brief child-state rule.** The rule `_brief_child_scope_is_valid` applies at commit `ff33d0dcc` between a brief's `brief_queue` collection and the observed states of its non-cooled child specs, with an unregistered brief's collection read as the `brief_queue` list named for its `Status:`.
- **Restored registry.** The head `workspace.toml` with exactly the entries the `repair-apply` run on this repository removed put back where they were.
- **Spec result.** For a spec membership: its `dispatchable` value, which of `canonical.ready`, `canonical.active`, and `canonical.blocked` holds its path, and the code and path of every finding in its own evaluation.

**The repair**

- [ ] **AC-0001.** `workspace-status repair-plan` holds one `intent-brief-drop` operation for each repo-origin intent or brief entry, cooled or not, naming its initiative key (empty for a top-level collection), its collection, its index in that collection, its `path`, and its `kind`.
- [ ] **AC-0002.** `repair-plan` holds no `intent-brief-drop` operation for a canonical membership whose `source.mode` is `tracker-origin`, or that is not a repo-origin intent or brief entry, such as a captured item's entry of `kind = "intent"` before or after the same run moves it.
- [ ] **AC-0003.** `repair-apply --yes` on that plan removes the entries of its applied `intent-brief-drop` operations in the same atomic `workspace.toml` write under the writer lock as its other applied operations. The parsed registry afterwards equals the parsed registry the same apply produces with its `intent-brief-drop` operations left out, with those entries removed; and every comment line outside a removed entry is kept.
- [ ] **AC-0004.** `repair-apply --yes` applies every `needs-to-header` and `needs-drop-cooled` operation in a plan before any `intent-brief-drop` operation, and refuses an `intent-brief-drop` operation, keeping its entry, when that entry still has a non-empty `needs` at that point, or when the registry read under the lock holds no entry at the planned initiative key, collection, and index with the planned `path` and `kind`, or holds one there that is not a repo-origin intent or brief entry.
- [ ] **AC-0005.** On a registry where every `needs-to-header` and `needs-drop-cooled` operation applies, one `repair-plan` and `repair-apply --yes` run leaves no repo-origin intent or brief entry, and a following `repair-plan` holds no `intent-brief-drop` operation.
- [ ] **AC-0006.** The legacy-migration repair's routes and selections are those it offers and accepts at commit `ff33d0dcc`.

**The engine**

- [ ] **AC-0007.** A cooled spec membership whose declared `source.parent` is a brief file that no brief membership names attributes the child to that brief: no `cooled_child_scope_unknown` finding names the entry; a `kind = "brief"` dependency on that brief, when the brief is not cooled and passes the dependency safety check, is refused with an `unsatisfied_dependency` finding whose path is that brief; and, in a repository where no other cooled spec membership has unknown scope, a `kind = "brief"` dependency on a different brief that no other cooled spec membership declares is not refused with the detail `brief child scope is unknown`.
- [ ] **AC-0008.** A cooled spec membership whose declared `source.parent` differs from a brief file's path only in letter case, names a symbolic link, or names a cooled path outside `docs/product/briefs/`, or names a listed brief while `docs/product/briefs/`, `docs/product/`, or `docs/` is a symbolic link, gives a `cooled_child_scope_unknown` finding naming the entry.
- [ ] **AC-0009.** These fixtures are byte-identical to their state at commit `ff33d0dcc`, and the suites that compare against them pass: `packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected.json`, `fixtures/depends-on-headers/expected-cooled-brief.json`, and `fixtures/captured-item-files/expected.json`.
- [ ] **AC-0010.** A dependency item that names an unregistered brief that is not cooled, breaks the brief child-state rule, and passes the dependency safety check is not satisfied, its waiter is not dispatchable, and the waiter's evaluation holds an `unsatisfied_dependency` finding whose path is that brief.
- [ ] **AC-0011.** A spec whose `Depends on:` names an unregistered intent whose own `Depends on:` names that spec gives no `dependency_cycle` finding, and its dependency on that intent is settled as the engine at commit `ff33d0dcc` settles a dependency on an unregistered intent.
- [ ] **AC-0012.** `workspace-status status` gives no finding naming an unregistered target, whatever its `Status:` and its own `Depends on:` line, apart from the dependency findings it gives to a waiter that names that path.

**The writers**

- [ ] **AC-0013.** For a signal whose `authority_mode` is `repo-origin`, `route_intake` returns `lifecycle_membership` `none`, a `mutation` that does not contain `register`, and the processor it returns at commit `ff33d0dcc`, for a `start` or `remember` action that carries no named gaps and whose `artifact_kind` is `intent` or `brief`, and for a ready-brief signal that `route_intake` sends to its ready-brief branch.
- [ ] **AC-0014.** `route_intake` returns the same `Route` as at commit `ff33d0dcc` for every other signal, including every signal whose `authority_mode` is `tracker-origin` and every signal for a spec.
- [ ] **AC-0015.** The `start-minimal-intent`, `remember-draft`, `remember-repo-origin`, and `ready-brief-zero-specs` cases of `packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json` expect the routes AC-0013 sets; every other case of that matrix, and every case of the `jira-brief-intake`, `jira-align-brief-intake`, `github-brief-intake`, and `linear-brief-intake` intake matrices, is byte-identical to its state at commit `ff33d0dcc`; and each matrix's comparison suite passes.
- [ ] **AC-0016.** The intent rename, given a source intent that no registry entry names, where neither the source path nor the successor path occurs in `workspace.toml` at the rename's base commit or when it is staged, does not refuse, and commits the tombstone, the successor, and every repointed citation, adding no registry entry.
- [ ] **AC-0017.** Such a rename writes nothing to `workspace.toml`. Once its request has passed the request checks it gives at commit `ff33d0dcc` (an unreadable or unparseable `workspace.toml`, more than one entry naming the source, an uncommitted change to a path it touches), its commit, recovery, and rollback make no decision from the live `workspace.toml`, whatever it holds when they run, apart from one check made before the rename's first file write: when `workspace.toml` then holds an occurrence of the source path or the successor path, the rename is refused with `registry-ambiguous` and writes nothing.
- [ ] **AC-0018.** A rename whose source intent no registry entry names, whose source path occurs in `workspace.toml` at its base commit, and whose successor path does not, gives the result a rename of a source with exactly one registry entry gives at commit `ff33d0dcc`: its commit repoints each occurrence of the source path in `workspace.toml`, and its rollback restores them.
- [ ] **AC-0019.** A rename whose source intent no registry entry names, and whose successor path occurs in `workspace.toml`, is refused with `registry-ambiguous`.
- [ ] **AC-0020.** A rename whose source intent has exactly one registry entry gives the result it gives at commit `ff33d0dcc`, and one whose source path is named by two or more registry entries is refused with `registry-ambiguous`.
- [ ] **AC-0021.** Read with each run of whitespace as one space, none of these files holds the phrase listed for it:
  - `packs/core/.apm/skills/author-delivery-brief/SKILL.md`: `Register one schema-valid Draft pointer`, `Move the complete structured brief entry`, or `Move an entry between the matching`;
  - `packs/core/.apm/skills/close-work/SKILL.md`: `moving its exact workspace entry`;
  - `packs/core/.apm/skills/work-intake/SKILL.md`: `Registering an intent, a brief, or a spec` or `intent path (registered)`;
  - `packs/core/.apm/skills/intake-intent/SKILL.md`: `register one non-dispatchable pointer`.
- [ ] **AC-0022.** Each file AC-0021 lists names `tracker-origin` and the `intent-brief-drop` repair.
- [ ] **AC-0023.** Read with each run of whitespace as one space, neither `packs/core/.apm/skills/workspace-status/SKILL.md` nor `guides/core/reference/workspace-toml-schema.md` holds `names no registered brief`.
- [ ] **AC-0024.** Read with each run of whitespace as one space, none of these files holds the phrase listed for it:
  - `guides/core/how-to/intake-an-external-brief.md`: `then registers the structured Draft entry`;
  - `guides/core/how-to/capture-work.md` and `guides/_shared/how-to/use-work-intake.md`: `Draft artifact, registers a`;
  - `guides/_shared/reference/work-intake-routing-and-lifecycle.md`: ``| brief | `brief_queue.draft` |`` or `registers it after the artifact exists`;
  - `guides/core/reference/work-intake-routing-and-lifecycle.md`: ``matching `brief_queue` collection`` or `Write and register a Draft, non-dispatchable artifact`;
  - `guides/core/tutorials/your-first-workspace.md`: `then registers a schema-valid`;
  - `guides/core/explanation/two-room-model.md`: `registers its lifecycle state`;
  - `guides/core/explanation/role-journeys.md`: ``a DoR-ready brief in `[brief_queue]`.``;
  - `guides/catalogue-curation/tutorials/your-first-skill.md`: ``Pulls confirmed slices from `[brief_queue]` ``;
  - `guides/product-engineering/how-to/hand-an-intent-to-build.md`: ``registers it in `workspace.toml`,``;
  - `guides/product-engineering/how-to/rename-an-intent.md`: `source-unregistered`;
  - `docs/architecture/work-intake-and-artifact-routing.md`: ``its `brief_queue` membership carry the same state`` or ``the artifact and `brief_queue` ``;
  - `docs/guides/reference/work-intake-maintenance.md`: ``its `brief_queue` collection identical``;
  - `web/src/content/packs/github.md`: ``when `receive-brief` registers the brief``;
  - `web/src/content/packs/linear.md`: `updated when the brief enters the queue`.

**The spec-status lint**

- [ ] **AC-0035.** `lint-spec-status.py` treats a `(deferred: <anchor>)` marker as resolved when `workspace.toml` `[backlog].open` resolves it as at commit `ff33d0dcc`, or when `docs/product/intents/<anchor>.md` or `docs/product/briefs/<anchor>.md` under the lint's `--root` is a regular file, not a symbolic link, whose preamble `- **Status:**` field, read as the lint reads a spec's status (HTML comments dropped, reading stopped at the first `## ` heading), has a leading word that is not terminal: for an intent, not `Fulfilled`, `Withdrawn`, `Cancelled`, or `Superseded`; for a brief, not `Shipped`, `Withdrawn`, or `Cancelled`. A file with no such field, such as a tombstone, does not resolve a marker. Any other marker gives an invariant (iv) hard violation naming the anchor.

**Governance and the retirement record**

- [ ] **AC-0025.** Each of these § Errata sections holds an entry dated on or after 2026-10-27 that links RFC-0106 and holds each literal listed for it:
  - `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`: `D4`; and the ADR's `- **Superseded in part:**` line holds `RFC-0106 D1`;
  - `docs/adr/0134-intent-rename-sealed-identity-bound-transaction.md`: `D4`, `Applies to`, and `lock`;
  - `docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md`: `D2`, `D4`, `D7`, and `D9`;
  - `docs/rfc/0064-ini-001-ai-native-ecosystem.md`: `[brief_queue]`, `receive-brief`, `author-brief`, and `M1`;
  - `docs/rfc/0083-work-intake-and-artifact-routing.md`: `§ 6`, `§ 8`, and `brief_queue.executing`;
  - `docs/rfc/0106-stop-registering-derivable-work.md`: `the unregistered intent or brief's own dependencies`, `the waiter's dependency cycle through an unregistered intent or brief`, `the entry-derived findings of an intent or brief target`, `the child-state check on a brief that never had an entry`, `the cooled child of a brief that never had an entry`, and `tracker-origin`.
- [ ] **AC-0026.** Each of these intents holds a paragraph that starts `**Amendment, ` with a date on or after 2026-10-27 and `eugenelim (owner)`, links RFC-0106, and holds each literal listed for it:
  - `docs/product/intents/FEAT-0001-intent-identity-and-registration.md`: `C3`;
  - `docs/product/intents/FEAT-0005-lifecycle-and-closure.md`: `Boundary`, `item 7`, and `brief`;
  - `docs/product/intents/FEAT-0007-work-item-promotion-routing.md`: `Opportunity` and `remember route`.
- [ ] **AC-0027.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one slice-7 row for each of these cases, its Case cell being the case's name, under the criteria the amended `workspace-retirement` spec states:
  - `the intent and brief entry removal`, as `reproduced`;
  - `the unregistered brief's child scope`, as `reproduced`;
  - `the brief child-state check`, as `reproduced`;
  - `the unregistered intent or brief's own dependencies`, as `accepted removal`;
  - `the waiter's dependency cycle through an unregistered intent or brief`, as `accepted removal`;
  - `the entry-derived findings of an intent or brief target`, as `accepted removal`;
  - `the child-state check on a brief that never had an entry`, as `intended change`;
  - `the cooled child of a brief that never had an entry`, as `intended change`;
  
  and each `accepted removal` or `intended change` row's Authority is an RFC-0106 § Errata entry naming its case.
- [ ] **AC-0034.** No row of `docs/specs/workspace-retirement/retirement-record.md` § Disposition carries Owner `7`.
- [ ] **AC-0028.** In `docs/specs/workspace-retirement/inventory.toml`, no row whose `pattern` lies outside `docs/specs/intent-brief-registration-stop/` carries `owner = 7`, and the inventory check passes.
- [ ] **AC-0029.** `docs/specs/intent-brief-registration-stop/notes/verification-ledger.md` holds one run of `python3 tools/compare-registry.py --root .` on this spec's branch before its first writer or registry change: the full default output, its exit code `0`, the commit it ran at, and that commit's merge base with `origin/main`.

**This repository**

- [ ] **AC-0030.** This repository's `workspace.toml` holds no repo-origin intent or brief entry.
- [ ] **AC-0031.** The ledger holds the `repair-plan` and `repair-apply` output that removed them, with the number of `intent-brief-drop` operations planned for intents and for briefs, and the number of entries the apply removed.
- [ ] **AC-0032.** The ledger holds a comparison of the engine at commit `ff33d0dcc` over the head tree with the restored registry against the head engine over the head tree: the restored registry's SHA-256, and every spec membership whose spec result differs between the two, each with its stated cause and the owner's recorded approval of the list.

## Follow-ons

- The brief's slice 8 stops spec registration, re-points the readiness bridge, and moves the spec-entry `source.parent` that ADR-0110's cooled child scope reads.
- The brief's slice 9 gives the tracker profile a home on the artifact (the retirement record's `source.tracker_profile` row), which ends tracker-origin intent and brief registration; and retires `close-work`'s dormant closure-packet registration field and the rest of the registry.

## Assumptions

none
