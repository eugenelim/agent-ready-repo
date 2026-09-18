# Verification ledger — design-handoff-read

## Reviewer gate, 2026-09-18

`reviewers-clean` was fired on the owner's explicit approval, **not** on a clean
sentinel. No pre-EXECUTE round returned one. Recording the basis so a later reader
does not mistake the transition for sentinel-backed evidence.

**What the gate rests on.** Six pre-EXECUTE rounds, both the adversarial and the
secure-design lane, every raw report and every adjudication persisted under
`.context/reviews/8e4969b4-9575-49c3-bcfe-f76e2c9eb9c8/`. Sustained findings per
round: 20 → 30 → 24 → (round 4 superseded by an owner decision) → 22 → 24. Every
sustained finding was repaired; the plan's Changelog carries one entry per round
naming what changed and why.

Two owner decisions changed the slice's shape rather than patching it. After round
three, what is consumed became frontmatter plus an opaque body, because measurement
showed a section-keyed contract extracts nothing from the only real
aesthetic-direction artifact in `docs/design/`. After round four, five controls
were dropped — a Unicode code-point denylist, redaction of location-bearing values
out of artifact content, display bounds on the confirmation prompt, a transcription
predicate, and frontmatter shape validation — because prose cannot carry them at
the precision they need. The spec's `## What this slice does not attempt` and its
Follow-ons record each with its reasoning.

**What it does not rest on.** No reviewer has seen the round-six repairs. Those
repairs closed twenty-four sustained findings, including the slug-validation
control, the widening of the refusal set from five to six, the reserved-tree test
at every resolved path, and three corrections inside T5's own test design. The
controls had converged by round six — the secure-design lane's blocker count ran
4, 5, 5, 5, 1, 1 — but the verification apparatus had not, and the round-six
blockers were concentrated there.

**Known residual risk.** Two classes recurred and are diagnosed rather than proven
absent.

The first is a hand-transcribed claim about the design artifacts that the real
corpus contradicts. It appeared in every round: frontmatter sets, heading literals,
a `.handover.md` collision, foreign `type:` values under the read paths, missing
required fields, duplicate H1s, a section count, a byte range, a median. T5's
corpus-agreement test exists to end it, and a reader finding another instance in
prose that T5 does not read should treat it as expected residue of that class.

The second is a vacuous differential arm. A mutation named in the plan greened
either way twice — in round four, where no corpus file witnessed it, and again in
round six, where the named witness sat off every read path under the slugs T5
binds. Both are corrected against measurement. The general lesson is recorded in
the plan: verification *data* asserted in prose is unverifiable until the test is
written, so T5's arms are re-derived when the corpus changes rather than trusted
from this document.

**Owner decision.** The owner approved the spec and plan and instructed
implementation to begin, having been shown the round-by-round finding counts, the
absent sentinel, the two recurring classes above, and the option to run a seventh
round.
