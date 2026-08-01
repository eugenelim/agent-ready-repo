# Expected behavior: propose-catalogue-pack

Documents the expected flow for AC6. The live QA session runs
`propose-catalogue-pack` with a real or sample pack proposal.

Source authority:
`packs/catalogue-curation/.apm/skills/propose-catalogue-pack/SKILL.md`
`packs/catalogue-curation/.apm/skills/propose-catalogue-pack/references/pack-shell.md`

---

## Sample pack proposal input

**Proposed area:** a `database-tooling` pack covering schema migration workflows,
query authoring, and data inspection for SQL databases ([relational-db-A],
[relational-db-B]).

**Operator prompt:** "Should we add a database-tooling pack for schema migration
and query workflows?"

---

## Expected: Step 1 — additivity + fit test

The skill reads `docs/CHARTER.md`. `database-tooling` (SQL-specific: schema
migration, query authoring for a relational database stack) is tech-stack-specific
by design — this makes it a **tech-stack accelerator pack** under the charter
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
| Dependencies | Depends on whether proposed skills compose with core workflows. If `schema-migrate` or `query-author` surfaces output that feeds into `work-loop` or other core skills, declare a `core` dependency in `pack.toml`. If the skills stand alone, no `core` dependency is needed. Do not cite `agentbundle.safety.write_jailed` — that is used by the scaffold step of `propose-catalogue-pack` itself, not a runtime dependency of `database-tooling`. |
| Out of scope | ORM configuration (project-specific); DBA capacity planning; NoSQL databases (distinct enough to warrant a separate pack) |
| Out-of-scope blocker | None identified — the pack can stand independently |

---

## Expected: Step 2.5 — accelerator gate collection (before scaffold)

Before proceeding to Step 3, the skill must collect the three accelerator-pack
gates that CHARTER.md:49-56 requires:

1. **Named maintainer** — ask the operator for the GitHub handle or team name
   that will maintain this pack. Required in `pack.toml`'s
   `[[pack.maintainers]]` field before any scaffold is written.
2. **Maturity scope** — ask the operator to declare one of:
   `experimental` / `contract-complete` / `validated`.
3. **Archiving/deprecation path** — ask the operator to state what happens
   when the pack is no longer maintained (e.g., "archived to a separate repo",
   "deprecated with a tombstone in README", "handed off to community").

Only after all three are supplied does the skill proceed to Step 3 (scaffold).
If the operator cannot supply them now, the skill stops and surfaces: "These
three gates are required by the catalogue charter before scaffolding an
accelerator pack. Please supply them and re-run."

---

## Expected: Step 3 — scaffold output (on pass, after accelerator gates cleared)

The skill scaffolds the pack shell at `packs/database-tooling/` via
`agentbundle.safety.write_jailed`. Expected files created:

```
packs/database-tooling/
  pack.toml               # name, version, description, dependencies,
                          # [[pack.maintainers]], maturity scope, [pack.evals]
  README.md               # one-paragraph overview + install command
  .claude-plugin/
    plugin.json           # name, version, description (only — schema is closed)
  .apm/
    skills/
      schema-migrate/
        SKILL.md          # stub: name + description stub only; body TBD via assimilation
        evals/
          eval_queries.json  # Tier-A activation evals (8–10 trigger + 8–10 near-miss stubs)
  evals/
    eval_queries.json     # pack-level Tier-A activation index (references skill evals)
    evals.json            # Tier-4 LLM-judge rubric stubs for judgment/authoring skills
```

Notes on the scaffold:
- `plugin.json` contains only `name`, `version`, and `description` — the schema
  (`contracts/plugin-manifest.schema.json`) is closed (`additionalProperties: false`)
  and does not support tool grants or other custom fields.
- `.apm/skills/schema-migrate/SKILL.md` is a minimal stub (frontmatter + one-line
  body). `pack-shell.md:15-16` requires at least one skill or agent; an empty
  `.apm/` fails pack validation. The stub is the minimum; the operator populates
  it via `assimilate-primitive` or `assimilate-repo` later.
- **Eval harness is required** (`packs/AGENTS.md:110-115`): a non-cosmetic pack
  update (and new-pack scaffold) must include:
  - Tier-A activation evals — `evals/eval_queries.json` (~8–10 should-trigger +
    ~8–10 near-miss entries per user-triggered skill) and a `[pack.evals]` block
    in `pack.toml` listing every user-triggered skill (`schema-migrate`,
    `query-author`, etc.).
  - Tier-4 LLM-judge rubric — `evals/evals.json` for judgment/authoring skills.
  The scaffold produces stub eval files (empty JSON arrays with a TODO comment);
  the operator populates them before shipping the pack.
- The maintainer handle from Step 2.5 is written into `pack.toml`'s
  `[[pack.maintainers]]` field; the maturity scope and deprecation path are
  documented in README.md.

---

## Expected: Step 4 — RFC output

The skill authors an RFC using the canonical template from
`packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md` as its base —
filling in all required sections. The template's required content sections are:
`Reviewer brief`, `The ask`, `Problem & goals`, `Proposal`, `Options considered`,
`Risks & what would make this wrong`, `Evidence & prior art`, `Open questions`,
`Follow-on artifacts`. The metadata fields (Status, Author, Approver, Date opened)
are frontmatter — not document sections but still required.

The `Author` field uses the canonical `<github-handle>` placeholder; the skill
stops and asks if no project convention for governance authorship is established.

The RFC adds one additional section not in the base template:

```markdown
## Candidate primitive inventory

| Primitive | Type | Verdict | Notes |
|-----------|------|---------|-------|
| schema-migrate | skill | Assimilate | Core migration workflow |
| query-author   | skill | Assimilate | Recurring query authoring |
| db-inspect     | skill | Needs assessment | Scope TBD — inspect vs. query overlap |
```

This section is appended after the `Options considered` section and before the
`Risks & what would make this wrong` section. Everything else follows the canonical
new-rfc template structure verbatim.

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
