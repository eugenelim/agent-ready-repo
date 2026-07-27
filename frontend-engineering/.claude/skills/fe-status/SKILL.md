---
name: fe-status
description: Orient skill — read the current surface's evidence manifest, known exceptions, and gate history to return a surface-state summary against the frontend engineering quality floor.
---

# Skill: fe-status

Load this skill before starting work on an **existing surface** to orient
without reading all the code. It reads the surface's evidence manifest, known
exceptions list, and recent gate run results to return a concise state
summary. Do not load it for new surfaces that have no prior gate history;
use `frontend-engineering` in `create` mode instead.

---

## What to look for

Read the following artifacts in the order listed. Stop when the summary
is complete — this skill reads, it does not write.

**1. Evidence manifest** — the 11-field record from the most recent
`frontend-engineering` gate run. If a manifest exists, locate:

- `states`: which of the 18 states were tested in the last run
- `a11y result`: the last pa11y/axe-core output plus manual-check outcomes
  for WCAG 2.4.11 and 2.5.8
- `perf result`: the last Lighthouse/CWV measurement
- `known exceptions`: documented, accepted gaps with owners
- `unverified items`: items that could not be verified in the last session

**2. Known exceptions list** — entries in the manifest's `known exceptions`
field. Note: which exceptions have an owner and a planned resolution date,
and which are undated (stale).

**3. Most recent gate run** — the last recorded run of the four GATES steps:
HTML validation, a11y audit, CSS token enforcement, and visual QA checklist.
Note which steps passed, which failed, and which were skipped.

**4. Open TODOs** — grep the HTML/CSS for `TODO`, `FIXME`, or `HACK` comments
in the surface's source files. These are informal a11y, token, or state-coverage
gaps that were deferred without being recorded in the manifest.

---

## Output format

Return a structured summary with the following sections:

```
## Surface state — <surface name or route>

**Evidence manifest:** [present / absent — last run: <date if known>]

**States covered:** [list from the 18-state matrix]
**States missing:** [states in the matrix that were not tested or are not implemented]

**A11y gate:** [pass / fail / untested]
  - axe-core wcag21aa: [pass/fail/untested]
  - manual 2.4.11 Focus Appearance: [pass/fail/untested]
  - manual 2.5.8 Target Size Minimum: [pass/fail/untested]

**CWV status:** [pass / fail / untested — LCP: <value>, INP: <value>, CLS: <value>]

**Token compliance:** [pass / fail / untested]

**Known exceptions:** [count] — [list summaries with owner/date if present]

**Open TODOs:** [count] — [brief description of each if ≤3; count only if >3]

**Next recommended action:** [one sentence — the highest-priority action before new work starts]
```

---

## When no manifest exists

If the surface has no evidence manifest, output:

```
## Surface state — <surface name>

**Evidence manifest:** absent — no gate history found.

No prior gate run exists for this surface. Before starting new work, run
`frontend-engineering` in `audit` mode to establish a baseline:
- State matrix coverage
- A11y gate (pa11y/axe-core + 2 manual checks)
- CSS token compliance grep
- CWV measurement

Record the audit output as the initial evidence manifest.
```

Do not estimate or infer the surface's state from the code alone. The
evidence manifest is the only ground truth for gate history; its absence
means the surface's compliance status is unknown.
