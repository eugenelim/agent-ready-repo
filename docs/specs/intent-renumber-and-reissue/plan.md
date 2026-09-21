# Plan: Intent renumber, reissue, and the tombstone

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Approach

One script under `packs/core/.apm/skills/work-intake/scripts/`, beside the
allocator it calls and the `file_safety.py` it confines with. It plans the whole
rename before it writes anything, writes through a staging directory, and swaps
into place with directory-descriptor-relative `os.replace` — the same primitive
`close-work/scripts/cooling.py:630` already uses. Planning first is what makes
AC-0003 reachable: every refusal AC-0021 and AC-0020 describe happens while the
tree is still untouched, so the common failure path never needs rollback at all.

Order of work: the request contract and its refusals first, because they gate
everything and need no filesystem writes; then the citation relation, which is
the riskiest part and the one two review rounds found wrong; then the
transaction; then the operator surface and the guide. The citation sweep is
riskiest because its scope is a moving target — the spec had to abandon two
attempts at enumerating citation forms before settling on string occurrence over
a derived file set.

Testing is TDD throughout except the packaged surface and the guide. Fixtures
are whole miniature corpora in `tmp_path`, never the real
`docs/product/intents/`, because a test that writes there would race the other
sessions working in this worktree.

## Constraints

- **ADR-0108 D2** bars renumbering on insertion or reorder. This design never
  renumbers: it allocates a new ordinal and retires the old name, so the bar is
  never reached. **D3** requires non-reuse and a recorded removal; the tombstone
  file is that record, one per retired name.
- **ADR-0033 D2** keeps `Level` an open set. Nothing here validates a `Level`
  value; the target token comes from the request and is checked against
  `NAMESPACE_TOKENS`, not against `Level`.
- **ADR-0098 D2** makes `intake-intent` the owner of admission. This operation
  is not admission and must not touch the admission transaction.
- **`docs/specs/intent-metadata-shape-contract/spec.md`** owns the corpus lint.
  Its AC-0017 routes by this spec's AC-0006 and validates the tombstone branch
  against AC-0005. Those two criteria are load-bearing for that spec's live
  implementation: do not change either without telling its owner.
- The blessed confinement helper is `file_safety.py`
  (`validate_confined_directory`, `list_confined_regular_files`,
  `read_confined_regular_file`), already vendored into this skill's `scripts/`.
  It exposes no move or rename, which is why T4 builds one.
- T7's ADR must be `Accepted` before T8 ships: it authorises applying
  ADR-0108 D3's non-reuse rule to intent filenames, which extends a decision
  scoped to loop-contract items. The `Depends on:` edge carries it.
- `work-intake` declares `Read Write Edit Bash`. No tool surface widens.

## Construction tests

**Integration tests:** one end-to-end rename per cause over a miniature corpus,
driven through the packaged surface rather than the module, covering AC-0025
and both arms of AC-0013.

**Manual verification:** an operator follows
`guides/product-engineering/how-to/` through one real rename, which is the only
way to learn whether the page is followable.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/adr/` | T7 | An Accepted ADR stating the tombstone convention and the two rejected name shapes | The ADR exists and `spec.md` cites it in `Constrained by:` |
| Interface compatibility — `guides/product-engineering/reference/intent-fields-and-modes.md` | T7 | The `Tombstone:` row and its three-field contract beside the existing intent fields | The page describes the field an adopter will see |
| Maintainer procedure — `guides/product-engineering/how-to/` | T8 | A how-to covering both causes and each refusal | The page walks one real rename end to end |
| Current product truth — `intake-intent` and `work-intake` `SKILL.md` | T8 | Both statements point at this operation instead of asserting the capability wall | No skill still claims an intent can never be renamed |
| Release history — `packs/core/CHANGELOG.md` | T8 | One entry for the shipped operation | Entry present under the released version |
| Reusable learning — `notes/verification-ledger.md` | T2, T4 | The citation-relation measurement and the transaction's failure-injection matrix | The ledger records the measurements the criteria rest on |

## Design (LLD)

### Data & schema

A tombstone is a Markdown file at the vacated path carrying exactly three
preamble fields. `Slug:` is copied byte-for-byte from the retired source;
`Tombstone:` is an ISO 8601 date; then exactly one of `Reissued as:` or
`Retired:`. This slice writes only the `Reissued as:` shape — the `Retired:`
shape is contracted so the sibling lint validates it, and written by the
follow-on that owns retirement.

The date is sampled once, when the transaction opens, and held in the plan
object. Sampling at write time is what would let an operation spanning midnight
write two dates into one transaction.

`workspace.toml` carries the registry `path` entries. The rename edits the
matching entry's `path` value and nothing else in the file; a stale entry raises
`missing_artifact`, which `tests/roster/test_workspace_status_projection.py:948`
treats as fail-closed.

Owned by: T3, T4

### Interfaces & contracts

The operator surface is a script invoked from the repository root with three
arguments — source path, target token, cause — mirroring `intent_ordinal.py`'s
existing argument style so an operator meets one convention, not two. It exits 0
on success and non-zero with one fixed diagnostic token per refusal class, which
is the discipline `intent_ordinal.py` already states for itself.

It calls `intent_ordinal.py` in-process by path, the way
`test_intent_ordinal.py` loads it, rather than by subprocess: a subprocess would
make the pre-write snapshot AC-0012 names hard to pin, because the corpus could
move between the two reads.

Refusal classes, each a fixed token: `source-missing`, `source-outside-root`,
`source-unregistered`, `token-unknown`, `cause-unknown`, `path-dirty`,
`allocator-refused`, `target-exists`.

Owned by: T1, T5, T6

### Behavior & rules

**The citation relation.** A citation is an occurrence of the vacated path
string in a file. Not a link target, not a field value — two review rounds
established that enumerating forms leaves a form out, and the counter-example is
in this repository: a `Discovery:` header carries a bare path no link-target
rule reaches.

The searched set is the pre-run `git ls-files` output plus every path the
operation creates, regardless of index state. Two paths are excluded by name:
the tombstone standing at the vacated path, and this spec's own
`notes/verification-ledger.md`, which records renames as history.

**The success domain.** A request succeeds when all of: the source resolves
inside `docs/product/intents/` and exists; the token is in `NAMESPACE_TOKENS`;
the cause is `duplicate-ordinal` or `altitude-change`; the source has a
`workspace.toml` entry; and every path the plan would touch is clean. Anything
else refuses. The domain is stated once here and each refusal token above maps
to one clause.

Owned by: T1, T2

### Failure, edge cases & resilience

Three phases, and the phase boundary is what bounds the failure model.

**Plan.** Read-only. Resolve and confine the source, allocate the ordinal
against the pre-write snapshot, compute the citing set, and collect every path
to be written. Every refusal lives here, so a refused request has touched
nothing and AC-0003's first arm is satisfied by construction rather than by
rollback.

**Stage.** Write every output into a staging directory under the repository
root: the successor, the tombstone, each rewritten citing file, and the edited
`workspace.toml`. A failure here abandons the staging directory and the tree is
untouched.

**Commit.** `os.replace` each staged file over its target, directory-descriptor
relative, source-before-citations so no window exists where a citation points at
a path that does not yet exist.

A process killed inside Commit leaves a partially applied rename. That is the
one state the design does not undo itself, and the spec does not promise it
does: the staging directory survives the kill and names every intended path, so
recovery is re-running the commit phase or `git restore`. Nothing durable is
written outside the working tree and index, which is what makes `git restore`
sufficient.

Edge cases: the source cites its own path (it becomes the tombstone, so it is
excluded from the citing set); a tombstone already points at the source (AC-0018
re-points it in the same transaction); the allocator refuses (`allocator-refused`
— the operation does not guess an ordinal, matching `intent_ordinal.py`'s own
refuse-rather-than-answer rule).

Owned by: T4

### Design decisions

- **Staging plus `os.replace` over write-in-place plus undo.** An undo log has
  to be correct under its own failures; a staging directory does not exist until
  it is complete. `cooling.py:630` sets the precedent in this repository.
- **String occurrence over a parsed citation relation.** A parser is narrower
  than the truth and each review round found the form it missed. A string search
  over a derived file set is exhaustive by construction; its cost is two named
  exclusions.
- **In-process allocator call over subprocess.** Pins the snapshot AC-0012
  names.

Owned by: T2, T4

## Tasks

### T1 — Every invalid request refuses with its own token, before any write

**Tests:** One refusing case per clause of the success domain, each asserting
the fixed token and that the fixture tree is byte-identical afterwards: absent
source, source outside `docs/product/intents/`, source that is a symlink out of
the root, token outside `NAMESPACE_TOKENS`, unrecognized cause, source with no
`workspace.toml` entry, and a path the plan would touch carrying an uncommitted
change. A positive case asserting a fully valid request passes validation.
Covers AC-0021, AC-0020, and AC-0003's refusal arm.

**Depends on:** none

### T2 — The citing set is exactly the files containing the vacated path

**Tests:** Over a fixture corpus, the computed set equals the set found by an
independent string search, in both directions — a missing file and an extra one
each fail. Cases: a Markdown inline link, a bare path in a `Discovery:` header,
a `path =` value in TOML, the same path inside a fenced code block, the two
named exclusions, and an untracked created file. The `Discovery:` case is the
one a link-target parser gets wrong and is the reason this task exists.
Covers AC-0001's relation.

**Approach:** Derive the parent set from `git ls-files` plus the operation's
planned creations. The exclusions are two literal paths, not a pattern, so the
set of things that can silently leave the search stays enumerable.

**Depends on:** none

### T3 — A tombstone round-trips its three fields and refuses every bad value

**Tests:** Write and re-read a tombstone; assert `Slug:` is byte-identical to
the source's — AC-0002's tombstone arm — `Tombstone:` is the transaction-open date,
and `Reissued as:` holds the successor path. Rejecting cases: a non-ISO date, an absolute
`Reissued as:`, one resolving outside `docs/product/intents/`, an empty
`Retired:`, both pointer fields present, neither present, a fourth field. A
transaction opened either side of midnight writes one date. Covers AC-0005,
AC-0015, AC-0016, AC-0017, and AC-0006's biconditional on both arms.

**Depends on:** none

### T4 — A rename applies in full or leaves the tree and index unchanged

**Tests:** A failure injected at each write point in Stage, and at each in
Commit. A Stage failure leaves the tree and index byte-identical. A Commit
interruption leaves either the full rename or a recoverable partial state whose
staging directory names every intended path, and nothing else. A successful
rename is compared byte for byte: the successor equals the source with the
vacated path substituted and differs nowhere else, which is the self-citing
source case; each citing file differs only at the path; no other file differs;
every intent the rename did not touch keeps its prior `Slug:` bytes. Covers
AC-0003, AC-0026, AC-0013, AC-0018, AC-0024, and AC-0002's successor and
unaffected-intent arms.

**Approach:** Stage-then-`os.replace` with directory descriptors, as
`close-work/scripts/cooling.py:630` does. Commit order is source before
citations, so no window exists where a citation names a path that does not yet
exist.

**Depends on:** T1, T2, T3

### T5 — The new ordinal is the allocator's next for the target token

**Tests:** A fixture where the vacated ordinal is free under the target token —
the case a carried-across ordinal would pass — asserting the operation still
takes the allocator's next value. For every token in `NAMESPACE_TOKENS`, the
next ordinal after a rename exceeds every ordinal that token carries, tombstones
counted. An allocator refusal produces `allocator-refused` and no write. Covers
AC-0004 and AC-0012.

**Depends on:** T1

### T6 — Resolution stops at a tombstone, and inbound tombstones re-point

**Tests:** A pointer resolving onto a tombstone yields a diagnostic naming the
tombstone and its `Reissued as:` target, and never the successor's content. A
corpus where two tombstones already point at the source: after the rename both
name the final target, inside the same transaction. A `Reissued as:` naming an
absent path, and one naming a file that itself carries `Tombstone:`, each fail
naming both paths. Covers AC-0007, AC-0008, AC-0009.

**Depends on:** T3, T4

### T7 — The convention is recorded where an adopter and a maintainer each find it

**Tests:** Goal-based. The ADR exists, is `Accepted`, and `spec.md` cites it in
`Constrained by:`; `intent-fields-and-modes.md` documents `Tombstone:` and its
three-field contract. Both are checked by reading the files, because neither is
executable.

**Approach:** The ADR states the tombstone convention and records the two
rejected name shapes from the 2026-09-21 measurement — the four that refuse the
directory and the one that silently frees the ordinal.

**Depends on:** T3

### T8 — An operator can run a rename from an installed core pack

**Tests:** An end-to-end rename per cause driven through the surface an
installed `packs/core` exposes, not through the module. `packs/core` builds and
the surface appears in its manifest. Covers AC-0025 and the integration tests
above. Manual: an operator follows the how-to through one real rename.

**Approach:** The two `SKILL.md` statements that nothing renames an intent point
here instead, and the changelog entry lands with them, because all three are the
same "what the pack now does" edit.

**Depends on:** T4, T5, T6, T7

## Changelog

- 2026-09-21 — drafted.
