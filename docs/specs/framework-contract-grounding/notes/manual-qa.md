# Manual-QA observations — framework-contract-grounding

Recorded per the spec's Testing Strategy (the two manual-QA items). Both passes
exercised the **projected** skill artifacts (`.claude/skills/…`), not the source,
the way a real session would load them. Scratch scenario fixtures live in
`.context/ac6-scenario/` (gitignored).

## 1. Behavioral happy path — EXECUTE (manual QA)

An implementing agent was posed an EXECUTE step writing code against an
unfamiliar third-party library (`acme_ratelimit.TokenBucket`) whose behavioral
contract (constructor signature, whether `acquire()` blocks, thread-safety) it
did not hold, and asked to follow the projected `work-loop` gate +
`infra-contract-acquisition` skill literally for two situations.

**Observed:**

- **Gate fires for the software case in both situations** — the agent
  classified the unknowns as the *behavioral* contract the widened gate names,
  and quoted "The bare grep rule confirms a symbol exists; it never confirms
  that behavioral contract — this gate closes that gap."
- **(a) framework skill present →** the agent routed to the T2 software
  sub-tier, said it would **consult the skill and emit a cited contract slice**
  (constructor signature, blocking semantics, thread-safety), quoting "If
  present, consult it and cite the contract slice the generated code relies on."
  It did **not** guess.
- **(b) no source available →** the agent landed on
  **detect-and-recommend-and-degrade**: recommend authoring an internal skill
  via the `author-a-skill` how-to / installing a published vendor skill /
  pointing the loop at a doc MCP, and **surface the gap as a decision** — never
  silent progress on a guessed contract. It correctly noted the doc-retrieval
  surface is **Tier-1 detect-and-stop, never mandated**, so its absence degrades
  rather than blocks, and that it must not bundle per-library data itself
  (Principle 1).

**Verdict:** PASS — the widened gate routes the software case to the
detect-and-recommend tier; present → consult-and-cite, absent → recommend +
surface, neither guesses.

## 2. Re-derivation — REVIEW (manual QA, AC6)

A real `quality-engineer` REVIEW pass was driven over a synthetic diff that uses
`acme_ratelimit.TokenBucket` and carries an inline **cited contract slice plus a
stated verification** — both deliberately *wrong* on three points vs. the
authoritative framework-library skill (`acme-ratelimit-skill.md`): (i) `acquire()`
claimed non-blocking + returning a bool (truth: blocking, returns `None`;
`try_acquire()` is the bool one); (ii) the bucket claimed thread-safe (truth: not
thread-safe in v3.x). The reviewer's brief inlined the widened
`infra-contract-acquisition` + the work-loop re-derivation bullet, exactly as the
orchestrator drives a software-contract-citing diff.

**Observed:** the reviewer **re-derived the cited slice independently from the
detected framework skill and explicitly did NOT trust the implementer's citation
or stated verification.** It caught all three planted contradictions as Blockers
(always-defer dead-code bug from the wrong `acquire` semantics; data race from
the false thread-safety claim) and closed with: "The citation was wrong on all
three contract points it asserted … which is exactly the field-report blind spot
the no-trust rule exists to catch."

**Verdict:** PASS — the software re-derivation is symmetric with the infra one;
the reviewer re-derives from the source rather than trusting the citation (AC6).
A prose-grep alone would not have demonstrated this; the live pass did.
