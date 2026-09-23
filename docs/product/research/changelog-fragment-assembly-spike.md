# Changelog fragment assembly — measurement spike

Throwaway prototype measuring four claims the per-update changelog design of
[ADR-0123](../../adr/0123-product-changelog-per-update-sources-and-generated-views.md)
makes and nothing in this repository had measured: that concurrent updates merge
independently, that assembly is deterministic, that `/now/` survives cutover
unchanged, and what the design costs the site build at scale.

- **Run date:** 2026-09-23
- **Owner:** eugenelim, Platform Core maintainer
- **Base:** `93bf9cc9e`, 351 parsed release records — 59 beneath `[Unreleased]`,
  292 free-standing released entries — projecting 157 `/now/` groups and 281
  bullets at `schemaVersion` 1, from a 598,239-byte `docs/product/changelog.md`
- **Verdict:** **survive.** Merge independence, determinism and `/now/` parity
  all clear their thresholds. Build cost misses its threshold and does not enter
  the aggregation — see [Verdict](#verdict)
- **Scope:** evidence only. No production code, schema, gate or migration was
  written. The assembler prototype lives outside the repository and was deleted
  with the clone it ran in; the one tracked artifact is
  [`tools/measure-changelog-fragment-merges.py`](../../../tools/measure-changelog-fragment-merges.py),
  wired to no gate and no Makefile target.
- **Compare against:**
  [Changelog fragmentation — feasibility spike](changelog-fragmentation-spike.md),
  whose closing known-unknown was randomized fragment enumeration. Measurement 2
  below answers it. That spike also ruled out fragmenting the *whole* changelog
  under two ordering schemes; this spike measures the shape that survived —
  history frozen, new updates fragmented.

## What this spike measures

Four claims, each paired with the arm that makes its figure readable. A bare
treatment figure is reported as inconclusive rather than as a result, because a
zero is equally consistent with the claim holding and with a harness that never
exercised the path.

| # | Claim | § 7 row | Arm that makes it readable |
| --- | --- | --- | --- |
| 1 | Concurrent updates do not collide | Mergeability | Monolith control arm |
| 2 | Assembly is enumeration-order independent | Determinism | Sort-removed mutation arm |
| 3 | Cutover changes no published byte | Historical compatibility, Content integrity | Today's live payload |
| 4 | Scale does not regress the build | Build performance | Unmodified build of the same revision |

## Method

The measurement script is tracked because its figure is the one a reader is most
likely to want to re-derive. The assembler prototype is not: it is throwaway, it
lives outside the repository, and it is reconstructed from this document rather
than maintained. Both import `tools/build-site.py` by path, so the prototype and
production agree about which `##` lines are real headings and about how a
`/now/` payload is shaped — the same seam the fragmentation spike used.

A fragment is TOML front matter delimited by `+++` carrying `schema`, `id`,
`date`, `heading` and `packages`, then a Markdown body whose only required
section is `Highlights`. The prototype validates nothing beyond what a
measurement needs; refusal behaviour is delivery-spec scope.

**The anchor is assigned, not slugged.** A fragment group's `changelogAnchor` is
`change-` plus its `id`'s 32 hexadecimal digits. It cannot be derived from
heading text: `_slug_base` strips `[`, `]` and the em dash and appends a `-N`
duplicate counter, so `[core][2.27.1] — 2026-09-23` slugs to
`core2271--2026-09-23`, and that slug moves when a neighbouring heading is
added. Assigning from fragment identity is the design property measurement 3
tests.

Every figure below comes from one of four retained runs, quoted verbatim in its
own section. Figures appearing only in framing prose are not measurements.

## Measurement 1 — fragment branches merge clean where monolith branches do not

Twenty synthetic branches per arm, built off `93bf9cc9e` as detached commit
objects through a scratch `GIT_INDEX_FILE` so the run cannot disturb a worktree
a coordination lease may be sharing. Each fragment-arm branch adds one
`docs/product/changelog.d/<uuid>.md` and nothing else; each control-arm branch
instead prepends one release section to `docs/product/changelog.md` at the
shared insertion anchor a new release actually takes. All 190 unordered pairs of
each arm are replayed with
`git merge-tree --write-tree --merge-base=<base>`.

Pairs bucket on **exit status**, not on output text. A clean merge writes only a
tree oid to stdout, so a text scan cannot separate a clean pair from a failed
invocation — and a clean fragment arm is the survive threshold, so that
confusion would invalidate the run rather than degrade it. Two hand-built pairs
exercise the classifier before either figure is taken.

```
$ python3 tools/measure-changelog-fragment-merges.py
base commit: 93bf9cc9ee821e4aed8ba677b52f064bbd5331d8
branches per arm: 20   unordered pairs per arm: 190

classifier self-check (runs before either arm's figure is taken):
  PASS  known-conflicting pair: exit 1 (want 1)
  PASS  known-clean pair: exit 0 (want 0)

fragment arm
  pairs replayed          : 190
  clean (exit 0)          : 190
  conflicting (exit 1)    : 0
  errored (any other exit): 0
control arm
  pairs replayed          : 190
  clean (exit 0)          : 0
  conflicting (exit 1)    : 190
  errored (any other exit): 0
```

The separation is total: every pair conflicts in the monolith arm and none does
in the fragment arm. The error bucket is empty in both, so neither figure is a
harness artefact. A clean-checkout run exits 0 and leaves `git status
--porcelain` empty.

**SURVIVE.** § 7 Mergeability requires no changelog-path conflict when fragment
IDs differ: 0 of 190 conflicting pairs, against a control arm at 190 of 190.

## Measurement 2 — assembly is identical under shuffled enumeration

The frozen baseline plus 20 fragments, assembled under 5 shuffled directory
enumerations, digested with SHA-256 over one canonical serialization. The
mutation arm repeats it with the assembler's canonical sort removed.

The mutation arm is what makes the shuffle arm a measurement. Without it a
single digest proves only that the enumeration never varied — so the run also
reports how many of the 5 enumeration orders were actually distinct. Fragment
dates repeat deliberately: ties are what force the canonical sort to carry a
fragment-identity tiebreak, and a corpus of distinct dates would let a date-only
sort pass while remaining order-dependent.

```
$ python3 assembler.py --repo . --base 93bf9cc9e determinism
base commit    : 93bf9cc9e
fragments       : 20
shuffled runs   : 5
distinct enumeration orders actually used: 5 of 5

canonical sort
  distinct output digests across 5 shuffled enumerations: 1
    c1f44d6e82ce1a828abff5785eb2832d1b8c17d13909154d650f9b725082be1a
mutation arm (sort removed)
  distinct output digests across 5 shuffled enumerations: 5
    0008582fea1724807d7a2035c4d0a753557e655a03933e59f95ef4323315b275
    23eabbe35ca9c942fe3be7c7af5668477aa0ab5855dbe31d5803f4f294022e01
    5eb0c0a1d2826d0feb2b70631e90e8beeed4c128b40a6d3a3fc114e81b7e6e10
    6588f260b6d6934d52e83097194577720c7f4762f32581741717d97cc16c6822
    f6f504c987927a9223a201980a0a63bbf0762972863f65b2d10ad46c2b7103ab
```

All 5 enumerations differed, so the single digest is a property of the sort
rather than of an unvaried input. Removing the sort produces a distinct digest
for every enumeration — the arm fails exactly as designed when the invariant is
removed.

This answers the fragmentation spike's closing known-unknown, which recorded
determinism under shuffled input as untested.

**SURVIVE.** § 7 Determinism requires byte-identical output from at least five
shuffled enumerations: 1 distinct digest across 5, against 5 in the mutation arm.

## Measurement 3 — the model reproduces today's payload and anchors each fragment

Four arms against the live `/now/` projection at `93bf9cc9e`. Both sides of the
byte comparison are serialized identically before comparing.

```
$ python3 assembler.py --repo . --base 93bf9cc9e parity
base commit: 93bf9cc9e

zero-fragment arm (the comparison)
  model payload byte-identical to project_now_highlights: True
  live sha256    : 72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40
  model sha256   : 72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40
  diagnostics (not the comparison):
    groups  : 157
    bullets : 281
    schemaVersion: 1

Highlights integrity arm
  authored fragment bullets            : 20
  present exactly once, byte-for-byte  : 20 of 20

anchor arm (denominator fixed at the corpus size)
  fragments producing a group in the payload           : 20 of 20
  those groups whose anchor matches change-[0-9a-f]{32}: 20 of 20

historical-anchor arm
  anchors in the zero-fragment payload          : 157
  absent or changed in the twenty-fragment payload: 0
```

The group, bullet and `schemaVersion` counts are diagnostics, not the
comparison: a reworded, reordered or regrouped payload holds all three. The byte
comparison is the criterion, and both sides hash to `72305605…`.

The third diagnostic is the anchor list itself. The zero-fragment payload
carries 157 anchors in payload order, from `core22636--2026-09-22` down to
`governance-extras097--2026-08-16`; the newline-joined list hashes to
`e08ff00753d505f624c31c73ffce52658f969eb3683125ba7d6d4f3d7ea34617`. Every one is
slugger-derived from heading text, which is what makes the `change-<uuid>` form
the fragment groups carry a visibly different scheme rather than a variation on
the same one.

The anchor arm reports against a fixed denominator of 20, so an assembler
emitting no fragment group would report 0 of 20 rather than 0 of 0.

**Two limits on how far these figures reach.** The zero-fragment arm is partly
true by construction: the model produces the historical half by calling the
shipping projector, so the arm establishes that the merge, re-sort and
re-serialization introduce no change — it does not independently re-derive the
payload from fragment sources. The historical-anchor arm is **structural rather
than empirical**: the baseline is parsed once and fragment anchors come from
fragment identity, so nothing can re-run the slugger over history and the arm
cannot fail in this model. Its value is confirming the model has that structure,
which is the architectural claim. The measurement that *could* fail — whether
prepending the same 20 updates into `changelog.md` moves historical anchors
through duplicate-suffix renumbering — was not run; see
[What this spike did not measure](#what-this-spike-did-not-measure).

**SURVIVE.** § 7 Historical compatibility requires identical model payloads and
anchors: byte-identical at `72305605…`, with 0 of 157 historical anchors absent
or changed. § 7 Content integrity requires every Highlights item to appear
exactly once with unchanged bytes: 20 of 20.

## Measurement 4 — site-build cost at ten times the released-entry count

Five timed `make site-build` runs per arm in a disposable clone of `93bf9cc9e`,
outside this repository and deleted before this figure was recorded. The
fragment arm has the prototype wired into that clone's `tools/build-site.py` and
2,920 fragments staged, so the timed path genuinely enumerates, reads, parses,
assembles and projects them — an unwired arm would time filesystem noise and
report it as assembly cost. The wiring was proved before timing: the fragment
arm's generated payload carries 3,077 groups and 3,201 bullets against the
control's 157 and 281.

The corpus is 2,920 fragments — ten times the 292 free-standing released entries
at this base — so the model carries 3,212 entries, **11.0 times** the current
count. That is the intended reading of § 7's "ten times the current
release-entry count": ten times the current count *added*, which is the more
demanding of the two readings.

Arms interleave and each discards one unmeasured warm-up, because page cache,
tool warm-up and thermal state drift monotonically across a session and a block
design would put that drift into the median difference the 10% bar reads.

```
$ python3 timeruns.py --clone <clone> --base 93bf9cc9e --runs 5 --corpus 2920
base commit     : 93bf9cc9e
staged corpus   : 2920 fragments (fragment arm only)
retained runs   : 5 per arm, plus 1 discarded warm-up per arm

interleaved run order (executed top to bottom):
   1. control warm-up (discarded)
   2. fragment warm-up (discarded)
   3. control run 1      7. control run 3     11. control run 5
   4. fragment run 1     8. fragment run 3    12. fragment run 5
   5. control run 2      9. control run 4
   6. fragment run 2    10. fragment run 4

   1. control  warm-up    23.02s  DISCARDED
   2. fragment warm-up    32.29s  DISCARDED
   3. control  run 1    26.35s  retained
   4. fragment run 1    31.74s  retained
   5. control  run 2    31.10s  retained
   6. fragment run 2    44.93s  retained
   7. control  run 3    27.05s  retained
   8. fragment run 3    39.05s  retained
   9. control  run 4    75.41s  retained
  10. fragment run 4    58.67s  retained
  11. control  run 5    22.92s  retained
  12. fragment run 5    86.88s  retained

discarded warm-ups (not in any median):
  control : 23.02s
  fragment: 32.29s

retained durations:
  control : [26.35, 31.10, 27.05, 75.41, 22.92]  (n=5)
  fragment: [31.74, 44.93, 39.05, 58.67, 86.88]  (n=5)

control median  : 27.05s
fragment median : 44.93s
difference      : +17.88s
regression      : +66.08%  (threshold: under 10%)
```

### What the instrument can and cannot resolve

The retained build logs decompose each run into its two Astro phases, and that
decomposition bounds the figure's precision. The docs-site build receives
**identical input in both arms** — 264 pages either way, because fragments never
reach it — so any arm difference it shows is definitionally noise.

| Phase | Control median | Fragment median | Delta | Input differs? |
| --- | ---: | ---: | ---: | --- |
| web build | 5.76s | 10.98s | +5.22s | yes — 216 vs 3,282 pages |
| docs-site build | 8.43s | 11.92s | +3.49s | **no** — 264 vs 264 pages |
| whole `make site-build` | 27.05s | 44.93s | +17.88s | partly |

Across all ten retained runs the identical-input docs phase spans 6.86s to
18.20s, a range of 11.34s. Only +5.22s of the +17.88s total falls in the phase
whose input actually changed; the remaining +12.66s sits inside that noise band.
**The whole-build wall clock cannot resolve a 10% threshold on this machine.**

The verdict direction survives that imprecision — every fragment run exceeded
the control median, and the miss is 6.6 times the threshold — but the figure
should be read as "well over 10%", not as "66.08%".

### Where the cost actually comes from

It is not the stimulus § 7 names. That row anticipates "many small files
increase scan and parse cost". The measured cost is page generation: the web
build emits **3,282 pages instead of 216**, because `/now/[release].astro`
generates one page per release group and 2,920 fragments become 2,920 more
groups. That route was added three commits before this base, in
[#1415](../../../web/src/pages/now/%5Brelease%5D.astro). Rendering 15.2 times the
pages cost only +5.22s, so Astro's per-page cost is low — but it is the
component that scales with fragment count, and § 7's threshold was written
against a build where release count did not drive page count.

**KILL.** § 7 Build performance requires less than 10% site-build regression at
ten times the current release-entry count: the measured regression is +66.08%,
over the bar by 6.6 times, with the precision caveat above.

Per this spec's Durable Outputs, a build-cost figure at or above the § 7 bar is
neither a survive nor a kill for the architecture delta: it leaves
`docs/architecture/changelog-fragment-source.md` at `Draft`, obliges the delivery
spec to carry a named performance task, and Platform Core maintainers decide
whether it blocks delivery.

## Verdict

| # | Measurement | Threshold | Figure | Result |
| --- | --- | --- | --- | --- |
| 1 | Merge independence | 0 conflicting pairs, § 7 Mergeability | 0 of 190, control 190 of 190 | **survive** |
| 2 | Deterministic assembly | 1 digest from 5 shuffles, § 7 Determinism | 1, mutation arm 5 | **survive** |
| 3 | `/now/` parity and anchors | byte-identical, § 7 Historical compatibility | identical; 20/20; 0 of 157 moved | **survive** |
| 4 | Site-build cost | under 10%, § 7 Build performance | +66.08% | **kill** |

**Overall: survive.** The aggregation rule is kill when merge independence,
determinism or parity is kill, and survive otherwise; build cost does not enter
it. All three aggregating measurements cleared their thresholds, two of them
against an arm that failed when the invariant was removed.

The design is not refuted. What the run changes is the delivery spec's shape:
the performance question moved from "will many small files slow the scan" to
"one page per release group does not scale", which is a routing and pagination
question about `/now/`, not an assembly question.

## What this spike did not measure

- **Any production code.** No schema, renderer, gate or migration was written.
  The prototype is throwaway, handles only what a measurement needs, and has no
  validation or error handling. It was deleted with its clone.
- **The monolith counterfactual for historical anchors.** Measurement 3's
  historical-anchor arm cannot fail in the fragment model. Whether prepending the
  same 20 updates into `changelog.md` moves historical anchors through
  `_Slugger`'s duplicate-suffix renumbering is the arm that could fail, and it was
  not run. It is the cheapest remaining check and belongs in the delivery spec.
- **Per-fragment parse cost at realistic body sizes.** The corpus is 2,920
  synthetic fragments of roughly 330 bytes carrying one Highlights bullet each.
  It faithfully models how many groups and pages the build produces, and
  understates per-fragment read and parse cost against real entries that run to
  paragraphs and several bullets. The understatement lands on the phase the
  decomposition showed was not the cost driver.
- **ADR-0123's fifth Confirmation signal** — that regeneration leaves no tracked
  diff — and § 7's rows for Git cleanliness, Failure diagnosability, and
  Dependency and privacy posture. These are delivery verification obligations:
  the spike ships no production assembler for them to observe.
- **A quiet-machine re-measurement of build cost.** The whole-build metric was
  run once, at five retained runs per arm, on a machine whose identical-input
  phase varied by 11.34s.
- **`[Unreleased]` aggregation.** How pending fragments merge into the four
  `[Unreleased]` groups at release time is untouched, and is where the
  fragmentation spike said the real design work sits.

## Next decision, for the owner

Author the delivery spec at `docs/specs/product-changelog-fragments/` from these
figures. Three of its thresholds are now grounded — 0 conflicting pairs, 1
digest from 5 shuffled enumerations, byte-identical payload — and can be lifted
directly. The fourth cannot: § 7's build-performance row needs rewriting against
the page-generation cost this run found rather than the scan-and-parse cost it
currently names, and the delivery spec owes a named performance task either way.
