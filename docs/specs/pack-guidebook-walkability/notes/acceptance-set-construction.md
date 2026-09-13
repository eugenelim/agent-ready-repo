# Acceptance-set construction record

Built while authoring. It records every candidate obligation, its disposition,
and — for each admitted criterion — the input that makes it red and the single
surface that observes the failure.

This is the second set for this slice. The first was authored against a narrower
scope — correcting the four-discipline walk's claims and adding one page — and
went through three adversarial rounds and a design gate before the owner
redirected the slice to the guidebook. That set and its rounds are recorded in
[`review-record.md`](review-record.md); the criteria that survive the rescope
are AC-0009 to AC-0011 here, because the walk's surfaces are still false and a
guidebook built over a false spine would teach it.

Candidates considered: 33. Admitted as criteria: 22. Routed to a named
owner: 10. Dismissed with the reason recorded: 1.

## Stage 1 — the changed contract obligations

| Id | Objective outcome |
| --- | --- |
| O1 | Each of the five packs' journeys is walkable as a guidebook. |
| O2 | The step contract is fixed and mechanically enforced. |
| O3 | Every published skill in those packs is reachable from its guidebook. |
| O4 | A guidebook cannot drift from its pack's own words. |
| O5 | The walk's surfaces stop claiming handoffs the packs do not make. |
| O6 | No two slices claim the same guides. |

| Id | Non-waivable Boundary |
| --- | --- |
| B1 | No adoption, completion, task-success or first-value claim. |
| B2 | No "optional" label without what skipping costs. |
| B3 | No sample response presented as deterministic. |
| B4 | No claim the two plugin routes are equivalent. |
| B5 | No `packs/**` change. |
| B6 | No edit to generated `web/src/content/journeys/*.md`. |
| B7 | No image in a guide. |
| B8 | No edit to `site.toml` or its `[[guide_groups]]`. |

## Stage 2–4 — candidates, admission, routing

Admission ground: externally observable behaviour (EOB), required refusal or
recovery path (REF), compatibility or safety guardrail (GRD).

| # | Candidate | Ground | Disposition |
| --- | --- | --- | --- |
| C1 | The contract is stated and enumerates its obligations | EOB | **Admitted** → AC-0001 |
| C2 | The lint fails a step missing an obligation, naming which | REF | **Admitted** → AC-0002 |
| C3 | Every contract obligation has a registered check | GRD | **Admitted** → AC-0003 |
| C4 | Guidebook shape matches the journey — count, order, stage identity | EOB | **Admitted** → AC-0004 |
| C5 | Every step of all five guidebooks passes the lint | EOB | **Admitted** → AC-0005 |
| C6 | Utterance and response verbatim from the owning stage, artifact path verbatim from the owning skill | GRD | **Admitted** → AC-0006 |
| C7 | The reader's turn and the agent's turn are separately attributed | EOB | **Admitted** → AC-0007 |
| C8 | Every published skill is named by at least one step | EOB | **Admitted** → AC-0008 |
| C9 | P2b carries no whole-pack handoff claim | EOB | **Admitted** → AC-0009 |
| C10 | P2b's fourth step ends at the decision brief | EOB | **Admitted** → AC-0010 |
| C11 | The journeys index's group body carries no handoff claim | EOB | **Admitted** → AC-0011 |
| C12 | The consolidation is recorded on both sides | GRD | **Admitted** → AC-0012 |
| C13 | No surface claims improved adoption or first value | REF | **Admitted** → AC-0013 |
| C14 | A criterion per contract obligation — one criterion per row | — | **Routed → AC-0003 and AC-0005.** This is the repair-the-generator response. The lint is the single enforcement point; AC-0003 guarantees it checks every obligation and AC-0005 that it passes over real content. Ten further criteria would restate what those two already establish, and each would red on the same input as the lint. |
| C15 | The guidebook validates and reaches the sidebar | — | **Routed → existing repository controls.** `tools/validate_guides.py`, `tools/lint-guide-titles.py`, `tools/check-guide-index.py` and the derived inventory at `tools/build-site.py:872` already enforce every part. Recorded in Testing Strategy. |
| C16 | The affordance audit's per-pack numbers improve | — | **Routed → the verification ledger, not a criterion.** The brief's own rabbit holes rule the audit an instrument built to size the problem, and promoting it to a gate a separate decision. The before-and-after is recorded because a slice quoting a baseline owes the second measurement; it is not asserted as a threshold, which would freeze corpus totals. |
| C27 | The machine/human check boundary is enforced, not merely stated | GRD | **Admitted** → AC-0014. Automation complacency degrades a judgement list that contains machine-checkable items, so the boundary needs an oracle. Raised by round 1: the first draft stated the rule in prose with nothing able to fail. |
| C28 | Every skill a step names carries its own utterance, path and outline | EOB | **Admitted** → AC-0015. Round 1 showed AC-0008's name-presence oracle lets a skill be listed without becoming runnable, which is the difference between mentioned and executable. |
| C29 | The three journey group signatures stay distinct and mapped | GRD | **Admitted** → AC-0016. Restored: the brief's absorbed design contract requires it and the rescope dropped it. |
| C30 | The onward route resolves whole, not by a shared fragment | GRD | **Admitted** → AC-0017. Restored, same reason. |
| C31 | P2b stays adjacent to P2 | GRD | **Admitted** → AC-0018. Restored, same reason. |
| C34 | P2b is not counted as a walkthrough stage | GRD | **Admitted** → AC-0019. Split from C31: a different observer, in a different test file, with a different red input. Bundling the three would have been one candidate no single case could hold. |
| C35 | P2 and P2b select on the fixed axis | GRD | **Admitted** → AC-0020. Split from C31, same reason. |
| C36 | A concept a step depends on resolves to an explanation | EOB | **Admitted** → AC-0022. Owner direction 2026-09-11. Admitted as *resolution* only: whether a step should have named a concept it silently assumed has no mechanical oracle and goes to the cold read as its eighth question, which is the same split used for the other semantic residues. |
| C32 | The cold read's defects are resolved before the next wave opens | REF | **Admitted** → AC-0021. Round 1 showed T4 could record a defect, defer it, and let every criterion stay green. |
| C23 | The artifact's location and expected shape | EOB | **Routed → the contract, rows 9 and 10**, enforced by AC-0003 and AC-0005, with the path's projection added to AC-0006. Not a criterion of its own: the lint is the single enforcement point, and a twelfth criterion would red on the same input as the lint. Raised by the owner 2026-09-11 — these skills write files, which the surveyed corpus does not cover. |
| C33 | A wave ordering ranked by deliverable-form cost | — | **Routed → wave 0 as a measurement task, not a claim.** Round 1 showed the ranking rested on a predicate that undercounts: `product-strategy` measures 0 of 9 under a headings-and-assets predicate and 1 of 9 under a wider one that also reads prose enumerations, while the skills the reviewer named do state their structure. The corpus figure moves between 33 and 38 of 74 depending on the predicate, which is too unstable to sequence work on. The per-skill ledger is built before the ordering is used. |
| C17 | A house wording for the variability caveat | — | **Dismissed, reason recorded.** The survey establishes there is no evidence which wording calibrates a reader best — it is a named known-unknown. A criterion pinning one wording would assert a finding the research explicitly does not support. The obligation that a caveat is *present* is checked; its wording is an authoring choice. |
| C18 | The remaining 17 packs get guidebooks | EOB | **Routed → follow-on.** The contract is proved on the five a team SOP needs; extending it is an appetite decision, not a gap here. |
| C19 | The marketing home routes a reader to the sequence | EOB | **Routed → `cohort-orientation-surfaces`.** Two sources agree it belongs and neither authorizes building it: the marketing brief records itself as "not authority to edit the header", and Shipped `site-shared-chrome` puts a header change under "Ask first". |
| C20 | A no-terminal route for a Claude Desktop reader | EOB | **Routed → `claude-apps-route-docs`** (Draft, unimplemented). |
| C21 | A committed-byte parity gate for generated journeys | GRD | **Routed → follow-on.** B5 means this slice changes no pack source, so it cannot produce the gate's red input. A gate whose red case this slice cannot exercise is a control that cannot fail. |
| C22 | `packs/experience-design/DESIGN.md`'s stale skill name | — | **Routed → the owning pack.** It names the state-matrix consumer `voice-and-microcopy`; the skill is `ux-writing`. A pack source edit, excluded by B5. Surfaces this slice writes name `ux-writing`. |

## Stage 5 — one red input and exactly one observer per criterion

`GB` = `tools/test_lint_guidebook_steps.py`, the new repository-level suite;
reads guide markdown, the convention, and the five `packs/*/JOURNEY.md` sources,
so it needs no build and cannot skip silently. `LINT` = the shipped lint run over
the five guidebooks. `WEB` = `web/src/test/FourDisciplineSequence.test.ts` over
`build/journeys/index.html` after `make site-build`.

| AC | Red input | Observer |
| --- | --- | --- |
| AC-0001 | Keep every obligation identifier in `guides/AGENTS.md` and delete the normative statement that the contract binds every step — the enumeration still reads correctly, so only the two-half check reds | GB |
| AC-0002 | A fixture step satisfying every obligation but `variability`; the report must name that obligation, not merely fail | GB |
| AC-0003 | Two mutations, because the obligation has two failure modes. Register a **no-op** check against a fresh obligation identifier — registry-key equality still holds. Then, for `artifact_outline`, change one heading while its template is unchanged, leaving the outline present — killed only by the divergence fixture, since a presence-only implementation passes the omission one | GB |
| AC-0004 | Swap two steps' `order` values, leaving every step present and every obligation met | GB |
| AC-0005 | Delete the failure path from one real step in one shipped guidebook | LINT |
| AC-0006 | Two mutations. Corrupt a non-utterance rung: replace one step's **artifact path** with an invented one and record no fallback, so a check reading only row 3's ladder passes. Then replace a stage's existing utterance with invented text and **record it as authored** — the fallback is recorded, so only the rung-order rule reds | GB |
| AC-0007 | Merge one step's input and agent response into a single unlabelled block, as a journey stage does today | GB |
| AC-0008 | Remove `marketplace-design` from the `experience-design` guidebook, leaving the other nineteen skills named | GB |
| AC-0009 | Delete the handoff-chain sentence from P2b without stating the corrected relationship — the lexical prohibition passes and the positive half reds | GB |
| AC-0010 | Restore "a change you approved before it merged" to P2b's fourth step | GB |
| AC-0011 | Two mutations, one per half. Correct the group body but leave the first three cards' handoff claims and the assertion requiring them in place. Then replace all four taglines with unrelated prose containing no prohibited handoff wording — the prohibitive half passes and only the positive half reds | WEB |
| AC-0012 | Omit one eligible target from **both** this ledger and its sibling's record, leaving every ledger row and every record resolving — killed only by the three-set comparison against the accepted-base universe, since ledger-to-record equality passes | GB |
| AC-0013 | Add one of the contract's enumerated prohibited terms to a step. A paraphrase is deliberately *not* the red input: the criterion is lexical and a paraphrase is the cold read's to catch | GB |
| AC-0014 | Declare a judgement check whose kind names `artifact_outline`, a machine-owned obligation — decidable against the closed set, where a paraphrase would not have been | GB |
| AC-0015 | Give a step ten named skills sharing one step-level utterance, so every obligation is present but none is attributable to a skill | GB |
| AC-0016 | Swap the sequence and loops modifiers, keeping three distinct at-rest rules — killed only by the mapping clause | WEB |
| AC-0017 | Point the onward link at a different path sharing the `/docs/guides/` and `#p2b` fragments | WEB |
| AC-0018 | Move P2b below P3, keeping its `P2b` label so it is still not a stage | GB |
| AC-0019 | Relabel P2b's heading `P6` with a bare number, making it a sixth stage | RENDER |
| AC-0020 | Keep an enumerated-clean condition but drop the disciplines-needed axis, so the prohibition half passes and the positive half reds | GB |
| AC-0022 | Name a concept as required and link it to a target that does not resolve, leaving every other concept correctly linked | GB |
| AC-0021 | Three mutations. Record a step the cold read could not answer, attach a deferral, and open wave 2. Then ship a later pack whose read answers only the first five questions, so the semantic residue goes unobserved in four of five packs. Then answer all eight for every step but omit the concept question, leaving a silently-assumed concept unobserved | COLD |

Five criteria carry more than one mutation, because their obligation has more
than one failure mode and a single mutation would have left the other mode
unproved. That is recorded rather than reduced: collapsing them would produce
one red input per criterion at the cost of an unobserved failure.

Every red input is distinct, and none is a bare deletion where a set is the
oracle: AC-0004 preserves the step count, AC-0008 preserves nineteen of twenty
skill names, and AC-0012 preserves the ledger. A length comparison passes all
three, which is why none of them is specified on a count.

## Stage 6 — coverage, read both ways

**Forward:**

| Item | Covered by |
| --- | --- |
| O1 | AC-0004, AC-0005, AC-0006, AC-0015, AC-0021 |
| O2 | AC-0001, AC-0002, AC-0003, AC-0014 |
| O3 | AC-0008, AC-0022 |
| O4 | AC-0007 |
| O5 | AC-0009, AC-0010, AC-0011, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020 |
| O6 | AC-0012 |
| B1 | AC-0013 |
| B2 | AC-0005, through the contract's prerequisite-cost obligation |
| B3 | AC-0005, through the contract's variability obligation |
| B4 | Boundaries, held at review |
| B5 | Boundaries, plus the empty-diff check in Testing Strategy |
| B6 | Boundaries, plus the same empty-diff check |
| B7 | Boundaries, held at review |
| B8 | Boundaries, held at review |

**Back:** AC-0001→O2, AC-0002→O2, AC-0003→O2, AC-0004→O1, AC-0005→O1,
AC-0006→O1, AC-0007→O4, AC-0008→O3, AC-0009→O5, AC-0010→O5, AC-0011→O5,
AC-0012→O6, AC-0013→B1, AC-0014→O2, AC-0015→O1, AC-0016→O5, AC-0017→O5,
AC-0018→O5, AC-0019→O5, AC-0020→O5, AC-0021→O1, AC-0022→O3. None names nothing, so none is
decoration.

**Necessity note on AC-0002 against AC-0005.** Both involve the lint, so both
are tested for the same predicate. They differ: AC-0002 is the lint's behaviour
on a fixture that isolates one obligation, and reds when the report fails to
name which obligation is unmet; AC-0005 is the state of real shipped content,
and reds when a real step is incomplete. A lint that failed without naming the
obligation would satisfy AC-0005 and fail AC-0002; a correct lint over an
incomplete guidebook would satisfy AC-0002 and fail AC-0005.

**Necessity note on AC-0009 and AC-0010.** Both read P2b. Their predicates
differ — one is the handoff-chain phrasing plus the corrected relationship, the
other is the fourth step's end state — and restoring either sentence leaves the
other criterion green.

**On lexical narrowing.** AC-0009, AC-0013 and AC-0020 each prohibit a claim,
and a prohibition on *meaning* has no mechanical oracle. Rather than assert one,
each is narrowed to the contract's enumerated phrasings and paired with a
positive half a scan can prove, with paraphrase assigned to the cold read
(AC-0021) as its named observer. This is the narrow-the-claim response, not a
repair: the alternative was a criterion no check could reach.
