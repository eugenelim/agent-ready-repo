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
| Tier B **Execution isolation & blast radius** | **design-altitude-only** → backlog `#llm-agent-module-agentic-boundary-extension` |
| Tier C **Inter-agent identity/privilege propagation** | **design-altitude-only** → backlog `#llm-agent-module-agentic-boundary-extension` |
| Tier C **Memory poisoning** (LLM04 anchor) | **design-altitude-only** (LLM04 is the OWASP anchor; the module carries no matching check yet) → backlog `#llm-agent-module-agentic-boundary-extension` |

**Pass condition (b): every overlay security-boundary concern resolves to a
named `llm-agent` check OR an explicit design-altitude-only status.** ✅ Seven
resolve to a module check; three resolve to design-altitude-only with the
backlog pointer.

## Net-new boundaries reconciled

The three design-altitude-only boundaries — **execution isolation & blast
radius**, **inter-agent identity/privilege propagation**, and **memory
poisoning** — exceed the current `llm-agent` surface (LLM01/02/03/05/06/10, no
Agentic-Top-10 content). They are named at design altitude in the lens; the
module extension (OWASP Agentic Top 10: tool misuse, identity/privilege abuse,
memory poisoning) is the deferred backlog entry
`docs/backlog.md#llm-agent-module-agentic-boundary-extension`, so the route-out
has a tracked destination. **No internal backlog anchor is written into the
shipped lens prose** — the lens names the boundaries and routes control-level
verification out generically; the anchor lives only in the spec AC and the
backlog register.
