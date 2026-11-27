# Ml saas serverless workload class lenses

- **Status:** Open
- **Kind:** defect
- **Detail:** packs/architect/.apm/skills/architect-review/references/rubric-well-architected.md

## Summary

Remove the unsupported SaaS workload-lens claim while preserving the backed GenAI, data and ML, and serverless routes


## Decision and remaining work

The maintainer chose on 2026-09-08 to remove the unsupported SaaS lens claim,
rather than invent a SaaS corpus. Remove SaaS from the workload-class enumeration
and its lack-of-corpus sentence; preserve GenAI/agentic, data/ML and serverless.
Check those links and the relevant pack/build gates. This item remains Open;
the rubric change has not been implemented by this retirement.

The original packet required a governed erratum or superseding decision because
the shipped platform-grounding acceptance criterion explicitly recorded the
named-but-unbacked state. ADR-0032 and ADR-0035 record that historical state but
neither authorizes nor forbids removal. Retiring the delivery files does not
settle that governance choice. The current rubric owns the published behavior;
this captured item owns the pending correction and its decision boundary.

Original decision and verification packet: [immutable record](https://github.com/eugenelim/agent-ready-repo/blob/7bdd03da0a93a35883ef1d32a121ec361b99211d/docs/specs/agentic-well-architected-overlay/notes/ml-saas-serverless-workload-class-lenses.md).
