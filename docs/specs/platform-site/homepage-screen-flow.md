# Homepage Screen Flow — agent-ready-repo marketing site

Adopter journey: **Arrive → Orient → Evaluate → Try → Go Deeper**  
Each section maps to exactly one stage. One section, one job.  
Reference: `site/aesthetic-direction.md`, `.context/site-information-architecture.md`

---

## Section order and content brief

---

### Section 1 — HERO
**Journey stage:** Arrive  
**Component:** `Hero.astro`  
**Surface:** Dark zone (`--ds-hero-bg`)

**Job:** Answer "what is this?" in one breath and give the skeptic a reason to scroll.

**Headline (display scale, negative tracking, max 12 words):**
> The supervised AI operating model for software teams.

*Alt if above tests short:*
> Discovery. Build. Release. Supervised — not autonomous.

**Subhead (body-lg, hero-fg-2, max 30 words):**
> Three peer loops span the full SDLC. Hard mechanical gates, cold-read specialist reviewers, and human checkpoints at every handoff — so the agent can't certify its own work.

**CTAs (two, side by side):**
- Primary (amber fill): `Install the core loop →`
- Ghost: `See the packs →`

**Background treatment:**
- `--ds-hero-bg` canvas
- Radial amber glow anchored at center-top, 15% opacity (`--ds-accent-glow`) — static, not animated
- Optional: 1px grid lines at 4% opacity, 28px repeat (same as current `extra.css`)
- Pipeline SVG (`Discovery → Build → Release`) as a subtle background element at 8% opacity — **static only**. No looping animation. One-shot fade-in on load (300ms, `prefers-reduced-motion`: skip). Rubric applied: ambient looping animation fails cognitive-load test for task-focused audiences (Calabro 2024); the static SVG with amber gate nodes achieves the identity move without the attention cost.

**State:** Single state only — no async content, no loading state.

---

### Section 2 — STAT STRIP
**Journey stage:** Arrive → Orient  
**Component:** `StatStrip.astro`  
**Surface:** Dark zone (continuous with hero — no visual break)

**Job:** Specificity as trust signal. Numbers that a skeptical engineer stops for.

**Stats (monospace, tabular-nums, amber number, muted label):**

| Number | Label |
|---|---|
| `3` | supervised loops |
| `7` | adapters |
| `1` | pip install |

> **Amended 2026-07-16 (owner request):** the original fourth stat `0 self-certified builds` was dropped. The strip now carries three stats; design-system-foundations.md permits a three-or-four-item strip.

**Layout:** Horizontal strip, 3 items, separated by `1px solid --ds-hero-border`. Centered. Full-width.

---

### Section 3 — THE PROBLEM
**Journey stage:** Orient  
**Component:** inline section in `index.astro`  
**Surface:** Hard-cut to light zone (`--ds-surface`)

**Job:** Name the pain that makes the product necessary. Two sentences maximum. No bullet lists. The engineering lead should feel: *"yes, that is the actual problem."*

**Headline (h2, negative tracking):**
> An unattended loop makes unattended mistakes.

**Body (one paragraph, body-lg):**
> Agent coding tools have moved the leverage from the prompt to the loop. But a loop running unattended is also a loop making mistakes unattended — and it will self-certify its way out of every check you give it. The answer is not a tighter prompt. It is a supervised loop with mechanical gates the agent cannot bypass.

**Visual treatment:** Large section. Generous vertical padding. The text is the entire section — no card, no icon. The whitespace IS the emphasis (Hemingway iceberg).

---

### Section 4 — HOW IT WORKS (Three supervised loops)
**Journey stage:** Orient → Evaluate  
**Component:** `ThreeLoops.astro`  
**Surface:** Light zone (`--ds-surface-alt` for slight separation)

**Job:** Make the three-loop structure legible and memorable. Show the handoff chain. One loop per "moment" — staged, not a grid.

**Headline (h2):**
> Three supervised peer loops. One handoff chain.

**Layout:** Three sequential sections, each with:
- Loop name (h3, monospace label style)
- Pack tag (`core`, `product-engineering`, `release-engineering`) as amber chip
- Two-sentence description — what the agent does, what the human gates
- Human gate callout: amber left-border, gate ID, one-line description of the human decision
- Link: `Read the [loop] journey →`

**Loop 1 — Discovery Loop**
- Pack: `product-engineering · discovery-lead`
- Description: Raw idea → ratified brief. Five candidate shapes explored in parallel, collapsed through product, UX, architecture, and safety lenses.
- Human gates: G0 (go/no-go on the idea), G1.5 (shape sign-off), G2 (brief ratification), G3 (hand-off to build)
- "Human gate" callout: *"G3 — you approve a ratified decision brief, not a validated solution."*

**Loop 2 — Build Loop**
- Pack: `core · work-loop`
- Description: Spec → shipped code. Lint, typecheck, and tests must pass. Three specialist reviewers each read the diff cold, in a fresh session — adversarial by design.
- Human gates: Plan approval, PR merge (G4)
- "Human gate" callout: *"G4 — you merge only when adversarial review is clean and all gates pass."*

**Loop 3 — Release Loop**
- Pack: `release-engineering · release-lead`
- Description: Built → production. Autonomous e2e convergence on ephemeral environments. Deployed findings feed back to the build loop automatically.
- Human gate: G5 (prod ship — never autonomous)
- "Human gate" callout: *"G5 — prod ship always surfaces to a human. Always."*

**Pipeline visualization:**
Three nodes connected by arrows with gate labels between them. Amber highlight on the gate nodes. This is a proper SVG/CSS component — not Mermaid. Styled with design tokens.

---

### Section 5 — HUMAN CONTROL POINTS
**Journey stage:** Evaluate  
**Component:** `HumanGates.astro`  
**Surface:** Light zone (`--ds-surface`) — **not dark.** Rubric applied: two content-area dark bands with a light interruption between them (dark → light → dark → light) produces disorienting visual rhythm; Neo4j research confirms one dark zone (hero + stat strip) with the rest light is the stable pattern. Emphasis is achieved via amber-bordered gate cards within the light section, not a dark band.

**Job:** This is the product's primary differentiator. Most AI tools promise the agent does everything. This product is the opposite: it makes the human role specific and structural. Surface that explicitly.

**Headline (h2, display scale, amber accent on "you"):**
> Every loop surfaces to you at exactly the right moment.

**Subhead:**
> Not as a workaround — as a design principle. The agent runs the loop; you control the gates. Here is what each handoff asks of you.

**Content:** Gate cards — one card per gate, amber left-border (4px solid `--ds-accent`), light card background (`--ds-surface-alt`). Cards answer three fields: **When it fires**, **What you decide**, **What you're looking for**.

| Gate | Loop | What you decide |
|---|---|---|
| G0 — Go / No-go | Discovery | Is this idea worth exploring? |
| G1.5 — Shape sign-off | Discovery | Does the chosen shape fit the product strategy? |
| G2 — Brief ratification | Discovery | Is the decision brief complete enough to build from? |
| G3 — Handoff to build | Discovery → Build | Is this brief specific enough to spec? |
| Plan approval | Build | Is the plan's trio correct? Do the risk triggers fire? |
| G4 — PR merge | Build | Is adversarial review clean? Does the spec match the implementation? |
| G5 — Prod ship | Release | Is this safe to put in front of users? |

**CTA:** `Explore a full journey →` → `/journeys/core/`

---

### Section 6 — WORKS WITH YOUR AGENT
**Journey stage:** Evaluate  
**Component:** `AdapterMatrix.astro`  
**Surface:** Light zone

**Job:** Answer "does it work with my setup?" before the visitor has to ask. Trust signal — specificity over "works everywhere."

**Headline (h3, not h2 — this is a trust checkpoint, not a major section):**
> One install. Every major agent.

**Table:** (existing adapter table from index.md — same data, new visual treatment)

| Agent | Skills | Subagents | Hooks | Commands |
|---|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ | ✓ |
| Codex | ✓ | ✓ | ✓ | — |
| Cursor | ✓ | ✓ | ✓ | — |
| Copilot | ✓ | ✓ | ✓ | — |
| Gemini CLI | ✓ | ✓ | ✓ | — |
| Kiro IDE | ✓ | ✓ | ✓ | — |
| Kiro CLI | ✓ | ✓ | ✓ | — |

**Note below table:** "Switch adapters with one flag. Your skills, subagents, and hooks project into the layout each agent expects."

---

### Section 7 — INSTALL
**Journey stage:** Try  
**Component:** `InstallTerminal.astro`  
**Surface:** Light zone (`--ds-surface-alt`)

**Job:** Remove friction from the first action. Make the install feel fast and real.

**Headline (h2):**
> Start in one command.

**Terminal component:** Styled window with fake title bar (`• • •`), monospace font, amber prompt character (`❯`), four tabs:

```
Flagship loop      With discovery     Full inception     Solution architect
```

Tab 1 — Flagship loop:
```bash
❯ pip install agentbundle
❯ agentbundle install --pack core
```

Tab 2 — With discovery:
```bash
❯ agentbundle install --pack core
❯ agentbundle install --pack product-engineering --scope user
```

Tab 3 — Full inception:
```bash
❯ agentbundle install --profile inception
```

Tab 4 — Solution architect:
```bash
❯ agentbundle install --profile solution-architect
```

**Below terminal:** "One command lands the loop. Any agent that reads a skill file inherits it automatically."

---

### Section 8 — THE CATALOGUE
**Journey stage:** Go Deeper  
**Component:** `PackCatalogue.astro`  
**Surface:** Light zone

**Job:** Show the full catalogue for visitors who have decided to explore. Progressive: loops first (large, high-contrast cards), optional packs second (smaller, grouped by scope).

**Headline (h2):**
> The catalogue.

**Subhead:** "A curated library of packs — each shaped through practitioner research and RFC governance. Start with the loops."

**Layout:** Three tiers:

**Tier 1 — The three loops (large cards, amber accent, most prominent):**
- Core, Product Engineering, Release Engineering
- Each: pack name, scope chip, 2-sentence description, install command, "Read the journey →" link

**Tier 2 — User-scope packs (medium cards, 2-column grid):**
- Research, Architect, Experience, Contracts, Converters, Atlassian, Figma, Credential Brokers

**Tier 3 — Repo-scope packs (smaller cards, 3-column grid):**
- Governance Extras, User Guide (Diataxis), Monorepo Extras

**Progressive disclosure (rubric applied):** Tier 1 (3 loops) — always visible, large cards, full weight. Tier 2/3 — secondary tier with an obvious expand affordance. Decision rule: Hick's Law penalises simultaneously visible equally-weighted options, not hierarchically-differentiated tiers (Nielsen NN/G progressive disclosure + Jakob Nielsen 2024). The 3-always + 11-on-reveal pattern resolves the Hick/Nielsen tension: visitors pick a tier first (2-option decision), then pick within it. Never hide Tier 2/3 with no affordance — the "See all X packs →" label must be visible in the initial render, below the first row of Tier 2 cards which are partially visible (peek pattern signals more content without requiring expansion to know it exists).

---

### Section 9 — BUILD YOUR ORG
**Journey stage:** Go Deeper → Advocate  
**Component:** inline section  
**Surface:** Dark zone (footer-adjacent — the only second dark band, at the very bottom, reads as closure not interruption; acceptable because it is adjacent to the footer dark band and not sandwiched between two light sections)

**Job:** Address the engineering lead who wants to adopt this for their whole team, not just their own machine. The "build your org pack" concept.

**Headline (h2, hero scale):**
> Make it your team's operating model.

**Body:**
> Adopt the catalogue as-is, or fork it as your own. Write your house conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line — the loop, the reviewers, and the standards come out identical on every machine and in every agent.

**CTA (amber):** `How to build your org's catalogue →` → links to `/docs/guides/_shared/how-to/build-an-org-stack-pack/`

---

## State matrix (homepage-level)

| Component | States | Notes |
|---|---|---|
| Hero | Content only | No async — static |
| Stat strip | Content only | No async — static |
| ThreeLoops | Content only | Pipeline SVG: animated / static (reduced-motion) |
| HumanGates | Content only | Table — no async |
| AdapterMatrix | Content only | Table — no async |
| InstallTerminal | Content / tab-selected | JS for tab switching; default tab = "Flagship loop" |
| PackCatalogue | Content / expanded | JS for show-all toggle; default = Tier 1 visible + first 4 of Tier 2/3 |
| BuildYourOrg | Content only | No async |

All async components have `aria-busy` and skeleton states as per the frontend-engineering skill requirements. On this homepage, all content is static — no async states needed. The tab switcher and show-all toggle are the only interactive states.
