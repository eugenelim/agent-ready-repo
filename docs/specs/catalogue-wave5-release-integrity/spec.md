# Spec: Catalogue Wave 5 — release integrity

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D8 and OQ3](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Discovery:** intent:catalogue-wave5-release-integrity ([intent](../../product/intents/catalogue-wave5-release-integrity.md))
- **Contract:** none — `catalogue-manifest.json` and the `catalogue package` JSON output have no schema file; AC-0001, AC-0002, AC-0013 and AC-0018 pin their shape, and the reference guides in Durable Outputs describe it.
- **Shape:** service

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

**Mode:** full. It changes a public CLI (`agentbundle catalogue package` gains
`--force`, `--compare` and `--format`, and its refusal exit code moves to 2),
the published `catalogue-manifest.json` shape, and integrity checks in
`catalogue verify --archive`.

## Outcome

A catalogue publisher or adopter can see which packs and profiles changed
between two releases, and can rely on a release version never being silently
replaced. Success is that `agentbundle catalogue package --compare <prior>`
names every added, removed and changed pack and profile from package-produced
evidence alone, and that re-packaging an existing release fails unless the
publisher passes `--force`.

## What Changes

- Per-unit content identity — each `packs[]` entry in `catalogue-manifest.json` gains `path` and `digest`; each `profiles[]` entry becomes `{name, path, digest}` (`catalogue_tooling/package.py`).
- Profile identity — only `.toml` files directly under `profiles/` are profile entries, matching `profiles/README.md`.
- Integrity checks — `catalogue verify --archive` (and packaging's staged self-verify) rejects malformed unit entries and recomputes each declared unit digest from `files[]` (`catalogue_tooling/archive.py`).
- Release refusal — an existing release archive refuses for both flavours; `--force` replaces it; see [Exit-code convention](#exit-code-convention).
- Release comparison — `--compare <archive>` reports the unit-level difference from one prior archive, in human output and with `--format json`.
- CI policy guard — `tools/test_catalogue_tooling_rewire.py` fails when first-party CI or the Makefile passes `--force` to `catalogue package`; the subcommand rejects abbreviated options.
- RFC-0076 OQ3 — resolved in [OQ3 resolution](#oq3-resolution-rfc-0076) below.

## OQ3 resolution (RFC-0076)

RFC-0076 OQ3 asks whether pack-level archives fall within the mutation-refusal
scope. AgentBundle produces no pack-level archive: the runtime flavour writes one
`catalogue-<release>.tar.gz` and the source flavour writes one
`catalogue-source-<release>.tar.gz`, each for the whole catalogue. The refusal
therefore covers exactly those two catalogue archives. A future pack-level
archive is new packaging scope and decides its own refusal rule then.

## Exit-code convention

`guides/_shared/reference/catalogue-ci-contract.md` defines exit 2 as a CLI
usage error. RFC-0076 D8 requires exit 2 for a refused replacement of an
existing release archive. The accepted RFC governs: the guide's exit-code table
gains that meaning for `catalogue package`. A CI step that treats any non-zero
exit as failure behaves as before. The deprecated top-level `package-catalogue`
command is unchanged and still exits 1 on the same refusal.

## Accepted limits

These are owner-accepted on 2026-10-20 and are not guarantees of this spec.

- For each flavour, a forced replacement places the archive and then its sidecar (and, for the source flavour, its manifest) as separate operations; a crash between them leaves a new archive beside the old sidecar, which `catalogue verify --archive --sha256-file` reports as a mismatch.
- A forced runtime replacement rewrites only the descriptor of the `--channel` given; another channel's descriptor naming the same release keeps the old SHA-256 until that channel is republished.
- A pre-Wave-5 prior archive packaged from a catalogue with `.toml` files below a `profiles/` subdirectory names a profile whose derived path does not exist, so `--compare` against it fails closed under AC-0016.
- On a filesystem without hard links, a non-forced run places the archive by exclusive-create copy; a crash mid-copy leaves a truncated archive at the release path, which later non-forced runs refuse and `--force` replaces.
- Unit digests and the comparison establish consistency with the archive's own `files[]`, not who published it; the archive sidecar and channel descriptor remain the provenance evidence.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface reference (CI) | `catalogue package` flags, output streams and exit codes change | `guides/_shared/reference/catalogue-ci-contract.md` and its byte-identical copy `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-ci-contract.md` | implementer | the `catalogue package` section and exit-code table describe `--force`, `--compare`, `--format json` and exit 2 on refusal | both copies updated and identical |
| Command reference | the flag table is stale today (old channel layout, no `--flavor`) and gains three flags | `docs/guides/reference/catalogue-commands.md` § `catalogue package` | implementer | whole-section refresh against `agentbundle catalogue package --help` | the table lists every flag `--help` lists |
| Archive reference | the manifest gains unit digests and verify gains checks | `docs/guides/reference/catalogue-archive.md` | implementer | a manifest section naming `packs[]`/`profiles[]` fields, the digest rule, `CAT-V-ARC-018`, `CAT-V-ARC-019`, and the consistency-not-provenance limit | section matches AC-0001, AC-0002, AC-0005, AC-0018 |
| Maintainer design | the packaging engine sequence gains refusal, force and compare steps | `packages/agentbundle/DESIGN.md` § Catalogue packaging engine | implementer | staging sequence lists the prior-archive read, the no-overwrite placement and the force path | section matches the shipped order |
| Release history | public CLI semantics and output change | release version `0.53.0`, moved together across `version.py`, `pyproject.toml`, `CHANGELOG.md` (entry carrying `Engine-Change-RFC: RFC-0076`), `README-pypi.md` (`What's new in 0.53.0` first), a `docs/product/changelog.d/` fragment, and the pin in `tests/roster/test_okf_catalogue_discovery.py` | implementer | changelog entry names the exit-code, abbreviation and `profiles` shape changes as breaking | `tests/roster/test_okf_catalogue_discovery.py` green |
| Decision rationale | OQ3 resolves here | this spec's OQ3 section; RFC-0076 acceptance checklist line for OQ3 marked done with a link here | implementer | RFC checklist item checked | link resolves |
| Product intent | the intent projects to this spec | intent `Decomposition` section; `workspace.toml` `["ini-007".work]` | lifecycle owner | intent names this spec; workspace lists it | `workspace-status` shows it canonical |

## Agent Rules

### Always do

- Derive every unit digest from the single confined `file_bytes` snapshot packaging already holds; never walk the source tree a second time.
- Open the prior archive only through `catalogue_tooling/archive.py` and only after `verify_archive` passes on it.
- Keep stdout for the JSON envelope alone; human output and diagnostic lines go to stderr in both formats.
- Pass `encoding="utf-8"` to every text read and write.

### Ask first

- Changing the manifest `schema` value.
- Adding `--force`, `--compare` or `--format` to the deprecated top-level `package-catalogue` command.
- Changing `self-hosted-source-manifest.json`.

### Never do

- Add a dependency or a new module; the change lives in `package.py`, `archive.py`, `results.py`, `commands/catalogue_package.py` and `cli.py`.
- Extract the prior archive to disk.
- Trust a digest the prior manifest declares instead of deriving it from that archive's verified `files[]`.
- Overwrite an existing release archive on a run without `--force`.
- Pass `--force` to `catalogue package` in any first-party workflow or Makefile recipe.

## Testing Strategy

- **Unit digests and manifest shape — TDD (AC-0001, AC-0002, AC-0003, AC-0004)** — the digest is a pure function of the snapshot, so a fixture catalogue pins exact values.
- **Archive manifest verification — TDD (AC-0005, AC-0006, AC-0018)** — `verify_archive` on hand-built fixture archives is a deterministic oracle.
- **Refusal, placement and force — TDD, integration through `run(args)` (AC-0007, AC-0008, AC-0009, AC-0019)** — the exit code and the output tree are observable from the handler.
- **CI policy guard and option parsing — goal-based and TDD (AC-0010, AC-0020)** — the guard test is green on the tree and red on planted violations; abbreviation rejection is a parser call.
- **Comparison — TDD, integration through `run(args)` (AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0021, AC-0022, AC-0023, AC-0024)** — pairs of fixture archives give exact expected differences.
- **Flavour conflicts — TDD (AC-0017)** — argument combinations are a closed set.
- **Adopter rehearsal — manual QA, end to end** — the intent's validation hook: the built CLI packages, compares, refuses and force-replaces in a temporary adopter tree with no source-workspace state.

## Acceptance Criteria

- [ ] **AC-0001.** Each `packs[]` entry in `catalogue-manifest.json` is `{name, version, path, digest}`, where `path` is `packs/<dir>` and `digest` is the unit digest of that path: `sha256:` followed by the lowercase hex SHA-256 of the UTF-8 text made of one line `<file sha256 hex>  <relative path>\n` (two spaces) per member file, lines sorted by relative path in byte order. A directory path's member files are the archived files whose path starts with `path + "/"`, each relative to that prefix; a file path's only member is the archived file at exactly `path`, with its basename as relative path.
- [ ] **AC-0002.** Each `profiles[]` entry is `{name, path, digest}` for each `profiles/<name>.toml` file directly under `profiles/`, with `path` equal to that file's path and `digest` its unit digest per AC-0001, entries sorted by name; a `.toml` file inside a subdirectory of `profiles/` produces no entry.
- [ ] **AC-0003.** Adding a file that packaging excludes — a build-residue name (`__pycache__/`, `.pyc`, `.DS_Store`, `.coverage*` and the rest of the package denylist) under a pack, or any file under a `_`-prefixed directory of `packs/` or `profiles/` — leaves every unit digest unchanged.
- [ ] **AC-0004.** The manifest `schema` value is `2`.
- [ ] **AC-0005.** `catalogue verify --archive` fails with diagnostic `CAT-V-ARC-018` for each `packs[]` or `profiles[]` entry carrying a `digest` whose value differs from the unit digest per AC-0001 of that entry's `path` over `files[]`, where a `path` with no member file counts as different.
- [ ] **AC-0006.** `catalogue verify --archive` reports no `CAT-V-ARC-018` or `CAT-V-ARC-019` for a manifest whose `packs[]` entries are `{name, version}` objects, whose `profiles` are plain name strings or absent, and whose entries carry no `digest`.
- [ ] **AC-0007.** For each flavour — runtime with an existing `catalogue-<release>.tar.gz`, source with an existing `catalogue-source-<release>.tar.gz` — `catalogue package` without `--force` exits 2 and prints the existing archive path on stderr.
- [ ] **AC-0008.** For each flavour in AC-0007, a refused run creates, modifies or deletes no file under `--output`.
- [ ] **AC-0009.** For each flavour, `catalogue package --force` over an existing release exits 0 and leaves an archive whose sidecar SHA-256 matches its bytes and whose manifest reflects the current content, with no `.tmp` file left beside it.
- [ ] **AC-0010.** `tools/test_catalogue_tooling_rewire.py` fails when a `catalogue package` command in `Makefile` or any `.github/workflows/*.yml` file, read with backslash-continued lines joined and whitespace runs collapsed to one space, contains `--force`, and passes on the repository tree.
- [ ] **AC-0011.** With `--compare <prior>`, the human output on stderr lists every added, removed and changed pack and every added, removed and changed profile, where changed means a different digest or version, and states the count of unchanged packs and of unchanged profiles.
- [ ] **AC-0012.** In the human comparison output, a changed pack whose version equals the prior version carries the marker `content changed, version unchanged`.
- [ ] **AC-0013.** With `--format json` on a successful run, stdout is exactly one JSON object with keys `schema_version`, `command` (`"catalogue"`), `operation` (`"package"`), `agentbundle_version`, `catalogue_schema_version`, `ok` and `diagnostics`, plus `comparison` when `--compare` is given, where `comparison` is `{"prior": {"archive", "bundle", "release"}, "packs": {"added", "removed", "changed", "unchanged"}, "profiles": {"added", "removed", "changed", "unchanged"}}`; `prior.archive` is the `--compare` value as given; added and removed items are `{name, version, digest}` for packs and `{name, digest}` for profiles; changed items are `{name, version: {from, to}, digest: {from, to}}` for packs and `{name, digest: {from, to}}` for profiles; each list is sorted by name and `unchanged` is an integer.
- [ ] **AC-0014.** When the prior archive fails `verify_archive`, `catalogue package --compare` exits 1, prints each verification error on stderr as `<code>: <message>`, and creates no file under `--output`.
- [ ] **AC-0015.** Against a prior archive whose manifest entries lack `path` and `digest`, the comparison derives each prior unit digest per AC-0001 from that archive's `files[]` with path `packs/<name>` or `profiles/<name>.toml`, so identical content reports the unit unchanged.
- [ ] **AC-0016.** When a prior unit's derived path has no member file, `catalogue package --compare` exits 1, names the unit on stderr, and creates no file under `--output`.
- [ ] **AC-0017.** `catalogue package --flavor source` combined with `--compare` or `--format json` exits 2 with a usage message, writes nothing on stdout, and creates no file under `--output`.
- [ ] **AC-0018.** `catalogue verify --archive` fails with diagnostic `CAT-V-ARC-019`, and raises no exception, for each of these manifest shapes: the top level is not an object; a `files[]` item is not an object with string `path` and `sha256`; `profiles` is present and not a list; a `packs[]` item is not an object with a string `name` and a string `version`; a `profiles[]` item is neither a string nor an object with a string `name`; an object item has a `path` or `digest` field that is not a string; an object item has a `digest` and no `path`.
- [ ] **AC-0019.** For each flavour, on a run without `--force`, when the release archive appears at its path after the run starts and before placement, `catalogue package` exits 2, the appeared archive's bytes are unchanged, and no `.tmp` file remains under `--output`.
- [ ] **AC-0020.** `catalogue package` rejects an abbreviated option such as `--forc` with exit 2.
- [ ] **AC-0021.** With `--format json`, a run that exits 1 or 2 after argument parsing — other than the AC-0017 combinations — writes exactly one JSON object on stdout with the AC-0013 envelope keys other than `comparison`, `ok` equal to `false`, `diagnostics` naming each error's code, and no `comparison` key.
- [ ] **AC-0022.** In every stderr line `catalogue package` prints that carries text derived from the prior archive — comparison lines, verification diagnostics and unit names — every character of that text for which Python's `str.isprintable()` is false is written as its `\x`, `\u` or `\U` escape, so no such character reaches stderr from the prior archive.
- [ ] **AC-0023.** When the `--compare` path is missing, is not a regular file, or is not a readable gzip tar archive, `catalogue package --compare` exits 1 with a diagnostic on stderr and creates no file under `--output`.
- [ ] **AC-0024.** An exception raised while reading the prior archive or deriving its unit digests makes `catalogue package --compare` exit 1 with a diagnostic and no traceback, and creates no file under `--output`.

## Follow-ons

- eugenelim: [intent validation hook](../../product/intents/catalogue-wave5-release-integrity.md#de-risking-verdict) — observe whether 3 of 5 publishers or adopters use the unit-level difference to make or explain a release decision.

## Assumptions

- Product: no publisher or adopter has used a unit-level comparison yet — the comparison's human layout is ungrounded in observed decisions until the follow-on runs.
