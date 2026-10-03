## Review result

**Result:** `Findings` (9)

**Targets:** `~/orca/workspaces/agent-ready-repo/visual-target-confirmation/docs/specs/visual-target-confirmation/spec.md`, `.../plan.md`, `~/orca/workspaces/agent-ready-repo/visual-target-confirmation/docs/adr/0131-visual-target-confirmation-is-an-explicit-state.md` — working tree, no revision marker; spec `Draft`, plan `Drafting`, ADR `Accepted`.

**Review context:** Round 2, spec mode, cold. Judged the twelve round-1 repairs against the artifact text and the shipped tree they name. Eight of the twelve repairs hold as written: the producing-side gate (AC-0024/AC-0025 over `converge.md` and the template), the changelog criterion (AC-0030 matches the header's free-standing-entry and Highlights-disposition rules verbatim), the `origin/main` version comparison, the `marketplace.json` regeneration route, the 964/968 ceiling (verified: `SKILL.md` is 968 total lines with a 4-line frontmatter, `BODY_BUDGET = 968` in `test_visual_authority_entrypoint.py`, ceiling owned by `design-to-build-value-handoff` AC-0013), the corrected Testing Strategy instrument attribution (`OBSERVATION` opens only `references/visual-observation.md`; `tests/roster/` is the only tree `lint-pack-test-boundary.py` check 8 permits to read both packs), the corpus claim in Risks (four files under `docs/design/direction/`, `token-verification.md` carries `type: design-system`), and the removal of plan self-narration.

**Consulted surfaces:** both packs' `.apm/` skills, templates, references and evals; `packs/{frontend-engineering,experience-design}/tests/`; `tests/roster/`; `tests/conformance/test_pack_metadata.py`; `tools/lint-pack-test-boundary.py`; `guides/frontend-engineering/how-to/read-the-design-handoff.md`; `.claude-plugin/marketplace.json`; `docs/product/changelog.md`; `docs/specs/{frontend-visual-authority,design-to-build-value-handoff}/`; AGENTS.md at root, `docs/`, `packs/`.

**Grounding gaps:** none consequential. I did not execute any suite, so every red/green claim below is derived from the assertion text, not from a run.

---

### 1. AC-0023 contradicts a shipped assertion; T10's Done-when cannot hold (high)

`packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py:89` hard-pins the pack version:

```python
    assert version == "0.4.0", (
        f"pack.toml carries {version!r}, not the 0.4.0 T7 release ships at. A "
        f"later delivery moves this pin with its own bump; ..."
```

`packs/frontend-engineering/pack.toml` carries `0.4.0` today. AC-0023 requires a version strictly greater than `origin/main`, so satisfying it reds this test. T10's Done-when requires "both packs' suites are green," and T10's `Touches` omits the file. The test's own docstring says a later delivery moves the pin — but nothing in this contract says this delivery does, and the file is the `frontend-visual-authority` release surface, which the plan otherwise treats as another spec's property (its Constraints reserve `test_visual_authority_slice_two.py` on exactly that ground). `experience-design` has no equivalent pin, so AC-0022 is unaffected.

**Fix:** add `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py` to T10's `Touches` and state in T10's Approach that the pin moves to this delivery's version; keep the assertion shape (equality to the value this release ships), since the criterion, not the pin, owns the bump direction.

### 2. Nothing in the criterion set removes the superseded infer-from-prose reading (high)

ADR-0131's whole ground is that "read the prose and judge that it sounded approved" is not a recorded confirmation. Every new criterion except AC-0006 is an additive presence check — AC-0011 "names", AC-0012 "names", AC-0013 "records", AC-0015 "states". A tree that carries both the new field rule and the old inference rule passes all of them green. Two live instances:

- `guides/frontend-engineering/how-to/read-the-design-handoff.md:64-67`: "**You are here if** the artifact says somewhere that the composition was approved or signed off, rather than merely proposed or picked." AC-0015 is satisfied by appending a paragraph beside it.
- `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:151-158`: the rung bullet reads "when it records a human-confirmed composition," and rung 2 reads "A direction recording no confirmation resolves here." AC-0012 is satisfied by adding the literal without touching either.

Both packs already ship the idiomatic instrument: `SUPERSEDED` in `test_visual_authority_slice_two.py` and `OBSOLETE_TERMS` in `test_design_system_contract.py` sweep for surviving superseded wording.

**Fix:** add one absence criterion per affected tree — no file under `packs/frontend-engineering/.apm/skills/frontend-engineering/` or under `guides/frontend-engineering/` states the rung's precondition as prose about an approved or signed-off composition — sweeping whitespace-normalized, as the shipped sweeps do.

### 3. ADR-0131 claims a regression test no criterion or task produces (high)

`docs/adr/0131-...md:136-137`, § Confirmation: "A regression test asserts that an artifact carrying `status: selected` and a named target, with no confirmation, does not resolve to the top rung." Round 1 found that test unimplementable and the repair replaced it with the AC-0017 cross-pack drift assertion. AC-0017 asserts field-name agreement across three files; it does not assert a resolution outcome for a `status: selected` artifact. The nearest coverage is AC-0019, an eval case — a recorded model gesture, which the plan's own Risks call the weakest verification in the set. The Accepted ADR is governing authority for this spec and currently promises verification the contract does not deliver.

**Fix:** amend the ADR's § Confirmation to describe what is actually asserted — the absent-field and `unconfirmed` rows in the rule table, the eval cases, and the drift assertion — and drop the resolution-regression sentence.

### 4. `visualize` is a second producing surface, and it is ungated (high)

The round-1 producing-side repair covered `converge.md` and the template. `visualize` is the operation that *forms* compositional commitments, and its shipped text carries the same existence-plus-approval framing the repair removed elsewhere:

- `packs/experience-design/.apm/skills/creative-direction/references/visualize.md:19`: "An approved visual target's compositional commitments are written into `<output_dir>/direction/<slug>.md` itself..."
- `visualize.md:13`: defines the approved visual target as "a composition the human has confirmed" — prose, not the field.
- `packs/experience-design/.apm/skills/creative-direction/SKILL.md:118`: "May change: compositional commitments recorded in the direction doc."

No criterion and no content pin touches any of them. The spec's Outcome asserts "An unconfirmed target's compositional commitments are not written into the direction artifact," and the accepted request's item 6 obliges `creative-direction` to use the same field and semantics throughout; `visualize.md` is a `creative-direction` surface stating the rule in the superseded vocabulary.

**Fix:** add a criterion (or, if the write really only happens in `converge`, a T4 content pin) that `visualize.md`'s value-boundary section states the commitments reach the doc only where `visual_target` reads `confirmed`, and states the write boundary against the field rather than against "an approved visual target".

### 5. AC-0027 leaves the annotated Status line self-contradictory (medium)

`docs/specs/frontend-visual-authority/spec.md:3` currently reads:

```
- **Status:** Shipped (superseded in part by ADR-0130 — 960-line body budget; everything else stands)
```

AC-0027 requires an added annotation naming ADR-0131 and `recorded-human-confirmation`. What ADR-0131 supersedes is AC-0003a (`spec.md:133`, `[x]`, "The `approved-visual-target` row's `requires` cell is `recorded-human-confirmation`"). A literal satisfaction of AC-0027 produces a Status line that both records the new supersession and still says "everything else stands."

**Fix:** reword AC-0027 to require the Status line to name both supersessions and to carry no residual claim that everything else stands, and name AC-0003a as the criterion superseded, not only its value.

### 6. AC-0017's agreement predicate is undefined, and its weakest implementation cannot fail (medium)

AC-0017 requires a red "when the `visual_target` values declared in `creative-direction-template.md` and the values named in `visual-observation.md` and `design-system`'s `SKILL.md` stop agreeing." The three surfaces name different numbers of values by design: the template enumerates three (AC-0001), the rule table's `states` row enumerates three (AC-0009), and the design-system source cell names one — `visual_target: confirmed` (AC-0011). So "agreeing" cannot mean set equality, and the criterion does not say what it does mean. The cheapest passing implementation asserts the field-name substring on all three, which does not red on a value rename — the drift this criterion exists to catch.

Secondary: `tests/roster/` runs only via the dispatch-only `test-roster.yml`, so AC-0015 and AC-0017 — the sole cross-pack drift control — are not reached by any PR gate.

**Fix:** state the predicate as two comparisons: the template's declared set equals the `states` row's set exactly, and every `visual_target` value named anywhere in `visual-observation.md` or `design-system`'s `SKILL.md` is a member of the template's declared set. Record a local roster run in T6/T7's evidence, since no PR workflow runs it.

### 7. AC-0026 is the sentence-exists shape the plan rejects, and it is the only control on the duplication boundary (medium)

The plan's § Design decisions cuts three obligations to living design because "the only check available for each is that a sentence exists, which the repository's spec template rules out as a criterion." AC-0026 — the `## Approved visual target` comment "names the frontmatter key as the canonical disposition and its body lines as provenance for a human reader" — is that same shape, and T3 implements it as exactly such an assertion. The policy is applied two ways in one document.

This matters beyond consistency, because AC-0026 is the single criterion carrying the accepted request's item 8 (no duplicated state unless one is canonical and the other a projection). The body still invites an independent authority claim: `creative-direction-template.md:78-80` carries `**Target:** <none, ...>` and `**Binding:** <composition, proportion, spatial relationship, or "none">`, which an author fills for a target whose field reads `unconfirmed`.

**Fix:** either restate AC-0026 against a checkable literal — the comment contains `visual_target` and states that the body's `**Target:**`, `**Binding:**` and `**Confirmation record:**` lines bind nothing on their own — or demote it to a T3 content pin and reinstate one of the three cut obligations on the same rule. Do not leave the two policies side by side.

### 8. AC-0028 edits a case pinned by two other specs' suites, and AC-0012 edits a byte-pinned sentence (low)

`visual-authority-approved-target` is pinned in `test_visual_authority_slice_two.py:136-139` (its `expected_output` must contain "resolved") and in `test_visual_authority_release.py:20-27` (id present, prompt/expected/assertions non-empty). Separately, `test_visual_authority_slice_two.py:142` pins the literal "It supplies no colour, type, spacing or motion values, so those always come from a lower rung." — which sits inside the rung bullet at `SKILL.md:153-154` that AC-0012 edits in place. The plan's Constraints name only the `test_visual_authority_slice_two.py` filename collision, and T5/T9's Approach name only the precedence exact-equality.

**Fix:** list both pins in T5 and T9's Approach as values the edit must preserve, alongside the precedence assertion already named.

### 9. "What Changes" undercounts the eval cases (low, advisory)

`spec.md:54-55` says "the shipped eval case ... is restated against the field, and four cases are added." The criteria add five (AC-0018, AC-0019, AC-0020, AC-0021, AC-0029), and T9 and the Testing Strategy both say five added plus one restated. Working material under the spec's own contract note, so this cannot block.

**Fix:** change "four" to "five".
