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
| file-to-markdown | 9 | `docling` + `Pillow` (heavy ML: torch + models) | ✅ `ok` (`sample.docx` → `sample.md`, 59 words) |

**All 6 covered `converters` skills are behavior-verified for real** (`msg-to-markdown`
is excluded by the converters carry-over gate). The Office skills were run
**template-less** (their documented opt-out path), so no binary template fixture
is needed; `file-to-markdown` ships a small `.docx` fixture (the only binary
fixture, since its input is a document). Each skill's deps were installed via its
own `## Prerequisites` (the repeatable contract) — none committed.

## Scope note

Full per-pack sweeps over `core` + `converters` (every covered skill ×
~18 queries × 3 runs) run report-only in `pack-evals.yml`; their first
scheduled/dispatch run produces the per-skill trigger-rate baselines. This
manual pass validates the live mechanism, not the calibration baseline (the
latter is RFC-0037 Open Q1, deferred).

## 6. LLM-judge (Phase 4, RFC-0037 § Errata E4) — live cross-model validation

Validated the quality-layer judge live with **both** backends on the **same**
artifact (a genuinely good `architect-design` design doc — idempotent webhook
delivery) graded against a rubric (`expected_output` + assertions: required
sections, dual-write designed out, ≥2 honest alternatives, risks-with-mitigations):

| judge backend | verdict |
| --- | --- |
| `claude-code` (same model) | **PASS** — "all three assertions hold … dual-write resolved via a same-transaction outbox" |
| `codex` (independent model/IDE, `-s read-only`) | **PASS** — "satisfies the required Google-style structure … alternatives and risks concise but concrete" |

Both ran through the config-driven seam (`get_judge` → `CommandJudge`), parsed a
structured JSON verdict, and **affirmed a good output** (the calibration concern —
that an LLM-judge reflexively nitpicks — did not occur). The cross-model agreement
with an *independent* judge (codex ≠ the skill's runtime) is the no-self-grade
posture E4 prefers. Judgment-only confirmed (claude no tools; codex sandboxed
read-only). Report-only — a quality signal, not a gate; a judge wobbles run-to-run
and wants periodic human calibration.

## 7. LLM-judge applied to judgment packs (architect, product-engineering) — live

The judge (E4) is the right Tier-B tool for judgment skills (no deterministic
artifact to check structurally). Authored quality rubrics (`evals/evals.json` —
`expected_output` + `assertions`) for `architect/architect-design` and
`product-engineering/frame-intent`, then ran `--mode judge` live:

| skill | artifact | verdict |
| --- | --- | --- |
| architect-design | a complete webhook-delivery design doc | **PASS** — "all six assertions pass; every section earns its place" |
| frame-intent | a proper intent (outcome + opportunity, level/scale, stops at the intent) | **PASS** — "all five hold; outcome is behavioral" |
| frame-intent | a "build a setup wizard" solution brief | **FAIL** — "a solution brief, not an intent — skips to implementation" |

The judge **discriminates quality** (affirms the good, fails the solution-brief),
proving the workflow for these packs: author a rubric → `--mode judge
--artifacts {skill: {eval_id: <artifact>}}`. Backend/model is configurable
(`--judge-adapter` / `--model`); report-only.

**Rollout to the rest of both packs (2026-06-22).** Every judgment skill in
`architect` (3) and `product-engineering` (5) now ships a rubric matched to its
own discipline:

| pack | skill | rubric grades |
| --- | --- | --- |
| architect | architect-design | Google-style design-doc quality |
| architect | architect-diagram | notation routing, structural discipline, grounded names |
| architect | architect-review | verdict form, severity-ordered actionable findings, grounded claims |
| product-engineering | frame-intent | outcome (not solution), opportunity, level/scale, stops at intent |
| product-engineering | de-risk-intent | reversibility triage, riskiest assumption, predeclared kill condition, verdict |
| product-engineering | decompose-intent | one level, shippability cut, recorded decision, Scale-correct projection |
| product-engineering | align-value-stream | federated catalog, contract home, single architecture, AND-rollup, currency |
| product-engineering | voice-and-microcopy | blame-free errors, next-action, verb+object CTAs, terminology consistency |

Two of the new rubrics were spot-checked live with good-vs-weak artifacts to
confirm they discriminate: `architect-review` (a proper severity-tagged critique
**PASS** / a "looks good, consider scalability" hand-wave **FAIL**) and
`voice-and-microcopy` (blame-free + actionable copy **PASS** / "You entered an
invalid code" / "Submit" / "Nothing here" **FAIL**). All 8 rubrics lint clean.

## 8. `design-craft` — both layers (Tier-A activation + Tier-4 judge), 2026-06-22

`design-craft`'s four skills are judgment/authoring skills (an aesthetic
direction, a token taxonomy, an IA doc, a heuristic critique — no deterministic
artifact), so **both** the layers that apply to judgment skills were added:
Tier-A activation (`evals/eval_queries.json` + a `[pack.evals]` block, all four
skills covered) **and** Tier-4 LLM-judge rubrics (`evals/evals.json` —
`expected_output` + `assertions` matched to each skill's procedure and
anti-patterns). No B-lite layer (nothing deterministic to re-derive).

| skill | rubric grades |
| --- | --- |
| aesthetic-direction | named + ranked goals, dominant-goal tiebreak, recorded arbitration, no values printed, accessibility-floor wins, stops at direction |
| design-critique | surface framed, quality-floor + heuristics, principle-mapped, 0–4 severity, worst-first headline, design-intent (not stack) recommendations |
| design-system-foundations | tokens trace to goals, semantic-role names, single ratio with symbolic steps, accessibility floor → WCAG, atomic composition + W3C Design Tokens, method-not-values |
| layout-and-information-architecture | job+audience per surface, forced primary rank, F/Z from the job, progressive disclosure + depth-vs-breadth nav, wayfinding as mental model, all states, concepts-not-code |

The `design-critique` rubric was spot-checked live (`--mode judge
--judge-adapter codex`) with good-vs-weak artifacts to confirm it discriminates:
a proper severity-tagged, principle-mapped, worst-first critique with a
quality-floor pass **PASS** / a "looks pretty good, bigger buttons, nicer blue,
more whitespace" polish note **FAIL** ("a brief polish note, not a
rubric-compliant design critique"). All 12 rubrics across the three judgment
packs lint clean; `design-craft` bumped 0.1.0 → 0.1.1 and `marketplace.json`
refreshed via `make build-self`.

## 9. `governance-extras` — both layers (Tier-A activation + Tier-4 judge), 2026-06-23

`governance-extras`'s three skills are governance authoring/judgment skills (an
ADR, an answer-first RFC, a route-through-RFC decision — no deterministic
artifact), so **both** layers that apply to judgment skills were added: Tier-A
activation (`evals/eval_queries.json` + a `[pack.evals]` block, all three skills
covered, 10 should-trigger + 10 near-miss each) **and** Tier-4 LLM-judge rubrics
(`evals/evals.json` — `expected_output` + `assertions` matched to each skill's
procedure and anti-patterns). No B-lite layer (nothing deterministic to
re-derive). Near-misses route across the three sibling governance skills
(`new-adr`↔`new-rfc`↔`update-conventions`) and out to `new-spec`/`bug-fix`/
`new-guide`/a plain PR — e.g. `update-conventions`'s negatives include the
skill's own documented exception (a typo/broken-link fix in CONVENTIONS.md is a
normal PR, not an RFC).

| skill | rubric grades |
| --- | --- |
| new-adr | decision as one declarative sentence, constraint-grounded context, honest negative consequences, alternatives with rejection reasons, decided-not-debated, frontmatter + problem/solution H1 |
| new-rfc | answer-first "The ask", MECE-with-do-nothing options grounded in prior art, recommendation-per-decision + ≤3 owned open questions, real pre-mortem, verifiable (non-fabricated) citations, no decided-default-also-open-question |
| update-conventions | pushes back on direct edits → routes through RFC, RFC scoped with the exact edited text, follow-up small PR cites the RFC footer, updates Follow-on artifacts, exempts trivial edits |

The `new-adr` rubric was spot-checked live (`--mode judge --judge-adapter codex`)
with good-vs-weak artifacts to confirm it discriminates: a template-complete ADR
(constraint-grounded context, a clear decision sentence, honest negatives, two
alternatives each rejected with a reason) **PASS** ("records a formally proposed
architecture choice rather than an open debate") / an unresolved "we're leaning
towards Postgres but haven't decided … there aren't really any downsides"
discussion note **FAIL** (all six assertions failed — "an unresolved discussion
note rather than an ADR"). The spot-check first caught two over-strict rubric
assertions and they were fixed before shipping: "Decision … at the top" (the
judge read it as document-top, but the ADR/MADR layout puts Context before the
Decision — reworded to "leading the Decision section"), and a bundled "the README
index is updated" clause (the judged artifact is a single ADR file, so a
cross-file README update can never appear in it — dropped).

The `update-conventions` rubric was also spot-checked live (`--mode judge
--judge-adapter codex`) after the adversarial-reviewer flagged the same class of
defect in it: assertion 4 said "Updates the RFC's Follow-on artifacts to point at
the merged commit" (a completed post-merge action), but the judged artifact is
the skill's **routing-decision response at request time**, where no merged commit
exists yet — reworded to "Plans to update … the eventual merged commit" so it
grades planned intent. After the fix the rubric discriminates: a proper
RFC-routing response (refuses the direct edit, scopes the RFC with a before/after
Proposal diff, plans the RFC-citing follow-up PR + Follow-on-artifacts update, and
exempts all three trivial-edit types — typos/broken-links/formatting) **PASS**
("satisfies every lifecycle requirement") / a "Sure! I've updated CONVENTIONS.md
for you … I'll just make them directly" response **FAIL** ("does the opposite of
the required routing"). Assertion 4 confirmed passable on the good artifact.

All three rubrics
lint clean; `governance-extras` bumped 0.3.0 → 0.3.1 and the self-host projection
(`.claude/skills/`, `.agents/skills/`) + `marketplace.json` refreshed via
`make build-self` (the projection drift is covered by `make build-check`, which
is green — unlike `design-craft`, `governance-extras` is self-host-projected).

## 10. `user-guide-diataxis` — both layers (Tier-A activation + Tier-4 judge), 2026-06-23

`new-guide` is a user-triggered judgment/authoring skill (it drafts Diátaxis
user-facing guides — tutorial / how-to / reference / explanation — by judgment,
no deterministic artifact), so **both** layers that apply to judgment skills
were added: Tier-A activation (`evals/eval_queries.json` + a `[pack.evals]`
block, 10 should-trigger + 10 near-miss) **and** a Tier-4 LLM-judge rubric
(`evals/evals.json` — `expected_output` + `assertions` matched to the skill's
discipline). No B-lite layer (a guide has no deterministic post-condition to
re-derive). The 10 near-misses route across the sibling authoring skills
(`new-spec` / `new-rfc` / `new-adr`), to contributor-facing architecture docs
(documentation, but not a *user* guide), to editing an existing guide (a normal
PR, not `new-guide`), to code docstrings / release notes / a blog post, and to
`voice-and-microcopy` (UI words, not documentation prose) — each shares
"write" / "document" / "guide" vocabulary but needs a different skill.

| skill | rubric grades |
| --- | --- |
| new-guide | single Diátaxis quadrant chosen by reader posture (no quadrant-mixing — adjacent material linked out), task-focused with concrete runnable/verifiable steps, prose hygiene (no reader-blaming fillers / softened imperatives / inline version-history), See-also links only to existing siblings |

The `new-guide` rubric was spot-checked live (`--mode judge --judge-adapter
claude-code`) with good-vs-weak artifacts to confirm it discriminates: a focused
how-to (one named task — rotate an expired API token — concrete steps each with
a "you should see…" checkpoint, clean prose, one defensible cross-link)
**PASS** ("a well-formed how-to guide that satisfies all rubric assertions") /
a quadrant-mixed blob (all four quadrants in one document, vague unverifiable
steps, reader-blaming fillers + inline version history, fabricated cross-links)
**FAIL** ("fails every assertion … blends all four Diátaxis quadrants in one
document"). This same `--mode judge` run **is** the Tier-B light-mode harness
smoke-check the standing `AGENTS.local.md` eval-coverage policy requires —
report-only, confirming the rubric loads and discriminates, not a calibration
gate.

The rubric lints clean; `user-guide-diataxis` bumped 0.1.4 → 0.1.5 and the
self-host projection (`.claude/skills/new-guide/evals/`,
`.agents/skills/new-guide/evals/`) + `marketplace.json` refreshed via
`make build-self` (the projection drift is covered by `make build-check`, which
is green). **Note:** `user-guide-diataxis` is `default-scope = "repo"` and is
self-host-projected — like `core` / `governance-extras`, not like the
user-scope `design-craft` — so the added eval files **do** project into
`.claude/` and `.agents/`, and `make build-check` is the gate that covers them.
