# Plan: The readiness bridge reads work-loop's dispatch output

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0108 D3 and its errata; RFC-0105 D3's 2026-10-12 erratum; RFC-0106 D1 and D3; RFC-0055; ADR-0074.
  - `docs/specs/intent-view-readiness-handover/spec.md` and `plan.md`: the Shipped contract this spec amends, its terms, and its test and browser-check layout.
  - `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py`: `REASONS`, `_WORKSPACE_FAILURE_CODES`, `_typed_finding`, `_typed_list`, `_walk`, `check`, `start`, `project`.
  - `packs/core/.apm/skills/navigate-intents/scripts/view_src/readiness.js`, `labels.js`, `detail.js`: the page wording; `scripts/navigate_intents.py`: the `--readiness` help text.
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
| The bridge's input | T2, T4 | `intent_readiness.py`; SKILL.md and evals | AC-0001 to AC-0011, AC-0019, AC-0020 and AC-0031 pass |
| User procedure | T4 | the guide section | AC-0019 passes; guide lints pass |
| Current architecture | T4 | `packs/core/DESIGN.md` | AC-0021 passes |
| Page wording | T3 | `readiness.js`, `labels.js`, `detail.js` | AC-0012 to AC-0015, AC-0032 and AC-0033 pass |
| Help text | T2 | `navigate_intents.py`'s `--readiness` help | AC-0034 passes |
| Decision rationale | T5 | three errata entries and the § Equivalence row | AC-0022 to AC-0024 pass |
| Product truth and inventory | T6 | the hand-over header line; inventory rows | AC-0025 and AC-0026 pass |
| Verification record | T5, T6 | `notes/verification-ledger.md` | AC-0016 to AC-0018, AC-0027, AC-0029 and AC-0030 pass |
| Delivery membership | T1 | Spec map row | AC-0028 passes |

## Design (LLD)

### Interfaces & contracts

Owned by: T2

- `_walk` checks the exact key sets AC-0001 to AC-0003 name and returns `Checked(active, ready, blocked, findings, decision)`. `_typed_list` keeps the per-list rule that a `ready` or `active` item carries no finding, which every `dispatch.py` output meets because the engine's `dispatchable` requires an evaluation with no finding.
- The argless-decision check recomputes the decision from the checked `active` and `ready` paths in input order and compares it with the input's, so the mark can only name a spec the checked lists already hold. The only other decision admitted is the argless refusal, which `bad_workspace` then catches; a named invocation's output passes only when it equals the argless decision or an argless refusal, because the bridge reads argless dispatch only.
- `start` reads the checked decision; `held` stays in the start object for the payload's shape and is always `false`, because a finding naming the decided path, such as a blocked waiter's `unsatisfied_dependency`, does not stop `work-loop` acting on a checked `start` or `resume`.
- `REASONS` drops `no_workspace`; `_WORKSPACE_FAILURE_CODES` is unchanged and is also read in `decision.findings`.

### Behavior & rules

Owned by: T3

- The `ask` note splits on `active_count`, because `dispatch.py` asks over active specs first and over ready specs only when none is active. The `held` notes go with `held`.

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

- **Depends on:** T1; `spec-registration-stop` T1 and T2
- **Verification mode:** TDD
- **Tests:** for AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0031, AC-0034: a check in `test_export_readiness.py` that `export --help` shows AC-0034's `--readiness` text, red before `navigate_intents.py` changes; `test_export_readiness.py` rewritten to the base input of this spec's terms, with one planted case per AC-0001 to AC-0004 clause, including a path twice in `ready` and twice in `active`, including a blocked item with a `null` status that passes and a ready item with a finding that does not; the argless-refusal and named-output cases; the `bad_workspace` cases; the reason order; the fail-closed, `page_too_big` and over-budget cases over every failing input with the pinned clock; the marker-string case; the four marks, the `dep-spec-open` shape, and `ask` over two ready specs; the corpus test with the planted invalid-TOML tree; and the hand-built and fixture hostile inputs. The tests of the carried criteria in `test_export_readiness.py` (hand-over 0001 to 0008, 0014, 0015, 0018 to 0020, 0034 to 0036, 0046 and 0047) are rewritten to the base input and keep their assertions. `test_independence.py` runs unchanged.
- **Done when:** those suites pass.

### T3: Page wording

- **Depends on:** T2
- **Verification mode:** scripted browser check
- **Tests:** for AC-0012, AC-0013, AC-0014, AC-0015, AC-0032, AC-0033: `view_browser_checks.py`'s readiness cases with the new literals, the title, the empty state and the `outstanding`-unavailable count, the `ask` note for zero and non-zero `active_count`, every reason's notice, the checked and unchecked Key, the label and glyph sets over the `hostile` fixture, a search of the rendered text outside `next_action` and record text for `workspace-status`; and the shared readiness input builders and every carried readiness case (hand-over 0024, 0025, 0027, 0030, 0032, 0035 to 0037, 0039, 0040, and the record-owners readiness export) rewritten to the base input with their assertions kept, apart from the carried 0030 lead assertions in `view_browser_checks.py` (the checked lead and its unchecked sibling), which move to AC-0033's lead; the mark-help, Key and finding-help strings.
- **Done when:** the full `view_browser_checks.py` pass succeeds with none skipped.

### T4: Instructions, eval and design note

- **Depends on:** T2; `spec-registration-stop` T1
- **Verification mode:** goal-based
- **Tests:** for AC-0019, AC-0020, AC-0021: rows in `spec-registration-stop`'s roster test that read each named section and paragraph by its heading or opening words at the head and at `dfa3fe067`, and assert the banned tokens present at the base and absent at the head; the guide lints.
- **Done when:** those rows and the guide lints pass.

### T5: Governance wording

- **Depends on:** T1; `spec-registration-stop` T1
- **Verification mode:** goal-based
- **Tests:** for AC-0022, AC-0023, AC-0024, AC-0027: the roster rows for each errata entry and the § Equivalence row, and the ledger rows comparing each approval timestamp with `git log --format=%aI` of the commit that adds the text; the `workspace-retirement` check.
- **Done when:** each entry is committed with approved wording and its rows pass.

### T6: This repository and the records

- **Depends on:** T2, T3, T4, T5
- **Verification mode:** goal-based
- **Tests:** for AC-0016, AC-0017, AC-0018, AC-0025, AC-0026, AC-0029, AC-0030: the ledger's real-input run, scale benchmark, 4 MiB timing and real export counts; the full browser pass and the `test-corpus.yml` dispatch at the final code commit; the `experience-reviewer` pass over the four changed states; a `git diff` of the hand-over spec showing only the header line; the inventory check.
- **Done when:** the ledger holds each run and the inventory check passes.

## Rollout

- **Delivery:** ships in `spec-registration-stop`'s `core` patch release. A maintainer who still pipes `workspace-status status` sees readiness unchecked with the `wrong_schema` notice, which names the command to run.
- **Reversal:** revert the release with its paired spec.

## Risks

- A maintainer's saved pipe command breaks silently into an unchecked page. The `wrong_schema` notice and the SKILL.md command are the mitigation.

## Changelog

- 2026-10-29: spec and plan approved by eugenelim at `67addcade`.
- 2026-10-29: spec re-approved by eugenelim at `b1f1a0528` after the controlled amendment.
- 2026-10-29: plan re-approved by eugenelim at `b1f1a0528` after the controlled amendment.
- 2026-10-29: the approved spec and plan bytes of `67addcade` are those of the rebased `12f5a8fe8`, later `be25285e5`; the re-approved bytes of `b1f1a0528` are those of the rebased `e3e1b3200`.
- 2026-10-30: shipped in core 3.1.40 (#1656).
