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

  Active: RFC-0043 (Draft) · RFC-0042 (Open)
  Resolved: 14  ·  Candidates: 3
```

---

## RFCs and ADRs

**RFC (Request for Comments)** — a structured proposal for any cross-cutting change: a new convention, an architectural direction, a team process. An RFC is not a decision; it's the case for a decision. It carries a proposer perspective (why this is worth doing) and a genuine objector perspective (the strongest case against it). You can seed `new-rfc` with context — pass a desk-research brief, an architect design doc, or any prior analysis and the skill folds them in as the factual grounding instead of inventing the case from scratch. Accepted RFCs can be amended with a signed cover note (erratum) — a compact correction that does not reopen the full RFC cycle.

`rfc-status` reads the full `docs/rfc/` landscape: active RFCs by lifecycle state (Draft / Open / Accepted / Rejected / Deferred), resolved counts, and any unproposed findings sitting in the candidate register waiting to become RFCs.

**ADR (Architecture Decision Record)** — the record of a decision already made. It captures the decision, the alternatives that were considered and why they were rejected, and the consequences. ADRs are immutable once merged; when a decision is reversed, the original ADR is superseded, not deleted. `new-adr` resolves the repository's portable `decision-record` destination before choosing an ordinal or index, so adopter policy and established custom/external locations win; `docs/adr/` is only the catalogue fallback. Its existing critique, preview, and confirmation method then runs inside that destination. If an RFC preceded the decision, the ADR links back to it.

When core's `project-knowledge` skill is installed, `new-rfc` may capture reusable supporting practice only after every mandatory check is clean and the RFC file and index entry have been written. `new-adr` may do the same only when the decision-maker actually changes the ADR from Proposed to Accepted. Drafts, previews, abandoned work, and normative proposal or decision content are never captured. Missing project knowledge is a named skip with no fallback file; any distillation is limited to receipts returned by that same authoring gate.

---

## Entry points

| Say this               | What happens                                            |
|------------------------|---------------------------------------------------------|
| `rfc-status`           | Orient — RFC landscape by status and findings count     |
| `new-rfc`              | Propose a cross-cutting change through a structured RFC |
| `new-adr`              | Record an architectural decision with critique tracks   |

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

**Requires — `core`:** governance-extras layers on top of core. `new-adr` consumes Core's `semantic-surface-resolution.v1` for repository decision-record destinations; RFC behavior remains independently governed. Install `core` first or alongside. If an older/incompatible Core cannot provide the contract, ADR authoring stops for destination confirmation or returns a portable handoff instead of simulating resolution.

**Optional handoff — `project-knowledge`:** At the `rfc-handoff-ready` and `adr-accepted` gates, the producer can submit the public typed captured-observation request through core's progressive skill. The authoring skill owns transient scratch and timing; it never accesses private journals, persists scratch automatically, or creates alternate storage.

**Downstream — `work-loop`:** When an RFC is accepted, a `work-loop` run implements it. The RFC's follow-on artifacts (specs, CONVENTIONS.md edits) become queue entries in `workspace.toml`.

**Downstream — `architect`:** ADRs record why the architecture is the way it is. Architect consumes the resolved `decision-record` surface as settled-decision context; it does not assume `docs/adr/` or re-debate what the ADRs already closed.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the [`governance-extras` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/governance-extras/).
