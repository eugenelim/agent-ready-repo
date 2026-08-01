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

1. **Named maintainer** — ask the operator for a team name or role alias
   (e.g., `platform-team`, `db-working-group`) to identify the maintainer.
   Do NOT ask for a personal account handle — committing a real username to
   `pack.toml` violates the privacy rules (AGENTS.md §Privacy, which prohibits
   real usernames in any committed file). If the operator supplies a personal
   handle, surface the conflict and ask for a role alias instead. Required in
   `pack.toml`'s `[[pack.maintainers]]` field before any scaffold is written.
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

> **QA session scope.** The AC6 QA session verifies that the skill produces
> the correct scaffold structure and shape — it does NOT commit the new pack
> to the repository. After verifying scaffold shape, the operator discards the
> output. Before opening a real PR for a new pack, the operator must expand
> the eval harness to ~8–10 trigger and ~8–10 near-miss entries and add the
> `[pack.evals]` block — `packs/AGENTS.md:112-115` requires a complete harness
> for any non-cosmetic pack update. The scaffold stubs are a starting point,
> not a production-ready deliverable.

The skill scaffolds the pack shell at `packs/database-tooling/` via
`agentbundle.safety.write_jailed`. Expected files created:

```
packs/database-tooling/
  pack.toml               # Required tables (per pack-shell.md:7-16):
                          #   [pack] name, version, description
                          #   [pack.adapter-contract] version
                          #   [pack.install] default-scope, allowed-scopes
                          #   [[pack.dependencies.required]] (only if this pack
                          #     composes around core; standalone packs omit this)
                          #   [pack.links]
                          #   [[pack.maintainers]]
                          # ([pack.evals] added later, once eval harness reaches coverage)
  README.md               # elevator pitch + link to pack's guide home + install command
  .claude-plugin/
    plugin.json           # name, version, description (only — schema is closed)
  .apm/                    # empty — propose-catalogue-pack scaffolds the shell only;
                           # skills are added later via assimilation
```

There is no pack-root `evals/` directory. Eval discovery is always per-skill.
The scaffold does not create any skill stubs, eval files, or agent definitions —
`propose-catalogue-pack/SKILL.md:33-36` is explicit: "empty `.apm/`". Primitives
are added in a subsequent assimilation pass, not at propose time.
`pack_evals.py` supports three mutually exclusive `--mode` invocations:
- `--mode headless` (default): Tier-A activation — reads each listed skill's
  `eval_queries.json` and measures whether the skill fires on trigger queries.
- `--mode judge --artifacts ...`: LLM-judge grading — reads `evals.json` and
  grades output quality against the rubric assertions.
- `--mode in-harness --check activation` (default `--check`): Tier-A, reads `eval_queries.json` from pre-collected run results.
- `--mode in-harness --check behavior`: Tier-B-lite output check — reads `evals.json`.
Each mode is a separate CLI invocation; running `headless` does not execute the
judge or behavior passes. A root-level `evals/` directory is not read by any
known tool.

Notes on the scaffold:
- `plugin.json` contains only `name`, `version`, and `description` — the schema
  (`contracts/plugin-manifest.schema.json`) is closed (`additionalProperties: false`)
  and does not support tool grants or other custom fields.
- `.apm/` is empty in the scaffold — `propose-catalogue-pack/SKILL.md:33-36`
  explicitly says "empty `.apm/`". No skill stubs, agent definitions, or eval
  files are created at propose time.
- `pack-shell.md:15-16` states "at least one primitive, or the pack won't
  validate." **The actual tooling does not enforce this at lint time.**
  `agentbundle catalogue lint --deep` succeeds immediately after scaffold
  creation on a metadata-valid pack with an empty `.apm/` — no primitives
  required. `agentbundle catalogue verify` requires `FORCE=1 make build-self`
  first (in a self-hosting checkout): verify step 15 checks self-host drift,
  and adding the new pack directory makes `marketplace.json` stale until
  `build-self` regenerates it. `pack-shell.md:15-16` describes an aspirational
  constraint, not one enforced by the current linter. The operator adds
  primitives in a subsequent `assimilate-primitive` or `assimilate-repo` pass.
  Eval harness requirements (`packs/AGENTS.md:110-115`) apply once primitives
  are assimilated, not at scaffold time.

**AC6 pass condition:** The QA session verifies that the skill (a) tests
additivity + fit and reports the result, (b) creates the correct empty scaffold
structure when the pack passes fit, and (c) emits an RFC. Post-scaffold:
- `agentbundle catalogue lint --deep` passes on the empty scaffold.
- `agentbundle catalogue verify` must run **after** `FORCE=1 make build-self` —
  verify step 15 (`check_self_host`) checks self-host projection drift; the new
  pack directory immediately makes `marketplace.json` stale, so verify fails
  before `build-self` regenerates it. Run `FORCE=1 make build-self` first,
  then verify.
AC6 is satisfied when the scaffold structure and RFC match the forms documented
in this file and both post-build-self gates pass clean.

**AC6 teardown (required after QA):** The `database-tooling` scaffold is a
throwaway for QA verification. After confirming AC6 passes, the QA operator
must clean up before the checkout is used for other work:
1. Delete `packs/database-tooling/` and the emitted RFC file.
2. Run `FORCE=1 make build-self` to remove the stale `marketplace.json` entry
   (deleting the pack directory without rebuilding leaves a dangling entry that
   fails `agentbundle catalogue verify`).
3. Run `agentbundle catalogue verify` to confirm the clean state.

Alternatively, run AC6 in a disposable git worktree
(`git worktree add /tmp/qa-propose-pack`) and remove it after
(`git worktree remove --force /tmp/qa-propose-pack`) — no teardown needed.
- The maintainer alias from Step 2.5 is written into `pack.toml`'s
  `[[pack.maintainers]]` field; the maturity scope and deprecation path are
  documented in README.md.

---

## Expected: Step 4 — RFC output

The skill authors an RFC using the canonical template from
`packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md` as its base.

**Metadata layout:** The RFC template does NOT use YAML frontmatter. The metadata
is a **Markdown bullet-list block** placed directly below the H1 title:

```markdown
# RFC-NNNN: database-tooling pack

- **Status:** Draft
- **Author:** <account-handle>
- **Approver:** <account-handle>
- **Date opened:** YYYY-MM-DD
- **Date closed:**
- **Decision weight:** standard
- **Related:**
```

**Note on the `Author`/`Approver` placeholder**: the source RFC template
(`packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md`) uses
`<github-handle>`. The repo privacy rule (`AGENTS.md:217-221`) prohibits
vendor-specific identifiers in committed artifacts, so this answer key
substitutes the generic `<account-handle>`. This is template drift — the
source template should be updated to use `<account-handle>` but has not been
yet. The skill stops and asks if no project convention for governance authorship
is established.
Do not emit YAML delimiters (`---`) around this block — it is not YAML frontmatter.

**Required document sections** (in template order):
`Reviewer brief`, `The ask`, `Problem & goals`, `Proposal`, `Options considered`,
`Risks & what would make this wrong`, `Evidence & prior art`, `Open questions`,
`Follow-on artifacts`. These sections follow the metadata bullet block verbatim.

The RFC adds one additional section not in the base template:

```markdown
## Candidate primitive inventory

| Primitive | Type | Verdict | Notes |
|-----------|------|---------|-------|
| schema-migrate | skill | Assimilate | Core migration workflow |
| query-author   | skill | Assimilate | Recurring query authoring |
| db-inspect     | skill | Reject | Overlaps query-author; inspection is a query sub-operation, not a distinct habit |
```

This section is appended after the `Options considered` section and before the
`Risks & what would make this wrong` section. Everything else follows the canonical
new-rfc template structure verbatim.

---

## Reject case: non-additive proposal

**Proposed area:** "add a git-workflow pack for commit, branch, and PR operations."

Expected output:

> **Reject: fails Principle 3 (Habit, not a tool).** Git operations — committing,
> branching, opening PRs — are atomic tool invocations, not repeating workflow
> habits. The developer issues `git commit` or `example-scm-cli pr create` directly; there is
> no recurring sequence that forms a habit a skill should encode. A skill here
> would substitute a wrapper for a CLI, not capture a genuine pattern of repeated
> judgment.
>
> Failing principle: **Habit, not a tool.**

The skill must name the failing principle.
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
