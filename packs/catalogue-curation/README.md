# catalogue-curation

The **catalogue-operator's toolkit** — the skills a maintainer reaches for to
*grow and maintain* an agent-skill catalogue, one meta-level above
`governance-extras`. It is **domain-agnostic**: the same toolkit serves this
software-delivery catalogue, a creative-writing catalogue, or an
investment-research one.

Growing a catalogue means several recurring jobs — standing up a new pack,
shaping a new skill to convention, bringing in good work from outside, and
producing a redistributable copy for another org or domain. Each was hand-run,
un-resumable, and craft-inconsistent. This pack makes them **gated, resumable,
and shaped to the repo's craft** — and it's the **home for catalogue operations
generally**, so new ones land here as they come up (see *Roadmap*).

## The toolkit today

| Skill | The catalogue job it serves |
| --- | --- |
| **`propose-catalogue-pack`** | Stand up a **new pack** — justify it's additive and fits the catalogue's charter, scaffold the shell, and emit an RFC (or reject it). |
| **`assimilate-primitive`** | Bring **one** external skill / subagent / hook (or a small bundle) in from a local path or URL — safely, then **reshaped to our craft** (activation, progressive disclosure, anti-pattern steering), or rejected. |
| **`assimilate-repo`** | Survey a **whole external repo/catalogue** into a reviewable RFC of per-candidate verdicts, resumable across sessions and worktrees via a ledger. |
| **`export-catalogue`** | Produce a **redistributable derivative** (organization rebrand or domain re-purposing) in `white-label` or `attributed` mode, with a fail-closed leak check. |

The **craft-shaping** engine that `assimilate-primitive` uses to bring an
external skill up to convention — activation-optimized description, collision
check, progressive disclosure, anti-pattern steering — is the same discipline a
maintainer applies when **authoring a new skill from scratch**; it's written to
be reused for both.

## Guardrails

- **Never** mutates the `agentbundle` engine or `credential-brokers` through any skill — a path-gate blocks protected-tree changes absent a deliberate, human-authored RFC.
- **Ingested code runs the repo's own gates** (lints + CodeQL/Snyk) before it lands, and known anti-patterns (a script that triggers a skill/agent, a misused agent, a flooding "skill") are steered to our shape or rejected — never laundered in.
- **Fail-closed export** — a run hard-fails if any upstream identity would leak.
- **No new engine, no new dependency** — skills plus declarative manifests only.

## Roadmap

The pack is the deliberate home for catalogue operations as they arise —
e.g. retiring a primitive, deprecating a pack, or a dedicated greenfield
skill-authoring flow. Deferred items live in `workspace.toml [backlog]`.

## Learn it

Full walkthroughs, references, and the "why" live in the per-pack guide:
[`docs/guides/catalogue-curation/`](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/catalogue-curation/).

Requires `core` and `governance-extras`. Repo-scope, opt-in; not in any default profile.
