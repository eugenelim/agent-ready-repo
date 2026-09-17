# product-strategy

Answer the committed strategic questions upstream of every product initiative.

---

## Start here

You don't need to know which method to use. Start with the question you're trying to answer.

> "Who should we serve first?"  
> "Which problem should we commit to?"  
> "Why would users switch to this?"  
> "How will they reach first value?"  
> "What retained behavior would prove the strategy is working?"  
> "What would cause us to change course?"

Type the question, or describe the product concept — the pack selects the method.

```text
Who should we serve first — enterprise teams or individual practitioners?
```

```text
write-prfaq

  Headline:  [Company] ships workspace.toml — product engineers who
             coordinate AI agent work across sessions.

  Customer:  A solo engineer shipping a 3-person startup's backlog
             with AI coding agents.
  Problem:   Every session starts blind. The agent doesn't know
             what was decided, what's blocked, or what ships next.
  Solution:  workspace.toml — a version-controlled queue the agent
             reads at session start. One grep, full context.

  Approve the PRFAQ? ›
```

The result is a committed artifact in `docs/product/shaping/` — a PRFAQ, a situation picture, a portfolio position, a cascaded OKR set, or a strategic narrative. Not a slide. A record the next stage can act on.

---

## Common jobs

**Pressure-test a product concept before building it**
Say `write-prfaq` and describe the product idea, problem, or elevator pitch.
Returns a press-release-and-FAQ document that forces an honest answer to "who is this for, what's the headline, and what's the FAQ critique?" Approve the PRFAQ or revise it. Written to `docs/product/shaping/`.

**Map the strategic situation before committing to an approach**
Say `run-swot` (or `run-pestle-analysis`, `run-porters-five-forces`). Describe the scope — organization, market, or product.
Returns a committed situation picture (quadrant map, five-force diagram, or PESTLE scan) as the foundation for the PRFAQ. Only reads information you provide; nothing is written until you approve.

**Position a product portfolio**
Say `run-bcg-matrix` and provide a list of initiatives with their relative market position.
Returns a portfolio matrix placing each initiative in a quadrant — Stars, Cash Cows, Question Marks, Dogs — with a disposition recommendation per initiative. You decide whether to act on the recommendation.

**Cascade strategy to the engineering queue**
Say `run-okr-cascade` and provide company OKRs (as text, a doc, or described inline).
Returns team-level OKRs and exposes the gaps — initiatives or KRs that no team owns. The gaps are written as `{type = "strategy"}` entries to `workspace.toml`, where `product-engineering`'s `frame-situation` picks them up.

**Synthesize research into a strategic narrative**
Say `synthesize-stakeholder-research` and attach one or more completed `desk-research-project-synthesize` briefs.
Returns a committed strategic narrative organized by theme — direct evidence converted to a record the PRFAQ or initiative brief can cite.

---

## How it works

```text
run-swot

  Quadrant       Items
  ─────────────  ──────────────────────────────────────────────────
  Strengths      Developer-first positioning; fast iteration cycle
  Weaknesses     Low brand awareness outside early-adopter segment
  Opportunities  AI-native distribution; enterprise channel open
  Threats        Funded competitor entering adjacent market

  Approve the situation picture? ›
```

```text
write-prfaq

  ...

  Approve the PRFAQ? ›
```

```text
run-okr-cascade

  Gap slug              KR                        Priority
  ──────────────────    ──────────────────────    ──────────
  retention-cohort      Retain 60% at week 4      High
  activation-depth      3 features in 14 days     High
  channel-enterprise    ARR from enterprise        Medium

  3 gaps → workspace.toml  [ini-001.shaping_queue].backlog
```

The gaps appear in `workspace-status` for product engineers to pick up via `frame-situation`.

---

## Installation and trust

- **Scope:** user — installs portably across all your repos
- **Reads:** information you provide in the conversation; prior strategy artifacts you reference
- **Local writes:** approved artifacts to `docs/product/shaping/` inside your current repo
- **Remote reads/writes:** none
- **Approval:** every artifact is approved before being written; the pack proposes, you commit
- **No growth or marketing execution tooling** — see `[backlog].open: growth-strategy-pack` for scope rationale

```bash
agentbundle install --pack product-strategy --scope user
```

---

## Skills included — under the hood

| Skill | Method | When to reach for it |
|-------|--------|----------------------|
| `write-prfaq` | Amazon-style press release + FAQ | Pressure-testing a new product concept |
| `run-swot` | SWOT synthesis (optionally from prior PESTLE / Porter's / BCG) | Situation picture before committing to direction |
| `run-pestle-analysis` | PESTLE scan | Macro-environment scan for market entry or product line |
| `run-porters-five-forces` | Porter's Five Forces | Competitive landscape map |
| `run-bcg-matrix` | BCG Matrix | Portfolio positioning across multiple initiatives |
| `run-okr-cascade` | OKR cascade | Cascading company OKRs to team level; exposing gaps |
| `synthesize-stakeholder-research` | Research synthesis | Converting desk-research output into strategic narrative |
| `define-ux-strategy` | Experience vision + goals/measures + plan | Upstream anchor for `journey-mapping` and `content-design` |
| `define-content-strategy` | Purpose · Process · Structure · Governance (this pack's composite) | Governance layer for content above per-surface design |

---

## Where these methods come from

Framework names are the procedure; the following is provenance only — who published what, and where this pack's version differs.

- **`define-ux-strategy`** — Jaime Levy's fourth tenet is named **frictionless UX** in the 2021 second edition of *UX Strategy*, and **killer UX design** in the 2015 first edition. This pack follows the 2021 second edition. See [UX Strategy, 2nd edition, ch. 2](https://www.oreilly.com/library/view/ux-strategy-2nd/9781492052425/ch02.xhtml).
- **`define-content-strategy`** — the skill's Purpose + Process + Structure + Governance is this pack's own composite. It matches neither published content-strategy quad: Kristina Halvorson and Melissa Rach's 2012 quad is Substance / Structure / Workflow / Governance, and Brain Traffic's 2018 revision is Editorial Strategy / Experience Design / Content Structure / Process Design. See [Brain Traffic's new content strategy quad](https://www.braintraffic.com/blog/new-thinking-brain-traffics-content-strategy-quad).
- **`write-prfaq`** — the PRFAQ (press release + FAQ) format is Amazon's internal product-development practice, documented in Colin Bryar and Bill Carr's *Working Backwards* (2021). See [Amazon's Working Backwards PR-FAQ](https://workingbackwards.com/resources/working-backwards-pr-faq/).

The remaining six skills (`run-swot`, `run-pestle-analysis`, `run-porters-five-forces`, `run-bcg-matrix`, `run-okr-cascade`, `synthesize-stakeholder-research`) name their framework directly in the procedure — the name itself is the instruction, not a separable citation.

---

## Cross-pack handoffs

**→ `product-engineering`:** `run-okr-cascade` writes `{type = "strategy"}` gap entries to `workspace.toml`. The PE pack's `frame-situation` reads them from the shaping queue.

**→ `experience-design`:** `define-ux-strategy` produces `ux-strategy.md` and `define-content-strategy` produces `content-strategy.md`. Both anchor `journey-mapping` and `content-design`.

---

## Go deeper

→ [Product Strategy guides](../../guides/product-strategy/)
→ [JOURNEY.md](JOURNEY.md) — the three-artifact strategy workflow from situation → decision → queue
