# Spec: Captured items stop being registered

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-27 by eugenelim, spec and plan, after three rounds of spec-stage shaping and adversarial review with every sustained finding repaired and adjudicated; review records under `.context/reviews/captured-item-registration-stop-spec-r1/` to `-r3/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, a type's registration stops in the release that ships the replacement for every responsibility its entries feed, and the contracts requiring it change in the same release through their own errata; D3, a captured item's own file), RFC-0105 (D3, the behavioral-equivalence gate and accepted authority for an intended change or a removal), ADR-0053 (D9, the OKR gap handoff), RFC-0063 (D9, the same handoff), RFC-0083 (§ 6 and § 8, remembered and defect items in `[backlog]`), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:captured-item-files, spec:depends-on-headers, spec:registry-comparison
- **Contract:** none — the captured-item file grammar is published in `work-intake`'s skill and the `workspace.toml` schema guide, and the criteria below change one rule of it.
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

A maintainer or agent who records a defect, a design question, or an OKR gap writes one file under `docs/product/captured/` and edits nothing else, and closing it later is one more edit to that file. Success is that no shipped skill or guide tells anyone to add a captured item to `workspace.toml`, and that a closed captured item with no registry entry gives no finding and settles a dependency exactly when its file says `Status: Closed` and `Resolution: fixed`.

## What Changes

- The captured-item grammar's `Resolution:` rule — required on every `Closed` item of any kind, not only on a defect — in `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and its packaged copy.
- Dependency satisfaction for a captured-item file that no registry entry names — settled by its own `Status:` and `Resolution:` — in the same engine.
- `work-intake`'s router: the `remember` route for a defect, design, or research item, and the `defect` start route, return no membership and no registration — `packs/core/.apm/skills/work-intake/scripts/intake_router.py`, its routing eval matrix, and the defect case of the four tracker brief-intake eval matrices in the `atlassian`, `github`, and `linear` packs. The defect start route's artifact is a captured-item file.
- `work-intake`'s intake transaction runs a route that registers nothing — `scripts/intake_transaction.py` and SKILL.md § 5.
- `work-intake`'s registration rule: a captured item is its file alone, and closing one that is still registered deletes its entry — `packs/core/.apm/skills/work-intake/SKILL.md` § Terse workspace capture and `references/lifecycle-index.md`.
- The other writers and suggesters write or suggest only the file: `work-loop`'s pre-flight failure capture; `run-okr-cascade` and its cross-pack routing reference, jointly with the `product-strategy` pack; `frame-situation` and `diverge-solutions` with their examples, jointly with the `product-engineering` pack; and the architect guide `establish-reference-architecture.md`.
- The guides and promise pages that describe captured-item registration — the core, shared, product-engineering, and product-strategy guides, `packs/core/DESIGN.md`, the `product-strategy` pack's `README.md`, `JOURNEY.md`, and `DESIGN.md`, and its web journey page.
- Errata entries on ADR-0053 and RFC-0063 replacing the shaping-queue handoff with the gap file; on RFC-0083 for remembered and defect items; and on RFC-0106 authorising the closed state of a captured item of another kind as an intended change and the unread header of an unregistered captured item as an accepted removal.
- The captured-item stop rows of `docs/specs/workspace-retirement/retirement-record.md` § Equivalence, admitted by a controlled amendment of the `workspace-retirement` spec, and the inventory rows this stop disposes or re-owns.
- `docs/specs/captured-item-files/spec.md`'s status line, marked superseded in part for its `Resolution:` rule.
- Unchanged: every existing registry entry, including the 51 migrated captured memberships and the 26 legacy slug-only entries; every rule for a captured item that has a membership, apart from the `Resolution:` grammar, which applies to every captured-item file; intent, brief, and spec registration, including the `remember` route for an intent, a brief, or a spec.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the captured-item file grammar and its closed state | Applicable: writers and readers share the file shape | `packs/core/.apm/skills/work-intake/SKILL.md` § Terse workspace capture and § 5, and `guides/core/reference/workspace-toml-schema.md` | Platform Core maintainer | AC-0001, AC-0011, and AC-0020 pass for the rules; the wording follows plan T4's design decisions and is checked in review | Both name `Resolution:` on every closed item and the deletion of a registered item's entry on close |
| Decision rationale: the contracts that required registration | Applicable: RFC-0106 D1 requires each to change in the stop's release | `docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md`, `docs/rfc/0063-product-strategy-pack.md`, and `docs/rfc/0083-work-intake-and-artifact-routing.md`, each § Errata | eugenelim, Decision-maker and Approver | AC-0015 passes | Each entry carries owner-approved wording |
| Decision rationale: equivalence evidence and the authority for the intended change and the removal | Applicable: RFC-0105 D3 gate 3 | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence, and `docs/rfc/0106-stop-registering-derivable-work.md` § Errata | Platform Core maintainer; eugenelim as RFC-0106 Approver | AC-0016 and the amended `workspace-retirement` check pass | Each case AC-0016 lists has a row |
| Current product truth: which consumers still depend on the registry | Applicable: the stop changes what several inventory rows describe | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0017 and the inventory check pass | No row outside the two captured-item spec directories names slice 3 |
| User documentation: how to remember and close work | Applicable: adopters capture and close items by hand or through `work-intake` | `guides/core/how-to/start-or-remember-work.md`, `guides/core/how-to/capture-work.md`, `guides/_shared/how-to/use-work-intake.md`, both `work-intake-routing-and-lifecycle.md` references, `guides/core/explanation/role-journeys.md`, `guides/product-engineering/how-to/frame-a-situation.md`, and the four `guides/product-strategy/` pages AC-0014 lists | Platform Core maintainer; each pack's owner for its guides | AC-0011 and AC-0014 pass for the pages they list; the generic remember and start text follows plan T4's design decisions and is checked in review | Each page tells the reader to write the file and never to register it |
| Cross-pack contract: OKR gaps and suggested captured items | Applicable: `run-okr-cascade`, `frame-situation`, and `diverge-solutions` change output | each skill's `SKILL.md`, references, examples, and evals; the `product-strategy` `README.md`, `JOURNEY.md`, `DESIGN.md`, `web/src/content/journeys/product-strategy.md`, and `packs/core/DESIGN.md` | Platform Core maintainer with each pack's owner | AC-0010, AC-0012, and AC-0014 pass; `packs/core/DESIGN.md` follows plan T4's design decisions and is checked in review | No surface names a shaping-queue entry for a gap |
| Verification record: the registry comparison before the stop | Applicable: FEAT-0034's validation hook | `docs/specs/captured-item-registration-stop/notes/verification-ledger.md` | Platform Core maintainer | AC-0018 passes | The ledger holds the run and no failing row |
| Release history | Applicable: shipped content changes in `core`, `product-strategy`, `product-engineering`, `atlassian`, `github`, and `linear` | a `docs/product/changelog.d/` fragment; each changed pack's `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog and version gates pass | The fragment names the stop and the closed-state rule |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read a captured-item file only through the engine's existing confined captured-item reader, and never open a cooled file's body.
- Regenerate the packaged and projected copies with `make build-self`, bump each changed pack's version, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits a file under `packages/agentbundle/`.
- Run `python3 tools/compare-registry.py --root .` on the implementing branch before any writer instruction changes, and stop for the owner if it exits non-zero.

### Ask first

- The wording of each errata entry on ADR-0053, RFC-0063, RFC-0083, and RFC-0106. The owner approves each before it is committed.
- Any change to a skill in the `product-strategy`, `product-engineering`, `atlassian`, `github`, or `linear` pack beyond its captured-item instructions, its gap or suggestion output, and the defect route's expected membership and mutation in its eval matrix.
- Adding a finding code.

### Never do

- Remove, move, or rewrite any existing `workspace.toml` entry, apart from adding and moving this spec's own entry and moving the parent brief's entry together with its `Status:` line.
- Change how a captured item with a registry entry is reconciled or how a dependency on one is settled, or change the `captured-to-file` repair, apart from what follows from the grammar AC-0001 sets for every captured-item file.
- Change intent, brief, or spec registration, the `remember` route for an intent, a brief, or a spec, or any `navigate-intents` file.
- Add a dependency, a skill, a module, or a top-level directory, or add any reader of the old `workspace.toml` shape outside the repair.

## Testing Strategy

- **Grammar and the closed state (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006): TDD.** Each is a rule over one file's preamble and one dependency, so one planted file per case reds each test before the rule exists.
- **Rules unchanged for registered items (AC-0007): goal-based.** The existing captured-item and dependency-header equivalence fixtures run unchanged against the new engine.
- **Router and transaction (AC-0008, AC-0009, AC-0020): TDD.** `route_intake` is a pure function, so each route reds against its expected membership and mutation; the transaction reds on a fixture repository whose `workspace.toml` bytes are compared.
- **Routing evals (AC-0010): goal-based.** The existing matrix comparisons in the `work-intake` and tracker brief-intake suites run against the edited matrices.
- **Writer, guide, and governance instructions (AC-0011, AC-0012, AC-0014, AC-0015): goal-based.** A roster check over a closed list of files and phrases.
- **Equivalence, inventory, and the comparison record (AC-0016, AC-0017, AC-0018): goal-based.** The amended `workspace-retirement` check and this spec's roster check run against this repository.
- **This repository unchanged (AC-0019): goal-based.** The engine before and after the change runs over the same tree.

## Acceptance Criteria

Terms used below. Captured-item directory, captured-item file, captured membership, cooled, and the echo rule are as the [`captured-item-files`](../captured-item-files/spec.md) spec's Acceptance Criteria define them. Dependency item and canonical membership are as the [`depends-on-headers`](../depends-on-headers/spec.md) spec's define them.

- **Unregistered captured item.** A captured-item file whose path no canonical membership names.

Each criterion from AC-0001 to AC-0006 is a rule the engine enforces. Given an input that breaks one, the result names the file's path under the echo rule.

**The closed state**

- [ ] **AC-0001.** A captured-item file whose `Status:` is `Closed` and that has no `Resolution:` line, or whose `Status:` is `Open` and that has one, gives `invalid_captured_item` naming `Resolution`, whatever its `Kind:` and whether or not a registry entry names it. Every other rule of the captured-item grammar is unchanged.
- [ ] **AC-0002.** A dependency item that names a non-cooled unregistered captured item is satisfied exactly when that file is valid, its `Status:` is `Closed`, and its `Resolution:` is `fixed`, whatever its `Kind:`.
- [ ] **AC-0003.** Such a dependency on a valid file that is `Open`, or `Closed` with `Resolution:` `declined` or `superseded`, gives `unsatisfied_dependency` and is not satisfied.
- [ ] **AC-0004.** Such a dependency on a confined, canonically spelled file whose `Kind:` is a captured kind and that is otherwise invalid gives that file's `invalid_captured_item` finding and is not satisfied.
- [ ] **AC-0005.** A dependency item that names an unregistered captured-item path that is cooled, missing, not a confined file, unreadable, spelled other than canonically, or whose `Kind:` is not a captured kind gives the result it gives at commit `dd4f7038c`, with and without a completion receipt; a cooled file is never opened.
- [ ] **AC-0006.** A valid unregistered captured item gives no finding naming its path in `workspace-status status` output, in `captured.findings` or in the canonical findings, whatever its `Status:`, `Kind:`, and `Type:`, and even when its own `Depends on:` line names a missing target or forms a cycle, apart from the dependency findings AC-0003 and AC-0004 set for a waiter that names it.
- [ ] **AC-0007.** `packs/core/tests/skills/workspace-status/fixtures/captured-item-files/expected.json`, `fixtures/depends-on-headers/expected.json`, and `fixtures/depends-on-headers/expected-cooled-brief.json` are byte-identical to their state at commit `dd4f7038c`, and the suites that compare against them pass. The only case those suites change is a registered `Closed` non-defect record gaining a `Resolution:` line, and each such case keeps its result at `dd4f7038c`.

**The writers**

- [ ] **AC-0008.** `route_intake` returns `lifecycle_membership` `none` and a `mutation` that does not contain `register` for a `remember` signal whose `artifact_kind` is `defect`, `design`, or `research`, and for a `start` signal whose `artifact_kind` is `defect`. It returns the same `Route` as at commit `dd4f7038c` for every other signal, including a `remember` signal for an intent, a brief, or a spec.
- [ ] **AC-0009.** For the `defect` start route, `route_intake` still returns the processor `bug-fix`.
- [ ] **AC-0010.** The defect case of `packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json`, and of the intake matrix of `jira-brief-intake`, `jira-align-brief-intake`, `github-brief-intake`, and `linear-brief-intake`, expects the route AC-0008 and AC-0009 set and an `artifact` under `docs/product/captured/`, and each matrix's comparison suite passes.
- [ ] **AC-0020.** `run_intake_transaction`, given no registration step, takes the writer lock, materializes the artifact, and dispatches the processor, and leaves `workspace.toml` byte-identical; given a registration step, it behaves as at commit `dd4f7038c`.
- [ ] **AC-0011.** No file in the closed list below holds a line that contains `docs/product/captured/` together with `path =`, `path=`, `[backlog].open`, or `shaping_queue`. Read with each run of whitespace, line breaks included, as one space, none holds any of these phrases: `Do not stop registering`, `register its path`, `register that path`, `registers that path`, `register that record`, `registers that file's path`, `entry that registers`, `Entry that registers`, `writes the record and the entry`, `writes the record and adds`, `registered by`, `is registered in`, `TOML entry`, `then register it`, `register it through`, `Its index entry's`, or `Its registry entry points at that file`. None of the six listed files under `packs/product-strategy/` or `packs/product-engineering/` holds `shaping_queue` on any line. The closed list is:
  - `packs/core/.apm/skills/work-intake/SKILL.md`;
  - `packs/core/.apm/skills/work-intake/references/lifecycle-index.md`;
  - `packs/core/.apm/skills/work-loop/SKILL.md`;
  - `packs/core/.apm/skills/work-loop/references/pre-flight-failures.md`;
  - `packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md`;
  - `packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md`;
  - `packs/product-engineering/.apm/skills/frame-situation/SKILL.md`;
  - `packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md`;
  - `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`;
  - `packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md`;
  - `guides/architect/how-to/establish-reference-architecture.md`;
  - `guides/core/reference/workspace-toml-schema.md`;
  - `guides/core/how-to/start-or-remember-work.md`.
- [ ] **AC-0012.** `packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md` and `references/cross-pack-routing.md` name neither `workspace.toml` nor `shaping_queue`, and the skill still names `Kind: intent` and `Type: strategy` for each gap file.
- [ ] **AC-0014.** Read with each run of whitespace as one space, none of these files holds `{type = "strategy"}`, `shaping_queue`, `gap entries in workspace.toml`, `` `workspace.toml` entries ``, `` `workspace.toml` snippet ``, `workspace.toml suggestion`, `` strategy entries in `workspace.toml` ``, `strategy-type entry`, or `` adds each gap to `workspace.toml` ``, and `guides/_shared/reference/work-intake-routing-and-lifecycle.md` holds no `` | defect context | `backlog.open` | ``:
  - `guides/core/explanation/role-journeys.md`;
  - `guides/product-engineering/how-to/frame-a-situation.md`;
  - `guides/product-strategy/how-to/cascade-okrs-into-the-shaping-queue.md`;
  - `guides/product-strategy/how-to/set-the-direction.md`;
  - `guides/product-strategy/reference/frameworks-and-artifacts.md`;
  - `guides/product-strategy/explanation/why-strategy-is-its-own-seat.md`;
  - `packs/product-strategy/README.md`;
  - `packs/product-strategy/JOURNEY.md`;
  - `packs/product-strategy/DESIGN.md`;
  - `web/src/content/journeys/product-strategy.md`.

**Governance and the retirement record**

- [ ] **AC-0015.** Each of these § Errata sections holds an entry dated on or after 2026-10-27 that links RFC-0106, names `docs/product/captured/`, and names each passage listed for it:
  - `docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md`: D9 and § Cross-pack routing contract, with `Type: strategy`;
  - `docs/rfc/0063-product-strategy-pack.md`: the Reviewer brief's Decision, D9, the `run-okr-cascade` row of § Skill set (v1), steps 4 and 5 of § Cross-pack routing contract, its diagram, and its Boundary, with `Type: strategy`;
  - `docs/rfc/0083-work-intake-and-artifact-routing.md`: § 6's start route, its remember route, and its flow; and § 8's `[backlog].open` and `[backlog].closed` rows, its sentence that an unassigned artifact appears only in `[backlog].open`, its sentence that defect contexts stay in the repository-level backlog, its defect move, and its defect dependency rule.
- [ ] **AC-0016.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one slice-3 row for each of these cases, its Case cell being the case's name, under the criteria the amended `workspace-retirement` spec states:
  - `the unregistered captured-item listing`, as `reproduced`;
  - `the closed defect without a membership`, as `reproduced`;
  - `the closed captured item of another kind`, as `intended change`, whose Authority is an RFC-0106 § Errata entry naming that case;
  - `the unregistered captured item's own dependencies`, as `accepted removal`, whose Authority is an RFC-0106 § Errata entry naming that case.
- [ ] **AC-0017.** In `docs/specs/workspace-retirement/inventory.toml`, no row whose `pattern` lies outside `docs/specs/captured-item-files/` and `docs/specs/captured-item-registration-stop/` carries `owner = 3`, and the inventory check passes.
- [ ] **AC-0018.** `docs/specs/captured-item-registration-stop/notes/verification-ledger.md` holds one run of `python3 tools/compare-registry.py --root .` on this spec's branch before its first writer change: the full default output, its exit code `0`, the commit it ran at, and that commit's merge base with `origin/main`.

**This repository**

- [ ] **AC-0019.** Over this repository's tree at the implementing pull request's head commit, the engine at that commit and the engine at commit `dd4f7038c` report the same `canonical.ready`, `canonical.active`, and `canonical.blocked` paths, the same canonical findings by code and path, and the same `captured` object.

## Follow-ons

- The brief's slice 9 removes the 51 migrated captured memberships and the 26 legacy slug-only entries with the rest of the registry, and re-points `lint-spec-status.py`'s deferral anchors from `[backlog].open` to captured-item files.

## Assumptions

none
