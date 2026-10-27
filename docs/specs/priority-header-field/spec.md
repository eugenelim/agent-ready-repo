# Spec: Priority header field

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D3, a human priority is a header field on the item, never a position in a shared list), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the field grammar is contracted by the criteria below.
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

A maintainer who wants a tracker sync to send this repository's own priority writes one `Priority:` line, `urgent`, `high`, `medium`, or `low`, on the intent, brief, spec, or captured item itself, and an item with no line has no priority. Success is that one reader validates the line on all four types in `make build-check`, and that changing only priority lines never changes what `workspace-status` reports as ready, active, or blocked, or what `navigate-intents` lists as outstanding.

## What Changes

- The `Priority:` preamble field on intents, briefs, specs, and captured items — the files themselves.
- Its reader and lint — a new `packs/core/.apm/skills/work-loop/scripts/lint-priority-field.py`, run by `make build-check` and named in `work-loop`'s finish checklist.
- A static guard that no dispatch, readiness, or navigation module reads the field — `tests/roster/`; an invariance test over `workspace-status` and `navigate-intents` — `packs/core/tests/skills/workspace-status/`.
- The field's documentation — the spec metadata contract, the intent field reference, `work-intake`'s captured-item file shape, and the delivery-brief skill.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the field grammar authors write | Applicable: a new published preamble field | `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md` § Spec metadata contract, `guides/product-engineering/reference/intent-fields-and-modes.md` § Intent fields, `packs/core/.apm/skills/work-intake/references/lifecycle-index.md` (the captured-item file shape), and `packs/core/.apm/skills/author-delivery-brief/SKILL.md` | Platform Core maintainer | AC-0008 passes | Each surface names the four values, that an absent line means no priority, and that the field never decides readiness, dispatch, or order |
| Maintainer procedure: running the lint | Applicable: adopters run it from a skill step | `packs/core/.apm/skills/work-loop/SKILL.md` finish checklist | Platform Core maintainer | The checklist names the command and its exit codes | The bullet is present |
| Current product truth: the inventory | Applicable: this spec names `workspace.toml` | `docs/specs/workspace-retirement/inventory.toml`, one `docs/specs/priority-header-field/*` contract row, owner 4 | Platform Core maintainer | `test_workspace_retirement_inventory.py` passes | The row is present |
| Release history | Applicable: shipped `core` behavior changes | a `docs/product/changelog.d/` fragment, with `core`'s `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog gate passes | The fragment names the field and the lint |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read every artifact through the co-located `_file_safety.py` confinement helpers, as `lint-graph-pointers.py` does.
- Keep the value set in one place: the lint's own constant. Every documentation surface and test reads or pins that constant.
- Regenerate the packaged copies with `make build-self` and bump `core`'s version.

### Ask first

- Adding a value to the vocabulary, or accepting a second spelling of one.
- Adding a carrier type beyond intents, briefs, specs, and captured items.
- Writing a `Priority:` line on any existing artifact in this repository.

### Never do

- Let any module that decides readiness, dispatch, order, or outstanding work read the field: the `workspace-status`, `work-loop`, `navigate-intents`, and `close-work` scripts, and the packaged engine copy. The lint is the only reader.
- Change `navigate-intents`, `workspace-status`, or the shipped `captured-item-files` criteria. This spec adds a field those surfaces ignore.
- Add a dependency, a second vocabulary copy, or a top-level directory.

## Testing Strategy

- **Field grammar, refusals, and the reader (AC-0001, AC-0002, AC-0003, AC-0004):** TDD, because the rules are a small closed predicate over preamble text, tested against fixture trees.
- **Gate wiring and the clean corpus (AC-0005):** goal-based check, because the gate chain step and one run over this repository decide it.
- **Never decides order (AC-0006, AC-0007):** a static roster guard over shipped source, plus an integration test that runs `workspace-status status` and `navigate-intents query --operation outstanding` over one fixture corpus before and after priority lines are added, with values set against the existing order so a priority sort would show.
- **Documentation (AC-0008):** goal-based check, a roster test that pins each surface to the lint's value set.

## Acceptance Criteria

- [ ] **AC-0001.** `lint-priority-field.py --root DIR` reads four carrier types: each file directly in `docs/product/intents/` or `docs/product/briefs/` whose name matches `^[A-Za-z0-9][A-Za-z0-9._-]*\.md$`; each `docs/specs/<dir>/spec.md` whose `<dir>` matches `^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$`; and each captured-item file, as the `captured-item-files` spec's Terms define it. Every other entry is ignored. In each carrier's preamble, using the `depends-on-headers` spec's Preamble and Field value terms, a `- **Priority:**` line is valid when its field value is exactly `urgent`, `high`, `medium`, or `low`. An item with no such line, or one whose field value is empty, has no priority and is valid.
- [ ] **AC-0002.** Each item gives at most one violation. Two or more `Priority:` lines give `duplicate_priority`, whatever their values. One line with any other value gives `invalid_priority`. Each violation prints one stdout line of exactly `<path>: <code>`, where `<path>` is the item's repository-relative path. Once its arguments parse and the check starts, the lint prints no line other than these and AC-0004's refusal line. With no refusal, any violation makes the lint exit 1 and none makes it exit 0.
- [ ] **AC-0003.** `read_priority(text)` in the same script returns the item's priority value, or `None` when it has none, and raises `PriorityError` carrying the one code AC-0002 assigns. The lint decides each item through this function alone.
- [ ] **AC-0004.** The lint exits 2, whatever violations it found, and prints one stderr line of exactly `<code>: <path>`, where `<path>` is the repository-relative file or carrier directory, and prints nothing on stdout, when a carrier file or directory is a symlink or not a regular file or directory, when a carrier file is not UTF-8, or when a walk bound is exceeded. The bounds are `lint-graph-pointers.py`'s: entries seen per walk (`MAX_ENTRIES`), carrier files (`MAX_FILES`), directory depth (`MAX_DEPTH`), bytes in one file (`MAX_ARTIFACT_BYTES`), and bytes across all files (`MAX_AGGREGATE_BYTES`). A missing carrier directory is not a refusal.
- [ ] **AC-0005.** `make build-check` runs the lint over this repository with `--root .`, and that run exits 0.
- [ ] **AC-0006.** No string constant contains `Priority` as a whole word, or the file name `lint-priority-field`, in any Python module under `packs/core/.apm/skills/{workspace-status,work-loop,navigate-intents,close-work}/scripts/` other than `lint-priority-field.py` itself, or in any `packages/agentbundle/agentbundle/_data/*.py` file that shares a name with one of those modules.
- [ ] **AC-0007.** A fixture corpus gives `workspace-status status` at least two items in each of `canonical.ready`, `shaping.ready`, and `captured.items` and at least one in each of `canonical.active` and `canonical.blocked`, and gives `navigate-intents query --operation outstanding` at least two intents. `Priority:` lines are then added to carrier files in the same root. Every value appears at least once, every carrier type carries at least one line, and in each of three orders the first item gets `low` and the last gets `urgent`: the specs of `canonical.ready`, the files of `captured.items`, and the intents of the outstanding result, each in output order. The whole `status` output is byte-equal before and after, and the whole `outstanding` output is equal apart from its `generated_at` value.
- [ ] **AC-0008.** Each surface in the Durable Outputs interface-compatibility row names all four values in the lint's order, says that an item with no line has no priority, and says the field never decides readiness, dispatch, or order of work.

## Assumptions

none

## Follow-ons

- A tracker sync reading the field belongs to [External tracker projection](../../product/intents/CAP-0004-external-tracker-projection.md), which maps the four values to each tracker's own priority field.
