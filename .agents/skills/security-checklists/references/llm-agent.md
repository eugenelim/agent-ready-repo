# llm-agent — prompts, tool exposure, MCP, model output

> **Loaded when:** the change constructs prompts, exposes tools/functions to a
> model, runs an MCP server/client, sandboxes agent actions, or consumes model
> output.
> **Standards:** OWASP Top 10 for LLM Applications:2025 (LLM01 Prompt
> Injection, LLM02 Sensitive Information Disclosure, LLM05 Improper Output
> Handling, LLM06 Excessive Agency, LLM03 Supply Chain, LLM10 Unbounded
> Consumption) · ASVS 5.0 (input/output validation principles applied to model
> I/O).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is an **instruction-vs-data boundary and a
least-privilege tool surface** — the spec should name how untrusted content is
isolated in the prompt, which tools the model can call, and which actions
require a human confirmation step. "The agent can take actions" with no tool
allowlist or confirmation criteria is the design-time miss.

## Implementation checks

- `reason` **Prompt injection (LLM01).** Untrusted content (user input,
  fetched pages, retrieved docs, tool output) flowing into the prompt without
  an instruction-vs-data boundary. Confirm untrusted content is delimited and
  the system prompt instructs the model not to treat it as instructions.
- `reason` **Excessive agency (LLM06).** Tools exposed to the model must be
  least-privilege; high-impact/mutating actions (delete, pay, send) need a
  confirmation step or a scoped credential, not unattended execution.
- `reason` **Improper output handling (LLM05).** Model output used as code,
  SQL, shell, HTML, or a file path without validation/escaping is injection
  with the model as the source — treat model output as untrusted input to the
  next sink.
- `reason` **Sensitive information disclosure (LLM02).** Secrets, system
  prompts, or other users' data reachable through model output; confirm the
  model isn't handed more context than the caller is entitled to.
- `reason` **Unbounded consumption (LLM10).** A user-triggered model call with
  no token/request/cost cap is a denial-of-wallet and DoS vector.
- `tool` **Model/MCP supply chain (LLM03).** Model weights, embeddings, or MCP
  servers loaded from unverified sources — pinning/provenance is partly
  tooling; confirm the source is trusted, and if no integrity check exists flag
  the gap.

## Established-helper bypass

Resolve the repo's sanctioned prompt-construction / content-isolation helper
and its tool-registration layer (where the allowlist and confirmation gating
live), and flag a change that concatenates untrusted content into a prompt
directly or registers a tool outside the blessed path — the helper is where
the instruction-vs-data boundary and least-privilege tool surface are enforced
once.
