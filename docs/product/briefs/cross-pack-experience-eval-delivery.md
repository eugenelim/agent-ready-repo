# Brief: prove the four-pack digital-experience chain composes

- **Slug:** `cross-pack-experience-eval-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed `Clean` by an independent delivery-brief review at commit `97221f5bb`; the later edits were wording corrections, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/cross-pack-experience-eval.md`](../intents/cross-pack-experience-eval.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** intent:cross-pack-experience-eval

## Outcome

Maintainers run one offline, deterministic check that every handoff between `product-strategy`, `product-engineering`, `experience-design` and `frontend-engineering` resolves, plus a report-only golden-path run over four fixture types. A pack that passes its own rubric but breaks the chain is caught before release.

## Success metrics

- The seam check fails on a seeded phantom handoff, an unresolved skill reference, a missing risk-mode field, drifted contract copy, a missing evidence-manifest entry, and an adapter projection that leaves a transformed, degraded or dropped primitive undeclared, and passes on the current tree.
- The host and model fields read `not measured` until the live follow-up supplies them.
- Each of the four fixture types (public marketing plus docs, SaaS onboarding plus workspace, internal dashboard, transactional service) has a recorded golden-path report with host, model, adapter-contract version, fixture, permissions and a measurement status per signal.

## Scope / Non-goals

**In scope:**

- Deterministic `tools/` checks for the five seam classes.
- Adapter-projection validation of canonical skill sources against `contracts/adapter.schema.json` and `docs/architecture/runtime-adapter-crosswalk.md`, in E1.
- Four fixtures and a report-only harness that reads recorded fixtures and compares them with a prior-version baseline.
- A `not measured` row for any host without automatable evidence.

**Non-goals:**

- Live per-host activation runs (follow-up below).
- Promoting any check to a gate; calibration comes after report-only runs.
- A general eval platform or remote-agent protocol.
- Skill-local activation fixtures, which stay with their skills.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| E1 | Seam checks in `tools/`: referenced skills resolve, adapter projections declare their transformed, degraded and dropped primitives, no phantom handoffs, risk-mode contract fields, contract-copy drift, evidence-manifest entries. Built on the shipped Digital Experience Contract, `visual-handoff-golden-path` and the roster suite. | pytest with one seeded violation per class and a clean run over the real tree | none | Ordering waiver (Constraints) |
| E2 | Four fixture types and the report-only golden-path harness over transcripts that E2 itself authors as committed fixtures (owner eugenelim), with the baseline being the previous committed report (the first report records `no baseline`), with the baseline comparison and the measurement-status record. Home: the same repository-level `tools/` area as E1, owner eugenelim; `experience-design` keeps the terminal whole-journey review (its `design-review` skill reviews the final journey), which resolves RFC-0071 D7's stale destination. The harness reports seven separate signal classes: activation, process, handoff, final artifact, journey outcome, style, and efficiency. | pytest over the fixtures; harness output validates against a schema; report-only exit code is zero | E1 | Delivered artifacts of M2a, M2b, M3c and M3d; execution waits for delivered artifacts, not approved specs, so fixtures use real field names |

### Manual or live residue, split off as non-blocking follow-ups

- Live headless runs on each supported host (Claude Code, Codex and others), owner eugenelim. Needs host CLIs and credentials, so it runs from a dispatch-only workflow and never blocks this brief.
- Calibration of report-only signals before any gate decision.

## Decisions

- Decided 2026-11-05 by eugenelim: per-host activation cases are waived for E1 and E2. The dispatch-only live-run follow-up stays named, with a `not measured` row per host until it runs.

## Constraints / Appetite

Waiver recorded 2026-11-05 by eugenelim, lifecycle owner: the RFC-0071 ordering is waived for slice E1 only. The rest of M5 keeps the strict order, and RFC-0071 text is unchanged.

Two sessions of medium size. If the harness starts to need a scheduler, a result store or a remote protocol, stop and re-cut.

## Assumptions / Risks

- **Riskiest assumption:** a bounded layered evaluation proves source projection, handoff and final artifact without becoming an eval platform. De-risk by shipping E1 alone first; it needs no model.
- Risk: fixtures encode fields the upstream specs later rename. E2 waits for the delivered artifacts for that reason.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: [`cross-pack-experience-eval.md`](../intents/cross-pack-experience-eval.md).
