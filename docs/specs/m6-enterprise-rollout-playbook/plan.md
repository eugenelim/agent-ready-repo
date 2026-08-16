# Plan: m6-enterprise-rollout-playbook

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> record why in the changelog.

## Approach

Create one cross-pack how-to that operates above the existing technical
distribution guides. Start from the adopter-persona track and stage contracts,
author the role handoffs, stage gates, checklist, decision record, and
retrospective in one page, then register and render it through the existing
guide pipeline. A focused content-contract test pins the load-bearing adoption
requirements without asserting prose wholesale. Three cold tabletop scenarios
verify that readers can reach an honest verdict without the spec beside them.

## Constraints

- RFC-0064 P5 owns the champion → CTO → platform team → engineers arc, pilot →
  wave → organization-wide stages, checklist, and retrospective.
- The adopter-persona brief and comparison matrix require three rollout tracks,
  nine design requirements, and an explicit mid-market evidence gap.
- `guides/AGENTS.md` owns frontmatter, generated navigation, build order, and
  link verification.
- The guide must link to, not restate, the technical catalogue enterprise-
  distribution procedures.
- No dependency on `m6-astro-work-index`; no change to `ini-008`, work-intake,
  workspace-routing, packs, package dependencies, or runtime behavior.

## Construction tests

**Integration tests:** `tools/validate_guides.py`, `tools/check-guide-index.py`,
`tools/test_documentation_entry_links.py`, the rendered-link checker, and
`make site-build` cover publication and link closure across the changed page.

**Manual verification:** three cold tabletop scenarios use technical,
enterprise, and non-technical inputs and record stage verdicts in
`notes/tabletop-scenarios.md`.

## Design (LLD)

### Design decisions

- One how-to, not three track pages: the reader's job is to run one enterprise
  rollout while selecting the appropriate overlay. Traces to AC1–AC5.
- Stage gates carry a common record shape, but track-specific evidence stays
  explicit. Traces to AC2–AC9.
- Existing technical guides remain canonical for distribution mechanics.
  Traces to AC10.

### Component / module decomposition

- `guides/_shared/how-to/roll-out-agent-ready-repo-across-an-enterprise.md` owns
  the public procedure, templates, and links. Traces to AC1–AC10.
- `guides/_shared/how-to/README.md` owns source-tree discovery. Traces to AC11.
- `tools/test_enterprise_rollout_playbook.py` owns semantic structure checks.
  Traces to AC2–AC10.
- `notes/tabletop-scenarios.md` owns manual-QA evidence. Traces to AC12.

### State & control flow

The reader chooses a track, prepares a stage, runs the bounded adoption work,
collects evidence, and records one of four verdicts. Only `advance` enters the
next stage; `hold` preserves scope, `revise` repeats the current stage after a
named change, and `stop` ends the rollout. Traces to AC2–AC9.

### Behavior & rules

The how-to uses outcome-first language before internal terminology, states
reads/writes and external mutations, gives every decision a human owner, and
ends stages at a shareable artifact. Traces to AC1–AC10.

### Quality attributes (NFRs)

Guide frontmatter, internal links, generated route, and heading hierarchy pass
the existing documentation gates. A new reader can complete each tabletop
scenario without consulting this spec. Traces to AC1, AC11, AC12.

## Tasks

### T1: The rollout playbook's semantic contract is executable

**Depends on:** none

**Touches:** `tools/test_enterprise_rollout_playbook.py`

**Mode:** TDD

**Tests:**
- `stub: true`
- **Stub:** `tools/test_enterprise_rollout_playbook.py` is a compilable red
  stdlib check marked `# STUB: AC1-AC10`; it fails while the guide is absent.
- A red stdlib test requires the role arc, stage sequence, track overlays, nine
  design requirements, stage verdicts, checklist, decision record,
  retrospective, mid-market disclaimer, and links required by AC1–AC10.
- The test rejects copied technical distribution commands as substitutes for
  adoption guidance.

**Approach:**
- Parse the Markdown as text and assert stable headings, field labels, link
  targets, and discriminating phrases rather than exact paragraphs.

**Done when:** the test compiles and fails only because the guide is absent.

### T2: A champion can run the three-stage, three-track rollout from one how-to

**Depends on:** T1

**Touches:** `guides/_shared/how-to/roll-out-agent-ready-repo-across-an-enterprise.md`, `guides/_shared/how-to/README.md`

**Mode:** goal-based check

**Tests:**
- `python3 tools/test_enterprise_rollout_playbook.py` passes AC1–AC10.
- `python3 tools/validate_guides.py` and `python3 tools/check-guide-index.py`
  pass AC1 and AC11.

**Approach:**
- Author the page to the how-to and conversation-first contracts.
- Put the copyable champion request in the first 120 words.
- Add role handoffs, stage gates, track overlays, checklist, decision record,
  retrospective, failure branches, and narrow links to existing guides.
- Register the page in the shared how-to index.

**Done when:** the content-contract and guide-structure gates pass.

### T3: Three cold scenarios reach honest rollout verdicts

**Depends on:** T2

**Touches:** `docs/specs/m6-enterprise-rollout-playbook/notes/tabletop-scenarios.md`

**Mode:** visual / manual QA

**Tests:**
- Run one technical, one enterprise, and one non-technical tabletop scenario.
- Record chosen track, stage, first task, human controls, evidence, recipient,
  unresolved risk, mutation status, and final verdict.
- Record the QA scope boundary: exact playbook sections exercised, where each
  scenario stopped, and which later-stage or external behavior was documented
  but not exercised.

**Approach:**
- Use scenarios grounded in the guide's own examples.
- Treat any missing decision owner or unverifiable claim as `revise` or `stop`,
  not as a successful run.
- Give `notes/tabletop-scenarios.md` a `## Scope boundary` section before the
  scenario records so the evidence cannot imply a live rollout occurred.

**Done when:** all three records are complete and no scenario needs the spec to
interpret the guide.

### T4: The published slice closes independently

**Depends on:** T2, T3

**Touches:** `docs/rfc/0064-ini-001-ai-native-ecosystem.md`, `docs/specs/README.md`, `workspace.toml`, `docs/product/changelog.md`

**Mode:** goal-based check

**Tests:**
- Full documentation and rendered-link gates pass.
- RFC-0064 Errata #9 records this independent P5 slice complete.
- `workspace-status reconcile` classifies the five-field record without a
  dependency on `m6-astro-work-index`.

**Approach:**
- Record closeout in RFC errata, the spec index, and the changelog after the guide is proven.
- Move this spec's exact canonical workspace record from queue to shipped only
  at closeout.

**Done when:** AC11–AC13 pass and workspace reconciliation reports no stale
entry for this spec.

## Rollout

The guide publishes through the existing static documentation build. Reverting
the guide, index entry, content test, and status records restores the prior
state. No infrastructure or external system changes.

## Risks

- A generic enterprise checklist can erase the track-specific constraints that
  motivated the work; the focused test and tabletop scenarios pin the
  distinctions.
- Duplicating distribution procedures creates competing sources of truth;
  AC10 keeps them linked and owned elsewhere.
- The mid-market gap can be softened into marketing copy; AC9 requires a clear
  refusal to promise the unsupported path.

## Changelog

- 2026-08-14: Initial full-mode plan grounded in RFC-0064 P5 and adopter-persona research.
- 2026-08-15: Implementation plan approved by eugenelim.
- 2026-08-16: Rebased onto Core 2.7 work-intake, confirmed no competing workflow, and closed the shipped slice after documentation, link, build, and browser verification.
