# About the walking skeleton

> Why the greenfield front door builds a kept, minimal, end-to-end **walking skeleton** instead of a throwaway prototype — and why that one choice changes how a new project ages. This page is for readers who want to understand the reasoning, not to run the flow. To run it, follow [From idea to a walking skeleton](../tutorials/start-a-new-project.md).

## The question this page answers

When you start a new project from an idea, you face a fork: build a quick throwaway to feel the shape of the thing, or build a thin slice you intend to keep. Both put working software in front of you fast. So why does `init-project` insist on the second — a walking skeleton authored as a real spec and built through `work-loop` — and refuse to generate a throwaway? Because the two look similar on day one and diverge sharply by month three.

## The shape of the answer

A **walking skeleton** is the thinnest slice that wires the *real* components together end to end: a real request reaching a real datastore through the real transport. It does almost nothing — but what it does, it does through the architecture you actually chose. It is **kept**: held to a feature contract, covered by tests, the literal first commit of the system you're building.

A **throwaway prototype** optimizes for a different thing — learning fast by cutting corners. Hardcoded values, no tests, the datastore faked, the transport stubbed. That's a legitimate tool for *answering a question* (a spike). The failure mode is what happens next: the prototype sort-of works, the pressure to ship is real, and nobody finds the moment to throw it away. It gets retrofitted into the foundation instead — and the rationale for every shortcut, never written down, is lost. You inherit the corners without the reasons.

The walking skeleton dodges that trap by being kept *from the start*. There is no "throw it away" moment to miss, because it was never disposable. The first real feature extends it; it doesn't replace it.

## Design choices and tradeoffs

- **Orchestrate, don't generate.** `init-project` authors the skeleton as a spec and hands the build to `work-loop` rather than generating the code itself. The alternative — an autonomous multi-agent generator that emits a whole codebase — trades the human-in-the-loop discipline (gates, adversarial review, scope control) for speed, and the "it just built the whole app" stories are survivorship bias. Composing the skills the repo already owns keeps every guardrail the normal loop has.
- **A foundation before the skeleton.** The stack is decided and recorded (an ADR plus `reference.md`) *before* the skeleton is authored, so the skeleton wires together components that were chosen on purpose. A skeleton built before the foundation would bake in accidental choices — exactly the throwaway failure mode, one level up.
- **Fluid phases, not a waterfall.** Authoring the skeleton routinely surfaces a wrong foundation decision; the flow expects you to go back and amend it. The skeleton is kept, but the foundation stays revisable until the build confirms it.

## How this differs from a spike

A **spike** is a throwaway by design — you build it to answer a question ("can this library do X?"), you read the answer, you delete the code. That's healthy, and the greenfield trigger gate explicitly sends spikes and one-off scripts *away* from this flow. The distinction is intent: a spike's value is the *knowledge* it produces and its code is disposable; a walking skeleton's value is the *code* it produces and it's the first brick of the building. Confusing the two — keeping a spike, or contract-testing a throwaway — is where the trouble starts.

## See also

- [From idea to a walking skeleton](../tutorials/start-a-new-project.md) — the guided first walkthrough.
- [Decide and record your foundation during inception](../how-to/record-your-foundation-during-inception.md) — the foundation step the skeleton builds on.
- [About foundation vs. map](foundation-vs-map.md) — the normative golden path the skeleton conforms to.
- [Why a brief layer](why-a-brief-layer.md) — the value-gate output that feeds inception.
