# Initiative: Agent Skill Engineering

- **ID:** `INI-009`
- **Name:** Agent Skill Engineering
- **Status:** Active
- **Appetite:** 1–2 quarters
- **Owner:** Repository maintainers
- **workspace.toml section:** `["ini-009"]` in `workspace.toml`

## Outcome

Authors and agent loops can use one portable, progressively disclosed engineering knowledge system to create, evaluate, review, and optimize agent skills across Python and TypeScript/Node contexts, including safe composition with subagents, hooks, plugins, skill/evaluation CI, worktrees, and shared hosts. This repository self-hosts that capability and measurably reduces duplicated guidance without losing repository-specific policy, enforcement, or external AgentBundle adapter mechanics.

## Scope

**In scope:**

- A portable `agent-skill-engineering` pack with author/update and review/optimize workflows.
- A governed same-pack OKF corpus and non-self-discovering provider router.
- Portable capability floors plus retrieval-dated profiles for Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Google Antigravity.
- Python/pytest and TypeScript/Node script and evaluation topics.
- A census-backed catalogue of current pack skill patterns, including knowledge providers, progressive authoring modes, orientation/workspace resumption, and result-presentation usability.
- Skill-, pack-, skill/evaluation-CI-, worktree-, and shared-host execution economics.
- Runtime-neutral security including untrusted-input handling, least authority, and authentication/secret resolution outside model context without coupling portable guidance to the repository's credential implementation.
- Optional work-loop and architect-design integrations, with a path for later explicit consumers.
- Self-host installation and evidence-gated reduction of duplicated catalogue-curation, tooling explanation, `AGENTS.local.md`, scoped guidance, and maintainer/author guides.
- Backlog disposition and an external non-AgentBundle portability pilot.

**Non-goals / out of scope:**

- Moving AgentBundle manifests, adapters, projection, self-host commands, versions, admission, or publication into portable pack content.
- A generic CI, pytest, Node, Git, or developer-productivity pack.
- Runtime OKF lookup, direct cross-pack raw OKF resolution, hosted retrieval, or executable knowledge.
- Treating Claude or Codex extension behavior as universal.
- Removing mechanical enforcement or always-loaded repository safety rules.

## Capability areas

| Capability | Description | Status |
| --- | --- | --- |
| Portable workflows | Author/update and review/optimize agent skills with task-shaped retrieval | Shaping |
| Governed knowledge | Same-pack OKF source, secure deterministic compilation, and bounded provider routing | Shaping |
| Languages and evaluation | Shared script/eval contracts with separate Python/pytest and TypeScript/Node depth | Shaping |
| Execution economics | Measurement-led optimization across local scripts, packs, skill/evaluation CI, worktrees, and shared hosts | Shaping |
| Security and authentication isolation | Treat inputs as untrusted, preserve least authority, and keep raw credentials outside model context | Shaping |
| Runtime composition | Common floors and retrieval-dated enterprise runtime profiles for subagents, hooks, and plugins | Shaping |
| Consumer integration | Optional work-loop, architect-design, and future provider-mediated retrieval | Shaping |
| Repository adaptation | Self-host, guide and guidance migration, catalogue-curation reduction, tooling rationale consolidation | Shaping |
| Evidence and maintenance | Promotion thresholds, provenance, revalidation, pilots, and backlog closeout | Shaping |

## Milestone sequence

| Milestone | Scope summary | Target quarter |
| --- | --- | --- |
| M0 | Accept RFC-0097, record the provider-mediated knowledge ADR, and approve delivery specs | Q3 2026 |
| M1 | Ship portable `frame`/`create`/`update` modes, secure compiled router, foundational corpus, authentication-isolation guidance, and foundation activation/behavior evals | Q3 2026 |
| M2 | Expand router/evals; activate `knowledge-provider` and `runtime-package`; add Python/pytest, TypeScript/Node, execution-economics, skill-pattern/usability topics, subagent, hook, plugin, and eight enterprise runtime profiles | Q3–Q4 2026 |
| M3 | Integrate work-loop and architect-design; self-host the pack in this repository | Q4 2026 |
| M4 | Update author/maintainer journeys and collapse duplicated guidance through measured parity gates | Q4 2026 |
| M5 | Complete the external portability pilot, disposition backlog items, publish maintenance ownership, verify every planned architecture section, change its status to `CURRENT` with the verifying commit, and close the initiative | Q4 2026 |

## Delivery rules

- RFC-0097 is the accepted governing decision. Implementation remains non-dispatchable until its canonical specs are approved and registered under this initiative.
- Every implementation slice gets a canonical spec before it is added to `["ini-009".work]`.
- Corpus content and AgentBundle delivery mechanics are reviewed as separate boundaries even when one spec touches both.
- Portable authentication guidance defines context isolation and bounded capability use; it does not name or depend on this repository's credential implementation.
- Shipping a runtime knowledge profile does not claim AgentBundle projection support for that runtime; adapter changes remain separately governed.
- Footprint deletion is gated by cold-agent task parity and retrieval measurements; a failed gate retains the old owner.
- Runtime claims carry a first-party source, date retrieved, exposed source version/update date, and verification date. Stale capability claims roll the profile to `needs-revalidation`; operative guidance is withheld rather than guessed.
- The planned architecture remains `PLANNED` until every described section is implemented and verified; M5 records the verifying commit when promoting it to `CURRENT`.

## Backlog disposition variances

RFC-0097 D7 approves a disposition *policy*, not a state change. Where canonical
backlog evidence contradicts the planning map the canonical owner wins on state and
this initiative records the variance; separately and unconditionally, D7 requires
every open→closed move to record its artifact, evidence, owner review, and date,
whoever performed the move. Both duties apply to the entries below. Recorded
variances:

- **2026-08-27 — `okf-index-title-interpolation-unescaped` and
  `okf012-nondeterminism-guard-untested` closed ahead of Slice 0.** D7 listed both as
  prerequisites to promote into the corpus/router foundation spec.
  [`docs/specs/okf-follow-ons/spec.md`](../../specs/okf-follow-ons/spec.md) resolved
  both instead — bounding and escaping compiler-owned OKF index display metadata, and
  adding a mutation-proven `OKF012` repeated-render test — and moved both to
  `[backlog].closed` with their original provenance preserved. Slice 0 inherits them
  satisfied and must not re-open or re-scope them. Evidence: `_index_display_value`
  and `_index_link_destination` in
  `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, the
  exact-byte hostile fixtures in
  `packs/catalogue-curation/tests/skills/compile-okf/test_render.py`, and the
  mutation-proven `OKF012` test in
  `packs/catalogue-curation/tests/skills/compile-okf/test_apply.py`.
  **Owner review: not obtained as a separate pre-move step.** This change performed
  the close itself; mover and item owner coincide (both packs declare maintainer
  `eugenelim`, and this initiative's owner is Repository maintainers), so no
  independent owner signed off before the move. No D7 exemption is claimed for it —
  the closing change's own adjudicated reviews are its verification, not an owner
  sign-off.
- **2026-08-27 — `architect-okf-bundle-root-missing-license` closed by the same
  spec.** D7 keeps this item separately owned by architect, so its closure is
  recorded here against D7's four required fields rather than claimed as a
  canonical-owner resolution:
  - **Artifact:** [`docs/specs/okf-follow-ons/spec.md`](../../specs/okf-follow-ons/spec.md).
  - **Evidence:** the `license: "Apache-2.0 OR MIT"` declaration in
    [`packs/architect/okf/architecture-lenses/index.md`](../../../packs/architect/okf/architecture-lenses/index.md)
    and the roster discovery/`show` regression test in
    `tests/roster/test_okf_catalogue_discovery.py` — not the `[backlog].closed`
    record, which the closing change wrote itself.
  - **Date:** 2026-08-27.
  - **Owner review: not obtained from architect's owner.** The closing change's
    own adjudicated reviews are its verification, not this item's owner sign-off.

  Three facts follow, and they are distinct. The pack-content defect itself is
  resolved on the evidence above. Architect's owner has not reviewed that
  closure. So D7's "before architect becomes the integration pilot" precondition
  is satisfied only on an owner-unreviewed closure — INI-009 should obtain
  architect's review before treating architect as the integration pilot, and
  that review is the only step still outstanding on this item.

## Delivery-cut variances

- **2026-08-29 — Slice 2 is delivered as 2a and 2b.** The original brief's
  single Slice 2 combined corpus, language, pattern, and execution-economics
  work. It is now split into the active
  [`agent-skill-engineering-corpus`](../../specs/agent-skill-engineering-corpus/spec.md)
  (2a) and queued
  [`agent-skill-engineering-languages-and-execution`](../../specs/agent-skill-engineering-languages-and-execution/spec.md)
  (2b), with 2b depending on 2a. **Authority:** the 2a spec's `Durable Outputs`
  table, `Delivery-cut variance` row, which identifies this split as a departure
  from RFC-0097's single corpus follow-on and requires this record.
- **2026-08-29 — `runtime-package` is deferred from 2a and 2b.** The capability
  is not shipped by either slice. **Authority:** RFC-0097 D1's mode-availability
  rule: `runtime-package` remains unavailable until M2 package-lifecycle claims
  and runtime-profile gates pass; the 2b spec's `Never do` boundary therefore
  excludes it from that successor slice.

## Links

- `workspace.toml` initiative section: `["ini-009"]`
- Governing RFC: [RFC-0097](../../rfc/0097-agent-skill-engineering.md)
- Planned architecture: [agent skill engineering](../../architecture/agent-skill-engineering.md)
- Delivery brief: [deliver agent skill engineering](../briefs/agent-skill-engineering.md)
- Evidence: [practice inventory](../../rfc/0097-notes/practice-inventory.md), [execution-economics archaeology](../../rfc/0097-notes/execution-economics-archaeology.md)
- Parent: none
- Shaping artifacts: RFC-0097 and its notes
