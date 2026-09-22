# Spec: workspace-status progressive disclosure

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — authority for `workspace.toml` and `workspace-status` behavior, which this delivery preserves unchanged
  - [RFC-0097](../../rfc/0097-agent-skill-engineering.md) — portable skill-authoring practice; names progressive disclosure as a first-class construction concern
- **Brief:** none
- **Discovery:** none
- **Contract:** none (skill body and its reference files; no machine-readable interface)
- **Shape:** integration

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

An agent orienting at session start loads a `workspace-status` body that states
the modes, the invocation contract, the status rendering contract, and the hard
prohibitions, and nothing else. Depth for reconciling, explaining, and mutating
the workspace arrives only when the agent routes to that branch, so a cold
orientation carries the instructions it uses and not the ones it does not.

## What Changes

- Mode selection — a four-mode section in `SKILL.md` naming `status`,
  `reconcile`, `explain`, and `mutate`, and mapping each to its backend
  subcommands.
- Reconciliation depth, including coordination-receipt authoring and
  `invalid_receipt` recovery — `references/reconcile.md`, loaded when the agent
  picks the `reconcile` mode.
- Investigation depth — `references/explain.md`, loaded when the agent picks the
  `explain` mode.
- Prune, repair, and selected-membership depth, including the consent flow and
  the refusal-code list — `references/mutate.md`, loaded when the agent picks the
  `mutate` mode.
- The `workspace.toml` initialisation template — `assets/workspace.toml.template`,
  cited from the invocation contract's exit-1 branch.
- The canonical-findings table and the status rendering contract — unchanged
  text, still in `SKILL.md`.
- The consent requirement for mutating subcommands — one always-loaded line in
  `SKILL.md`'s `Never` section, pointing at `references/mutate.md`.
- The roster-step placement guidance — `tests/AGENTS.md`, restated to match how
  `gate-main` actually runs, keeping the instruction to place a named step above
  the bulk pytest step and naming attribution as the reason.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the skill body is the procedure an agent follows | `packs/core/.apm/skills/workspace-status/SKILL.md` and its three reference files | work-loop implementer | The skill-shape suite named in Testing Strategy | Body at or under 500 lines with all three references linked |
| Maintainer procedure | Applicable — the roster-step placement guidance disagrees with the workflow it describes, and this delivery adds a roster step under it | `tests/AGENTS.md` | work-loop implementer | The conditional consistency check named in Testing Strategy | Guidance agrees with the workflow and retains the placement instruction |
| Interface compatibility | Applicable — the eight backend subcommands are the skill's stable surface and none changes | `packs/core/.apm/skills/workspace-status/scripts/` (unchanged) | work-loop implementer | Byte-equality assertion over the four backend scripts | Scripts byte-identical to their pre-change content |
| Release history | Applicable — a non-cosmetic pack-content change publishes | `docs/product/changelog.md`, free-standing `##` core pack entry | work-loop implementer | The entry, plus a recorded `Highlights` disposition | Entry present with an explicit Highlights decision |
| Current product truth | Not applicable — no user-visible behavior changes; the eight subcommands, their argv, exit codes, and JSON output are untouched | — | — | — | — |
| Decision rationale | Not applicable — progressive disclosure is already the accepted authoring pattern, so this delivery applies an existing decision rather than making one | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Move prose by cut-and-paste. When a sentence relocates from `SKILL.md` to a
  reference, its bytes travel unchanged.
- Re-run the six pin-holding suites named in Testing Strategy after every edit
  to `SKILL.md` or a reference file, because each pin is a whole-file substring
  match that a relocation breaks silently.
- Edit under `packs/core/.apm/`, then regenerate the `.claude/` and `.agents/`
  projections with self-host.

### Ask first

- Relocating any sentence a test pins, beyond the refusal-code list this spec
  already routes to `references/mutate.md`.
- Adding a fourth reference file, or any destination beyond the three references
  and the one asset this spec names.
- Changing the wording of a relocated sentence rather than its location.

### Never do

- Edit any of the four backend scripts. This delivery changes prose and file
  layout only.
- Edit a `.claude/` or `.agents/` projection by hand.
- Weaken, narrow, or delete the refusal-code control to make a relocation pass.
- Add a new top-level directory, a new module boundary, or a new dependency.
- Cite an RFC or ADR ordinal, an acceptance-criterion number, or a `docs/`
  repository path in shipped pack content.

## Testing Strategy

- **Body length (AC-0001)** — goal-based check. One line count against one
  threshold; a TDD cycle buys nothing over reading the number.
- **Reference files exist (AC-0002)** — goal-based check. Three path
  existence tests.
- **Reference linkage (AC-0003)** — goal-based check. Three substring searches
  in one file. Separated from AC-0002 because a citation to a file that was
  never written passes a linkage check on its own.
- **Mode-to-subcommand mapping (AC-0004)** — TDD. The expected set is parsed
  from the backend's `_SUBCOMMANDS` literal at run time, and the assertion is
  per-line rather than whole-file so a subcommand named in the wrong mode's row
  fails. A whole-file presence check passes on a wrong mapping, which is the
  regression this criterion exists to catch.
- **Refusal-code documentation (AC-0005)** — TDD. The existing control derives
  its expected set from the prune source's `_prune_error` call sites;
  retargeting keeps that derivation and changes only which file it reads. The
  plan requires mutation proof as this control's construction evidence, because
  a control that cannot find its anchor reports a clean result.
- **Template asset content (AC-0006)** — goal-based check. A byte comparison
  against the block as it stands at the base commit.
- **Template no longer inlined (AC-0007)** — goal-based check. Separated from
  AC-0006 because copying the block out and forgetting to delete the original
  leaves both green under a single combined assertion.
- **Backend immutability (AC-0008)** — goal-based check. Four digests compared
  against the four fixed values the criterion names.
- **Roster-placement guidance accuracy (AC-0009)** — TDD. The check derives the
  guard condition from the workflow rather than hard-coding it, so removing the
  guards later changes what the check demands of the guidance.

Four obligations are design material rather than criteria. Three are prose
whose only failure is a reader's objection to a missing sentence, and each is
pinned by an assertion in the same test module: the always-loaded consent line
in `Never`, the retained roster-placement instruction with its attribution
reason, and the portability grep over the new files. The fourth is the
refusal-code mutation proof, which is not prose at all but evidence about a
test's sensitivity; the plan carries it as T5's construction evidence.

The six pin-holding suites are regression surface rather than criteria: each
already owns its own pins, so this delivery runs them unchanged and does not
restate their obligations here.

## Acceptance Criteria

- [x] **AC-0001.** the body of `packs/core/.apm/skills/workspace-status/SKILL.md`,
      counted from the line after the closing frontmatter delimiter, is at most
      500 lines.
- [x] **AC-0002.** the files `references/reconcile.md`, `references/explain.md`,
      and `references/mutate.md` exist under the skill directory.
- [x] **AC-0003.** `SKILL.md` references each of `references/reconcile.md`,
      `references/explain.md`, and `references/mutate.md` at least once by that
      skill-relative path.
- [x] **AC-0004.** in `SKILL.md`'s mode-selection section, every subcommand in
      the `_SUBCOMMANDS` set in `scripts/workspace_status.py` appears on a line
      that also names exactly one of the four modes.
- [x] **AC-0005.** every refusal code the `_prune_error` call sites in
      `scripts/workspace_status_prune.py` emit appears as a code in the
      refusal-code list in `references/mutate.md`.
- [x] **AC-0006.** the file `assets/workspace.toml.template` exists under the
      skill directory and its bytes equal the `workspace.toml` template block
      `SKILL.md` carries at this spec's base commit.
- [x] **AC-0007.** `SKILL.md` cites `assets/workspace.toml.template` and does
      not contain that template's content.
- [x] **AC-0008.** the four files under `scripts/` have these SHA-256 digests,
      taken at base commit `8ef829ab7947d7212dd814aa64af69fcfec6e764`:
      `workspace_status.py` `b07efea9132f1ddfeab8ce81554c65633d8fac3f5065fdeba31e40a0ef6d7484`,
      `workspace_status_engine.py` `b99ad663713333d2a221d655af73ff08898a0553e3e238356fd88d274ca4eea0`,
      `workspace_status_prune.py` `65076e175c821f2818dfcf5ea762df3d6b9f29334216948e3aac502e2a6c0f98`,
      `workspace_mcp_server.py` `c2b252f55c99d54558b253e3c14aa40a5feec5bbcaad1340154e57e3d2c03199`.
- [x] **AC-0009.** `tests/AGENTS.md` asserts no claim that a named roster step
      placed below the bulk pytest step in `.github/workflows/build-check.yml`
      does not run, while every roster step in that workflow carries an `if:`
      guard.

## Follow-ons

none — every discovery this delivery made is inside its own scope.

## Assumptions

- none — the two open design questions at authoring time were settled by the
  owner before the body was written. The consent line stays always-loaded and is
  carried in `What Changes` as design material with a content pin; the
  initialisation template lives in `assets/` and is carried by AC-0006 and
  AC-0007.
