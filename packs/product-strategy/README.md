# product-strategy

The strategy seat upstream of every initiative — committed artifacts.

---

## Start here

Type `write-prfaq` and describe the product concept you want to pressure-test.

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

  draft  docs/product/shaping/prfaq.md
```

On any session return, ask the agent what's in `docs/product/shaping/` — or continue directly with `run-swot`.

---

## Entry points

| Say this | Give it | What happens |
|----------|---------|--------------|
| `write-prfaq` | A product concept, elevator pitch, or problem statement | Drafts the press release + FAQ before the product exists — the altitude-0 forcing function |
| `run-pestle-analysis` | The scope: organization, market entry, or product line | Scans the macro environment across six lenses — Political, Economic, Social, Technological, Legal, Environmental |
| `run-porters-five-forces` | The industry and the competitive reference point | Maps the competitive landscape — supplier and buyer power, new entrants, substitutes, rivalry |
| `run-bcg-matrix` | A list of initiatives or products with their relative market position | Positions each in the portfolio matrix — Stars, Cash Cows, Question Marks, Dogs |
| `run-swot` | Scope alone (elicits inline), or prior PESTLE / Porter's / BCG artifacts | Synthesizes the situation picture — Strengths, Weaknesses, Opportunities, Threats |
| `run-okr-cascade` | Company OKRs (text, doc, or described inline) | Cascades to team level, identifies gaps, and routes them to the PE shaping queue in `workspace.toml` |
| `synthesize-stakeholder-research` | One or more `desk-research-project-synthesize` briefs | Converts research evidence into a committed strategic narrative by theme |
| `define-ux-strategy` | The approved PRFAQ and market situation (optional but improves grounding) | Sets the experience vision, goals with measures, and plan — upstream of `journey-mapping` |
| `define-content-strategy` | Organizational context and any prior strategy artifacts | Sets the governance layer for content — Purpose, Process, Structure, Governance — upstream of `content-design` |

---

## How a session runs

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

## Cross-pack

**Downstream — `product-engineering`:** `run-okr-cascade` writes `{type = "strategy"}` gap entries to `workspace.toml`. The PE pack's `frame-situation` reads them from the shaping queue.

**Downstream — `experience-design`:** `define-ux-strategy` produces `ux-strategy.md` and `define-content-strategy` produces `content-strategy.md`. Both are strategic anchors the experience-design pack's `journey-mapping` and `content-design` read from.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, pillars, invariants, and decision log.  
→ **Go deeper:** the [`product-strategy` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/product-strategy/).
