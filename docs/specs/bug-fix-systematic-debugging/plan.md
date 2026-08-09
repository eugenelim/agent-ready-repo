# Plan: Bug-fix systematic debugging

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog at
> the bottom.

## Approach

Extend the canonical skill in place. First materialize a deterministic red test
for the durable workflow contract, then revise the skill around its existing
sequence instead of replacing it. Broaden the frontmatter activation contract
from fix-word-heavy prompts to natural debugging language and pin both positive
and near-miss routes. Add skill-local LLM-judge scenarios for the judgment
branches that literal tests cannot prove. Finish with the required core patch
release metadata and one self-host projection after all source edits. Run the
focused gates before the catalogue and repository gates, then exercise the
projected skill through a read-only ephemeral Codex invocation.

The riskiest part is preserving the skill's strong normal path while adding
exceptions without creating contradictory instructions. The production-
emergency path is the only case where containment can precede reproduction and
the red regression test; environmental/external outcomes must remain honest
about the absence of an established internal root cause.

## Constraints

- The source of truth is
  `packs/core/.apm/skills/bug-fix/SKILL.md`; `.agents/` and `.claude/`
  projections are generated, never edited directly.
- Pack-specific deterministic tests live under
  `packs/core/tests/skills/bug-fix/`; agent-behavior evals stay skill-local
  under `.apm/skills/bug-fix/evals/`.
- Core receives the patch version named by AC14 in `pack.toml` and
  `.claude-plugin/plugin.json`, followed by self-host regeneration and a dated
  changelog section.
- Shipped pack content contains no repository-only spec, RFC, ADR, or
  acceptance-criterion citations.
- No dependency, new skill, module boundary, blanket defense-in-depth rule, or
  adjacent cleanup enters this change.
- All hand edits use `apply_patch`; generated projections use only the
  documented self-host command.

## Construction tests

**Integration tests:** catalogue lint and verification consume the edited pack;
self-hosting then proves the projected `.agents` and `.claude` skills are
byte-consistent with the canonical source. Repository build checks exercise the
same pack through the catalogue pipeline.

**Manual verification:** run an ephemeral, read-only `codex exec` invocation
against a synthetic multi-component asynchronous defect and record the final
response and exit code in the work-loop handoff. Inspect the response against
AC1–AC7 and AC11; a successful command alone is not sufficient. AC8–AC10 are
covered by their dedicated behavior evals rather than this prompt.

## Design (LLD)

### Design decisions

- Preserve the existing numbered workflow and insert targeted investigation and
  outcome branches; a wholesale rewrite makes regression review unreliable.
  Traces to AC1–AC11.
- Put deterministic structure and ordering in one named pytest test per mapped
  criterion, and put diagnostic judgment in LLM-judge rubrics. Literal tests
  cannot establish that an agent reasons honestly from evidence. Traces to
  AC1–AC13.
- Keep exceptional outcomes inside `bug-fix`; a separate debugging skill would
  split one user journey and weaken activation. Traces to AC3, AC7–AC10.

### Component / module decomposition

- `SKILL.md`: canonical normal path, investigation branches, failure outcomes,
  production-emergency exception, and anti-patterns.
- `test_bug_fix_skill_body.py`: durable structural and ordering contract against
  the canonical skill source.
- `evals/evals.json`: scenario prompts plus positive and negative judge
  assertions for evidence quality and refusal behavior.
- `evals/eval_queries.json`: activation positives and near misses matching the
  frontmatter description, including the observed natural-language gap.
- Pack manifests, changelog, specs index, marketplace aggregate, and self-host
  projections: release and discoverability surfaces.
- `AGENTS.local.md` and the spec note: corrected repo-local verification command
  plus the history explaining why the standalone path must not return.

### State & control flow

Normal flow remains reproduction → red contract test → broad evidence gathering
when the path crosses components → 2–3 rival hypotheses and one-factor
experiments → backward root-cause trace → minimum production fix → coverage and
release hygiene. A known-good comparison supplies evidence before hypothesis
selection.

Three branches alter the flow without erasing it:

1. Active risk permits labelled containment before analysis, then returns to
   evidence-preserving reproduction and diagnosis.
2. Environmental, timing, or external evidence can end without an internal
   root-cause claim, with bounded handling or observability when justified.
3. Three failed evidence-backed hypotheses or fix attempts stop patch stacking
   and surface an architectural discussion; failure count is a stop signal, not
   proof of architectural fault.

### Behavior & rules

- Diagnostic experiments change one factor at a time and are not production
  fixes.
- Multi-component localization observes inputs, outputs, state, and
  configuration at relevant boundaries in one end-to-end run before narrowing.
- Known-good comparisons enumerate meaningful differences rather than copying a
  nearby implementation by intuition.
- Backward tracing follows the bad value or event through each producer and
  caller until its origin or an explicit evidence limit is reached.
- Async waits poll the real condition with a bound; a retry is evidence or
  mitigation, never proof.
- Additional guards are justified only at a crossed boundary, independent
  bypass path, or concrete safety consequence.

### Failure, edge cases & resilience

- An irreproducible defect remains an investigation outcome with documented
  versions, data, attempts, and evidence; it does not become a speculative fix.
- External and timing failures distinguish bounded resilience from root-cause
  correction.
- Emergency containment preserves logs, traces, inputs, and timing evidence
  where doing so does not extend harm.
- Temporary logging, probes, and fault injection are removed before shipping or
  explicitly accepted as durable observability.

### Quality attributes (NFRs)

- Reviewability: the skill diff remains focused and the deterministic test pins
  requirements without hashing or snapshotting the whole document.
- Reliability: model-eval rubrics contain both required and forbidden behaviors
  so a generic debugging answer cannot pass by mentioning keywords.
- Portability: shipped content uses only Markdown and JSON; deterministic tests
  use the repository's existing Python/pytest stack and no new dependency.

### Dependencies & integration

No runtime dependency or external contract is added. The change uses the
existing core-pack eval runner, pytest layout, catalogue commands, self-host
projection, changelog, and Codex CLI already present in the repository workflow.

## Tasks

### T1: The canonical workflow and activation surfaces satisfy their contracts

**Depends on:** none

**Touches:** packs/core/.apm/skills/bug-fix/SKILL.md, packs/core/.apm/skills/bug-fix/evals/eval_queries.json, packs/core/tests/skills/bug-fix/test_bug_fix_skill_body.py

**Verification mode:** TDD

**Tests:**

- Materialize the following compilable red stub as
  `packs/core/tests/skills/bug-fix/test_bug_fix_skill_body.py`, collect it, and
  run it against the unfixed source. It gives each deterministically checked
  criterion (AC1, AC2, AC3, AC11, AC17) its own named test without a full-file
  snapshot or line-count assertion. AC4–AC10 remain judgment checks in T2 and
  T5 rather than being reduced to keyword presence.
- `stub: true`

```python
import json
from pathlib import Path


SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "bug-fix"
    / "SKILL.md"
)
EVAL_QUERIES = SKILL.parent / "evals" / "eval_queries.json"


def _body() -> str:
    return SKILL.read_text(encoding="utf-8")


# STUB: AC1 — the normal path keeps reproduction and red before a fix
def test_ac1_normal_path_keeps_the_regression_test_before_the_fix() -> None:
    body = _body()
    ordered_markers = [
        "**Reproduce first.",
        "**Write the failing test (red).",
        "**Investigate before narrowing.",
        "**Minimum fix.",
    ]
    positions = [body.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


# STUB: AC2 — rival hypotheses retain evidence fields and one-factor probes
def test_ac2_rival_hypotheses_keep_evidence_and_one_factor_experiments() -> None:
    body = _body()
    hypothesis_start = body.index("**List candidate causes, then falsify each.")
    root_cause_start = body.index("**Trace the root cause backward.")
    hypothesis_section = body[hypothesis_start:root_cause_start]
    assert "2–3" in hypothesis_section or "2-3" in hypothesis_section
    assert "Expected / Actual / Verdict" in hypothesis_section
    assert "one factor at a time" in hypothesis_section


# STUB: AC3 — multi-component localization precedes narrowing
def test_ac3_multicomponent_localization_observes_boundaries_before_narrowing() -> None:
    body = _body()
    investigation_start = body.index("**Investigate before narrowing.")
    hypothesis_start = body.index("**List candidate causes, then falsify each.")
    investigation_section = body[investigation_start:hypothesis_start]
    assert "inputs, outputs, state, and configuration" in investigation_section
    assert "run the reproduction once" in investigation_section
    assert "locate the failing component" in investigation_section
    assert "before narrowing" in investigation_section


# STUB: AC11 — retained scope, coverage, commit, and tracker disciplines
def test_ac11_preserves_minimum_diff_and_release_hygiene() -> None:
    body = _body()
    for preserved in (
        "Validate at boundaries the request crosses",
        "independent bypass path",
        "concrete safety consequence",
        "coverage gap",
        "Refuse to fix adjacent issues",
        "Commit body documents the root cause",
        "Loop back to the tracker",
    ):
        assert preserved in body


# STUB: AC17 — router description and activation queries cover the same boundary
def test_ac17_description_and_queries_pin_natural_debugging_language() -> None:
    body = _body()
    frontmatter = body.split("---", 2)[1]
    description = next(
        line.removeprefix("description:").strip().lower()
        for line in frontmatter.splitlines()
        if line.startswith("description:")
    )
    for signal in (
        "root cause",
        "ci-only",
        "intermittent",
        "flaky",
        "production incident",
        "new features",
        "behavior-preserving refactors",
        "postmortems",
        "skill maintenance",
    ):
        assert signal in description

    queries = json.loads(EVAL_QUERIES.read_text(encoding="utf-8"))
    original_queries = {
        ("Fix the bug where saving a draft loses the title", True),
        ("The search returns stale results — diagnose and fix it", True),
        ("This is broken: clicking submit twice creates duplicate orders", True),
        ("Investigate this regression in the CSV parser", True),
        ("Users report the avatar upload fails silently — fix it", True),
        ("The date picker shows the wrong month, please fix it", True),
        ("Our nightly job started crashing yesterday — find and fix the cause", True),
        (
            "Fix this: the total doesn't update when I remove an item from the cart",
            True,
        ),
        ("There's a defect in the rounding logic, track it down and fix it", True),
        ("Let's spec out a new feature to let users export their data", False),
        (
            "Refactor this module to be cleaner — behavior should stay the same",
            False,
        ),
        ("Add a new endpoint for listing invoices", False),
        ("Record why we chose to retry failed webhooks", False),
        ("Write a spec for improved error messages", False),
        ("Bootstrap a new service repo from scratch", False),
        ("Decompose this requirements packet into specs", False),
        ("Upgrade us from React 17 to React 18", False),
        ("Document the deployment runbook", False),
    }
    actual_queries = {
        (item["query"], item["should_trigger"])
        for item in queries
    }
    assert original_queries <= actual_queries

    positives = "\n".join(
        item["query"].lower() for item in queries if item["should_trigger"]
    )
    negatives = "\n".join(
        item["query"].lower() for item in queries if not item["should_trigger"]
    )
    for signal in (
        "root cause",
        "only fails in ci",
        "intermittent",
        "flaky",
        "production incident",
    ):
        assert signal in positives
    for boundary in (
        "new retry feature",
        "behavior-preserving refactor",
        "resolved incident postmortem",
        "improve the bug-fix skill",
    ):
        assert boundary in negatives
```

**Approach:**

- Create the test exactly from the approved stub, run it red, and confirm the
  missing systematic branches—not a path or collection error—cause failure.
- Revise the canonical skill in place, retaining the current strengths and
  adding the normal-path investigation stage, known-good comparison, backward
  trace, async wait guidance, stop rule, honest external outcome, emergency
  containment exception, and diagnostic cleanup rule.
- Broaden the frontmatter description to natural root-cause, CI-only,
  intermittent/flaky, and active-incident language while explicitly excluding
  new features, behavior-preserving refactors, postmortems, and maintenance of
  the skill itself.
- Extend `eval_queries.json` with the four matching positive classes and four
  explicit near-miss boundaries while retaining every existing query; run the
  named AC17 test red before changing either router surface and green afterward.
- Run the dedicated pytest process green, then simplify the skill text without
  weakening the pinned requirements.

**Done when:** the dedicated test is red for the intended missing requirements
before the source edit and green afterward, and the skill remains a single
coherent workflow.

### T2: Behavior evals distinguish systematic diagnosis from plausible patching

**Depends on:** T1

**Touches:** packs/core/.apm/skills/bug-fix/evals/evals.json

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based)` — `python3 -m json.tool` parses the behavior-eval file.
- Validate every behavior eval has `id`, `prompt`, `expected_output`, and non-empty
  `assertions`, with unique IDs and at least one refusal assertion per scenario.
- Inspect the eval runner's discovery of `bug-fix` and, when the configured judge
  is available, run focused behavior evals as report-only evidence.

**Approach:**

- Add five synthetic scenarios: multi-component localization with known-good
  comparison, backward trace, and diagnostic/fix separation; flaky async wait;
  third failed attempt; external/timing outcome; and active production emergency
  with exact-action confirmation, minimized/redacted evidence handling, and an
  instruction-vs-data boundary for diagnostic artifacts.
- Make each rubric require the relevant evidence and forbid the tempting false
  success mode; do not encode repository-only spec references in shipped JSON.

**Done when:** the eval file is valid, discoverable, structurally complete, and
its rubrics collectively cover AC3–AC10. T1 owns AC17's activation boundary.

### T3: The core patch publishes the focused skill improvement without projection drift

**Depends on:** T1, T2

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, docs/specs/README.md, docs/specs/bug-fix-systematic-debugging/notes/lint-agent-artifacts-archaeology.md, AGENTS.local.md, guides/core/how-to/bug-fix.md, .claude-plugin/marketplace.json, .agents/skills/bug-fix/**, .claude/skills/bug-fix/**

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based)` — both source manifests and the regenerated marketplace
  report the target version named by AC14.
- Deep catalogue lint, catalogue verification, self-host write, and drift checks
  pass in their documented order.
- The internal-governance-marker grep is clean for shipped pack content.
- `AGENTS.local.md` contains no reference to the deleted standalone linter and
  names the same current CLI commands proven by `python -m agentbundle ... --help`.
- The production-hotfix guide matches the skill's containment-as-mitigation,
  exact-action confirmation, minimized/redacted-evidence, and diagnostic
  instruction-vs-data contract; guide validation, index coverage, and
  changed-page relative links are clean.

**Approach:**

- Bump both core manifest versions to the target named by AC14, add the dated
  changelog entry, and list this spec as active.
- Correct the stale repo-local command and retain the git-history rationale in
  the spec note; do not add a compatibility wrapper for the deleted script.
- Replace the guide's deferred-regression-test exception with containment as
  labelled mitigation, last-mile confirmation, minimized/redacted evidence,
  an instruction-vs-data boundary for diagnostic artifacts, and the normal
  permanent-fix sequence.
- Run `FORCE=1 make build-self` only after every source and metadata edit; inspect
  and retain only generated changes attributable to this pack update.

**Done when:** release metadata agrees, projections match their source, the spec
is discoverable, the shipped hotfix guidance agrees with the skill, and
catalogue and guide checks pass without direct projection edits.

### T4: The projected skill passes all mechanical repository gates

**Depends on:** T3

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based)` — run the focused pytest, JSON validation,
  artifact lint, catalogue lint/verify, self-host drift, applicable build checks,
  and `lint-spec-status.py` unfiltered.

**Approach:**

- Run gates from narrowest to broadest and fix only failures caused by this diff.

**Done when:** every applicable deterministic gate is green and its unfiltered
exit status is recorded separately from manual behavior evidence.

### T5: A real read-only invocation follows the projected workflow

**Depends on:** T4

**Verification mode:** visual / manual QA

**Tests:**

- `no stub (visual / manual QA)` — invoke
  `codex exec --ephemeral --sandbox read-only` with a natural-language synthetic
  multi-component asynchronous defect prompt that does not name `bug-fix`;
  record exit code and final response, then check AC1–AC7 and AC11 plus that one
  positive AC17 route against the response.

**Approach:**

- Exercise the generated `.agents/skills/bug-fix/` artifact, not the source file
  in isolation. Treat authentication or runtime failure as a named manual-QA gap
  after one bounded attempt rather than retrying an enterprise-blocked command.
- Record whether the answer keeps the red contract test early, localizes the
  component boundary, compares a known-good path, traces backward, uses a real
  condition for waiting, separates diagnostics from the fix, and respects the
  minimum-diff rule. Do not claim this prompt exercises the separate repeated-
  failure, external-outcome, or production-emergency branches; T2 covers them.

**Done when:** the observed invocation follows the intended workflow rather than
merely loading the skill successfully, and AC15 records the composite positive
sample without claiming the rest of AC17's route matrix.

## Rollout

This is the patch release named by AC14 for the repo-scoped core pack. It changes Markdown and
JSON behavior guidance only: no infrastructure, data migration, feature flag,
external-system sequencing, or irreversible step applies. Rollback is a normal
revert to the prior skill and eval content, followed by self-host regeneration.

## Risks

- Added branches could bury the early regression-test discipline. The ordering
  test and manual invocation make that regression visible.
- A literal contract test could freeze editorial wording. Assertions therefore
  pin named workflow markers and obligations, not hashes, snapshots, line counts,
  or full paragraphs.
- Model evals could pass on keyword repetition. Positive and negative assertions
  require sequencing, evidence, and explicit refusals; manual QA checks the
  integrated answer.
- Emergency containment could read as permission for uncontrolled production
  changes. The skill limits action to existing authority, labels mitigation,
  preserves evidence, and returns to root-cause analysis.
- The core version may have advanced on another branch. This plan uses the clean
  branch's observed `2.5.0` baseline and stops rather than riding a different
  unreleased version if metadata changes before execution.

## Changelog

- 2026-08-08: Initial full-mode plan. Preserves the existing bug-fix workflow,
  adds targeted systematic-debugging branches, deterministic contract coverage,
  behavior evals, patch metadata, projection, and manual shipped-skill QA.
- 2026-08-08: Spec review split deterministic and manual verification, narrowed
  each test to the criterion it can prove, corrected the marketplace path, and
  brought the stale repo-local artifact-lint command plus its decision history
  into scope at the user's direction.
- 2026-08-08: Added frontmatter and Tier-A activation coverage after the user
  clarified that an earlier real debugging session failed to select `bug-fix`;
  self-maintenance remains an explicit near miss owned by `work-loop`.
- 2026-08-09: Quality review found the shipped hotfix guide still deferred the
  regression test. Added a focused guide-alignment criterion and verification
  instead of leaving contradictory public guidance in the release.
- 2026-08-09: Security review tightened production containment with last-mile
  confirmation and data-minimized, redacted evidence handling. A proposed new
  `deploy_action` metadata boundary was not adopted because it is outside the
  catalogue's published boundary vocabulary and the skill grants no deploy tool.
- 2026-08-09: Final security review added an instruction-vs-data boundary for
  diagnostic artifacts; the spec and T2/T3 verification text were synchronized
  after adversarial review caught the contract drift.
