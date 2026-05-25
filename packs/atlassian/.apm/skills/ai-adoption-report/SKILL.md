---
name: ai-adoption-report
description: Use this skill to compare flow-metrics JSON outputs and produce a Markdown comparison report — "how do our flow metrics now compare to pre-AI?", "within Q4 did AI-tagged tickets behave differently from untagged?", "what does Q4 look like across all teams in the program?". Three modes — baseline (two windows, one scope), cohort (within-window AI vs control), program (roll up many scopes for one window). Read-only — consumes flow-metrics JSON files, makes no upstream calls, never invokes flow-metrics / jira / jira-align. Writes only the Markdown report and an optional JSON sidecar.
metadata:
  version: "1.0"
---

# Skill: ai-adoption-report

A read-only workflow skill that consumes one or more `flow-metrics`
JSON outputs and renders a comparison report. It has three modes —
`baseline`, `cohort`, `program` — all sharing one pairing-and-delta
engine. The skill is deliberately boring: pair files, subtract numbers,
render a table. It encodes no judgment about what the deltas mean and
emits no flags; interpretation belongs to the reader.

## When to use

- **`baseline`** — compare a single scope across two windows (pre-AI
  vs current). Two `flow-metrics` JSONs in, deltas out.
- **`cohort`** — surface the within-window AI-cohort vs control split
  that `flow-metrics` already computed via `--cohort-jql`. One JSON in,
  deltas out.
- **`program`** — roll up many scopes for a single window. N JSONs in,
  per-scope rows + aggregates out.
- **Do NOT** use this skill for live metric computation — that's the
  `flow-metrics` skill's job. This skill consumes `flow-metrics`'
  outputs; it never recomputes them and never reads Jira.

## Invocation

Two equivalent forms (both call the same `ai_adoption_report.main`):

```bash
# Installed package — exposes an `ai-adoption-report` shim on PATH:
ai-adoption-report baseline --baseline A.json --current B.json --output report.md

# Or any environment where the package is on PYTHONPATH:
python -m ai_adoption_report baseline --baseline A.json --current B.json --output report.md
```

From a working copy of this pack, add the package to PYTHONPATH first:

```bash
export PYTHONPATH="$(pwd)/scripts:$PYTHONPATH"
python -m ai_adoption_report --help
```

Every example below uses the bare `ai-adoption-report` form; substitute
`python -m ai_adoption_report` if you're invoking from source.

## Inputs

### baseline mode

```
ai-adoption-report baseline --baseline PATH --current PATH --output FILE [common flags]
```

| Flag | Required? | Meaning |
|---|---|---|
| `--baseline PATH` | yes | `flow-metrics` JSON for the prior window. |
| `--current PATH` | yes | `flow-metrics` JSON for the current window. Must share `meta.scope` with `--baseline`; `--baseline.window.to` must be `<=` `--current.window.from` (back-to-back windows allowed). |
| `--include-cohort-breakdown` | no | Append a cohort-vs-control comparison when both inputs carry a `cohort_breakdown` block with matching `meta.cohort_jql`. No-ops with a note when either input lacks `cohort_breakdown`; section omitted with a note when `cohort_jql` values differ. |

### cohort mode

```
ai-adoption-report cohort --input PATH --output FILE [common flags]
```

| Flag | Required? | Meaning |
|---|---|---|
| `--input PATH` | yes | `flow-metrics` JSON produced with `--cohort-jql`. Missing `cohort_breakdown` exits 2. |

### program mode

```
ai-adoption-report program --inputs DIR --window FROM..TO --output FILE [common flags]
```

| Flag | Required? | Meaning |
|---|---|---|
| `--inputs DIR` | yes | Directory of `flow-metrics` JSON files. Globs `*.json` directly in `DIR` (no recursion). |
| `--window FROM..TO` | yes | Two `YYYY-MM-DD` dates separated by `..`. Only inputs whose `meta.window` matches by string equality are included; zero matches exits 2. |
| `--include-cohort-breakdown` | no | Roll up cohort and control sides independently across scopes that carry a `cohort_breakdown` block. Scopes without `cohort_breakdown` are dropped with a note. Per-team flattened rows are excluded from the cohort rollup (`flow-metrics` v1 does not split `per_team` by cohort). |

### Common flags

| Flag | Meaning |
|---|---|
| `--output FILE` | Path to Markdown output. JSON sidecar is written to the same path with `.md` replaced by `.json` (or appended if no extension). |
| `--format markdown\|json\|both` | Output format. Default: `both`. `json` skips Markdown rendering; `markdown` skips the JSON sidecar. |
| `--overwrite` | Replace existing output files. Without it, exit 2 on collision. With `--format both`, the rule applies to both files. |
| `--title TITLE` | Optional title for the Markdown header. Default: `"AI-adoption report — <mode>"`. |
| `--verbose` | Debug logging. |

**Path rules.** All input paths are taken literally — no tilde
expansion, no env-var expansion, no globbing (except `--inputs DIR`
for program mode, which globs `*.json` directly in `DIR` with no
recursion). All paths must resolve inside the current working
directory or its descendants; absolute paths outside CWD exit 2.

## Outputs

The skill writes a Markdown report and (by default) a JSON sidecar:

- **Markdown** (`--output FILE.md`) — fixed section order: title,
  mode-specific header line, `## Summary`, `## Metric deltas`,
  `## Per-scope rows` (program mode only), `## Cohort breakdown`
  (when `--include-cohort-breakdown`), `## Notes`, `## Provenance`.
  Sections absent for a mode are omitted entirely.
- **JSON sidecar** (`FILE.json`, derived from `--output`) — compact
  twin of the Markdown report. `meta.skill_version` plus per-input
  provenance (basename, scope dict + inferred kind, window, both
  config SHAs, upstream `generated_at`, upstream `schema_version`),
  the full `deltas` block, `per_scope` (program mode), optional
  `cohort_breakdown`, and the sorted `notes` array.

`--format` dispatch:

- `both` (default) — both files written atomically. Pre-flight
  collision check covers both targets at once.
- `markdown` — only the Markdown file is written; sidecar skipped.
- `json` — only the sidecar is written; the Markdown renderer is
  **not** invoked. The `--output` path is still interpreted as the
  Markdown-shaped value (sidecar path is derived from it), so
  `--format=json --output report.md` writes `report.json` and never
  touches `report.md`.

For the full output schema (delta math, JSON canonicalisation, scope
canonical representation, metric row order) see
`docs/specs/ai-adoption-report.md` §"Output: Markdown" and §"Output:
JSON sidecar".

## Examples

The three literal commands from spec §"Users and use cases".

### Baseline: pre-AI vs current

```
ai-adoption-report baseline --baseline outputs/PROJ-Foo-2024Q1.json --current outputs/PROJ-Foo-2025Q4.json --output report.md
```

### Cohort: within-window AI vs control

```
ai-adoption-report cohort --input outputs/PROJ-Foo-2025Q4-with-cohort.json --output report.md
```

The input must be a `flow-metrics` run that was invoked with
`--cohort-jql`; the skill reads the existing `cohort_breakdown`
block.

### Program: roll up across teams

```
ai-adoption-report program --inputs outputs/ --window 2025-10-01..2025-12-31 --output q4-program.md
```

Skill globs `*.json` in the input directory, filters to files whose
`meta.window` matches `--window`, and aggregates.

## Exit codes

| Exit | When |
|---|---|
| 0 | Report written. |
| 1 | Bug in the skill (uncaught exception). |
| 2 | Bad input: missing/extra flags, unreadable file, invalid JSON, missing required meta field, scope mismatch (baseline mode), window overlap (baseline mode), missing `cohort_breakdown` (cohort mode), no inputs matched window (program mode), overlapping scopes (program mode), output exists without `--overwrite`. |

Error messages always name the offending file (basename) and the
specific field or rule that triggered the exit. No bare "validation
failed" messages.

## Reproducibility

The skill writes `meta.generated_at` (UTC ISO-8601 seconds-precision
with trailing `Z`) from the runtime clock at report-write time. For
deterministic-build tests and golden-file diffs, set the env var
**`AI_ADOPTION_REPORT_GENERATED_AT`** to a fixed ISO-8601 string —
the skill uses that value verbatim instead of reading the clock. All
other output is deterministic given the same inputs and the same
skill version: object keys are codepoint-sorted (except the `deltas`
block, which follows the canonical metric row order), floats are
rounded to 4 decimal places at serialisation, and the per-input
`meta.inputs` array is sorted by `basename` codepoint-ascending.
Setting `LC_ALL=C` is recommended for byte-identical reruns across
hosts.

## Read-only contract

This skill makes no upstream calls — it does NOT invoke
`flow-metrics`, `jira`, `jira-align`, or any other skill or external
service. Its only inputs are local `flow-metrics` JSON files; its
only filesystem writes are `--output` (the Markdown report) and its
derived `.json` sidecar (via a temp file in the same parent directory
for atomic replace). The contract is enforced by tests in
`tests/test_t9_packaging.py` that patch the `subprocess` /
`os.spawn*` / `os.system` surface and snapshot the working
directory before and after a run.

## Spec reference

See `docs/specs/ai-adoption-report.md` for:

- the full Inputs table and validation rules,
- delta math (zero baseline, null on either side, distribution
  per-percentile rule),
- program-mode aggregation math (throughput-weighted `rework_rate`,
  flow-distribution-denominator-weighted `defect_ratio`,
  median-of-medians for distribution metrics),
- cohort-rollup independence (cohort and control sides aggregated
  separately, never combined into one weighted average),
- per-team flattening rules and overlap detection,
- Markdown rendering rules (Unicode minus in numeric cells, em-dash
  for absent / undefined cells, scope/team name escaping),
- JSON canonicalisation (codepoint-sorted keys, 4 dp floats,
  `deltas` block in canonical metric order),
- the complete contract-test inventory.
