## Shaping review — spec mode

**Targets**
- `docs/specs/visual-target-confirmation/spec.md` (Status: Draft)
- `docs/specs/visual-target-confirmation/plan.md` (Status: Drafting, changelog 2026-09-29)

**Result: Findings** (12)

### High

**F1. An unconfirmed target still reaches composition authority through `converge`, so request 4 is not met.**
The contract fixes only the consuming side. On the producing side, `converge.md:80` still says "When an approved visual target exists, write the selected direction's compositional commitments into the doc here", and the template's `## Compositional commitments` comment (line 215) gates the same section on "the selected direction, when an approved visual target exists". Both key on *existence* plus *selection* — the exact conflation ADR-0131 exists to remove. An `unconfirmed` target therefore still gets its compositional commitments written into the direction doc, where `direction-and-taxonomy` reads them (its `Binds` cell covers "axis commitments … and every value the taxonomy resolved"). The unconfirmed target then binds composition from the second rung, and AC-0017's regression only watches the top rung, so nothing reds.
**Fix:** add two criteria — `converge.md` writes compositional commitments only where `visual_target: confirmed`, and the template's `## Compositional commitments` comment states the same gate — and add them to T4 and T3 respectively.

**F2. AC-0017 names an observation no mechanism can make.**
"A regression test fails when a direction artifact … **is resolved to** the `approved-visual-target` rung" presumes a resolver. There is none: `approved-visual-target` appears in only four Python files in the tree, all of which assert over shipped Markdown, and the rung resolution itself is model behaviour. Plan T6 restates the same shape ("must not resolve to the top rung") and marks it `stub: true`, so the stub cannot compile against anything. The Testing Strategy's claim that it "reds if the rule is stated but not enforced" is not achievable — there is no enforcement surface to red against.
**Fix:** either restate AC-0017 as the byte-level property that actually exists (for example: no shipped surface states a condition under which `status: selected` alone satisfies the top rung's `requires` cell, swept over `WHOLE_EXPORT_TREE`), or move it to the eval set beside AC-0019 and drop the TDD claim.

**F3. Deferring the changelog entries to a follow-on conflicts with two governing rules.**
`docs/product/changelog.md`'s own header: "an entry is owed in the same change that bumps a released artifact's version — you know the version at write time, because you are setting it", and "**Reviewed like code.** Write them in the same PR as the implementation". `packs/AGENTS.local.md` § Marketplace and release pipeline makes the entry step 3 of the same four-step sequence that begins with the bump. The spec's Follow-ons claims the entries "belong to the publish pipeline rather than to this content change"; what `AGENTS.local.md` assigns to the pipeline is the `Highlights` **disposition** (step 4), not the entry, and that step also says "do not leave it to a human to remember". This is a required-documentation control being dropped by a non-goal, not a scoping choice.
**Fix:** delete the Follow-on, add a criterion for a free-standing `##` release entry per pack with its `Highlights` disposition recorded (including an explicit "none" verdict and reason), and hang it on T10.

**F4. The version bump leaves `.claude-plugin/marketplace.json` stale, and no gate catches it.**
`packs/AGENTS.local.md` step 2 requires `FORCE=1 make build-self` to regenerate `marketplace.json` after the bump; `packs/AGENTS.md` § Self-hosting projection requires self-host after all pack edits. `marketplace.json` carries `"version": "0.4.0"` for `frontend-engineering`. Nothing in the spec or plan regenerates it: Durable Outputs' "Release history" row names only `pack.toml` and `plugin.json`, and T10's Touches lists the same four files. Version parity against `marketplace.json` is tested only for the `atlassian` pack (`tests/roster/test_atlassian_marketplace_version_parity.py`), so for these two packs the drift ships green.
**Fix:** add `FORCE=1 make build-self` to T10 as the regeneration mechanism, list `.claude-plugin/marketplace.json` in the Release-history durable output, and extend AC-0022/AC-0023 to require the marketplace entry to carry the same version.

### Medium-high

**F5. AC-0022 and AC-0023 cannot fail, and the instrument they name does not exist.**
The check that exists is `tests/conformance/test_pack_metadata.py::test_pack_and_plugin_versions_match`, which asserts only `plugin["version"] == pack["version"]`. It holds on the unchanged tree, so it can never observe that a bump *happened* — only that the two files agree. Separately, the spec ("Pack release-surface tests pass", Testing Strategy "The existing pack release-surface tests are the one-liner") and plan T10 name a surface that is absent: there is no `packs/experience-design/tests/pack/` or `packs/frontend-engineering/tests/pack/` directory; the only `test_release_surface.py` in the tree belongs to `packs/atlassian`. T10's Done-when runs `make lint-ruff lint-mypy` and "both packs' suites", neither of which runs `tests/conformance/`.
**Fix:** name the real instrument (`tests/conformance/test_pack_metadata.py`) in both documents, put it in T10's Done-when, and give the bump a falsifying observation — assert the version is strictly greater than the one on `main`, or pin the expected new version in the criterion.

**F6. AC-0012 and AC-0013 both add to a `SKILL.md` that is four lines from a frozen ceiling, and the raise is an ask-first matter owned by another spec.**
`packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` is 968 lines with a 4-line frontmatter, so the lint-equivalent body is 964 against `BODY_BUDGET = 968` in `test_visual_authority_entrypoint.py`. That constant encodes AC-0013 of the **Shipped** `design-to-build-value-handoff` spec, whose Agent Rules § Ask first reads: "Raising the `SKILL.md` body-line budget above 968, the ceiling AC-0013 of this spec sets." The test's own message names the only two admissible responses — pay with a removal, or amend that spec. The contract under review touches this file twice (the rung bullet at 151-154 and the manifest row at 880) and records neither the ceiling nor the ask-first obligation anywhere.
**Fix:** add the 968-line ceiling to the plan's Constraints and an Ask-first entry to the spec mirroring the Shipped spec's, and state in T5 that AC-0012 and AC-0013 land as in-place edits to the existing bullet and manifest cell, not as added lines.

### Medium

**F7. The field name is hard-coded in two packs with no drift coverage, and a shipped guard already names this hazard.**
AC-0001 fixes `visual_target` in the experience-design template (verified by `packs/experience-design/tests/skills/creative-direction/test_contract.py`); AC-0006, AC-0007 and AC-0012 fix the same literal in frontend-engineering (verified by that pack's suite); AC-0011 fixes it again in `design-system`. Three suites in two packs each assert a string none of them derives from the others, and the pack-test boundary forbids one reading the other's tree — so renaming the key on one side leaves both suites green and the rung keyed on a field that no longer exists. `test_visual_authority_precedence.py` line 45 states the rule this breaks: "A rung keyed on another pack's template vocabulary goes wrong at that template's next edit, and no declared-dependency check can see it." Its literal check (`UPSTREAM_ENUM = ("proposed", "selected")`) stays green only because `confirmed` is not in that tuple. ADR-0131 settled *that* the rung keys on the field; it did not decide who owns the name or what detects the drift.
**Fix:** add a criterion placing the cross-pack check where it is allowed — a `tests/roster/` assertion that the template's declared `visual_target` values and the two rung tables' cells agree — and state in the spec whether `UPSTREAM_ENUM` / `CONDITION_COLUMNS` is amended to admit the new condition vocabulary or deliberately left alone.

**F8. AC-0014 is a judgment gate, not a mechanizable criterion.**
"`frame` operation scopes its interrogation instruction so it does not apply on the `inherit` route" states an effect, not an observable. `SKILL.md:108` currently reads "Run the interrogation:" with no qualifier; the criterion does not say what the scoped text must contain, so T8's contract test has to invent its own predicate, and any predicate it invents satisfies the AC by construction. Contrast AC-0007, which fixes row keys in order. Note the adjacent line 106 already shows the shape the repair should take ("on `inherit`, which reaches no writer, hold it in the session").
**Fix:** state the observable — for example, the sentence containing "Run the interrogation" also names `inherit` and excludes it — so the test reds if the qualifier is removed or moved to another sentence.

**F9. The Testing Strategy misattributes the verifying instrument for three criteria.**
The second bullet groups AC-0006 through AC-0013 and claims they "parse through the shipped `observation_table` and `rule` helpers". Those helpers live in `frontend_engineering_visual_authority_rules.py` with `OBSERVATION` hard-coded to `visual-observation.md`. AC-0011 (design-system's table, a different pack), AC-0012 (`SKILL.md`) and AC-0013 (the evidence manifest) cannot use them, and the pack-test boundary forbids importing across packs. The plan's T5 is correct; the spec's strategy is not.
**Fix:** split the bullet so AC-0006 to AC-0010 name the helpers, and AC-0011 to AC-0013 name their real homes (`test_design_system_contract.py`, and the frontend `SKILL.md` / evidence assertions).

**F10. Request 8's no-duplication rule is unaddressed for the body's existing `none` state.**
The template's `## Approved visual target` comment says 'If no target exists, write "none" and continue', and `**Binding:**` offers `composition, proportion, spatial relationship, or "none"`. After this change the same disposition is recorded in frontmatter as `visual_target: none`. That is state in two places with no statement of which is canonical and no drift coverage — the condition request 8 permits only with both. AC-0003 distinguishes `status` from `visual_target` but says nothing about the body lines.
**Fix:** add a criterion that the section comment marks the body lines as provenance for a human reader and names the frontmatter key as the canonical state, matching the treatment the plan's Design section already gives `**Confirmation record:**`.

### Low

**F11. Scenario (a) has no model-behaviour case, while scenario (c) has two.**
The write side of "target present, confirmation absent" is covered only by AC-0004, an instruction-text assertion. The read side has AC-0019. Nothing records a `converge` gesture that writes `unconfirmed`, whereas the `none` disposition gets both AC-0004's sibling and the AC-0018 eval. The write side is where the conflation originates.
**Fix:** add a fifth `creative-direction` eval case whose expected output records `visual_target: unconfirmed` for a selected direction with a named, unapproved target, and add it to T9.

**F12. The plan narrates its own authoring path.**
T2's Approach ("This task landed during PLAN rather than EXECUTE, because the spec's `Constrained by:` header cites ADR-0131 and a spec shipped to review with a dangling citation is a defect the review would rightly find"), T1's "The pre-plan probe already established the set", and T5's "the anchor test the step-8a sweep predicted" describe the drafting process rather than the work. `docs/AGENTS.md` § Authoring: "Describe current state. Cut dead ends, old trade-offs, weak claims, notes about the draft."
**Fix:** keep `*(Met during PLAN.)*` on T2's Done-when, which a reader acts on, and delete the three explanations of how the draft came to be.

**Grounding gaps.** I read only; no suite was executed, so every claim about what reds is derived from the shipped assertion text. The 4-line headroom in F6 is arithmetic over the file (968 lines, frontmatter closing at line 4), not the lint's own derivation run. I confirmed no self-host projection of these two skills exists under `.claude/`, so F4's regeneration concern is scoped to `marketplace.json`; I did not enumerate every other artifact `make build-self` writes.
