# Project-knowledge engineering and operational integrations

- **Status:** Draft
- **Level:** capability

## Outcome

Engineering and operational workflows use the portable project-knowledge
lifecycle at explicit semantic gates without turning logs, telemetry,
incidents, build output, or transient execution state into ambient memory.

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

- Identify the bounded engineering and operational workflow families whose
  terminal products can produce independently reusable practice.
- Define exact capture, distillation, enquiry, unavailable, and non-gate
  behavior before authoring a delivery spec.
- Preserve existing project-knowledge schemas and public/private boundaries
  unless evidence justifies a separately reviewed contract change.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0077-distill-knowledge.md
- Revision: sha256-bytes-v1:94de8754c752838d99562a6b5bbcfbaf64ed688072d0e26149063f5fbac81016
