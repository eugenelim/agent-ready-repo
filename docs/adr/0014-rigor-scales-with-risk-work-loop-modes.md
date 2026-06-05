# ADR-0014: Rigor scales with risk — `work-loop` light/full modes

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-05
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0025 (the proposal this records); ADR-0005 (supervisor-mode scheduling — orthogonal); ADR-0007 (doc-drift lint shipped as a `work-loop` skill script)

## Context

The spec→plan→`work-loop` methodology produces reliably good output, but it had
effectively **one gear**, and the rule into that gear was **file count**:
`work-loop/SKILL.md:55-56` and `AGENTS.md:162` escalated any no-spec change above
one file straight into `new-spec` + full `work-loop`. Full mode runs
`adversarial-reviewer` iterated to `Clean`, a `quality-engineer` pass that is
discretionary at selection but a floor at the end-of-session checklist
(`SKILL.md:449`), up to `max_iterations: 5`, behind the `loop-cohort` state
machine.

Two forces made this a problem:

- **Cost.** A user reported ~$60 of budget for a ~2-hour `new-spec`/`work-loop`
  session (a single anecdote, but a directional one). The dominant driver is the
  reviewer fan-out iterated to clean across loop iterations, not artifact size.
- **A risk-blind trigger.** File count is a poor proxy for risk: a two-file,
  familiar, single-task change paid compliance-grade cost, while the field norm
  (Copilot plan mode, Kiro Quick Plan, OpenSpec) graduates rigor by *risk* —
  reserving heavy treatment for unfamiliar, multi-person, or compliance work.

The decision was debated and accepted in RFC-0025 (merged in #237). This ADR
records it; it is not a fresh tradeoff debate.

## Decision

**`work-loop` has two modes, and which one runs is chosen by the risk of the
work, not its file count.**

- **Light mode (the default for low-risk work).** A lean spec written inline —
  Objective + Acceptance Criteria + a short task list (other `new-spec` sections
  become optional); a **single bounded** `adversarial-reviewer` pass — a Blocker
  earns exactly **one** re-review of the fix, then **escalates to full mode**
  rather than iterating; **no default `quality-engineer` pass**; **no
  `loop-cohort` state machine**. Scoped to a **single logical task** (it may
  touch a few files but carries no inter-task dependencies).
- **Full mode (unchanged).** Reached when the work trips any **risk trigger**:
  unfamiliar territory; more than one person builds or reviews it; it decomposes
  a multi-feature brief or has dependent tasks; it touches a compliance/governance
  surface or a security boundary; it changes structure or a public/published
  interface; it performs a destructive/irreversible operation; or it adds a
  dependency.

The **risk-trigger set replaces the `">1 file → new-spec"` rule.** Each trigger
maps to a gate the repo already maintains, which is the boundary's exhaustiveness
argument.

**Vehicle:** a `work-loop` SKILL.md mode branch plus making the named `new-spec`
template sections optional. **No new executable code, skill, or artifact type;**
`loop-cohort.py` and `lint-spec-status.py` are unchanged — light mode is defined
by *not invoking* them.

## Consequences

**Positive:**
- The default path for ordinary low-risk work is materially cheaper in tokens and
  wall-clock, while keeping a review floor (one adversarial pass).
- Rigor tracks risk rather than a file-count proxy, matching field practice.
- Full mode is untouched and still reached whenever risk warrants it.
- Subtraction-shaped: no new code, skill, or artifact format to maintain.

**Negative:**
- **Light mode forgoes the `quality-engineer` lens's checklist-floor** — its
  testability/observability/reliability/maintainability concerns have *no floor*
  in light mode. This is the most material accepted loss; the bet is that
  low-risk single-task work rarely carries those concerns, and a surviving
  Blocker (which can be a maintainability Blocker) still escalates into the full
  lens. The trigger set therefore mirrors existing gates **minus** this one
  deliberately-dropped lens.
- We give up the uniform "every change passes the full gate" guarantee.
- A second mode is real cognitive surface, and mode selection is a judgment call
  with no mechanical check; misclassification is possible.

**Neutral / to revisit:**
- Mode selection mechanism (agent auto-classifies from triggers vs. explicit user
  flag) is deferred to the implementation spec.
- Whether a single bounded adversarial pass is a sufficient floor — revisit if
  light-mode escapes show up in practice.
- Whether light multi-task work ever needs a bare iteration cap — by definition
  such work has crossed into full mode, so this stays unbuilt unless observed.

## Alternatives considered

- **Do-nothing** — keep the single heavy gear. Rejected: the cost problem and the
  risk-blind trigger persist.
- **Tune the full path** (e.g. `max_iterations` 5→3, lints to CI) — Rejected:
  shaves the only gear without addressing the trigger or giving small multi-file
  work anywhere lean to land; the band-aid the surrounding work was criticised
  for.
- **Raise the rule by docs only, no lean mode** — Rejected: relocates the
  boundary but leaves full machinery as the only landing once triggered, so the
  cost win is small.
- **A separate lightweight skill / Copilot-style no-spec mode** — Rejected:
  builds a parallel system duplicating `new-spec`/`work-loop` and drops the
  persisted contract entirely; more surface, not less.

## References

- RFC-0025 — `docs/rfc/0025-work-loop-light-mode-and-risk-based-escalation.md` (#237).
- Field prior art: [GitHub Copilot plan mode](https://github.blog/changelog/2026-01-21-github-copilot-cli-plan-before-you-build-steer-as-you-go/); [AWS Kiro best practices / Quick Plan](https://kiro.dev/docs/specs/best-practices/); [OpenSpec vs Spec Kit weight](https://www.augmentcode.com/tools/best-spec-driven-development-tools).
- Implementation lands in `packs/core` sources + `make build-self` for the projected paths (`.claude/...`, `docs/CONVENTIONS.md` — the latter rescued by `PROJECTED_README_OVERRIDES`); root `AGENTS.md` is Manual (`EXCLUDED_PATTERNS`) and is edited **directly** with its seed `packs/core/seeds/AGENTS.md` kept in sync — `build-self` does not re-project it. Tracked by the follow-on spec `docs/specs/work-loop-light-mode/`.
