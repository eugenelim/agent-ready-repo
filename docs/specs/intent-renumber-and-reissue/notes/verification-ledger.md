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
