# Manual QA — pack-activation-evals (Tier A runner)

Records the live-model checks for AC1 (real detector parse) and AC10 (bounded
artifact inspection). The runner is report-only dev tooling; a full
`core` + `converters` sweep (~hundreds of live `claude -p` calls) is the
scheduled `pack-evals.yml` workflow's job, not a per-PR gate. This pass
exercises **every live seam** on a bounded scale, which is what AC1/AC10's
mechanism hinges on.

Environment: `claude` 2.1.185 on PATH (the spec's target version).

## 1. Detector format — why `stream-json --verbose` (RFC-0037 § Errata E1)

Captured real `claude -p` output two ways against a projected `core` skill:

- `--output-format json`: a **result-only** envelope —
  `{type, subtype, result, usage, permission_denials, …}`, **no `tool_use`
  events**. Activation is not observable here.
- `--output-format stream-json --verbose`: the activation appears as an
  `assistant` event whose `message.content[]` holds
  `{"type":"tool_use","name":"Skill","input":{"skill":"new-spec","args":…}}`,
  and the stream ends with a `{"type":"result","result":"…"}` event. This is
  the format the runner uses.

## 2. Real end-to-end run through `run_eval`

Ran the real `ClaudeCodeDetector` (real `agentbundle` projection + live
`claude -p stream-json --verbose --allowed-tools Skill`) against a 1-skill
mini-pack wrapping `core`'s **actual `new-spec` skill**, 1 run/query:

| query | should_trigger | observed trigger_rate | graded |
| --- | --- | --- | --- |
| "Let's write a spec for a new CSV export feature" | true | 1.0 | pass |
| "Fix the bug where the login button does nothing" | false | 0.0 | pass |

Workspace written exactly as specified:

```
.eval-workspace/mini/iteration-1/
  new-spec/q00/with_skill/run-1/outputs/result.txt
  new-spec/q01/with_skill/run-1/outputs/result.txt
  summary.json
```

Reserved grading slots (`without_skill/`, `timing.json`, `grading.json`,
`benchmark.json`) were **not** produced (Tier A only). The real
`agentbundle` projection placed only the pack's skills under
`.projection/.claude/skills/`.

## 3. Bounded-artifact inspection (AC10)

The emitted `summary.json` contained only `{pack, adapter, runs, iteration,
skills:{<skill>:{queries:[{query_id, query, should_trigger, trigger_rate,
passed, errored_runs, exclusivity_violations}], pass_count, total,
error_count}}}` — all bounded fields; **no** `stderr`, no process environment,
no `ANTHROPIC_API_KEY`. (`error_count`/`errored_runs` distinguish a harness
failure — non-zero `claude` exit, timeout, truncated stream — from a genuine
non-activation, so an all-zero `trigger_rate` from a broken CLI is not misread
as a regression.) The per-run `outputs/result.txt`
held only the parsed `.result` text. The CI artifact glob
(`.eval-workspace/**/summary.json`) uploads only `summary.json`, excluding the
`outputs/` captures. The bounded shape is also locked by
`tools/test-run-pack-evals.py` (asserts the summary carries no key / stderr /
env).

## 4. In-harness mode (Phase 2, RFC-0037 § Errata E2) — live validation

Validated the in-harness premise live by dispatching read-only sub-contexts
(Claude Code `Agent` tool) for two of `core/new-spec`'s queries, each given the
5 covered core skills' descriptions and asked which it would activate:

| query | reported | tool calls |
| --- | --- | --- |
| "Let's write a spec for a new CSV export feature" | `new-spec` | **0** |
| "Fix the bug where the login button does nothing" | `bug-fix` | **0** |

Both sub-contexts returned a judgement only — **0 tool calls** — confirming the
containment control (the dispatched context never executes skill bodies or
project tools against the query string; AC25). Feeding the reports through the
real CLI (`run-pack-evals.py --pack core --mode in-harness --reports …`)
produced a `mode: in-harness`, `fidelity: reported` summary that graded the
positive `1.0`/pass and flagged `bug-fix` as an exclusivity violation — the full
Phase-2 path end-to-end. The reported signal is a description-match judgement
(lower fidelity than headless's observed router event), labelled as such.

## Scope note

Full per-pack sweeps over `core` + `converters` (every covered skill ×
~18 queries × 3 runs) run report-only in `pack-evals.yml`; their first
scheduled/dispatch run produces the per-skill trigger-rate baselines. This
manual pass validates the live mechanism, not the calibration baseline (the
latter is RFC-0037 Open Q1, deferred).
