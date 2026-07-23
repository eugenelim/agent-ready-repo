# Catalogue operator journey

How the three operator sub-personas — org-stack engineer, catalogue maintainer, and catalogue author — use the curation pack at their operating altitude.

## First install and orientation

If you have not yet installed the pack, run `agentbundle install --pack catalogue-curation --scope repo`.
The pack requires core and governance-extras at repo scope.
After install, run `agentbundle show catalogue-curation` to confirm all four skills are present with their activation phrases.

The pack is off every default profile by design: it is for people who build catalogues, not for people who use them.
If you are installing skills from a catalogue, you do not need this pack.

This guide picks up after first install.
It explains how each sub-persona fits into the system, what their primary touchpoints are, and where to go next.

Before diving into the personas, read [Skill standards](skill-standards.md) — it names the three standards every skill is measured against and gives the reading order for the full guide set.
Both paths covered here (writing a new skill, assimilating an existing one) are governed by those same standards.

---

## Org-stack engineer

An org-stack engineer maintains an org's own pack — a fork of `core`, an org-specific skill set, or a domain pack for the team's tools.
They have found one external skill or subagent they want in their kit: a utility, a review agent, a domain-specific search skill.

### Single-primitive intake

The org-stack engineer's path skips the survey and RFC.
They run `assimilate-primitive` directly, pointing at the source URL or local path.
The skill shows the raw body verbatim before anything is written — this is the security review gate.
The OWASP Agentic Skills Top 10 v1.0 (AST01–AST10) review runs on the candidate.
The skill reshapes the candidate to agentskills.io standard and catalogue craft, then writes it through the path-jail to the destination pack.

The skill reads workspace context (the CHARTER, the pack directory layout) automatically from the repo's own structure.
The engineer does not configure input file paths; the skill discovers what it needs.

No ledger is opened on a direct assimilation — the assimilation is its own record.
The engineer reviews the diff before the PR is merged; the PR is the governance artifact for a single-primitive adoption.

After landing, run `python tools/run-pack-evals.py --pack <name>` to verify the new skill activates on the right prompts and stays quiet on near-misses.

**Primary touchpoints:** `assimilate-primitive`.

**Where to go next:** [Your first assimilation](../tutorials/first-assimilation.md) walks the full single-primitive skill flow end to end.
For subagent-specific concerns, see [Your first subagent](../tutorials/your-first-subagent.md).

---

## Catalogue maintainer

A catalogue maintainer manages a full derived catalogue — a fork, a domain-specific adaptation, or an org-wide catalogue that multiple teams install from.
Their work is a recurring loop: survey external sources, evaluate candidates, propose packs, assimilate approved primitives, and publish updates.

### Pack arc: the four-stage progression

The four skills form a natural arc:

| Stage | Skill | Output |
|---|---|---|
| Discover | `assimilate-repo` | Ledger of candidates with verdicts |
| Scaffold | `propose-catalogue-pack` | Pack shell + RFC draft |
| Fill | `assimilate-primitive` × N | Shaped skills and subagents in the pack |
| Publish | `export-catalogue` | Redistributable fork or profile update |

Each stage's output is the input to the next.
The survey's ledger determines what gets proposed.
The proposed pack's shell determines where primitives land.
The filled pack is what gets exported or profiled.

A single-primitive intake enters at Fill, skipping Discover and Scaffold entirely.
A maintenance update skips Scaffold (the pack already exists) and re-fills from a re-run survey.
The arc describes the full flow; each operator enters at the stage their situation requires.

### Survey and evaluate

The survey phase uses `assimilate-repo` to inventory a source into a resumable ledger.
The ledger lives at a deterministic path derived from the run-id, so an interrupted survey can be resumed without re-fetching.
Each candidate gets a verdict: `assimilate`, `reject`, or `needs-new-pack`.

For `needs-new-pack` candidates, `propose-catalogue-pack` tests the proposed pack against the catalogue's charter before scaffolding anything.
The charter test is the gate — if the proposed pack doesn't clear all four principles, scaffolding does not happen and the reason is named.

### Assimilate and shape

Each approved primitive goes through `assimilate-primitive`.
Context for the assimilation is read from the workspace's own structure — the CHARTER, the pack directory layout — not from user-supplied file paths.
This means the skill's behavior is consistent across any workspace that has the catalogue installed and does not depend on operator-configured knowledge locations.

The security review at this step runs the full OWASP AST01–AST10 check against the candidate.
The operator is the last human gate before the skill lands: the raw body is always shown verbatim, and any code (hooks, scripts) requires explicit confirmation.

### Workspace queue integration

Survey and evaluation work lives in `[shaping_queue]` — it is shaping work, not build work.
Once an RFC is accepted and a pack shell exists, individual primitive assimilations move to `[work].queue` as build tasks: one spec per primitive.
Running `workspace-status` at session start surfaces the current assimilation queue without reading any other file.
Between sessions, a new agent or a colleague can pick up exactly where the previous session left off.

### Profile and publish

A catalogue that has grown through assimilation can be published two ways.

The first is a **profile update**: the maintained catalogue proposes a new profile (via RFC) so the adopted set installs in one command.
A profile is a curated, single-scope manifest — see [Design a profile](../../_shared/how-to/design-a-profile.md) for the four design tests and worked examples.

The second is an **export**: `export-catalogue` produces a redistributable fork in white-label mode (all upstream identity stripped) or attributed mode (upstream credit preserved in the declared attribution surface).
The export's verify step is fail-closed — any surviving identity anchor stops the export.

**Primary touchpoints:** `assimilate-repo`, `propose-catalogue-pack`, `assimilate-primitive`, `export-catalogue`.

**Where to go next:**
[Survey a repo](../how-to/survey-a-repo.md) ·
[Export a fork](../how-to/export-a-fork.md) ·
[The convergence model](the-convergence-model.md) ·
[Design a profile](../../_shared/how-to/design-a-profile.md)

---

## Catalogue author

A catalogue author contributes back upstream — either to the parent catalogue their fork derived from, or to an open catalogue they participate in.

### Contributing upstream

The author's path is the inverse of assimilation.
They have shaped a skill to their catalogue's craft and want to upstream it.
The path is a PR against the upstream repo: take the shaped skill from `packs/<pack>/.apm/skills/<name>/`, open a PR against the upstream, and let the upstream's own assimilation review run.

The upstream will run its own OWASP AST review and activation evals — it treats the contribution as a fresh primitive.
The author can pre-clear these by running `python tools/lint-skill-spec.py` and `python tools/run-pack-evals.py --pack <name>` locally before opening the PR.

There is no `export-to-upstream` skill — the upstream PR is intentionally a manual, human-reviewed act.
The no-merge-back principle means the upstream reviews the contribution as new work, not as a trusted sync.
This is the correct posture: bidirectional sync between a catalogue and its derivatives is where divergence accumulates and identity-leak accidents happen.

**Primary touchpoints:** The upstream repo's own assimilation review; `lint-skill-spec.py` and `run-pack-evals.py` for pre-clearance.

**Where to go next:** [The convergence model](the-convergence-model.md) — the no-merge-back principle explained.

---

**Source journey maps:**
[catalogue-engineer-converges-skills](../../../product/journeys/catalogue-engineer-converges-skills.md)
