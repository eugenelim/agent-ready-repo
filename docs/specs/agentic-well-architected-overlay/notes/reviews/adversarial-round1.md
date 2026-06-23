# Adversarial review — round 1

**1. Dogfood manual-QA artifact not recorded.** `docs/specs/agentic-well-architected-overlay/notes/dogfood.md`. AC70 cannot be checked without a durable record of the two architect-design runs. Fix: record the two dogfood runs in notes/dogfood.md.

**2. SKILL.md routing branch RAG/chat clause contradicts its own trigger.** `packs/architect/.apm/skills/architect-design/SKILL.md:61`. Trigger scoped to agentic but clause asserts plain RAG/chat loads baseline tier — a path that never executes. Fix: widen trigger to generative-or-agentic (LLM on the critical path).

**3. Coverage-parity LLM08 cell mixes two claims.** `docs/specs/agentic-well-architected-overlay/notes/coverage-parity.md:34`. Cell does not show which direction-(b) arm LLM08 satisfies. Fix: split the cell to mark LLM01 as the module check and LLM08 as the design-altitude-only OWASP anchor.
