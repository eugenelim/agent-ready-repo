# Spec: Dependency edges on the waiting item

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-25 by eugenelim, spec and plan, after clean spec-stage shaping, adversarial, and security reviews; review records under `.context/reviews/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D3, `Depends on:` with RFC-0103 typed references on the waiting item; D1, a writer stops only with its contract), RFC-0105 (D3, the behavioral-equivalence gate), RFC-0103 (D1, the `<kind>:<slug>` reference and the refusal of an ambiguous name), ADR-0103 (the completion receipt's fields and outcome vocabulary), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Contract:** none — the header grammar is contracted by the criteria below; `contracts/jsonschema/workspace-entry.schema.json` keeps its shape, because the repair reads the old `needs` content through it.
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

A maintainer or agent records that one piece of work waits for another by editing only the waiting item's own `Depends on:` header, and `workspace-status` blocks on that header exactly as it blocked on the registry's `needs` edge. Success is that every typed `needs` edge in this repository moves to a header in one repair run, with an edge-for-edge comparison showing that none was lost, and that an entry still carrying `needs` content is refused and pointed at the repair, never read as having no dependency.

## What Changes

- The `Depends on:` and `Dependency receipts:` preamble fields — on any file a registry entry names: spec, brief, intent, or a captured item's own file.
- Their reader, and the switch of blocking from `needs` to the header — `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and its packaged copy.
- The `unmigrated_needs` refusal and the `invalid_dependency` finding — the same engine.
- A `needs-to-header` operation in `repair-plan` and `repair-apply` — `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`.
- The migration of this repository's 113 typed `needs` edges into the headers of their 78 waiting files, and `needs = []` on those entries — `workspace.toml` and the waiting files.
- Four registered Shipped specs' free-text `Depends on:` lines, normalized by hand to typed references.
- The blocking equivalence record — `docs/specs/workspace-retirement/retirement-record.md` § Equivalence, by a controlled amendment of the `workspace-retirement` spec.
- An RFC-0106 errata entry for the two behaviors that cannot be kept, the cooled waiting item's edges and the pruned captured item settled by a completion receipt, and a new ADR that supersedes ADR-0103 D6 in part, moving the receipt's carrier.
- Every live instruction that tells an author to write a `needs` edge or a receipt on one — the sites AC-0018 lists.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the header grammar authors write | Applicable: a new published preamble field pair | `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md` § Spec metadata contract, the spec template, and `guides/core/reference/workspace-toml-schema.md` § `needs` | Platform Core maintainer | The grammar text matches the terms and AC-0004; AC-0018 passes | Each surface names both fields and the repair |
| User documentation: how an adopter moves their edges | Applicable: adopters upgrade by running the repair | `packs/core/.apm/skills/workspace-status/references/mutate.md` § Repair subcommands and `docs/product/workspace-toml-deps.md` | Platform Core maintainer | The `needs-to-header` operation and its confirmation are described | The text names the command, its confirmation, and its edge comparison |
| Decision rationale: equivalence evidence | Applicable: RFC-0105 D3 gate 3 | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence | Platform Core maintainer | The amended `workspace-retirement` check passes | Every case in AC-0014 has a row |
| Decision rationale: removal authority for the cooled waiting item and the receipt-settled pruned captured item | Applicable: two behaviors are dropped | `docs/rfc/0106-stop-registering-derivable-work.md` § Errata | Platform Core maintainer, as RFC-0106 Approver | A dated entry naming both cases | Both Equivalence rows link it |
| Decision rationale: the receipt's carrier | Applicable: ADR-0103 D6 names the `workspace.toml` edge as the carrier, and ADR-0117 D3 admits errata only for a clarification | A new ADR under `docs/adr/` with `Supersedes in part: ADR-0103 D6`, mirrored by `Superseded in part` on ADR-0103, citing RFC-0106 D3 | Platform Core maintainer | The ADR is Accepted; `lint-adr-shape.py docs/adr` passes | Both supersession fields resolve |
| Current product truth: contracts that say an edge is a `needs` entry | Applicable: inventory rows with owner 2 | ADR-0110, CAP-0004, FEAT-0002, `packs/architect/DESIGN.md`, `guides/architect/how-to/establish-reference-architecture.md`, and the `cooling-brief-child-scope-closure` and `dependency-scoped-completion-receipts` spec directories | Platform Core maintainer | Each states the header as the edge's home, or its inventory row moves to the slice that still owns its registry fact | `test_workspace_retirement_inventory.py` passes |
| Maintainer procedure: where `close-work` keeps a receipt | Applicable: a live instruction changes | `packs/core/.apm/skills/close-work/SKILL.md` | Platform Core maintainer | AC-0018 passes | The instruction names `Dependency receipts:` |
| Release history | Applicable: shipped `core` behavior changes | a `docs/product/changelog.d/` fragment, with `core`'s `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog gate passes | The fragment names the repair and the refusal |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Open every waiting item and dependency target through the engine's existing confinement checks, and never open a cooled artifact's body.
- Keep each satisfaction rule as it is: what makes a spec, brief, intent, or defect satisfied, and how a completion receipt or coordination receipt is validated. Only the place an edge is read from moves.
- Regenerate the packaged copies with `make build-self`, bump `core`'s version, and carry the `Engine-Change-RFC:` trailer on every commit that edits an engine source.
- Run the repair on this repository only as `repair-plan`, then the owner's confirmation of that exact plan, then `repair-apply`.

### Ask first

- Running `repair-apply` against this repository's `workspace.toml`. The owner confirms the exact plan.
- The wording of the RFC-0106 errata entry and of the ADR that supersedes ADR-0103 D6 in part. The Approver signs each.
- Adding a finding code other than `unmigrated_needs` and `invalid_dependency`.
- Editing a `retirement-record.md` Disposition row other than the Home cells of `crossRepoNeed.type`, `crossRepoNeed.kind`, `crossRepoNeed.receipt_id`, `crossRepoNeed.accepted_revision`, and the `localNeed.receipt` rows.

### Never do

- Change `navigate-intents`.
- Let any shipped reader other than the repair derive a dependency, satisfaction, or readiness from typed `needs` content.
- Add a dependency, a skill, a module outside the two `workspace-status` scripts and their packaged copies, or a top-level directory. `tomlkit` stays confined to `repair-apply`, as `packs/core/AGENTS.md` declares.
- Edit a frozen record beyond adding the repair's header lines to a waiting file and normalizing the four registered Shipped specs' existing `Depends on:` lines.
- Edit `workspace.toml` beyond the repair's `needs = []` rewrites, adding and moving this spec's own entry, and the parent brief's entry moved together with its `Status:` line.

## Testing Strategy

- **Header reading and refusals (AC-0001, AC-0002, AC-0004, AC-0005, AC-0006, AC-0027): TDD.** Each is a rule over one file's preamble, one registry entry, or one directory listing, so a fixture with one planted case reds each test before the rule exists.
- **Blocking equivalence (AC-0003, AC-0007, AC-0008): TDD, paired fixtures.** Each case is written once as a typed `needs` edge and once as a header. The outcome of the `needs` form is recorded from the engine at commit `1f9c27342` as a frozen expectation, and the header form must produce the same result.
- **Repair and echoed output (AC-0009, AC-0010, AC-0011, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0028, AC-0029, AC-0030, AC-0031): TDD over fixture repositories**, including an interrupted apply and a rerun.
- **This repository's migration (AC-0012, AC-0013, AC-0015, AC-0017): goal-based.** The repair runs here once, and the `status` output of the tree it read is compared with the tree it left. `navigate-intents` then runs over the result.
- **Instructions (AC-0016, AC-0018): goal-based.** A roster check over the named globs and files.
- **Equivalence record (AC-0014): goal-based.** The amended `workspace-retirement` check runs against this repository.

## Acceptance Criteria

Terms used below:

- **Canonical membership.** A registry entry that the canonical reconciliation parses as a target entry. Its **waiting item** is the file its `path` names.
- **Preamble.** A file's lines before its first `## ` heading, outside fenced blocks, with HTML comments hidden. This is the rule the engine already uses for `Status:`.
- **Dependency items.** Every comma-separated item of every `- **Depends on:**` preamble line of a waiting item, trimmed, with empty items dropped. A line whose first word is `none` contributes no item.
- **Slug.** One or more lowercase letters, digits, and hyphens, starting with a letter or digit.
- **Field value.** A preamble field's value with a trailing HTML comment hidden and one pair of surrounding backticks stripped. A `Kind:` or `Level:` value is its first word.
- **Live intent.** A file directly in `docs/product/intents/` whose name matches `^[A-Za-z0-9][A-Za-z0-9._-]*\.md$` and whose preamble has no `Tombstone:` field, the admission rule `navigate-intents` applies. Its **intent kind** is `outcome` or `opportunity` when its `Kind:` field value says so, `capability` when its `Level:` field value is `capability`, and `intent` otherwise.
- **Typed reference.** `spec:<slug>`, `brief:<slug>`, or `<k>:<slug>` where `<k>` is `intent`, `outcome`, `opportunity`, or `capability`. Its **target** is, in turn: `docs/specs/<slug>/spec.md`, opened by its path with no directory listing; the brief under `docs/product/briefs/` whose `Slug:` field value is `<slug>`, or whose file stem is `<slug>` when its preamble was read and has no `Slug:`; or the live intent whose intent kind is `<k>` and whose `Slug:` field value is `<slug>`.
- **Captured-item reference.** A path of one or more `/`-separated segments, each matching `[A-Za-z0-9._-]+` and none `.` or `..`, that is not a `docs/specs/<d>/spec.md` file and lies outside `docs/product/briefs/` and `docs/product/intents/`. Its kind is the `kind` of the canonical membership at that path, or, when there is none, the `Kind:` field value of the file's own preamble. When no file and no membership exist at the path, it is a missing target at that path.
- **Header edge.** A pair of a waiting item and one of its dependency items, together with that item's receipt from AC-0004 when it has one.
- **Resolution index.** The listings of `docs/product/briefs/` and `docs/product/intents/` that typed brief and intent references resolve against, and the preamble of each entry it admits: in either directory, an entry whose name matches the Live intent name pattern. It ignores every other entry.

Each criterion from AC-0001 to AC-0011 and from AC-0019 to AC-0031 is a rule the engine or the repair enforces. Given an input that breaks one about a single membership, the result names the waiting path and the offending item, as AC-0028 allows. AC-0029 names its workspace-level cause instead.

- [ ] **AC-0001.** The canonical reconciliation takes a canonical membership's dependencies from its waiting item's dependency items, and from nothing else.
- [ ] **AC-0002.** A dependency item gives an `invalid_dependency` finding naming the waiting path and the item, and makes the membership not dispatchable, when it is neither a typed reference nor a captured-item reference, when it has more than one target, or when it is a captured-item reference to an existing file with no kind. A repository path to a spec, brief, or intent is not a captured-item reference. An indented non-blank line directly after a `Depends on:` or `Dependency receipts:` line also gives `invalid_dependency`, because a wrapped item would otherwise be dropped.
- [ ] **AC-0003.** For each of these cases, a header edge gives the same finding codes and the same dispatchable result as the same edge written as a typed `needs` entry gave at commit `1f9c27342`. A typed reference with no target is treated as a missing target at `docs/specs/<slug>/spec.md` for a spec, and at the reference itself otherwise.
  - a spec, brief, or intent target that is terminal, and one that is not;
  - a defect target with a `backlog.closed` membership, one with a `backlog.open` membership, and one with no membership whose own `Kind:` line is `defect`;
  - a cooled target;
  - a brief target whose child scope is unknown;
  - a missing target, given as a typed reference and as a captured-item reference;
  - a missing typed target with a completion receipt whose outcome is `completed`, one whose outcome is `abandoned`, and one with an invalid value;
  - a coordination receipt that matches, one whose `accepted_revision` differs, and a containing brief whose receipt block is invalid.
- [ ] **AC-0004.** A `- **Dependency receipts:**` preamble line holds comma-separated receipts, each made of tokens separated by whitespace:
  - `<reference> completion <delivery_id> <outcome> <completion_event> <evidence_ref>`;
  - `<reference> coordination <remote_kind> <receipt_id> <accepted_revision>`, where `<receipt_id>` and `<accepted_revision>` match `[A-Za-z0-9._:/@+-]{1,200}`.

  A receipt gives `invalid_dependency` when any of these holds: its `<reference>` is not a dependency item of the same file; a second receipt names the same reference; its keyword is neither of the two; it has the wrong token count; it is a coordination receipt on anything but a `brief:` reference; or it is a completion receipt on a captured-item reference. Field values are validated by the rules the engine already applies to `needs` receipts, with the same finding codes.
- [ ] **AC-0027.** When a resolution-index listing fails or is refused, or an entry the index admits cannot be read or is refused, every membership with a reference into that directory gets the existing `unreadable_artifact` finding and is not dispatchable. No such reference is treated as a missing target.
- [ ] **AC-0028.** In a finding or in `repair-apply` output, each part of an echoed value is judged on its own. A waiting path appears verbatim when it equals the `path` of a canonical membership, a dependency item when it matches the typed-reference or captured-item-reference grammar, and a receipt token when it passes AC-0004's validation for its position, including the engine's existing field rules AC-0004 incorporates. A part also needs at most 200 characters and no control character. A part that fails appears without its content, and the other parts of the same edge still appear. AC-0011's edge-set comparison and AC-0026's item comparison use the unredacted values.
- [ ] **AC-0005.** A canonical membership whose registry entry carries a non-empty `needs` array gets an `unmigrated_needs` finding naming its path, whose next action names `workspace-status repair-plan`. The membership is not dispatchable, whatever its `needs` content and its header say.
- [ ] **AC-0006.** For a cooled canonical membership, the reconciliation opens no part of the waiting item, and the membership contributes no header edge.
- [ ] **AC-0007.** Header edges between non-cooled local memberships that form a cycle give each member a `dependency_cycle` finding, as the same `needs` edges did.
- [ ] **AC-0008.** The legacy ready and blocked lists, and the `blocking_needs` of `explain` and of the MCP tools, treat each header edge of a canonical membership exactly as they treated the same typed `needs` edge at commit `1f9c27342`.
- [ ] **AC-0009.** `repair-plan` emits one `needs-to-header` operation for each non-cooled canonical membership with a non-empty typed `needs` array and no edge AC-0020 refuses. The operation names the waiting path and its SHA-256, the registry edges, and every `Depends on:` and `Dependency receipts:` item derived from those edges. Items already in the waiting item are skipped only at apply, under AC-0010.
- [ ] **AC-0019.** `repair-plan` writes no file other than its plan file.
- [ ] **AC-0020.** `repair-plan` reports a manual finding naming the edge, and emits no operation for its membership, for each of these edges: a target that is a brief or intent that does not exist, an intent file whose preamble has a `Tombstone:` field, or an intent with no `Slug:`; a captured-item target that carries a completion receipt; a local edge whose `kind` differs from its target's kind; a cross-repo edge whose `path` differs from its `containing_brief`; a receipt value outside AC-0004's grammar; a waiting path holding a control character; and any edge whose planned `Depends on:` and `Dependency receipts:` items do not re-parse under AC-0002 and AC-0004 to exactly that edge. A waiting item that is unreadable, outside the repository, or one AC-0030 would refuse to write is refused the same way.
- [ ] **AC-0029.** When the canonical findings hold `invalid_workspace` or `configuration_mismatch`, `repair-plan` emits no operation of any type, and no AC-0020 manual finding, overriding AC-0009, AC-0020, and AC-0021; its findings name that cause.
- [ ] **AC-0031.** The plan file holds, unredacted, every waiting path, item, and receipt that `repair-apply` writes or compares.
- [ ] **AC-0021.** For a cooled canonical membership with a non-empty typed `needs` array, `repair-plan` emits an operation that sets its `needs = []` without opening the waiting item, and lists its edges as `dropped_cooled`.
- [ ] **AC-0010.** `repair-apply`, given a confirmed plan, adds each operation's items to the waiting item's preamble, skipping any dependency item or receipt already there for the same reference, and then sets that entry's `needs = []`.
- [ ] **AC-0022.** `repair-apply` changes no byte of `workspace.toml` outside the migrated entries' `needs` arrays, and no line of a waiting item outside the `Depends on:` and `Dependency receipts:` lines it adds or extends.
- [ ] **AC-0023.** `repair-apply` refuses an operation whose waiting-file SHA-256 or registry fingerprint no longer matches the plan, and leaves that entry's `needs` unchanged.
- [ ] **AC-0025.** Under its lock, `repair-apply` refuses a `needs-drop-cooled` operation, and leaves that entry's `needs` unchanged, when the membership is no longer cooled or the cooled state cannot be read.
- [ ] **AC-0026.** `repair-apply` refuses a `needs-to-header` operation, and leaves that entry's `needs` unchanged, when its waiting path is not the `path` of a non-cooled canonical membership, or when its items differ from the items re-derived from that entry's current `needs`.
- [ ] **AC-0030.** `repair-apply` writes a waiting item only at that operation's path, and only when the path has no symbolic link in any segment and names a regular file inside the repository with exactly one link. Otherwise it refuses the operation and leaves that entry's `needs` unchanged.
- [ ] **AC-0024.** After an interrupted `repair-apply`, a rerun of `repair-plan` and `repair-apply` finishes the migration, and no waiting item holds any dependency item or receipt twice.
- [ ] **AC-0011.** `repair-apply` reports the header edges read before it writes, the registry edges other than `dropped_cooled` edges, and the header edges read back after. It exits non-zero when the read-back set differs from the union of the first two. An edge is its waiting path, its typed or captured-item reference, and its receipt.
- [ ] **AC-0012.** On this repository at the implementing pull request's head commit, no canonical membership carries a non-empty `needs` array. The header edges equal the typed `needs` edges of the registry the repair read, other than its `dropped_cooled` edges, plus only the edges AC-0013 adds.
- [ ] **AC-0013.** Each of the four registered Shipped specs that carried a free-text `Depends on:` line at commit `1f9c27342` carries only typed references in that line, with any remaining prose in a trailing HTML comment. Those specs are `agent-skill-engineering-consumer-integrations`, `design-handoff-read`, `claude-plugin-hook-parity`, and `frontend-experience-composition`.
- [ ] **AC-0014.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one row for each of these cases, under the criteria the amended `workspace-retirement` spec states for that section:
  - the coordination receipt;
  - the pruned target;
  - the pruned captured item settled by a completion receipt;
  - the defect;
  - the cooled dependency;
  - the cooled waiting item;
  - the brief child scope;
  - the dependency cycle;
  - the unmigrated `needs` refusal;
  - the `needs` edge migration.
- [ ] **AC-0015.** On this repository, `workspace-status status` run by this slice's engine over the tree after `repair-apply` reports the same `canonical.ready`, `canonical.active`, and `canonical.blocked` paths, the same canonical findings by code and path, and the same legacy ready and blocked lists as the engine at commit `1f9c27342` reports over the tree the repair read.
- [ ] **AC-0017.** On this repository after the migration, `navigate-intents query --operation dependencies` reports no fault-state diagnostic for any item the repair wrote.
- [ ] **AC-0016.** No Markdown file under `packs/*/.apm/`, `packs/*/seeds/`, or `guides/` holds a fenced `toml` block with a non-empty `needs` array, except `packs/core/.apm/skills/workspace-status/references/mutate.md`, which describes the repair's input.
- [ ] **AC-0018.** Each of these files names `Depends on:`:
  - `packs/core/.apm/skills/close-work/SKILL.md`, which also names `Dependency receipts:` as the place a completion receipt is kept and no longer says it is kept on the citing local need;
  - `packs/core/.apm/skills/workspace-status/SKILL.md`;
  - `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`;
  - `packs/core/.apm/skills/new-spec/assets/spec.md`;
  - `guides/core/reference/workspace-toml-schema.md`;
  - `guides/architect/how-to/establish-reference-architecture.md`;
  - `packs/architect/DESIGN.md`;
  - `docs/product/workspace-toml-deps.md`.

## Follow-ons

- The owner of the `entry.needs (string form)` Disposition row: the three legacy string edges on slug-only captured items move with the legacy-entry migration that row names.
- The owner of the `source.parent` Disposition row: `source.parent`, which decides a brief's child scope, stays a registry fact until spec registration stops.

## Assumptions

none
