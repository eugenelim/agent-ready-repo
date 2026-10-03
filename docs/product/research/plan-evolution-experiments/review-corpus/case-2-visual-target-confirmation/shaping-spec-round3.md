**Result: Findings** (spec mode, round 3)

**Targets** — `~/orca/workspaces/agent-ready-repo/visual-target-confirmation/docs/specs/visual-target-confirmation/spec.md`, `.../plan.md`, `~/orca/workspaces/agent-ready-repo/visual-target-confirmation/docs/adr/0131-visual-target-confirmation-is-an-explicit-state.md`
**Reviewed revision** — none supplied; read from the worktree as found on 2026-09-29.
**Review context** — round 3, judging the round-2 delta and anything it introduced. Seven of the eight round-2 repairs hold as claimed: AC-0027's two-supersession wording, AC-0017's two explicit comparisons, the `test_visual_authority_release.py` pin moved into plan Constraints and T10's Touches, ADR-0131's Confirmation section now claiming only what criteria establish, and the roster gate-topology risk are all sound. The two sweeps and AC-0026 are where the delta went wrong, below.
**Consulted surfaces** — the three targets; `docs/specs/frontend-visual-authority/spec.md`; `docs/specs/design-to-build-value-handoff/spec.md` (AC-0013, 968); `packs/AGENTS.local.md` § Marketplace and release pipeline; `docs/product/changelog.md` header; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`, `references/visual-observation.md`, `evals/evals.json`; `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py`, `test_visual_authority_slice_two.py`, `test_visual_authority_entrypoint.py`; `packs/experience-design/.apm/skills/creative-direction/SKILL.md`, `references/visualize.md`, `references/converge.md`, `assets/creative-direction-template.md`; `guides/frontend-engineering/how-to/read-the-design-handoff.md`.
**Grounding gaps** — no reviewed-revision identifier was supplied, so findings bind to the working tree read today; I did not run any suite.

---

### 1. (High) AC-0006 contradicts a contract-tier Agent Rule of the Shipped `frontend-visual-authority` spec, and AC-0027 does not name it

`docs/specs/frontend-visual-authority/spec.md:80` (§ Agent Rules → Always do) states: *"State rung conditions as properties this pack defines. A frontmatter value only an upstream template produces is an illustration, never the condition itself."* That spec's own tier note puts `Agent Rules` in the amendable contract tier, alongside Acceptance Criteria.

New AC-0006 puts `visual_target: confirmed` — a frontmatter value only `creative-direction`'s template produces — directly in the `requires` cell, making it the condition itself. The shipped test says the same thing in its own words at `test_visual_authority_precedence.py:45-48`: *"A rung keyed on another pack's template vocabulary goes wrong at that template's next edit, and no declared-dependency check can see it."* AC-0027 annotates only ADR-0131's supersession of the `requires` *value* `recorded-human-confirmation`, which leaves the rule that forbids the new value's *shape* standing and unsuperseded. The frozen spec's Assumption at line 186 restates it too (working material, advisory).

This is not a reopened decision: ADR-0131 settles that the rung binds on the field, and I am not disputing that. What the record does not answer is the conflict with an applicable, non-superseded obligation in a Shipped spec.

**Fix:** extend AC-0027 to require the frozen spec's `Status` annotation to name this Always-do rule as superseded in part by ADR-0131 as well, and record in ADR-0131 § Decision why keying on an upstream-produced value is now correct (the pack still installs standalone; the field is adopter-writable like `type:`). Alternatively, restate AC-0006's cell as a pack-defined property with the field as its illustration — but that re-admits the inference the slice exists to delete, so the annotation route is the one to take.

### 2. (High) AC-0031 cannot pass under the current task set — a second eval case carries the retired phrase and no task edits it

AC-0031 sweeps all of `packs/frontend-engineering/.apm/` for `records a human-confirmed composition`. That tree has two carriers of that literal today, not one:

- `.../SKILL.md:152` — the rung-1 bullet, edited by AC-0012/T5.
- `.../evals/evals.json:90` — the `visual-authority-direction-only` case's prompt: *"Nothing records a human-confirmed composition. Build the page."*

AC-0028 restates only `visual-authority-approved-target` (line 77). T9 enumerates six cases and does not include `visual-authority-direction-only`; T5 owns AC-0031 but its Touches list excludes `evals/`. So the sweep reds with no criterion or task owning the edit that would clear it, and the task that would notice is not the task that owns the file.

**Fix:** add a criterion restating `visual-authority-direction-only`'s prompt against the field (the natural home is AC-0019, which today merely requires that *a* case exist — point it at this shipped case instead of a new one), add it to T9's enumeration, and add `.../evals/evals.json` to T5's Touches or move AC-0031 to T9 so the sweep runs after the last writer of that tree. Note also `test_visual_authority_slice_two.py:136-139` pins this case id and the literal `resolved` in its `expected_output`; the restatement must preserve both, and the plan Constraints should record that pin as it already records the other three.

### 3. (Medium-high) The retired-phrase set is derived from one wording, so the rung-2 mirrors of the superseded reading survive

The round-2 finding was that presence-only criteria leave the superseded prose reading alive. AC-0031/AC-0032 close the rung-1 wording only. Three live carriers of the same reading are outside both closed sets:

- `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:157` — *"A direction recording no confirmation resolves here, and the run records that it was unconfirmed."*
- `guides/frontend-engineering/how-to/read-the-design-handoff.md:64-65` — *"your `direction/<slug>.md` records that a person confirmed the composition"*.
- `guides/frontend-engineering/how-to/read-the-design-handoff.md:74-75` — *"**You are here if** you have a direction but nothing in it records a human confirming the composition."*

AC-0012 covers only the rung-1 bullet; AC-0015 is a presence check over the guide. After the change a reader lands on rung 2 by judging whether the artifact "records a human confirming the composition" — the exact inference ADR-0131 § Context says the rung exists to prevent — while every criterion is green.

**Fix:** state rung 2's condition against the field on both surfaces and hold it: add `visual_target` readings other than `confirmed` to the rung-2 entry in `SKILL.md` and to the guide's rung-2 *You are here if*, pin each with a literal criterion, and extend the AC-0031/AC-0032 closed set with `records that a person confirmed`, `records a human confirming` and `recording no confirmation`. Derive the set by sweeping the two trees for the reading, not for the one phrase round 2 named.

### 4. (Medium) AC-0026's restatement is half a literal check, so the cut-criterion policy is still applied two ways — and its test does not match its text

The plan's own rule (§ Design → Design decisions) is that "the only check available is that a sentence exists" disqualifies a criterion; three criteria were cut on it. AC-0026's first clause is a literal (`visual_target` appears in the comment). Its second clause — "states that the section's `**Target:**`, `**Binding:**` and `**Confirmation record:**` lines bind nothing on their own" — is a sentence-exists check with no pinned literal, indistinguishable in checkability from the three that were cut. The duplication hazard is real, so the criterion should stay; the restatement just did not finish.

Separately, T3's test for it reads *"names the frontmatter key as canonical and the body lines as provenance"* — a third wording again, matching neither the criterion nor a literal. A criterion and its stated test that describe different strings cannot both be the contract.

**Fix:** pin the second clause to a literal the comment must contain (for example `bind nothing on their own`) alongside the three line labels, and restate T3's test in exactly those terms.

### 5. (Medium) AC-0030's Highlights clauses are not mechanizable, and its none-branch is almost certainly the wrong branch for this release

The rescope correctly moved the none-verdict reason to the PR. What remains is still a judgment gate: "a `### Highlights` subsection under any entry that owes one" turns on `packs/AGENTS.local.md`'s question *does this change what a consumer of the pack can do?* — which no check can answer, and the plan's own T10 Approach concedes "No changelog byte records it, so no check here looks for one." So the criterion's second and third clauses cannot fail.

The branch is also very likely false here. ADR-0131 records the tradeoff that *"every direction artifact written before this record reads `unconfirmed` and loses any top-rung binding it previously had by inference"*, and adds a new field an adopter must write. That is a change in what a consumer can do, on the file's own test.

**Fix:** settle the verdict in the spec now rather than leaving a branch: state that both release entries carry a `### Highlights` subsection, and make AC-0030 assert a free-standing `##` entry per new version each with a `### Highlights` subsection beneath it. Delete the none-branch and the PR-routing sentence, or keep the PR routing in the plan as guidance only.

### 6. (Medium) AC-0017's second comparison states no extraction predicate, and what it can check is already covered

"every `visual_target` value named anywhere in `visual-observation.md` or in `design-system`'s `SKILL.md` is a member of that declared set" does not say how a value is recognised. `visual-observation.md` contains bare `none` in at least two cells (`none — terminal`, `none — stated in-session`, lines 25 and 22-25 of the precedence table), so a word-level scan over the declared set miscounts, and a scan keyed on `visual_target:\s*(\w+)` makes the design-system half redundant with AC-0011, which already pins that cell to the literal `visual_target: confirmed`.

**Fix:** name the extraction predicate in the criterion — matches of `visual_target:\s*<value>`, whitespace-normalized — and scope the membership half to those matches. Keep the first comparison (template set equals the `states` row set exactly) as the drift control it is.

### 7. (Medium) The producing side is gated in `converge` only; `visualize` still instructs recording an unconfirmed target's binding, and still owns a second `none`

This is my answer to the round-2 adjudication, and it is a different claim from the one that was refuted. The adjudication is correct about what it addressed: `visualize.md:13` scopes "approved visual target" to a confirmed composition, `:19` and `:41` and `SKILL.md:118` establish that `visualize` writes nothing and `converge` is the only writer. I accept that; the rung-1 sentence is not ungated.

What it did not reach is `visualize.md:21-27`, which is not about the *approved* target:

> "When a target exists, record its identity and three boundaries: what is binding, what is illustrative, and what may adapt responsively. … When no target exists, record `none` and continue."

That instruction is keyed on *a target existing*, not on confirmation, so it tells the operation to record "what is binding" for an unconfirmed target — which `converge` then captures into `## Approved visual target`'s `**Binding:**` line (`converge.md:56`, `template:80`). The spec's own Outcome says "An unconfirmed target's compositional commitments are not written into the direction artifact"; AC-0025 gates only the `## Compositional commitments` section, and AC-0026 mitigates for a template reader via a comment. No criterion and no task touches `visualize.md` at all — it appears in no Touches list. The `record `none`` at `:26` is also a second, body-level home for the `none` state whose canonical home the spec puts in frontmatter, and AC-0017's roster comparison does not read `visualize.md` or `converge.md`, so a drift there reds nothing.

**Fix:** either scope `visualize.md:21` to the confirmed case and route the unconfirmed case to `**Target:**` plus the disposition alone, adding `visualize.md` to T4's Touches with a criterion pinning the scoping literal; or state in the spec why `**Binding:**` on an unconfirmed target is harmless given AC-0026's comment, and say so in ADR-0131 rather than leaving the Outcome's claim wider than the criteria that hold it.
