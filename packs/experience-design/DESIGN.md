# Experience Design Pack — Design Document

Living design reference for the experience-design pack. Records the philosophy, method architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

---

## TL;DR

`experience-design` is the design seat for a product team. It runs a walkable method from outcome to realization — journey → content direction → screen flow → aesthetic direction → per-screen craft → independent review — where each step produces a portable artifact the next step consumes. Every skill ships method, never stack code or values: the adopter derives their design from the method and fills in numbers. The quality floor (handle-all-states, WCAG accessibility, reduced-motion) is non-negotiable and referenced by every consuming skill. An independent `experience-reviewer` subagent reads design artifacts cold — no authoring memory — at the end of the thread.

---

## Non-Goals

Things a reasonable reader might expect this pack to provide. It doesn't, by design:

- **No stack specifics.** No UI-framework code, no styling-language syntax, no animation library, no fixed spacing/timing/color/motion-curve tables, no token values, no pixel comps. The pack ships the method to derive your design; you choose your tools and fill in the numbers.
- **No product strategy.** The pack assumes an agreed user and outcome. Framing, opportunity sizing, and UX strategy are upstream (`product-strategy` pack). When that input is absent, `journey-mapping` degrades gracefully but the output is weaker.
- **No UI copy strings.** Per-state UI copy (button labels, error messages, empty states) is the `voice-and-microcopy` skill's domain in `product-engineering`. This pack sets content intent and copy direction; `voice-and-microcopy` writes the actual strings keyed to the state matrix.
- **No code review.** `experience-reviewer` reviews design artifacts only — journeys, screen flows, briefs, aesthetic directions. It never reviews code diffs (use core's `adversarial-reviewer`) or architecture docs (use architect's `design-reviewer`).
- **No persistent runtime.** No hook, engine, validator daemon, or state machine. This pack is habits, not infrastructure. `design-review` is an authoring-time interactive skill; `experience-reviewer` is a one-shot forked subagent.

---

## 1. The design thread

### The full sequence

```
journey-mapping
    ↓
content-design
    ↓
copy-direction  ←──── tone-of-voice (brand register, optional)
    ↓
user-flow
    ↓
design-principles  ←──── creative-direction
    ↓                          ↓
information-architecture   design-system
  (or genre-direct skill)
    ↓
interaction-design
    ↓
design-review     ←  quality-floor check (authoring-time)
    ↓
experience-reviewer  ←  independent cold review
```

`service-blueprint` and `process-mapping` are parallel to the main thread (they map what backs the screens, and the internal operations behind them) rather than sequential gates.

### Why the sequence exists

Each skill consumes a specific upstream artifact and cannot produce reliable output without it:

- `content-design` needs the journey's key touchpoints to know what the surface is trying to accomplish and for whom.
- `copy-direction` needs the content brief from `content-design` to name per-surface copy goals grounded in the surface's declared intent. For acquisition surfaces, `tone-of-voice`'s brand register is an optional upstream anchor.
- `user-flow` needs the content brief to sequence screens in a way that delivers on the stated content intent, not just the functional path.
- `creative-direction` needs the journey's emotional arc (the pains, the moments of relief) to ground the aesthetic direction in real user feeling rather than preference.
- `design-system` needs the named aesthetic direction to derive a token taxonomy that isn't arbitrary.
- `information-architecture` (and the genre-direct skills) needs both the content brief and the aesthetic direction as constraints.
- `interaction-design` needs the per-screen brief produced by `user-flow` — which includes the state matrix — to design behavior for the right set of states.
- `design-review` and `experience-reviewer` need the completed artifacts to review against something concrete.

Skipping a step doesn't save time — it pushes the missing input forward as an implicit assumption, where it gets designed around rather than decided.

### The minimal viable thread

The minimum that makes the output coherent:
1. `journey-mapping` — the outcome and failure modes
2. `user-flow` — the screen list and per-screen briefs
3. One craft pass on each screen (at minimum: `information-architecture` → `interaction-design`)
4. `experience-reviewer` — the cold review

Everything else in the pack enhances this thread. `experience-status` tells you where you are on it.

---

## 2. The quality floor

### What the floor covers

Every skill in the craft sequence references one shared quality-floor checklist:

1. **Handle all states.** Every screen must be designed for: empty state, loading/skeleton state, populated state, error state, success/confirmation state, and any partial states specific to the surface (partially-loaded, degraded, offline). Missing a state is not a styling gap — it's a functional gap that will surface to users.

2. **Accessibility floor — WCAG 2.2 AA minimum.** Colour contrast ratios, label associations, focus order, reduced-motion respect, touch target sizes. This pack points to WCAG; it does not reprint the standard or fix values. The designer derives conformant values; the floor only sets the target level.

3. **Motion communicates state; honour reduced-motion.** Motion is a communication tool. Every animation must communicate something (state change, hierarchy, feedback). Every animation must respect the user's reduced-motion preference and have a non-motion fallback that communicates the same thing.

### Correctness is the floor, not the ceiling

A design that passes the quality floor is correct. It is not necessarily good. Meeting WCAG AA alone produces accessible-but-tasteless work; handling all states alone produces complete-but-generic work.

The `creative-direction` skill is the gate between correct and good: it grounds visual and brand goals in persona, precedent, and platform conventions — naming a direction that the rest of the craft sequence must satisfy as a coherence constraint. A `creative-direction` doc that only restates correctness goals ("it should be accessible and clear") has not cleared the gate.

This principle applies to every skill in the pack. `design-principles` must name principles that a team would actually dispute, not principles everyone already agrees with. `tone-of-voice` must produce ranked goals that create real copy arbitration, not aspirational adjectives.

---

## 3. The method principle: derive, never prescribe

### Why no values tables

The pack ships method and taxonomy shapes, not values. This is a deliberate scope decision, not a gap:

- **Portability.** Values are always project-specific (a fintech's type scale is not a gaming product's type scale). A pack that ships values forces the adopter to either use them as-is (wrong) or override them everywhere (friction without benefit).
- **Standards don't need reprinting.** WCAG contrast ratios, Material 3 motion curves, Apple HIG tap target sizes — these are published, maintained, and authoritative. A pack that reprints them creates a maintenance burden and an accuracy risk. The method says what to check and points to where; the adopter follows the live standard.
- **Method survives stack changes.** The token taxonomy shape (primitive → semantic → component) is stable across design tools, styling preprocessors, and component frameworks. A values table is not.

### What "method" means in practice

Each skill:
- Names what to decide (e.g. "name each spacing value by semantic role, not by numeric scale")
- Gives a decision rule (e.g. "every token decision must trace back to a named goal in the aesthetic direction")
- Points to the standard for the constraint (e.g. "WCAG 2.2 AA for contrast ratios")
- Leaves values blank (e.g. the taxonomy shape has named slots; the adopter fills the numbers)

### The two kinds of "no stack"

**No framework code.** The pack never emits framework-specific components, utility-class markup, native-platform views, or styling code. These belong in the build loop (`frontend-engineering` in core).

**No tool prescriptions.** The pack never names a specific design tool winner (Figma, Sketch, Penpot). Tool categories appear where relevant (vector-based screen design tool, design-token plugin); specific tools do not.

---

## 4. The connective thread skills

### How the thread flows

The connective skills map the flow from a user's outcome to a set of screens ready for craft:

| Skill | Input | Output | What it settles |
|-------|-------|--------|-----------------|
| `journey-mapping` | User, outcome, platform | Journey map (stages × emotions × pains × opportunities) | What the user is trying to accomplish and where it breaks |
| `content-design` | Journey key touchpoints | Content brief per surface | What the surface says, for whom, to what objective |
| `tone-of-voice` | Brand/product register | Brand-register doc (copy goals + arbitration rules) | How the brand sounds across all surfaces; what wins when goals conflict |
| `copy-direction` | Content brief + tone-of-voice brand register (optional) | Per-surface copy goals | Which copy goals govern each acquisition surface |
| `user-flow` | Journey + content brief | Screen inventory, transitions, per-screen briefs | Which screens exist, what state each handles, how they connect |
| `service-blueprint` | Journey + screen flow | Blueprint (frontstage / backstage / support) | What services back each screen action |
| `process-mapping` | Internal workflow | As-is / to-be process (SIPOC, swimlane, pain register) | What the internal operations look like, where waste is |
| `design-principles` | Journey insights | 3–5 named principles with arbitration tests | The decision rules that hold screens to a shared standard |

### Platform/surface axis

`journey-mapping` and `user-flow` carry a platform/surface axis — responsive-web, iOS, Android, cross-platform. This affects what the method asks at each stage (iOS has HIG interaction patterns; cross-platform requires explicit divergence documentation). Skills that consume per-screen briefs inherit the platform context from the brief.

### Content-design vs. tone-of-voice vs. copy-direction vs. ux-writing

Four skills touch copy; they operate at different layers:

- **`tone-of-voice`** sets the brand register: named, ranked copy goals grounded in persona and precedent, with arbitration rules. Brand-level and cross-surface — sets the standard all per-surface copy decisions reference.
- **`content-design`** sets surface intent: what this specific surface says, for whom, in what structure. Execution-layer, per-surface — answers "what goes here?" not "how does it sound?"
- **`copy-direction`** names per-surface copy goals for a specific marketing or acquisition surface. Takes the content brief from `content-design` and the brand register from `tone-of-voice` (optional) as upstream inputs — answers "how does this surface sound and what does it emphasize?"
- **`ux-writing`** (product-engineering pack) writes the actual per-state UI strings. Consumes the state matrix from `user-flow` and loads the brand register from `tone-of-voice` by fixed path as voice input.

Running `content-design` before `copy-direction` is correct. Running `tone-of-voice` before `copy-direction` is correct (the brand register is an optional upstream anchor for per-surface copy goals). Running `ux-writing` after `user-flow` is correct.

---

## 5. The craft sequence

### Why this order

The craft sequence follows a dependency chain where each skill's output constrains the next:

**Design-principles** ← journey insights  
Principles must derive from real user pain points in the journey. A principle not grounded in a journey moment is an opinion, not a design rule. These are produced before aesthetic work begins because they are the meta-level arbitration rules the aesthetic work must satisfy.

**Creative-direction** ← principles + persona + precedent  
The aesthetic direction names the emotional and brand goals that visual decisions must serve. It is grounded in three things: the persona (who the user is, what their existing context looks like), stable referents (products or visual traditions that achieve the named goal), and platform conventions (iOS/Material/web norms the design inherits whether it wants to or not). An aesthetic direction not grounded in all three is arbitrary.

**Design-system** ← aesthetic direction  
The token taxonomy derives from the aesthetic direction. Every token decision must trace back to a named goal in the direction. A token that can't be explained by the direction is a gap in the direction, not a token decision.

**Information-architecture / genre-direct skills** ← content brief + aesthetic direction  
Hierarchy, reading flow, and wayfinding are set before behavioral design begins. The IA is the skeleton; interaction design is the muscle. Designing interaction without a settled IA produces behaviors that fight the structure.

**Interaction-design** ← per-screen brief + IA  
The behavioral layer is designed last in the craft sequence because it depends on knowing what states exist (from the per-screen brief's state matrix) and what the structural hierarchy is (from IA).

### The genre-direct skills

Six surface-typed IA skills run in place of the general `information-architecture` skill when the screen has a known surface genre:

| Skill | Surface genre | What's specific |
|-------|--------------|-----------------|
| `analytical-design` | Dashboards, reporting surfaces | Widget hierarchy, role-based view architecture, business-question-to-layout map |
| `conversion-design` | Marketing, acquisition, landing pages | Above-fold contract, scroll story, social-proof architecture |
| `documentation-design` | Docs, help, reference | Diátaxis content typing, navigation strategy, TTFV architecture |
| `informational-design` | Editorial, content-first pages | Typographic hierarchy, reading-pattern calibration, editorial grid |
| `marketplace-design` | Listings, search, transactional surfaces | Listing card IA, filter and facet architecture, transaction bridge |
| `workspace-design` | Productivity tools, workspace surfaces | Context-persistence architecture, attention zone layout, interrupt design |

The genre-direct skills are not a replacement for `creative-direction` or `design-system` — they are a replacement for `information-architecture` only. The full craft sequence runs; only the IA step changes.

---

## 6. Independent review architecture

### Why the experience-reviewer is forked

The `experience-reviewer` agent runs in a forked context with no access to the authoring session. The reasons are structurally identical to why core's `adversarial-reviewer` runs cold:

An agent that reviews its own work in the same session is primed to read the artifacts charitably — it knows what was intended, which means it interprets gaps as "the reader will understand" and inconsistencies as "acceptable trade-offs I already considered." A reviewer that has never seen the authoring rationale reads the artifacts as a user would: with no benefit of the doubt.

### What the experience-reviewer covers

The reviewer runs five lenses in sequence:

| Lens | What it checks |
|------|---------------|
| Quality floor | handle-all-states, WCAG 2.2 AA contrast and labels, reduced-motion guard |
| Grounded aesthetic fit | Do the screens satisfy the named goals in the aesthetic direction? Are visual decisions traceable to a principle? |
| Platform fit | Do interactions match platform conventions? (iOS tap targets, Material elevation, web hover/focus patterns) |
| Cross-brief coherence | Do screens that share a user flow tell a coherent story? Do adjacent screens use the same vocabulary? |
| Marketing clarity | Fires on `communication_mode: product-copy` artifacts only — tweet test, five-second scan, painkiller-first framing |

### What the experience-reviewer never does

- Reviews code diffs (use core's `adversarial-reviewer`)
- Reviews architecture design docs (use architect's `design-reviewer`)
- Rewrites artifacts (read-only by contract — flags only, never fixes)
- Runs before the minimal viable thread is complete (the reviewer needs a journey + screen flow + at least one per-screen brief to give a useful review)

---

## 7. Output artifact model

### Where artifacts live

Artifact-writing skills resolve their output path through the `[design]` table of the adopter-owned `agentbundle-layout.toml`:

```toml
[design]
output_dir = "docs/design"   # resolves to: docs/design/{journeys,screens,briefs,...}/
```

Each skill writes under a subdirectory of `output_dir`:

| Subdirectory | Written by |
|---|---|
| `journeys/` | journey-mapping |
| `content/` | content-design |
| `screen-flows/` | user-flow |
| `blueprints/` | service-blueprint |
| `processes/` | process-mapping |
| `aesthetic/` | creative-direction, design-system, design-principles |
| `screens/` | interaction-design, and the craft/genre skills |

The path is elicited once per repo, written to `agentbundle-layout.toml`, and reused by every subsequent skill. `experience-status` reads from this directory to orient.

### Why user-scope by default

Design method is portable, not project-specific. A designer using the same method across multiple repos should not need to install the pack per-repo. The skills produce per-repo artifacts (they write to `docs/design/` in the repo), but the method itself doesn't change between repos.

This is the same scope decision as `architect` and `desk-research`. Compare with `core`, which is repo-scope because the work-loop's gate commands (`lint`, `typecheck`, `tests`) are project-specific.

---

## 8. Cross-pack dependencies

### Upstream: product-strategy

The `product-strategy` pack is the strategic anchor this pack builds on. Before `journey-mapping` runs, a strategist may have committed:

- `ux-strategy.md` (vision → goals + measures → plan) — read by `journey-mapping` as the stated rationale for the journey.
- `content-strategy.md` (Halvorson quad: Purpose + Process + Structure + Governance) — read by `content-design` for organizational governance intent.

Both inputs are optional; the skills degrade gracefully when absent. With them, the design thread has explicit strategic grounding; without them, it must infer intent from the stated user and outcome.

### Downstream: product-engineering

The per-screen state matrix produced by `user-flow` is the hand-off artifact `voice-and-microcopy` (product-engineering pack) consumes. Each cell in the matrix (screen × state) maps to a copy string. The two packs are designed to meet at this interface.

### Downstream: architect / contracts

The backstage column of the `service-blueprint` is the slicing instrument handed to the `architect` and `contracts` packs by name. When a service blueprint exists, an architect using `architect-design` should read it before proposing a backend design — it encodes the frontstage obligations the backend must fulfill.

---

## 9. Safety invariants

1. **`experience-reviewer` is read-only.** It flags, never rewrites. Any suggestion to have the reviewer apply its own findings is out of scope — flagging is the deliverable.

2. **`experience-status` is read-only.** It never writes files, never elicits `[design] output_dir` (stops at "not configured"), never advances state.

3. **The quality floor is non-negotiable.** No skill may produce output that explicitly defers the quality floor ("we'll add states later," "accessibility to follow"). The floor is the minimum bar for any output to leave the skill; if the design can't meet it, the skill surfaces to the human rather than shipping below floor.

4. **No values, ever.** No skill may emit a fixed colour value, spacing value, timing curve, or breakpoint table. Method and taxonomy shape only.

5. **No tool winners.** No skill names a specific design tool (Figma, Sketch, Penpot, etc.) as the prescribed tool. Tool categories are allowed ("a vector-based screen design tool"); specific tools are not.

6. **The aesthetic direction must be grounded, not aspirational.** A `creative-direction` output that only lists adjectives ("premium, calm, focused") without named referents (precedent products or traditions that achieve those qualities) has not met the skill's output contract.

---

## 10. Design decisions and rationale log

### Why no values tables (from v1)

The pack ships in two parts: method (what to decide and how) and taxonomy shape (the slot structure for values). Values are intentionally absent because: (a) they are always project-specific, (b) the authoritative standards (WCAG, HIG, Material) already publish them and are better maintained, (c) any values we ship create a false anchor the adopter will optimize against rather than derive from first principles. The method works precisely because it forces derivation.

**Alternative considered:** ship sensible defaults for common stacks (one for web, one for iOS, one for Android). Rejected because "sensible defaults" become cargo-culted values within one sprint. Teams stop asking "does this ratio serve the aesthetic direction?" and start asking "does this match the default?" The method value evaporates.

### Why user-scope by default (from v1)

Design method is the same across repos; only the artifacts differ. Installing per-repo would require reinstallation on every new project without any change to the skills. The scope decision mirrors `architect` (same reasoning: the method is portable, the knowledge surface is not project-specific).

**Alternative considered:** repo-scope to colocate the skill definitions with the artifacts they produce. Rejected because it creates installation friction for cross-repo designers and doesn't improve artifact colocation (artifacts already live in the repo via `agentbundle-layout.toml`; the skills don't need to be repo-installed to write to a repo path).

### Why the experience-reviewer runs forked (from v1)

Structurally identical to core's adversarial-reviewer rationale. An authoring-session reviewer is primed by the authoring intent and cannot read the artifact as a stranger would. The value of the review comes from genuine ignorance of the design rationale. See core DESIGN.md §15 for the parallel decision.

**Alternative considered:** stateful review that has access to the authoring session's reasoning, so it can review the design *and* the decision trail. Rejected for the same reason as in core: a reviewer that knows what was intended will systematically read gaps charitably.

### Why six genre-direct skills instead of one general IA skill with genre flags (from v1)

Each genre has a distinct structural logic that a general IA skill with a flag would produce via branching. A conversion surface's above-fold contract is not a weaker version of a dashboard's widget hierarchy — they are different structural problems. Separate skills make the genre's structural logic explicit and reviewable without reading a flag-driven conditional tree.

**Alternative considered:** one `information-architecture` skill with a `genre:` parameter. Rejected because the genre-specific reasoning (above-fold contract, scroll story, social-proof architecture for conversion; TTFV architecture, Diátaxis typing for documentation) is substantive enough to earn a separate skill definition. A flag-parameterized skill would bury the genre logic; separate skills make it first-class.

### Why correctness is the floor, not the ceiling (from v1)

Meeting the quality floor (WCAG AA, handle-all-states, reduced-motion) is necessary but not sufficient for a good design. A pack that only produced correct designs would produce accessible, complete, and inoffensive work — but work that competes on accessibility alone doesn't win. The `creative-direction` skill is the gate between correct and good: it creates the aesthetic constraint that the rest of the craft sequence must satisfy. Collapsing the two (treating taste as optional) produces work that no one complains about but no one uses.

**Alternative considered:** make `creative-direction` optional — treat aesthetic direction as a nice-to-have for when the team has time. Rejected because without a named aesthetic constraint, every subsequent craft decision becomes a local opinion (each screen looks "reasonable" in isolation; the thread has no visual coherence). The quality floor is a mechanical gate; the aesthetic direction is a coherence gate. Both are required.
