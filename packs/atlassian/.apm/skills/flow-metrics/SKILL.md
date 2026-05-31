---
name: flow-metrics
description: Use this skill when the user asks for DORA / Flow Framework metrics over a Jira scope -- "what's our cycle time this quarter for PROJ", "give me throughput and WIP for the Foo team", "compare flow efficiency before/after the AI-pairing rollout via a cohort split", "rollup flow metrics across program 42". Computes cycle time, lead time, throughput, WIP, flow load, rework rate, flow efficiency, flow distribution, and defect ratio from Jira changelogs (optionally joined with Jira Align for program / portfolio scope). Read-only -- never transitions, comments, creates, updates, or deletes Jira data. Do NOT use for live-dashboard streaming, deployment-event metrics (Change Failure Rate / MTTR proper), or anything requiring a tracker that isn't Jira.
metadata:
  version: "0.1.0"
---

# Skill: flow-metrics

This skill is the one place to compute Flow Framework / DORA-style
metrics over a Jira scope. It composes two upstream skills and emits a
canonical JSON / CSV / JSONL block; it does **not** invent new tracker
verbs or replicate them inline.

- **`jira` skill** (sibling in this pack) — every Jira read: `check`,
  `whoami`, `get-issue`, `search`, `get-project`, plus a tightly-
  allowlisted set of `raw GET` paths for the custom-field catalog,
  project-status enumeration, and per-issue changelog pagination.
- **`jira-align` skill** (sibling in this pack) — used **only** for
  `--program-id` / `--portfolio-id` scope, and **only** for the four
  team / program / portfolio enumeration paths. Time-in-state numbers
  always come from Jira's changelog.

The pipeline (config validation, scope JQL, changelog walk, per-issue
derivation, aggregation, cohort split, per-team rollup, notes, meta,
output rendering, caching) lives in `scripts/flow_metrics/`. This SKILL.md
tells the agent how to **invoke** the CLI for common flows; for design
details, read the inline module docstrings.

## Cross-skill invocation — name, not path

This skill names sibling skills (`jira`, `jira-align`) by their `name:`
field, never by path. Install locations vary by IDE and scope, and
skills can be renamed at install time. The agent's harness resolves the
name to whatever location the user picked. **If you find yourself
writing a hardcoded skill path, stop — look up the skill by name
instead.**

Install guidance for the named dependencies lives in `manifest.json`
under `deps.skills` — that's a *where to get them* hint, not a runtime
path.

## Prerequisites

Before computing metrics, confirm:

1. The `jira` skill is installed and authenticated. Invoke it:
   `jira: check`. Exit 0 → proceed. Exit 2 → tell the user to run
   `credential-setup` skill themselves; do not attempt to read
   `~/.agentbundle/credentials.env` from this skill.
2. For program / portfolio scope, the `jira-align` skill is installed
   and authenticated. If `--program-id` or `--portfolio-id` is in play
   and `jira-align: check` fails, exit 3 and surface upstream stderr
   verbatim.
3. The Jira `team_field.id` you've configured (default
   `customfield_10001` in the shipped state config) exists in this
   instance's field catalog. If it doesn't, the skill exits 2 at
   startup naming the missing field.

## Invocation

The skill ships one CLI. Two equivalent forms (both call the same
`flow_metrics.main`):

```bash
# Installed package — exposes a `flow-metrics` shim on PATH:
flow-metrics --project PROJ

# Or any environment where the package is on PYTHONPATH:
python -m flow_metrics --project PROJ
```

The spec's examples use the bare `flow-metrics` form. From a working
copy of this pack, add the package to PYTHONPATH first:

```bash
export PYTHONPATH="$(pwd)/scripts:$PYTHONPATH"
python -m flow_metrics --help
```

Every example below uses the bare form; substitute `python -m
flow_metrics` if you're invoking from a clone.

### CLI flags

The full flag surface:

- **`--project KEY`** — Jira project key. Mutually exclusive with
  `--program-id` / `--portfolio-id`.
- **`--team NAME`** — Optional sub-scope within a project. Resolution
  rule depends on `team_field.kind` (`single_value` or `array`). Only
  valid with `--project`.
- **`--program-id ID`** — Jira Align program ID. Triggers a Jira Align
  join for team mapping.
- **`--portfolio-id ID`** — Jira Align portfolio ID. Triggers a rollup
  across constituent programs / teams.
- **`--from ISO`**, **`--to ISO`** — Window bounds, `YYYY-MM-DD`. Both
  inclusive of the named day. Default: `--to = today (UTC)`,
  `--from = today − 90 days`.
- **`--jql "<expr>"`** — Extra JQL ANDed into the scope query. Always
  wrapped as `(<scope>) AND (<--jql expr>)` — your expression is
  parenthesised verbatim.
- **`--align-filter "<expr>"`** — Extra OData ANDed into Jira Align
  queries with the same parenthesisation rule.
- **`--cohort-jql "<expr>"`** — Issues matching this JQL are marked
  `cohort: true` in the output. Aggregate mode emits a
  `cohort_breakdown` block; per-issue mode tags each row.
- **`--metrics LIST`** — Comma list. Default: all ten. Names:
  `cycle_time, lead_time, throughput, wip, flow_load, rework_rate,
  flow_time, flow_efficiency, flow_distribution, defect_ratio`.
  Unrequested metrics are **omitted** from `aggregates` (not emitted
  as `null`); `meta.metrics_requested` records the resolved list.
- **`--state-config FILE`** — JSON file mapping raw statuses to
  canonical states. Defaults to the shipped
  `references/states.default.json`.
- **`--issuetype-config FILE`** — JSON file mapping issuetypes to Flow
  Distribution buckets. Defaults to `references/issuetypes.default.json`.
- **`--team-field-override ID`** — Override `team_field.id` from the
  state config for this run.
- **`--align-join-field NAME`** — Override the Jira ↔ Jira Align join
  field. Defaults to the `align_join_field` entry in the state config;
  if neither is set and Jira Align scope is requested, exit 2.
- **`--align-teams-path PATH`** — Override the Jira Align endpoint
  used to enumerate teams in a program. Must match one of the four
  allowlisted `jira-align` `raw GET` patterns.
- **`--include-subtasks`** — Include subtasks in throughput, cycle
  time, lead time, flow efficiency, rework rate. Default: false.
  Flow Distribution is always insensitive to this flag.
- **`--format json|csv`** — Output format. Default: `json`.
- **`--output FILE`** — Write to file instead of stdout. Required for
  `--per-issue`. Path is rejected if it lands under a system root.
- **`--per-issue`** — Emit one JSONL row per issue with all derived
  fields, instead of aggregates. Requires `--output`.
- **`--no-cache`** — Bypass the on-disk cache at
  `.context/flow-metrics/cache/<cache-key>.jsonl`.
- **`--verbose`** — Debug logging (state-transition walks, cache hits,
  upstream skill invocations).
- **`--yes`** — Overwrite `--output FILE` without prompting.

**Exactly one** of `--project`, `--program-id`, `--portfolio-id` must be
provided. `--team` is only valid with `--project`.

## Common flows

Each example is a literal command line the agent can run.

### Project-scope, default 90-day window

```bash
flow-metrics --project PROJ
```

JSON to stdout. The shipped default state config maps the common Jira
workflow ("To Do" / "In Progress" / "Done" / "Won't Do") out of the
box.

### Project-scope with a specific window and JQL filter

```bash
flow-metrics \
  --project PROJ \
  --from 2026-02-01 --to 2026-04-30 \
  --jql 'labels = ai-assisted AND component = checkout'
```

### Jira Align program scope (joins via Jira Align)

```bash
flow-metrics \
  --program-id 42 \
  --align-join-field "Program ID" \
  --from 2026-02-01 --to 2026-04-30
```

`--align-join-field` is required for Align scope unless the state
config provides it.

### Cohort split (A/B comparison)

```bash
flow-metrics \
  --project PROJ \
  --cohort-jql 'labels = ai-assisted' \
  --format json
```

Output gains a `cohort_breakdown` block with `cohort` and `control`
sides. Cohort-jql matching zero issues produces an empty cohort with
`throughput: 0` and `null` percentiles — exit 0.

### Filter to a subset of metrics

```bash
flow-metrics \
  --project PROJ \
  --metrics throughput,cycle_time,defect_ratio
```

Only the requested metrics appear in `aggregates`. `meta.metrics_requested`
records the resolved list. `flow_distribution` and `defect_ratio` are
separate keys — requesting one does not auto-include the other.

### Bypass the on-disk cache

```bash
flow-metrics --project PROJ --no-cache
```

Use when the underlying Jira data has changed and you suspect cache
staleness. Cache lives at
`.context/flow-metrics/cache/<cache-key>.jsonl`.

### Per-issue dump (downstream consumer input)

```bash
flow-metrics \
  --project PROJ \
  --per-issue \
  --output .context/flow-metrics/per-issue.jsonl
```

JSONL on disk, one row per in-scope issue. Downstream consumers
(notably `ai-adoption-report`) MUST filter on
`delivered_in_window: true` before computing delivery-based metrics.

## Don't

- **Don't bypass the upstream-skill allowlist.** This skill invokes
  only the allowlisted verbs and `raw GET` paths. Any other invocation
  is a regression. If a verb is missing, extend the `jira` or
  `jira-align` skill — don't shim around it here.
- **Don't read `credentials.env` from this skill.** Credentials live
  in the `jira` / `jira-align` skills and are isolated from this one.
  Authentication failures surface as upstream exit 3; the fix is to
  run the upstream skill's `setup_credentials.sh`, not to read its
  config file from here.
- **Don't issue write verbs.** This skill is read-only. No
  `create-issue`, `update-issue`, `delete-issue`, `transition`,
  `comment`, `attach` — and no `raw POST` / `PUT` / `PATCH` / `DELETE`
  to any upstream skill. A contract test wraps the upstream skills
  and fails on any out-of-allowlist call.
- **Don't add `numpy` or any other pip dependency.** v1 is stdlib
  only — percentiles use `statistics.quantiles(..., method="exclusive")`
  at indices 49 / 74 / 89 for p50 / p75 / p90. The schema validator
  used by the contract test is the same stdlib-only posture; do not
  add `jsonschema` to satisfy it.
- **Don't infer the `align_join_field`.** Instances vary; silently
  picking `customfield_10001` is a wrong-answer risk. If neither
  `--align-join-field` nor the state config sets it and Align scope is
  requested, exit 2 with a clear message.
- **Don't normalise JQL semantically in v1.** `normalize_jql` only
  collapses whitespace; two semantically equivalent JQL expressions
  with different clause order produce different cache files. That's
  the documented v1 trade.
- **Don't paraphrase the metric definitions.** They are pinned
  and tested. If a metric "feels wrong", read the module docstrings
  before changing anything.

## Security rules

This skill operates under a **read-only contract** with credential
isolation:

- **Read-only contract:** the upstream-skill allowlist names every
  verb and `raw GET` path this skill is permitted to invoke. Any other
  upstream invocation, including the `raw POST` / `PUT` / `PATCH` /
  `DELETE` escape hatches, is forbidden and enforced by a contract test
  that wraps the upstream skills.
- **Credential isolation:** this skill **never reads
  `credentials.env`** or any other secret file directly. Credentials
  belong to the `jira` / `jira-align` skills; this skill invokes them
  by name and lets them load their own credentials. If `jira: check`
  fails, surface the error and tell the user to run the upstream
  skill's setup — do not attempt to authenticate on its behalf.
- **No write verbs:** this skill emits no `POST` / `PUT` / `PATCH` /
  `DELETE` HTTP requests, and invokes no write-class verbs (transition,
  comment, create, update, delete, attach) on any upstream skill. The
  output is metrics; it never mutates Jira state.
- **Path safety:** `--output`, `--state-config`, `--issuetype-config`
  are rejected if they resolve under a privileged system root (POSIX:
  `/etc`, `/sys`, `/proc`, `/dev`, `/boot`; Windows: the system drive's
  `Windows`, `Program Files`, and `Program Files (x86)` directories),
  or if they contain a null byte. Exit 2.

## Edge cases

The key edge cases to know about:

- **Cancelled issues.** An issue transitioning into a
  `terminal_non_delivery_states` canonical state (default: `cancelled`)
  in-window with no first-ever delivery in-window is
  cancelled-in-window. Excluded from throughput, cycle time, lead
  time, flow efficiency, and Flow Distribution; counted in `notes`.
  A cancel-then-reopen-still-active-at-`--to` issue is also in WIP —
  both signals are reported simultaneously.
- **Empty cohort.** `--cohort-jql` matching zero issues produces an
  empty cohort sub-object with `throughput: 0` and percentile fields
  `null`. The skill exits 0.
- **Permission undercounting.** Jira silently omits issues the caller
  lacks browse permission on. For project scope, the skill compares
  the JQL count against `jira: get-project <KEY>` and emits a `notes`
  entry recording the delta. Field-level permission undercount on the
  `team_field` is also detected and reported as a synthetic
  `(no team)` row in `per_team`. The skill does not retry as a
  different user or escalate. `meta.caller` records the calling
  account so downstream consumers can spot cross-account
  discrepancies.
- **Changelog pagination (Cloud regression).** Cloud Jira's
  `/search/jql` endpoint returns at most ~100 inline changelog entries
  per issue. The skill detects "more pages exist" via `isLast`,
  `nextPageToken`, or `histories.length < total`, then drains via
  `jira: raw GET issue/<KEY>/changelog`. Long-lived issues silently
  lose cycle-time math without this, so the pagination contract is
  required, not optional.
- **Unmapped raw status.** Any raw status not listed under any
  `canonical_states` entry causes exit 2 at startup with the offending
  name. The shipped default config maps "Won't Do" / "Cancelled" /
  "Duplicate" to `cancelled` deliberately so first-run users on a
  normal Jira workflow get accurate throughput out of the box.
- **Issue with no commitment_state transition** (closed directly from
  backlog). Delivered-in-window = true; cycle-eligible = false.
  Contributes to throughput and lead time. Excluded from cycle time.
- **`--per-issue` without `--output`.** Exit 2 — JSONL must go to a
  file.

## Output contract

The canonical wire format is pinned by
`references/output.schema.json` (JSON Schema draft 2020-12). The shape:

- `meta` — caller, scope, window, sources, metrics_requested,
  schema_version, generated_at, state_config_sha, issuetype_config_sha,
  per_team_double_counted, and optionally `cohort_jql` (omitted when
  `--cohort-jql` was not provided).
- `aggregates` — one key per requested metric. Unrequested metrics
  are **absent**, not null. `additionalProperties: false` in the
  schema pins this.
- `cohort_breakdown` — optional. Emitted only when `--cohort-jql` is
  set AND `--per-issue` is not set. Carries `cohort` and `control`
  sub-objects with the same metric shape as `aggregates`.
- `per_team` — optional array of per-team rows. Emitted when scope is
  `--program-id` / `--portfolio-id`, or when scope is `--project` and
  the resolved issue set spans more than one distinct team value.
- `notes` — array of descriptive strings, lex-sorted.

Output is canonicalised at serialisation: codepoint-sorted object keys
(except `flow_distribution` which uses a fixed bucket order), floats
rounded to 4 decimal places, per_team sorted by team name codepoint.
The schema does **not** re-validate canonicalisation rules — those are
enforced by the renderer's contract tests in T10.

## Further reading

The module docstrings in `scripts/flow_metrics/` cover:

- metric definitions and core population predicates (`predicates.py`, `aggregate.py`),
- the upstream-skill allowlist and verbs (`upstream.py`),
- state-config and issuetype-config schemas (`config.py`),
- canonicalisation rules and output rendering (`output.py`),
- cache-key derivation (`cache.py`),
- edge-case handling (`per_issue.py`, `notes.py`).
