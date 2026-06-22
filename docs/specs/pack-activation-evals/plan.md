# Plan: pack-activation-evals

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This spec/plan + ADR-0028 land in **one PR**; the implementation lands in a
**separate implementing PR** (RFC-0037 § Follow-on artifacts). The tasks below
are that implementing PR's work-breakdown.

The shape of the change is: two **lint preconditions** first (they must accept
the new files before the files can land), then the **runner**, then the per-pack
**eval authoring** (converters before core — converters is user-scope and
lighter; core is self-host-projected and needs `make build-self`), then the
**scheduled CI workflow** last (it runs the runner over the now-covered packs).

The deterministic core of the runner — parsing a `claude -p` JSON payload for a
`Skill` `tool_use` event, computing `trigger_rate`, grading against 0.5 — is
unit-tested against captured JSON fixtures, **not** live calls, so CI stays
deterministic. The single live-model surface (the actual `claude -p`
invocations) lives only in the report-only scheduled workflow and in a recorded
manual run; it is the riskiest part and is de-risked by the report-only posture,
the `trigger_rate`-over-3 averaging, and the spike that already confirmed the
flags.

## Constraints

- **RFC-0037** (Accepted) — the three decisions, the file/section/runner shapes,
  the report-only posture, Tier-A scope, and both resolved open questions.
- **ADR-0028** — the durable record of those decisions; the plan must not
  contradict it.
- **RFC-0031 / ADR-0021** — `pack.toml` is the rich source of truth;
  `[pack.evals]` extends it.
- **Charter Principle 3** — the runner is catalogue-internal tooling, never a
  shipped pack primitive; it stays in `tools/` and is never projected.

## Construction tests

Most tests live per-task below. Cross-cutting:

**Integration tests:** a recorded **manual** end-to-end run of
`tools/run-pack-evals.py --pack converters` and `--pack core` after T4/T5,
observing the JSON summary (live-model; not CI-gated).
**Manual verification:** a `workflow_dispatch` of `pack-evals.yml` produces
artifact summaries without failing the build.

## Design (LLD)

Shape = `service`. Stack: Python ≥3.11 (stdlib + `tomllib`), the existing
`agentbundle` projection path, and the `claude` CLI (2.1.185 on this machine;
RFC-0037 spike was 2.1.181). No new
third-party dependency.

### Design decisions

- **Detector = the convention's own `claude -p` form**, not the Anthropic SDK
  (wrong layer — won't load skills) and not a remote sandbox (heavier infra,
  Principle-3 tension). Traces to: AC1 · runner CLI.
- **Per-run bound is a wall-clock timeout**, because `--max-turns` is an SDK
  option absent from the `claude` CLI (0 hits in `claude --help`). Traces to: AC5.
- **Coverage is an explicit `[pack.evals].skills` allowlist**, not auto-discovery
  — some skills ship no trigger evals and the list is a deliberate contract.
  Traces to: AC7.
- **Deterministic logic and the live call are separated** so the parse/grade core
  is unit-testable without a model and CI stays green. Traces to: AC1, AC2.
- **`eval_queries.json` is a separate file** from `evals/evals.json` (no schema
  fork). Traces to: AC6 · spec § Never do.
- **Reference-harness proxy, headless-only, detector seam.** Activation is
  measured on **claude-code as the reference harness** — a proxy for the
  byte-identical `description:` projected to every adapter — and **only**
  headlessly. GUI-only IDEs (Kiro IDE, Cursor IDE) expose no headless surface and
  are out of scope (an in-editor `userTriggered` `.kiro.hook` driver was
  considered and rejected: runtime infra, not catalogue dev tooling — Principle
  3). The other headless CLIs (codex `codex exec --json`, copilot `copilot -p
  --output-format json`, cursor-agent, gemini) become additive detectors later
  behind a small `Detector` seam (`project-for-adapter → run-headless →
  parse-activation`); the first cut ships the `claude-code` detector only.
  Traces to: AC1, AC18.

### Interfaces & contracts

- **Runner CLI:** `run-pack-evals.py --pack <name> [--runs N]` → writes an
  `iteration-<N>/` under the gitignored eval-workspace; exit 0 on completion
  (report-only; an eval miss is not a non-zero exit in the first cut). Traces to:
  AC1, AC4.
- **Eval-workspace layout (forward-compatible convention; agentskills.io
  evaluating-skills):** Traces to: AC4, AC10, AC21.

  ```
  .eval-workspace/<pack>/                    # repo-relative, gitignored (NOT the temp projection dir)
  └── iteration-<N>/                        # one per full eval-loop pass
      ├── <skill>/<query-id>/
      │   └── with_skill/
      │       └── run-<r>/outputs/          # Tier A: parsed .result of the claude -p JSON envelope
      │       # reserved (future grading RFC): run-<r>/{timing.json,grading.json}
      │   # reserved (Tier-B baseline): <query-id>/without_skill/...
      └── summary.json                      # Tier-A activation summary (trigger_rate, pass counts)
      # reserved (Tier-B): iteration-<N>/benchmark.json (pass_rate/delta)
  ```

  The eval-workspace (`.eval-workspace/`, gitignored) is **distinct from the temp
  dir the pack is projected into** for discovery (ephemeral). Tier A produces only
  `with_skill/.../outputs/` + `summary.json`; the `without_skill/`, `timing.json`,
  `grading.json`, `benchmark.json` slots are named-but-unused so a grading RFC
  fills them without restructuring. `outputs/` stores the **parsed `.result`
  field** of the `claude -p --output-format stream-json --verbose` stream (the
  terminal `result` event) — never the raw stdout stream, stderr, env, or key;
  `summary.json` is the bounded aggregation (AC10). (Detector format: RFC-0037
  § Errata E1 — `--output-format json` carries no `tool_use` events.)
- **`evals/eval_queries.json` schema:** a JSON array; each element
  `{ "query": <non-empty str>, "should_trigger": <bool> }`. Validated by
  `lint-skill-spec.py`. Traces to: AC6, AC14.
- **`[pack.evals]` block:** `[pack.evals]\nskills = [<str>, ...]`; each names a
  skill dir shipping `eval_queries.json`. Traces to: AC7, AC12, AC13, AC17.

### Failure, edge cases & resilience

- `claude` missing from PATH → the runner fails fast with a clear message (it is
  a hard prerequisite of the eval run, not a per-query miss).
- A `claude -p` run that **times out** or returns unparseable JSON → recorded as
  **not fired** for that run (so it counts against a positive query's
  `trigger_rate`), distinct from a runner-level crash.
- A `[pack.evals].skills` entry whose `eval_queries.json` is absent → the
  coverage lint (T2) fails **before** the runner ever runs. Traces to: AC7.
- Empty `eval_queries.json` array → the skill contributes no queries (a no-op,
  not an error); flagged in the summary. Traces to: AC4.

### Dependencies & integration

- **`claude` CLI** (activation detector) and **`ANTHROPIC_API_KEY`** (a new repo
  secret that must be provisioned before `pack-evals.yml` can run — see Rollout).
- **`agentbundle`** projection (to isolate a pack into a temp dir). Traces to:
  AC1.

### Quality attributes (NFRs)

- **Cost bound:** `~20 queries × 3 runs × N skills`, bounded by the per-run
  timeout + the `[pack.evals]` allowlist + schedule-not-push cadence. Traces to:
  AC5, AC7, spec § Ask first (report-only → gate).

## Tasks

### T1: `lint-skill-spec.py` accepts an `eval_queries.json`-only skill and validates it

**Depends on:** none

**Tests:**
- A skill dir with only `evals/eval_queries.json` (a valid array of
  `{query, should_trigger}`) **passes** (AC6).
- An `evals/` dir with neither `evals.json` nor `eval_queries.json` still
  **errors** (AC6).
- `eval_queries.json` that is not a JSON array → error; an element missing
  `query`, with an empty-string `query`, or with a non-bool `should_trigger` →
  error (AC6).
- A skill shipping **both** `evals.json` and `eval_queries.json` → passes.

**Approach:**
- In `check_evals` (`tools/lint-skill-spec.py:534`), branch: if `evals.json`
  exists, validate it via the existing path; else if `eval_queries.json` exists,
  validate the trigger schema (new `validate_eval_queries` helper); else error
  naming **both** acceptable files.
- Update the module's self-tests; keep the error wording adopter-clean (no
  catalogue-internal references).

**Done when:** new + existing `lint-skill-spec` self-tests green; `lint-packs`
green on the current tree (no skill ships `eval_queries.json` yet).

### T2: `[pack.evals].skills` coverage check

**Depends on:** none

**Tests:**
- `[pack.evals].skills` naming a real skill dir that ships `eval_queries.json` →
  passes (AC7).
- Naming a missing skill dir → error; naming a skill dir without
  `eval_queries.json` → error (AC7).
- A pack with no `[pack.evals]` block → no-op (AC7).

**Approach:**
- Add a pack-level pass (in `lint-skill-spec.py` or `lint-packs`) reading
  `[pack.evals].skills` via `tomllib`; assert each entry resolves to a skill dir
  shipping `eval_queries.json`.
- Wire into the local pack-lint gate **and** both CI lint surfaces (source
  `lint-packs` + projection `lint-agent-artifacts`) — the two-lint-surface
  convention.

**Done when:** self-test green; `lint-packs` green on existing packs (all no-op).

### T3: `tools/run-pack-evals.py`

**Depends on:** none <!-- consumes T4/T5's files at *runtime* but does not import them; built against fixtures -->

**Tests:**
- **Parse:** a captured `claude -p --output-format stream-json --verbose` payload containing a
  `Skill` `tool_use` with `.input.skill == X` → `(fired=True, skill=X)`; a
  payload with no `Skill` event → `(fired=False, skill=None)` (AC1).
- **`trigger_rate`:** firing fraction over a list of run-results (AC2).
- **Grading:** `0.67`+`should_trigger:true` → pass; `0.33`+true → fail;
  `0.33`+false → pass; `0.67`+false → fail (AC2).
- **Exclusivity:** flag set when a different in-pack skill fired (AC3).
- **Detector seam:** the `claude-code` detector is reached through a thin
  adapter-`Detector` interface (`project-for-adapter → run-headless →
  parse-activation`); a fixture test confirms the seam dispatches to the
  registered detector and that an unknown/non-headless adapter is rejected, not
  silently run (AC18).
- **Workspace layout:** a test asserts a run writes `.eval-workspace/<pack>/iteration-<N>/`
  with per-eval `with_skill/.../outputs/` capturing the parsed `.result` and a pass
  `summary.json`, and that the reserved grading slots (`without_skill/`,
  `timing.json`, `grading.json`, `benchmark.json`) are **not** produced by Tier A
  (AC4, AC21).
- **Gitignored control:** `git check-ignore` on a representative
  `.eval-workspace/<pack>/iteration-1/.../outputs/<file>` path exits 0 (the
  `.gitignore` entry exists); a captured `outputs/` artifact contains the parsed
  result only — no env var, no `ANTHROPIC_API_KEY`, no stderr (AC4, AC10).

**Approach:**
- stdlib + `tomllib`. The `claude-code` detector runs
  `subprocess.run([claude, "-p", query, "--output-format", "stream-json",
  "--verbose", "--allowed-tools", "Skill"], timeout=…)` — argv list, no `shell`
  (detector format: RFC-0037 § Errata E1);
  `--allowed-tools` stays **`Skill` only** (the observe-don't-execute trust
  boundary, spec § Never do). Parse the JSON envelope; capture its **`.result`
  field** (not the raw stdout stream) to
  `.eval-workspace/<pack>/iteration-<N>/<skill>/<query-id>/with_skill/run-<r>/outputs/`
  and write the pass's `summary.json` to `iteration-<N>/` (the forward-compatible
  layout above; reserve the grading slots, don't produce them). Add the
  `.eval-workspace/` entry to the repo `.gitignore` and verify with `git check-ignore`.
- Keep detection behind a small `Detector` seam so codex/copilot/cursor-agent/
  gemini headless detectors are additive later; ship only `claude-code` now.
  GUI-only IDEs are rejected by the seam (no headless surface). Traces to: AC18.
- **Summary serialization is an allowlist** — only `{skill, query, trigger_rate,
  pass-counts}` (spec AC). Never serialize raw subprocess `stderr`, the process
  environment, or any secret; never echo `ANTHROPIC_API_KEY`. The timeout /
  unparseable-JSON path records a bare `not-fired` flag, not the raw payload.
- Project the pack into a temp dir via the existing `agentbundle` path
  (claude-code adapter, minimal `.claude/settings.json`).
- Keep parse / `trigger_rate` / grade as **pure functions** for the fixture
  tests; the live call is the only impure seam.

**Done when:** unit tests green; `python tools/run-pack-evals.py --help` works;
a manual run against `converters` (after T4) writes a summary (recorded; not
CI-gated). Wire the new test path into CI (explicit per-path line — the
package-tests-need-explicit-wiring convention).

### T4: `converters` eval_queries.json + `[pack.evals]`; bump + build

**Depends on:** T1, T2

**Tests:**
- `lint-skill-spec` + the coverage check green on `converters` (AC7, AC13).
- Each covered skill's `eval_queries.json` has ~8–10 each-way near-miss cases
  (AC14).
- `make build` refreshes `marketplace.json` to the bumped version (AC15).
- `agentbundle validate` passes with the `[pack.evals]` block present, and
  `git diff` on `marketplace.json` shows no `evals` key — the section is not
  projected (AC17).
- **Manual:** `run-pack-evals.py --pack converters`, trigger rates recorded.

**Approach:**
- Author `eval_queries.json` for the covered converters skills
  (`markdown-to-docx`, `markdown-to-pptx`, `markdown-to-xlsx`, `markdown-to-html`,
  `file-to-markdown`, `mermaid-renderer`) — the three Office skills' near-misses
  deliberately disambiguate docx/pptx/xlsx (the RFC-0036 activation risk).
- **Exclude `msg-to-markdown`** from the covered set: the existing carry-over
  gate (`build-check.yml`) **hard-errors if `msg-to-markdown/evals` exists at
  all**, so authoring `evals/eval_queries.json` there would create the `evals/`
  dir and trip the gate. It ships no `eval_queries.json` and is not in
  `[pack.evals].skills` (the converters parallel to `core`'s
  `security-checklists` exclusion).
- Add `[pack.evals].skills`; bump the pack version; **leave** the existing
  `evals/evals.json` carry-over gate untouched (AC13); `make build`.

**Done when:** lints + build green; `marketplace.json` reflects the bump; manual
run recorded.

### T5: `core` eval_queries.json + `[pack.evals]`; bump + build-self

**Depends on:** T1, T2

**Tests:**
- `lint-skill-spec` + coverage check green on `core` (AC7, AC12).
- `security-checklists` and `work-loop` are **not** in `[pack.evals].skills` (AC12, spec § Never do).
- `make build-self` projects the new `evals/` files into `.claude/skills/<skill>/evals/`;
  `git status` clean afterwards (AC16).
- **Manual:** `run-pack-evals.py --pack core`, trigger rates recorded.

**Approach:**
- Author `eval_queries.json` for `core`'s sharp-boundaried user-triggered skills:
  `new-spec`, `bug-fix`, `receive-brief`, `init-project`, `adapt-to-project`.
  Near-misses cross these boundaries (e.g. "record this decision" is a near-miss
  for `new-spec`).
- Explicitly **exclude** both `security-checklists` (reviewer-internal, never
  self-discovered) **and** `work-loop` (loaded broadly by the plan→execute→review
  discipline, not by a narrow user-prompt surface — a clean negative set isn't
  writable for it in the first cut); document both exclusions in the
  `[pack.evals]` comment.
- Bump `core`; `make build-self` (projected pack).

**Done when:** lints + build-self green; clean `git status` (no projection
drift); manual run recorded.

### T6: `.github/workflows/pack-evals.yml`

**Depends on:** T3, T4, T5

**Tests:**
- Goal-based: the YAML has `schedule:` + `workflow_dispatch:` and **no**
  `push`/`pull_request` trigger; declares `permissions: contents: read`;
  references `secrets.ANTHROPIC_API_KEY`; the eval step does not fail the job on a
  miss; the YAML parses (AC8, AC9-permissions, AC10-summary).
- `make build-check` unchanged — no live-model step (AC11).

**Approach:**
- A `schedule` (cron) + `workflow_dispatch` workflow with a least-privilege
  top-level `permissions: contents: read` (the repo's secret-consuming-workflow
  precedent): set up Python + the `claude` CLI, run `run-pack-evals.py` for
  `core` and `converters`, upload the JSON summaries as artifacts, **never** fail
  the build (report-only).
- A changelog `[Unreleased]` entry for the new eval capability lands in this
  implementing PR.

**Done when:** the workflow parses; a manual dispatch produces artifact
summaries; `make build-check` is untouched.

### T7: Update authoring + architecture docs for writing, running, and the outputs of activation evals

**Depends on:** T1 (the convention/lint must exist before the docs describe it)

**Tests:**
- Goal-based: `docs/guides/_shared/how-to/author-a-skill.md` gains a section
  covering (a) writing `evals/eval_queries.json` — the trigger-eval convention
  (flat `[{query, should_trigger}]`, ~8–10 each way, near-miss negatives),
  **distinct** from the output-quality `evals/evals.json`; (b) declaring
  `[pack.evals].skills` in `pack.toml`; (c) running
  `python tools/run-pack-evals.py --pack <name>` locally; and its existing
  `evals/` description no longer implies `evals.json` is the only accepted layout
  (AC19).
- Goal-based: the guide disambiguates the **two** eval files and documents the
  **human-authored portions** of the output-quality convention — `evals/evals.json`
  `expected_output` + `assertions` craft (good-vs-weak) + the human-review
  discipline — each marked **"author now; automated running/grading deferred
  (Tier B, future RFC)"**, and states which file serves which tier (AC20).
- Goal-based: `docs/architecture/pack-layout.md` names both eval source files
  (`eval_queries.json` + `evals/evals.json`) and documents the generated
  `.eval-workspace/<pack>/iteration-<N>/…/outputs/` as a gitignored run-artifact
  emitted by the runner, distinct from pack source (AC22).

**Approach:**
- Extend `author-a-skill.md` (the canonical skill-authoring how-to): add the
  trigger-eval subsection under the existing `evals/` material, contrast it with
  output-quality evals, and document the local run command + the `[pack.evals]`
  coverage declaration. Cross-link the spec, don't restate the runner internals.
- Add a short **two-files** subsection: `eval_queries.json` (Tier A — triggering,
  run by the runner) vs `evals/evals.json` (Tier B — output quality, **authored
  by hand now**, running/grading deferred). Capture the human craft for Tier B
  from agentskills.io's [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
  — `expected_output`, good-vs-weak `assertions`, the human-review pass — so the
  ~4 packs already shipping `evals.json` (and future authors) have guidance, while
  being explicit that **this RFC does not execute them**.
- Document the **eval-workspace convention** (the forward-compatible
  `iteration-<N>/` + `outputs/` layout, with the reserved grading slots) so both
  the Tier-A runner output and any hand-run Tier-B output land in the same place a
  future grading RFC will read (AC21).
- Update **`docs/architecture/pack-layout.md`**: name both authored eval source
  files in a skill's `evals/` (`eval_queries.json` + `evals/evals.json`; the
  line-116 entry today says only `evals/`), and add the **generated**
  eval-output workspace `.eval-workspace/<pack>/iteration-<N>/…/outputs/` as a
  gitignored run-artifact (not pack source) emitted by `run-pack-evals.py` (AC22).
- Sweep the per-pack reference guides touched by the first cut
  (`docs/guides/core/`, `docs/guides/converters/`) for any `evals/`-layout claim
  that the relaxed lint makes stale; fix in place.

**Done when:** the guide documents writing + running the Tier-A evals **and** the
human-authoring craft for the Tier-B output-quality evals (with the deferred-
running boundary stated); a reader could author both an `eval_queries.json` and an
`evals.json` and run the Tier-A eval from the guide alone; `pack-layout.md`
documents both eval source files and the generated `.eval-workspace/` outputs; no
stale `evals.json`-only layout claim remains in the touched docs.

### T8 (follow-on, non-blocking): migrate the `converters` carry-over gate to read `[pack.evals].skills`

**Depends on:** T2, T4 — (deferred: pack-evals-converters-gate-consolidation)

The RFC names this as an optional consolidation that "may land as a follow-on PR
rather than blocking the harness". Recorded in `docs/backlog.md`.

## Phase 2 — in-harness / agent-dispatch detector (RFC-0037 § Errata E2)

### Design (LLD addendum)

Phase 1 (headless) measures activation via `claude -p` and its real `Skill`
`tool_use` event. Phase 2 adds reach to harnesses with **no** `claude -p` CLI
(**Kiro IDE**) and to interactive Claude Code, via a second detector behind the
seam — **lower fidelity**, never replacing the headless reference.

**The isolation finding (load-bearing).** A dispatched sub-context (Claude
Code's `Agent` tool, Kiro's spawn) **cannot be scoped to only the pack's
skills** — skill discovery is rooted at the session, not the sub-context's cwd,
so projecting the pack into a temp dir (the headless trick) does **not** isolate
a subagent. Consequence: the in-harness mode supplies the candidate skills'
names + `description:` **in the dispatch prompt** and asks the sub-context which
it would activate. That is a **description-match judgement (reported)**, not the
real router event (observed) — a materially different, lower-fidelity signal.
This is why E2's signal decision is "reported", and why the summary labels
`fidelity`.

**Architecture (reuse, don't fork).** The driver does the agent dispatch; the
runner keeps the model-free logic:

- `run-pack-evals.py` factors out reusable helpers (project, `trigger_rate`,
  `grade`, workspace-write) and gains `grade_reports(pack, reports, mode=…)`
  that turns collected `{skill: {query_id: [reported_skill_per_run]}}` into the
  same `summary.json` (with `mode`/`fidelity` fields). No `claude` call.
- A **catalogue-internal driver** (a repo-owned `.claude/` command for Claude
  Code; a `.kiro/` equivalent for Kiro — **not** a projected pack primitive, so
  Principle 3 holds) reads a pack's `eval_queries.json` + covered descriptions,
  dispatches a **read-only, no-tool-execution** sub-context per query, collects
  the reported skill, and calls `grade_reports`.

**Containment (new trust boundary).** The dispatched sub-context holds the
host's full tool surface; the `--allowed-tools Skill` headless sandbox does not
transfer. The driver must dispatch a sub-context that **elicits the activation
judgement only** — it must not run a skill body or any project tool against the
author-influenced query string. Verified by construction (the dispatch prompt
grants no execution + the sub-context is read-only) and by inspecting that a
dispatched run touched no files / ran no tools.

### T9: runner `grade_reports` + `--mode` plumbing (model-free)

**Depends on:** none — **TDD.** Tests: `grade_reports` over synthetic collected
reports produces a `mode: in-harness`, `fidelity: reported` summary with correct
`trigger_rate`/grading and the same workspace layout; `--mode headless` stays
the default and unchanged. Done when: unit tests green; headless path untouched.

### T10: catalogue-internal in-harness driver (Claude Code) + live validation

**Depends on:** T9 — **manual QA.** A repo-owned `.claude/` command drives the
dispatch loop (read-only sub-contexts, candidate descriptions in the prompt,
collect reported activation, call `grade_reports`). Validate **live** by
dispatching real sub-contexts for a covered skill's queries and recording the
observed reports + that no tool executed against the query (containment). Done
when: a recorded in-harness run over a `core` skill produces a labelled summary;
containment confirmed.

### T11: Kiro IDE driver

**Depends on:** T9 — **goal-based.** The Kiro-native driver (`.kiro/` hook or
command) invoking the same `grade_reports` contract. Sequenced after T10 proves
the model in Claude Code; may land as its own follow-on.

### T12: docs + ADR note

**Depends on:** T9, T10 — **goal-based.** `author-a-skill.md` gains the
in-harness run path + the fidelity caveat; ADR-0028 carries the E2 companion
note; the in-harness mode + `mode`/`fidelity` labelling documented.

## Rollout

- **Delivery:** report-only, no flag. Fully reversible — delete the workflow +
  the `eval_queries.json` files + the `[pack.evals]` blocks. Nothing
  irreversible ships (no data migration, no published event).
- **Infrastructure:** a new **`ANTHROPIC_API_KEY` repo secret** must be
  provisioned before `pack-evals.yml` can run — the one external precondition.
- **External-system integration:** the scheduled workflow consumes the Anthropic
  API via `claude -p`; cost is bounded by the allowlist + per-run timeout +
  schedule cadence.
- **Deployment sequencing:** lint preconditions (T1, T2) **before** the eval
  files (T4, T5) — otherwise the new files fail the unchanged lint; the workflow
  (T6) **last** (it runs the runner over the covered packs).

## Risks

- **Live-model variance** erodes trust if the workflow ever hard-failed on noise
  — mitigated by report-only first + `trigger_rate` over 3 runs.
- **Cost creep** — mitigated by the per-run timeout, the `[pack.evals]`
  allowlist, and schedule-not-push.
- **A new repo secret** to manage (`ANTHROPIC_API_KEY`) — operational, named in
  Rollout.
- **Convention drift** if agentskills.io relocates the trigger file — mitigated
  by reading the path from one pinned place.
- **First long-lived API-key secret in CI.** This PR introduces the repo's first
  `ANTHROPIC_API_KEY` workflow secret, and the repo wires no secret scanner today
  (only CodeQL + Bandit/Semgrep). A committed-key regression in a future eval
  file or workflow edit would not be caught in CI — recorded as a follow-up
  (`docs/backlog.md` → `secret-scanner-for-api-key-workflows`), out of scope for
  this spec.

## Changelog

- 2026-06-21: initial plan (authored alongside the spec + ADR-0028; implementation deferred to a separate PR per RFC-0037 § Follow-on artifacts).
- 2026-06-21: implementing PR — T1–T7 landed; Status → Done. Detector corrected to `--output-format stream-json --verbose` (RFC-0037 § Errata E1 — the `json` envelope carries no `tool_use` events on claude 2.1.185); the T2 coverage check is hosted in `lint-skill-spec.py` (a source-surface lint run locally + in CI), since `pack.toml` is never projected and `lint-agent-artifacts` reads only `.claude/`. T8 deferred to `docs/backlog.md`.
