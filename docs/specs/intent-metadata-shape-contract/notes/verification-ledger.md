# Measurement spike — 2026-09-21

## Question

Does applying every packet-decidable acceptance criterion to the 148 intents in
`docs/product/intents/` refuse any value the corpus legitimately carries, or
does it identify only migration work? The measurement read only the preamble
block: the run of `- **Field:**` lines before the first `## ` heading.

## Results

| Criterion | Refusals | Nature |
| --- | ---: | --- |
| AC-0001 missing `Owner:` | 143 | absent field |
| AC-0001 missing `Slug:` | 122 | absent field |
| AC-0001 missing `Level:` | 10 | absent field |
| AC-0001 missing `Status:` | 2 | absent field |
| AC-0009 retired name `Authority` | 54 occurrences across 45 files | needs rename to `Governed by:` |
| AC-0025 repeated preamble field | 8 files, every one `Authority` x2 or x3 | see below |
| AC-0009 `Type` / `Raised` / `Stage` / `Parent` / `Source` | 1 each | single-file drift |
| AC-0002 `Status` value | **0** | no legitimate value refused |
| AC-0022 `Kind` / `Scale` / `Maturity` values | **0** | no legitimate value refused |
| AC-0031 `Governed by:` form, applied to the 54 `Authority` values | **0** | no legitimate value refused |
| AC-0032 `Parent intent:` form, applied to all 31 values | **0** | no legitimate value refused |
| AC-0005 / AC-0006 progress fields | **0** | no intent carries one yet |

1. **No criterion refuses a value the corpus legitimately carries.** Every
   refusal is an absent field or a retired field name: migration work, not a
   contract defect.
2. **AC-0002 refused zero `Status` values even though two intents carry a
   `- **Status:** Run 2026-09-09; killed on …` line.** Those lines sit below the
   first `## ` heading, inside a de-risk record, so AC-0011's preamble-bounding
   rule excluded them. The measurement demonstrates the rule.

## Earlier measurements

These measurements predate the 2026-09-21 spike and were not re-run:

- The two writers diverge: core's `intake-intent` and product-engineering's
  `frame-intent` share exactly one preamble field, `Level:`.
- `Authority` has three distinct usages: a bolded preamble governance pointer;
  a bolded `## Source` owner attribution; and an unbolded `## Source`
  provenance token whose values are `repo-origin` (27) and
  `transferred-to-repository` (4).

# Execution observations — 2026-09-21

Recorded here rather than in `spec.md` or `plan.md`, both of which are pinned in
substance from their 2026-09-21 approval.

## The corpus moved under the plan

The branch was rebased onto `origin/main` (34 commits) before T1. The intent
corpus is now **150 files, all live, no tombstones** — 145 before the rebase and
148 at the measurement spike above. The five files upstream added
(`CAP-0005-work-item-capture-and-disposition.md`,
`FEAT-0006-work-item-capture-contract.md`,
`FEAT-0007-work-item-promotion-routing.md`,
`FEAT-0008-governance-item-record-routing.md`,
`FEAT-0009-duplicate-coverage-check.md`) each **omit `Owner:`**, so AC-0033 does
not hold on the rebased base and T10 carries a residual pass beyond commit
`e03205242`.

None of the five declares an owner anywhere — no `Owner:` field and no `## Owner`
section — and `workspace.toml` registers all five with no owner either. The
spec's Agent Rules forbid inferring the field from git authorship, so the value
was **declared by the owner (eugenelim) on 2026-09-21** rather than derived.
144 of the other 145 intents carry `eugenelim`; one carries
`Repository maintainers (ini-002)`.

## T1 verification, beyond the suite

Two checks that the 78 passing tests do not themselves establish:

1. **Agreement with the real corpus.** The validator refuses exactly 5 of the
   150 real intents, every refusal an absent `Owner:`, and refuses no value the
   corpus legitimately carries. This reproduces the spike's AC-0002 and AC-0022
   zero-refusal result against live values, and matches an independent ad-hoc
   measurement written before the validator existed.
2. **The ordering assertion can fail.** Reversing normalization to strip
   backticks before discarding the comment fails 10 tests — the direct
   `normalize_value` assertion plus every `backticked-and-commented` accept case
   across `Status`, `Superseded by`, `Kind`, `Scale` and `Maturity`. The
   composed-shape control is therefore not passing by construction.

## AC-0002's test shape departs from the plan's wording

T1's plan bullet asks that the `Status` vocabulary be "read from the same table
the implementation uses rather than a second literal list". Iterating a table
against itself cannot fail, so an implementation whose table gained or lost a
member would pass. The suite does both: accept cases iterate the implementation's
table, so a new member needs no test edit, and one assertion pins bare membership
literally, so a wrong table fails. This satisfies the plan's anti-drift intent
without leaving AC-0002 unfalsifiable.

## Gate coverage is narrower than `make lint-ruff lint-mypy` suggests

`tools/lint-mypy.py` is scoped to three typed packages and states that skill
scripts are not checked, so its green says nothing about
`packs/core/.apm/skills/work-intake/scripts/intent_shape.py`. `tools/lint-ruff.py`
runs `ruff check` at the repository root and does cover it. The new module was
additionally type-checked directly as a self-check (clean), which is not a gate.

## Obligations the plan does not state

- **`packs/AGENTS.md` version bump.** A non-cosmetic `.apm/**` change bumps
  matching versions in `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`. Upstream already advanced both during
  the rebase window, so the bump is taken once for this branch rather than per
  task, and must not borrow an unreleased version.
- **`packs/AGENTS.md` eval harness.** "A non-cosmetic pack update also updates
  that pack's eval harness." Agents carry no eval directory, so this misses T5
  and lands on T7, which touches `intake-intent` (which has one).
- **Projection drift predates this change.** `.claude/agents/shaping-reviewer.md`
  and `.claude/agents/adversarial-reviewer.md` both lack the 3-line
  `metadata: boundaries: [filesystem_read_untrusted]` block their `.apm/` sources
  carry; the other four core agents are clean. A self-host run during T5 sweeps
  in both files' drift, only one of which T5 authors.
- **T4's confinement needs the parity fallback.** The plan names
  `agentbundle.catalogue_tooling.file_safety` as the blessed helper. A shipped
  pack cannot assume `agentbundle` is importable, and
  `intake_guard.py:154` already establishes the pattern: import the helper, and
  on `ImportError` fall through to a portable parity path. T4 follows that
  rather than importing the helper bare.

## Pre-EXECUTE review was recorded not-warranted, not passed

The engine refused `spec-approved` directly from `SPEC-PLAN-REVIEW`, so the
already-recorded 2026-09-21 human approvals could not be registered without
leaving that state. No mandatory pre-EXECUTE reviewer is warranted: the spec's
Durable Outputs record that the lint "ships inside an existing skill's script
directory and adds no module boundary", the change adds no trust boundary
(reusing the existing confinement pattern over repository-local files), and the
design-intent pass is advisory in both modes. `reviewers-clean` was therefore
fired as a vacuous clean rather than an earned one.

Worth noting for a later run: the `reviewers-clean` edge out of
`SPEC-PLAN-REVIEW` carries **no guard** —
`_guard_check_spec_status_on_code_review` returns `None` unless the state is
`CODE-REVIEW` — so the engine would not have stopped an unearned clean here.

## T5's site list is correct, and two pins constrain it

The shaping reviewer carries four count-bearing sentences, but only three are
intent-mode condition counts (the intent-mode opener, the `MALFORMED(owner)`
suppression sentence, and the sentence under
`## Known failure modes in delivery-brief and spec mode`). The fourth, the
`six-predicate self-check` reference, counts `finding-adjudicator`'s predicates,
which AC-0030 does not reach; the plan correctly leaves it alone.

`packs/core/tests/pack/test_shaping_review_contract.py` pins both
`"six-predicate self-check"` and `"MALFORMED(owner)` is emitted alone"`, as well
as `"suppresses the other five"`. So the suppression rewrite must drop the
"other five" wording while preserving the "emitted alone" substring, and must
not strip the adjudicator's own count. Neither unpinned prose site is guarded by
any test.

## Concurrent session

A peer session held uncommitted work in this shared worktree and committed it as
`c8a82bd04` before the rebase, then revised the sibling spec further in
`be771c08f`. `docs/specs/intent-renumber-and-reissue/spec.md`'s AC-0005 and
AC-0006 — the two criteria AC-0017 cites — were verified byte-identical across
that second commit by hashing the AC-0005-to-AC-0007 span. That spec's AC-0006 is
now preamble-bounded, which agrees with AC-0011 rather than conflicting with it.

**Open, not owed to T1:** the spec's Follow-on asking which side owns the routing
obligation now contradicts the sibling spec, which records it as settled. The
sibling's AC-0006 is the partition rule; AC-0017 and AC-0028 own routing every
file and failing the gate. The Follow-on is working material and should become a
settled note, naming who settled it and on what ground, before this spec ships.

# Owner decisions — 2026-09-21

Recorded here so the controlled amendment has a stable authority reference. Each
was decided by the scope owner (eugenelim) in session on 2026-09-21.

1. **`Owner:` on the five unowned intents is `eugenelim`.** None of
   `CAP-0005`, `FEAT-0006`, `FEAT-0007`, `FEAT-0008` or `FEAT-0009` declared an
   owner in a preamble field, a body section, or its `workspace.toml`
   registration, and the spec's Agent Rules forbid deriving the field from git
   authorship. The owner declared the value rather than the migration inferring
   it.

2. **The `Level:` conflict is resolved by a new ADR superseding ADR-0098 D3 in
   part.** AC-0001 requires `Level:` on every live intent. ADR-0098 D3 states
   that "Product fields — level, opportunity, assumptions, scale, and JTBD —
   stay optional enrichment on a repository intent." The two cannot both hold:
   `intake-intent` writes to `docs/product/intents/<slug>.md`, the directory
   AC-0028's gate guards, and every existing `render_minimal_intent` call passes
   no `level`, so admission would produce an intent the gate rejects.

   The owner chose the superseding ADR over an erratum and over narrowing
   AC-0018. RFC-0102 fixes the instrument: an accepted record's body is frozen,
   status-only changes are the sole permitted edit, and "anything else is a
   *new* ADR that supersedes". An erratum records an error, and D3 was correct
   when written, so a decision change is not an erratum. ADR-0098's metadata
   block stays writable after acceptance by RFC-0102's prose/metadata split,
   which is what lets `Superseded in part` be added to it.

   This overrides the plan's T9 Approach sentence "No new ADR", which is why
   the change goes through the controlled amendment rather than in place.

## A cross-spec criterion citation resolves locally, and silently

`lint-contract-item-alignment.py` rule 4 (line 642) runs `CRITERION_REF`
(`\bAC-\d{4}\b`) over the **whole** text of `spec.md` and `plan.md`, subtracting
the live and retired identifiers of *that* spec directory. AC-0017 cites
"`docs/specs/intent-renumber-and-reissue/spec.md` AC-0006" and "that spec's
AC-0005". Both numbers also exist in this spec, meaning different things —
AC-0005 is the `De-risked:` / `Shaping-reviewed:` rule and AC-0006 is the
`Decomposed:` rule — so the lint resolves them to the local criteria and reports
nothing.

The run is clean (0 findings) for the wrong reason. A dangling reference would
be caught; a reference that resolves to the wrong criterion never will, and
ADR-0108 D1 scopes an identifier to its own spec directory, so a number crossing
a boundary has no addressing guarantee. The remedy is to cite the obligation by
name and the spec by path, dropping the number. No gate will catch a regression,
so the property to preserve is that a reader resolving a citation in its own
directory cannot get a coherent wrong answer.

# Release history rehomed to the existing convention — 2026-09-21

The spec's Release-history Durable Output named "each pack's `CHANGELOG.md`",
and no pack has one: the only `CHANGELOG.md` files in the repository are
`packages/agentbundle/`, `packages/credbroker/` and
`packages/jsonl-otlp-exporter/`. Building two new per-pack changelogs would
have invented a convention rather than followed one.

The existing convention is `docs/product/changelog.md`. Its own header states
the rules: an entry is owed in the same change that bumps a released artifact's
version; a released section is free-standing and directly beneath
`[Unreleased]`, written `## [<artifact>][<version>] — YYYY-MM-DD` at the top
level, newest first; a versioned entry nested under `[Unreleased]` is
permanently invisible to the `/now/` projection; and exactly one blank line
sits above and below every heading, which `tools/test_build_site_routing.py`
checks on any pull request into `main`. Both packs already release this way —
`## [core][2.26.28]` and `## [product-engineering][0.13.15]` are current
entries.

Rehomed on the owner's direction (2026-09-21). The Durable Outputs table is
working material under the spec's own contract note, so this is a correction in
place rather than an amendment.

**Still owed at T9:** that task's `Touches` field names the two non-existent
pack changelogs. `Touches` is a pinned plan field, so correcting it is
controlled-amendment work and is folded into T9 rather than taken as a second
amendment for one path. Nothing gates on `Touches` mechanically — `loop-cohort`
reads it only for a wave disjointness prediction it labels "never a greenlight",
and `explore-grounding` reads it as an exploration seed — so the pin is
substantive rather than enforced.

# T7's "unamended suite" is falsified by ADR-0121 — 2026-09-21

T7's `Tests` field requires that "the existing `intake-intent` admission suite
runs unamended and green, which is how the ADR-0098 D2 controls are evidenced
as preserved rather than re-specified." That is no longer achievable, and the
reason is the decision the owner took two steps earlier.

The suite pins precisely what ADR-0121 D3 changes:

- `packs/core/tests/skills/intake-intent/test_intake_intent.py:32` asserts
  `inspect.signature(renderer.render_minimal_intent).parameters["level"].default
  is None` — the optionality ADR-0121 D3 removes.
- The same file calls `render_minimal_intent(..., level=None)` at lines 54 and
  218, which must now be refused rather than rendered.
- `test_intake_intent.py:59` and
  `packs/core/tests/skills/work-intake/test_work_intake.py:223` both assert
  `"## Owner"` is a rendered heading, and the spec moves owner out of that
  section into a preamble field.

Five assertions across two files. The intent behind the field still holds — the
ADR-0098 D2 admission controls must be evidenced as preserved rather than
re-specified — but "unamended" is the wrong instrument for it now, because the
suite also pins two things this change is required to alter. The amendment
restates the obligation as: the confinement, provenance and authority-transfer
controls stay green and unedited, while the level-optionality and
`## Owner`-heading assertions move with the contract.

Also folded into this amendment: T9's `Touches` field still names
`packs/core/CHANGELOG.md` and `packs/product-engineering/CHANGELOG.md`, which
do not exist. The destination is `docs/product/changelog.md` per the owner's
direction, already corrected in the spec's Durable Outputs.
