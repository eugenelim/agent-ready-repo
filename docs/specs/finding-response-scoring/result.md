# Result: the run works; its arm comparison is not decisive

Measured 2026-09-13 by `tools/score_finding_responses.py`. The scored-run table
and the disposition counts reproduce by running the scorer over the committed
cases and transcripts. The first-run figures are recounted by hand from a
retained disposition listing the scorer cannot parse, and the test count comes
from pytest.

## The scored run

| Case | Arm | Repair share | Other responses | Criteria change |
| --- | --- | ---: | --- | ---: |
| small-determined | fix-grammar | 7/7 | — | +0 |
| small-determined | neutral-grammar | 7/7 | — | +0 |
| large-mixed | fix-grammar | 6/15 | dismiss-and-re-present 6, bound-out-of-scope 3 | +0 |
| large-mixed | neutral-grammar | 13/15 | narrow-the-claim 1, cut-the-item 1 | +0 |
| judgment-dominated | fix-grammar | 6/6 | — | +0 |
| judgment-dominated | neutral-grammar | 6/6 | — | +1 |

Across the six cells, five of the eight responses were used at all: repair 45,
dismiss-and-re-present 6, bound-out-of-scope 3, narrow-the-claim 1, cut-the-item
1. Three were never used: repair-the-generator, route-to-owner, and
accept-as-proportionate. Four of the six cells used only repair.

## The repeated cell

`large-mixed` / `fix-grammar` was run a second time. The first run is retained at
[`superseded/`](superseded/README.md); the second is the one scored above.

| Run | repair | narrow | dismiss-and-re-present | bound-out-of-scope |
| --- | ---: | ---: | ---: | ---: |
| first | 13 | 2 | 0 | 0 |
| second | 6 | 0 | 6 | 3 |

The first run's inputs were not retained, so whether the two runs received the
same input is not established.

## What this run does and does not support

**It does not establish whether the finding grammar affects how findings are
answered.** One session per cell cannot characterise run-to-run variation, and
the one cell that was repeated moved by 7 findings in repair share — the same
size as the between-arm difference in that case. No decision about neutralizing
the grammar should rest on this run.

Answering the question needs replication: enough runs per cell to characterise
its spread before any arm difference is interpreted. How many that is cannot be
read off a single repeated cell.

## What is established

The instrument works. The scorer parses cases and transcripts, validates finding
correspondence, validates arm controls, counts acceptance criteria, and emits a
deterministic report. The corpus test additionally binds each transcript to its
canonical rendering by path, SHA-256, and declared grammar label, and rejects a
transcript file the case set does not account for.

That binding is enforced by the corpus test, not by the scoring CLI. The CLI
parses and scores the two files it is given; it does not read renderings. The
corpus test is therefore a required companion gate rather than a property of any
single invocation.

42 tests pass. The guards named above each have a negative test, and the
mutations run against them are recorded with their observed failures in
[`notes/mutation-log.md`](notes/mutation-log.md).

## Standing limits, independent of sample size

- **The neutral arm has no shipped implementation.** Sessions were handed the
  grammar directly rather than reading it from a changed parser, so this measures
  a grammar's effect on a reader, not the parser change's effect.
- **Neutral clauses run longer than their fix counterparts.** Stating a condition
  without naming a remedy takes more words, so length could not be equalised
  without removing obligation content. Length is an uncontrolled variable.
- **Criteria change is a session-stated delta** re-based on a counted baseline.
  No session produced an artifact, so no post-answer count was independently
  observed. Each `*.answered.md` records that arithmetic.
- **One classifier per batch**, blind to arm, nothing marked low-confidence, no
  second labeller.
- **Sessions' own words mislead.** "Accept." routinely means accept the finding
  and repair it, not accept the defect as proportionate. Classification reads the
  substance, which is why the protocol forbids self-reported dispositions.

## Corrections made during this run

Recorded because the pattern matters more than the instances. Each was caught by
independent review before any decision rested on it.

**This whole account is working-tree recollection.** The superseded renderings,
the instruction that produced them, and the sweep output were not retained, so
items 1 and 2 cannot be audited from the repository. They are kept because the
failure modes are worth knowing, not because they are evidenced. Item 3's
corrections are checkable: the numbers it names appear in the current files.

1. **The first neutral arm was not neutral** — its clauses read as the fix
   clauses with the imperative verb removed, so the run compared grammatical mood
   rather than grammar. The superseded renderings were not retained, so this
   description is a working-tree recollection rather than an auditable record; the
   rendering instruction that produced them demanded both clauses be
   "informationally equivalent at the same specificity", which forbids exactly the
   openness about means that is the treatment. Regenerated and rerun.
2. **One clause survived that regeneration** with the same defect, and was found
   by sweeping every pair rather than by reading the one the reviewer cited. The
   check used to verify the regeneration had been weaker than the instruction used
   to produce it. The sweep's figures were not retained and are not cited.
3. **Claims outran evidence repeatedly** — a between-run swing described as larger
   than a between-arm difference when both are 7; a byte-identity claim whose
   inputs were not retained; totals cited for passes whose scores were not kept;
   and a criteria-change cell reported as +0 when the scorer says +1. Each was
   answered by withdrawing or correcting the claim rather than by manufacturing
   support for it.

## Inputs

| Case | Findings | Source adjudication |
| --- | ---: | --- |
| small-determined | 7 | `docs/specs/direct-skill-repository-installation/notes/reviews/preexecute-security-adjudication.md` |
| large-mixed | 15 | `docs/specs/knowledge-enquiry-scope-reachability/notes/adjudication-round-1.md` |
| judgment-dominated | 6 | `docs/specs/cooling-untrusted-input-refusals/notes/adjudication.md` |

Each transcript records its grammar, rendering path and SHA-256, baseline, model
and settings, and a hash of the instruction text outside the grammar. A case's
two transcripts must agree on baseline, model, settings and instructions, and
differ on arm, grammar and rendering. Every session's verbatim answer sits beside
its classification as `*.raw.md`.
