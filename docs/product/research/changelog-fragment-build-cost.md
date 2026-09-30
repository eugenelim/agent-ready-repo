# Changelog fragment build cost — three-arm measurement run

Plan task T13 prices the delivered fragment layout against a monolith holding
the same records, at ten times today's released-entry count. This is the
re-measurement the
[assembly spike](changelog-fragment-assembly-spike.md) asked for: its control
arm ranged from 22.92 s to 75.41 s on identical input, so its `+66.08%` figure
carried no error bound.

- **Run date:** 2026-09-30. The run started 2026-09-29 22:53 and ended
  2026-09-30 01:53, local time.
- **Verdict, § 7 Build performance:** `INCONCLUSIVE`. Two separate reasons, each
  sufficient on its own. `make site-build` does not complete on this tree, so
  the metric the bar reads cannot be produced at all. And the retained spreads
  of the substitute phase measurement fail the approved validity rule.
- **Verdict, § 7 Published page count:** `SURVIVE`. The two large arms emit
  3,369 marketing pages and 3,319 `/now/` pages each, from an identical record
  set laid out two different ways.
- **Needs a Platform Core maintainer decision.** Two findings below are
  delivery-blocking and are not an implementer's call: the `make site-build`
  break, and the per-fragment Git fan-out.

## The headline before the numbers

`make site-build` fails on **all three arms**, including today's unmodified
corpus. The failure is in the delivered T0–T12 tree, not in the corpus this run
built. See [The build is broken](#the-build-is-broken).

Once that is fixed, the second finding still stands. Validating one fragment
runs **five Git subprocesses**. At 2,970 fragments that is 14,850 process
spawns per `build-site.py` run, and `make site-build` runs `build-site.py`
three times — 44,550 spawns per build. On this machine one `build-site.py` run
took about 21 minutes in the fragment arm against about 4 seconds in the
monolith arm. See [Where the cost lives](#where-the-cost-lives).

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

That last row matters more than it looks. It is roughly ten times what an
unmanaged machine costs, and it multiplies any design that spawns a process per
record.

**Observed noise.** During setup, before any timed sample, another session on
this machine ran `make build-check` and a `pytest` suite. Both had exited before
the timed protocol began. Nothing monitored the machine for the three hours the
protocol then ran, so this run does not claim the machine stayed quiet
throughout. No throttling was observed, and none was checked for.

## Base and overlay identity

| Item | Value |
| --- | --- |
| Base commit | `708ae9cd1c87d16b034e183e7b577d1f80d095c4` |
| Tracked-diff SHA-256 | `d3112015613d8898cc869b31278ccd31a6030ccf7935238ec4ec4a0fb67d02d5` |
| Overlay manifest SHA-256 | `d689726a688012b2639a5e14880a4cf3a42b0b8604601ca4c21c9b06686efdcb` |
| Files in the overlay | 6,743 |
| Files differing from the source worktree | 0 |

The tracked-diff hash is `git diff HEAD` over the source worktree. The overlay
manifest hash covers every path and content hash in the staged tree, sorted, so
it pins the exact T0–T12 state that was measured.

The overlay excluded `.git`, `.context`, `build/`, `node_modules/`, `.astro/`,
`dist/`, the Python and test caches, and `.loop-run/`. Everything else was
copied, so the clone carried the untracked implementation: `tools/changelog.py`,
`tools/test_changelog.py`, `docs/product/changelog-fragment-template.md`,
`tools/measure-changelog-anchor-drift.py` and the tracked edits to
`tools/build-site.py`. A file-by-file hash comparison found zero content
differences against the source worktree.

## Setup and commands

The run used a disposable **clone**, never a Git worktree, because
`make site-build` cleans `build/` and a worktree shares the parent's Git
directory.

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t13-buildcost.XXXXXXXX)
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete <excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
make bootstrap-sites                       # setup, never inside a measured duration
```

`make bootstrap-sites` installed 457 web packages and 466 docs-site packages,
8 seconds each, 0 reported vulnerabilities. Dependency install is setup and sits
outside every timed sample. Corpus generation and cleanup are also outside every
timed sample.

Timed commands:

```bash
python3 tools/build-site.py                # the site-sync phase
npm run build --prefix web                 # isolated Astro web phase
npx astro build                            # run inside docs-site/, see the note below
make site-build                            # ATTEMPTED; fails on every arm
```

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
- **Fragment id** is a fixed UUIDv4 built from SHA-256 over a fixed
  namespace and the record index. Same inputs, same corpus, every time.

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
| Normalized record-set SHA-256 | `99fb73837c929fd3d0ea95835d90af7764ab7c475c79f7062ea45511ad6828f7` |

So entry count, complete body text and bytes, `Highlights`, dates, package
names and versions, and package fan-out are identical across the two large arms.

### Physical layout difference

| Arm | `changelog.md` on disk | `changelog.d/` | Fragment bytes |
| --- | --- | --- | --- |
| today | 648,990 B | absent | — |
| monolith-10x | 5,132,870 B | absent | — |
| fragments-10x | 648,990 B | 2,970 files | 4,977,110 B |

The generated fragments were **committed** in the clone and `origin/main` was
pointed at that commit. That models the real steady state: at ten times today's
release count almost every fragment is old and already merged. It also means
each fragment takes the full identity path through
`_enforce_committed_identity`, which is the path a real build takes.

### Proof the corpus was traversed

Retained stdout from the site-sync phase:

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

## The build is broken

`make site-build` returns exit code 2 on the **today** arm — before any
generated corpus is involved. The web phase succeeds, then the docs-site phase
fails:

```
[InvalidContentEntryDataError] docs → changelog data does not match collection schema.

  title**: **title: Required

  Location:
    docs-site/src/content/docs/changelog.md:0:0
```

**Cause.** `generate_changelog_views` writes that destination directly:

```python
changelog_out.write_text(rendered_changelog, encoding="utf-8")   # tools/build-site.py:1659
```

At the base commit the same destination was written through
`copy_file(changelog_src, changelog_dst, rewriter=_rewrite_changelog)`, and
`copy_file` adds Starlight frontmatter to any file that lacks it
(`_inject_frontmatter`, `tools/build-site.py:477`, called at line 1006). The new
writer skips that step, so the page reaches Starlight with no `title`, and the
docs collection schema rejects it.

**Proof of cause.** Prepending `---\ntitle: "Changelog"\n---` to that generated,
gitignored file and running `npx astro build` inside `docs-site/` succeeded:
267 pages in 17.42 s. Nothing in the implementation was edited; T13 is a
measurement task.

This is why every `make site-build` figure is absent below. It is also why the
isolated docs-site phase had to be run as `npx astro build` rather than
`npm run build --prefix docs-site`: that script's `prebuild` hook regenerates
the same file without frontmatter, so the phase fails the same way.

## Where the cost lives

This section is counting, not timing. It holds whatever the machine does.

`collect_validated_fragments` calls `validate_fragment` with immutability
enforcement on, which calls `_enforce_committed_identity` per fragment.
Instrumenting `_run_git` over 20 committed fragments recorded **100 Git
subprocesses — exactly 5.0 per fragment**, one each of `rev-parse`,
`merge-base`, `diff`, `ls-files` and `show`.

| Quantity | Value |
| --- | --- |
| Git subprocesses per fragment | 5 |
| Per `build-site.py` run, at 2,970 fragments | 14,850 |
| `build-site.py` runs inside one `make site-build` | 3 |
| Git subprocesses per `make site-build` | 44,550 |

The three runs are the `site-sync` target plus the `prebuild` hook in each of
`web/package.json` and `docs-site/package.json`. Both hooks call
`build-site.py --renderer-inputs`, which reaches
`report_changelog_views(..., fragments=...)` and re-validates the whole
directory.

At this machine's 37.9 ms bare spawn latency, 14,850 spawns cost at least
563 seconds — 9.4 minutes — from spawn overhead alone, before Git does any work.
Measured Git spawns here ran about 88 ms each.

Parsing is not the problem. The same 100 fragments validated in **2.4 ms each**
with identity enforcement off, against **413 ms each** with it on.

## Timing protocol

### Predeclared order

Fixed before any timing below was taken, and not changed afterwards:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

One warm-up per arm is discarded. Retained samples then follow, round-robin.

### Two declared deviations

1. **The fragment arm is truncated to two retained samples.** One fragment-arm
   `build-site.py` run takes about 21 minutes, so five retained samples plus a
   warm-up would need over two hours for that arm alone, and the full
   `make site-build` protocol would need about 6.5 hours of quiet machine. The
   truncation was approved before timing and keeps the round-robin order intact.
2. **`make site-build` is replaced by its phases**, because it does not
   complete. § 7's threshold reads `make site-build` only, so nothing below is
   offered as the whole-build metric.

The docs-site phase pass ran the three arms **in sequence, not interleaved**,
because each arm needs its own untimed site-sync first. A session-level trend
cannot be separated there. Treat those three medians as the weakest numbers in
this report.

## Retained durations

### Site-sync phase — `python3 tools/build-site.py`

| Arm | Discarded warm-up | Retained samples (s) | n |
| --- | --- | --- | --- |
| today | 3.41 | 3.97, 3.34, 3.03, 3.26, 2.84 | 5 |
| monolith-10x | 4.57 | 3.99, 5.05, 4.02, 4.51, 3.89 | 5 |
| fragments-10x | 1392.72 | 1244.52, 1383.63 | 2 |

| Arm | Median | Min | Max | Spread | Spread / median | 20% rule |
| --- | --- | --- | --- | --- | --- | --- |
| today | 3.26 | 2.84 | 3.97 | 1.13 | **34.7%** | **fail** |
| monolith-10x | 4.02 | 3.89 | 5.05 | 1.16 | **28.9%** | **fail** |
| fragments-10x | 1314.08 | 1244.52 | 1383.63 | 139.11 | 10.6% | pass, but n = 2 |

### Isolated Astro web phase — `npm run build --prefix web`

Attribution only. This command includes its own `prebuild` hook, so the
fragment arm's number is mostly that hook, not Astro.

| Arm | Discarded warm-up | Retained samples (s) | Median | Spread / median | 20% rule |
| --- | --- | --- | --- | --- | --- |
| today | 9.65 | 8.41, 9.46, 9.00 | 9.00 | 11.7% | pass, n = 3 |
| monolith-10x | 16.74 | 12.22, 14.35, 15.38 | 14.35 | **22.0%** | **fail** |
| fragments-10x | none | 1479.06 | 1479.06 | not computable | n = 1 |

### Isolated Astro docs-site phase — `npx astro build` in `docs-site/`

Attribution only, weakest numbers in this report, and not the command § 7
names. Each arm's generated inputs were prepared by an untimed site-sync before
its timer started, then the generated changelog page had `title` frontmatter
restored so Astro would accept it.

| Arm | Discarded warm-up | Retained samples (s) | Median | Spread / median | Pages | Generated page bytes |
| --- | --- | --- | --- | --- | --- | --- |
| today | 16.46 | 15.14, 14.57, 14.74 | 14.74 | 3.9% | 267 | 650,858 |
| monolith-10x | 72.30 | 16.13, 16.28, 16.59 | 16.28 | 2.8% | 267 | 5,136,434 |
| fragments-10x | 69.87 | 12.05, 10.13, 10.44 | 10.44 | 18.4% | 267 | 5,362,709 |

The fragment arm reads faster than today's arm here on a larger input. Arms ran
in sequence, so that ordering cannot be split out from an Astro content-cache
effect. No claim is made from this table beyond the page count, which is 267 in
every arm: the changelog is one docs page however its source is stored.

## Validity against the approved rule

The rule was approved before any measurement was seen:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

Applied to each arm on its own:

| Phase | today | monolith-10x | fragments-10x |
| --- | --- | --- | --- |
| site-sync | 34.7% **fail** | 28.9% **fail** | 10.6% pass, n = 2 |
| web | 11.7% pass | 22.0% **fail** | n = 1 |
| docs-site | 3.9% pass | 2.8% pass | 18.4% pass |

Arms fail the rule in both phases that separate the arms. **No performance ratio
is accepted or judged from this run.** The instrument is not softened into a
direction.

Why it failed is worth naming: today's and the monolith's site-sync medians are
3–4 seconds, so roughly one second of ordinary machine jitter is already 25–35%
of the median. The absolute spreads, 1.13 s and 1.16 s, are nearly identical
across those two arms. The dispersion is a floor of this machine, not a property
of either corpus.

## Numbers recorded, not accepted

Recorded because the task requires every number even when the run is
inconclusive. **None of these is an accepted result**, and none may be cited as
a measured ratio, because the arms above fail the validity predicate and because
`make site-build` — the only command § 7's bar reads — never completed.

```text
site-sync phase, from medians in the table above
  fragment layout   (1314.08 - 4.02) / 4.02 = +32,589%   (about 327x)
  release growth    (4.02 - 3.26) / 3.26    = +23.3%

isolated web phase, from medians in the table above
  fragment layout   (1479.06 - 14.35) / 14.35 = +10,207%  (about 103x)
  release growth    (14.35 - 9.00) / 9.00     = +59.4%
```

The § 7 bar is under 10% on `make site-build`. These figures sit three orders of
magnitude away from it, which is consistent with the subprocess count in
[Where the cost lives](#where-the-cost-lives) and no tightening of the
instrument brings it near the bar. That reasoning does not turn
an invalid instrument into a result. It is why a maintainer decision is needed
now rather than after a re-run.

## Published page count

Read from emitted HTML after each isolated web build, and stable across every
repeat of each arm.

| Arm | Marketing pages | `/now/` pages | Docs pages | Release groups |
| --- | --- | --- | --- | --- |
| today | 251 | 201 | 267 | 190 |
| monolith-10x | 3,369 | 3,319 | 267 | 3,160 |
| fragments-10x | 3,369 | 3,319 | 267 | 3,160 |

The two large arms hold the same records at the same release count and emit
**the same page count**, which is what § 7 Published page count requires. Page
count tracks release count, not how entries are stored. Today's figures are
recorded separately, as required; § 7's baseline row of 216 pages at 157 release
groups predates the 190 release groups the changelog carries today.

## Verdicts

```text
SURVIVE / KILL / INCONCLUSIVE lines, one per § 7 row
```

**§ 7 Build performance: `INCONCLUSIVE`.**

Two separate reasons. `make site-build` does not complete on this tree, so
the metric the bar reads was never produced. And the substitute phase
measurements fail the approved 20% validity rule in both arms that carry the
comparison.

**§ 7 Published page count: `SURVIVE`.**

3,369 marketing pages and 3,319 `/now/` pages in both large arms, from a record
set proved identical before timing, differing only in physical layout.

## What needs a maintainer

Neither item is an implementer's call.

1. **`make site-build` is broken on the current tree.** Described in
   [The build is broken](#the-build-is-broken), with the cause traced to one
   line and the fix shown on a generated file. No gate caught it: the
   source worktree's `build/` directory holds only
   `product-changelog.md` from a `tools/changelog.py render` run, so no site
   build has been run against this implementation.
2. **Five Git subprocesses per fragment, 44,550 per build at 10× scale.** This
   is a counted structural fact, not a timing estimate. Whatever the 10% bar
   turns out to measure once the build runs again, a design that spawns a
   process per record per build phase is the thing to decide about.

## Limitations

- **This run cannot resolve the 10% bar.** It did not produce a single
  `make site-build` sample. § 7's threshold reads that command and nothing else.
- **No accepted ratio.** Arms fail the approved dispersion rule. Both phase
  ratios are recorded as arithmetic over medians and are not results.
- **The fragment arm has two retained site-sync samples and one web sample.**
  Below the five the protocol asks for, by an approved time budget.
- **The docs-site phase pass was sequential, not interleaved.** Its ordering
  and any Astro content-cache effect cannot be split out.
- **The machine was not monitored for quiet.** Concurrent heavy work by another
  session was observed during setup and had exited before timing. Nothing
  watched the following three hours.
- **Every generated record carries `Highlights`.** The fragment contract
  requires it, so keeping the two arms' record sets identical forces it. Today
  only 190 of 330 released entries carry one. The large arms therefore project
  more `/now/` groups per entry than today's corpus does, which inflates page
  count in **both** large arms equally and so does not affect their equality.
- **One machine, one session.** Spawn latency here is about 37.9 ms, roughly ten
  times an unmanaged machine's. That amplifies the per-fragment subprocess
  design and is a large part of why the absolute fragment-arm durations are what
  they are. The subprocess *count* does not depend on the machine.
- **Isolated phases are attribution, never the whole-build metric.** Both npm
  phases re-run `build-site.py --renderer-inputs` through a `prebuild` hook, so
  a phase sum would double-count fragment validation.

## Disposable clone

| Item | Value |
| --- | --- |
| Exact resolved path | `/private/tmp/t13-buildcost.9tLaEfdC` |
| Size before deletion | 1.0 GB |
| Deletion | `rm -rf -- /private/tmp/t13-buildcost.9tLaEfdC` |
| Proof | `test -e /private/tmp/t13-buildcost.9tLaEfdC` → false; no `/private/tmp/t13-buildcost.*` path remains |

The delete target was the resolved absolute path, checked against the
`/private/tmp/t13-buildcost.` prefix before running. The clone was created with
`mktemp -d` and removed after the run.
