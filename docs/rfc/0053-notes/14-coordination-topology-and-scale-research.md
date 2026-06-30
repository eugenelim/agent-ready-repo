# Coordination topology & scale — research (does "never agent-to-agent" still hold?)

> RESEARCH NOTE (RFC-0053). Pressure-tests Decision 5's "coordinate through the shared
> blackboard, never agent-to-agent" against the 2026 landscape — agent-interoperability
> protocols, agentic mesh, and the refined multi-agent-failure picture. Desk research from the
> main thread, 2026-06-30 (subagent web is blocked here).

## What changed since MAST (early 2025)

Agent-to-agent communication is now **standardized and in enterprise production**, which it wasn't
when RFC-0048's MAST grounding was written:

- **A2A (Agent-to-Agent)** — Google-initiated, now Linux-Foundation-hosted; **150+ organizations**,
  integrated across Google/Microsoft/AWS, production deployments at the one-year mark. Cross-platform
  agent collaboration. [Linux Foundation; IBM]
- **MCP** (agent ↔ tool), **ACP** (structured messaging within a local environment), **ANP** (agent
  network) — a complementary multi-protocol stack; surveys frame MCP+ACP+A2A+ANP as converging.
  [arXiv:2505.02279; Zylos 2026]
- Gartner: **40% of enterprise apps will embed task-specific agents by 2026** (up from <5% in 2025).

So "agent teams talk to each other" is no longer exotic — but note **how**: via **structured, typed
protocols** (capability cards, typed messages, function-call semantics), **not** free-form chat.

## The crux: structured coordination ≠ free-form chat-to-consensus

The multi-agent literature shows a **clear preference for structure**: predefined message types
(`REQUEST_TASK` / `ACCEPT_TASK` / `TASK_COMPLETE`), programmatic function-call communication "to
improve efficiency and reliability." **What MAST condemned is *free-form chat-negotiation-to-consensus*
+ unverified manager-routing — not communication as such.** RFC-0053's D5 conflated the two: the
failure mode is *unstructured chat*, and the safe pattern is *structured coordination + verification*.
The blackboard is **one instance** of structured coordination, not the only one.

## The pattern depends on the shape of the work

Topologies (centralized · decentralized · hierarchical; hierarchical cuts O(n²) gossip to O(n)):

| Coordination shape | Best mechanism | Why |
| --- | --- | --- |
| **Many interdependent specialists, order unknown in advance** (= discovery convergence) | **Blackboard** (shared structured state) | Eliminates the "phone game" + context loss; agents react to state async; the research's stated sweet spot. [arXiv:2507.01701] |
| **Linear pipeline / simple handoff** | **Direct typed messaging** | Fine for simple relationships — but classical message-passing **burns tokens** (copies history into every prompt → context degradation). |
| **Long-running async handoff between loops/teams** | **Event-driven** (Kafka/Flink-style) | Retries, decoupling, no agent blocking another — reliability direct calls can't give. |
| **Many teams, cross-org, dynamic discovery at scale** | **Agentic mesh** (capability directory + A2A/ACP + event bus) | Agents discover and coordinate "without a centralized controller"; the company-OS-at-scale pattern. |

## Synthesis for RFC-0053 (where this leaves Decision 5)

D5's "shared blackboard, never agent-to-agent" is **right for the discovery loop's *internal*
convergence** (many interdependent lenses, order unknown) — that is exactly the blackboard's sweet
spot, and free-form chat there is the MAST thrash. But as a **universal** claim it is **too strong**;
the honest, scale-aware position is three-layered:

1. **Intra-loop convergence → blackboard.** Lenses coordinate through the shared
   discovery-workspace; **free-form chat-to-consensus is the failure mode**, not communication per se.
   (D5, correct for this shape.)
2. **Inter-loop handoff → durable contract artifacts (+ event-driven).** discovery → build → release
   coordinate through stable-id artifacts (the RFC-0048 "seams are artifacts, not calls"), which is
   the right pattern for long-running async handoff.
3. **Company-OS scale → structured agent protocols + an agentic mesh.** At scale, teams *do* interact
   dynamically — via **A2A/ACP + a capability directory + an event bus**, which is defensible because
   it is **structured/typed/verified, the opposite of free-form chat**. Crucially this is the
   **harness's / platform's layer (CHARTER Principle 3)** — this contract ships the discovery
   loop-team (blackboard-coordinated) + the artifact seams; it does **not** ship the mesh, but its
   stable-id artifacts are **mesh-ready** (a mesh consumes exactly those).

**The invariant across all three:** *structured coordination + verification, never free-form
chat-negotiation-to-consensus.* The blackboard is that invariant **right-sized to the convergence
shape** — not a rejection of agent-to-agent communication in general.

## Sources

- [A2A surpasses 150 orgs / production (Linux Foundation)](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year)
- [Survey of agent interoperability protocols: MCP/ACP/A2A/ANP, arXiv:2505.02279](https://arxiv.org/pdf/2505.02279)
- [The Orchestration of Multi-Agent Systems: Architectures, Protocols, Enterprise Adoption, arXiv:2601.13671](https://arxiv.org/html/2601.13671v1)
- [Advanced LLM Multi-Agent Systems Based on Blackboard Architecture, arXiv:2507.01701](https://arxiv.org/html/2507.01701v1)
- [Agentic mesh — enterprise agent ecosystems (InfoWorld)](https://www.infoworld.com/article/3978819/agentic-mesh-the-future-of-enterprise-agent-ecosystems.html)
