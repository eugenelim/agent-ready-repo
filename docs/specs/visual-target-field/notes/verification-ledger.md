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
