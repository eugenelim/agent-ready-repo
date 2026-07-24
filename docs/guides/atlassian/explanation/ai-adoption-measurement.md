# Measuring AI adoption with flow metrics

The `flow-metrics` and `ai-adoption-report` skills answer one question: **are the teams that use AI coding assistants delivering differently from the teams that aren't?** This doc explains the measurement model, why self-certification produces trustworthy data, what the metrics actually tell you, and where the limits of this approach sit.

## The two-skill workflow

`flow-metrics` reads Jira changelogs to compute how long issues took (cycle time), how many shipped (throughput), and how work was distributed across types. It never modifies Jira. It writes canonical JSON.

`ai-adoption-report` takes two or more `flow-metrics` JSON files and renders a comparison report. It never reads Jira — it only reads the files `flow-metrics` already produced. The split between the two skills is intentional: computing metrics and interpreting change are separate jobs, and keeping them separate means you can re-run the report against historical snapshots without going back to Jira.

**Three comparison patterns:**

| Pattern | Mode | Use when |
|---|---|---|
| Before vs after AI rollout | `baseline` | Proving ROI over time — same scope, two time windows |
| AI-tagged vs untagged, same window | `cohort` | Ongoing sprint-over-sprint tracking |
| Multiple teams, single window | `program` | Rolling up to program or value stream level |

## The self-certification model

There is no automatic way to know from Jira whether an engineer used an AI tool on a given story. Jira doesn't know which IDE they opened or whether Copilot drafted the implementation. The person who knows is the engineer.

Self-certification makes that knowledge visible. Engineers apply a Jira label — `ai-assisted` — to stories where AI made a material contribution. `flow-metrics` then splits stories on that label: `--cohort-jql 'labels = ai-assisted'`. The cohort (labeled) and control (unlabeled) sides are measured identically and placed side by side in the report.

**What crosses the "material contribution" bar:** AI drafted the core logic, debugged a non-obvious problem, wrote tests or documentation that would have taken significant manual effort, or proposed the design that the engineer adopted. One-line autocomplete does not cross the bar.

**Why the ownership sits with engineers, not tooling:** Measurement imposed top-down gets gamed. Self-certification treats engineers as the experts they are — they know better than any automated tool whether the AI contributed — and gives them a positive signal to surface rather than a metric imposed on them. Teams that label consistently get better data and a clearer case for the tooling investment. Teams that don't label have a smaller cohort, which is its own signal worth discussing.

**Trust horizon:** A single sprint of labeling is too small for reliable percentiles. Two to three sprints of consistent labeling produces a usable cohort. Delivery leads should focus on making the labeling habit stick; the data quality follows from the habit, not from auditing individual stories.

## The metrics and what they tell you

`flow-metrics` computes ten metrics. Not all of them show a clean AI-cohort signal. The five with the most consistent signal:

**Cycle time (p50 / p75 / p90)**
Time from first active-state transition to delivery. The three percentiles matter differently: p50 is the typical story, p90 is the hard tail. AI assistance tends to compress p90 most — the hardest, most uncertain stories are the ones where AI makes the biggest difference. If you can report only one metric, this is it.

**Throughput**
Count of issues delivered in the window. Higher throughput in the AI cohort is a positive signal, but read it alongside cycle time: if AI-assisted stories skew systematically smaller or simpler, the throughput advantage may partly reflect scope, not speed. Use throughput as supporting evidence, not a primary claim.

**Defect ratio**
Defects as a fraction of all delivered work. A lower ratio means more time on new value, less on rework. If the AI cohort's defect ratio is higher than the control's, that's a flag: it may mean AI-assisted code is generating downstream bugs. Worth investigating before attributing the difference to anything else.

**Rework rate**
Stories reopened or returned after being marked done. Lower means "done" actually means done. Teams report that AI assistance during development — particularly for test generation and edge-case review — tends to reduce rework.

**Flow distribution**
Breakdown of delivered work by type: features, defects, technical debt, risk. If AI is helping teams move faster on the mechanical parts of their work, the distribution shifts toward features over time. This metric is better for showing a trend over quarters than for a single-window comparison.

## What the model does not measure

Understanding the limits is part of understanding the model:

- **Change Failure Rate and MTTR.** These DORA metrics require deployment event data from CI/CD pipelines. Jira status transitions don't carry that signal. If you need these, you need a separate data source (your deployment tooling, an observability platform).

- **Individual engineer productivity.** The skills measure work at the story level. There is intentionally no per-engineer breakdown. Building one from this data would misrepresent what the data says and create the wrong incentives.

- **Code quality.** Test coverage, cyclomatic complexity, static-analysis findings — use your CI quality gates for these. They're not in Jira changelogs.

- **Adoption breadth at enterprise scale, in a single command.** `flow-metrics` runs one scope at a time. Measuring 100 teams requires 100 invocations. The `program` mode of `ai-adoption-report` handles the rollup, but the data collection step must be scripted at that scale. See [Report AI adoption as a delivery lead](../how-to/report-ai-adoption-as-a-delivery-lead.md#roll-up-to-program-value-stream-level) for the scripted pattern.

- **Real-time or live metrics.** Each run is a point-in-time snapshot with a defined window. There is no streaming or live-dashboard mode.

- **Unmeasured adoption.** Stories where AI was used but not labeled are in the control group. The model measures what teams declare, not what they actually do. Better labeling produces better data; the model cannot compensate for inconsistent labeling after the fact.
