# Verification ledger — intent renumber, reissue, and the tombstone

Measurements the spec's criteria rest on. This file is one of the two paths
AC-0001 excludes from the citation search by name, because it records vacated
paths as history.

## 2026-09-28 — a generated projection cites an intent, and it is tracked

Measured during the spec-mode adversarial review, when the citation sweep's
behaviour over a generated projection was found unstated.

`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` cites
`docs/product/intents/FEAT-0001-intent-identity-and-registration.md`. Two
adapter-root projections of that file carry the same citation:

| Path | Role | Tracked | In `.gitignore` |
| --- | --- | --- | --- |
| `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` | source | yes | no |
| `.claude/skills/work-loop/scripts/lint-traceability.py` | projection | yes | no |
| `.agents/skills/work-loop/scripts/lint-traceability.py` | projection | yes | no |

What it bounds: a projection is inside AC-0001's derived set, so the citation
relation reaches it and the sweep cannot ignore it. What it does not bound: the
number of projections a rename touches, which grows with the self-host recipe's
projection roots and is not fixed by this measurement.

This is why the operation repoints the `.apm/` source and writes no projection,
and why AC-0001 folds the self-host step into "after a rename".

## 2026-09-28 — projection fidelity is owned by an existing gate, not by this slice

Measured while deciding whether AC-0018's conservation clause should reach a
projection. It should not: the rename never writes that file, so "no other
content in that file changes" over a projection is a property of the self-host
step. A version line, a header rewrite, or the `x.md` → `x.toml` extension
substitution would falsify it with the rename entirely correct.

The owning control, verified end to end:

| Link | Evidence |
| --- | --- |
| Diagnostic | `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:1557-1581` — step 15 emits `CAT-V-015 self-host projection is out of date` |
| Chained into | `tools/repo/build_gate_chain.py:232-235` — `catalogue verify --root .` is the chain's first step |
| Target | `Makefile:161-166` — `make build-check` runs the chain |
| Trigger | `.github/workflows/build-check.yml` — runs on every pull request |
| Division of labour | `docs/architecture/agentbundle.md:291-292` — `CAT-V-015` owns source/projection drift, `CAT-V-014` owns `dist/` drift |

Checked rather than assumed: `_step_selfhost_drift` emits nothing when
`.adapt-discovery.toml` is absent (`verify.py:1564-1569`). That file exists at
the repository root, so the control fires here. The recorded blind spot in the
sibling gate — `CAT-V-014` returning `[]` when `dist/` is absent,
`docs/product/intents/gates-that-read-clean-while-gating-nothing.md:29` — is
about `dist/` output drift and does not reach `CAT-V-015`.

`tools/lint-generated-path-ownership.py:18-27` names duplicating this drift
gate as the thing not to do, and states that "content inside a present entry is
the drift gate's to answer".

What it bounds: AC-0018 excludes a generated projection, and nothing is left
unverified provided `CAT-V-015` stays in force. What it does not bound: whether
`CAT-V-015` remains chained into `build-check`. If that link is ever removed,
AC-0018's exclusion loses its cover and this decision needs revisiting.

## 2026-09-28 — where a Commit temporary may be orphaned, measured two ways

Measured while settling AC-0026's forward-recovery arm. Commit copies rather
than moves, so it creates a per-target temporary; a `SIGKILL` runs no cleanup
handler, so that temporary can be orphaned. What decides the damage is which
directory it was orphaned in, and the two candidate directories behave
differently.

**Filename routing — benign.** The allocator's `classify`
(`packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py`) was called
directly on candidate temporary names:

| Name | `classify` |
| --- | --- |
| `CAP-0003-workspace-coordination-reorganization.md` | `valid` |
| `.CAP-0003-old-slug.md.tmp-0` | `outside` |
| `.FEAT-0001-intent-identity-and-registration.md.tmp-0` | `outside` |
| `.tmp-0` | `outside` |
| `CAP-0001x.md` | `malformed` |

A leading dot puts the name outside the allocator's set, so an orphan does not
reach the `malformed` branch that the 2026-09-21 tombstone-name measurement
recorded as refusing the whole directory. The allocator is unaffected.

**Content routing — fails a Shipped spec's gate.** The corpus lint
(`packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py`, which
walks the directory through `list_confined_regular_files`) does not skip
dotfiles. Against a two-file fixture corpus:

| Corpus | Result |
| --- | --- |
| one valid live intent | `clean — 1 entry, 1 live, 0 tombstone` · exit 0 |
| plus `.FEAT-0002-….md.tmp-0` holding only `Slug:` and `Tombstone:` | `2 violation(s) — 2 entries, 1 live, 1 tombstone` · exit 1 |

The two violations were `a tombstone carries exactly one of 'Reissued as:' or
'Retired:', and this one carries 0` and `a tombstone carries exactly 3 fields,
and this one carries 2`. AC-0006 routes by content, so a partial copy of a
tombstone is read as a tombstone and fails AC-0005.

What it bounds: a temporary orphaned in `docs/product/intents/` breaks
`intent-metadata-shape-contract`'s lint, which is Shipped. That is what makes
Commit's opening sweep non-optional, and what T4 asserts through the lint
rather than through the temporary's name.

Relocating temporaries into the staging root was considered as a way to make
the state unreachable rather than recovered, and rejected: the replace would
then cross directories, and `rename(2)` refuses `EXDEV` between distinct mount
points even when both share one device, so no `st_dev` comparison can predict
it. An `EXDEV` met during Commit would also defeat the forward recovery that
re-runs Commit, leaving AC-0026 with one arm. A same-directory replace cannot
raise `EXDEV` at all, so the temporary stays beside its target and recovery
removes the orphan.

What it does not bound: whether any other instrument reads
`docs/product/intents/`. Two were measured — the allocator's `classify` and the
corpus lint — and the directory may have readers neither covers. Nor does it
bound the mount topology of any adopter's checkout; it establishes only that
the chosen design never needs to care, because it never renames across
directories.

## 2026-09-28 — the transaction's failure modes, measured instead of reasoned

Five generations of this transaction were specified in prose, and each review
round found a defect in the newest one. The sixth was written from measurement.
A throwaway spike drove real `SIGKILL`s at controlled points against fixture
trees and recorded what survived. Nothing from the spike ships; what ships is
the design it corrected.

| # | Question | Result |
| --- | --- | --- |
| A | Does `SIGKILL` strand `.workspace-repair.lock`? | **Yes.** File survives; recorded owner PID verifiably dead; next writer gets `FileExistsError`; the module exposes only `WORKSPACE_LOCK_FILE` and `_acquire_workspace_lock` |
| B | Does `os.replace` consume its source? | **Yes.** Source gone, target holds source bytes |
| C | Same-directory vs cross-device replace | Same-directory succeeds; cross-device raises `EXDEV` (errno 18) |
| D | Does path-based `mkdir` follow a swapped parent symlink? | **Yes — it escaped the root.** An `O_NOFOLLOW` descriptor walk refused it |
| E | What does `SIGKILL` mid-copy leave? | A surviving 120-byte orphan holding a partial tombstone preamble |
| F | Does `dir_fd` + `O_NOFOLLOW` + `S_ISREG` sweep safely? | **Yes.** Symlinked candidate refused, its target survived, real orphan unlinked |

**A is the one that changed the design.** An earlier repair had this operation
acquire the shared workspace lock before allocation and hold it to disposal, to
serialise against `intake-intent` admission. The measurement shows what that
costs: one kill inside the operation leaves a lock no code can clear, and every
workspace writer — repair-apply, migration apply and rollback, guarded refresh,
prune, admission — blocks until a human deletes the file. The fix traded a
silent two-writer race for a repository-wide outage, so it was withdrawn. The
lock is now held only around the registry read-modify-write, which is the
smallest window that still makes that edit atomic against other registry
writers.

The successor-filename race that the long hold was meant to close is instead
closed where it occurs. Commit creates the successor with exclusive-create; on
`FileExistsError` it compares the existing bytes against the staged successor.
Identical means this transaction's own earlier pass already applied it, so the
step is a no-op and forward recovery stays idempotent — the property that
refuted a plain exclusive-create guard. Different bytes mean another writer
minted that filename, which is `commit-interrupted` naming the path, never a
silent overwrite.

**A also records a gap that is not this slice's.** The lock file carries the
owner PID and that PID is checkably dead after a kill, so stale-lock recovery is
implementable — but no writer in the repository performs it, and the helper
exposes no release or break verb. That predates this work and affects every
workspace writer equally. It is named under `## Follow-ons` rather than repaired
here, because widening a shared helper is not this contract's outcome.

**D and E** confirm two security findings that were previously argued rather
than shown: a staging root created by path is reachable outside the repository
if its parent is swapped between validation and use, and a kill mid-copy really
does leave a partial tombstone preamble of the kind the corpus lint rejects.
**F** validates the bounded sweep as specified.

What this does not bound: the same-device-different-mount `EXDEV` case, which
needs a bind mount the spike could not create without elevation. It is moot for
this design, because after the 2026-09-28 decision Commit never renames across
directories. Nor does it bound Windows behaviour, where the reparse-point
semantics of D and F differ and were not exercised.

## 2026-09-28 — the allocator property, re-run rather than re-measured

What AC-0004 rests on, and where that evidence lives. The six candidate
tombstone filenames were measured on 2026-09-21 and recorded in
`docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md` under
`## 2026-09-21 — what the tombstone decision inherits from this slice`. This
slice cites that table and does not re-measure it: two of the six keep the
`<TYPE>-NNNN-<slug>.md` shape and allocate correctly, three refuse the whole
directory, and one — a `tombstone-` prefix that leaves the namespace — silently
frees the ordinal. The last is the shape to avoid, because the refusing three
fail visibly and it does not.

The inherited control is
`test_tombstone_filename_shapes_pin_allocation_and_check` in
`packs/core/tests/skills/work-intake/test_intent_ordinal.py`, committed
87768ba4d. Re-run on 2026-09-28: 6 passed in 0.94s. This slice adds no
coverage there.

What was verified separately, because the inherited test pins filename *shapes*
rather than the property itself: the allocator's next ordinal exceeds every
ordinal its token carries in `docs/product/intents/`, over the corpus as it
stands.

| Token | Ordinals present | Highest | Next allocated |
| --- | --- | --- | --- |
| `CAP` | 7 | 7 | 8 |
| `FEAT` | 14 | 14 | 15 |
| `STRAT` | 4 | 4 | 5 |
| `VISION` | 1 | 1 | 2 |

And the tombstone arm, which is the half the property exists for: a tombstone
placed above the current maximum keeps its ordinal out of circulation. A
tombstone at `CAP-0012` moved the next allocation from 8 to 13; one at
`FEAT-0019` moved it from 15 to 20. Measured on a temporary copy of the corpus,
never the real directory, because other sessions share this worktree.

What it bounds: the guarantee holds over the directory as it stands, with
tombstones counted alongside live intents. What it does not bound: a tombstone
deleted by hand frees its ordinal again, and nothing here detects that — the
residual `## Assumptions` already records.
