# RFC-0073: SLO-authoring capability and error-budget PRR integration

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-27
- **Date closed:** 2026-07-27
- **Decision weight:** medium <!-- New skill in an existing pack; extends the PRR format with a concrete resolution protocol; resolves the RFC-0049 § Follow-on provisional scope call. Pre-stable; the adopter impact is additive only (not-defined behaviour preserved). -->
- **Related:**
  - [RFC-0048](0048-autonomous-product-team-operating-model.md) (operating model foundation — **Accepted 2026-06-30**)
  - [RFC-0049](0049-the-release-loop-and-company-os.md) (release-loop parent RFC — **Accepted 2026-06-30**; § Follow-on explicitly defers SLO-authoring skill home to "the sibling RFC" — this RFC settles that call)
  - [RFC-0072](0072-release-loop-deploy-doctrine.md) (sibling — G4 artifact format and progressive delivery; the G4 package schema this RFC's skill output is committed alongside)
  - [`docs/specs/release-loop/spec.md`](../specs/release-loop/spec.md) (AC6b requires the error-budget field in the PRR; currently records `error-budget: not-defined` as the default)

---

## Reviewer brief

- **Decision:** Whether to (a) adopt OpenSLO v1 as the harness-neutral SLO artifact format,
  (b) specify the required SLO document fields and an `error_budget_policy` companion block,
  (c) define a four-state resolution protocol for the PRR `error-budget` field, and (d) home
  the new `define-slo` skill in the `release-engineering` pack.
- **Recommended outcome:** Accept D1–D5.
- **Change if accepted:**
  - A new **`define-slo` skill** lands in `packs/release-engineering/.apm/skills/define-slo/`
    (D4). The skill produces an OpenSLO v1 YAML file committed to the repo at
    `slos/<service>.yaml` (D1 / D2).
  - The `release-loop` skill's release-readiness gate section is updated to replace the
    placeholder sentence about `error-budget: not-defined` with the four-state resolution
    protocol (D3 / D5) — the `not-defined` path is preserved as the explicit "no SLO
    document" state.
  - `docs/specs/release-loop/spec.md` AC6b receives a cross-reference to this RFC as the
    source of the SLO artifact schema and the PRR field resolution states — no AC text
    changes.
- **Affected surfaces:**
  - New: `packs/release-engineering/.apm/skills/define-slo/SKILL.md`
  - `packs/release-engineering/.apm/skills/release-loop/SKILL.md` — release-readiness gate
    section updated with four-state resolution; no structural changes
  - `docs/specs/release-loop/spec.md` — cross-reference note in AC6b
  - `packs/release-engineering/pack.toml` + `.claude-plugin/plugin.json` — minor version bump
  - `docs/product/changelog.md` — `[Unreleased]` entry
- **Stakes:** Additive — the `not-defined` behaviour is preserved. The OpenSLO v1 format
  choice is stable (v1 spec has been stable since 2022); the risk is moderate toolchain
  fragmentation (Sloth and Pyrra each have their own native schemas; the skill produces
  OpenSLO, which requires a toolchain-side translation step). Reversible: a follow-on RFC
  can revise the format choice before adopter SLO documents accumulate.
- **Review focus:** All decisions resolved in authoring session (D1–D5). D4 (skill home)
  is the one previously-provisional scope call — confirm or redirect.
- **Not in scope:** Ongoing error-budget monitoring, alerting backend wiring, or on-call
  ownership (future operate/incident loop). Generating Prometheus recording rules or
  alerting rules (toolchain work; the skill produces the SLO declaration, not the derived
  rules). Changes to `work-loop` or `discovery-loop`. New reviewer agents.

---

## The ask

**Recommendation:** Ship a `define-slo` skill in the `release-engineering` pack that
produces an OpenSLO v1 YAML document, and wire its output into the release-loop PRR via
a four-state resolution protocol.

**Why now (SCQA — Situation / Complication / Question / Answer):**

*Situation:* The `release-loop` PRR (launch pre-production readiness record, AC6b)
consolidates convergence results, operational-safety verdicts, and a security verdict
before the G5 prod-ship gate. It includes one field — `error-budget` — that reads the
service's cumulative reliability budget status over the trailing window, distinct from
the per-promotion canary SLO thresholds (AC6). An exhausted error budget is a
surface-to-human / halt-releases signal (Google's error-budget policy), not a canary
metric.

*Complication:* Every PRR currently ships with `error-budget: not-defined` because no
SLO-authoring capability exists. The AC6b spec explicitly calls this out as a placeholder
visible to the human — not a silent pass — and defers the capability to RFC-0049
§ Follow-on, which names it as the first of two follow-on candidates and explicitly
defers the skill home to "the sibling RFC." This RFC is that sibling RFC.

*Question:* What format should SLO documents take, what does an SLO-authoring skill
produce, and where does it live?

*Answer:* OpenSLO v1 is the harness-neutral interchange format — it has broader cross-
vendor support than Sloth's native schema and is not tied to a specific observability
backend the way Pyrra (Kubernetes-only) or Nobl9 (SaaS) are. The skill produces a YAML
file committed to the repo; the PRR gate reads the file at gate-check time. The
`release-engineering` pack is the natural home — SLO authoring is the SRE/reliability
discipline, the same seat `release-loop` occupies. `core` stays unopinionated about
deploy-and-release concerns.

---

## Decisions requested

| ID | Question | Recommendation | Rationale | Decide by | Reviewer action |
|----|----------|----------------|-----------|-----------|-----------------|
| D1 | SLO artifact format: (A) OpenSLO v1 (`openslo/v1`) as the harness-neutral interchange format, (B) a custom schema, or (C) Sloth's native `prometheus/v1` schema? | **A — OpenSLO v1** | OpenSLO is the only format with explicit cross-vendor governance (Nobl9, Dynatrace, and others). Sloth can consume OpenSLO YAML directly (`sloth generate -i <openslo-file>`), so the adopter's choice of rules-generator is not constrained by the format choice. Pyrra requires its own CRD — if an adopter uses Pyrra they author a translation shim, not a second SLO document. A custom schema has no ecosystem tooling and no migration path. | This review | Confirmed |
| D2 | Required SLO fields: (A) specify a minimum required field set (service, budgetingMethod, timeWindow, indicator with good/total queries, objectives[0].target) plus an `error_budget_policy` companion block, or (B) leave field requirements to the adopter? | **A — specify minimum required fields and the error_budget_policy block** | The PRR gate's four-state resolution (D3) requires `objectives[0].target` to compute the budget ceiling and the `error_budget_policy` block to determine which threshold applies. Without minimum required fields, the gate has no inputs; without the policy block, the halt-at-100% threshold has no specified home. The skill may scaffold a complete template; the minimum field set is the gate's hard dependency. | This review | Confirmed |
| D3 | PRR error-budget field resolution: (A) four explicit states (`not-defined` / `within-budget` / `warning:<N>%-remaining` / `exhausted:halt-releases`) derived from the SLO document and live telemetry at gate-check time, or (B) binary pass/fail? | **A — four states** | Binary pass/fail collapses the warning band that is operationally important: a service at 10% remaining budget should not record the same PRR state as one at 80% remaining. The four states map to Google's four-threshold error-budget policy (halt at 100% consumed, warn below 25% remaining, postmortem at 20% consumed by a single incident). The `not-defined` state is preserved exactly as AC6b specifies it — the absence is *recorded and visible*, never a silent pass. | This review | Confirmed |
| D4 | SLO-authoring skill home: (A) `release-engineering` pack (new skill `define-slo`), (B) `core` pack, or (C) its own new pack? | **A — `release-engineering` pack, new `define-slo` skill** | RFC-0049 § Follow-on lists three home candidates: "a skill in `release-engineering`, vs. part of the operate/incident loop, vs. its own pack." The operate/incident loop is a future sibling RFC — deferring there leaves `error-budget: not-defined` permanently. A standalone pack for one skill is premature (RFC-0041 precedent: the capability fits the existing discipline seat). `core` is explicitly scoped away from deploy-and-release concerns by the release-engineering pack's `core` dependency boundary. `release-engineering` is correct: SLO authoring is the SRE/reliability discipline and naturally paired with the loop it feeds. The skill name `define-slo` follows the `define-` prefix convention for definitional/authoring skills. | This review | Confirmed |
| D5 | Live budget consumption gap: (A) acknowledge that `budget_consumed_pct` cannot be filled statically — the skill instructs release-lead to query the telemetry backend at gate-check time using a template query derived from the SLO's metric expressions, recording `error-budget: query-failed (surface)` on failure — or (B) treat the gap as out-of-scope and leave the field at `not-defined` even when an SLO document exists? | **A — acknowledge the gap; specify query-at-gate-time + query-failed state** | Option B means the PRR gate cannot distinguish "no SLO document" from "SLO document exists but telemetry is unreachable" — both would record `not-defined`, obscuring two very different situations. Option A is honest about the integration gap while giving an implementing `release-lead` a concrete instruction: derive the trailing-window query from the SLO's `good_query` / `total_query` expressions, execute it at gate time, and record `query-failed` if the telemetry backend is unreachable. The `query-failed` state surfaces to the human — it is not a silent pass. | This review | Confirmed |

*Default if no objection: adopt D1–D5 and proceed to implementation.*

---

## Problem and goals

### Error budget is a defined PRR requirement with no fulfillment path

AC6b of the release-loop spec states: "The service's cumulative error-budget status — a
defined reliability target with the budget not exhausted" is one of four inputs to the
PRR. It further states: "This is distinct from AC6's per-promotion canary SLO thresholds:
AC6 judges the single deploy's success/error/latency metrics; AC6b reads budget-burn over
the trailing window — an exhausted budget is a surface-to-human / halt-releases signal
(Google's error-budget policy), not an autonomous promote."

The spec records: "The error-budget artifact is supplied by a follow-on SLO-authoring
capability (home provisional — RFC-0049 § Follow-on; a scope call its sibling RFC
settles); until it exists the record carries an explicit `error-budget: not-defined`
field the human sees."

This is the sibling RFC. Its goal is to supply that capability.

### Goals

- Specify the SLO artifact format (OpenSLO v1).
- Specify the minimum required SLO document fields and the error_budget_policy block.
- Define the four-state PRR field resolution protocol.
- Home the `define-slo` skill in the `release-engineering` pack.
- Acknowledge the live budget consumption integration gap and specify the query-at-gate
  instruction + `query-failed` state.

---

## Evidence

### SLO specification format landscape

Four formats have meaningful adoption:

| Format | Governance | Backend | Minimum schema |
|---|---|---|---|
| OpenSLO v1 (`openslo/v1`) | Cross-vendor (Nobl9, Dynatrace, community) | Backend-agnostic (DataSource object) | apiVersion, kind, metadata.name, spec.indicator, spec.objectives[].target |
| Sloth `prometheus/v1` | Open-source (slok/sloth) | Prometheus only | service, objective (%), sli.events.errorQuery, sli.events.totalQuery |
| Pyrra `pyrra.dev/v1alpha1` | Open-source (Kubernetes-only CRD) | Prometheus + Kubernetes | spec.target, spec.window, spec.indicator.ratio |
| Nobl9 `n9/v1alpha` | Proprietary SaaS | Nobl9 only | metadata.project, spec.service, spec.indicator.metricSource.name |

Sloth can consume OpenSLO YAML directly — the format choice does not preclude Sloth
adoption. Pyrra requires a Kubernetes cluster; it is not harness-neutral. OpenSLO is the
only format designed for cross-vendor interchange.

### OpenSLO v1 minimum schema (D1/D2 worked example)

```yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: <service>-availability   # RFC1123; e.g. "payments-availability"
  displayName: "<Service> Availability"
spec:
  service: <service>
  description: "HTTP availability SLO for the <service> API surface."
  budgetingMethod: Occurrences   # Occurrences (event-based, default) | Timeslices
  timeWindow:
    - count: 30
      unit: Day
      isRolling: true             # rolling 30-day window (default)
  indicator:
    apiVersion: openslo/v1
    kind: SLI
    metadata:
      name: <service>-availability-sli
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus      # adopter fills in backend type and query
            spec:
              query: >
                sum(rate(http_requests_total{job="<service>",code!~"5.."}[{{.window}}]))
        total:
          metricSource:
            type: Prometheus
            spec:
              query: >
                sum(rate(http_requests_total{job="<service>"}[{{.window}}]))
  objectives:
    - target: 0.999              # 99.9% — adopter sets; no default enforced
      displayName: "99.9% availability"

# error_budget_policy is an extension block (not part of OpenSLO core spec).
# Carried alongside the SLO document — either as a separate sidecar YAML or
# as a non-spec field the skill appends. The gate reads this block.
error_budget_policy:
  trailing_window: 30d
  halt_at: "100%"               # budget exhausted: block releases, surface to human
  warn_at: "25%_remaining"      # <25% remaining: surface warning in PRR (non-blocking)
  postmortem_at: "20%_per_incident"  # single incident consuming >20%: mandatory postmortem
```

The `metricSource.type` and query expressions are the adopter's backend-specific
contribution; the skill scaffolds the template and marks these fields as
`# TODO: fill in for <backend>`.

### Error budget field derivation

```
error_budget_pct  = 1 - objectives[0].target
                  = 1 - 0.999 = 0.001 (0.1%)

budget_minutes    = error_budget_pct × window_minutes
                  = 0.001 × 43,200 = 43.2 minutes (for 30-day window)

budget_consumed_pct = (observed_bad_events / total_events) / error_budget_pct
                    -- computed by the gate's trailing-window telemetry query
```

### Four-state resolution mapping (D3)

| Field value | Condition | Action |
|---|---|---|
| `not-defined` | No `slos/<service>.yaml` found | Record and surface as visible absence; non-blocking but flagged |
| `within-budget` | `budget_consumed_pct` < (100% − warn_at threshold) | Pass; include burn rate in PRR |
| `warning: <N>% remaining` | `budget_consumed_pct` ≥ warn_at but < 100% | Surface warning in PRR; human sees it; not a hard block unless adopter tightens |
| `exhausted: halt-releases` | `budget_consumed_pct` = 100% | Block release; surface to human as a blocking item in the G5 consent gate |
| `query-failed` | Telemetry backend unreachable at gate-check time (D5) | Surface to human; non-blocking by default (the SLO document exists; only the live read failed) |

The `warn_at` and `halt_at` thresholds are read from the SLO document's
`error_budget_policy` block. If the block is absent from the SLO document, the gate
uses the defaults above (halt at 100%, warn below 25% remaining). This is Google's
published policy; adopters who need tighter thresholds (e.g., halt at 50% for
safety-critical services) override the block.

### Error budget policy — Google SRE Workbook alignment

Google's four-threshold error-budget policy:
1. Single incident consuming > 20% of the four-week budget → mandatory postmortem.
2. Budget exhausted in trailing 30 days → block releases; focus on reliability.
3. Budget exhausted, root cause unknown → escalate SRE support.
4. Budget exhausted in trailing 90 days, root cause unknown → executive escalation.

This RFC adopts thresholds 1 and 2 as the skill's defaults. Thresholds 3 and 4 require
human-and-process escalation beyond the scope of a pre-prod release loop; they belong to
the future operate/incident loop.

### OpenSLO toolchain translation gap

Sloth consumes OpenSLO directly and generates Prometheus multiwindow multi-burn-rate
alerting rules from it (fast-burn 14.4× / slow-burn 1× / ticket-level 1× over three
windows — Google Table 5-8). Pyrra uses a Kubernetes CRD; adopters using Pyrra author a
Pyrra CRD in addition to the OpenSLO document, or replace it. This is an explicit
trade-off the implementing spec should note: the skill produces the harness-neutral
declaration; toolchain-side rule generation is outside the skill's scope.

---

## Drawbacks

- **OpenSLO toolchain fragmentation.** Sloth, Pyrra, and Nobl9 each have their own native
  schemas; OpenSLO requires a translation step for Pyrra adopters and adds a dependency on
  Sloth's OpenSLO import path. Mitigated by Sloth's native OpenSLO support and the explicit
  "adopter translation shim for Pyrra" note in the skill.
- **Live budget consumption requires a telemetry query at gate time.** The PRR gate's
  `budget_consumed_pct` cannot be filled statically. The query-at-gate instruction
  is concrete but depends on the release-lead agent being able to reach the telemetry
  backend, which may not be available in all environments. Mitigated by the `query-failed`
  state (surfaces, does not hard-block) and the explicit integration gap acknowledgment.
- **Metric query accuracy is adopter-dependent.** The skill scaffolds placeholder queries;
  the adopter fills in correct PromQL / backend-specific expressions. An incorrect query
  produces an incorrect budget read without a detectable error. Mitigated by the skill
  including a validation step: execute the query against the backend once at SLO authoring
  time and confirm it returns a result within the expected range.
- **Single objective per SLO document (simplification).** OpenSLO supports multiple
  objectives per SLO; the PRR gate reads `objectives[0].target`. Adopters with multiple
  SLO tiers (e.g., 99.9% availability + 99.5% latency) must author separate SLO documents.
  This is a simplification for v1; a follow-on can extend the gate to read multiple
  objectives.

## Follow-on artifacts

On acceptance:
- **New skill:** `packs/release-engineering/.apm/skills/define-slo/SKILL.md` — the
  `define-slo` skill per D1–D5.
- **Skill update:** `packs/release-engineering/.apm/skills/release-loop/SKILL.md` —
  replace the `error-budget: not-defined` placeholder paragraph in the release-readiness
  gate section with the four-state resolution protocol.
- **Spec update:** `docs/specs/release-loop/spec.md` — add a cross-reference note to
  AC6b pointing to this RFC as the source of the SLO schema and the PRR field resolution
  states; no AC text changes.
- **Pack version bump:** `packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json` — minor version bump.
- **Changelog:** `docs/product/changelog.md` — `[Unreleased]` entry.
- **Future:** Ongoing error-budget monitoring, alerting backend wiring, and on-call
  ownership are the operate/incident loop's scope — a future sibling RFC to RFC-0049.
