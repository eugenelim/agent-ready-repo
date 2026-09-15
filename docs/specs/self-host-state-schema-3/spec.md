# Spec: self-host state schema 3

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0059 (the catalogue-curation pack, which owns the white-label export boundary)
- **Contract:** none — `.agentbundle/self-host-state.json` is defined in code only and has no file under `contracts/`
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

A derived catalogue records what it was derived *from* and what it was derived
*with*, so a re-run reproduces the derivation instead of re-inventing it, and a
later `catalogue sync` has a recipe to replay.

`catalogue init --preset self-hosted` writes
`.agentbundle/self-host-state.json` at `schema_version` `"3"`. Two field groups
join the schema-2 fields:

```
recipe   packs, profiles, guides, attribution, tooling, and the identity fields
pin      source_uri, source_revision, archive_sha256, synced_at
```

`init` reads part of that file back. A re-run takes the recorded **selection**
(`packs`, `profiles`) and the recorded **identity values** (`name`,
`display_name`, `description`, `owner_name`, `owner_email`,
`preferred_adapter`, `repository_url`) in preference to re-deriving them. An
explicit flag still wins, and on a TTY the recorded value becomes the prompt's
default rather than replacing the prompt. A bare re-run therefore reproduces
the catalogue it found instead of silently renaming and widening it.

The recorded **mode** fields (`attribution`, `tooling`, `guides`) are written
and never read. An omitted `--attribution` resolves `white-label` whatever the
file says, so a file no leak check scans cannot select a disclosing mode.

The pin is written and not read. `--source` accepts a local path, so
`source_revision` and `archive_sha256` hold `null`, and `source_uri` is present
only under `attributed`.

Every value the file carries is free of upstream identity unless attribution
mode permits it. The identity leak check runs over the planned byte map before
this file is written, so the file is outside it and each field is its own
control.

The file is committed and travels with a published derived catalogue, so the
recipe an `init` run reads may have been authored by someone with no access to
the machine running it. Recorded values are third-party input on every run,
constrained before use and escaped at every sink they reach.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — the file's field list is stated here and becomes wrong | [`docs/architecture/catalogue/state.md`](../../architecture/catalogue/state.md) | eugenelim | Schema-3 field list replaces the schema-2 list; "Planned: schema 3" folds into current-state prose | The file's recorded field list equals AC-0002's key set, and no heading contains "Planned" |
| Current architecture | Applicable — this delivers a numbered phase of that rollout | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | § Rollout phase 1 marked done; a recorded note that `git+https://` affords no resolved ref and no digest | § Rollout's phase-1 entry is struck through or marked done, and the section names both missing pin values |
| Current architecture | Applicable — its state table names the schema version | [`docs/architecture/agentbundle.md`](../../architecture/agentbundle.md) | eugenelim | The derivation-state table row names schema 3 | Row matches what the code writes |
| Release history | Applicable — a non-cosmetic package change requires a release | [`packages/agentbundle/CHANGELOG.md`](../../../packages/agentbundle/CHANGELOG.md), [`docs/product/changelog.md`](../../product/changelog.md) | eugenelim | A topmost `0.45.0` entry in both | Both headings name the version in `packages/agentbundle/agentbundle/version.py` |
| Interface compatibility | Applicable — the PyPI readme is a pinned release surface | `packages/agentbundle/README-pypi.md` | eugenelim | A "What's new in" section naming the shipped version | `tests/roster/test_okf_catalogue_discovery.py` passes |
| User-facing promise | Applicable — `catalogue init --preset self-hosted` is a documented adopter command whose re-run behavior changes | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | eugenelim | A section describing what a re-run reproduces and what it still overwrites | The page mentions re-running `init`, which it currently does not |
| Maintainer procedure | Not applicable — no runbook governs this file | — | — | — | — |

## Boundaries

### Always do

- Keep every value written to `.agentbundle/self-host-state.json` free of
  upstream identity unless attribution mode permits it.
- Branch attribution-sensitive behavior on `attribution == "attributed"`, so
  any other value falls to the non-disclosing result.
- Keep a schema-2 state file readable.
- Escape every value interpolated into a generated TOML document for that sink.
- Constrain a recorded value before it reaches any sink, including the
  operator's terminal.

### Ask first

- Before making `--source` accept a URI, or otherwise populating
  `source_revision` or `archive_sha256`.
- Before reading `attribution`, `tooling`, or `guides` back from the recipe.
- Before changing what a re-run overwrites, aborts on, or removes.

### Never do

- Never add a module, package, or top-level directory.
- Never add a third-party dependency. The standard-library imports this uses
  are `dataclasses`, `json`, `re`, and `datetime`.
- Never bring the state file inside the identity leak check.
- Never let a recorded value widen what a re-run writes.

## Testing Strategy

Every outcome is a compressible invariant over a pure function or a single
`init` call, so all are **TDD** except the release surface, which is a
**goal-based check**. The plan's § Construction tests owns where they live.

- **Schema-3 emission (AC-0001, AC-0002, AC-0003, AC-0004)** — TDD: the
  emitted JSON is a compressible invariant over one function, so a key-set
  comparison is exact. AC-0004 is driven by a run that passes no pack filter,
  because that is the only input under which recording the unresolved value
  differs from recording the resolved one.
- **Upstream identity stays out of the file (AC-0005)** — TDD: the oracle is
  the repository's own leak check applied to the state file, so the anchor set
  and matching semantics stay identical to the tree's and a field added later
  inherits the control.
- **Attribution is preserved, not rewritten (AC-0006)** — TDD: the mirror of
  AC-0005 in the mode where the transform is a no-op; only a byte comparison
  across two runs catches a recipe that silently rewrote what the tree kept.
- **Attribution-gated pin (AC-0007, AC-0008)** — TDD: parametrised over
  `attributed`, `white-label`, and an unrecognised third value, because only an
  unrecognised value distinguishes a branch that fails closed from one that
  merely knows two modes.
- **Empty pin for a local source (AC-0009, AC-0010)** — TDD: a fixed expected
  value per field.
- **Schema-2 compatibility (AC-0011)** — TDD as a regression guard: an
  observed deletion, not a successful parse, and green today because this is
  shipped behavior the change must not break.
- **Recipe read-back (AC-0012)** — TDD: driven over every field the criterion
  enumerates, at that field's stated read location; the schema-2 companion case
  separates "the recipe was read" from "the value happened to match".
- **Flag precedence (AC-0013)** — TDD as a regression guard: the property
  already holds with no recipe present, so this case is green today and becomes
  discriminating only once the competing term exists.
- **Mode fields fail closed (AC-0014)** — TDD: driven differentially over all
  three fields, since this asserts an absence of behavior.
- **Hostile and malformed recipes (AC-0015, AC-0017, AC-0020, AC-0022)** —
  TDD: a crafted recorded value is the only way to reach the escaping and
  rejection paths, which no valid input exercises.
- **Malformed recipe container (AC-0016)** — TDD as a regression guard: a
  non-object recipe is already inert because nothing reads the key yet, so this
  case is green today and guards the property once the reader exists.
- **Confined read (AC-0021)** — TDD: a refusal is only observable by driving
  the helper against a path it rejects, so the fail direction needs its own
  case rather than being left to the mechanism.
- **TTY default seeding (AC-0018)** — TDD: `_prompt` is patchable, so both the
  offered default and the typed value are observable without a terminal.
- **Release surface (AC-0019)** — goal-based check: a version string needs a
  file comparison, not a unit test.

## Acceptance Criteria

- [x] **AC-0001.** The `.agentbundle/self-host-state.json` that `catalogue init
      --preset self-hosted` writes carries `schema_version` `"3"`.
- [x] **AC-0002.** That file carries a `recipe` object whose keys are exactly
      `packs`, `profiles`, `guides`, `attribution`, `tooling`, `name`,
      `display_name`, `description`, `owner_name`, `owner_email`,
      `preferred_adapter`, and `repository_url`.
- [x] **AC-0003.** That file carries a `pin` object whose keys include
      `source_revision`, `archive_sha256`, and `synced_at`.
- [x] **AC-0004.** After a run that passes no pack or profile filter,
      `recipe.packs` and `recipe.profiles` hold the resolved names the run
      selected — never `null`, an empty list, or a token standing for "all".
- [x] **AC-0005.** Under any `attribution` value other than `attributed`, the
      identity strings the file records — `recipe.name`, `display_name`,
      `description`, `owner_name`, `owner_email`, `preferred_adapter`,
      `repository_url`, and `pin.source_uri` — pass the same identity leak
      check the planned byte map passes, against the same anchor set. The
      structural values are out of scope: `recipe.packs`, `recipe.profiles`,
      `managed_paths`, and `managed_target_path` hold names drawn from the
      source tree or the adopter's filesystem, not values the identity
      transform owns.
- [x] **AC-0006.** Under `--attribution attributed`, a re-run that supplies no
      identity flags leaves every identity value in the target's
      `catalogue.toml` byte-identical to the first run's.
- [x] **AC-0007.** Under `--attribution attributed`, `pin.source_uri` holds the
      source path in the same resolved form the run used to read the source.
- [x] **AC-0008.** Under any other `attribution` value, the `pin` object has no
      `source_uri` key.
- [x] **AC-0009.** For a local-path `--source`, `pin.source_revision` and
      `pin.archive_sha256` are both `null`.
- [x] **AC-0010.** `pin.synced_at` matches the pattern
      `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z` against the whole string, with no
      leading or trailing character of any kind.
- [x] **AC-0011.** Given a state file carrying `schema_version` `"2"` with
      neither a `recipe` nor a `pin` key, a path recorded in its
      `managed_paths` whose recorded `sha256` matches the file on disk, and
      which the current run no longer plans, is deleted from the target.
- [x] **AC-0012.** On a re-run over a target holding a schema-3 state,
      invoking `init` without a given field's flag produces the recorded value,
      read at that field's location:

      | Field | Read location |
      | --- | --- |
      | `name` | `catalogue.toml` `[catalogue].name` |
      | `display_name` | `catalogue.toml` `[catalogue].display_name` |
      | `description` | `catalogue.toml` `[catalogue].description` |
      | `preferred_adapter` | `catalogue.toml` `[catalogue].preferred_adapter` |
      | `owner_name` | `catalogue.toml` `[[catalogue.maintainers]][0].name` |
      | `owner_email` | `catalogue.toml` `[[catalogue.maintainers]][0].email`, absent when the recorded value is empty |
      | `repository_url` | `catalogue.toml` `[catalogue.links].repository` |
      | `packs` | the directory names under the target's `packs/` |
      | `profiles` | the `.toml` file stems under the target's `profiles/` |

- [x] **AC-0013.** For each field AC-0012 enumerates, the same re-run invoked
      with that field's flag writes the flag's value, not the recorded one.
- [x] **AC-0014.** On a re-run over a target whose recipe records
      `attribution = "attributed"`, `tooling = "vendored"`, and
      `guides = "none"`, invoking `init` without `--attribution`, `--tooling`,
      or `--guides` resolves `white-label`, `external`, and `selected`
      respectively.
- [x] **AC-0015.** Every path that discards a recorded value — a failed field
      constraint, a `recipe` that is not an object, a read the confinement
      helper refuses, or a selection name the source does not ship — emits a
      diagnostic naming what was discarded and
      `.agentbundle/self-host-state.json` as its origin, without reproducing
      the discarded value. No discard is silent.
- [x] **AC-0016.** A `recipe` key whose value is not a JSON object is treated
      as absent, and the run produces the same derivation it would have
      produced had the key been missing.
- [x] **AC-0017.** Every value the generated `catalogue.toml` interpolates —
      `name`, `display_name`, `description`, `preferred_adapter`,
      `repository_url`, `owner_name`, `owner_email`, and each adapter entry —
      is escaped for that sink, so that a recorded value containing any
      character the field's own constraint admits — including a double quote, a
      backslash, a newline, and a control character such as `ESC` or `NUL` —
      leaves the document parseable and carrying exactly the tables and keys a
      benign value produces.
- [x] **AC-0018.** On a TTY re-run, the prompt for a recorded field offers the
      recorded value as its default, and a value typed at that prompt is the
      one written.
- [x] **AC-0019.** The version string in
      `packages/agentbundle/agentbundle/version.py` is `0.45.0`, and that same
      value appears in `packages/agentbundle/pyproject.toml`, the "What's new
      in" heading of `packages/agentbundle/README-pypi.md`, the topmost
      release heading of `packages/agentbundle/CHANGELOG.md`, the topmost
      `agentbundle` release heading of `docs/product/changelog.md`, and the
      `expected` literal in `tests/roster/test_okf_catalogue_discovery.py`.
- [x] **AC-0020.** Every recorded value is rejected before any use if it
      carries a character that alters rendering or cursor state — the C0 and C1
      control ranges, the ANSI escape introducer, and the Unicode bidirectional
      and format overrides. This is a property of the value at read time, so it
      holds at every sink it would otherwise reach: the generated
      `catalogue.toml`, the whole-tree byte transform, the operator's terminal,
      and any diagnostic. It applies to every field, including those whose
      other constraint is a URL or address pattern.
- [x] **AC-0021.** The state file is read through the repository's confined
      regular-file helper, rooted at the target and bounded at 4 MiB; a file
      exceeding that bound is refused. When the helper refuses a read for any
      reason, the run produces the no-recipe derivation rather than aborting.
- [x] **AC-0022.** A recorded `packs` or `profiles` entry is used only when it
      is a member of the set of names the source actually ships, compared as a
      name and never as a path fragment, so that an entry such as
      `../../elsewhere` is rejected rather than resolved. A rejected entry
      yields the no-recipe derivation for that selection; it does not abort the
      run.

## Follow-ons

- **Populating the pin** — making `--source` accept a URI and carrying
  provenance out of the fetchers. Owner: a later phase of
  [`upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Rollout.
- **Non-destructive re-run** — Tier classification replacing the unconditional
  overwrite, and reading the mode fields back once a re-run is safe. Owner:
  phase 3 of the same rollout.
- **A TOML-escaping lint** — a rule requiring every value interpolated into a
  generated TOML string to pass the escaping helper would catch AC-0017's
  class rather than its instance. Owner: unassigned; raised by the
  secure-design pass.

## Assumptions

- Technical: runtime is Python >=3.11 (`packages/agentbundle/pyproject.toml:9`).
- Technical: the state file has no contract under `contracts/` and no schema
  validation on read. A schema-2 file therefore loads unchanged, and an older
  `agentbundle` reading a schema-3 file also works, because the migration path
  touches only `managed_paths`.
- Technical: no gate, Makefile, or CI workflow reads the state file. A
  repository-wide search over `*.py`, `Makefile`, `*.yml`, `*.toml`, and `*.md`
  returns documentation plus one unit suite.
- Technical: `resolve_catalogue()` returns a bare `Path` with no provenance
  (`catalogue.py:94-124`), and `_resolve_https` never resolves a ref to a
  commit SHA (`catalogue.py:127-139`). The digest-bearing fetcher serves
  runtime archives, and the source-distribution archive kind is refused in
  three places (`catalogue_tooling/archive.py:399`, `commands/install.py:541`,
  `commands/install.py:4891`). This is why `source_revision` and
  `archive_sha256` hold `null`.
- Technical: the default description `collect_fields` derives embeds the
  **source** catalogue's name. The derived tree escapes that only because the
  identity transform rewrites it inside the planned bytes, which the state file
  is not among — so a recorded description needs its own control. AC-0005 is
  that control. It is stated over the identity strings rather than that one
  field, so an identity field added later inherits it.
- Technical: `validate_fields` covers `name`, `repository_url`, `archive_uri`,
  and `owner_email` only, so it was never the control for the free-text fields
  that reach the generated `catalogue.toml` and the whole-tree byte transform.
  The replay constraints are: they apply at read time to every replay-eligible
  recipe value — the seven identity scalars plus `packs` and `profiles` — and
  at write time to the transformed values actually recorded, so `init` refuses
  to emit a recipe its own re-read would discard. The recorded mode fields and
  the pin are not replay-eligible and are not read through that validation.
- Technical: the validators that do exist are not sink-safe on their own, which
  is why AC-0017 and AC-0020 are stated over every value rather than over the
  fields that prompted them. Verified by running the compiled patterns:
  `_URL_RE.fullmatch("https://x\x1b]0;pwned\x07")` matches,
  `_EMAIL_RE.fullmatch("a\x1b]0;x\x07@b.co")` matches, and
  `_SAFE_NAME_RE.match("abc\n")` matches. All three are `$`-anchored, and
  Python's `$` matches before a trailing newline; `\S` and `[^@\s]` both admit
  the escape introducer. `_EMAIL_RE` additionally admits a double quote.
- Technical: AC-0005 is scoped to the identity strings rather than the whole
  file, because the structural values can collide with an anchor by
  coincidence and carry no information when they do. A source catalogue named
  `extern` makes the code-defined token `"external"` a substring match, which
  would refuse a legitimate derivation while disclosing nothing — `"external"`
  is the value whatever upstream is called. Two limits follow and are accepted:
  a pack or profile whose name embeds upstream identity is recorded verbatim,
  and `managed_paths` has carried such names since schema 2. Neither is new
  exposure — `verify` scans file contents and never path names, so those names
  already sit unchecked in the derived tree's directory structure.
- Technical: AC-0005's oracle is blind to any value the anchor builder does not
  anchor. That builder skips values of four characters or fewer and reads only
  `name`, `display_name`, `description`, one maintainer name and email, and the
  two link values. The suite's source fixture declares only the first three, so
  the fixture gains a maintainer and both links; without that, the whole-file
  claim covers half the anchorable surface.
- Technical: the identity transform's attribution gate lives in
  `_apply_identity_transform_bytes`, which returns early under `attributed`;
  `_transform_text` beneath it has no gate. A recipe that transformed
  unconditionally would rewrite recorded identity in the one mode where the
  tree keeps it, so AC-0006 exists to pin the attributed side.
- Technical: the anchor builder skips any source value of three characters or
  fewer, and the transform replaces case-sensitively while the leak check
  matches case-insensitively. AC-0005 therefore names the leak check itself as
  its oracle rather than restating a matching rule that would diverge from it.
- Technical: `synced_at` is set on every run, so the state file differs after a
  re-run that changes nothing else (user confirmation 2026-09-14).
- Process: a non-cosmetic package change bumps `version.py` and
  `pyproject.toml` (`packages/AGENTS.md` § Version bump rule). The target is
  `0.45.0` (user confirmation 2026-09-14).
- Process: `tests/roster/test_okf_catalogue_discovery.py` runs only under the
  dispatch-only `test-roster.yml`, not on a PR, and it does not read the
  `agentbundle` heading in `docs/product/changelog.md`. AC-0019 therefore names
  every surface directly instead of delegating to that test.
- Process: this spec is not registered in `workspace.toml`
  (user confirmation 2026-09-14).
- Product: the beneficiary is the adopter of a derived catalogue who will later
  run `sync`; no canonical local source records this.
