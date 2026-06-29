# ADR-0042: Agent additions are keyed to loop and work type, not a global cap

- **Status:** Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-29
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0023
- **Related:** RFC-0050 (§ D7 — the `experience-reviewer`, decided within this policy), RFC-0048 (§ lens-team roster — the multi-loop reviewer model this generalizes), RFC-0032 (architect `design-reviewer` — the first non-core reviewer admitted), `docs/CHARTER.md` (Scope non-goal: "Not a marketplace of specialized agents. Three reviewers is the ceiling.")

## Decision summary

- **Decision:** We add an agent only when it clears a value test keyed to the **loop and work type** it serves — never as a default; the charter's "three reviewers is the ceiling" binds the **core `work-loop` code-review gate** specifically, not agents catalogue-wide.
- **Because:** the real risk the charter names is undisciplined *proliferation*, not agent *count* — and agents add genuine, non-substitutable value in specific shapes (forked-context independence, parallelism, a distinct surface/cadence).
- **Applies to:** every pack and every loop in the catalogue (reviewers, executors, retrieval subagents, lenses). Supersedes ADR-0023's narrower core-loop-lenses framing.
- **Tradeoff accepted:** "no global cap, judged by a test" is softer than a hard number and relies on disciplined application.
- **Revisit if:** the cross-loop roster grows without additions clearing the test (drift toward a marketplace), or a fourth *core-loop* code-review lens becomes genuinely necessary (a charter question), or adapter dispatch becomes universally exact-name (weakening the collision-hardening rationale).

## Context

ADR-0023 settled that the charter's *"three reviewers is the ceiling"* scopes the
**always-on core code-review lenses** (`adversarial-reviewer`, `security-reviewer`,
`quality-engineer`) and not a global cap on agents — admitting `architect`'s
`design-reviewer` as the first non-core reviewer. That reading is correct. But it
was framed narrowly, as a binary between *core-loop lenses* and *one opt-in design
reviewer*, and the catalogue has since outgrown that frame:

- The catalogue now runs **several distinct loops**, each with its own agents: the
  `work-loop` (supervisor + `implementer` executor + the three code-review lenses);
  the **discovery loop** with its own design-time reviewer roster
  (`discovery-threat-reviewer`, `discovery-reliability-reviewer`, reused
  `design-reviewer` — RFC-0048 §lens-team roster); and `research` retrieval
  subagents (`evidence-retriever`, `source-extractor`).
- The operating model is moving toward **more-autonomous operation** (RFC-0048,
  RFC-0050; deployment onto autonomous-agent substrates such as Hermes), where the
  question "may we add an agent here?" recurs per loop and cannot be answered by a
  single core-loop carve-out.

Two forces shape the rule:

- **Anti-proliferation.** The charter non-goal — *"Not a marketplace of specialized
  agents"* — and the MAST finding that fewer agents win (arXiv:2503.13657, as
  consolidated in RFC-0048's research notes). Blindly adding an agent because "it
  might help" is the documented failure mode.
- **Genuine agent value.** An agent earns its existence where a skill cannot: a
  **forked context** that reviews without marking its own homework; **parallelism**
  over disjoint work (the parallel lens-team / executor fan-out); a **distinct
  surface or cadence** (design-time review vs. code-diff review). Denying these
  wholesale is as wrong as adding blindly.

RFC-0050's D7 pressure-test made the gap concrete: ADR-0023's narrow framing was
being *mis-cited to forbid an admissible reviewer* (a UX/design-lens reviewer that
is opt-in, different-surface, different-cadence), while RFC-0048 already operates a
multi-loop reviewer roster ADR-0023 never generalized. The decision must be stated
as a loop/work-type-keyed rule.

## Decision

> We add an agent when, and only when, it clears a value test **keyed to the loop
> and work type it serves** — never as a default — and the charter's "three
> reviewers is the ceiling" binds the **core `work-loop` code-review gate
> specifically**, not agents catalogue-wide.

Concretely:

- **The cap that stays (ADR-0023's core holding, carried forward).** The always-on
  core `work-loop` code-review gate is capped at the **three lenses**
  (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`). Adding a fourth
  *core-loop* lens is a **charter question** (RFC + charter amendment); this ADR
  does **not** pre-authorize it.

- **The test for any other agent** — a reviewer, an executor, a retrieval subagent,
  a lens. It is admissible when **all** hold:
  1. it serves a **different loop or work type** than the core code-review gate
     (e.g. the discovery loop, design/experience review, research retrieval,
     parallel execution, autonomous operation);
  2. it earns its existence by a value an agent **uniquely** provides —
     **forked-context independence** (it does not mark its own homework),
     **parallelism** (disjoint fan-out), or a **distinct surface/cadence**;
  3. it clears the **charter's four principles**; and
  4. it is **collision-hardened by construction** — a distinct discipline-word head
     that is *not* a substring of another agent's name, plus a role-disambiguating
     `description:` cue (the RFC-0048 §"names are collision-hardened" rule), because
     agents are dispatched by **role-match** and exact-name dispatch is not
     available on every adapter.

- **Default bias: fewer agents (MAST).** The burden is on the *addition* to clear
  the test; "it might help" does not. An agent that only duplicates a skill's
  in-context capability, or that exists to pad a 1:1 agent-per-role org chart,
  fails.

- **Loop/work-type is the key, not pack.** The same surface reviewed at a
  *different cadence by a different loop* can warrant a distinct agent (design-time
  UX review is not code-diff review); but two agents that would run in the **same
  gate on the same surface** should be **one**.

## Decision drivers

- **Independence** — the forked-context, doesn't-mark-its-own-homework property.
- **Parallelism** — disjoint fan-out (the lens-team / executor case).
- **Distinct surface/cadence** — a genuinely different loop or work type.
- **MAST / anti-proliferation** — fewer agents win; the marketplace non-goal.
- **Charter's four principles.**
- **Adapter dispatch reality** — role-match, not exact-name, so names must carry the
  distinction.

## Consequences

**Positive:**

- A reusable, stated test for "can we add an agent?" that resolves **at this ADR**
  rather than re-litigating the charter line each time — extending ADR-0023's intent
  to every loop.
- Generalizes cleanly to today's tree (the discovery roster, research retrieval
  subagents, the `work-loop` `implementer`) and to autonomous operation; RFC-0050's
  D7 `experience-reviewer` is decided *within* it, not against the charter.
- Keeps the **core code-review ceiling intact** while admitting value-adding agents
  in other loops — widening *what category* an agent is in, not *how many* core
  lenses there are.

**Negative:**

- "No global cap, judged by a test" is **softer than a hard number** and relies on
  disciplined application and reviewer judgment — an erosion risk if the test is
  rubber-stamped. Mitigated by the explicit burden-on-the-addition, the MAST
  default, and the collision-hardening construction rule.
- "Loop/work type" is a **judgment boundary**; borderline cases (is this a new loop
  or the same one?) need adjudication by the RFC Approver.
- "Agent" / "reviewer" now spans several categories; the **description-cue
  discipline** is load-bearing to keep them distinct on role-match adapters.

**Revisit if:** the cross-loop roster grows without additions clearing the test
(drift toward a marketplace-of-agents), or a fourth *core-loop* code-review lens
becomes genuinely necessary (a charter RFC, not this ADR), or adapter dispatch
becomes universally exact-name (weakening the collision-hardening rationale).

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** every new agent's RFC/spec **names the loop/work type it serves, the
  unique-value test it clears (independence / parallelism / distinct
  surface-cadence), and its collision-hardened name + `description:` cue**; the
  `adversarial-reviewer` pass and the RFC Approver check it against this ADR.
- **Owner:** the RFC Approver + the `adversarial-reviewer` pass.

## Alternatives considered

- **Keep ADR-0023 as-is** (core-loop-lenses-only framing). Rejected: the *reading*
  is right but the *framing* is too narrow — it did not generalize to the multi-loop
  roster RFC-0048 already runs, and it was mis-cited in RFC-0050 D7 to forbid an
  admissible reviewer. This ADR keeps the holding and states the general rule.
- **A hard global cap** (a literal "N agents total"). Rejected against the
  *anti-proliferation* and *independence* drivers, and already false in the tree
  (`research` ships two retrieval subagents; `architect` ships `design-reviewer`;
  RFC-0048 adds discovery reviewers). A literal count contradicts reality and blocks
  value-adding agents.
- **No cap / open marketplace.** Rejected against the *MAST / anti-proliferation*
  driver and the charter non-goal — blind proliferation is the documented failure
  mode.
- **Leave it to per-RFC judgment with no recorded policy.** Rejected: it
  re-litigates the charter line on every proposal; recording the rule once is the
  point of an ADR.

## References

- **Supersedes** ADR-0023 (`docs/adr/0023-reviewer-ceiling-scopes-core-code-review-lenses.md`).
- RFC-0050 § D7 — the `experience-reviewer`, the first agent decided under this policy.
- RFC-0048 § lens-team roster + § "names are collision-hardened by construction" —
  the multi-loop reviewer model and the naming rule this ADR generalizes.
- RFC-0032 — the architect `design-reviewer` (the first non-core reviewer admitted, under ADR-0023).
- `docs/CHARTER.md` — Scope non-goal and the four principles.
- MAST (multi-agent failure taxonomy), arXiv:2503.13657 — consolidated in RFC-0048's research notes; the "fewer agents win" default.
