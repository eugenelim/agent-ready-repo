# Coverage parity — agentic overlay ↔ `security-checklists` `llm-agent`

Re-runnable artifact for the bidirectional coverage-parity AC
(`spec.md` coverage-parity AC; plan T4). Source of the control surface:
`packs/core/.apm/skills/security-checklists/references/llm-agent.md`. Source of
the overlay concerns: `…/architect-design/references/lens-genai-agentic.md`
(mirrored in `architect-review`).

The `llm-agent` module enumerates: a **spec-stage proactive control**
(instruction-vs-data boundary + least-privilege tool surface + confirmation
criteria) and six implementation checks — **LLM01** Prompt Injection, **LLM06**
Excessive Agency, **LLM05** Improper Output Handling, **LLM02** Sensitive
Information Disclosure, **LLM10** Unbounded Consumption, **LLM03** Model/MCP
Supply Chain.

## Direction (a) — every `llm-agent` control maps to an overlay concern

| `llm-agent` control | Overlay concern (tier) |
| --- | --- |
| Spec-stage proactive control (instruction-vs-data + least-privilege tools + confirmation) | Tier A **Prompt injection** (instruction-vs-data boundary) + Tier B **Tool-use authorization & bounded autonomy** (the allowlist + confirmation question) |
| LLM01 Prompt Injection | Tier A **Prompt injection** |
| LLM06 Excessive Agency | Tier B **Tool-use authorization & bounded autonomy** |
| LLM05 Improper Output Handling | Tier B **Output handling** |
| LLM02 Sensitive Information Disclosure | Tier A **Data egress & disclosure** (bidirectional) |
| LLM10 Unbounded Consumption | Tier A **Token cost** (denial-of-wallet half) + Tier B **Reliability under non-determinism** (runaway-loop / loop-cap half) |
| LLM03 Model/MCP Supply Chain | Tier B **Tool / MCP source provenance** + Tier C **Sub-agent provenance** (multi-agent-gated facet) |

**Pass condition (a): no `llm-agent` control unmapped.** ✅ All 7 map.

## Direction (b) — every overlay security-boundary concern resolves to a check or a design-altitude-only status

| Overlay security-boundary concern (tier) | Resolves to |
| --- | --- |
| Tier A **Prompt injection** (incl. retrieved-content/embedding, LLM08 anchor) | LLM01 (the concern's module check); LLM08 is the OWASP anchor on the same injection surface — no separate module line item, design-altitude-only |
| Tier A **Data egress & disclosure** | LLM02 |
| Tier B **Tool-use authorization & bounded autonomy** | LLM06 + proactive control |
| Tier B **Tool / MCP source provenance** | LLM03 |
| Tier C **Sub-agent provenance** | LLM03 (multi-agent facet) |
| Tier B **Output handling** | LLM05 |
| Tier A token / Tier B loop-cap **consumption** | LLM10 |
| Tier B **Execution isolation & blast radius** | `llm-agent` **Execution isolation & blast radius** check (Agentic ASI02 / ASI05) |
| Tier C **Inter-agent identity/privilege propagation** | `llm-agent` **Inter-agent identity/privilege propagation** check (Agentic ASI03) |
| Tier C **Memory poisoning** (LLM04 anchor) | `llm-agent` **Memory & context poisoning** check (Agentic ASI06 / LLM04) |

**Pass condition (b): every overlay security-boundary concern resolves to a
named `llm-agent` check OR an explicit design-altitude-only status.** ✅ All ten
now resolve to a named `llm-agent` module check — the three that were formerly
design-altitude-only (execution isolation & blast radius, inter-agent
identity/privilege propagation, memory poisoning) gained module checks when the
`llm-agent-agentic-boundary-extension` spec added the Agentic-Top-10 surface.

## Net-new boundaries reconciled

The three boundaries that once exceeded the `llm-agent` surface — **execution
isolation & blast radius**, **inter-agent identity/privilege propagation**, and
**memory poisoning** — are now **named module checks**. The `llm-agent` module
gained an Agentic-Top-10 surface (ASI02 / ASI03 / ASI05 / ASI06 + LLM04) via the
`llm-agent-agentic-boundary-extension` spec, so the lens's design-altitude
route-out for them lands on a control-level check like every other
security-boundary concern, rather than on cross-cutting standards alone. **No
internal backlog anchor is written into the shipped lens prose** — the lens names
the boundaries and routes control-level verification to the `llm-agent` module
generically; it never carried the anchor.
