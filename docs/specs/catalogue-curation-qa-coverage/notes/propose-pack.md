# Expected behavior: propose-catalogue-pack

Documents the expected flow for AC6. The live QA session runs
`propose-catalogue-pack` with a real or sample pack proposal.

Source authority:
`packs/catalogue-curation/.apm/skills/propose-catalogue-pack/SKILL.md`
`packs/catalogue-curation/.apm/skills/propose-catalogue-pack/references/pack-shell.md`

---

## Sample pack proposal input

**Proposed area:** a `database-tooling` pack covering schema migration workflows,
query authoring, and data inspection for SQL databases (PostgreSQL, SQLite).

**Operator prompt:** "Should we add a database-tooling pack for schema migration
and query workflows?"

---

## Expected: Step 1 — additivity + fit test

The skill reads `docs/CHARTER.md`. `database-tooling` (SQL-specific: schema
migration, query authoring for PostgreSQL/SQLite) is tech-stack-specific by
design — this makes it a **tech-stack accelerator pack** under the charter
(CHARTER.md §"What this project does").

**Accelerator-pack routing:** The charter explicitly exempts accelerator packs
from principle 1 ("Universal"). They clear the **remaining three principles
instead**, plus three additional accelerator gates.

For `database-tooling`, expected analysis:

| Check | Assessment | Notes |
|-------|-----------|-------|
| Accelerator-pack classification | **Yes** | SQL-database-specific; serves adopters who have already chosen a relational DB stack. |
| Principle 1 (Universal) | **Exempt** | Accelerator packs are tech-stack-specific by design; principle 1 does not apply. |
| Principle 2 (Substantive, not duplicative) | **Pass** | No existing pack covers schema migration or query authoring. `iac-terraform` is infrastructure-layer; no overlap. |
| Principle 3 (Habit, not a tool) | **Pass** | Schema migration is a repeating workflow (every schema change); query authoring recurs throughout development. |
| Principle 4 (Used often enough to stick) | **Pass** | Any project with a relational DB touches migrations repeatedly. |
| Named maintainer | **Required — must be supplied** | Accelerator gate: a named maintainer must be identified before the pack is approved. |
| Maturity scope | **Required — must be supplied** | Accelerator gate: one of `experimental / contract-complete / validated` (CHARTER.md:53–54). |
| Archiving/deprecation path | **Required — must be supplied** | Accelerator gate: the pack must declare what happens when it is no longer maintained. |

Expected skill output:

> **Accelerator-pack classification: tech-stack-specific (SQL databases).**
> Exempt from principle 1 (Universal); clears principles 2, 3, and 4 instead —
> all three pass. Three additional accelerator gates are required before
> approval: a named maintainer, a stated maturity scope (experimental /
> contract-complete / validated), and an archiving/deprecation path. Please
> supply these before the RFC is finalised.

---

## Expected: Step 2 — boundary diagnosis

| Field | Expected output |
|-------|----------------|
| Primitives | At minimum: `schema-migrate` skill, `query-author` skill, possibly a `db-inspect` skill |
| Dependencies | `core` (write path uses `agentbundle.safety.write_jailed`); no dependency on other non-core packs |
| Out of scope | ORM configuration (project-specific); DBA capacity planning; NoSQL databases (distinct enough to warrant a separate pack) |
| Out-of-scope blocker | None identified — the pack can stand independently |

---

## Expected: Step 3 — scaffold output (on pass)

The skill scaffolds the pack shell at `packs/database-tooling/` via
`agentbundle.safety.write_jailed`. Expected files created:

```
packs/database-tooling/
  pack.toml               # name, version, description, dependencies
  README.md               # one-paragraph overview + install command
  .claude-plugin/
    plugin.json           # display name, description, tool grants
  .apm/                   # empty; skills added when assimilated
```

The skill should **not** populate `.apm/` with skills — that is assimilation
work (`assimilate-primitive` / `assimilate-repo`), not scaffolding work.

---

## Expected: Step 4 — RFC output

The skill authors an RFC (next available number in `docs/rfc/`) with:

```
# RFC-NNNN: database-tooling pack

Status: Draft
Author: [operator name from git config]

## Proposal
Add a `database-tooling` pack covering schema migration and query authoring
for SQL databases.

## Additivity + fit assessment
[Four-principle table as above]

## Candidate primitive inventory
| Primitive | Type | Verdict | Notes |
|-----------|------|---------|-------|
| schema-migrate | skill | Assimilate | Core migration workflow |
| query-author | skill | Assimilate | Recurring query authoring |
| db-inspect | skill | Needs assessment | Scope TBD — inspect vs. query overlap |

## Out of scope
- ORM configuration
- NoSQL databases
- DBA capacity planning

## Decision
Pending operator approval.
```

---

## Reject case: non-additive proposal

**Proposed area:** "add a git-workflow pack for commit, branch, and PR operations."

Expected output:

> **Reject: duplicative.** Git workflow operations (commit, branch, PR) are
> covered by the `core` pack's `bug-fix`, `capture-work`, and `work-loop`
> skills, and by `github`'s `github-brief-intake`. A `git-workflow` pack would
> duplicate their activation surface without adding distinct capability.
>
> Failing principle: **Substantive, not duplicative.**

The skill must name the failing principle and cite the colliding pack(s).
No scaffold is produced on a reject.

---

## Non-auto-invocation boundary

The skill must **not** be auto-invoked from `assimilate-repo`. If a candidate
in an `assimilate-repo` survey receives a `needs-new-pack` verdict, the skill
surfaces the offer:

> "This candidate may warrant a new pack. Run `propose-catalogue-pack` to
> assess additivity and scaffold."

It does not trigger `propose-catalogue-pack` automatically. (This is the
existing Never-do from the parent spec; this note confirms the QA session
should verify that boundary is respected during the AC6 session.)
