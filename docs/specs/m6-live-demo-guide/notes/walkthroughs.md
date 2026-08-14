# Cold walkthroughs: m6-live-demo-guide

- **Date:** 2026-08-13
- **Facilitator:** cold quality reviewer; not the guide author
- **Fixture:** isolated disposable repository under `/private/tmp`
- **Decision posture:** typed facilitator verdicts were simulated for
  construction QA and are identified below
- **Shared-repository mutation:** none during the walkthroughs

These records test whether a cold facilitator can follow the authored guide
without inventing pack routing, decision points, artifacts, or proof. The temp
fixture contained generic, sanitized repository sources only. It contained no
credentials, personal information, production data, external integrations, or
`workspace.toml`.

## Technical — Core direct `new-spec`

**Opening request**

```text
Use Core's new-spec skill on missing rendered-link proof in onboarding. Read
only AGENTS.md, docs/CONVENTIONS.md, docs/architecture/overview.md,
guides/core/how-to/onboard-to-demo-repo.md, tools/link_check.py. Surface and
verify assumptions, then draft one spec/plan pair at
docs/specs/demo-doc-link-proof/. Do not create a brief, implement, approve,
register work, or change an external system.
```

| Beat | Observed time |
| --- | ---: |
| Pre-flight | 3:10 |
| Enter | 5:40 |
| Shape or cut | 4:25 |
| Draft delivery handoff | 6:55 |
| Receipt | 2:20 |
| **Total** | **22:30** |

- **Evidence:** `guides/core/how-to/onboard-to-demo-repo.md`,
  `tools/link_check.py`, and `docs/architecture/overview.md`.
- **Human decision:** simulated typed verdict—baseline recognizable and
  feature-sized; success command trusted.
- **Artifacts:** `docs/specs/demo-doc-link-proof/spec.md` (`Draft`) and
  `docs/specs/demo-doc-link-proof/plan.md` (`Draft`).
- **Provenance:** no brief; the source guide and verification command are cited
  directly.
- **Proof:** `python3 tools/link_check.py --build-dir build` exited successfully
  against the fixture. The final independent re-run also exited successfully.
- **Safe-stop probe:** a missing baseline stops before `new-spec`; the guide
  required no invented recovery instruction.
- **Recipient:** `Example Engineer`.
- **Mutation statement:** No external systems changed; no work-intake
  registration; no implementation.

**Completion receipt**

```text
Outcome: Success
Track: Technical
Packs and scopes used: Core at repo scope
Skills invoked: new-spec
Changed paths and statuses: docs/specs/demo-doc-link-proof/spec.md — Draft; docs/specs/demo-doc-link-proof/plan.md — Draft
Provenance links: no brief; source guide and verification command cited directly by the Draft spec
Verified proof: python3 tools/link_check.py --build-dir build exited successfully twice
Unresolved or unverified items: Draft pair awaits formal review; no demo proof gaps
Human decisions recorded: problem is recognizable and feature-sized; success command is trusted
Formal spec approval fired: no
Formal plan approval fired: no
Implementation started: no
Work-intake registration performed: no
External systems changed: no
Next reviewer and action: Example Engineer reviews accuracy and circulation readiness
Share recipient: Example Engineer
Elapsed time: 22:30
```

## Enterprise — Core `receive-brief` to `new-spec`

**Opening request**

```text
Use Core's receive-brief skill on
docs/product/briefs/demo-governed-doc-pilot.md. Confirm its load-bearing fields,
propose independently shippable slices, and wait for the domain owner to choose
the first slice. Mark the brief Ready only if its gate passes, then use
new-spec for that slice. Do not implement, approve, register work, edit
workspace.toml, or change an external system.
```

| Beat | Observed time |
| --- | ---: |
| Pre-flight | 3:30 |
| Enter | 6:20 |
| Shape or cut | 5:10 |
| Draft delivery handoff | 7:50 |
| Receipt | 3:05 |
| **Total** | **25:55** |

- **Evidence:** `docs/product/briefs/demo-governed-doc-pilot.md`,
  `docs/policies/pilot-control.md`, and `docs/architecture/overview.md`.
- **Human decision:** simulated typed verdict—selected
  `rendered-link-proof-prompt`; accepted the Ready gate only after Outcome,
  Appetite, a Rabbit hole, and the Spec map row were visible.
- **Artifacts:** `docs/product/briefs/demo-governed-doc-pilot.md` (`Ready`),
  `docs/specs/demo-rendered-link-pilot/spec.md` (`Draft`), and
  `docs/specs/demo-rendered-link-pilot/plan.md` (`Draft`).
- **Provenance:** policy/control source → Ready brief → selected slice → Draft
  spec backlink.
- **Proof:** the policy/control claim traces to AC1 and plan T1; a residual-risk
  recipient is named.
- **Safe-stop probe:** a missing policy owner stops before `Ready`; the guide
  supplied the stop condition.
- **Recipient:** `Example Risk Reviewer`.
- **Mutation statement:** No external systems changed; no `workspace.toml`
  write; no implementation.

**Completion receipt**

```text
Outcome: Success
Track: Enterprise
Packs and scopes used: Core at repo scope
Skills invoked: receive-brief, new-spec
Changed paths and statuses: docs/product/briefs/demo-governed-doc-pilot.md — Ready; docs/specs/demo-rendered-link-pilot/spec.md — Draft; docs/specs/demo-rendered-link-pilot/plan.md — Draft
Provenance links: policy/control source to Ready brief to selected slice to Draft spec backlink
Verified proof: policy claim traces to AC1 and plan T1; residual-risk recipient is named
Unresolved or unverified items: mid-market path remains uncharacterized; Draft pair awaits formal review
Human decisions recorded: selected rendered-link-proof-prompt and accepted the completed Ready gate
Formal spec approval fired: no
Formal plan approval fired: no
Implementation started: no
Work-intake registration performed: no
External systems changed: no
Next reviewer and action: Example Risk Reviewer checks control accuracy and circulation readiness
Share recipient: Example Risk Reviewer
Elapsed time: 25:55
```

## Non-technical — Product Engineering into Core

**Opening request**

```text
Use user-scoped Product Engineering to frame onboarding proof confusion at
feature level and app scale from guides/core/how-to/onboard-to-demo-repo.md and
sanitized observations. Pause at G0 for my framing decision, test the one
riskiest assumption against a predeclared kill condition, and project the
surviving intent to one Core brief. Then use repo-scoped Core to receive that
brief and draft one spec/plan pair. Do not decide user meaning or craft quality
for me; do not implement, approve, register work, or change an external system.
```

| Beat | Observed time |
| --- | ---: |
| Pre-flight | 3:45 |
| Enter | 6:50 |
| Shape or cut | 5:55 |
| Draft delivery handoff | 8:35 |
| Receipt | 3:20 |
| **Total** | **28:25** |

- **Evidence:** `guides/core/how-to/onboard-to-demo-repo.md`, its sanitized
  observations, `docs/CONVENTIONS.md`, and repo-root
  `agentbundle-layout.toml` with `[product] output_dir = "docs/product"`.
- **Resolved Product Engineering output:**
  `/private/tmp/m6-live-demo-guide-cold-qa-20260813/demo-repo/docs/product`,
  verified to remain inside the disposable fixture repository. No user-home
  layout file was read, created, or edited.
- **Human decision:** simulated typed verdict—G0 approved with the participant
  correction from “quality gate” to “review evidence”; the kill condition was
  accepted; the assumption survived for the demo but remains `to-validate`.
- **Artifacts:** `docs/product/intents/demo-onboarding-proof-intent.md`
  (`Draft`), `docs/product/briefs/demo-onboarding-proof-brief.md` (`Ready`),
  `docs/specs/demo-onboarding-review-evidence/spec.md` (`Draft`), and
  `docs/specs/demo-onboarding-review-evidence/plan.md` (`Draft`).
- **Ready gate:** the brief visibly contains Outcome, Appetite, at least one
  Rabbit hole, and a Spec map row before its status changes to `Ready`.
- **Provenance:** source guide → corrected intent → Ready Core brief → Draft
  spec with brief and discovery links.
- **Proof:** “review evidence” propagates from the participant correction into
  the intent and spec; the unresolved validation hook remains visible.
- **Safe-stop probe:** a killed assumption stops before decomposition; the guide
  supplied the stop condition.
- **Recipient:** `Example Product Owner`.
- **Mutation statement:** No external systems changed; no work-intake
  registration; no implementation.

**Completion receipt**

```text
Outcome: Success
Track: Non-technical
Packs and scopes used: Product Engineering at user scope, then Core at repo scope
Skills invoked: frame-intent, de-risk-intent, decompose-intent, receive-brief, new-spec
Changed paths and statuses: docs/product/intents/demo-onboarding-proof-intent.md — Draft; docs/product/briefs/demo-onboarding-proof-brief.md — Ready; docs/specs/demo-onboarding-review-evidence/spec.md — Draft; docs/specs/demo-onboarding-review-evidence/plan.md — Draft
Provenance links: source guide to corrected intent to Ready Core brief to Draft spec and plan
Verified proof: participant correction propagates through the intent and spec; validation hook remains visible
Unresolved or unverified items: surviving assumption remains to-validate; Draft pair awaits formal review
Human decisions recorded: G0 framing, kill condition, survive verdict, participant wording, and Core slice cut
Formal spec approval fired: no
Formal plan approval fired: no
Implementation started: no
Work-intake registration performed: no
External systems changed: no
Next reviewer and action: Example Product Owner checks meaning, authorship, and circulation readiness
Share recipient: Example Product Owner
Elapsed time: 28:25
```

**Corrective layout revalidation (2026-08-14):** after review made the existing
repo-scoped layout an explicit prerequisite, the cold facilitator added only
the fixture's repo-root layout file and reran pre-flight/output resolution. The
rerun observed Pre-flight 3:40, Enter 2:20, Shape or cut 2:15, Draft delivery
handoff 2:10, and Receipt 1:20 (11:45 total). It verified path containment and
then rechecked the unchanged downstream artifacts: the intent remained Draft
with its G0 verdict, participant correction, kill condition, validation hook,
and `to-validate` marker; the brief remained Ready with all four gate fields;
and the spec/plan remained Draft with brief/discovery provenance. No user-home
layout write occurred. Verdict: **Clean — ready to record.**

## Result

All three canonical paths reached one Draft spec/plan pair inside the 30-minute
limit and preserved their own decision model. The non-technical path was the
tightest at 28:25, so the guide's feature-level/app-scale constraint is
load-bearing. No facilitator invention, unsupported claim, or blocker was
observed. Cold quality verdict: **Clean — ready to record.**
