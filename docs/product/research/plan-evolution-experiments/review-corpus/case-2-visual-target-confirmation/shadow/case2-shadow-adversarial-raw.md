## Findings

### Blockers

None. The dependency graph is acyclic; T1, T2, and T8 can start immediately; no proposed mechanism is incapable of doing what the contract needs.

---

### Concerns

**C-1. T6's roster assertion is narrower than AC-0017 requires.**

Where: plan.md, T6 Tests block; spec.md AC-0017.

AC-0017's second comparison covers four files: `visual-observation.md`, `design-system`'s `SKILL.md`, `converge.md`, and `visualize.md`. T6's described roster assertion only sweeps the first two: "the `visual_target` values declared in the template and the values named in `visual-observation.md` and `design-system`'s `SKILL.md` agree." `converge.md` and `visualize.md` are not mentioned.

T4 independently pins exact literals in `converge.md` and `visualize.md` (via the experience-design suite), but T4's assertions check that specific values *exist*, not that every `visual_target: <value>` occurrence in those files is a member of the declared set. A commentary line or a counterexample in `converge.md` carrying an undeclared value (say, `visual_target: proposed` in a prose aside) would pass T4 and T6 as described while failing AC-0017.

Fix: extend the T6 roster assertion to also sweep `converge.md` and `visualize.md` for whitespace-normalized `visual_target: <value>` occurrences, consistent with AC-0017's stated scope.

---

**C-2. T11's described test covers two of four AC-0027 conditions; the absence check for `everything else stands` is missing.**

Where: plan.md, T11 Tests block; spec.md AC-0027; repository file `docs/specs/frontend-visual-authority/spec.md` line 3.

AC-0027 has four checkable conditions:

1. The Status field names ADR-0130's body budget.
2. The Status field names ADR-0131's `requires` value `recorded-human-confirmation`.
3. The Status field names ADR-0131's Always-do rule (that a rung condition is a property the pack defines, not an upstream template's value).
4. The Status field contains no whitespace-normalized match for `everything else stands`.

T11's plan describes only conditions 2 (ADR-0131 and `recorded-human-confirmation`): "it carries a supersession annotation naming ADR-0131 and the superseded `requires` value `recorded-human-confirmation`."

The existing Status field reads `Shipped (superseded in part by ADR-0130 — 960-line body budget; everything else stands)` — condition 4 is currently violated, and conditions 2 and 3 are absent. An implementer who adds the ADR-0131 annotation but forgets to remove "everything else stands" would pass T11 as described while failing AC-0027. Condition 3 (the Always-do rule annotation) is the least load-bearing in practice, but it is a named part of the criterion.

Fix: extend T11's assertion to also check for the absence of a whitespace-normalized `everything else stands` match and for the presence of language naming the Always-do rule reversal, in addition to the ADR-0131 and `recorded-human-confirmation` checks.

---

### Nits

**N-1. Plan says "byte-identical"; the controlling test uses whitespace-normalized matching.**

Where: plan.md, T5 Approach block ("The bullet's protected sentence about supplying no values stays byte-identical."); repository file `test_visual_authority_slice_two.py` line 201.

`test_the_rung_one_value_rule_survives` calls `holds(flat(SKILL), statement)`, which is case-insensitive and whitespace-normalized — not byte-identical. The constraint is real and the implementer must respect it, but the protection is slightly weaker than the plan implies. The phrase "stays byte-identical" should read "stays whitespace-normalized match" to match what the test actually enforces and to avoid a false pass if the sentence is reformatted without changing its words.

---

**N-2. T1's "Done when" condition names a determination only T7 can confirm.**

Where: plan.md, T1 Done when block.

"The verification ledger records the reader set, the green roster run, and whether either journey page became a T7 surface." T7 depends on T5, which depends on T3, which depends on T1. At T1 execution time, T7 has not run; T1 cannot record whether the journey pages *did* become T7 surfaces, only whether they *should*. During execution this could cause a T1 reviewer to hold the task open waiting for a determination that is weeks away. The wording should read "identifies which journey pages, if any, require a T7 surface" so T1 closes on its own evidence.
