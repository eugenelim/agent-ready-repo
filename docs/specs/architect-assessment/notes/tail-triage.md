# Tail triage

Date: 2026-08-21

## Review shape

`WIDE + DEEP`. The tracked diff alone spans 54 files, 1,001 insertions, and
2,142 deletions; the new pack-local corpus, generated references, workflow,
tests, research packets, spec, and product guides add substantial untracked
source material. The two modified typed-asides ledger files pre-date this
initiative and are excluded from its review claim.

## Dependency-ordered boundaries

1. Research method and source packets define the assessment and corpus claims.
2. Canonical `packs/architect/okf/architecture-lenses/` content compiles into
   the same-pack `architecture-lenses-reference` surface.
3. `architect-assess`, `architect-design`, and `architect-review` consume that
   generated reference surface; the profiler remains optional and read-only.
4. Pack metadata, product guides, journey, changelog, and NOW projection expose
   the shipped user outcome.

## Transformation and verification invariant

Canonical OKF is the only knowledge source; generated router, index, and
reference files are replaceable output. Two write-mode compiles followed by
check mode produced no managed-output drift. Focused tests cover claim/source
traceability, all seven installed adapters, profiler safety, planted review
failures, and guide-driven cross-shape dogfood. The supported operator-terminal
`make build-check` completed every leg, including Bandit, pip-audit, npm audit,
Semgrep, and scanner self-tests.

## Sampled review and rollback

Adversarial, security, and quality reviewers independently returned
`Clean — ready to commit.` after the final lifecycle repair. The cold-context
assessment fixture also detected every planted failure class. If the release
must be withdrawn before publication, revert architect 0.15.0 as one unit,
restore the previous consumer references, and regenerate the architect pack;
do not hand-edit generated OKF output.

## Learning disposition

No uncaptured reusable project lesson remains. The generalizable safety lessons
from review—classify protected roots as well as descendants, share finite work
budgets across phases, and bind validation to descriptor-confined writes—are
encoded directly in profiler tests and adopter-facing reference documentation.
