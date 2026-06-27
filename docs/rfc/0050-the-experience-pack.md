# RFC-0050: the `experience` pack — rename `design-craft`, add the connective UX skills, and ground taste

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:**
- **Related:** **RFC-0048** (the autonomous product-team operating model — this is its child-1, the `experience`-pack effort; Decision 3 adopted everything below at the foundation level, this RFC *models it out*) · RFC-0033 (`design-craft` pack — the pack being renamed and grown; **frozen, bridged by ADR-0038**) · ADR-0024 (`design-craft` agnosticism + all-skills-zero-agents posture — **frozen, bridged by ADR-0038**) · RFC-0047 § Errata 2026-06-25 (the *actual* `infra-contract-acquisition → contract-acquisition` rename — the dirs+erratum, no-alias precedent this migration follows) · RFC-0040 / ADR-0030 (`agentbundle-layout.toml` path-resolution contract) · RFC-0037 / ADR-0028 (pack-activation-evals) · RFC-0030 (`product-engineering` — `voice-and-microcopy`'s home) · RFC-0032 / ADR-0023 (the `design-reviewer` subagent + the "three reviewers is a code-review ceiling" reading) · RFC-0004 (install-scope-per-pack, Rail A) · promoted research in [`0048-notes/04`](0048-notes/04-artifact-inventory.md), [`/06`](0048-notes/06-pack-delta-and-orchestration.md), [`/07`](0048-notes/07-screen-brief-format.md), [`/09`](0048-notes/09-gap-resolutions.md)

## The ask

**Recommendation (BLUF).** Grow the catalogue's design/UX seat into the **`experience` pack** — rename `design-craft → experience`, add three **connective** UX skills (`map-journey`, `blueprint-service`, `inventory-screens`) that turn outcomes into journeys into screens into backing services, **ground** `aesthetic-direction` and add a **taste mode** to `design-critique`, and **wire `voice-and-microcopy`** (which stays in `product-engineering`) to the screen inventory. All **pure-markdown skills, zero new agents, no runtime** — the `design-craft` posture (ADR-0024) preserved. This is **child-1 of RFC-0048**; that RFC already *decided* this set (Decision 3), so this RFC models it to buildable depth and runs the series lifecycle, it does not re-open the choices.

**Why now (SCQA).** *Situation:* `design-craft` (RFC-0033) ships four framework-agnostic craft skills — `aesthetic-direction`, `design-system-foundations`, `layout-and-information-architecture`, `design-critique` — that design *a* screen. *Complication:* RFC-0048 traced a worked example end-to-end and found the **connective UX layer missing** — nothing turns an outcome into a journey, a journey into a screen inventory, or a screen into its backing service ([`0048-notes/04`](0048-notes/04-artifact-inventory.md)); `voice-and-microcopy` is words-only and not tied to any screen list; and the pack's name undersells the seat. *Question:* can we add the connective layer (and rename the seat) without violating the pack's two load-bearing guardrails — **stack-neutrality** (no values tables) and **all-skills-zero-agents** (ADR-0024) — and keep the pack standalone-useful?

**Decisions requested.**

1. **Rename `design-craft → experience`.** Migrate via the **`contract-acquisition` precedent** (RFC-0047 § Errata): rename the dirs + `name` + manifests + cross-links + the guides dir + the layout key; **no install-time alias** (none exists, grep-confirmed by RFC-0048); frozen governance (RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, README index rows) keeps `design-craft` as historical record, **bridged by ADR-0038**. · *why:* `experience` names the seat better than `design-craft`, and v0.1.1 user-scope keeps migration cheap. · decide-by: RFC accept (records **ADR-0038**).
2. **Add three connective skills** — `map-journey`, `blueprint-service`, `inventory-screens` — pure-markdown, no new agents, framework-agnostic intent specs. Each carries the **platform/surface axis** where it applies; `inventory-screens` **emits one per-screen brief per screen**. · decide-by: RFC accept.
3. **Carry the platform/surface axis** (responsive web · iOS · Android · cross-platform) on `map-journey`, `inventory-screens`, and `aesthetic-direction`, grounded in **platform conventions** (HIG / Material 3 / responsive breakpoints / PWA) — *pointed to, never reprinted* (the stack-neutral guardrail holds). · decide-by: RFC accept.
4. **Ground `aesthetic-direction`** in persona + precedent + standards + platform conventions (a stable taste referent), and **add a taste mode to `design-critique`** (evidence-grounded critique against that referent + platform fit). `design-critique` stays an **interactive skill, not a reviewer agent** — the live-lens reviewer (RFC-0048 O5) is `core`/`architect`'s seat, out of this RFC. · decide-by: RFC accept.
5. **Wire `voice-and-microcopy`** (resident in `product-engineering`) to consume the screen inventory's per-screen state matrix (closes RFC-0048 GAP-C1), and cross-link the two packs. · decide-by: RFC accept.
6. **Resolve artifact paths config → default → discover-by-marker** (never hardcoded): a new `[experience]` table in `agentbundle-layout.toml` (default `parent = "docs/design"`), mirroring `product-engineering`'s pattern (RFC-0040). · decide-by: RFC accept.

*Default if no objection: adopt all six. Each is already decided at the foundation level by RFC-0048 Decision 3; this RFC's job is to model them, pressure-test them, and reconcile any drift back into RFC-0048 (the series-execution standard, RFC-0048 Decision 9).*

## Problem & goals

**Diagnosis.** `design-craft` designs *a* screen well but cannot answer the questions a product team asks *before* a screen exists:

- **No journey.** Nothing maps the outcome to the stages and actions a user moves through — so screens get invented, not derived.
- **No screen↔service tie.** Nothing connects a screen's actions to the backing services that fulfil them, so a screen can be designed that nothing can build (RFC-0048's reconciliation gap).
- **No enumerated, sequenced screen set.** `design-craft` has no notion of "the screens this product needs," their order, or their per-screen states — so `voice-and-microcopy` has nothing to attach copy to (GAP-C1), and there is no unit a per-screen generation step can consume.
- **The name undersells the seat.** "design-craft" reads as visual polish; the seat is the whole **experience** — flow, service, screen, taste, and words.

**Goals.**
- Add the **connective layer** (journey → screen inventory → service blueprint) as pure-markdown intent specs the build and the tech packs consume.
- **Ground taste** so aesthetic judgment runs against a stable referent (persona + precedent + standards + platform), not fresh opinion (Kahneman: valid intuition needs a stable referent — [`0048-notes/05`](0048-notes/05-judgment-decomposition-and-phases.md); primary citation in RFC-0048 § Evidence).
- Emit a **per-screen brief** self-contained enough to generate one screen in isolation, yet carrying the connective context so the whole stays coherent ([`0048-notes/07`](0048-notes/07-screen-brief-format.md)).
- Keep every skill **standalone-useful** (detect-and-degrade on the upstream product artifacts) and **stack-neutral**, and ship **zero new agents**.

**Non-goals** (could-have-been-goals, deliberately dropped):
- **A new reviewer agent.** `design-critique`'s taste mode is a *mode of the existing interactive skill*; the design-artifact live-lens reviewer (RFC-0048 O5) lives on `core`'s `security-reviewer`/`quality-engineer` and `architect`'s `design-reviewer` — separate efforts, not this pack (preserves ADR-0024's all-skills-zero-agents posture and RFC-0032's "three reviewers is a *code-review* ceiling" reading).
- **An install-time pack alias.** No pack-level rename/alias field exists (grep-confirmed, RFC-0048); inventing one is a distribution-mechanism RFC, not this one. We follow the `contract-acquisition` precedent: rename + erratum, no alias.
- **Pixel comps / Figma files.** Agents author design **intent specs** (markdown/mermaid/tables); a designer or UI-codegen realizes them (the `design-craft` framing, unchanged).
- **Values tables.** No fixed breakpoints, HIG spacing, or Material token sets reprinted — the platform axis *points to* the conventions, the method derives the values (RFC-0033's guardrail).
- **The traceability lint / Domain Framing + Scope Boundary / self-coverage gate.** Those are RFC-0048's sibling child efforts (Decisions 4–6); this RFC *consumes* their contracts (the per-screen brief's traceability columns) but builds none of them.
- **Building the discovery loop or `discovery-lead`.** The connective skills are invoked by a human designer today and by `discovery-lead` once it ships (RFC-0048 D8) — this RFC makes them work either way.

## Proposal

The detail cascades under each decision. The full producer→consumer artifact inventory is [`0048-notes/04`](0048-notes/04-artifact-inventory.md); this RFC models the `experience`-pack rows of it.

### D1 — rename `design-craft → experience`

**Mechanism (the `contract-acquisition` precedent, verified at RFC-0047 § Errata 2026-06-25).** The live surface is renamed; frozen governance keeps the old name as historical record, bridged by a new ADR. No install-time alias.

*Renamed (the live surface):*
- `packs/design-craft/` → `packs/experience/` (the pack dir and everything under it).
- `pack.toml` `name = "experience"` + `display_name` + `description`; `.claude-plugin/plugin.json` `name`/`description`.
- `.claude-plugin/marketplace.json` — the aggregated pack entry (`name`, `displayName`, `description`, links, `documentation`).
- `docs/guides/design-craft/` → `docs/guides/experience/` and the `[pack.links].documentation` URL.
- The `agentbundle-layout.toml` section key: the new `[experience]` table (D6) is the layout key from the start; there is no `[design-craft]` table shipped today, so this is a fresh key, not a rename.
- **The framework-agnosticism CI lint** — `tools/lint-design-craft-agnostic.py` hardcodes the scan root `packs/design-craft/` (`:147`) and **errors when that root is gone** (`:154`); it, its self-test `tools/test-lint-design-craft-agnostic.py`, and both CI steps (`build-check.yml:440`, `build-check-windows.yml:173`) name `design-craft`. The migration **renames the tool + self-test to `lint-experience-agnostic.py` / `test-lint-experience-agnostic.py`, retargets the scan root to `packs/experience/`, renames the `DESIGN_CRAFT_ROOT` override env var to `EXPERIENCE_ROOT` (the self-test sets it), and updates the two CI step descriptors** — so the stack-neutral guardrail this RFC leans on (D3, and the pre-mortem) keeps enforcing at the exact moment the three platform-axis skills land. **Two provenance pointers stay pinned to their frozen sources, not retargeted:** the RFC-0033 citation in the lint docstring, and the `(design-craft-pack AC8)` tag in the CI step name — both point at frozen governance (RFC-0033, the Shipped `design-craft-pack` spec) and there is no `experience` spec/AC to repoint them to; only the tool filename, scan root, env var, and leading descriptor change.
- README, cross-links in the new and existing skills, and this RFC's implementing spec / changelog / backlog.

*Kept as historical record (frozen governance — NOT edited, bridged by ADR-0038):* RFC-0033 (created the pack), ADR-0024 (its agnosticism + posture decision), the Shipped `docs/specs/design-craft-pack/` spec, and the `docs/rfc` / `docs/specs` README index rows that name `design-craft`. Each names `design-craft`; **that is the same pack, now `experience`**, bridged once in ADR-0038 (and the changelog) — exactly as RFC-0047's erratum bridged frozen RFC-0044 for the skill rename.

*No install-time alias* — an installed `design-craft` is uninstalled/reinstalled as `experience` by the adopter; v0.1.1 + user-scope-default + a pre-stable version (RFC-0048's blast-radius note: version is a recency signal, not an install-count one) keep the tail short. **Version: `0.1.1 → 0.2.0`** (minor — three new skills + enhancements, under a new pack identity).

### D2 — the three connective skills

All three are **pure-markdown SKILL.md + `references/` + `assets/`**, no adapter primitives, no agents — so they project to every adapter `design-craft` already supports. Each is **standalone-useful**: it elicits its inputs inline when the upstream product artifacts (persona, outcomes, intents) are absent, and **degrades** when downstream packs (`architect`, `contracts`) are not installed (it names services/components textually rather than emitting C4/contracts).

| Skill | Produces | Grounded in | Consumed by |
| --- | --- | --- | --- |
| **`map-journey`** | a **journey map** — stages × actions / emotions / pains / opportunities (frontstage), with the **platform/surface axis** | NN/g journey mapping; Patton user-story mapping; Torres opportunity-solution tree ([`0048-notes/01`](0048-notes/01-research-consolidation.md)) | `inventory-screens`, `blueprint-service` |
| **`blueprint-service`** | a **service blueprint** — frontstage / line-of-visibility / backstage / support — the screen↔service tie | NN/g service blueprints ([verified](https://www.nngroup.com/articles/service-blueprints-definition/)) | `architect` (backstage → C4 + contracts); the spec LLD |
| **`inventory-screens`** | a **screen inventory + per-screen state matrix** (states **defer to the shared handle-all-states floor**), the **platform/surface axis**, and **one per-screen brief per screen** | the screen briefs ride the `0048-notes/07` template; states from the shared handle-all-states floor (today `design-critique/references/quality-floor.md`) | `aesthetic-direction` / `design-system-foundations` / `layout-and-information-architecture`; `voice-and-microcopy` |

`map-journey` → `inventory-screens` → `blueprint-service` is the natural order, but each runs alone. `blueprint-service`'s backstage column is the **slicing instrument** RFC-0048 names (each backstage service → a component); its hand-off to `architect`/`contracts` is by-reference (a named service), not an import.

**Shared handle-all-states floor.** The canonical state set lives today in `design-critique`'s `references/quality-floor.md` (the floor RFC-0033 shipped: empty / loading / error / success / partial / disabled). With three more skills now consuming it, the implementing spec **promotes it to a pack-shared reference** (the natural home is a pack-level `references/`, the existing cross-skill-reference pattern `aesthetic-direction` already uses), so `inventory-screens` and `voice-and-microcopy` defer to one floor rather than a private sibling reference. `permission/denied` is an **additional gated-screen state** (named in `0048-notes/07`), not a replacement list — it extends the floor, it does not fork it.

### D3 — the platform/surface axis

`map-journey`, `inventory-screens`, and `aesthetic-direction` each carry a **surface** value: `responsive-web | iOS | Android | cross-platform`. The axis changes *what the method asks*, not *what values it prints*:
- **iOS** → consult **Apple HIG** ([verified](https://developer.apple.com/design/human-interface-guidelines)) for navigation patterns, gestures, and platform affordances.
- **Android** → consult **Material 3** ([verified](https://m3.material.io/)) for its component vocabulary and adaptive-layout guidance.
- **responsive-web** → consult **responsive breakpoints / media queries** ([MDN, verified](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)) and, where installable, **PWA** conventions.
- **cross-platform** → design the shared intent once, then name the per-surface adaptations (the journey and screen list are shared; chrome/navigation/gestures adapt per surface).

The skills **point to** these standards (the way `design-craft` already points to WCAG / W3C tokens) and **never reprint** breakpoint tables or HIG spacing — the stack-neutral guardrail (RFC-0033) is preserved by construction.

### D4 — the per-screen brief

`inventory-screens` emits, per screen, the brief in [`0048-notes/07`](0048-notes/07-screen-brief-format.md) (its `assets/` carries the template). The brief is a **split**:
- a **shared design contract** — authored once per product (by `aesthetic-direction` + `design-system-foundations` + the navigation model + the shared handle-all-states floor) and **referenced**, never copied, by every screen brief; this is what keeps N independently-generated screens coherent;
- a **per-screen spec** — this screen only (job, states, data, actions, copy pointer).

Coherence is enforced by three things, only one of which this RFC ships: (a) every brief references the *same* contract (shipped here); (b) the **traceability lint** (RFC-0048 D6, sibling effort) checks every action → a named service and every screen → a journey step; (c) `design-critique` reviews each generated screen against the contract and its neighbours (the taste mode, D5).

**Forward idea picked up (notes/07 § Consistency & prototyping; sample-bank notes/09).** `inventory-screens`' procedure ends not at "briefs emitted" but at a **cross-brief consistency pass** (shared components reused, states uniform, copy voice aligned, no contradictory navigation) and then **reaches for the cheapest whole-journey verification available** *before* G4: trigger a wireframe/prototyping tool via MCP to assemble a low-fi clickable prototype and walk the journey end-to-end, **or**, when no such tool is present, build a **text-only steel thread** (a scripted walk through the briefs in journey order asserting every transition resolves and every action has a backing service). The skill body teaches the model to reach for this unprompted — the modelling discipline RFC-0048's sample-bank logs, not just a feature.

### D5 — grounded `aesthetic-direction`, taste-mode `design-critique`

**`aesthetic-direction` (⊕).** Today it converges a felt vibe into ranked named goals. The enhancement **grounds** those goals in a stable referent — the **persona** (from the Domain Framing, or elicited inline if absent), **precedent** (a brief survey of comparable products' taste, refreshed only when the loop needs it), recognized **standards**, and **platform conventions** (D3). The recorded direction names *what grounds each goal*, so a later choice points back to a referent, not a fresh opinion. It stays method-not-values (no palette/font/value printed).

**`design-critique` (⊕).** Today it runs a heuristic + quality-floor evaluation. The enhancement adds a **taste mode**: an evidence-grounded critique of a screen against the **grounded aesthetic reference** + **platform fit**, run **fresh-context** (the design-side analog of an adversarial pass). The critique's rubric is reusable by the live-lens reviewer (RFC-0048 O5) — but `design-critique` itself stays an **interactive authoring-time skill, not a reviewer subagent** (ADR-0024; RFC-0032's ceiling reading). No new agent.

### D6 — path resolution (config → default → discover-by-marker)

The connective skills write durable artifacts; their paths resolve in **three tiers, never hardcoded** (RFC-0040 / ADR-0030, mirroring `product-engineering`'s `frame-intent`):

1. **Config** — the `[experience]` table of the adopter-owned `agentbundle-layout.toml` (repo-root overrides user-profile), `parent = "<base>"`.
2. **Designed default** — `parent = "docs/design"` (the pack's `[pack.layout.repo]` default; committed design docs, the natural home, paralleling `product-engineering`'s `docs/product`). No `[pack.layout.user]` default — output is per-repo, like `product-engineering`.
3. **Discover-by-marker** — if neither resolves and the adopter chose a different layout, search the workspace for the artifact's canonical filename + frontmatter `type:` (`type: journey-map` / `service-blueprint` / `screen-inventory`).

File-per-slug shapes under `<parent>`:
- `map-journey` → `<parent>/journeys/<slug>.md`
- `blueprint-service` → `<parent>/blueprints/<slug>.md`
- `inventory-screens` → `<parent>/screens/<slug>-inventory.md` + per-screen briefs `<parent>/screens/<slug>/<screen-name>.md`

A `references/agentbundle-layout.md` in each new skill documents the table (the `product-engineering` pattern); the pack ships the `[pack.layout.repo]` default in `pack.toml`; `init-project`/`adapt-to-project` seed the config; each skill creates its dir lazily on write and surfaces the resolved path before the first write.

### Cross-pack edit — `voice-and-microcopy` (D5/GAP-C1)

`voice-and-microcopy` **stays in `product-engineering`** (its home; RFC-0030). The edit: its procedure learns to **consume the screen inventory's per-screen state matrix** — when a screen inventory is present, it writes copy **per screen × state** keyed to the inventory, rather than ad-hoc; absent one, it behaves as today (detect-and-degrade). The `experience` README cross-links to `voice-and-microcopy` (and vice-versa), so the seat reads as one even though words live in PE. `product-engineering` takes a **minor bump (`0.6.0 → 0.7.0`)** for this.

### Packaging & evals

- `[pack.evals].skills` gains the three new skills (all user-triggered authoring skills); each ships `evals/eval_queries.json` (trigger evals) + `evals/evals.json` (Tier-4 judge rubric), per RFC-0037.
- `[pack.install]` is unchanged (user-scope default; same `allowed-adapters`, declared-order load-bearing).
- The enhancements to `aesthetic-direction` / `design-critique` are SKILL.md + `references/` edits — no new primitives, no contract bump.

### Migration path

One implementing spec lands: (1) the dir/manifest/guides/cross-link rename + the `0.2.0` bump + the marketplace re-aggregation (`make build` / build-self as the manifests require) + ADR-0038's frozen-governance bridge + a changelog entry; (2) the three new skills + their evals + the `[experience]` layout default; (3) the two enhancements; (4) the `voice-and-microcopy` wiring + PE bump. Existing repos with an installed `design-craft` reinstall as `experience`; no repo silently breaks (the pack is method, not stateful infra).

## Options considered

**Axis: how the connective UX layer + rename are *packaged*** — this exhausts the space from "do nothing" through "grow the existing pack" to "split into a new pack" to "fold into another pack."

| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Do nothing** | `design-craft` stays four craft skills; the connective layer never lands | Cost of delay: every product re-derives the journey→screen→service chain by hand; `voice-and-microcopy` stays unattached; RFC-0048's worked-example gap recurs. **Rejected.** |
| **B. Grow `design-craft` in place, no rename** | add the three skills + enhancements, keep the name | Lands the capability but leaves the name underselling the (now much larger) seat, and forfeits the cheap-rename window (v0.1.1). RFC-0048 D3 weighed this and chose the rename. **Rejected (the capability half is adopted; only the no-rename half is dropped).** |
| **C. Grow + rename to `experience`** ★ | this RFC | **Recommended.** One pack = one seat (ADR-0024); `experience` names it; the `contract-acquisition` precedent makes the rename a known, alias-free move; the capability is the missing connective layer. |
| **D. New separate `ux-flow` pack** | connective skills in a *new* pack, `design-craft` unchanged | Splits one seat across two packs an adopter must co-install; couples the journey skills away from the craft skills they feed; more catalogue surface for no benefit. **Rejected.** |
| **E. Fold the connective skills into `product-engineering`** | journey/blueprint/screens as PE skills | Conflates the product-intent seat with the design seat; `product-engineering` is already the heaviest pack; the design skills want the craft pack's stack-neutral guardrails. **Rejected** (only `voice-and-microcopy` stays in PE, because it already lives there). |

Prior art grounds the axis: RFC-0033 chose the one-pack-one-seat shape for `design-craft`; RFC-0047's erratum is the rename-without-alias precedent; the connective artifacts (journey / service blueprint / screen inventory) are the standard product-team UX ontology (NN/g, Patton, Torres — [`0048-notes/01`](0048-notes/01-research-consolidation.md)).

## Risks & what would make this wrong

**Pre-mortem.**
- *The rename breaks adopters.* `design-craft` is user-scope-default, so a rename touches every repo an adopter opened. **Mitigation:** the `contract-acquisition` precedent (rename + erratum, no alias) is proven; v0.1.1 + pre-stable bounds blast radius; the implementing spec re-aggregates the marketplace and bridges frozen governance in one PR.
- *The new skills become checklist ceremony* — a journey map that's a table nobody reads, a brief that's boilerplate. **Mitigation:** the skills require *substantive* per-stage / per-screen content (the RFC-0048 anti-ceremony rule), and `inventory-screens` ends in a real verification step (the consistency pass + steel-thread, D4), not "emitted."
- *The platform axis leaks values* — a skill starts printing breakpoints or HIG spacing. **Mitigation:** the stack-neutral guardrail (RFC-0033) is restated in each new skill's anti-patterns; the axis points to standards, never reprints them.
- *`design-critique`'s taste mode drifts into a reviewer agent* — re-creating the thing ADR-0024 declined. **Mitigation:** the taste mode is explicitly an interactive-skill mode; the live-lens reviewer is named as a *separate* (`core`/`architect`) effort.

**Key assumptions (falsifiable).**
- *The connective artifacts are agent-producible as intent specs* (markdown/mermaid/tables), not pixel comps — so a skill can author them. If journeys/blueprints genuinely need visual fidelity to be useful, the intent-spec framing is too thin.
- *Taste grounded in persona + precedent + standards is better than ungrounded taste* (Kahneman's stable-referent condition). If the persona/precedent referent is usually absent or unreliable, the grounding is theatre and `aesthetic-direction` should stay as-is.
- *The rename is low-cost at this stage.* If `design-craft` has meaningful install depth already, the no-alias migration is too disruptive and a pack-alias mechanism (deferred) becomes the real blocker.

**Drawbacks.** Three more skills to maintain; two enhanced skills; a cross-pack edit in `product-engineering`; the rename's migration tail and the frozen-governance bridge; added surface in the `experience` README. Mitigated by the standalone-useful + detect-and-degrade posture (no skill *requires* the others) and the one-spec migration.

## Evidence & prior art

**Spike / de-risk result.** *Riskiest assumption — the rename is cheap at v0.1.1.* Timeboxed repo sweep: `design-craft` is referenced outside its own dir in governance docs (ADR-0024, RFC-0033, specs — all frozen, bridged not edited), the marketplace aggregation, the guides dir, the README, and `packages/agentbundle/CHANGELOG.md`; **no `profiles/*.toml` references it** (grep-confirmed — so no profile edits), and per the self-host scope (user-scope-default packs are not in this repo's working-tree projection) **no `.claude/` projection changes**. The live migration surface is the pack dir + four manifest/guide touchpoints + cross-links + **the framework-agnosticism CI lint and its self-test and two CI steps** (`tools/lint-design-craft-agnostic.py` hardcodes `packs/design-craft/` — D1) — exactly the `contract-acquisition` shape, plus one CI-tool touchpoint the skill rename did not have. **Conclusion: the assumption holds; the rename is a known, bounded move.**

**Repo precedent.** RFC-0033 + ADR-0024 (the pack and its posture), RFC-0047 § Errata 2026-06-25 (the verified rename-without-alias precedent — *the `infra-contract-acquisition → contract-acquisition` skill rename: live surface renamed, frozen governance bridged, no alias*), RFC-0040 / ADR-0030 (the `agentbundle-layout.toml` three-tier path resolution this RFC reuses), RFC-0037 / ADR-0028 (the eval coverage shape the new skills join), RFC-0030 (`voice-and-microcopy`'s home), RFC-0032 / ADR-0023 (the "three reviewers is a *code-review* ceiling" reading that keeps `design-critique` an interactive skill).

**External prior art** (fetched and confirmed to contain the cited claim): the connective artifacts are the established product-team UX ontology — **[NN/g service blueprints](https://www.nngroup.com/articles/service-blueprints-definition/)** (frontstage / line-of-visibility / backstage / support), NN/g journey mapping, Patton user-story mapping, Torres opportunity-solution trees (consolidated in [`0048-notes/01`](0048-notes/01-research-consolidation.md)). The platform axis points to the platform owners' own conventions — **[Apple HIG](https://developer.apple.com/design/human-interface-guidelines)** (iOS/iPadOS/macOS platform conventions), **[Material 3](https://m3.material.io/)** (Google's open-source Android/cross-platform design system), and **[MDN responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)** (breakpoints / media queries, mobile-first). No fabricated sources; the design ontology is well-established prior art, not novel.

**Promoted research.** This RFC rests on RFC-0048's promoted investigation — the artifact inventory ([`/04`](0048-notes/04-artifact-inventory.md)), the per-pack delta ([`/06`](0048-notes/06-pack-delta-and-orchestration.md)), the per-screen brief format ([`/07`](0048-notes/07-screen-brief-format.md)), and the gap-resolution sample-bank ([`/09`](0048-notes/09-gap-resolutions.md), to which this effort appends its own sample reads per the series-execution standard).

## Open questions

None at the design level — RFC-0048 Decision 3 adjudicated the value calls (rename, skill set, axis), and the resolve-vs-surface lens grounded the rest in repo precedent (the `contract-acquisition` migration, the `product-engineering` layout pattern, the `quality-floor` state set). Two items are **deliberately deferred to sibling efforts, not open here**:

- **The traceability lint** that enforces the per-screen brief's action→service and screen→journey edges is RFC-0048 Decision 6 (a separate child); this RFC ships the briefs that *carry* the edges. · owner: RFC-0048 child-4 · decide-by: its own RFC/spec.
- **The design-artifact live-lens reviewer mode** (RFC-0048 O5) on `core`'s reviewers / `architect`'s `design-reviewer` reuses `design-critique`'s rubric; that wiring is `core`/`architect`'s effort. · owner: RFC-0048 follow-on · decide-by: its own effort.

## Follow-on artifacts

Filled on acceptance:

- **ADR-0038:** record the `design-craft → experience` rename + the frozen-governance bridge (RFC-0033, ADR-0024, the Shipped `design-craft-pack` spec, README rows keep `design-craft` as historical record). *(Authored alongside this RFC.)*
- **Spec:** `docs/specs/experience-pack/` — the rename migration (dirs/manifests/guides/cross-links + `0.2.0` + marketplace re-aggregation + the changelog/erratum bridge); the three connective skills + their evals + the `[experience]` layout default; the `aesthetic-direction` / `design-critique` enhancements; the `voice-and-microcopy` wiring + the `product-engineering` minor bump.
- **Sample-bank append:** the resolve-vs-surface sample reads this effort produced, into [`0048-notes/09`](0048-notes/09-gap-resolutions.md). *(Done in this PR.)*
- **Drift reconciliation:** any divergence this effort surfaces against RFC-0048 is reconciled there as a tracked amendment (the provisional-foundation discipline). This effort surfaced **two** items, both reconciled in-body and logged in the sample-bank: **(i)** the per-screen state set defers to the shared handle-all-states floor (`permission/denied` is an *additional* gated-screen state, not a replacement list) — D2/D4; **(ii)** `inventory-screens` ships the **cross-brief consistency pass + low-fi-prototype / steel-thread verification step** (D4), which RFC-0048 Decision 3's decided body does not enumerate — it originates as a *forward idea for child-1* in `0048-notes/07` § Consistency & prototyping and is sanctioned by Decision 9's proactive-model-thinking expectation, so this RFC **promotes it from forward-idea to shipped procedure** and records the promotion here as the tracked amendment to RFC-0048 D3's skill scope.
