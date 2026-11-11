# Plan: Per-update product changelog sources and generated views

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
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
shared failure boundary. T13 prices the integrated build, and T15 removes the
aggregate-only duplicate projection before producing the first valid ratio:
+18.69%, a kill against the under-10% bar. T16's pre-edit profile then locates
7.55 seconds of quadratic released-inventory re-validation and normalizes that
inventory once per projection. Two post-change runs were inconclusive on a
loaded machine, so T16 admits one final run only after a predeclared sustained
readiness gate. Pass 5 was valid at +12.12%, still a kill. Attribution spikes
put the whole remaining gap in the changelog projection: about 3 s from
reloading the file-safety helper per fragment, and the rest scaling with the
loose-fragment count. T16 now loads the helper once. T17 adds ADR-0143's
monthly bundles, and T18 remeasures at the bundle policy's worst admitted
state. T14 closes the dependency-posture half of § 7 only after every touched
entry point and build route is final.

The riskiest part is T6. Its design question is open in the spec's Assumptions
and the answer may oblige an architecture amendment rather than code, so it
carries an explicit stop rather than a default. The second riskiest is T13: the
three-arm build-cost run has to be genuinely wired in and genuinely quiet, and
the assembly spike's own instrument failed on the second count.

### Amendment assumptions and disposition for T16

- **Expected files:** `tools/changelog.py`, `tools/test_changelog.py`, and the
  existing build-cost report. The pre-edit profile names
  `is_fragment_released` and its callers as the production owner.
- **Done proof:** the amended red turns green, normalization and membership call
  counts become linear, output bytes remain fixed, focused refusal suites pass,
  and one readiness-gated three-arm pass records a valid fragment-overhead
  verdict. Pass 5 recorded that verdict as a valid +12.12% `KILL`, which is
  T16's closing measurement rather than a failed gate. T16 then closes when
  AC-B1 is green. The strictly-below-10% requirement lives only in T18.
- **Not changing:** the blessed file-safety helper, fragment schema, identity
  enforcement, build orchestration, pass-4 corpus, validity rule, or cost bar.
- **Declined:** caching parsed fragments or retaining file bytes. Content
  caching adds invalidation and trust-boundary work the outcome does not need.
  Loading `_file_safety` once per projection was also declined at first,
  because normalization once per projection looked sufficient. Pass 5 showed it
  was not, so T16 now adopts AC-B1, which passes one helper handle through a
  projection and keeps no state between projections.
- **Tail:** under 2,000 reviewable behavior/test lines; expected shape is DEEP
  but small because one projection-lifetime inventory invariant controls the
  change.
- **Resolve-vs-surface record:** pass 4 is preserved as inconclusive twice. Its
  unaccepted 18.41% and 14.66% ratios do not replace pass 3's valid 18.69%
  `KILL`. The owner authorized one pass 5 after the sustained readiness gate;
  there is no second pass-5 attempt if the instrument still fails.

## Constraints

- ADR-0123 is Accepted. D1–D7 are implemented here, not revisited. A delivery
  that cannot satisfy a D-decision or a Confirmation signal opens a superseding
  ADR rather than editing the accepted one.
- ADR-0143, numbered ADR-0138 when accepted on 2026-10-04, narrows ADR-0123 D2,
  D4 and D6 for released-record storage, and T17 and T18 implement it. It is
  reopened to Proposed only for D9's change to a 500 ceiling and a 375 warning,
  which T19 implements. Platform Core maintainers own its acceptance.
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
| Current architecture — `docs/architecture/changelog-fragment-source.md` | T0–T18 | A named passing test per § 4 and § 7 row | Every row's Verification column names a test that exists and passes; Platform Core maintainers resolve the delta's `Status` |
| Decision rationale — ADR-0123 | T4, T5, T8, T10 | A named passing test per Confirmation signal | All five signals covered; an unsatisfiable signal opens a superseding ADR |
| Decision rationale, released-record storage — `docs/adr/0143-released-changelog-records-move-into-monthly-bundles.md` | T17, T18 | ADR-0143's five Confirmation signals: per-rule fixtures (T17), compaction and retraction round trips (T17), zero blob reads on an unchanged set (T17), the valid pass at the ceiling (T18), and the merge replay with parts on the base (T17) | Every Confirmation signal has a named passing test |
| Maintainer procedure — `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the `changelog.md` header, the fragment template | T12, T17 | The four edited surfaces | A repository search for instructions to edit `changelog.md` returns only the frozen-history notice |
| Interface compatibility — the six `/now/` payload and anchor consumers | T7 | The payload validating against the unedited consumer guards | No consumer guard edited; no historical anchor moved |
| Operations — `.github/workflows/pages.yml`, `Makefile` and the validation job | T7, T11, T15, T16, T17 | Path-trigger test plus one fixture per diagnostic class; T7's count output; T15's aggregate-versus-standalone orchestration check; T16's before/after profile and output-equivalence proof | Each diagnostic class has a fixture; the build reports fragment, release and Highlights counts; the aggregate build projects once; standalone package builds retain their hooks; optimized reads preserve every guarding control |
| Dependency and privacy posture — every `tools/` entry point this delivery touches | T14 | The static dependency check's output and the offline build | No third-party import is reported and the offline build completes |
| Reusable learning — `docs/product/research/changelog-fragment-build-cost.md` | T13, T15, T16, T18 | Every three-arm run's retained stdout plus T16's before/after profile | The report preserves each run and names the final run's machine, base commit, required ratios and verdict per ratio |

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

Metadata that reaches a heading or published identity has a closed grammar:
`packages.name` is `[A-Za-z0-9][A-Za-z0-9._-]*`, `packages.version` is
`[A-Za-z0-9][A-Za-z0-9._+-]*`, and `date` is a real ISO `YYYY-MM-DD` calendar
date. Those characters are safe in the established Markdown release-heading
shape. The renderer derives the slug from that validated heading and appends
the lowercase UUID material, so the anchor consumed as a DOM id, URL segment
and Atom identity is separately constrained to the validated slug-and-UUID
token rather than copied from arbitrary contributor text.

The body's admitted section names come from the established changelog section
set; the parser rejects an unknown or duplicate section and any release-level
heading, because a release-level heading inside a fragment would make the
renderer's own heading ambiguous.

Traces to: the fragment source and identity criteria, and the published anchor
criteria · contracts: none.
Owned by: T1, T2, T3.

### Interfaces & contracts

`tools/changelog.py` exposes five command surfaces — `new`, `validate`,
`render`, and under ADR-0143 `compact` and `retract` — and one importable model.
T17 adds `validate`, `compact` and `retract`. The model is what `tools/build-site.py`,
`tools/check-core-release.py` and `tools/repo/check_release_impact.py` consume;
none of them re-parses a fragment or reads a generated view.

Contract refusals use `FragmentValidationError`, a `ValueError` subclass whose
message names the fragment path, failed field or invariant, and expected
correction. This gives the T1 construction stub a stable public error surface
without pinning helper internals.

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
edit, merge-base or base-blob read failure, and unsafe path. A fragment that fails any of them fails the build before
any view is published; there is no partial render and no degraded mode, because
a published half-view is worse than a failed build for a documentation surface.

The immutability check resolves the merge base and changed-path status before
reading any base blob. Only a path classified as added may treat an absent base
blob as legitimate. A missing merge base, shallow-history failure, renamed or
modified path with no readable base blob, unexpected `git show` exit, or
malformed Git result is a fail-closed refusal, never evidence that an existing
fragment is new.

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
- `test_build_site_uses_shared_changelog_parser` (`AC1`), `stub: true`:

```python
# STUB: AC1 — build-site calls the parser owned by tools/changelog.py
def test_build_site_uses_shared_changelog_parser() -> None:
    owner = Path(build_site.parse_changelog_releases.__code__.co_filename)
    assert owner.name == "changelog.py"
```

  PLAN validation: syntax PASS; intended red PASS on 2026-09-29 because the callable is still owned by `tools/build-site.py`.

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
- One fixture per sink-safe metadata class — invalid package name, invalid package version, impossible date, and metadata containing whitespace, `/`, `]`, quotes, angle brackets or a control character — refused the same way. A valid prerelease/version token using `.`, `_`, `+` or `-` is accepted. Verifies AC2 at every heading and published-identity input.
- One fixture per body class — unknown section, duplicate section, release-level heading, absent `Highlights`, empty `Highlights` — refused the same way. Verifies the body criterion.
- A symlink, a directory entry and a FIFO under the fragment directory are each refused by path through the blessed confined-file helpers. Verifies the confined-reader criterion.
- A tree exceeding the helpers' entry, file-count or depth bound, and a fragment exceeding their per-file byte bound, are each refused fail-closed by path rather than enumerated or read. Verifies the reader-bounds criterion. The bound values come from the `Ask first` decision the spec Assumptions name, not from this task.
- `test_validate_fragment_refuses_mismatched_stem` (`AC3`), `stub: true`:

```python
# STUB: AC3 — a filename stem that differs from the envelope id is refused
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


_SCRIPT = Path(__file__).with_name("changelog.py")
_SPEC = importlib.util.spec_from_file_location("product_changelog", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
changelog = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = changelog
_SPEC.loader.exec_module(changelog)


def test_validate_fragment_refuses_mismatched_stem() -> None:
    with TemporaryDirectory() as temp_dir:
        fragment = Path(temp_dir) / "11111111-1111-4111-8111-111111111111.md"
        fragment.write_text(
            """+++
schema = 1
id = "22222222-2222-4222-8222-222222222222"
anchor = "core300--2026-09-29-22222222222242228222222222222222"
date = 2026-09-29
[[packages]]
name = "core"
version = "3.0.0"
+++
## Highlights
- Adds per-update changelog sources.
""",
            encoding="utf-8",
        )

        try:
            changelog.validate_fragment(fragment)
        except changelog.FragmentValidationError as error:
            message = str(error)
        else:
            raise AssertionError("mismatched stem was accepted")

    assert str(fragment) in message
    assert "id" in message
    assert "filename stem must equal envelope id" in message
```

  PLAN validation: syntax PASS; intended red PASS on 2026-09-29 because `tools/changelog.py` does not yet exist.

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
- no stub (implementation-discovered) — the callable seam behind the `new` command is not fixed before implementation. Discovery predicate: identify the in-process function the delivered CLI calls to construct and write one fragment. Constraint: the test must invoke that same path, must prove the UUID and recomputed anchor contract, and must prove creation reads no sibling fragment. Required outcome: materialize a compilable TDD test that creates one fragment through that function and round-trips it through `validate_fragment` without refusal. Verification mode: TDD as soon as the callable seam exists.

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
- A path classified as Added may lack a merge-base blob and is accepted as new; a Modified or Renamed path whose merge-base blob cannot be read is refused. Verifies AC4's distinction between legitimate absence and an unreadable prior identity.
- A missing or shallow merge base, any unexpected failure from the Git query or base-blob read, and any malformed Git result are refused with the fragment path, failed prerequisite and expected correction named. Verifies AC4's complete fail-closed set and diagnostic contract.
- `test_validate_fragment_refuses_date_edit_after_commit` (`AC4`, `AC5`), `stub: true`:

```python
# STUB: AC4/AC5 — a committed fragment's date cannot be changed
import subprocess
from contextlib import chdir


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_validate_fragment_refuses_date_edit_after_commit(tmp_path: Path) -> None:
    fragment_id = "11111111-1111-4111-8111-111111111111"
    repo = tmp_path
    fragment_dir = repo / "docs/product/changelog.d"
    fragment_dir.mkdir(parents=True)
    fragment = fragment_dir / f"{fragment_id}.md"
    original = """+++
schema = 1
id = "11111111-1111-4111-8111-111111111111"
anchor = "core300--2026-09-28-11111111111141118111111111111111"
date = 2026-09-28
[[packages]]
name = "core"
version = "3.0.0"
+++
## Highlights
- Adds per-update changelog sources.
"""
    edited = original.replace("2026-09-28", "2026-09-29")
    fragment.write_text(original, encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", str(fragment.relative_to(repo)))
    _git(repo, "commit", "-m", "test: add changelog fragment")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    fragment.write_text(edited, encoding="utf-8")

    with chdir(repo):
        try:
            changelog.validate_fragment(fragment)
        except changelog.FragmentValidationError as error:
            message = str(error)
        else:
            raise AssertionError("committed fragment date edit was accepted")

    assert str(fragment) in message
    assert "date" in message
    assert "must not change after merge" in message
```

  PLAN validation: syntax PASS; intended red PASS on 2026-09-29 against a no-op validator that accepts the committed identity edit.

- no stub for the fail-closed Git error matrix (implementation-discovered) — the Git command/base-reader injection seam is not fixed before implementation. Discovery predicate: identify the smallest callable boundary that resolves the merge base, classifies the changed path and reads the base blob. Constraint: injected missing-base, shallow-history, rename/modify missing-blob, unexpected read failure and malformed-result cases must each refuse with the fragment path and expected correction, while a classified Added path with no base blob must pass. Required outcome: materialize that complete AC4 matrix without changing the approved public-stub bytes. Verification mode: TDD as soon as that internal boundary exists.

**Approach:**
- Read the base copy through `git show <base>:<path>`, not from a working-tree cache: the check has to see the merge base's bytes, and a cached copy is the failure mode where a second edit in the same branch passes.

**Done when:** the three identity-edit refusal fixtures and two acceptance fixtures are green; every AC4 missing-base, shallow-history, rename/modify missing-blob, unexpected-failure and malformed-result fixture refuses with the fragment path and expected correction; and the classified-Added absence fixture passes.

### T4: Assembly is identical under shuffled enumeration and differs without the sort

**Depends on:** T0, T1

**Touches:** tools/changelog.py, tools/test_changelog.py

**Tests:**
- Assembling the frozen baseline plus a fragment set across 5 shuffled directory enumerations produces 1 distinct output digest. Verifies the determinism criterion, per § 7 Determinism.
- The same 5 enumerations with the canonical sort removed produce at least 2 distinct digests. Verifies the mutation-arm criterion, without which the shuffle arm proves only that the enumeration never varied.
- Output order is `date` descending then `id` ascending, asserted over a fixture with two same-date fragments whose `id`s order oppositely to their enumeration.
- No output field derives from a clock or filesystem order: two assemblies of the same sources taken at different wall-clock times are byte-identical, and the shuffle arms above cover enumeration order.
- Git-history arm: the assembler runs against one source set in two checkouts whose commit history differs — different commit SHAs, authors and dates for byte-identical sources — and the two outputs are byte-identical. Verifies the Git-history clause of the determinism criterion, which the wall-clock arm holds fixed rather than exercising. This arm constrains the assembler only; T3's read-only merge-base reads sit in validation, which ADR-0123 D4 does not reach.
- no stub (implementation-discovered) — the canonical assembly callable and its source-collection boundary are not fixed before implementation. Discovery predicate: identify the callable that accepts the frozen baseline plus validated fragment records and returns the canonical serialized view. Constraint: the test must vary enumeration order at that boundary rather than pre-sort its input, and its mutation arm must remove or bypass only the canonical sort. Required outcome: materialize a compilable TDD test that hashes two shuffled assemblies and asserts equal digests. Verification mode: TDD as soon as the assembly seam exists.

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
- no stub (goal-based) — the observable is the complete output of `python3 tools/changelog.py render --output build/product-changelog.md`, not a settled internal callable. The named command and the recorded digest of the frozen historical span provide the executable proof, while the other fixtures above pin fragment fidelity and anchors.

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

### T15: The aggregate site build projects once and its valid three-arm rerun records the cost verdict

**Depends on:** T13

**Touches:** Makefile, tools/test_build_site_routing.py, docs/product/research/changelog-fragment-build-cost.md

**Tests:**
- The `site-build` recipe runs `site-sync` once, then invokes both package build scripts with npm lifecycle hooks disabled for those two aggregate invocations. A construction test pins both aggregate commands. Verifies that the two package `prebuild` hooks do not repeat the already-complete shared projection.
- `web/package.json` and `docs-site/package.json` retain their existing `prebuild` hooks, and the existing hook-coverage test remains green. Verifies that direct package builds still project their renderer inputs before building.
- The T13 three-arm protocol is repeated unchanged after the orchestration fix. Every arm must satisfy the precommitted retained-duration spread bound of 20%; otherwise the rerun is inconclusive and this task stops.
- On a valid rerun, `(fragment median - monolith median) / monolith median` is judged against the § 7 Build performance bar of 10%, and the equal-scale fragment and monolith arms emit the same published page count. A ratio at or above 10% stops delivery rather than being averaged with or substituted by an isolated-phase figure.
- no stub (goal-based)

**Approach:**
- Preserve the package-local safety net. The optimization is confined to `make site-build`, whose `site-sync` prerequisite has already generated the complete content and renderer inputs before either Astro build starts; standalone npm entry points keep their lifecycle hooks unchanged.
- Use npm's supported lifecycle-suppression option only on the two aggregate build invocations. Confirm that option against the installed npm contract before editing the recipe, then exercise the real target rather than relying only on the construction test.
- Append the rerun to the existing T13 report with its machine, base commit, interleaved order, warm-ups, retained durations, spreads, page counts and verdict. Keep the earlier inconclusive run intact as provenance.

**Done when:** the aggregate-versus-standalone orchestration checks pass; a real `make site-build` completes; and the appended three-arm rerun is instrument-valid, records equal published page counts, records its verdict against the under-10% bar, and deletes its disposable clone.

### T16: Normalize one released inventory and load the file-safety helper once per projection

**Depends on:** T15

**Touches:** tools/changelog.py, tools/test_changelog.py, docs/product/research/changelog-fragment-build-cost.md

**Tests:**
- The retained pre-edit profile records the equal-scale fragment projection at 13.58 seconds, including 7.55 seconds of released-inventory re-validation, 8,912 normalizations and 33,183,844 regex matches. It names `is_fragment_released` and its two projection callers as the production owner. The earlier loader-cache stub is removed because its locked hypothesis was refuted before production code changed.
- Each of `assemble_changelog` and `project_fragment_now_highlights` validates and normalizes its released-version inventory exactly once, whatever the fragment count. Direct `is_fragment_released(fragment, raw_inventory)` remains a validating boundary for independent callers. Within a projection, membership checks consume only the already-normalized inventory.
- `test_release_inventory_is_normalized_once_per_projection` (`AC-cost`), `stub: true`:

```python
def test_release_inventory_is_normalized_once_per_projection(
    tmp_path: Path, monkeypatch,
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            f"{index + 1:08d}-1111-4111-8111-111111111111",
            "2026-09-29",
            f"Highlight {index + 1}.",
        )
        for index in range(2)
    ]
    fragments = changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    inventory = {"core": {"3.0.0"}}
    calls = 0
    original = changelog._normalize_released_versions

    def counted(value):
        nonlocal calls
        calls += 1
        return original(value)

    monkeypatch.setattr(changelog, "_normalize_released_versions", counted)
    changelog.assemble_changelog(
        "# Changelog\n", fragments, released_versions=inventory
    )
    assert calls == 1

    calls = 0
    changelog.project_fragment_now_highlights(fragments, inventory)
    assert calls == 1
```

  Intended red: current assembly normalizes five times for two fragments and
  current `/now/` projection normalizes three times. The exact stub is validated
  in disposable scratch before EXECUTE and replaces, rather than coexists with,
  the refuted loader-cache stub.
- A call-count construction test proves each projection makes one release-membership decision per fragment, rather than assembly checking every fragment twice. The direct public helper still refuses malformed package names and versions before membership is read.
- The complete changelog and `/now/` payload produced from the profile corpus are byte-identical before and after the optimization. Every existing file-safety, byte-limit, schema, identity, release-transition and fail-closed fixture remains green.
- The unchanged T13 protocol was repeated with equal canonical record sets in its two large arms, as pass 5. Every arm passed the precommitted 20% spread bound and large-arm published page counts were equal. Its valid +12.12% ratio is recorded as T16's closing measurement, and the strictly-below-10% requirement moves to T18.
- `test_file_safety_helper_loads_once_per_projection` (`AC-B1`), `stub: true`. It asserts one helper load per projection, a fresh load on a second projection, and the 1,048,576-byte bound on every confined read:

```python
def test_file_safety_helper_loads_once_per_projection(
    tmp_path: Path, monkeypatch,
) -> None:
    fragment_dir = tmp_path / "docs/product/changelog.d"
    paths = [
        _assembly_fragment(
            fragment_dir,
            f"{index + 1:08d}-1111-4111-8111-111111111111",
            "2026-09-29",
            f"Highlight {index + 1}.",
        )
        for index in range(3)
    ]
    loads = 0
    bounds: list[int | None] = []
    original = changelog._file_safety

    def counted():
        nonlocal loads
        loads += 1
        module = original()
        real_read = module.read_confined_regular_file

        def read(directory, path, *, max_bytes=None):
            bounds.append(max_bytes)
            return real_read(directory, path, max_bytes=max_bytes)

        module.read_confined_regular_file = read
        return module

    monkeypatch.setattr(changelog, "_file_safety", counted)
    changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    assert loads == 1
    assert bounds == [changelog.MAX_FRAGMENT_BYTES] * 3

    changelog.collect_validated_fragments(
        fragment_dir, enumerator=lambda _directory: paths
    )
    assert loads == 2
```

  Intended red, earned in disposable scratch on 2026-10-04: `assert 4 == 1`, one load at the start plus one per fragment read for three fragments. T17 extends the bound assertion to part and retraction-list reads.
- Pass 4 is retained as two inconclusive executions: its `today` spreads were
  29.47% and 27.60% on a loaded machine. Pass 5 begins only after untimed setup
  and five consecutive one-minute samples with one-minute load `<= 10.0` and
  ten-spawn mean latency `<= 40 ms`, followed immediately by a 60-spawn mean
  confirmation `<= 40 ms`. The readiness samples and confirmation are recorded
  with timestamps. The gate admits exactly one complete pass-5 execution; an
  invalid pass 5 is final rather than grounds for another retry.
- Pass 5 runs only in a fresh disposable clone created under one resolved
  `/private/tmp/t16pass5.` path. The source worktree is read-only measurement
  input; the clone shares no Git directory or mutable build state with it and
  touches no production or shared external state. Setup creates no billable
  external resource. Cleanup is installed before setup and runs after success,
  failure, interruption or an unmet readiness gate. Before deletion, the
  resolved target must still be the exact created clone path and carry the
  `/private/tmp/t16pass5.` prefix; no glob, unresolved variable, parent path or
  bulk cleanup is admitted. The report records clone size, the exact deletion
  target, `test -e` false afterward and zero remaining paths with that prefix.

**Approach:**
- Preserve `is_fragment_released` as a validating public boundary. Add one private membership predicate over a normalized inventory; the public helper normalizes then delegates, while the two projection entry points normalize once and use the private predicate for every fragment.
- Partition pending and released fragments in one assembly pass so one fragment receives one membership decision there. `/now/` likewise performs one decision per fragment. The normalized dict-of-sets is local to one projection call and is not retained, mutated or shared across requests.
- Load `_file_safety` once per projection and pass that handle to every confined read, per AC-B1. Pass 5 showed the inventory fix alone left +12.12%, and the bundle attribution spikes measured a 3.07-second paired saving from loading the helper once. Keep no state between projections. Cache no fragment bytes, parsed records, Git state, paths or rendered output.
- Preserve the before/after profile and both pass-4 executions. Rebuild pass 5
  from pass 4's recorded canonical serialization, UUID namespace and derivation
  rule, and require the same normalized record-set SHA-256
  `9338c9a0d45c9f350bf56d9589b07c3e607ff7f0d86a8c4cab532cbe7556c99b`,
  monolith manifest SHA-256
  `571d2a8a96be7125227a1a7a206a1ec75495972036dd7262070e0accc1d785f2`,
  fragment manifest SHA-256
  `bb8b19397e022d76f7cfcd573bf788cbb6534260ab495c136571fb96cf30777d`,
  and established record/group/highlight counts before timing. Add no permanent
  generator tool. Append pass 5 as a self-contained report section and compare
  only its equal-record arms for the verdict.
- Capture a bounded source-worktree manifest before the clone is created and
  compare it after teardown. Only the report and verification-ledger receipt
  may change in the source worktree; HEAD, `git log -1`, Git metadata and every
  other path must remain byte-identical. A mismatch stops handoff rather than
  being repaired with reset, checkout, clean or restore.
- At the pass-3 medians, the fragment arm had to fall below 84.755 seconds if the monolith median stayed 77.05 seconds. The profile attributes a median 8.40-second paired saving to inventory normalization, above the 6.695-second planning gap; the actual verdict still uses the new paired medians and unchanged validity rule.

**Done when:** the amended red turns green; normalization and membership call
counts are linear; output-equivalence and complete focused changelog suites
pass; the readiness gate admitted exactly one pass 5, whose valid +12.12%
`KILL` is T16's recorded measurement; its disposable clone is deleted; and
AC-B1 is green, with one helper load per projection and every confined read
still at the 1,048,576-byte bound. The remeasure moved to T18.

### T17: Released records move into monthly bundles, and a bundled record can only be retracted

**Depends on:** T16

**Touches:** tools/changelog.py, tools/test_changelog.py, tools/build-site.py, tools/test_build_site_routing.py, tools/check-core-release.py, tools/test_check_core_release.py, tools/repo/check_release_impact.py, tools/test_check_release_impact.py, tools/measure-changelog-fragment-merges.py, .github/workflows/pages.yml, tools/test-pages-workflow.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py, docs/product/AGENTS.md, packs/AGENTS.local.md, docs/product/changelog-retractions.toml

**Tests:**
- TDD, one fixture per refusal class: AC-B2 container, AC-B2a bundle-ready fragments, AC-B3 part names, AC-B3a read confinement, AC-B4 cross-form identity, AC-B4a retraction, AC-B5 raw bytes, AC-B6 compaction and AC-B7 bounds.
- AC-B6's inventory parity: `compact` and the site build classify the same fragments as released on one fixture repository.
- AC-B8: every named consumer reads through the one reader without substitute seams. The build warns when more than 750 released fragments are loose, refuses when more than 1,000 are loose, and warns when more than 250 are pending. Fixtures sit at exactly 750, 1,000 and 250, which pass, and one above each, which does not.
- AC-B8a: the release-impact refusal fixtures, plus a passing version-bump-with-deletions fixture.
- AC-B4's ride-along fixture: a part-adding change that also adds a new fragment passes. AC-B4b and AC-B8b: pinned text checks over `docs/product/AGENTS.md` and `packs/AGENTS.local.md`.
- Goal-based integration: compaction and retraction round trips leave every other record's output byte-identical, and AC-B9's merge replays hold with bundle parts on the base.
- AC-B10 and AC-B11: `pages.yml` triggers on both new paths, pinned in `REQUIRED_PATHS`; `build-check.yml` gate-main runs `python3 tools/changelog.py validate` on every pull request, with its `STEP_DISPOSITION` entry and `tools/test-lint-ci-parity.py` green.
- no stub (TDD fixtures are authored with the code)

**Approach:**
- Keep the container parser, the cross-form identity comparison, the part writer and the `validate`, `compact` and `retract` commands in `tools/changelog.py`. Every other consumer only calls the one reader.
- Move the released-version inventory derivation from `tools/build-site.py` into `tools/changelog.py`: pack discovery of names and versions, plus the historical inventory. `tools/build-site.py` imports it, so `compact` and the build share one inventory and AC1's import direction holds.
- Expose the part writer as one function over an explicit record set. `compact` passes it a month's released fragments, and T18 passes it every record except the newest 1,000.
- Decide "changed" by object id computed over loaded bytes, in the repository's object format, and read merge-base blobs as size-checked raw bytes.
- `compact` plans and validates in memory, writes parts with exclusive create, re-reads them, and only then deletes the fragments it bundled. `retract` rewrites one part and appends one list entry, each atomically.
- Add the compaction step to the release checklist in `packs/AGENTS.local.md` and the gesture to `docs/product/AGENTS.md`.

**Done when:** every AC-B2 to AC-B11 check passes, including AC-B2a, AC-B3a, AC-B4a, AC-B4b, AC-B8a and AC-B8b; the existing fragment suites stay green; and a month compacted twice, an interrupted compaction rerun, and a retraction each leave every other record's complete-view and `/now/` bytes unchanged.

### T18: One readiness-gated pass measures the bundle policy's worst admitted state

**Depends on:** T17

**Touches:** docs/product/research/changelog-fragment-build-cost.md, docs/specs/product-changelog-fragments/notes/verification-ledger.md

**Tests:**
- One pass under pass 5's protocol and readiness gate, unchanged, with exactly one admitted run and no retry.
- no stub (goal-based, end-to-end)

**Approach:**
- Run the guarding suites first, in the clone, against the repository's current `docs/product/changelog.md`: focused T16 and AC-B1 checks, `tools/test_changelog.py`, `tools/test_build_site_routing.py`, Ruff and `py_compile`. Their digest pins describe the current file, so they run before any restore.
- Then restore pass 4's baseline `docs/product/changelog.md` bytes and require SHA-256 `ff02ab9146baff843c9f7483b589d5b521d09f585327f13b459371349d8ef084` (648,990 bytes). The source is `git show ac54cc871b3078edfe6b13526827767e9e4ebf1e:docs/product/changelog.md` with the current migration notice applied in its place. A digest mismatch stops before timing. The repository's frozen history has grown since pass 4, and the corpus is derived from that baseline.
- Rebuild pass 4's corpus byte for byte under pass 5's exact-value gate, then run pass 5's output-equivalence proof against the restored baseline.
- Then store it with T17's part writer: every record except the newest 1,000 in canonical order goes into bundle parts, and the newest 1,000 stay loose. That is the ceiling's worst admitted state for released records. The arm holds no pending fragments.
- Commit the corpus and repoint `origin/main`, as in pass 5.
- Spike 4 predicts about 2.5%, or 3–4% on a whole-build basis. T18 confirms the ceiling, not whether bundles were necessary.

**Done when:** before timing, the large fragment arm reads back through the one reader as exactly 1,000 released loose fragments, 0 pending fragments and 1,970 generated records in bundle parts, beside the 330 historical records, with a record set equal to the monolith arm's; every arm passes the 20% spread rule; the fragment-layout ratio is strictly below 10%; the large arms' page counts are equal; the run is appended to the build-cost report; and its disposable clone is deleted. An invalid run or a ratio at or above 10% stops delivery without T14. A ratio at or above 5% also triggers ADR-0138's Revisit clause.

### T19: Lower the loose-fragment ceiling to 500 and carry ADR-0143's final number

**Depends on:** T18

**Touches:** tools/changelog.py, tools/test_changelog.py, tools/test_build_site_routing.py

**Tests:**
- AC-B8: the production constants are `LOOSE_RELEASED_WARN_THRESHOLD == 375` and `LOOSE_RELEASED_REFUSE_THRESHOLD == 500`, asserted in tools/test_changelog.py and through tools/build-site.py in tools/test_build_site_routing.py. In `test_acb8_threshold_behavior`, the small monkeypatched proxy values (`SMALL_WARN`, `SMALL_REFUSE` and `SMALL_PENDING`) stay unchanged, the production-constant assertions change from 750 and 1,000 to 375 and 500, and the analogue comments name 375 and 500.
- The existing suites stay green, including every AC-B4 to AC-B11 fixture and the T14 dependency and offline checks.
- No `ADR-0138` citation remains in tools/changelog.py, tools/test_changelog.py or tools/test_build_site_routing.py; each names ADR-0143.
- no stub (goal-based: constant change and citation rename)

**Approach:**
- T18 measured +7.22% with 1,000 released fragments loose, at or above ADR-0143's 5% Revisit line, and the owner chose to lower the ceiling to 500 with the warning at 375. T18's figure bounds the new ceiling from above, so T18 is not rerun.
- ADR-0138 was renumbered to ADR-0143, because ADR numbers 0138–0142 were taken on other branches before this delivery merged. The sealed T17 and T18 sections keep the number they were written with.
- Change only the two constants, their assertions and the citations. The comparison code is unchanged.

**Done when:** the constants are 375 and 500 with their assertions green, the four suites and the T14 checks pass, and no `ADR-0138` citation remains in the touched files.

### T14: No touched `tools/` entry point imports a third party, and the build runs offline

**Depends on:** T3, T6, T7, T8, T9, T10, T11, T15, T16, T17, T18, T19

**Touches:** tools/test_changelog.py

**Tests:**
- A static dependency check over every `tools/` path the tasks above pin in their `Touches` fields reports no third-party import **added** by this delivery: every import in a file this delivery creates must be standard library, and a file that already exists must gain no third-party import it did not carry at the merge base. Pre-existing third-party imports in an existing suite are out of scope — `tools/test_check_core_release.py` imports `pytest` today, and `tools/AGENTS.md` binds only new `tools/` additions to pure stdlib. That closed set, read off those fields, is `tools/changelog.py`, `tools/build-site.py`, `tools/check-core-release.py`, `tools/repo/check_release_impact.py`, `tools/measure-changelog-fragment-merges.py`, `tools/measure-changelog-anchor-drift.py`, `tools/test-pages-workflow.py`, `tools/test_build_site_routing.py`, `tools/test_check_core_release.py`, `tools/test_check_release_impact.py`, `tools/lint-ci-parity.py` and `tools/test_changelog.py` — every touched `tools/` file, test suites included, because `tools/AGENTS.md` binds a new `tools/` addition to pure stdlib without distinguishing a suite from an entry point. Verifies the static half of the dependency criterion, per § 7 Dependency and privacy posture.
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
- **Skipping package lifecycle hooks hides a missing aggregate prerequisite.** T15 may suppress `prebuild` only after `site-sync`, and the construction test must keep the standalone hooks pinned. A package script change that adds a different prerequisite must make the aggregate target provide it before lifecycle suppression remains valid.
- **A faster release predicate weakens validation.** T16 keeps the public helper
  validating raw inventories and normalizes at each projection boundary. A
  caller cannot mark an arbitrary dict as trusted, retain it across calls, or
  skip malformed-name/version refusals. Output-equivalence and invalid-inventory
  fixtures pin that line.
- **The final corpus is internally valid but not pass-3 identical.** The old
  generator was not retained, and its normalization serialization and UUID
  namespace cannot be recovered. Pass 4 recorded enough identity to reproduce
  its replacement corpus; pass 5 must reproduce that exact corpus and decides
  the bar only from its own equal-record large arms. Neither pass makes a direct
  median comparison to pass 3.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-09-23: spec approved by eugenelim
- 2026-09-23: plan approved by eugenelim
- 2026-09-29: spec and plan returned to drafting to address sustained pre-execution review findings.
- 2026-09-29: amended spec approved by eugenelim.
- 2026-09-29: amended plan approved by eugenelim.
- 2026-09-30: returned to drafting after the first valid equal-scale comparison reported 49.5% fragment overhead; the owner kept the § 7 bar as a delivery blocker and authorized aggregate-build optimization plus a repeat measurement.
- 2026-09-30: performance amendment spec approved by eugenelim.
- 2026-09-30: performance amendment plan approved by eugenelim.
- 2026-09-30: returned to drafting after the first valid rerun measured 18.69% fragment overhead; the owner kept the under-10% bar and authorized profiling plus a reader-hot-path optimization.
- 2026-09-30: fragment-reader optimization amendment spec approved by eugenelim.
- 2026-09-30: fragment-reader optimization amendment plan approved by eugenelim.
- 2026-09-30: returned to drafting after the pre-edit profile refuted helper loading as the dominant cost; the owner authorized the measured `is_fragment_released` inventory-normalization owner instead.
- 2026-09-30: released-inventory normalization amendment spec approved by eugenelim.
- 2026-09-30: released-inventory normalization amendment plan approved by eugenelim.
- 2026-10-02: returned to drafting after both pass-4 executions were inconclusive on the loaded machine; the owner authorized exactly one pass 5 after a sustained quiet-machine readiness gate.
- 2026-10-02: quiet-machine pass-5 amendment spec approved by eugenelim.
- 2026-10-02: quiet-machine pass-5 amendment plan approved by eugenelim.
- 2026-10-03: returned to drafting after pass 5 measured a valid 12.12% fragment overhead. The owner chose to load the file-safety helper once in T16 and to add monthly bundles under ADR-0138, adding T17 and T18.
- 2026-10-04: ADR-0138 status set to Accepted at the direction of eugenelim. Its decision-makers are Platform Core maintainers.
- 2026-10-04: the engine recorded the amendment as `contract-amendment`. The round-12 pre-EXECUTE review sustained findings, which were folded in, and one owner decision was made: retraction residuals are documented, not purged (ADR-0138 Errata).
- 2026-10-04: monthly-bundle amendment spec approved by eugenelim.
- 2026-10-04: monthly-bundle amendment plan approved by eugenelim.
- 2026-10-12: returned to drafting after T18 measured a valid +7.22% at 1,000 loose fragments, triggering ADR-0143's Revisit. The owner chose to lower the ceiling to 500 and the warning to 375, and approved narrowing AC-B9 to Git's rename behaviour for one-record parts. ADR-0138 was renumbered to ADR-0143. T19 was added.
- 2026-10-12: ADR-0143 re-accepted by eugenelim with D9 at a 500 ceiling and a 375 warning.
- 2026-10-12: pre-PR amendment spec approved by eugenelim.
- 2026-10-12: pre-PR amendment plan approved by eugenelim.
