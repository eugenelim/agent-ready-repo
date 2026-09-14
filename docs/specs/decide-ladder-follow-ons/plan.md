# Plan: DECIDE ladder follow-ons

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/.apm/skills/work-loop/SKILL.md` DECIDE and
  conditional-reference routing; `docs/specs/finding-response-receptacle/spec.md`;
  `docs/specs/finding-response-receptacle/notes/owner-decisions.md`;
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`;
  the three existing skill test modules named below

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

Land the four rows as three bounded guidance changes, destination-specific
lifecycle tests, and release/projection bookkeeping. The content guards are
class guards: each reads every occurrence in a bounded region and carries an
explicit exception map. Each guard includes an in-memory regression mutation
that the old or naive predicate accepts and the new predicate rejects.

The core skill has a hard edit budget. R1 receives 5 added DECIDE body lines, R2
receives 7, and R3 receives 3: 15 DECIDE lines total. R4 receives exactly one
conditional-routing table row; its substance has a 24-body-line ceiling in the
new reference. Starting from 874 body lines after frontmatter, the final
`work-loop/SKILL.md` body must be no more than 890 lines and remains below the
1,000-line CAT-S003 error threshold.

## Constraints

- The answer set, tokens, order, stop rule, and the advisory effect of
  `response` and `reason` are fixed by the owner decisions and this spec's
  Ask-first boundary.
- R1, R2, and R4 are guidance plus content pins only. No acceptance criterion
  may be introduced for their content while
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`
  owns the deferred promotion gate.
- R3 alone contributes acceptance criteria. Its tests must assert each newly
  covered destination, because the current broad substring assertions do not
  detect these omissions.
- The marker convention names the criterion a stub pins; R1, R2, and R4 stubs
  instead name their content pin because those rows ship prose under a
  criterion-promotion gate.
- `references/delivery-contract-lifecycle.md` remains the single owner of where
  observed mutation reds are recorded. The new reference links there and does
  not restate that placement rule.
- `FORCE=1 make build-self` runs only from a clean source commit. The generated
  projections land in a separate second commit.
- No new shipped pack prose may cite an internal acceptance-criterion
  identifier, RFC/ADR ordinal, or `docs/specs`, `docs/rfc`, `docs/adr`, or
  `docs/contracts` path. The portability condition for this slice is no NEW
  match in the shipped pack files it adds or edits, compared against a recorded
  per-file baseline — not a no-match result, and not a claim that the
  repository-wide corpus is zero. It is not: `packs/` currently carries roughly
  2045 matches, and `work-loop/evals/evals.json` alone holds 14 permitted
  illustrative adopter examples. The scoped path list must name every `packs/`
  file this slice touches, eval registers included, since those ship as live
  adapter projections. Preserve permitted illustrative teaching examples;
  rewrite only citations to this repository's internal governance while
  retaining their rationale.
- EXECUTE materializes each approved stub unchanged and earns the red before
  production edits. R3 uses `# STUB: AC<n> — <property>`; R1, R2, and R4 use
  `# STUB: <test_function_name> — <the property this test pins>`.
- The release edits both version carriers to 2.25.25 and adds a new changelog
  section; no released changelog body is changed.

## Construction tests

The per-task suites below own the row-level checks. After all source tasks, run
the touched pack suites, the two projection roster nodes, and the repository's
local lint gate. Mutation observations are recorded during execution in
`docs/specs/decide-ladder-follow-ons/notes/verification-ledger.md`, which is
created only when those observations exist.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| DECIDE guidance in `work-loop/SKILL.md` | T1, T2 | Region-wide pins and mutation regressions | T7 gate receipt and body-line count |
| Upstream lifecycle rules | T2 | Three destination-specific tests | AC-0001 through AC-0003 checked |
| Mutation-proof reference and route | T3 | Obligation, link, and routing tests | Mutation reds in the verification ledger |
| Changed-skill eval registers | T4 | Catalogue structural lint and three content pins | Registers are valid; no eval execution is claimed |
| Roadmap and release truth | T5 | Four closed rows, version parity, new changelog section | Closeout confirms no released section changed |
| Self-host projections | T6 | Both projection roster nodes | Generated files are isolated in the projection commit |

## Design (LLD)

### Design decisions

- R1 narrows the existing `narrow-the-claim` definition; it does not add or
  reorder an answer. The old clause about stated reach shrinking stays in place
  so the existing pin remains useful.
- R2 names a literal sweep and a semantic walk as separate instruments, requires
  both after a review repair, and re-fires the step-8a anchor-test sweep only
  over files touched by that repair.
- R3 treats revision-bound lifecycle invalidation as a valid upstream pin and a
  content test as the downstream pin. The materiality lists, not DECIDE, perform
  the invalidation.
- AC-0001 through AC-0003 are narrowed to guidance that the named content
  oracles reach: destination-specific materiality classification plus the
  demotion instruction. No named oracle performs an artifact lifecycle
  transition, so strengthening a check cannot reach the former runtime claim.
- R4 owns proof discipline in `references/mutation-proof.md`. The routing row
  loads it when a repair or claimed fix needs mutation proof, and the reference
  points to the existing verification-ledger section for observation placement.

## Shipped ahead of a criterion, deliberately

- **R1 — claim/check mismatch and direct-property repair.** The discriminator
  is deferred AC-0024 in
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`.
  That intent's Boundary permits the guidance to be edited and shipped against
  a content pin but gates its promotion to an acceptance criterion.
- **R2 — literal sweep plus semantic walk after repair.** Deferred AC-0023 owns
  the review-response sweep obligation. This delivery ships the corrected
  guidance and a class guard without creating a second criterion owner.
- **R4 — mutation-proof discipline.** Deferred AC-0022 is the neighbouring
  authoring criterion for executing and recording a stated mutation. The new
  reference supplies the missing discipline and a content pin, while criterion
  promotion remains with the same gating intent.

## Tasks

### T1: R1 and R2 DECIDE class guards pass

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/tests/skills/work-loop/test_finding_response_fields.py`

**Verification mode:** TDD

**Tests:**

- `test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks`
  (`stub: true`); pins the reachable-check strengthening versus
  unreachable-check narrowing discriminator.
- `test_fix_requires_a_check_of_the_property_not_a_consequence`
  (`stub: true`); pins direct-property checking rather than consequence-only
  checking.
- `test_post_repair_traversal_uses_literal_and_semantic_instruments`
  (`stub: true`); pins both traversal instruments and the touched-file
  anchor-test rerun.

```python
"""PLAN-only red stub for DECIDE guidance content pins."""

import re
from pathlib import Path


WORK_LOOP = Path.cwd() / "packs/core/.apm/skills/work-loop/SKILL.md"


def _section(heading: str) -> str:
    """Return one Markdown section from the work-loop skill."""
    text = WORK_LOOP.read_text(encoding="utf-8")
    level = len(heading) - len(heading.lstrip("#"))
    start = re.search(rf"^{re.escape(heading)}\s*$", text, re.M)
    assert start is not None
    following = text[start.end() :]
    end = re.search(rf"^#{{1,{level}}} ", following, re.M)
    return text[start.start() :] if end is None else text[start.start() : start.end() + end.start()]


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace."""
    return " ".join(text.split())


# STUB: test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks — claim reach selects strengthen or narrow
def test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks() -> None:
    cut = _flat(_section("### Cut"))

    assert "some check can reach the claimed property" in cut
    assert "strengthen the check" in cut
    assert "no check can reach the claimed property" in cut


# STUB: test_fix_requires_a_check_of_the_property_not_a_consequence — a repair check asserts the property itself
def test_fix_requires_a_check_of_the_property_not_a_consequence() -> None:
    fix = _flat(_section("### Fix"))

    assert "check asserts the repaired property itself" in fix
    assert "not only a consequence" in fix


# STUB: test_post_repair_traversal_uses_literal_and_semantic_instruments — post-repair traversal has both instruments
def test_post_repair_traversal_uses_literal_and_semantic_instruments() -> None:
    decide = _flat(_section("## Step 5. DECIDE"))

    assert "literal sweep" in decide
    assert "semantic walk" in decide
    assert "step-8a anchor-test sweep" in decide
    assert "every file the repair touched" in decide
```

Recorded compile/red validation: bare
`pytest /private/tmp/decide_ladder_t1_stub.py` collected 3 tests and printed
`FFF [100%]`; the exact first missing strings were
`some check can reach the claimed property`,
`check asserts the repaired property itself`, and `literal sweep`, followed by
`3 failed in 0.94s`. The disposable file was deleted after validation.

- Add `test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks`.
  Its extractor walks every answer bullet in `### Cut`; the named exception map
  is `drop-the-claim`, `cut-the-item`, and `demote-the-claim`, because none
  changes the reach of a surviving contract claim. Mutate the scoped
  `narrow-the-claim` body back to the pre-change implementation. Prove the old
  `test_narrow_the_claim_keeps_the_obligation_in_contract` predicate still
  passes that mutation and the new two-outcome oracle fails it.
- Add `test_fix_requires_a_check_of_the_property_not_a_consequence`. Its region
  contains every repair requirement under `### Fix`; the named exceptions are
  the two answer-token bullets, which select the repair target rather than the
  property asserted. Mutate only the direct-property requirement to permit a
  consequence. Prove a naive guard that sees both repair tokens stays green and
  the new oracle reds.
- Replace the exact-sentence test at the current R2 seam with
  `test_post_repair_traversal_uses_literal_and_semantic_instruments`. It scans
  every traversal-instrument sentence between the frontier start and the
  severity routing. The named exceptions are the frontier-expansion and
  empty-frontier termination sentences, which define extent rather than an
  instrument. Restore the pre-change one-mode sentence in the mutation; prove
  the old quote predicate passes and the new dual-instrument, post-repair oracle
  reds.
- Add a second isolated mutation that removes or weakens only the touched-file
  step-8a anchor-test rerun while leaving the literal sweep and semantic walk
  intact. The naive traversal-only guard must stay green while the complete
  oracle reds.
- Run `pytest packs/core/tests/skills/work-loop/test_finding_response_fields.py`.
- Run `sed -n '11,$p' packs/core/.apm/skills/work-loop/SKILL.md | wc -l` and
  require a count no greater than 890.

**Approach:**

- Preserve the existing narrowing clause, add the reachable-check branch, and
  add the direct-property Fix sentence within R1's five-line allocation.
- Split the traversal sentence by instrument and add the post-repair anchor-test
  rerun within R2's seven-line allocation.

**Done when:** Every command and mutation assertion in this task's `Tests`
passes, including the body-line ceiling.

### T2: All upstream demotion destinations invalidate their lifecycle bindings

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/intake-intent/SKILL.md`,
`packs/core/.apm/skills/author-delivery-brief/SKILL.md`,
`packs/core/tests/skills/intake-intent/test_intent_shaping_review.py`,
`packs/core/tests/skills/author-delivery-brief/test_delivery_brief_shaping_review.py`

**Verification mode:** TDD

**Tests:**

- `test_intent_opportunity_edit_is_material_lifecycle_change` (AC-0001);
  `stub: true`.
- `test_rabbit_holes_edit_is_material_lifecycle_change` (AC-0002);
  `stub: true`.
- `test_design_artifacts_edit_is_material_lifecycle_change` (AC-0003);
  `stub: true`.
- `test_demotion_pin_guidance_distinguishes_upstream_and_downstream`
  (AC-0001, AC-0002, AC-0003); `stub: true`.

```python
"""PLAN-only red stub for upstream demotion materiality."""

from pathlib import Path


ROOT = Path.cwd()
INTENT = ROOT / "packs/core/.apm/skills/intake-intent/SKILL.md"
BRIEF = ROOT / "packs/core/.apm/skills/author-delivery-brief/SKILL.md"
WORK_LOOP = ROOT / "packs/core/.apm/skills/work-loop/SKILL.md"


def _between(path: Path, start: str, end: str) -> str:
    """Return a normalized bounded prose region."""
    text = " ".join(path.read_text(encoding="utf-8").split())
    return text.split(start, 1)[1].split(end, 1)[0]


# STUB: AC-0001 — Opportunity is an intent materiality destination
def test_intent_opportunity_edit_is_material_lifecycle_change() -> None:
    materiality = _between(INTENT, "For an intent, material means", "Before sealing")

    assert "`Opportunity`" in materiality


# STUB: AC-0002 — Rabbit holes is a brief materiality destination
def test_rabbit_holes_edit_is_material_lifecycle_change() -> None:
    materiality = _between(BRIEF, "For a brief, material means", "Before sealing")

    assert "`Rabbit holes`" in materiality


# STUB: AC-0003 — Design artifacts is a brief materiality destination
def test_design_artifacts_edit_is_material_lifecycle_change() -> None:
    materiality = _between(BRIEF, "For a brief, material means", "Before sealing")

    assert "`Design artifacts`" in materiality


# STUB: AC-0001 — upstream and downstream pins stay distinct for intent demotion
# STUB: AC-0002 — upstream and downstream pins stay distinct for brief demotion
# STUB: AC-0003 — upstream and downstream pins stay distinct for brief demotion
def test_demotion_pin_guidance_distinguishes_upstream_and_downstream() -> None:
    decide = _between(WORK_LOOP, "### Cut", "### Route")

    assert "revision-bound lifecycle invalidation" in decide
    assert "downstream" in decide
    assert "content test" in decide
```

Recorded compile/red validation after one bounded correction that normalized
the source's line-wrapped boundary text: bare
`pytest /private/tmp/decide_ladder_t2_stub.py` collected 4 tests and printed
`FFFF [100%]`; the exact missing strings were `` `Opportunity` ``,
`` `Rabbit holes` ``, `` `Design artifacts` ``, and
`revision-bound lifecycle invalidation`, followed by `4 failed in 0.64s`.
The disposable file was deleted after validation.

- Add `test_intent_opportunity_edit_is_material_lifecycle_change`. Enumerate
  every recording section in the intent's bounded movement region; `Assumptions`
  is the named exception because it is recording context but not an admitted
  demotion destination. Delete only `Opportunity` from the materiality list and
  prove the existing broad material-revision test stays green while this test
  reds. Verifies AC-0001.
- Add `test_rabbit_holes_edit_is_material_lifecycle_change` and
  `test_design_artifacts_edit_is_material_lifecycle_change`. Enumerate every
  recording section in the brief's bounded movement region; `Ready gaps` is the
  named exception because the brief drops it on leaving `Draft`. Delete each
  admitted destination independently and prove the existing broad test stays
  green while its destination test reds. Verify AC-0002 and AC-0003 separately.
- Add a DECIDE content pin that enumerates every demotion-pin type in the
  demotion paragraph; downstream lifecycle material is the named exception to
  upstream revision binding and must retain a content test. Mutate the upstream
  branch back to content-test-only; prove the prior pin vocabulary remains
  present while the new two-branch oracle reds.
- Run `pytest packs/core/tests/skills/intake-intent/test_intent_shaping_review.py`.
- Run `pytest packs/core/tests/skills/author-delivery-brief/test_delivery_brief_shaping_review.py`.
- Run `pytest packs/core/tests/skills/work-loop/test_finding_response_fields.py`.
- Run `sed -n '11,$p' packs/core/.apm/skills/work-loop/SKILL.md | wc -l` and
  require a count no greater than 890.

**Approach:**

- Add `Opportunity`, `Rabbit holes`, and `Design artifacts` to the materiality
  lists that invalidate bound shaping-review results.
- Use R3's three DECIDE lines to distinguish upstream revision binding from
  downstream content tests; do not restate either lifecycle list in DECIDE.

**Done when:** Every command and mutation assertion in this task's `Tests`
passes, including all three destination-specific reds and the body-line ceiling.

### T3: Mutation-proof obligations have one routed owner

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/references/mutation-proof.md`,
`packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/tests/skills/work-loop/test_finding_response_fields.py`

**Verification mode:** TDD

**Tests:**

- `test_mutation_proof_reference_carries_every_obligation`
  (`stub: true`); pins every mutation-proof field and the pre-fix
  implementation requirement.
- `test_mutation_proof_requires_edit_restore`
  (`stub: true`); pins edit-only restoration.
- `test_mutation_proof_reference_is_conditionally_routed`
  (`stub: true`); pins the conditional route to the mutation-proof owner.

```python
"""PLAN-only red stub for mutation-proof guidance."""

from pathlib import Path


ROOT = Path.cwd()
REFERENCE = ROOT / "packs/core/.apm/skills/work-loop/references/mutation-proof.md"
WORK_LOOP = ROOT / "packs/core/.apm/skills/work-loop/SKILL.md"


def _reference() -> str:
    """Return normalized mutation-proof guidance."""
    return " ".join(REFERENCE.read_text(encoding="utf-8").split())


# STUB: test_mutation_proof_reference_carries_every_obligation — the reference carries every proof field
def test_mutation_proof_reference_carries_every_obligation() -> None:
    reference = _reference()

    for field in (
        "invariant",
        "catching test",
        "exact mutation",
        "expected failure",
        "observed failure",
    ):
        assert field in reference
    assert "pre-fix implementation" in reference
    assert "do-nothing stub" in reference


# STUB: test_mutation_proof_requires_edit_restore — implementation restoration is edit-only
def test_mutation_proof_requires_edit_restore() -> None:
    reference = _reference()

    assert "restore the implementation only by editing" in reference
    for forbidden in ("checkout", "reset", "stash"):
        assert forbidden in reference


# STUB: test_mutation_proof_reference_is_conditionally_routed — repair verification routes to this owner
def test_mutation_proof_reference_is_conditionally_routed() -> None:
    skill = WORK_LOOP.read_text(encoding="utf-8")

    assert "references/mutation-proof.md" in skill
    assert "repair or claimed fix needs mutation proof" in skill
```

Recorded compile/red validation: bare
`pytest /private/tmp/decide_ladder_t3_stub.py` collected 3 tests and printed
`FFF [100%]`; the first two tests raised the exact
`FileNotFoundError: [Errno 2] No such file or directory` for
`packs/core/.apm/skills/work-loop/references/mutation-proof.md`, and the third
failed on the exact missing string `references/mutation-proof.md`, followed by
`3 failed in 0.76s`. The disposable file was deleted after validation.

- Add `test_mutation_proof_reference_carries_every_obligation`. Enumerate every
  proof field in the new reference: invariant, catching test, exact mutation,
  expected failure, and observed failure. Ledger placement is the named
  exception because the linked lifecycle reference already owns it. Mutate the
  pre-fix-implementation rule to permit a do-nothing stub while retaining all
  obvious mutation keywords; prove the naive keyword guard passes and the
  obligation oracle reds.
- Add `test_mutation_proof_requires_edit_restore` and mutate `editing` to a Git
  restore operation. Scan every restore method in the reference; temporary-file
  cleanup is the named exception because it does not restore implementation.
  Prove a naive `restore` keyword guard stays green while the method oracle reds.
- Add `test_mutation_proof_reference_is_conditionally_routed`. Inspect every
  reference row whose predicate concerns repair verification; state-schema is
  the named exception because it owns loop state rather than proof discipline.
  Mutate the new row's target to state-schema and prove a generic routing-row
  guard passes while the owner-specific oracle reds.
- Run `pytest packs/core/tests/skills/work-loop/test_finding_response_fields.py`.
- Run `sed -n '11,$p' packs/core/.apm/skills/work-loop/SKILL.md | wc -l` and
  require a count no greater than 890.

**Approach:**

- Create a reference of no more than 24 body lines. State that the proof uses
  the pre-fix implementation, never a do-nothing stub; states the five proof
  fields; rejects a still-green mutation; and restores only by editing, never
  checkout, reset, or stash.
- Link to `references/delivery-contract-lifecycle.md#verification-ledger`
  instead of restating where observations go. Add exactly one routing-table row.
  Do not edit the existing lifecycle reference.

**Done when:** Every command and mutation assertion in this task's `Tests`
passes, the routing row is unique, the linked ledger remains the single
placement owner, and the body-line ceiling holds.

### T4: Changed skills update their eval registers

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`,
`packs/core/.apm/skills/intake-intent/evals/evals.json`,
`packs/core/.apm/skills/author-delivery-brief/evals/evals.json`

**Verification mode:** goal-based structural check

**Tests:**

- Run `rg -n '"id": "(decide-repair-traversal|intent-opportunity-materiality|brief-materiality-destinations)"' packs/core/.apm/skills/work-loop/evals/evals.json packs/core/.apm/skills/intake-intent/evals/evals.json packs/core/.apm/skills/author-delivery-brief/evals/evals.json` and require exactly one matching case in its owning register.
- Pin each owning case to the guidance this change alters, not merely to its
  identifier. An identifier-only check cannot tell a correct eval update from
  three structurally valid cases carrying the right ids and unrelated content.
  For each register, run the bounded command below and require the named token
  to appear inside the matched case region, between its `"id"` line and the end
  of that case:
  - `rg -n -A 14 '"id": "decide-repair-traversal"' packs/core/.apm/skills/work-loop/evals/evals.json` must contain both `literal sweep` and `semantic walk`.
  - `rg -n -A 14 '"id": "intent-opportunity-materiality"' packs/core/.apm/skills/intake-intent/evals/evals.json` must contain `Opportunity`.
  - `rg -n -A 14 '"id": "brief-materiality-destinations"' packs/core/.apm/skills/author-delivery-brief/evals/evals.json` must contain both `Rabbit holes` and `Design artifacts`.
- Run `agentbundle catalogue lint --root . --deep` to validate the three JSON
  registers, their skill names, unique IDs, assertion shape, and any fixture
  references. This is a structural/lint check only: `evals.json` is a register,
  and no suite executes these cases.

**Approach:**

- Add one focused eval case to each changed skill: literal-plus-semantic repair
  traversal for work-loop, `Opportunity` materiality and review invalidation for
  intake-intent, and `Rabbit holes` plus `Design artifacts` materiality and
  review invalidation for author-delivery-brief.
- Both shaping skills have their own `evals/` directories and `evals.json`
  registers, so neither uses the work-loop register as a substitute.

**Done when:** The identifier command finds exactly one owning case for each
changed skill, each of the three bounded content-pin commands shows its named
token inside the matched case region, and catalogue lint accepts all three
registers — without claiming that the registered evals ran.

### T5: Source release and roadmap records are ready for projection

**Depends on:** T4

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`docs/product/changelog.md`, `docs/product/findings/roadmap-intents.md`,
`docs/specs/decide-ladder-follow-ons/notes/verification-ledger.md`,
`web/src/lib/now-highlights.generated.json`

**Verification mode:** goal-based check

**Tests:**

- Run `rg -n '2\.25\.25' packs/core/pack.toml packs/core/.claude-plugin/plugin.json`
  and require exactly one matching version field in each file.
- Run `rg -n '^## \[core\]\[2\.25\.25\] — 2026-09-13$|^### Highlights$' docs/product/changelog.md`
  and inspect only the new release region for one grounded outcome-led
  highlight written as a `-` bullet; a paragraph is invalid because the parser
  silently drops it.
- Run `rg -n '→ spec/decide-ladder-follow-ons|SKILL\.md:528|delivery-contract-lifecycle\.md:71|_loop_guards\.py:578' docs/product/findings/roadmap-intents.md`
  and require all four scoped rows to point to this spec and the R4 row to name
  the corrected occurrence evidence.
- Run `grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' packs/core/.apm/skills/work-loop/SKILL.md packs/core/.apm/skills/work-loop/references/mutation-proof.md packs/core/.apm/skills/intake-intent/SKILL.md packs/core/.apm/skills/author-delivery-brief/SKILL.md packs/core/.apm/skills/work-loop/evals/evals.json packs/core/.apm/skills/intake-intent/evals/evals.json packs/core/.apm/skills/author-delivery-brief/evals/evals.json --exclude='AGENTS*.md'`
  and require no NEW match in the shipped pack prose files this slice adds or
  edits. The path list must cover every `packs/` file this slice touches,
  including the three eval registers T4 edits — those registers ship as live
  adapter projections, so a citation written into an eval case would otherwise
  pass every T4 check and reach adopters unseen. `work-loop/evals/evals.json`
  already carries permitted illustrative adopter examples (`docs/specs/my-feature`,
  `AC3`); those are the pre-existing baseline for that one file and are not
  violations. Preserve permitted illustrative teaching examples rather than
  stripping them mechanically.
- Run `python3 tools/build-site.py --journeys-only` after writing the bullet
  highlight.
- Run `python3 -m pytest tools/test_build_site_routing.py -k now -q`.
- Run `git diff --check`.

**Approach:**

- Bump both version carriers together. Add a free-standing core 2.25.25 release
  section above 2.25.24 without changing any released section. Write its
  highlight as a `-` bullet, then regenerate the public `/now/` projection.
- Update only the four scoped roadmap dispositions and correct R4's occurrence
  statement. Record all content-pin mutation outcomes in the verification
  ledger, then commit the complete non-generated source change.

**Done when:** Every command and inspection in this task's `Tests` passes; the
scoped portability command returns exactly its recorded pre-change baseline and
nothing more — measured 2026-09-13 as 14 matching lines in
`work-loop/evals/evals.json`, all permitted illustrative adopter examples, and
0 in each of the other six paths, with `references/mutation-proof.md` created at
0 by T3; the `/now/` projection test passes; the source commit is clean; and no
released changelog section changed. A bare no-match result is not the condition
here, because that one register's permitted examples are pre-existing.

### T6: Self-host projections match the committed pack source

**Depends on:** T5

**Touches:** `.agents/**`, `.claude/**`, `.codex/**`, `.agentbundle/**`,
`.claude-plugin/marketplace.json`

**Verification mode:** goal-based check

**Tests:**

- From the clean T5 source commit, run `FORCE=1 make build-self`.
- Run `pytest tests/roster/test_agent_skill_engineering_consumer_integrations.py::test_ac11_work_loop_projections_are_byte_identical_to_the_source`.
- Run `pytest tests/roster/test_cognitive_load_repository_contract.py::test_self_host_skill_projections_match_their_canonical_sources`.
- Run `git diff --check` before the projection commit.

**Approach:**

- Keep the source commit untouched. Generate projections only after the tree is
  clean, review the generated set reported by Git, and commit those projections
  separately.

**Done when:** `FORCE=1 make build-self` and every command in this task's
`Tests` pass, and the projection-only commit is clean and separate from the
source commit.

### T7: The complete bounded change passes local gates

**Depends on:** T6

**Touches:** none

**Verification mode:** goal-based check

**Tests:**

- Run `pytest packs/core/tests/skills/work-loop/test_finding_response_fields.py`.
- Run `pytest packs/core/tests/skills/intake-intent/test_intent_shaping_review.py`.
- Run `pytest packs/core/tests/skills/author-delivery-brief/test_delivery_brief_shaping_review.py`.
- Run `pytest tests/roster/test_agent_skill_engineering_consumer_integrations.py::test_ac11_work_loop_projections_are_byte_identical_to_the_source`.
- Run `pytest tests/roster/test_cognitive_load_repository_contract.py::test_self_host_skill_projections_match_their_canonical_sources`.
- Run `agentbundle catalogue lint --root . --deep`.
- Run `make lint-ruff lint-mypy`.
- Run `sed -n '11,$p' packs/core/.apm/skills/work-loop/SKILL.md | wc -l` and
  require a count no greater than 890.

**Approach:**

- Run only the repository local gate and the suites touched by this slice. Keep
  heavier corpus and roster-wide runs for CI.

**Done when:** Every command in this task's `Tests` passes and the final
work-loop body count remains within the allocated ceiling.

## Rollout

This is a patch release of portable guidance. It uses the normal core-pack
source commit followed by a separate self-host projection commit. Rollback is a
normal revert of both commits; there is no infrastructure, migration, secret,
or external-system sequence.

## Risks

- A literal phrase pin can stay green after the same claim moves to plain text.
  Region-wide extraction, named exceptions, and old-guard-survives mutation
  checks are therefore required for each new pin.
- DECIDE is already above CAT-S003's warning threshold. The per-row allocation
  and post-edit count stop this slice from consuming unbounded headroom.
- A dirty source tree makes `make build-self` refuse to run. The two-commit
  sequence is part of the construction strategy, not optional cleanup.
- The roadmap's R4 evidence correction must not weaken its valid core claim that
  no mutation-proof obligation currently exists.

## Changelog

- 2026-09-13: Initial plan for the four decided roadmap rows; only R3 receives
  acceptance criteria, while R1, R2, and R4 ship behind content pins under the
  authoring-protocol intent's criterion-promotion gate.
