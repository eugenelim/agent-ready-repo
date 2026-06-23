# Spec: pack-activation-evals

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived --> <!-- Phase 1 (headless) + Phase 2 (in-harness activation) + Phase 3 (lightweight B-lite behavior/output check, RFC-0037 § Errata E3) shipped -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0037, ADR-0028
- **Brief:** none
- **Contract:** none <!-- the runner exposes a script CLI (argv + a JSON summary file) documented in the plan's LLD; it is not one of the formal openapi/asyncapi/proto/graphql/jsonschema contract surfaces. The eval_queries.json file schema and the [pack.evals] block are pinned in Acceptance Criteria instead. -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A catalogue maintainer can measure — repeatably and empirically — whether each
covered skill **activates** on the prompts it should and stays quiet on the
near-misses it shouldn't, producing a number comparable across model versions and
`description:` edits. `tools/run-pack-evals.py --pack <name>` reads the pack's
`[pack.evals].skills` allowlist, projects the pack into an isolated temp
directory so only that pack's skills are discoverable, runs each covered skill's
`evals/eval_queries.json` through the headless detector `claude -p "<query>"
--output-format stream-json --verbose --allowed-tools Skill` (RFC-0037 § Errata
E1), computes a `trigger_rate` over N
runs, grades each query against the 0.5 threshold, and writes each pass's runs +
activation summary into a gitignored, **iteration-numbered eval-workspace** — the
agentskills.io evaluating-skills layout (`iteration-<N>/` per pass, per-eval
`outputs/` capturing the actual run output), **established here as a
forward-compatible convention** with reserved slots so a future grading RFC adds
output-quality grading without restructuring. It runs in a scheduled / dispatch,
**report-only** `pack-evals.yml` workflow — never on the PR critical path — and
`make build-check` stays structural and fast. The first cut covers `core` and
`converters`. The **first cut's** scope is **Tier A (activation/selection)** via
the headless detector; two errata extend it (see § Errata-driven phases at the
end of this Objective). Scope is **Tier A** — the
agentskills.io [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
*methodology* (the `evals/eval_queries.json` **path is the catalogue's
instantiation**, not agentskills.io's — it illustrates a bare `eval_queries.json`
and never mandates the `evals/` subdir). The entire
[Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
page (Tier B — with/without-skill runs, LLM-judge grading, `benchmark.json`
pass-rate deltas, the human `feedback.json` review, the SKILL.md improvement
loop) plus the triggering page's train/validation split and
description-*optimization* loop are **out of scope** for the **full** grading — a
separate future RFC (full exclusion list in ADR-0028 § Consequences). *(A
**lightweight** slice — running `evals/evals.json` and checking deterministic
post-conditions + attested assertions — is admitted by RFC-0037 § Errata E3;
see § Errata-driven phases.)*

The **first cut's** detector is **headless-only** and measures **claude-code as
the reference harness** — a deliberate proxy for activation quality across every
adapter. Every adapter projects skills as native `direct-directory` primitives to
`<tool>/skills/<name>/` with the load-bearing `description:` projected
**byte-identical**, so the variable a trigger-eval tests is constant across
adapters; only claude-code exposes a headless prompt mode with a parseable
skill-activation event to measure it automatically. The other headless CLIs
(codex, copilot, cursor-agent, gemini) expose JSON-stream output and become
**additive headless detectors later**, behind a detector seam; the first cut
ships the `claude-code` detector only.

### Errata-driven phases

Headless (above) is **Phase 1** and stays the high-fidelity reference. Two signed
errata extend the scope, each behind the same detector seam (full ACs in their
Phase sections under Acceptance Criteria):

- **Phase 2 — in-harness activation (RFC-0037 § Errata E2).** A second detector
  where the **host harness's own agent** (Claude Code subagent / **Kiro IDE**
  agent-spawn) reports activation — bringing Kiro IDE and interactive Claude Code
  *into* scope (they are no longer out of scope). Lower fidelity: a *reported*
  description-match judgement, not the observed router event.
- **Phase 3 — lightweight behavior/output check (RFC-0037 § Errata E3).** A
  bounded slice of Tier B: run the skill and validate its outputs against
  deterministic post-conditions (`tier: B-lite`). The **full** Tier-B grading
  (LLM-judge, `benchmark.json` deltas, with/without-skill, train/val) remains the
  separate future RFC.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Store trigger evals as per-skill `evals/eval_queries.json` under the blessed
  `evals/` subdir — a flat JSON array of `{query, should_trigger}`, with
  near-miss negatives (prompts that share keywords/concepts with the skill but
  need a different one), not trivially-irrelevant prompts.
- Read coverage **only** from `pack.toml`'s `[pack.evals].skills` (an explicit
  allowlist, never auto-discovery).
- Detect activation via a parseable `Skill` `tool_use` event from `claude -p
  "<query>" --output-format stream-json --verbose --allowed-tools Skill`
  (RFC-0037 § Errata E1 — the `json` envelope carries no `tool_use` events),
  recording both *whether*
  it fired and *which* skill (`.input.skill`), bounded by a per-run wall-clock
  timeout (`--max-turns` is not a CLI flag on the `claude` CLI).
- Use only Python stdlib + `tomllib` + the `claude` CLI already on PATH.
- Grade per the convention: a `should_trigger:true` query passes iff
  `trigger_rate > 0.5`; a `should_trigger:false` query passes iff
  `trigger_rate < 0.5`.
- Pass model-influenced query strings to the subprocess as an **argv list**
  (never `shell=True`, never an interpolated command string); write summaries
  only under a gitignored workspace dir.

### Ask first

- Promoting the workflow from report-only to a hard-fail gate — only after a
  calibration baseline exists, and gating on regression-from-baseline, not an
  absolute threshold (RFC-0037 Open Q1).
- Adding a train/validation split to the eval sets (RFC-0037 Open Q2; serves
  description optimization, not regression measurement).
- Building Tier B output-quality grading (separate future RFC).
- Consolidating the existing `converters` `evals/evals.json` carry-over gate onto
  `[pack.evals].skills` (may land as a follow-on PR; not blocking this cut).

### Never do

- **No new top-level directory and no new dependency** — the runner is one file
  under existing `tools/`; the workflow under existing `.github/workflows/`.
- **No `should_trigger` field added to `evals/evals.json`** — that forks the
  published output-quality schema.
- **No pack-level shared negative-set file** outside any skill — ownership stays
  with the skill's `description:`.
- **No live model on the PR critical path / `make build-check`** — the eval
  workflow is `schedule` + `workflow_dispatch` only.
- **Never list a non-self-discovered skill in `[pack.evals].skills`** (e.g.
  `security-checklists`, which is reviewer-internal and has no user-prompt
  activation surface).
- **Never widen `--allowed-tools` beyond `Skill`** in the runner's `claude -p`
  invocation. Restricting it to `Skill` is a **trust boundary**, not just a
  Tier-A scope choice: it ensures the run *observes* the activation event but
  never *executes* a skill **body** (whose tools could run shell/file/network
  actions) against author-influenced query strings. Widening it "for fidelity"
  silently converts an observe-only harness into one that runs arbitrary skill
  bodies.
- **Headless is the reference mode; the in-harness mode never executes skill
  bodies or project tools.** *(Amended — RFC-0037 § Errata E2.)* The original
  boundary made the eval headless-only and put GUI-only IDEs out of scope; E2
  narrows that — a second **in-harness / agent-dispatch** detector is admitted
  behind the seam (the host harness's agent runs each query in a fresh
  sub-context, supplied the candidate descriptions, and **reports** which skill
  it would activate — a description-match judgement, not a pack-isolated router
  observation; see AC24), bringing **Kiro IDE**
  and interactive Claude Code into scope. What stays forbidden: the in-harness
  mode must **not** let the dispatched sub-context execute skill bodies or
  project tools against author-influenced query strings (the headless
  `--allowed-tools Skill` sandbox does not transfer — the dispatched context
  holds the host's full tool surface, so containment is a distinct control, AC25
  below). The driver stays **catalogue-internal** (repo-owned `.claude/` /
  `.kiro/`, not a projected pack primitive) so Charter Principle 3 holds.
  Headless `claude -p` remains the **high-fidelity reference**; the in-harness
  signal is **reported, lower-fidelity** and every result is labelled by mode.

## Testing Strategy

- **`lint-skill-spec.py` accepts an `eval_queries.json`-only skill + validates
  its schema** (array of `{query: non-empty str, should_trigger: bool}`): **TDD**
  — a pure validator over fixture skill dirs, compressible pass/fail set.
- **`[pack.evals].skills` coverage check** (each entry names a real skill dir
  that ships `eval_queries.json`; absent block is a no-op): **TDD** — pure read
  over fixture pack dirs.
- **Runner detector parse** (a `claude -p --output-format stream-json --verbose` payload → fired?
  + which skill): **TDD** — over a captured/representative JSON fixture, not a
  live call.
- **Adapter-`Detector` seam** (AC18 — dispatches to the registered `claude-code`
  detector; rejects an unknown / non-headless adapter rather than running it):
  **TDD** — fixture dispatch test, no live call.
- **Runner `trigger_rate` + 0.5 grading**: **TDD** — pure functions over
  synthetic run-results.
- **In-pack-exclusivity detection** (AC3 — a *different* in-pack skill fired on a
  query): **TDD** — its own unit test over synthetic multi-skill run-results, so
  the negative-coverage code path is exercised deterministically and not only
  live.
- **Runner end-to-end** (projects a pack, runs queries, writes a summary):
  **manual QA** — exercised by hand against `core` and `converters`, the observed
  summary recorded. Live-model, **not** a CI gate; this satisfies the work-loop
  "exercise the real built artifact" rule.
- **`pack-evals.yml` posture** (schedule + dispatch only; report-only): **goal-based
  check** — assert the workflow has `schedule:`/`workflow_dispatch:` and no
  `push`/`pull_request` trigger, references the `ANTHROPIC_API_KEY` secret, and
  has no step that fails the build on an eval miss; the YAML parses.
- **First-cut pack wiring** (`core` + `converters` ship `eval_queries.json` for
  covered skills + a `[pack.evals]` block; lints/build green): **goal-based check**.
- **Pack-authoring guide update** (`author-a-skill.md` documents writing
  `eval_queries.json`, declaring `[pack.evals].skills`, and running the eval; no
  stale `evals.json`-only layout claim in the touched guides; **plus** the
  two-file disambiguation and the human-authored Tier-B output-quality craft with
  its deferred-running boundary; **and** `docs/architecture/pack-layout.md` names
  both eval source files and the generated `.eval-workspace/` run-outputs):
  **goal-based check**.

## Acceptance Criteria

- [x] `tools/run-pack-evals.py --pack <name> [--runs 3]` reads `packs/<pack>/pack.toml` `[pack.evals].skills`, projects the pack in isolation (claude-code adapter, only that pack's skills discoverable), and for each query in each covered skill's `evals/eval_queries.json` runs `claude -p "<query>" --output-format stream-json --verbose --allowed-tools Skill`, parsing the event stream for an `assistant` event whose `message.content[]` holds a `Skill` `tool_use` block (`.input.skill`) — recording whether it fired and which skill. **(Amended — RFC-0037 § Errata E1 / ADR-0028 correction: `--output-format json` returns a result-only envelope with no `tool_use` events on claude 2.1.185, so `stream-json --verbose` is required to observe activation; signed off by eugenelim, RFC-0037 Approver, 2026-06-21.)**
- [x] The runner runs each query `--runs` times (default 3), computes a per-query `trigger_rate` (fraction of runs that fired the skill), and grades: `should_trigger:true` passes iff `trigger_rate > 0.5`; `should_trigger:false` passes iff `trigger_rate < 0.5`.
- [x] When a positive query is run against the whole projected pack and a **different in-pack** skill fires, the runner flags it (intra-pack exclusivity); cross-*pack* collisions are explicitly out of scope for the per-pack runner.
- [x] Each full eval-loop pass writes its own `iteration-<N>/` directory under a per-pack eval-workspace rooted at the repo-relative `.eval-workspace/<pack>/` — **distinct from the isolated temp dir the pack is *projected* into for discovery** (the projection is ephemeral; the eval-workspace persists across passes). Each eval case (skill × query) captures its **actual run output** under a per-run `with_skill/.../outputs/` folder (the Tier-A sibling of the reserved `without_skill/` baseline), and the pass's activation summary (per-query `trigger_rate` + pass counts per skill) is written as `summary.json` in that `iteration-<N>/`. The implementing PR adds a `.gitignore` entry for `.eval-workspace/`, verified by `git check-ignore` on a representative `outputs/` path (the gitignored property is the control that keeps captured outputs out of history). The runner uses only Python stdlib + `tomllib` + the `claude` CLI — no new dependency.
- [x] The runner bounds each `claude -p` invocation with a **wall-clock timeout** (not `--max-turns`), and invokes it via an argv list (no `shell=True`).
- [x] `tools/lint-skill-spec.py` accepts a skill shipping **only** `evals/eval_queries.json` — it no longer errors on an `evals/` directory that lacks `evals/evals.json` — and validates that file as a JSON array whose every element is `{query: non-empty str, should_trigger: bool}`; an `evals/` with neither file still errors, and a skill shipping both files is accepted.
- [x] A coverage check validates that every `[pack.evals].skills` entry names a real skill directory under the pack that ships `evals/eval_queries.json`, failing on a missing skill dir or a missing file; a pack with no `[pack.evals]` block is a no-op. It is hosted in **`tools/lint-skill-spec.py`** (co-located with the `eval_queries.json` schema check) — a source-surface lint that reads `packs/*/pack.toml` and runs both **locally** (via `pre-pr-catalogue.py` in `make build-check`) and in **CI** (the `build-check.yml` required check **and** the `docs.yml` skill-spec job). **(Amended from the original "`lint-packs` source + `lint-agent-artifacts` projection" wording: `[pack.evals]` lives only in `pack.toml`, which is never projected — `lint-agent-artifacts` reads only `.claude/`, so it structurally cannot host a `pack.toml` coverage check; the eval_queries.json *schema* is still validated on both projection and source by the per-skill walk.)**
- [x] `.github/workflows/pack-evals.yml` triggers on `schedule` + `workflow_dispatch` **only** (never `push`/`pull_request`, so an untrusted-fork PR cannot reach the secret), consumes `ANTHROPIC_API_KEY` from repo secrets, reports `trigger_rate` per skill (uploaded as a build artifact), and **never fails the build** in the first cut.
- [x] `pack-evals.yml` declares a least-privilege top-level `permissions: contents: read` (matching the repo's existing secret-consuming `release-agentbundle.yml`), so a compromised dependency or `claude` invocation in the run cannot push commits or mint releases via the default `GITHUB_TOKEN`.
- [x] The `summary.json` serializes **only** bounded fields (`skill`, `query`, `trigger_rate`, pass counts, harness `error_count`/`errored_runs`, and the `mode`/`fidelity`/`provenance` labels) — never raw subprocess `stderr`, the process environment, or the API key — and the runner never echoes `ANTHROPIC_API_KEY` to stdout/logs. The per-run `outputs/` capture stores the **parsed result field** of the `claude -p --output-format stream-json --verbose` stream (the terminal `result` event's `.result`, the model's text) — **not** the raw subprocess stdout stream, and **never** `stderr`, the environment, or the key. **(Detector format per RFC-0037 § Errata E1; see AC1.)** The CI artifact uploaded is the bounded `summary.json` (the upload glob **excludes** `outputs/`). The uploaded artifact's contents are inspected and recorded in the manual-QA pass.
- [x] `make build-check` gains **no** live-model step and stays structural, deterministic, and fast — the eval workflow is wholly separate.
- [x] `core` ships `evals/eval_queries.json` for each user-triggered skill it covers and a `[pack.evals].skills` block listing exactly those skills; `security-checklists` (reviewer-internal, never self-discovered) and `work-loop` (loaded broadly by the plan→execute→review discipline, no narrow user-prompt surface) are **not** listed.
- [x] `converters` ships `evals/eval_queries.json` for each covered skill and a `[pack.evals].skills` block; `msg-to-markdown` is **excluded** (it ships no `evals/` at all — the existing carry-over gate hard-errors if `packs/converters/.apm/skills/msg-to-markdown/evals` exists, `build-check.yml`), so its negative assertion and the rest of the `evals/evals.json` carry-over gate are left untouched (any consolidation is a deferred follow-on).
- [x] Each shipped `eval_queries.json` carries ~8–10 should-trigger and ~8–10 should-not-trigger **near-miss** cases (negatives share keywords/concepts with the skill but need a different one — not trivially-irrelevant prompts).
- [x] `converters` (user-scope) bumps its pack version for the non-cosmetic addition and `make build` refreshes `marketplace.json` to the new version; `lint-packs` and the build are green.
- [x] `core` (self-host-projected) bumps its pack version and `make build-self` projects the new `evals/eval_queries.json` files into `.claude/skills/<skill>/evals/` with a clean `git status` afterward (no projection drift); `lint-packs` and the build are green.
- [x] Adding a `[pack.evals]` block to a `pack.toml` passes `agentbundle validate` and does not drift `marketplace.json` (the section is not projected into plugin/marketplace manifests).
- [x] The runner isolates activation detection behind a small adapter-`Detector` seam (project-for-adapter → run-headless → parse-activation-event) so additional **headless** adapter detectors (codex / copilot / cursor-agent / gemini) are additive, not a rewrite; the first cut ships the `claude-code` detector only. *(The seam also hosts the **in-harness mode** admitted by RFC-0037 § Errata E2 — see Phase 2 ACs below.)*
- [x] The pack-authoring guide (`docs/guides/_shared/how-to/author-a-skill.md`) documents how to **write** activation evals — `evals/eval_queries.json`, the trigger-eval convention (flat `[{query, should_trigger}]`, ~8–10 each way, near-miss negatives), **distinct** from the output-quality `evals/evals.json` — how to declare `[pack.evals].skills`, and how to **run** them locally (`python tools/run-pack-evals.py --pack <name>`); its existing `evals/` description no longer implies `evals.json` is the only accepted layout, and the per-pack reference guides touched by the first cut (`docs/guides/core/`, `docs/guides/converters/`) carry no stale `evals.json`-only layout claim.
- [x] The same guide **disambiguates the two eval files** and captures the **human-authored portions** of the output-quality convention (Tier B — authored by hand, **not executed by this RFC**): for `evals/evals.json` (`{skill_name, evals:[{id, prompt, expected_output, files?, assertions?, expect?}]}` — where the optional `expect` block `{produces, output_contains, output_excludes}` is the Phase-3 B-lite grading surface) it documents what makes a good `expected_output` and a good-vs-weak `assertion`, and names the human-review discipline — each marked **"author now; automated running/grading is deferred to a future RFC (Tier B)"**. The guide states which file serves which tier: `eval_queries.json` → Tier A (triggering, run by `run-pack-evals.py`) vs `evals/evals.json` → Tier B (output quality, authored, not yet executed).
- [x] The eval-workspace layout adopts the agentskills.io evaluating-skills convention and is **forward-compatible with a future grading RFC**: `iteration-<N>/` per full pass; per eval, the Tier-A run output is captured under `with_skill/.../outputs/`; and the layout **reserves (this RFC does not produce) the grading slots** a future RFC fills — `without_skill/` (the Tier-B baseline run), per-run `timing.json` and `grading.json`, and an `iteration-<N>/benchmark.json` (Tier-B `pass_rate`/`delta`) — so adding grading later **fills slots without restructuring** the Tier-A output. The workspace is gitignored (run artifacts, not history).
- [x] `docs/architecture/pack-layout.md` is updated to document **both** (a) the authored eval **source** files in a skill's `evals/` — `eval_queries.json` (Tier-A triggering) alongside the existing `evals/evals.json` (Tier-B quality) — and (b) the **generated** eval-output workspace `.eval-workspace/<pack>/iteration-<N>/…/outputs/` produced when `run-pack-evals.py` runs, explicitly marked **gitignored run-artifacts, not pack source** (so a reader of the layout doc knows what the runner emits vs what authors commit).

### Phase 2 — in-harness / agent-dispatch detector mode (RFC-0037 § Errata E2)

Admitted by E2 so activation evals run where there is no `claude -p` CLI — **Kiro
IDE** — and from an **interactive Claude Code** session. Headless (Phase 1, above)
stays the high-fidelity reference; Phase 2 is the portable, lower-fidelity path.

- [x] **In-harness detector behind the seam.** A second detector mode runs each `eval_queries.json` query through the **host harness's own agent** (Claude Code's `Agent`/subagent tool; Kiro IDE's agent-spawn) in a **fresh sub-context** supplied with the covered skills' names + `description:`, and records which skill the sub-context **reports** it would activate (or none). It reuses the Phase-1 `trigger_rate` + 0.5 grading and the same eval-workspace + `summary.json` contract; every result is **labelled `mode` (`headless`|`in-harness`) and `fidelity` (`observed`|`reported`)** so a reader never conflates the two. Selected via a `--mode in-harness` flag / a catalogue-internal driver.
- [x] **Reported, not observed — the isolation finding is documented.** A dispatched sub-context **cannot be restricted to only the pack's skills** (skill discovery is rooted at the session, not the sub-context's cwd), so the in-harness mode supplies the candidate descriptions explicitly and the sub-context reports a **description-match judgement** — materially lower fidelity than headless's real `Skill` `tool_use` router event. The spec, the summary `fidelity` field, and the authoring guide state this plainly; the in-harness number is a reach proxy, never the calibration baseline.
- [x] **Containment trust boundary (the headless sandbox does not transfer).** The dispatched sub-context holds the host's **full** tool surface, so author-influenced query strings must not be able to drive side effects: the driver dispatches a **read-only / no-execution** sub-context (it elicits the activation judgement, it does **not** let a skill body or any project tool run against the query). This is a **distinct** control from headless's `--allowed-tools Skill` and is specified here as its own AC. Its floor is two procedure-level controls — a **read-only / no-execution dispatch** and **treat-the-query-as-data** (delimited, classify-don't-obey, against prompt injection in author-influenced strings) — documented in the authoring guide; a benign run validated **0 tool calls** (`notes/manual-qa.md`). It is an operator-followed procedure, not a mechanically-enforced sandbox like headless's allowlist. The driver is **catalogue-internal** — a harness-agnostic **documented procedure** the host agent follows (authoring guide) plus the `--mode in-harness` grading CLI; **not** a projected pack primitive — so Charter Principle 3 holds.

### Phase 3 — lightweight in-harness behavior/output check (RFC-0037 § Errata E3)

A bounded slice of Tier B (RFC-0037 § Errata E3): once a skill activates, *does
it do the job* — run the right script, produce the expected artifact, avoid the
documented anti-action? The **full** Tier-B grading (LLM-judge, `benchmark.json`
deltas, with/without-skill, train/validation) stays out of scope (the separate
future RFC); this is the *lightweight* check only.

> **Validation status:** the grading contract (`grade_behavior`, the re-derivation,
> fail-closed) is unit-tested, and the driver loop is validated live **both** with
> a proxy skill **and** end-to-end against a real covered skill —
> `converters/markdown-to-html` ships an `expect` block (eval id 8); a genuine run
> rendered the fixture with the real `render.js` and the runner re-derived the
> deterministic checks to grade it `ok` (`notes/manual-qa.md` §5).

- [x] **Lightweight behavior/output check (`tier: B-lite`).** For each eval in a covered skill's `evals/evals.json`, the in-harness driver has the host agent **run the skill** on the eval's `prompt` **in a per-eval working directory seeded with the eval's `evals/files/` fixtures**; grading then splits by trust: (a) the **deterministic post-conditions are re-derived by the runner itself** — the eval carries an optional `expect` block (`{produces: [<file>], output_contains: [<str>], output_excludes: [<str>]}`); `grade_behavior` reads the working directory and checks `expect.produces` exist and `expect.output_contains`/`output_excludes` hold against the driver-captured `.eval-output.txt` (the runner does **not** trust operator-supplied `*_ok` booleans); a malformed `expect` (e.g. a string where a list is required) or an eval with **no** post-conditions at all (no `expect` and no `assertions`) **fails closed**; (b) only the **semantic `assertions`** a string check can't cover are the host agent's **per-assertion self-attestation**. A malformed/contradictory results file **fails closed**. No separate judge model, no `benchmark.json` deltas, no with/without-skill baseline. Reuses `evals/evals.json` (no new file); writes pass/fail-per-eval + counts to the eval-workspace, labelled `mode: in-harness`, `tier: B-lite`, `provenance: operator-attested`. **Fidelity:** the re-derived post-conditions are **observed** (real artifacts the runner inspects); the semantic-`assertion` verdicts are **self-attested**.
- [x] **Behavior-check containment — an operator/agent-followed procedure with a scope gate, NOT a mechanical sandbox.** The behavior check **must** execute the skill body, and (per the Phase-2 isolation finding) a host agent running the skill keeps its full tool surface, real cwd, inherited environment, and network — so a temp working directory is **not** a mechanical sandbox (honest, like the Phase-2 containment AC). The control is three layers: **(1) scope gate** — only skills the author **opts into** behavior-checking via `evals/evals.json`, restricted to those whose run is **non-destructive and needs no network or credentials** (a destructive or egressing body is out of scope for B-lite until a real OS-level sandbox exists); **(2) procedure** — the documented driver runs the skill in a per-eval working dir under the OS temp root (`tempfile.mkdtemp`, **not** repo-relative), instructs the agent to confine writes to it, and tears it down in a `finally` (guaranteed on error/interrupt) under a per-eval max-runtime; **(3) enforceable slices** — fixtures are copied (via `seed_workspace`, on the live path through `--prepare-workspace`) with **path-confinement**: each fixture's unresolved path is rejected if it or any parent is a symlink, and the resolved path must stay under the eval's `evals/files/` root. *(Aspirational, not yet on any path: the current runner never itself spawns a skill script — the host agent runs the skill — so there is no runner-side env-scrub/network-deny to enforce today; a future runner-executed variant would scrub `ANTHROPIC_API_KEY`/`*_TOKEN`/`*_SECRET` and deny network.)* The spec states plainly this is procedure + scope-gate, not a guarantee the architecture can mechanically keep. A **`security-reviewer` spec-stage pass signed off this design (2026-06-22)** before execution code; a future real sandbox (container / separate user / netns) would lift the scope gate.
- [x] **Pre-test setup is the skill's own Tier-1 prerequisite contract; credentialed/backend skills are activation-only.** The behavior check **never installs anything itself**. Before running a skill it relies on that skill's existing `## Prerequisites` + detection (`--check` / `require.resolve`, the three-tier dependency policy): deps present → run; **deps absent → skip that skill and surface the skill's own documented install command** (never a silent auto-install). This makes adopter runs **repeatable** — install once per the skill's Prerequisites (Node deps install **in place**; `node_modules/` + `package-lock.json` are gitignored so the in-tree install doesn't pollute git), then every subsequent run detects-present and proceeds; nothing about the harness is a one-off. **Skills that integrate a logged-in backend** (credentialed skills on the `auth: cli` / credential-broker contract — e.g. `atlassian`, `figma`) are **out of B-lite scope** by the same scope gate: they need live authentication and a real backend and may mutate remote state, so the harness covers them at **activation (Tier A) only** and **never injects real credentials** into an eval run. Repeatable *behavior* testing of a backend skill needs **recorded-interaction replay (cassettes)** or a disposable **test backend** — a distinct, heavier mechanism that is **future-Tier-B-RFC** scope (recorded in `docs/backlog.md`).

### Phase 4 — report-only LLM-judge for the quality layer (RFC-0037 § Errata E4)

The deterministic B-lite check (Phase 3) covers validity/shape; the **quality**
layer (is the contract well-designed? the diagram the right abstraction? the
verdict correct?) has no ground truth and needs a model.

- [x] **LLM-judge mode behind a config-driven, multi-adapter backend seam.** `run-pack-evals.py --mode judge --judge-adapter <name> [--model M] [--judge-config <toml>] --artifacts <file>` grades each produced artifact against the eval's **rubric** (its `expected_output` + `assertions`) by running a judge backend, parsing a **strict-JSON verdict** (`{verdict: PASS|FAIL, assertions, rationale}`); an unparseable/missing verdict **fails closed** (ERROR, never silent PASS). Backends are **declarative command templates** (`{command, model-flag, extract}`) — built-ins `claude-code` (same model) and `codex` (independent model/IDE, `-s read-only`); an **adopter adds their own (e.g. `kiro-cli`) and selects the model purely by config**, no code change. `{prompt}` is a discrete argv element (no shell). The judge is **judgment-only** (claude granted no tools; codex sandboxed read-only), **report-only**, labelled `mode: judge` / `judge_adapter` / `fidelity: model-judged`. **Honest limits:** a judge wobbles (mitigate: structured per-assertion verdict + report-only) and needs periodic **human calibration**; the **full** Tier-B grading (`benchmark.json` deltas, with/without-skill, train/validation, the formal human-feedback loop) remains the separate future RFC. Validated live: `claude` and `codex` each returned a structured PASS on a good `architect-design` artifact.

## Assumptions

- Technical (validated 2026-06-21): `claude` is on PATH at **2.1.185** (RFC-0037's spike was 2.1.181) and exposes `-p`/`--print`, `--output-format` (`json` **and** `stream-json`), `--verbose`, and `--allowed-tools`; `--max-turns` is **not** a CLI flag (0 hits in `claude --help`). **Corrected (RFC-0037 § Errata E1):** the spike's `--output-format json` returns a result-only envelope with **no `tool_use` events** — the detector uses `--output-format stream-json --verbose`, where the `Skill` activation appears as an `assistant`-event `tool_use` block and the terminal `result` event still carries `.result` (source: live `claude -p` captures, both formats, 2026-06-21).
- Technical (validated 2026-06-21): `tools/lint-skill-spec.py` `check_evals` returns early-error `"evals/ directory present but evals/evals.json is missing"` when `evals/` exists without `evals.json` — the precondition to relax (source: re-read `tools/lint-skill-spec.py` `check_evals`, ~L534).
- Technical (validated 2026-06-21): `evals/` is already a blessed skill subdir (source: `tools/lint-skill-spec.py` `BLESSED_SUBDIRS = {"scripts", "references", "assets", "evals"}`).
- Technical: every adapter projects skills as native `direct-directory` primitives to `<tool>/skills/<name>/` with the `description:` projected byte-identical, but headless-measurability differs: **claude-code** exposes a headless prompt mode with a parseable skill-activation event (`Skill` tool_use); **codex** (`codex exec --json`) and **copilot** (`copilot -p --output-format json`) expose JSON streams (activation-event parse needs a per-adapter spike); **cursor-agent** (the headless Cursor CLI, distinct from the `cursor` GUI launcher) and **gemini** are documented headless+JSON but their CLIs were not installed to probe here; **kiro** and **cursor** are GUI editor launchers (VS Code-fork CLIs: `kiro [paths…]`, no prompt mode), and **kiro-cli** is headless but emits text only (`--format json` is `--list-*`-scoped). Skill projection is a verbatim `shutil.copytree` of the `.apm` tree (`build/main.py`; no per-skill frontmatter rewrite), so the `description:` *bytes* are identical across adapters; each harness's own frontmatter *parsing* may still differ (e.g. Kiro's documented description-length cap) — a separate runtime concern the file-level proxy does not erase (source: `adapter.toml` skill projection rules + `build/main.py` copytree + `claude`/`kiro`/`kiro-cli`/`codex`/`copilot` CLI probes 2026-06-21; cursor-agent/gemini per their docs, not probed here).
- Technical (validated 2026-06-21): `[pack.evals]` passes the `pack.schema.json` validation used by `agentbundle validate` without a schema migration — confirmed empirically by validating a converters manifest with a `[pack.evals].skills` block added (source: `jsonschema.validate(manifest+[pack.evals], pack.schema.json)` probe; the `pack` subschema sets no `additionalProperties: false`).
- Technical (validated 2026-06-21): no live-model CI workflow exists today; the only secret-consuming workflows are the two release workflows (`release-agentbundle.yml` / `release-credbroker.yml`, consuming `ARTIFACTORY_*` — **not** PyPI). `codeql.yml` is `schedule`-triggered but consumes only the built-in `GITHUB_TOKEN`; `build-check*` / `docs` reference no secrets — so `pack-evals.yml` is the first managed-secret + model-API workflow (source: per-workflow `secrets.*` + trigger grep).
- Process (validated 2026-06-21): RFC-0037 is **Accepted** (Status line) and resolved both open questions to their recommended defaults; this spec follows it and ADR-0028 records the decisions (source: re-read RFC-0037 § Status / § Open questions / § Follow-on artifacts).
- Process (validated 2026-06-21): `converters` is `default-scope = "user"` — not projected to this repo's working tree, but a version bump drifts the aggregated top-level `marketplace.json`, refreshed by `make build`; `core` is `default-scope = "repo"` and self-host-projected (its skills appear under `.claude/skills/`), so a bump + added `evals/` files need `make build-self` (source: `packs/{converters,core}/pack.toml` `default-scope` + `build/recipes/self-host.toml` `over = "packs/*/"` + `.claude/skills/` listing).
- Process (validated 2026-06-21): a non-cosmetic pack edit bumps the pack version — this is **repo practice, not a `docs/CONVENTIONS.md` clause** (a grep of `CONVENTIONS.md` finds no pack-version rule; the rule is stated and enforced by precedent — `docs/specs/enriched-pack-manifest/{spec.md,plan.md}` + its merge-base version-diff AC) (source: `CONVENTIONS.md` grep + enriched-pack-manifest precedent).
- Product (not empirically validatable — user direction): this PR delivers the **ADR + spec/plan only**; the runner, lint changes, eval files, `[pack.evals]` blocks, and the workflow land in a separate implementing PR (source: user direction 2026-06-21 "do the ADR and spec/plan"; RFC-0037 § Follow-on artifacts).
- Security (design intent for the implementing PR — no runner code exists this PR to validate against): the runner shells out to `claude -p` with model-influenced query strings passed as **argv** (no `shell=True`), reads `ANTHROPIC_API_KEY` from CI secrets, and writes only to a gitignored workspace dir; the controls are pinned as acceptance criteria (AC5 / AC9 / AC10) and § Never do (source: RFC-0037 Decision 3; security-reviewer spec-stage pass 2026-06-21).
