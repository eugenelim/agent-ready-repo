# Plan: Reproducible preservation authoring on the shared-graph case

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `none — non-structural`. The edit stays inside one
  existing reference,
  `packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md`,
  and its content-pin suite
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`.

## Approach

Every miss traces to the reference, not to the case. The reference says the
map is working material but never asks the author to say so; it offers "a
criterion or a named gap" with no rule for choosing; and it names full and
alternate construction as a class without saying the paths must agree. Three
edits close those gaps, pinned by content tests. The behavior can only be shown by graded runs,
so they come last, against the rebuilt projection, repeated for the positive
case. The riskiest part is run-to-run variance: if any final-projection run
misses, the reference is revised and every final-projection run is redone.

## Constraints

- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations, § Version bump rule, and § Self-hosting projection.
- `tools/lint-pack-test-boundary.py`: a pack test reads nothing above its pack.
- `assets/spec.md` § Acceptance Criteria owns criterion shape; the reference
  cites it and this change does not restate it.
- The brief's C1 stop rule allows "a named gap that blocks review"; this change
  narrows when a gap is the right answer and keeps that it blocks review.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** the graded runs in T3.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — brief Spec map row, C3 bullet, captured item | T2, T4 | Row added; spec `Brief:` line; bullet links the ledger; captured item `Closed` | Row derives `Shipped`; no `[backlog].open` entry names the captured item |
| Release history — the Core patch AC-0004 states | T2 | Manifests and fragment | AC-0004 |
| Reusable learning — verification ledger | T3 | Every graded run recorded | The spec's Reusable learning closeout condition |

## Design (LLD)

### Behavior & rules

**Diagnosis.** In the five graded runs of the case on unedited guidance (one on
Core 3.1.33; four on 3.1.37–3.1.38, whose `new-spec` is byte-identical), the
two misses are independent:

| Run | Disposability (assertion 5) | Invalidation (assertion 4) |
| --- | --- | --- |
| 3.1.33 | stated | criterion |
| 3.1.38 head run 1 | not stated | criterion with allowed delta none |
| 3.1.38 head run 2 | not stated; plan labelled repository-durable | named gap |
| 3.1.37 base | "This map is working material" | named gap |
| 3.1.38 base, rerun | not stated | criterion |

Every gap run cited the same reason: no supplied file produces the
`dependencies` map that `invalidated_files` reads. But `invalidated_files` is
itself visible, and its base-revision output on fixture inputs is an oracle, as
head run 1 showed.

**Spike (step 5a).** One graded run against a `/tmp` projection carrying Edits
1 and 2 scored 5 of 6. It opened its map with "This map is working material.
Deleting or rebuilding it changes no criterion." and bounded `invalidated_files`
with a criterion, recording the absent `dependencies` producer as an
assumption. It missed assertion 4 on a third point: it checked the full build
and the incremental build each against its own golden, and no criterion made
them agree with each other. Edit 3 closes that. Two further spike runs
carrying all three edits each held 6 of 6. Spike runs are design evidence, not
AC-0001 runs: they ran on a `/tmp` copy, not on the rebuilt projection.

**Edit 1 — § When to stop.** Replace the bullet "Do not dismiss a reachable
class…" and the gap bullet with:

- Do not dismiss a reachable class because the new member seems not to affect
  it. Give it a criterion that states the bound.
- A consumer you can read gets a criterion even when code that feeds it is out
  of view. Take its output on base-revision inputs as the oracle, state the
  allowed delta, and record the unseen producer in `## Assumptions` as a fact
  the criterion still bounds, not as a gap.
- Name a gap only when no oracle can be built from the repository for a
  reachable class, such as when the consumer itself is out of view. Write the
  gap in the spec's `## Assumptions`. It blocks review while it stands.

**Edit 2 — § Where the consumer map lives.** After "never in `spec.md`.",
add: "Open the map with one sentence saying it is working material and that
deleting or rebuilding it changes no criterion. A plan kept long-term does not
make its map accepted scope."

**Edit 3 — § What a preservation criterion adds.** After the four-item list,
add: "When two paths build the same structure, such as a full build and an
incremental build, the old behavior includes that they agree. Its oracle builds
the same final state both ways with the new member present and compares the two
results, in addition to comparing each with the base revision."

**Pins.** Four phrases join `RULES`: "Name a gap only when no oracle can be
built", "not as a gap", "Open the map with one sentence", and "the old behavior
includes that they agree". The existing "never in `spec.md`" and
sustained-finding pins stay.

The frozen case already exercises all three edits, so the eval harness needs no
change (`packs/AGENTS.md` § Security and authoring rules: the harness covers
the changed content).

Traces to: AC-0001, AC-0002 · none.

Owned by: T1.

### Graded-run method

Each run copies the named projection's `.claude/skills` and `.claude/agents`
into a fresh `/tmp` directory, removes every `evals/` directory and
`adapt-to-project`, and copies the case's `files` into a separate working
directory. A fresh subagent gets only the case prompt, the two directory paths,
and an instruction to stay inside them. A separate grader subagent gets only
the output text and the case's assertions, and returns one PASS or FAIL with a
quoted reason per assertion. The base projection comes from
`git archive <base> .claude/skills .claude/agents`. Outputs and grades are
stored under `notes/graded-runs/`.

Traces to: AC-0001, AC-0002 · none.

Owned by: T3.

## Tasks

### T1: The reference states the disposability sentence, when a gap is allowed, and path agreement

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md, packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py

**Mode:** TDD. The four new pins are written first and fail on the current
reference.

**Tests:**
- The four new `RULES` phrases in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`
  fail before Edits 1–3 and pass after.
- `test_repository_grounding_evals.py`, the rest of
  `packs/core/tests/skills/new-spec/`, and
  `packs/core/tests/skills/work-loop/test_preservation_evidence_reference.py`
  pass unchanged.

**Done when:** both `Tests:` bullets pass.

### T2: Release, projection, and registration

**Depends on:** T1

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*, docs/product/briefs/repository-grounding-preservation.md, workspace.toml, docs/specs/workspace-retirement/inventory.toml, .agents/**, .claude/**, .codex/**

**Mode:** goal-based.

**Tests:**
- AC-0003, AC-0004, AC-0005 commands.
- `agentbundle catalogue self-host --root . --write --force` leaves no diff on
  re-run.
- The roster version-bump, brief-coverage, and workspace inventory checks pass.

**Done when:** every `Tests:` bullet passes.

### T3: Graded runs against the final rebuilt and base projections

**Depends on:** T2

**Touches:** docs/specs/grounding-preservation-authoring-reproducibility/notes/**

**Mode:** visual / manual QA of the rebuilt agent artifact.

**Tests:**
- AC-0001 and AC-0002 runs, plus one base run of each case, recorded in
  `notes/verification-ledger.md` with outputs and grades under
  `notes/graded-runs/`.

**Done when:** the ledger records every run with its pack version and
revision, and AC-0001 and AC-0002 hold.

### T4: Close the captured item and point the brief at the evidence

**Depends on:** T3

**Touches:** docs/product/captured/new-spec-positive-case-reproducibility.md, docs/product/briefs/repository-grounding-preservation.md, workspace.toml

**Mode:** goal-based.

**Tests:**
- The captured item reads `Status: Closed`, `[backlog].open` has no entry for
  it, this spec's workspace entry sits in `["ini-002".work].shipped`, and the
  brief's C3 positive-fixture bullet links this spec's ledger.
- `lint-spec-status.py --root .` and `workspace-status` report no new finding.

**Done when:** every `Tests:` bullet passes.

## Changelog

