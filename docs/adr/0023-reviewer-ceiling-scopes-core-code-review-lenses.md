# ADR-0023: The "three reviewers" ceiling scopes the core code-review lenses

- **Status:** Superseded by [ADR-0042](0042-agent-additions-keyed-to-loop-and-work-type.md). ADR-0042 keeps this ADR's core holding (the ceiling binds the core code-review gate) and generalizes the rest into a loop/work-type-keyed agent-addition policy.
- **Date:** 2026-06-14
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0032 (architect `design-reviewer` subagent), **ADR-0042 (the superseding agent-addition policy)**, `docs/CHARTER.md` (Scope non-goal "Not a marketplace of specialized agents. Three reviewers is the ceiling"), `docs/specs/architect-design-reviewer/`

## Context

`docs/CHARTER.md` carries a Scope non-goal: *"Not a marketplace of specialized
agents. Three reviewers is the ceiling. New skills earn a place by clearing the
four principles below."* Read literally as a global cap on reviewer agents, that
line would forbid RFC-0032's `design-reviewer` — a fourth thing called a
"reviewer."

But the catalogue already ships agents beyond the three named in the charter:
the `research` pack ships two retrieval subagents (`evidence-retriever`,
`source-extractor`). So the non-goal is plainly not a global agent count — it is
a restraint on a specific kind of proliferation. RFC-0032 needs the scope of
that restraint settled before a design-side reviewer can land, because the
phrase genuinely brushes the line: a `design-reviewer` *is* a reviewer.

The charter's own Scope text resolves the ambiguity. It enumerates the ceiling
in the same breath it sets it: the catalogue ships *"three review lenses
(adversarial, security, quality)"* (`docs/CHARTER.md:29-30`) — the always-on
code-review lenses the `work-loop` runs on every PR.

## Decision

> The charter's "three reviewers is the ceiling" governs the **always-on core
> code-review lenses** (`adversarial-reviewer`, `security-reviewer`,
> `quality-engineer`) — not a global cap on reviewer agents across all packs.

Concretely:

- A reviewer that runs **inside the core `work-loop`'s default gate sequence on
  every PR** counts against the ceiling. Adding a fourth such lens is the move
  the charter restrains, and it stays restrained.
- A reviewer that lives in an **opt-in pack**, reviews a **different surface**
  (design artifacts, not code diffs), and runs at a **different cadence** (only
  when that pack is installed and invoked) is a different category. It is
  admissible when it clears the charter's four principles — and is still subject
  to them.
- This is an **interpretation recorded against the charter, not an amendment**.
  The charter text is unchanged; this ADR pins how its existing words are read,
  so the next "can we add a reviewer?" question resolves here rather than
  re-litigating the line.

The first artifact admitted under this reading is the architect pack's
`design-reviewer` subagent (RFC-0032).

## Consequences

**Positive:**
- RFC-0032 lands without a charter edit; the charter stays stable (charter
  changes are the highest-ceremony change in the repo).
- Future reviewer proposals have a clear test: *does it run in the core loop's
  default gate sequence?* If yes, it's against the ceiling; if it's an opt-in,
  different-surface lens, it's judged on the four principles.

**Negative:**
- The word "reviewer" now means two things in the repo (a core-loop lens vs. an
  opt-in design/other-surface lens). This ADR is the disambiguator; without it,
  the charter line reads as a flat cap.
- A determined reading could treat this as ceiling-erosion by reinterpretation.
  Mitigation: the scope is bounded to *core-loop* lenses and every candidate
  still passes the four principles — this widens *what category* a reviewer is
  in, not *how many* core lenses there are.

**Neutral / to revisit:**
- If a future change wants a fourth *core-loop* reviewer, that is a charter
  question (RFC + charter amendment), and this ADR does not pre-authorize it.
- If the "reviewer" overload proves confusing in practice, a future charter RFC
  could restate the ceiling explicitly as "three *code-side* review lenses."

## Alternatives considered

- **Amend the charter** to read "three code-side reviewers." Rejected for now —
  unnecessary ceremony when the Scope text already enumerates the ceiling as the
  three code-review lenses; an interpretation ADR is the lighter, reversible
  vehicle. Left open as a future option if the overload causes friction.
- **Decline the design-reviewer** to preserve the literal count. Rejected —
  RFC-0032 establishes the design-side reviewer clears all four principles and
  fills a gap the pack already names as preferred; the literal-count reading is
  contradicted by the research pack's existing agents.
- **Treat the ceiling as a global agent cap.** Rejected as already false in the
  tree (research ships two non-reviewer agents).

## References

- RFC-0032 — `docs/rfc/0032-architect-design-reviewer-subagent.md` (§ Proposal,
  Charter reconciliation; § Decisions requested #2).
- `docs/CHARTER.md` — Scope ("three review lenses (adversarial, security,
  quality)") and the Principles.
- `packs/research/.apm/agents/` — the existing non-reviewer subagents that show
  the non-goal is not a global agent count.
