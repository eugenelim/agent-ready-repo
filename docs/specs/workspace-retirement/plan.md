# Plan: Workspace retirement record

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0105 D3.
  - RFC-0106 D1's responsibility table and § Errata.
  - RFC-0055 (errata on an Accepted RFC).
  - `contracts/jsonschema/workspace-entry.schema.json`.
  - `packs/core/.apm/skills/close-work/scripts/closure_terminality.py`: `is_intent_terminal`, `is_brief_terminal`, `is_spec_terminal`.
  - `tests/roster/test_brief_lifecycle_single_home.py`: a roster test that scans the repository from `tests/roster/`.
  - `.github/workflows/build-check.yml`: the step "pytest brief lifecycle single home (roster-owned)".
  - `tools/lint-ci-parity.py`: `_LOCAL_STEP_DISPOSITION` and the step-name list beside it.

## Approach

Build the check first, against fixtures, so each rule reds before the real inventory exists. Then fill the real inventory and record until the check passes on this repository. The check is the only thing that keeps the inventory closed while slices 2 to 9 run, so it ships in the same pull request as the record it guards.

## Constraints

- Standard library only. `tomllib` needs Python 3.11, which is the version `build-check.yml` pins.
- The check reads the repository and writes nothing.
- A roster test may not import from a pack's `.apm/` tree, except by path. It loads `closure_terminality.py` by file path under a unique module name, as `close-work`'s other parity tests do, so the terminal sets have one home.

## Construction tests

Each task's `Tests:` lists the checks. Every fixture is built in `tmp_path` by the test that uses it; nothing is committed under `tests/roster/fixtures/`.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| `inventory.toml` | T3 |
| `retirement-record.md` § Disposition | T4 |
| RFC-0106 errata entry | T4 |
| FEAT-0034 open questions | T5 |
| Brief coverage answer | T4 |
| Delivery membership | T5 |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T4

- **A TOML inventory beside the spec, not a table in `spec.md`.** Every live consumer outside a skill directory, and every RFC, ADR, or other untyped file under the governance roots, takes its own exact-path row, so the file runs to a few hundred rows. A parsed file keeps the check simple.
- **First match governs, and breadth is capped.** `fnmatch.fnmatchcase` lets `*` cross `/`, so AC-0005 lets a wildcard cover one skill directory or one spec directory and nothing wider, such as `packs/core/.apm/skills/work-loop/*`, `.claude/skills/workspace-status/*`, or `docs/specs/workspace-mcp/*`. Every other row is an exact path. Each Shipped spec directory that mentions the registry takes one directory row, classed `contract` when the spec states a current registry rule and `historical` when it names the registry only as history; AC-0008 keeps a live spec's directory out of `historical`. Each finished or live intent that discusses the registry takes an exact row. Terminal briefs, Archived spec directories, and files whose only mentions are source locators are exempt by rule. A path an exact row names stays scanned whatever its status, so FEAT-0001, which is Fulfilled but still states the rename lockstep RFC-0106 D1 names, keeps its `contract` row. A new mention inside a directory a row already names passes. That is accepted, because that directory's consumer is already inventoried and owned. On 2026-10-25 the rule exempts 72 of the 1,112 files that mention the registry (44 locator-only, 25 in Archived spec directories, 3 terminal briefs), leaving 1,042 scanned, of which 506 sit in 264 Shipped spec directories. These counts illustrate the layout; the check recomputes the sets on every run.
- **List-order readers carry `reads_order = true`.** That gives FEAT-0034's first open question a home in the inventory. The `entry position` Disposition row's Home lists those consumers.
- **Removal authority is an RFC-0106 errata entry.** The entry names each dropped behavior in the words of its Fact cell, `entry position` included, so AC-0015 finds the text under `## Errata` (slug `errata`). Only a row whose Fact text already appears in RFC-0106 D3, such as `next_queue`, links to `#d3--per-item-homes-for-what-headers-cannot-yet-supply` instead.
- **The GitHub slug rule.** Lowercase the heading text, drop every character that is not a letter, digit, underscore, space, or hyphen, and replace each space with a hyphen. Underscores stay, so a heading naming `next_queue` slugs to `next_queue`.

### Data & schema

Owned by: T1, T3

`inventory.toml`:

```toml
[[row]]
pattern = "packs/core/.apm/skills/workspace-status/*"
class = "reader"
consumer = "workspace-status skill and its engine"
owner = 9
reads_order = true

[[row]]
pattern = ".claude/skills/workspace-status/*"
class = "projection"
consumer = "generated Claude Code projection of workspace-status"
source = "packs/core/.apm/skills/workspace-status/*"
owner = 9
```

### Failure, edge cases & resilience

Owned by: T1

- A file that does not decode as UTF-8 is outside the scanned set. Binary files cannot carry a consumer reference that matters here.
- The check reads `git ls-files`, so untracked scratch under `.context/` is never scanned.
- An unparseable `inventory.toml`, a missing record file, or a missing brief fails the check with the cause named, never a silent pass.

## Tasks

### T1: The inventory rules, against fixtures

**Depends on:** none

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0019, AC-0021.
- Every rule reports a violation tagged with its criterion identifier, and every fixture test asserts that the tag it expects is the only one reported.
- `test_workspace_retirement_inventory.py` takes the repository root, the inventory path, the record path, and the brief path as parameters, so the fixture tests and the real-repository test share one code path.
- Each fixture is a small Git repository built in `tmp_path` by `git init` and `git add`, with exactly one planted violation. AC-0005's fixtures plant a `*` row, a `packs/core/.apm/skills/*` reader row, and a `guides/*` `guide` row, each over a file a later exact row also names, so only AC-0005 fires; its controls are a `packs/core/.apm/skills/workspace-status/*` row and an exact-path `historical` row for a changelog, both passing. AC-0019's fixture plants an exact-path `record` row outside the spec directory. AC-0021's fixture governs `docs/product/AGENTS.md` with a `guide` row. AC-0006's fixture plants a row that an earlier row shadows. AC-0008's fixture plants a Draft spec, with a mention outside any locator line, under an exact-path `historical` row; a control puts a `contract` row for that spec ahead of it, and passes. An AC-0021 control names a Fulfilled intent with an exact `contract` row and passes. The exempt-path fixtures plant a Draft intent whose only mention is `- Locator: workspace.toml` with no row, and an Archived spec's `notes/` file with no row, both passing; and a Shipped spec and a Draft spec, each with one mention outside a locator line and no row, each failing AC-0004. AC-0005's spec-directory control is a `docs/specs/<feature>/*` `historical` row over a Shipped spec, passing; AC-0008's spec-directory case is the same row over a Draft spec's `plan.md`, failing.
- The terminal-set test loads `closure_terminality.py` by path, and asserts that a spec whose status is `Shipped (2026-09-11)` counts as terminal.

**Done when:** each fixture test reds before its rule exists and passes after.

### T2: The record rules, against fixtures

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016.
- The fixtures plant each violation: a record with a missing heading, a record with two headings out of order, a fact with no row, a schema property reached only through `allOf` that the check must not require, a `$defs` property written without its definition name, an `ini-099` table not written as `<initiative>`, a sixth category, an empty Home, an empty Owner, a removal link to a `Draft` RFC, a link to `#errata` when the Errata section does not name the fact, a link to a heading containing `_` whose anchor drops it, and a coverage row whose Home is prose.

**Done when:** each fixture test reds before its rule exists and passes after.

### T3: The real inventory

**Depends on:** T1

**Mode:** goal-based

**Tests:**
- Criteria: AC-0018, for AC-0001 to AC-0009, AC-0019, and AC-0021.
- Run the check against this repository and add rows until it passes. Mark each consumer that reads list order with `reads_order = true`.

**Done when:** the real-repository inventory tests pass at the pull request's head commit.

### T4: The real record and the errata entry

**Depends on:** T2, T3

**Mode:** goal-based

**Tests:**
- Criteria: AC-0018, for AC-0010 to AC-0016.
- Draft the RFC-0106 errata entry, and ask the Approver to sign its wording (spec Ask-first).
- The coverage row names what is left to change in `author-delivery-brief` and `lint-brief-coverage.py`, or reads `nothing`.

**Done when:** the real-repository record tests pass, and the errata entry carries the Approver's sign-off.

### T5: Wiring, lifecycle memberships, and FEAT-0034

**Depends on:** T3, T4

**Mode:** goal-based

**Tests:**
- Criteria: AC-0017, AC-0022.
- Add the build-check step "pytest workspace retirement inventory (roster-owned)" next to the brief-lifecycle step. Register it in `tools/lint-ci-parity.py` with `LOCAL("test-after-build-check")`.
- `python3 tools/lint-ci-parity.py` passes.
- With no arguments, `test_workspace_retirement_inventory.py` runs the real-repository check on the checkout as collected tests with no skip condition, so a missing or unreadable inventory, record, or brief fails the step with its AC-0001, AC-0010, or input violation. A goal-based run adds an unrowed, non-exempt file, `tools/planted_mention.py`, that mentions `workspace.toml` to a scratch clone and confirms the step fails.
- Every `docs/specs/<slug>` literal in the new roster test is listed in `.workspace-prune-protected.toml`, and `tests/roster/test_two_sided_prune_closure_invariant.py` passes.
- While this spec is `Implementing`, its `workspace.toml` entry sits in `work.active` and the parent brief is `Status: Executing` with its entry in `brief_queue.executing`. `lint-brief-coverage.py` passes, and `workspace-status` reports no finding for either path.
- Answer FEAT-0034's two open questions with links to the `reads_order` rows and the Disposition rows.

**Done when:** the wiring test passes; the real-repository tests collect with no skip condition; the planted-mention run fails the step; `lint-ci-parity`, the prune-closure roster test, and `lint-brief-coverage.py` pass; `workspace-status` reports no finding for the spec or brief path; and FEAT-0034 § Unresolved questions links both answers.

### T6: Legacy entry facts in the record

**Depends on:** T5

**Mode:** TDD

**Tests:**
- Criteria: AC-0011, AC-0018.
- The fact-set function adds the five legacy literals AC-0011's last bullet names, and a fixture record missing the `entry.slug` row reports AC-0011 naming `entry.slug` and nothing else.
- The real record carries a Disposition row for each of the five, with a Category, Home, and Owner.
- A legacy key classed `deliberate removal` has its Fact text added to the RFC-0106 errata entry under a fresh Approver sign-off (spec Ask-first) before its row lands.

**Done when:** the fixture test reds before the fact-set change and passes after, the real-repository record test passes, and any text added to the errata entry carries the Approver's sign-off.

## Rollout

- **Delivery:** one pull request. The check blocks a pull request that adds a registry mention outside an inventoried directory, and one that removes, renames, or deletes the last mention in a file a row names.
- **Reversal:** remove the build-check step.

## Risks

- **The inventory is large.** Design decisions bullet 2 gives the dated counts. Most scanned files sit under one skill-directory or spec-directory row, but each of the 264 Shipped spec directories needs a `contract` or `historical` judgement in T3.
- **The check could block unrelated work.** A new mention outside every inventoried skill or spec directory needs one exact row per file. That includes an intent or brief that discusses the registry beyond its source locator. A new spec directory that discusses it costs one directory row. Dropping the last mention from a file, or renaming or deleting it, fails until its row is edited or removed, and each later slice of the brief hits that case. A status change to terminal does not fail the check for an exact row, because an exactly named path stays scanned. Archiving a Shipped spec does fail it: the directory becomes exempt, so its `docs/specs/<feature>/*` row governs nothing until the archiving change deletes that row. The slice that owns a row removes it when that slice ships. Either failure names the file and the inventory path.

## Changelog

- 2026-10-25: spec approved by eugenelim
- 2026-10-25: plan approved by eugenelim
- 2026-10-25: spec amendment approved by eugenelim (Never-do rule admits the lifecycle moves the spec's status forces; AC-0011 fact set adds five legacy entry keys)
- 2026-10-25: plan amendment approved by eugenelim (T5 reopened and rewritten; T6 added)
