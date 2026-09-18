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

## Execution observation — T1, the pack-portability conflict, 2026-09-18

T1's check list asks the reference to *name* the spec's Testing Strategy
terminal-effect list rather than restate its items. `packs/AGENTS.md` § Shipped
pack content carries no internal-governance citations forbids exactly that: under
`packs/`, write portable guidance only, and do not cite this catalogue's internal
records or repository-only paths. A probe confirms the rule is kept — no file
under `packs/frontend-engineering/.apm/` cites `docs/specs`, `docs/adr` or
`docs/rfc`.

**Resolution.** The reference states the terminal-effect obligation directly and
in full. An adopter reading it has no access to this repository, so a pointer
would resolve to nothing for the only audience the file has.

**What that costs.** The obligation now has two full statements: the spec's
Testing Strategy, which the repo-side verification reads, and the reference,
which ships. The spec's one-canonical-home rule was written for repository
artifacts and is not breached by a portability copy, but the two can drift, and
nothing mechanical compares them. Recorded here rather than left implicit. T5
parses the reference's read-path table, not its prose, so T5 does not close this.

## Execution observation — a line-wrapped clause read as a missing one, 2026-09-18

T1's first verification harness reported a false FAIL: it matched
`not downgraded to a skip` as a contiguous string against a file where the clause
wraps as `the refusal is not\ndowngraded to a skip`. The clause was present and
correct.

Every T1 and T2 check is a claim about prose, and prose wraps. A harness that
matches raw text will report a defect that is not there, and — the direction that
matters — could equally pass a file where the words appear in separate sentences.
Both harnesses normalise whitespace before matching from this point on. Recorded
because the failure mode is silent in the passing direction.

## Execution observation — T2 inserted as step 0, not a renumbering, 2026-09-18

The plan required every pre-flight step enumeration in the pack to resolve after
the insertion, and named `token-architecture/SKILL.md`'s reference to "the seed
token block in `frontend-engineering` step 2" among them.

Inserting the handoff read as **step 0** rather than as a new step 1 leaves steps
1, 1b, 2 and 3 at their existing numbers. That keeps three references true without
editing them: `token-architecture/SKILL.md:11` ("step 2"), the shared pre-flight's
own "proceed to step 2" inside genre routing, and the tutorial's "(step 1b —
requires experience-design)". A renumbering insertion would have falsified all
three, two of them outside this pack's skill.

Five sites did change: the skill's opening summary, the five-step count, the
`Steps 0–3` heading, both mode "run steps" lines, `JOURNEY.md`'s implementation
sequence, and `pack.toml`'s starter prompt and expected result. A sweep for
`step 1, 1b` / `all four steps` / `Steps 1–3` across `packs/frontend-engineering/`
returns nothing.

## Execution observation — three false readings from one harness habit, 2026-09-18

T1's and T2's checks are claims about prose, and a harness matching raw text gave
a wrong answer three times in two tasks: once on a line wrap
(`not\ndowngraded to a skip`), once on sentence-initial capitalisation (`No
\`agentbundle-layout.toml\`` against a lowercase pattern), and once on the same
wrap class inside a bulleted clause. Every instance was a false **negative** —
the content was present — but the same habit produces false positives just as
easily, because words matched across a wrap can come from two unrelated
sentences.

Both harnesses now normalise whitespace and case before matching. Recorded because
the passing direction is the silent one, and a prose check that cannot be trusted
in both directions is not evidence.
