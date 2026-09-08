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

