# Plan: Core impact-evidence routing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness);
  `packs/core/tests/pack/test_exploration_consumer_boundary.py` (the guard this
  change narrows); `packs/core/tests/skills/repository-exploration/test_exploration_evals.py`
  and `packs/core/tests/pack/test_work_intake_surface.py` (eval pins and the
  activation-eval allowlist). Non-structural: prose and eval edits only.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Change the guard first, then the prose it guards, so the narrowed test is red
before the sentences exist. Then sharpen the exploration description, add the
evals and their pins, and finish with the release surfaces and a self-host run.
The riskiest part is the narrowed ban: it must allow exactly the three pinned
sentences and still red on any other mention.

## Constraints

- RFC-0079 and `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`:
  Core never depends on or names a provider pack.
- `docs/specs/optional-intelligence-exploration-composition/spec.md`: its
  consumer-boundary name-absence scan is narrowed by owner decision on 2026-10-10 to
  admit the quoted sentences in `work-loop` and `bug-fix` only; its AC-0008
  ceremony ban stays in force.
- `docs/specs/native-provider-selection-validation/spec.md` (Draft): no blind
  provider-selection scoring, and no change to Core's no-provider path.
- `tools/lint-pack-test-boundary.py` check 8: pack tests read only
  `packs/core/`, so changelog and `docs/specs/` checks are goal-based commands.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none; AC-0011 proves projection parity.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise — `packs/core/README.md` § Repository exploration | T2 | README sentence; README assertion in `test_impact_evidence_routing.py` | Section names both calling workflows |
| Decision rationale — consumer-boundary scan pointer | T4 | Note under the shipped spec's consumer-boundary verification entry | spec-status lint clean |
| Release history — `docs/product/changelog.md` | T4 | Versions match; entry placed | Entry under `[Unreleased]` with Highlights |

## Design (LLD)

### Design decisions

Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0007.

Owned by: T1, T2.

- The route is a named skill, not a tool list: naming `repository-exploration`
  keeps provider choice inside the one skill that owns fit, disclosure, and
  caveats, so consuming procedures stay provider-neutral.
- Each mention is optional ("you may ask", "can gather"), so it adds no phase.
- The ban narrows by sentence allowlist, not by file: the test strips each
  quoted sentence from the flattened file text and then asserts the name is
  absent. An unpinned mention anywhere still reds.
- `repository-grounding`'s description stays as is: it is path-seeded and does
  not use caller or impact triggers.
- The description carries no colon-space sequence, because the frontmatter is a plain YAML scalar.
- Exploration's description leads with a pending decision and drops the
  provider's trigger words (blast radius, callers and callees). A provider skill
  that hands decisions back to "whichever workflow skill asked" then composes
  under it. The "Do NOT use it to plan, build, or fix" clause keeps it from
  taking over `work-loop` or `bug-fix`.

### Behavior & rules

Owned by: T1, T2.

The three routing sentences are quoted in AC-0001, AC-0002, and AC-0003; the
test reads them from one `_ROUTE_SENTENCES` map keyed by file. Placement:

- AC-0002's sentence goes right after the PLAN step 5 trio sentence.
- AC-0001's fragment replaces "— grep for callers or trace the entry point." in DECIDE, keeping the leading em dash.
- AC-0003's sentence goes right after "…or reach an explicit evidence limit." in `bug-fix` step 6, and that step's "Grep for the same caller" becomes "Search for the same caller".

The `repository-exploration` description:

"Use this skill when a workflow step or a user needs bounded, attributed repository evidence to settle a pending decision — which files a plan must touch, whether a rename or removal is safe, where a bad value enters before a fix, or whether a fix reaches a live code path. It owns that inquiry for the caller. It records the question and stopping rule, uses an already-exposed capability only when its native action fits, otherwise answers from repository search, and checks load-bearing claims against source. The caller keeps the decision, and no provider is required. Do NOT use it to plan, build, or fix the change itself — the calling workflow owns that. Route path-seeded \"what governs these paths?\" questions to repository-grounding instead."

The README sentence, added after the section's first paragraph:
"`work-loop` and `bug-fix` name it as an optional route for caller, dependents, and impact questions — a plan's touch list, whether a fix reaches a live code path, or where a bug's bad value comes from."

## Tasks

### T1: Narrowed consumer-boundary test and workflow routing sentences

**Depends on:** none

**Touches:** packs/core/tests/pack/test_exploration_consumer_boundary.py, packs/core/tests/pack/test_impact_evidence_routing.py, packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/bug-fix/SKILL.md

**Tests:**
- `test_exploration_consumer_boundary.py`: `_ROUTE_SENTENCES` maps `work-loop/SKILL.md` to the AC-0001 and AC-0002 quotations and `bug-fix/SKILL.md` to the AC-0003 quotation. The name test asserts each quotation is present exactly once in its flattened file, removes them, and asserts the name is then absent. The other seven files keep the plain ban; the four phrase-ban tests are unchanged (AC-0001, AC-0002, AC-0003, AC-0004).
- Mutation: a helper-level test appends an unquoted mention to the flattened `work-loop` text and asserts the strip-then-check helper still reports the name (AC-0004).
- T1 creates `test_impact_evidence_routing.py` with the "grep for callers" and step 6 "Grep for" absence checks (AC-0001, AC-0003).
- Red first: the narrowed test fails before the sentences exist.

**Done when:** both suites pass, and the red run is recorded in `notes/verification-ledger.md`.

### T2: Exploration description, README, and provider-name scan

**Depends on:** T1

**Touches:** packs/core/.apm/skills/repository-exploration/SKILL.md, packs/core/README.md, packs/core/.apm/skills/new-spec/evals/evals.json, packs/core/tests/pack/test_impact_evidence_routing.py

**Tests:**
- `test_impact_evidence_routing.py` parses the description from the `.apm/` frontmatter and checks the required and forbidden strings (AC-0005).
- The same file walks `packs/core/` regular files outside `tests/` with `rglob` and checks the literals (AC-0006). The two `new-spec` eval prompts change "a code-intelligence pack" to "any code-intelligence provider".
- The same file asserts the README "Repository exploration" section names both `work-loop` and `bug-fix`.

**Done when:** `test_impact_evidence_routing.py` and `test_readme_repository_exploration.py` pass.

### T3: Activation evals and behavior evals

**Depends on:** T1, T2

**Touches:** packs/core/.apm/skills/repository-exploration/evals/eval_queries.json, packs/core/.apm/skills/repository-exploration/evals/evals.json, packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/.apm/skills/bug-fix/evals/evals.json, packs/core/pack.toml, packs/core/tests/pack/test_work_intake_surface.py, packs/core/tests/skills/repository-exploration/test_exploration_evals.py, packs/core/tests/pack/test_impact_evidence_routing.py

**Tests:**
- `test_work_intake_surface.py::_EVAL_QUERY_FILES` gains `repository-exploration`, so its balance test covers it (AC-0007).
- `test_impact_evidence_routing.py` checks the decision markers with a whole-word, case-insensitive regex, asserts that regex rejects the AC-0007 fixture example, and checks the bug-fix and `Implement` negatives and the prefix ban (AC-0007).
- `test_exploration_evals.py` gains the new case in `_EXPECTED_EVAL_IDS` and `_PINNED_EVAL_CASES`, with fixture `evals/files/src-function-py.py` and its assertion digest (AC-0008).
- `test_impact_evidence_routing.py` asserts the three new case ids exist, each prompt contains the fixed phrase, and each has an assertion containing "repository search" (AC-0008).
- `agentbundle catalogue lint --root . --deep` passes.

**Done when:** the named suites and the catalogue lint pass.

### T4: Release surfaces, shipped-spec pointer, projections

**Depends on:** T1, T2, T3

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/optional-intelligence-exploration-composition/spec.md

**Tests:**
- `grep -c '"version": "3.0.2"' packs/core/.claude-plugin/plugin.json` and `grep -c '^version = "3.0.2"' packs/core/pack.toml` each print `1` (AC-0009).
- `grep -n -m2 '^## \[' docs/product/changelog.md` prints `## [Unreleased]` then `## [core][3.0.2] — YYYY-MM-DD`, and the next `###` heading after it is `### Highlights` (AC-0009).
- A Python one-liner slices `docs/specs/optional-intelligence-exploration-composition/spec.md` from the line after its consumer-boundary verification entry to the next verification entry, collapses whitespace, and asserts each of the five AC-0010 substrings with `in` (the last is the whole phrase `AC-0008 ceremony criterion is unchanged`), and `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .` reports clean metadata (AC-0010).
- After commit: `agentbundle catalogue verify --root .` passes and `agentbundle catalogue self-host --root . --write` leaves `git status --porcelain` empty (AC-0011).

**Done when:** every command above prints its expected result.

## Rollout

Pure guidance change in a patch release. Rollback is a revert of the PR. No
infrastructure, migration, or sequencing.

## Risks

- The provider skill's description still matches a bare "what calls X?" prompt;
  this change does not decide that case (spec Assumptions).
- `work-loop/SKILL.md` is long and widely pinned by phrase tests; the
  `packs/core/tests` suites touching it run in GATES.

## Changelog
- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
