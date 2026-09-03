# Pack-eval rollout completion

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0037 Errata E3](../../rfc/0037-pack-activation-evals.md)

## Outcome

Eligible pack skills have stable behavior coverage and the remaining pack-eval rollout decisions are ready for their next dedicated slices.

## Opportunity

Tier 1 activation coverage and Tier-5 workflow wiring have shipped, but deterministic contracts coverage, calibration, gate consolidation, and credentialed backend behavior verification remain incomplete.

## What this absorbs

### pack-eval-coverage-rollout

Finish `spec/pack-activation-evals` Tier 2–5 work. This is medium-effort internal work with no external environment; it needs a focused session or an RFC decision. Tier 1 activation evaluation for all catalogue packs completed on 2026-07-02, including core activation cases for `capture-work`, `author-brief`, `receive-brief`, and `new-spec`. The remaining concrete Tier-2 B-lite gap is contract artifact behavior for deterministic `contracts` skills `api-contract` and `event-contract`: emit and validate a contract artifact, then add an `expect` block and fixture. Tier 4 still needs LLM-judge rubrics for `new-package` and core judgment skills; other pack rubrics are done. Tier 5 workflow wiring has shipped at `.github/workflows/pack-evals.yml:59`, which supplies `ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}`, but calibration remains deferred before RFC-0037 Open Q1 decides report-only versus regression-from-baseline gating. RFC-0064 Amendment #4 also calls for the four core activation-boundary cases and reusable first-value rubric fields: first-task completion, visible-artifact presence, recovery path, and next-action clarity for the cross-pack adoption overlay. Take this pack-by-pack, Tier 2 first. The original GitHub-secret unblock condition is satisfied by the workflow wiring; calibration remains the next unresolved work.

### pack-evals-converters-gate-consolidation

After `pack-eval-coverage-rollout` Tier 2 ships, take `spec/pack-activation-evals` plan T8 as its own PR. `.github/workflows/build-check.yml:600` hand-enumerates `file-to-markdown`, `markdown-to-html`, `markdown-to-docx`, `markdown-to-pptx`, and `markdown-to-xlsx` for the converters carry-over gate. RFC-0037’s optional consolidation is to read `[pack.evals].skills` instead. Reconcile `mermaid-renderer`, whose coverage exists outside that five-skill enumeration, in the same PR. Do not fold it in prematurely because it risks the harness. Unblocks when Tier 2 ships.

### behavior-check-for-backend-skills

Address `spec/pack-activation-evals` Phase 3 and RFC-0037 Errata E3: atlassian’s 8 skills and figma’s 1 skill have Tier-A activation coverage but no behavior test. Live behavior needs authentication and a backend that can mutate remote state. Repeatable verification requires recorded-interaction replay through cassettes or a disposable backend or sandbox with broker-provisioned test credentials. Open a Tier-B grading RFC for LLM-judge/deltas or a dedicated cassette-harness spec. RFC-0037 states at line 306 that credentialed skills are outside B-lite and require recorded cassettes or a disposable test backend separately. Unblocks when a Tier-B grading RFC or cassette-harness spec is accepted.

## Assumptions

- The rollout state changed: Tier-5 secret workflow wiring shipped, so the remaining work is contracts `expect` blocks and deferred calibration rather than secret configuration.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
