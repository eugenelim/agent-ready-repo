---
name: propose-catalogue-pack
description: Use to justify and scaffold a NEW pack area for this catalogue — test that it is additive and fits the catalogue's declared coverage model plus the four charter principles, then scaffold the pack shell and emit an RFC with a per-primitive inventory, or reject it as non-additive. Triggers on "should we add a pack for <area>", "propose a new pack", "justify a <vendor/domain> pack". Do NOT use to ingest units (use assimilate-primitive or assimilate-repo).
metadata:
  boundaries: [filesystem_write]
---

# Skill: propose-catalogue-pack

Stand up a **new pack** the right way: prove it earns its place, scaffold the
shell to convention, and route the decision through an RFC — or reject it.
Justification-first; the scaffold is the reward for clearing the bar, not the
starting point.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.
Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. Don't force narrative into a table.

## Procedure

1. **Test additivity + fit against the *local* charter.** Read this catalogue's
   `docs/CHARTER.md` coverage model (SDLC here; a different model in a
   re-purposed fork) and the four charter principles — universal · substantive
   not duplicative · a habit not a tool · used often enough to stick. A proposed
   area that duplicates an existing pack, or fails a principle, is a **reject**
   with the failing principle named.

   **Tech-stack accelerator packs** are a distinct routing path — their
   specificity is the point, so they are **exempt from Principle 1 (Universal)**
   and must instead clear **Principles 2–4** plus three extra gates: (1) a named
   maintainer, (2) a stated maturity scope (`validated` / `contract-complete` /
   `experimental`), and (3) an archiving/deprecation path. An accelerator pack
   that cannot satisfy all three extra gates is a reject. If the proposal is
   tech-stack-specific (a CI/CD platform, IaC tool, SaaS integration), route it
   through this path explicitly — do not fail it on Principle 1.
2. **Diagnose the boundary.** What primitives would the pack carry, what does it
   depend on (`core`? another pack?), what's explicitly out of scope. If a
   heavy-knowledge dependency on another folder path in the same source is
   discovered, surface it as a blocker — a pack that can't stand on its own
   isn't additive.
3. **Scaffold the shell** (only on a pass) — `pack.toml`, `.claude-plugin/plugin.json`,
   `README.md`, empty `.apm/`. Route all writes through
   `agentbundle.safety.write_jailed`. See
   [`references/pack-shell.md`](references/pack-shell.md).
4. **Emit an RFC** with the per-**primitive** inventory + verdicts (the pack's
   candidate skills/agents/hooks, each assimilate/reject). When the inventory
   comes from a survey, consume `assimilate-repo`'s output rather than
   re-inventorying.
5. **Prepare elicitation, don't flood.** Where fit, naming, or scope is a
   judgment, present what you found + options + a recommendation.

## Never do

- Write under this repo's `packages/agentbundle/**` or `packs/credential-brokers/**`
  (RFC-0059 D6).
- Scaffold a pack that hasn't cleared the additivity + four-principles bar —
  reject non-additive areas explicitly rather than shipping a shell.
- Write outside `agentbundle.safety.write_jailed`.

_Depends on `core` + `governance-extras`. Repo-scope; not in any default profile._
