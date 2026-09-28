# Plan: Intent renumber, reissue, and the tombstone

- **Status:** Approved
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
  Its corpus-lint routing-and-validation criterion — cited by name and path,
  because a bare criterion number resolves against this spec's own criteria —
  routes by this spec's AC-0006 and validates the tombstone branch against
  AC-0005. Those two criteria are load-bearing for that spec's live
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

**Integration tests:** one end-to-end rename driven through the packaged
surface rather than the module, covering AC-0025 and AC-0013.

**Manual verification:** an operator follows
`guides/product-engineering/how-to/` through one real rename, which is the only
way to learn whether the page is followable.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/adr/` | T7 | An Accepted ADR stating the tombstone convention and the two rejected name shapes | The ADR exists and `spec.md` cites it in `Constrained by:` |
| Interface compatibility — `guides/product-engineering/reference/intent-fields-and-modes.md` | T7 | The `Tombstone:` row and its three-field contract beside the existing intent fields | The page describes the field an adopter will see |
| Maintainer procedure — `guides/product-engineering/how-to/` | T8 | A how-to covering the rename and each refusal | The page walks one real rename end to end |
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

The operator surface is a script invoked from the repository root with two
arguments — source path and target token — mirroring `intent_ordinal.py`'s
existing argument style so an operator meets one convention, not two. It exits 0
on success and non-zero with one fixed diagnostic token per refusal class, which
is the discipline `intent_ordinal.py` already states for itself.

It calls `intent_ordinal.py` in-process by path, the way
`test_intent_ordinal.py` loads it, rather than by subprocess: a subprocess would
make the pre-write snapshot AC-0012 names hard to pin, because the corpus could
move between the two reads.

Refusal classes, each a fixed token: `source-missing`, `source-outside-root`,
`source-unregistered`, `token-unknown`, `path-dirty`, `target-occupied`,
`allocator-refused`.

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

**A tracked generated projection is repointed at its source, never written.**
A projection under `.claude/`, `.agents/` or any other adapter root is a copy
of an `.apm/` file, and both are tracked, so both land in the searched set. The
operation rewrites the `.apm/` source and writes no projection — `spec.md`'s
`Never do` bars editing one, and `packs/AGENTS.md` § Self-hosting projection
bars it independently. The projection is brought into line by the self-host
step that `packs/AGENTS.md` already mandates after any `.apm/` edit, which the
T8 how-to names as the rename's closing step and which AC-0001 folds into
"after a rename". This is why the exclusion list stays two literal paths: a
projection is not excluded from the search, it is corrected by regeneration.

The live case is not hypothetical; `notes/verification-ledger.md` records the
measured instance and the date it was measured.

**The success domain.** A request succeeds when all of: the source resolves
inside `docs/product/intents/` and exists; the token is in `NAMESPACE_TOKENS`;
the source has a `workspace.toml` entry; the allocator can answer for the
corpus; the target filename is free; and every path the plan would touch is
clean. Anything
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

**Commit.** First sweep: unlink every orphaned per-target temporary in each
destination directory Commit is about to write. Then, for each staged file, copy
it to a per-target temporary *beside its target* — exclusive-create,
`O_NOFOLLOW`, successive candidate names on `FileExistsError` — and `os.replace`
that temporary onto the target with one directory descriptor as both ends. Order
is source before citations, so no window exists where a citation points at a
path that does not yet exist.

Two properties are load-bearing, and each answers a failure the other does not.

*Commit copies rather than moves.* `os.replace` consumes its source, so a
Commit that replaced straight out of staging would destroy the record its own
forward recovery reads: after the first success, re-running Commit would find
that entry gone and could not distinguish "already applied" from "never
staged". Copying leaves the canonical staged entries intact through Commit,
which is what makes forward recovery idempotent — a re-run rewrites each target
from a source that is still there, and an already-applied target is rewritten
with identical bytes.

*The temporary sits beside its target, and the sweep is what makes that safe.*
A kill runs no cleanup handler, so a temporary can be orphaned wherever it
lives. Two designs were considered and the difference is where the orphan is
answered, not whether it can occur. Putting temporaries in the staging root
would keep them out of tracked directories, but the replace would then cross
directories, and `rename(2)` refuses `EXDEV` between distinct mount points even
when both share one device — so no `st_dev` comparison can predict it, and an
`EXDEV` met during Commit would defeat the forward recovery that re-runs Commit,
collapsing AC-0026 to one arm. A same-directory replace cannot raise `EXDEV` at
all. So the temporary stays beside its target and the orphan is recovered rather
than prevented: it is a member of the partial state a kill inside Commit already
produces, which is the state the partition exists to name and both directions
exist to clear.

The exposure that makes the sweep non-optional is measured, not predicted. An
orphaned partial copy of a tombstone in `docs/product/intents/` carries
`Tombstone:`, so AC-0006 routes it as a tombstone on its content — the name does
not exempt it — and it then fails AC-0005's three-field contract, failing the
Shipped sibling's corpus lint. `notes/verification-ledger.md` records the run
that established it, together with the finding that the allocator is unaffected
because such a name classifies as `outside`. The window in which that state
exists is the window between a kill and the next recovery action, which is the
window the design already accepts for a half-applied rename.

A process killed inside Commit leaves a partially applied rename. That is the
one state the design does not undo itself, and the spec does not promise it
does. What makes AC-0026's second arm reachable is that the staging directory
survives the kill and names every path Commit intended to write. The partition
that recovery reads is derived from what Commit writes, not enumerated by hand:

- **Exactly one file is created** — the successor, at a filename the allocator
  had not yet issued, so it is untracked and git holds no version of it.
- **Every other target is replaced** — each citing file, `workspace.toml`, and
  the tombstone. The tombstone belongs here, not with the created paths: it
  lands at the vacated path, which is the live source's own tracked path, and
  Commit never moves the source aside. Every path in this set is tracked and
  has a committed version.
- **The staging directory is not a target at all.** It is the recovery record,
  created during Stage, and it is a directory, so no unlink reaches it.
- **Per-target temporaries are created and normally consumed.** Each lives
  beside its target and is consumed by the `os.replace` that applies it, so
  after a complete Commit none remain. A kill can orphan the one in flight, so
  recovery routes them explicitly: they are untracked, `git restore` does not
  remove them, and leaving one behind is the third state AC-0026 forbids just
  as much as leaving the successor behind.

Recovery is one of two operations over that derivation, and `git restore` alone
is neither:

- **Forward.** Re-run Commit over the surviving staging directory. Its first
  sweep clears any temporary the kill orphaned, and it terminates in the
  complete rename because Commit copies rather than moves: every staged entry
  is still present whatever prefix of Commit ran, and rewriting an
  already-applied target with identical bytes is a no-op.
- **Back.** Sweep the per-target temporaries first, because `git restore`
  cannot see them. Then `git restore` every replaced path — which includes the
  vacated path, restoring the source over the tombstone — unlink the successor,
  and remove the staging directory tree with a stdlib recursive removal under
  the same confinement check every other write passes. Ends in the pre-rename
  state.

The backward direction states its own directory teardown because `cooling.py`
offers no precedent for one: it establishes `os.replace` at `cooling.py:630`
and a single-file `os.unlink` at `cooling.py:643`, and nothing more.

`git restore` on its own cannot reach either state, because the successor and
the staging directory are untracked and it does not remove them; a bare
`git restore` would leave both standing beside a restored source, which is the
third state AC-0026 forbids. Deriving the partition from Commit's writes is
what makes both directions terminate, and it is why the staging directory is
retained until recovery rather than cleaned up at Commit's end. Nothing durable
is written outside the working tree, the index, and that staging directory.

A concurrent reader is the one cross-component case. `intent-metadata-shape-contract`'s
corpus lint reads `docs/product/intents/` and holds no lock, and neither does
this operation. Commit is a sequence of `os.replace` calls, so a lint running
across it can see a half-applied directory. That is acceptable because its read
is confined: a torn read surfaces as an unreadable corpus and a non-zero exit,
never as a false clean. Do not add a lock to make this quieter — a loud failure
is the property worth keeping, and its owning session confirmed the behaviour
on 2026-09-21.

Edge cases: the source cites its own path (it becomes the tombstone, so it is
excluded from the citing set); a tombstone already points at the source (AC-0018
re-points it in the same transaction); the allocator refuses (`allocator-refused`
— the operation does not guess an ordinal, matching `intent_ordinal.py`'s own
refuse-rather-than-answer rule).

Owned by: T4

### Design decisions

- **Staging plus `os.replace` over write-in-place plus undo.** An undo log has
  to be correct under its own failures; a staging directory does not exist until
  it is complete.
- **`cooling.py`'s swap, with one deviation, and a sweep it has no need of.**
  `packs/core/.apm/skills/close-work/scripts/cooling.py:615-645` is the
  repository's durable-write precedent, and Commit inherits its swap whole: the
  exclusive-create `O_NOFOLLOW` open, the `FileExistsError` name retry, the
  temporary beside its target, and one directory descriptor as both ends of the
  `os.replace`. The deviation is **the retained staging root**, which
  `cooling.py` has no equivalent for because it writes one file; this operation
  writes across several directories, so its partial state spans files and needs
  one place naming the whole intended path set. What is added rather than
  deviated is **the sweep**: `cooling.py` discards its temporary in a `finally`
  block, which a kill never runs, and tolerates an orphan only by retrying
  names. That is sufficient for one file whose directory nothing lints; it is
  not sufficient for `docs/product/intents/`, so recovery removes orphans
  instead of relying on a handler that may not run. § Failure, edge cases &
  resilience owns the argument.
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
the root, token outside `NAMESPACE_TOKENS`, source with no
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
one a link-target parser gets wrong and is the reason this task exists. One
further case is a fixture carrying an `.apm/` source and its adapter-root
projection, both citing the vacated path: the computed plan rewrites the source
and leaves the projection untouched, and after the fixture's self-host step the
vacated path occurs in neither. A plan that writes the projection directly
fails this case even though a bare path search over the finished tree would
come back clean, which is the whole point of asserting it here.
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
staging directory names every intended path, and nothing else. From that partial
state, each of the two recovery directions above is run and the resulting tree
compared byte for byte: forward recovery yields the complete rename, backward
recovery yields the pre-rename tree — the source restored at the vacated path
with no tombstone standing there — and neither leaves the successor or the
staging directory behind, which is the third state AC-0026 forbids and the case
a bare `git restore` produces. One case asserts the tombstone is restored by the
replaced-path arm rather than unlinked, because classifying it as created is the
error that makes backward recovery delete the source. One case interrupts
Commit after each prefix and re-runs it, asserting every staging entry survived
that prefix and the re-run ends in the complete rename: forward recovery is
idempotent only because Commit copies to a temporary instead of moving out of
staging, and a Commit that moved would pass every other case here while
failing this one. Three cases cover the per-target temporary, because it is the
one path class that a kill can leave in a tracked directory. One kills Commit
part-way through a single target's copy, then runs each recovery direction and
asserts no temporary remains in any destination directory afterwards — a
direction that skips the sweep fails here and nowhere else. One asserts the
corpus lint over the fixture's intents directory is clean after that recovery,
which is the instrument the orphan actually breaks: asserting on the
temporary's name instead would pass while the lint failed, because AC-0006
routes on content. One leaves an orphan in place from a previous attempt and
asserts the next Commit's opening sweep removes it and the rename then
succeeds, rather than the orphan surviving under a retried name. A successful
rename is compared byte for byte: the successor equals the source with the
vacated path substituted and differs nowhere else, which is the self-citing
source case; each citing file differs only at the path; no other file differs;
every intent the rename did not touch keeps its prior `Slug:` bytes. These
assertions are evaluated at the transaction's exit; AC-0001's post-self-host
arm over a projection is T2's case, and AC-0018 does not reach a projection at
all. Covers
AC-0003, AC-0026, AC-0013, AC-0018, AC-0024, and AC-0002's successor and
unaffected-intent arms.

**Approach:** Stage, then sweep each destination directory for orphaned
temporaries, then per target copy to a temporary beside its target and
`os.replace` it with one directory descriptor as both ends — inheriting
`close-work/scripts/cooling.py:615-645`'s exclusive-create open, name retry and
descriptor-relative replace whole. Commit order is source before citations, so
no window exists where a citation names a path that does not yet exist. Commit
never moves a file out of the staging directory, which is what forward recovery
depends on; the sweep is what keeps a kill from leaving a file the corpus lint
reads.

**Depends on:** T1, T2, T3

### T5 — The new ordinal is the allocator's next for the target token

**Tests:** A fixture where the vacated ordinal is free under the target token —
the case a carried-across ordinal would pass — asserting the operation still
takes the allocator's next value. For every token in `NAMESPACE_TOKENS`, the
next ordinal after a rename exceeds every ordinal that token carries, tombstones
counted. An allocator refusal produces `allocator-refused` and no write. Covers
AC-0004 and AC-0012.

**Depends on:** T1, T4 — both cases assert over a completed rename, which T4
builds.

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
`Constrained by:`, which is AC-0027; `intent-fields-and-modes.md` documents `Tombstone:` and its
three-field contract. Both are checked by reading the files, because neither is
executable.

**Approach:** The ADR states the tombstone convention and records the two
rejected name shapes from the 2026-09-21 measurement — the four that refuse the
directory and the one that silently frees the ordinal.

**Depends on:** T3

### T8 — An operator can run a rename from an installed core pack

**Tests:** An end-to-end rename driven through the surface an
installed `packs/core` exposes, not through the module. `packs/core` builds and
the surface appears in its manifest. Covers AC-0025 and the integration tests
above. Manual: an operator follows the how-to through one real rename, ending
with the self-host step, and confirms the vacated path then occurs in no
tracked file — projections included.

**Approach:** The two `SKILL.md` statements that nothing renames an intent point
here instead, and the changelog entry lands with them, because all three are the
same "what the pack now does" edit.

The how-to names the self-host projection step as the rename's closing step,
not as an optional tidy-up: when the vacated path was cited by an `.apm/` file,
the operation repoints the source only, and AC-0001 does not hold until the
projections are regenerated. A rename whose operator stops at the refusal-free
exit leaves a stale citation in every adapter root.

**Depends on:** T4, T5, T6, T7

## Changelog

- 2026-09-21 — drafted.
