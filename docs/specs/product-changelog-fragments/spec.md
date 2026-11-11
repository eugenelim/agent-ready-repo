# Spec: Per-update product changelog sources and generated views

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0123, ADR-0143
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Contributors to this repository publish a product changelog update from their
own implementation pull request without contending with anyone else's, because
each update is an independently tracked file rather than a section prepended at
one shared anchor. Success is that two updates authored on separate branches
merge in either order, and that every published view — the complete changelog,
`/now/`, its pages, archive, permalinks and feed — still carries exactly the
text a human reviewer approved.

## What Changes

- New update records — `docs/product/changelog.d/<id>.md`, one file per update
- Fragment creation, validation, assembly and rendering — `tools/changelog.py`
- The historical changelog — `docs/product/changelog.md`, frozen behind a migration notice and a gate that rejects later release-section edits
- The complete local changelog — `build/product-changelog.md`, generated, never tracked
- Site changelog and `/now/` input — `tools/build-site.py` reads the shared model instead of parsing one file
- Release validation — `tools/check-core-release.py` and `tools/repo/check_release_impact.py` recognize fragments
- Documentation build triggers — `.github/workflows/pages.yml` gains the fragment directory
- Full-site build orchestration — `make site-build` projects shared inputs once,
  while direct package builds retain their self-projecting `prebuild` hooks
- Fragment-reader hot path — profile the remaining projection, remove repeated
  setup work without weakening per-file confinement or validation, and remeasure
- Author guidance — `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `changelog.md` header, and a fragment template
- A quiet-machine three-arm build-cost measurement, which the assembly spike could not supply
- Released-record storage — under ADR-0143, `compact` moves released fragments
  into append-only monthly bundle parts under `docs/product/changelog.months/`,
  `retract` withdraws a bundled record and logs it in
  `docs/product/changelog-retractions.toml`, and one reader in
  `tools/changelog.py` returns every record to every consumer

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — this delivery makes the delta's § 4 rows live | `docs/architecture/changelog-fragment-source.md` | Platform Core maintainers | A named passing test for every § 4 row's Verification column and every § 7 row's Verification column | Each § 4 and § 7 row names a test that exists and passes; the delta's `Status` line is resolved by Platform Core maintainers, who own that transition |
| Decision rationale | Already owned | `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md` | Platform Core maintainers | The accepted ADR and its five Confirmation signals | Every Confirmation signal has a named passing test. A delivery that cannot satisfy one opens a superseding ADR rather than editing this one |
| Decision rationale, released-record storage | Already owned | `docs/adr/0143-released-changelog-records-move-into-monthly-bundles.md` | Platform Core maintainers | The accepted ADR and its Confirmation signals, each mapped to a T17 or T18 test | Every Confirmation signal has a named passing test |
| Maintainer procedure | Applicable — the authoring gesture changes for every contributor | `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `docs/product/changelog.md` header, and the fragment template | eugenelim | Each surface states the fragment gesture and none still instructs an author to edit `changelog.md` | A repository-wide search for instructions to edit `changelog.md` returns only the frozen-history notice |
| Interface compatibility | Applicable — `/now/<anchor>/` and the Atom `<id>` are published identities | `web/src/pages/now/` and `web/src/components/now/NowHighlights.astro` | eugenelim | The payload validates against the five importers' existing `schemaVersion` guards without editing them, and every historical anchor is unchanged | No consumer guard is edited and no historical anchor moves |
| Operations | Applicable — validation and the site build gain failure modes | `.github/workflows/pages.yml`, `Makefile`, and the existing validation job | eugenelim | A fixture per diagnostic class, each naming a fragment path and an invariant; an orchestration check proving the aggregate target projects once without weakening direct package builds | Every diagnostic class has a fixture, the build reports fragment, release and Highlights counts, and `make site-build` does not repeat the shared projection in package lifecycle hooks |
| Reusable learning | Applicable — the build-cost question the assembly spike left open | `docs/product/research/changelog-fragment-build-cost.md` | eugenelim | The three-arm run's retained stdout, its run order, discarded warm-ups, retained durations and per-arm page counts | The report names its machine, its base commit, the two ratios § 7 Build performance and § 7 Published page count each require, and a survive or kill line against each |
| Release history | Not applicable | — | — | — | The changelog's release headings are pack-scoped and `tools/repo/check_release_impact.py` does not treat `tools/`, `docs/` or `web/` as release-impacting, so no pack version moves and no entry is owed |
| User promise, current product truth | Not applicable | — | — | — | The published changelog and `/now/` carry the same text before and after; what changes is where a contributor writes it, which the maintainer-procedure row owns |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Take every threshold from the row of `docs/architecture/changelog-fragment-source.md` § 4 or § 7 that owns it. Where this spec and § 7 disagree, § 7 wins.
- Follow `tools/AGENTS.md`: a new `tools/` addition is pure-stdlib Python. Reach the blessed confined-file helpers by `importlib`-from-path, as `tools/check-output-readability.py` already does at its `_file_safety` loader — not by importing `agentbundle`.
- Pair each measurement with the control or mutation arm this spec names for it, and report a bare treatment figure as inconclusive rather than as a result.
- Record the base commit beside every figure, because the changelog grows daily and a figure without a base cannot be re-derived.
- Ship the fragment contract, the assembler, every consumer and the cutover gate together, per § 8's shared failure boundary.

### Ask first

- Any change to a decision ADR-0123 records as D1 through D7.
- Any change to a threshold, an arm or a corpus size this spec's Acceptance Criteria state.
- Proceeding past a three-arm build-cost figure at or above the § 7 Build performance bar. Platform Core maintainers decide whether that figure blocks delivery; an implementer does not.
- Any resolution of the `[Unreleased]` release transition that would require editing a merged fragment's `packages`, `date` or `id`, which § 4 Published identity permanence forbids.
- The numeric values for the fragment reader's traversal and byte bounds. No § 4 or § 7 row owns them, and this spec does not originate a threshold those sections own.
- The instrument-validity stop predicate that classifies a T13 run as inconclusive. No § 7 row owns an instrument threshold.
- ADR-0143's thresholds and arm, each proposed there and owned by Platform Core maintainers:
  - the 500-released-loose-fragment build refusal;
  - the 375-fragment warning;
  - the 250-pending-fragment warning;
  - the 65,536-record cap across both storage forms;
  - the 1,048,576-byte bound on merge-base blobs and on the retraction list;
  - the redefined § 7 Build performance fragment arm.

### Never do

- Track a generated combined changelog, add a custom merge driver for it, add a post-merge bot writer, or add a protected-branch bypass. ADR-0123 D6 keeps all four out of the merge-queue-critical path. ADR-0143 bundle parts are authoring source, not a generated view, and only `compact` and `retract` write them.
- Edit, reorder or reword a historical release section or heading in `docs/product/changelog.md`. A migration notice is the only admitted change.
- Combine, summarize, reword or re-split any fragment's Highlights during assembly.
- Bump `now-highlights.generated.json` past `schemaVersion` 1.
- Read a generated view as an authoring input.
- Give the assembler a network, clock, Git-history or model dependency, per ADR-0123 D4. Validation and the release checks may make read-only merge-base and changed-path Git reads, which § 4 Published identity permanence names as its enforcement mechanism; no such read may reach published content.
- Add a new top-level directory, package or third-party dependency.
- Bypass or weaken confined reads, merge-base identity enforcement, fragment
  validation, output-integrity checks or the precommitted measurement rules to
  meet the performance bar.

## Testing Strategy

- Fragment envelope, body, identity, anchor and immutability validation: **TDD**. Each is a pure function over text with a compressible invariant, and each refusal is a named diagnostic class.
- Canonical ordering and deterministic assembly: **TDD**, with a mutation arm — the canonical sort removed — that must change the output.
- `/now/` payload parity and Highlights integrity: **goal-based**, exercised by an **integration** test that compares the assembled payload against the serialized payload the shipping projector emits.
- Merge independence: **goal-based**, exercised by an **integration** check that replays synthetic branch pairs through `git merge-tree`, with a monolith control arm.
- Historical-anchor stability under the monolith counterfactual: **goal-based**, exercised by an **integration** check that prepends the same updates into `changelog.md` and re-slugs.
- Complete-view rendering, regeneration cleanliness and workflow triggers: **goal-based**, each verified by one command whose observable is a file, a digest or an empty `git status`.
- Build cost and published page count: **goal-based**, exercised **end-to-end** by the real `make site-build` in a disposable clone across three arms.
- The authoring gesture — `python3 tools/changelog.py new`, then `render` — is **visual / manual QA**: a maintainer invokes both and records the created path, the rendered output and the exit codes.
- Bundle container, cross-form identity, retraction, bounds, and the `compact` and `retract` commands: **TDD**. Each is a pure rule over bytes or a record set, and each refusal is a named diagnostic class.
- Compaction and retraction round trips, and merge replay with bundle parts on the base: **goal-based**, exercised by **integration** checks.
- Each task's `Tests` field in `plan.md` is the canonical verification-mode
  register. T16 combines its TDD inventory-normalization and membership-call
  invariant with goal-based profiling, output equivalence and an end-to-end
  measurement; this spec does not duplicate the per-task counts.

## Acceptance Criteria

Each criterion below states its own threshold. Where the threshold comes from
`docs/architecture/changelog-fragment-source.md` § 4 or § 7, the criterion cites
the row that owns it; those sections win where this spec and they ever disagree.
Where a criterion lifts a figure the assembly spike measured, it names the base
commit that figure was taken at.

### Fragment source and identity

- [x] **AC1 — shared owner:** `parse_changelog_releases`, `ParsedChangelog`, `ChangelogHeading`, `_parse_release_identity`, `_strip_changelog_comments`, `_slug_base`, `_Slugger`, `highlight_segments` and `_project_parsed` live in `tools/changelog.py`; `tools/build-site.py` imports and re-exports those same objects, and `tools/changelog.py` never loads `tools/build-site.py`. Per ADR-0123 D7 and § 8 Shared changelog model and assembler.
- [x] **AC2 — sink-safe metadata:** every `packages.name` matches `[A-Za-z0-9][A-Za-z0-9._-]*`, every `packages.version` matches `[A-Za-z0-9][A-Za-z0-9._+-]*`, and `date` is a real ISO `YYYY-MM-DD` calendar date. Validation refuses whitespace, `/`, `]`, quotes, angle brackets and control characters in either package field, naming the path, field and accepted grammar. The renderer composes the established `[name][version] — date` heading only from those validated fields; the published anchor, DOM id, URL segment and Atom identity use the separately validated lowercase slug-and-UUID anchor token. Verifies target-format safety at the Markdown, HTML-attribute, URL-path and feed sinks.
- [x] `python3 tools/changelog.py new` creates exactly one file, at `docs/product/changelog.d/<id>.md`, whose filename stem is a lowercase UUIDv4 and whose envelope `id` is that same string, per ADR-0123 D2 and § 4 Fragment identity and path.
- [x] **AC3 — fragment identity refusal:** validation refuses each member of this closed set, naming the fragment path and the offending field: a stem that does not match the envelope `id`; an `id` that is not a lowercase UUIDv4; an uppercase-hexadecimal `id`; and an `id` that duplicates another fragment's. Per § 4 Fragment identity and path.
- [x] Validation accepts a fragment whose front matter opens with a `+++` line, carries TOML `schema`, `id`, `anchor`, `date` and one or more `packages` records each with `name` and `version`, and closes with a second `+++` line; and refuses each member of this closed set, naming the path and the offending field: a missing delimiter, a missing required field, an unknown field, a field of the wrong type, malformed TOML, and an unrecognized `schema` value. Per § 4 Fragment envelope.
- [x] Validation accepts a body whose sections are drawn from the changelog's established section names and which carries a non-empty `Highlights` section, and refuses each member of this closed set: an unknown section name, a duplicate section, a release-level heading, and an absent or empty `Highlights`. Per § 4 Fragment body.
- [x] The fragment reader admits only regular files under `docs/product/changelog.d/`, refusing a symlink, a directory entry and a non-regular file by path, through the repository's blessed confined-file helpers.
- [x] The fragment reader passes the blessed confined-file helpers' traversal bounds — their entry, file-count and depth limits — and their per-file byte bound, and refuses fail-closed by path when any one is exceeded, rather than enumerating or reading an untrusted tree without a ceiling.

### Published anchor and identity permanence

- [x] A fragment's envelope `anchor` is the slug the existing slugger produces for that fragment's package-and-date heading, a hyphen, then the fragment's own `id` as 32 lowercase hexadecimal digits; `new` writes it at creation and the validator recomputes it from `packages`, `date` and `id` and refuses a mismatch. Per § 4 Stable links.
- [x] Two fragments whose `packages` and `date` produce the same slug receive distinct anchors, and neither anchor is derived from reading the other fragment. Per § 4 Stable links.
- [x] **AC4 — fail-closed merge-base prerequisite:** identity validation must resolve the merge base and classify changed paths before comparing bytes. Only a path classified as added may accept a missing base blob. A missing merge base, shallow-history failure, renamed or modified path with no readable base blob, non-zero `git show` result other than the expected added-path absence, or any malformed Git result refuses validation by path and expected correction; none is treated as a new fragment.
- [x] **AC5 — published identity immutability:** validation refuses a change to `packages`, to `date`, or to `id` in a fragment already present at the merge base, naming the field and the fragment path. Per § 4 Published identity permanence.
- [x] Every anchor the renderer emits appears as `<a id="<anchor>"></a>` immediately before its update heading in the generated complete changelog, and every `/now/` anchor resolves to an element of that id in the emitted changelog page. Per § 4 Stable links.

### Assembly, ordering and determinism

- [x] Assembling the frozen baseline plus a fragment set across 5 shuffled directory enumerations produces 1 distinct output digest, and the same 5 enumerations with the canonical sort removed produce at least 2. Per § 7 Determinism; the figures 1 and 5 were measured at base `93bf9cc9e`.
- [x] Output order is `date` descending then `id` ascending, and the renderer emits no field derived from a clock, from filesystem enumeration order or from Git history. Per § 4 Canonical identity and order and § 4 Deterministic assembly.
- [x] Every fragment appears exactly once in the complete view, and every Highlights item appears exactly once and byte-for-byte in the `/now/` payload. Per § 7 Content integrity and ADR-0123 D3.
- [x] Every fragment's complete body — every section's text and the order those sections appear in — is present in the complete view unchanged and exactly once, so a dropped or reworded non-Highlights section fails. Per § 4 Fragment body, whose Verification column requires round-trip fixtures and exact-body assertions, and ADR-0123 D3.

### Historical compatibility

- [x] The `/now/` payload assembled with zero fragments is byte-identical to the payload `tools/build-site.py` emits from `docs/product/changelog.md` alone, whose sha256 is `72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40` at base `93bf9cc9e`. Per § 7 Historical compatibility.
- [x] No anchor present in the zero-fragment payload is absent or changed in a payload assembled with fragments present. Per § 7 Historical compatibility.
- [x] Prepending the same fragment set into `docs/product/changelog.md` as release sections moves at least one historical anchor through the slugger's duplicate-suffix renumbering, or the run records that it moves none; the figure is recorded either way, against the fragment path's figure of zero. This is the arm the assembly spike named as the one that can fail and did not run.
- [x] The generated complete changelog contains every pre-cutover release section from `docs/product/changelog.md` with its heading text and section body unchanged, verified against a recorded digest of those sections. Per § 4 Immutable historical baseline.
- [x] A change that edits a historical release section or heading in `docs/product/changelog.md` is refused by a gate naming the edited heading. Per § 4 Immutable historical baseline.
- [x] `docs/product/changelog.md` carries a migration notice naming the public `/changelog/` view and the `python3 tools/changelog.py render --output build/product-changelog.md` command, and that notice is the only change to the file. Per § 5.

### `[Unreleased]` aggregation at release time

- [x] A fragment for a package version that is not yet released appears in the `[Unreleased]` region of the generated complete changelog and produces no `/now/` group.
- [x] After that version is released, the same fragment's Highlights appear exactly once in a released group of the `/now/` payload, and the fragment's `id` is the one it was created with.
- [x] Each released fragment yields one distinct `/now/` group carrying that fragment's own `anchor` and only that fragment's own Highlights, so two fragments' bullets collapsed into one group fails. Per § 4 Atomic Highlights, which derives the permalink page and the feed entry from that group.
- [x] A fragment moving from unreleased to released changes no byte of any other fragment's record in the complete view or the `/now/` payload.

### Merge independence and Git cleanliness

- [x] For 20 synthetic branches that each add one `docs/product/changelog.d/<uuid>.md` and nothing else, 0 of the 190 unordered branch pairs are classified as conflicting on a changelog path by `git merge-tree`, and 0 pairs exit non-zero for any other reason. Per § 7 Mergeability; measured as 0 of 190 at base `443f141f2`.
- [x] For a control arm of 20 branches that each instead prepend one release section to `docs/product/changelog.md`, the conflicting-pair figure is greater than zero and the error figure is 0, without which the fragment arm's zero is not a measurement. Measured as 190 of 190 at base `443f141f2`.
- [x] Regenerating every view from a clean checkout leaves `git status --porcelain` empty, and `git check-ignore build/product-changelog.md` reports the file ignored. Per § 7 Git cleanliness and ADR-0123's fifth Confirmation signal.

### Consumers and release validation

- [x] `now-highlights.generated.json` stays at `schemaVersion` 1, and a payload assembled with fragments present validates against the existing guards in `web/src/pages/now/index.astro`, `web/src/pages/now/page/[page].astro`, `web/src/pages/now/archive/index.astro`, `web/src/pages/now/[release].astro`, `web/src/pages/now/feed.xml.ts` and `web/src/components/now/NowHighlights.astro` with none of those six files' guards edited. Per § 4 Projection schema version.
- [x] `tools/check-core-release.py` matches a core release to a changed fragment rather than to the topmost heading of `docs/product/changelog.md`, and refuses a release whose fragment carries no Highlights bullet.
- [x] `tools/repo/check_release_impact.py` treats an added or changed path under `docs/product/changelog.d/` as satisfying its changelog requirement, and its existing refusal for a release-impacting change with no changelog evidence still fires.
- [x] `.github/workflows/pages.yml` triggers the documentation build on a change under `docs/product/changelog.d/` and on a change to `docs/product/changelog.md`, and the repository's owning allowlist — `REQUIRED_PATHS` in `tools/test-pages-workflow.py`, enforced over the `push` and `pull_request` triggers — pins both paths, so removing either trigger fails.

### Diagnosability, posture and cost

- [x] Every refusal this spec names reports the fragment path, the field or invariant that failed, and the expected correction; a fixture exercises each refusal class. Per § 7 Failure diagnosability.
- [x] A successful build reports the fragment count, the release count and the Highlights count, which is what makes a parity check possible without a second parse. Per § 6.
- [x] A fragment set containing any refusal class this spec names produces no generated view and changes no existing generated view, exercised over at least one file-safety refusal and one schema refusal. Per § 3's failure path, which publishes no new output.
- [x] An end-to-end build of every view completes with no network access available, and a static dependency check reports no third-party import added by any `tools/` entry point this delivery touches, that set being the one the plan's tasks pin in their `Touches` fields. Per § 7 Dependency and privacy posture and § 4 Human editorial authority.
- [x] `make site-build` runs the shared content and renderer-input projection once before its two Astro builds, without repeating either package's `prebuild` projection; a direct `npm run build --prefix web` or `npm run build --prefix docs-site` still projects its own renderer inputs first. This removes aggregate-only duplicate work without weakening either standalone entry point.
- [x] A profile of the equal-scale fragment arm identifies the remaining projection's dominant repeated work before it is optimized. The released-version inventory is validated and normalized once per projection, then reused only for read-only membership checks; it is never normalized once per fragment. The optimized reader keeps the same confined-file helper, per-file byte bound, refusal diagnostics, validated model, and rendered bytes, and adds no cache that survives a projection and no third-party dependency.
- [x] A three-arm interleaved measurement on a quiet machine, each arm discarding one warm-up run, records the median `make site-build` duration for today's corpus, for a monolith carrying ten times the released entries, and for that same canonical record set stored as § 7 Build performance defines the fragment arm. Under ADR-0143 that arm holds at least the ceiling's count of released records loose as fragments and every other record in bundle parts written by the `compact` part writer. T18 measured it with 1,000 loose, above the 500 ceiling, so its figure bounds the ceiling's worst state from above. The two large arms are generated from one record set and differ only in physical layout. The recorded ratio is the fragment median minus the monolith median over the monolith median, judged against § 7 Build performance, which owns the bar.
- [x] The same measurement records each arm's retained-duration spread and applies the instrument-validity stop predicate Platform Core maintainers set for it, classifying a run that fails that predicate as inconclusive rather than as a ratio. Until that predicate is recorded, no T13 ratio is accepted; the predicate is not a restatement of the § 7 Build performance bar, which judges an already-valid run.
- [x] The final pass begins only after untimed setup and a predeclared quiet-machine gate: five consecutive one-minute samples with one-minute load at or below the machine's 10 logical CPUs and mean latency at or below 40 ms for ten `/usr/bin/true` spawns, followed immediately by a 60-spawn confirmation at or below 40 ms. One complete pass is admitted after that gate; if an arm still exceeds the 20% spread bound, the result is inconclusive and no retry-until-valid run follows.
- [x] That same measurement records the published page count per arm, and the fragment and monolith arms at equal release count emit the same number of pages. Per § 7 Published page count.
- [x] The two Astro phases are timed in isolation rather than in sequence, so the recorded fragment-versus-monolith difference is attributable rather than inherited from the phase before it.

### Monthly bundles (ADR-0143)

- [x] **AC-B1 — helper once:** one projection loads the file-safety helper exactly once and passes that handle to every confined read. A second projection loads it afresh, so no helper state survives a projection. Every confined read the projection makes — of a fragment, a part or the retraction list — passes the 1,048,576-byte bound.
- [x] **AC-B2 — container:** a bundle part is refused by part path and record position when it has any of these:
  - a missing leading `+++ record +++` separator;
  - an empty record;
  - trailing bytes;
  - a byte-order mark;
  - a CR;
  - a record without a final LF;
  - non-UTF-8 bytes;
  - a separator line in a record's front matter or body;
  - two records with equal canonical keys;
  - records out of canonical order.

  A fenced `+++ b/path` line in a body is accepted. Lines split on LF over raw bytes.
- [x] **AC-B2a — bundle-ready fragments:** fragment validation refuses, by path, a loose fragment that would not bundle unchanged under ADR-0143 D4. That covers a byte-order mark, a CR, non-UTF-8 bytes, a missing final LF, and a line equal to `+++ record +++` in its front matter or body.
- [x] **AC-B3 — part names:** these are refused before any Git path parsing: a name that does not fullmatch `YYYY-MM-NN.bundle` with a real month, a duplicate `NN`, a stray entry in `docs/product/changelog.months/`, and a record whose `date` month differs from its part's.
- [x] **AC-B3a — read confinement:** `docs/product/changelog.months/` is read through the blessed confined-file helpers with the same entry, file and depth bounds as `docs/product/changelog.d/`. A symlink, hard link or non-regular entry is refused by path, even when it carries a valid part name. `docs/product/changelog-retractions.toml` is read through the same helper, and a link or non-regular file there is refused. Each case has a fixture.
- [x] **AC-B4 — cross-form identity:** validation compares the merge-base record set with the current one by `id`, never through Git rename pairing, and refuses each of these by `id` and every path:
  - an `id` that occurs more than once anywhere in the record set, whether across forms, across parts or within one part;
  - a bundled record edited in place;
  - a bundled record moved into an added part with its `date` changed;
  - a fragment moved into a one-record part with a body change;
  - an unretracted removed bundled record or part;
  - a removed months directory;
  - a new `id` added directly to a part;
  - an existing part changed other than by a listed retraction;
  - a part-adding change that drops an unbundled merge-base fragment;
  - a part-adding change that changes anything under `docs/product/changelog.d/`, `docs/product/changelog.months/` or `docs/product/changelog-retractions.toml` other than three things: adding parts, deleting fragments those parts carry byte-exactly, and adding new fragments absent at the merge base and not bundled. That keeps ADR-0143 D9's same-PR compaction for an urgent change.

  It accepts a byte-exact move, a part-adding change that also adds a new fragment, and the deletion of a loose fragment in a change that adds no part. A pull request that leaves the record set unchanged reads 0 Git blobs, counted through the Git runner. "Changed" is decided by an object id computed over the exact loaded bytes, in the object format `git rev-parse --show-object-format` reports, with no attribute, end-of-line, `ident` or filter conversion. It is never decided by the index. A SHA-256 repository fixture and an `ident`-attributed part edit fixture cover this. Merge-base, tree-listing and blob-read failures refuse, including when either directory is empty or absent.
- [x] **AC-B4a — retraction:**
  - `retract --id --category` removes exactly one record, keeping every other record's bytes, order and output.
  - It rewrites the part first, then appends the list entry, each atomically. A failure between the two writes leaves the record removed and unlisted, which validation refuses. Rerunning `retract` for the same `id` completes the retraction, and an injected-failure fixture proves it.
  - Retracting the last record of a part deletes the part, leaving a gap in `NN`.
  - Each retraction-list entry has a UUIDv4 `id`, a category from `credential`, `personal-data`, `legal` and `other`, known keys only, and a unique `id`.
  - Validation refuses an edited or removed list entry against the merge base, a listed `id` reappearing in either form, and a removed bundled record not newly listed in the same change.
  - The list and the rewritten part keep `compact`'s confinement, symlink-refusal and atomic-write fixtures.
- [x] **AC-B4b — retraction procedure:** `docs/product/AGENTS.md` documents `retract` and states each of these. A pinned test checks the text:
  - contain or rotate a leaked credential before retracting;
  - the retraction commit's diff, Git history, forks and feed readers still disclose the retracted bytes;
  - any history rewrite is a separate decision for the owner.
- [x] **AC-B5 — raw bytes:** merge-base blobs are read as bytes, so a CR or non-UTF-8 byte changed in a moved record is refused.
- [x] **AC-B6 — compaction:**
  - `compact --month YYYY-MM` needs a real month. It moves only fragments of that month released against the same released-version inventory the site build uses, and leaves pending ones. A pinned test shows `compact` and the build classify the same fragments as released.
  - It reads no clock, which a fixture with a patched clock proves.
  - It appends parts after the month's highest `NN` and rewrites none. It writes new parts with exclusive create inside a non-link directory.
  - It re-reads every part it wrote and checks its bytes before deleting any fragment.
  - It reports a fragment too large for a part and leaves it loose.
  - It leaves the complete view and `/now/` payload byte-identical.
  - A failure before deletion removes the created parts.
  - A failure injected partway through deletion leaves the parts and every record present in at least one form, and a rerun completes the move.
  - Its part writer takes an explicit record set. `compact` and T18 both call it, and it orders and splits that set the same way for both.
- [x] **AC-B7 — bounds:** these are refused fail-closed: a part over 1,048,576 bytes, more than 65,536 records across both forms, and a traversal-bound breach in either directory. A merge-base blob or retraction list over 1,048,576 bytes is refused after a size check, without being read in full.
- [x] **AC-B8 — single reader and ceiling:** `tools/build-site.py`, `tools/check-core-release.py`, `tools/repo/check_release_impact.py` and the `render` command read records through one reader in `tools/changelog.py`. None passes a substitute enumerator, helper handle or Git runner, and a fixture checks those call sites. `tools/build-site.py` does three things:
  - it warns when more than 375 released fragments are loose;
  - it refuses to build when more than 500 are loose;
  - it warns when more than 250 fragments are pending.
- [x] **AC-B8a — release evidence:** among changelog paths, only an added or changed fragment counts as release evidence in `tools/repo/check_release_impact.py`. Fragment deletions, part additions and retraction-list entries do not. A release-impacting change whose only evidence is one of those is refused, with a fixture for each shape. The existing version-file indicators still count. A version bump paired with fragment deletions passes, with its own fixture.
- [x] **AC-B8b — release checklist:** the release checklist in `packs/AGENTS.local.md` states the step of running `compact` for each closed month with released fragments still loose. A pinned test checks the text.
- [x] **AC-B9 — merge replay:** with bundle parts on the base, 20 fragment-adding branches still yield 0 of 190 conflicting pairs. A fragment-adding branch against a compaction does not conflict. A body edit against a compaction of the same month either reports the modify/delete conflict or, where Git treats a one-record part as a rename and merges cleanly, leaves a result that `validate` refuses as a bundled record edited in place. Two compactions of one month conflict.
- [x] **AC-B10 — workflows:** `.github/workflows/pages.yml` triggers on `docs/product/changelog.months/` and `docs/product/changelog-retractions.toml`, both pinned in `REQUIRED_PATHS` in `tools/test-pages-workflow.py`.
- [x] **AC-B11 — merge-blocking validation:** the required `build-check.yml` gate-main job runs `python3 tools/changelog.py validate` on every pull request with no paths filter. That covers cross-form identity, the container rules and the retraction list against the pull request's merge base. A failure blocks the merge. The step carries its `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`.

## Follow-ons

- Platform Core maintainers: `docs/architecture/changelog-fragment-source.md` — resolving the delta's `Status` line once this delivery lands is theirs, not this spec's.
- eugenelim: `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md` — a superseding ADR, should the three-arm build-cost figure lead maintainers to block delivery. Out of scope here by ADR-0123's own revisit clause.

## Assumptions

- Technical: whether the `[Unreleased]` release transition can be implemented without writing a merged fragment's `packages`, `date` or `id` is unresolved. § 4 Published identity permanence forbids editing any of the three in an already-merged fragment, and a fragment authored before its release date must acquire a release date somehow — from a field the envelope does not yet carry, from the release pipeline, or by deferring fragment creation to release time. It would change the envelope and the release gesture (settled by: Platform Core maintainers; a resolution requiring that row to change is an architecture amendment, not a spec decision).
- Technical: whether a synthetic corpus of repeated bodies stands in for real fragment prose at ten times the entry count is unsettled, and the assembly spike recorded that it never measured a realistic body weight — it would change how much weight the three-arm figure carries (settled by: the owner, on reading the run).
- Technical: the assembly spike's `+66.08%` build-cost figure is unusable for the rewritten § 7 Build performance bar in either direction, because it sums a fragment-versus-monolith delta and a monolith-versus-today delta that the row assigns to different owners, and no monolith-at-scale arm was ever built — so the fragment-versus-monolith ratio is ungrounded until this spec's three-arm task runs.
- Technical: the per-file byte bound is settled at 1,048,576 bytes for fragments, bundle parts, merge-base blobs and the retraction list, and records across both storage forms are capped at 65,536 (settled by: ADR-0143 D5 and D10). The traversal bounds' values remain owned by Platform Core maintainers through the `Ask first` threshold route.
- Technical: the instrument-validity stop predicate is settled: an arm is valid
  only when `(maximum retained duration - minimum retained duration) / median
  duration <= 20%`; if any arm fails, the run is inconclusive and no ratio is
  accepted. This is an instrument rule, not § 7's performance bar (settled by:
  eugenelim before T13, recorded in the verification ledger).
- Technical: the valid T15 rerun measured 18.69% fragment overhead. T16's
  equal-scale pre-edit profile refuted helper-module loading as the dominant
  cost and measured released-inventory re-validation at 7.55 seconds (55.6%)
  versus helper loading at 2.25 seconds (16.6%). The production owner is
  `is_fragment_released`: normalize one inventory once per projection rather
  than once per fragment (settled by: measured T16 profile and owner approval).
- Technical: both post-T16 pass-4 executions were inconclusive because the
  short `today` arm exceeded the precommitted 20% spread bound on a loaded
  machine. Their unaccepted large-arm ratios were 18.41% and 14.66%, so they do
  not replace pass 3's valid 18.69% `KILL`. The owner authorizes one pass 5 only
  after the explicit quiet-machine gate above, with no retry if that pass is
  also inconclusive (settled by: pass-4 evidence and 2026-10-02 owner approval).
- Technical: pass 5 was valid at +12.12% fragment overhead, a `KILL` against the under-10% bar. Four attribution spikes put the whole gap in the changelog projection: about 3 s from reloading the file-safety helper per fragment, and the rest scaling with the loose-fragment count. The owner chose on 2026-10-03 to load the helper once in T16 and to add monthly bundles under ADR-0143, remeasured by T18 (settled by: pass-5 and spike evidence, recorded in the build-cost report, and owner approval).
- Technical: a bundle part's month is the month of the envelope `date`, which AC5 already freezes for a merged record, so no `[Unreleased]` release transition can move a record between months (settled by: AC5 and ADR-0143 D2).
- Technical: whether the `/now/` permalink, pagination, archive and feed routes need a durable spec of their own is unresolved. `docs/specs/site-now-surface/spec.md` is Shipped and silent on all four, so the routes under `web/src/pages/now/` are the only description of them, and this spec cites that spec only for editorial authority (settled by: Platform Core maintainers).
