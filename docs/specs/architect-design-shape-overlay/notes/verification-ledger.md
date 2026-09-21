# Verification ledger

Execution observations. The approved `spec.md` and `plan.md` carry obligations;
this file carries what was observed when they were discharged.

## T1 executed ahead of the pre-EXECUTE gate — 2026-09-20

**Deviation from the task row's literal method, recorded because it is one.**
The scope owner directed that T1 be built before the engine reached
`CODE-IMPLEMENTATION`, so the overlay probe's routed arm could be authored
against the real region rather than a paraphrase. It was — against T1's
working-tree draft of that region. Review changed two sentences in it
afterwards, so the arm did not read the delivered bytes;
`notes/probe/method.md` names both changes and what they cost. The engine was at
`SPEC-PLAN-REVIEW` at the time and no transition was fired to disguise that;
the run's history shows the gap.

**The red, and its three distinct failures.** The implementer wrote
`packs/architect/tests/skills/architect-design/test_shape_axis_routing.py`
first and ran it against a `SKILL.md` with no shape-axis region. Re-derived by
the controller on 2026-09-20 by stripping the region from the working copy and
re-running, then restoring it byte-exact. The **restored** file — the
axis-present T1 draft, not the stripped fixture — hashes to SHA-256
`604962f3…`, which is the digest the strip started from and returned to. No
digest is recorded for the stripped fixture: it was a transient mutation and
one was never taken. Review has edited the region since `604962f3…`, so that
is not the delivered digest either — run `shasum -a 256` on the file for
that.


| Failure | Count | Tests |
| --- | --- | --- |
| `AssertionError: shape-axis region is missing a marker` | 5 | the five that call `_region()`; its guard refuses a file missing either marker, before the slice runs |
| `AssertionError: assert 0 == 1` | 1 | `test_the_shape_axis_is_anchored_by_one_start_and_one_end_marker`, from `text.count(SHAPE_START) == 1` |
| `ValueError: substring not found` | 1 | `test_the_shape_axis_sits_between_scope_determination_and_template_selection`, from `text.index(SHAPE_START)` |

Two corrections landed here, both from re-running rather than re-reading. The
first draft recorded all seven as `IndexError`, which was wrong about the two
whole-file tests — exactly the pair discharging AC-0089. The second was owed
when `_region()` gained a guard that refuses a missing marker before slicing:
the five region tests then fail that guard's `AssertionError`, and no
`IndexError` occurs at all.

**Green.** `python3 -m pytest packs/architect/tests/skills/architect-design/ -q`
→ 149 passed, comprising the 142 pre-existing tests and the 7 new ones.
`packs/architect/tests/pack/` → 31 passed, 72 subtests, unchanged.
`tools/add-rendering-directives.py --check` reports no drift for this skill.

**Independent verification by the controller.** Markers appear exactly once
each and in order; the five literals AC-0084, AC-0085, AC-0087 and AC-0088 pin
are present in the marker-delimited slice; the skill description parses at 849
characters, unchanged; the managed output-rendering block is intact; and only
the two files T1's `Touches` names were modified.

## Router state during the probe's control arm — 2026-09-20

`SKILL.md` was returned to its state at commit
`7c794b79341313f8b6832d36db5df5ef4e27114d` for the duration of arm C's
authoring so the control arm saw the pre-axis router, then restored to the
with-region working state. The restored file's SHA-256 equalled the digest
taken before the checkout (`604962f3…`, which is **not** the delivered digest —
the region was edited afterwards; `notes/probe/method.md` records what
changed), and the architect-design suite returned to 149 passed. `notes/probe/method.md` holds the full method.

## Approval taken without a confirming review round — 2026-09-20

**Deviation, recorded because it is one.** The final review round returned two
blockers and three concerns; all five were repaired and each repair was
verified mechanically — the red re-derived by re-running against a
region-stripped `SKILL.md`, the payload re-materialised and re-linted, the
merge-base command corrected to read `git merge-base HEAD origin/main` rather
than `origin/main`'s tip, and the receipt name reconciled against the skill's
own convention at `SKILL.md:106`. No reviewer saw those five repairs.

The scope owner directed that the build proceed on that basis. `reviewers-clean`
was therefore fired on repairs the loop verified but no reviewer confirmed, and
the round count stands at roughly twenty-three across the authoring effort.

**What happened next, which settles it.** Review did resume after this point,
so the gap is bounded rather than open. Two reviewers then read the
implementation and returned thirteen findings, three of them defects in
shipped behaviour — recorded in the next section with the mutation evidence
that fixed them. The base rate held: writing a claim instead of running it was
the defect class again. Later rounds found the same class in this ledger's own
prose, not in the code.


## Post-review repair round — 2026-09-20

Two reviewers read the implementation after the final wave. Thirteen findings
between them; the three that were defects in shipped behaviour rather than in
its description:

**`_region()` could be satisfied by its own anchor comment.** `SHAPE_START` is
an unterminated prefix, so the sliced span opened inside the marker's
explanatory comment and every content token was checkable against prose that
ships no routing instruction. The helper now drops through that comment's own
`-->`.

**The rules survived their own negation.** All five content assertions were
substring presence, so `never record \`no shape lens selected\`` passed a test
whose criterion it violates. They are now contiguous phrases. Five mutations,
each reding exactly one test: negate whole-loading, negate the receipt, negate
the trigger, remove the multi-shape rule, remove the descent path.

**The eval's path check pointed at the wrong tree.** `CONCEPTS` resolved
against the source corpus while the skill descends the projection, and the two
differ by the index file this axis cites. Both are now checked.

**Mutation evidence, every row re-derived by running the mutation.** An
earlier draft of this section claimed region deletion "reds all nine tests".
It does not, and that claim was the same defect class this ledger names as the
base rate — written rather than run.

| Mutation | Result |
| --- | --- |
| shape-axis region deleted | 7 failed, 2 passed |
| end marker deleted alone | 7 failed, 2 passed |
| whole-load rule negated | 1 failed, 8 passed |
| receipt rule negated | 1 failed, 8 passed |
| selection trigger negated | 1 failed, 8 passed |
| multi-shape rule removed | 1 failed, 8 passed |
| descent path removed | 1 failed, 8 passed |
| shape stem inlined in the skill | 1 failed, 8 passed |
| index title inlined in the skill | 1 failed, 8 passed |
| eval case 13 deleted | 1 failed, 8 passed |

Two of the nine cannot red on a region mutation, by construction, and that is
correct rather than a gap: `test_the_eval_case_exercises_the_shape_axis` reads
`evals.json` and the two concept trees and never opens `SKILL.md`, and
`test_the_skill_does_not_enumerate_the_shape_names` asserts an absence, so
deleting the region can only make it pass. Each of the eight single-failure
rows reds exactly the one test that owns the rule it breaks.

**Final counts.** `make lint-ruff lint-mypy` clean over 148 source files.
`packs/architect/tests/skills/architect-design/` gives 151 passed;
`packs/architect/tests/ tests/conformance/test_pack_metadata.py
tools/test_build_site_routing.py tests/roster/test_verification_ledger_contract.py`
gives 409 passed, 1 skipped, 72 subtests. `FORCE=1 make build-self` exits 0
with no further regeneration.

**Deviations from T1's and T2's pinned payloads, recorded here.** The basis is
narrower than "the plan is sealed" — `state.json` shows `approved_plan_hash`
and `approved_spec_hash` both null and the plan at `Drafting`, because the
amendment cleared them. What pins T1, T2 and T6 is
`completed_task_section_hashes`: those three sections still match byte-for-byte,
so editing them would be refused as `completed task section changed`. The spec
and T5 carry no such pin and remain editable in place. T2's
pinned block used `CONCEPTS = PACK_ROOT / "okf" / ...` and selected its case by
scanning for a substring; the shipped test resolves against both the source
and projected trees and selects by id, after review found the substring scan
could re-point at the wrong case and the single tree could pass on an
unopenable path. T1's entry named seven functions; the shipped suite carries
nine, the two additions being the AC-0090 assertion T2 owns and the
no-enumeration guard review asked for. No criterion changed.


## The frozen plan's `## Risks` carries a superseded word — 2026-09-20

`plan.md`'s first Risks bullet says "S2 and S3 stay ungated". That reverses
the fact. The probe returned no verdict, so the condition `S2` and `S3` are
conditional on is **unmet, not lifted**: both stay gated and neither is
contracted. Review round 12 found the wording at three sites; the two live
homes — `docs/product/intents/architect-design-conditional-overlays.md` and
this spec's `workspace.toml` entry — were corrected and say "stay gated".

The plan's copy was corrected too, and then restored, because correcting it
breaks a pin. `## Risks` sits inside T6's `completed_task_section_hashes`
span: `walk_task_sections` ends the last task section at end of file, so
`## Rollout`, `## Risks` and `## Changelog` are all pinned bytes of T6.
Editing any of them returns `completed task section changed: T6` from
`validate_completed_task_sections`, and clearing that needs a
`contract-amendment` — a second approval cycle for one adjective in a
non-owning copy. The intent owns the `S2`/`S3` gating, per this spec's
`## Follow-ons`, so this note is the correction's home and the plan's word
stays as approved.

## Two gates were red, and why one shaped the code — 2026-09-20

**This section no longer enumerates which CI gates this change triggers.**
Four review rounds each found one more, and two of those were red when found.
The enumeration cannot be kept true from `paths:` blocks, so pushing and
watching the checks is the answer and a list here is not.

Two reds are named because the repair is not obvious from the diff.

`tools/lint-pack-test-boundary.py` exited 1 on `(CONCEPTS / p)` and
`(PROJECTED / p)`: it reads a `Path` joined to a variable segment as a pack
test reaching above its own pack, whatever the anchor. The repair builds
`system-shapes/<name>.md` sets from constant-anchored globs and tests
membership — the awkward form at
`packs/architect/tests/skills/architect-design/test_shape_axis_routing.py`
exists for this reason, and simplifying the join re-creates the red. It now
exits 0.

`tests/roster/test_workspace_status_projection.py` failed on
`impossible_transition | active spec status`: the spec was registered in
`work.active` while its Status read `Draft`, after `contract-amendment` reset
the Status and the registration was not moved back. The entry is in `queue`
again and the suite gives 25 passed.

**Local green, measured.** `packs/architect/tests/` inside a full
`tests/` run: 2,049 passed, 6 skipped, 128 subtests, 349s.

## T5 executed ahead of its gate, and AC-0094's merge-base observation

**Deviation, recorded for the same reason T1's is.** T5's four artifacts —
`pack.toml`, `plugin.json`, `.claude-plugin/marketplace.json` and
`docs/product/changelog.md` — are in the tree while `state.json` lists
`completed_task_ids` as T1, T2 and T6 only, and the engine sits at
`SPEC-PLAN-REVIEW`. T5's wave was the current one before the amendment — the pre-amendment
snapshot shows `current_wave_index: 2` — and the amendment cycle then returned
the run to drafting. `dispatch_receipts` is now empty and no snapshot ever
listed T5 as completed, so the engine holds no receipt for it: the work is
done and verified, its record in the state machine is not.

**AC-0094's increment, observed by hand because nothing gates it.**
`tests/conformance/test_pack_metadata.py` decides only that the two files
agree, and `tools/repo/check_release_impact.py` covers `packages/agentbundle/`
and `contracts/`, not `packs/`. Read against merge base `8bc651b6fcd1`:

| File | At merge base | In the tree |
| --- | --- | --- |
| `packs/architect/pack.toml` | `0.15.13` | `0.15.14` |
| `packs/architect/.claude-plugin/plugin.json` | `0.15.13` | `0.15.14` |
| `.claude-plugin/marketplace.json` (architect) | `0.15.13` | `0.15.14` |

One patch above the merge base on both version files, with the marketplace
entry regenerated to agree. That is the whole of AC-0094's second conjunct,
and this table is the only place it is recorded.

**The bump was 0.15.13 and became 0.15.14 during the rebase.** This branch was
cut from `7c794b793413`, where architect stood at `0.15.12`, so the delivery
bumped to `0.15.13`. Main released its own `0.15.13` first, in
`63aad7ddd`'s line of work, and the collision surfaced as a changelog conflict
rather than as a failing gate — nothing compares a branch's bump against the
remote before the merge. Both version files, the marketplace entry and the
changelog heading moved to `0.15.14`, and main's `0.15.13` section was kept
below the new one.


## T6 — the ADR erratum, observed 2026-09-20

AC-0099 and AC-0101 are goal-based checks, so a recorded observation is their
only verification artifact. T1, T2 and T5 each had a section here; this one
was missing.

**AC-0099 — the erratum exists and is dated.** `docs/adr/0118-...md` carries a
`## Errata` section whose entry is dated 2026-09-20 and names the
open-decision trigger, the whole-load rule, and the receipt value.

**AC-0101 — the tokens match the shipped region.** Compared literal by
literal between the erratum and the shape-axis region of
`packs/architect/.apm/skills/architect-design/SKILL.md`:

| Token | In the erratum | In the region |
| --- | --- | --- |
| `open decision` | yes | yes |
| `loads whole` | yes | yes |
| `no tier selection` | yes | yes |
| `no shape lens selected` | yes | yes |

**One row was false when first written, and the region was reflowed to make
it true.** `loads whole` was split across a line break in the skill
(`loads` ending line 219, `whole` opening line 220), so the literal token
AC-0101 requires was not in the bytes. The construction suite did not catch
it: `_region()` collapses whitespace before matching. Re-measured after the
reflow with `rg -c -F`, each of the four tokens now appears in both files —
`open decision` 4 times in the skill and twice in the ADR, the other three
once in each.

**The shape lint stays green.**
`python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr` reports
`read: 119  refused: 0  unreadable: 0`, so the append did not break the
record's pinned shape. ADR-0118's Decision section, its `D1`–`D6`, and its
`Status: Accepted` are untouched.

**Expected CI warning.** `docs.yml`'s `check-adr-immutability` warns on a body
edit to an ADR that was Accepted on the base branch. It is non-blocking —
"warns but always exits 0 — reviewers make the call" — and an erratum append
is the sanctioned route, which `docs/adr/0027-adr-format-is-madr-aligned-but-lean.md`
demonstrates. The pull request states this.
