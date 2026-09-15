# Plan: self-host state schema 3

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`docs/architecture/catalogue/state.md`](../../architecture/catalogue/state.md)
  (the file's current field list and its two named limits);
  [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md)
  § Stage 2 and § White-label pins carry no upstream identity;
  `packages/AGENTS.md` § Version bump rule; analogous implementation
  `PackState` (`agentbundle/config.py:170-171`) and its emitter
  (`config.py:711-714`) for the provenance vocabulary this schema mirrors.

## Approach

Four commits on top of the two design-doc commits already on the branch: a
standalone sink-escaping fix, then the write path, the read path, and finally
the release surface with the documentation the others make stale.

The escaping fix goes first and alone because it is a pre-existing defect this
change makes newly reachable, and it should be revertable without taking the
schema with it.

## Constraints

- Every field written to the state file is its own control — see spec
  § Boundaries, *Always do*.
- Values read back out of the file are untrusted input reaching three sinks:
  the generated `catalogue.toml`, the whole-tree byte transform, and the
  operator's terminal via the seeded prompt. A value is offered as a prompt
  default only after it passes its field's read-time constraint.
- A schema-2 file has no `recipe` key; absence resolves to the no-recipe
  derivation.

## Construction tests

All tests land in
`packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`,
which already exposes `_make_source(tmp_path)` (an upstream catalogue named
`upstream-catalogue`, display name `Upstream Catalogue`, packs `core` and
`governance-extras`) and `_read_state(target)`.

The three existing `schema_version == "2"` assertions (lines 344, 433, 746) are
contract anchors on the artifact this change edits; they move to `"3"` in T2.

`_make_source` creates exactly one profile, `default.toml`, so a profiles
read-back case built on it holds whether or not the recipe is read. T3 adds a
second profile to the helper; that is a harness change, not a free reuse.

**Red validation.** The stubs below were extracted to disposable scratch and
run against the current implementation; each fails for the absence of the
feature it names. Three criteria cannot earn red, because they assert behavior
that already holds and must survive this change:

| Criterion | Why it is green today |
| --- | --- |
| AC-0011 | Schema-2 stale-path removal is shipped behavior the change must not break. |
| AC-0013 | With no recipe to lose to, a supplied flag already wins; the case becomes discriminating once T3 adds the competing term. |
| AC-0016 | Nothing reads `recipe` yet, so a malformed one is already inert. |
| AC-0005 | The current state file carries no recipe, so there is no upstream identity in it to find. |

The first three are regression guards on shipped behavior, and the spec's
Testing Strategy labels them as such. AC-0005 is a different kind of green: it
guards against a leak *this change could introduce*, so it is green before the
change by construction and only discriminates once T2 emits the recipe. That is
the expected shape for it, not a defect — but it means AC-0005 is not evidence
until T2 lands, and the last measured run confirms it (4 failed, 1 passed; the
pass is AC-0005).

One caution for EXECUTE. A case that merely reads a key the schema does not yet
emit is red on the `KeyError`, not on its own property, so each built-out case
must be re-checked against an implementation that emits the key and still gets
the behavior wrong. Red alone does not prove a case discriminates.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| `state.md` schema-3 field list | T4 |
| `upstream-sync.md` phase-1 done + pin-fidelity note | T4 |
| `agentbundle.md` table row | T4 |
| Both changelogs, README-pypi, version surfaces | T4 |
| `create-a-self-hosted-catalogue.md` re-run section | T4 |

## Design (LLD)

### Design decisions

**D1 — the recipe records resolved selections.** `select_packs` returns
everything when its filter is falsy (`initialise_self_hosted.py:430-431`), so
persisting an unresolved `None` would let a later bare `sync` re-select
whatever the source offers at sync time. The recipe stores the resolved lists
under the JSON keys `packs` and `profiles`.

**D2 — one attribution predicate, several callers.** `_source_pack_identity`
branches on `cfg.attribution == "attributed"`, and `_apply_identity_transform_bytes`
early-returns on the same test. Extract `_is_attributed(cfg) -> bool` and route
all three uses — that function, the pin's `source_uri`, and D3's recipe
transform — through it.

**D3 — the recipe records the bytes the tree records, in both modes.**
`collect_fields` derives a default description embedding the **source**
catalogue's name (`:346-352`), and `cfg` is never rewritten, so writing `cfg`
values straight into the recipe would ship that name into a file no leak check
scans. Each recipe **string** is therefore passed through the same transform
the tree's bytes receive — including its `attributed` early-out. Transforming
unconditionally would be the mirror defect: under `attributed` the tree keeps
the upstream wording while the recipe stored a rewritten copy, and AC-0012
would then write that copy into `catalogue.toml`, an attribution surface,
on the next bare re-run. AC-0005 and AC-0006 pin the two halves.

Two groups are the exception, both for the same reason — they are closed
vocabularies whose values must match a fixed set, not free text that can carry
identity. `recipe.packs` and `recipe.profiles` hold directory and file names
that must match the source tree on disk; transforming them would make a
read-back select packs that do not exist. `recipe.guides`, `recipe.attribution`,
and `recipe.tooling` hold one of a fixed set of mode tokens. Both groups are
recorded **verbatim**.

The mode fields are not a theoretical case. `_transform_text` performs a
substring `str.replace`, so a source catalogue named `extern` rewrote
`tooling` from `"external"` to the derived name plus `"al"` — measured on the
implementation before this was corrected. Only the fields that can actually
carry upstream identity take the transform: `description`, whose derived
default embeds the source catalogue's name, and `preferred_adapter`, which
falls back to the source's value.

**D4 — mode fields are recorded, not consumed.** Reading `attribution` back
would let an edit to an unscanned file select `attributed`. Reading `tooling`
back would let it select `vendored`, which copies the agentbundle package into
the tree. Both stay write-only.

**D5 — the recipe is a parameter, not a pre-merge.** The state is loaded once
more before step 4 and passed to `collect_fields` as an argument. Merging it
into `cfg` before the call would make every `if not cfg.<field>:` block false
and skip every prompt, which contradicts D7 and makes AC-0018 unreachable. The
signature gains one optional parameter; the existing step-10 load is untouched.

The state-file read routes through `file_safety.read_confined_regular_file`,
the helper the repository blesses and this module already calls at `:514` and
`:987`. The current `is_file()` check follows symlinks and the read is
unbounded; that was tolerable while the output fed only stale-path removal, but
this change promotes it to a source of values reaching the transform.

That helper's `max_bytes` defaults to `None`, and both existing call sites pass
nothing, so routing through it supplies confinement but not a bound. This call
passes **4 MiB**. The origin: `managed_paths` carries one `{path, sha256}`
entry per written file, this repository's own catalogue ships 1,891 files under
`packs/` and `profiles/`, and a representative entry serialises to 134 bytes —
about 247 KiB, so 4 MiB is roughly sixteen times the largest state file the
current corpus can produce. A refusal for any reason, bound or confinement,
falls back to the no-recipe derivation and emits AC-0015's diagnostic.

**D6 — per-field resolution is three shapes, not one.** Verified in source:
`name`, `display_name`, `description`, `owner_name`, and `owner_email` are
`if not X:` blocks with TTY prompts (`:336-360`); `preferred_adapter` is a
single `or` against the **source's** value (`:362`); and `repository_url` is not
resolved by `collect_fields` at all — it passes through at `:376`, and the
`https://example.com/my-catalogue` placeholder lives downstream in the
transform's replacement builder (`:566-573`). A recorded `repository_url`
therefore reaches three sites: that placeholder branch, the homepage branch at
`:569-573`, and the `repository =` emission at `:682`. The implementation sets
it on `cfg` inside `collect_fields` so all three see one value.

**D7 — the recipe seeds the prompt, it does not replace it.** On a TTY the
recorded value becomes the bracketed default, so an operator can still change
it. A recorded value that fails its constraint is never offered.

### Data & schema

Two dataclasses nested in `SelfHostOwnershipState`, each with its own
`to_dict`. `SelfHostPin.to_dict` omits the `source_uri` key entirely when it is
unset, which is what AC-0008 requires and what `upstream-sync.md:254` and
`state.md:92` both specify — an absent key, not a present null.

### Behavior & rules

A typed reader returns a recipe only when the `recipe` value is a JSON object,
and returns each field only when its value is a string satisfying that field's
constraint. A rejected field emits a diagnostic naming the state file and falls
through to the existing derivation.

Two rules govern the whole table, not individual rows. Every pattern is
matched against the **whole string** with leading and trailing whitespace
rejected — `_SAFE_NAME_RE`, `_URL_RE`, and `_EMAIL_RE` are all `$`-anchored and
so all admit a trailing newline. And every value is rejected outright if it
carries a character that alters rendering or cursor state, per AC-0020; that
check is independent of the pattern, because `\S` and `[^@\s]` both admit the
escape introducer.

| Field | Additional constraint | Sinks it must survive |
| --- | --- | --- |
| `name` | `_SAFE_NAME_RE` | TOML value, transform, terminal |
| `repository_url` | `_URL_RE`, `_URL_USERINFO_RE` | TOML value, transform, terminal |
| `owner_email` | `_EMAIL_RE` | TOML value, terminal |
| `preferred_adapter` | membership in the shipped adapter-name set from `agentbundle/_data/adapter.toml`; an unreadable or empty set rejects every value rather than accepting any | TOML value, terminal |
| `display_name`, `description`, `owner_name` | bounded length | TOML value, transform, terminal |
| `packs`, `profiles` | each entry is a string and a **member** of the names the source ships, compared as a name rather than resolved as a path, so `../../elsewhere` is rejected rather than escaping the root | `select_packs` / `_select_profiles`, and the filesystem beneath them |

The escaping in T1 is the sink-side control and does not depend on these; both
are required, because `_URL_RE` and `_EMAIL_RE` each admit a double quote.

### Failure, edge cases & resilience

| Case | Resolution |
| --- | --- |
| Target absent (first run) | Loader returns `None`; no-recipe derivation |
| Schema-2 state (no `recipe`) | Missing key reads as absent; same |
| `recipe` not an object | Rejected whole (AC-0016) |
| One field invalid | Rejected alone, diagnostic emitted (AC-0015), not offered as a prompt default |
| A valid-shaped but hostile value | Escaped at the TOML sink (AC-0017) |
| A recorded selection name the source does not ship, or one shaped like a path | Rejected by the membership check; that selection falls back to the no-recipe derivation rather than raising out of `select_packs` (AC-0022) |
| Any discard at all | Announced. AC-0015 makes every discard path emit a diagnostic naming what was dropped and the state file as its origin, so a silent fallback — the exact harm this change exists to prevent — cannot be the outcome of a malformed recipe |
| The file is edited between the early read and the step-10 read | The early read feeds `cfg`; the late read feeds stale-path removal, which is independently bounded by its own path-confinement and `sha256` guards (`:761-793`). |
| The recipe was authored by a third party | The state file is committed, so it ships with a published derived catalogue and the adopter who runs `init` may not be the adopter who wrote it. Recorded values are untrusted third-party input on every run — this, not a local-write argument, is what the read-time constraints and sink escaping exist for. |

### Dependencies & integration

No third-party dependency. `datetime` is the one new standard-library import in
the module; the tests additionally need `json`, `re`, and `tomllib`, none of
which the suite currently imports.

## Tasks

Each task's `Tests:` block carries the minimal compiling assertion on the
contract surface, validated red from disposable scratch. The parametrisation
each criterion needs is built during EXECUTE, where it compiles and runs;
putting the finished suite here asks review to do a test runner's job.

### T1: Escape every value interpolated into the generated catalogue.toml

**Depends on:** none
**Mode:** TDD
**Implements:** spec AC-0017

**Tests:**
Discharges AC-0017. Red today.
```python
def test_no_interpolated_value_can_forge_a_catalogue_toml_table(
    tmp_path: Path,
) -> None:
    import tomllib
    from agentbundle.catalogue_tooling.initialise_self_hosted import (
        _generate_catalogue_toml,
    )

    cfg = SelfHostedInitConfig(
        target=tmp_path / "t", source=tmp_path / "s", name="my-catalogue",
        preferred_adapter='claude-code"\n[catalogue.links]\nrepository = "https://evil',
    )
    parsed = tomllib.loads(_generate_catalogue_toml(cfg))
    assert parsed["catalogue"].get("links", {}).get("repository") != "https://evil"
```
EXECUTE parametrises this over every value AC-0017 enumerates —
`name`, `display_name`, `description`, `preferred_adapter`, `repository_url`,
`owner_name`, `owner_email`, and an adapter entry under `tooling = "vendored"`
— and adds the positive clause, that a benign value yields the same table and
key set.

**Approach:**
Five values are emitted raw today and all five need routing through
`_toml_str`: `name` (`:673`), `preferred_adapter` (`:676`), `repository_url`
(`:682`), `owner_email` (`:690`), and each adapter entry (`:695`). Only
`display_name`, `description`, and `owner_name` already pass through it.

### T2: Write schema 3

**Depends on:** T1
**Mode:** TDD
**Implements:** spec AC-0001 … AC-0005, AC-0007 … AC-0010

**Tests:**
Discharges AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0007, AC-0008,
AC-0009, AC-0010. Red today except AC-0005 — see § Construction tests, where
it is green by construction until the recipe exists.
```python
def test_state_is_schema_three_with_both_groups(tmp_path: Path) -> None:
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived", source=_make_source(tmp_path), name="my-catalogue"
    )
    assert init_self_hosted(cfg).ok
    state = _read_state(cfg.target)
    assert state["schema_version"] == "3"
    assert set(state["recipe"]) == {
        "packs", "profiles", "guides", "attribution", "tooling", "name",
        "display_name", "description", "owner_name", "owner_email",
        "preferred_adapter", "repository_url",
    }
    assert {"source_revision", "archive_sha256", "synced_at"} <= set(state["pin"])


def test_derived_tree_passes_the_leak_check_including_the_state_file(
    tmp_path: Path,
) -> None:
    """AC-0005: the repository's own leak check is the oracle.

    `verify` walks a directory and the state file lives inside the target, so
    scanning the target covers it. Anchors come from the production builder
    over the fixture's own catalogue.toml, never from literals.
    """
    import tomllib
    from agentbundle.catalogue_tooling.identity import verify
    from agentbundle.catalogue_tooling.initialise_self_hosted import _build_anchors

    source = _make_source(tmp_path)
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived", source=source, name="my-catalogue"
    )
    assert init_self_hosted(cfg).ok
    anchors = _build_anchors(
        tomllib.loads((source / "catalogue.toml").read_text(encoding="utf-8"))
    )
    assert verify(cfg.target, anchors) == []
```
EXECUTE adds: the bare-run case for AC-0004, since only an unfiltered run
separates a resolved selection from an unresolved one; the unrecognised-third-
mode parametrisation for AC-0008, whose `attributed` arm is also AC-0007's
case, comparing `pin.source_uri` against the source path in the same resolved
form `init` used to read it; and the pin-field cases for AC-0009 and AC-0010. It also extends `_make_source` to declare a maintainer name, a
maintainer email, and both link values above the anchor builder's floor —
without those, AC-0005's oracle is blind to three of the six anchorable values.

**Approach:**
Add `SelfHostRecipe` and `SelfHostPin`; extract `_is_attributed`; route each
recipe string through the transform *with its `attributed` early-out* and
record the selection lists verbatim. Move the three `schema_version` anchors.

### T3: Read the recipe back

**Depends on:** T2
**Mode:** TDD
**Implements:** spec AC-0006, AC-0011 … AC-0016, AC-0018, AC-0020 … AC-0022

**Tests:**
Discharges AC-0006, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016,
AC-0018, AC-0020, AC-0021, AC-0022. The two stubs below were measured red for
AC-0006 and the `name` slice of AC-0012. The rest are unmeasured until EXECUTE
builds them; AC-0011, AC-0013 and AC-0016 are expected green throughout — see
§ Construction tests.
```python
def test_recorded_name_survives_a_bare_rerun(tmp_path: Path) -> None:
    import tomllib
    source = _make_source(tmp_path)
    target = tmp_path / "derived"
    assert init_self_hosted(SelfHostedInitConfig(
        target=target, source=source, name="recorded-name"
    )).ok
    assert init_self_hosted(SelfHostedInitConfig(target=target, source=source)).ok
    parsed = tomllib.loads((target / "catalogue.toml").read_text(encoding="utf-8"))
    assert parsed["catalogue"]["name"] == "recorded-name"


def test_attributed_rerun_preserves_what_the_tree_keeps(tmp_path: Path) -> None:
    """AC-0006: the mirror of AC-0005 in the mode where the transform is a no-op."""
    source = _make_source(tmp_path)
    target = tmp_path / "derived"
    assert init_self_hosted(SelfHostedInitConfig(
        target=target, source=source, name="my-catalogue", attribution="attributed"
    )).ok
    first = (target / "catalogue.toml").read_bytes()
    assert init_self_hosted(SelfHostedInitConfig(
        target=target, source=source, attribution="attributed"
    )).ok
    assert (target / "catalogue.toml").read_bytes() == first
```
EXECUTE builds out, one case per criterion: the nine-field read-back table of
AC-0012 with each field read at its stated location, including
`[[catalogue.maintainers]][0]` and the empty-`owner_email` absence branch; the
flag-precedence cases of AC-0013, each using a flag value distinguishable from
the recorded one, and covering `packs` and `profiles` as well as the seven
scalars; the three-field mode differential of AC-0014; the schema-2 deletion of
AC-0011; the rejection-with-diagnostic of AC-0015 and the re-derived outcome of
AC-0016; the control-character cases of AC-0020, which must cover the URL and
address fields because their patterns admit the escape introducer; the
confinement-refusal fallback of AC-0021 plus a file over the 4 MiB bound; the
traversal and unknown-name rejections of AC-0022; and AC-0018's two halves,
patching `initialise_self_hosted._prompt` to observe both the bracketed default
offered and the value a typed reply writes.

**Approach:**
Add the early confined read — rooted at the target, bounded, and failing closed
to the no-recipe derivation on refusal — a typed reader applying the
§ Behavior & rules constraints, and the recipe parameter to `collect_fields`
feeding each of the three resolution shapes D6 names.

### T4: Release surface and documentation

**Depends on:** T3
**Mode:** goal-based check
**Implements:** spec AC-0019

**Tests:**
Discharges AC-0019.
Done when the six paths spec AC-0019 enumerates all carry the same version and
`python3 -m pytest packages/agentbundle/tests/unit/test_version.py tests/roster/test_okf_catalogue_discovery.py -q`
passes. The roster half is a local run: that file is not on the PR gate.

**Approach:**
Bump the six surfaces; fold `state.md`'s "Planned: schema 3" into current-state
prose; mark `upstream-sync.md` § Rollout phase 1 done and record there that
`git+https://` affords an unresolved ref and no digest; update the
`agentbundle.md` table row; add a re-run section to
`guides/_shared/how-to/create-a-self-hosted-catalogue.md`.

## Rollout

- **Delivery:** one PR, four commits. Reversible by revert; the schema is
  additive and unread by any other component.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none. An older `agentbundle` reading a schema-3
  file uses `managed_paths` only, so a mixed-version tree degrades to schema-2
  behavior rather than failing.

## Risks

- **A recorded value reaches the whole-tree transform.** `validate_fields`
  covers four fields and none of the free-text ones, so the read-time
  constraints in § Behavior & rules are the actual control, not that function.
- **The pin looks finished but is empty.** Recorded in the spec and the design
  doc so an empty pin is not read as a defect.
- **`synced_at` diffs on every run.** An adopter who commits the state file
  sees a one-line diff from a re-run that changed nothing else.

## Changelog

- 2026-09-14 — initial draft.
- 2026-09-14 — D3 corrected during T2: the closed-vocabulary mode fields join
  the list fields as recorded-verbatim. The original wording said "each recipe
  string", which the worker implemented faithfully and which corrupted
  `recipe.tooling` under a source name that is a substring of a mode value.
- 2026-09-14 — revised against three spec-stage reviews: recipe written
  post-transform (D3), read-back extended to `packs`/`profiles`, per-field
  read-time constraints, prompt seeding (D7), TOML sink escaping split out as
  T1, and the per-field resolution shape corrected (D6).
