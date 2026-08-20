# RFC-0090 evidence base

Supporting material for RFC-0090. The RFC body carries the argument; this file
carries the proof. Every external source below was fetched on 2026-08-19 and
confirmed to contain the claim attributed to it. Where the common summary of a
source drifts from what the source says, the drift is recorded.

## External sources

| # | Source | Verified claim (exact wording where quoted) | Confidence / limit |
|---|---|---|---|
| 1 | [Google eng-practices, Small CLs](https://github.com/google/eng-practices/blob/master/review/developer/small-cls.md) | "100 lines is usually a reasonable size for a CL, and 1000 lines is usually too large, but it's up to the judgment of your reviewer." Also "It's usually best to do refactorings in a separate CL from feature changes or bug fixes" and, for unavoidably large CLs, "get consent from your reviewers in advance". | Strong practitioner guidance. Not agent-specific, not an empirical study. |
| 2 | [Chromium cl_tips](https://chromium.googlesource.com/chromium/src/+/main/docs/cl_tips.md) | "Try to keep changes below 500 lines of code – including tests." Allows 200 production + 600 test lines when tests follow a regular pattern. "CLs should only effect one type of change." | Strong operational prior art from a large codebase. Not a universal limit. |
| 3 | [SmartBear / Cisco case study](https://static0.smartbear.co/support/media/resources/cc/book/code-review-cisco-case-study.pdf) | Prescriptive: "a reviewer will probably not be able to review more than 300-400 lines of code before his performance" degrades; "total review time should be under 90 minutes"; "after 60 minutes reviewers 'wear out' and stop finding additional defects". **Descriptive, not prescriptive:** "most reviews are smaller than 200 lines of code". | 2006 study; 2,500 reviews, 3.2M LOC, 50 developers at Cisco MeetingPlace. In-situ vendor study, not a controlled experiment. **The widely-quoted "recommends under 200 LOC" misreads a distribution observation as advice.** |
| 4 | di Biase, Bruntink, van Deursen, Bacchelli, "The effects of change decomposition on code review — a controlled experiment", PeerJ CS 5:e193 (2019). [DOI](https://doi.org/10.7717/peerj-cs.193) · [PeerJ](https://peerj.com/articles/cs-193/) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7924728/) | Decomposition "leads to fewer wrongly reported issues" and increases context-seeking, "yet impacts neither understanding the change rationale nor the number of found defects." | Controlled experiment, 28 developers (professionals and graduate students). **Does not show decomposition finds more bugs.** Establishes no numeric cap. |
| 5 | [OpenAI, How OpenAI uses Codex](https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf) | "Codex works best with well-scoped tasks that would take you or a teammate about an hour to complete or a few hundred lines of code to implement. As models improve, expect the size of the tasks it can take on to increase." Ask-mode plan first for large changes; task queue as a "lightweight backlog" for "tangential ideas, partial work, or incidental fixes". | Vendor guidance about one agent. Explicitly time-bound — the document says the workable size will grow. |
| 6 | [OpenAI, Harness engineering](https://openai.com/index/harness-engineering/) | Single Codex runs "upwards of six hours". "working depth-first: breaking down larger goals into smaller building blocks (design, code, review, test...)". Deterministic rails — linters, type checkers, unit tests — block the agent from marking a task complete. | Vendor practice report. Direct fetch returned HTTP 403; claims confirmed from search snippets of the primary URL. |
| 7 | [OpenAI, Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/) | "Some issues produce multiple PRs across repos". Agent work "no longer tied to PRs". A Planner decomposes work into a task tree scheduled by "dependency ordering and file lock availability". | Vendor spec announcement. Direct fetch returned HTTP 403; claims confirmed from search snippets of the primary URL. |
| 8 | [GitHub Copilot, get the best results](https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results) | An ideal task carries a clear problem description, "Complete acceptance criteria on what a good solution looks like", and which files change. Avoid cross-repository knowledge, deep domain knowledge, substantial business logic, security/PII/auth, and ambiguous open-ended work. | Vendor task-scoping guidance. |
| 9 | [GitHub, About stacked PRs](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) | "When you generate a lot of code at once, often with AI agents, a stack gives each change a place to go. An agent completes one task, then starts the next task that builds on it. That sequence maps directly onto a stack: one pull request per task, each based on the one below." | The most direct vendor mapping of agent work to review units. Guidance, not evidence of outcomes. |
| 10 | [Graphite, best practices for reviewing stacks](https://graphite.com/docs/best-practices-for-reviewing-stacks) | "Set up an automation to comment on PRs larger than 250 lines of code or 25 files changed to encourage authors to break up larger changes into stacks." Also "Review a PR in a stack as though it was an independent change". | Practitioner / vendor guidance. Not an independent empirical threshold. |
| 11 | Agent checkpoint practice: [Aider](https://aider.chat/docs/git.html) · [Cline](https://docs.cline.bot/core-workflows/checkpoints) · [Cursor](https://docs.cursor.com/agent/chat/checkpoints) · [Anthropic, How Anthropic teams use Claude Code](https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf) | Aider: "Whenever aider edits a file, it commits those changes with a descriptive commit message." Cline: "a shadow Git repository separate from your project's actual Git history". Cursor: "Checkpoints are stored locally and separate from Git. Only use them for undoing Agent changes; use Git for permanent version control." Anthropic RL Engineering team: "an iterative approach that includes frequent checkpointing and rollbacks", a "try and rollback" methodology. | Converges on cheap rollback. **No tool prescribes a numeric commit size.** Supports the recovery-checkpoint vs semantic-commit distinction only. The Cursor URL carrying an `/en/` path segment is stale and redirects to the docs root; the link above is the live page. |
| 12 | [arXiv 2606.15689](https://arxiv.org/abs/2606.15689), "Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review" (Kumar, Bararia, Raj) · [arXiv 2603.26130](https://arxiv.org/abs/2603.26130), "SWE-PRBench" (D. Kumar) | 2606.15689: "diff size is the dominant predictor of review quality, with F1 dropping from 0.657 on diffs under 10 lines to 0.043 on diffs over 150 lines." 2603.26130: "all 8 models degrade monotonically from config_A to config_C"; a "structured 2,000-token diff-with-summary prompt outperforms a 2,500-token full-context prompt". | **Low confidence.** Recent preprints. 2606.15689 evaluates 5 models on 150 samples. Sufficient to reject the claim that an AI reviewer makes a large undifferentiated PR safe. **Not sufficient to set any production threshold.** F1 is the harmonic mean of precision and recall. |

## Repository measurements

Method: `git log --first-parent main`, taking commits whose subject ends
`(#NNNN)` as landed PRs (the repository squash-merges), then `git show
--numstat` per commit. Changed lines are insertions plus deletions. Sample is
the most recent 400 first-parent commits, of which 337 are PR-shaped. Measured
2026-08-19.

### Landed PR size

| Metric | Median | Mean | Max |
|---|---|---|---|
| Changed lines | 790 | 2,257 | 38,331 |
| Files changed | 11 | 23 | 329 |

Share of the 337 landed PRs exceeding each published threshold:

| Threshold | Source of the threshold | Share over |
|---|---|---|
| 250 lines / 25 files | Graphite warn level | 71% / 25% |
| 400 lines | Current repository rule; SmartBear reviewer capacity | 64% |
| 500 lines | Chromium | 58% |
| 1,000 lines | Google "usually too large" | 44% |
| 5,000 lines | — | 11% |

Largest landed PRs by changed lines: 104 files / 38,331 lines; 113 / 33,170;
175 / 28,536; 124 / 28,193; 82 / 25,388; 203 / 21,968; 31 / 20,038;
69 / 19,019; 207 / 17,254; 250 / 14,646.

### Single-file concentration

Measured two ways, because the denominator changes the answer completely.

Across the 214 landed PRs with at least 400 total changed lines, using **total
changed lines** as the denominator: maximum single-file share is 100%, and 131
of 214 (61%) have a file at or above 20% of the diff. The most concentrated
cases are single documents — `docs/rfc/0079-codebase-context-pack.md` at 100%
of a 3,570-line diff, and repeated `docs/rfc/0088-notes/spikes/` archive edits
at 98–99%. A single-document change is reviewable as one unit, so total-line
share is the wrong signal.

Excluding documentation (`docs/`, `*.md`, `guides/`, `CHANGELOG`,
`workspace.toml`) and generated output (`dist/`, `marketplace.json`,
`.claude/`, `.agents/`, `package-lock.json`), across the 91 landed PRs carrying
at least 400 authored lines:

| Statistic | Single-file share of authored lines |
|---|---|
| Median | 28% |
| p75 | 52% |
| p90 | 62% |
| Max | 99% |

| Condition | PRs meeting it |
|---|---|
| A file at or above 30% of authored lines | 40 of 91 (44%) |
| A file at or above 40% | 32 of 91 (35%) |
| A file at or above 50% | 24 of 91 (26%) |
| A file at or above 60% | 11 of 91 (12%) |
| A file at or above 75% | 2 of 91 (2%) |
| A file of at least 1,000 authored lines | 17 |
| A file of at least 2,000 authored lines | 8 |
| A file of at least 3,000 authored lines | 3 |

Most concentrated authored files observed: `tools/test_marketplace_envelope_parity.py`
at 99.0% (1,302 of 1,315); `tools/test-build-check-workflow.py` at 65.2%
(1,966 of 3,016); `tools/test_workspace_status.py` at 64.9% (2,298 of 3,542);
`packages/agentbundle/agentbundle/workspace_mcp.py` at 61.6% (1,800 of 2,922).

Limits: one repository, historical, no review-outcome or defect data. These
figures calibrate triage thresholds. They carry no claim about defect risk.

### Convention conflict

`docs/specs/` contains 114 occurrences of the phrase "one PR" as an explicit
per-spec delivery declaration, including on specs sized 48 acceptance criteria
and 15 tasks, and 40 acceptance criteria and 10 tasks.

`Depends on:` appears in 305 of 380 spec directories. The observed dependency
distribution is 426 tasks declaring `none`, 293 declaring `T1`, 117 `T2`,
56 `T3`, 51 `T1, T2`, and 45 `T1, T2, T3`. The highest task number seen is 14.
Dependency structure suitable for deriving stack layers already exists, though
task quality varies and the field is not universal.

### Provenance of the current rule

Commit `92edf24827866aee44db53b88d432aac6d02589a`, dated 2026-05-17, subject
"docs(conventions): add PR size target and name Shift Left in enforcement".
The commit body states the intent: the section "gains a one-line size target
(~100-line aim, ~400-line split threshold unless the change is genuinely
atomic)", which "gives 'limit the diff to what the request requires' a
quantitative anchor." The commit cites no empirical source for either number.

### Motivating case

The reported session shape — roughly 17,000 changed lines with roughly 6,000 in
one file — was not found as a landed PR in `main` history. The nearest landed
analogue is `4f5b978f`, 20,038 changed lines across 31 files, whose largest file
is 3,676 lines (18% of total changed lines). Whether the reported 6,000-line
file was authored or generated was not established, which is why the policy
routes concentrated volume through both an authored-line trigger and a
total-volume trigger.

## Decomposition analysis of the wide-change analogue

`4f5b978f` ("feat(workspace-status): enforce canonical routing invariants"),
20,038 changed lines across 31 files, is the largest landed PR carrying a
written plan. Deduplicating its changed files by content hash:

| Component | Lines | Share |
|---|---:|---:|
| Byte-identical replicated copies | 9,021 | 45% |
| Distinct implementation | 4,844 | 24% |
| Distinct tests | 5,736 | 29% |
| Distinct docs and spec | 437 | 2% |

The replication is dominated by one file. `workspace_status_engine.py` appears
at four paths — the pack source under `packs/core/.apm/`, two agent projections
(`.claude/`, `.agents/`), and a packaged copy at
`packages/agentbundle/agentbundle/_data/` — all byte-identical at content hash
`3fc1febc092d`, 3,676 lines each. That one file contributes 7,149 duplicate
lines, 36% of the whole PR.

Its plan declares four tasks in a strict linear chain: T1 → T2 → T3 → T4, each
depending on the previous. A linear chain is the canonical stack shape, so the
work was decomposable into four dependent layers. Four layers would have carried
roughly 2,754 distinct lines each (about 1,211 implementation lines), a sevenfold
reduction in review-unit size — while still sitting about three times above a
400-authored-line threshold. Reaching that threshold would have required roughly
twelve tasks. The plan had four, averaging 5,009 diff lines per task.

The conclusion is that decomposition was available and would have helped
substantially, but task granularity at specification time was the binding
constraint, not pull-request discipline at merge time.

## Replication across wide changes

Content-hash deduplication applied to the 116 landed PRs of at least 400 changed
lines in the most recent 160 first-parent commits:

| Statistic | Replicated-copy share of the diff |
|---|---|
| Median | 0% |
| Mean | 7% |
| Maximum | 71% |

| Condition | PRs |
|---|---|
| At least 10% of the diff is byte-identical replication | 26 of 116 (22%) |
| At least 25% | 16 of 116 (14%) |
| At least 40% | 5 of 116 (4%) |

Replication is rare in typical changes but concentrated in the largest ones. The
six largest PRs in the sample carry replication shares of 36.8%, 39.2%, 40.6%,
40.2%, 45.0%, and 39.4% — on diffs of 33,170, 28,536, 25,388, 21,968, 20,038,
and 17,254 lines respectively. Raw `git diff --numstat` therefore overstates the
review burden of exactly the changes this policy targets, by roughly 1.6 to 1.8
times. Detection needs no new tooling: identical content hashes across paths in
one diff are computable from `git show` output.

## Reach: how much work is specification-tracked

Across the 337 landed PRs sampled, 76 (23%) carry a `Spec: docs/specs/...`
commit footer and 261 (77%) do not.

| Group | PRs | Median lines | Mean | Over 400 lines | Total volume |
|---|---:|---:|---:|---:|---:|
| With `Spec:` footer | 76 (23%) | 822 | 2,748 | 79% | 208,810 |
| Without | 261 (77%) | 712 | 2,115 | 59% | 551,917 |

Two conclusions follow, and they pull in different directions.

First, most change volume — 551,917 lines, 73% of the total — lands outside the
specification-tracked path. Guidance that lives only in a workflow skill invoked
during specification-driven work cannot reach it. The conventions text, which
applies to every pull request regardless of how the work was produced, is the
surface with full reach.

Second, specification-tracked work is not smaller. Its median is 822 lines
against 712, and 79% of it exceeds 400 lines against 59%. Routing more work
through the planning loop would not by itself reduce review-unit size, because
the loop as it stands does not size review units.

A caveat on the measurement: the absence of a `Spec:` footer does not prove a
planning loop was skipped. Light-mode work-loop uses a lean inline specification
that produces no file under `docs/specs/`, and therefore no footer. Git history
cannot separate light-mode loop runs from work done outside the loop entirely.
Tool usage analytics is the appropriate instrument for that distinction; this
measurement establishes only how much work is traceable to a written
specification.

## The measured quantities

The policy distinguishes raw diff lines from what a reviewer actually reads.
Measured over 187 landed PRs. Generated paths (`.claude/`, `.agents/`, `dist/`,
`marketplace.json`, `package-lock.json`) are removed first, then byte-identical
copies are collapsed using post-image blob SHAs from `git diff --raw`. Removing
generated paths before deduplication matters: otherwise a projection can claim
the content hash that belongs to its own source, and the source is dropped from
the count.

| Quantity | Median | Over 400 |
|---|---:|---:|
| Raw diff lines | 1,068 | 72% |
| After deduplication and removing generated output | 1,057 | 70% |
| Code plus behaviour-bearing content, prose excluded | 231 | 40% |

Totals: 460,993 reviewable authored lines, of which 227,923 are code plus
behaviour-bearing content. Non-executable documentation prose is therefore about
51% of reviewable authored lines.

Two results matter for the policy.

Deduplication barely moves the population, from 72% to 70%. Replication is
concentrated in a handful of very large changes rather than spread across the
repository, so deduplication matters for fair triage of the largest PRs and not
for the headline rate.

Prose is the dominant contributor. Excluding non-executable documentation drops
the median from 1,057 to 231 and the over-400 share from 70% to 40%. Every
external source cited in this file measures code review; none measures prose.

## Classification must follow role, not file extension

An earlier version of this measurement treated every `.md` file as documentation
prose. That is wrong in this repository, and the same error in policy would
exempt the surface the policy exists to govern. The repository contains 127
`SKILL.md` files and 473 markdown files under `packs/*/.apm/`. Those files are
agent instruction sets: they define shipped behaviour, and editing one changes
what adopters' agents do. Two `.mdx` files under `docs-site/` carry interpreted
content. An extension-based carve-out would allow several hundred lines of agent
behaviour to be rewritten without ever tripping a split signal, including edits
to the work-loop instruction file this RFC itself proposes to change.

Classification therefore follows operational role. Non-executable explanatory
text addressed to people is prose and is sized by coherence. Behaviour-bearing
content is authored work whatever its extension, including agent instruction
files, agent and command definitions, interpreted content embedded in
documentation, and fenced code that is extracted, executed, or tested rather
than merely illustrated. A file mixing both is classified by its
behaviour-bearing portion.

A caution on comparability: the 337-PR figures elsewhere in this file are raw
diff lines. The 187-PR figures above separate the quantities. Raw-line history
and authored-line policy thresholds are different measures and should not be
compared directly.

## Cadence and the shape of the distribution

Measured over 234 landed PRs carrying behaviour or test content, across 24
active days (2026-07-27 to 2026-08-19).

| Statistic | Reviewable behaviour and test lines |
|---|---:|
| Median | 152 |
| p75 | 877 |
| p90 | 2,452 |
| p95 | 5,300 |
| Max | 17,275 |

Cadence is 9.75 PRs per active day. The median is already inside every
threshold this file cites: Google's roughly 100, Chromium's 500, and the
SmartBear reviewer-capacity range of 300 to 400. The distribution is a healthy
median with a thin and very heavy tail.

Applying generic split thresholds to that distribution is destructive. Modelling
each PR as splitting into `ceil(lines / threshold)` units:

| Threshold | PRs split | Review-unit multiplier | PRs per day |
|---:|---:|---:|---:|
| 100 | 54% | 10.6x | 119 |
| 400 | 36% | 3.2x | 36 |
| 800 | 27% | 2.0x | 22 |
| 2,000 | 13% | 1.3x | 15 |

Volume concentrates in the tail: PRs over 400 lines are 36% of the corpus but
95% of volume; over 2,000, 13% and 71%; over 5,000, 6% and 52%; over 10,000, 2%
and 28%.

## The tail is not one shape

Of the 34 PRs above 2,000 reviewable behaviour and test lines, classified by
median lines per changed file:

| Shape | Count | Character |
|---|---:|---|
| WIDE, 60 or fewer lines per file | 23 | repo-wide mechanical spread |
| MIXED, 60 to 200 | 9 | |
| DEEP, 200 or more | 2 | concentrated authoring |

Examples of the WIDE shape: a governance-marker strip touching 319 files at a
median of 6 lines each; a test-collection refactor of 17,275 lines across 85
files at a median of 24. Splitting a change of that shape into 2,000-line slices
produces eight pull requests of the same undifferentiated change and makes none
of them reviewable. Splitting helps the DEEP and MIXED shapes only.

## Where the trigger cannot apply

Eight of 234 PRs, 3.4%, contain a single file whose behaviour and test change
exceeds 2,000 lines. The largest single-file change in the corpus is 3,676
lines; p95 is 1,469 and the median is 126.

| Single file | Lines |
|---|---:|
| `workspace_status_engine.py` | 3,676 |
| a `project-knowledge` script | 3,340 |
| `test_loop_engine.py` | 3,229 |
| `test-loop-engine.py` | 2,906 |
| an OKF compiler script | 2,434 |
| `test_loop_guards.py` | 2,354 |
| `tools/test_workspace_status.py` | 2,298 |
| a self-host build-pipeline test | 2,274 |

Five of the eight are test files, which is why disproportionate test volume for
a single unit is treated as one review unit rather than as an overrun. Chromium
already allows this, permitting 200 production lines beside 600 test lines when
the tests follow a regular pattern.

Breaking changes are not indivisible. All three in the corpus are spread rather
than concentrated, and the largest — an engine export boundary change of 14,445
lines — has a largest single file of only 2,274, so an expand, migrate, contract
sequence applies.

## Net effect of the tail trigger with widened ride-alongs

The tail trigger at 2,000 catches 34 PRs. The 23 WIDE ones take reproducibility
proof rather than splitting, so they add no units. The 11 MIXED and DEEP ones
split, adding 27 units.

Against that, widening ride-alongs absorbs work that currently lands as separate
pull requests. Classifying strictly by mechanical intent in the subject and
excluding feature, performance and security work gives 60 candidates, 26% of the
corpus: 52 hand-made at 200 lines or fewer with a median of 28, and 8
reproducible wide-shaped changes with a median of 408.

| Absorption rate | Net review units | Per day | Change from 9.75 |
|---:|---:|---:|---:|
| 0% | 261 | 10.88 | +1.12 |
| 25% | 246 | 10.25 | +0.50 |
| 50% | 231 | 9.62 | -0.12 |
| 75% | 216 | 9.00 | -0.75 |
| 100% | 201 | 8.38 | -1.38 |

Break-even is near 46% absorption. Above it the combined policy reduces the
number of review units rather than increasing it.

Limits of this model. Absorbability is inferred from commit subjects, not from
verifying that a host change existed in the same area and time window, so full
absorption is unreachable. The 234-PR baseline excludes pull requests with no
behaviour or test content. The 341 currently deferred items — 177 in
`workspace.toml [backlog].open` and 164 `(deferred: ...)` markers across 73
specs — are not counted, so their mechanical share is upside beyond the table.
