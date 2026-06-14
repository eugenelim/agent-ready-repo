# RFC-0033: A `design-craft` pack — framework-agnostic design discipline for interaction/visual designers

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-14
- **Date closed:** 2026-06-14
- **Related:** RFC-0030 (`product-engineering` pack — the new-audience precedent, and the UX-writing home) · RFC-0032 (architect `design-reviewer` subagent — established that opt-in design-side review is *not* bound by the three-reviewer ceiling, and that a design discipline can carry both a review skill and a review subagent) · RFC-0007 (first user-scope pack — `converters`) · RFC-0004 (install-scope per pack — the user-scope dimension) · RFC-0024 / RFC-0026 / RFC-0027 (copilot / cursor / gemini user-scope skill projection — packaging-no-obstacle) · `architect` pack (`architect-design` / `architect-diagram` / `architect-review` — the author→review house pattern and the method-not-data precedent) · `figma` pack (user-scope-default design-adjacent precedent) · `docs/CHARTER.md` (the four principles, "not a framework that picks your tech stack", "not a marketplace of specialized agents")

---

## The ask

**Recommendation (BLUF).** Add a new **opt-in, user-scope `design-craft` pack** that serves an audience the catalogue does not serve today — **interaction/visual designers** — with **framework-agnostic design *discipline*** shipped as **four skills + one shared checklist**: `aesthetic-direction`, `design-system-foundations`, `layout-and-information-architecture`, and `design-critique`, plus a shared `quality-floor` checklist (all-states + accessibility floor + "motion communicates state, honor reduced-motion"). Every skill is stripped to portable method — **zero** React/Vue/Tailwind/CSS, no Framer Motion, no static reference-data tables (px/ms/hex/easing/breakpoint values). All are **skills, not agents**; the pack is **habits, not infrastructure**. RFC now; the pack is built as a follow-on once accepted.

**Why now (SCQA).**
- *Situation.* The catalogue makes a repo ready for engineering agents and, since RFC-0030, for the product shaping *upstream* of specs. Design intent — the aesthetic direction, the token taxonomy, the information architecture that steer a UI build — has no home and no discipline.
- *Complication.* Designers (and design-eng hybrids) author that intent by hand, ad hoc, per feature, with no shared method that lives in the repo and survives handoff. The artifacts that *should* steer the build either aren't written down or aren't written down portably.
- *Question.* Should the catalogue carry that design discipline as a pack, in a shape that is lightweight, recognizable, stack-neutral, and opt-in — so it serves designers without burdening pure-engineering repos?

**Decisions requested** (each: recommended option · decide-by = on circulation close):

1. **Add the pack at all** → *yes, as an opt-in user-scope pack* (vs do-nothing / fold into `core` / fold into `product-engineering`).
2. **Serve a new audience** → *yes — interaction/visual designers, as authors of upstream **design intent** the build consumes* (the same seam RFC-0030 opened for product shaping). The load-bearing charter judgment; argued explicitly below.
3. **Skill roster** → *four skills + one shared checklist*: `aesthetic-direction` · `design-system-foundations` · `layout-and-information-architecture` · `design-critique`; shared `quality-floor` checklist.
4. **Framework-agnosticism** → *achievable for all four, with two named guardrails* baked into the build spec (point to external standards for floors/formats; phrase landmarks as platform-neutral wayfinding).
5. **Skill-vs-agent** → *all four are skills; zero agents* — each is an interactive authoring/critique discipline the designer runs, not an automated `work-loop` convergence rung; none needs a forked context or restricted tools. (RFC-0032 separately confirms a design discipline *may* later add a review subagent — see decision 5 / §4.)
6. **Install scope** → *user-scope-default, `allowed-scopes = ["user","repo"]`* — opt-in user scope is itself the demand validator (mirrors `architect`/`figma`).
7. **Packaging** → *as specified below; ship no `seeds/`* (carry any template as a skill asset the skill copies at runtime).
8. **Out-of-pack boundaries** → *UX-writing/voice-&-tone → `product-engineering`; data/diagram visualization → `architect`*. Non-goals.

---

## Problem & goals

**Problem (diagnosis).** The catalogue serves the people who *build* a product and, since RFC-0030, the people who *shape* it — but not the people who *design* its interface. An interaction/visual designer working alongside an AI agent has no shared, portable discipline for the work that most determines whether a UI is coherent: interrogating a vague aesthetic "vibe" into named goals, deriving a systematic token taxonomy from intent, structuring information so it can be read, and critiquing a design against recognized principles. Today that work is done ad hoc and, worse, often expressed in stack-specific terms (a Tailwind config, a Framer Motion snippet, a fixed token JSON) that don't travel, don't survive a stack change, and read as configuration rather than as the durable *design intent* that should steer the build. The expensive failure is incoherence: choices made without a named direction, tokens named for their literal value, layouts that ignore how people read, and designs that ship without ever being critiqued.

**Goals.**
- A lightweight, opt-in discipline for the core design-craft loop — **direct** (aesthetic direction) → **systematize** (foundations) → **structure** (layout/IA) → **critique** (heuristic review) — usable by a solo designer, a design-eng hybrid, and a design team alike.
- Anchored to **recognized** method (design-token semantics, reading-pattern research, usability heuristics, accessibility standards) — not invented jargon and not borrowed-and-renamed.
- **Strictly framework-agnostic** — portable method only; nothing that picks or assumes a tech stack (the charter's second "does not").
- Produces durable **design-intent** artifacts that live in the repo and steer the build, composing with `product-engineering` (intent) and `architect` (system design) rather than duplicating them.
- Stays **habits, not infrastructure** — clears the charter's four principles per skill, adds no `work-loop` reviewer subagents, no engine, no hooks, no validators.

**Non-goals** (could-have-been goals, deliberately dropped).
- **Not** for frontend *engineers* and **not** implementation — no React/Vue/Tailwind/CSS, no component code, no build tooling, no design-to-code handoff mechanics. The pack stops at design intent; the implementation boundary is `core`/stack packs.
- **Not** UX-writing / voice-&-tone — that serves a different audience (content/writers) and is proposed for `product-engineering`, not here.
- **Not** data or diagram visualization — that is `architect` territory (`architect-diagram`).
- **Not** prototyping or usability *validation* — that is `product-engineering`'s `de-risk-intent` (prototype-as-validator) seam, and it is tool-heavy.
- **Not** a static reference library — no values tables (px/ms/hex/easing), no breakpoint tables, no fixed token sets. Reference data fails the charter's "a habit, not a tool" bar; the pack ships the *method* to derive those values, never the values.
- **Not** a `work-loop` reviewer subagent — `design-critique` is a skill (an authoring-time discipline the designer runs interactively), not an automated convergence-loop reviewer. (RFC-0032 shows a design discipline *can* add such a subagent; this pack's v1 does not — see decision 5 / OQ#2.)

---

## Proposal

### Design brief at a glance

| Dimension | Decision |
|---|---|
| **Pack** | `design-craft`, opt-in, **user-scope-default** (`allowed-scopes = ["user","repo"]`). Habits, not infra. No `seeds/`, no hooks, no validators. |
| **Audience** | Interaction/visual designers (and design-eng hybrids) — authors of upstream **design intent**, not implementers. |
| **Skills** | `aesthetic-direction` · `design-system-foundations` · `layout-and-information-architecture` · `design-critique` (4 skills). |
| **Shared checklist** | `quality-floor` — all-states + accessibility floor + "motion communicates state, honor reduced-motion"; referenced by the authoring skills and applied by `design-critique`. |
| **Agnosticism** | Strict: zero stack specifics; method only; two named guardrails (below). |
| **Skill-vs-agent** | All skills. Zero agents — no `work-loop` reviewer subagents (a future `design-reviewer` is left open per RFC-0032; OQ#2). |
| **Artifacts** | Durable design-intent docs (e.g. an aesthetic-direction doc, a token-taxonomy rationale) the designer writes and the build references. Carried as **skill assets** the skills copy at runtime (no `seeds/`). |
| **Guides** | A per-pack Diátaxis home at `docs/guides/design-craft/` (via `new-guide`). |
| **Seams** | `product-engineering` (intent upstream; UX-writing), `architect` (system design; diagrams), `core` (the build the design intent steers). |

### 1. The audience and the "design intent" framing (decision 2 — the charter judgment)

The catalogue's mission is "repos ready for AI agents doing real engineering work," and its scope is explicitly *not* "a framework that picks your tech stack." A pack *for designers* is a genuinely new audience — so it has to earn its place against the mission, not just the four principles.

It earns it on the **same seam RFC-0030 opened**: `product-engineering` serves people who are not engineers (PMs, requirements engineers) because the *artifact they produce* — an intent, a brief — is upstream of, and consumed by, the engineering the catalogue exists to support. `design-craft` is the design-side twin. An **aesthetic-direction doc**, a **token-taxonomy rationale**, an **information-architecture** all live in the repo as durable design intent and *steer the UI build* exactly the way an intent steers a spec. The pack is in-scope as **upstream design intent the build consumes**, not as a design tool. This is the falsifiable claim the approver is signing: *if* the design discipline produced only ephemeral, tool-bound artifacts that never steer a build, it would be out of scope — but the four skills are deliberately shaped to produce durable, portable, repo-resident intent, which is what keeps them in.

### 2. The skill roster, mapped to the complete design workflow (decision 3)

The roster is cut to span the recognized interaction/visual-design pipeline — and *only* that pipeline, with prototyping, validation, and handoff deliberately left to their owners.

| Workflow stage | Recognized method | Pack coverage |
|---|---|---|
| Aesthetic direction | mood/brand/emotional goals → a named, written direction | **`aesthetic-direction`** |
| Information architecture & layout | IA, hierarchy, F/Z scanning, progressive disclosure, wayfinding | **`layout-and-information-architecture`** |
| Design-system foundations | semantic-over-literal tokens, ratio-based scales, atomic composition ("build systems, not pages") | **`design-system-foundations`** |
| Visual / mockup synthesis | apply direction + system + layout to a concrete screen | *convergence of the three above — no separate skill* |
| State / a11y / motion quality floor | handle-all-states, accessibility floor, reduced-motion | **`quality-floor`** (shared checklist) |
| **Critique / review** | **heuristic evaluation** (recognized usability heuristics, severity-rated) | **`design-critique`** |
| Prototyping & validation | clickable prototype, usability test | *out → `product-engineering` `de-risk-intent`* |
| Dev handoff | specs/assets to engineers | *out → implementation boundary* |

The four skills give the pack the catalogue's own **author → review** symmetry — the same shape `architect` ships (`architect-design`/`architect-diagram` author and produce; `architect-review` critiques). `design-critique` is the design-side `architect-review`.

**`aesthetic-direction`** — interrogate a vague aesthetic "vibe" into **named emotional/brand goals** and a written **aesthetic-direction doc** that downstream work references; provide **coherence arbitration** when choices conflict (which goal wins, and why). Method only: the interrogation sequence and the doc shape, not any palette or font.

**`design-system-foundations`** — derive a systematic **token/scale taxonomy from intent**: semantic-over-literal naming, ratio-based scales (the *concept* of a ratio, not a fixed set), accessibility-as-floor, contrast budgets, "purpose before token," and the **atomic-composition** mental model (build up from primitives — "build systems, not pages"). It ships the **derivation method** and **points to external standards** (WCAG for the contrast floor; the W3C Design Tokens interchange shape) — it never reprints a values table.

**`layout-and-information-architecture`** — hierarchy, depth-vs-breadth, **reading patterns** (F/Z scanning), **progressive disclosure**, and platform-neutral **wayfinding/orientation** (landmarks framed as *concepts*, never ARIA roles or CSS grid). Stack-neutral cognitive/IA method; no layout code.

**`design-critique`** — structured **heuristic evaluation**: review a design against recognized usability principles, map each issue to the violated principle, assign a **severity rating**, and produce a prioritized findings list with recommendations. The most framework-agnostic skill in the set (heuristics are stack-neutral by construction) and the most-recurring (critique happens every iteration). It applies the shared `quality-floor` checklist as part of the pass. A **skill**, not a `work-loop` reviewer subagent — the designer runs it interactively at authoring time; it is the UI/UX-heuristic twin of `architect-review` (the skill), distinct from RFC-0032's `design-reviewer` subagent (the automated convergence rung). A `design-craft` review subagent is left open for a later RFC (OQ#2), exactly as RFC-0032 added one to `architect` alongside its review skill.

**Shared `quality-floor` checklist** — referenced by the authoring skills and applied by `design-critique`: **handle all states** (empty/loading/error/success/partial/disabled/etc.), **accessibility floor** (meet the recognized standard — the skill points to WCAG, it does not reprint ratios), and **"motion communicates state, honor reduced-motion"** (motion as a *principle* — respect the user's reduced-motion preference — not a CSS media-query snippet). This checklist is the **durable residue of three candidates declined as standalone skills** because each is framework-locked or reference-data on its own: component-state authoring, responsive/breakpoint strategy, and motion choreography. Their portable core survives here; their stack-specific mass does not ship.

### 3. Framework-agnosticism — confirmed, with two guardrails (decision 4)

The charter forbids a pack that picks a tech stack. This pack ships **zero** React/Vue/Tailwind/CSS, no Framer Motion, no animation library, and **no static reference-data tables** (px/ms/hex/easing values, breakpoint tables, fixed token sets). Each skill is the *portable method* only. Two guardrails make this enforceable in the build spec and at review:

- **Guardrail A — point to standards, never reprint values.** `design-system-foundations` and `quality-floor` reference external standards (WCAG for the accessibility/contrast floor; the W3C Design Tokens interchange shape) rather than shipping any ratio/px/hex/ms table. The line is *"derive a taxonomy from intent"* (method) vs *"here are the tokens"* (data, which fails the "habit not tool" bar).
- **Guardrail B — concepts, not platform primitives.** `layout-and-information-architecture` phrases landmarks/wayfinding as platform-neutral *orientation concepts* (applicable to mobile, voice, print, web), never ARIA roles or CSS grid; `quality-floor`'s motion line is the *principle* (honor reduced-motion), never `@media (prefers-reduced-motion)`.

A build-spec lint (a stack-token grep over the pack's SKILL.md + references, analogous to the no-attribution and rail-C greps in RFC-0007) and adversarial review enforce both. `aesthetic-direction` and `design-critique` carry near-zero agnosticism risk by nature (interrogation→doc; heuristic critique).

### 4. Skill-vs-agent (decision 5)

All four are **skills**. None needs a forked context window or a restricted tool surface — each is an authoring/interrogation/critique discipline a designer reaches for interactively, exactly like `architect-design` and `architect-review` (both skills). The determination rests on the *nature of the work*, not on a reviewer headcount: these are interactive authoring disciplines, not automated `work-loop` convergence rungs.

`design-critique` is the case that warrants the most care, because RFC-0032 just landed a forked-context `design-reviewer` *subagent* for `architect`. Two things follow. First, RFC-0032's accepted reading is that the charter's "three reviewers is the ceiling" scopes the **core code-review lenses** (adversarial/security/quality), **not** opt-in design-side review — so the ceiling is *not* the reason `design-critique` is a skill, and this RFC does not lean on it. Second, RFC-0032 establishes that a design discipline can carry **both** a review skill (`architect-review`) **and** a review subagent (`design-reviewer`). This pack's v1 ships only the skill, because the value designers reach for is interactive heuristic critique during authoring, not an automated rung in someone else's build loop. A `design-craft` `design-reviewer` subagent — the exact twin of RFC-0032's — is a coherent, ceiling-unconstrained follow-on, left open in OQ#2. Zero agents are added in v1.

### 5. The four principles, per skill (the charter gate)

Each skill clears all four bars. Bar #4 (used-often-enough) is the honest hard one for design work, addressed in decision 6.

| Skill | 1 Universal | 2 Substantive | 3 Habit | 4 Used-often |
|---|---|---|---|---|
| `aesthetic-direction` | vibe→named-goals is stack-neutral | nothing else names emotional goals or arbitrates coherence | interrogation discipline + a doc | start of every feature/redesign with a UI surface (burstiest — gated user-scope) |
| `design-system-foundations` | derivation method; points to standards | no token-taxonomy derivation exists elsewhere | "purpose before token" discipline | every new system/redesign; re-referenced during component work |
| `layout-and-information-architecture` | cognitive/IA principles, any platform | no IA/reading-pattern method exists elsewhere | a way of structuring information | every screen and flow |
| `design-critique` | heuristics are stack-neutral by construction | `architect-review` critiques *architecture*, not UX/UI | structured critique discipline | **every design iteration and review — the most-recurring skill; the bar-#4 anchor** |

### 6. Install scope — user-scope-default, opt-in as the demand validator (decision 6)

Design work is **bursty** — reached for per feature, per redesign, per new product, not daily. That is exactly the cadence of `architect` (design docs) and `figma`, both gated **user-scope-default** for the same reason. User-scope gating *is* the lightweight demand validator: only designers who want the discipline install it, so nothing is forced on any pure-engineering repo, and bar #4 becomes the honest test *"reached for regularly by the designers who installed it"* — which the roster passes (and `design-critique`, the most-recurring skill, makes comfortable rather than marginal). The pack declares `default-scope = "user"`, `allowed-scopes = ["user","repo"]` (a design-system repo may want it pinned per-repo). This is how bar #4 is cleared honestly — not waved past, and not by claiming daily use.

**Packaging is no obstacle (verified).** User-scope agents/skills are fully supported across every shipped adapter — RFC-0024 (copilot), RFC-0026 (cursor), and RFC-0027 (gemini) each gave their skill primitive a user-scope target, and `architect`/`research` already ship user-scope-default to all seven adapters (`claude-code`, `codex`, `copilot`, `kiro-ide`, `kiro-cli`, `cursor`, `gemini`).

### 7. Pack shape (decision 7 — the build follow-on)

```
packs/design-craft/
├── pack.toml
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── .apm/
    └── skills/
        ├── aesthetic-direction/
        │   ├── SKILL.md          # lean; detail in references/
        │   ├── references/
        │   └── assets/           # e.g. aesthetic-direction-doc template (copied at runtime)
        ├── design-system-foundations/
        │   ├── SKILL.md
        │   └── references/
        ├── layout-and-information-architecture/
        │   ├── SKILL.md
        │   └── references/
        └── design-critique/
            ├── SKILL.md
            ├── references/       # the quality-floor checklist + heuristic set live here
            └── assets/
```

`pack.toml` declares `categories`/`keywords`, `[pack.adapter-contract] version` (matching the pure-markdown-skills packs — `research` is at `0.12`; the spec pins the exact level at build), `[pack.install] default-scope = "user"` + `allowed-scopes = ["user","repo"]`, the `allowed-adapters` list (all seven shipped adapters), `[pack.links]` (homepage/repository/`documentation` → `docs/guides/design-craft/`), and a `[[pack.maintainers]]` entry. A `.claude-plugin/plugin.json` and a `README.md` ship per the standard pack shape. Skills follow **progressive disclosure** — SKILL.md lean, detail in `references/`. The shared `quality-floor` checklist lives as a `references/` file (referenced by the authoring skills and applied by `design-critique`).

**No `seeds/`.** A pack with a non-empty `seeds/` cannot declare `"user" ∈ allowed-scopes` (RFC-0004 Rail A; confirmed by the RFC-0030 erratum). Any template the pack ships (e.g. the aesthetic-direction doc) is carried as a **skill asset** the skill copies into the repo at runtime — so the template travels with the skill and the filled doc still lands repo-scope, with no scope conflict. No hooks, no `<adapt:NAME>` markers (RFC-0007's three user-scope refusal rails pass by construction).

**Registration.** A new pack ⇒ `pack.toml` + `.claude-plugin/plugin.json` + aggregation into the top-level `marketplace.json`. As a user-scope-default pack, `design-craft` is **not projected into this repo's working tree** (like `architect`/`figma`/`research`) but **must** appear in `marketplace.json` — the build refreshes it. Guides land via `new-guide` under `docs/guides/design-craft/`.

---

## Options considered

**Axis A — where design discipline lives** (MECE along *the home of the discipline*; includes do-nothing):

| Option | Prior art | Trade-off |
|---|---|---|
| **Do-nothing** (stays ad hoc) | status quo | Zero cost; design intent stays unwritten or stack-bound, never steers the build portably. Cost of delay: every designer re-invents the method, incoherently. |
| Fold into `core` | `core` owns the universal layer | Forces design discipline onto every pure-engineering repo — violates opt-in, bloats `core`, fails "substantive-not-duplicative" for non-UI projects. |
| Fold into `product-engineering` | RFC-0030 | Different audience (PM/requirements vs visual/interaction design) and different artifact (intent/brief vs aesthetic direction/tokens/IA). You explicitly route UX-writing *into* `product-engineering`; routing design *craft* there too would conflate two audiences. |
| **New opt-in user-scope pack** ★ | RFC-0030 (`product-engineering`), RFC-0007 (`converters`), `architect`/`figma` | Clears Principle 2 (substantive, new audience, not duplicative); opt-in user scope keeps pure-eng repos clean and validates demand. |
| External design tool only | Figma/design tools | Already exists for *artifacts*; but offers no portable, repo-resident *discipline* that steers an AI build — the whole point. |

**Axis B — the skill roster** (MECE along *which design-workflow stages get a skill, partitioned by portable-method vs framework-locked/reference-data*): the recognized pipeline is direction → IA/layout → foundations → (mockup synthesis) → critique, with prototyping/validation and handoff downstream. Survivors as portable method become skills; reference-data/stack-locked candidates collapse into the shared checklist or stay out.

| Roster option | Verdict |
|---|---|
| 1 mega-skill ("design") | Rejected — buries four distinct disciplines; no progressive disclosure; un-reachable triggers. |
| 3 skills + checklist (original scope) | Viable but asymmetric — authoring skills with no critique skill, unlike every other authoring discipline in the catalogue (`architect`). |
| **4 skills + checklist** ★ (add `design-critique`) | Completes the author→review symmetry; `design-critique` is the most agnostic and most-recurring skill, strengthening bar #4. |
| 6–7 skills (add component-state, responsive, motion as standalones) | Rejected — the three extra candidates are framework-locked or reference-data on their own; their portable residue is the shared `quality-floor` checklist, not three more skills. |

**Axis C — install scope** (MECE): repo-scope-default [forces design on every repo] · **user-scope-default** ★ [opt-in; mirrors `architect`/`figma`; opt-in is the demand validator] · not-yet/validate-demand-first [a separate trial phase is redundant when user-scope opt-in *is* the trial].

**Axis D — agent-vs-skill** (MECE along *does any candidate need a forked context or restricted tools?*): all agents [rejected — none needs isolation; they are interactive authoring disciplines] · some agents (`design-critique` as a `work-loop` reviewer subagent) [rejected *for v1* — the value is interactive critique during authoring, not an automated convergence rung; but RFC-0032 shows this is a coherent, ceiling-unconstrained *follow-on*, not a closed door — OQ#2] · **all skills** ★.

---

## Risks & what would make this wrong

**Pre-mortem (top failure modes + mitigations).**
- *A skill smuggles in stack specifics or a values table* (the agnosticism failure). → Guardrails A/B (decision 4), a build-spec stack-token grep + adversarial review, and the explicit "method not data" line per skill. **This is the riskiest assumption — spiked below.**
- *Designers never reach for it* (fails bar #4). → Opt-in user scope (only installs for designers who want it); `design-critique` recurs every iteration, anchoring bar #4; the discipline is reached for at the start of every UI feature.
- *It drifts toward implementation* (becomes a frontend-eng pack). → Hard Non-goal: no component code, no handoff mechanics; the pack stops at design intent; the implementation boundary is `core`/stack packs.
- *Audience creep* — designers expect UX-writing, prototyping, or data-viz here. → Explicit Non-goals route each to its owner (`product-engineering`, `de-risk-intent`, `architect`).
- *It reads as a borrowed-and-renamed catalogue.* → Every technique is framed on its own merit and anchored to recognized public method (design-token semantics, reading-pattern research, usability heuristics, accessibility standards), not to any source roster.

**Key assumptions (falsifiable).**
- *Each of the four skills can be expressed as portable method with zero stack specifics and no values table.* (Spiked below.)
- *Design discipline is in-scope as upstream design intent the build consumes* — falsifiable if the artifacts turn out to be ephemeral/tool-bound and never steer a build; the skills are shaped to produce durable repo-resident intent precisely to hold this.
- *Opt-in user scope is a sufficient demand validator* — falsifiable if a separate measured trial is needed before building; `architect`/`figma`/`product-engineering` all shipped on this basis.
- *`design-critique` as a skill (not a subagent) is the right call for v1* — falsifiable if real use wants it wired into `work-loop` as an automated rung; RFC-0032 shows that is an available follow-on (a `design-reviewer` twin), not a contradiction.

**Drawbacks (not "none").** A fourth product-adjacent surface — after the `core` brief layer, `architect`, and `product-engineering` — raises the catalogue's conceptual area and serves an audience the maintainers are not themselves the primary user of (design vs engineering) — so demand signal is thinner than for an eng pack. Strict agnosticism makes the skills *less* immediately actionable than a stack-specific cheat-sheet would be (a designer wanting "the Tailwind config" won't find it — by design). And four skills, even opt-in, is real ongoing maintenance for a discipline outside the maintainers' core expertise.

---

## Evidence & prior art

**Spike / de-risk (riskiest assumption: can every skill stay framework-agnostic with no values table?).** Worked per skill:
- `aesthetic-direction` — pure interrogation → written doc + coherence arbitration. No stack surface at all (mirrors `architect-design`, which ships a doc-shaping method, not a stack). **Agnostic ✓.**
- `design-system-foundations` — the only real risk (the values-table trap). Resolved by Guardrail A: ship the *derivation method* (semantic-over-literal naming, ratio-as-concept, purpose-before-token, atomic composition) and **point to** WCAG (contrast floor) and the W3C Design Tokens interchange shape rather than reprint any ratio/px/hex table. The W3C Design Tokens format is itself stack-neutral interchange (tool-exchange JSON, not a framework), which confirms the *method* exists independent of any stack. **Agnostic ✓ with Guardrail A.**
- `layout-and-information-architecture` — cognitive/IA principles (F/Z scanning, progressive disclosure) are platform-neutral; the one risk (landmarks → ARIA/CSS) is closed by Guardrail B (wayfinding as concept). **Agnostic ✓ with Guardrail B.**
- `design-critique` — heuristic evaluation is stack-neutral by construction (it critiques *any* UI against recognized principles). **Agnostic ✓✓.**
- Shared `quality-floor` — all-states is conceptual; accessibility floor *points to* the standard; the motion line is the *principle* (honor reduced-motion), not the CSS query. **Agnostic ✓.**

**Spike passes:** all four skills + the checklist are expressible as portable method, with the two named guardrails carrying the only real risk (`design-system-foundations`, layout landmarks). `architect` is the in-repo proof that a design-adjacent pack ships method/rubric, not data.

**Repo precedent.**
- RFC-0030 (`product-engineering`) — the new-audience, opt-in, user-scope, habits-not-infra pattern; the precedent that the catalogue can serve non-engineers whose artifacts steer the build; the UX-writing home this pack routes to.
- RFC-0032 (architect `design-reviewer` subagent) — the governing precedent for the skill-vs-agent call (§4): its accepted reading scopes the three-reviewer ceiling to the core code-review lenses (not opt-in design-side review), and it ships *both* a review skill and a review subagent for one design discipline — making a future `design-craft` `design-reviewer` (OQ#2) a coherent, ceiling-unconstrained follow-on.
- RFC-0007 (`converters`) — first user-scope pack; ships no `seeds/`, no hooks, no `<adapt:>` markers (the three refusal rails); the automated-grep enforcement pattern this RFC reuses for the agnosticism lint.
- RFC-0004 — the install-scope-per-pack dimension `design-craft` consumes.
- `architect` (`architect-design`/`architect-diagram`/`architect-review`) — the author→review house pattern `design-critique` completes, and the in-repo proof that a design-adjacent discipline ships method/rubric, not values; user-scope-default to all seven adapters.
- `figma` — user-scope-default design-adjacent precedent.
- RFC-0024 / RFC-0026 / RFC-0027 — copilot/cursor/gemini user-scope skill projection → packaging is no obstacle.
- `docs/CHARTER.md` — the four principles and "not a framework that picks your tech stack" (the agnosticism constraint). Note: its "not a marketplace of specialized agents" / three-reviewer ceiling is *not* the basis for this pack's all-skills call — RFC-0032 scoped that ceiling to the core code-review lenses; §4's reasoning rests on the nature of the work instead.

**External prior art** (✓ = fetched and confirmed by the author).
- ✓ **W3C Design Tokens Format Module 2025.10** — reached its *first stable version* (Oct 2025) and supports **alias/reference tokens** (one token referencing another) — grounds "semantic-over-literal naming" as recognized, stack-neutral method and shows the interchange shape is framework-agnostic. ([stable-version announcement](https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/), [DTCG](https://www.w3.org/community/design-tokens/))
- ✓ **NN/g F-shaped reading pattern** — "Eyetracking research shows that people scan webpages and phone screens in various patterns, one of them being the shape of the letter F" (identified 2006 via eye-tracking) — grounds the reading-pattern method. ([F-pattern](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/))
- ✓ **Progressive disclosure (NN/g)** — defer advanced/rarely-used features to a secondary screen so interfaces are easier to learn without removing capability — grounds the layout method. ([progressive disclosure](https://www.nngroup.com/videos/progressive-disclosure/))
- ✓ **Usability heuristics (NN/g)** — a set of recognized general UI principles, originally 1990 (with Molich), refined 1994; heuristic evaluation maps each issue to a violated principle with a severity rating — grounds `design-critique`. ([10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/))
- ✓ **Atomic design (Brad Frost, 2013)** — atoms/molecules/organisms/templates/pages as a *mental model* ("build systems, not pages"), explicitly "not a linear process" and stack-neutral — grounds the composition method folded into `design-system-foundations`. ([Atomic Design ch.2](https://atomicdesign.bradfrost.com/chapter-2/))
- ✓ **WCAG 2.3.3 Animation from Interactions** — motion triggered by interaction "can be disabled, unless essential," honored via `prefers-reduced-motion` — grounds the `quality-floor` reduced-motion line as a recognized accessibility floor, framed as a principle. ([WCAG 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html))
- ✓ **Design workflow stages** — direction → wireframe/IA → mockup → prototype → handoff is the recognized pipeline; the pack covers direction/IA/foundations/critique and leaves prototype/handoff to their owners. ([UXPin — wireframe/mockup/prototype](https://www.uxpin.com/studio/blog/prototypes-wireframes-mockup-difference/))

---

## Open questions

1. **Exact `[pack.adapter-contract]` version pin** — `research` is at `0.12`; the build spec pins the level once the pack's primitive surface is final (pure-markdown skills should match `research`). *Default:* match `research` (`0.12`). *Owner:* eugenelim. *Decide-by:* spec authoring.
2. **Does `design-craft` add a `design-reviewer` subagent (the RFC-0032 twin)?** Decision 5 stands for v1 (interactive `design-critique` skill only); this asks only whether a *later* RFC adds the automated convergence-rung twin RFC-0032 built for `architect` — it is not re-litigating v1, and RFC-0032's reading means the three-reviewer ceiling does not block it. *Default:* skill only for v1; add the subagent via a follow-on RFC if real use wants it wired into `work-loop`. *Owner:* eugenelim. *Decide-by:* post-adoption signal.

---

## Follow-on artifacts

Filled in on acceptance:
- **ADR-NNNN** — the "design-craft serves designers as upstream design-intent authors" scope decision + the strict-agnosticism guardrails (the durable architectural record).
- **Spec:** `docs/specs/design-craft-pack/` (via `new-spec`) — the four skills + the shared `quality-floor` checklist, progressive-disclosure SKILL.md + `references/`, the runtime-copied asset templates (no `seeds/`), `pack.toml`/`plugin.json`/`README.md`, the agnosticism stack-token grep as a `Tests:` entry + CI check, `marketplace.json` registration, and the `docs/guides/design-craft/` Diátaxis set.
- **Guides:** via `new-guide` — an explanation (the design-craft loop and why portable discipline), how-tos (one per skill or grouped), and a reference (the four skills + the quality-floor checklist).
- **No CONVENTIONS edit.** The agnosticism stack-token lint ships as a **pack-scoped check** (a grep over `packs/design-craft/`, the RFC-0007 enforcement pattern) — *not* a top-level convention. Generalizing it into a repo-wide convention would be a separate RFC, decided on its own merits, never smuggled in via this pack's spec.
