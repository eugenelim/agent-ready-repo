# Extracted review corpus

Raw reviewer reports, adjudications, and the single shadow-audit measurement
from the review-effectiveness study's prospective cohort. Moved into the
repository on 2026-10-02 so the study stands alone.

## Why these files are here

Every finding count in
[`review-effectiveness-baseline.json`](../review-effectiveness-baseline.json)
and [`review-effectiveness-report.md`](../review-effectiveness-report.md) — raw,
sustained, refuted, blockers, repair-origin — was derived from these reports.
Until this extraction they lived only under `.context/`, which is **gitignored**,
and partly inside a second worktree. The numbers were published while the
material behind them sat in untracked local directories, and three files the
record cites were already gone by the time this was noticed.

That is the same failure the study documents about itself: evidence recorded
somewhere nothing preserves. Here it is fixed rather than described.

## What is here — 128 files, 1.0 MB

### `case-2-visual-target-confirmation/` — 13 files

Four adversarial and four shaping spec-review rounds, a `PROVENANCE.md`, and
**the only shadow audit the study ever ran**:

| File | What it is |
| --- | --- |
| `shadow/shadow-prompt.txt` | the exact measurement prompt, **53,388 bytes** |
| `shadow/case2-shadow-adversarial-raw.md` | what the cold auditor returned |
| `shadow/case2-shadow-usage.json` | the returned-token telemetry |
| `shadow/shadow-launch-observed.json` | the observed launch and its pre-launch gates |

The prompt's byte count matches `prompt_bytes.used: 53388` recorded in the
ledger exactly, which confirms this is the artifact that was measured. This
measurement is irreplaceable: it is the single data point behind the finding
that eight shadow audits would cost 2.35× the frozen cohort token ceiling.

### `case-3-visual-target-field/` — 37 files

Pre-EXECUTE adversarial rounds with their adjudications, post-gates adversarial
and experience-reviewer rounds, and two archived post-gates adjudications. The
experience-reviewer files are the basis for the observation that the role
produced no unique sustained finding on this diff.

### `case-4-visual-target-rung-precondition/` — 78 files

The complete corpus for case 4:

| Kind | Files |
| --- | ---: |
| `N-pre-execute-*-raw.md` | 27 |
| `N-pre-execute-*-adjudication.md` | 21 |
| `N-post-repair-*-raw.md` | 15 |
| `N-post-gates-*-raw.md` | 10 |
| other adjudication artifacts | 3 |
| reviewer briefs | 2 |
| **total** | **78** |

By role, counting any filename mentioning it: adversarial-reviewer 32,
security-reviewer 31, quality-engineer 10, findings-adjudication 2. Role counts
and kind counts are different cuts of the same 78 files and do not sum to it.

## Reading these against the record

The ledger's per-round counts are the derived view; these are the source. A
round's `raw` count is the numbered findings in that round's `-raw.md` files,
and its `sustained` count is what the matching `-adjudication.md` carried
forward. Both can be re-derived independently, which is the point of keeping
them.

What these files **cannot** supply is the contract's required per-finding rows.
They carry no per-finding token, wall-clock or prose-churn attribution, because
that telemetry was session-local and was never written down. That is blocker B
in the report, and no amount of re-reading closes it. Case 2's
`shadow/case2-shadow-usage.json` is the one exception, and it covers the
measurement side only.

## Provenance and redaction

Copied verbatim on 2026-10-02 from:

- `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/` → case 4
- the `visual-target-confirmation` worktree's
  `.context/reviews/1adcfbc1-0d36-401b-9f3d-ebfc2493790a/` → case 3
- the same worktree's `.context/reviews/visual-target-confirmation/` → case 2

One change was made: absolute paths under the controller's home directory were
rewritten to `~`, per the repository rule against committing identifying paths.
No other edit. All 128 files were screened for emails, tokens and credentials;
none were found.

Case 1 has no corpus, which is why it was excluded — see the report.
