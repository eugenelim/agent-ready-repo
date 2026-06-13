# Dogfood brief — enterprise brain (leading-edge domain)

> **Fixture for `well-architected-cloud` manual QA.** A design brief in a domain
> with **no shipped pillar/lens/provider reference** — it exists to exercise the
> leading-edge path. Referenced by path so the gesture is replayable.

## The brief

We want to build an **"enterprise brain"** — a continuously-updated, queryable
model of everything the company knows. It ingests documents, conversations,
tickets, and code; maintains **living ontologies** that evolve as the business
changes; tracks **provenance** (where each fact came from, how confident we are);
and serves both humans and agents that reason over it.

Open shape:

- Should the knowledge model be **one centralized ontology** or **federated**
  per-domain ontologies that reconcile at query time?
- How do we represent **memory** — episodic (what happened) vs. semantic (what's
  true) vs. procedural (how we do things)?
- How do we **govern** a model that changes itself — provenance, access, the
  right to be forgotten, drift?

Constraints: this is genuinely novel territory; the patterns aren't settled
practice yet. We need an architecture concept we can defend, with the
uncertainty named honestly.

---

## Expected observables (QA scaffolding — not part of the brief)

- `architect-design` recognizes **no shipped reference covers this domain** and
  takes the **leading-edge path** (`leading-edge-domains.md`): **flags the
  novelty** explicitly.
- **Composes with the `research` skill** (`applied` / `deep`) when it is
  installed to survey current grey literature; **degrades** to first-principles +
  flagged-novelty + **lowered confidence** when `research` is absent — never
  erroring or requiring it.
- **Synthesizes an ad-hoc enterprise-brain lens** for this engagement (memory
  types / knowledge stratums / provenance / governance) rather than forcing the
  brief into a cloud pillar reference.
- Surfaces the **centralized-vs-federated-ontology** decision as a **judgment
  finding** carrying **source + confidence** — never auto-resolved.
- Ships **no enterprise-brain content in the pack** — the lens is built per
  engagement, not from a committed reference.
