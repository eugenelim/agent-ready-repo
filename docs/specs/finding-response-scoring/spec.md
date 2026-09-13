# Spec: Finding-response scoring

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** docs/product/intents/spec-authoring-protocol-measured-before-shipping.md
- **Contract:** none
- **Shape:** data

## Objective

A maintainer deciding whether to neutralize the repository's finding grammar
reads one recorded score and learns whether the neutral grammar changed how
sustained findings were answered.

The score is produced by `tools/score_finding_responses.py`, a deterministic
function over recorded transcripts. Three frozen cases are each answered twice
— once under the current grammar, which requires every sustained finding to end
`Fix: <text>`, and once under a neutral grammar that states a required outcome
and its constraints. For each arm the scorer reports three numbers: the share of
findings answered by repair, the mix of non-repair responses, and the change in
acceptance-criteria count across the answered artifact.

Both arms of a case run under one recorded protocol in which the finding
grammar is the only difference: same baseline artifact, same model and settings,
same instructions apart from the grammar, a fresh context each time, and the
disposition of each answer classified after the fact from the recorded response
rather than self-reported by the session that produced it. A session told to
label its own responses is a session told what its choices are.

The score is evidence for a decision a person makes. It is not a gate, and
nothing in the repository consumes it as one.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Reusable learning | `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md` | eugenelim | The recorded run result referenced from the intent | The result states, over three cases, whether the neutral grammar changed the repair share and what it cost in criteria count |
| Maintainer procedure | `tools/README.md` entry for the scorer | eugenelim | Invocation line and its output shape | An operator can run the scorer from the entry alone |
| Current product truth | `docs/specs/finding-response-scoring/result.md` | eugenelim | The three metrics per arm over three cases | The result exists and names the transcripts it read |

Retention class: repository-durable. The cases, transcripts and result stay in
the repository because the decision they support is revisited whenever the
grammar changes again, and a score whose inputs are gone cannot be rechecked.

No architecture, interface-compatibility, release-history or operations output
applies: the scorer adds no boundary, no published interface, no released
artifact and no runtime surface.

## Boundaries

### Always do

- Record, inside each transcript, the exact arm grammar the session was given,
  so a transcript read later is self-describing.
- Keep the scorer a pure function over files it is given: it reads its inputs,
  writes its report to stdout, and changes nothing on disk.

### Ask first

- Changing what any of the three metrics means, or adding a fourth.
- Changing the case count away from three.
- Recording an arm with any grammar other than the two the cases name.

### Never do

- Add a new top-level directory or any new dependency; the scorer uses the
  standard library only.
- Give the scorer a failing exit code derived from a score. A parse or input
  error may exit non-zero; a measured result never does.
- Edit anything under `packs/` in this spec. The grammar change is a separate
  delivery that this score exists to inform.

## Testing Strategy

- **Transcript correspondence and disposition vocabulary (AC-0001, AC-0002)** —
  TDD. Both are pure predicates over two parsed files, and each has an obvious
  disconfirming case: a transcript citing a finding its case does not contain,
  and a disposition outside the owner's eight.
- **Metrics and determinism (AC-0003, AC-0004)** — TDD. A fixed output shape
  over fixture inputs, and an exact-bytes assertion. Determinism is tested
  against expected bytes rather than against a second run, because two
  nondeterministic runs can agree by chance.
- **Corpus shape (AC-0005)** — TDD. Shape assertions over committed files. They
  red when a case or an arm is missing.
- **Arm control (AC-0006)** — TDD. Constructed transcript pairs differing on
  exactly one recorded control. A valid committed corpus cannot carry a
  mismatch, so only constructed pairs can exercise the rejection.

## Acceptance Criteria

- [x] **AC-0001.** The scorer rejects a transcript whose set of cited finding
      identifiers is not exactly its case's set, each appearing once, and names
      every identifier that is missing, extra, or repeated.
- [x] **AC-0002.** The scorer admits as a disposition only the eight responses
      that `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`
      carries verbatim in its `## The deferred criteria, carried verbatim`
      section, in the lexical encoding the scorer's format
      contract fixes, and rejects any other value, naming the rejected value and
      the finding it was attached to.
- [x] **AC-0003.** For each arm the scorer emits the repair share, the count per
      non-repair response, and the acceptance-criteria count of both the shared
      baseline artifact and that arm's answered artifact, which the transcript
      header names separately.
- [x] **AC-0004.** Two runs of the scorer over identical inputs produce
      byte-identical output.
- [x] **AC-0005.** The corpus holds three cases, each with a transcript for both
      the `fix-grammar` and `neutral-grammar` arms, and every one parses.
- [x] **AC-0006.** The scorer rejects a case whose two transcripts disagree on
      any recorded control — baseline artifact, model, settings, or instruction
      text outside the grammar — naming the control that differs.

## Follow-ons

- Neutralizing the emitted finding grammar across the reviewer agents, the
  adjudicator, `loop-cohort.py`'s parser and its contract tests. Owner:
  eugenelim. This spec produces the evidence that decision needs and performs
  none of it.
- Registering
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md` in
  `workspace.toml`. It owns this work and has no dispatchable entry, so nothing
  routes to it. Owner: eugenelim.
- Amending that same intent, which still sends the frozen cases to the pack eval
  register while this spec keeps them repo-only under today's owner decision.
  The conflict is real and this spec does not resolve it silently. Owner:
  eugenelim.

## Assumptions

- Technical: Python >= 3.11 with a bare `pytest` runner (packages/agentbundle/pyproject.toml:9; pyproject.toml:1-14)
- Technical: no eval runner exists — `evals.json` is read by ~12 test files for shape and content only (grep over packs/core/tests, tools, tests, packages)
- Technical: the current grammar is machine-required by `STRICT_SUSTAINED_FINDING_LINE_RE` (packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:1626)
- Technical: `review-verdict.v1` `findings[]` carries no response enum and no per-finding reason (packs/core/.apm/skills/work-loop/references/review-verdict-record.md:57-88)
- Process: the scorer ships as repo-only tooling, not pack content, so no pack version bump and no eval-harness update applies (user confirmation 2026-09-13)
- Product: one run is three frozen cases scored under both arms (user confirmation 2026-09-13)
- Product: the score is read by the maintainer at the point of deciding the grammar change, and by nothing else (user confirmation 2026-09-13)
