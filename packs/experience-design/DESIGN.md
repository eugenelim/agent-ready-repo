# Experience Design Pack — Design Document

Living design reference for the experience-design pack. Records the philosophy, method architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

---

## TL;DR

`experience-design` is the design seat for a product team. It runs a walkable method from outcome to realization — journey → content direction → screen flow → aesthetic direction → per-screen craft → independent review — where each step produces a portable artifact the next step consumes. Every skill ships method, never stack code or values: the adopter derives their design from the method and fills in numbers. The quality floor (handle-all-states, WCAG accessibility, reduced-motion) is non-negotiable and referenced by every consuming skill. An independent `experience-reviewer` subagent reads design artifacts cold — no authoring memory — at the end of the thread.

---

## Non-Goals

Things a reasonable reader might expect this pack to provide. It doesn't, by design:

- **No stack specifics.** No UI-framework code, no styling-language syntax, no animation library, no fixed spacing/timing/color/motion-curve tables, no token values, no pixel comps. The pack itself carries no value — nothing here would arrive the same way for two unrelated products. A `design-system` run resolves the values *your* approved direction, existing system and platform give it authority to fix, and writes them into your artifact.
- **No product strategy.** The pack assumes an agreed user and outcome. Framing, opportunity sizing, and UX strategy are upstream (`product-strategy` pack). When that input is absent, `journey-mapping` degrades gracefully but the output is weaker.
- **No UI copy strings.** Per-state UI copy (button labels, error messages, empty states) is the `ux-writing` skill's domain in `product-engineering`. This pack sets content intent and copy direction; `ux-writing` writes the actual strings keyed to the state matrix.
- **No code review.** `experience-reviewer` reviews design artifacts only — journeys, screen flows, briefs, aesthetic directions. It never reviews code diffs (use core's `adversarial-reviewer`) or architecture docs (use architect's `design-reviewer`).
- **No persistent runtime.** No hook, engine, validator daemon, or state machine. This pack is habits, not infrastructure. `design-review` is an authoring-time interactive skill; `experience-reviewer` is a one-shot forked subagent.

---

## 1. The design thread

### The full sequence

```
journey-mapping
    ↓
content-design [message and narrative structure]
    ↓
content-design [per-surface copy goals]  ←──── content-design [brand-level register] (optional)
    ↓
user-flow
    ↓
design-principles  ←──── creative-direction
    ↓                          ↓
information-architecture   design-system
  (route by genre when known)
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
- `content-design`'s per-surface acquisition copy goals mode needs the content brief its own message and narrative structure mode writes, to name per-surface copy goals grounded in the surface's declared intent. For acquisition surfaces, the brand register is an optional upstream anchor.
- `user-flow` needs the content brief to sequence screens in a way that delivers on the stated content intent, not just the functional path.
- `creative-direction` needs the journey's emotional arc (the pains, the moments of relief) to ground the aesthetic direction in real user feeling rather than preference.
- `design-system` needs the named aesthetic direction so the system it resolves isn't arbitrary.
- `information-architecture` needs both the content brief and the aesthetic direction as constraints. When a screen declares a surface genre, it loads the matching genre method before arranging hierarchy.
- `interaction-design` needs the per-screen brief produced by `user-flow` — which includes the state matrix — to design behavior for the right set of states.
- `design-review` and `experience-reviewer` need the completed artifacts to review against something concrete.

Skipping a step has a cost: the missing input travels forward as an implicit
assumption, where it gets designed around rather than decided. That cost is what
the minimal viable thread below is chosen against — it names the four steps whose
inputs nothing downstream can reconstruct, not a licence to drop the rest for free.

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

This principle applies to every skill in the pack. `design-principles` must name principles that a team would actually dispute, not principles everyone already agrees with. `content-design`'s brand-level register mode must produce ranked goals that create real copy arbitration, not aspirational adjectives.

---

## 3. The method principle: derive, never prescribe

### Why the pack ships no values, and a run resolves them

The pack ships no value; the artifact a run writes for one product does. Those
are two different statements and only the first is a scope decision:

- **Portability.** Values are always project-specific (a fintech's type scale is not a gaming product's type scale). A pack that ships values forces the adopter to either use them as-is (wrong) or override them everywhere (friction without benefit).
- **Standards don't need reprinting.** WCAG contrast ratios, Material 3 motion curves, Apple HIG tap target sizes — these are published, maintained, and authoritative. A pack that reprints them creates a maintenance burden and an accuracy risk. The method says what to check and points to where; the adopter follows the live standard.
- **Method survives stack changes.** The system's shape (primitive → semantic → component) is stable across design tools, styling preprocessors, and component frameworks. A values table is not.

What none of that licenses is refusing to decide. A run that leaves typography, color, spacing or shape for whoever writes the code has not avoided arbitrary values — it has moved them to a surface with less design context, where they will be filled from category habit. So a `design-system` run resolves every domain its authority reaches, records the authority that supplied each one, and records a domain nothing reached as unresolved rather than choosing.

### What "method" means in practice

Each skill:
- Names what to decide (e.g. "name each spacing value by semantic role, not by numeric scale")
- Gives a decision rule (e.g. "every token decision must trace back to a named goal in the aesthetic direction")
- Points to the standard for the constraint (e.g. "WCAG 2.2 AA for contrast ratios")
- Resolves the values that rule implies for this product, and records which authority supplied each one (e.g. the direction's axis tokens, the incumbent system, or the named platform's convention)

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
| `content-design` (brand-level register) | Brand/product register | Brand-register doc (copy goals + arbitration rules) | How the brand sounds across all surfaces; what wins when goals conflict |
| `content-design` (per-surface copy goals) | Content brief + brand register (optional) | Per-surface copy goals | Which copy goals govern each acquisition surface |
| `user-flow` | Journey + content brief | Screen inventory, transitions, per-screen briefs | Which screens exist, what state each handles, how they connect |
| `service-blueprint` | Journey + screen flow | Blueprint (evidence of service / frontstage / line of visibility / backstage / support) | What services back each screen action |
| `process-mapping` | Internal workflow | As-is / to-be process (SIPOC, swimlane, pain register) | What the internal operations look like, where waste is |
| `design-principles` | Journey insights | 3–5 named principles with arbitration tests | The decision rules that hold screens to a shared standard |

### Platform/surface axis

`journey-mapping` and `user-flow` carry a platform/surface axis — responsive-web, iOS, Android, cross-platform. This affects what the method asks at each stage (iOS has HIG interaction patterns; cross-platform requires explicit divergence documentation). Skills that consume per-screen briefs inherit the platform context from the brief.

### Choosing a copy mode, and the one cross-pack boundary

The copy layer is **one skill in three modes**, plus one skill in another pack.
There is no longer a choice between copy skills to get wrong; there is a mode
selection the skill makes from the request, and a pack boundary that still
matters.

- **`content-design`, brand-level register mode** sets the brand register: named,
  ranked copy goals grounded in persona and precedent, with arbitration rules.
  Brand-level and cross-surface — it sets the standard all per-surface copy
  references. Writes the reserved `copy/brand-register.md`.
- **`content-design`, message and narrative structure mode** sets surface intent:
  what this specific surface says, for whom, in what structure. Per-surface —
  it answers "what goes here?", not "how does it sound?". Writes
  `content/<slug>.md`.
- **`content-design`, per-surface acquisition copy goals mode** names copy goals
  for one marketing or acquisition surface. Takes the content brief and the brand
  register (optional) as upstream referents. Writes `copy/<surface-slug>.md`.
- **`ux-writing`** (product-engineering pack) writes the actual per-state UI
  strings. It consumes the state matrix from `user-flow` and loads the brand
  register by fixed path as voice input. **This is the boundary that remains
  real**, because it crosses packs: UI state copy lives there, everything else
  here.

The ordering inside the skill is unchanged by the fold. Running the message and
narrative structure mode before the per-surface mode is correct. Running the
brand-level register mode before the per-surface mode is correct — the register
is an optional upstream anchor for per-surface goals. What the fold removed is
the need for a reader to know which of three registrations a copy task belonged
to; what it kept is every artifact, path and `type:` those registrations wrote.

The three modes were separate skills until the copy fold. That change is recorded
in the errata of the two RFCs that established them, which are the durable record
of why the boundary moved.

### Shared references are held identical by test, not by autonomy

An earlier note in this pack read *"Skill autonomy beats DRY at this scale — each
skill stands alone"*, and it justified shipping `references/editorial-quality-gates.md`
as independent per-skill copies that were free to drift. **That note is
superseded.** The file is now one body with two copies —
`content-design`'s and `information-architecture`'s — held byte-identical by
`test_every_editorial_quality_gates_copy_is_byte_identical` in the roster suite,
following the same precedent `containment.md` already set in this pack.

Autonomy is still why the copies exist: a skill installs standalone and cannot
reach another skill's reference files. What changed is that the copies may no longer
drift silently. Duplication is the delivery mechanism; equality is the contract.

---

## 5. The craft sequence

### Why this order

The craft sequence follows a dependency chain where each skill's output constrains the next:

**Design-principles** ← journey insights  
Principles must derive from real user pain points in the journey. A principle not grounded in a journey moment is an opinion, not a design rule. These are produced before aesthetic work begins because they are the meta-level arbitration rules the aesthetic work must satisfy.

**Creative-direction** ← principles + persona + precedent  
The aesthetic direction names the emotional and brand goals that visual decisions must serve. It is grounded in three things: the persona (who the user is, what their existing context looks like), stable referents (products or visual traditions that achieve the named goal), and platform conventions (iOS/Material/web norms the design inherits whether it wants to or not). An aesthetic direction not grounded in all three is arbitrary.

**Design-system** ← aesthetic direction + the product's existing system  
The system derives from the aesthetic direction and whatever the product already has. Every decision must trace back to a named goal or a committed axis in the direction, to a stated constraint, or to the incumbent system. A decision that can't be explained by one of those is a gap in the authority, not a decision to make anyway.

**Information-architecture with genre routing** ← content brief + aesthetic direction
Hierarchy, reading flow, and wayfinding are set before behavioral design begins. The IA is the skeleton; interaction design is the muscle. When a screen has a known surface genre, the genre route supplies the specialized structural vocabulary inside `information-architecture`. Designing interaction without a settled IA produces behaviors that fight the structure.

**Interaction-design** ← per-screen brief + IA  
The behavioral layer is designed last in the craft sequence because it depends on knowing what states exist (from the per-screen brief's state matrix) and what the structural hierarchy is (from IA).

### The genre routes

`information-architecture` is the single IA skill. For known surface genres, it selects the matching genre reference before designing hierarchy:

| Surface genre | What's specific |
|--------------|-----------------|
| Analytical surfaces | Widget hierarchy, role-based view architecture, business-question-to-layout map |
| Marketing surfaces | Above-fold contract, scroll story, social-proof architecture |
| Documentation surfaces | Diátaxis content typing, navigation strategy, TTFV architecture |
| Informational surfaces | Typographic hierarchy, reading-pattern calibration, editorial grid |
| Marketplace surfaces | Listing card IA, filter architecture, comparison, transaction bridge |
| Workspace surfaces | Context-persistence architecture, attention zone layout, interrupt design |

The genre routes are not a replacement for `creative-direction` or `design-system` — they specialize `information-architecture` only. The full craft sequence runs; only the IA method changes.

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
output_dir = "docs/design"   # base path; the subdirectories are the ones listed below
```

Each skill writes under a subdirectory of `output_dir`:

| Subdirectory | Written by |
|---|---|
| `journeys/` | journey-mapping |
| `content/` | content-design |
| `copy/` | content-design — its brand-level register mode writes the register, its per-surface acquisition copy goals mode writes one record per surface |
| `screens/` | user-flow (the screen flow and the per-screen briefs), information-architecture (the IA doc). `interaction-design` and the craft skills enrich a brief `user-flow` owns; they write no file of their own |
| `blueprints/` | service-blueprint |
| `processes/` | process-mapping |
| `principles/` | design-principles |
| `direction/` | creative-direction |
| `tokens/` | design-system |

The path is elicited once per repo, written to `agentbundle-layout.toml`, and reused by every subsequent skill. `experience-status` reads from this directory to orient.

### Why user-scope by default

Design method is portable, not project-specific. A designer using the same method across multiple repos should not need to install the pack per-repo. The skills produce per-repo artifacts (they write to `docs/design/` in the repo), but the method itself doesn't change between repos.

This is the same scope decision as `architect` and `desk-research`. Compare with `core`, which is repo-scope because the work-loop's gate commands (`lint`, `typecheck`, `tests`) are project-specific.

---

## 8. Cross-pack dependencies

### Upstream: product-strategy

The `product-strategy` pack is the strategic anchor this pack builds on. Before `journey-mapping` runs, a strategist may have committed:

- `ux-strategy.md` (vision → goals + measures → plan) — read by `journey-mapping` as the stated rationale for the journey.
- `content-strategy.md` (Purpose + Process + Structure + Governance — the product-strategy pack's own composite, informed by the content-strategy quad but not identical to either published version) — read by `content-design` for organizational governance intent.

Both inputs are optional; the skills degrade gracefully when absent. With them, the design thread has explicit strategic grounding; without them, it must infer intent from the stated user and outcome.

### Downstream: product-engineering

The per-screen state matrix produced by `user-flow` is the hand-off artifact `ux-writing` (product-engineering pack) consumes. Each cell in the matrix (screen × state) maps to a copy string. The two packs are designed to meet at this interface.

### Downstream: architect / contracts

The backstage column of the `service-blueprint` is the slicing instrument handed to the `architect` and `contracts` packs by name. When a service blueprint exists, an architect using `architect-design` should read it before proposing a backend design — it encodes the frontstage obligations the backend must fulfill.

---

## 9. Safety invariants

1. **`experience-reviewer` is read-only.** It flags, never rewrites. Any suggestion to have the reviewer apply its own findings is out of scope — flagging is the deliverable.

2. **`experience-status` is read-only.** It never writes files, never elicits `[design] output_dir` (stops at "not configured"), never advances state.

3. **The quality floor is non-negotiable.** No skill may produce output that explicitly defers the quality floor ("we'll add states later," "accessibility to follow"). The floor is the minimum bar for any output to leave the skill; if the design can't meet it, the skill surfaces to the human rather than shipping below floor.

4. **No universal values, ever.** No skill may ship a fixed colour value, spacing value, timing curve, or breakpoint table — nothing that would arrive the same way for two unrelated products. This binds what the pack carries. It does not bind what a run writes: `design-system` resolves project-specific values into its artifact wherever the approved direction, the incumbent system, a stated constraint or the named platform's convention gives it the authority, and records a domain nothing reached as unresolved rather than filling it.

5. **No tool winners.** No skill names a specific design tool (Figma, Sketch, Penpot, etc.) as the prescribed tool. Tool categories are allowed ("a vector-based screen design tool"); specific tools are not.

6. **The aesthetic direction must be grounded, not aspirational.** A `creative-direction` output that only lists adjectives ("premium, calm, focused") without named referents (precedent products or traditions that achieve those qualities) has not met the skill's output contract.

---

## 10. Design decisions and rationale log

### Why the pack ships no values (from v1, amended)

The pack ships in two parts: method (what to decide and how) and the system's shape (the structure decisions live in). Pack-level values are intentionally absent because: (a) they are always project-specific, (b) the authoritative standards (WCAG, HIG, Material) already publish them and are better maintained, (c) any values we ship create a false anchor the adopter will optimize against rather than derive from first principles. The method works precisely because it forces derivation.

**Alternative considered:** ship sensible defaults for common stacks (one for web, one for iOS, one for Android). Rejected because "sensible defaults" become cargo-culted values within one sprint. Teams stop asking "does this ratio serve the aesthetic direction?" and start asking "does this match the default?" The method value evaporates.

**Amendment.** v1 also read this rule as forbidding a *run* from resolving values, which left the artifact naming categories and deciding nothing. That is the same failure by another route: the decisions still got made, just downstream by an agent holding less design context, which is exactly where a category default gets reached for. The prohibition now binds what the pack carries, and a run resolves what its authority supports. The pack-level half is the one a mechanical check can hold, and a check holds it over every Markdown file in this pack.

### Why user-scope by default (from v1)

Design method is the same across repos; only the artifacts differ. Installing per-repo would require reinstallation on every new project without any change to the skills. The scope decision mirrors `architect` (same reasoning: the method is portable, the knowledge surface is not project-specific).

**Alternative considered:** repo-scope to colocate the skill definitions with the artifacts they produce. Rejected because it creates installation friction for cross-repo designers and doesn't improve artifact colocation (artifacts already live in the repo via `agentbundle-layout.toml`; the skills don't need to be repo-installed to write to a repo path).

### Why the experience-reviewer runs forked (from v1)

Structurally identical to core's adversarial-reviewer rationale. An authoring-session reviewer is primed by the authoring intent and cannot read the artifact as a stranger would. The value of the review comes from genuine ignorance of the design rationale. See core DESIGN.md §15 for the parallel decision.

**Alternative considered:** stateful review that has access to the authoring session's reasoning, so it can review the design *and* the decision trail. Rejected for the same reason as in core: a reviewer that knows what was intended will systematically read gaps charitably.

### Why genre methods now live inside information-architecture (approved by eugenelim, 2026-09-26)

Surface genres still have distinct structural logic, but they no longer need separate skill registrations to preserve it. The genre method is clearer as a selected reference inside `information-architecture`: the user chooses one IA skill, the brief's `surface-genre:` value selects the specialized method, and the method remains reviewable without making the skill roster carry six extra entries.

**Earlier rationale amended:** the v1 rejection below treated a single skill with a genre flag as the only alternative to separate registrations. The accepted shape is narrower: one IA skill with explicit genre routes and reference-loaded methods, not a hidden conditional tree.

### Why the original genre-direct split changed (from v1, amended)

At v1, each genre's distinct structural logic was recorded as the reason for separate registrations. A conversion surface's above-fold contract is not a weaker version of a dashboard's widget hierarchy — they are different structural problems. That method-preservation claim still stands, but registration is no longer the mechanism that preserves it.

**Alternative considered:** one `information-architecture` skill with a `genre:` parameter. Rejected in v1 because the genre-specific reasoning (above-fold contract, scroll story, social-proof architecture for conversion; TTFV architecture, Diátaxis typing for documentation) is substantive enough to need its own method body. Amended on 2026-09-26: the method body can stay first-class as a loaded reference while `information-architecture` owns the routing decision.

### Why correctness is the floor, not the ceiling (from v1)

Meeting the quality floor (WCAG AA, handle-all-states, reduced-motion) is necessary but not sufficient for a good design. A pack that only produced correct designs would produce accessible, complete, and inoffensive work — but work that competes on accessibility alone doesn't win. The `creative-direction` skill is the gate between correct and good: it creates the aesthetic constraint that the rest of the craft sequence must satisfy. Collapsing the two (treating taste as optional) produces work that no one complains about but no one uses.

**Alternative considered:** make `creative-direction` optional — treat aesthetic direction as a nice-to-have for when the team has time. Rejected because without a named aesthetic constraint, every subsequent craft decision becomes a local opinion (each screen looks "reasonable" in isolation; the thread has no visual coherence). The quality floor is a mechanical gate; the aesthetic direction is a coherence gate. Both are required.
