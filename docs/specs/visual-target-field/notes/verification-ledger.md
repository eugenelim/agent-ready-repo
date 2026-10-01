# Verification ledger: visual-target-field

Execution root: `<repository-root>` (the `visual-target-confirmation` worktree).

## T4 verification

Date: 2026-10-01

T4 was committed before the 2026-10-01 amendment and was **not met** at that
point: the amendment rewrote its `Done when` so it could not pass while two
already-shipped artifacts stood non-conforming. Both are now repaired. All five
conditions are recorded below, measured after the repair.

**Authorship, recorded because the dispatch receipt cannot carry it.** T4's
original implementation was built by an implementer subagent and is committed at
`774f9e5ae`; that is what `dispatch-receipt --receipt` asserts and it is true.
The two-defect repair below was applied by the controller, not by an implementer
subagent. The receipt vocabulary has no value for a controller-applied repair —
`--decline`'s two reasons are `no-implementer-installed` and `human-directed`,
and neither is accurate here — so the fact is recorded in this ledger instead of
being folded into the receipt. The owner was asked and directed this disclosure
on 2026-10-01 rather than a reverted-and-redispatched repair or a scoped ruling.

### 1. Byte identity against the approved stub

`tests/roster/test_visual_target_release_surface.py` is byte-identical to the
stub block stored in this task's plan section, per `tdd-stubs.md` § *Lifecycle*.

- Approved stub SHA-256: `91dfb32f2c1aead03bc9b5ba28d401240c9e0e5e7e776e07e277ceb9e005bbf5`
- Materialized file SHA-256: `91dfb32f2c1aead03bc9b5ba28d401240c9e0e5e7e776e07e277ceb9e005bbf5`

The delta repaired was exactly 2 hunks and 13 changed lines, all of it the
release-literal split: the committed file derived the changelog heading from the
live pack `version`, where the approved stub pins a `RELEASE = "4.1.2"` literal
and keeps the three-site version agreement reading the live version. `import re`
is absent from both the stub and the materialized file, so byte identity and
`ruff` hold together.

### 2. Both repair-state defects (recorded manual observation)

No lint reads prose register, so this condition is a recorded observation rather
than a gate. Read against `docs/product/changelog.md`'s own header rules.

**Defect (a) — the stated condition.** The published bullet said `converge`
records the disposition "when writing compositional commitments". The string
`when writing compositional commitments` now occurs nowhere in
`docs/product/changelog.md` (0 occurrences), and the replacement states no other
condition on recording. Grounds that the removed claim was false:
`packs/experience-design/.apm/skills/creative-direction/references/converge.md:56-61`
instructs `converge` to record the key with one of the three values in every
case — the three conditions there select *which* value, not *whether* the key is
written. The replacement says it "writes it every time it runs", which matches.

**Defect (b) — register.** `changelog.md`'s header requires Highlights bullets
to be "outcome-led, user-facing", to "Rewrite for users, not contributors", and
to "Describe what someone can now do". The bullet now opens "You can now record
whether a direction's visual target was ever confirmed, and tell that apart from
never having asked" — an adopter outcome — where it previously opened with the
frontmatter key, which is the artifact mechanism. It no longer closes "this is
an additive schema change adopters author against", which was contributor
register; it closes on what the reader may do with the record.

**Retained, as the condition requires.** The entry is still a single `- ` bullet,
so the `/now/` projection (which extracts only bullets) still picks it up; it
still carries the literal `visual_target`, which AC-0010's assertion greps for;
and it still says plainly that nothing reads the field and nothing is gated on
it.

### 3. Lint and type gates

- `make lint-ruff lint-mypy` — exit 0 (`All checks passed!`; `Success: no issues found in 149 source files`).
- `ruff check .` — exit 0.

### 4. Suites

`python3 -m pytest tests/conformance/test_pack_metadata.py tests/roster/test_visual_target_release_surface.py -q`
— exit 0, `50 passed in 0.65s`.

### 5. Placement lints

- `python3 tools/lint-conformance-portability.py --root .` — exit 0.
- `python3 tools/lint-ci-parity.py` — exit 0.

Every exit code above was read from the command's own status, not from its
output tail.

## T5 mutation proofs

Date: 2026-10-01

Both assertions are green on first run because T1 already committed the material
they check. The owner's waiver (recorded in `notes/amendment-2026-10-01.md`)
permits a mutation proof to stand in for the intended red at both plan-approval
and EXECUTE phases. Two mutations are recorded below.

### AC-0012 mutation proof

- **Invariant:** `visual_target: "<none | unconfirmed | confirmed>"` appears
  exactly once as a line (after `rstrip`) inside the `type: creative-direction`
  fenced excerpt of
  `guides/experience-design/how-to/establish-design-intent.md`.
- **Catching test:** `tests/roster/test_visual_target_guide_excerpt.py::test_visual_target_guide_excerpt`
- **Exact mutation:** deleted the single line
  `visual_target: "<none | unconfirmed | confirmed>"` from the guide's fenced
  excerpt only (line 153 of `establish-design-intent.md`). The fence still
  carried `visual_target` three times (in the comment) and the `RECORD_LINE`
  intact, so the mutation falsifies the key-line sub-property without deleting
  the whole construct.
- **Expected failure:** `test_visual_target_guide_excerpt` fails on the
  `KEY_LINE` count assertion (`assert 0 == 1`).
- **Observed failure:** `FAILED tests/roster/test_visual_target_guide_excerpt.py::test_visual_target_guide_excerpt` —
  `AssertionError: AC-0012: 'visual_target: "<none | unconfirmed | confirmed>"'
  must appear exactly once in the template fence. … assert 0 == 1`. The
  `RECORD_LINE` check passed; only the `KEY_LINE` count failed, confirming the
  assertion decides the key's presence independently.

  *Controller correction, 2026-10-01.* The implementer's record of this proof
  stated "Exit code 0 (pytest itself exited 0, failure was in the assertion)".
  That is false and self-contradictory against the `FAILED` line beside it:
  pytest exits 1 when a test fails, confirmed by a control run on a deliberately
  failing test. The claim is struck rather than replaced, because the mutated
  run's process exit code was not separately measured and § *Proof record* does
  not require it — `Observed failure` is carried by the assertion text above.
- **Restoration:** added the deleted line back by editing the guide file directly
  (no `git checkout`, `git reset`, or `git stash`). Confirmed
  `python3 tools/lint-guidebook-steps.py guides/experience-design` exits 0
  and `test_visual_target_guide_excerpt` passes.

### AC-0011 mutation proof

- **Invariant:** the `## Approved visual target` section comment in
  `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md`
  contains the contiguous phrase `An absent \`visual_target\` reads as \`unconfirmed\``
  (after whitespace normalisation).
- **Catching test:** `packs/experience-design/tests/skills/creative-direction/test_contract.py::test_template_carries_the_visual_target_disposition`
  — specifically the `normalized_comment` assertion that replaced the old
  AC-0011 line. `Catching test` is load-bearing here because this assertion is
  one of four criterion checks inside the same function.
- **Exact mutation:** in the template only, changed
  `An absent \`visual_target\` reads as` to
  `When \`visual_target\` is absent from the frontmatter, it is treated as` —
  the reworded sentence still contains both `absent` and `unconfirmed` but not
  as the pinned contiguous run. The guide was **not** re-derived while the
  mutation stood, as required by the plan.
- **Expected failure:** `test_template_carries_the_visual_target_disposition`
  fails on the replaced AC-0011 assertion.
- **Observed failure:** `FAILED packs/experience-design/tests/skills/creative-direction/test_contract.py::test_template_carries_the_visual_target_disposition` —
  `AssertionError: AC-0011: the comment must state the absent-field reading as
  one contiguous phrase. … assert 'An absent \`visual_target\` reads as
  \`unconfirmed\`' in '… When \`visual_target\` is absent from the frontmatter,
  it is treated as \`unconfirmed\`, …'`.
- **Contrast (the superseded co-occurrence form):** under this same mutation, the
  superseded assertion `"unconfirmed" in comment and "absent" in comment.lower()`
  evaluated to `True` (passes), while the replacement contiguous-phrase assertion
  evaluated to `False` (fails). Verified by direct evaluation in Python against
  the mutated template. Those two evaluated outcomes are the whole of what this
  proof records; the reason the replacement was adopted is stated in the spec's
  AC-0011 and is not restated here, so this record cannot drift from it.
- **Restoration:** edited the template back to `An absent \`visual_target\` reads
  as \`unconfirmed\`, so record it deliberately rather than leaving it off.`
  directly (no `git checkout`, `git reset`, or `git stash`).
  `test_template_carries_the_visual_target_disposition` passes after restoration.
  The guidebook lint was expected to red during the mutation (the comment is
  reproduced verbatim in the guide); it was not re-run during the mutation and
  returns to green after restoration.

Every exit code above was read from the command's own status, not from its
output tail.
