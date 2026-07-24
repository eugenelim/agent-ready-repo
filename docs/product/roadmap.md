# Roadmap

> Direction for the next 2-4 quarters. **Not** commitments. The whole point
> of writing this down is that it can change.

**Last updated:** 2026-07-18
**Reviewed:** quarterly. Next review: 2026-10-18.

If the current date is more than 90 days past "Last updated", treat this
file as stale and ask before relying on it.

> **Orientation:** This roadmap tracks INI-002 (Platform Core) — this repo's
> slice of INI-001 (AI-Native Ecosystem). For the governing RFC and full AC
> list, read [`docs/rfc/0064-ini-001-ai-native-ecosystem.md`](../rfc/0064-ini-001-ai-native-ecosystem.md).
> For the product vision, read [`docs/product/shaping/product-vision-INI-001.md`](shaping/product-vision-INI-001.md).

## Now

**ini-003 Wave 2 · M3c — Design token skills.** Renamed `design-system` → `design-token-taxonomy` (alias-free; ADR-0038); corrected DTCG description (W3C Community Group, not W3C Recommendation); added `design-system-foundations` skill (lightweight + full mode); updated FE genre routing; added two-step chain how-to guide. Pack version 1.2.1 → 1.3.0. [spec/xd-design-system-foundations — Shipped 2026-07-24]

**M1 · Workspace Foundation.** `workspace.toml` seed + `workspace-status` skill + brief template DoR fields (Status, Rabbit holes, Instrumentation, Design artifacts) + work-loop / receive-brief / new-rfc extensions + agentbundle-layout.toml `[product]` table + ADR for D2/D4 architectural decisions. [RFC-0064](../rfc/0064-ini-001-ai-native-ecosystem.md)

**M1 fix — work-loop done-step lifecycle.** Extended done-step to find the current spec in `queue` (not just `active`), add Step 0 stale-queue warning, and fix the `spec/` prefix path-resolution bug. [spec/work-loop-queue-shipped-fix]

**M1 · Session-arc conventions (RFC-0067, Change D).** Pack workflow design guide (`docs/guides/_shared/explanation/pack-workflow-design.md`) — five-step framework for pack authors: workflow-type classification, arc-stage mapping, skill naming, vault-path shape, workspace-status registration. CONTRIBUTING.md step 0 added. [spec/spec-D-pack-workflow-guide — Shipped; Changes A/B/C in queue]

**RFC-0067 Change B — Pack status skills.** Two new read-only cold-start orient skills: `desk-research-project-status` (desk-research pack) and `experience-status` (experience-design pack). Added `design` as a valid `shaping_queue` type; `workspace-status` routes `{type = "design"}` entries to `experience-status` (fallback: `journey-mapping`). [spec/spec-B-pack-status-skills]

**RFC-0064 amendment — workspace-status integrity trust boundary.** Documents the session-fragmentation gap (workspace.toml silently incomplete when RFC acceptance and spec generation happen in separate sessions); restructures `## Amendments` to two-layer format. [spec/rfc-0064-errata-workspace-integrity]

**M1 · capture-work — classify-then-triage front-door (RFC-0064 Amendment #3).** Renames `queue-add` → `capture-work`; adds build/shape classification before write; routes shaping items to `[shaping_queue]` or typed `[backlog].open`; progressive capability-detected hand-off. `workspace-status` now prefixes every Ready and Backlog item with `[build]`, `[shape]`, or `[brief]`. `work-loop` step-0 guard redirects shaping items to the correct skill. [spec/capture-work]

**RFC-0064 P3 · author-brief documentation.** New intake how-to (`docs/guides/core/how-to/intake-an-external-brief.md`) covering the `author-brief` skill end-to-end; DoR gate section + `Rabbit holes`/`Status` rows added to `product-brief-fields.md`; `receive-brief` how-to decision table updated. [spec/author-brief-docs]

**RFC-0064 Amendment #4 — cross-pack first-value adoption overlay.** Defines Level A/B pack obligations and pilot-first rollout contract for pack onboarding. Five new work items queued: `spec/portfolio-pack-first-value-contract` (semantic onboarding contract, no dependency), three pilot specs (`architect`/`figma`/`governance-extras`, each needing the contract), and `spec/agentbundle-first-value-handoff` (install completion UX, needing the contract). Two shaping entries added: `nontechnical-pack-first-value-rollout` (shape, blocked on pilots) and `portfolio-outcome-entry-surfaces` (design, blocked on contract + pilots). Feeds P5 adoption evidence. [RFC-0064 Amendment #4]

## Next

**M2 · Strategic Shaping.** Five new PE pack skills grounding the six-step sequence (Outcome → Problem → Diverge → Validate → Bet → Spec) at initiative altitude. `frame-situation` (bottom-up signal → typed finding → six-step route; embeds Wardley capability maturity for situational awareness). `identify-opportunities` (step-2 opportunity assessment; embeds JTBD framing — functional / emotional / social jobs). `diverge-solutions` (step-3 option generation; must resolve overlap with existing `explore-options` skill). `place-bet` (step-5 human commitment gate; betting table surface). `map-capabilities` (product vision → all capability areas in one structured pass). Initiative brief artifact + Lean Canvas template as altitude-0/1 framing. Three-altitude model grounded: Company (years; PRFAQ, OKR) → Initiative (quarters; vision, capability map, initiative brief) → Project (weeks; brief, spec, plan). [RFC-00XX · pe-pack-strategic-shaping, opens when M1 ships]

**M3 · Findings & RFC Management.** `rfc-status` skill in governance-extras. `research-project-start` `.context/` bug fix. Findings register seeds (`rfc-candidates.md`, `roadmap-intents.md`). Pack renames: `research` → `desk-research` (canonical consulting/design-UX term); `experience` → `experience-design` (canonical agency term; used by frog, Fjord, AKQA). [No sub-RFC needed — direct implementation]

## Later

**M4 · Product Strategy Layer.** Full build-out of the `product-strategy` pack (RFC-0063, already open as draft — M4 begins on acceptance). OKR cascade skill: company OKRs → gap analysis → `frame-situation` routing (bottom-up and top-down meet). PRFAQ template as the Amazon-style altitude-0 forcing function ("write the press release before the product"). Market analysis skills: Porter's Five Forces (competitive landscape), PESTLE (macro environment), BCG Matrix (portfolio position), SWOT (situation synthesis). Each skill produces a structured artifact that feeds the six-step sequence at initiative altitude. [RFC-0063 · product-strategy-pack]

**M5 · Tracker Integration.** `github-brief-intake`, `linear` pack + `linear-brief-intake`, `jira-align-brief-intake`. [RFC-00XX · linear-pack]

**M6 · Documentation Wave.** Full documentation channel sweep for workspace.toml and PE pack. Diátaxis guides (tutorials, how-tos, reference, explanation). Astro site project index view. [No sub-RFC needed]

## Shaping queue — research threads

Topics surfaced in the INI-001 design session that need further investigation before sister initiative RFCs can be written. Not M1–M6 scope. Captured here so they aren't lost.

**Remote agent session pickup protocol.** How `workspace.toml` is consumed at session start by each major harness — Claude Code (reads from git, stateless), Devin (reads from VM snapshot), Manus (reads from TiDB record), Copilot Agent (platform-managed context). What the handoff contract looks like; what state beyond `workspace.toml` must transfer. Feeds INI-003 RFC.

**Harness adapter pattern.** Whether a single adapter contract is feasible across the four execution models, or whether each harness needs a purpose-built adapter. MCP vs. static skill-file installation per harness. How the adapter handles skill invocation, gate presentation, and completion write-back. Feeds INI-003 RFC.

**Cross-harness skill compatibility.** Ensuring `work-loop`, `workspace-status`, and `receive-brief` produce equivalent outcomes regardless of harness. What the test surface looks like for a skill that must behave identically in a local Claude Code session and a remote Devin VM. Feeds INI-003 RFC.

**State persistence schema.** What specific agent state must survive session boundaries: `workspace.toml` (declared intent), spec execution progress (plan step, current file, intermediate artifacts), gate outcomes, agent context (decisions made mid-task not yet committed). Format and storage choices for each harness's model. Feeds INI-005 RFC.

**Telemetry events schema.** What events matter for exception-based review: `spec-started`, `gate-reached`, `gate-passed`, `gate-failed`, `gate-waived`, `budget-exceeded`, `spec-stalled`, `spec-shipped`. What metadata each event carries; how events map to alert thresholds configurable per project. Feeds INI-005 RFC.

**Brief-to-agent dispatch patterns.** Pull model (agents claim from `[brief_queue].ready`) vs. push model (team lead assigns). How agents signal capacity. What the dispatch API surface looks like for INI-003 to expose and INI-004 to consume. Feeds INI-004 RFC.

**Adopter persona research.** Validate the Step-1 hypothesis (most teams are at Step 1 — our working assumption). Who adopts INI-002 first: solo engineer, startup PM, enterprise platform team. What their onboarding journey looks like at each altitude. Closes the known-unknown in RFC-0064.

**Portfolio pack design.** How a portfolio-level pack bridges research from a private vault or team repo into this repo's shaping queue. Multi-repo initiative coordination above `workspace.toml` level — what the data model looks like when an initiative spans three repos. Feeds post-M3 RFC.

**Linear 2-way sync mechanics.** The write direction (spec ships → Linear Issue closes via `Fixes LIN-123` in PR body) is settled. The read direction — Linear Issue updated / closed externally → `workspace.toml` updated — needs webhook handler design and event schema. Feeds M5 sub-RFC (linear-pack).

## Not in scope (this repo)

Things governed by sister initiatives — each has its own RFC when its trigger fires. See `docs/product/shaping/ecosystem-overview.md` for the full picture.

- **INI-003 Coding CLI Adapter Pack.** Headless CLI adapters for Claude Code `-p`, Codex CLI, Kiro CLI, Copilot CLI, Gemini CLI; swarm orchestration via `workspace.toml`. Trigger: INI-002 M1 ships.
- **INI-004 Remote Agent Runtime.** Cloud/VM-hosted and orchestration harnesses: Devin (VM-snapshot), Manus (TiDB-backed), Omnigent (meta-harness / pluggable sandbox providers: Modal, E2B, Daytona, Databricks), GitHub Copilot Coding Agent. Trigger: INI-002 M2 ships.
- **INI-005 Infra & Observability.** State persistence, telemetry (spec-started / gate-failed / spec-stalled / spec-shipped events), exception detection, monitoring feedback loop. Trigger: INI-004 M1 ships.
- **INI-006 Control Plane.** UI dashboards, brief-to-agent dispatch, exception-surfacing UI; extends INI-002 M6 Astro site. Trigger: INI-005 M1 ships.

## How this file is maintained

- **Owners:** the maintainers (or the steering committee, if one exists).
- **Updates:** roadmap items move between sections via small PRs. Substantive
  additions or deletions go through an RFC.
- **Review cadence:** quarterly. The review updates the "Last updated" date
  even if no items change — fresh eyes, fresh dates.
- **Drift signal:** if items in "Now" haven't moved in two consecutive
  reviews, either they're not actually being worked on (move them out)
  or the roadmap doesn't reflect what the team is doing (rewrite it to
  match).
