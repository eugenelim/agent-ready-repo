# governance-extras

decisions committed, proposals structured, conventions tracked.

---

## Start here

Type `new-rfc` and describe the change you want to propose.

```text
new-rfc [adopt trunk-based development]

  identifier   RFC-0043
  title        Trunk-based development over feature branches
  status       Draft
  target       docs/rfc/0043-trunk-based-development.md

  Proposer     Reduces integration latency; CI catches regressions fast
  Objector     Long-lived branches give teams isolation; trunk conflicts are costly

Approve? ›
```

On any session return, type `rfc-status` to see where proposals stand.

```text
rfc-status

  Active:

  | State | RFCs                                       |
  |-------|--------------------------------------------|
  | Draft | RFC-0043: Trunk-based development          |
  | Open  | RFC-0042: Conventional commits adoption    |

  Resolved:

  | State    | Count |
  |----------|------:|
  | Accepted |    12 |
  | Rejected |     2 |

  RFC candidates: 3 entries
```

---

## Entry points

| Say this               | What happens                                            |
|------------------------|---------------------------------------------------------|
| `rfc-status`           | Orient — RFC landscape by status and findings count     |
| `new-rfc`              | Propose a cross-cutting change through a structured RFC |
| `new-adr`              | Record an architectural decision with critique tracks   |
| `update-conventions`   | Evolve CONVENTIONS.md through tracked RFC review        |

---

## How a session runs

```text
rfc-status

  Active:

  | State | RFCs                                       |
  |-------|--------------------------------------------|
  | Draft | RFC-0043: Trunk-based development          |

  Resolved:

  | State    | Count |
  |----------|------:|
  | Accepted |    12 |
  | Rejected |     2 |

  RFC candidates: 3 entries
```

```text
new-rfc [adopt trunk-based development]

  identifier   RFC-0043
  title        Trunk-based development over feature branches
  status       Draft
  target       docs/rfc/0043-trunk-based-development.md

  Proposer     Reduces integration latency; CI catches regressions fast
  Objector     Long-lived branches give teams isolation; trunk conflicts are costly

Approve? ›
```

```text
new-adr [primary store: Postgres over DynamoDB]

  identifier   ADR-0027
  title        Primary store: Postgres over DynamoDB
  status       Proposed
  target       docs/adr/0027-primary-store-postgres.md

  Decision     Use Postgres as the primary relational store
  Tradeoff     Operational overhead vs. DynamoDB's managed scaling

Approve? ›
```

The agent previews each draft before writing. Approve — RFC first, then ADR.

---

## Cross-pack

**Requires — `core`:** governance-extras layers on top of core. The RFC and ADR templates scaffold into `docs/` — the same directory core's `work-loop` reads for specs and specs' plans. Install `core` first or alongside.

**Downstream — `work-loop`:** When an RFC is accepted, a `work-loop` run implements it. The RFC's follow-on artifacts (specs, CONVENTIONS.md edits) become queue entries in `workspace.toml`.

**Downstream — `architect`:** ADRs record why the architecture is the way it is. The `architect` pack's `architect-design` skill reads `docs/adr/` as the settled-decisions context — it doesn't re-debate what the ADRs already closed.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the [`governance-extras` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/governance-extras/).
