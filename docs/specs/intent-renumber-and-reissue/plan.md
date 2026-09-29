# Plan: Intent renumber, reissue, and the tombstone

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Approach

Two pure-function modules beside the allocator they sit with, one re-run of an
existing test, and two documents in the places their readers already look:

| Artifact | Destination | Task |
| --- | --- | --- |
| Request validation module | `packs/core/.apm/skills/work-intake/scripts/` | T1 |
| Tombstone read/write module | `packs/core/.apm/skills/work-intake/scripts/` | T2 |
| Allocator property re-run (no new module) | `packs/core/tests/skills/work-intake/test_intent_ordinal.py` | T3 |
| Tombstone-convention ADR | `docs/adr/` | T4 |
| `Tombstone:` field reference | `guides/product-engineering/reference/intent-fields-and-modes.md` | T4 |
| Measurement record | `notes/verification-ledger.md` | T3 |

Nothing here writes to the repository outside its own tests: request
validation answers a question, the tombstone reader and writer round-trip a
file's bytes, and the allocator property is a corpus read. The operation that
composes them into a transaction is
[`intent-rename-transaction`](../intent-rename-transaction/spec.md), and the
absence of a transaction here is deliberate — it is what makes this slice
buildable without one.

Order of work: the request contract first, because it gates everything and
needs no filesystem writes; then the tombstone shape, which the sibling corpus
lint already reads; then the allocator property, which is a re-run rather than
new coverage; then the ADR, which the sibling slice's tombstone writing
depends on.

T1 and T2 are TDD. T3 re-runs coverage that already exists and authors none.
T4 is a goal-based check, because neither document it produces is executable.
Each task's `Tests:` block names its own mode and the file that carries it.

Fixtures are whole miniature corpora in `tmp_path`, never the real
`docs/product/intents/`, because a test that writes there would race the other
sessions working in this worktree. A fixture corpus includes its own
`workspace.toml` and, where a task needs one, its own Git working tree, so
"pure function over fixture bytes" stays true of the module under test rather
than of the fixture that feeds it.

## Constraints

- **ADR-0033 D2** keeps `Level` an open set. Nothing here validates a `Level`
  value; the target token comes from the request and is checked against
  `NAMESPACE_TOKENS`, not against `Level`.
- **ADR-0098 D2** makes `intake-intent` the owner of admission. Nothing here is
  admission and nothing here touches the admission transaction.
- **`docs/specs/intent-metadata-shape-contract/spec.md`** owns the corpus lint.
  Its corpus-lint routing-and-validation criterion — cited by name and path,
  because a bare criterion number resolves against this spec's own criteria —
  routes by this spec's AC-0006 and validates the tombstone branch against
  AC-0005. Those two criteria are load-bearing for that spec's live
  implementation: do not change either without telling its owner.
- **T2 reuses the existing tombstone vocabulary rather than restating it.**
  `intent_corpus_lint.py`, in this same skill's `scripts/`, already owns the
  field vocabulary and the structural read: `TOMBSTONE_PARTITION_FIELD`,
  `TOMBSTONE_REQUIRED`, `TOMBSTONE_EDGES` and `TOMBSTONE_FIELD_COUNT` at lines
  40-43, `_validate_tombstone` at line 123, and `_is_tombstone` at line 162.
  T2 imports those constants and reads preambles through the shared
  `intent_shape.read_preamble`, so the field set has one canonical home.
  What T2 adds is what no module implements: a writer, and the three
  value-shape rules — the ISO 8601 date, the confined `Reissued as:` path, and
  the non-empty `Retired:` line. Verified absent before deciding this: that
  module has no date parsing and no path validation of any kind. The lint is
  not refactored to depend on T2, because it ships inside a Shipped sibling's
  gate and this slice has no outcome that needs it moved.
- **Path resolution reuses `resolve_confined_target`**
  (`packs/core/.apm/skills/work-intake/scripts/intake_transaction.py:144-165`),
  in this same skill's `scripts/`. It already does repository-relative
  canonicalise-then-verify-descendant, rejecting absolute paths, backslashes
  and dot segments. T1 uses it rather than hand-rolling a resolver.
- **The repository root is established by rule**, not by the caller's working
  directory: the `git rev-parse --show-toplevel` of the invocation, refused
  when absent.
- **AC-0027's ADR gates the sibling slice, not this one's other tasks.** T4
  authorises applying ADR-0108 D3's non-reuse rule to intent filenames, which
  the transaction slice's tombstone writing rests on.
- `work-intake` declares `Read Write Edit Bash`. No tool surface widens.

## Construction tests

**Integration tests:** none. No task composes two modules, and the end-to-end
path belongs to the sibling slice.

Two T1 cases read state outside the module under test — a working tree
carrying an uncommitted change, and the repository root resolved from
`git rev-parse --show-toplevel` rather than the working directory. Both stay
unit tests: each builds its own Git working tree under `tmp_path`, so the
module is still called directly and still returns a value rather than writing
one. They are named here because "pure function over fixture bytes" would
otherwise read as a promise that no task touches Git at all.

**Manual verification:** none. The operator how-to belongs to the sibling
slice, because there is no operation to follow here yet.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/adr/` | T4 | An Accepted ADR stating the tombstone convention and the two rejected name shapes | The ADR exists and `spec.md` cites it in `Constrained by:` |
| Interface compatibility — `guides/product-engineering/reference/intent-fields-and-modes.md` | T4 | The `Tombstone:` row and its three-field contract beside the existing intent fields | The page describes the field an adopter will see |
| Reusable learning — `notes/verification-ledger.md` | T3 | The tombstone-filename-shape measurement AC-0004 rests on, cited to its 2026-09-21 record in `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md` rather than re-measured | The ledger records the measurement AC-0004 rests on |
| Release history — `docs/product/changelog.md` | T1, T2 | One core entry naming the released version, under the version pair `tools/check-core-release.py` verifies | The entry is present under the released version |

## Design (LLD)

### Data & schema

A tombstone is a Markdown file whose preamble fields, their permitted values,
and the rule that exactly one pointer field appears are held canonically by
`spec.md` at AC-0005 and AC-0015 through AC-0017. They are not restated here:
the sibling corpus lint reads those criteria directly, so a second copy in this
plan could drift from the text the shipped lint enforces.

What this section owns is construction the criteria do not carry.

The date is a value the caller supplies, sampled once when a transaction opens.
Sampling it here would put a clock inside a pure function and would let an
operation spanning midnight write two dates.

This slice writes no tombstone into the live corpus. It contracts and
round-trips the shape; the operation that produces one is the transaction
slice.

Owned by: T2

### Interfaces & contracts

Three callables, each total and side-effect free: validate a rename request and
return either the resolved request or one fixed refusal token; serialise and
parse a tombstone; and report the allocator's next ordinal for a token over a
given corpus, counting tombstones alongside live intents.

Refusal tokens, each fixed: `root-unresolved`, `source-missing`,
`source-outside-root`, `source-not-regular`, `source-unreadable`,
`source-tombstone`, `source-unregistered`, `registry-unparseable`,
`registry-ambiguous`, `token-unknown`, `path-dirty`.

Every token here is one this slice's validator can decide from the request and
the corpus as they stand. `target-occupied` and `allocator-refused` are not in
the list: both are knowable only once an ordinal has been issued and a
successor name computed, which is applying a rename rather than validating a
request. They belong to
[`intent-rename-transaction`](../intent-rename-transaction/spec.md), which maps
this vocabulary without re-deriving it.

Owned by: T1, T2, T3

### Behavior & rules

**Liveness is established, not inferred from an absence.** AC-0006 makes a
file in `docs/product/intents/` a tombstone if and only if its preamble
carries `Tombstone:`. Read naively that is one field test, and it fails open:
`intent_shape.read_preamble` does not raise on content it cannot interpret, it
returns no pairs, so a source whose preamble is unreadable or unparseable
carries no `Tombstone:` field and reads as live. That is the one reading this
validator must not take — it would let a retired name through the
`source-tombstone` refusal that exists to stop ADR-0108 D3 re-issue.

So the validator refuses unless it positively establishes which side of the
partition the source falls on, and "the preamble parsed to something" is not
that. `read_preamble` skips a line it cannot match rather than failing on it,
so a source carrying a well-formed `- **Slug:** …` beside a damaged
`Tombstone:` marker returns fields, shows no `Tombstone:`, and would resolve
live — the same fail-open one step further in. Refusing only the empty
preamble does not close it.

Strictness is therefore scoped to the marker that decides the partition,
not to the whole preamble. Demanding that every preamble line parse would
refuse every real intent: measured over `docs/product/intents/` on
2026-09-28, all 157 open with an H1 title the field grammar cannot match,
and some also carry annotation bullets and blockquotes before the first
`## ` heading, none of which `read_preamble` accepts. The corpus simply is
not whole-preamble conformant, and the shipped corpus lint reads it
best-effort for that reason.

A source refuses `source-unreadable` when any of these holds:

- its bytes do not decode;
- its preamble yields no parsed field at all;
- a visible preamble line, after HTML comments are discarded, contains the
  token `Tombstone` case-insensitively yet does not parse as a well-formed
  `Tombstone:` field — a damaged marker, which the validator may not read as
  prose;
- a `Reissued as:` or `Retired:` field parses while `Tombstone:` does not.
  Those fields exist only on a tombstone, so this is a structurally
  impossible live intent. It is a parsed-field test rather than a text scan,
  so it cannot misfire on prose, and it catches a marker damaged in its own
  name — `Tombstome:` parses as a field, puts no `Tombstone` token on any
  line, and the near-miss rule alone would read it live.

Every other unmatched line — the H1 title, blanks, comment-only lines,
non-field bullets — is exempt and refuses nothing. A source is live when at
least one field parses, no `Tombstone:` field parses, no unparsed line bears
the token, and no pointer field stands alone. A parsed `Tombstone:` refuses
`source-tombstone`.

Two scans on 2026-09-28 fixed the cost of both text-sensitive rules at zero:
no live preamble in the corpus mentions `Tombstone` outside a well-formed
field, and none parses a pointer field without one.

**A source that is not a regular file refuses.** An in-root symlink passes
`source-outside-root`, so without `source-not-regular` a later reader would
follow it.

**An unresolvable repository root refuses.** The root is the
`git rev-parse --show-toplevel` of the invocation, never the caller's working
directory. When that call fails or returns nothing, the validator has no
boundary to confine against and refuses `root-unresolved` before reading
anything.

Owned by: T1, T2

### Design decisions

- **Refusal tokens over exceptions.** One fixed token per class, matching the
  discipline `intent_ordinal.py` already states for itself, so the transaction
  slice can map each to an operator diagnostic without re-deriving the set.
- **No clock and no filesystem writes in this slice.** It is what lets every
  task here be a pure-function test, and it is why the slice is buildable while
  the transaction is still being designed.

Owned by: T1, T2

## Tasks

### T1 — Every invalid request refuses with its own token

**Mode:** TDD. **Artifact:** a new
`packs/core/tests/skills/work-intake/test_intent_rename_request.py`, beside the
other `work-intake` script suites, exercising the module directly at the
validate-a-request boundary.

**Tests:** One refusing case per clause, each asserting the fixed token: absent
source; source outside `docs/product/intents/`; source that is a symlink out of
the root; source that exists but is not a regular file, including an in-root
symlink, which `source-outside-root` does not catch; source that is a tombstone
rather than a live intent; token outside `NAMESPACE_TOKENS`; source with no
`workspace.toml` entry; a `workspace.toml` that does not parse; a
`workspace.toml` carrying two entries for the source; and a path the request
names carrying an uncommitted change.

Four cases pin the fail-closed direction the `Behavior & rules` section fixes,
because each is a state a naive reading resolves to "live" rather than to a
refusal. A source that is a regular file inside the root whose bytes do not
decode, and one whose preamble yields no parseable field at all, each refuse
`source-unreadable`. A third carries a well-formed `- **Slug:** …` line beside
a malformed `Tombstone:` marker — it parses to a non-empty field list holding
no `Tombstone:`, which is precisely the shape that reads as live under a
best-effort parse, and it must refuse `source-unreadable`. None of the three
may return a resolved request. A fourth asserts that an invocation whose
repository root does not resolve refuses `root-unresolved` before any read.

Two more cases guard the opposite failure, over-strictness, which the first
attempt at this rule had: a positive fixture whose preamble is copied from a
real corpus file — H1 title, annotation bullet and all — must pass, and a
source carrying `- **Reissued as:** …` with its `Tombstone:` marker damaged
in the field name itself must refuse. The first fails if the rule reaches
past the partition marker; the second fails if it keys only on the literal
token.

A positive case asserts a fully valid request passes, so the suite cannot be
satisfied by refusing everything. One case invokes validation from a
subdirectory and asserts the repository root resolves to the `git rev-parse`
toplevel rather than the working directory. Covers AC-0021 and AC-0020.

**Approach:** Resolve through `resolve_confined_target`. Establish liveness
positively, per `Behavior & rules`: a preamble that does not parse refuses
rather than reading as a live intent.

**Depends on:** none

### T2 — A tombstone round-trips its three fields and refuses every bad value

**Mode:** TDD. **Artifact:** a new
`packs/core/tests/skills/work-intake/test_tombstone_shape.py`, exercising the
serialise/parse pair directly at the round-trip boundary.

**Tests:** Write and re-read a tombstone; assert `Slug:` is byte-identical to
the source's, `Tombstone:` is the supplied date, and `Reissued as:` holds the
successor path. Rejecting cases: a non-ISO date, an absolute `Reissued as:`,
one resolving outside `docs/product/intents/`, an empty `Retired:`, both
pointer fields present, neither present, a fourth field. A date supplied either
side of midnight writes exactly what it was given. Covers AC-0005, AC-0015,
AC-0016, AC-0017, and AC-0006's biconditional on both arms.

**Depends on:** none

### T3 — The allocator's next ordinal clears every tombstone

**Mode:** goal-based check — this task authors no test, so TDD does not apply
and the global "T1 and T2 are TDD" does not reach it. **Artifact:** the
existing `test_tombstone_filename_shapes_pin_allocation_and_check` in
`packs/core/tests/skills/work-intake/test_intent_ordinal.py`, re-run rather
than re-authored. **Done when:** that test passes in the work-intake suite.

**Tests:** For every token in `NAMESPACE_TOKENS`, the next ordinal exceeds
every ordinal that token carries in the corpus, tombstones counted alongside
live intents. Re-runs `test_tombstone_filename_shapes_pin_allocation_and_check`
in `packs/core/tests/skills/work-intake/test_intent_ordinal.py` — committed
87768ba4d, six shapes, green — rather than re-authoring it. Covers AC-0004.

**Depends on:** none

### T4 — The convention is recorded where an adopter and a maintainer each find it

**Mode:** goal-based check. **Artifact:** none executable — the two documents
are read directly, because neither an ADR nor a reference page runs.

**Tests:** Goal-based. The ADR exists, is `Accepted`, and `spec.md` cites it in
`Constrained by:`, which is AC-0027; `intent-fields-and-modes.md` documents
`Tombstone:` and its three-field contract. Both are checked by reading the
files, because neither is executable.

**Approach:** The ADR states the tombstone convention and records the two
rejected name shapes from the 2026-09-21 measurement. That measurement tried
six candidate names: two keep the `<TYPE>-NNNN-<slug>.md` shape and allocate
correctly, three refuse the whole directory, and one — a `tombstone-` prefix
that leaves the namespace — silently frees the ordinal. The ADR records the
two rejected categories, and the silent one is the shape to name first,
because the refusing three fail visibly and it does not.

**Depends on:** T2

## Changelog

- 2026-09-21 — drafted.
- 2026-09-28 — spec approved by eugenelim after the spec-mode adversarial
  review that `new-spec` step 7 requires, which had never run on this slice.
  Nine rounds, findings 11 → 1 → 0 → 1 → 1 → 0 → 1 → 2 → 0, each report
  persisted, validated and independently adjudicated under
  `.context/reviews/3eabe26e-3ed2-432c-a3a8-e83f0b17d776/`.
- 2026-09-28 — plan approved by eugenelim.
- 2026-09-28 — the transaction was cut into
  [`intent-rename-transaction`](../intent-rename-transaction/spec.md), taking
  twelve criteria and four tasks with it. A spec-stage security pass sustained
  ten findings against the transaction design, four more against the repairs to
  those, and six more against the repairs to those; a spike then measured the
  failure modes and confirmed the difficulty was structural rather than
  editorial. What remains here — the request contract, the tombstone shape, the
  allocator property and the ADR — was untouched by every one of those findings
  and is buildable without a transaction.
- 2026-09-28 — repaired five findings the pre-EXECUTE adversarial review
  sustained over the reduced pair, all of them artefacts of the cut: the
  Approach inventory and the per-task verification modes now name the artifacts
  and destinations the four tasks actually own; the Construction-tests note no
  longer promises that no task touches Git; the LLD stops restating the
  tombstone schema the criteria hold canonically; and the Durable Outputs table
  drops the two rows the transaction took, corrects the release destination to
  `docs/product/changelog.md`, and agrees with the plan's map. Three further
  findings were refuted on the evidence. Round 4, adjudicated under
  `.context/reviews/63804b99-bb0f-4f30-8405-0345af393fa0/`.
- 2026-09-28 — closed a fail-open a spec-stage security pass sustained as a
  Blocker. Liveness was specified as one field read, and
  `intent_shape.read_preamble` returns no pairs rather than raising on content
  it cannot interpret, so a source with an unreadable or unparseable preamble
  carried no `Tombstone:` field and read as live — passing straight through the
  `source-tombstone` refusal that exists to stop re-issue against a retired
  name. Liveness is now established positively, `source-unreadable` and
  `root-unresolved` join the token list with a T1 case each, and
  `target-occupied` and `allocator-refused` leave it for the sibling slice,
  which is the only place either is decidable. The same round recorded why T2
  adds a tombstone module beside an existing parser, moved T3 onto a permitted
  verification mode, and narrowed the reusable-learning evidence to the
  measurement a remaining criterion actually rests on. Rounds 5 and 6, five
  sustained findings, four refuted — two of those because they restated
  round-4 refutations on unchanged text.
- 2026-09-28 — corrected T4's count of the 2026-09-21 measurement. It said
  four candidate names refuse the directory; the measurement records three,
  alongside two that allocate correctly and one that silently frees the
  ordinal. The number reached no gate — it sits in `Approach:`, which the plan
  template marks working material — but it is the instruction for what T4's
  ADR must record, so an uncorrected count would have been copied into a
  governance document. Round 7 raised it and its adjudication could not settle
  it, because the measurement lives in another spec's ledger that was not
  supplied to the adjudicator; the count was then read directly from
  `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md`.
  Round 7's other seven findings were all refuted, six as restatements of
  earlier refutations on unchanged text.
- 2026-09-28 — split the spec's `## Retired identifiers` preface into the two
  groups it actually introduces. It read "These twelve were authored here and
  moved", above a single list of seventeen: twelve that moved to the sibling
  and five retired earlier for their own reasons. The lint reads the entry
  lines rather than the preface, so nothing red, but the sentence disagreed
  with its own enumeration. Both group memberships are now named. Round 8,
  one sustained Nit; its other six findings were refuted, four of them third
  or fourth restatements of earlier refutations on unchanged text.
- 2026-09-28 — a security confirmation pass re-run over the round-6 repair
  found it incomplete, and closed it properly. Refusing only the *empty*
  preamble left the fail-open reachable one step in: `read_preamble` skips a
  line it cannot match rather than failing, so a source carrying a good
  `- **Slug:** …` beside a damaged `Tombstone:` marker returned fields,
  showed no `Tombstone:`, and still resolved live. Measured against the real
  parser, three separate malformations of that marker each did so. Liveness
  now requires the whole preamble to parse — every non-blank visible line
  before the first `## ` heading must match the field grammar, and any line
  the parser would skip refuses — which also catches a damaged marker in any
  other field. The three fail-closed cases and the root-resolution case moved
  into the contract-tier Testing Strategy, because the previous repair had
  stated them only in this plan, which no completion gate reads. Round 10:
  one Blocker, one Concern, none refuted. Five adversarial passes had run
  over the incomplete repair and reported clean on it; the lens that raised
  the finding was the one that caught it.
- 2026-09-28 — narrowed that repair, which had over-corrected. Requiring the
  whole preamble to parse was measured against the corpus and refused all
  157 live intents: every one opens with an H1 title the field grammar
  cannot match, and some carry annotation bullets and blockquotes too, so
  whole-preamble conformance is not a property the corpus has. Strictness is
  now scoped to the marker that decides the partition. A damaged `Tombstone:`
  marker refuses two ways — a line bearing the token that does not parse as
  the field, and a pointer field parsing while `Tombstone:` does not, which
  catches a marker damaged in its own name where the token test cannot see
  it. Two scans fixed the cost of both at zero on the real corpus. T1 gained
  a positive fixture taken from a real preamble and a damaged-field-name
  case, so the suite now fails on over-strictness as well as under. The same
  narrowing was made in the contract-tier Testing Strategy bullet, which had
  inherited the identical over-strict wording. Round 11: one Blocker, none
  refuted.
