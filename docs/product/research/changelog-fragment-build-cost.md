# Changelog fragment build cost — three-arm measurement run

Plan task T13 prices the delivered fragment layout against a monolith holding
the same records, at ten times today's released-entry count. Plan task T15
removes two redundant projections from the aggregate build and repeats the same
three-arm protocol. Plan task T16 profiles the one projection that remains.
All three answer the
re-measurement the
[assembly spike](changelog-fragment-assembly-spike.md) asked for: its control
arm ranged from 22.92 s to 75.41 s on identical input, so its `+66.08%` figure
carried no error bound.

- **Run dates:** 2026-09-30 to 2026-10-12. Five passes and T18.
  **T18 is now the authoritative record for § 7 Build performance.** It ran
  21:47–22:05 UTC on 2026-10-12, after plan task T16 loaded the file-safety
  helper once per projection and T17 added ADR-0143's monthly bundles, and
  every arm passed the validity rule. Pass 5 was the valid record before the
  bundles, and passes 1–4 are provenance. All are kept below.
- **Verdict, § 7 Build performance:** `SURVIVE`. T18 is valid — every arm's
  retained spread is at or under 11.12% of its median — and the fragment
  layout, stored at the bundle ceiling's worst admitted state, costs
  **+7.22%** over the same records held in one file. § 7 requires under 10%.
  Pass 5 measured +12.12% before the bundles.
- **ADR-0143's Revisit clause is triggered.** 7.22% is at or above its 5% line,
  which the ADR answers by lowering the 1,000-fragment ceiling. The owner
  decides that change. See
  [T18](#t18-the-bundle-ceilings-worst-admitted-state-valid-and-a-survive).
- **Verdict, § 7 Published page count:** `SURVIVE`. In T18 both large arms
  emitted 3,371 marketing pages, 3,319 `/now/` pages and 273 docs pages in
  every retained sample. Passes 3–5 found 3,369, 3,319 and 267 on the
  pre-rebase site.
- **The remaining gap is located.** Four attribution spikes put all of it in
  the changelog projection. About 3 s is the reader reloading its file-safety
  helper per fragment. The rest scales with the number of loose fragments. Plan
  task T16 now loads the helper once, and
  [ADR-0143](../../adr/0143-released-changelog-records-move-into-monthly-bundles.md)
  added monthly bundles. See
  [Bundle attribution spikes](#bundle-attribution-spikes-where-pass-5s-gap-lives).
- **The T16 profile named a different hot path, and the code now follows it.**
  Over half the fragment projection was one avoidable cost, and it was not the
  one T16's plan predicted. See
  [T16 pre-edit profile](#t16-pre-edit-profile-the-locked-hypothesis-is-refuted).
  The amended T16 change then landed: each projection normalizes the
  released-version inventory once instead of once per fragment, which passes 4
  and 5 measured as a drop from 8,912 normalizations to 2 with byte-identical
  output.

Current verdict lines, in the form § 7 reads:

```text
Verdict, § 7 Build performance: SURVIVE
Verdict, § 7 Published page count: SURVIVE
```

## The short version

T18 settles the figure with ADR-0143's bundles in place. It is valid and a
survive:

| Arm | T18 median (current) | T18 range | Spread / median |
| --- | --- | --- | --- |
| today | 16.18 s | 15.60 – 17.40 | 11.12% pass |
| monolith-10x | 72.06 s | 70.54 – 73.91 | 4.68% pass |
| bundled-10x | 77.27 s | 76.44 – 80.34 | 5.05% pass |

With the newest 1,000 records loose and the rest in bundle parts, the fragment
layout costs 5.20 s more than the identical records in one file: **+7.22%**
against a bar of under 10%. That is at or above ADR-0143's 5% Revisit line.
Full detail is in
[T18](#t18-the-bundle-ceilings-worst-admitted-state-valid-and-a-survive).

Before the bundles, pass 5 measured the all-fragments layout:

| Arm | Pass 5 median | Pass 5 range | Spread / median |
| --- | --- | --- | --- |
| today | 16.17 s | 14.55 – 16.49 | 11.98% pass |
| monolith-10x | 74.77 s | 69.98 – 75.37 | 7.21% pass |
| fragments-10x | 83.83 s | 80.35 – 89.48 | 10.89% pass |

The fragment layout costs 9.06 s more than the identical records in one file,
which is **+12.12%** against a bar of under 10%. To pass, the fragment median
had to be below 82.25 s at this monolith median. Full detail is in
[Pass 5](#pass-5-the-readiness-gated-final-run-valid-and-a-kill).

The pass-3 history below explains how the instrument first became valid.
The T15 fix made the instrument work. It did not bring the cost under the bar.

| Arm | Pass 3 median | Pass 3 range | Spread / median | Pass 2 median |
| --- | --- | --- | --- | --- |
| today | 17.40 s | 16.17 – 17.66 | 8.6% pass | 23.69 s |
| monolith-10x | 77.05 s | 73.86 – 79.63 | 7.5% pass | 86.57 s |
| fragments-10x | 91.45 s | 86.13 – 93.60 | 8.2% pass | 129.41 s |

Every build got faster, and the two large arms' retained ranges still do not
overlap. The two arms hold the same 3,300 records and differ only in physical
layout. The fragment layout costs 14.40 s more than the identical records in one
file, which is **+18.69%** against a bar of under 10%.

Pass 2 could produce no figure at all, because its `today` arm varied by 47.4%
of its median. Pass 3's widest arm varies by 8.6%, so the bar can be read and
the answer is a kill. Full detail, including what the fix did and did not move,
is in [Pass 3](#pass-3-the-t15-post-optimization-rerun).

Pass 4 then applied the T16 fix and ran the same protocol twice on a loaded
machine. Its `today` arm varied by 29.5% and 27.6%, so neither run can be read.
What pass 4 did settle is that the fix is free: the complete changelog and
`/now/` payload come out byte-identical while released-inventory normalizations
fall from 8,912 to 2. Full detail is in
[Pass 4](#pass-4-the-post-t16-rerun-inconclusive-twice).

## Pass 5: the readiness-gated final run, valid and a kill

This section stands on its own. It ran on **2026-10-03**, with the same T16
code as pass 4, on pass 4's exact corpus, after a predeclared gate confirmed a
quiet machine. The gate admits exactly one pass 5, and this is it.

**Result: valid, and `KILL`.** All three arms passed the 20% spread bound. The
fragment layout costs **+12.12%** over the same records in one file. § 7 needs
strictly under 10%, so T16 stops delivery and T14 must not run.

### Readiness gate

The gate started only after every setup and corpus check below had passed. It
sampled once per minute. Each sample took the 1/5/15-minute load averages and
the mean of ten sequential `/usr/bin/true` spawns. Admission needed five
consecutive samples with one-minute load `<= 10.0` and ten-spawn mean
`<= 40 ms`, then an immediate 60-spawn confirmation `<= 40 ms` with load still
`<= 10.0`. A failed sample reset the streak.

| # | UTC, 2026-10-03 | Load 1 / 5 / 15 | 10-spawn mean (ms) | Pass | Streak |
| --- | --- | --- | --- | --- | --- |
| 1 | 15:45:49.425 | 10.23 / 29.58 / 39.65 | 15.22 | no | 0 |
| 2 | 15:46:49.436 | 9.93 / 26.08 / 37.66 | 33.37 | yes | 1 |
| 3 | 15:47:49.433 | 7.57 / 22.38 / 35.47 | 25.15 | yes | 2 |
| 4 | 15:48:49.436 | 10.53 / 20.39 / 33.90 | 22.77 | no | 0 |
| 5 | 15:49:49.433 | 6.67 / 17.52 / 31.90 | 28.38 | yes | 1 |
| 6 | 16:06:46.067 | 98.64 / 36.35 / 37.64 | 402.41 | no | 0 |
| 7 | 16:22:48.746 | 167.98 / 67.42 / 49.16 | 31.42 | no | 0 |
| 8 | 16:23:48.746 | 81.57 / 61.49 / 48.22 | 28.31 | no | 0 |
| 9 | 16:40:05.709 | 93.51 / 67.46 / 51.27 | 28.17 | no | 0 |
| 10 | 16:41:05.711 | 43.62 / 57.63 / 48.68 | 31.25 | no | 0 |
| 11 | 16:42:05.712 | 18.95 / 47.97 / 45.67 | 27.97 | no | 0 |
| 12 | 16:43:05.712 | 11.57 / 40.75 / 43.14 | 29.35 | no | 0 |
| 13 | 16:44:05.708 | 6.07 / 33.86 / 40.40 | 26.18 | yes | 1 |
| 14 | 16:45:05.713 | 5.29 / 28.57 / 37.97 | 31.08 | yes | 2 |
| 15 | 16:46:05.713 | 4.68 / 24.15 / 35.67 | 31.95 | yes | 3 |
| 16 | 16:47:05.711 | 4.70 / 20.62 / 33.57 | 22.14 | yes | 4 |
| 17 | 16:48:05.714 | 11.02 / 19.45 / 32.24 | 24.55 | no | 0 |
| 18 | 16:49:05.713 | 6.25 / 16.51 / 30.26 | 26.12 | yes | 1 |
| 19 | 16:50:05.715 | 9.56 / 15.34 / 28.87 | 24.77 | yes | 2 |
| 20 | 16:51:05.714 | 4.91 / 12.93 / 27.05 | 27.30 | yes | 3 |
| 21 | 16:52:05.716 | 3.22 / 11.01 / 25.36 | 27.50 | yes | 4 |
| 22 | 16:53:05.711 | 6.53 / 10.70 / 24.28 | 19.15 | yes | 5 |

**Confirmation:** 60 spawns from 16:53:05.904 to 16:53:07.088 UTC, mean
**19.72 ms**, one-minute load **6.53**. It passed, and the pass was admitted at
16:53:07.088 UTC.

Two gaps in the sample times are real machine stalls, not skipped samples:
5 → 6 is 17 minutes and 8 → 9 is 16 minutes, both during heavy external load.
Neither touched the admitting streak: samples 18–22 are five consecutive
one-minute samples. A 60-spawn probe taken after the pass and its attribution
phases measured a mean of 60.32 ms and a median of 36.22 ms, so load returned
once the window closed.

### Machine and toolchain

Same machine and toolchain as passes 3 and 4. No hostname or user name is
recorded.

| Property | Value |
| --- | --- |
| OS and architecture | Darwin 25.5.0, arm64 |
| Logical CPUs | 10 |
| Memory | 34,359,738,368 bytes (32 GiB) |
| Python | 3.13.13 |
| Node | v26.7.0 |
| npm | 11.19.0 |
| Git | 2.50.1 (Apple Git-155) |
| Ruff | 0.16.10 |

### Base and overlay identity

| Item | Value |
| --- | --- |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e` |
| Tracked-diff SHA-256 | `a724e3f766e5931f494cf6a5e8741cfcad76fbea274613f7323f3579c6aa81b5`, equal in source and clone |
| Source-worktree manifest SHA-256 | `94e1cfee75fb8f6b0097f762113d5d87f7cd872efea3675f2760c479ee7a5679` (7,005 files) |
| Overlay manifest SHA-256 | `a92157bf3f59a5c28743e7fff6215d3aee3688c0cb34980ce752b53b1b18f1d1` (6,743 files) |
| Files differing from the source worktree | 0 |
| Paths present only in the clone | 0 |
| Paths present only in the source worktree | 262, all under `docs-site/src/content/docs/` |

The tracked diff and source manifest differ from pass 4's because this report
and the ledger gained pass 4 in between. The overlay carried the same T15 and
T16 implementation. The 262 source-only paths are inherited generated docs
content, removed before setup so no arm inherited another build's pages. The
manifest is every included path's SHA-256, sorted, as `<sha256>  <path>` lines.

The clone was a fresh `git clone --no-hardlinks` with its own `.git` directory,
never a Git worktree. The overlay excluded `.git`, `.context`, `build/`,
`node_modules/`, `.astro/`, `dist/`, the Python and test caches, `.venv/`,
`.loop-run/`, and credential, dotfile and browser-state paths.

### Setup and commands

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t16pass5.XXXXXXXX)   # resolved, prefix-checked, trap installed
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete --exclude-from=<excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
git clean -fdX -- docs-site/src/content/docs        # drop inherited build output
make bootstrap-sites                                # setup, never timed
make site-build                                     # one untimed today build for the routing suite
```

`make bootstrap-sites` took 12.44 s and added 457 web and 466 docs-site
packages. The untimed `today` build exists because
`test_build_site_routing.py` checks the emitted changelog page and skips without
one; pass 4 had the same build in place from a trial run. Corpus generation,
the corpus commit, layout switching, page counting and cleanup all sit outside
every timed sample.

The timed command, and the only command § 7's Build performance row reads:

```bash
make site-build
```

Isolated phases, attribution only, after the whole-build pass:

```bash
npm run build --prefix web
npm run build --prefix docs-site
```

All 18 `make site-build` samples returned exit 0. So did all 24 phase samples.
No sample failed, was retried, dropped or substituted.

### Corpus: pass 4's, rebuilt byte for byte

Pass 5 reran pass 4's exact generator, recovered from the pass-4 session record.
Its SHA-256 matched the recorded value before use. The generator lived only in
the disposable clone. No permanent repository tool was added.

| Exact gate value | Required | Pass 5 |
| --- | --- | --- |
| Generator SHA-256 | `5799a245…08547` | match |
| Baseline `changelog.md` SHA-256 | `ff02ab91…ef084` (648,990 B) | match |
| Monolith input manifest SHA-256 | `571d2a8a…785f2` | match (1 entry, 5,131,928 B) |
| Fragment input manifest SHA-256 | `bb8b1939…0777d` | match (2,970 entries, 4,982,726 B) |
| Canonical generated record set SHA-256 | `ae206e10…6e262` | match, both layouts |
| Normalized record set read back from disk | `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b` | match, both layouts |
| Released records | 3,300 | 3,300 in each large layout |
| Generated plus historical | 2,970 + 330 | 2,970 + 330 |
| Released `/now/` groups | 3,160 | 3,160 in each large layout |
| Highlights | 5,648 | 5,648 in each large layout |
| Records read back, monolith / fragments | 2,970 / 2,970 | 2,970 / 2,970 |
| Records unique to either layout | 0 | 0 |

The input manifest is a JSON array of `{"bytes", "path", "sha256"}` entries,
serialized with sorted keys and `(",", ":")` separators plus one trailing
newline. The canonical serialization and UUID rules are unchanged from pass 4,
under [Corpus: rebuilt for pass 4](#corpus-rebuilt-for-pass-4-and-not-comparable-to-pass-3).

The fragments were committed in the clone as `b03560cb2a34f2036ae5ec59aba469031e3f4a5f`,
with `refs/remotes/origin/main` pointed at it. `git merge-base origin/main HEAD`
resolved to that commit and all 2,970 fragments were tracked, as in pass 4.

**Pass-5 medians are comparable to pass 4's, but not to pass 3's.** Passes 4 and
5 share one corpus. Pass 3's corpus could not be reproduced.

### Guarding checks, before timing

| Check | Result |
| --- | --- |
| Focused T16 checks | 2 passed, 49 deselected, 0.46 s |
| `tools/test_changelog.py` | 51 passed, 9.42 s |
| `tools/test_build_site_routing.py` | 110 passed, 5.08 s |
| Ruff on `tools/changelog.py` and `tools/test_changelog.py` | pass |
| `py_compile` on the same two files | pass |
| Standalone `prebuild` hooks in `web/` and `docs-site/` | both present |

Output equivalence was measured on the fragment corpus in one process, by
patching the loaded module to restore the pre-T16 call pattern. No source file
was edited.

| Check | Before T16 | After T16 |
| --- | --- | --- |
| Complete changelog | 5,368,312 B, `3fe1d172fe7f886a56babaf2a888a52bc0827a21e7befb334f312e219ec03cbb` | **identical** |
| `/now/` payload | 3,924,027 B, `d6d2fb92e50a182d5989b6be481ca6156259fe9d53231e0216a893d4c63f71af` | **identical** |
| Confined fragment reads | 2,970 | 2,970 |
| Byte bound on every read | 1,048,576 | 1,048,576 |
| Released-inventory normalizations | **8,912** | **2** |

These are the same hashes pass 4 recorded, from the same corpus.

### Predeclared order

Fixed before timing and run unchanged:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

### Whole-build durations

Times are UTC on 2026-10-03, taken when each sample ended. The largest untimed
gap between samples was 5.9 s.

| Order | Ended | Arm | Round | Duration (s) |
| --- | --- | --- | --- | --- |
| 1 | 16:53:24 | today | warm-up, discarded | 14.381826542085037 |
| 2 | 16:54:36 | monolith-10x | warm-up, discarded | 68.56223720801063 |
| 3 | 16:55:57 | fragments-10x | warm-up, discarded | 77.06983658391982 |
| 4 | 16:56:14 | today | 1 | 14.55478229187429 |
| 5 | 16:57:28 | monolith-10x | 1 | 69.98003225005232 |
| 6 | 16:58:52 | fragments-10x | 1 | 80.35360058397055 |
| 7 | 16:59:11 | today | 2 | 16.422340124845505 |
| 8 | 17:00:30 | monolith-10x | 2 | 75.34641666593961 |
| 9 | 17:02:01 | fragments-10x | 2 | 85.11264774994925 |
| 10 | 17:02:20 | today | 3 | 16.173546750098467 |
| 11 | 17:03:38 | monolith-10x | 3 | 74.40365141583607 |
| 12 | 17:05:12 | fragments-10x | 3 | 89.480232458096 |
| 13 | 17:05:30 | today | 4 | 16.49291095789522 |
| 14 | 17:06:49 | monolith-10x | 4 | 75.37305749999359 |
| 15 | 17:08:18 | fragments-10x | 4 | 83.83311866596341 |
| 16 | 17:08:36 | today | 5 | 16.07229012507014 |
| 17 | 17:09:55 | monolith-10x | 5 | 74.77085141604766 |
| 18 | 17:11:22 | fragments-10x | 5 | 83.10567395808175 |

### Validity: every arm passes

The precommitted rule, unchanged since T13:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

| Arm | Median (s) | Min (s) | Max (s) | Max − min (s) | Spread / median | Valid |
| --- | --- | --- | --- | --- | --- | --- |
| today | 16.173546750098467 | 14.55478229187429 | 16.49291095789522 | 1.9381286660209298 | 11.983% | pass |
| monolith-10x | 74.77085141604766 | 69.98003225005232 | 75.37305749999359 | 5.3930252499412745 | 7.213% | pass |
| fragments-10x | 83.83311866596341 | 80.35360058397055 | 89.480232458096 | 9.12663187412545 | 10.887% | pass |

Pass 5 is **valid**. This is the first post-T16 run in which the `today` arm
held inside the bound.

### The accepted ratios

From unrounded medians:

```text
fragment layout cost = (83.83311866596341 - 74.77085141604766) / 74.77085141604766
                     = 9.06226724991575 / 74.77085141604766
                     = 12.120%

release growth cost  = (74.77085141604766 - 16.173546750098467) / 16.173546750098467
                     = 362.303%
```

**Verdict, § 7 Build performance: `KILL`.** 12.12% is not strictly below 10%.
At this monolith median the fragment median needed to be under 82.248 s. It was
83.833 s, 1.585 s over.

For context only, against pass 3's accepted +18.69%: T16 removed about a third
of the fragment layout's relative cost. The two passes used different corpora,
so this is a direction, not a paired measurement.

### Proof the corpus was traversed

Retained stdout, identical in all 15 retained samples and all three warm-ups:

```
today          0 fragment(s),  190 released highlight group(s),  338 highlight(s)
monolith-10x   0 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
fragments-10x  2970 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
```

Every sample reported the shared projection line once and the package
`prebuild` projection line zero times, so the aggregate build still projects
once.

### Published page count

| Arm | Marketing | `/now/` | Docs |
| --- | --- | --- | --- |
| today | 251 | 201 | 267 |
| monolith-10x | **3,369** | **3,319** | **267** |
| fragments-10x | **3,369** | **3,319** | **267** |

Identical in all ten large-arm retained samples, and the same figures passes 3
and 4 recorded. Marketing counts include the `/now/` pages.

**Verdict, § 7 Published page count: `SURVIVE`.**

### Isolated phases — attribution only

Run after the whole-build pass, with pass 4's protocol: one warm-up plus three
retained samples per arm per phase, interleaved, each preceded by an untimed
`tools/build-site.py` run. 24 samples, all exit 0. **These never substitute for
the whole-build metric.**

| Phase | Arm | Warm-up (s) | Retained samples (s) | Median | Spread / median |
| --- | --- | --- | --- | --- | --- |
| web | today | 9.077 | 8.679, 7.443, 7.632 | 7.6318 | 16.19% |
| web | monolith-10x | 13.194 | 14.343, 12.384, 13.976 | 13.9764 | 14.01% |
| web | fragments-10x | 21.667 | 21.097, 21.176, 22.656 | 21.1756 | 7.36% |
| docs-site | today | 14.343 | 13.627, 14.163, 14.473 | 14.1631 | 5.97% |
| docs-site | monolith-10x | 70.318 | 70.913, 70.447, 74.116 | 70.9130 | 5.17% |
| docs-site | fragments-10x | 80.458 | 81.306, 87.585, 89.292 | 87.5854 | 9.12% |

Docs-site still dominates both large arms. By median, the fragment arm is
slower than the monolith arm by 7.20 s in web and 16.67 s in docs-site.

### Disposable clones and cleanup

Cleanup was trapped before any setup and checked the resolved target against
the exact created path and the `/private/tmp/t16pass5.` prefix before deleting.

The measured clone:

| Item | Value |
| --- | --- |
| Exact resolved path and deletion target | `/private/tmp/t16pass5.yvunLRUp` |
| Size at deletion | 1.1 GB (1,119,064 KiB) |
| `test -e` after deletion | false |
| Paths remaining with the `/private/tmp/t16pass5.` prefix | 0 |

**Three earlier setup attempts each stopped before the readiness gate and
before any timing.** Each used its own fresh clone, and each was deleted by the
same trapped cleanup:

| Attempt | Stopped at | Cause | Clone, deleted | Size |
| --- | --- | --- | --- | --- |
| 1 | overlay | the exclude `.git/` matched only a directory; this worktree's `.git` is a file | `/private/tmp/t16pass5.khGWp9v0` | 322 MB |
| 2 | clone isolation check | the check resolved a relative Git path from the wrong directory | `/private/tmp/t16pass5.93xWABq3` | 319 MB |
| 3 | guarding checks | the routing suite reported 109 passed, 1 skipped, because no site had been built yet | `/private/tmp/t16pass5.zJbOXiZs` | 939 MB |

Each recorded `test -e` false and zero remaining prefix paths. The contract
asks for exactly one clone. Four were created in sequence, never two at once.
Only the fourth reached readiness or timing. The fixes were to the harness
only: exclude `.git` as a file or directory, resolve the Git path absolutely,
and run one untimed `today` build before the tests.

### Source-worktree integrity

The source manifest was taken before the first clone and again after each
teardown, before any report edit. Every comparison matched:
`94e1cfee75fb8f6b0097f762113d5d87f7cd872efea3675f2760c479ee7a5679`, 7,005
files. HEAD stayed `ac54cc871b3078edfe6b13526827767e9e4ebf1e`. No commit, push,
stash, reset, clean, checkout or restore touched the source worktree.

### Limitations of pass 5

- **One corpus, one machine, one run.** The verdict is final for T16 by
  precommitment, not because a second run would agree to the decimal.
- **Not comparable to pass 3's medians.** The corpus differs. The pass-3 and
  pass-5 ratios are each internally valid.

## T18: the bundle ceiling's worst admitted state, valid and a survive

This section stands on its own. Plan task T18 ran on **2026-10-12**, after
plan task T16 loaded the file-safety helper once per projection and T17
added ADR-0143's monthly bundles. It is the one admitted pass at the bundle
policy's worst state for released records: the newest 1,000 records loose,
every other record in bundle parts.

**Result: valid, and `SURVIVE`.** All three arms passed the 20% spread bound.
The fragment layout costs **+7.22%** over the same records held in one file,
which is strictly below the 10% bar. That figure is at or above ADR-0143's 5%
Revisit line, which the ADR answers by lowering the 1,000-fragment ceiling.
The owner decides that change.

### Readiness gate

The gate opened only after every setup and corpus check below passed. It
sampled once per minute, and admitted the pass after five consecutive
samples with one-minute load at or below 10.0 and a ten-spawn mean at or
below 40 ms, then a 60-spawn confirmation at or below 40 ms.

| # | UTC, 2026-10-12 | Load 1 / 5 / 15 | 10-spawn mean (ms) | Pass | Streak |
| --- | --- | --- | --- | --- | --- |
| 1 | 21:19:22.529 | 17.89 / 34.88 / 51.84 | 21.63 | no | 0 |
| 2 | 21:20:22.539 | 13.11 / 30.39 / 49.00 | 21.31 | no | 0 |
| 3 | 21:21:22.538 | 10.58 / 26.62 / 46.33 | 20.00 | no | 0 |
| 4 | 21:22:22.531 | 18.66 / 25.57 / 44.56 | 20.95 | no | 0 |
| 5 | 21:23:22.539 | 12.19 / 22.46 / 42.10 | 28.77 | no | 0 |
| 6 | 21:24:22.539 | 10.66 / 20.08 / 39.87 | 17.98 | no | 0 |
| 7 | 21:25:22.539 | 9.69 / 18.07 / 37.77 | 24.13 | yes | 1 |
| 8 | 21:26:22.537 | 10.70 / 16.59 / 35.86 | 19.80 | no | 0 |
| 9 | 21:27:22.533 | 9.05 / 15.14 / 34.01 | 18.55 | yes | 1 |
| 10 | 21:28:22.539 | 8.45 / 13.84 / 32.23 | 33.31 | yes | 2 |
| 11 | 21:29:22.535 | 8.53 / 12.89 / 30.63 | 25.36 | yes | 3 |
| 12 | 21:30:22.534 | 8.37 / 12.05 / 29.10 | 107.78 | no | 0 |
| 13 | 21:31:22.536 | 80.14 / 26.69 / 33.12 | 394.16 | no | 0 |
| 14 | 21:32:22.541 | 70.48 / 38.16 / 37.28 | 24.78 | no | 0 |
| 15 | 21:33:22.541 | 33.48 / 33.42 / 35.57 | 28.38 | no | 0 |
| 16 | 21:34:22.540 | 19.57 / 29.46 / 33.94 | 26.21 | no | 0 |
| 17 | 21:35:22.541 | 12.98 / 25.66 / 32.21 | 26.57 | no | 0 |
| 18 | 21:36:22.541 | 13.33 / 23.49 / 30.95 | 21.56 | no | 0 |
| 19 | 21:37:22.541 | 10.23 / 20.77 / 29.42 | 28.48 | no | 0 |
| 20 | 21:38:22.532 | 11.82 / 19.71 / 28.46 | 19.66 | no | 0 |
| 21 | 21:39:22.541 | 9.36 / 17.57 / 27.06 | 26.23 | yes | 1 |
| 22 | 21:40:22.541 | 10.08 / 16.26 / 25.92 | 26.58 | no | 0 |
| 23 | 21:41:22.541 | 8.34 / 14.62 / 24.65 | 17.58 | yes | 1 |
| 24 | 21:42:22.541 | 11.22 / 14.49 / 23.93 | 26.15 | no | 0 |
| 25 | 21:43:22.535 | 9.66 / 13.47 / 22.90 | 33.92 | yes | 1 |
| 26 | 21:44:22.532 | 8.64 / 12.43 / 21.86 | 21.57 | yes | 2 |
| 27 | 21:45:22.531 | 7.16 / 11.31 / 20.80 | 21.42 | yes | 3 |
| 28 | 21:46:22.541 | 7.02 / 10.60 / 19.89 | 23.87 | yes | 4 |
| 29 | 21:47:22.541 | 6.80 / 9.84 / 18.97 | 21.91 | yes | 5 |

**Confirmation:** 60 spawns from 21:47:22.761 to 21:47:23.764 UTC, mean
**16.71 ms**, one-minute load **6.80**. The pass was admitted at 21:47:23.764
UTC. A 60-spawn probe after the pass and its attribution phases measured a
mean of 17.22 ms and a median of 15.36 ms.

### Machine, toolchain and identity

Same machine as passes 3–5. No hostname or user name is recorded.

| Property | Value |
| --- | --- |
| OS and architecture | Darwin 25.5.0, arm64, 10 logical CPUs, 34,359,738,368 bytes (32 GiB) |
| Python | 3.13.13 |
| Node / npm | **v26.10.0 / 11.19.1** — pass 5 ran v26.7.0 / 11.19.0 |
| Git / Ruff | 2.50.1 (Apple Git-155) / 0.16.10 |
| Base commit | `6dc2ba5f5f8bb2c3b003c21d5b29145faf44e700`, the delivery rebased onto `afcc1eeb8` |
| Tracked-diff SHA-256 | `cea3fb2f264083dfa54b91fb0b2c5fae17899dcfcf562930634c18d6574173a8`, equal in source and clone |
| Source manifest SHA-256 | `4206614e1b8d619dcdf682085c7d587fa98e4b95fdb00fc86555e75f9851cc91` (7,299 files) |
| Overlay manifest SHA-256 | `bd0c31779822915be6a721a1aa570e62ea4119c98ce1b87a59820e81b7cea404` (7,031 files) |
| Overlay differences | 0 differing files, 0 clone-only paths, 268 source-only paths, all generated docs under `docs-site/src/content/docs/` |

**T18 decides only from its own arms.** Node, npm and the base commit all
moved since pass 5, so its medians are not comparable to pass 5's. Both
passes measured the same corpus.

### Corpus: pass 4's, rebuilt byte for byte

T18 restored pass 4's baseline `docs/product/changelog.md` from
`git show ac54cc871b30:docs/product/changelog.md` with the current migration
notice applied, and required SHA-256
`ff02ab9146baff843c9f7483b589d5b521d09f585327f13b459371349d8ef084`
(648,990 bytes). It then ran pass 4's generator unchanged, SHA-256
`5799a24514f9b54b4b1347feaa880a987f5cdbff26d2506054f5fb7bad508547`.

**One input was pinned.** The generator maps a non-pack package name onto a
pack by a hash index into the sorted pack list. Upstream added the
`code-intelligence` pack after pass 4, which shifted that index: the first
setup attempt produced a monolith manifest of `bb4d3932…` instead of
`571d2a8a…` and stopped at the gate before any timing. A wrapper pins the
generator's view of the pack list to pass 4's 22 packs, all still present, so
every record still publishes. The generator file is not modified.

| Exact gate value | Required | T18 |
| --- | --- | --- |
| Monolith input manifest | `571d2a8a…785f2` | match |
| Fragment input manifest | `bb8b1939…0777d` | match |
| Canonical generated record set | `ae206e10…6e262` | match, both layouts |
| Normalized record set, read back | `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b` | match — monolith, all fragments, and bundled, the last through the one reader |
| Records read back, unique to either | 2,970 each, 0 | 2,970 each, 0 |
| Released `/now/` groups / highlights | 3,160 / 5,648 | 3,160 / 5,648 in every large layout |

### The bundled arm

T17's own part writer, `changelog.write_bundle_part`, moved every record
except the newest 1,000 in canonical order into monthly parts, byte for
byte. Read back through `collect_changelog_records`:

| Property | Value |
| --- | --- |
| Loose fragments | **1,000**, all released, **0 pending** |
| Bundled records | **1,970**, in `2026-08-00`, `2026-08-01`, `2026-09-00` and `2026-09-01` |
| Complete changelog SHA-256 | `3fe1d172fe7f886a56babaf2a888a52bc0827a21e7befb334f312e219ec03cbb` — identical to the all-fragments layout |
| `/now/` payload SHA-256 | `d6d2fb92e50a182d5989b6be481ca6156259fe9d53231e0216a893d4c63f71af` — identical to the all-fragments layout |

Those two digests are the same bytes passes 4 and 5 recorded for the
fragment layout, so storing records as bundles changed no output. The corpus
was committed in the clone as `7300e7690164c718101e49b4e3f531dac10ef2ff` with
`origin/main` repointed to it. Relayout was deterministic: `git status` stayed
empty. `python3 tools/changelog.py validate` accepted the committed corpus.

### Guarding checks, before the baseline restore

Run in the clone against the repository's current `changelog.md`, whose
digest pins describe that file:

| Check | Result |
| --- | --- |
| Focused T16 inventory and AC-B1 helper-once checks | 2 passed |
| `tools/test_changelog.py` | 118 passed |
| `tools/test_build_site_routing.py` | 115 passed |
| Ruff and `py_compile` on `tools/changelog.py`, `tools/test_changelog.py`, `tools/build-site.py` | pass |

### Whole-build durations

Fixed order: one discarded warm-up per arm, then five rounds of today,
monolith-10x, bundled-10x. Times are UTC on 2026-10-12, taken when each
sample ended. All 18 `make site-build` samples exited 0.

| Order | Ended | Arm | Round | Duration (s) |
| --- | --- | --- | --- | --- |
| 1 | 21:47:44 | today | warm-up, discarded | 18.131 |
| 2 | 21:49:01 | monolith-10x | warm-up, discarded | 72.256 |
| 3 | 21:50:24 | bundled-10x | warm-up, discarded | 74.416 |
| 4 | 21:50:41 | today | 1 | 15.596 |
| 5 | 21:51:55 | monolith-10x | 1 | 70.539 |
| 6 | 21:53:25 | bundled-10x | 1 | 80.339 |
| 7 | 21:53:43 | today | 2 | 16.177 |
| 8 | 21:55:01 | monolith-10x | 2 | 73.909 |
| 9 | 21:56:27 | bundled-10x | 2 | 77.265 |
| 10 | 21:56:45 | today | 3 | 16.336 |
| 11 | 21:58:02 | monolith-10x | 3 | 73.319 |
| 12 | 21:59:28 | bundled-10x | 3 | 76.437 |
| 13 | 21:59:45 | today | 4 | 15.820 |
| 14 | 22:01:01 | monolith-10x | 4 | 72.061 |
| 15 | 22:02:27 | bundled-10x | 4 | 77.054 |
| 16 | 22:02:47 | today | 5 | 17.395 |
| 17 | 22:04:02 | monolith-10x | 5 | 71.573 |
| 18 | 22:05:28 | bundled-10x | 5 | 77.428 |

### Validity and the accepted ratios

| Arm | Median (s) | Min – max (s) | Spread / median | Valid |
| --- | --- | --- | --- | --- |
| today | 16.1773 | 15.596 – 17.395 | 11.12% | pass |
| monolith-10x | 72.0607 | 70.539 – 73.909 | 4.68% | pass |
| bundled-10x | 77.2652 | 76.437 – 80.339 | 5.05% | pass |

```text
fragment layout cost = (77.2652 - 72.0607) / 72.0607 = 7.222%
release growth cost  = (72.0607 - 16.1773) / 16.1773 = 345.442%
```

**Verdict, § 7 Build performance: `SURVIVE`.** 7.22% is strictly below 10%.
At this monolith median the bundled arm needed to stay under 79.267 s, and it
measured 77.265 s.

**ADR-0143 Revisit: triggered.** 7.22% is at or above 5%. The spikes had
estimated 2.5–4% at this state. They measured the projection under load,
while this is the whole build on a quiet machine, so the per-fragment cost is
higher than they suggested.

### Traversal and published page count

Every sample's stdout reported the same traversal, ran the shared projection
once, and ran no package `prebuild` projection. Every bundled-arm sample also
logged the 750-fragment ceiling warning, as AC-B8 expects at 1,000 loose.

| Arm | Records read | Groups | Highlights | Marketing | `/now/` | Docs |
| --- | --- | --- | --- | --- | --- | --- |
| today | 0 | 190 | 338 | 253 | 201 | 273 |
| monolith-10x | 0 | 3,160 | 5,648 | **3,371** | **3,319** | **273** |
| bundled-10x | 2,970 | 3,160 | 5,648 | **3,371** | **3,319** | **273** |

**Verdict, § 7 Published page count: `SURVIVE`.** The two large arms matched
in all ten retained samples. Page totals are two higher than pass 5's because
the rebased site gained two marketing pages and six docs pages.

### Isolated phases — attribution only

Run after the whole-build pass: one warm-up plus three retained samples per
arm per phase, each preceded by an untimed `tools/build-site.py`. All 24
samples exited 0. These never substitute for the whole-build metric.

| Phase | Arm | Retained samples (s) | Median | Spread / median |
| --- | --- | --- | --- | --- |
| web | today | 7.848, 7.635, 7.919 | 7.8481 | 3.62% |
| web | monolith-10x | 9.905, 9.829, 10.603 | 9.9054 | 7.82% |
| web | bundled-10x | 13.177, 13.107, 13.678 | 13.1774 | 4.33% |
| docs-site | today | 11.729, 10.740, 11.392 | 11.3920 | 8.68% |
| docs-site | monolith-10x | 67.573, 67.460, 67.116 | 67.4600 | 0.68% |
| docs-site | bundled-10x | 67.850, 70.749, 70.062 | 70.0624 | 4.14% |

### Disposable clones

| Attempt | Clone | Outcome |
| --- | --- | --- |
| 1 | `/private/tmp/t18pass.r8pTNG4A` | stopped at the corpus gate before timing; deleted, `test -e` false |
| 2 | `/private/tmp/t18pass.rt0Vc6ZY` | the admitted pass; 999 MB at deletion, `test -e` false |

No `/private/tmp/t18pass.*` path remains. The source-worktree manifest
matched after both teardowns.

## Bundle attribution spikes: where pass 5's gap lives

Four spikes on 2026-10-03 located the cost pass 5 measured. They led to
[ADR-0143](../../adr/0143-released-changelog-records-move-into-monthly-bundles.md)
and to amending plan task T16. **Every figure here is attribution, not a
result.** The machine ran at load averages of 20–170, and no readiness gate
applied. The same arm measured 9.17 s in spike 1 and 7.32 s in spike 3.

### Setup

| Item | Value |
| --- | --- |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e`, with the pass-5 overlay |
| Corpus | Pass 4's, rebuilt byte for byte: monolith manifest `571d2a8a…`, fragment manifest `bb8b1939…` |
| Fragment corpus commit | Committed in each clone, with `origin/main` repointed to it, as in pass 5 |
| Clones | Four, under `/private/tmp/t16bundle.`, each deleted with `test -e` false and no prefix path left |

Projection-only samples time one fresh process running
`build-site.py::generate_changelog_views`, after one discarded warm-up, with
arms interleaved round by round.

### The whole gap is the changelog projection

Spike 1 split the build into its three steps. Each sample ran
`python3 tools/build-site.py`, then
`npm run build --prefix web --ignore-scripts`, then
`npm run build --prefix docs-site --ignore-scripts`. There was one warm-up and
four retained rounds per arm, and all 30 steps exited 0.

| Step | Monolith median (s) | Fragments median (s) |
| --- | --- | --- |
| Projection (`build-site.py`) | 6.65 | 13.89 |
| Web build | 16.18 | 13.95 |
| Docs build | 72.61 | 73.57 |

Fragments are slower only in the projection. This explains pass 4's and pass
5's isolated phases, where the fragment arm looked 7–17 s slower per package
build. Those phases ran each package's `prebuild` hook, which repeats the
projection, so each one paid the projection gap again.

### One defect, and the per-file remainder

| Spike | Arm | Retained samples (s) | Median (s) |
| --- | --- | --- | --- |
| 1 | Monolith | 0.921, 0.935, 0.947, 0.932, 0.929 | 0.932 |
| 1 | 2,970 fragments | 8.625, 8.485, 9.389, 9.174, 9.206 | 9.174 |
| 1 | All records in monthly files, prototype | 0.404, 0.488, 0.410, 0.420, 0.390 | 0.410 |
| 3 | 2,970 fragments, helper reloaded per file | 6.101, 7.315, 6.723, 10.944, 13.288 | 7.315 |
| 3 | 2,970 fragments, helper loaded once | 3.743, 3.650, 3.818, 7.876, 4.825 | 3.818 |

The reader in `tools/changelog.py` reloads the file-safety helper for every
fragment. Spike 3 counted **2,971** loads per projection, and **1** with the
helper loaded once. Paired by round, loading it once saved a median
**3.07 s**. Each fragment kept its own confined read at the 1,048,576-byte
bound. Spike 2 tried the same change, but patched a module copy the build does
not call, so it measured nothing and is not reported.

### Cost by loose-fragment count

Spike 4 loaded the helper once in every arm. It left the newest N records in
canonical order as loose fragments and grouped the rest by month into bundle
files. There was one warm-up and seven retained rounds per arm.

| Loose fragments | Retained samples (s) | Median (s) |
| --- | --- | --- |
| 2,970 | 5.47, 5.75, 5.15, 7.60, 5.15, 5.42, 4.92 | 5.415 |
| 1,000 | 6.68, 3.09, 2.31, 2.79, 3.37, 2.52, 2.07 | 2.786 |
| 300 | 1.44, 1.79, 1.51, 1.55, 1.40, 1.46, 1.45 | 1.462 |
| 0 | 0.41, 0.41, 0.40, 0.44, 0.42, 0.40, 0.37 | 0.410 |

That is about 1.6 ms per loose fragment, plus about 1 s whenever any are loose.
Over pass 5's 74.77 s monolith build, the projection-only gaps estimate about
6.0% fully loose, 2.5% at 1,000 and 0.7% at 300. A whole-build basis, which adds
pass 5's roughly 0.8 s of other gap, gives about 8% and 3–4%.

### Output and fidelity

Every fragment-sourced and bundle arm in every spike produced the same 3,160
groups and 5,648 highlights. Each produced the complete changelog `3fe1d172…`
and the `/now/` payload `d6d2fb92…`, the same bytes pass 5's equivalence proof
recorded.

The bundle prototype was not the ADR-0143 design. It made three departures:

- it skipped merge-base identity checks;
- it read its month files at a 64 MiB bound, because two of them exceeded
  1,048,576 bytes;
- it used its own record separator.

Its 0.41 s is a floor, not a design figure. Plan task T18 measures the design
itself.

## Pass 4: the post-T16 rerun, inconclusive twice

This section stands on its own. It ran on **2026-10-01**, after the amended T16
change landed in `tools/changelog.py`, and it repeats the pass-3 protocol
unchanged on a newly built corpus of the same scale.

**Result: `INCONCLUSIVE`, twice.** The protocol was executed in full twice —
run 4a, then run 4b — and in both the `today` arm's retained spread exceeded the
precommitted 20% bound. Per that rule no performance ratio is accepted from
either run, and § 7 Build performance continues to read pass 3's `KILL`. No
sample was deleted, no order was changed, no spread was rounded, and no
isolated-phase figure was substituted.

Run 4b exists because run 4a was disturbed: a 1,955-second untimed stall seized
the machine between two of its samples. Repeating the protocol was agreed before
4b's numbers were seen, and 4a is retained in full below. Run 4b was not
disturbed — its largest untimed gap between samples is 19 seconds — and its
`today` arm still failed, at 27.60%. **Two independent runs failing the same arm
is the finding.** On this machine the `today` arm is too short to hold inside the
bound: it carries a 6–7 second absolute swing on a median of 16–26 seconds, and
pass 2 failed on the same arm.

### What changed in the code between pass 3 and pass 4

Only `tools/changelog.py`'s release-membership path. Each projection now
validates and normalizes the released-version inventory once and consumes the
already-normalized inventory for every fragment, through a private
`_fragment_in_released_inventory` predicate:

```python
inventory = _normalize_released_versions(released_versions)
...
if _fragment_in_released_inventory(fragment, inventory):
```

`is_fragment_released(fragment, raw_inventory)` remains a validating public
boundary for independent callers: it normalizes, then delegates to the same
predicate. Assembly partitions pending and released fragments in one pass, so
one fragment receives one membership decision. Nothing is memoized — no file
bytes, no parsed fragment, no Git state, no rendered output.

### Run dates and machine

Run 4a ran **06:38:36–07:28:27 UTC** on 2026-10-01. Run 4b ran
**13:40:50–14:03:51 UTC** the same day. The isolated phases ran between them.

Non-identifying description. No hostname or user name is recorded. Same machine
as pass 3, with Node, npm, Python and Git pinned to the same builds, so no
toolchain change sits inside any comparison below.

| Property | Pass 4 | Pass 3 |
| --- | --- | --- |
| OS and architecture | Darwin 25.5.0, arm64 | same |
| Logical CPUs | 10 | same |
| Memory | 34,359,738,368 bytes (32 GiB) | same |
| Python | 3.13.13 | same |
| Node | v26.7.0 | same |
| npm | 11.19.0 | same |
| Git | 2.50.1 (Apple Git-155) | same |
| Bare process-spawn latency | **60.2 ms mean, 52.3 ms median**, 60 spawns of `/usr/bin/true` | 32.8 ms mean, 27.5 ms median |

**Observed noise, measured rather than assumed.** Bare process-spawn latency is
**1.8 times pass 3's**, taken on the same machine with the same probe. Every
pass-4 arm is correspondingly slower than its pass-3 counterpart, including the
two arms that passed their spread bound. The machine was under sustained
external load throughout, which is the condition the validity rule exists to
detect, and it detected it.

### Base and overlay identity

| Item | Value |
| --- | --- |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e` |
| Tracked-diff SHA-256 | `085e6df58509fc4f8c504ddac0e0fd45fffcf45497a14bebfe916c1195b32dbf` |
| Source-worktree manifest SHA-256 | `f415964edbd30debb16c4f47cea4eabcfbd03bae1ec5d56c8ffe27b1acb7438d` (7,005 files) |
| Overlay manifest SHA-256 | `c0880d83822085670f111bd0eb3442a27c05cdddf2a6d1a8b119e3cf524cae47` |
| Files in the overlay | 6,743 |
| Files differing from the source worktree | 0 |
| Paths present only in the clone | 0 |
| Paths present only in the source worktree | 262, all under `docs-site/src/content/docs/` |

Those 262 paths are inherited generated docs content, removed before corpus
construction so no arm inherited another build's pages. Every remaining file is
byte-identical to the source worktree. The manifest hash covers every path and
content hash in the overlaid tree, sorted, so it pins the exact state this pass
measured. The overlay carried the uncommitted T15 and T16 changes and every
untracked implementation file.

Pass 4 used a disposable **clone**, never a Git worktree, because
`make site-build` cleans `build/` and a worktree shares the parent's Git
directory. The overlay excluded `.git`, `.context`, `build/`, `node_modules/`,
`.astro/`, `dist/`, the Python and test caches, `.venv/`, `.loop-run/`, and
credential, dotfile and browser-state paths.

### Setup and commands

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t16pass4.XXXXXXXX)   # resolved, prefix-checked
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete --exclude-from=<excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
git clean -fdX -- docs-site/src/content/docs        # drop inherited build output
make bootstrap-sites                                # setup, never inside a timed sample
```

`make bootstrap-sites` was needed: neither `web/node_modules` nor
`docs-site/node_modules` existed in the fresh clone. It took 19.9 s and added
457 web packages (0 vulnerabilities) and 466 docs-site packages (1 low-severity
vulnerability). Dependency install, corpus generation, the corpus commit,
layout switching between samples, page counting and cleanup all sit outside
every timed sample.

The timed command, and the only command § 7's Build performance row reads:

```bash
make site-build
```

Isolated phases, attribution only:

```bash
npm run build --prefix web
npm run build --prefix docs-site
```

All 36 `make site-build` samples across the two runs returned exit 0. So did all
24 phase samples. 60 timed samples, no failure, no retry, no substitution.

### Corpus: rebuilt for pass 4, and not comparable to pass 3

**Pass-4 medians are not directly comparable to pass 3's.** Pass 3's corpus
generator was never retained, and its normalized corpus hash `99fb7383…` cannot
be reproduced because the report never recorded the serialization it was taken
over. Pass 4 therefore built its own corpus and decides its arithmetic only from
its own two large arms. Everything needed to rebuild it byte for byte is
recorded here.

The generator lived only in the disposable clone. No permanent repository tool
was added.

| Reproducibility field | Value |
| --- | --- |
| Generator SHA-256 | `5799a24514f9b54b4b1347feaa880a987f5cdbff26d2506054f5fb7bad508547` |
| Baseline `changelog.md` SHA-256 | `ff02ab9146baff843c9f7483b589d5b521d09f585327f13b459371349d8ef084` (648,990 B) |
| UUID namespace | the exact byte string `agent-ready-repo/changelog-fragment-build-cost/pass-4` |
| Monolith input manifest SHA-256 | `571d2a8a96be7125227a1a7a206a1ec75495972036dd7262070e0accc1d785f2` (1 entry, 5,131,928 B) |
| Fragment input manifest SHA-256 | `bb8b19397e022d76f7cfcd573bf788cbb6534260ab495c136571fb96cf30777d` (2,970 entries, 4,982,726 B) |
| Canonical generated record set SHA-256 | `ae206e10dfeed66fd6ca53bd0b9573c8c330a7c35acaab87f435bdb088b6e262`, identical for both layouts |
| Normalized record set read back from disk | `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b`, identical for both layouts |
| Corpus commit in the clone | `a49b6a27161cd8f89146bd275d4a835eeb3b65e5`, with `refs/remotes/origin/main` repointed at it |

**Canonical serialization rule.** A record normalizes to its date, its packages
as `(name, version)` pairs sorted ascending, and its sections in source order
with each body's leading and trailing blank lines dropped. That structure is
serialized as JSON with sorted keys, `ensure_ascii=False` and `(",", ":")`
separators. The record-set hash is SHA-256 over those lines sorted ascending and
newline-joined, with one trailing newline.

**UUID derivation rule.** For record index `i` in `0…2969`:
`digest = sha256(b"agent-ready-repo/changelog-fragment-build-cost/pass-4" + b":" + f"{i:05d}".encode())`.
Take `digest[:16]`, set byte 6 to `(b & 0x0F) | 0x40` and byte 8 to
`(b & 0x3F) | 0x80` for RFC 4122 version 4 and variant, then format lowercase
with the standard hyphens. The repository validator accepts only a lowercase
UUIDv4 whose string equals the filename stem, so the version and variant forcing
is required rather than cosmetic.

**Record construction.** The pool is every free-standing released entry in
today's changelog carrying at least one `Highlights` bullet, in document order —
190 entries holding 338 highlights. Record `i` reuses `pool[i % 190]`:

- the source entry's own ISO date, unchanged;
- the source entry's `###` subsections whose titles the fragment contract names,
  body lines verbatim, in source order. `Scope`, `Notes`, `Known gap` and
  `Upgrading` are dropped, which is what makes every pool body a valid fragment
  body;
- the source entry's package fan-out arity and names, with version `0.0.<i+1>`
  on every package in the record. That version is unique per record and orders
  below every current pack version, so the fragment arm's records publish
  through `_version_lte`.

**One deliberate departure from the pass-3 recipe, and why.** A package name the
build does not find in `packs/` cannot reach released status for a *new* version
through the pack-manifest path. Copied verbatim, such a record would publish in
the monolith arm — where inline entries define the inventory directly — and stay
pending in the fragment arm, destroying the equal scale the comparison needs. So
a non-pack name is replaced by a discovered pack, chosen as a SHA-256 index into
the sorted 22-pack list and linear-probed so one record never names the same
package twice. On this base commit exactly one name is affected:
**`agentbundle` → `desk-research`**, in the 20 pool entries that carry it.

Cyclic reuse over 2,970 records lands the established scale exactly, with no
tuning: `15 × 338 + 240 = 5,310` generated highlights, which with today's 338
gives 5,648.

| Quantity | Pass 4 | Recorded by pass 3 |
| --- | --- | --- |
| Parsed release records today | 389 | 389 |
| Beneath `[Unreleased]` | 59 | 59 |
| Today's free-standing released entries | 330 | 330 |
| Source body pool | 190 | 190 |
| Generated records | 2,970 | 2,970 |
| Large-arm total released entries | **3,300** | 3,300 |
| Released highlight groups | **3,160** | 3,160 |
| Highlights | **5,648** | 5,648 |
| `changelog.md`, today and fragment arms | 648,990 B | 648,990 B |
| `changelog.md`, monolith arm | 5,131,928 B | 5,132,870 B |
| Fragment files | 2,970 | 2,970 |
| Fragment bytes | 4,982,726 B | 4,977,110 B |

Fragment and monolith byte totals differ slightly from pass 3's because pass-4
ids come from a different, now-recorded namespace and one package name is
substituted. Every count matches.

### Equality proof, read back from disk

Both physical layouts were written, then read back — the monolith through
`parse_changelog_releases`, the fragments through the production
`collect_validated_fragments` boundary — and normalized by the canonical rule
above.

| Check | Result |
| --- | --- |
| Records read back from the monolith | 2,970 |
| Records read back from the fragments | 2,970 |
| Records present only in the monolith | **0** |
| Records present only in the fragments | **0** |
| Normalized record sets equal | **yes** |
| Normalized record set SHA-256, both sides | `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b` |

So entry count, complete body text, `Highlights`, dates, package names and
versions, and package fan-out are identical across the two large arms. Physical
layout is the only difference.

The generated fragments were **committed** in the clone and
`refs/remotes/origin/main` was pointed at that commit, so
`git merge-base origin/main HEAD` resolves to it and all 2,970 fragments are
tracked and unmodified. That models the real steady state — at ten times today's
release count almost every fragment is old and already merged — and puts each
fragment on the full identity path a real build takes.

### Proof the corpus was traversed

Retained stdout, identical in every one of the 30 retained whole-build samples
across both runs:

```
today          0 fragment(s),  190 released highlight group(s),  338 highlight(s)
monolith-10x   0 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
fragments-10x  2970 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
```

The two large arms report the **same 3,160 groups and 5,648 highlights** from
2,970 fragments versus none, so they traverse the same released groups and the
same Highlights.

Every sample in every arm also reported the shared projection line **once** and
the package `prebuild` projection line **zero** times, so the T15 orchestration
fix is intact: the aggregate build runs the shared projection once. Both
standalone hooks remain available — `web/package.json` and
`docs-site/package.json` each still carry
`"prebuild": "python3 ../tools/build-site.py --renderer-inputs"`.

### Predeclared order

Fixed before any pass-4 timing, applied identically to runs 4a and 4b, and not
changed afterwards:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

One warm-up per arm is discarded. Five retained samples per arm follow,
round-robin. Both runs executed this in full.

### Whole-build durations — run 4a

| Arm | Warm-up (discarded) | Retained samples (s) | Median | Min | Max | Spread / median | Valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| today | 15.477 | 16.595, 14.788, 14.480, 16.129, 19.233 | 16.1286 | 14.480 | 19.233 | **29.47%** | **FAIL** |
| monolith-10x | 76.444 | 70.598, 66.434, 68.157, 65.978, 72.460 | 68.1569 | 65.978 | 72.460 | 9.51% | pass |
| fragments-10x | 83.930 | 81.349, 74.729, 77.981, 80.701, 81.012 | 80.7014 | 74.729 | 81.349 | 8.20% | pass |

**The disturbance, stated exactly.** Samples ran 17–89 seconds apart for the
first thirteen of eighteen. Between `monolith-10x` round 4 (06:51:29 UTC) and
`fragments-10x` round 4 (07:25:25 UTC) the untimed interval was **1,955
seconds**. The next timed sample, `today` round 5 at 19.233 s, is that arm's
maximum and the single value that carries the spread past the bound. The sample
is retained and counted.

### Whole-build durations — run 4b

| Arm | Warm-up (discarded) | Retained samples (s) | Median | Min | Max | Spread / median | Valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| today | 27.445 | 23.616, 20.540, 26.200, 25.972, 27.709 | 25.9717 | 20.540 | 27.709 | **27.60%** | **FAIL** |
| monolith-10x | 84.239 | 89.650, 84.742, 88.207, 85.163, 87.969 | 87.9687 | 84.742 | 89.650 | 5.58% | pass |
| fragments-10x | 91.903 | 112.731, 97.882, 100.292, 100.868, 106.829 | 100.8683 | 97.882 | 112.731 | 14.72% | pass |

Run 4b completed in 23 minutes with no stall; its largest untimed interval
between samples is 19 seconds. Every arm is slower than in 4a, consistent with
the doubled process-spawn latency, and the `today` arm still failed.

### Validity: both runs are inconclusive

The precommitted rule, unchanged since T13:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

`today` measures 29.47% in run 4a and 27.60% in run 4b. Both exceed the bound,
so **both runs are `INCONCLUSIVE` and no performance ratio is accepted from
either.**

### Numbers recorded, not accepted

These are retained for provenance only. They are **not** a verdict and nothing
downstream may read them as one, because the runs that produced them failed the
validity rule.

| Quantity | Run 4a | Run 4b | Pass 3 (accepted) |
| --- | --- | --- | --- |
| Large-arm absolute gap | 12.5445 s | 12.8997 s | 14.40 s |
| `(fragments − monolith) / monolith` | 18.41% | 14.66% | 18.69% |
| `(monolith − today) / today` | 322.58% | 238.71% | — |

One observation a maintainer should not have to dig for: in both unaccepted
runs the fragment layout figure is well above the under-10% bar, and the
absolute large-arm gap barely moved from pass 3's 14.40 s despite the T16 change
removing 8,910 inventory normalizations per projection. **Nothing in pass 4
suggests the fragment layout has come under the bar.** That is a signal about
where a valid pass 5 would likely land, not a result, and § 7 Build performance
is still decided by pass 3.

### Published page count

| Arm | Marketing | `/now/` | Docs |
| --- | --- | --- | --- |
| today | 251 | 201 | 267 |
| monolith-10x | **3,369** | **3,319** | **267** |
| fragments-10x | **3,369** | **3,319** | **267** |

Identical in every one of the ten large-arm retained samples across both runs,
from a record set proved identical before timing, and identical to the three
figures pass 3 recorded. Marketing counts include the `/now/` pages.

**Verdict, § 7 Published page count: `SURVIVE`.** This criterion compares page
counts between two equal-record arms and does not read a duration, so the timing
runs' invalidity does not touch it.

### Output equivalence and guarding controls

Measured on the pass-4 fragment corpus, in one process, by patching the loaded
module to restore the pre-T16 call pattern. **No source file was edited.** The
plan's T16 criterion is byte identity of the complete changelog and the `/now/`
payload *before and after the optimization*, which is what this proves.

| Check | Before T16 | After T16 |
| --- | --- | --- |
| Complete changelog bytes | 5,368,312 | 5,368,312 |
| Complete changelog SHA-256 | `3fe1d172fe7f886a56babaf2a888a52bc0827a21e7befb334f312e219ec03cbb` | **identical** |
| `/now/` payload bytes | 3,924,027 | 3,924,027 |
| `/now/` payload SHA-256 | `d6d2fb92e50a182d5989b6be481ca6156259fe9d53231e0216a893d4c63f71af` | **identical** |
| Confined fragment reads | 2,970 | 2,970 |
| Byte bound on every read | 1,048,576 | 1,048,576 |
| Released-inventory normalizations | **8,912** | **2** |
| Fragment count / groups / highlights | 2,970 / 3,160 / 5,648 | 2,970 / 3,160 / 5,648 |

The 8,912 figure is exactly what the T16 pre-edit profile recorded for 2,970
fragments — `3 × 2,970 + 2` — so the pass-4 corpus reproduces the profiled call
shape before the fix, and the fix reduces it to one normalization per projection
regardless of fragment count. Every confined read still goes through the blessed
helper at the unchanged 1 MiB bound.

A note on scope, because the two large arms are sometimes read as owing byte
identity to each other: they cannot, and are not required to. The fragment
layout emits an `<a id="…"></a>` anchor per assembled record and its `/now/`
groups carry UUID-suffixed anchors, neither of which the monolith has any reason
to produce. What the two arms owe each other is **record** equality, proved
above from disk.

No dependency, network, cache, file-safety, schema, identity or
release-transition control was weakened. `is_fragment_released` still refuses a
malformed package name or version before membership is read; the private
predicate is reached only through a normalization that has already validated the
whole inventory; and the normalized dict-of-sets is local to one projection
call, never retained, mutated or shared.

### Checks run in the disposable environment

| Suite | Result |
| --- | --- |
| Focused T16 checks (`…normalized_once_per_projection`, `…linear_and_public_helper_validates`) | 2 passed, 49 deselected, 4.95 s |
| `tools/test_changelog.py` | 51 passed, 48.42 s |
| `tools/test_build_site_routing.py` | 110 passed, 15.24 s |

The approved red was also reproduced before accepting the implementation:
restoring only the pre-edit call pattern on a scratch copy — no source file
touched — fails the approved stub with `assert 5 == 1`, exactly as the plan
predicted for two fragments.

### Isolated phases — attribution only

One warm-up plus three retained samples per arm per phase, interleaved, each
sample preceded by an untimed `tools/build-site.py` run so its generated inputs
existed before the timer started. 24 samples, all exit 0. **These never
substitute for the whole-build metric.**

| Phase | Arm | Retained samples (s) | Median | Spread / median |
| --- | --- | --- | --- | --- |
| web | today | 7.686, 7.972, 7.678 | 7.6864 | 3.82% |
| web | monolith-10x | 12.071, 13.095, 13.328 | 13.0954 | 9.60% |
| web | fragments-10x | 20.978, 22.312, 21.818 | 21.8183 | 6.11% |
| docs-site | today | 11.808, 12.209, 11.702 | 11.8085 | 4.29% |
| docs-site | monolith-10x | 61.441, 60.907, 64.983 | 61.4413 | 6.63% |
| docs-site | fragments-10x | 69.375, 73.447, 80.473 | 73.4468 | 15.11% |

Docs-site dominates both large arms, and the fragment layout's extra cost sits
mostly there, which is where the shared projection runs.

### Disposable clone

| Item | Value |
| --- | --- |
| Exact resolved path | `/private/tmp/t16pass4.NBOeM5lA` |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e` |
| Overlay files | 6,743 after removing inherited generated docs content |
| Files differing from the source worktree | 0 |
| Corpus commit, `origin/main` repointed to it | `a49b6a27161cd8f89146bd275d4a835eeb3b65e5` |
| Size at deletion | 1.0 GB |
| Deletion proof | `test -e` → false; no `/private/tmp/t16pass4.*` remains |

The delete target was the resolved absolute path, checked against its expected
`/private/tmp/t16pass4.` prefix before running. The clone was created with
`mktemp -d` and removed after the run.

### Limitations of pass 4

- **No Build performance verdict.** Both runs failed the validity rule on the
  `today` arm. § 7 Build performance still reads pass 3.
- **Not comparable to pass 3's medians.** Pass 3's generator was not retained,
  so pass 4 built its own corpus. Cross-pass median comparison is not available;
  only within-pass arithmetic would have been, had a pass been valid.
- **The machine was loaded.** Bare process-spawn latency was 1.8 times pass 3's
  on the same hardware and probe. A valid pass needs a quieter machine, and the
  `today` arm — the shortest and most fragile of the three — is the one to watch.
- **A third run was not attempted.** Repeating until an arm happens to pass is
  the behaviour the precommitment exists to prevent. Run 4b was agreed on the
  strength of an identified instrument fault in 4a, before its numbers were
  seen; a 4c has no such justification.

## T16 pre-edit profile: the locked hypothesis is refuted

Plan task T16 holds that repeated loading of the blessed file-safety helper is
what makes the fragment projection expensive, and it gates its code change on a
profile confirming that. The profile does not confirm it. **No production code
was changed.**

The real cost is that the projection re-validates the whole released-version
inventory once per fragment, three times over. That work is **7.55 s of a
13.58 s projection**. Repeated helper loading is **2.25 s**. T16's own planning
gap is 6.695 s, so the change T16 locked in could not have closed it even if
nothing else were wrong.

| Candidate repeated cost | Seconds | Share of the projection |
| --- | --- | --- |
| Released-inventory re-validation | 7.55 | 55.6% |
| File-safety helper loading | 2.25 | 16.6% |

### What was profiled, and with what

Run on **2026-09-30**, on the pass-3 machine described under
[Run date and machine](#run-date-and-machine): Darwin 25.5.0 arm64, 10 logical
CPUs, 32 GiB, Python 3.13.13.

The profiled call is `build-site.py::generate_changelog_views`. That is the
projection `make site-build` runs once per build, and it covers the whole path:
fragment enumeration, confined reads, TOML and body parsing, merge-base identity
setup and per-record enforcement, model assembly, and both `/now/` projections.

Two instruments, because they answer different questions:

- **Timers.** A `perf_counter` wrapper and a call counter on each named phase.
  Overhead is a few microseconds per call, so its wall time is comparable to a
  real build's. **Its phase totals are the figures to read.**
- **`cProfile`.** The function-level breakdown and call counts. Deterministic
  profiling roughly triples this workload's wall time, so its times show shape,
  not magnitude.

Both run one fresh process per sample, same harness and same process shape for
both layouts. Corpus construction, the corpus commit and Git setup all sit
outside every sample.

`pstats` cannot read this profile. The unoptimized loader executes
`file_safety.py` once per fragment, which creates thousands of distinct code
objects sharing one `(filename, lineno, name)` key, and `snapshot_stats` keeps
only the last one it sees. Read naively it reports `read_confined_regular_file`
as **1 call taking 0.0018 s** when the true figure is 2,970 calls. The numbers
below aggregate `getstats()` entries by code filename and name instead.

### Phase totals, fragment arm against the monolith control

Median of three samples per arm. The fragment arm's own median wall time is
**13.580 s** (13.511, 13.580, 13.734). The monolith control is **0.945 s**
(0.931, 0.945, 1.060), so **12.635 s is fragment-only**.

| Phase | Calls | Fragment arm (s) | Monolith control (s) |
| --- | --- | --- | --- |
| **Released-inventory membership** | **8,910** | **7.844** | 0 |
| ⤷ of which inventory re-validation | 8,912 | 7.555 | 0 |
| Model assembly | 1 | 5.270 | 0.004 |
| `/now/` projection, fragment-sourced | 1 | 2.621 | 0.001 |
| Fragment collection, whole | 1 | 5.413 | 0 |
| ⤷ confined fragment reads | 2,970 | 4.400 | 0 |
| ⤷⤷ of which helper loading | 2,971 | 2.254 | 0 |
| ⤷⤷⤷ `spec_from_file_location` | 2,971 | 0.053 | 0 |
| ⤷⤷⤷ `module_from_spec` | 2,971 | 0.025 | 0 |
| ⤷⤷⤷ `exec_module`, by subtraction | 2,971 | 2.176 | 0 |
| ⤷ fragment parse, whole | 2,970 | 0.321 | 0 |
| ⤷⤷ TOML parse | 2,970 | 0.166 | 0 |
| ⤷⤷ body validation | 2,970 | 0.039 | 0 |
| ⤷ per-record identity enforcement | 2,970 | 0.197 | 0 |
| ⤷ merge-base context setup | 1 | 0.218 | 0 |
| Canonical sort | 2 | 0.003 | 0 |
| Record serialization | 2,970 | 0.010 | 0 |
| Baseline changelog parse | 1 | 0.099 | 0.821 |

Membership is nested inside model assembly and the `/now/` projection, so those
three rows are not additive: 5.270 + 2.621 = 7.891, which is the 7.844 s
membership row plus the small remainder of real assembly and rendering work.

The monolith control spends its time in the opposite place. It parses one 5 MB
file in 0.821 s and does nothing else of consequence, which is why the whole
fragment-versus-monolith gap lives in the fragment projection.

### Why the inventory work is quadratic

`tools/changelog.py`'s `is_fragment_released` calls
`_normalize_released_versions` on its entire inventory argument, on every call.
`assemble_changelog` calls it once per fragment to pick pending records and
again per fragment to pick released ones; `project_fragment_now_highlights`
calls it once more. That is three per fragment:

```text
3 × 2,970 fragments + 2 direct calls = 8,912 calls
```

Each call re-validates every package name and every version in an inventory
that, at ten times today's release count, holds roughly 3,000 versions. The
`cProfile` run counts the result exactly:

| Function | Calls | tottime (s, inflated) |
| --- | --- | --- |
| `_normalize_released_versions` | 8,912 | 14.47 |
| `re.Pattern.fullmatch` | 33,183,844 | 8.07 |
| `set.add` | 32,972,990 | 3.73 |
| `posix.open` | 5,940 | 3.80 |
| `_io.open_code` | 2,972 | 2.62 |

33.2 million regex matches is fragments × inventory size. The cost therefore
grows with the **square** of the release count, which is exactly the shape that
makes the fragment layout lose ground as the changelog grows. Helper loading, by
contrast, grows linearly.

### What each candidate change would actually recover

Measured in the disposable clone by patching the loaded module in process.
**Nothing here edited a source file.** One discarded warm-up per arm, then five
retained samples, interleaved round-robin in the order base, loader, inventory,
both.

| Arm | What it removes | Retained samples (s) | Median |
| --- | --- | --- | --- |
| base | nothing | 16.614, 16.421, 16.657, 15.759, 12.905 | 16.421 |
| loader | helper reloading — T16's locked edit | 12.265, 12.887, 12.883, 11.514, 11.062 | 12.265 |
| inventory | repeated inventory re-validation | 9.280, 7.888, 8.253, 5.192, 5.006 | 7.888 |
| both | both | 4.929, 4.051, 3.754, 2.550, 2.374 | 3.754 |

**This set is not instrument-valid and no ratio is taken from it.** Three arms
drift downward across rounds and fail the 20% spread rule — base at 22.9%,
inventory at 54.2%, both at 68.1%; only loader passes, at 14.9%. It is recorded
as attribution, on the same footing as the isolated phases in pass 3.

Pairing each arm against the base sample from its own round cancels most of that
drift. Median saving per round:

| Arm | Saving per round (s) | Median saving |
| --- | --- | --- |
| loader | 4.349, 3.534, 3.774, 4.245, 1.843 | 3.774 |
| inventory | 7.334, 8.533, 8.404, 10.567, 7.899 | 8.404 |
| both | 11.685, 12.370, 12.903, 13.209, 10.531 | 12.370 |

Every one of the 20 retained samples, across all four arms, produced the
**identical** complete changelog and `/now/` payload:

```text
complete changelog  5,362,696 B  sha256 6f199dc43d65649871aa85c9db24fb1adad6b59ed94fe71f1003fc591dcee4e0
/now/ payload       3,915,603 B  sha256 0e6d8c9d8070549f2490eeff01747e707d647b62bb14064f2e7c01c037c9a988
```

Every arm also kept **2,970 confined helper reads at a 1,048,576-byte bound** —
one per fragment, unchanged. The loader arm made **1** loader call instead of
2,971 without changing a single read.

### The gate result

T16 gates its production edit on repeated helper loading being the largest
fragment-only repeated component **and** being large enough to plausibly recover
6.695 s. It is neither:

- Inventory re-validation costs **7.55 s** against the loader's **2.25 s** — the
  loader is 3.4 times smaller, and it is not even the largest per-fragment cost,
  since the confined reads themselves cost about 2.15 s net of it.
- The loader change recovers a median **3.77 s** per projection, against a
  6.695 s target. It closes roughly **56%** of the gap on its own.

So the profile stops T16 rather than confirming it. **`tools/changelog.py` was
not edited, no fourth measurement pass ran, and both § 7 verdicts above still
read pass 3.**

The approved red stub is present and unchanged at
`tools/test_changelog.py:1772`, SHA-256
`3fb8546ec2435fdeb101dff1d03ba5274b45c783bc523cb217076886206414b5` for the whole
file, and it still fails exactly as the plan predicted:

```text
AttributeError: 'function' object has no attribute 'cache_clear'
1 failed, 49 deselected in 0.74 s
```

### What a maintainer decides next

T16 needs a plan amendment before any code is written. The evidence supports a
different owner and a different claim:

1. **`is_fragment_released` is the production owner**, not `_file_safety`. The
   fix is to normalize one inventory once per projection rather than once per
   fragment. It caches no file bytes, no parsed fragment, no Git state and no
   rendered output, so it sits inside the same trust-boundary limit T16 already
   accepts.
2. **Both changes together** bring the projection from a 16.42 s median to
   3.75 s in this clone. Pass 3 attributes about 19.0 s of a 91.45 s fragment
   build to the single projection, and the fragment layout needs to shed 6.695 s
   to reach the bar. On that arithmetic the combined change has real headroom —
   but **that is an estimate from a non-valid instrument, not a result.** Only a
   fourth whole-build three-arm pass can decide § 7 Build performance.
3. **Nothing here changes the shipped verdict.** § 7 Build performance remains
   `KILL` at +18.69% until a valid pass 4 replaces it.

### Corpus: a reconstruction, not the pass-3 artifact

The pass-3 corpus generator was never retained in the repository, and this
report's recipe does not pin the generator byte for byte. The corpus above was
rebuilt from that recipe. What it reproduces **exactly**:

| Check | Recorded by pass 3 | This reconstruction |
| --- | --- | --- |
| Parsed release records today | 389 | 389 |
| Beneath `[Unreleased]` | 59 | 59 |
| Free-standing released entries | 330 | 330 |
| Source body pool | 190 | 190 |
| Generated records | 2,970 | 2,970 |
| `changelog.md`, today and fragment arms | 648,990 B | 648,990 B |
| Fragment files | 2,970 | 2,970 |
| **Fragment bytes** | **4,977,110 B** | **4,977,110 B** |
| Released highlight groups | 3,160 | 3,160 |
| Highlights | 5,648 | 5,648 |

What it does **not** reproduce, stated plainly:

- **The monolith arm is 5,132,090 B against pass 3's 5,132,870 B** — 780 bytes
  low, 0.015%. Far below anything that moves a timing figure, but not identical.
- **The normalized corpus hash `99fb7383…` cannot be reproduced at all.** The
  report records the hash but never records the serialization it was taken over,
  so no reconstruction can be checked against it. The fragment-id namespace is
  likewise unrecorded, so generated fragment ids and anchors differ from pass
  3's. Ids are fixed-width UUIDs, which is why fragment bytes still match
  exactly.

The pool is the 190 released entries carrying `Highlights`. Each generated
record reuses one of their bodies, keeping only the `###` sections the fragment
contract names and dropping `Scope`, `Notes` and `Known gap`; that is what makes
every pool body a valid fragment body and what makes the generated Highlights
total land on 5,310, which with today's 338 gives the recorded 5,648.

**What this limits.** A profile needs equal scale between its two arms, and this
corpus delivers that — both arms traverse the same 3,160 groups and 5,648
highlights. A future pass 4 computes its ratio from its own two arms, so it
would be internally valid on this corpus too. What weakens is the comparison
*across* passes: pass 4 medians on this corpus are not strictly comparable to
pass 3's 77.05 s and 91.45 s. A maintainer who wants that comparability has to
decide whether to retain the generator this time.

### Disposable clone

| Item | Value |
| --- | --- |
| Exact resolved path | `/private/tmp/t16prof.d8MdXvJ3` |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e` |
| Overlay files | 6,743 after removing inherited generated docs content |
| Files differing from the source worktree | 0 |
| Corpus commit, `origin/main` repointed to it | `e254560d96f2e7e4933abe4022738611e83385a3` |
| Size at deletion | 288 MB |
| Deletion proof | `test -e` → false; no `/private/tmp/t16prof.*` remains |

The delete target was the resolved absolute path, checked against its expected
`/private/tmp/t16prof.` prefix before running. The clone was created with
`mktemp -d` and removed after the profile.

## Pass 3: the T15 post-optimization rerun

This section stands on its own. It repeats the pass-2 protocol unchanged on the
same corpus, after plan task T15 changed how `make site-build` orchestrates its
two package builds.

### What changed in the build between pass 2 and pass 3

Only the aggregate recipe:

```make
site-build: site-sync
	npm run build --prefix web --ignore-scripts
	npm run build --prefix docs-site --ignore-scripts
```

`site-sync` already projects the full shared model. Before T15 each of the two
package builds then ran its own `prebuild` hook, which projected the changelog
again. So one `make site-build` projected three times. Now it projects once.

`web/package.json` and `docs-site/package.json` keep their `prebuild` hooks
unchanged, so a direct `npm run build --prefix web` still projects its own
renderer inputs first. Only the two aggregate invocations suppress them.

**Checked before timing, in the clone:**

| Check | Result |
| --- | --- |
| `test_site_build_projects_once_then_suppresses_package_lifecycle_hooks` | pass |
| `test_every_npm_entry_point_projects_its_renderer_inputs_first` | pass |
| Focused `pytest` run | 2 passed, 108 deselected, 0.40 s |
| One real untimed `make site-build`, fragments arm | exit 0 in 111.4 s |

That untimed build is the direct evidence, not the construction test. Its stdout
reports `projecting released changelog highlights` **once** and the fragment
count line **once**. The `build-site: projected N renderer input(s)` line that a
`prebuild` hook prints appears **zero** times. Run directly, the same script
still prints it, so the standalone path is intact.

### Run date and machine

Run on **2026-09-30**. The whole-build protocol ran 22:48:46–23:28:21 UTC, and
the isolated phases ran 23:28:41–23:49:15 UTC.

Non-identifying description. No hostname or user name is recorded.

| Property | Value | Pass 2 |
| --- | --- | --- |
| OS and architecture | Darwin 25.5.0, arm64 | same |
| Logical CPUs | 10 | same |
| Memory | 34,359,738,368 bytes (32 GiB) | same |
| Python | 3.13.13 | same |
| Node | v26.7.0 | same |
| npm | 11.19.0 | same |
| Git | 2.50.1 (Apple Git-155) | same |
| Bare process-spawn latency | 32.8 ms mean, 27.5 ms median, 60 spawns of `/usr/bin/true` | 37.9 ms mean |

Node and npm were pinned to the same builds pass 2 used, so no toolchain change
sits inside the pass-2 comparison below.

**Observed noise.** The machine was not monitored for quiet, and no throttling
was checked for. No arm showed an outlier this time: the widest retained spread
of the three whole-build arms is 8.6% of its median, against 47.4% in pass 2.

### Base and overlay identity

| Item | Pass 3 | Pass 2 |
| --- | --- | --- |
| Base commit | `ac54cc871b3078edfe6b13526827767e9e4ebf1e` | `d72fffe55a58d2835128e2967b7d52f2090c6243` |
| Tracked-diff SHA-256 | `59d71f7a89d2e960f7477a4b5894539f0a3586542f9e09aba70b134c10eadca4` | `de74509c3e23c64990df823cd8f438bf3a0e32f25fb2a94848388bea74fc5659` |
| Overlay manifest SHA-256 | `b8a4c0e37d5be6c2dd1b3ffeff5a2d1f0fc49971d5f72c9b7352d761a1ed2b4d` | `6e87c7b97ee13a46396f7fa1128f97a031ce223de53418c9ba52b636fedd6719` |
| Files in the overlay | 7,005 | 7,008 |
| Files differing from the source worktree | 0 | 0 |
| Paths present in only one tree | 0 | 0 |

The manifest hash covers every path and content hash in the overlaid tree,
sorted, so it pins the exact state this pass measured. The overlay carried the
uncommitted T15 change to `Makefile` and `tools/test_build_site_routing.py`, and
every earlier untracked implementation file.

Pass 3 used a disposable **clone**, never a Git worktree, because
`make site-build` cleans `build/` and a worktree shares the parent's Git
directory. The overlay excluded `.git`, `.context`, `build/`, `node_modules/`,
`.astro/`, `dist/`, the Python and test caches, `.venv/` and `.loop-run/`.

Four inherited generated paths under `docs-site/src/content/docs/` were removed
before corpus construction, so no arm inherited another build's pages:
`changelog.md`, `contributing.md`, `guides/` and `packs/`. Only tracked content
remained.

### Setup and commands

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t15rerun.XXXXXXXX)
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete <excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
git clean -fdX -- docs-site/src/content/docs        # drop inherited build output
make bootstrap-sites                                # setup, never inside a timed sample
```

`make bootstrap-sites` was needed: neither `web/node_modules` nor
`docs-site/node_modules` existed in the fresh clone. It added 457 web packages
(458 audited, 5 s, 0 vulnerabilities) and 466 docs-site packages (467 audited,
6 s, 1 low-severity vulnerability), 12.3 s in total. Dependency install, corpus
generation, the corpus commit and cleanup all sit outside every timed sample.

Timed commands:

```bash
make site-build                        # the metric § 7's bar reads
npm run build --prefix web             # isolated phase, attribution only
npm run build --prefix docs-site       # isolated phase, attribution only
```

All 18 `make site-build` samples returned exit 0. So did all 24 phase samples.
42 timed samples, no failure, no retry, no substitution.

### Corpus: the same records pass 2 measured

Construction is unchanged from pass 2, and the result is provably the same
corpus. The normalized record-set hash is
`99fb73837c929fd3d0ea95835d90af7764ab7c475c79f7062ea45511ad6828f7` — **identical
to pass 1's and pass 2's**. So the three passes differ in code, not in content.

| Quantity | Value |
| --- | --- |
| Parsed release records today | 389 |
| Today's free-standing released entries | 330 |
| Large-arm total released entries | 3,300 |
| Generated records added to reach it | 2,970 |
| Real released entries in the body pool | 190 |

One canonical list of 2,970 records feeds both large arms, rendered twice — once
as inline released sections, once as fragment files — so layout is the only
difference. Each record reuses a real released entry's body byte for byte, and
only identity changes: package fan-out copied from the source entry, version
`0.0.<n>`, the source entry's real date, and a fragment id derived by SHA-256
over a fixed namespace and the record index.

Bytes of section-body text per generated record:

| min | p25 | median | p75 | max | mean | total |
| --- | --- | --- | --- | --- | --- | --- |
| 148 | 680 | 1,129 | 1,833 | 7,045 | 1,434.5 | 4,260,483 |

### Equality proof, read back from disk

Both physical layouts were written, then parsed back and normalized to
`(packages, date, sections)` with trailing blank lines trimmed.

| Check | Result |
| --- | --- |
| Records read back from the monolith | 2,970 |
| Records read back from the fragments | 2,970 |
| Records present only in the monolith | 0 |
| Records present only in the fragments | 0 |
| Normalized record sets equal | yes |

So entry count, complete body text and bytes, `Highlights`, dates, package names
and versions, and package fan-out are identical across the two large arms.

Physical layout, the only difference:

| Arm | `changelog.md` on disk | `changelog.d/` | Fragment bytes | Assembled docs page |
| --- | --- | --- | --- | --- |
| today | 648,990 B | absent | — | 650,845 B |
| monolith-10x | 5,132,870 B | absent | — | 5,136,421 B |
| fragments-10x | 648,990 B | 2,970 files | 4,977,110 B | 5,362,696 B |

The generated fragments were **committed** in the clone as
`8aa11084f0eac773b6746a3bfbbc31fc19b608d5`, and `refs/remotes/origin/main` was
pointed at that commit, so `git merge-base origin/main HEAD` resolves to it.
That models the real steady state — at ten times today's release count almost
every fragment is old and already merged — and puts each fragment on the full
identity path a real build takes.

### Proof the corpus was traversed

Retained stdout from every arm's build:

```
today          0 fragment(s),  190 released highlight group(s),  338 highlight(s)
monolith-10x   0 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
fragments-10x  2970 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
```

The two large arms report the **same 3,160 groups and 5,648 highlights** from
2,970 fragments versus none, so they traverse the same released groups and the
same Highlights. The fragment arm's generated payload confirms it reached the
renderer:

```
schemaVersion: 1
groups in generated payload: 3160
bullets: 5648
fragment-sourced groups (UUID-suffixed anchor): 2970
example anchor: core001141--2026-09-29-02123a39434e4b11be4b00376f5531aa
```

That example anchor is the same string pass 2 recorded, which is the corpus
generator's determinism shown rather than asserted.

### Predeclared order

Fixed before any pass-3 timing, and not changed afterwards:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

One warm-up per arm is discarded. Five retained samples per arm follow,
round-robin. Pass 3 executed this in full. The isolated phases ran the same
interleaved shape, one warm-up plus three retained per arm per phase, each
sample preceded by an untimed `build-site.py` run so its generated inputs
existed before the timer started.

### Whole-build durations — `make site-build`

This is the only command § 7's Build performance row reads.

| Arm | Discarded warm-up | Retained samples (s) |
| --- | --- | --- |
| today | 16.68 | 17.40, 17.63, 16.17, 17.22, 17.66 |
| monolith-10x | 78.38 | 78.14, 79.63, 77.05, 74.02, 73.86 |
| fragments-10x | 94.76 | 93.60, 91.45, 93.56, 86.13, 91.14 |

| Arm | Median | Min | Max | Spread | Spread / median | 20% rule |
| --- | --- | --- | --- | --- | --- | --- |
| today | 17.40 | 16.17 | 17.66 | 1.49 | 8.6% | pass |
| monolith-10x | 77.05 | 73.86 | 79.63 | 5.77 | 7.5% | pass |
| fragments-10x | 91.45 | 86.13 | 93.60 | 7.47 | 8.2% | pass |

### Validity: the rerun is valid

The rule is the one approved before pass 2, unchanged:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

**Every whole-build arm passes**, at 8.6%, 7.5% and 8.2%. This is the first pass
in which a ratio may be accepted at all.

### The accepted ratios

```text
fragment layout cost  (91.45 - 77.05) / 77.05 = +18.69%
release growth cost   (77.05 - 17.40) / 17.40 = +342.82%
```

The fragment layout costs 14.40 s more than the identical records held in one
file. § 7 Build performance requires under 10%, so **+18.69% is a kill**. It is
not rounded down, not averaged with an isolated-phase figure, and not waived.

The release-growth figure is recorded separately. § 7 explicitly does not own
it, and it now reads a valid arm rather than the failing one pass 2 had.

The two large arms' retained ranges still do not overlap: 73.86–79.63 s against
86.13–93.60 s. The most favourable pairing of retained samples,
`(86.13 - 79.63) / 79.63`, is +8.16%, and the least favourable,
`(93.60 - 73.86) / 73.86`, is +26.73%. The accepted figure is the median ratio
above; these two bound the observed range and neither replaces it.

### What the T15 fix did, measured

Same corpus, same machine, same protocol — so the two passes' medians are
directly comparable. Read this as explanation, not as the accepted result.

| Arm | Pass 2 median | Pass 3 median | Change | Change |
| --- | --- | --- | --- | --- |
| today | 23.69 s | 17.40 s | −6.29 s | −26.6% |
| monolith-10x | 86.57 s | 77.05 s | −9.52 s | −11.0% |
| fragments-10x | 129.41 s | 91.45 s | −37.96 s | −29.3% |

Every arm got faster, and the fragment arm gained the most. That is the expected
shape. Each `make site-build` dropped from three changelog projections to one,
and the fragment arm's projection is by far the most expensive one, because it
reads and validates 2,970 files.

Dividing each arm's saving by the two projections removed gives a rough cost per
projection: about 19.0 s for the fragment arm, 4.8 s for the monolith arm and
3.1 s for today. The gap between the two large arms' per-projection cost is
about 14.2 s — which is almost exactly the 14.40 s the fragment arm still costs
over the monolith arm in pass 3.

So the remaining overhead is, to a close approximation, **the one fragment
projection that has to happen**. T15 removed the two repeats; it could not
remove the first. Bringing the fragment layout under 10% would take making
fragment reading itself cheaper, not removing more repeats.

The pass-2 report recorded +49.5% as arithmetic it could not accept. The valid
figure is +18.69%. Both the drop and the remaining gap are explained by the
projection count.

### Published page count

Read from emitted HTML after each whole build, and **identical across all six
samples of each arm** — no sample of any arm produced a different count.

| Arm | Marketing pages | `/now/` pages | Docs pages | Total HTML | Release groups |
| --- | --- | --- | --- | --- | --- |
| today | 251 | 201 | 267 | 518 | 190 |
| monolith-10x | 3,369 | 3,319 | 267 | 3,636 | 3,160 |
| fragments-10x | 3,369 | 3,319 | 267 | 3,636 | 3,160 |

Counted the same way as pass 2: marketing is every emitted HTML file outside
`build/docs/`, `/now/` pages are counted under `build/now/`, and docs pages are
counted under `build/docs/`. Every figure matches pass 2 exactly.

The two large arms hold the same records at the same release count and emit the
same page count, which is what § 7 Published page count requires. Page count
tracks release count, not how entries are stored. Docs pages stay at 267 in
every arm, because the changelog is one docs page however its source is stored.

### Isolated phases — attribution only

Not the whole-build metric, and non-authoritative. Each npm phase re-runs
`build-site.py --renderer-inputs` through its own `prebuild` hook — which the
aggregate build no longer does — so these do not decompose a `make site-build`.

| Arm | Web warm-up | Web retained (s) | Web median | Docs warm-up | Docs retained (s) | Docs median |
| --- | --- | --- | --- | --- | --- | --- |
| today | 7.70 | 6.63, 6.92, 7.41 | 6.92 | 14.15 | 17.30, 13.89, 13.57 | 13.89 |
| monolith-10x | 14.73 | 12.00, 11.76, 13.87 | 12.00 | 76.79 | 82.78, 73.54, 71.95 | 73.54 |
| fragments-10x | 28.89 | 30.22, 30.42, 36.62 | 30.42 | 97.44 | 92.84, 89.94, 94.58 | 92.84 |

Spreads, recorded for completeness and judging nothing:

| Phase | today | monolith-10x | fragments-10x |
| --- | --- | --- | --- |
| isolated web | 11.3% | 17.6% | 21.0% |
| isolated docs-site | 26.9% | 14.7% | 5.0% |

**These medians still sum to more than the whole build they came from.** The
fragment arm's two phase medians total 123.26 s against a 91.45 s whole-build
median. The reason is now explicit: each isolated sample pays for its own
`prebuild` projection, and the aggregate build pays for none. That is exactly
why a phase sum is not the whole-build metric.

### Verdicts

```text
Verdict, § 7 Build performance: KILL
Verdict, § 7 Published page count: SURVIVE
```

**§ 7 Build performance: `KILL`.**

The rerun is instrument-valid: every arm's retained spread is at or under 8.6%
of its median. The fragment layout costs +18.69% over the same records in one
file, against a bar of under 10%.

**§ 7 Published page count: `SURVIVE`.**

3,369 marketing pages, 3,319 `/now/` pages and 267 docs pages in both large
arms, identical in all six samples each, from a record set proved identical
before timing.

### What needs a maintainer now

**Whether the fragment layout ships against § 7's 10% bar.** T13's Approach
reserves that decision: "Stop and surface if the fragment-versus-monolith ratio
is at or above the § 7 bar. Whether that blocks delivery is a Platform Core
maintainer decision, not an implementer's."

Pass 2 left two paths open. The first — re-run until the instrument is valid —
has now been taken, and it produced a decided figure instead of a range. So the
question a maintainer faces is narrower than it was:

- The figure is **+18.69%**, valid, on a quiet-enough instrument.
- The bar is under 10%. The figure is a kill, at roughly twice the bar.
- The overhead traces to the single fragment projection, not to repeated work
  that could still be removed from the orchestration.
- At today's scale the cost is far smaller: 330 released entries, not 3,300.
  This measurement deliberately prices ten times today's release count.

This report does not decide it.

### Disposable clone

| Item | Value |
| --- | --- |
| Exact resolved path | `/private/tmp/t15rerun.S0gPJ1Nr` |
| Size at deletion | 1.0 GB |
| Deletion proof | `test -e` → false; no `/private/tmp/t15rerun.*` remains |

The delete target was the resolved absolute path, checked against its expected
`/private/tmp/t15rerun.` prefix before running. The clone was created with
`mktemp -d` and removed after the pass.

### Limitations of pass 3

- **The machine was not monitored for quiet**, and no throttling check was made.
  The evidence that it was quiet enough is the validity rule passing on all
  three arms, not an observation of the machine.
- **One machine, one session.** Spawn latency here is about 32.8 ms, which
  inflates any per-process work.
- **Isolated phases are attribution, never the whole-build metric.** Two of the
  six phase arms fail the 20% rule, and their medians sum to more than the whole
  build. Nothing above is judged from them.
- **The per-projection attribution is an estimate**, obtained by dividing each
  arm's pass-2-to-pass-3 saving by the two projections removed. It assumes the
  projection count was the only thing that changed, which is what T15 changed,
  but it is arithmetic over two passes rather than a direct measurement.
- **Every generated record carries `Highlights`.** The fragment contract
  requires it, so keeping the two arms' record sets identical forces it. This
  inflates page count in **both** large arms equally and so does not affect
  their equality.


## Pass 2: the first complete whole-build run, superseded

Everything from here to [Pass 1](#pass-1-what-it-established-and-why-it-is-superseded)
records **pass 2**, which was inconclusive. Its facts are preserved as
provenance. Pass 3 above owns the current machine description, corpus proof,
durations, ratios, page counts and verdicts.

## Machine

Non-identifying description. No hostname or user name is recorded.

| Property | Value |
| --- | --- |
| OS and architecture | Darwin 25.5.0, arm64 |
| Logical CPUs | 10 |
| Memory | 34,359,738,368 bytes (32 GiB) |
| Python | 3.13.13 |
| Node | v26.7.0 |
| npm | 11.19.0 |
| Git | 2.50.1 (Apple Git-155) |
| Bare process-spawn latency | 37.9 ms for `/usr/bin/true`, mean of 60 spawns |

**Observed noise.** The machine was not monitored for quiet, and two signals say
it was not. During pass 1's setup another session ran `make build-check` and a
`pytest` suite; both had exited before timing began. In pass 2 the `today` arm's
isolated web phase recorded 39.50 s against 6.67 s and 8.31 s in its sibling
samples — a 4.8× outlier that no corpus property explains. The `today` whole-build
arm also carries the widest spread of the three. Treat the `today` arm as the
contended one. No throttling was observed, and none was checked for.

## Base and overlay identity

| Item | Pass 2 (authoritative) | Pass 1 |
| --- | --- | --- |
| Base commit | `d72fffe55a58d2835128e2967b7d52f2090c6243` | `708ae9cd1c87d16b034e183e7b577d1f80d095c4` |
| Tracked-diff SHA-256 | `de74509c3e23c64990df823cd8f438bf3a0e32f25fb2a94848388bea74fc5659` | `d3112015613d8898cc869b31278ccd31a6030ccf7935238ec4ec4a0fb67d02d5` |
| Overlay manifest SHA-256 | `6e87c7b97ee13a46396f7fa1128f97a031ce223de53418c9ba52b636fedd6719` | `d689726a688012b2639a5e14880a4cf3a42b0b8604601ca4c21c9b06686efdcb` |
| Files in the overlay | 7,008 | 6,743 |
| Files differing from the source worktree | 0 | 0 |

The tracked-diff hash is `git diff HEAD` over the source worktree. The overlay
manifest hash covers every path and content hash in the staged tree, sorted, so
it pins the exact state each pass measured.

Each pass used a disposable **clone**, never a Git worktree, because
`make site-build` cleans `build/` and a worktree shares the parent's Git
directory. The overlay excluded `.git`, `.context`, `build/`, `node_modules/`,
`.astro/`, `dist/`, the Python and test caches, and `.loop-run/`. Everything
else was copied, so each clone carried the untracked implementation —
`tools/changelog.py`, `tools/test_changelog.py`,
`docs/product/changelog-fragment-template.md`,
`tools/measure-changelog-anchor-drift.py` — and the tracked edits to
`tools/build-site.py`. A file-by-file hash comparison found zero content
differences against the source worktree in both passes.

In pass 2 the overlay also carried 262 generated, gitignored files under
`docs-site/src/content/docs/`, left by an earlier local build. They were removed
with `git clean -fdX` scoped to that directory before timing, so no arm inherited
another build's pages and the page counts below are not inflated.

## Setup and commands

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t13rerun.XXXXXXXX)
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete <excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
git clean -fdX -- docs-site/src/content/docs        # drop inherited build output
make bootstrap-sites                                 # setup, never inside a measured duration
```

`make bootstrap-sites` installed 457 web packages and 466 docs-site packages,
8 seconds each, 0 reported vulnerabilities. Dependency install is setup and sits
outside every timed sample. Corpus generation, corpus commit and cleanup are
also outside every timed sample.

Timed commands:

```bash
make site-build                        # the metric § 7's bar reads
npm run build --prefix web             # isolated phase, attribution only
npm run build --prefix docs-site       # isolated phase, attribution only
```

All 18 `make site-build` samples returned exit 0. So did all 24 phase samples.

## Corpus

### What "ten times" means here

**Ten times the total, not ten times added.** The locked plan's T13 and the
rewritten § 7 Build performance row both say "a monolith carrying ten times the
released entries". The old spike read § 7's earlier wording as ten times
*added* and reported an 11.0× model; that reading is not inherited here.

| Quantity | Value |
| --- | --- |
| Parsed release records today | 389 |
| Of those, beneath `[Unreleased]` | 59 |
| Today's free-standing released entries | 330 |
| Large-arm total released entries | 3,300 |
| Generated records added to reach it | 2,970 |

### How the records were built

One canonical list of 2,970 records feeds both large arms. Each record is
rendered twice — once as an inline released section, once as a fragment file —
so layout is the only difference.

Each generated record reuses a **real released entry's body, byte for byte**.
The source pool is the 190 of today's 330 released entries that carry a
`Highlights` section and whose body holds no heading-shaped line. That second
filter is needed because the fragment body validator has no fenced-code state
machine, so a `# comment` inside a code block would be refused as a heading.
The pool cycles, so each real body is reused about 15 times.

Per record, only identity changes:

- **Package fan-out** copies the source entry's own fan-out. Today's released
  entries run 321 single-package, four two-package, four five-package and one
  six-package. Two historical package names are not current packs
  (`agentbundle`, `credbroker`); they map by a fixed rule to `core` and
  `credential-brokers` so every generated version resolves in the release
  inventory.
- **Version** is `0.0.<n>` for n = 1..2,970. Every current pack version is
  greater, so `_released_versions_from_packs` admits all of them, and the
  headings stay unique.
- **Date** is the source entry's real release date, so the date spread mirrors
  today's.
- **Fragment id** is a fixed UUIDv4 built from SHA-256 over a fixed namespace
  and the record index. Same inputs, same corpus, every time.

### The two passes measured the same corpus

Pass 2's normalized record-set hash is
`99fb73837c929fd3d0ea95835d90af7764ab7c475c79f7062ea45511ad6828f7` — **identical
to pass 1's**. Today's changelog was also unchanged between passes: 389 parsed
records, 330 released, 190 `/now/` groups, 645,855 characters. So the two passes
differ in code, not in corpus, and their figures are directly comparable.

### Body-size distribution

Bytes of section-body text per generated record:

| min | p25 | median | p75 | max | mean | total |
| --- | --- | --- | --- | --- | --- | --- |
| 148 | 680 | 1,129 | 1,833 | 7,045 | 1,434.5 | 4,260,483 |

These are complete real bodies, not one-bullet stubs. For comparison, today's
330 released sections run 116 to 10,302 bytes with a 911-byte median.

### Equality proof

The proof is a read-back, not an assertion about the generator. Both physical
layouts were written, then parsed back and normalized to
`(packages, date, sections)` with trailing blank lines trimmed.

| Check | Result |
| --- | --- |
| Records read back from the monolith | 2,970 |
| Records read back from the fragments | 2,970 |
| Records present only in the monolith | 0 |
| Records present only in the fragments | 0 |

So entry count, complete body text and bytes, `Highlights`, dates, package
names and versions, and package fan-out are identical across the two large arms.

### Physical layout difference

| Arm | `changelog.md` on disk | `changelog.d/` | Fragment bytes |
| --- | --- | --- | --- |
| today | 648,990 B | absent | — |
| monolith-10x | 5,132,870 B | absent | — |
| fragments-10x | 648,990 B | 2,970 files | 4,977,110 B |

The generated fragments were **committed** in each clone and `origin/main` was
pointed at that commit. That models the real steady state: at ten times today's
release count almost every fragment is old and already merged. It also puts each
fragment on the full identity path through `_enforce_committed_identity`, which
is the path a real build takes.

### Proof the corpus was traversed

Retained stdout from every arm's build:

```
today          0 fragment(s),  190 released highlight group(s),  338 highlight(s)
monolith-10x   0 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
fragments-10x  2970 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
```

The two large arms report the **same 3,160 groups and 5,648 highlights** from
2,970 fragments versus none. The fragment arm's generated payload confirms it
reached the renderer:

```
schemaVersion: 1
groups in generated payload: 3160
bullets: 5648
fragment-sourced groups (UUID-suffixed anchor): 2970
example anchor: core001141--2026-09-29-02123a39434e4b11be4b00376f5531aa
```

## Timing protocol

### Predeclared order

Fixed before any pass-2 timing, and not changed afterwards:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

One warm-up per arm is discarded. Five retained samples per arm then follow,
round-robin. Pass 2 executed this in full, with no truncation and no
substitution. The isolated phases ran the same interleaved shape, one warm-up
plus three retained per arm per phase, each sample preceded by an untimed
`build-site.py` run so its generated inputs existed before the timer started.

## Whole-build durations — `make site-build`

This is the only command § 7's Build performance row reads.

| Arm | Discarded warm-up | Retained samples (s) |
| --- | --- | --- |
| today | 46.39 | 23.69, 24.90, 30.98, 19.75, 23.12 |
| monolith-10x | 97.75 | 86.57, 90.63, 93.70, 84.47, 84.01 |
| fragments-10x | 140.80 | 131.40, 141.27, 129.41, 128.79, 118.77 |

| Arm | Median | Min | Max | Spread | Spread / median | 20% rule |
| --- | --- | --- | --- | --- | --- | --- |
| today | 23.69 | 19.75 | 30.98 | 11.23 | **47.4%** | **fail** |
| monolith-10x | 86.57 | 84.01 | 93.70 | 9.69 | 11.2% | pass |
| fragments-10x | 129.41 | 118.77 | 141.27 | 22.50 | 17.4% | pass |

## Validity against the approved rule

The rule was approved before any measurement was seen:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

Applied to each arm on its own:

| Phase | today | monolith-10x | fragments-10x |
| --- | --- | --- | --- |
| whole build | 47.4% **fail** | 11.2% pass | 17.4% pass |
| isolated web | 395.1% **fail** | 38.0% **fail** | 9.2% pass |
| isolated docs-site | 19.0% pass | 10.8% pass | 11.3% pass |

The `today` whole-build arm fails. The rule says any arm failing makes the run
inconclusive, and it is not conditional on which arm, so **no ratio is accepted
or judged from this run.**

Two things are worth stating precisely, because they change what a maintainer
should do next without changing the verdict.

**First, the arms that form the fragment-layout ratio both pass.** That ratio is
the fragment median minus the monolith median over the monolith median. The
`today` arm appears only in the release-growth figure, which § 7 explicitly does
not own. So the failing arm is not one of the two the bar reads.

**Second, the two large arms' retained ranges do not overlap.** The monolith arm
spans 84.01–93.70 s and the fragment arm spans 118.77–141.27 s. Pairing the
fastest fragment sample against the slowest monolith sample — the pairing most
favourable to the design — still gives +26.8%. The bar is under 10%. No pairing
of the ten retained large-arm samples reaches it.

That is a statement about the observed range, not a point estimate, and it is not
drawn from the arm that failed the predicate. It does not convert an invalid
instrument into a result, and the verdict stays `INCONCLUSIVE`.

## Numbers recorded, not accepted

Recorded because the task requires every number even when the run is
inconclusive. **None of these is an accepted result** and none may be cited as a
measured ratio.

```text
whole build, from the medians above
  fragment layout cost  (129.41 - 86.57) / 86.57 = +49.5%
  release growth cost   (86.57 - 23.69) / 23.69  = +265.4%

bounding pairings over the retained large-arm samples
  most favourable to the design   (118.77 - 93.70) / 93.70 = +26.8%
  least favourable                (141.27 - 84.01) / 84.01 = +68.2%
```

## Published page count

Read from emitted HTML after each whole build, and **identical across all six
samples of each arm** — no sample of any arm produced a different count.

| Arm | Marketing pages | `/now/` pages | Docs pages | Release groups |
| --- | --- | --- | --- | --- |
| today | 251 | 201 | 267 | 190 |
| monolith-10x | 3,369 | 3,319 | 267 | 3,160 |
| fragments-10x | 3,369 | 3,319 | 267 | 3,160 |

The two large arms hold the same records at the same release count and emit
**the same page count**, which is what § 7 Published page count requires. Page
count tracks release count, not how entries are stored. Docs pages stay at 267
in every arm, because the changelog is one docs page however its source is
stored. Today's figures are recorded separately, as required; § 7's baseline row
of 216 pages at 157 release groups predates the 190 release groups the changelog
carries today.

## Isolated phases — attribution only

Not the whole-build metric. Each npm phase re-runs `build-site.py
--renderer-inputs` through its own `prebuild` hook, so these do not decompose a
`make site-build`.

| Arm | Web warm-up | Web retained (s) | Web median | Docs warm-up | Docs retained (s) | Docs median |
| --- | --- | --- | --- | --- | --- | --- |
| today | 7.45 | 6.67, 39.50, 8.31 | 8.31 | 15.14 | 16.15, 19.90, 19.72 | 19.72 |
| monolith-10x | 11.44 | 10.66, 16.21, 14.61 | 14.61 | 78.29 | 74.83, 75.60, 83.03 | 75.60 |
| fragments-10x | 27.85 | 37.82, 36.03, 34.51 | 36.03 | 93.88 | 106.41, 106.43, 94.41 | 106.41 |

**These medians sum to more than the whole build they came from.** The fragment
arm's two phase medians total 142.44 s against a 129.41 s whole-build median.
That is itself the proof that a phase sum is not the whole-build metric: inside
one `make site-build` the two prebuild hooks and the Astro content cache are
already warm from the `site-sync` that preceded them, and an isolated sample
pays that cost again. Read these as attribution and nothing else.

Both large arms emit the same page count, so the fragment arm's extra phase
time is fragment reading and assembly plus a slightly larger assembled docs
page — 5,362,696 bytes against the monolith arm's 5,136,434.

## Verdicts — pass 2, superseded by pass 3

**§ 7 Build performance: `INCONCLUSIVE`.**

All 18 whole builds completed, so the metric exists for the first time. The
`today` arm's retained spread is 47.4% of its median, and the rule approved
before the run refuses a ratio when any arm exceeds 20%.

**§ 7 Published page count: `SURVIVE`.**

3,369 marketing pages, 3,319 `/now/` pages and 267 docs pages in both large
arms, identical in all six samples each, from a record set proved identical
before timing.

## What needed a maintainer after pass 2, now answered by pass 3

Pass 3 took the first of the two paths below and produced a decided figure.
The live question is in
[What needs a maintainer now](#what-needs-a-maintainer-now).

**Whether the fragment layout ships against § 7's 10% bar.** T13's Approach
reserves that decision: "Stop and surface if the fragment-versus-monolith ratio
is at or above the § 7 bar. Whether that blocks delivery is a Platform Core
maintainer decision, not an implementer's." No pairing of the ten retained
large-arm samples puts the design within the bar, and the closest is +26.8%.

Two paths, and this report does not choose between them:

1. **Re-run the `today` arm until it satisfies the predicate**, then read the
   ratio and record a decided verdict. The cost is low now — the full 18-sample
   protocol took about 35 minutes. The `today` arm is the fastest and so the most
   jitter-sensitive, and it carried a 4.8× outlier in the same session, so a
   quiet machine is the whole task.
2. **Decide on the range instead.** The two large arms' retained ranges are
   disjoint and the bar is 10%. A maintainer may judge that sufficient without a
   further pass.

Pass 1's two findings are both already fixed in the tree this pass measured: the
`make site-build` break, and the per-fragment Git fan-out. Neither is open.

## Pass 1: what it established and why it is superseded

Pass 1 ran against base `708ae9cd1` and produced no whole-build figure, because
`make site-build` exited 2 on **all three arms**, today's unmodified corpus
included. `generate_changelog_views` wrote
`docs-site/src/content/docs/changelog.md` with a bare `write_text`, skipping the
Starlight frontmatter that `copy_file` supplied at that commit, and the docs
collection schema rejected the page with `title: Required`.

Pass 1 also counted, by instrumenting `_run_git`, that identity validation ran
**five Git subprocesses per fragment** — one each of `rev-parse`, `merge-base`,
`diff`, `ls-files` and `show`. At 2,970 fragments that was 14,850 spawns per
`build-site.py` run and 44,550 per `make site-build`, because both npm
`prebuild` hooks re-validated the whole directory. Per fragment: 413 ms with
enforcement on against 2.4 ms with it off. The fragment arm's site-sync median
was 1314.08 s, which is why pass 1 could not run the protocol as specified.

Both are fixed in the tree pass 2 measured. Validation now resolves the
repository root, the merge base, one directory-wide changed-path read and one
tracked-path read per pass, and skips the base blob for a path Git reports
unchanged. **Pass 1's fragment-arm durations therefore describe code that no
longer exists and must not be cited as current.** Its corpus, equality proof,
machine description and page-count result all carried forward unchanged.

## Limitations of pass 2

- **No accepted ratio.** The `today` arm fails the approved dispersion rule at
  47.4%. Every ratio above is arithmetic over medians, recorded and not accepted.
- **The machine was not monitored for quiet**, and two signals say it was not:
  concurrent heavy work by another session during pass 1's setup, and a 4.8×
  outlier in pass 2's `today` web phase.
- **One machine, one session.** Spawn latency here is about 37.9 ms, roughly ten
  times an unmanaged machine's, which inflates any per-process work.
- **Isolated phases are attribution, never the whole-build metric.** Their
  medians sum to more than the whole build, as shown above.
- **Every generated record carries `Highlights`.** The fragment contract
  requires it, so keeping the two arms' record sets identical forces it. Today
  only 190 of 330 released entries carry one. The large arms therefore project
  more `/now/` groups per entry than today's corpus does, which inflates page
  count in **both** large arms equally and so does not affect their equality.
- **The release-growth figure is the weakest number here.** It is the one ratio
  that reads the failing arm, and § 7 does not own it.

## Disposable clones

| Pass | Exact resolved path | Size | Deletion proof |
| --- | --- | --- | --- |
| 3 | `/private/tmp/t15rerun.S0gPJ1Nr` | 1.0 GB | `test -e` → false; no `/private/tmp/t15rerun.*` remains |
| 2 | `/private/tmp/t13rerun.04f7nIIp` | 1.0 GB | `test -e` → false; no `/private/tmp/t13rerun.*` remains |
| 1 | `/private/tmp/t13-buildcost.9tLaEfdC` | 1.0 GB | `test -e` → false; no `/private/tmp/t13-buildcost.*` remains |

All three delete targets were the resolved absolute path, checked against its expected
prefix before running. Each clone was created with `mktemp -d` and removed
after its pass.
