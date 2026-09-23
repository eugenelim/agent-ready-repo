# Plan: Changelog fragment assembly — measurement spike

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/changelog-fragment-source.md` § 7 and
  ADR-0123 § Confirmation name the claims; `docs/product/research/changelog-fragmentation-spike.md`
  and `docs/product/research/changelog-generator-quality-spike.md` are the two
  analogous runs, and supply the method — import `tools/build-site.py` so the
  prototype agrees with production about which `##` lines are headings, keep the
  prototype outside the repository, and carry a control arm;
  `tools/measure-changelog-conflicts.py` is the tracked-measurement precedent and
  the construction path for T1. Named uncertainty: whether a synthetic corpus of
  repeated bodies stands in for real prose at ten times the entry count (spec
  Assumptions).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure.

## Approach

Four measurements, then one report. Three of them need a throwaway assembler
prototype, so that prototype is built once in T2 and reused by T3 and T4; the
fourth, merge independence, needs only Git and ships as a tracked script because
its figure is the one a reader is most likely to want to re-derive. Each
measurement carries the arm that makes its figure readable — a monolith control
for T1, a sort-removed mutation for T2, today's live payload for T3, and an
unmodified build of the same revision for T4 — because a treatment figure with
nothing to compare against is what the two prior changelog spikes went out of
their way to avoid. The riskiest part is T4: `make site-build` runs the whole
marketing and documentation build and the fragment arm has to be genuinely
wired in, so those runs happen in a disposable clone that is deleted afterwards
rather than in this worktree.

## Constraints

- ADR-0123 is Accepted. This spike measures the merge-independence, determinism,
  Highlights-integrity and anchor-stability signals of its Confirmation section,
  and leaves the fifth — that regeneration leaves no tracked diff — to delivery
  verification, matching the spec's What Changes. It does not re-open the
  decision, and a kill verdict routes to a superseding ADR rather than to an
  edit of the accepted one.
- `docs/architecture/changelog-fragment-source.md` § 7 owns the mergeability,
  determinism, historical-compatibility, content-integrity and build-performance
  bars; each acceptance criterion cites the row it takes its threshold from, and
  § 7 wins where the two disagree.
- `tools/AGENTS.md`: a new `tools/` script is pure-stdlib Python.
- `docs/product/AGENTS.md`: `/now/` is projected from the changelog and the
  generated JSON is gitignored — the parity arm reads that projection, never a
  committed copy.

## Construction tests

**Integration tests:** none beyond per-task tests. Every task's observable is a
run whose stdout T5 quotes — against this repository for T1 and against a
disposable clone for T4 — so there is no seam left for a cross-task integration
check to cover.

**Manual verification:** none. No user invokes anything this spike produces.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Spike report — `docs/product/research/changelog-fragment-assembly-spike.md` | T5 | The report, with each task's retained stdout quoted | Every figure in the report appears in a quoted run, and the base commit is named |
| Measurement script — `tools/measure-changelog-fragment-merges.py` | T1 | `python3 tools/measure-changelog-fragment-merges.py` output | A clean-checkout run reproduces both arms' conflicting-pair and error counts and leaves `git status` clean |
| Decision rationale — ADR-0123 | T5 | The overall verdict line | A survive verdict obliges nothing; a kill verdict opens a superseding ADR |
| Current architecture — `docs/architecture/changelog-fragment-source.md` | T5 | The report's overall verdict and its build-cost figure | The delta's `Status` line is left at `Draft` on survive and withdrawn on kill; a build-cost figure at or above the § 7 bar leaves it at `Draft` and hands the delivery spec a named performance task |

## Design (LLD)

### Data & schema

The prototype fragment is the minimum that lets T3 answer the anchor question:
TOML front matter delimited by `+++` carrying `schema`, `id`, `date`, and
`packages` as ADR-0123 D2 and the architecture's envelope row state, then a
Markdown body whose only required section is `Highlights`. The spike validates
nothing beyond what a measurement needs — refusal behaviour is delivery-spec
scope, and building it here would mean specifying the schema this spike exists
to inform. Fragment `id` is a lowercase UUIDv4 from stdlib `uuid.uuid4()`;
the anchor under test is `change-` plus that UUID's 32 hexadecimal digits.

Traces to: the anchor and Highlights criteria · contracts: none.
Owned by: T2, T3.

### Interfaces & contracts

The prototype reads the frozen baseline through `tools/build-site.py`'s
`parse_changelog_releases`, loaded by `importlib` from its file path because the
module name contains a hyphen. That is the same seam the fragmentation spike
used, and it is what makes "the prototype and production agree about which `##`
lines are real headings" true rather than assumed. The parity comparison in T3
is against `project_now_highlights` from that same module, so both sides of the
comparison come from the code that ships, and both are serialized the same way
before the byte comparison. T4 wires the same prototype into a disposable
clone's copy of `tools/build-site.py`, which is the only way a timed build
actually reaches the fragment path.

The confined-reader question the architecture raises — whether a `tools/`
script can reach `packages/agentbundle/…/file_safety.py` under the site-build
job — is delivery scope, not spike scope: the prototype reads its own scratch
fixtures, and `tools/check-output-readability.py` already demonstrates the
`importlib`-by-path route works.

Traces to: the parity, determinism and build-cost criteria · contracts: none.
Owned by: T2, T3, T4.

## Tasks

### T1: Fragment branches merge clean where monolith branches do not

**Depends on:** none

**Touches:** tools/measure-changelog-fragment-merges.py

**Tests:**
- Fragment arm: 20 synthetic branches off one named base, each adding a single `docs/product/changelog.d/<uuid>.md`; every unordered pair replayed with the `git merge-tree --write-tree --merge-base` invocation `tools/measure-changelog-conflicts.py` already uses. Verifies the fragment-arm criterion.
- Control arm: the same 20 branches rebuilt to prepend one release section to `docs/product/changelog.md` instead, replayed identically. Verifies the control criterion, and is what stops a zero in the fragment arm from being read as a measurement of nothing.
- Classifier arm: each pair bucketed by `git merge-tree`'s exit status into clean, conflicted, or error — exit 0, exit 1, anything else — and the error bucket reported per arm. Verifies the harness-failure criterion; without this bucket an invocation that errors on every pair is indistinguishable from a clean fragment arm, which is the survive threshold.
- The classifier is exercised against one hand-built pair known to conflict and one known to be clean, and must bucket each correctly before either arm's figure is recorded.
- A clean-checkout run leaves `git status --porcelain` empty, so the script's own scaffolding cannot be mistaken for a repository change. Verifies the worktree-cleanliness criterion.
- no stub (goal-based)

**Approach:**
- Build both arms as detached commits over the same base, never as branches on the working tree, so the measurement cannot disturb a worktree the coordination lease may be sharing.
- Bucket on exit status rather than on whether the output text names a changelog path: `git merge-tree` writes nothing to stdout for a clean merge, so a text scan cannot tell a clean pair from a failed invocation.

**Done when:** `python3 tools/measure-changelog-fragment-merges.py` prints, per arm, the conflicting-pair count and the error count out of 190 pairs, plus its two classifier self-check results, names its base commit, and exits zero with a clean `git status`.

### T2: Assembly output is identical under shuffled enumeration and differs without the sort

**Depends on:** none

**Touches:** none tracked — the prototype lives outside the repository

**Tests:**
- Assemble the frozen baseline plus 20 fragments under 5 shuffled directory enumerations; count distinct output digests. Verifies the determinism criterion.
- Mutation arm: repeat with the canonical sort removed from the prototype and count distinct digests again. Verifies the criterion that the shuffle arm can fail — without it a passing shuffle proves only that the enumeration never varied.
- no stub (goal-based)

**Done when:** the prototype's stdout reports 1 distinct digest across the 5 shuffled runs and more than 1 in the mutation arm, both figures captured for T5.

### T3: The model reproduces today's `/now/` payload and gives each fragment its own anchor

**Depends on:** T2

**Touches:** none tracked

**Tests:**
- Zero-fragment arm: the prototype's payload serialized canonically and compared byte-for-byte against the same serialization of `project_now_highlights` on the live changelog at the named base. Verifies the parity criterion. The counts stay in the output as diagnostics — the live payload at `93bf9cc9e` is 157 groups and 281 bullets — but they are not the comparison, because a reworded, reordered or regrouped payload holds all three counts.
- Twenty-fragment arm: each authored Highlights bullet located in the payload, counting exact-once byte-for-byte matches out of the total. Verifies the Highlights criterion.
- Anchor arm: how many of the 20 fragments produce a group at all, and how many of those groups carry an anchor matching `change-` plus exactly 32 lowercase hexadecimal digits; both counts reported against the fixed denominator of 20, so an assembler emitting no fragment group reports 0 of 20 rather than 0 of 0. Verifies the anchor criterion.
- Historical-anchor arm: every anchor present in the zero-fragment payload located in the twenty-fragment payload, counting those absent or changed. Verifies the historical-anchor criterion.
- no stub (goal-based)

**Done when:** the prototype's stdout carries the zero-fragment arm's byte-comparison result, the Highlights, anchor and historical-anchor counts, and any mismatch named by its anchor value rather than only counted. The group, bullet and anchor-list figures appear alongside as diagnostics.

### T4: Site-build cost with the fragment path wired in is measured against today's build

**Depends on:** T2

**Touches:** none tracked — the timed runs happen in a disposable clone outside this repository

**Tests:**
- Control arm: five timed `make site-build` runs in a disposable clone at `93bf9cc9e`, unmodified, so the control is today's build reading only `docs/product/changelog.md`. Verifies the control half of the build-cost criterion.
- Fragment arm: five timed `make site-build` runs in the same clone with the T2 prototype wired into the site build and a staged corpus of 2,920 fragments present, so the timed path actually enumerates, reads, parses, assembles and projects them. Verifies the treatment half.
- The figure recorded is the fragment median minus the control median, divided by the control median. Verifies the percentage criterion, whose denominator is the control arm.
- The interleaved run order, the discarded warm-up run per arm, and the ten retained durations are all captured. Verifies the run-order criterion.
- This repository's own `git status --porcelain` is empty throughout, and the disposable clone is deleted before the figure is recorded.
- no stub (goal-based)

**Approach:**
- Wire the prototype into the clone's `tools/build-site.py`, not into this repository's. Unwired, the staged fragments are inert files the build never opens, so the median difference would measure filesystem noise and report it as assembly cost — the whole figure would be false while looking well-formed. The clone is why the spec's Never-do rule can still forbid an assembler any build in this repository invokes.
- Interleave the arms — control, fragment, control, fragment — rather than running two blocks, and discard one unmeasured warm-up run per arm. Page cache, tool warm-up and thermal state all drift monotonically across a session, so a block design puts that drift straight into the median difference the 10% bar reads.
- Time the whole `make site-build` rather than the parse alone: the architecture's bar is stated against that target.

**Done when:** the run log carries the interleaved order, two discarded warm-ups, ten retained durations, two medians, and the percentage difference, with the disposable clone deleted.

### T5: The report states four verdicts and one overall verdict against named thresholds

**Depends on:** T1, T2, T3, T4

**Touches:** docs/product/research/changelog-fragment-assembly-spike.md

**Tests:**
- Every figure in the report traces to a quoted run from T1–T4; a figure with no quoted source is a defect, not a rounding. Verifies the criterion that the report contains no figure its stdout lacks.
- The report's header carries the base commit and corpus size, and each measurement section carries a survive or kill line naming the threshold it was judged against. Verifies the verdict and base-commit criteria.
- The report's overall verdict line is checked against the aggregation rule for the four recorded measurement verdicts: kill when merge independence, determinism or parity is kill, survive otherwise. Verifies the aggregation criterion, which the per-measurement verdict bullet above does not reach.
- The report's `Scope` line states what was not measured, following the three prior spikes' scope discipline.
- no stub (goal-based)

**Done when:** the report exists at its destination, every acceptance criterion in `spec.md` is checked, and `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` is clean.

## Rollout

Nothing ships. The only tracked artifacts are one measurement script and one
research document, both inert: no gate, no Makefile target, and no build reads
either. Rollback is deleting them.

## Risks

- **The T4 clone is not isolated.** The clone must be a real second checkout, not a worktree of this repository: a worktree shares the parent's git directory and its `make site-build` would still clean this tree's `build/`, which a concurrent session would read as an unrelated failure.
- **The T4 clone survives the run.** A clone left behind holds a full second copy of the tree and, on a re-run, a warm `build/` that makes the next timing wrong. Delete it before recording the figure, and record the deletion.
- **The prototype and production drift.** Loading `tools/build-site.py` by path pins the agreement, but only at the base commit the run names; a figure quoted later against a moved base is not the same figure.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-09-23: spec approved by eugenelim
- 2026-09-23: plan approved by eugenelim
- 2026-09-23: T3 and T4 base repointed from `5b379c51f` to `93bf9cc9e` and the
  T4 corpus from 2,910 to 2,920 fragments, by eugenelim, after an authorized
  rebase onto `origin/main` rewrote the pinned commit and moved the
  free-standing released-entry count from 291 to 292. Amended before
  `approve-plan` recorded this run's baseline; the 10 x entry-count
  arithmetic and every other task row are unchanged.
