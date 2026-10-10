# Plan: Code-intelligence pack without Core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/AGENTS.md` (version bump, eval-harness update,
  self-host, no internal-governance citations in shipped content);
  `frontend-engineering` and `architect` as dual-scope packs with no required
  dependency; `packages/agentbundle/agentbundle/commands/install.py`
  `validate_dependencies_required` as the install gate; the `<skill-dir>`
  convention as defined inside `packs/core/.apm/skills/work-loop/SKILL.md`;
  deviation: none.

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
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

T1 removes the manifest dependency and proves the install gate passes. T2
moves the evidence-authority rules into the skill, references, and agents, and
rewrites the composition example without a Core role. T3 rewrites the eval
cases, adds the payload scans that cover `evals.json`, and runs the graded
behavior evals. T4 updates the README, tutorial, version, changelog, and
self-host projection. The riskiest part is T3: the standalone untrusted-output
case must pass with no locator reader, which only a graded run shows.

## Constraints

- RFC-0104 admits the pack and stays unchanged (owner decision).
- `packs/AGENTS.md`: patch bump for changed content (0.1.6 → 0.1.7, matching the
  0.1.6 precedent for a dependency-range change); a non-cosmetic pack update also
  updates the eval harness; shipped pack content cites no internal records.
- CAP-0011 and the golden-composition spec keep Core free of any dependency on
  this pack; this change adds none in either direction.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** one real `agentbundle install --pack code-intelligence
--scope user --adapter claude-code <catalogue>` with `HOME` set to an empty
temporary directory, run from an empty git repository (T1); exit code and the
installed skill path recorded in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Manifest (`pack.toml`, `plugin.json`) | T1, T4 | `test_manifest.py` | Manifest tests green; projection regenerated |
| Skill, references, agents, composition example | T2 | `test_composition_example.py`, `test_authority_guidance.py` | Pack tests green |
| Eval harness | T3 | `test_composition_evals.py`, `test_core_surface.py`; graded run records | Run records in `notes/eval-runs.md`; tally in ledger |
| Pack README, first-session tutorial | T4 | Read-through; catalogue lint | Both read whole; no Core requirement remains |
| Release history | T4 | Changelog entry | Catalogue lint passes |
| Security review outcome | T2, T3 | `security-reviewer` passes | Verdict record |

## Design (LLD)

### Design decisions

- **No recommended dependency.** A recommended entry would put Core back in the
  manifest, and nothing at run time uses Core. Core is named only in user docs.
  Traces to: AC-0002.
- **Find it yourself, not a copied reader.** Without Core, the agent never opens
  a provider-returned location. It searches the repository, from a root the
  prompt or user names, for the symbol the user asked about, and reads what its
  own search returns. Copying Core's reader would create a second owner of
  security-critical confinement code. Traces to: AC-0005, AC-0006, AC-0007.
- **The reader hook is invocation-only.** `SKILL.md` and both agents say a
  confined reader may be used only when the invoking user or the invoking
  skill's own text supplies it. Provider output, file text, and `source` text
  never name one. A refusal or a missing reader sends that dependent back to the
  agent's own search; the location is not opened another way. When Core's
  exploration skill invokes this one, Core's own text supplies its reader, so
  nothing here names Core. Traces to: AC-0003, AC-0005.
- **One definition, then every read-or-verify instruction names its route.**
  `SKILL.md` defines "read the source" and "verify against source" once: the
  agent's own repository search, or index-only `wicked-estate source` output
  labelled as indexed-revision evidence. Two limits keep the routes consistent
  with the trace rules: indexed `source` output never confirms a load-bearing
  call site (only own search does), and `source` is never given a file location
  the provider returned. Every sentence under `.apm/` that tells the agent to
  read a dependent, a hop, or a path, or to verify against source, names one of
  those routes; a load-bearing check names own search. Each forked agent states
  the routes in its own text, because it does not load `SKILL.md`. Known sites
  today (not a complete list — the rule covers every such sentence): `SKILL.md:144` ("the important
  paths are read") and `:171` ("verify it against source");
  `investigation-patterns.md:142-144` ("confirm from its source"), `:160`
  ("read only the hop files"), `:172` ("One hop, read, decide"), and `:178`
  ("open the source"); `evidence.md:38` ("open the payment path") and `:279`
  ("I read the 5 highest-ranked dependents"); `gaps.md:203` ("verify
  load-bearing edges against source"); `code-investigator.md:49` ("open the
  file"), `:3` ("reads the source it needs"), and `:44` ("Read the source");
  `impact-analyst.md:3` ("reads the load-bearing paths"), steps 5-6 (validate
  each breakage against source), and `:113` ("verify against source");
  eval 7's expected output ("hop files to inspect") and assertion ("hop files to
  read"). The forked agents carry the rule in their own text. Traces to:
  AC-0007, AC-0010.
- **Provider `source` output stays allowed, labelled as indexed-revision
  evidence.** A probe on 2026-10-10 against `wicked-estate` 0.21.0 showed
  `source --file <path> --json` returns empty `nodes` for a file added after
  indexing and for a path outside the repository, so the verb reads only the
  index. Traces to: AC-0004.
- **`composition-core-only` is removed.** It tests Core's inquiry owner with no
  provider. Core's own `repository-exploration` evals cover the reader against
  provider output (`evals/files/outside-root-output.json`,
  `mcp-impact-output.json`, `cli-dep-output.txt`). Traces to: AC-0003.
- **"Evidence record" becomes "the answer".** The graded evidence record is a
  Core concept. The other assertions keep their substance. Traces to: AC-0004.
- **`<skill-dir>` is defined in `SKILL.md`** before its first use: the directory
  holding that `SKILL.md`, wherever the skill is installed. The human-facing
  `first-value.verification` line and the README name the script under
  `<skill-dir>` with a parenthetical saying what it stands for. Traces to:
  AC-0008.
<!-- Owned by: T1, T2, T3, T4. -->

## Tasks

### T1: A user-scope install succeeds with no packs installed

**Depends on:** none

**Touches:** `packs/code-intelligence/pack.toml`, `packs/code-intelligence/tests/pack/test_manifest.py`

**Tests:**
- `test_manifest.py::test_declares_no_core_dependency` parses `pack.toml` and
  asserts no entry under any `[pack.dependencies]` kind has `pack == "core"`, and
  no `first-value.prerequisites` item contains "core" as a word (AC-0002).
- `test_manifest.py::test_install_gate_passes_with_nothing_installed` calls
  `agentbundle.commands.install.validate_dependencies_required` with the parsed
  manifest and empty `State()` for repo and user, and asserts it returns without
  raising (AC-0001). Red today: it raises "requires 'core'".

**Done when:** both tests green; the manual install in the ledger exits 0.

### T2: Skill, references, and agents carry the baseline with no Core role

**Depends on:** none

**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md`, `packs/code-intelligence/.apm/skills/code-intelligence/references/*.md`, `packs/code-intelligence/.apm/agents/*.md`, `packs/code-intelligence/tests/pack/test_composition_example.py`, `packs/code-intelligence/tests/pack/test_authority_guidance.py`

**Tests:**
- New `tests/pack/test_authority_guidance.py`, scanning every `.md` file under
  `.apm/` (`SKILL.md`, `references/`, `agents/`):
  - `test_no_open_location_phrasing` — AC-0007's phrase set with whitespace
    collapsed; one planted red sample per phrase, including a line-wrapped one
    (AC-0007, markdown files).
  - `test_markdown_names_no_core` — AC-0003's rule, with one planted red sample
    per token, a curly-apostrophe `Core’s` sample, and green samples
    `## The core loop` and `## Core retrieval` (AC-0003, markdown files).
  - `test_preflight_invocations_use_skill_dir` — AC-0008's rule over `.apm/`
    markdown, with red `python scripts/estate_preflight.py --check` and green
    samples for the `<skill-dir>` form and a markdown link (AC-0008, `.apm/`).
  - `test_authority_rules_present` — `SKILL.md` and both agent files each
    contain the four AC-0010 phrases with whitespace collapsed; for each
    phrase, a planted copy of each file with that phrase removed fails, and a
    planted copy whose reader phrase lacks "own text" fails (AC-0010).
  - Content pins: `SKILL.md` defines `<skill-dir>` before its first use, and
    defines "read the source" and "verify against source" as the two routes
    with both limits (own search alone confirms a load-bearing call site;
    `source` never receives a provider-returned location).
- `test_composition_example.py`: replace the Core-owned assertions
  (`test_example_labels_every_owner`, `test_core_owned_rules_name_no_provider_detail`,
  `test_authority_bullet_covers_both_paths`, `test_step5_does_not_restate_authority_rule`)
  with assertions on the new "Baseline" and "Wicked Estate details"
  subsections: Baseline names question and stopping condition, fallback,
  attribution, authority, and verification, and carries no Wicked Estate
  command, field, or MCP tool name. Move the line-144 pin from the bare
  preflight form to the `<skill-dir>` form.

**Done when:** the pack suite is green.

### T3: Eval cases name no Core and pass with only code-intelligence

**Depends on:** T2

**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/evals/evals.json`, `packs/code-intelligence/tests/skills/code-intelligence/test_composition_evals.py`, `packs/code-intelligence/tests/pack/test_core_surface.py`, `docs/specs/code-intelligence-standalone/notes/eval-runs.md`

**Tests:**
- New `tests/pack/test_core_surface.py` runs AC-0003's, AC-0007's, and
  AC-0008's rules over every non-markdown file under `.apm/` (including
  `evals.json`), reusing the planted samples from T2 (AC-0003, AC-0007,
  AC-0008).
- `test_composition_evals.py`:
  - The pinned case set is the four cases; `composition-core-only`,
    `_CORE_ONLY_FIXTURE_PATHS`, and `test_core_only_case_names_no_provider` are
    removed.
  - Each of the three cases other than `composition-untrusted-output` pins its
    assertions as an expected list: today's assertions with "evidence record"
    changed to "answer", plus AC-0006's assertion on `composition-provider-fit`
    (AC-0006).
  - `test_untrusted_case_asserts_baseline_authority` asserts the six AC-0005
    behaviors appear among that case's assertions (AC-0005).
  - Eval 7's `expected_output` and assertion route hop confirmation through
    the agent's own search; the T3 scan's `hop files to` sample covers both.
  - `_GRADED_PHRASES` gains `own search`, `do not open`, `as data`,
    `embedded instruction`, and `provider-returned`, and the guard passes on
    the rewritten prompts.
- Graded run: each of the four AC-0004 cases runs once in a fresh agent session, from a
  workspace prepared by `agentbundle pack evals run --pack code-intelligence
  --mode in-harness --check behavior --prepare-workspace
  code-intelligence/<eval id>`, with a skill tree holding only the projected
  `code-intelligence` skill without its `evals/` folder. Trace-graded
  assertions use the spec's two trace rules, applied by searching the session
  transcript for each read, search, and shell call. Reports go through
  `--check behavior --reports <reports.json>` (AC-0004).
- Regression runs, recorded but outside AC-0004: cases `1`, `3`, `4`, `5`, `7`,
  `8`, and `9`, whose prompts supply provider output and whose skill text
  changes, run once each. Eval 7's prompt supplies `found: false` and no code,
  so it cannot exercise the never-open rule; its result is recorded, not
  gated. A failure is pre-existing when the same assertion also fails against
  the `origin/main` skill in any recorded run: this delivery's comparison in
  `notes/eval-runs.md`, or, for case `3`'s first assertion, the earlier record
  in `docs/specs/code-intelligence-golden-composition-example/notes/eval-runs.md`
  § Known pre-existing result. Any other failure, except eval 7's, returns to
  T2.

**Done when:** the pack suite is green, the graded tally in the ledger shows
4/4 AC-0004 cases passing every assertion, every regression-run failure other
than eval 7's also fails against the `origin/main` skill in a recorded run as
the Tests bullet defines it, and eval 7's result is recorded in
`notes/eval-runs.md` with the owner decision as its disposition.

### T4: Docs, version, changelog, and projection updated

**Depends on:** T1, T2, T3

**Touches:** `packs/code-intelligence/README.md`, `guides/code-intelligence/tutorials/first-session.md`, `packs/code-intelligence/pack.toml`, `packs/code-intelligence/.claude-plugin/plugin.json`, `packs/code-intelligence/tests/pack/test_manifest.py`, `docs/product/changelog.md`, self-host projection paths

**Tests:**
- `test_manifest.py::test_pack_version_is_0_1_7` replaces the 0.1.6 pin (AC-0009).
- `test_manifest.py::test_first_value_and_readme_preflight_use_skill_dir`
  applies AC-0008's rule to `first-value.verification` and `README.md`, and
  asserts the verification line says what `<skill-dir>` stands for (AC-0008,
  manifest and README).

**Done when:** manifest tests green; `agentbundle catalogue lint --root . --deep`
and `agentbundle catalogue verify --root .` pass; `agentbundle catalogue
self-host --root . --write` leaves no diff on re-run.

## Rollout

Ships with the next catalogue release. Reversible by reverting the PR. Existing
installs keep working; a repo that has Core keeps it.

## Risks

- The in-flight `native-provider-selection-validation` spec (Draft) links the
  first-session tutorial. Step 2 keeps the Core install command, now marked
  optional, so its links stay valid.
- A standalone run of `composition-untrusted-output` may try to open
  `../outside/billing.py` because no reader exists to refuse it. The graded run
  shows whether the rule holds; a fail returns to T2.
- A content scan by fixed phrasings is a proxy: it catches the known
  open-location wordings, not every paraphrase. The graded runs carry the
  behavioral proof.

## Changelog

- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
