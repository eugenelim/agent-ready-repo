# Spec: experience-pack

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0050, ADR-0038, ADR-0042, ADR-0030, ADR-0028, RFC-0040, RFC-0037, RFC-0033 (frozen, bridged), ADR-0024 (frozen, bridged)
- **Brief:** none
- **Contract:** none — the pack ships pure-markdown method + a forked-context reviewer agent; no API/event/RPC interface surface. The per-screen brief and the design-tool handover are markdown artifact *templates* (skill `assets/`), not versioned interface contracts.
- **Shape:** mixed — a pack rename (dirs/manifests/CI-lint), five new pure-markdown skills, two enhanced skills, one reviewer agent, an eval surface, a layout table, and a cross-pack skill edit. No application LLD; the design work is method-authoring, not a runtime.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product team gets the catalogue's design/UX seat as the **`experience` pack** —
the grown-up successor to `design-craft`. `design-craft` ships four craft skills
that design *a* screen but leaves the connective layer (outcome → journey →
screen → backing service), the behavioral pillar (how an interaction behaves),
and the internal-business-process view unaddressed, and its name undersells the
seat. Success is: an adopter (or an autonomous agent invoking the pack) can map a
customer journey, derive and brief the screen set it implies, blueprint the
backing services, map an internal business process, ground aesthetic taste in a
stable referent, design how each screen *behaves*, hand a screen off to a
generative design tool, and have all of it independently reviewed by a
forked-context UX reviewer — as **one complete, walkable design-flow thread**
whose completeness is proved by a non-droppable steel-thread walk (no broken
link from journey to realization), and **without** any skill reprinting a values
table, adding a runtime/hook/validator, or authoring a pixel comp. The pack is renamed
in place (no install-time alias; frozen governance bridged by the already-accepted
ADR-0038), and every new skill is standalone-useful and detect-and-degrades on its
upstream and downstream dependencies. This spec is the **implementing contract for
RFC-0050 (Accepted 2026-06-29), decisions D1–D10**; it builds the pack, not the
discovery loop, traceability lint, or user-research producer (RFC-0048 sibling
efforts / a deliberately deferred owner).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit pack **sources** under `packs/experience/.apm/...` and `packs/experience/.claude-plugin/...`, then re-aggregate `marketplace.json` (`make build` / `build-self` as the manifests require). `experience` is user-scope-default, so it aggregates into `marketplace.json` but is **not** projected into this repo's working tree (no `.claude/` projection change — per the self-host scope).
- Keep every skill **pure-markdown** — `SKILL.md` + `references/` + `assets/` only, no adapter-specific primitives — so each projects to every adapter `design-craft` already supported (`claude-code`, `codex`, `copilot`, `kiro-ide`, `kiro-cli`, `cursor`, `gemini`).
- **Point to** external standards (WCAG, W3C tokens, Apple HIG, Material 3, MDN responsive, APQC PCF, BPMN 2.0, BABOK, Nielsen heuristics, Laws of UX) — never reprint their values (breakpoints, HIG spacing, token sets, the APQC framework text, BPMN XML).
- Run the renamed framework-agnosticism lint against `packs/experience/` after every skill edit; it must stay clean.
- Make each new skill **standalone-useful** (elicit its inputs inline when upstream product artifacts are absent) and **detect-and-degrade** (name services/components textually when `architect`/`contracts` are not installed; behave as today when a downstream artifact is absent).
- Resolve every durable artifact path through the three-tier layout contract (config → `docs/design` default → discover-by-marker), never hardcoded.

### Ask first

- Any edit to **frozen governance** beyond the ADR-0038 bridge — RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, or the `docs/rfc` / `docs/specs` README index rows that name `design-craft` as historical record.
- Introducing an **install-time pack alias / rename mechanism** (none exists; inventing one is a separate distribution RFC, not this spec).
- Widening the pack's surface beyond RFC-0050 D1–D10 — e.g. authoring a **user-research producer** skill (deliberately deferred to its owning effort), or carrying the platform/surface axis on `map-internal-process` (it is actor/swimlane-shaped, not device-shaped).
- Changing the `voice-and-microcopy` **home** — it stays in `product-engineering`; only its procedure and the cross-link change.

### Never do

- Reprint a **values table** — fixed breakpoints, HIG/Material spacing or token sets, easing curves, hex/px/ms values, or the APQC framework text / full BPMN XML. Point to the source; let the method derive the value.
- Add a **hook, engine, in-pack validator, daemon, or any runtime** — the pack stays habits-not-infra (ADR-0024 posture, unchanged). The autonomous-agent substrate is a deployment target, never built here (Principle 3).
- Author **pixel comps / Figma files** — the pack authors design *intent* and a *handover instruction set*; realization stays the design tool's / a human's job. The D8 handover is instructions keyed to the brief, never a comp.
- **Name a winning design tool** — the D8 handover names tool *categories* (Figma AI, Claude, v0, …), endorses none, requires none.
- Name the reviewer agent so that it **embeds `design-reviewer`** (architect's) as a substring — it is `experience-reviewer`, with a `description:` leading with a design-time-only cue.
- Build a **sibling effort's surface** — the traceability lint (RFC-0048 D6), the discovery loop / `discovery-lead` (RFC-0048 D8), or `Domain Framing` / self-coverage gates. This spec ships the briefs that *carry* those edges, not the enforcers.

## Testing Strategy

This spec adds pure-markdown method + a reviewer agent + a CI-lint rename — there
is no application logic with a compressible invariant, so **no TDD**. Two modes:

- **Goal-based check** — the dominant mode. The rename, layout table, manifest
  bumps, marketplace re-aggregation, lint rename/retarget, eval-file presence,
  and cross-link wiring are each verified by a one-liner (`ls`/`grep`/`make
  build`/the renamed lint's own self-test/`run-pack-evals.py`). Don't write a
  test that asserts what the build or the agnosticism lint already proves.
- **Visual / manual QA** — for every artifact a user (or agent) invokes directly:
  each new/enhanced **skill** is exercised end-to-end through its documented happy
  path (a cold prompt produces the artifact at the resolved layout path, with the
  platform axis / per-screen brief / as-is-to-be content the skill promises), and
  the **`experience-reviewer` agent** is dispatched against a sample journey +
  screen flow and observed to return severity-tagged findings against the
  grounded reference + platform fit + cross-brief coherence + the full quality
  floor. The activation **evals** (trigger + Tier-4 judge) are the automated
  surface of this mode, run by `tools/run-pack-evals.py`.

The framework-agnosticism lint rename is verified **goal-based** by its own
renamed self-test (`tools/test-lint-experience-agnostic.py`) plus a clean run
against `packs/experience/`.

## Acceptance Criteria

### Design-flow completeness (the cross-cutting bar)

- [ ] The pack's skills form a **complete, walkable design-flow thread** with no broken link: journey (`map-customer-journey`) → screen flow + per-screen briefs (`map-screen-flow`) → backing services (`blueprint-service`) → per-screen design (the craft skills + `interaction-design`, applied to each brief) → copy (`voice-and-microcopy`) → review (`design-critique` + `experience-reviewer`) → realization (the D8 handover); `map-internal-process` is the inside-out sibling. Each adjacent pair connects by a **named seam** — verifiable by reading each connective skill's `SKILL.md` input + `Consumed by:` declarations (required in D2) against the RFC § D2 producer→consumer table; no node names a consumer/producer that does not exist.
- [ ] The thread is **proved complete by the steel thread** (see D4): `map-screen-flow` always runs the whole-journey walk asserting every transition resolves and every action has a backing service. This verification is **load-bearing and non-droppable** — it is the pack's guarantee that being coarser-grained than maximalist design-skill catalogues never leaves a *flow* gap.
- [ ] The one input the pack does **not** produce — **generative user research** (personas, usability testing) — is consumed by detect-and-degrade (each connective skill elicits inline when it is absent), so no skill *blocks* on it; it is a named deferral (Assumptions / RFC-0050 Open questions), not a silent hole.

### D1 — rename `design-craft → experience`

- [ ] `packs/experience/` exists with all skill content moved under it; `packs/design-craft/` no longer exists.
- [ ] `pack.toml` and `.claude-plugin/plugin.json` carry `name = "experience"`, a refreshed `display_name`/`description`, and **version `0.2.0`**.
- [ ] `.claude-plugin/marketplace.json` aggregates the `experience` entry (name, displayName, description, links, documentation) and carries **no** `design-craft` entry; re-aggregation ran (`make build`/`build-self`).
- [ ] `docs/guides/design-craft/` is renamed to `docs/guides/experience/` and the `[pack.links].documentation` URL points to it.
- [ ] No install-time pack alias is added (grep-confirmed: no new rename/alias field in any manifest).
- [ ] Frozen governance (RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, the `docs/rfc`/`docs/specs` README index rows) is **not** edited; the rename is bridged by ADR-0038 (already Accepted) and a changelog entry.

### D1 — the framework-agnosticism CI lint

- [ ] `tools/lint-design-craft-agnostic.py` → `tools/lint-experience-agnostic.py` and `tools/test-lint-design-craft-agnostic.py` → `tools/test-lint-experience-agnostic.py`; the scan root is retargeted to `packs/experience/` and the override env var `DESIGN_CRAFT_ROOT` → `EXPERIENCE_ROOT` (the self-test sets it).
- [ ] Both CI steps (`build-check.yml`, `build-check-windows.yml`) name the renamed tool; the lint runs clean against `packs/experience/`.
- [ ] The two **provenance pointers stay pinned, not retargeted**: the RFC-0033 citation in the lint docstring and the `(design-craft-pack AC8)` tag in the CI step name (both point at frozen sources with no `experience` equivalent).

### D2 — the connective skills + shared quality floor

- [ ] Three new skills exist as pure-markdown `SKILL.md` + `references/` + `assets/`: `map-customer-journey`, `blueprint-service`, `map-screen-flow`; each projects to all seven allowed adapters.
- [ ] `map-screen-flow` produces a **screen flow** — the journey's screens *sequenced*, with transitions and **error/edge flows** (a failed action → which screen/state), the **per-screen state matrix** (deferring to the shared quality floor), and the platform axis — i.e. the *interaction flow across screens*, not a bare list; the enumerated screen inventory is the spine it is drawn over. (The *micro* interaction behavior within one screen is `interaction-design`'s, D10 — not this skill's; see D10.)
- [ ] Each connective skill is standalone-useful (elicits inputs inline when persona/outcomes/intents are absent) and detect-and-degrades (names services/components textually when `architect`/`contracts` are absent).
- [ ] Each connective skill's `SKILL.md` **declares its inputs and a `Consumed by:` seam** (the downstream artifact/skill it feeds), so the flow thread is readable end-to-end (the verification target for the design-flow-completeness AC above).
- [ ] `quality-floor.md` is promoted from `design-critique/references/` to a **pack-shared `references/` location**, with **all three sections intact** — handle-all-states, the accessibility floor (WCAG pointed-to), and reduced-motion; `map-screen-flow`, `interaction-design`, and `voice-and-microcopy` defer to the one shared floor (no private sibling copy).
- [ ] `permission/denied` is documented as an *additional* gated-screen state extending the floor, not a replacement list.

### D3 — the platform/surface axis

- [ ] `map-customer-journey`, `map-screen-flow`, and `aesthetic-direction` each carry a `surface` value (`responsive-web | iOS | Android | cross-platform`) that changes *what the method asks* (consult Apple HIG / Material 3 / MDN responsive / shared-then-adapt), and **points to** those standards — grep-confirmed: no reprinted breakpoint/HIG/Material values.
- [ ] `map-internal-process` does **not** carry the platform/surface axis.

### D4 — the per-screen brief

- [ ] `map-screen-flow` emits **one per-screen brief per screen** using the `0048-notes/07` brief format carried in its `assets/`, split into a **shared design contract** (referenced, not copied, by every brief) and a **per-screen spec**.
- [ ] `map-screen-flow`'s procedure ends in a **cross-brief consistency pass** (shared components reused, states uniform, copy voice aligned, navigation non-contradictory) and then a **whole-journey verification that always runs** — a low-fi prototype via MCP when a tool is present, **else the text-only steel thread** (a scripted walk through the briefs in journey order asserting *every transition resolves* and *every action has a backing service*). The steel thread is the **non-droppable floor**: it degrades from prototype → text-only, never to nothing, so `map-screen-flow` never ends at "briefs emitted."

### D5 — grounded `aesthetic-direction`, taste-mode `design-critique`, `voice-and-microcopy` wiring

- [ ] `aesthetic-direction` grounds each named goal in a stable referent (persona + precedent + standards + platform conventions) and records *what grounds each goal*; it stays method-not-values (no palette/font/value printed).
- [ ] `design-critique` gains a **taste mode** (evidence-grounded critique against the grounded aesthetic reference + platform fit) and stays an **interactive authoring-time skill** — not a reviewer agent, and explicitly not "fresh-context".
- [ ] `voice-and-microcopy` (resident in `product-engineering`) consumes the screen flow's per-screen state matrix when present (copy per screen × state, keyed to it) and behaves as today when absent; the `experience` and `product-engineering` READMEs cross-link each other.
- [ ] `product-engineering` takes a minor version bump (**`0.7.0 → 0.8.0`** — its current version, the RFC's literal `0.6.0 → 0.7.0` predates an intervening PE bump).

### D6 — path resolution

- [ ] `pack.toml` ships `[pack.layout.repo] parent = "docs/design"`; there is a new `[experience]` table in the adopter-owned `agentbundle-layout.toml` contract, resolved config → default → discover-by-marker (frontmatter `type:` `customer-journey`/`service-blueprint`/`screen-flow`/`process-flow`).
- [ ] Each new artifact-writing skill ships a `references/agentbundle-layout.md` documenting the table; file-per-slug shapes match the RFC (`journeys/`, `blueprints/`, `screens/<slug>-flow.md` + `screens/<slug>/<screen>.md`, `processes/<slug>.md`); each skill surfaces the resolved path before its first write and creates its dir lazily.

### D7 — the `experience-reviewer` agent

- [ ] An `experience-reviewer` agent exists under `packs/experience/.apm/agents/`: forked-context, read-only, flags-never-rewrites; its name is **not** a substring of `design-reviewer` or any core/discovery reviewer.
- [ ] Its `description:` **leads with a design-time-only cue** (reviews journey / screen-flow / per-screen-brief / aesthetic artifacts; never code diffs; never architecture design docs).
- [ ] Its review list carries the grounded aesthetic reference (D4) + platform fit (D3) + cross-brief coherence (the D4 consistency pass) + the **full quality floor — handle-all-states, accessibility, and reduced-motion** (the promoted three-part floor; accessibility is the only independent a11y check between human-value-add gates).
- [ ] The agent ships its eval surface per the agent-eval shape.
- [ ] RFC-0048's lens-team roster (line 236) reflects UX/design as *skill + an opt-in forked `experience-reviewer`* — a tracked amendment **within RFC-0048, which is still Open**; this spec verifies the reconciliation holds at build time (see the RFC-0048-Open assumption below for D7's load-bearing-vs-optional conditional).

### D8 — the optional design-tool handover

- [ ] `map-screen-flow` can emit an **optional** design-tool handover keyed to each per-screen brief (job · states · layout intent · navigation · copy pointer · platform surface · grounded aesthetic reference), detect-and-degrade: a design-tool MCP present → trigger it; absent → emit the handover file at `<parent>/screens/<slug>/<screen-name>.handover.md` for paste.
- [ ] The handover is **instructions, never pixels/values**; it names tool *categories*, endorses/requires none — grep-confirmed clean under the agnosticism lint.

### D9 — `map-internal-process`

- [ ] A `map-internal-process` skill exists in `experience` (pure-markdown, agnostic): anchored on the **APQC L3 process → L4 activities** (L5 tasks out of scope), carrying **as-is + to-be** with an as-is→to-be delta table, a SIPOC scoping table, a swimlane flow in mermaid (`flowchart` + `subgraph` lanes), and a pain/waste register; it points to APQC PCF / BPMN 2.0 / BABOK, reprinting none.
- [ ] It writes to `<parent>/processes/<slug>.md` (frontmatter `type: process-flow`), cross-references the service blueprint by-name when a process is customer-triggered, and is the producer of `frame-intent`'s "current-state process map" input.
- [ ] The journey skill is named `map-customer-journey` (customer/end-user-scoped; employee-journey mapping is out of v1).

### D10 — the `interaction-design` craft skill

- [ ] An `interaction-design` craft skill exists (pure-markdown, agnostic) — **one coarse skill covering the pillars**, not a fan-out: feedback & response (incl. the Doherty-Threshold perceived-performance lens, design-time only), input & forms, **component/screen state machines** (statechart-modeled, authored as a mermaid `stateDiagram-v2` in the brief — **no state-management library reprinted**), **motion & micro-animations** (purposeful motion that communicates state, pointing to Material/HIG motion guidance, **honoring the quality floor's reduced-motion rule** and **reprinting no durations/easing/curves**), navigation-as-behavior, gesture & pointer affordances (on the D3 platform axis), and cognitive-law fit (cross-referencing `design-critique`'s `heuristics.md` + Laws of UX, not duplicating).
- [ ] It **references** (points to, does not author as standalone skills) recognized **onboarding** (progressive onboarding, empty-state-as-onboarding, coachmarks) and **search-interaction** (typeahead, faceted filtering, zero/error results) pattern families a per-screen brief can invoke.
- [ ] It **enriches the per-screen brief** (the interaction/behavior section) and **defers to the shared quality floor** rather than emitting its own file-per-slug artifact, so it needs **no new D6 layout entry**.
- [ ] It is demonstrably distinct from `layout-and-information-architecture` (structure/wayfinding), `aesthetic-direction` (visual taste), and — the load-bearing carves — the **quality floor** and **`map-screen-flow`**: the three state homes are the quality floor (the state *set* / reduced-motion *rule*), `map-screen-flow` (the *cross-screen* routing), and `interaction-design` (the *in-component* state machine + motion + feedback). Macro-flow (`map-screen-flow`) vs micro-behavior (`interaction-design`), since both touch states/transitions/errors.

### Packaging, evals & governance

- [ ] `[pack.evals].skills` gains the new authoring skills (`map-customer-journey`, `blueprint-service`, `map-screen-flow`, `map-internal-process`, `interaction-design`); each ships `evals/eval_queries.json` (trigger) + `evals/evals.json` (Tier-4 judge). `run-pack-evals.py` measures them.
- [ ] `[pack.install]` is unchanged (user-scope default; same `allowed-adapters`; declared order load-bearing).
- [ ] A `docs/product/changelog.md` `[Unreleased]` entry records the rename + the new skills/agent/handover + the PE wiring.
- [ ] `docs/specs/README.md` lists `experience-pack` in the active list.

## Assumptions

- Process: RFC-0050 is **Accepted** (2026-06-29); its D1–D10 are the binding decisions this spec implements (source: `docs/rfc/0050-the-experience-pack.md`, this PR).
- Process: the two follow-on ADRs already exist and are **Accepted** — ADR-0038 (the rename + frozen-governance bridge) and ADR-0042 (the agent-addition policy superseding ADR-0023, within which D7 is decided) (source: `docs/adr/0038-*.md`, `docs/adr/0042-*.md`).
- Process: RFC-0048 — the home of the *agent-autonomous-where-possible* posture, and of the lens-team roster D7 amends — is still **Open**. So D7 ships the `experience-reviewer` as **load-bearing under that stated posture** (RFC-0050:194, "one honest dependency"), with ADR-0042's **admissible-but-optional** standing as the fallback if the posture is not ratified at RFC-0048's acceptance. The roster line (RFC-0048:236) is therefore a tracked amendment within an as-yet-unaccepted RFC — a reviewer of the build PR should know the reconciliation target can still move (source: `docs/rfc/0048-*.md` Status; RFC-0050 § D7 / "One honest dependency").
- Technical: `design-craft` is at `v0.1.1`; the rename bumps it to `v0.2.0` under the new identity (source: `packs/design-craft/pack.toml`, `.claude-plugin/plugin.json`).
- Technical: `product-engineering` is **already at `v0.7.0`**, so its minor bump for the `voice-and-microcopy` wiring is `0.7.0 → 0.8.0` — the RFC's literal `0.6.0 → 0.7.0` predates an intervening PE bump and is recorded here as superseded (source: `packs/product-engineering/pack.toml`).
- Technical: the agnosticism lint is `tools/lint-design-craft-agnostic.py` (+ self-test), scan root hardcoded to `packs/design-craft/`, override env `DESIGN_CRAFT_ROOT`, wired into both CI workflows; it errors when its scan root is absent (source: `tools/lint-design-craft-agnostic.py`, `.github/workflows/build-check*.yml`).
- Technical: the canonical quality floor lives at `packs/design-craft/.apm/skills/design-critique/references/quality-floor.md` and is three-part (states + accessibility + reduced-motion) (source: that file; RFC-0050 § D2).
- Technical: the per-screen brief format and the connective-artifact research are in `docs/rfc/0048-notes/04`, `/07`, `/09` (source: RFC-0050 § Proposal / Evidence).
- Technical: `experience` is user-scope-default, so it aggregates into `marketplace.json` but is not projected into this repo's working tree — the local gate is `lint-packs` + `validate` + `build` (marketplace re-aggregation) + `pytest`, not `build-self`/`pre-pr` (source: self-host pack scope; `packs/design-craft/pack.toml [pack.install]`).
- Technical: the reviewer agent follows the forked-context, read-only, flags-never-rewrites shape of architect's `design-reviewer` (source: `packs/architect/.apm/agents/design-reviewer.md`).
- Product: this spec builds the `experience` pack only — not the RFC-0048 discovery loop / `discovery-lead`, the traceability lint (RFC-0048 D6), or a user-research producer; those are sibling efforts or a deferred owner (source: RFC-0050 § Not in scope / Open questions).
