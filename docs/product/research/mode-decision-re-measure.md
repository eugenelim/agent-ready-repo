# Mode-decision measurements: when to re-measure

- **Date:** 2026-11-05
- **Owner:** eugenelim, Platform Core maintainer
- **Spec:** [risk-trigger record](../../specs/risk-trigger-record/spec.md)

Three questions about the work-loop's mode decision and its review evidence
were measured on 2026-11-05. Each answer was too thin to act on. This note
gives each one's baseline, the condition that makes a re-measure worth doing,
and how to count.

## Unfamiliar as the only trigger

- **Baseline:** 0 of 51 recorded full-mode decisions named Unfamiliar as the
  only trigger. 3 named Unfamiliar beside other triggers. The 51 came from
  `Mode:` lines in specs, and no spec added after 2026-10-24 carries one, so
  nothing covers Unfamiliar's current wording ("you cannot predict the
  design") or the one-spike allowance.
- **Re-measure when:** 20 specs on `main` carry a live `Risk triggers:` line
  whose value is not `none`. A live line is one the spec-status lint reads:
  it starts `- **Risk triggers:**` at column 0 in the preamble, outside any HTML
  comment or code fence, and its value is not empty once comments are hidden.
- **Method:** on freshly fetched `origin/main`, read each
  `docs/specs/*/spec.md` and keep only live lines. Hide HTML comments first,
  drop a line whose value is then empty (an unfilled template line is one),
  and trim spaces around each comma-separated token, as the lint does. Count
  the specs whose value is not `none` (the trigger), and the specs whose only
  token is `unfamiliar` (the answer). The work-loop lint's
  `risk_trigger_lines` function returns exactly the live lines, so a script
  can call it rather than re-implement the rule. Each line records the
  decision its spec was approved under.

## RFC-0111's effect on full-mode runs

- **Baseline:** no measurable cut. Full mode's share of merged code changes was
  83% (20 of 24) in the 6 days before #1642 merged on 2026-10-29 06:15 UTC, and
  87% (27 of 31) in the 6 days after. No merged PR after #1642 said it split an
  independent bundle or ran a guidance edit light.
- **Re-measure when:** on or after 2026-11-28 06:15 UTC, when 30 days of
  merged PRs exist after #1642.
- **Method:** compare the 30 days before #1642 with the 30 days after. Class
  each merged PR as full when its body's `review-verdict.v1` block says
  `"mode": "full"`, or, with no verdict mode, when it changes a spec or plan
  and code; as light when the verdict says light or direct-light, or it changes
  code with no spec or plan; otherwise docs-only. Report full mode's share of
  code changes on each side. Also count PRs whose own text records the RFC-0111
  routing (a bundle shown independent and split, or a guidance edit run
  light), and specs added after #1642 whose live `Risk triggers:` line holds only
  `multi-feature` or only `structural-interface`, the two triggers RFC-0111
  narrows.

## Code-stage findings that carry a run

- **Baseline:** 27 of 292 code-stage findings (9.2%) named a command and an
  observed result. 21 of the 27 (7.2% of all) were real runs on a hand read.
  Counting runs reported without the literal command, the share was about 16%.
  Only 23 code-stage findings postdated #1677 (verify entries, merged
  2026-11-02 19:33 UTC), and 2 of those carried a run.
- **Re-measure when:** 100 code-stage findings exist from reviews after #1677,
  and no earlier than 2026-11-30, four weeks after #1677 merged.
- **Method:** collect raw reviewer reports from supervisor runs
  (`<N>-<stage>-<reviewer>-raw.md`) and hand-named review folders. Code stage
  means a `post-gates` or `code` stage, or a folder name containing `impl` or
  `code`. Split each report into findings. A finding carries a run when it has
  both a command (a backticked invocation such as `python3 x`, `pytest`, or
  `./x`, or a fenced block starting with one; a bare `file.py:12` does not
  count) and an observed result (an exit code or status, a pass or fail count,
  a traceback, printed output, or a re-run report). Hand-check a seeded sample
  of 30 hits. Copy the review folders before counting, because worktrees are
  deleted over time.
