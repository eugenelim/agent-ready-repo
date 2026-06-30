# Plan: experience-pack

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **method-authoring + a bounded rename migration**, not application
code. It lands in **one implementing spec** (RFC-0050 § Migration path) over a
task DAG whose backbone is: rename first (T1), then the two shared substrates
every new skill leans on — the promoted quality floor (T2) and the layout
contract (T3) — then the connective skills and the two new craft/process skills
(T4–T8), then the two enhancements (T9–T10), then the reviewer agent that reviews
all of it (T11), then evals (T12), the cross-pack `voice-and-microcopy` wiring
(T13), and finally the changelog/README/marketplace close-out (T14).

The **riskiest part is T1** — the rename touches the agnosticism CI lint that
*errors when its scan root disappears*, so the rename of the pack dir and the
retarget of the lint must land together or CI breaks; and frozen governance must
be bridged (ADR-0038, already Accepted) **not edited**. Everything after T1 is
additive pure-markdown that the renamed lint keeps honest. The testing story is
goal-based (build/grep/lint/eval-presence) for the mechanical work and manual-QA
(cold-prompt skill invocation + agent dispatch + `run-pack-evals.py`) for the
authored skills and the reviewer.

Each new skill is authored **standalone-useful + detect-and-degrade** so the DAG
edges are *authoring* dependencies (a skill references the shared floor / layout
doc / sibling artifact), never *runtime* coupling.

## Constraints

- **RFC-0050** (Accepted 2026-06-29) D1–D10 — the binding decisions.
- **ADR-0038** — the `design-craft → experience` rename + the frozen-governance bridge (RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, README index rows kept as historical record). Already Accepted.
- **ADR-0042** (supersedes ADR-0023) — the loop/work-type-keyed agent-addition policy; D7's `experience-reviewer` is decided within its four-conjunct test. Already Accepted.
- **ADR-0030 / RFC-0040** — the `agentbundle-layout.toml` three-tier path-resolution contract (the `[experience]` table mirrors `product-engineering`).
- **ADR-0028 / RFC-0037** — the pack-activation-eval coverage shape (`eval_queries.json` + `evals.json`, `run-pack-evals.py`).
- **RFC-0033 / ADR-0024** (frozen, bridged) — the pack's stack-neutrality + anti-infrastructure guardrails, unchanged.
- **RFC-0030** — `voice-and-microcopy`'s home (`product-engineering`), unchanged.
- **Self-host pack scope** — `experience` is user-scope-default: re-aggregate `marketplace.json`, do not project into this repo's working tree.

## Construction tests

Most verification is per-task (below). Cross-cutting:

**Integration tests:**
- The renamed agnosticism lint (`tools/lint-experience-agnostic.py`) runs clean against the *whole* `packs/experience/` tree after every skill lands — the standing guard that no new skill leaked a values table.
- `tools/run-pack-evals.py` exercises the trigger evals for all five new authoring skills (the integrated activation surface, not per-skill unit checks).

**Manual verification:**
- Cold-prompt each new/enhanced skill end-to-end and confirm the promised artifact lands at the resolved layout path with the promised content (platform axis / per-screen brief / as-is-to-be / interaction section).
- Dispatch `experience-reviewer` against a sample journey + screen flow; confirm severity-tagged findings covering the grounded reference + platform fit + cross-brief coherence + the full quality floor (incl. accessibility).

## Design (LLD)

Shape is `mixed`, but the feature is method-authoring + a rename — the only
design decisions worth recording are structural (where shared content lives, how
the reviewer is disambiguated). No data/schema, interface, or resilience design.

### Design decisions

- **Quality floor home (T2).** Promote `quality-floor.md` to a **pack-level
  `references/`** directory (the existing cross-skill-reference pattern
  `aesthetic-direction` already uses), referenced by every consuming skill —
  rather than leaving it private to `design-critique` or duplicating it. Rejected:
  copy-per-skill (drifts) and a new top-level dir (banned). Traces to: D2 ACs.
- **Reviewer name + disambiguation (T11).** `experience-reviewer` (distinct head,
  not a substring of `design-reviewer`) + a `description:` leading with a
  design-time-only cue handles both collision modes (substring trap + role-match
  attraction on the shared `reviewer` token) per ADR-0042 conjunct 4. Rejected:
  `experience-design-reviewer` (embeds architect's name). Traces to: D7 ACs.
- **`interaction-design` carries no own artifact (T8).** It enriches the
  per-screen brief and defers to the shared floor, so it needs no `[experience]`
  layout entry and no file-per-slug shape — the carve that keeps it a *craft*
  skill, not a connective one. Traces to: D10 ACs.
- **Rename + lint retarget are one task (T1).** The lint errors when its scan
  root is gone, so splitting them would red CI between commits. Traces to: D1 ACs.

### State & control flow

The layout path-resolution is the only stateful flow: config (`[experience]` in
`agentbundle-layout.toml`, repo-root over user-profile) → designed default
(`docs/design`) → discover-by-marker (canonical filename + frontmatter `type:`).
Each skill creates its dir lazily on first write and surfaces the resolved path
before writing. Mirrors `product-engineering`'s `frame-intent`. Traces to: D6 ACs.

## Tasks

### T1: rename `design-craft → experience` (dirs + manifests + guides + cross-links + lint + marketplace)

**Depends on:** none

**Tests:** (goal-based)
- `ls packs/experience/.apm/skills` lists the four existing skills; `packs/design-craft/` is gone.
- `grep -r '"name": "experience"' packs/experience/.claude-plugin/plugin.json` and `version` = `0.2.0`; same in `pack.toml`.
- `python tools/lint-experience-agnostic.py` exits clean; `python tools/test-lint-experience-agnostic.py` passes (sets `EXPERIENCE_ROOT`).
- `grep -rn design-craft .github/workflows/` returns only the pinned `(design-craft-pack AC8)` CI step tag and the RFC-0033 provenance pointer — no live tool/path reference.
- `make build` re-aggregates `marketplace.json`: an `experience` entry, no `design-craft` entry. Verifies D1 ACs.

**Approach:**
- `git mv packs/design-craft packs/experience`; update `pack.toml` `name`/`display_name`/`description`/`version=0.2.0`, `[pack.links].documentation` URL, and `.claude-plugin/plugin.json` `name`/`version`/`description`.
- `git mv docs/guides/design-craft docs/guides/experience`.
- `git mv tools/lint-design-craft-agnostic.py tools/lint-experience-agnostic.py` and the self-test; retarget the scan root (`:147`) to `packs/experience/`, rename the env override `DESIGN_CRAFT_ROOT` → `EXPERIENCE_ROOT`, update the self-test's env set and the leading descriptor of both CI steps. **Leave pinned:** the RFC-0033 docstring citation and the `(design-craft-pack AC8)` CI step name.
- Update cross-links in the four existing skills + README; re-aggregate `marketplace.json`.
- Do **not** edit RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, or README index rows (bridged by ADR-0038).

**Done when:** the lint + self-test pass against `packs/experience/`, `marketplace.json` shows `experience`, and `git grep -l design-craft` returns only frozen-governance/pinned-provenance hits.

### T2: promote the three-part quality floor to a pack-shared reference

**Depends on:** T1

**Tests:** (goal-based)
- The single shared `quality-floor.md` contains all three sections (handle-all-states, accessibility, reduced-motion); `grep -c '^##'` matches the three-part structure.
- Every consuming skill references the one floor sibling-relative (`grep '../design-critique/references/quality-floor.md'`); no private sibling copy exists. Verifies D2 ACs.

**Approach (amended — see RFC-0050 § Amendments + spec D2 floor AC):**
- A **pack-level `references/` directory does not project** to any adapter (the build projects only `skills`/`agents`/`hooks`/`hook-wiring`/`commands`), so the buildable realization of "one pack-shared floor" is the **single canonical file kept resident at `design-critique/references/quality-floor.md`**, documented as the pack-shared floor and referenced **sibling-relative** by every consuming skill (`map-screen-flow`, `interaction-design`, the existing craft skills); cross-pack `voice-and-microcopy` defers by-name. Add `permission/denied` as an *additional* gated-screen state. The file is **not** moved (moving it to a non-projecting location would dangle on every adopter; moving it to another skill's `references/` is churn for no projection benefit and the existing referrers already point at it).

**Done when:** one shared floor file with all three sections, referenced sibling-relative by every consumer; no private copy.

### T3: the `[experience]` layout table + per-skill `agentbundle-layout.md`

**Depends on:** T1

**Tests:** (goal-based)
- `grep -A1 '\[pack.layout.repo\]' packs/experience/pack.toml` shows `parent = "docs/design"`.
- Each artifact-writing skill ships `references/agentbundle-layout.md` documenting the `[experience]` table with the file-per-slug shapes. Verifies D6 ACs.

**Approach:**
- Add `[pack.layout.repo] parent = "docs/design"` to `pack.toml` (no `[pack.layout.user]`, like PE). Author the `[experience]` section in the layout contract + the per-skill `references/agentbundle-layout.md` (the PE pattern), documenting the four `type:` markers and file-per-slug shapes.

**Done when:** the layout default ships and each artifact-writing skill documents its path resolution.

### T4: `map-customer-journey` skill (D2/D3)

**Depends on:** T1, T2, T3

**Tests:** (manual-QA + goal-based)
- Cold prompt produces a journey map (stages × actions/emotions/pains/opportunities) carrying the platform/surface axis, written to `<parent>/journeys/<slug>.md`.
- Standalone-useful: with no persona present it elicits inline; degrades when downstream packs absent.
- Lint clean. Verifies the D2 journey + D3 axis ACs.

**Approach:** author `SKILL.md` (<~100 lines) + `references/` (NN/g journey mapping, Patton, Torres — pointed-to) + `agentbundle-layout.md`; customer/end-user-scoped (employee journeys out of v1).

**Done when:** a cold prompt yields the journey artifact at the resolved path, lint clean.

### T5: `blueprint-service` skill (D2)

**Depends on:** T1, T2, T3

**Tests:** (manual-QA + goal-based)
- Cold prompt produces a service blueprint (frontstage / line-of-visibility / backstage / support) at `<parent>/blueprints/<slug>.md`; backstage column names services textually when `architect`/`contracts` absent (degrade) and by-reference when present.
- Lint clean. Verifies the D2 blueprint AC.

**Approach:** author `SKILL.md` + `references/` (NN/g service blueprints) + `agentbundle-layout.md`; the backstage column is the slicing instrument handed to `architect`/`contracts` by-name.

**Done when:** a cold prompt yields the blueprint with the four rows, lint clean.

### T6: `map-screen-flow` skill + per-screen brief + consistency pass + D8 handover (D2/D3/D4/D8)

**Depends on:** T3, T4, T5

**Tests:** (manual-QA + goal-based)
- Cold prompt produces a **screen flow** at `<parent>/screens/<slug>-flow.md` (frontmatter `type: screen-flow`) — the screens *sequenced* with transitions and **error/edge flows**, the per-screen state matrix (deferring to the shared floor), the platform axis — **plus one per-screen brief per screen** (shared-contract / per-screen-spec split, the `0048-notes/07` template in `assets/`) at `<parent>/screens/<slug>/<screen>.md`.
- `SKILL.md` **declares the skill's inputs + a `Consumed by:` seam** — the verification target for the design-flow-completeness ACs.
- The procedure ends in a cross-brief consistency pass + the **always-runs** whole-journey verification — a low-fi prototype via MCP, **else the text-only steel thread** (every transition resolves, every action has a backing service); the steel thread is **non-droppable** (degrades prototype → text-only, never to nothing).
- The optional design-tool handover emits at `<parent>/screens/<slug>/<screen>.handover.md` when no MCP tool is present, and triggers the tool when one is; it carries instructions (not pixels/values) and names tool categories only — lint clean. Verifies D2/D3/D4/D8 + the design-flow-completeness ACs.

**Approach:** author `SKILL.md` + the brief template in `assets/` + the handover template + `references/` + `agentbundle-layout.md`; **foreground the macro flow** (sequence, transitions, cross-screen error/edge routing) — the *micro* per-screen interaction behavior is `interaction-design`'s (T8), not here; states defer to the shared floor; the handover is a detect-and-degrade branch.

**Done when:** the screen flow + briefs + (optional) handover land at resolved paths; the non-droppable steel-thread step runs; the `SKILL.md` input/`Consumed by:` declarations make the thread readable end-to-end; lint clean.

### T7: `map-internal-process` skill (D9)

**Depends on:** T1, T2, T3

**Tests:** (manual-QA + goal-based)
- Cold prompt produces, at `<parent>/processes/<slug>.md` (frontmatter `type: process-flow`): a SIPOC scoping table, a swimlane mermaid (`flowchart` + `subgraph` lanes), as-is + to-be with an as-is→to-be delta table, and a pain/waste register; anchored on APQC L3→L4; points to APQC/BPMN/BABOK, reprints none.
- It carries **no** platform/surface axis; cross-references the service blueprint by-name. Lint clean. Verifies D9 ACs.

**Approach:** author `SKILL.md` + `references/` (APQC PCF, BPMN 2.0, BABOK elicitation) + `agentbundle-layout.md`; producer of `frame-intent`'s current-state process-map input (by-name seam to PE).

**Done when:** a cold prompt yields the process artifact with all four sub-artifacts, no platform axis, lint clean.

### T8: `interaction-design` craft skill (D10)

**Depends on:** T2

**Tests:** (manual-QA + goal-based)
- Cold prompt enriches a per-screen brief's interaction/behavior section across feedback & timing (Doherty-Threshold, design-time only), input/forms, **a component state machine** (mermaid `stateDiagram-v2`, no state-management library code), **motion & micro-animations** (purposeful, reduced-motion-honoring, no durations/easing reprinted), navigation-as-behavior, gesture/pointer (platform axis), cognitive-law fit (cross-referencing `design-critique/references/heuristics.md` + Laws of UX, not duplicating).
- It **references** onboarding + search-interaction pattern families (pointed-to, not standalone skills).
- It emits **no** own file-per-slug artifact and adds **no** `[experience]` layout entry; defers to the shared floor.
- A review of a brief that conflated it with `layout-and-information-architecture`, `map-screen-flow` (cross-screen routing), or the floor (state set / reduced-motion rule) would be flagged (the three-state-home carve holds). Lint clean (incl. no motion durations/easing — the values guardrail). Verifies D10 ACs.

**Approach:** author `SKILL.md` + `references/` (statecharts, Material/HIG motion, Nielsen/Laws-of-UX — pointed-to); the carve is one-directional — existing skills own *what/where*, `map-screen-flow` owns cross-screen routing, this owns *how-it-behaves-here* (in-component state machine, motion, feedback). One coarse skill; onboarding/search referenced, not sub-skills.

**Done when:** the skill enriches a brief's interaction section (incl. a state machine + motion), references the pattern families, owns no artifact/layout entry, lint clean.

### T9: ground `aesthetic-direction` (D5/D3)

**Depends on:** T2

**Tests:** (manual-QA + goal-based)
- The enhanced skill grounds each named goal in persona + precedent + standards + platform conventions and records *what grounds each goal*; carries the platform/surface axis; prints no palette/font/value. Lint clean. Verifies the D5 grounding + D3 axis ACs.

**Approach:** edit `aesthetic-direction/SKILL.md` + `references/` to add the grounding + the axis; method-not-values preserved.

**Done when:** a cold prompt yields a grounded direction citing its referents, lint clean.

### T10: taste-mode `design-critique` (D4/D5)

**Depends on:** T2

**Tests:** (manual-QA + goal-based)
- `design-critique` runs a taste mode (evidence-grounded critique against the grounded reference + platform fit) and stays an interactive authoring-time skill (the SKILL.md states it is *not* fresh-context / not the reviewer agent). Lint clean. Verifies the D4/D5 ACs.

**Approach:** add the taste mode to `design-critique/SKILL.md`; cross-reference the `experience-reviewer` as the fresh-context runner.

**Done when:** the taste mode exists and the authoring-time/reviewer boundary is documented, lint clean.

### T11: `experience-reviewer` agent + eval surface + RFC-0048 roster reconciliation (D7)

**Depends on:** T6, T8, T9, T10

**Tests:** (manual-QA + goal-based)
- The agent exists under `packs/experience/.apm/agents/experience-reviewer.md`, forked-context / read-only / flags-never-rewrites; name is not a substring of `design-reviewer`; `description:` leads with the design-time-only cue.
- Dispatched against a sample journey + screen flow, it returns severity-tagged findings covering the grounded reference + platform fit + cross-brief coherence + the **full quality floor (handle-all-states + accessibility + reduced-motion)**.
- Its eval surface ships; RFC-0048:236 reflects *skill + opt-in forked reviewer*. Verifies D7 ACs.

**Approach:** author the agent (the `design-reviewer` shape) with the three-part floor explicit in its review list; ship the agent-eval surface; verify the already-logged RFC-0048 Amendment holds.

**Done when:** a dispatch returns the expected findings shape incl. accessibility; the roster reconciliation is verified.

### T12: evals for the five new authoring skills + `[pack.evals]` wiring

**Depends on:** T4, T5, T6, T7, T8

**Tests:** (goal-based)
- `[pack.evals].skills` lists the connective trio + `map-internal-process` + `interaction-design`; each ships `evals/eval_queries.json` + `evals/evals.json`.
- `python tools/run-pack-evals.py` (scoped to `experience`) detects activation for each. Verifies the packaging/evals ACs.

**Approach:** author trigger evals + Tier-4 judge rubrics per RFC-0037; wire `[pack.evals]`. `interaction-design`'s judge scores the interaction section it contributes to the brief (not a standalone artifact).

**Done when:** all five skills are eval-covered and `run-pack-evals.py` measures them.

### T13: `voice-and-microcopy` wiring + cross-links + PE bump (D5/GAP-C1)

**Depends on:** T6

**Tests:** (manual-QA + goal-based)
- `voice-and-microcopy` (in `product-engineering`) consumes the screen flow's per-screen state matrix when present (copy per screen × state) and behaves as today when absent.
- `experience` and `product-engineering` READMEs cross-link each other; `product-engineering` `pack.toml`/`plugin.json` bump `0.7.0 → 0.8.0` (the RFC literal `0.6.0 → 0.7.0` is superseded by an intervening PE bump — see spec D5 AC) and `marketplace.json` re-aggregates. Verifies the D5 cross-pack ACs.

**Approach:** edit `voice-and-microcopy/SKILL.md` to add the screen-flow consumption (copy per screen × state) + degrade path; add the cross-links; bump PE minor; re-aggregate.

**Done when:** copy keys to the screen flow when present, cross-links resolve both ways, PE at `0.8.0`.

### T14: changelog + specs README + final marketplace/lint close-out

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13

**Tests:** (goal-based)
- **Design-flow thread completeness:** walking the connective skills' `SKILL.md` input/`Consumed by:` declarations against the RFC § D2 producer→consumer table resolves end-to-end (journey → screen flow → service / per-screen design → copy → review → realization; `map-internal-process` the inside-out sibling) with **no node naming a consumer/producer that does not exist**. Verifies the cross-cutting design-flow-completeness ACs.
- `docs/product/changelog.md` `[Unreleased]` records the rename + new skills/agent/handover + PE wiring.
- `docs/specs/README.md` lists `experience-pack`; this spec's `Status:` flips to Shipped with ACs checked.
- `make build` clean; `python tools/lint-experience-agnostic.py` clean across the whole pack; `python .claude/skills/work-loop/scripts/lint-spec-status.py` clean. Verifies the governance ACs.

**Approach:** verify the thread (read the seams); write the changelog entry; update the specs README active list; flip the spec to Shipped + check ACs in the implementing PR (per the set-final-status-in-implementing-PR discipline); final re-aggregation + lint sweep.

**Done when:** the flow thread resolves end-to-end, changelog + README updated, spec Shipped, all gates green.

## Rollout

- **Delivery:** big-bang within the catalogue, but **reversible** — pure-markdown method + manifests, no stateful infra. The one irreversible-feeling step is the dir rename, mitigated by the ADR-0038 bridge and the proven `contract-acquisition` no-alias precedent.
- **Infrastructure:** none — no compute/storage/queues/secrets/IAM. The pack is habits-not-infra.
- **External-system integration:** none required at build time. The D8 handover *optionally* drives a design-tool MCP at *use* time (detect-and-degrade), never a build-time dependency.
- **Deployment sequencing:** T1 (rename + lint retarget) must land before any new skill so the agnosticism lint stays green; T2/T3 (floor + layout) before the skills that reference them; T11 (reviewer) after the artifacts it reviews exist; T14 closes out. Adopters with an installed `design-craft` reinstall as `experience` (no silent break — the pack is method, not stateful).

## Risks

- **The rename breaks CI mid-migration** if the lint retarget lags the dir move (the lint errors when its scan root is gone). Mitigation: T1 lands both together; its `Done when` is the lint passing against `packs/experience/`.
- **A new skill leaks a values table.** Mitigation: the renamed agnosticism lint runs after every skill task (cross-cutting integration test) and in both CI workflows.
- **Scope creep into sibling efforts** (traceability lint, discovery loop, user-research producer). Mitigation: the spec's `Never do` / `Ask first` boundaries name each explicitly; this plan ships only the briefs that carry the edges, not the enforcers.
- **PE version collision on rebase** — PE moved to `0.7.0` independently; if another PR bumps it again before this lands, T13's `0.7.0 → 0.8.0` may need re-pinning. Mitigation: T13 bumps from PE's *then-current* version, not a hardcoded literal.

## Changelog

- 2026-06-29: initial plan — RFC-0050 (Accepted) D1–D10, one implementing spec, 14-task DAG (rename → shared substrates → skills → enhancements → reviewer → evals → cross-pack → close-out).
