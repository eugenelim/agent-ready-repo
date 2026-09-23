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
  bullets at `schemaVersion` 1, from a 598,239-byte `docs/product/changelog.md`.
  Measurements 2, 3 and 4 were taken here. Measurement 1's retained run is at
  `443f141f2`, because its script was corrected during review and re-run each
  time; that section names its own base, and every figure below sits beside the
  base its own run names.
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
than maintained.

Both load `tools/build-site.py` by path, for different reasons, and neither
modifies it. The **prototype** reuses its parser and its `/now/` projector, so
the prototype and production agree about which `##` lines are real headings and
about how a payload is shaped — the same seam the fragmentation spike used. The
**measurement script** uses only one thing from it: the position of the first
free-standing release heading, which is where a monolith update inserts. It
takes that from the parser rather than scanning lines, because which `##` lines
are real is decided by a fence and comment state machine that a second scanner
would drift from. Everything else the script does is standard library and Git,
so a reader re-derives its counts without the prototype existing.

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

Every figure in this report comes from a retained run, quoted verbatim in the
section that uses it. The base figures in the header come from this run, using
the repository's own parser:

```
$ python3 -c '<import tools/build-site.py by path; parse docs/product/changelog.md>'
base commit      : 93bf9cc9e
total records    : 351
unreleased       : 59
free-standing rel: 292
now groups       : 157
now bullets      : 281
schemaVersion    : 1
changelog bytes  : 598239
```

## Measurement 1 — fragment branches merge clean where monolith branches do not

Twenty synthetic branches per arm, built off `443f141f2` — this measurement's
base, which is not the base in the header; see the note after the run — as
detached commit objects through a scratch `GIT_INDEX_FILE` and a private object
directory, so the run disturbs neither a worktree a coordination lease may be
sharing nor the shared object store. Each fragment-arm branch adds one
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
base commit: 443f141f2ecb007dcc913ff1404ae9938228d3c4
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

**This measurement's base is `443f141f2`, not the `93bf9cc9e` in the header.**
The script names whichever commit it ran against, and it was re-run after each
of the five corrections review made to it. The counts above are recorded
against `443f141f2`; no run at `93bf9cc9e` is retained, so nothing here claims
they also hold at the header's base. The other three measurements were taken at
`93bf9cc9e`. Each figure in this report is recorded beside the base its own run
names, which is what the spec requires; the report has no single base.

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

The third diagnostic AC 6 names is the anchor list itself, recorded here in
full and in payload order. Every one is slugger-derived from heading text,
which is what makes the `change-<uuid>` form the fragment groups carry a
visibly different scheme rather than a variation on the same one. The long
entries are multi-package releases, whose heading names every artifact.

```
$ python3 assembler.py --repo . --base 93bf9cc9e parity --emit-anchor-list
base commit: 93bf9cc9e
zero-fragment payload anchor list: 157 anchors, in payload order
sha256 of the newline-joined list: e08ff00753d505f624c31c73ffce52658f969eb3683125ba7d6d4f3d7ea34617

core22636--2026-09-22
agentbundle0480--2026-09-22
core22629--2026-09-22
experience-design208--2026-09-22
product-engineering01316--2026-09-22
desk-research119--2026-09-22
core22628--2026-09-21
agentbundle0473--2026-09-21
frontend-engineering031--2026-09-21
core22627--2026-09-21
core22626--2026-09-21
agentbundle0472--2026-09-21
core22625--2026-09-21
agentbundle0471--2026-09-21
core22624--2026-09-21
product-engineering01315--2026-09-21
core22623--2026-09-20
core22622--2026-09-20
core22621--2026-09-20
product-engineering01314--2026-09-20
experience-design207--2026-09-20
architect01514--2026-09-20
architect01513--2026-09-20
architect01512--2026-09-19
core22620--2026-09-18
core22619--2026-09-18
core22618--2026-09-18
core22617--2026-09-18
core22616--2026-09-18
architect01511--2026-09-18
architect0159--2026-09-18
core22615--2026-09-18
frontend-engineering030--2026-09-18
experience-design206--2026-09-18
core22614--2026-09-17
governance-extras0110--2026-09-17
core22613--2026-09-17
core22612--2026-09-17
core22611--2026-09-17
experience-design205--2026-09-17
core22610--2026-09-17
core2269--2026-09-17
core2268--2026-09-16
agentbundle0470--2026-09-16
core2265--2026-09-15
agentbundle0460--2026-09-15
agentbundle0450--2026-09-14
core2263--2026-09-14
core2262--2026-09-14
core2261--2026-09-14
agentbundle0442--2026-09-14
frontend-engineering025--2026-09-14
core22527--2026-09-13
core22526--2026-09-13
frontend-engineering024--2026-09-13
core22525--2026-09-13
core22524--2026-09-13
core22520--2026-09-13
frontend-engineering023--2026-09-13
core22519--2026-09-13
core22518--2026-09-12
product-engineering01312--2026-09-12
core22516--2026-09-11
agentbundle0440--2026-09-11
core22514--2026-09-10
core22513--2026-09-10
core22512--2026-09-10
core22511--2026-09-10
core22510--2026-09-10
core2259--2026-09-09
agentbundle0431--2026-09-09
agent-skill-engineering042--2026-09-09
core2258--2026-09-08
core2256--2026-09-08
agentbundle0430--2026-09-08
core2255--2026-09-08
architect0157--2026-09-08
core2254--2026-09-08
core2253--2026-09-08
core2252--2026-09-04
core2251--2026-09-04
architect0156--2026-09-04
agent-skill-engineering041--2026-09-04
core2250--2026-09-04
core2243--2026-09-04
product-engineering0139--2026-09-03
product-strategy025--2026-09-03
experience-design203--2026-09-03
frontend-engineering022--2026-09-03
core2242--2026-09-03
core2240--2026-09-03
core2232--2026-09-03
core2231--2026-09-03
core2230--2026-09-03
core2220--2026-09-02
core2210--2026-09-01
core2201--2026-09-01
core2200--2026-09-01
core2190--2026-09-01
core2182--2026-09-01
core2180--2026-08-31
catalogue-curation046--governance-extras0105--2026-08-31
core2173--2026-08-31
core2172--2026-08-31
agent-skill-engineering040--2026-08-31
agent-skill-engineering030--2026-08-31
core2171--2026-08-31
core2170--2026-08-31
core2166--2026-08-31
architect0155--2026-08-30
core2165--governance-extras0103--2026-08-30
core2163--2026-08-30
core2162--2026-08-30
agent-skill-engineering020--2026-08-30
agentbundle0410--2026-08-30
core2160--product-engineering0138--2026-08-29
agentbundle0403--2026-08-29
core2155--2026-08-29
core2154--2026-08-29
core2153--2026-08-29
agentbundle0402--2026-08-28
core2152--governance-extras0102--product-documentation011--user-guide-diataxis031--agent-skill-engineering011--2026-08-28
catalogue-curation045--2026-08-28
architect0154--experience-design202--figma033--product-engineering0137--product-strategy024--2026-08-28
contracts036--converters096--frontend-engineering021--iac-terraform019--monorepo-extras019--release-engineering0110--2026-08-28
atlassian093--credential-brokers033--desk-research116--github023--linear033--2026-08-28
core2151--2026-08-28
core2140--2026-08-28
core2130--2026-08-27
agent-skill-engineering010--2026-08-27
catalogue-curation044--2026-08-27
core2125--2026-08-27
core2124--2026-08-27
catalogue-curation043--2026-08-26
architect0153--2026-08-26
core2123--2026-08-26
agentbundle0400--2026-08-25
catalogue-curation042--2026-08-25
core2122--2026-08-25
core2121--architect0152--governance-extras0101--monorepo-extras018--iac-terraform018--2026-08-24
agentbundle0394--2026-08-24
core2110--2026-08-24
core21010--product-engineering0135--2026-08-24
core2120--2026-08-23
core2109--2026-08-23
core2108--2026-08-23
agentbundle0393--2026-08-23
core2107--2026-08-23
agentbundle0392--2026-08-23
core2106--2026-08-23
architect0151--2026-08-23
catalogue-curation041--2026-08-21
architect0150--2026-08-21
core2105--2026-08-21
agentbundle0390--2026-08-21
core2104--2026-08-20
governance-extras097--2026-08-16
```

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
report it as assembly cost. The wiring was proved before timing, by running the
clone's site-sync alone and counting what reached the generated payload:

```
$ python3 tools/build-site.py   # in the fragment-armed clone
  3201 released highlight(s) in 3077 release group(s)
$ python3 -c '<count web/src/lib/now-highlights.generated.json>'
groups in generated payload: 3077
bullets: 3201
fragment-sourced groups: 2920
example anchor: change-fffdf77df4504567b382b6e520d1411d
```

The control arm's same payload carries 157 groups and 281 bullets, so the
staged corpus is genuinely traversed rather than sitting inert beside a build
that never opens it.

The corpus is 2,920 fragments — ten times the 292 free-standing released entries
at this base — so the model carries 3,212 entries, **11.0 times** the current
count. That is the intended reading of § 7's "ten times the current
release-entry count": ten times the current count *added*, which is the more
demanding of the two readings.

Arms interleave and each discards one unmeasured warm-up. Nothing here measures
page cache, tool warm-up or thermal state, so no claim is made about how they
move. Interleaving mitigates a gradual trend across the session, which a
blocked design would fold straight into the median difference the 10% bar
reads. It is not general protection: every retained pair runs control before
fragment, so an alternating effect, or one acting within a pair, stays aligned
with the fragment arm and this design would not separate it.

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

The retained build logs time each run's two Astro phases separately. They are
recorded here as observations, and deliberately not as a decomposition of the
whole-build difference.

```
$ python3 -c '<per-phase medians over the 10 retained t4 build logs>'
base commit: 93bf9cc9e -- observed per-phase durations, read from the 10 retained t4 build logs
phases run sequentially inside one `make site-build`; these are observations, not a decomposition

phase                      pages c/f  control median  fragment median   control range   fragment range
web build                 216 / 3282           5.76s           10.98s      5.49-7.16        9.28-12.54
docs-site build            264 / 264           8.43s           11.92s      6.86-18.20       7.09-14.05
whole site-build                   -          27.05s           44.93s     22.92-75.41      31.74-86.88
```

**Why these are not components.** `site-build` runs the web build and then the
docs-site build in one invocation. The docs phase therefore executes after a web
phase that produced fifteen times more pages in the fragment arm. Its input is
identical either way, but it inherits page cache, memory pressure and thermal
state from the phase before it, so its timings are not a treatment-free
baseline and the gap between two phase medians cannot be separated into a part
caused by the treatment and a part that is not. Subtracting medians computed
independently would not give a valid split even if the phases were independent.

**What the ten runs do support** is narrow: the whole-build point estimate is
+66.08%, which does not meet the 10% bar, and the two samples overlap.

```
$ python3 -c '<dispersion of the 10 retained t4 durations>'
control runs sorted : [22.92, 26.35, 27.05, 31.1, 75.41]
fragment runs sorted: [31.74, 39.05, 44.93, 58.67, 86.88]
control-fragment run pairs where the fragment run is slower: 21 of 25
overlap: max control 75.41s exceeds 4 of 5 fragment runs
```

Five runs per arm at this dispersion support no valid uncertainty bound on the
whole-build difference, so +66.08% is the observed point estimate and nothing
more. A quiet-machine re-measurement is owed before any threshold is set from
this number, and it should time the phases in isolation rather than in sequence.

### A structural change this measurement does not price

Two facts here come from code and from the retained build logs, with no timing
inference. First, the fragment arm's web build emits **3,282 pages against the
control's 216** — both counts are in the logs. Second, the reason is structural:
`/now/[release].astro` calls `getStaticPaths` over every group in the generated
payload, so each of the 2,920 fragments becomes one more page. That route arrived in
[#1415](../../../web/src/pages/now/%5Brelease%5D.astro), which is in this run's
base.

What this run does **not** establish is what that costs. The phases were timed
in sequence, not in isolation, so nothing here attributes any part of the
measured difference to page generation. The page-count growth is a recorded
structural fact; "page generation is what makes the fragment build slower"
remains an **untested hypothesis** — the most plausible one available, and the
one the delivery spec should price first, but not something these ten runs
demonstrate.

The same caution applies to § 7's own framing. Its Build performance row
anticipates the stimulus "many small files increase scan and parse cost", and
this run neither confirms nor refutes that: it did not isolate the parse phase,
and its corpus understates byte volume by design.

**KILL.** § 7 Build performance requires less than 10% site-build regression at
ten times the current release-entry count. The observed point estimate is
+66.08%, which does not meet it. The measurement does not support a precision
claim on that number — see above — so the kill rests on the recorded figure
against the recorded threshold, and the figure itself is owed a re-measurement.

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

The design is not refuted. What the run changes is the delivery spec's shape.
The build-cost figure misses its threshold, and the run also records that
release count now drives page count through `/now/[release]`. Which of those
two facts explains the other is not settled here, so the delivery spec inherits
a measurement to redo rather than a cause to fix — and it should redo it on a
quiet machine before setting any threshold.

## What this spike did not measure

- **Any production code.** No schema, renderer, gate or migration was written.
  The prototype is throwaway, handles only what a measurement needs, and has no
  validation or error handling. It was deleted with its clone.
- **The monolith counterfactual for historical anchors.** Measurement 3's
  historical-anchor arm cannot fail in the fragment model. Whether prepending the
  same 20 updates into `changelog.md` moves historical anchors through
  `_Slugger`'s duplicate-suffix renumbering is the arm that could fail, and it was
  not run. It is the cheapest remaining check and belongs in the delivery spec.
- **Per-fragment parse cost at realistic body sizes.** The corpus models group
  and page counts faithfully and understates byte volume badly:

  ```
  $ python3 -c '<regenerate the staged corpus from the same seeded generator>'
  fragments        : 2920
  bytes per fragment: min 273, median 279, max 279
  total corpus bytes: 812466
  Highlights bullets per fragment: 1
  ```

  Ten times the entry count is only 1.36 times the byte volume of the existing
  598,239-byte changelog, because each synthetic body is one short bullet where
  a real entry runs to paragraphs and several. That byte-volume mismatch is
  what was measured. Its effect on read and parse cost is unknown in both
  direction and size, because the run never isolated the parse phase, so this
  run cannot be cited for parse cost.
- **ADR-0123's fifth Confirmation signal** — that regeneration leaves no tracked
  diff — and § 7's rows for Git cleanliness, Failure diagnosability, and
  Dependency and privacy posture. These are delivery verification obligations:
  the spike ships no production assembler for them to observe.
- **A quiet-machine re-measurement of build cost.** The whole-build metric was
  run once, at five retained runs per arm, on a machine whose identical-input
  phase varied by 11.34s.
- **`[Unreleased]` aggregation.** How pending fragments merge into the
  `[Unreleased]` region at release time is untouched, and is where the
  fragmentation spike said the real design work sits.

## Next decision, for the owner

Author the delivery spec at `docs/specs/product-changelog-fragments/` from these
figures. Three of its thresholds are now grounded — 0 conflicting pairs, 1
digest from 5 shuffled enumerations, byte-identical payload — and can be lifted
directly. The fourth cannot. The build-cost figure is a point estimate from an
instrument that could not resolve its own threshold, so it grounds nothing yet;
the delivery spec owes a named performance task and a re-measurement on a quiet
machine. When that runs, it should isolate the phases, because this run recorded
that release count now drives page count without establishing what that costs.
