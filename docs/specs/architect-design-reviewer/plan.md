# Plan: architect-design-reviewer

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is markdown primitives + governance docs + release mechanics — no
runtime logic. The shape: author one self-contained agent file
(`packs/architect/.apm/agents/design-reviewer.md`), wire its consumers (the
convergence-loop rung, the README exclusion, the architect guides), co-land the
governance ADR that licenses it, then run release mechanics (version bump +
changelog + `make build-self`) and verify cross-adapter projection plus a green
suite. The riskiest part is the **agent body**: it must be self-contained
(agents bundle no `references/`) yet reuse `architect-review`'s methodology
faithfully without drifting from it — handled by inlining a condensed rubric and
noting the skill's `references/` as the fuller source, the pack's standing
duplication-over-DRY stance. The second risk is the **build/inventory surface** —
architect ships its first agent, so the package suite and projection are the
integration check (T5). Order: agent file → consumer prose → ADR (independent) →
release mechanics → projection + suite verification.

## Constraints

- **RFC-0032** (Accepted 2026-06-14) — the agent's contract, the read-only +
  forked-context design, the charter-ceiling interpretation, and the
  graceful-degrade requirement all derive from it.
- **Architect pack design principles** (`packs/architect/README.md`) —
  workspace-agnostic, no required configuration, no required composition,
  duplication-over-DRY for rubrics. The agent honors all four.
- **Self-host projection discipline** — edit `packs/architect/.apm/` source,
  then `make build-self`; never edit projected paths.

## Construction tests

**Integration tests:** the full `packages/agentbundle` pytest suite (run in T5)
spans T1+T4 — it is the surface that catches any shipped-pack inventory or
declaration assertion that newly sees architect carrying an agent, plus the
cross-adapter projection. No new test framework is introduced; existing
contract/adapter tests are extended only if a gap is found.
**Manual verification:** none — every check is a one-liner (grep / lint / build)
or the suite.

## Design (LLD)

Shape: `integration`. Stack is the catalogue's own pack/build pipeline (Python
`agentbundle`, markdown primitives) — no application framework.

### Design decisions
<!-- Traces to: AC1–AC6 · contracts/: none -->
- **Self-contained single-file agent**, not a skill-style dir with `references/`
  — agents project as a flat `.md` (verified in the adapter modules), so the
  rubric is inlined. Rejected: pointing the agent at `architect-review`'s
  `references/` by path — fragile across adapters/scopes and breaks "no required
  composition." A one-line note still points there as the fuller source where
  co-installed.
- **Read-only tools (`Read, Grep, Glob`)** make "flag, never rewrite" a tool
  boundary, not a request. Rejected: granting `Edit` and relying on prose.
- **Soft dependency** — the convergence-loop rung names the agent as preferred
  *when installed* and degrades to the existing ladder; the loop never errors on
  its absence (RFC-0032 + the loop's standing degrade-gracefully wording).
- **`model: opus`** mirrors the core reviewers (judgment-heavy review).

### Interfaces & contracts
<!-- Traces to: AC2–AC4 · contracts/: none (no formal contract type) -->
The agent's output *is* its interface: a one-line verdict (SHIP IT / SHIP WITH
CHANGES / MAJOR REWRITE / WRONG ARTIFACT), then findings grouped by severity
(🟥/🟧/🟨/⚪), each also tagged 🔧 mechanical / 🧭 judgment in well-architected
mode — the same shape the convergence loop already consumes and the core
reviewers' findings-only output contract. Input contract: seeded with the
artifact + concept + constraints, never the authoring chain-of-thought.

### Dependencies & integration
<!-- Traces to: AC9, AC10, AC13 · contracts/: none -->
New consumer of the existing agent-projection path (7 adapters). The version
bump drifts `marketplace.json` (all-packs aggregation), refreshed by
`make build-self`. No new dependency; no adapter-contract bump (agents admitted
since v0.7; architect stays at 0.10).

## Tasks

### T1: Author the `design-reviewer` agent file

**Depends on:** none

**Tests:** (goal-based — AC1–AC5)
- `grep` confirms `packs/architect/.apm/agents/design-reviewer.md` frontmatter:
  `name: design-reviewer`, `tools: Read, Grep, Glob` (exactly — no Edit/Write/Bash),
  `model: opus`, and a `description` ≤ 1024 chars — the cap originates in the
  kiro frontmatter parser and is **enforced by `lint-packs`
  (`_check_agent_metadata`)**, not `lint-skill-spec` (which walks skills only,
  never `.apm/agents/`). The description must contain **no unquoted `: `** (the
  kiro fail-silent hazard, #8329 — e.g. don't write `seeded with: the artifact`
  unquoted); this hazard is **not lint-gated for agents**, so this grep is its
  sole guard.
- `grep` confirms body anchors: the four verdict labels, the four severity
  glyphs, the `mechanical` / `judgment` taxonomy tokens, the genre-routing list
  (design doc / C4 / sequence / state / ER / generic), the "never the authoring
  chain-of-thought" clause, the "flag … never rewrite" clause, the findings-only
  output rule, and the one-line note pointing at `architect-review`'s `references/`.
- **Byte-faithfulness diff:** the inlined verdict labels, severity glyphs, and
  🔧/🧭 taxonomy match `architect-review/SKILL.md` + `references/rubric-well-architected.md`
  verbatim at authoring time (record the diff in the PR description).
- `lint-packs` (source lint — the gate that actually walks `packs/*/.apm/agents/`
  and runs `_check_agent_metadata`) is green for the new agent. Note:
  `lint-agent-artifacts.py` walks the *projected* `.claude/agents/`, which
  architect is not projected into in this repo — so it does **not** exercise
  this agent here; don't read its pass as validation of the agent frontmatter.

**Approach:**
- Mirror the shape of `packs/core/.apm/agents/adversarial-reviewer.md` (inline
  checklist, findings-only output) and `packs/research/.apm/agents/*` (frontmatter).
- Inline the condensed rubric: verdict scheme + severity glossary (from
  `architect-review/SKILL.md`), the mechanical/judgment test (from
  `architect-review/references/rubric-well-architected.md`), and genre routing.
- Cover both modes (verdict critique + WA risk-register) and the
  reviewer-independence + read-only + findings-only contract.

**Done when:** both greps pass and `lint-agent-artifacts` + `lint-packs` are
green for `design-reviewer.md`.

### T2: Wire consumers — convergence-loop rung, README exclusion, guides

**Depends on:** T1

**Tests:** (goal-based — AC6–AC8)
- `grep` confirms `convergence-loop.md` § *Where the review comes from* names
  `design-reviewer` as the rung-1 (fresh-context) source when installed, and the
  soft-dependency / degrade wording is preserved.
- `grep` confirms `packs/architect/README.md` no longer carries the old
  "design-side review is a skill, not a subagent" exclusion verbatim and now
  documents the `design-reviewer` subagent.
- `grep` confirms `docs/guides/architect/how-to/review-an-architecture-artifact.md`
  and `docs/guides/architect/README.md` mention the subagent.
- `lint-packs` green (no broken cross-references in the edited pack files).

**Approach:**
- Add the rung to `convergence-loop.md` § *Where the review comes from* above the
  `architect-review`-installed bullet, framed as the strongest isolation.
- Revise the README's "What's NOT in this pack" Subagents bullet → a "Subagents"
  entry documenting `design-reviewer`; update the skills table / overview line.
- Add a short paragraph to the how-to and a line to the guides home offering the
  subagent as the independent-review option alongside the in-thread skill.

**Done when:** all four greps pass and `lint-packs` is green.

### T3: Co-land the charter-ceiling ADR

**Depends on:** none

**Tests:** (goal-based — AC11)
- The new `docs/adr/<NNNN>-*.md` exists, Status `Accepted`, and records the
  RFC-0032 decision-2 reading.
- RFC-0032's *Follow-on artifacts* and this spec's `Constrained by` reference the
  assigned ADR ordinal; links resolve (`lint-spec-status.py` reference check /
  manual link check).

**Approach:**
- Use the `new-adr` skill; next ordinal from `docs/adr/`.
- Title ~ "The 'three reviewers' ceiling scopes the core code-review lenses";
  decision = the RFC-0032 reading; consequences = design-side reviewers in opt-in
  packs are admissible.
- **Edit RFC-0032's *Follow-on artifacts* to name the concrete ADR ordinal** once
  assigned. Adding a follow-on back-link to an Accepted RFC is the sanctioned
  *mechanical* completion of a follow-on pointer — not a substantive change to a
  frozen decision, so it needs no erratum (contrast the frozen-RFC-divergence
  rule, which applies only when spec/impl *contradicts* the RFC).

**Done when:** the ADR file exists with Accepted status and the back-links (RFC
follow-on + spec `Constrained by`) resolve.

### T4: Release mechanics — version bump, changelog, build-self

**Depends on:** T1, T2

**Tests:** (goal-based — AC9, AC12)
- `grep` confirms `version = "0.6.0"` in `packs/architect/pack.toml` and
  `"version": "0.6.0"` in `packs/architect/.claude-plugin/plugin.json`.
- `docs/product/changelog.md` `[Unreleased] → Added` carries a `design-reviewer`
  entry.
- `make build-self` runs clean; `git status` shows no unexpected drift; the
  build-check drift gate is green (marketplace.json refreshed).

**Approach:**
- Bump `0.5.3` → `0.6.0` in both files; refresh the plugin.json description to
  mention the subagent if it enumerates primitives.
- Add the changelog entry.
- Run `make build-self` (FORCE=1 only if the tree is intentionally dirty mid-loop)
  and confirm marketplace.json updated; verify no projected-path drift.

**Done when:** both version strings read `0.6.0`, the changelog entry exists, and
`make build-self` + the drift gate are clean.

### T5: Verify cross-adapter projection + green suite

**Depends on:** T1, T4

**Tests:** (goal-based, integration — AC10, AC13)
- A **durable, re-runnable** check (the verification of record) asserts
  `design-reviewer` projects for architect across all seven adapter routes —
  either an extended contract/adapter-test assertion or a committed goal-based
  one-liner over a freshly built `dist/`. A manual `dist/` peek is supplement
  only (`dist/` is gitignored). This lands RFC-0032's deferred `kiro-cli`
  install-confirmation.
- Full `packages/agentbundle` pytest, `lint-packs`, `lint-agent-artifacts`,
  `validate`, and `build` green. Check the pre-named candidate assertions —
  `test_plugin_manifest_schema.py`, `test_contract.py`,
  `test_adapter_{codex,cursor}.py`, the `test_multi_pack_install.py` architect
  scenarios — and update any that go red.

**Approach:**
- Add/extend the durable projection assertion, then build and confirm the agent
  appears in each adapter's native form (`.claude/agents/…`, `codex-agent-toml`,
  `.github/agents/…`, `.kiro/agents/…`, kiro-cli, `.cursor/agents/…`,
  `.gemini/agents/…`).
- Run the full suite; fix any of the named candidate assertions that hard-code
  architect as agent-free.

**Done when:** the agent is present under all seven adapter routes and the full
suite + lints + validate + build are green.

## Rollout

Pure content + catalogue-metadata change. **Delivery:** big bang via the pack
version bump (0.5.3 → 0.6.0); fully reversible (delete the agent file, revert the
bump and prose). No data migration, no published event, no infrastructure.
**Deployment sequencing:** none beyond the in-PR task order; the agent reaches
adopters when they next install/upgrade architect.

## Risks

- **Inventory assertions hard-code architect as agent-free.** A package test may
  assert architect ships only skills; T5's full-suite run surfaces it. Mitigation:
  update the assertion in the same PR (allowed — the spec authorizes it).
- **Rubric drift between agent and skill.** The inlined rubric could diverge from
  `architect-review`'s over time. Mitigation: the agent carries the one-line
  note naming the skill as the fuller source, matching the pack's existing
  duplicated-with-a-note convention; no generator is introduced.
- **`make build-self` reverts a projection-only edit.** If any edit lands only in
  a projected path, build-self silently reverts it. Mitigation: all edits are to
  `.apm/` source or repo-owned docs; verify `git status` after build (T4).

## Changelog

- 2026-06-14: initial plan.
