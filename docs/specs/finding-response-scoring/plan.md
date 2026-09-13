# Plan: Finding-response scoring

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/` for repo-only instrumentation and its
  sibling tests; `pyproject.toml:1-14` for the bare-`pytest` sys.path contract
  that lets `tools/` modules import by package name; committed adjudication
  artifacts under `docs/specs/*/notes/` for the recorded shape of a real finding
  set. No analogous scorer exists, which is the named absence of precedent.

## Approach

Build the scorer first against hand-written fixture transcripts, then record the
real arms against it. The scorer is the only artifact with an oracle, so it is
the only artifact that can be wrong in a way a test catches; the transcripts are
data whose correctness is their faithfulness to what a session actually did.

Arm production is in-agent and manual by necessity: the repository has no
mechanism that executes a scored model run, so a session is dispatched per case
per arm and its answer recorded verbatim. That is the cost this design accepts in
exchange for not building an eval runner.

## Constraints

The spec's `## Boundaries` owns the dependency, exit-code and `packs/` limits;
this plan cites them rather than restating them. One implementation consequence
follows that the spec does not state: because the exit code may not carry a
score, the scorer's caller reads its report on stdout, so the report is the
interface and its shape is what the tests pin.

## Construction tests

`tools/test_score_finding_responses.py`, collected by the repository's bare
`pytest` run. It owns every criterion, including AC-0006: a control mismatch is
an assertion over two parsed transcript headers, not a search.

The fixture corpus for the scorer's own tests is distinct from the frozen-case
corpus under `cases/`: the tests need malformed inputs that the real corpus must
never contain.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Reusable learning (the intent) | T4 | The intent cites `result.md` |
| Maintainer procedure (`tools/README.md`) | T1 | The entry names the invocation and its output shape |
| Current product truth (`result.md`) | T4 | Three metrics per arm over three cases |

## Design (LLD)

### Design decisions

The scorer takes two paths per arm — a case file and a transcript file — and
parses both into `{finding_id: disposition}`. Correspondence is set equality
with multiplicity, and the error aggregates every offender rather than stopping
at one. Reporting only the first would make the error depend on an ordering the
criterion deliberately does not define, and would hide a second violation behind
the first until the author fixed one and re-ran.

The eight response tokens are a module-level frozen set. Keeping the vocabulary
in one place is what lets AC-0002's rejection name the offending value; a
scattered membership test can only say "invalid".

The acceptance-criteria count is read from two artifacts the transcript header
names separately — the baseline both arms of a case start from, and that arm's
answered artifact — rather than inferred from the dispositions, because a repair
can change the count without any disposition recording that it did. This is the
13-to-36 inflation the whole measurement exists to see. A single input cannot
yield a delta, and a per-arm baseline could not show the two arms began
identically, so the baseline is one frozen artifact shared by both arms.

The case format follows what the repository already records rather than the
strict emitted line grammar. A committed adjudication is a hand-written table of
identifier, finding and settling evidence — see
`docs/specs/knowledge-enquiry-scope-reachability/notes/adjudication-round-1.md`,
which records 15 sustained findings, 4 refuted and 3 indeterminate. Parsing the
strict `**N.` form instead would reject every artifact this repository actually
holds.

**History supplies cases and never arms.** Those artifacts record the
adjudicator's verdict and stop there; which of the eight responses the author
then took is recorded nowhere, which is the same missing receptacle this
measurement exists to inform. So the arms cannot be reconstructed from history
and must be newly produced, and T3 cannot be shortened by scoring the archive.

Determinism is achieved by a canonical emission order — response tokens in the
order their owner declares them, findings by identifier — not by sorting at each
call site. The risk is real rather than theoretical: a report built by iterating
a set of response tokens varies across runs. Comparing two runs is not a
sufficient oracle, because two nondeterministic runs can coincidentally agree;
the test pins the exact expected bytes instead, which reds on the first
divergent emission whatever caused it.

### Data & schema

A case file lists sustained findings, one per line, each with a stable
identifier. A transcript file carries a header naming its arm, the grammar it
was given, and the answered artifact, then one line per finding pairing the
identifier with a disposition and its reason.

Both formats are line-oriented and parsed with the standard library. No schema
library is introduced.

### Arm-production protocol

One protocol governs every run so that grammar is the only variable. Each
transcript header records the baseline artifact, the model and its settings, and
the instruction text given apart from the grammar; a case's two transcripts must
agree on all of them, which AC-0006 checks mechanically rather than trusting the
operator to have held them steady. Each run starts from a fresh context, and the
two arms of a case are run in alternating order across the three cases so run
order cannot align with arm.

Dispositions are classified after the fact from the recorded response, never
self-reported by the session that produced it. Self-labelling would hand the
neutral arm the response menu the measurement is trying to detect the absence
of, which converts the experiment into its own treatment. The raw response is
preserved verbatim beside its classification so a disputed label is
re-checkable, and a label the classifier cannot settle is recorded as
`unclassified` rather than forced.

### Failure, edge cases & resilience

A transcript that cites an unknown identifier, omits one, repeats one, or uses
an unknown disposition is a hard parse failure naming every offender. These are
authoring mistakes in a hand-recorded corpus, and a scorer that tolerates them
silently reports a number computed over the wrong set.

### Quality attributes (NFRs)

Determinism is the only NFR with a criterion, because the before-and-after
comparison the score exists for is invalid without it.

## Tasks

### T1: Scorer — parsing and correspondence

- **Implements:** AC-0001, AC-0002
- **Depends on:** none
- **Mode:** TDD
- **Touches:** `tools/score_finding_responses.py`,
  `tools/test_score_finding_responses.py`, `tools/README.md`
- **Tests:** AC-0001 and AC-0002. Cases in `tools/test_score_finding_responses.py` covering a
  transcript missing an identifier, carrying an extra one, repeating one, and
  using an out-of-vocabulary disposition, plus one fixture committing several of
  those violations at once. Each asserts the raised error names every specific
  offender, not just that it raised — a test that only asserts "raises" passes
  against an error that names nothing, and a single-offender fixture passes
  against an implementation that reports only the first, which is the behaviour
  AC-0001 was narrowed away from.
- **Approach:** Parse both files into ordered mappings; compare with
  multiplicity; validate each disposition against the frozen token set.
- **Done when:** every test this task's `Tests` names passes.

### T2: Scorer — metrics and determinism

- **Implements:** AC-0003, AC-0004
- **Depends on:** T1
- **Mode:** TDD
- **Touches:** `tools/score_finding_responses.py`,
  `tools/test_score_finding_responses.py`
- **Tests:** AC-0003 and AC-0004. A metrics case asserting the repair share, the
  per-response counts, the baseline criteria count, the answered criteria count
  and the change between them, against a fixture whose expected numbers are
  computed by hand in the test, not by calling the scorer. It reds against an
  implementation that reads only one artifact, which cannot produce the change.
  A determinism case asserting the exact expected report bytes for a fixture,
  rather than comparing two runs to each other — two nondeterministic runs can
  agree by chance, so a self-comparison can pass under the very mutation it is
  meant to catch. It reds under a mutation that emits an unordered iteration.
- **Approach:** Compute the repair share and per-response counts from the parsed
  dispositions; read the criteria count from both artifacts the transcript header
  names — the shared baseline and that arm's answered artifact — and report both
  with their difference; emit in the canonical order.
- **Done when:** every test this task's `Tests` names passes.

### T3: Frozen-case corpus

- **Implements:** AC-0005, AC-0006
- **Depends on:** T2
- **Mode:** TDD
- **Touches:** `docs/specs/finding-response-scoring/cases/`,
  `docs/specs/finding-response-scoring/transcripts/`,
  `tools/test_score_finding_responses.py`
- **Tests:** AC-0005 and AC-0006. A corpus case that discovers the three cases, asserts each has a
  `fix-grammar` and a `neutral-grammar` transcript, and parses every one through
  the scorer's own parser. It reds when a case or an arm is added without its
  pair, which is the drift AC-0005 guards. AC-0006 is exercised separately by
  constructed pairs that differ on exactly one recorded control — baseline
  artifact, model, settings, instruction text — each asserting the error names
  the control that differs; the committed corpus cannot test a mismatch, because
  a corpus containing one would be invalid.
- **Approach:** Source three cases of differing shape from committed
  adjudication artifacts — a small set of determined fixes, a large set of mixed
  determinacy, and a set dominated by judgment findings. Candidates confirmed
  present: `docs/specs/knowledge-enquiry-scope-reachability/notes/adjudication-round-1.md`,
  `docs/specs/cooling-untrusted-timezone-bound/notes/adjudication.md`, and the
  two under `docs/specs/direct-skill-repository-installation/notes/reviews/`.
  Dispatch one session per case per arm under the arm-production protocol in
  `## Design (LLD)`, record each answer verbatim, and classify its dispositions
  afterwards.
- **Done when:** every test this task's `Tests` names passes.

### T4: Record the result

- **Implements:** none directly; produces the spec's durable outputs
- **Depends on:** T3
- **Mode:** Goal-based check
- **Touches:** `docs/specs/finding-response-scoring/result.md`,
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`
- **Tests:** none — this task records a measurement rather than implementing
  behavior.
- **Approach:** Run the scorer over all six transcripts, write the three metrics
  per arm into `result.md` naming the transcripts read, and cite it from the
  owning intent.
- **Done when:** `result.md` exists carrying six scored transcripts, and the
  intent links it.

## Rollout

- **Delivery:** big bang; the change adds one tool and a corpus and alters no
  existing behavior. Reversible by deletion.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none.

## Risks

- **The three cases are selected by the same session that built the scorer**,
  so selection could favour cases that flatter the metric. T3 sources cases from
  committed adjudication artifacts rather than inventing them, and records which
  artifact each case came from so the selection is auditable.
- **The neutral-grammar arm has no shipped implementation to run against**, so
  the arm is produced by giving a session the neutral grammar directly. This
  measures the grammar's effect on a session, not the effect of the shipped
  parser change, and `result.md` states that limit.

## Changelog

- 2026-09-13 — Drafted. Scope set to the repair-response arm only by owner
  decision; the authoring-guidance arm stays with the owning intent.
- 2026-09-13 — Spec review round 3: two findings, both `prior-round-repair`,
  both stale companions of round 2's aggregate-error and AC-0006 repairs. The
  Nit was repaired rather than deferred because it contradicted a criterion, and
  deferring it would have closed half a class. Two consecutive rounds of pure
  repair-churn ended the rounds.
- 2026-09-13 — Spec review round 2: three findings, all `prior-round-repair` —
  round 1's spec-side repairs left stale companion text in the plan. Swept for
  the whole class before repairing: exactly three instances, no fourth.
- 2026-09-13 — Spec review round 1: eleven findings, answered with six
  responses. AC-0006's absence search was cut rather than repaired, AC-0001 was
  narrowed, the two measurement-validity findings were answered once as a
  missing arm-production protocol, and the intent conflict was routed to its
  owner as a follow-on.
- 2026-09-13 — Disconfirming probe over committed review history changed the
  design twice: the case format follows the recorded table shape rather than the
  strict emitted grammar, and history was confirmed to supply cases but never
  arms, so T3 cannot be shortened by scoring the archive.
