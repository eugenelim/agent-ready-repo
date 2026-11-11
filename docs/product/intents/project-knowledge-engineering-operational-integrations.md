# Project-knowledge engineering and operational integrations

- **Slug:** `project-knowledge-engineering-operational-integrations`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** capability
- **Owner:** eugenelim
- **Depends on:** spec:project-knowledge-research-integrations

## Outcome

The project-knowledge lifecycle's shipped gates and the delivery-failure candidates mode are checked against engineering and operational workflows, and each workflow family that qualifies gets its own spec; families that do not qualify are recorded as closed. Logs, telemetry, incidents, build output and transient execution state never become ambient memory.

## Opportunity

RFC-0077 establishes the repository-first lifecycle and the authoring, review,
and research slices prove its public seams. Engineering and operational
workflows remain the final integration class needed before adoption can be
evaluated across the whole portable lifecycle.

## Assumptions

- Research integration is the shipped prerequisite for this shaping work.
- Each producer retains authority over its own operational evidence, failure
  judgment, and remediation decision.
- External storage, cross-project memory, and automatic transcript or log
  mining remain outside this effort.

## Decomposition

- **Survey (this intent's first session):** name each bounded engineering and operational workflow family (bug fix, close-work, work-loop gates, incident-style work), its terminal product, and whether that product is independently reusable practice, citing a file for each.
- **Closing non-qualifying families:** record each family that does not qualify as closed, with the survey evidence, in this intent.
- **Per-family specs:** each qualifying family becomes one child spec defining exact capture, distillation, enquiry, unavailable and non-gate behavior. Those specs do not exist yet; the survey names them. If fewer than two qualify, this intent is withdrawn with the survey as evidence.

Constraint, not a member: logs, telemetry, incidents, build output and transient execution state never become ambient memory, and existing project-knowledge schemas and public/private boundaries stay unless a separately reviewed contract change justifies otherwise.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0077-distill-knowledge.md
- Revision: sha256-bytes-v1:94de8754c752838d99562a6b5bbcfbaf64ed688072d0e26149063f5fbac81016

## Readiness

Route: direct-light survey, one short session, then close or spec. Survey the engineering and operational workflows (bug fix, close-work, work-loop gates, incident-style work) for terminal products that give independently reusable practice, with "none qualify" an allowed result. If fewer than two qualify, withdraw this intent with that evidence; the delivery-failure candidates mode already covers the common case. If two or more qualify, write one spec per family. Agent-only proof: the survey names each workflow's terminal product and cites its file. The shipped prerequisite `project-knowledge-research-integrations` is met.

## Unowned part

No child intent covers engineering and operational workflows using the lifecycle yet. The first survey session decides whether any workflow family qualifies; if none does, this intent is withdrawn with that evidence.

**Riskiest assumption:** at least two engineering or operational workflows end in a product that is independently reusable practice. Tested agent-only by the survey, which names each workflow's terminal product with a file citation and allows a "none qualify" result.

## Non-goals

- External storage, cross-project memory, and automatic transcript or log mining.
- Changing the project-knowledge schemas or the public and private boundaries without a separately reviewed contract change.
- Delivering any family's integration in this intent; each qualifying family becomes its own child spec after the survey.
