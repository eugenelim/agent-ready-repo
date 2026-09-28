# Plan: Intent renumber, reissue, and the tombstone

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)

## Approach

Three pure-function modules and one document, all under
`packs/core/.apm/skills/work-intake/scripts/` beside the allocator they sit
with. Nothing here writes to the repository outside its own tests: request
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

Testing is TDD throughout except the ADR. Fixtures are whole miniature corpora
in `tmp_path`, never the real `docs/product/intents/`, because a test that
writes there would race the other sessions working in this worktree.

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

**Integration tests:** none. Every task here is a pure function over fixture
bytes or a document check; the end-to-end path belongs to the sibling slice.

**Manual verification:** none. The operator how-to belongs to the sibling
slice, because there is no operation to follow here yet.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/adr/` | T4 | An Accepted ADR stating the tombstone convention and the two rejected name shapes | The ADR exists and `spec.md` cites it in `Constrained by:` |
| Interface compatibility — `guides/product-engineering/reference/intent-fields-and-modes.md` | T4 | The `Tombstone:` row and its three-field contract beside the existing intent fields | The page describes the field an adopter will see |
| Reusable learning — `notes/verification-ledger.md` | T2, T3 | The tombstone-name and orphan measurements the criteria rest on | The ledger records the measurements the criteria rest on |

## Design (LLD)

### Data & schema

A tombstone is a Markdown file carrying exactly three preamble fields. `Slug:`
is copied byte-for-byte from the retired source; `Tombstone:` is an ISO 8601
date; then exactly one of `Reissued as:` or `Retired:`. This slice contracts
both shapes and writes neither into the live corpus — the sibling lint
validates whichever a writer produces, and the operation that produces one is
the transaction slice.

The date is a value the caller supplies, sampled once when a transaction opens.
Sampling it here would put a clock inside a pure function and would let an
operation spanning midnight write two dates.

Owned by: T2

### Interfaces & contracts

Three callables, each total and side-effect free: validate a rename request and
return either the resolved request or one fixed refusal token; serialise and
parse a tombstone; and report the allocator's next ordinal for a token over a
given corpus, counting tombstones alongside live intents.

Refusal tokens, each fixed: `source-missing`, `source-outside-root`,
`source-not-regular`, `source-tombstone`, `source-unregistered`,
`registry-unparseable`, `registry-ambiguous`, `token-unknown`, `path-dirty`,
`target-occupied`, `allocator-refused`.

Owned by: T1, T2, T3

### Behavior & rules

**Liveness is a field read.** AC-0006 makes a file in `docs/product/intents/` a
tombstone if and only if its preamble carries `Tombstone:`, so validating that
a source is live costs one read and needs no separate index. A source that is
a tombstone refuses `source-tombstone`: renaming one would re-issue against a
retired name and leave a tombstone of a tombstone, the outcome ADR-0108 D3
exists to prevent.

**A source that is not a regular file refuses.** An in-root symlink passes
`source-outside-root`, so without `source-not-regular` a later reader would
follow it.

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

**Tests:** One refusing case per clause, each asserting the fixed token: absent
source; source outside `docs/product/intents/`; source that is a symlink out of
the root; source that exists but is not a regular file, including an in-root
symlink, which `source-outside-root` does not catch; source that is a tombstone
rather than a live intent; token outside `NAMESPACE_TOKENS`; source with no
`workspace.toml` entry; a `workspace.toml` that does not parse; a
`workspace.toml` carrying two entries for the source; and a path the request
names carrying an uncommitted change. A positive case asserts a fully valid
request passes, so the suite cannot be satisfied by refusing everything. One
case invokes validation from a subdirectory and asserts the repository root
resolves to the `git rev-parse` toplevel rather than the working directory.
Covers AC-0021 and AC-0020.

**Approach:** Resolve through `resolve_confined_target`; read liveness through
the same field test AC-0006 states.

**Depends on:** none

### T2 — A tombstone round-trips its three fields and refuses every bad value

**Tests:** Write and re-read a tombstone; assert `Slug:` is byte-identical to
the source's, `Tombstone:` is the supplied date, and `Reissued as:` holds the
successor path. Rejecting cases: a non-ISO date, an absolute `Reissued as:`,
one resolving outside `docs/product/intents/`, an empty `Retired:`, both
pointer fields present, neither present, a fourth field. A date supplied either
side of midnight writes exactly what it was given. Covers AC-0005, AC-0015,
AC-0016, AC-0017, and AC-0006's biconditional on both arms.

**Depends on:** none

### T3 — The allocator's next ordinal clears every tombstone

**Tests:** For every token in `NAMESPACE_TOKENS`, the next ordinal exceeds
every ordinal that token carries in the corpus, tombstones counted alongside
live intents. Re-runs `test_tombstone_filename_shapes_pin_allocation_and_check`
in `packs/core/tests/skills/work-intake/test_intent_ordinal.py` — committed
87768ba4d, six shapes, green — rather than re-authoring it. Covers AC-0004.

**Depends on:** none

### T4 — The convention is recorded where an adopter and a maintainer each find it

**Tests:** Goal-based. The ADR exists, is `Accepted`, and `spec.md` cites it in
`Constrained by:`, which is AC-0027; `intent-fields-and-modes.md` documents
`Tombstone:` and its three-field contract. Both are checked by reading the
files, because neither is executable.

**Approach:** The ADR states the tombstone convention and records the two
rejected name shapes from the 2026-09-21 measurement — the four that refuse the
directory and the one that silently frees the ordinal.

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
