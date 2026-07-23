# Report AI adoption as a delivery lead

This guide is for delivery leads who run two to eight teams, need to report AI adoption impact upward to program or value stream leadership, and are not responsible for running the CLI themselves — the agent does that. It covers the full journey from first-time setup through a stakeholder-ready report.

For the conceptual background on the measurement model and self-certification, read [Measuring AI adoption with flow metrics](../explanation/ai-adoption-measurement.md) first.

## Before you start

### Install the pack and set up credentials

Ask your agent to install the atlassian pack if it is not already installed:

> "Install the atlassian pack and set up my Jira credentials."

The agent installs the pack and walks you through credential setup interactively. You will need:

- A Jira API token — generated from your Atlassian account at `id.atlassian.com` under Security → API tokens.
- Your Jira Cloud URL, for example `https://yourorg.atlassian.net`.

The token is stored in your OS keychain and never written to a file the agent can read. The agent tells you when credential setup is complete.

For Jira Data Center or Server instances that block API tokens (common in enterprise environments with SSO enforcement), see [Authenticate Jira and Confluence with SSO cookies](authenticate-jira-confluence-with-sso-cookies.md).

For program-level reports that join Jira Align for team structure, you also need Jira Align credentials:

> "Set up my Jira Align credentials."

### Confirm credentials are working

> "Check my Jira credentials."

The agent runs a credential check. Exit 0 means you're ready. If it fails, the agent will prompt you to re-run credential setup — it will not retry automatically.

For the technical credential model, see [The `atlassian` pack as a system](../explanation/atlassian-pack.md#the-auth-model).

## Set up the labeling convention with your teams

Before you can run a cohort comparison, your teams need to apply the `ai-assisted` Jira label to stories where AI made a material contribution. Establish this as a team habit before your first reporting window.

### Agree on a definition

Define "AI-assisted" with your teams before the sprint starts. A workable bar: **AI materially contributed to the solution** — not just autocomplete for a variable name. Stories that cross the bar include:

- The agent drafted the core logic or the implementation approach the engineer adopted.
- AI debugged a non-obvious problem that would otherwise have taken significant investigation.
- The agent generated tests or documentation that would have taken an hour or more of manual work.

One-line autocomplete, auto-formatting, and spell-checking do not cross the bar.

### Who applies the label and when

The engineer — or their AI agent in an agentic workflow — applies the label when marking the story done, or earlier in development if AI's involvement is clear from the start. In an agentic workflow where the agent writes the solution and transitions the ticket, the agent can apply the label in the same step:

> "Fix issue PROJ-1234, transition it to Done, and add the label 'ai-assisted'."

### What to do with unlabeled stories

Do not retroactively label stories en masse — that introduces noise. Let unlabeled stories remain the control group. The cohort comparison works because the control and cohort are measured against the same window. An unlabeled story is not a problem; it is the baseline.

### Trust horizon

One sprint of consistent labeling produces a small, potentially noisy cohort. Two to three sprints produces enough stories for reliable percentile metrics. If the cohort has fewer than ten stories in a window, the cycle time p50/p75/p90 figures will be unreliable. Continue collecting before drawing conclusions; the report will flag a small cohort.

## Measure at team level

### Option A — Within-window cohort split (recommended for ongoing tracking)

Run metrics for a single window and split stories into AI-assisted (labeled) and control (unlabeled) within it. This is the right approach for sprint-over-sprint tracking because it holds the window and scope constant.

> "Run Q1 2026 flow metrics for project PROJ with an AI-assisted cohort split, and produce the adoption report."

The agent runs:

```bash
flow-metrics \
  --project PROJ \
  --from 2026-01-01 --to 2026-03-31 \
  --cohort-jql 'labels = ai-assisted' \
  --format json \
  --output outputs/PROJ-2026Q1-cohort.json

ai-adoption-report cohort \
  --input outputs/PROJ-2026Q1-cohort.json \
  --output reports/PROJ-2026Q1-adoption.md
```

The report shows cycle time, throughput, defect ratio, rework rate, and flow distribution side-by-side for the AI cohort and the control group.

### Option B — Before/after comparison (for proving ROI over time)

Compare the same project across two windows — before the AI rollout and after. This shows aggregate improvement for the whole team, whether or not stories are individually labeled.

> "Compare our Q1 2024 metrics against Q1 2026 metrics for project PROJ to show AI adoption impact."

The agent runs:

```bash
flow-metrics --project PROJ --from 2024-01-01 --to 2024-03-31 \
  --format json --output outputs/PROJ-2024Q1.json

flow-metrics --project PROJ --from 2026-01-01 --to 2026-03-31 \
  --format json --output outputs/PROJ-2026Q1.json

ai-adoption-report baseline \
  --baseline outputs/PROJ-2024Q1.json \
  --current outputs/PROJ-2026Q1.json \
  --output reports/PROJ-baseline-comparison.md
```

The `baseline` window must end on or before the `current` window starts. Use `--include-cohort-breakdown` if both runs included `--cohort-jql` and you want to see the cohort delta alongside the window delta in one report.

### Narrowing the scope

By default, `flow-metrics` includes all issues in the project that transitioned to a delivered state within the window. Narrow the scope with a JQL filter if you want to exclude components, specific teams, or issue types:

> "Run flow metrics for project PROJ, Q1 2026, only the Mobile component, with cohort split."

The agent adds `--jql 'component = "Mobile"'`. Your JQL expression is ANDed onto the scope query automatically — the cohort JQL is separate and does not interfere with the scope filter.

## Roll up to program / value stream level

### With Jira Align

If your organisation uses Jira Align to manage the program structure (teams, ARTs, value streams), you can collect program-level metrics in a single invocation. You need the Jira Align program ID — ask your Jira Align administrator — and the name of the Jira custom field that links Jira issues to Jira Align (called the "join field").

> "Run flow metrics for program 42 in Jira Align, Q1 2026, with AI-assisted cohort split."

The agent runs:

```bash
flow-metrics \
  --program-id 42 \
  --align-join-field "Program ID" \
  --cohort-jql 'labels = ai-assisted' \
  --from 2026-01-01 --to 2026-03-31 \
  --format json \
  --output outputs/program-42-2026Q1.json

ai-adoption-report cohort \
  --input outputs/program-42-2026Q1.json \
  --output reports/program-42-2026Q1-adoption.md
```

The JSON output includes a `per_team` block with team-by-team breakdowns. The adoption report surfaces which teams have the highest AI adoption cohort share and how their metrics compare.

### Without Jira Align (project-by-project rollup)

If your teams don't use Jira Align, collect metrics for each project individually, then roll them up using `ai-adoption-report program` mode:

> "Run Q1 2026 flow metrics for PROJ1, PROJ2, and PROJ3 with cohort split, then produce a program-level adoption report."

The agent runs:

```bash
mkdir -p outputs/q1-2026

for proj in PROJ1 PROJ2 PROJ3; do
  flow-metrics \
    --project "$proj" \
    --cohort-jql 'labels = ai-assisted' \
    --from 2026-01-01 --to 2026-03-31 \
    --format json \
    --output "outputs/q1-2026/${proj}.json"
done

ai-adoption-report program \
  --inputs outputs/q1-2026/ \
  --window 2026-01-01..2026-03-31 \
  --include-cohort-breakdown \
  --output reports/program-2026Q1-adoption.md
```

The program-mode report includes per-scope rows (one per project) plus aggregated totals across all included scopes.

### Scale: what this looks like for many teams

For three to ten projects, the approach above is the right one. For larger programs:

**10–30 projects:** Script the `flow-metrics` loop. Each invocation takes 30–90 seconds depending on issue volume. Ask your agent to write a script:

> "Write a script that runs flow-metrics for each project in this list with Q1 2026 dates and ai-assisted cohort split, writing each output to outputs/q1-2026/."

**100+ teams:** This is at the edge of what you can do interactively in a session. The data collection step scales linearly with project count and must be scripted. The rollup step (`ai-adoption-report program`) handles any number of JSON files in the directory with no additional effort — it's the collection that's serial. Consider scheduling the collection script as a nightly or weekly job and keeping the outputs directory as a standing dataset.

What is not currently possible in a single command: running `flow-metrics` across hundreds of projects simultaneously. Each invocation is one Jira project or one Jira Align program — there is no "all projects" mode, and parallelising the invocations within one agent session is constrained by the Jira API rate limits on your instance.

## Convert the report to a shareable format

The report is a Markdown file with a predictable section order: Summary, Metric deltas, Per-scope rows (program mode), Cohort breakdown (if requested), Notes, Provenance. Several paths to stakeholder-ready content:

### Publish to Confluence

The fastest path if your organisation uses Confluence for async reporting:

> "Publish the Q1 adoption report to Confluence in the ENG space under 'AI Adoption Tracking'."

The agent uses `confluence-publisher` to push the Markdown directly. The page renders with formatted tables, code-highlighted metric values, and the full provenance section so readers can see which Jira projects and windows the data covers.

### Paste into a doc or slide deck

The Markdown tables render in most tools without additional formatting:

- **Microsoft Teams posts or Wiki pages** — paste the Markdown directly; Teams renders tables.
- **Google Docs** — paste into a blank doc; the table rows carry over. Reformat the heading levels as needed.
- **PowerPoint or Keynote** — take the `## Summary` paragraph and the key metric rows from `## Metric deltas` for your headline slide. Three numbers are better than ten for an exec audience: cycle time p50 delta, throughput delta, defect ratio delta, each expressed as a percentage change.
- **Notion or Linear** — both render Markdown tables natively.

### Work with the JSON sidecar for dashboards

By default, `ai-adoption-report` writes both a Markdown report and a JSON sidecar. The sidecar contains the same delta data in structured form:

```bash
ai-adoption-report cohort \
  --input outputs/PROJ-2026Q1-cohort.json \
  --output reports/PROJ-2026Q1-adoption.md \
  --format both
```

The file `reports/PROJ-2026Q1-adoption.json` holds `deltas`, `cohort_breakdown`, `per_scope` (program mode), and full provenance. Feed it into Power BI, Tableau, or a Python script to produce a dashboard or trend chart.

### Write an executive summary from the report

For a brief to leadership (three bullets, no tables):

> "Summarise the Q1 adoption report in three sentences suitable for a leadership update. Lead with cycle time improvement, then throughput, then quality."

The agent reads the report and drafts the summary. Review it — the agent cannot tell you whether the numbers match leadership's expectations or prior commitments.

## What the key metrics mean

**Cycle time (p50 / p75 / p90)**
Time from when work started to when it was delivered. The three percentiles tell different stories: p50 is the typical story; p90 is the hard tail — the 90th-percentile story took at least this long. AI assistance tends to compress p90 the most, because the hardest stories benefit most from AI helping unblock the engineer. If you can lead with one metric, lead with cycle time p50 and p90, and the percentage change between the AI cohort and the control.

**Throughput**
Count of issues delivered in the window. Higher in the AI cohort is a good signal, but read it with context: if AI-assisted stories systematically skew smaller or simpler (which is sometimes the case as engineers reach for AI on well-defined tasks), the throughput advantage partly reflects scope, not speed. Support the throughput claim with cycle time data.

**Defect ratio**
Defects as a fraction of all delivered work. Lower means more time on new value, less on bug-fixing. A rising defect ratio in the AI cohort — compared to control — is a red flag worth investigating before attributing the difference to AI. It can mean AI-assisted code is introducing defects downstream, or that the labeling convention is capturing a different population of work than expected.

**Rework rate**
Stories reopened or returned after being marked done. Lower rework means "done" actually means done. AI assistance during development — test generation, edge-case reasoning — tends to reduce rework. This metric also reflects the reliability of your definition of done, so interpret it alongside team process context.

**Flow distribution**
Breakdown of delivered work by type: features, defects, technical debt, risk. A healthy distribution is feature-heavy. If AI is accelerating the mechanical parts of technical debt and defect resolution, the distribution shifts toward features over time. This is better as a quarterly trend metric than a single-window comparison.

## What this does not cover

- **Change Failure Rate and MTTR** — These DORA metrics require deployment event data from your CI/CD tooling. Jira status transitions don't carry that signal; the atlassian pack doesn't see your deployment pipeline.

- **Individual engineer productivity** — The skills measure work at the story level, not at the engineer level. There is intentionally no per-engineer breakdown.

- **Code quality metrics** — Test coverage, complexity, static-analysis findings — use your CI quality gates. These are not in Jira changelogs.

- **Automatically detected AI usage** — The `ai-assisted` label is self-reported. Stories where AI was used but not labeled appear in the control group. No automation can recover those stories after the fact. The model measures what teams declare; better labeling produces better data.

For more on the measurement model's design and its limits, see [Measuring AI adoption with flow metrics](../explanation/ai-adoption-measurement.md).
