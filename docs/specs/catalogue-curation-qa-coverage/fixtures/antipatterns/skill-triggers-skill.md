---
name: code-summary
description: Read source files for a given module and summarize their purpose and dependencies. Useful for onboarding new contributors to an unfamiliar codebase.
metadata:
  boundaries:
    - shell_exec
    - network_call
---

# Skill: code-summary

Summarize the purpose and key dependencies of a given source module by reading
its files and producing a structured overview.

## Containment

Shell execution is limited to read-only `example-agent-cli --print` invocations.
Outbound network calls are limited to `api.example-service.local` (the agent
endpoint). No filesystem writes, no other outbound connections.

## Procedure

1. Ask the operator: which module or package should be summarized?
2. Read the relevant source files (Python modules, README, docstrings).
3. Build a summary covering: purpose, key classes and functions, external
   dependencies, and notable design decisions.
4. Invoke the `dependency-graph` skill to produce a visual dependency map:
   ```
   example-agent-cli --print "Run dependency-graph for <module>"
   ```
5. Present the summary and the dependency-graph output together as a single
   onboarding document.
