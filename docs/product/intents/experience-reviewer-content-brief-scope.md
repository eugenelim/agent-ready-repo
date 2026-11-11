# Extend experience-reviewer to review content briefs

- **Slug:** `experience-reviewer-content-brief-scope`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [RFC-0062 OQ1](../../rfc/0062-content-design-and-copy-direction-skills.md)

## Outcome

`experience-reviewer` reviews the content briefs produced by `content-design`.

## Opportunity

`experience-reviewer` does not yet review the content briefs produced by `content-design`.

## What this absorbs

### experience-reviewer-content-brief-scope

RFC-0062 OQ1 records a follow-on: extend `experience-reviewer` to include content briefs (`type: content-brief`) as a reviewable artifact type. RFC-0062's `content-design` skill produces that artifact. The recorded fix is a follow-on RFC extending RFC-0062 to add `content-brief` to the `experience-reviewer` reviewable-artifact set. The RFC-0062 `content-design-skill` spec is Shipped, so this item is actionable.

Unblocks when: the follow-on RFC extends the reviewable-artifact set.

## Assumptions

- The shipped `content-design-skill` makes this reviewer-scope follow-on actionable.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 768c0a90b87e635220c3c784d7cdae67644d7e1d

## Readiness

Route: direct-light, one small session; no follow-on RFC is needed for a reviewer-scope edit. Change: add `type: content-brief` (and the brand-register document type the `content-design` skill also defers) to the reviewable set in `experience-reviewer.md`, remove the two "deferred to a follow-on" notes in `content-design`, add one eval case, bump `experience-design`. Agent-only proof: the eval case passes and the pack tests pass. Checked 2026-11-05: the agent says line 81 it does not review content briefs, and `content-design` names this as the hand-off point. Land it before `xd-state-reviewer-doctrine`, which edits the same agent file.

## Outcome note

End state: a content brief produced by `content-design` receives an experience review like any other design artifact.

## Non-goals

- Reviewing code, or architecture documents.
- Rewriting content briefs; the reviewer flags only.
- A follow-on RFC; this is a reviewer-scope edit.

**Riskiest assumption:** adding the content-brief type does not make the marketing-clarity lens fire on briefs. Tested agent-only by an eval case with a content brief that must not trigger that lens.
