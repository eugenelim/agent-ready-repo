# Plan: a brief's lifecycle is a closed contract, and a closed cut is declared

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `guides/_shared/reference/skill-script-conventions.md`
  (skills are self-contained; no cross-skill import), `packs/AGENTS.md` (version
  bump, self-host projection, no internal-governance citation in shipped pack
  content), `packs/AGENTS.local.md` (the release pipeline and where a pack entry
  lands), `tests/AGENTS.md` (what a new `tests/roster/` file owes)

## Approach

Three surfaces bound a preamble in this repository and they disagree.
`lint-spec-status.parse_status` strips comments, bounds at the first section
heading and skips ATX heading lines. `intent_shape.read_preamble` bounds at the
first heading only. `lint-brief-coverage.parse_brief_status` bounds nothing.
This plan builds one reader for the brief surface, so the new field and the
existing `Status:` read are bounded by the same code rather than by two rules
that drift.

The module lands in `author-delivery-brief/scripts/` rather than a shared
location because `lint-brief-coverage.py` is its only importer and skills must
be self-contained. `close-work` does not import it: its brief path is prose,
and the refusal it describes is the lint's.

## Constraints

- Standard library only, and no import from another skill's directory.
- No internal-governance citation anywhere under `packs/*/.apm/` — no
  acceptance-criterion identifier, no `docs/specs/…` path, no task id,
  including in eval JSON. `packs/*/tests/` and `tests/` are exempt.
- A new `tests/roster/` file owes three edits (`tests/AGENTS.md` § Roster steps):
  a named step in `.github/workflows/build-check.yml` **above** the bulk step,
  a matching `LOCAL("test-after-build-check")` entry in
  `tools/lint-ci-parity.py`'s `_LOCAL_STEP_DISPOSITION`, and an entry in
  `.workspace-prune-protected.toml` only when the test names a
  `docs/specs/<slug>` path as a literal. This plan's roster test names no such
  literal, so the third does not apply. Both edits landed. Measured 2026-09-26:
  `lint-ci-parity` exits 0 with or without the parity entry, at identical step
  counts, so the entry is a convention every sibling roster-owned step follows
  rather than a gate-enforced obligation. The earlier claim that it decides the
  gate was not measured.

## Construction tests

| Suite | Surface it drives | What it proves |
| --- | --- | --- |
| `packs/core/tests/skills/author-delivery-brief/test_brief_shape.py` (new) | `brief_shape.py` at the module boundary | The bounding rules, the value grammar, the full six-status coherence matrix, and the transition table over ordered pairs |
| `packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py` (exists, 22 subprocess CLI tests) | the lint's CLI | That the consumer refuses what the module refuses, with the exit code and message the spec requires |
| `tests/roster/test_brief_lifecycle_single_home.py` (new) | the source tree under `packs/*/.apm/` | AC-0019: no other `*.py` under `packs/*/.apm/` carries a literal directly enumerating all six tokens |

The third searches outside `packs/core/`, so it is a repository-level assertion
and belongs in `tests/roster/` per `tests/AGENTS.md`.

## Durable-output map

| Durable output | Task |
| --- | --- |
| `brief_shape.py` module docstring | T6 |
| `guides/core/reference/product-brief-fields.md` | T6 |
| `author-delivery-brief/SKILL.md` § Brief lifecycle | T6 |
| `docs/product/changelog.md` | T6 |
| `lint-brief-coverage.py` interface | T3 |

## Design (LLD)

### Design decisions

- **The bound is found in the same pass that handles comments**, and **AC-0006
  is what justifies it**, not AC-0003. Measured 2026-09-25 against
  `lint-spec-status.parse_status`: on a straddling comment with a live field
  after the `-->`, the two-pass order returns the live value — the same answer
  one pass gives, because stripping the comment also removes the heading inside
  it and the bound lands on the first surviving heading either way. The orders
  diverge only on an **unterminated** comment: `_HTML_COMMENT_RE` requires a
  closing `-->`, so a two-pass reader strips nothing and reads the field lines
  inside the open comment (measured: it returns `Shipped`), while a per-line
  tracker returns no fields at all. That is exactly what AC-0006 contracts, so
  AC-0006's fixture is the one that reds a two-pass implementation. The
  `lint-spec-status` Follow-on is a report about that lint, not this decision's
  evidence.
- **A heading inside a comment is not a heading.** It does not end the
  preamble, and AC-0001 says "first uncommented heading" so the pair agrees. The alternative — letting a commented-out `## ` close the bound —
  would make a live field below the comment read as absent, which is the silent
  miss the spec's first Agent Rule exists to prevent. AC-0003 fixes the
  direction so an implementer cannot choose the other one.
- **The transition table is data, not branching.** A frozen set of ordered
  pairs, so AC-0017 and AC-0018's partition of all 36 ordered pairs is enumerable and every
  illegal move is asserted rather than a chosen few.
- **The coherence matrix is pinned before the move, not after.** The shipped
  CLI suite's brief fixtures use only `Executing` and `Shipped`, so four of the
  six rows are unexercised today and "the existing suite still passes" would
  not detect a behaviour change in them.

### Data & schema

`Cut-closed:` is a preamble field on a brief, absent by default. Its value is
an ISO 8601 date followed by non-empty evidence text. The grammar is
reimplemented rather than imported, because cross-skill import is banned. The
spec's § Agent Rules › Always do carries the hand-lockstep obligation that
creates, and § Durable Outputs requires the function's own docstring to record
it.

### Component / module decomposition

`brief_shape.py` sits in `author-delivery-brief/scripts/` and exports the
bounded reader, one accessor per field it reads, the value rules, the status vocabulary, the coherence predicate and the
transition table. `extract_token` moves in with the reader and the lint loads it back for all
five of its call sites, including the two on the spec path (:113, :119).

**The load uses the `_load_sibling` form, not a bare import.**
`packs/AGENTS.md` § Writing pack tests bans putting a skill's `scripts/` on
`sys.path` and importing by bare name: skills are independent, several may ship
a same-named script, and a bare `import` binds whichever directory reached the
path first and caches it for every later importer. The production precedent is
`work-intake/scripts/intent_corpus_lint.py:58-75`, which builds the module with
`importlib.util.spec_from_file_location` on a script-relative path and
registers it as `core_work_intake_intent_shape`. This slice mirrors it as
`core_author_delivery_brief_brief_shape`. A bare import would also fail
outright when the lint is loaded in-process through `importlib` rather than run
as a script, which the existing subprocess-driven suite cannot see. `lint-brief-coverage.py` loads it by that form and defines
none of them.

### Failure, edge cases & resilience

Today the vocabulary check and the coherence predicate are one conjunction
emitting a single diagnostic (`lint-brief-coverage.py:293-295`). Splitting them
across AC-0010, AC-0011 and AC-0012 changes what a reader sees, so the message
text is part of the change rather than incidental to it. The absent-status case
currently reaches the hard list as a contradiction; AC-0011 makes it say the
status is absent.

### Dependencies & integration

No new dependency. `pack.toml` and `.claude-plugin/plugin.json` move together
from `2.26.41`; the level is **minor**, because a new gate that refuses a brief
adds behaviour an adopter must satisfy without breaking an existing field.
`packs/AGENTS.md` § Self-hosting projection requires `FORCE=1 make build-self`
after pack edits, regenerating the adapter copies and `marketplace.json`.

## Tasks

### T1: the bounded reader and the value grammar hold at the module boundary

**Depends on:** none

**Tests:**
- `test_brief_shape.py` covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0005 and
  AC-0006, one fixture pair per rule. AC-0002's comment sits wholly inside the
  preamble; AC-0003's opens in the preamble and closes after a `## ` line;
  AC-0006's never closes.
- AC-0008 and AC-0009 together: a malformed value refuses, a well-formed one
  does not, and an empty or comment-only value reads as absent. AC-0009 is the
  accepting twin, so a reader that refuses every value cannot pass this task.

**Touches:** packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py, packs/core/tests/skills/author-delivery-brief/test_brief_shape.py

**Approach:**
- `test_brief_shape.py` loads the module under a pack-and-skill-qualified name
  per `packs/AGENTS.md`, not by bare import. That yields a different module
  object from the one the lint's subprocess loads, which is correct and worth
  knowing: the two suites prove the module and the CLI separately.

**Done when:** those eight criteria are green at the module boundary and no
consumer has changed.

### T2: the state table, the declaration matrix and the transition table

**Depends on:** T1

**Tests:**
- AC-0010 as a set comparison against the exported frozenset, not a spelling of
  the six tokens in the test.
- AC-0011 and AC-0012 over all six states, pinning the matrix before any
  consumer moves. A child is a Spec-map row **or** a back-linking spec absent
  from the map; the fixture set includes a back-linked-only child, because that
  join is the behaviour the shipped comment protects.
- AC-0013, AC-0014, AC-0015 and AC-0016 as the twelve-cell declaration matrix.
- AC-0017 and AC-0018 over ordered pairs, enumerating all 30 two-different-state
  pairs plus the 6 self-pairs, so every cell of the 36 has a verdict.

**Approach:**
- The matrix is pinned here, before T3 removes the shipped predicate, so the
  move has an oracle independent of the code being moved.

**Touches:** packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py, packs/core/tests/skills/author-delivery-brief/test_brief_shape.py

**Done when:** all 36 ordered pairs and all twelve declaration cells are
asserted and green.

### T3: the lint reads through the module and defines nothing itself

**Depends on:** T2

**Tests:**
- **AC-0007, once per bounding rule and once per field.** Each of AC-0001
  through AC-0006's fixtures is driven through the lint's own entry point for
  `Status:`, `Cut-closed:` and `Slug:`, asserting the value the lint acts on
  matches that field's module accessor. Every fixture must be a differential,
  and the two rule shapes need opposite arrangements:

  *The five suppressing rules* — AC-0001, AC-0002, AC-0004, AC-0005, AC-0006 —
  place the field only where the bound must hide it, so bounded reports absent
  and unbounded reports a value. `Status:` reds bounded under AC-0011;
  `Cut-closed:` on a `Draft` brief accepts bounded and reds unbounded under
  AC-0016; `Slug:` carries a value **differing from the filename stem**, or the
  stem fallback masks the bound.

  *AC-0003 is the accepting rule* and inverts the arrangement: a decoy of the
  same field inside the straddling comment, and a **different** live value
  after the `-->`. Both parsers return their first match, so bounded returns
  the live value and unbounded returns the decoy. Equal values would make the
  arm pass against unrepaired code. Per field: `Status:` uses an
  out-of-vocabulary decoy token, so unbounded reds under AC-0010; `Cut-closed:`
  uses a state that **permits** the record and is child-coherent under
  AC-0012 — `Ready` with an empty Spec map, since `Executing` and `Cancelled`
  both require a child at `Implementing` or `Shipped` — with a malformed decoy
  and a well-formed live value, so bounded accepts and unbounded reds under AC-0008
  — a `Draft` brief cannot serve, since AC-0016 refuses on presence and both
  reads would red alike; `Slug:` uses different slugs, and the coverage line at
  `lint-brief-coverage.py:312` prints the joined value. The same fixture also
  separates a third wrong implementation — one that treats a commented `## ` as
  ending the preamble — which returns the field absent, distinct from both.
- AC-0025, AC-0026, AC-0027, AC-0028, AC-0029 and AC-0030 through the lint's
  entry point, each asserting the coherence verdict as well as the parse.
  AC-0026's fixtures cover both child-set arms — a back-linking spec, whose
  status still reaches the child set through the untracked arm, and a mapped
  spec with no back-link, which leaves it. AC-0030's fixture is the shipped
  annotation shape `| alpha | Shipped <!-- ... --> |`, and **the mapped spec's
  own Status must differ from the recorded token** — `Draft` against a
  recorded `Shipped`. Measured 2026-09-25: with the spec at `Shipped`, a
  correct implementation and one that destroys the cell both emit nothing,
  because `extract_token("")` returns `""` and `_UNSET_CELLS` exempts it, so
  the truncation half of the criterion cannot red. With the spec at `Draft` a
  correct implementation records `shipped`, drifts, and names the cell, while
  a cell-destroying one stays silent. Without the mismatch only the
  row-survives half of AC-0030 is falsifiable.
- **AC-0027's fixture is measured, not reasoned.** Two earlier attempts at it
  asserted the same verdict on both sides. The shape that discriminates, run
  against the reader on 2026-09-25:

  ```
  ## Spec map

  | Spec | Status |
  | --- | --- |
  | alpha | Shipped |            <- real spec, Status: Shipped, survives
  <!--
  ## Governance references
  -->
  | no-such-slug | <auto> |     <- no docs/specs/no-such-slug/spec.md
  ```

  Unrepaired the terminator fires, only `alpha` parses, `child_states` is
  `{"shipped"}` and the `Shipped` brief **validates and reports delivered**.
  Repaired both rows parse, `child_states` is `{"shipped", "missing"}`, and it
  is refused. Measured both sides.

  Three things make it work and each defeated an earlier attempt. The dropped
  row names a slug with **no** `docs/specs/<slug>/spec.md`, so the untracked
  arm cannot restore it — a back-linking spec would move from `mapped` into
  `untracked` and `child_states.update()` would put its status straight back,
  giving the same verdict either side. A live `Shipped` row **survives above**
  the comment, or the child set empties and `_brief_lifecycle_is_valid` refuses
  at the non-empty check instead, again the same verdict either side. The ghost row's recorded cell is **`<auto>`**, not `Shipped`: `_UNSET_CELLS`
  exempts it from the drift check, so the lifecycle refusal is the sole
  observable. With `Shipped` there, drift co-fires — `recorded_norm` is
  `shipped` while `actual` is `missing` — and a test asserting only the exit
  code cannot tell which rule produced it. And the
  comment is **multi-line**, with `## ` starting its own line: `:184` matches
  `^##\s+`, so a single-line `<!-- ## Governance references -->` begins with
  `<!--`, never reaches the terminator, and tests nothing.

- **AC-0024**, a source-absence search proving no second scan of any brief
  preamble field survives. AC-0024 reaches preamble fields only and declares
  one exception, `parse_spec`'s spec-side status scan; `parse_spec_map` falls
  outside that rule's scope entirely and has its own contract in AC-0025
  through AC-0030.
- `test_lint_brief_coverage.py` gains AC-0013's refusal, AC-0021's message
  assertions and AC-0022's exit code; its existing 22 cases pass with only the
  diagnostic-text changes § Failure, edge cases & resilience names.
- `tests/roster/test_brief_lifecycle_single_home.py` performs AC-0019's search
  over `*.py` under `packs/*/.apm/` and asserts the result set is exactly
  `brief_shape.py`. Measured 2026-09-25 by AST scan, the only match on the tree
  today is `lint-brief-coverage.py:62`, which T3 removes. The three nearby
  shapes in `workspace_status_engine.py` all fall outside the rule: the
  `brief_queue` tuple at :1492 is lowercase, the collection map at :3336-3343
  nests the tokens inside per-collection sets rather than enumerating them
  directly, and the derivation at :2696-2706 branches on single tokens. Those
  are worked examples, not contract — the criterion decides without them.
  Prose is out of scope, so no carve-out list has to stay in step with the
  tree and the test needs nothing from T6.

**Approach:**
- `parse_brief_status` and `parse_brief_slug` are both repaired here rather
  than in T1, so the bounded reader has a consumer before either unbounded read
  is removed. The slug read is the rollup's join key, so it is repaired rather
  than carved out.

**Touches:** packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py, packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py, tests/roster/test_brief_lifecycle_single_home.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Done when:** AC-0007 is green through the CLI, the six Spec-map criteria
are green including AC-0027's wrongly-passing case and AC-0030's preserved
annotation shape, the roster test is green, its
named step sits above the bulk step in `build-check.yml`, its
`_LOCAL_STEP_DISPOSITION` entry exists, and `python3 tools/lint-ci-parity.py`
exits 0.

### T4: the corpus satisfies the gate it is about to be governed by

**Depends on:** T3

**Tests:**
- AC-0020: the lint exits 0 against the real tree.

**Approach:**
- `tech-site-completion.md` is the only `Shipped` brief and carries no
  declaration, so the gate would refuse it on the first run. Its nine mapped
  specs are all `Shipped`, so the declaration records a fact rather than
  creating one. The value is `2026-08-25`, the closure date that brief's own
  § Spec map already states, with evidence text naming that section.

**Touches:** docs/product/briefs/tech-site-completion.md

**Done when:** AC-0020 is green, and `git diff --numstat` shows that brief
gained exactly one line.

### T5: a brief copied from the seed template is not refused

**Depends on:** T1

**Tests:**
- AC-0023: the template's preamble, copied verbatim into a new `Draft` brief,
  is refused by no rule this spec adds. The `Cut-closed:` row is present for a
  reader and absent to the parser, which is AC-0009's rule exercised through
  the artifact a maintainer actually copies.

**Touches:** packs/core/seeds/docs/product/briefs/_template.md, packs/core/tests/skills/author-delivery-brief/test_brief_shape.py

**Done when:** AC-0023 is green.

### T6: the durable outputs describe the shipped behaviour

**Depends on:** T4, T5

**Tests:**
- A content check that the module docstring's refusal registry equals the set of
  refusals the module raises — a set comparison, not a sentence-exists check.
- A check that the `brief_shape.py` docstring cites § The brief state table
  rather than restating it, and that the guide carries the derivation line.
- A read — not a test — confirming each mirrored function's docstring names its
  counterpart (`extract_token` against `lint-spec-status.extract_status_token`,
  the date-grammar check against `intent_shape._check_dated_evidence`) and that
  the module docstring names both exist. The mirrors are hand-held by design,
  so this read is the only thing that catches their absence.

**Approach:**
- The guide keeps its reader-facing tables — being the authoritative field list
  is that page's job — and gains a line naming `brief_shape.py` as what they are
  derived from. AC-0019 does not reach `guides/`, so the guide is a documented
  derivation rather than a competing definition.
- `close-work/SKILL.md` gains a sentence saying the refusal is the lint's. It is
  prose with no independent behaviour, so no criterion reaches it. The
  eval-harness update `packs/AGENTS.md` requires for a non-cosmetic pack change
  is carried here for both changed skills.

**Touches:** packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py, packs/core/.apm/skills/author-delivery-brief/SKILL.md, packs/core/.apm/skills/close-work/SKILL.md, packs/core/.apm/skills/close-work/evals/evals.json, packs/core/.apm/skills/author-delivery-brief/evals/evals.json, guides/core/reference/product-brief-fields.md, docs/product/changelog.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json

**Done when:** both version files read the same bumped minor version; the
changelog entry is free-standing at `##` with a `### Highlights` block; the
guide and `author-delivery-brief/SKILL.md` both cite `brief_shape.py`; both
eval harnesses are updated; the mirror read above is recorded; and a
**second** `FORCE=1 make build-self` run
produces no further change, the first having written the two new projected
copies of `brief_shape.py` under `.agents/` and `.claude/`, which are committed.

## Rollout

- **Delivery:** big bang within the pack. The gate newly refuses a `Shipped`
  brief with no declaration; the predicate that matters is *briefs whose status
  token is `Shipped` and which carry no `Cut-closed:` field*, and T4 empties it
  before T6 ships.
- **The Spec-map repair changes no verdict on today's tree.** Measured
  2026-09-25: no brief carries a comment inside a Spec-map section and no
  commented `## Spec map` heading exists anywhere, so AC-0020's real-tree run
  is unaffected and no backfill is owed. That is also what makes the
  terminator's verdict cheap to set now — nothing in the corpus depends on it
  yet.
- **Reversible:** yes — the refusal is one predicate and the field is additive.
- **Deployment sequencing:** T4 precedes T6, or the gate ships refusing the
  corpus. T3's roster test and its two CI edits land together.

## Risks

- **The move changes behaviour in a row the shipped suite never exercises.**
  Mitigated by T2 pinning all six rows, including a back-linked-only child, at
  the module boundary before T3 moves anything.
- **The reader is correct and nothing calls it.** This is the failure that
  would leave the headline defect in place while every module criterion passes;
  AC-0007 exists only to make it red.

## Changelog

- 2026-09-25 — drafted.
- 2026-09-25 — approved by eugenelim after both spec-stage reviews returned
  `Clean` over seventeen rounds. The cut confirmation for this slice is
  separate from the four-slice set confirmation, per ADR-0098 D6.
