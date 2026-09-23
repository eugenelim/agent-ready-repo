# Plan: Per-update product changelog sources and generated views

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/adr/0123-product-changelog-per-update-sources-and-generated-views.md`
  D1–D7 and `docs/architecture/changelog-fragment-source.md` § 4, § 7 and § 8
  own the decisions and the bars; `docs/product/research/changelog-fragment-assembly-spike.md`
  supplies three measured figures and names the two arms it did not run.
  Analogous production implementations: `tools/build-site.py` — its
  `parse_changelog_releases`, `_Slugger`/`_slug_base` and `_project_parsed`
  are the seam the model reuses, and `tools/check-output-readability.py`'s
  `_file_safety` loader is the `importlib`-by-path route to the blessed
  confined-file helpers that `tools/AGENTS.md`'s pure-stdlib rule requires.
  Construction path for a tracked measurement script:
  `tools/measure-changelog-fragment-merges.py`. Named uncertainty: whether the
  `[Unreleased]` release transition can be built without editing a merged
  fragment's `packages`, `date` or `id` (spec Assumptions).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure.

## Approach

One new module, `tools/changelog.py`, owns the changelog contract end to end:
the historical parser and slugger relocated into it by T0, then creation,
validation, the shared model, canonical ordering and rendering. Every other
touched file becomes a caller of it and none of them is called back, which is
what § 8's "one shared Python owner" buys — fragment logic cannot diverge
between the site build, the release checks and a maintainer's local render, and
the module edge stays acyclic.

The order of operations is contract first, consumers second, measurements last.
T0 leads because the anchor composition and the canonical sort both reach for
the historical slugger and parser, and a shared owner that loads its caller to
get them is not a shared owner. Validation and identity (T1–T3) come before the
model (T4) because the model's
canonical sort is only meaningful over records that already have a unique,
immutable identity. Rendering (T5) precedes both consumers and the freeze,
because the freeze gate compares generated output against a digest of the
historical sections and that comparison needs a renderer. The two promoted
verification gaps sit where their subject lands: the monolith anchor
counterfactual (T9) after the freeze, the `[Unreleased]` transition (T6) beside
the model it changes. Consumers (T7, T11) then switch in one change, per § 8's
shared failure boundary, and T14 closes the dependency-posture half of § 7 that
only holds once every touched entry point is final.

The riskiest part is T6. Its design question is open in the spec's Assumptions
and the answer may oblige an architecture amendment rather than code, so it
carries an explicit stop rather than a default. The second riskiest is T13: the
three-arm build-cost run has to be genuinely wired in and genuinely quiet, and
the assembly spike's own instrument failed on the second count.

## Constraints

- ADR-0123 is Accepted. D1–D7 are implemented here, not revisited. A delivery
  that cannot satisfy a D-decision or a Confirmation signal opens a superseding
  ADR rather than editing the accepted one.
- `docs/architecture/changelog-fragment-source.md` § 4 owns every contract row
  and § 7 owns every quality bar, including the rewritten Build performance row
  and the new Projection schema version, Published identity permanence and
  Published page count rows added at `0ab3de273`. Each task cites the row it
  takes a threshold from; § 4 and § 7 win where this plan and they disagree.
- `tools/AGENTS.md`: a new `tools/` addition is pure-stdlib Python. The blessed
  confined-file helpers are reached by `importlib`-from-path.
- `docs/product/AGENTS.md`: `web/src/lib/now-highlights.generated.json` is
  generated and gitignored, rebuilt by the `npm run` scripts that import it.
  Nothing in this delivery commits it.
- `build/` is already gitignored and `docs-site/src/content/docs/changelog.md`
  is already an untracked generated copy. Neither needs a new ignore rule.
- `docs/specs/site-now-surface/spec.md` is Shipped and silent on the permalink,
  pagination, archive and feed. It is cited for editorial authority only; the
  routes under `web/src/pages/now/` are the only description of those surfaces.

## Construction tests

**Integration tests:**
- One end-to-end render from a clean checkout that produces `build/product-changelog.md`, the site changelog copy and the `/now/` payload from one model pass, then asserts `git status --porcelain` is empty. This spans T5, T7 and T8 and is the only check that sees all three outputs come from a single parse.
- One offline build of every view with no network access available, spanning T5 and T7.

**Manual verification:** a maintainer runs `python3 tools/changelog.py new`,
edits the created fragment, runs `python3 tools/changelog.py render --output
build/product-changelog.md`, and records the created path, both exit codes and
the rendered update's position and anchor in the output.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture — `docs/architecture/changelog-fragment-source.md` | T0–T14 | A named passing test per § 4 and § 7 row | Every row's Verification column names a test that exists and passes; Platform Core maintainers resolve the delta's `Status` |
| Decision rationale — ADR-0123 | T4, T5, T8, T10 | A named passing test per Confirmation signal | All five signals covered; an unsatisfiable signal opens a superseding ADR |
| Maintainer procedure — `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `changelog.md` header, the fragment template | T12 | The four edited surfaces | A repository search for instructions to edit `changelog.md` returns only the frozen-history notice |
| Interface compatibility — the six `/now/` payload and anchor consumers | T7 | The payload validating against the unedited consumer guards | No consumer guard edited; no historical anchor moved |
| Operations — `.github/workflows/pages.yml` and the validation job | T7, T11 | Path-trigger test plus one fixture per diagnostic class; T7's count output | Each diagnostic class has a fixture; the build reports fragment, release and Highlights counts |
| Dependency and privacy posture — every `tools/` entry point this delivery touches | T14 | The static dependency check's output and the offline build | No third-party import is reported and the offline build completes |
| Reusable learning — `docs/product/research/changelog-fragment-build-cost.md` | T13 | The three-arm run's retained stdout | The report names its machine, base commit, both required ratios and a verdict per ratio |

## Design (LLD)

### Data & schema

A fragment is TOML front matter delimited by a `+++` line at the head and a
second `+++` line closing it, then a Markdown body. Required envelope fields are
`schema`, `id`, `anchor`, `date`, and one or more `packages` records each with
`name` and `version`, exactly as § 4 Fragment envelope states. `id` is a
lowercase UUIDv4 produced by `uuid.uuid4()`. TOML is parsed by the standard
library's `tomllib`, so the envelope adds no parser dependency; field presence
and type are then checked explicitly, because `tomllib` validates syntax and not
shape.

`anchor` is composed once, at creation, and never looked up against another
fragment: the slugger's package-and-date slug, a hyphen, then `id.hex` as 32
lowercase hexadecimal digits. The validator recomputes it from `packages`,
`date` and `id` and refuses a mismatch, which is what makes the three fields'
immutability and the anchor's permanence the same guarantee.

The body's admitted section names come from the established changelog section
set; the parser rejects an unknown or duplicate section and any release-level
heading, because a release-level heading inside a fragment would make the
renderer's own heading ambiguous.

Traces to: the fragment source and identity criteria, and the published anchor
criteria · contracts: none.
Owned by: T1, T2, T3.

### Interfaces & contracts

`tools/changelog.py` exposes three command surfaces — `new`, `validate` and
`render` — and one importable model. The model is what `tools/build-site.py`,
`tools/check-core-release.py` and `tools/repo/check_release_impact.py` consume;
none of them re-parses a fragment or reads a generated view.

The dependency runs one way: `tools/build-site.py` imports from
`tools/changelog.py`, and `tools/changelog.py` never loads its caller. The
shared owner cannot depend on a consumer it is supposed to own, and two
module-level `importlib` loads of each other recurse rather than raise a
recognizable circular-import error.

T0 makes that direction true by relocating the changelog primitives —
`parse_changelog_releases` and the `ParsedChangelog`/`ChangelogHeading` records,
`_parse_release_identity`, `_strip_changelog_comments`, `_slug_base`,
`_Slugger`, `highlight_segments` and `_project_parsed` — out of
`tools/build-site.py` and into `tools/changelog.py`, leaving `build-site.py`
importing them. That is the single seam the historical parser and slugger are
reached through, and it is what § 8's "one shared Python owner" and ADR-0123 D7's
"consume the shared changelog model rather than reparse" already require.
`tools/build-site.py` carries a hyphen in its name, so its importers load
`tools/changelog.py` by `importlib` from its path — the same route
`tools/check-output-readability.py` uses for the confined-file helpers. Only
the confined-file helpers are still reached that way from `tools/changelog.py`.

The `/now/` payload keeps the group shape `_project_parsed` already emits —
`packages`, `date`, `heading`, `changelogAnchor`, `highlights` — at
`schemaVersion` 1. A fragment-backed group differs from a history-backed one
only in where `changelogAnchor` came from, which is why § 4 Projection schema
version can hold the version still.

Traces to: the assembly, historical-compatibility and consumer criteria ·
contracts: none.
Owned by: T0, T4, T5, T7, T11.

### Component / module decomposition

New: `tools/changelog.py` — envelope parser, body parser, confined fragment
reader, identity and immutability validators, the shared model, the canonical
sort, and the complete-view renderer.

Relocated by T0, behaviour preserved: the changelog parser, slugger and
highlight segmenter keep what they do and change module ownership from
`tools/build-site.py` to `tools/changelog.py`. Modified: `tools/build-site.py`'s
`/now/` projection entry point and its changelog copy step, which now take a
model rather than a file path.

Traces to: the assembly and consumer criteria · contracts: none.
Owned by: T4, T5, T7.

### State & control flow

An update has two states in the complete view: beneath `[Unreleased]`, and
released. Today that state is carried by heading nesting in one file; with
fragments there is no enclosing heading, so the state has to be derived or
declared per fragment.

This is the plan's one unresolved load-bearing choice and the spec records it as
an Assumption. The three candidate resolutions are: derive released-ness by
comparing each `packages` record's `version` against the released version of
that pack; carry an explicit unreleased marker in the envelope that the release
pipeline clears; or defer fragment creation to release time so no fragment is
ever unreleased. The first two interact with § 4 Published identity permanence,
which forbids editing a merged fragment's `packages`, `date` or `id`; the third
changes the authoring gesture the whole design exists to make independent. T6
stops for that decision rather than defaulting to one, and a resolution that
needs the § 4 row to change is an architecture amendment, not a code change.

Traces to: the `[Unreleased]` aggregation criteria · contracts: none.
Owned by: T6.

### Failure, edge cases & resilience

Every refusal is a named class carrying the fragment path, the failing field or
invariant, and the expected correction, per § 7 Failure diagnosability. The
classes are: identity mismatch, malformed identity, duplicate identity, envelope
delimiter, missing field, unknown field, wrong field type, malformed TOML,
unrecognized schema, unknown body section, duplicate body section, release-level
heading in a body, absent or empty Highlights, anchor mismatch, merged-field
edit, and unsafe path. A fragment that fails any of them fails the build before
any view is published; there is no partial render and no degraded mode, because
a published half-view is worse than a failed build for a documentation surface.

The reader refuses a symlink, a directory entry and any non-regular file through
the blessed confined-file helpers rather than through its own `lstat` logic.

Traces to: the diagnosability criterion and the fragment-source criteria ·
contracts: none.
Owned by: T1, T3.

### Quality attributes (NFRs)

Determinism is structural: the canonical sort runs before any view is
constructed, so filesystem enumeration order cannot reach the output, and no
field is read from a clock or from Git history. The mutation arm — the sort
removed — is what makes the shuffled-enumeration figure a measurement rather
than an observation that the enumeration never varied.

Build cost is the one attribute this delivery cannot design its way to. The
assembly spike's figure is unusable against the rewritten § 7 bar in either
direction, so T13 measures it fresh, three arms, phases isolated, on a quiet
machine, and Platform Core maintainers decide what a failing ratio means.

Observability is the build's own report: fragment, release and Highlights counts
printed per run, which is what makes a parity check possible without a second
parse. T7 owns that output, because the production build is where it is emitted;
T4 owns only the determinism properties above it.

Traces to: the determinism, diagnosability and cost criteria · contracts: none.
Owned by: T4, T7, T13.

### Dependencies & integration

No new package, service, top-level directory or third-party dependency. The
cross-module coupling added runs one way — `tools/build-site.py`,
`tools/check-core-release.py` and `tools/repo/check_release_impact.py` each load
`tools/changelog.py` by `importlib` from its path — plus the same path-load of
the blessed confined-file helpers from `tools/changelog.py`. Nothing loads
`tools/build-site.py` from `tools/changelog.py`. `tools/check-core-release.py` is
delivery-time only — no workflow or Makefile target invokes it — so its change
is verified by direct invocation rather than by a gate.
`tools/repo/check_release_impact.py` runs at
`.github/workflows/catalogue-tooling-ci-gates.yml:561`, so its change is
verified there.

Traces to: the consumer and posture criteria · contracts: none.
Owned by: T7, T11.

## Tasks

### T0: The changelog parser, slugger and projector move to the shared owner

**Depends on:** none

**Touches:** tools/changelog.py, tools/build-site.py, tools/test_build_site_routing.py

**Tests:**
- `parse_changelog_releases`, `ParsedChangelog`, `ChangelogHeading`, `_parse_release_identity`, `_strip_changelog_comments`, `_slug_base`, `_Slugger`, `highlight_segments` and `_project_parsed` live in `tools/changelog.py`, and `tools/build-site.py` imports them from there. Verifies the one-shared-owner direction § 8 requires.
- `tools/changelog.py` contains no load of `tools/build-site.py`, asserted by searching the module's source for that path. Verifies the acyclic direction: the shared owner must not load its caller.
- Every existing `tools/test_build_site_routing.py` case that exercised those callables is green against their new home, unmoved in substance. That suite is the one that reaches them — it carries 23 references to `parse_changelog_releases`, `_project_parsed`, `_slug_base`, `_Slugger` and `highlight_segments`, and the other five `tools/test_build_site_*.py` suites carry none.
- The `/now/` payload `tools/build-site.py` emits is byte-identical before and after the relocation, so the move changes no output.
- stub: true — one compilable assertion that `tools.changelog.parse_changelog_releases` is the same object `tools/build-site.py` calls.

**Approach:**
- Relocate rather than duplicate. A second copy of the fence-and-comment state machine is exactly the drift `ParsedChangelog`'s own docstring warns about, and two copies would disagree about which `##` lines are real headings the first time either is touched.
- Do this first. T2 composes an anchor from the slugger and T4 sorts the model, so both would otherwise have to reach back into the caller.

**Done when:** `python3 -m pytest tools/test_build_site_routing.py -q` is green, the search for a `build-site` load inside `tools/changelog.py` returns nothing, and the emitted `/now/` payload's sha256 is unchanged.

### T1: Every named refusal class refuses, naming its path and field

**Depends on:** none

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- A fragment with a well-formed envelope and a non-empty `Highlights` body validates. Verifies the envelope and body acceptance criteria.
- Each refusal fixture below asserts all three elements the diagnosability criterion requires — the fragment path, the failed field or invariant, and the expected correction — not two of them. Verifies the third element of the diagnosability criterion, per § 6, which states the same three.
- One fixture per identity class — stem/`id` mismatch, non-UUIDv4 `id`, uppercase-hexadecimal `id`, duplicate `id` — each refused with the fragment path, the offending field and the expected correction in the message. Verifies the identity refusal criterion.
- One fixture per envelope class — missing head delimiter, missing closing delimiter, missing required field, unknown field, wrong field type, malformed TOML, unrecognized `schema` — refused the same way. Verifies the envelope criterion.
- One fixture per body class — unknown section, duplicate section, release-level heading, absent `Highlights`, empty `Highlights` — refused the same way. Verifies the body criterion.
- A symlink, a directory entry and a FIFO under the fragment directory are each refused by path through the blessed confined-file helpers. Verifies the confined-reader criterion.
- A tree exceeding the helpers' entry, file-count or depth bound, and a fragment exceeding their per-file byte bound, are each refused fail-closed by path rather than enumerated or read. Verifies the reader-bounds criterion. The bound values come from the `Ask first` decision the spec Assumptions name, not from this task.
- stub: true — one compilable assertion that `validate_fragment` on the mismatched-stem fixture raises the refusal type and its message contains the fragment path.

**Approach:**
- Reach `file_safety` by `importlib` from its path, following `tools/check-output-readability.py`'s `_file_safety` loader, because `tools/AGENTS.md` forbids importing `agentbundle` from a `tools/` script.
- Check field presence and type explicitly after `tomllib.loads`; `tomllib` validates syntax only, so an envelope with the right keys and wrong types parses cleanly.

**Done when:** `python3 -m pytest tools/test_changelog.py -q` is green, every refusal class above has a fixture, and each refusal message contains all three of the fragment path, the field or invariant name, and the expected correction.

### T2: `new` creates one fragment carrying its own composed anchor

**Depends on:** T0, T1

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- `new` creates exactly one file at `docs/product/changelog.d/<id>.md` whose stem is a lowercase UUIDv4 and whose envelope `id` equals that stem. Verifies the creation criterion.
- The written `anchor` equals the slugger's package-and-date slug, a hyphen, then `id.hex` — 32 lowercase hexadecimal digits — and the validator recomputes it and accepts. Verifies the anchor composition criterion.
- Two fragments whose `packages` and `date` yield the same slug receive distinct anchors, and neither invocation reads the other's file. Verifies the collision criterion.
- An anchor edited by hand after creation is refused with the recomputed value named. Verifies the anchor-mismatch refusal.
- stub: true — one compilable assertion that a `new`-created fragment round-trips through `validate_fragment` without refusal.

**Approach:**
- Compose the anchor from the fragment's own three fields only. A lookup against sibling fragments is what races across branches, and § 4 Stable links rests on its absence — assert in the test that the second `new` invocation opens no other fragment.

**Done when:** `python3 tools/changelog.py new` prints the created path, exits zero, and the created file validates; the collision test shows two distinct anchors from one slug.

### T3: A merged fragment's `packages`, `date` and `id` cannot be edited

**Depends on:** T1

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- For a fragment present at the merge base, an edit to `packages` is refused naming the field and the path; likewise for `date`; likewise for `id`. Verifies the immutability criterion, per § 4 Published identity permanence.
- An edit to the same fragment's body Highlights is accepted, so the refusal is scoped to the three identity fields rather than to the file.
- A fragment absent at the merge base is accepted with all three fields freely set, so a new fragment is not caught by the merged-fragment rule.
- stub: true — one compilable assertion that the `date`-edited merged fixture raises the refusal type.

**Approach:**
- Read the base copy through `git show <base>:<path>`, not from a working-tree cache: the check has to see the merge base's bytes, and a cached copy is the failure mode where a second edit in the same branch passes.

**Done when:** the three refusal fixtures and the two acceptance fixtures are green, and each refusal names the field.

### T4: Assembly is identical under shuffled enumeration and differs without the sort

**Depends on:** T0, T1

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- Assembling the frozen baseline plus a fragment set across 5 shuffled directory enumerations produces 1 distinct output digest. Verifies the determinism criterion, per § 7 Determinism.
- The same 5 enumerations with the canonical sort removed produce at least 2 distinct digests. Verifies the mutation-arm criterion, without which the shuffle arm proves only that the enumeration never varied.
- Output order is `date` descending then `id` ascending, asserted over a fixture with two same-date fragments whose `id`s order oppositely to their enumeration.
- No output field derives from a clock or filesystem order: two assemblies of the same sources taken at different wall-clock times are byte-identical, and the shuffle arms above cover enumeration order.
- Git-history arm: the assembler runs against one source set in two checkouts whose commit history differs — different commit SHAs, authors and dates for byte-identical sources — and the two outputs are byte-identical. Verifies the Git-history clause of the determinism criterion, which the wall-clock arm holds fixed rather than exercising. This arm constrains the assembler only; T3's read-only merge-base reads sit in validation, which ADR-0123 D4 does not reach.
- stub: true — one compilable assertion that two shuffled assemblies of one fixture set have equal digests.

**Done when:** the shuffle arm reports 1 digest, the mutation arm reports at least 2, and both figures appear in the test's own output rather than only in an assertion.

### T5: `render` emits the complete view with frozen history and per-update anchors

**Depends on:** T4

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- `render --output build/product-changelog.md` writes a file containing every pre-cutover release section from `docs/product/changelog.md` with heading text and body unchanged, verified against a recorded digest of those sections. Verifies the frozen-history criterion, per § 4 Immutable historical baseline.
- Every fragment appears exactly once in the output, and every Highlights item appears exactly once and byte-for-byte. Verifies the content-integrity criterion, per § 7 Content integrity.
- Every fragment's complete body — each section's text and the order the sections appear in — is present unchanged and exactly once, exercised by a round-trip fixture carrying a non-Highlights section that a byte-count check alone would not catch. Verifies the body-fidelity criterion, per § 4 Fragment body's round-trip and exact-body requirement.
- Each update heading is immediately preceded by `<a id="<anchor>"></a>` carrying that fragment's envelope `anchor`. Verifies the emitted-anchor criterion, per § 4 Stable links.
- `git check-ignore build/product-changelog.md` reports the file ignored, and a render from a clean checkout leaves `git status --porcelain` empty. Verifies the Git-cleanliness criterion, per § 7 Git cleanliness and ADR-0123's fifth Confirmation signal.
- stub: true — one compilable assertion that the rendered output contains the historical sections' digest-matching span.

- A fragment set containing one file-safety refusal, and separately one schema refusal, produces no output file and leaves an existing `build/product-changelog.md` unchanged. Verifies the render half of the fail-closed criterion, per § 3's failure path.

**Done when:** `python3 tools/changelog.py render --output build/product-changelog.md` exits zero, the digest comparison passes, `git status --porcelain` is empty afterwards, and both refusal fixtures leave the output absent or unchanged.

### T6: A fragment for an unreleased version aggregates under `[Unreleased]` and moves once

**Depends on:** T4

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- A fragment for a package version that is not yet released appears in the `[Unreleased]` region of the complete view and produces no `/now/` group. Verifies the first `[Unreleased]` criterion.
- After that version is released, the same fragment's Highlights appear exactly once in a released group of the `/now/` payload, carrying the `id` the fragment was created with. Verifies the second.
- The transition changes no byte of any other fragment's record in either the complete view or the payload, asserted by comparing every other record before and after. Verifies the third.
- no stub (implementation-discovered) — the seam is the released-ness predicate, and which of the three candidate resolutions it rests on is unresolved. Discovery predicate: Platform Core maintainers answer the spec Assumption naming § 4 Published identity permanence. Constraint: the resolution must not write `packages`, `date` or `id` into a merged fragment unless that § 4 row is amended first. Required outcome: the three tests above. Verification mode: TDD once the predicate is fixed.

**Approach:**
- Stop and surface before implementing. The three candidates — derive from released pack version, carry a clearable envelope marker, or defer creation to release time — differ in what they write to a merged fragment, and the spec's Ask-first rule makes this a human decision rather than an implementer's default.

**Done when:** the resolution is recorded in the verification ledger with its decider, and the three tests above are green.

### T7: The site changelog and `/now/` are rendered from one model pass

**Depends on:** T4, T5

**Touches:** tools/build-site.py, tools/test_build_site_routing.py

**Tests:**
- The `/now/` payload assembled with zero fragments is byte-identical to the payload `tools/build-site.py` emits from `docs/product/changelog.md` alone, whose sha256 is `72305605f91380cc591c488a956695f8d2856770411f514a7d12a8705d538b40` at base `93bf9cc9e`. Verifies the parity criterion, per § 7 Historical compatibility.
- No anchor present in the zero-fragment payload is absent or changed in a payload assembled with fragments present. Verifies the historical-anchor criterion.
- The payload stays at `schemaVersion` 1 and validates against the existing guards in `web/src/pages/now/index.astro`, `web/src/pages/now/page/[page].astro`, `web/src/pages/now/archive/index.astro`, `web/src/pages/now/[release].astro`, `web/src/pages/now/feed.xml.ts` and `web/src/components/now/NowHighlights.astro`, with none of those six files edited. Verifies the schema-version criterion, per § 4 Projection schema version.
- Every `/now/` anchor resolves to an element of that id in the emitted changelog page. Verifies the second half of the emitted-anchor criterion.
- Each released fragment yields one distinct `/now/` group carrying that fragment's own `anchor` and only its own Highlights, exercised by a fixture of two same-date fragments whose bullets a collapsing assembler would merge. Verifies the atomic-grouping criterion, per § 4 Atomic Highlights.
- One build pass produces the site changelog copy and the `/now/` payload from a single parse, asserted by instrumenting the parse count.
- A successful build prints the fragment count, the release count and the Highlights count. Verifies the build-counts criterion, per § 6; T7 owns this output because the production build is where it is emitted.
- A fragment set containing one file-safety refusal, and separately one schema refusal, publishes no view and leaves every previously generated view unchanged. Verifies the build half of the fail-closed criterion, per § 3's failure path.
- no stub (goal-based)

**Approach:**
- Known limit inherited from the assembly spike: the zero-fragment arm builds its historical half by calling the shipping projector, so it shows that merge, re-sort and re-serialization change nothing rather than independently re-deriving the payload. Record that limit beside the figure rather than reporting the byte match as a stronger claim than it is.

**Done when:** the byte comparison against the recorded sha256 passes, the six consumer files are unmodified in the diff, the parse-count assertion shows one parse, the build prints the three counts, and both refusal fixtures publish nothing.

### T8: The historical baseline is frozen and a later edit to it is refused

**Depends on:** T5

**Touches:** docs/product/changelog.md, tools/changelog.py, tools/test_changelog.py

**Tests:**
- `docs/product/changelog.md` carries a migration notice naming the public `/changelog/` view and the `python3 tools/changelog.py render --output build/product-changelog.md` command. Verifies the migration-notice criterion.
- The diff to `docs/product/changelog.md` contains that notice and nothing else: the historical sections' digest is unchanged. Verifies the only-change half of the same criterion.
- A change that edits a historical release section or heading is refused by a gate naming the edited heading. Verifies the freeze-gate criterion, per § 4 Immutable historical baseline.
- A change that edits only the migration notice is accepted, so the gate is scoped to release sections rather than to the file.
- The edited-heading fixture is refused through the boundary that actually invokes the gate, not only by calling the checker directly. Verifies that the freeze is enforced rather than merely implemented.
- no stub (implementation-discovered) — the seam is the gate's invoking boundary. Discovery predicate: which surface owns the invocation, among the validation job the spec's Operations row names, `.github/workflows/pages.yml`, and a Makefile target. Constraint: it must run on a pull request that edits `docs/product/changelog.md`, and adding a `build-check.yml` step obliges a `STEP_DISPOSITION` entry per `tools/AGENTS.md`. Required outcome: the two fixtures above, exercised through that boundary. Verification mode: goal-based once the boundary is fixed.

**Done when:** the digest of the historical sections before and after the notice is identical, the invoking boundary is named in the verification ledger, and the gate refuses the edited-heading fixture while accepting the notice-only fixture through that boundary.

### T9: The monolith counterfactual for historical anchors is measured

**Depends on:** T8

**Touches:** tools/measure-changelog-anchor-drift.py

**Tests:**
- Prepending the same fragment set into `docs/product/changelog.md` as release sections, then re-slugging, records how many historical anchors move through the slugger's duplicate-suffix renumbering; the figure is recorded whatever it is. Verifies the monolith-counterfactual criterion — this is the arm the assembly spike named as the one that can fail and did not run.
- The fragment path's figure for the same set is recorded beside it, so the two are read together rather than the counterfactual standing alone.
- Control arm: a deliberately constructed pair of headings that must collide under the slugger's duplicate-suffix renumbering is run through the same prepend-and-re-slug harness, and the harness must report that anchor as moved before either real figure is recorded. A harness that reports zero on this case is broken, and the run fails rather than recording. Verifies that a zero from the real corpus is a measurement rather than a silent instrument failure — the seam T10's classifier self-check already establishes.
- The script names its base commit and leaves `git status --porcelain` empty.
- no stub (goal-based)

**Approach:**
- Build the monolith arm as detached commits over a named base, never as edits to the working tree, so the measurement cannot disturb a worktree another session may be sharing. This follows `tools/measure-changelog-fragment-merges.py`'s construction.

**Done when:** `python3 tools/measure-changelog-anchor-drift.py` reports its control case as moved, then prints both arms' moved-anchor counts, names its base commit, exits zero, and leaves `git status` clean. A control case reporting zero exits non-zero and records nothing.

### T10: Fragment branches merge clean where monolith branches do not

**Depends on:** T2

**Touches:** tools/measure-changelog-fragment-merges.py

**Tests:**
- For 20 synthetic branches that each add one `docs/product/changelog.d/<uuid>.md` created by the delivered `new` command, 0 of the 190 unordered pairs are classified as conflicting on a changelog path, and 0 pairs exit non-zero for any other reason. Verifies the merge-independence criterion, per § 7 Mergeability; measured as 0 of 190 at base `443f141f2`.
- The monolith control arm of 20 branches each prepending one release section reports a conflicting-pair figure greater than zero and an error figure of 0. Verifies the control criterion; measured as 190 of 190 at base `443f141f2`.
- The classifier is exercised against one hand-built conflicting pair and one clean pair and must bucket each correctly before either figure is recorded.
- no stub (goal-based)

**Approach:**
- Re-point the existing script at the delivered `new` command rather than at a synthetic fragment writer. The spike's figure was taken against a prototype; this run is what shows the shipped creation path produces independently mergeable records.

**Done when:** the script prints both arms' conflicting-pair and error counts out of 190, both classifier self-checks, and its base commit, and leaves `git status` clean.

### T11: Release validation and the documentation build recognize fragments

**Depends on:** T1, T2, T4

**Touches:** tools/check-core-release.py, tools/repo/check_release_impact.py, .github/workflows/pages.yml, tools/test-pages-workflow.py, tools/test_check_core_release.py, tools/test_check_release_impact.py

**Tests:**
- `tools/check-core-release.py` matches a core release to a changed fragment rather than to the topmost heading of `docs/product/changelog.md`, and refuses a release whose fragment carries no Highlights bullet. Verifies the core-release criterion.
- `tools/repo/check_release_impact.py` treats an added or changed path under `docs/product/changelog.d/` as satisfying its changelog requirement. Verifies the first half of the release-impact criterion.
- The same script still refuses a release-impacting change that carries no changelog evidence and no version bump. Verifies the second half — the existing refusal must survive the widening.
- `.github/workflows/pages.yml` triggers on a change under `docs/product/changelog.d/` and on a change to `docs/product/changelog.md`, and `REQUIRED_PATHS` in `tools/test-pages-workflow.py` pins both over the `push` and `pull_request` triggers, so removing either trigger fails. Verifies the workflow-trigger criterion; `pages.yml` already carries the `changelog.md` trigger today, and pinning it in the allowlist is what stops it being dropped.
- no stub (goal-based)

**Approach:**
- `tools/check-core-release.py` is delivery-time only: no workflow or Makefile target invokes it, so its change is verified by direct invocation, not by a gate run. `tools/repo/check_release_impact.py` runs at `.github/workflows/catalogue-tooling-ci-gates.yml:561`, so its change is verified there.
- Both scripts consume the T4 model rather than reparsing a changelog, which is why this task waits on T4 and not only on the validator — ADR-0123 D7 requires it and `tools/check-core-release.py` currently reads the topmost heading of `docs/product/changelog.md` directly.
- `tools/test-pages-workflow.py` is a hyphenated standalone entry point: `tools/AGENTS.md` records that a directory sweep collects none of them, so run it by name rather than reading a green `pytest tools/` as covering it.

**Done when:** both scripts pass their fixtures by direct invocation, the widened release-impact check still refuses its negative fixture, and `python3 tools/test-pages-workflow.py` is green with both changelog paths in `REQUIRED_PATHS`.

### T12: No guidance surface still tells an author to edit `changelog.md`

**Depends on:** T2, T5, T8

**Touches:** docs/product/AGENTS.md, packs/AGENTS.local.md, docs/product/changelog.md, docs/product/changelog-fragment-template.md

**Tests:**
- A repository-wide search for instructions to edit `docs/product/changelog.md` returns only the frozen-history migration notice. Verifies the maintainer-procedure closeout condition.
- `docs/product/AGENTS.md` states the fragment gesture — run `new`, edit the created file, stop — and keeps its existing statement that the `/now/` JSON is generated and gitignored.
- `packs/AGENTS.local.md`'s pack release pipeline names the fragment path where it currently names the changelog.
- The tracked template lives at `docs/product/changelog-fragment-template.md`, outside `docs/product/changelog.d/`, and a build with the template present succeeds. Verifies that the template is not in the validated scan set: the reader refuses any stem under `changelog.d/` that is not a UUIDv4 matching its envelope `id`, so a tracked template inside that directory would fail every build.
- The template validates as a fragment once its placeholders are filled and it is written to a `changelog.d/<uuid>.md` path, and is refused while they are not.
- Each guidance surface points at the template's path outside the scanned directory.
- no stub (goal-based)

**Done when:** the search returns only the migration notice, a build with the template tracked at its new path succeeds, and the template's filled and unfilled forms are accepted and refused respectively.

### T13: Three arms on a quiet machine price the fragment layout against a monolith at equal scale

**Depends on:** T7

**Touches:** docs/product/research/changelog-fragment-build-cost.md

**Tests:**
- Three interleaved arms, each discarding one warm-up run, record the median `make site-build` duration for today's corpus, for a monolith carrying ten times the released entries, and for that same canonical record set laid out as fragments. Verifies the three-arm criterion.
- The two large arms are generated from one canonical record set and differ only in physical layout — identical entries, bytes, Highlights, dates and package fan-out — asserted by comparing the two arms' record sets before the runs. Verifies that the recorded difference cannot be content.
- The recorded ratio is the fragment median minus the monolith median over the monolith median, judged against § 7 Build performance, which owns the bar. The monolith-versus-today difference is recorded separately as release-growth cost this design does not own. Verifies the ratio criterion.
- Published page count is recorded per arm, and the fragment and monolith arms at equal release count emit the same number. Verifies the page-count criterion, per § 7 Published page count.
- The two Astro phases are timed in isolation rather than in sequence. Verifies the attributability criterion — the assembly spike could not separate them and said so.
- Each arm's retained-duration spread is recorded and the instrument-validity stop predicate is applied; a run failing it is reported as inconclusive rather than as a ratio. Verifies the instrument-validity criterion. The predicate itself is the `Ask first` decision the spec Assumptions name, and no ratio is accepted before it is recorded.
- The report names the machine, the base commit, the interleaved run order, the three discarded warm-ups, every retained duration, and a survive or kill line against each of the two § 7 rows.
- no stub (goal-based)

**Approach:**
- Run in a disposable clone, not a worktree of this repository: a worktree shares the parent's git directory and its `make site-build` would clean this tree's `build/`. Delete the clone before recording the figure.
- Stop and surface if the fragment-versus-monolith ratio is at or above the § 7 bar. Whether that blocks delivery is a Platform Core maintainer decision, not an implementer's.
- Obtain the instrument-validity stop predicate before the run, not after reading the numbers. A dispersion bound chosen once the spread is known is fitted to the result rather than to the instrument.

**Done when:** the report exists at its destination carrying both ratios, the per-arm page counts, the isolated phase timings, each arm's recorded spread against the stop predicate, and a verdict line per § 7 row; the disposable clone is deleted and its deletion recorded.

### T14: No touched `tools/` entry point imports a third party, and the build runs offline

**Depends on:** T3, T6, T7, T8, T9, T10, T11

**Touches:** tools/test_changelog.py

**Tests:**
- A static dependency check over every `tools/` path the tasks above pin in their `Touches` fields reports no third-party import **added** by this delivery: every import in a file this delivery creates must be standard library, and a file that already exists must gain no third-party import it did not carry at the merge base. Pre-existing third-party imports in an existing suite are out of scope — `tools/test_check_core_release.py` imports `pytest` today, and `tools/AGENTS.md` binds only new `tools/` additions to pure stdlib. That closed set, read off those fields, is `tools/changelog.py`, `tools/build-site.py`, `tools/check-core-release.py`, `tools/repo/check_release_impact.py`, `tools/measure-changelog-fragment-merges.py`, `tools/measure-changelog-anchor-drift.py`, `tools/test-pages-workflow.py`, `tools/test_build_site_routing.py`, `tools/test_check_core_release.py`, `tools/test_check_release_impact.py` and `tools/test_changelog.py` — every touched `tools/` file, test suites included, because `tools/AGENTS.md` binds a new `tools/` addition to pure stdlib without distinguishing a suite from an entry point. Verifies the static half of the dependency criterion, per § 7 Dependency and privacy posture.
- An end-to-end build of every view completes with no network access available. Verifies the offline half of the same criterion, which § 7 pairs with the static check.
- no stub (goal-based)

**Approach:**
- Give the static check a named home rather than leaving it asserted in design prose. § 7 Dependency and privacy posture names two verifications and the Durable Outputs closeout requires a named passing test per § 7 row, so an unowned half cannot be discharged.
- Take the set from the pinned `Touches` fields rather than from a directory sweep: `tools/AGENTS.md` records that the pure-stdlib rule has no lint enforcing it, so the scope has to come from the plan. A sweep would also miss `tools/test-pages-workflow.py`, which that same file records as a hyphenated standalone entry point no directory collection reaches.
- Depend on every task that creates or edits a file in the set, not only on the two consumer tasks. T9 and T10 create the two measurement scripts and T3, T6 and T8 each still edit `tools/changelog.py`, so a T14 that ran after T7 and T11 alone would scan an incomplete set and report clean.

**Done when:** the static check reports, across every pinned path, that no file this delivery creates imports a third party and no existing file gained one against its merge-base imports; and the offline build completes with no network access.

## Rollout

- **Delivery:** big bang at cutover, in one change. § 8 requires the fragment contract, the assembler, every consumer and the cutover gate to ship together, because splitting them splits authority over the same failure boundary. There is no flag and no steady-state dual write.
- **Infrastructure:** none. No service, database, queue, scheduled writer, model endpoint or cross-repository process is added.
- **External-system integration:** none.
- **Deployment sequencing:** within the change, the migration notice and the freeze gate (T8) land after the renderer (T5) exists, because the gate compares against generated output. Consumers (T7, T11) switch in the same commit as the freeze, so no window exists in which a consumer reads a file that is already frozen against a model that does not yet feed it.
- **Rollback:** ordered and atomic, per § 5. Keep every fragment reader active, render each post-cutover fragment into a candidate aggregate, prove complete-changelog and `/now/` parity, then commit the source and consumer switch together. A partial rollback therefore leaves the fragment path serving all published entries.

## Risks

- **T6 stalls the delivery.** The `[Unreleased]` resolution is a human decision that may require an architecture amendment before any code is written, and T7 through T13 do not depend on it. If the decision is slow, the rest of the graph still completes and T6 is the last task in — but the spec's acceptance criteria are not satisfied until it lands, so this cannot be finished around.
- **The quiet machine is not quiet.** The assembly spike's control arm varied from 22.92s to 75.41s on identical input, which is why its figure supports no uncertainty bound. A T13 run with comparable dispersion produces another unusable number. Record the dispersion alongside the medians and treat a wide spread as a failed instrument rather than as a result.
- **Isolating the Astro phases changes what is measured.** § 7 Build performance states its bar against `make site-build`, and timing the phases separately is not the same invocation. Record the whole-build figure as the one the bar reads and the isolated phase figures as the attribution, rather than substituting one for the other.
- **A consumer guard is edited to make the payload validate.** The schema-version criterion is satisfied by leaving all six files alone; a guard edited to accommodate a payload shape converts a caught regression into a shipped one. Assert the six files are absent from the diff, not just that the build passes.
- **The prototype-to-production gap in T10.** The spike's 0-of-190 was measured against a prototype fragment writer. Re-pointing the script at the delivered `new` command is what makes the figure a statement about the shipped path; a run left pointed at the old writer would report the same number and mean less.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-09-23: spec approved by eugenelim
- 2026-09-23: plan approved by eugenelim
