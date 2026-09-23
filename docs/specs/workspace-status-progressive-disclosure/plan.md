# Plan: workspace-status progressive disclosure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - `guides/_shared/how-to/author-a-skill.md` — the line budget, the
    progressive-disclosure pattern, and the skill-relative reference rule
  - `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py` —
    the mechanical form of those rules, as CAT-S003 and the blessed-subdirectory
    set
  - `packs/AGENTS.md`, `packs/AGENTS.local.md` — the export boundary, the
    version-bump rule, the portability rule, and the release pipeline
  - `tests/AGENTS.md` — the roster-step placement obligations, one of which this
    delivery corrects
  - Analogous implementation: `packs/core/.apm/skills/work-loop/` — the same
    dispatcher-plus-references shape, pinned by
    `tests/roster/test_wave4_durable_outputs_and_release.py::test_work_loop_keeps_detail_in_a_linked_reference`
  - Analogous implementation: `packs/file-to-markdown/` — the routing model the
    authoring guide names, where the body loads exactly one strategy reference

## Approach

Relocate prose without rewriting it, then pin the resulting shape.

The delivery is a move, not an edit. Every sentence that leaves `SKILL.md`
arrives in a reference file with its bytes unchanged, which is what lets the six
existing pin-holding suites act as the conservation check: a pin that stays in
`SKILL.md` proves the sentence did not travel, and a pin retargeted to a
reference proves it arrived intact. Only one pin is retargeted, and it is the
one whose content this spec deliberately moves.

The shape is then pinned by a new roster test, because nothing today stops the
body growing back. The repository already has this test for `work-loop`; this
adds its sibling.

## Constraints

- The four backend scripts are out of bounds. This delivery contains no Python
  behavior change, so any red in the backend suites is a pre-existing failure,
  not this work.
- `packs/core/.apm/` is the source of truth. The `.claude/` and `.agents/`
  copies are regenerated, never hand-edited, and their byte equality with the
  source is already gated.
- The roster suite is not run locally. It costs about fifteen minutes and at
  least one case reads the live working tree, so a local run reds a clean tree
  for a peer worker. Roster evidence comes from a CI dispatch.
- Shipped pack content stays portable: no RFC or ADR ordinal, no acceptance
  criterion number, no `docs/` repository path inside the new files.

## Construction tests

One new test module carries this delivery's criteria:
`tests/roster/test_workspace_status_progressive_disclosure.py`.

It is roster-owned rather than pack-owned because AC-0004 and AC-0005 read the
backend source alongside the skill body, and AC-0009 reads
`.github/workflows/build-check.yml` and `tests/AGENTS.md` — all outside any
single pack's test reach under `tools/lint-pack-test-boundary.py`. AC-0008's
digest comparison and the three content pins are cheap enough to be assertions
in the same module rather than a second suite.

Three expected sets are derived from the artifact under test at run time, never
hard-coded: the backend's `_SUBCOMMANDS` literal for AC-0004, the
`_prune_error` call sites for AC-0005, and the workflow's `if:` guards for
AC-0009. A hard-coded copy stays green after the source grows a ninth
subcommand or a tenth refusal code, which is the regression these criteria
exist to catch. AC-0008 is the deliberate exception: its four digests are fixed
in the contract precisely because a derived baseline would agree with whatever
the tree currently holds.

## Durable-output map

| Spec durable output | Tasks | Evidence the task produces |
| --- | --- | --- |
| Maintainer procedure — skill body and references | T2, T3, T4, T5 | The new module green on AC-0001 through AC-0007 |
| Maintainer procedure — `tests/AGENTS.md` | T6 | The new module green on AC-0009, plus its placement-instruction content pin |
| Interface compatibility — backend unchanged | T1, T7 | AC-0008's four digests matched at start and at close, recorded in the ledger |
| Release history | T8 | The changelog entry and its recorded Highlights decision |

## Design (LLD)

### Design decisions

Owned by: T2, T3, T4

**The body keeps what every mode needs; a reference takes what one mode needs.**
This is the split the authoring guide describes, and it decides each section
mechanically rather than by taste. The canonical-findings table and the status
rendering contract are read on every orientation, so they stay. The prune
authority flow is read only when the agent is about to mutate, so it goes. The
coordination-receipts section reads as orientation material because the
findings table names its finding code, but what it actually contains is how to
author a receipt and recover from a bad one — remediation for one code, reached
only after reconciliation reports it, so it goes too.

**One safety line does not follow its detail into the reference.** The consent
requirement for the mutating subcommands stays in the body's `Never` section
even though its procedure moves. A guard that is only in context once the agent
has already decided to mutate is guarding the wrong moment. The cost is two
lines of the body's budget.

**The refusal-code control moves with its content, and keeps its derivation.**
The existing control finds an anchor sentence, reads the bullet list beneath it,
and asserts every refusal code the prune source emits appears there. Retargeting
changes the file it opens and nothing else, and the anchor sentence travels
verbatim so the control still finds it.

Two failure modes are distinct here and the plan treats them separately. A
missing anchor already fails loudly — the control asserts the anchor is present
before it slices anything, with the message that it cannot otherwise bound
itself — so relocation cannot silently disarm it that way. What a green run
against the real tree does not establish is the other half: that the comparison
between the emitted codes and the documented list can still fail at all in the
new file. Mutation proof is for that half.

**The initialisation template becomes an asset, not a fourth reference.**
`assets/` is a blessed subdirectory and the template is literally a file the
skill writes. Putting it in `references/` would say it is something an agent
reads to decide, which it is not.

### Component / module decomposition

Owned by: T2, T3

```
packs/core/.apm/skills/workspace-status/
  SKILL.md                      dispatcher: purpose, modes, invocation,
                                rendering contract, never
  references/
    agentbundle-layout.md       (unchanged)
    reconcile.md                full-audit depth + coordination-receipt
                                authoring and `invalid_receipt` recovery
    explain.md                  single-item investigation depth
    mutate.md                   prune, repair-*, selected-membership,
                                consent flow, refusal codes
  assets/
    workspace.toml.template     emitted on exit 1
  scripts/                      (unchanged, out of bounds)
  evals/                        reviewed, updated if behavior descriptions move
```

### Behavior & rules

Owned by: T1, T7

No runtime behavior changes. The eight subcommands, their argument vectors,
their exit codes, and their JSON output are identical before and after. The only
observable difference is which instructions an agent has in context at which
moment.

### Failure, edge cases & resilience

Owned by: T4, T5

The failure this delivery must not cause is a silently relocated obligation: a
sentence that a test pins moving out of the file the test reads, in a way that
leaves the test green because it matched somewhere else or matched nothing it
checked. Two instruments cover it. The six pin-holding suites catch a pin whose
sentence left `SKILL.md`. The mutation proof on T5 catches the retargeted
control's comparison going vacuous in its new home.

### Quality attributes (NFRs)

Owned by: T4

The body's ceiling is 500 lines, which is the linter's warning threshold rather
than an invented bar. Current body is 685, so at least 185 lines must leave, and
the restructuring itself adds roughly 30 back for the purpose, mode table, never
section, and reference routing.

A measurement before review corrected this budget. The inlined template is 25
lines, not the 60 first assumed — the fence runs from line 88 to line 112. The
first cut therefore landed at about 512 lines, over the ceiling, which is why
the coordination-receipts section is in the move list:

| Section | Lines | Destination |
| ---: | ---: | --- |
| Coordination receipts | 40 | `references/reconcile.md` |
| Subcommand guidance, per-mode depth | ~48 of 83 | the three references |
| Prune workflow | 65 | `references/mutate.md` |
| Interrupted-prune recovery | 28 | `references/mutate.md` |
| Repair workflow | 37 | `references/mutate.md` |
| Initialisation template | 25 | `assets/workspace.toml.template` |
| **Leaving** | **243** | |

That lands the body near 472 with about 28 lines of slack. The slack is thin
enough that T4 measures rather than estimates before it is called done.

### Dependencies & integration

Owned by: T2, T7

No new dependency. `tomlkit` remains a runtime dependency of `repair-apply`
only, declared in the core pack's guidance, and its detection prose travels into
`references/mutate.md` with the rest of the mutation flow — with the
prerequisite itself staying in the body, because an agent needs to know the
dependency exists before it routes.

## Tasks

### T1: The backend baseline is recorded before any edit

**Depends on:** none

**Tests:**
- Recompute the four SHA-256 digests AC-0008 names and confirm they match at
  the current HEAD, then record the transcript in the verification ledger. The
  criterion carries the digests, so this task proves the tree still agrees with
  the contract before work starts rather than manufacturing the baseline after.

**Done when:** the four digests match the values in AC-0008 and `git status`
shows no modification under `scripts/`.

### T2: The three reference files carry the relocated depth

**Depends on:** T1

**Tests:**
- No test in this task. The content is a move, and the assertions that prove it
  arrived belong to T4 and T5; a test here would assert against text this task
  is still writing.

**Approach:**
- Cut from `SKILL.md` and paste into the reference, one section at a time, so a
  diff of the pair shows a pure move. Write the reference files before trimming
  the body so no intermediate commit loses the text.
- `references/mutate.md` receives the prune workflow, interrupted-prune
  recovery, the repair workflow, and the `selected-membership` invocation,
  including the anchor sentence and the refusal-code list verbatim.
- `references/reconcile.md` receives the coordination-receipts section whole.
  No test reads it from `SKILL.md`, and it is remediation detail for one finding
  code rather than anything an orientation renders.

**Done when:** the three files exist, and for each moved section a diff of the
removed and added text is empty apart from heading level and surrounding blank
lines.

### T3: The initialisation template is an asset the body cites

**Depends on:** T2

**Tests:**
- AC-0006: the asset's bytes equal the template block as it stands at the base
  commit AC-0008 names. Read it with `git show <that commit>:<skill path>`
  rather than from the working copy, and take the commit from the criterion
  rather than repeating it here — two copies of a baseline drift apart and
  AC-0006 and AC-0008 would then measure against different trees.
- AC-0007: `SKILL.md` contains the asset's skill-relative path and does not
  contain the template's opening comment line.

**Done when:** both assertions pass.

### T4: The body is a dispatcher at or under its ceiling

**Depends on:** T2, T3, T5

**Tests:**
- AC-0001: body length counted from the line after the closing frontmatter
  delimiter, matching how `skill_spec_lint.py` counts it.
- AC-0002 and AC-0003: the three reference files exist, and each path appears in
  the body.
- AC-0004: parse the `_SUBCOMMANDS` frozenset literal from the backend with
  `ast`, not a regex over the source text, then assert each member appears on a
  line of the mode-selection section that names exactly one of the four modes.
  Scoping to the section is what makes a wrong mapping fail.
- Content pin, not a criterion: the body's `Never` section states the consent
  requirement for the mutating subcommands.
- The six pin-holding suites stay green, proving no pinned sentence left the
  file.

**Approach:**
- Restructure into the approved section order — purpose, mode selection,
  invocation contract, status rendering contract, never, conditional references
  — rather than deleting in place. Section order is what makes the mode table
  the first thing an agent reads.
- The status rendering contract absorbs the next-actions section whole, because
  two of its strings are pinned and folding is a move rather than a rewrite.
- Move prose by cut-and-paste so relocated bytes are unchanged; re-run the six
  pin-holding suites after each section moves rather than once at the end, so a
  break names the section that caused it.

**Done when:** `agentbundle catalogue lint --root . --deep` reports no CAT-S003
body-length finding for this skill, and AC-0001 through AC-0004 pass.

### T5: The refusal-code control bounds itself in its new home

**Depends on:** T2

**Tests:**
- AC-0005: retarget the control in
  `tests/roster/test_two_sided_prune_closure_invariant.py` to open
  `references/mutate.md`. Change the path it reads and nothing else — the
  anchor search, the `_prune_error` regex, and the bullet-list slice all stay.
- Construction evidence, not a criterion: mutation proof. Copy the prune source
  to the scratch directory, add a `_prune_error("undocumented_code", ...)` call
  site, point the control at the copy, and record that it fails. The anchor
  assertion already fails loudly on a missing anchor, so that half needs no
  proof; what the mutation establishes is that the emitted-versus-documented
  comparison still reaches a verdict against the relocated list.

**Done when:** the control passes against the real tree, fails against the
mutated copy, and both transcripts are in the ledger.

### T6: The roster-step guidance matches the workflow

**Depends on:** none

**Tests:**
- AC-0009: parse `.github/workflows/build-check.yml` with `yaml.safe_load`, and
  take the guard condition as true when every step in `gate-main` whose `run`
  invokes a `tests/roster/` path carries an `if:` key. While that holds, assert
  `tests/AGENTS.md` contains neither "fail-fast" nor "never runs" within its
  roster-placement section. Deriving the condition rather than hard-coding it is
  what makes the check follow the workflow if the guards are later removed.
- Content pin, not a criterion: `tests/AGENTS.md` still instructs placing a new
  named step above the bulk pytest step, and still names attribution as the
  reason.

**Approach:**
- Correct the claim, keep the instruction. The three placement obligations the
  file lists are unaffected and stay; only the stated reason for the first one
  changes, from "a step below never runs" to "a step below reports the failure
  against a broad target instead of the named one".

**Done when:** AC-0009 passes, the content pin passes, and the file still lists
all three obligations.

### T7: The delivery is projected, versioned, and portable

**Depends on:** T3, T4, T5, T6

**Tests:**
- AC-0008: the four backend digests still match the values the criterion names.
- Content pin, not a criterion: the citation grep from `packs/AGENTS.local.md`
  returns no match inside the new reference and asset files.
- The existing projection suites confirm the `.claude/` and `.agents/` copies
  match the source.

**Approach:**
- Bump `packs/core/pack.toml` by a patch level from 2.26.32, then run
  `FORCE=1 make build-self`. The plugin manifest's version is derived, so it is
  regenerated rather than hand-edited.
- Register the new roster module in the two places `tests/AGENTS.md` requires: a
  named step above the bulk pytest step at `build-check.yml:574`, and a matching
  `STEP_DISPOSITION` entry of `LOCAL("test-after-build-check")` in
  `tools/lint-ci-parity.py`. The third obligation does not fire — the module
  names no `docs/specs/<slug>` path as a literal.
- Review the eval harness. The pack rule obliges the review; whether it obliges
  an edit depends on whether any eval describes a flow whose documentation
  moved.

**Done when:** `make lint-ruff lint-mypy`, `agentbundle catalogue verify --root .`,
and `python3 tools/lint-ci-parity.py` are all clean, and `git status` is clean
after a second `make build-self`.

### T8: The release surface carries the change

**Depends on:** T7

**Tests:**
- A free-standing `##` core pack entry exists in `docs/product/changelog.md`,
  not nested under `[Unreleased]`, and the topmost release heading is this one.

**Approach:**
- Decide the `Highlights` disposition explicitly against the one question the
  pack's release guidance asks: does this change what a consumer of the pack can
  do? An unwritten decision here is a release the public page never mentions, so
  the answer is recorded either as a `### Highlights` block or as a stated
  verdict in the pull request.

**Done when:** the entry is present and the Highlights decision is written down
in one of those two places.

## Rollout

No flag, no infrastructure, no sequencing. The change ships in one pull request
and is reversible by reverting it; a consumer who installs the pack afterwards
gets a skill with the same eight subcommands and a different file layout.

## Risks

- **A relocated sentence loses its scope.** Prose that reads correctly inside a
  section about pruning can read as a general rule once it is the opening of its
  own file. Mitigated by moving whole sections rather than sentences, and by
  reading each reference file top to bottom after the move rather than only
  diffing it.
- **The body grows back.** Nothing today stops it, which is how it reached 686
  lines. Mitigated by AC-0001 becoming a standing test rather than a one-time
  measurement.
- **The mutation proof is skipped because the control is green.** A green
  retargeted control is consistent with a control that silently matches nothing,
  and the proof is construction evidence rather than a criterion, so no
  acceptance checkbox forces it. Mitigated by T5 naming it as a `Done when:`
  condition with a required ledger transcript.

## Changelog

- 2026-09-22 — drafted.
- 2026-09-22 — a pre-review measurement corrected the line budget: the inlined
  template is 25 lines rather than the 60 first assumed, so the first cut landed
  near 512 and the coordination-receipts section joined the move list.
- 2026-09-22 — contract review round 1 (Codex, contract and governance focus):
  11 findings, 10 sustained and 1 refuted. Criteria fell from 11 to 9. The
  always-loaded consent line, the retained roster-placement instruction, the
  portability grep, and the refusal-code mutation proof were demoted from
  criteria to design material with content pins. AC-0008 gained four fixed
  digests and a base commit, because a baseline the implementation creates
  later cannot constrain it.
- 2026-09-22 — relocation review round 1 (Codex, pin-preservation focus): 2
  findings, both sustained. T4 now depends on T5, because T2 removes the
  refusal anchor from the body and T4's pin-suite gate would fail until T5
  retargets the control. The design rationale no longer claims a missing anchor
  yields a clean result — that control asserts the anchor before slicing — so
  the mutation proof is scoped to the comparison rather than to anchor
  detection. The reviewer confirmed the structural `<ini-slug>`-to-Brief-queue
  adjacency survives and found no reverse-pin error.
- 2026-09-22 — spec approved by eugenelim (scope decision).
- 2026-09-22 — plan approved by eugenelim (build-strategy decision).
- 2026-09-22 — implementation review: 2 rounds on Codex. Round 1 (adversarial +
  security) raised 2 Concerns, both sustained and repaired, plus a precision
  repair to the Never bullet they exposed; its confirmation pass raised 1 more,
  also repaired. Round 2 (quality lens) raised 6, of which 5 sustained and 1
  refuted on the evidence in packs/AGENTS.local.md:70. All nine criteria verified
  and the delivery closed.
- 2026-09-22 — convergence round: 3 findings, all attributed by the reviewer to
  prior-round repairs rather than to the draft, which is the stop signal. Two
  stale companion statements and one duplicated base-commit SHA were corrected;
  the reviewer read the T1-T8 dependency edges and confirmed no cycle. Review
  rounds closed.
