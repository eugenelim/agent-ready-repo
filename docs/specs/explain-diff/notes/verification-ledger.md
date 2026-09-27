# Verification ledger: Explain diff

## T1: Contract-test baseline

- The approved nine-test renderer stub family was materialized at `packs/core/tests/skills/explain-diff/test_render_explanation.py` with byte identity to the plan, compiled successfully, and produced the intended absent-implementation red.

## T2: Safe structured renderer

- The first complete renderer contract suite passed with `18 passed`. After review hardening for hostile parser failures and exact version typing, the expanded suite passed with `20 passed`.

## T3: Skill workflow and Core integration

- The canonical `SKILL.md`, document schema, activation evals, Core README entry, and eval allowlist were added. `packs/core/tests/pack/test_work_intake_surface.py` passed with `7 passed` and now pins the skill's least-authority tool surface.

## T5: Adaptive version-2 contract red

- The renderer fixture family now uses required version-2 `presentation` and section `layout` fields and preserves the earlier escaping, filesystem, publication, CSP, quiz, and refusal assertions.
- New tests cover all eight archetypes and their anchor contracts; all four layouts; semantic diagrams, timelines, and annotated code; exact numeric bounds; graph identity and endpoint integrity; one-based exact-integer annotation ranges; hostile new text sinks; and materially distinct semantic composition.
- Intended red: `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/explain-diff/test_render_explanation.py -q` reported `30 failed, 7 passed`. Adaptive and migrated valid cases stopped at the pre-T6 renderer boundary `error: document unknown field presentation`; there were no syntax, import, or test-construction failures. `make lint-ruff` and `make lint-mypy` passed.

## T6: Adaptive version-2 renderer

- The renderer now accepts only schema version 2 and validates the closed presentation enums, section-layout matrix, diagram graph integrity and bounds, timeline bounds, annotated-code ranges, and archetype anchor contracts before resolving or creating output.
- Renderer-owned page classes and semantic markup cover all eight archetypes, four section layouts, three visual modes, three densities, diagrams, timelines, and line-addressable annotated code. Structured input remains escaped data and cannot supply HTML, CSS, JavaScript, URLs, element names, or attribute names.
- Targeted proof: `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/explain-diff/test_render_explanation.py -q` reported `37 passed in 52.00s`.
- Adaptive mutation proof: forcing every document to the narrative archetype class failed `test_renderer_renders_materially_distinct_archetype_structures`; bypassing diagram endpoint membership failed `test_renderer_enforces_diagram_identity_and_endpoint_integrity`; and bypassing reversed annotation-range rejection failed `test_renderer_enforces_exact_one_based_annotation_ranges`. Each invariant was restored through an edit after its named test failed.

## T4: Published Core projections carry the new skill

- Date: 2026-09-25
- Core source manifest: `packs/core/pack.toml` bumped from `2.26.42` to `2.27.0`.
- Claude plugin source manifest: `packs/core/.claude-plugin/plugin.json` bumped from `2.26.42` to `2.27.0`.
- Projection build: `make build-self` failed because the worktree was dirty; `env FORCE=1 make build-self` then failed while replacing generated projections with `PermissionError: [Errno 1] Operation not permitted: '.claude/skills/assimilate-primitive/scripts'`. Direct `rmdir` of that empty generated directory also failed with `Operation not permitted`. `make bootstrap-sites` passed, adding/auditing 457 web packages and 466 docs-site packages with 0 vulnerabilities reported.
- Projection recovery: the failed build deleted four tracked `.claude/skills/assimilate-primitive/` files. Their exact `HEAD` bytes were restored with patches and `git status` no longer reports those deletions. The managed profile rejected writes under `.agents/`, so the user ran `/Users/eu.gene.lim/.pyenv/versions/3.13.13/bin/python3 -m agentbundle catalogue self-host --root . --write --force` in their terminal. It reported `catalogue self-host --write: ok` and created both `explain-diff` projections. Controller SHA-256 checks confirmed the projected `SKILL.md` and renderer bytes matched the canonical Core source before the review fixes below.
- Catalogue verification: passed in the user's supported terminal profile with `catalogue verify: ok`. The output contained only the repository's existing unclassified-file informational records and expected pack-scope exclusions.
- Local gates: passed. `make lint-ruff lint-mypy` reported `All checks passed!` and `Success: no issues found in 149 source files`.
- Targeted renderer suite: passed. `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest packs/core/tests/skills/explain-diff/ -q` reported `18 passed` with a pytest cache warning caused by `Operation not permitted` under `.pytest_cache`.
- Pack-surface tests: passed. `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest packs/core/tests/pack/test_work_intake_surface.py -q` reported `7 passed` with the same pytest cache warning.
- Rendered visual QA: `skipped-no-browser`; this session exposes no browser runtime, so no rendered page was opened or visually inspected.

## Review fixes and mutation proof

- `SEC-001` invariant: the skill does not receive existing-file `Edit` authority. Catching test: `test_changed_skill_permissions_are_minimal`. Exact mutation: restore `Edit` to the `explain-diff` `allowed-tools` line. Expected and observed failure: the test failed on `explain-diff`, comparing `Read Write Edit Bash` with `Read Write Bash`. The canonical skill was restored through an edit.
- `SEC-002` invariant: under-limit hostile JSON parser failures use the renderer's concise refusal channel. Catching test: `test_renderer_contains_hostile_json_parser_failures`. Exact mutation: remove the `RenderError`, `ValueError`, and `RecursionError` handlers around `json.loads`. Expected and observed failure: the 5,000-digit integer returned exit code 1 with a traceback instead of exit code 2 and one stable error line. The handlers were restored through an edit.
- `ADV-001` invariant: `document.version` accepts only the JSON integer `2`. Catching test: `test_renderer_requires_integer_version_two`. Exact mutation: replace the exact-type guard with equality-only validation. Expected and observed failure: JSON `true` rendered successfully with exit code 0 instead of being refused with exit code 2. The exact-type guard was restored through an edit.
- Focused post-fix suites: renderer `20 passed`; Core pack surface `7 passed`.
- Projection status after review fixes: pending a final supported-profile self-host run; the canonical skill metadata and renderer changed after the successful projection proof above.

## T7: Adaptive explainer workflow

- The canonical skill now requires an evidence-grounded version-2 archetype selection before content authoring, routes detailed selection guidance through `references/archetype-selection.md`, keeps renderer input structured-only, and keeps browser opening optional on an adopter-exposed capability with manual local-file-open instructions as the fallback.
- Workflow evals now include one positive selection case for each archetype: algorithm execution trace, transformation data flow, stateful lifecycle transition, focused before/after refactor, component architecture map, API contract, line-addressable annotated code, and justified narrative fallback.
- Canonical renderer proof: `env PYTHONDONTWRITEBYTECODE=1 python3 -c '<fixture render invocation>'` rendered three representative version-2 documents through `packs/core/.apm/skills/explain-diff/scripts/render_explanation.py` into `/private/tmp/explain-diff-t7-7klih_kd/`.
- Structural distinctions recorded from the rendered HTML: `/private/tmp/explain-diff-t7-7klih_kd/data-flow.html` contains `archetype-data-flow`, `data-block-type="diagram"`, and `data-diagram-kind="data-flow"`; `/private/tmp/explain-diff-t7-7klih_kd/state-transition.html` contains `archetype-state-transition`, `data-block-type="diagram"`, and `data-diagram-kind="state-transition"`; `/private/tmp/explain-diff-t7-7klih_kd/annotated-code.html` contains `archetype-annotated-code`, `data-block-type="annotated-code"`, and `data-line-number="1"`.

## Final quality-review repairs

- The renderer suite now sends every rendered schema string field through a hostile payload and parses the generated HTML to prove the values remain decoded text or inert attribute values. It also rejects input-created elements, event-handler attributes, and external navigation or fetch targets.
- The distinct-composition proof now derives semantic/layout signatures from parsed HTML for data-flow, before/after, and annotated-code families and checks the matching renderer-owned visual rules.
- Schema, anchor, escaping, and semantic rendering checks now call the importable validator and renderer in memory. The CLI remains covered for parsing, path confinement, publication, permissions, and full end-to-end smoke behavior. The complete renderer suite improved from `37 passed in 52.00s` to `38 passed in 7.69s`.
- Post-repair gates: `make lint-ruff` passed; `make lint-mypy` passed with no issues in 149 source files; the Core pack surface suite reported `9 passed in 0.79s`.

## T4 final projection proof

- The repository maintainer completed the final supported-shell self-host and catalogue verification commands on 2026-09-26.

## Model-owned-design reset and T8 construction proof

- On 2026-09-26 the scope owner authorized the work-loop reset required after
  the completed-final-task hash made the controlled amendment unschedulable.
  The reset removed only the cohort and engine state records; the approved
  spec, plan, implementation, and prior evidence remained in the worktree. The
  fresh code-mode run is `6c8442dc-cbaf-4529-a97d-7c1cf8fbd387`.
- Engine reset reported the managed profile's known `os.rmdir` denial while
  trying to remove the empty `.loop-run/` directory. No retry was attempted;
  engine reinitialization succeeded with the directory left in place.
- The exact T8 plan-contained publisher stub compiled from
  `docs/specs/explain-diff/plan.md`. A scratch execution at
  `/private/tmp/explain-diff-t8-stub/test_publish_explanation.py` collected 40
  cases and all 40 earned the intended implementation-absent red in 5.69
  seconds. Accepted paths failed on the absent publisher; refusal paths failed
  because no stable refusal category was emitted. The scratch run made no
  browser or visual-quality claim.
- The canonical verification artifact was materialized at
  `packs/core/tests/skills/explain-diff/test_publish_explanation.py` from the
  approved T8 Python fence. `env PYTHONDONTWRITEBYTECODE=1 python3 -m
  py_compile packs/core/tests/skills/explain-diff/test_publish_explanation.py`
  passed. `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider
  packs/core/tests/skills/explain-diff/test_publish_explanation.py -q`
  collected 40 cases and reported `40 failed in 6.67s`; every case reached the
  intended absent-publisher red because
  `packs/core/.apm/skills/explain-diff/scripts/publish_explanation.py` does not
  exist yet.
- Canonical, `.agents`, and `.claude` SHA-256 values match for the adaptive skill (`147004b2e7a04756cd97401342cff22630f22cd685c479c612fdca5499ff9a4c`), renderer (`cf25baec34e4d49b7cf45127cfc6c2bbc3c74dd73f9187671be650a8feb168df`), and archetype guide (`29123cceb5c3776c735a20b1b2be29a9846bc94649f9f21573dd0d97988b3c55`).
- `git status --short` shows no deletions or unrelated tracked changes after regeneration; the earlier four `assimilate-primitive` projection deletions are restored.
- A controller-side catalogue verification attempt encountered the environment's known `Python os.rmdir` denial while `TemporaryDirectory` cleaned its generated `dist/agent-plugins/product-documentation/skills/author-product-docs/references` tree. No catalogue error preceded cleanup. Per the managed-profile instruction, this cleanup-sensitive command was not retried or weakened; the supported-shell completion and matching projection hashes are the verification evidence.

## T9: Guarded model-owned HTML publisher

- The canonical Core skill now has the stdlib-only publisher at `packs/core/.apm/skills/explain-diff/scripts/publish_explanation.py`. It validates a static semantic HTML/CSS subset, refuses active/external capabilities and sensitive literals, injects only the fixed quiz runtime plus matching CSP, and publishes through confined, no-overwrite, owner-only atomic writes.
- Reuse search stopped at the existing explain-diff renderer helpers: its confined input, safe output-name, exclusive `0600` temp-file, and atomic link/unlink publication shape were reused in the new publisher. Other catalogue helpers were not imported because the skill must remain independent at runtime.
- Focused publisher proof in this managed profile reached `39 passed, 1 failed` for `packs/core/tests/skills/explain-diff/test_publish_explanation.py`. The sole pytest failure is the oversized-input parameter of `test_publisher_rejects_size_and_encoding_before_output`; direct invocation through the test helper returned exit code 2, emitted `error: input exceeds 1,048,576 bytes`, and left no output file, so the remaining pytest failure is recorded as the known post-assertion cleanup-sensitive profile limitation and left to CI or a supported profile.
- The obsolete structured renderer surface was removed: `render_explanation.py`, `document-schema.md`, `archetype-selection.md`, and `test_render_explanation.py`.
- Controller gates after the final line-wrap repair passed: `make lint-ruff
  lint-mypy` completed with no errors, and the unaffected publisher suite passed
  `38 passed, 2 deselected in 13.96s` using the exact function-level deselection
  for `test_publisher_rejects_size_and_encoding_before_output`. The direct
  oversized-input assertion above remains the local proof; the complete pytest
  node remains for CI or a supported profile.

## T10: Direct HTML skill workflow and composition floor

- The canonical skill now replaces JSON/archetype authoring with direct complete
  HTML/CSS composition through
  `packs/core/.apm/skills/explain-diff/scripts/publish_explanation.py`. The
  workflow requires a work-specific teaching concept, audience, central visual,
  and reading sequence; four role regions; evidence labels; five native-control
  quiz questions; sensitive placeholder replacement; exact publisher
  placeholders; exact-path reporting; and adopter-specific browser consent.
- The new `references/html-authoring.md` carries the portable authoring floor:
  semantic/native HTML, page-specific tokens, useful unstyled order, narrow
  reflow, visible focus, reduced motion, no external assets, and guidance
  against generic purple-gradient/card-grid/rounded-everything composition. The
  skill remains independent and names no required pack or skill outside its own
  files and Python 3.11 standard library.
- Workflow evals now cover model-authored HTML, architecture boundary, data
  flow, fail-closed lifecycle, sensitive placeholder replacement, independence
  with no other packs installed, browser consent, and no-browser handoff.
  Activation queries retain non-activation coverage for review, document
  conversion, and product UI requests.
- Real publisher proof wrote three distinct artifacts under
  `/private/tmp/explain-diff-t10-clean-6vgeyyv_`: architecture
  `/private/tmp/explain-diff-t10-clean-6vgeyyv_/architecture-published.html`
  with body token `boundary-map` and CSS SHA-256
  `689cf2310c74fd266c1da8e779b3a97fcde1b05983d8e12ccfceb69f00652654`;
  data flow
  `/private/tmp/explain-diff-t10-clean-6vgeyyv_/data-flow-published.html` with
  body tokens `flow-path` and `field-ledger` and CSS SHA-256
  `4d9a0eab4ab06b4b004bc01d54151861b1bf7f7a95bf5fb7b141cc15f20c8a37`;
  lifecycle
  `/private/tmp/explain-diff-t10-clean-6vgeyyv_/lifecycle-published.html` with
  body tokens `state-strip` and `decision-note` and CSS SHA-256
  `1cab75c7e7e7724b4af0a49d9eb303aa18420c204a8a31613c41bfcc7c3ad038`.
  Browser visual QA is `skipped-no-browser`; this session exposes no browser
  runtime, so no rendered inspection was claimed.
- Focused verification passed: skill validator `Skill is valid!`; pack-surface
  suite `9 passed in 0.87s`; unaffected publisher suite
  `38 passed, 2 deselected in 13.16s` using the known cleanup-sensitive
  oversized-input deselection; and `make lint-ruff lint-mypy` completed with no
  errors.

## T4: Model-owned-design projection and final local gates

- The in-session self-host attempt was blocked once by the managed profile at
  `.claude/skills/assimilate-primitive/scripts` and was not retried. The
  repository maintainer then ran the supported-shell self-host command on
  2026-09-26 and confirmed completion.
- Canonical, `.agents`, and `.claude` SHA-256 values now match for the amended
  skill (`9b63f2cda3267ed08fde4b26cbd01ce6869f62897eb744a0f5214aa2233967f1`),
  publisher (`2fcef7e69f24b80aa341795d748fb1d4ecb200f83963eca57d81ea2984701fdc`),
  and HTML authoring reference
  (`49311d2a44696149546846487af7694148741acd51b69edf73c0f32c9f396ffb`).
- Final local gates passed after projection: `make lint-ruff lint-mypy`; skill
  validator `Skill is valid!`; Core pack surface `9 passed in 0.64s`; and the
  unaffected publisher suite `38 passed, 2 deselected in 19.75s` with the exact
  cleanup-sensitive function deselection already recorded under T9.
- Rendered visual QA remains `skipped-no-browser`; no Chrome/browser runtime is
  exposed in this session.

## Final same-diff comparison handoff

- Generated a same-model, same-worktree comparison under
  `/private/tmp/explain-diff-final-comparison-2026-09-26/`: the amended skill
  published `amended-skill.html` through the guarded publisher, the original
  gist prompt produced `gist-skill.html`, and `index.html` presents both pages
  side by side.
- Static parsing succeeded for all three files. The amended publisher exited
  zero and reported the exact output path. Neither page uses an external asset.
- Visual acceptance remains the human gate. This session exposes no browser
  runtime, so it does not claim rendered inspection.

## Security closeout amendment

- The implementation security review reproduced two publisher bypasses: a
  credential assignment could evade the sensitive-literal floor, and duplicate
  attributes could preserve an external URL while validation saw a later
  fragment value.
- Regression cases failed before the fix. The canonical publisher now rejects
  high-confidence credential assignments and duplicate attribute names after
  case folding. Focused proof passed `14 passed, 28 deselected`; the unaffected
  publisher suite passed `40 passed, 2 deselected in 17.00s`; and
  `make lint-ruff lint-mypy` passed.
- Supported projections require one more self-host refresh before the security
  reviewer can close the projection finding. The earlier parity hashes in this
  ledger predate this security amendment.

## Human-readability refinement

- A rendered side-by-side review found that the original-gist comparison gave
  reviewers a faster architecture summary and teaching feedback, while the
  guarded page retained stronger semantics, evidence labels, and accessible
  quiz grouping. The review also reported narrow-screen overflow in the guarded
  page and ambiguous native controls plus a filename overlap in the gist page.
- The accepted refinement keeps model-owned composition and adds outcome floors:
  a reviewer fast path, source and symbol traceability, one worked behavior,
  skippable prerequisite context for mixed audiences, question-specific quiz
  rationales supplied as inert data, stronger narrow-layout and control-state
  checks, and session-specific inspection status only in the handoff.
- The canonical publisher now requires non-empty `data-quiz-rationale` on every
  question and its fixed runtime writes that rationale with `textContent` after
  either a correct or incorrect choice. Model-authored script remains forbidden.
- Verification passed: publisher suite `40 passed, 2 deselected in 30.40s` with
  the known cleanup-sensitive function deselection; Core pack surface `9 passed
  in 0.73s`; skill validator `Skill is valid!`; `make lint-ruff lint-mypy`
  passed; and `git diff --check` passed.
- Supported projections still require one self-host refresh after this
  refinement. Rendered verification of a newly generated page remains pending.

## Text-comprehension and final quality pass

- Direct text comparison found that the guarded page grounded evidence better
  but stacked several analogies, while the gist page stated the core authority
  split more directly. The authoring contract now requires the literal
  technical thesis before metaphor and at most one dominant analogy.
- The quality review found that the documented quiz legend was not mechanically
  enforced. A removed-legend regression failed before the fix; the publisher
  now requires exactly one legend per question. The quality, adversarial, and
  canonical security re-reviews all returned `Clean — ready to commit.`
- Final canonical gates passed after that fix: publisher suite `40 passed, 2
  deselected in 18.23s`; Core pack surface `9 passed in 1.32s`; and
  `make lint-ruff lint-mypy` passed.
- `/private/tmp/explain-diff-final-comparison-2026-09-26/index.html` now points
  to `amended-skill-v4.html`, which uses a literal authority thesis, one
  publishing-press analogy, source and symbol mapping, a worked accepted/refused
  example, teaching rationales, skippable beginner context, and additional
  shrink/overflow safeguards. This session still does not claim rendered QA.

## Subject-dependent visual systems

- The cream serif comparison page is one model-authored treatment, not a
  shipped template. The authoring contract now explicitly chooses palette,
  typography, density, contrast, spacing rhythm, and diagram language afresh
  from the current change and audience.
- No cream, dark, editorial, terminal, dashboard, light/dark mode, font stack,
  prior artifact, or sample CSS is a default house style. Offline publication
  still limits typography to system-local stacks, and every page retains the
  contrast, non-color-cue, accessibility, and internal-coherence floors.
- Skill-engineering provider discovery found no eligible
  `agent-skill-engineering-reference/v1` capability: `knowledge provider
  unavailable`.
- Canonical verification passed: Core pack surface `9 passed in 0.82s`; skill
  validator `Skill is valid!`; and `make lint-ruff lint-mypy` passed. Both the
  adversarial and quality re-reviews returned `Clean — ready to commit.`
- Supported projections still require the pending self-host refresh; the
  earlier projection hashes predate the readability, security, and visual-
  variability amendments.

## Rendered-browser feedback refinement

- User-supplied headless-Chrome evidence for the amended v4 page at 1440, 768,
  and 390 CSS pixels exposed four concrete presentation defects: page-level
  overflow from non-wrapping inline paths, success-colored incorrect quiz
  feedback, mid-word table labels, and a clipped short code sample. This session
  did not run that browser and treats the measurements as supplied evidence.
- The reusable contract now distinguishes inline code from source/diagram
  blocks, keeps tables word-readable in contained scrollers, requires neutral
  pre-evaluation feedback plus distinct text states, and requires typography to
  tolerate fallback font metrics. Print styling is conditional on the named
  audience; neither a light palette nor the v4 cream/serif composition is a
  house style.
- The review's claim that the gist page's font, dark palette, and radio issues
  were not similarly fixable was rejected. Those can be repaired with a robust
  fallback stack, audience-appropriate print rules, and clear native-control
  states. The durable architectural difference remains evidence semantics and
  the guarded fixed-runtime publisher.
- The adversarial review also found that the documented radio-group contract
  was not enforced. A two-case regression first proved that the publisher
  accepted a question split across names and two questions joined under one
  name. The publisher now requires one non-empty name per question and distinct
  names across all five questions.
- The quality review found an off-by-one at the input ceiling. A valid draft of
  exactly 1,048,576 bytes first failed with the publisher's size refusal. The
  loader now rejects only larger inputs, while the existing 1,048,577-byte
  refusal case remains unchanged.
- Post-fix proof passed: publisher `43 passed, 2 deselected in 24.58s` with the
  recorded cleanup-sensitive function deselection; Core pack surface `9 passed
  in 0.51s`; skill validator `Skill is valid!`; `make lint-ruff lint-mypy`; and
  `git diff --check`. The quality re-review returned `Clean — ready to commit.`
  The adversarial review's sole remaining finding is stale generated projections
  pending the supported self-host refresh.
- The repository maintainer completed that supported self-host refresh.
  Canonical, `.agents`, and `.claude` SHA-256 values now match for `SKILL.md`
  (`28bfbd0f1a236ccc58690b37a4b30b80056d7f30a903768dbe9aa1aa3d90ec69`),
  `references/html-authoring.md`
  (`547116a56584c3923b39dbc854b1e7052e06050dec3426940cf29bd12d1f3990`),
  `scripts/publish_explanation.py`
  (`46bd5c89606980d1335e5ed2e9544955bac757a9c5e4c06746383b70e5b9598e`),
  and `evals/evals.json`
  (`647132a26d0e333d92fe3078a90eee7ecbb2bcea243d94969ba727bda0f32275`).
- The repository maintainer visually accepted the amended v6 comparison against
  the original-gist page on 2026-09-26. This closes the human readability and
  rendered-layout gate. The spec is `Shipped`, the plan is `Done`, and all
  fifteen accepted criteria are complete.
