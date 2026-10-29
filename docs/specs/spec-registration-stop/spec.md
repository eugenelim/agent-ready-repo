# Spec: Specs stop being registered

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, spec registration stops in the release that ships header-derived dispatch, the `unregistered_work` refusal is retired, and the contracts requiring registration change in that release; D3, several ready specs are listed and the user is asked), RFC-0105 (D3, the behavioral-equivalence gate), RFC-0064 (D4 and its `work-loop` writer rows), ADR-0110 (a cooled child's parent scope is declared, and an undeclared one fails closed), ADR-0076 (dispatch starts from specs), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:header-derived-dispatch
- **Contract:** none — `dispatch.py`'s output is skill-internal JSON read in `core` only, and the registry schema is published in the `workspace.toml` schema guide, whose text the criteria below change.
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
> gates the text it cites.

## Outcome

A maintainer or agent who writes, starts, resumes, or ships a repo-origin spec edits the spec and never adds, moves, or removes a `workspace.toml` entry for it, and `work-loop` decides what to start or resume from `dispatch.py`, listing several ready specs and asking. Success is that this repository's registry holds no registered repo-origin spec, that `dispatch.py` gives the same output before and after the repair that removed them, and that an adopter removes theirs with the same repair, apart from a cooled spec whose entry declares a parent its record lacks, and an entry whose `needs` the repair cannot migrate, each of which the plan names.

## What Changes

- **Dispatch.** `work-loop`'s Step 0 ORIENT runs `scripts/dispatch.py`, with or without `workspace.toml`, and acts on its `decision`, in place of `workspace-status`'s `canonical.ready` and `canonical.active` and the first-ready selection — `packs/core/.apm/skills/work-loop/SKILL.md` and its evals.
- **`unregistered_work` removed** from `workspace_status.py`'s `_canonical_explain`, the engine's finding table and its packaged copy, the `workspace-status` SKILL.md and schema-guide tables, and the readiness bridge's pinned copy. `cooled_child_scope_unknown`'s next action, and the `workspace-status` eval that grades it, name the lifecycle record's `parent`.
- **Readiness bridge.** Re-pointed to `dispatch.py`'s output by the `docs/specs/readiness-bridge-dispatch-input/` spec, which ships in the same release; this spec changes only the bridge's pinned finding table.
- **Writers.** `work-intake`'s router returns no membership for a repo-origin spec's start or remember route; the `workspace-status` repair plans `queue-to-shipped` and `queue-remove` only for an entry that is not a drop candidate; `work-intake`, `new-spec`, `new-rfc` (in `repo-governance`), the deferral guidance, and the guides stop telling anyone to register or move a repo-origin spec.
- **Repair.** A `workspace-status` step, `spec-entry-drop`, removes each repo-origin spec entry. It holds a cooled spec's entry, naming the `parent` value to add to its lifecycle record, while that record lacks a parent the entry declares. It never writes a lifecycle record. The Type 1 audit, which reports a live spec with no entry, reports nothing. Run once on this repository.
- **Spec-status lint.** A `(deferred: <anchor>)` marker also resolves through an open `docs/specs/<anchor>/spec.md`.
- **Governance.** § Errata on RFC-0064, RFC-0106, ADR-0076 and ADR-0110; dated owner amendments on FEAT-0005 and FEAT-0007; the `docs/product/AGENTS.md` coverage sentence; the `agent-skill-engineering` brief's registration steps.
- **Records.** The retirement record's slice-8 rows, the inventory's owner-8 rows, the brief's Spec map, and this spec's ledger.
- **Unchanged:**
  - `dispatch.py`'s output and decision rules;
  - tracker-origin spec entries, and every route, writer and repair step that keeps them;
  - the legacy-migration repair, which still writes a canonical entry for a legacy spec entry, and the next run drops it;
  - refresh; captured items, intents and briefs;
  - `close-work`, whose cooling guidance already names the record's `parent`;
  - the `atlassian`, `github` and `linear` packs; every Shipped spec's body.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: how `work-loop` dispatches | Applicable: every adopter's argless start and resume changes | `packs/core/.apm/skills/work-loop/SKILL.md` Step 0 and its evals | Platform Core maintainer | AC-0001 and AC-0002 pass | Step 0 names `dispatch.py` and each decision action |
| Interface compatibility: which spec entries the registry holds, and the repair that removes the rest | Applicable: adopters' writers and the repair share the schema | `guides/core/reference/workspace-toml-schema.md`, `packs/core/.apm/skills/workspace-status/references/mutate.md`, and `packs/core/.apm/skills/workspace-status/SKILL.md` | Platform Core maintainer | AC-0012 to AC-0021 and AC-0023 pass | Each names `spec-entry-drop` and says a repo-origin spec gets no entry |
| Decision rationale: the contracts that required registration | Applicable: RFC-0106 D1 requires each to change in the stop's release | RFC-0064, RFC-0106, ADR-0076 and ADR-0110, each § Errata; FEAT-0005 and FEAT-0007 amendments; `docs/product/AGENTS.md`; the `agent-skill-engineering` brief | eugenelim, Decision-maker, Approver, and owner | AC-0027 to AC-0031 pass | Each carries owner-approved wording |
| Decision rationale: equivalence evidence and authority | Applicable: RFC-0105 D3 gate 3 | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence and § Disposition | Platform Core maintainer; eugenelim as RFC-0106 Approver | AC-0032 and AC-0033 pass | Each case has a row; no owner-8 row is left open |
| Current product truth: which consumers still depend on the registry | Applicable: the stop changes what the owner-8 inventory rows describe | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0034 passes | No row names slice 8 apart from those left to the bridge spec |
| User documentation: how a spec is started, remembered, cooled and shipped | Applicable: adopters follow the guides by hand | the guides AC-0026 lists | Platform Core maintainer | AC-0026 passes; the rewritten paragraphs are checked in review | No listed page tells a reader to register or move a repo-origin spec |
| Verification record: comparison, replay, repair, dispatch before and after, and approvals | Applicable: FEAT-0034's validation hook | `docs/specs/spec-registration-stop/notes/verification-ledger.md` | Platform Core maintainer | AC-0031 and AC-0035 to AC-0038 pass | The ledger holds each run, each approval, and no failing row |
| Release history | Applicable: `core` and `repo-governance` content changes | a `docs/product/changelog.d/` fragment; each pack's `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog and version gates pass | The fragment names the stop, the repair step, and the list-and-ask start |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Run `python3 tools/compare-registry.py --root .` and `tools/replay-dispatch.py` over a `git worktree` of the branch's merge base with `origin/main` before any writer instruction, router branch, repair step, or registry entry other than this spec's own changes, and stop for the owner if the comparison exits non-zero or the replay shows a difference no accepted authority names.
- Decide a cooled entry's parent from the raw `source.parent` key and the engine's provenance normalizer and brief-file rule, telling an absent key apart from a declared `none` or empty value, and never open a cooled spec's body.
- Regenerate the packaged and projected copies with `make build-self`, bump `core` and `repo-governance` once each, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits a file under `packages/agentbundle/`.

### Ask first

- The wording of each errata entry, amendment and rewritten sentence AC-0027 to AC-0030 list, and the new `cooled_child_scope_unknown` next action. The owner approves each before it is committed.
- Running `repair-apply` on this repository's `workspace.toml`. The owner sees the whole plan file first.
- Any change to a `navigate-intents` file other than the readiness bridge's pinned finding table; the bridge's re-point belongs to its own spec.
- Any change to a tracker-origin route, to refresh, to a tracker-origin entry, or to a skill in the `atlassian`, `github`, or `linear` pack.

### Never do

- Remove, move, or rewrite any `workspace.toml` entry by hand, apart from adding and moving this spec's own entry and moving the parent brief's entry with its `Status:` line before the repair runs. The repair alone removes spec entries.
- Write, or give `workspace-status` a way to write, a lifecycle record; change `cooling.py` or `close-work`'s authority checks.
- Change `dispatch.py`'s output or decision rules, the engine's readiness rules, or a frozen replay fixture.
- Edit the body of a Shipped spec, or add a finding code.
- Add a dependency, a skill, a module, or a top-level directory, or add any reader of the old `workspace.toml` shape outside the repair and `dispatch.py`'s kept entries.

## Testing Strategy

- **Dispatch instructions and evals (AC-0001, AC-0002, AC-0043): goal-based.** A roster check over the SKILL.md text and the eval file's cases by id; the decision itself is `dispatch.py`'s, already proven by its replay, and the eval cases are graded by a model outside any gate.
- **`unregistered_work`, the cooled-child next action and the Type 1 audit (AC-0003, AC-0004, AC-0005, AC-0039, AC-0041): goal-based and TDD.** A search over the shipped trees, one `explain` and one `reconcile` call on a planted unregistered spec that red before the change, the parity test, and a read of the eval case.
- **Router and matrices (AC-0012, AC-0013): TDD.** `route_intake` is pure, so each route reds against its expected membership and mutation.
- **Repair (AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0042): TDD.** Each rule is a plan or apply result over a planted `workspace.toml` and lifecycle record, so one planted entry per case reds before the step exists.
- **Spec-status lint (AC-0021): TDD.** A planted open spec reds before the lint changes; the closed and link cases are regression guards.
- **Equivalence fixtures (AC-0022): goal-based.** The frozen fixtures and their suites run unchanged.
- **Writer and guide text (AC-0023, AC-0024, AC-0025, AC-0026): goal-based.** A roster check over closed lists of files and phrases, each phrase present at the base.
- **Release pairing (AC-0044): goal-based.** A read of the bridge spec's `Status:` and of the branch's fragment front matter and Highlights at this spec's ship commit.
- **Governance and records (AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0045, AC-0032, AC-0033, AC-0034): goal-based.** The same roster check reads each entry and the ledger's approval rows; the `workspace-retirement` check reads the record and inventory.
- **This repository (AC-0035, AC-0036, AC-0037, AC-0038): manual QA with a byte comparison.** The comparison, replay and repair run once over real data; `dispatch.py`'s before-and-after output is compared byte for byte, and the owner judges any replay difference.

## Acceptance Criteria

Terms used below. Kept entry is as the [`header-derived-dispatch`](../header-derived-dispatch/spec.md) spec's Acceptance Criteria define them; canonical membership and cooled as the [`depends-on-headers`](../depends-on-headers/spec.md) spec's do; brief file as the [`intent-brief-registration-stop`](../intent-brief-registration-stop/spec.md) spec's does.

- **Base.** Commit `dfa3fe067`.
- **Repo-origin spec entry.** A `workspace.toml` table whose `kind` is exactly `"spec"`, whose `source` is a table with `mode` exactly `"repo-origin"`, and whose `needs` is present as an array.
- **Registered repo-origin spec.** An element of the first list the engine's `_extract_canonical_memberships` returns, its parsed canonical memberships, as at the base, in a collection whose label starts `work.` or `backlog.`, with `kind` `spec` and `source.mode` `repo-origin`.
- **Drop candidate.** A registered repo-origin spec whose `needs` is empty, or is emptied by a `needs-to-header` or `needs-drop-cooled` operation of the same plan.
- **Declared parent.** For a cooled drop candidate whose raw `source.parent` key is present: `none` when its value is `none` or an empty string; otherwise the path `_resolved_provenance_parent(source.parent, require_local_brief=True)` returns, when that path is a brief file and matches `^docs/product/briefs/[a-z0-9][a-z0-9-]{0,127}\.md$`. An absent key, or any other value, declares no parent.
- **Held entry.** A cooled drop candidate that has a declared parent and whose lifecycle record carries no `parent`.

**Dispatch**

- [ ] **AC-0001.** Read with each run of whitespace as one space, `packs/core/.apm/skills/work-loop/SKILL.md` holds `scripts/dispatch.py`, `decision`, `candidates`, `--start`, and `--resume`, and holds none of `canonical.ready`, `canonical.active`, `canonical.blocked`, `select only the first`, ``If `workspace.toml` is present, read it and Surface``, and ``If `workspace.toml` is absent, an explicit current request``.
- [ ] **AC-0002.** `packs/core/.apm/skills/work-loop/evals/evals.json` parses and holds these cases by id, each with an `expected_output` and `assertions` that name the outcome listed:
  - `step0-dispatch-start` and `step0-dispatch-resume`: an argless start whose decision is `start` or `resume`, reading the named spec and plan and going to PLAN;
  - `step0-dispatch-ask`: an argless start whose decision is `ask`, listing every `candidates` path and asking;
  - `step0-dispatch-none` and `step0-dispatch-refuse`: stopping and surfacing each finding's `code`, `path` and `next_action`;
  - `step0-supplied-path-start`: a supplied spec path that `dispatch.py --start` accepts, starting it;
  - `step0-supplied-path-resume-refused`: a supplied spec path that `dispatch.py --resume` refuses, stopping with its findings;
  - `step0-explicit-request-conflict`: an explicit current request for new work whose scope matches a spec in `dispatch.py`'s `ready`, `active` or `blocked` list, naming that spec and not starting direct-light work;
  - `step0-no-registry-start`: a repository with no `workspace.toml` and one ready spec, starting it.
- [ ] **AC-0043.** No case of that file holds `canonical.ready`, `canonical.active`, `canonical workspace-status preflight`, or `untracked live specs` in its `prompt`, `expected_output` or `assertions`, matched without regard to letter case.

**`unregistered_work` and the cooled-child next action**

- [ ] **AC-0003.** No file under `packs/core/.apm/skills/` or `packages/agentbundle/agentbundle/_data/`, and not `guides/core/reference/workspace-toml-schema.md`, holds `unregistered_work`.
- [ ] **AC-0004.** `workspace-status explain docs/specs/<slug>/spec.md` for a spec that no canonical evaluation and no finding names prints `selector_status` `not_found` and an empty `findings` list.
- [ ] **AC-0005.** The engine's `cooled_child_scope_unknown` next action, its packaged copy, the readiness bridge's pinned copy, the `workspace-status` SKILL.md table and the schema guide's table each hold the sentence the ledger records as owner-approved, which names the lifecycle record's `parent`, and the bridge's pinned-table parity test passes.
- [ ] **AC-0039.** Case 11 of `packs/core/.apm/skills/workspace-status/evals/evals.json` names the lifecycle record's `parent` as the repair in its `expected_output` and `assertions`, and does not hold ``declare `source.parent` on the named entry``.

**Writers**

- [ ] **AC-0012.** For a signal whose `authority_mode` is `repo-origin` and `artifact_kind` is `spec`, carrying no named gaps, `route_intake` returns `lifecycle_membership` `none` with mutation `materialize-and-dispatch` and processor `new-spec` for `start`, and `none` with `materialize-draft-non-dispatchable` and processor `none` for `remember`. It returns the same `Route` as at the base for every other signal.
- [ ] **AC-0013.** The core routing matrix `packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json` gains the cases `start-repo-origin-spec` and `remember-repo-origin-spec` expecting AC-0012's routes; its other cases and every case of the `jira-brief-intake`, `jira-align-brief-intake`, `github-brief-intake` and `linear-brief-intake` matrices are byte-identical to the base; and each matrix's comparison suite passes.
- [ ] **AC-0014.** `workspace-status repair-plan` holds no `queue-to-shipped` or `queue-remove` operation for a drop candidate, so a held entry keeps its collection, and holds the operations it holds at the base for every other entry.
- [ ] **AC-0015.** The legacy-migration repair's routes and selections are those it offers and accepts at the base, and a `repair-plan` run after its apply holds a `spec-entry-drop` operation for each drop candidate it wrote that is not a held entry, and AC-0017's manual item for each held one.

**The repair**

- [ ] **AC-0016.** `repair-plan` holds one `spec-entry-drop` operation for each drop candidate that is not a held entry, naming its initiative key (empty for a top-level collection), collection, index, `path`, `kind` and registry fingerprint. It holds none for any other entry, including a `workspace.toml` table the membership iterator does not yield, such as a `kind = "spec"` entry with no `needs` key, which keeps the finding the engine gives it at the base.
- [ ] **AC-0017.** For each held entry, `repair-plan` holds no `spec-entry-drop` operation and one manual item naming the entry's `path`, its lifecycle record's path, and the `parent` value to add to that record: the declared parent.
- [ ] **AC-0018.** `repair-plan` and `repair-apply --yes` change no file under `docs/lifecycle/`: the set of paths there, and each file's bytes and modification time, are the same afterwards.
- [ ] **AC-0019.** `repair-apply --yes` applies every `needs-to-header` and `needs-drop-cooled` operation before any `spec-entry-drop` operation, and removes the entries of its applied drops in the same atomic, comment-preserving `workspace.toml` write under the writer lock as its other applied operations. It refuses a drop, keeping its entry, when the entry still has non-empty `needs` at that point, when the registry read under the lock holds no repo-origin spec entry at the planned locator with the planned `path` and fingerprint, or when that entry is then a held entry.
- [ ] **AC-0020.** On a registry where every planned operation applies, one `repair-plan` and `repair-apply --yes` run leaves no drop candidate other than held entries, and a following `repair-plan` holds no `spec-entry-drop` operation. Once a held entry's record carries `parent`, the next `repair-plan` holds a `spec-entry-drop` operation for it.
- [ ] **AC-0041.** `reconcile`'s `reconciliation.type1` is an empty list, and `repair-plan`'s manual list holds no `type1-untracked` item, for every tree, including a tree with an Approved or Implementing spec that no entry names.
- [ ] **AC-0042.** For each planted tree of the repair suite, including a cooled drop candidate with an absent `source.parent`, a held entry before and after its record gains `parent`, and a cooled drop candidate whose record already carries `parent`, the stdout of `dispatch.py --root <tree>` is byte-identical immediately before and immediately after `repair-apply --yes`, when that plan holds no `needs-to-header` or `needs-drop-cooled` operation.

**The spec-status lint**

- [ ] **AC-0021.** `lint-spec-status.py` also treats a `(deferred: <anchor>)` marker as resolved when `docs/specs/<anchor>/spec.md` under `--root` is a regular file, not a symbolic link, in a real directory, whose preamble status's leading word, read as the lint reads a spec's status, is not `Shipped` or `Archived`; every marker that resolves or fails at the base does the same.

**Equivalence fixtures**

- [ ] **AC-0022.** `packs/core/tests/skills/work-loop/fixtures/header-derived-dispatch/expected.json`, `packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected.json`, `fixtures/depends-on-headers/expected-cooled-brief.json` and `fixtures/captured-item-files/expected.json` are byte-identical to the base, and the suites that compare against them pass.

**Writer and guide text**

Each phrase below is present in its file at the base, and each check reads the file with each run of whitespace as one space.

- [ ] **AC-0023.** None of these files holds the phrase listed for it, and each names `tracker-origin` and the `spec-entry-drop` repair:
  - `packs/core/.apm/skills/work-intake/SKILL.md`: `A spec is registered, including when remembered` or `register an already-materialized spec`;
  - `packs/core/.apm/skills/workspace-status/SKILL.md` and `guides/core/reference/workspace-toml-schema.md`: `Register or reconcile the canonical entry explicitly`.
- [ ] **AC-0024.** None of these files holds the phrase listed for it:
  - `packs/core/.apm/skills/new-spec/SKILL.md`: `The workspace entry for a`;
  - `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`: `for queue registration`;
  - `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`: ``resolve to an entry in `workspace.toml [backlog].open` ``;
  - `packs/core/.apm/skills/work-loop/SKILL.md`: ``historical deferral anchors in `[backlog].open` `` or ``anchors still resolve in `[backlog].open` ``;
  - `packs/core/.apm/agents/adversarial-reviewer.md`: ``resolves to a slug entry in `workspace.toml [backlog].open` ``;
  - `packs/core/.apm/skills/workspace-status/references/reconcile.md`: `finds work nobody registered` or ``without being added to `workspace.toml` ``;
  - `packs/core/.apm/skills/workspace-status/SKILL.md`: ``run `reconcile` to also check for untracked live specs``, `Full audit: find untracked live specs`, `also finds untracked live specs (Type 1)`, `untracked live specs (empty in status/explain`, ``Autonomous dispatch consumers must use `canonical.ready` as the ready set``, ```canonical.ready` is the only queue-ready set and `canonical.active` the only resumable one``, or ``add to [work].queue through `work-intake` ``.
- [ ] **AC-0025.** `packs/core/.apm/skills/workspace-status/SKILL.md` names `work-loop`'s `dispatch.py` as the source of ready and resumable specs, and its next-action choices for starting or resuming a spec name `dispatch.py` rather than `canonical.ready` or `canonical.active`.
- [ ] **AC-0026.** None of these files holds the phrase listed for it:
  - `guides/core/tutorials/your-first-workspace.md`: ``Move the entry in `workspace.toml` from``;
  - `guides/core/explanation/role-journeys.md`: ``moves the spec from `[work].active` to `[work].shipped` `` or ``routes them to `[work].queue` ``;
  - `guides/core/explanation/two-room-model.md`: ``The spec's path enters the build room's `queue` ``;
  - `guides/core/how-to/start-or-remember-work.md`: ``then adds the `workspace.toml` ``;
  - `guides/_shared/reference/work-intake-routing-and-lifecycle.md`: ```work.queue` only after approval and sibling plan``;
  - `guides/catalogue-curation/tutorials/your-first-skill.md`: `registers a spec or tracker-origin item` or ``into specs in `[work].queue` ``;
  - `guides/core/how-to/close-and-disposition-work.md`: `declare source.parent on its workspace entry`;
  - `docs/product/journeys/engineer-runs-work-loop.md`: ``canonical ready/active spec from `workspace-status` ``.

**Governance**

- [ ] **AC-0027.** Each of these § Errata sections holds an entry dated on or after 2026-10-29 that links RFC-0106 and holds each literal listed for it:
  - `docs/rfc/0064-ini-001-ai-native-ecosystem.md`, in both its Current state table and its History: `D4`, `[work]`, `work-loop`, and `M1`;
  - `docs/rfc/0106-stop-registering-derivable-work.md`: `the spec entry removal`, `spec-entry-drop`, and `tracker-origin`;
  - `docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md`: `Revisit if`, `parent`, and `lifecycle record`;
  - `docs/adr/0076-briefs-persist-dispatch-starts-from-specs.md`, in a `## Errata` section the ADR gains: `dispatch.py` and `Brief:`.
- [ ] **AC-0028.** Each of these intents holds a paragraph that starts `**Amendment, ` with a date on or after 2026-10-29 and `eugenelim (owner)`, links RFC-0106, and holds each literal listed for it:
  - `docs/product/intents/FEAT-0005-lifecycle-and-closure.md`: `item 7` and `spec`;
  - `docs/product/intents/FEAT-0007-work-item-promotion-routing.md`: `spec` and `remember route`.
- [ ] **AC-0029.** `docs/product/AGENTS.md` does not hold ``Registered spec membership in `workspace.toml` ``, and its § Status has one home names the spec's `Brief:` header as the coverage evidence.
- [ ] **AC-0045.** The Non-goals of `docs/product/briefs/workspace-registry-retirement-delivery.md` admit, in owner-approved wording, keeping the bridge's pinned finding table equal to the engine's when a slice adds, removes or rewords a finding code, and no longer hold `when a slice adds a finding code, as the bridge's parity test requires`.
- [ ] **AC-0030.** `docs/product/briefs/agent-skill-engineering.md` holds none of ``registered under `ini-009` ``, ``register the spec under `ini-009` ``, and ``register approved specs in `workspace.toml` ``, and `lint-brief-coverage.py` passes on it.
- [ ] **AC-0031.** `docs/specs/spec-registration-stop/notes/verification-ledger.md` holds one row for each entry AC-0027 lists, each intent AC-0028 lists, the files AC-0029, AC-0030 and AC-0045 name, and the AC-0005 sentence, naming its target file and the owner's approval with an ISO 8601 timestamp to the minute with its UTC offset, which is earlier than the author date (`git log --format=%aI`) of the commit that adds that text.

**Records**

- [ ] **AC-0032.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one slice-8 row for each of these cases, under the criteria the [`workspace-retirement`](../workspace-retirement/spec.md) spec states: `the spec entry removal`, as `reproduced`.
- [ ] **AC-0033.** No row of that record's § Disposition carries Owner `8`, apart from `spec registration as brief coverage evidence`, whose Home is exactly `nothing`.
- [ ] **AC-0034.** In `docs/specs/workspace-retirement/inventory.toml`, no row carries `owner = 8` apart from the rows left to `docs/specs/readiness-bridge-dispatch-input/`, which are exactly those whose `pattern` lies under that directory, `packs/core/.apm/skills/navigate-intents/`, `packs/core/tests/skills/navigate-intents/`, `.claude/skills/navigate-intents/`, `.agents/skills/navigate-intents/`, `docs/specs/intent-view-readiness-handover/`, `docs/specs/intent-navigation/` or `docs/specs/intent-navigation-export/`, or is `guides/core/how-to/navigate-intents.md` or `docs/rfc/0108-skill-html-view-standard.md`; this spec's directory has one `docs/specs/spec-registration-stop/*` `contract` row at owner `8`; and the inventory check passes.

**Release pairing**

- [ ] **AC-0044.** At the commit that sets this spec's `Status:` to `Shipped`, `docs/specs/readiness-bridge-dispatch-input/spec.md` exists with `Status:` `Shipped`, and one `docs/product/changelog.d/` fragment that the branch adds carries a `[[packages]]` entry whose `name` is `core` and whose `version` equals `core`'s `pack.toml` version at that commit, and whose Highlights hold both `spec-entry-drop` and `--readiness`.

**This repository**

- [ ] **AC-0035.** The ledger holds, from before any writer instruction, router branch, repair step, or registry entry changes other than this spec's own entry: one run of `python3 tools/compare-registry.py --root .` with its full output, exit code `0`, commit, and merge base with `origin/main`; and one run of `tools/replay-dispatch.py` over a `git worktree` of that merge base, with every differing spec assigned to an accepted authority or the owner's recorded approval.
- [ ] **AC-0036.** This repository's `workspace.toml` holds no registered repo-origin spec, and the brief's Spec map holds `spec-registration-stop`.
- [ ] **AC-0037.** The ledger holds the `repair-plan` and `repair-apply` output that removed them; the number of `needs-to-header` and `needs-drop-cooled` operations, held entries, needs manual items, `type1-untracked` items, and `spec-entry-drop` operations planned, and of entries the apply removed; and the owner's recorded sight of the plan file before the apply.
- [ ] **AC-0038.** The ledger holds the SHA-256 of `dispatch.py --root .`'s stdout and of `dispatch.py --root . --resume docs/specs/spec-registration-stop/spec.md`'s stdout, each taken immediately before and immediately after that apply, and each pair is equal; that plan holds no `needs-to-header` or `needs-drop-cooled` operation and no held entry.

## Follow-ons

- `docs/specs/readiness-bridge-dispatch-input/`, owned jointly with the `navigate-intents` owner, re-points `export --readiness -` to `dispatch.py`'s output and amends the readiness hand-over spec, with the RFC-0105 and RFC-0108 errata and the `the readiness bridge's first-ready mark` equivalence row. It ships in this spec's release (AC-0044). The bridge criteria first drafted here, and the round-3 findings against them, are its shaping input.
- The brief's slice 9 gives tracker-origin specs, intents and briefs a home for their tracker profile, ends their registration, moves whatever engine rules `dispatch.py` still needs into `work-loop`, shrinks `workspace-status` to the repair, and deletes `workspace.toml`.

## Assumptions

none
