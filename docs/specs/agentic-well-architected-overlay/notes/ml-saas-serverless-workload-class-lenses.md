# Workload-class lens claim correction

## Confirmed outcome

On 2026-09-08, the maintainer chose to remove the unsupported SaaS lens claim
instead of inventing a SaaS corpus. This packet is ready for a future
implementation work-loop; it does not change the published pack itself.

## Required change

In
`packs/architect/.apm/skills/architect-review/references/rubric-well-architected.md`:

- remove `SaaS` from the workload-class lens enumeration;
- remove the sentence that says SaaS lacks a dedicated corpus concept; and
- preserve the existing GenAI/agentic, data/ML, and serverless routes.

Do not add a SaaS reference document or open an RFC solely to preserve the
legacy four-lens wording. Data/ML already routes to
`data-analytics-and-ml.md`, and serverless already routes to `serverless.md`.

## Verification

- The rubric's workload-class selection text makes no SaaS lens claim.
- The GenAI/agentic, data/ML, and serverless links still resolve.
- The relevant pack verification and repository build checks pass.

## The rubric edit is not sufficient on its own

Read this before treating the change above as a chore. The edit is two lines,
but landing it alone leaves a Shipped spec asserting a state the shipped pack
contradicts.

`docs/specs/architect-platform-grounding/spec.md:77` is a **ticked** criterion
on a spec whose Status is `Shipped`. It reads "ML / SaaS remain
named-but-unbacked; serverless is marked resolved", and its body asserts that
`rubric-well-architected.md` "still names ML and SaaS as workload-class lenses
without backing files". It records that as a *met* criterion of its own pull
request, not as a deferral. Removing SaaS falsifies it, and so does renaming
`ML` to `data/ML`.

ADR-0032 and ADR-0035, both Accepted, likewise record ML and SaaS as
named-but-unbacked. ADR-0032 says its decision "neither backs nor removes
them", so the removal sits outside what either ADR settled rather than being
forbidden by them.

**Unblocks when** an erratum against that ticked criterion, or a superseding
ADR, carries the removal. That is a governed amendment with an owner, not
register hygiene, and it is why the `[backlog].open` entry for this note stays
open.

