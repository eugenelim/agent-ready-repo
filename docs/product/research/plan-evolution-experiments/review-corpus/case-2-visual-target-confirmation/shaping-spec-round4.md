## Result: Findings (spec mode, round 4)

**Targets** (all under `~/orca/workspaces/agent-ready-repo/visual-target-confirmation/`)
- `docs/specs/visual-target-confirmation/spec.md` — sha256 `82e2c2cf…7e1e30` (as supplied)
- `docs/specs/visual-target-confirmation/plan.md` — sha256 `4bffb807…137c6e`
- `docs/adr/0131-visual-target-confirmation-is-an-explicit-state.md` — sha256 `23749bdc…5adb460`

**Review context.** Cold read of the three targets plus the real trees they name. Findings 2–4 and 6 below are the direct answers to the four questions asked. Round-3 findings 1, 4, 5, 6 and 7 are sustained as repaired (with the residue in F4 and F8). The criterion-ID ordering in § Acceptance Criteria puts AC-0034 before AC-0033; cosmetic, noted here rather than as a finding.

**Consulted surfaces** (read, not merely cited): `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` §§ 1 (lines 145–169), `references/visual-observation.md` (lines 22, 95–103), `.apm/agents/frontend-reviewer.md` (232–251), `.apm/skills/frontend-engineering/evals/evals.json` (cases at 66–95), `packs/frontend-engineering/JOURNEY.md` (178–190); `packs/experience-design/.apm/skills/creative-direction/SKILL.md` (80–109), `references/visualize.md` (10–31), `references/converge.md` (grep), `assets/creative-direction-template.md` (grep), `.apm/skills/design-system/SKILL.md` (93, 142, 208), `.apm/skills/design-system/references/value-derivation.md` (60–99), `assets/token-taxonomy-template.md` (25–42); `guides/frontend-engineering/how-to/read-the-design-handoff.md` (55–104), `guides/frontend-engineering/reference/frontend-engineering.md`, `guides/frontend-engineering/tutorials/scaffold-a-component.md` (57), `guides/experience-design/how-to/establish-design-intent.md` (33, 209, 406); `tests/roster/test_frontend_visual_authority_adopter_prose.py` (whole); `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py` (26, 75–78); `docs/specs/frontend-visual-authority/spec.md` (1–188).

**Grounding gaps.** I did not read `AGENTS.md`, `docs/AGENTS.md`, `packs/AGENTS.md`, `packs/AGENTS.local.md`, the changelog header, or `docs/specs/design-to-build-value-handoff/spec.md` this round; no finding below rests on them, and the body-budget (968) and version-bump claims are taken from the plan's own citations unverified. I ran no tests and read no round-3 report — the delta summary is taken as attributed data.

---

### F1 (High). AC-0031 obliges the literal `visual_target: confirmed` on two members whose job is the opposite reading

AC-0031 quantifies unconditionally ("**Each** surface in the confirmation-reading set states the top rung's precondition as the literal `visual_target: confirmed`") over a set that includes the `visual-authority-direction-only` eval case and the evidence-manifest row in `frontend-engineering`'s `SKILL.md`. Both are obliged elsewhere to carry a different value:

- AC-0019 requires `visual-authority-direction-only` to state its precondition as `visual_target: unconfirmed`, resolving to `direction-and-taxonomy`.
- AC-0013 requires the evidence-manifest entry to record *the artifact's* `visual_target` reading — any of three values, whichever was found.

AC-0032 uses the guarded form ("Each surface in that set **that states rung 2's condition**"); AC-0031 has no such guard. As written the pair is contradictory for those two members, and the plan compounds it: T9 says both shipped eval cases are set members and that AC-0031 therefore reaches `evals.json`.

**Fix:** guard AC-0031 the way AC-0032 is guarded — "Each surface in that set that states the top rung's precondition states it as the literal `visual_target: confirmed`" — and name the direction-only case and the evidence-manifest row explicitly as members governed by AC-0032/AC-0013 rather than AC-0031.

### F2 (High). AC-0033 relocates the unenumerable obligation rather than closing it, and misstates where the set lives

AC-0033 bans "any member of the retired-reading set, which **the plan enumerates** from a recorded sweep of both trees". The plan does not enumerate it. T5's Approach says to derive it at execute time ("sweep both trees for statements of the rung condition in terms of what the artifact records, and record the resulting set and the command in the verification ledger"). Three consequences:

1. The criterion's text is false against the plan as it stands — nothing in `plan.md` contains a retired-reading set.
2. The sweep predicate ("statements of the rung condition in terms of what the artifact records") is a judgment gate, not a mechanizable one; it is the same English-paraphrase problem round 3 identified, moved from the contract into a task.
3. The set is chosen by the same agent that writes the replacement prose, after it reads the tree it is about to edit. Defining the set as exactly the phrases removed makes AC-0033 pass by construction — it is self-grading and cannot fail. The recorded ledger entry makes the choice auditable, not falsifiable.

**Fix:** replace the absence-of-phrases shape with a positive exclusive property, which is closed over paraphrase. Example that is mechanizable over the enumerated loci: within each locus, every sentence containing a whole-word match of `confirm` (any inflection) or `approved` must also contain the literal `visual_target`. That reds on any surviving prose statement of the condition, including one nobody anticipated, and it does not depend on an author-chosen ban list. Keep the ledger sweep as evidence of coverage, not as the criterion's oracle.

### F3 (High). The enumerated set is stated at rung-1 locus granularity, so AC-0032 and AC-0033 cannot reach the two rung-2 carriers the plan says they reach

AC-0031 enumerates *loci*, not files: "the **rung-1 bullet** and the evidence-manifest row in `SKILL.md`", "the **rung-1 clause** of `read-the-design-handoff.md`". AC-0032 and AC-0033 then quantify over "that set". On the locus reading, the two texts that actually carry the superseded rung-2 reading sit outside it:

- `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:157-158` — "A direction recording no confirmation resolves here, and the run records that it was unconfirmed."
- `guides/frontend-engineering/how-to/read-the-design-handoff.md:74-75` — "**You are here if** you have a direction but nothing in it records a human confirming the composition."

Yet plan T5 claims the set assertion "Verifies … AC-0032 for the rung-2 bullet" and T7 claims the guide's rung-2 clause is covered, quoting that exact sentence. So either "surface" means the whole file (contradicting the rung-1/evidence-manifest sub-file phrasing, and leaving the intended scope of the sweep undefined) or the plan asserts coverage the contract does not grant. Answering the completeness question directly: the *membership list* is closed, but its *granularity* is not, and that ambiguity is what decides whether the two principal carriers are swept.

**Fix:** enumerate at file granularity and list the loci per file, e.g. "`SKILL.md` § *1. Resolve visual authority* — the rung-1 and rung-2 bullets and the evidence-manifest row" and "`read-the-design-handoff.md` § *How visual authority resolves* — the rung-1 and rung-2 items". Then AC-0031, AC-0032 and AC-0033 all range over the same, unambiguous text spans.

### F4 (High). A second producing surface still records a binding claim for an unconfirmed target — the round-3 finding-7 repair was scoped to one of two files

AC-0034 scopes `references/visualize.md:21-24` ("When a target exists, record its identity and three boundaries: what is binding, what is illustrative, and what may adapt responsively"). The identical instruction is the skill's own output contract, one file up and unscoped:

`packs/experience-design/.apm/skills/creative-direction/SKILL.md:92-93` — "**Approved visual target** — optional. When present, identify the target, what is binding, what is illustrative, and what may adapt responsively."

Nothing in the criterion set scopes that line, and `creative-direction/SKILL.md` appears in T8's Touches for the `inherit` sentence only. A producer following the output contract still writes a `**Binding:**` claim for an unconfirmed target, which is exactly what this spec's Outcome forbids ("An unconfirmed target's compositional commitments are not written into the direction artifact"). Because the output contract is the always-loaded surface and `visualize.md` is a reference, this is the more load-bearing of the two.

**Fix:** extend AC-0034 to both files — "`references/visualize.md`'s and `creative-direction/SKILL.md`'s instruction to record a target's binding boundaries is scoped to the confirmed reading" — and add `creative-direction/SKILL.md` to T4's Touches.

### F5 (Medium). AC-0017's second comparison passes vacuously when the key disappears, so ADR-0131's stated drift control is weaker than the ADR claims

AC-0017's second half: "every value captured by a whitespace-normalized match of `visual_target:` followed by a value, anywhere in [four files], is a member of that declared set". If a consuming surface renames or drops the key, the match set for that file is empty and a universal over the empty set holds. The assertion cannot distinguish "this surface names the field correctly" from "this surface no longer names the field at all".

This matters beyond the criterion: ADR-0131 § Decision rests its reversal of the frozen Always-do rule on precisely this control — "a cross-tree assertion compares the values the template declares against the values the consuming surfaces name, so a rename on either side fails rather than passing silently." A rename on the consuming side does *not* fail this assertion. (AC-0006, AC-0011 and AC-0012 catch a rename on three of the four surfaces by pinning the literal, so the exposure is partial, not total — converge.md is covered by AC-0004/AC-0025 literals, visualize.md by nothing literal.)

**Fix:** add a non-emptiness half — "each of the four named surfaces yields at least one match" — before the membership half, and adjust the ADR sentence to describe the control that ships.

### F6 (Medium). ADR-0131's § Confirmation still describes the round-2 mechanism the round-3 repair deleted

§ Confirmation says: "A closed retired-phrase sweep over that pack's export tree and over its public guide asserts the superseded prose reading is gone." That mechanism is exactly what round 3 removed; the spec now runs four criteria over a closed *surface* set, with no closed phrase set and no export-tree-wide sweep. The same paragraph says the roster assertion compares template values "against those named on both consuming surfaces", while AC-0017 now names four files. The ADR is the Accepted decision record this spec cites as `Constrained by`, so its confirmation paragraph is currently a description of a design that was withdrawn.

On the substance of the reversal itself — sound. The ground stated (a precondition no consumer can check, satisfied by reading prose) is real and independently recorded by the owning spec: `docs/specs/frontend-visual-authority/spec.md` § Follow-ons line 179 already names this gap and assigns it to frontend-engineering. Citing that follow-on would strengthen the ADR's case and is stronger evidence than the current appeal to `type:`.

**Fix:** rewrite § Confirmation to describe the four surface-set criteria, the four-file value comparison, and whatever AC-0033 becomes under F2; cite § Follow-ons line 179 of the frozen spec in § Decision.

### F7 (Medium). Carriers of the confirmed-state reading sit outside the enumerated set, and the Always-do rule's scope is broader than anything that checks it

§ Agent Rules Always-do says "Use the exact field name `visual_target` … on **every surface that names the state**." Nothing enumerates that population, and at least one consuming surface naming the state is outside AC-0031's set and outside every other criterion:

- `packs/experience-design/.apm/skills/design-system/references/value-derivation.md:76` — "An approved visual target **is a confirmed composition**. It binds arrangement, proportion and spatial relationships." The file goes on to say this is "the third place the same rule is written" (lines 79-81), so the pack already knows this text duplicates the rung rule. AC-0011 covers only the `## Design authority` table's source cell in `design-system/SKILL.md`, not this reference.
- Lesser, but in the same class: `design-system/SKILL.md:208` routes on "a visual target is present" with no confirmation gate; `guides/frontend-engineering/tutorials/scaffold-a-component.md:57` states the chain as "no confirmed visual target".

**Fix:** add `design-system/references/value-derivation.md` § *What a visual target gives you, and what it does not* to the enumerated set (and to T5's or T6's Touches, respecting the pack-test boundary — this is an experience-design file, so its assertion belongs in that pack's suite), or narrow the Always-do rule's scope to the enumerated set so the rule and the criteria describe the same population.

### F8 (Medium). Second home for the binding claim with no canonical link and no drift coverage

`packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md:35-36` — "**Visual target:** \<what it is and what it was read for, or "none". It binds composition and relationships; it supplies no value\>" — and its mirror in `guides/experience-design/how-to/establish-design-intent.md:406`. The token-taxonomy artifact records both the target's existence and its binding, with the literal `none` overlapping one of the closed set's values, and with no confirmation gate and no pointer to `visual_target` as canonical. AC-0017's regex does not reach it (the line spells `Visual target:`, not `visual_target:`). The accepted request forbids "duplicated state lacking a canonical home and drift coverage"; this is that shape, and this slice leaves it as it found it while creating the canonical home the line should defer to.

**Fix:** either add a criterion that the taxonomy template's `**Visual target:**` line names the direction artifact's `visual_target` field as the canonical state and scopes its binding clause to the confirmed reading, or record it as an owner-settled out-of-scope follow-on naming the owner (experience-design) — an explicit decision, not silence.

### F9 (Medium). AC-0027 is only one-third mechanizable, and the frozen spec's working material is left contradicting shipped behaviour

AC-0027 requires the Status field to "name all three superseded parts". Only one part carries a literal a test can look for (`recorded-human-confirmation`); "ADR-0130's body budget" and "the Always-do rule that a rung condition is a property the pack defines…" have no pinned literal, so the implementer picks the wording and the assertion at the same time — the milder form of F2. The banned literal (`everything else stands`) is pinned and does make the criterion able to fail, so this is a partial, not total, defect. Verified against the current Status line (`docs/specs/frontend-visual-authority/spec.md:3`): it reads "superseded in part by ADR-0130 — 960-line body budget; everything else stands", so the ban has a real target today.

On coherence of the frozen spec after the annotation: the contract tier stays consistent — AC-0003a is the only contract criterion the change falsifies, and the Status annotation plus T5's update of `test_visual_authority_precedence.py:77-78` covers it; AC-0028a's two byte-pinned sentences are respected by T5's Approach. Two working-material entries are left contradicting the shipped result, and because that spec's preamble tiers `Assumptions` and `Follow-ons` as working material, this is **advisory** and cannot block:

- § Assumptions line 186 — "`recorded-human-confirmation` is a property this pack defines, and no control verifies it … a writer that records confirmation some other way than the one the reference illustrates still satisfies rung 1." False after this slice.
- § Follow-ons line 179 — the gap this slice closes, left open.

**Fix (contract part):** name the three parts as literals AC-0027 can match, e.g. require the Status field to contain `ADR-0130`, `960-line body budget`, `ADR-0131`, `recorded-human-confirmation`, and `rung conditions as properties this pack defines`. **Fix (advisory part):** correct the two working-material entries in the same PR.

### F10 (Low). The eval counts no longer add up after the AC-0019 repair

With AC-0019 turned from an added case into a restatement of the shipped `visual-authority-direction-only` case, four cases are added (AC-0018, AC-0020, AC-0021, AC-0029) and two are restated (AC-0019, AC-0028). Two places still say otherwise:

- plan T9: "Five added cases and one restated" — then its own list restates two.
- spec § What Changes: "The shipped eval case that states the top rung's precondition in prose is restated against the field, and five cases are added" — singular "case" for two restatements, and five for four. (§ What Changes is working material in this spec's own tier declaration, so that half is advisory; T9 is not.)

**Fix:** T9 → "Four added cases and two restated"; § What Changes → "The two shipped eval cases … are restated against the field, and four cases are added."

---

**Summary judgement on the four questions asked.**
1. *Is AC-0031's set complete?* The list is closed but its granularity is not (F3), and at least one consuming carrier of the confirmed reading sits outside it (F7), alongside a second producing carrier (F4). Not yet complete.
2. *Is the recorded-sweep mechanism legitimate?* No — as written it is self-grading and unmechanizable, and AC-0033 misdescribes the plan (F2). A positive exclusive property closes the same hole without an enumeration.
3. *Is the ADR's reversal sound, and does AC-0027 leave the frozen spec coherent?* The reversal's reasoning is sound and is corroborated by the frozen spec's own Follow-on; its stated compensating control overstates what AC-0017 can catch (F5) and its § Confirmation is stale (F6). The frozen spec's contract tier is left coherent; two working-material entries are not (F9, advisory).
4. *Did a repair introduce a new problem?* Yes — F1 (new contradiction between AC-0031 and AC-0019/AC-0013), F3 (new granularity ambiguity), F6 (ADR left describing the withdrawn mechanism) and F10 (count drift) all arise from the round-3 repairs.
