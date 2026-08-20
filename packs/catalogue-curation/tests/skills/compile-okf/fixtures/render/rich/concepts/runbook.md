---
id: runbook
title: Reviewed Runbook
type: Playbook
status: Active
license: CC-BY-4.0
compatibility: okf-0.2
boundaries:
  - filesystem_read_untrusted
x-agentbundle:
  profile: agentbundle-okf/v1
  skill:
    name: reviewed-runbook
    description: Use when a reviewed runbook should guide an operator.
    instruction-section: Procedure
    include:
      - guides/include.md
unknown-extension:
  preserved: true
---
# Reviewed Runbook

Introductory data that must not be projected.

## Procedure

1. Inspect the request.
2. Cite `concepts/runbook.md`.

### Detail

Keep this nested heading.

## Appendix

Do not include this section.
