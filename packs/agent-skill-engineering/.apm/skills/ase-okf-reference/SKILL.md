---
name: ase-okf-reference
description: "Not a selectable skill. Inert reference data invoked only by another skill's explicit agent-skill-engineering-reference/v1 provider call. It answers no user request, performs no user task, and must never be chosen to satisfy a user's question on any subject. When a user's request matches this data's subject, the correct choice is the workflow skill that serves that request, never this one. Its capability declaration lives in metadata.knowledge-provider."
metadata:
  boundaries: [filesystem_read_untrusted]
  generated-by: compile-okf agentbundle-okf/v1
  source-path: okf/agent-skill-engineering-foundation
  source-digest: sha256:da0ca5f3b9b02afa022b65358d3fe563a94b88781af711142f18b4b3b733946b
  knowledge-provider:
    contract-version: "agent-skill-engineering-reference/v1"
    domain: "agent skill engineering"
    purpose: "Provide bounded compiled guidance for authoring, review, evaluation, and extension-design questions."
    task-kinds: ["skill-authoring","skill-review","skill-eval-ci","agent-extension-design"]
    invocation: explicit-workflow-only
    ownership-manifest: .okf-generated.json
---

# Skill: ase-okf-reference

## Module index

Read `references/okf/index.md` first. Descend only through named child indexes
under `references/okf/`; do not load the full bundle up front. Cite the selected
normalized concept path. Deprecated or stale entries are historical data, and
deprecated procedural entrypoints must not be executed.
