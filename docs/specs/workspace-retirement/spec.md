# Spec: Workspace retirement record

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-25 by eugenelim, spec and plan; re-approved the same day after a controlled amendment (Never-do rule admits forced lifecycle moves; AC-0011 adds five legacy entry keys; T5 reopened; T6 added), clean on spec-mode shaping and adversarial review of the amendment; review records under `.context/reviews/`. Re-approved 2026-10-26 by eugenelim after a controlled amendment by the brief's slice 2 (AC-0023 to AC-0026 govern § Equivalence; AC-0018 and AC-0022 reopen; T7 added), clean on adversarial review; records under `.context/reviews/`. Re-approved 2026-10-26 by eugenelim after a controlled amendment by the brief's slice 3 (AC-0024 admits `intended change`; AC-0026 governs its Authority; AC-0027 and AC-0028 added; AC-0018 and AC-0022 reopen; T8 added), clean on adversarial review after three rounds; records under `.context/reviews/retirement-amendment-slice3/`. Re-approved 2026-10-27 by eugenelim after a controlled amendment by the brief's slice 3 registration stop (AC-0028 admits `the closed captured item of another kind`; AC-0018, AC-0022, and AC-0028 reopen; T9 added), after two rounds of adversarial review; records under `.context/reviews/retirement-amendment-registration-stop/`. Amended 2026-10-28 by the brief's slice 7 (AC-0028 admits `the child-state check on a brief that never had an entry` and `the cooled child of a brief that never had an entry`; AC-0018, AC-0022, and AC-0028 reopen; T10 added); re-approved by eugenelim the same day. Amended 2026-10-29 by eugenelim during `spec-registration-stop`: AC-0021 exempts a named contract that no longer mentions the registry, because AC-0006 then forbids its row; approval in `docs/specs/spec-registration-stop/notes/verification-ledger.md`. Amended 2026-10-30 by `pre-cutover-closure`: AC-0029 requires a numbered owner to be the brief's last slice, the four enforced-rule lists name it, and task T11 is added; re-approved by eugenelim the same day, approval in `docs/specs/pre-cutover-closure/notes/verification-ledger.md`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, the four retirement gates and the one retirement specification), RFC-0106 (D1, its responsibility table and the contracts to amend; D3, where residual facts live), RFC-0055 (errata entries on an Accepted RFC)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Contract:** none — the inventory file's shape is contracted by the criteria below and lives only in this spec's directory.
- **Shape:** data

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

The Platform Core maintainer gets one record that names every operative consumer of `workspace.toml` and `workspace-status`, and the home of every fact the registry holds, as RFC-0105 D3's first two gates require. Success is that a pull request fails its own check when it adds a registry mention that is neither in a finished brief or an Archived spec nor a source locator, in a file no inventory row names, or when it adds a registry fact with no named home.

## What Changes

- The consumer inventory — `docs/specs/workspace-retirement/inventory.toml`, one row per consumer, each a path pattern with a class.
- The retirement record — `docs/specs/workspace-retirement/retirement-record.md`, with four sections: Disposition, Equivalence, Compatibility closure, and Certification. This slice fills Disposition. Slice 2 of the brief adds the Equivalence criteria and its rows by amending this spec, slices 3, 7, and 8 add their rows under those criteria, and slice 9 completes the closure checklist and the certification by amending this spec.
- A repository check — `tests/roster/test_workspace_retirement_inventory.py`, run as a named step in `.github/workflows/build-check.yml` on every pull request.
- An errata entry on RFC-0106 — the accepted authority for removing behavior that lives only outside tracked files, which the repair does not carry over.
- This spec stays `Implementing` until the brief's slice 9 certifies all four gates.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth: which surfaces still depend on the registry | Applicable: RFC-0105 D3 names this record as the retirement gate evidence | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | The inventory check passes on the merge commit | `close-work` verifies the check step is green on the slice 9 retiring change |
| Decision rationale: where each registry fact goes, and the authority for each removal | Applicable: RFC-0105 D3 gate 2 | `docs/specs/workspace-retirement/retirement-record.md` § Disposition | Platform Core maintainer | AC-0011 to AC-0016 pass | Every removal row's authority resolves at closeout |
| Decision rationale: authority for dropping adopter-only behavior | Applicable: the no-seam owner decision in FEAT-0034 needs accepted authority | `docs/rfc/0106-stop-registering-derivable-work.md` § Errata | Platform Core maintainer, as RFC-0106 Approver | A dated errata entry that the record's removal rows link to | The entry exists and AC-0015 finds each removal's Fact text under it |
| Product truth: FEAT-0034's two open questions | Applicable: the brief's slice 1 settles them | `docs/product/intents/FEAT-0034-workspace-registry-retirement.md` § Unresolved questions | Platform Core maintainer | Each question is answered with a link to its inventory or Disposition rows | Both questions are answered |
| Product truth: whether brief coverage already reads only `Brief:` | Applicable: the brief's slice 8 depends on the answer | `retirement-record.md` § Disposition, the row for spec registration as coverage evidence | Platform Core maintainer | A row naming what is left to change, or `nothing`, with a link to the reader | The row exists |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and the spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Give each consumer the narrowest row AC-0005 allows. A row that names a whole skill or spec directory is the widest a consumer gets.
- Run the inventory check locally before pushing a change to the inventory or the record.
- Link a removal row only to a section that already names its Fact. The RFC-0106 errata entry follows Ask-first.

### Ask first

- Adding a class or a disposition category beyond the ones AC-0002 and AC-0013 list.
- Governing an Accepted RFC or ADR that states a current registry rule with a `historical` row instead of a `contract` row.
- Writing the RFC-0106 errata entry's wording. The Approver signs it.

### Never do

- Change how any registry reader or writer behaves. This slice records; later slices change behavior.
- Add a dependency. The check uses the Python 3.11 standard library only, including `tomllib`.
- Add a top-level directory, or put the inventory anywhere but this spec's directory.
- Edit `workspace.toml` beyond the lifecycle moves this spec's own status forces, where "forces" means `lint-brief-coverage.py` or `workspace-status`'s canonical reconciliation reports a finding without the move: this spec's own entry moved between collections, and the parent brief's entry moved together with the brief's `Status:` line, in either direction, each with the comment lines that annotate that entry and no other, where they sit directly above the entry or directly above the opening line of the collection that holds it.

## Testing Strategy

- **Inventory rules (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0019, AC-0021, AC-0029): TDD.** Each rule is a compressible invariant over a file list and a parsed TOML document, so a fixture repository with one planted violation per rule reds each test before the rule exists.
- **Record rules (AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028): TDD.** A fixture schema, registry, record, and RFC with one planted violation per rule red each test.
- **Per-pull-request wiring (AC-0017, AC-0022): goal-based.** A test reads the workflow file, and one run of the step on a checkout with a planted unrowed mention fails.
- **The real inventory and record (AC-0018): goal-based.** The same checks run against this repository and pass.

## Acceptance Criteria

Terms used below:

- **Mention.** A line that contains `workspace.toml`, `workspace-status`, or `workspace_status`.
- **Exempt path.** A brief whose status is terminal; a file at any depth under a `docs/specs/<feature>/` directory whose `spec.md` status is `Archived`; or a typed file, or a file at any depth under a `docs/specs/<feature>/` directory, in which every mention is a provenance line. A provenance line matches `^\s*-\s*(\*\*)?Locator:(\*\*)?\s`. A path that a row's `pattern` names exactly is never exempt. A Shipped spec's directory and a finished intent are not exempt, because each can still state a current registry rule.
- **Scanned set.** Every path `git ls-files` lists whose bytes decode as UTF-8, that holds a mention, and that is not an exempt path.
- **Governing row.** For a path, the first row in `inventory.toml` file order whose `pattern` matches the path under `fnmatch.fnmatchcase`.
- **Typed file.** A path matching `docs/product/intents/*.md` is an intent, `docs/product/briefs/*.md` a brief, and `docs/specs/*/spec.md` a spec. Its status is the leading word of its first `- **Status:**` line.
- **Classes.** `reader`, `writer`, `projection`, `fixture`, `seed`, `guide`, and `promise` are RFC-0105 D3 gate 1's consumer kinds. `contract` is a governance record or live artifact that states a current registry rule, and `workspace.toml` itself. `record` is a file in this spec's own directory. `historical` is a frozen record outside the exempt paths that states no current rule, such as a package changelog or an Accepted RFC that only cites the registry.
- **Skill directory.** A directory that holds a `SKILL.md`; a directory under `.claude/` or `.agents/` with the same final segment as one; or `packs/<pack>/tests/skills/<skill>` where `packs/<pack>/.apm/skills/<skill>` is one.
- **Spec directory.** A `docs/specs/<feature>` directory that holds a `spec.md`.
- **Fact text.** A Fact cell or a section's text with backtick code-span markers removed.
- **Case text.** A Case cell with backtick code-span markers removed.
- **Slice numbers.** The numbers of the numbered items under the brief's `## Delivery slices` heading.

Each criterion from AC-0001 to AC-0016, AC-0019, AC-0021, and AC-0023 to AC-0029 is a rule the check enforces: given an input that breaks it, the check fails and names the offending path, row, or fact.

- [x] **AC-0001.** `inventory.toml` parses with `tomllib` and holds a non-empty array of tables named `row`. Each row has a non-empty string `pattern`, a `class`, a non-empty string `consumer`, and an `owner`. A row may carry a boolean `reads_order`.
- [x] **AC-0002.** Every row's `class` is one of the ten classes.
- [x] **AC-0003.** Every row's `owner` is a slice number, or the string `none`. Only `historical` and `record` rows may carry `none`.
- [x] **AC-0029.** A row whose `owner` is a slice number has the highest of the slice numbers.
- [x] **AC-0004.** Every path in the scanned set has a governing row.
- [x] **AC-0005.** A row whose `pattern` holds `*`, `?`, or `[` has a `pattern` of the form `<prefix>/*`, where `<prefix>` holds no wildcard character and is either a skill directory, with a `class` other than `historical` and `record`, or a spec directory, with a `class` of `contract` or `historical`. Every other row's `pattern` is an exact path.
- [x] **AC-0019.** Every `record` row's `pattern` starts with `docs/specs/workspace-retirement/`.
- [x] **AC-0006.** Every row is the governing row of at least one path in the scanned set.
- [x] **AC-0007.** Every `projection` row carries a `source` string equal to the `pattern` of a row that is not `projection`. Every path in the scanned set that starts with `.claude/` or `.agents/` has a `projection` governing row.
- [x] **AC-0008.** No path whose governing row is `historical` is a typed file with a status outside its type's terminal set, as `close-work`'s `closure_terminality` decides it, or a file under a spec directory whose `spec.md` status is outside the spec terminal set. A typed file with no `- **Status:**` line under a `historical` row also fails.
- [x] **AC-0009.** The governing row of `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py` has a `consumer` containing `readiness bridge`.
- [x] **AC-0010.** `retirement-record.md` has exactly four `##` headings, in this order: `Disposition`, `Equivalence`, `Compatibility closure`, `Certification`.
- [x] **AC-0011.** § Disposition holds a Markdown table with the columns Fact, Category, Home, Owner, and Authority, and, for each member of the fact set, a row whose Fact text equals it. The fact set is:
  - every property of `contracts/jsonschema/workspace-entry.schema.json` reached through `properties` keys alone, not through `allOf`, `anyOf`, `oneOf`, `if`, `then`, or `not`, written `entry.<property>` for a top-level property and `<definition>.<property>` for a property of a `$defs` member, with nested object properties joined by `.`;
  - every key of this repository's `workspace.toml`, joined by `.`, stopping at a key whose value is an array, with each top-level table whose name matches `ini-[0-9]+` written `<initiative>`;
  - `entry position`, `spec registration as brief coverage evidence`, and `behavior outside tracked files`;
  - the legacy entry keys the schema does not reach: `entry.slug`, `entry.intent`, `entry.type`, `entry.source (string form)`, and `entry.needs (string form)`.
- [x] **AC-0012.** Every Disposition row has a non-empty Home and a non-empty Owner.
- [x] **AC-0013.** Every Disposition row's Category is one of RFC-0105 D3's five: `canonical artifact metadata`, `derived state`, `externally owned projection`, `temporary migration state`, or `deliberate removal`.
- [x] **AC-0014.** Every `deliberate removal` row's Authority cell holds one Markdown link that, resolved from the record's own directory, names a file under `docs/rfc/` or `docs/adr/` whose `- **Status:**` leading word is `Accepted`.
- [x] **AC-0015.** That link's anchor equals the GitHub heading slug of a heading in the target file, and the row's Fact text appears in the Fact text of the section under that heading, up to the next heading of the same or a higher level.
- [x] **AC-0016.** The Home cell of the `spec registration as brief coverage evidence` row names at least one path, resolved from the repository root, that `git ls-files` lists, or is exactly `nothing`.
- [x] **AC-0017.** `.github/workflows/build-check.yml` triggers on `pull_request`, and holds a step that runs `python -m pytest tests/roster/test_workspace_retirement_inventory.py`. Neither the step nor its job carries `continue-on-error:`. The job carries no `if:`, and the step's `if:`, when present, is exactly `!cancelled() && steps.python.conclusion == 'success'`, the condition its neighbouring roster steps use. The workflow carries no `paths` or `paths-ignore` filter.
- [x] **AC-0021.** The governing row of each contract RFC-0106 D1 names is a `contract` row: `docs/rfc/0064-ini-001-ai-native-ecosystem.md`, `docs/product/AGENTS.md`, `docs/product/intents/FEAT-0005-lifecycle-and-closure.md`, `docs/product/intents/FEAT-0001-intent-identity-and-registration.md`, and `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`, unless the file no longer mentions `workspace.toml`, `workspace-status` or `workspace_status`.
- [x] **AC-0022.** The step AC-0017 names applies every rule from AC-0001 to AC-0016, AC-0019, AC-0021, and AC-0023 to AC-0029 to the checked-out repository on every run. On a checkout where one tracked, non-exempt file that no row governs mentions `workspace.toml`, that step fails.
- [x] **AC-0023.** § Equivalence holds a Markdown table with the columns Case, Slice, Result, Evidence, and Authority, with at least one row.
- [x] **AC-0024.** Every Equivalence row's Slice is a slice number, and its Result is `reproduced`, `accepted removal`, or `intended change`.
- [x] **AC-0027.** Every Equivalence row's Case text is non-empty.
- [x] **AC-0028.** Every `intended change` row's Case text is one of these, and no other: `entries that carry no kind`, from RFC-0106 D3's kind assignment by the migration; `a captured-item file that carries a Type: line`, the change RFC-0106 D1 calls intended; `matches nothing else`, the limit D1 sets on that guard; `the closed captured item of another kind`, which RFC-0106 § Errata authorises: a captured item of any kind with no registry entry now settles a dependency when its own file is `Status: Closed` with `Resolution: fixed`; and `the child-state check on a brief that never had an entry` and `the cooled child of a brief that never had an entry`, which RFC-0106 § Errata authorises for the intent and brief registration stop. A further intended change needs an amendment of this list.
- [x] **AC-0025.** Every Equivalence row's Evidence cell names at least one path, resolved from the repository root, that `git ls-files` lists.
- [x] **AC-0026.** Every `accepted removal` or `intended change` row's Authority cell meets AC-0014 and AC-0015, with the row's Case text in place of the row's Fact text; the section side of AC-0015 is unchanged. Every `reproduced` row's Authority cell is exactly `none`.
- [x] **AC-0018.** Against this repository at the implementing pull request's head commit, the check passes every rule from AC-0001 to AC-0016, AC-0019, AC-0021, and AC-0023 to AC-0029.

## Follow-ons

- The brief's slices 3 and 8 add their Equivalence rows under AC-0023 to AC-0026.
- The brief's slice 9 amends this spec to add the compatibility-closure criteria and the certification, and then ships it.

## Assumptions

- **"The specification must contain" is read as "the specification's directory holds".** RFC-0105 D3 says the retirement specification contains the inventory, the disposition, the equivalence evidence, and the closure checklist. Here they sit in `inventory.toml` and `retirement-record.md` beside `spec.md`, so the contract stays readable. If the RFC's Approver reads it as `spec.md` itself, the record moves into this file. Who settles it: the RFC-0105 Approver, at spec approval.
