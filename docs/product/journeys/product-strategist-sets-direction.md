---
type: customer-journey
slug: product-strategist-sets-direction
persona: product-strategist
outcome: altitude-0-direction-committed-and-cascaded
surface: cross-platform
status: proposed
initiative_links:
  - id: INI-002
    name: Platform Core
    milestones: M4 (primary); M2 (prerequisite — frame-situation must exist for cascade routing)
    role: primary
updated: 2026-07-18
---

# Journey: Product strategist sets altitude-0 direction

**Persona:** A product strategist, CPO, or senior PM working at altitude-0 — company or multi-product level. They set the strategic direction that all initiatives must align to. Their time horizon is years, not quarters. In smaller orgs this may be the same person as the product engineer; in larger orgs it is a distinct role with a distinct artifact vocabulary (OKRs, PRFAQs, market analysis, portfolio position).

**Outcome:** A set of committed altitude-0 artifacts — PRFAQ, OKR cascade, market context, portfolio position — that translate company direction into initiative-level shaping inputs. Gaps identified by the OKR cascade feed directly into `frame-situation` as shape-typed shaping items, closing the loop between altitude-0 direction and altitude-1 shaping.

**Surface:** cross-platform — CLI/terminal, agent-assisted.

**Trigger:** Annual or quarterly planning cycle; a significant market event requiring strategic re-evaluation; or a new initiative cluster being scoped and the strategist needs to anchor it in altitude-0 thinking.

**End state:** Altitude-0 artifacts committed to `docs/product/shaping/`. OKR gaps routed to `[shaping_queue]` as `shape`-typed items for the product engineer to pick up via `frame-situation`. The initiative portfolio has a visible, justified strategic rationale that any team member can read.

---

## Prerequisites

| Pack | Scope | Status | Provides |
|---|---|---|---|
| product-strategy pack | user | planned (M4) | SWOT, Porter's Five Forces, PESTLE, BCG Matrix, OKR cascade, PRFAQ |
| PE pack | user | M2 required for cascade routing | `frame-situation` — target of the OKR cascade cross-pack routing |

**One-time setup (when M4 ships):**
1. Install product-strategy pack at user scope — altitude-0 direction applies across repos and orgs.
2. Install PE pack at user scope as a co-install — required for OKR cascade routing to `frame-situation`; absent PE pack produces a "frame-situation not found — install PE pack" diagnostic rather than a silent failure.
3. For each repo where OKR gaps will be routed to the shaping queue: install core pack at repo scope — `workspace.toml` is committed to `main` as part of M1 Batch 2; no branch configuration needed.

**Scale:** both packs are user-scoped. In smaller orgs the strategist and PE may be the same person with both packs already installed. The cross-pack dependency (OKR cascade → `frame-situation`) is agent-mediated — the strategist invokes both in sequence; no mechanical cross-pack wiring is assumed.

---

## Interaction model

### Current state — before M4

```mermaid
sequenceDiagram
    participant S as Product Strategist
    participant A as Agent
    participant F as External tools (Notion, slides, spreadsheets)

    Note over S,F: Altitude-0 work today — disconnected
    S->>F: Write OKRs in Notion / Google Docs
    S->>F: Build market analysis in slides
    S->>A: Help me think through portfolio position
    A-->>S: Ad-hoc analysis in session context
    Note over A: Session closes — analysis lost
    S-->>S: Copy insights manually into initiative briefs
    Note over S: No committed artifact — no cascade into shaping queue
```

### To-be state — M4 shipped

```mermaid
sequenceDiagram
    participant S as Product Strategist
    participant A as Agent
    participant SK as Skills (product-strategy pack)
    participant SA as docs/product/shaping/
    participant WS as workspace.toml

    Note over S,WS: Altitude-0 direction — M4+
    S->>SK: PESTLE + Porter's Five Forces [context brief]
    SK->>SA: Write market-context.md (macro + competitive landscape)
    S->>SK: BCG Matrix + SWOT [portfolio snapshot]
    SK->>SA: Write portfolio-position.md
    S->>SK: PRFAQ [press release draft for the initiative cluster]
    SK->>SA: Write prfaq.md (altitude-0 forcing function)
    S->>SK: OKR cascade [company OKRs]
    SK->>SA: Write okr-cascade.md (company → team → initiative gaps)
    SK-->>S: Gaps identified: [gap-A, gap-B] → route to frame-situation?
    S->>WS: [shaping_queue].backlog += {slug: gap-A, needs: nothing}
    Note over WS: Product engineer picks up gap-A via check-workspace
    Note over WS: frame-situation routes gap into six-step sequence
```

---

## Stage 1: Market Context

### Now

| Row | Content |
|-----|---------|
| **Actions** | Gathers market signals manually from news, analyst reports, competitors. Synthesises in slides or Notion. Shares in planning meetings. |
| **Emotions** | Informed but scattered (neutral). The synthesis is good but lives outside the platform — it can't be referenced by shape-room skills. |
| **Pains** | "My market analysis is in a Notion page that no one else in the team reads." "No structured format — each strategist does it differently." "The agent running `frame-situation` has no way to access the market context I've already done." |
| **Opportunities** | Committed market-context artifact in `docs/product/shaping/` that `frame-situation` can reference when routing a signal; PESTLE and Porter's Five Forces as the structuring framework. |

> **With M4** — PESTLE + Porter's Five Forces skills ship: structured market-context artifact committed; feeds directly into `frame-situation`'s Wardley capability-maturity situational-awareness input.

---

## Stage 2: Portfolio Position

### Now

| Row | Content |
|-----|---------|
| **Actions** | Assesses where each initiative sits in the portfolio relative to market position and growth. Uses BCG Matrix and SWOT mentally or in slides. |
| **Emotions** | Strategic but isolated (neutral). The portfolio view is valuable but disconnected from what teams are actually building. |
| **Pains** | "My BCG Matrix is a static slide — it doesn't update when initiatives ship." "No link between portfolio position and which shaping items get prioritised." "SWOT lives in planning decks, not in the committed tree — teams building the product can't access it." |
| **Opportunities** | Committed portfolio-position artifact that updates alongside the initiative structure; SWOT linked to shaping queue prioritisation so strategic position drives what gets shaped next. |

> **With M4** — BCG Matrix + SWOT skills ship: portfolio-position.md committed; links to `[shaping_queue]` backlog priority (higher portfolio urgency → moves higher in backlog).

---

## Stage 3: Direction Setting (PRFAQ)

### Now

| Row | Content |
|-----|---------|
| **Actions** | Writes a press release or product narrative for major bets in slide decks or documents. Shares in leadership reviews. Rarely committed to the repo. |
| **Emotions** | Purposeful but aware of the gap (positive → neutral). The PRFAQ discipline is valuable but exists only in meetings — it doesn't anchor the shaping room. |
| **Pains** | "I write a great press release in PowerPoint and then it disappears. Six months later no one knows what the original vision was." "The shaping room has no altitude-0 anchor — PEs shape without knowing what the company is trying to achieve." "PRFAQ is an Amazon thing — no structured tool for it here." |
| **Opportunities** | PRFAQ template committed to `docs/product/shaping/` as the altitude-0 forcing function; linked from initiative briefs as the "why this initiative?" artifact; any agent or reviewer can trace a brief back to the PRFAQ that motivated it. |

> **With M4** — PRFAQ template ships: strategist writes press release, commits it to `docs/product/shaping/`; initiative briefs link to PRFAQ via `## Design artifacts`; traceability lint can enforce the link.

---

## Stage 4: OKR Cascade

### Now

| Row | Content |
|-----|---------|
| **Actions** | Sets company OKRs in Notion / Google Sheets. Cascades to team OKRs in planning meetings. Hopes the cascade reaches the product team's shaping backlog. Rarely does. |
| **Emotions** | Resigned (negative). The cascade is a planning ritual, not a live connection. By the time an engineer writes a spec, the OKR that motivated it is invisible. |
| **Pains** | "Company OKRs are in Notion; team OKRs are in a spreadsheet; the shaping queue has no idea either exists." "Gaps between current state and OKR targets are identified in planning meetings and then lost." "No mechanism for OKR gaps to flow into `frame-situation` as shaping inputs." |
| **Opportunities** | OKR cascade skill that (a) takes company OKRs, derives team-level OKRs, and identifies gaps; (b) routes each gap as a `shape`-typed shaping item into `frame-situation`; (c) writes the cascade as a committed artifact. The altitude-0 → altitude-1 handoff becomes a skill invocation, not a meeting. |

> **With M4** — OKR cascade skill ships: company OKRs → gap analysis → `frame-situation` routing; gaps added to `[shaping_queue].backlog` as typed items; product engineer picks them up via `check-workspace`. Cross-pack dependency: PE pack (frame-situation, M2) must be installed.

---

## Stage 5: Initiative Prioritisation

### Now

| Row | Content |
|-----|---------|
| **Actions** | Decides which initiatives get resourced in the planning cycle. Decision is made in meetings with no committed rationale. |
| **Emotions** | Confident in the room (positive) but aware the rationale will be lost (neutral). Six months later the team doesn't know why initiative X was picked over initiative Y. |
| **Pains** | "Initiative prioritisation is a meeting outcome — it's not committed anywhere." "No structured betting table at altitude-0 — I can't show stakeholders the trade-offs I considered." "The shaping queue doesn't reflect strategic priority — PEs pick whatever is interesting, not whatever is most urgent." |
| **Opportunities** | Portfolio-level bet committed to `docs/product/shaping/`; shaping queue backlog ordered by strategic priority; stakeholders can see the trade-offs the strategist weighed. |

> **With M4** — Portfolio bet artifact ships alongside OKR cascade; `[shaping_queue].backlog` ordering reflects strategic priority; altitude-0 rationale is committed and traceable.

---

## Frontstage actions

- **Skill:** run-pestle-analysis
- **Skill:** run-porters-five-forces
- **Skill:** run-bcg-matrix
- **Skill:** run-swot
- **Skill:** write-prfaq
- **Skill:** run-okr-cascade
- **Skill:** prioritise-initiative-portfolio

---

## Emotional arc

Lowest point: **Stage 4 (OKR Cascade)** — resigned — because the altitude-0 → altitude-1 handoff is a ritual that does not produce a committed artifact or a live connection to the shaping queue. OKR gaps identified in planning disappear before they reach a product engineer's workspace.

Highest-opportunity pain: "I set company OKRs and cascade them to team OKRs. By the time an engineer is writing a spec, neither exists in their context. There is no committed handoff — just hope."

Primary design response: OKR cascade skill routing gaps to `[shaping_queue]` as `shape`-typed items; PRFAQ and portfolio-position committed to `docs/product/shaping/` as traceable altitude-0 anchors.

---

## Handoff notes

**For `map-screen-flow`:** Stage 4 (OKR Cascade) and Stage 5 (Initiative Prioritisation) carry the highest-opportunity pains. A portfolio-level dashboard showing which initiatives are resourced and why — with links to the committed altitude-0 artifacts — is the highest-priority screen-level input for INI-006 (control plane).

**For `blueprint-service`:** backstage services include `docs/product/shaping/` (altitude-0 artifact store), `workspace.toml` (shaping queue state), PE pack's `frame-situation` (cross-pack routing target). The cross-pack dependency (OKR cascade → frame-situation) is the primary integration point and requires agent-mediated invocation — not a mechanical cross-pack call.
