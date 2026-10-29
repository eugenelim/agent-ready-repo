# Plan: The readiness bridge reads work-loop's dispatch output

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0108 D3 and its errata; RFC-0105 D3's 2026-10-12 erratum; RFC-0106 D1 and D3; RFC-0055; ADR-0074.
  - `docs/specs/intent-view-readiness-handover/spec.md` and `plan.md`: the Shipped contract this spec amends, its terms, and its test and browser-check layout.
  - `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py`: `REASONS`, `_WORKSPACE_FAILURE_CODES`, `_typed_finding`, `_typed_list`, `_walk`, `check`, `start`, `project`.
  - `packs/core/.apm/skills/navigate-intents/scripts/view_src/readiness.js`, `labels.js`, `detail.js`: the page wording.
  - `packs/core/tests/skills/navigate-intents/test_export_readiness.py`, `test_independence.py`, `view_browser_checks.py`, `view_bench.py`, and `fixtures/hostile_workspace/`.
  - `packs/core/.apm/skills/work-loop/scripts/dispatch.py` (the argless decision, lines 474–485) and `packs/core/tests/skills/work-loop/test_header_derived_dispatch_replay.py` (its case-tree builder).
  - `docs/specs/spec-registration-stop/`: the paired spec, built on the same branch, whose criterion 0034 names this spec's inventory rows and whose criterion 0044 pairs the release.

## Approach

Checks first, wording second, records last. T2 rewrites the input checks and the mark against `dispatch.py`'s shape, because every later task reads a checked member. T3 changes the page wording and its browser checks. T4 changes the instructions, eval and design note. T5 commits governance wording after the owner approves each. T6 runs this repository's real-input checks, writes the records, and disposes the bridge's inventory rows.

## Constraints

- Standard library only in `intent_readiness.py`; no new module or script part; no import from another skill. Tests load `dispatch.py` and the replay builder by unique module name.
- The shipped content-security policy string keeps its form; only its digests change.
- `make build-self` reprojects the skill into `.claude/skills/` and `.agents/skills/`; projections are never hand-edited.
- `core` takes the one patch bump `spec-registration-stop` takes, and the eval file gains a case.
- An accepted RFC changes through § Errata (RFC-0055); the hand-over spec gains only its `Amended in part by:` header line.
- The spec and its Spec-map row are added together; the brief stays `Executing`.

## Construction tests

- **Corpus (T2):** the suite builds each replay case tree through the replay module's builder, runs `dispatch.py --root <tree>`, and feeds its stdout to `intent_readiness.member` with a `path_to_id` from the tree's spec files.
- **This repository (T6):** a ledger-recorded script reads `dispatch.py --root .` stdout and computes the counts and start by this spec's terms; the export over the same bytes is compared with it.
- **Manual verification:** the owner's errata approvals (T5) are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| The bridge's input | T2, T4 | `intent_readiness.py`; SKILL.md and evals | AC-0001 to AC-0011, AC-0019, AC-0020 pass |
| User procedure | T4 | the guide section | AC-0019 passes; guide lints pass |
| Current architecture | T4 | `packs/core/DESIGN.md` | AC-0021 passes |
| Page wording | T3 | `readiness.js`, `labels.js`, `detail.js` | AC-0012 to AC-0015 pass |
| Decision rationale | T5 | three errata entries and the § Equivalence row | AC-0022 to AC-0024 pass |
| Product truth and inventory | T6 | the hand-over header line; inventory rows | AC-0025 and AC-0026 pass |
| Verification record | T5, T6 | `notes/verification-ledger.md` | AC-0016 to AC-0018 and AC-0027 pass |
| Delivery membership | T1 | Spec map row | AC-0028 passes |

## Design (LLD)

### Interfaces & contracts

Owned by: T2

- `_walk` checks the exact key sets AC-0001 to AC-0003 name and returns `Checked(active, ready, blocked, findings, decision)`. `_typed_list` keeps the per-list rules that still hold: an `active` item carries no finding; a `ready` item may carry findings, because `dispatch.py` lists every dispatchable queue spec.
- The argless-decision check recomputes the decision from the checked `active` and `ready` paths in input order and compares it with the input's, so the mark can only name a spec the checked lists already hold.
- `start` reads the checked decision; `held` keeps today's rule over top-level and item findings.
- `REASONS` drops `no_workspace`; `_WORKSPACE_FAILURE_CODES` is unchanged, and `refuse` joins it as a `bad_workspace` cause.

### Behavior & rules

Owned by: T3

- The `ask` note splits on `active_count`, because `dispatch.py` asks over active specs first and over ready specs only when none is active.

### Dependencies & integration

Owned by: T6

- Inventory rows this spec disposes: the `navigate-intents` skill, test and projection rows, `intent_readiness.py`, `guides/core/how-to/navigate-intents.md` and `docs/rfc/0108-skill-html-view-standard.md` move to owner `9`, with consumer text naming `dispatch.py`'s output, which still loads the `workspace-status` engine; `docs/specs/intent-navigation/*` and `docs/specs/intent-navigation-export/*` become `historical`, owner `none`; `docs/specs/intent-view-readiness-handover/*` stays `contract` at owner `9`, because its carried criteria stay live.

## Tasks

### T1: Spec map and inventory row

- **Depends on:** none
- **Verification mode:** goal-based
- **Tests:** for AC-0028: the Spec map row, this spec's `docs/specs/readiness-bridge-dispatch-input/*` `contract` row at owner `8`, `lint-brief-coverage.py`, and the inventory check.
- **Done when:** the coverage lint and the inventory check pass.

### T2: Input checks and the mark

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011: `test_export_readiness.py` rewritten to the base input of this spec's terms, with one planted case per AC-0001 to AC-0004 clause, including a `null` status and a ready item with a finding that pass; the `bad_workspace` cases; the reason order; the fail-closed and budget cases over every failing input; the marker-string case; the four marks and `ask` over two ready specs; the corpus test; and the hand-built and fixture hostile inputs. `test_independence.py` runs unchanged.
- **Done when:** those suites pass.

### T3: Page wording

- **Depends on:** T2
- **Verification mode:** scripted browser check
- **Tests:** for AC-0012, AC-0013, AC-0014, AC-0015: `view_browser_checks.py`'s readiness cases with the new literals, the `ask` note for zero and non-zero `active_count`, every reason's notice, the Key, the label set, and a search of the rendered text for `workspace-status`.
- **Done when:** the full browser pass, with none skipped, is in the ledger.

### T4: Instructions, eval and design note

- **Depends on:** T2
- **Verification mode:** goal-based
- **Tests:** for AC-0019, AC-0020, AC-0021: the roster rows `spec-registration-stop`'s roster test holds for this spec's phrase lists, with each banned phrase's presence at the base asserted from `git show dfa3fe067:<path>`; the guide lints.
- **Done when:** those rows and the guide lints pass.

### T5: Governance wording

- **Depends on:** T1
- **Verification mode:** goal-based
- **Tests:** for AC-0022, AC-0023, AC-0024, AC-0027: the roster rows for each errata entry and the § Equivalence row, and the ledger rows comparing each approval timestamp with `git log --format=%aI` of the commit that adds the text; the `workspace-retirement` check.
- **Done when:** each entry is committed with approved wording and its rows pass.

### T6: This repository and the records

- **Depends on:** T2, T3, T4, T5
- **Verification mode:** goal-based
- **Tests:** for AC-0016, AC-0017, AC-0018, AC-0025, AC-0026: the ledger's real-input run, scale benchmark and real export counts; a `git diff` of the hand-over spec showing only the header line; the inventory check.
- **Done when:** the ledger holds each run and the inventory check passes.

## Rollout

- **Delivery:** ships in `spec-registration-stop`'s `core` patch release. A maintainer who still pipes `workspace-status status` sees readiness unchecked with the `wrong_schema` notice, which names the command to run.
- **Reversal:** revert the release with its paired spec.

## Risks

- A maintainer's saved pipe command breaks silently into an unchecked page. The `wrong_schema` notice and the SKILL.md command are the mitigation.

## Changelog

- Drafted 2026-10-29.
