# Tradeoff & sensitivity points — name them, don't list pillars flat

The clearest quality win over a flat per-pillar checklist is naming where the
design's decisions *pull pillars against each other*. From ATAM (and echoed by
Azure WAF's explicit "Tradeoffs"); the ceremony is dropped, the two concepts
come across.

> Note: this reference is intentionally duplicated into `architect-review`'s
> `references/tradeoffs-and-sensitivity.md`. Skill autonomy beats DRY at this
> scale — each skill stands alone. See the pack README.

## The two concepts

- **Sensitivity point** — a decision where a *small change swings one quality
  attribute a lot*. (Cache TTL swings staleness; replica count swings recovery
  time; thread-pool size swings tail latency.) It's a knob the design is
  sensitive to — worth calling out so it isn't tuned blind.
- **Tradeoff point** — a decision that is a sensitivity point for *two or more
  pillars pulling opposite ways*. The decision can't optimize both; choosing is
  the architecture.
  - Cache TTL: performance ↑ / consistency ↓.
  - Multi-AZ / multi-region: reliability ↑ / cost ↑.
  - Synchronous replication: durability ↑ / write latency ↑.
  - Self-host inference vs. external LLM API: control + data-residency ↑ /
    operational burden + capability lag (cost, undifferentiated heavy lifting).

## What each side of the loop does with them

- **Design-time** — when you make a call at a tradeoff point, *name the tradeoff
  and which way you resolved it, and why*. A design doc that silently picks one
  side of a tradeoff hides the most important decision in it. Surface at least
  one explicit tradeoff, and a sensitivity point where one exists.
- **Review-time** — flag an **undocumented** tradeoff (the design picked a side
  without saying it traded the other pillar away) and any sensitivity point left
  un-named.

## A tradeoff is a judgment call, never a mechanical fix

Resolving a tradeoff point requires choosing between defensible options — that
is the definition of a **judgment** finding. The convergence loop must
**surface** a tradeoff to the human as a decision; it must never auto-resolve one
by silently picking a side. A *missing label* on an already-decided tradeoff is
mechanical (add the sentence naming it); *which way to decide* is judgment.

## Use, don't recite

Name the one or two tradeoffs that actually shape this design. A list of generic
tradeoffs the design doesn't make is padding.
