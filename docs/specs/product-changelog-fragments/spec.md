# Spec: Per-update product changelog sources and generated views

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0123
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
- Author guidance — `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `changelog.md` header, and a fragment template
- A quiet-machine three-arm build-cost measurement, which the assembly spike could not supply

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — this delivery makes the delta's § 4 rows live | `docs/architecture/changelog-fragment-source.md` | Platform Core maintainers | A named passing test for every § 4 row's Verification column and every § 7 row's Verification column | Each § 4 and § 7 row names a test that exists and passes; the delta's `Status` line is resolved by Platform Core maintainers, who own that transition |
| Decision rationale | Already owned | `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md` | Platform Core maintainers | The accepted ADR and its five Confirmation signals | Every Confirmation signal has a named passing test. A delivery that cannot satisfy one opens a superseding ADR rather than editing this one |
| Maintainer procedure | Applicable — the authoring gesture changes for every contributor | `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `docs/product/changelog.md` header, and the fragment template | eugenelim | Each surface states the fragment gesture and none still instructs an author to edit `changelog.md` | A repository-wide search for instructions to edit `changelog.md` returns only the frozen-history notice |
| Interface compatibility | Applicable — `/now/<anchor>/` and the Atom `<id>` are published identities | `web/src/pages/now/` and `web/src/components/now/NowHighlights.astro` | eugenelim | The payload validates against the five importers' existing `schemaVersion` guards without editing them, and every historical anchor is unchanged | No consumer guard is edited and no historical anchor moves |
| Operations | Applicable — validation and the site build gain failure modes | `.github/workflows/pages.yml` and the existing validation job | eugenelim | A fixture per diagnostic class, each naming a fragment path and an invariant | Every diagnostic class has a fixture and the build reports fragment, release and Highlights counts |
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

### Never do

- Track a combined changelog, add a custom merge driver for it, add a post-merge bot writer, or add a protected-branch bypass. ADR-0123 D6 keeps all four out of the merge-queue-critical path.
- Edit, reorder or reword a historical release section or heading in `docs/product/changelog.md`. A migration notice is the only admitted change.
- Combine, summarize, reword or re-split any fragment's Highlights during assembly.
- Bump `now-highlights.generated.json` past `schemaVersion` 1.
- Read a generated view as an authoring input.
- Give the assembler a network, clock, Git-history or model dependency, per ADR-0123 D4. Validation and the release checks may make read-only merge-base and changed-path Git reads, which § 4 Published identity permanence names as its enforcement mechanism; no such read may reach published content.
- Add a new top-level directory, package or third-party dependency.

## Testing Strategy

- Fragment envelope, body, identity, anchor and immutability validation: **TDD**. Each is a pure function over text with a compressible invariant, and each refusal is a named diagnostic class.
- Canonical ordering and deterministic assembly: **TDD**, with a mutation arm — the canonical sort removed — that must change the output.
- `/now/` payload parity and Highlights integrity: **goal-based**, exercised by an **integration** test that compares the assembled payload against the serialized payload the shipping projector emits.
- Merge independence: **goal-based**, exercised by an **integration** check that replays synthetic branch pairs through `git merge-tree`, with a monolith control arm.
- Historical-anchor stability under the monolith counterfactual: **goal-based**, exercised by an **integration** check that prepends the same updates into `changelog.md` and re-slugs.
- Complete-view rendering, regeneration cleanliness and workflow triggers: **goal-based**, each verified by one command whose observable is a file, a digest or an empty `git status`.
- Build cost and published page count: **goal-based**, exercised **end-to-end** by the real `make site-build` in a disposable clone across three arms.
- The authoring gesture — `python3 tools/changelog.py new`, then `render` — is **visual / manual QA**: a maintainer invokes both and records the created path, the rendered output and the exit codes.

## Acceptance Criteria

Each criterion below states its own threshold. Where the threshold comes from
`docs/architecture/changelog-fragment-source.md` § 4 or § 7, the criterion cites
the row that owns it; those sections win where this spec and they ever disagree.
Where a criterion lifts a figure the assembly spike measured, it names the base
commit that figure was taken at.

### Fragment source and identity

- [ ] `python3 tools/changelog.py new` creates exactly one file, at `docs/product/changelog.d/<id>.md`, whose filename stem is a lowercase UUIDv4 and whose envelope `id` is that same string, per ADR-0123 D2 and § 4 Fragment identity and path.
- [ ] Validation refuses each member of this closed set, naming the fragment path and the offending field: a stem that does not match the envelope `id`; an `id` that is not a lowercase UUIDv4; an uppercase-hexadecimal `id`; and an `id` that duplicates another fragment's. Per § 4 Fragment identity and path.
- [ ] Validation accepts a fragment whose front matter opens with a `+++` line, carries TOML `schema`, `id`, `anchor`, `date` and one or more `packages` records each with `name` and `version`, and closes with a second `+++` line; and refuses each member of this closed set, naming the path and the offending field: a missing delimiter, a missing required field, an unknown field, a field of the wrong type, malformed TOML, and an unrecognized `schema` value. Per § 4 Fragment envelope.
- [ ] Validation accepts a body whose sections are drawn from the changelog's established section names and which carries a non-empty `Highlights` section, and refuses each member of this closed set: an unknown section name, a duplicate section, a release-level heading, and an absent or empty `Highlights`. Per § 4 Fragment body.
- [ ] The fragment reader admits only regular files under `docs/product/changelog.d/`, refusing a symlink, a directory entry and a non-regular file by path, through the repository's blessed confined-file helpers.
- [ ] The fragment reader passes the blessed confined-file helpers' traversal bounds — their entry, file-count and depth limits — and their per-file byte bound, and refuses fail-closed by path when any one is exceeded, rather than enumerating or reading an untrusted tree without a ceiling.

### Published anchor and identity permanence

- [ ] A fragment's envelope `anchor` is the slug the existing slugger produces for that fragment's package-and-date heading, a hyphen, then the fragment's own `id` as 32 lowercase hexadecimal digits; `new` writes it at creation and the validator recomputes it from `packages`, `date` and `id` and refuses a mismatch. Per § 4 Stable links.
- [ ] Two fragments whose `packages` and `date` produce the same slug receive distinct anchors, and neither anchor is derived from reading the other fragment. Per § 4 Stable links.
- [ ] Validation refuses a change to `packages`, to `date`, or to `id` in a fragment already present at the merge base, naming the field and the fragment path. Per § 4 Published identity permanence.
- [ ] Every anchor the renderer emits appears as `<a id="<anchor>"></a>` immediately before its update heading in the generated complete changelog, and every `/now/` anchor resolves to an element of that id in the emitted changelog page. Per § 4 Stable links.

### Assembly, ordering and determinism

- [ ] Assembling the frozen baseline plus a fragment set across 5 shuffled directory enumerations produces 1 distinct output digest, and the same 5 enumerations with the canonical sort removed produce at least 2. Per § 7 Determinism; the figures 1 and 5 were measured at base `93bf9cc9e`.
- [ ] Output order is `date` descending then `id` ascending, and the renderer emits no field derived from a clock, from filesystem enumeration order or from Git history. Per § 4 Canonical identity and order and § 4 Deterministic assembly.
- [ ] Every fragment appears exactly once in the complete view, and every Highlights item appears exactly once and byte-for-byte in the `/now/` payload. Per § 7 Content integrity and ADR-0123 D3.
- [ ] Every fragment's complete body — every section's text and the order those sections appear in — is present in the complete view unchanged and exactly once, so a dropped or reworded non-Highlights section fails. Per § 4 Fragment body, whose Verification column requires round-trip fixtures and exact-body assertions, and ADR-0123 D3.

### Historical compatibility

- [ ] The `/now/` payload assembled with zero fragments is byte-identical to the payload `tools/build-site.py` emits from `docs/product/changelog.md` alone, whose sha256 is `72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40` at base `93bf9cc9e`. Per § 7 Historical compatibility.
- [ ] No anchor present in the zero-fragment payload is absent or changed in a payload assembled with fragments present. Per § 7 Historical compatibility.
- [ ] Prepending the same fragment set into `docs/product/changelog.md` as release sections moves at least one historical anchor through the slugger's duplicate-suffix renumbering, or the run records that it moves none; the figure is recorded either way, against the fragment path's figure of zero. This is the arm the assembly spike named as the one that can fail and did not run.
- [ ] The generated complete changelog contains every pre-cutover release section from `docs/product/changelog.md` with its heading text and section body unchanged, verified against a recorded digest of those sections. Per § 4 Immutable historical baseline.
- [ ] A change that edits a historical release section or heading in `docs/product/changelog.md` is refused by a gate naming the edited heading. Per § 4 Immutable historical baseline.
- [ ] `docs/product/changelog.md` carries a migration notice naming the public `/changelog/` view and the `python3 tools/changelog.py render --output build/product-changelog.md` command, and that notice is the only change to the file. Per § 5.

### `[Unreleased]` aggregation at release time

- [ ] A fragment for a package version that is not yet released appears in the `[Unreleased]` region of the generated complete changelog and produces no `/now/` group.
- [ ] After that version is released, the same fragment's Highlights appear exactly once in a released group of the `/now/` payload, and the fragment's `id` is the one it was created with.
- [ ] Each released fragment yields one distinct `/now/` group carrying that fragment's own `anchor` and only that fragment's own Highlights, so two fragments' bullets collapsed into one group fails. Per § 4 Atomic Highlights, which derives the permalink page and the feed entry from that group.
- [ ] A fragment moving from unreleased to released changes no byte of any other fragment's record in the complete view or the `/now/` payload.

### Merge independence and Git cleanliness

- [ ] For 20 synthetic branches that each add one `docs/product/changelog.d/<uuid>.md` and nothing else, 0 of the 190 unordered branch pairs are classified as conflicting on a changelog path by `git merge-tree`, and 0 pairs exit non-zero for any other reason. Per § 7 Mergeability; measured as 0 of 190 at base `443f141f2`.
- [ ] For a control arm of 20 branches that each instead prepend one release section to `docs/product/changelog.md`, the conflicting-pair figure is greater than zero and the error figure is 0, without which the fragment arm's zero is not a measurement. Measured as 190 of 190 at base `443f141f2`.
- [ ] Regenerating every view from a clean checkout leaves `git status --porcelain` empty, and `git check-ignore build/product-changelog.md` reports the file ignored. Per § 7 Git cleanliness and ADR-0123's fifth Confirmation signal.

### Consumers and release validation

- [ ] `now-highlights.generated.json` stays at `schemaVersion` 1, and a payload assembled with fragments present validates against the existing guards in `web/src/pages/now/index.astro`, `web/src/pages/now/page/[page].astro`, `web/src/pages/now/archive/index.astro`, `web/src/pages/now/[release].astro`, `web/src/pages/now/feed.xml.ts` and `web/src/components/now/NowHighlights.astro` with none of those six files' guards edited. Per § 4 Projection schema version.
- [ ] `tools/check-core-release.py` matches a core release to a changed fragment rather than to the topmost heading of `docs/product/changelog.md`, and refuses a release whose fragment carries no Highlights bullet.
- [ ] `tools/repo/check_release_impact.py` treats an added or changed path under `docs/product/changelog.d/` as satisfying its changelog requirement, and its existing refusal for a release-impacting change with no changelog evidence still fires.
- [ ] `.github/workflows/pages.yml` triggers the documentation build on a change under `docs/product/changelog.d/` and on a change to `docs/product/changelog.md`, and the repository's owning allowlist — `REQUIRED_PATHS` in `tools/test-pages-workflow.py`, enforced over the `push` and `pull_request` triggers — pins both paths, so removing either trigger fails.

### Diagnosability, posture and cost

- [ ] Every refusal this spec names reports the fragment path, the field or invariant that failed, and the expected correction; a fixture exercises each refusal class. Per § 7 Failure diagnosability.
- [ ] A successful build reports the fragment count, the release count and the Highlights count, which is what makes a parity check possible without a second parse. Per § 6.
- [ ] A fragment set containing any refusal class this spec names produces no generated view and changes no existing generated view, exercised over at least one file-safety refusal and one schema refusal. Per § 3's failure path, which publishes no new output.
- [ ] An end-to-end build of every view completes with no network access available, and a static dependency check reports no third-party import added by any `tools/` entry point this delivery touches, that set being the one the plan's tasks pin in their `Touches` fields. Per § 7 Dependency and privacy posture and § 4 Human editorial authority.
- [ ] A three-arm interleaved measurement on a quiet machine, each arm discarding one warm-up run, records the median `make site-build` duration for today's corpus, for a monolith carrying ten times the released entries, and for that same canonical record set laid out as fragments; the two large arms are generated from one record set and differ only in physical layout. The recorded ratio is the fragment median minus the monolith median over the monolith median, judged against § 7 Build performance, which owns the bar.
- [ ] The same measurement records each arm's retained-duration spread and applies the instrument-validity stop predicate Platform Core maintainers set for it, classifying a run that fails that predicate as inconclusive rather than as a ratio. Until that predicate is recorded, no T13 ratio is accepted; the predicate is not a restatement of the § 7 Build performance bar, which judges an already-valid run.
- [ ] That same measurement records the published page count per arm, and the fragment and monolith arms at equal release count emit the same number of pages. Per § 7 Published page count.
- [ ] The two Astro phases are timed in isolation rather than in sequence, so the recorded fragment-versus-monolith difference is attributable rather than inherited from the phase before it.

## Follow-ons

- Platform Core maintainers: `docs/architecture/changelog-fragment-source.md` — resolving the delta's `Status` line once this delivery lands is theirs, not this spec's.
- eugenelim: `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md` — a superseding ADR, should the three-arm build-cost figure lead maintainers to block delivery. Out of scope here by ADR-0123's own revisit clause.

## Assumptions

- Technical: whether the `[Unreleased]` release transition can be implemented without writing a merged fragment's `packages`, `date` or `id` is unresolved. § 4 Published identity permanence forbids editing any of the three in an already-merged fragment, and a fragment authored before its release date must acquire a release date somehow — from a field the envelope does not yet carry, from the release pipeline, or by deferring fragment creation to release time. It would change the envelope and the release gesture (settled by: Platform Core maintainers; a resolution requiring that row to change is an architecture amendment, not a spec decision).
- Technical: whether a synthetic corpus of repeated bodies stands in for real fragment prose at ten times the entry count is unsettled, and the assembly spike recorded that it never measured a realistic body weight — it would change how much weight the three-arm figure carries (settled by: the owner, on reading the run).
- Technical: the assembly spike's `+66.08%` build-cost figure is unusable for the rewritten § 7 Build performance bar in either direction, because it sums a fragment-versus-monolith delta and a monolith-versus-today delta that the row assigns to different owners, and no monolith-at-scale arm was ever built — so the fragment-versus-monolith ratio is ungrounded until this spec's three-arm task runs.
- Technical: the numeric traversal and byte bounds the fragment reader enforces are unresolved. The blessed confined-file helpers expose the bounds, but no § 4 or § 7 row fixes their values and this spec's own `Always do` rule forbids it inventing one — it would change how a large or deep untrusted tree is refused (settled by: Platform Core maintainers, through the `Ask first` threshold route).
- Technical: the instrument-validity stop predicate for T13 is unresolved. § 7 Build performance owns the ratio bar but no authority fixes a dispersion bound, and the assembly spike's control arm varied from 22.92s to 75.41s on identical input — it would decide whether a noisy run yields a ratio or an inconclusive verdict (settled by: Platform Core maintainers).
- Technical: whether the `/now/` permalink, pagination, archive and feed routes need a durable spec of their own is unresolved. `docs/specs/site-now-surface/spec.md` is Shipped and silent on all four, so the routes under `web/src/pages/now/` are the only description of them, and this spec cites that spec only for editorial authority (settled by: Platform Core maintainers).
