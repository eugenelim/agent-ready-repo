# catalogue-curation

Grow and maintain an agent-skill catalogue — bring in new skills, survey external repos, propose new packs, and produce redistributable derivatives.

---

## Start here

| Skill | The catalogue job it serves |
| --- | --- |
| **`propose-catalogue-pack`** | Stand up a **new pack** — justify it's additive and fits the catalogue's charter, scaffold the shell, and emit an RFC (or reject it). |
| **`assimilate-primitive`** | Bring **one** external skill / subagent / hook (or a small bundle) in from a local path or URL — safely, then **reshaped to our craft** (activation, progressive disclosure, anti-pattern steering), or rejected. |
| **`assimilate-repo`** | Survey a **whole external repo/catalogue** into a reviewable RFC of per-candidate verdicts, resumable across sessions and worktrees via a ledger. |

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

**Create a self-hosted catalogue**
Run `agentbundle catalogue init --preset self-hosted` to scaffold a new catalogue from the managed template. No fork required.

---

## Guardrails

- **Never** mutates the `agentbundle` engine or `credential-brokers` through any skill — a path-gate blocks protected-tree changes absent a deliberate, human-authored RFC.
- **Ingested code runs the repo's own gates** (lints + CodeQL/Snyk) before it lands, and known anti-patterns (a script that triggers a skill/agent, a misused agent, a flooding "skill") are steered to our shape or rejected — never laundered in.
- **No new engine, no new dependency** — skills plus declarative manifests only.

---

## Who this is for

`catalogue-curation` is for **catalogue maintainers** — the people who own the shape of the catalogue and decide what lands in it. It is not for ordinary adopters who want to install and use skills.

For internal procedures and how-tos, see [`docs/guides/`](../../docs/guides/) (maintainer documentation, not published as adopter-first content).

Repo-scope, opt-in; not in any default profile. For derived or enterprise catalogues, use `agentbundle catalogue init --preset self-hosted` instead.
