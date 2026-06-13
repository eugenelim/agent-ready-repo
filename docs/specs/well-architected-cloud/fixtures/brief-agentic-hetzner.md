# Dogfood brief — agentic platform on Hetzner

> **Fixture for `well-architected-cloud` manual QA.** Feed this brief to
> `architect-design` and `architect-review`. Referenced by path so the gesture
> is replayable. The *Planted findings* block at the bottom records what this
> fixture is engineered to exercise — it is QA scaffolding, not part of the
> brief the skill reasons over.

## The brief

We're building **A2UI** — a multi-agent assistant that drives a web UI on the
user's behalf. A planner agent decomposes a request; worker agents call tools
(search, a code-runner, an email-sender) and can **take actions in the UI**
(fill forms, click, submit). We want to ship on **Hetzner Cloud** to keep the
bill flat and predictable.

Current thinking:

- A few `cx`-class cloud servers behind a Hetzner load balancer.
- Conversation state and tool results in **self-managed Postgres** on a server
  we run ourselves.
- The agents call an **external hosted LLM API** for reasoning; user
  conversation context (which can include uploaded internal documents) is sent
  in the prompt.
- We want it to be **highly available** — the assistant shouldn't go down.

Constraints: small founding team, cost-sensitive, EU users (data should stay in
the EU). No managed-cloud commitment yet — Hetzner is the call.

Questions for the design: is Hetzner the right substrate? How do we make it
production-grade? Should we keep using the external LLM API or self-host
inference?

---

## Planted findings (QA scaffolding — not part of the brief)

This fixture is engineered so the skills surface specific things:

- **(a) Auto-resolved mechanical finding.** The internal-document →
  external-LLM-API call crosses a **trust boundary the brief leaves unlabeled**.
  The pillar spine determines it must be labeled; labeling it is determinate, so
  the convergence loop should **auto-resolve** it (add the boundary + name the
  egress) without asking.
- **(b) Stasis-escape mechanical finding.** "Highly available" with
  **self-managed Postgres but no stated RPO/restore target** and no constraint
  that determines one. "State the recovery target" is spine-required (looks
  mechanical), but the *value* is underivable from anything given — so the loop
  cannot determinately fix it, it survives a pass, and the **stasis escape**
  escalates it to the human rather than looping.
- **Judgment finding (never auto-resolved).** **Self-host inference vs. external
  LLM API** is a tradeoff (control + EU data-residency vs. operational burden +
  capability lag). The loop must **surface** it as a decision, never pick a side.

Expected `architect-design` concept observables: names the **primitives class** +
at least the **data-tier** and **edge/CDN** capability gaps; prioritizes
**Security (agentic)** + **Performance**; surfaces the self-host-vs-external call
as a tradeoff / sensitivity point.

Expected `architect-review` WA-mode observables (GenAI/agentic + security
lenses): a risk register naming the **internal-data → external-LLM egress
boundary** and the **A2UI surface-authority risk** (a worker agent that can act
in the UI is a confused-deputy surface), each finding mechanical/judgment-tagged.
