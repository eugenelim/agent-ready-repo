# Example: placing a bet

A product engineer has evaluated options for `batch-export-v2` — a feature
letting users export large data sets — and is ready to commit the team's direction.

---

## Path (a) — diverge-solutions artifact present

The PE invokes `place-bet`. The skill resolves:

- **output_dir:** `docs/product/` (from `agentbundle-layout.toml [product]`)
- **slug:** `batch-export-v2` (active `[shaping_queue]` item)
- **Solutions artifact:** `docs/product/shaping/batch-export-v2/solution-options.md` — found
- **validation-notes.md:** `docs/product/shaping/batch-export-v2/validation-notes.md` — found

> Resolved write path: `/workspace/docs/product/shaping/batch-export-v2/bet.md`
> (realpath-expanded; no `..` escapes; no symlink escapes detected)

### Options surfaced from solution-options.md

| Option | Summary | Confidence |
|---|---|---|
| A | CSV export via async email delivery | low |
| B | Direct download with streaming | high |
| C | API-first export with webhook notification | medium |

**PE selects Option B.**

### Validation-notes folded in

From `validation-notes.md`:

- **Risk accepted:** Streaming is untested at >500 concurrent users; a
  load-test gate is required before launch.
- **Kill condition:** If p95 download start latency exceeds 3s under 200
  concurrent users in staging, revert to email delivery (Option A) rather
  than optimising streaming.

### Betting table filled

| Field | Value |
|---|---|
| option | Direct download with streaming |
| option-source | `docs/product/shaping/batch-export-v2/solution-options.md` |
| confidence | high |
| appetite | 3 weeks |
| rationale | Provides immediate, user-controlled export with the lowest ops overhead. Email delivery (A) adds async complexity the UX doesn't need; API-first (C) over-engineers for current usage patterns — no downstream consumers requiring webhooks have been identified. |
| risks-accepted | Streaming untested at scale; load-test gate required before launch |
| assumptions | Streaming is within existing CDN budget; no auth changes required for export file delivery |
| kill-condition | p95 download start latency >3s under 200 concurrent users in staging → revert to Option A |
| next-step | map-capabilities |

### Artifact written

Path: `docs/product/shaping/batch-export-v2/bet.md`

```markdown
---
type: bet
slug: batch-export-v2
date: 2026-07-21
option: Direct download with streaming
option-source: docs/product/shaping/batch-export-v2/solution-options.md
confidence: high
appetite: 3 weeks
---

# Bet: batch-export-v2

## Option chosen
Direct download with streaming — the user initiates export and receives the
file immediately via the browser, served from the CDN.

## Rationale
Provides immediate, user-controlled export with the lowest ops overhead.
Email delivery (Option A) adds async complexity the UX doesn't need; an
API-first approach (Option C) over-engineers for current usage patterns
(95th-percentile export size is under 50 MB; no downstream consumers
requiring webhooks have been identified).

## Risks accepted
- Streaming is untested at scale; a load-test gate is required before launch.

## Assumptions
- Download streaming is within existing CDN budget.
- No auth changes required for export file delivery.

## Kill condition
If p95 download start latency exceeds 3s under 200 concurrent users in
staging, revert to email delivery (Option A) rather than optimising streaming.

## Next step
`map-capabilities` — use this bet as the anchor for the capability map.

## Suggested workspace.toml transition
```toml
# batch-export-v2: bet committed — ready for map-capabilities
# Move from shaping_queue active → update type or hand to build queue
# after map-capabilities completes.
```
Run `capture-work` or edit `workspace.toml` manually.
```

### Workspace.toml suggestion printed

```toml
# batch-export-v2: bet placed — next step is map-capabilities
# After map-capabilities: transition to [ini-NNN.work].queue as a build item.
```

---

## Path (b) — no solutions artifact

The PE invokes `place-bet` on slug `onboarding-friction` before running
`diverge-solutions`.

The skill resolves:

- **output_dir:** `docs/product/`
- **slug:** `onboarding-friction`
- **Solutions artifact:** none found at `docs/product/shaping/onboarding-friction/`
- **validation-notes.md:** none found

**Skill offers `diverge-solutions` first:**

> No solutions artifact found at `docs/product/shaping/onboarding-friction/`.
>
> Recommend running `diverge-solutions` first.
>
> **Impact of skipping:** Without structured comparable options, the rationale
> and risks-accepted in the betting table are less defensible — the bet will
> rest on a single informally-described direction rather than a structured
> comparison.
>
> Would you like to run `diverge-solutions` now, or continue with free-form
> description of the options you have considered?

**PE declines**, provides free-form:

> "We looked at two options: (1) a guided checklist on the first-login flow,
> and (2) replacing the setup wizard with a short video tour. Going with the
> checklist — it's testable step-by-step and avoids video production cost."

**Skill surfaces missing validation before populating the table:**

> No validation evidence found at `docs/product/shaping/onboarding-friction/`.
> I see no `validation-notes.md` and no `de-risk-intent` output, and you
> haven't described validation you have done.
>
> **Placing a bet without validation is an accepted risk, not a silent default.**
>
> Would you like to proceed, or run `de-risk-intent` (or document validation
> notes) first?

**PE confirms:** "Proceed — we're time-boxed and comfortable with the risk."

### Betting table filled from free-form input

| Field | Value |
|---|---|
| option | Guided checklist on first-login flow |
| option-source | free-form |
| confidence | medium |
| appetite | 2 weeks |
| rationale | Testable step-by-step; no video production budget required. Video tour (Option 2) ruled out on cost and maintainability grounds. |
| risks-accepted | No comparative user validation; team is betting on the checklist pattern without structured evidence |
| assumptions | Users complete the checklist rather than skipping; analytics events are instrumented on first-login steps |
| kill-condition | _(blank — no de-risk-intent output available)_ |
| next-step | map-capabilities |

Artifact written to `docs/product/shaping/onboarding-friction/bet.md`
with `option-source: free-form`.

The skill surfaced the missing validation before writing — the PE confirmed
to proceed. `kill-condition` is left blank (no validation evidence to fold in).
