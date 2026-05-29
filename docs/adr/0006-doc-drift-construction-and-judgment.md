# ADR-0006: Doc drift — prevented by construction + judgment for adopters; mechanically gated only as catalogue governance

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-05-29
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0016; `docs/specs/doc-drift-prevention/`; `docs/CONVENTIONS.md` § 4

## Context

The work-loop replaced "feel" with mechanical gates (lint / typecheck / test)
everywhere except documentation. Every doc-drift control we had was the
opposite of mechanical: an honor-system principle ("spec drift is a bug — fix
it in the same PR") and a judgmental reviewer check. The recurrence was the
evidence — a `Shipped` spec with 11/11 acceptance criteria unchecked, an
out-of-vocabulary status (`Drafting`) on a live spec, deferrals recorded only
in PR comments that then rotted.

The intuitive fix — ship a `lint-spec-status.py` gate to everyone — turns out
**not to reach adopters**, for three independently fatal reasons established
while drafting RFC-0016:

- **Linters don't project.** `tools/lint-*.py` have no `packs/` source; they're
  catalogue-internal. The `seeds/` construct is restricted to placeholder
  templates, not working scripts.
- **No guaranteed runtime.** The pack ships files, not interpreters. A
  JS/Java/Go adopter has no Python; a hardcoded `python …` hook can't run
  locally. The only language-agnostic runtime surface is CI, which provisions
  Python regardless of project language.
- **No pre-PR hook event, and copilot can't fire hooks at all.** Hook *wiring*
  exists only for SessionStart-class events (the wrong moment); there is no
  PR-open lifecycle event to bind a fail-closed gate to.

So a hard, fail-closed gate is achievable only inside this catalogue (Python +
CI both present). For adopters, prevention must use the surfaces that *do*
project — skills (all 4 adapters), agents (3 of 4), and seeds (all 4).

## Decision

> We prevent doc drift for adopters through **construction + judgment**, and
> keep a hard **mechanical gate only as catalogue governance** — inside this
> repo, where Python and CI both exist.

Specifically:

- **Construction + judgment ship to adopters** via the surfaces that project:
  (1) a canonical-by-birth `new-spec` template that stamps the status
  vocabulary, `- [ ]` AC notation, and the `(deferred: <anchor>)` hatch;
  (2) a sharpened `adversarial-reviewer` "Spec drift" check naming four concrete
  metadata invariants; (3) the same invariants in the work-loop finish-time
  checklist; (4) the contract those judgments measure against, pinned in the
  CONVENTIONS seed § 4; (5) a durable, version-controlled deferred-work register
  (`docs/backlog.md`) that `(deferred: <anchor>)` markers point into, replacing
  the lossy "the PR is the durable record" rule.
- **The mechanical gate is catalogue-only.** `tools/lint-spec-status.py` checks
  the same invariants over *our* spec corpus, invoked from the Makefile
  `build-check` target. It has no `packs/` source and is deliberately **not**
  wired into the projected `tools/hooks/pre-pr.py` — doing so would make an
  adopter's hook call a script absent from their tree.
- **The contract is metadata-only.** The lint and the pinned contract govern the
  *shape* of status, criteria, and deferrals — not whether the spec matches the
  code. Detecting *semantic* spec↔code drift remains the `adversarial-reviewer`'s
  judgment call.

## Consequences

**Positive:**
- Drift you never author costs nothing to prevent: template-shaped specs are
  canonical from birth on every adapter.
- The catalogue keeps a hard, fail-closed gate where it can actually run.
- Deferred work has a greppable, version-controlled home instead of a rotting
  PR comment; the `(deferred:) ↔ backlog.md` link is mechanically checked here
  and reviewer-checked for adopters.

**Negative:**
- No fail-closed guarantee for adopters — a real downgrade from a CI linter,
  accepted because the alternative is undeliverable.
- Ongoing maintenance cost: the Tier-1 lint plus the pinned formats it measures.
- The agent-primitive surface reaches 3 of 4 adapters today (copilot's agent
  projection is `dropped`); the sharpened reviewer is construction+judgment on
  the skill/seed surfaces but only judgment-where-the-agent-runs.

**Neutral / to revisit:**
- Whether to flip copilot's `agent` projection to enabled (extending the
  reviewer to 4/4) — deferred to a separate follow-up.
- Invariant (iii) (dangling references) covers doc-refs only in v1; code paths
  are deferred to v1.1 once the warn-only rate is observed.

## Alternatives considered

- **Do nothing** (honor-system + reviewer): the recurrence is the evidence it
  fails.
- **Reviewer-only** (sharpen the reviewer alone): necessary but not sufficient —
  judgmental, and reaches only 3/4 adapters.
- **Mechanical lint everywhere** (ship the linter to adopters): the obvious fix,
  but undeliverable for the three packaging/runtime/event reasons above. Kept as
  catalogue governance only.
- **By-construction status** (derive status from AC state): strongest in
  principle; folded into the construction mechanism (the template) rather than a
  separate derivation engine, which no adapter runtime could execute anyway.
