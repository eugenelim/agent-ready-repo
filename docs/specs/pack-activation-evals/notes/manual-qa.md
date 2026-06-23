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

The emitted `summary.json` contained only `{pack, adapter, mode, fidelity,
runs, iteration, skills:{<skill>:{queries:[{query_id, query, should_trigger,
trigger_rate, passed, errored_runs, exclusivity_violations}], pass_count,
total, error_count}}}` (in-harness summaries add `provenance`) — all bounded
fields; **no** `stderr`, no process environment, no `ANTHROPIC_API_KEY`. (`error_count`/`errored_runs` distinguish a harness
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

## 5. Behavior/output check (Phase 3, RFC-0037 § Errata E3) — live validation

Validated the full B-lite loop end-to-end. A sub-context was dispatched to act
**only inside an OS-temp working directory** (the procedure's containment),
simulating a skill run on the prompt "write the report": it produced `out.txt`
and a `.eval-output.txt` log (`OUTPUT: out.txt`), writing nothing outside the
dir. `grade_behavior` then **re-derived** the deterministic post-conditions from
that directory itself — `expect.produces` (`out.txt` exists) and
`output_contains`/`output_excludes` (`OUTPUT:` present, no `Traceback`) — and
graded the eval **PASS**, labelled `mode: in-harness`, `tier: B-lite`,
`fidelity: observed+attested`, `provenance: operator-attested`. The re-derivation
is genuine (the runner reads the real artifacts; a unit test confirms deleting
the artifact flips the grade to fail, and a missing workspace fails closed).

**Real end-to-end run (2026-06-22).** Beyond the proxy, a genuine B-lite pass
was run against the real **`markdown-to-html`** skill, which ships an `expect`
block on eval id 8 (`packs/converters/.apm/skills/markdown-to-html/evals/evals.json`):

- a temp copy of the skill got its npm deps (`marked` + `highlight.js`) — never
  creating `node_modules` under `packs/`;
- `run-pack-evals.py --pack converters --prepare-workspace markdown-to-html/8`
  seeded a confined OS-temp working dir with the `evals/files/sample.md` fixture;
- the **real** `node scripts/render.js sample.md` ran there → produced
  `sample.html` and printed `OUTPUT: …`, `SECTIONS: 2`, `MERMAID: no` (captured to
  `.eval-output.txt`);
- `--mode in-harness --check behavior` then **re-derived** the deterministic
  checks from the working dir — `expect.produces` (`sample.html` exists) and
  `output_contains` (`OUTPUT:`, `SECTIONS:`) — and graded **eval 8 `ok`**.
  Evals 1–7 (human-authored Tier-B craft, no `expect` block, not run this pass)
  correctly **fail-closed as errored** (unmeasured ≠ pass).

So the B-lite path is now validated against a real skill that really executes
and really produces an artifact the runner inspects — not only the proxy.

**B-lite coverage across the `converters` skills (2026-06-22).** Each covered
skill now ships an `expect`-block eval + an `evals/files/` fixture, and was run
end-to-end (deps installed per the skill's own `## Prerequisites`; the skill
really executed in a confined per-eval workspace; the runner re-derived the
deterministic checks):

| skill | eval | deps (temp-installed) | result |
| --- | --- | --- | --- |
| markdown-to-html | 8 | npm `marked` + `highlight.js` | ✅ `ok` (produces `sample.html`) |
| markdown-to-docx | 6 | `docxtpl` (template-less render) | ✅ `ok` (produces `sample.docx`) |
| markdown-to-pptx | 6 | `python-pptx` (default template) | ✅ `ok` (produces `sample.pptx`) |
| markdown-to-xlsx | 6 | `openpyxl` (template-less render) | ✅ `ok` (produces `sample.xlsx`) |
| mermaid-renderer | 5 | npm `@mermaid-js/mermaid-cli` (`mmdc` + headless Chromium) | ✅ `ok` (renders `mermaid-1.png`) |
| file-to-markdown | — | `docling` (heavy ML: torch + models) | ⏳ see below |

`file-to-markdown` is the one skill whose deps (Docling — torch + downloaded
models) are heavy; its result is recorded once the install completes, else it
stays the lone environment-blocked skill with `docs/backlog.md` noting what it
needs. The Office skills were run **template-less** (their documented opt-out
path) so no binary template fixture is needed.

## Scope note

Full per-pack sweeps over `core` + `converters` (every covered skill ×
~18 queries × 3 runs) run report-only in `pack-evals.yml`; their first
scheduled/dispatch run produces the per-skill trigger-rate baselines. This
manual pass validates the live mechanism, not the calibration baseline (the
latter is RFC-0037 Open Q1, deferred).
