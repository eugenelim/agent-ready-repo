# ADR-0145: Shaping entry points: `intent` for the intent lifecycle, `initiative` for the longer route

- **Status:** Rejected
- **Date:** 2026-10-12
- **Areas:** shaping
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0140 (D1, which this would have superseded in part); RFC-0107 (D1, Experiment); ADR-0111; docs/specs/intent-longer-and-supervised-verbs/

## Context

- ADR-0140 D1 put every shaping step into one `intent` skill. Folding the nine
  longer-route and discovery skills into it fails RFC-0107's activation bound.
  - On held-out queries, the positive trigger rate fell from 0.856 to 0.728, then
    to 0.739 after one description revision. The floor is 0.826.
  - A repeated pre-fold baseline gave 0.856 again; the aggregate standard error is
    about 0.019, so the drop is real.
- Every miss was a run where no skill fired. A cold forced-choice probe still picked
  the right skill and mode in 72 of 72 runs. The fold routes correctly but loads
  less often.
- The losses cluster in steps whose descriptions lost their concrete nouns: the
  validation plan (0.87 to 0.27), `situate`, `ground`, and `diverge` options
  (1.00 to 0.73–0.87). Steps that kept a distinctive noun held: `find`, `canvas`,
  `frame`.
- Ten verbs in one 1,024-character description leave about 60 characters each.
- The pack listing with one extra description is about 4,300 characters, well
  inside Codex's 8,000-character budget.

## Decision

We will reach the shaping stage through two verb-mode skills: `intent` for one
intent's lifecycle, and `initiative` for the initiative-scale longer route.

- **D1:** `intent` holds route mode and the modes `frame`, `de-risk` (including its
  validation-plan section), `decompose`, and `ground`.
- **D2:** `initiative` holds the modes `situate`, `find`, `diverge`, `bet`, `map`,
  and `canvas`. It has no route mode of its own: `intent`'s route mode names
  `initiative situate` as the longer route's first step.
- **D3:** ADR-0140's remaining decisions stand. Route mode stays stateless,
  `discovery-loop` stays separate and calls modes of both skills at its gates, and
  `align-value-stream` stays separate.

## Decision drivers

- Activation within RFC-0107's bound on the required hosts.
- Listing cost within host budgets.
- One owner per drawn route, so the lifecycle map stays legible.
- No stateful controller.

## Consequences

**Positive:**
- Each description has about twice the room per mode for the nouns users type.
- The longer route lives in one skill, so its steps and offers stay together.
- The *frame* name collision stays removed.

**Negative:**
- Selection has two shaping candidates instead of one, so a request can pick the
  wrong one.
- The listing is about 1,000 characters longer than ADR-0140 planned.
- Whether two descriptions recover activation is unmeasured until the next held-out
  run.

**Revisit if:** the held-out activation run for this split fails RFC-0107's bound on
a required host, or a host budget forces the pack below two shaping descriptions.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** a held-out activation run on a fresh query set meets RFC-0107's bound,
  and a cold probe routes each mode to the right skill.
- **Owner:** eugenelim
- **Result (2026-10-13):** the signal failed, so eugenelim rejected this decision. The
  cold probe passed (72 of 72 runs right, all high confidence). The activation run on
  a fresh held-out set gave a positive trigger rate of 0.461 against a pre-fold 0.600
  and a floor of 0.570. 90 of the 97 missed runs fired no skill. The nine narrow
  shaping skills stay; ADR-0140 D1 stands as written. Evidence:
  docs/specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md.

## Alternatives considered

- **Rewrite the one description again:** two attempts reached 0.728 and 0.739, and
  the held-out set no longer gives an unseen test. It fails the activation driver.
- **Split the four weakest skills back out, as RFC-0107 prescribes:** `intent` would
  keep a mixed set, and the longer route would span skills. Part of the "weakest"
  ranking rests on a group that the repeated baseline shows is noise.
- **Use Claude Code's `when_to_use` field for extra trigger text:** only one host
  reads it, so it would pass the measured host without fixing the others.
- **Keep the nine narrow skills:** the 14 shaping skills used 8,401 characters,
  which fails the listing-cost driver.

## References

- docs/specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md
- docs/specs/intent-longer-and-supervised-verbs/notes/routing-classification-evidence.md
- RFC-0107 § Experiment / validation
