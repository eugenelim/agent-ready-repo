# llm-agent — prompts, tool exposure, MCP, model output

> **Loaded when:** the change constructs prompts, exposes tools/functions to a
> model, runs an MCP server/client, sandboxes agent actions, or consumes model
> output.
> **Standards:** OWASP Top 10 for LLM Applications:2025 (LLM01 Prompt
> Injection, LLM02 Sensitive Information Disclosure, LLM04 Data & Model
> Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM03
> Supply Chain, LLM10 Unbounded Consumption) · OWASP Top 10 for Agentic
> Applications:2026 (ASI02 Tool Misuse & Exploitation, ASI03 Agent Identity &
> Privilege Abuse, ASI05 Unexpected Code Execution, ASI06 Memory & Context
> Poisoning) — the agentic surface, for systems that act, delegate, or persist
> state · ASVS 5.0 (input/output validation principles applied to model I/O).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is an **instruction-vs-data boundary and a
least-privilege tool surface** — the spec should name how untrusted content is
isolated in the prompt, which tools the model can call, and which actions
require a human confirmation step. "The agent can take actions" with no tool
allowlist or confirmation criteria is the design-time miss.

For an **agentic** system that acts, delegates, or persists state, the
design-time control additionally names three boundaries: the
**execution-isolation posture** for any code-running or untrusted-content tool
(containment — what a call can reach once made — not just authorization); how
**identity and privilege propagate** across a delegation chain (a sub-agent must
not inherit more authority than the spawning request should carry); and the
**memory-integrity** gate (what is trust-checked before it is persisted into
agent memory or a vector store). A design that runs code, delegates to
sub-agents, or persists memory without these named is the agentic design-time
miss.

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

The next three checks are the **agentic surface** — they apply once the system
acts, delegates, or persists state (a plain prompt-in/text-out call trips none of
them):

- `reason` **Execution isolation & blast radius (Agentic ASI02 / ASI05).** A
  tool that runs code or processes untrusted content must be *contained* — this
  is distinct from being *authorized* (LLM06): authorization is who may call;
  containment is what a call can reach once made. Verify the three confinement
  axes: **filesystem scope** (which paths the tool can read/write), **network
  egress** (whether the sandbox can reach internal services or the
  cloud-metadata endpoint — this facet is `hybrid`: a scanner can find the egress
  flow, you judge whether the confinement is correct; see `outbound-ssrf`), and
  **resource/time caps** (CPU / memory / wall-clock). A code-execution tool with
  unbounded blast radius is the finding.
- `reason` **Inter-agent identity/privilege propagation (Agentic ASI03).** Across
  a delegation chain, confirm a sub-agent cannot inherit more authority than the
  spawning request should carry — privilege that amplifies as it crosses agents
  is the multi-agent confused deputy. Check that delegated identity is scoped and
  is not silently widened on hand-off (the caller's narrow grant must bound the
  callee, not reset to the agent's own broad credential).
- `reason` **Memory & context poisoning (Agentic ASI06 / LLM04).** Persisted
  agent memory or a vector store is an instruction surface that outlives the turn
  that wrote it. Verify the **write gate** — untrusted retrieved content or an
  injected past turn is attributed / trust-checked / quarantined *before* it is
  persisted — and the **read side** — persisted context that does reach memory
  can't silently steer a later decision. Treat poisoned memory as stored prompt
  injection, distinct from the LLM03 model/MCP *source* supply chain above.

## Established-helper bypass

Resolve the repo's sanctioned prompt-construction / content-isolation helper
and its tool-registration layer (where the allowlist and confirmation gating
live), and flag a change that concatenates untrusted content into a prompt
directly or registers a tool outside the blessed path — the helper is where
the instruction-vs-data boundary and least-privilege tool surface are enforced
once.
