# catalogue-curation

Grow and maintain an agent-skill catalogue — bring in new skills, survey external repos, propose new packs, and produce redistributable derivatives.

---

## Start here

Decide what you're trying to do, then describe it.

```text
I found a well-crafted research skill in an external repo.
Can we bring it into our catalogue?
```

```text
I want to stand up a new pack for our data-engineering team.
```

The pack identifies the job (assimilate, propose, survey, or export), runs the appropriate gates, and presents a preview before writing anything to the repository. All changes are local — nothing is published remotely. An RFC is emitted wherever the work requires one.

---

## Common jobs

**Bring an external skill or agent into the catalogue**
Describe the source (a local path or public URL) and the skill you want to assimilate.
Returns an activation review, a collision check against existing skills, a craft-shaping proposal (activation description, progressive disclosure, anti-pattern steering), and a diff preview. You review and approve each step. Result: skill lands in the correct pack directory, shaped to your catalogue's craft, with a gate-passing record.

```text
assimilate-primitive

  Source: https://github.com/example-org/research-skills/tree/main/deep-research
  ● Activation check: description routes correctly — no collision
  ● Craft gap: missing progressive-disclosure depth
  ● Proposed reshape: [preview shown]

  Approve and land? ›
```

**Survey a whole external repo for candidates**
Say `assimilate-repo` and point to a repo path or URL.
Returns a per-candidate verdict (in / out / reshape / defer) written to a resumable ledger file. You review the ledger; each approved candidate can then be assimilated individually. Nothing is changed in your repo during the survey step.

**Propose a new pack**
Say `propose-catalogue-pack` and describe the new pack's purpose.
Tests whether the pack is additive (doesn't duplicate an existing pack) and fits the catalogue's charter, then scaffolds a pack shell and emits an RFC for human review. No RFC means no new pack.

**Produce a redistributable derivative**
Say `export-catalogue` and specify white-label or attributed mode and the target organization name.
Produces a redistributable copy of the catalogue with upstream identity either stripped or credited. Runs a fail-closed leak check before writing any output — the command hard-fails if any identity signal would escape. Result is a local directory; you publish it.

---

## Guardrails

- **All changes are local** — no remote publish, no direct commit to a shared branch; you approve the diff, then commit.
- **Preview before any write** — every assimilation and export shows a diff and waits for your approval.
- **RFC gate** — `propose-catalogue-pack` always emits an RFC; a new pack cannot land without it.
- **Ingested code runs gates** — skills brought in via `assimilate-primitive` pass the repo's lint + CodeQL/Snyk before landing.
- **Protected paths are blocked** — a path-gate prevents any skill from mutating the `agentbundle` engine or `credential-brokers` pack absent a human-authored RFC.
- **Fail-closed export** — `export-catalogue` hard-fails if any upstream identity would leak to the derivative.

---

## Who this is for

`catalogue-curation` is for **catalogue maintainers** — the people who own the shape of the catalogue and decide what lands in it. It is not for ordinary adopters who want to install and use skills.

For internal procedures and how-tos, see [`docs/guides/`](../../docs/guides/) (maintainer documentation, not published as adopter-first content).

For users who want to install and use skills from the catalogue, see the [catalogue guide](../../guides/README.md).

---

## Installation and trust

- **Scope:** repo — operates within the catalogue repo; not a portable user skill
- **Reads:** external repos, pack metadata, existing skill sources (read-only during survey and review steps)
- **Local writes:** new skill files, pack scaffolding, RFC documents — only after you approve
- **Remote reads:** public URLs provided by you (for `assimilate-primitive` and `assimilate-repo`)
- **Remote writes:** none
- **Requires:** `core` and `governance-extras` installed at repo scope

```bash
agentbundle install --pack catalogue-curation
```

---

## Skills included — under the hood

| Skill | The catalogue job it serves |
|-------|---------------------------|
| `assimilate-primitive` | Bring one external skill / agent / hook in from a local path or URL |
| `assimilate-repo` | Survey a whole external repo into a reviewable per-candidate verdict ledger |
| `propose-catalogue-pack` | Stand up a new pack — justify fit, scaffold the shell, emit an RFC |
| `export-catalogue` | Produce a redistributable derivative (white-label or attributed mode) |

---

## Go deeper

→ [`guides/catalogue-curation/`](../../guides/catalogue-curation/)
