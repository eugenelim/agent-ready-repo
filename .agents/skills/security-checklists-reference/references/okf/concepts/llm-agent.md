---
title: "llm-agent"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# llm-agent

Use when the change alters a prompt trust boundary, model/tool authority,
permissions, MCP, sandboxing, agent delegation, persisted memory, or
model-output/data handling. Ordinary prompt wording with none of those effects
does not load this module.

## Spec-stage

Require an instruction-vs-data boundary, least-privilege tool surface, human
confirmation for high-impact actions, and explicit containment for agentic
systems that act, delegate, or persist state.

## Implementation checks

- `reason` Delimit untrusted content and instruct the model not to obey it.
- `reason` Scope tools and require confirmation for high-impact mutations.
- `reason` Treat model output as untrusted input to downstream sinks.
- `reason` Avoid exposing secrets or unauthorized context to the model.
- `reason` Bound tokens, requests, and cost.
- `tool` Confirm model/MCP supply-chain provenance.
- `reason` Check execution isolation, delegated identity, and memory integrity.

## Established-helper bypass

Resolve the sanctioned prompt-construction and tool-registration helpers and
flag direct prompt concatenation or out-of-band tool registration.
