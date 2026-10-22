# RFC-0109: Publish the agentbundle catalogue specification as a versioned site section with stable schema URLs

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-10-21
- **Date closed:** 2026-10-21
- **Decision weight:** heavy (it amends two accepted RFCs and mints permanent public schema identifiers; minting an `$id` and choosing a URL path are one-way doors)
- **Related:** [RFC-0003](0003-spec-and-cli.md) (amended), [RFC-0076](0076-catalogue-contracts-composition-semantics-discovery.md) (D1, D9 and D10 amended), [RFC-0055](0055-rfc-amendment-and-errata-convention.md), [RFC-0089](0089-starlight-docs-boundary.md), [RFC-0092](0092-first-class-distribution-routes.md), [survey](../product/research/catalogue-spec-publication-survey.md), Draft intents `docs/product/intents/catalogue-specification-publication.md` and `docs/product/intents/catalogue-wave7-marketing-evaluator.md` (both on PR #1589)

## Reviewer brief

- **Decision:** How the agentbundle catalogue specification is published on the project website as a versioned set with stable URLs, kept apart from work-loop and delivery contracts.
- **Recommended outcome:** Accept D1 to D8.
- **Change if accepted:**
  - One manifest in `contracts/` names the 10 files that make up the specification. The same manifest drives the site, the CLI's bundled copies and `public-contracts.txt`.
  - The docs site serves each released version at `https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/<MAJOR.MINOR>/`, starting at `0.1`, and each member schema's `$id` is its URL there.
  - No contract moves on disk. A new schema covers the release archive manifest `catalogue-manifest.json`.
- **Affected surface:** `contracts/`, the CLI's `_data/` copies and their parity gate, `docs-site/`, `tools/build-site.py`, the Pages workflow, the agentbundle tag-release workflow, and RFC-0003 and RFC-0076 through correction entries.
- **Stakes:**
  - The manifest, the site section and the generated pages are two-way doors.
  - Each released `$id` and each released URL is a one-way door: once published, it never changes.
- **Review focus:** the `$id` host and path (D3), the tag-time release gate (D7), and the membership rule (D1).
- **Not in scope:**
  - changing what any contract means;
  - publishing work-loop, delivery, workspace or work-intake contracts;
  - a sibling repository, a neutral organisation or a custom domain;
  - the specification's licence;
  - building the Wave 7 evaluator page or the Wave 6 Build a Catalogue route.

## Terms used here

- **Catalogue.** A repository of installable agent-context packs that `agentbundle` validates, packages and installs. An adopter builds their own.
- **Contract.** A machine-readable file, a JSON Schema or a TOML rule file, that `agentbundle` checks catalogue files against.
- **`_data/` copies.** Byte-identical copies of contracts inside the `agentbundle` Python package (`packages/agentbundle/agentbundle/_data/`), so the CLI works offline. A build gate keeps them equal to `contracts/`.
- **`$id`.** The JSON Schema keyword that names a schema with a URI. JSON Schema treats it as an identifier, not a promise that the URI can be fetched.
- **Snapshot.** A frozen, committed copy of the specification files and page sources as released at one version.
- **CLI release.** An `agentbundle-v*` tag push, which is what publishes the package to PyPI. A version bump without a tag is not a release.
- **RFC-0003.** The accepted decision that made the adapter contract a published, versioned specification with a reference CLI. It made the GitHub file path canonical for v0.x.
- **RFC-0076.** The accepted decision for the catalogue contracts programme, delivered in nine waves. D1 says `contracts/` is the authored source. D9 adds a Build a Catalogue section to the docs site. D10 adds an evaluator page to the marketing site.

## The ask

**Recommendation:** accept D1 to D8.

**Why now.** On 2026-10-21 the owner decided that the catalogue contracts must be published the way other platforms publish a specification: on the website, versioned, at stable addresses. Today an adopter opens `contracts/` and finds 61 schemas outside `vendor/`. Catalogue, work-loop, delivery and CLI-output schemas sit side by side, and nothing marks which ones a catalogue needs. No schema resolves at a real URL. Only `adapter.toml` carries a version (`0.18`).

The Wave 7 evaluator page links to this specification, and Wave 9 closeout depends on Wave 7. That puts this RFC on the critical path for closing RFC-0076. Accepted RFC-0003 and RFC-0076 D9 and D10 set a different home, so the change needs this RFC.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which contracts form the specification, and where is membership declared? | 9 existing files plus a new archive-manifest schema. One manifest, `contracts/catalogue-spec.toml`, declares them and drives the site, the `_data/` copies and `public-contracts.txt` | A member describes a catalogue source file, an adapter-neutral output adopters consume, or the adapter contract. Host-specific projections and engine settings are not members | This review | Confirm the rule and the edge-case calls |
| D2 | Where is it published? | A `/docs/spec/catalogue/` section of the Starlight docs site. Build a Catalogue links to it. The marketing site links to it and stays free of schemas | The docs site already owns technical reference (RFC-0089). MCP and Kubernetes publish their spec inside their docs site | This review | Confirm the home and the D9 and D10 amendments |
| D3 | What are the URL, version and `$id` schemes? | The existing `github.io` site host. Semver `MAJOR.MINOR` for the set, starting at `0.1`. Immutable path per version. `$id` equals the served URL. `latest` and `draft` are aliases, never identities | The pattern Agent Plugins, OpenAPI and JSON Schema use, under RFC-0003's semver rule | This review | Confirm the host, path, version line and `$id` rule |
| D4 | Do contracts move on disk? | No. The manifest separates them | Moving just the 8 core files breaks 553 path references in 188 files, and every GitHub link RFC-0003 made canonical | This review | Confirm no move |
| D5 | Does `catalogue-manifest.json` get a schema? | Yes: `contracts/catalogue-manifest.schema.json`, a member, matching what the verifier accepts | Adopters verify archives, and today the shape exists only in prose and in two verifier checks | This review | Confirm the new contract |
| D6 | Are spec pages generated or narrative? | A generated field table for every member, plus short narrative pages that link to fields and never define them | `contracts/` is normative (RFC-0076 D1). Kubernetes generates its reference the same way | This review | Confirm the split and its owner |
| D7 | How does CI prove the published spec equals the enforced one? | Four checks: manifest parity, `$id` version consistency, append-only immutable snapshots, and a gate at CLI release time | Every released CLI then carries exactly the member bytes the site publishes for the version it reports | This review | Confirm the four checks and the tag-time trigger |
| D8 | How does it roll out? | Correction entries at acceptance, then four slices, S1 to S4. Only S4 is one-way | Each slice ships alone, and the one-way step comes last | This review | Confirm the order |

## Problem & goals

### Diagnosis

The facts below are from revision `3cc898b9`, 2026-10-21.

- **There are 61 schemas in three folders, with no domain marking.**
  - 13 sit at the top level, mostly catalogue authoring.
  - 18 sit under `jsonschema/`, mostly work-loop, workspace and work-intake records, plus `agentbundle-show`.
  - 30 sit under `delivery/`, all delivery-engine records.
- **No schema has a real identity.** 32 use `$id`s on the reserved `agent-ready-repo.invalid` host and 16 on `agent-ready-repo.example`. The core catalogue schemas use a bare filename (`pack.schema.json`). `adapter.schema.json` has neither `$id` nor `$schema`.
- **Membership is positional, not declared.** `tools/catalogue/sync_contract_inventory.py` writes `public-contracts.txt` from every top-level `.json` and `.toml` file plus `jsonschema/knowledge-*.schema.json`. So the work-loop `knowledge-captured-observation` schema is in the CLI bundle, and a new top-level file joins it by being placed there.
- **Only one contract is versioned.** `adapter.toml` carries `[contract] version = "0.18"`. `agentbundle --version` prints it, as in `agentbundle 0.51.0 (spec 0.18)`. The catalogue set has no version.
- **The release archive manifest has no schema.** Adopters verify `catalogue-manifest.json`. Its shape lives only in [`catalogue-archive.md`](../guides/reference/catalogue-archive.md) and in the verifier's `CAT-V-ARC-011` and `CAT-V-ARC-019` checks (`catalogue_tooling/archive.py`).
- **A local contract copy can override the bundled one.** Two load paths read a catalogue-side file first. `packages/agentbundle/agentbundle/build/lint_packs.py` looks for `contracts/target-vocab.toml` in every ancestor directory before it reads the bundled copy. `packages/agentbundle/agentbundle/commands/pack_evals.py` loads `contracts/adapter.toml` from the catalogue root, which defaults to the working directory, with no bundled fallback. RFC-0076 D1 says catalogue-local copies "cannot override the running AgentBundle version". A planted file could loosen lint limits such as name patterns or length caps.
- **No site publishes a contract.** `web/` serves `/agent-ready-repo/` and `docs-site/` serves `/agent-ready-repo/docs/`. Neither has a contract page, so links fall back to GitHub file views. The Pages workflow does not run when `contracts/**` changes.

### Goals

- An adopter can find, read and pin the exact files a catalogue must satisfy, at a named version, from the website alone.
- A released schema URL keeps serving the same bytes forever.
- Every CLI release carries exactly the member files the site publishes for the version that CLI reports.
- `contracts/` stays the one authored source, as RFC-0076 D1 requires.

**Limit of the guarantee.** D7 proves the member *files* match. Some rules live only in code, such as the `CAT-V-ARC-*` verifier checks and the `JOURNEY.md` validator. Byte checks cannot cover those. The spec pages describe what those checks do, and D1 names the `JOURNEY.md` format as the first gap to close with a contract file.

### Non-goals

- **Moving the specification to a sibling repository or neutral organisation.** RFC-0003 reserved that for v1.0. D3 makes it unnecessary for stable URLs.
- **A custom domain.** D3 uses the existing host. A later domain is a new identity line, not a move (see Risks).
- **Converting schema dialects.** One member, `skill-manifest.schema.json`, uses draft-07. Changing a dialect is a contract change for its owning spec.
- **A portable conformance suite.** RFC-0003 § Conformance test suite still owns conformance.

## Proposal

### D1 — Membership, declared in one manifest

**Rule.** A contract is a member of the catalogue specification when it does one of three things:

1. It describes a source file a catalogue author writes, or a value such a file may hold.
2. It describes an adapter-neutral output that `agentbundle` gives adopters to consume, such as the catalogue index or the release archive manifest.
3. It is the adapter contract that RFC-0003 publishes and that packs declare a version of.

Three kinds of contract are not members. Contracts for files that exist only for one agent host's install route are *host projections*. Contracts that configure this project's own engine are *engine settings*. Contracts the CLI never applies to a catalogue's files are *other records*.

**Members in version 0.1.**

| Member | Clause | What an adopter uses it for |
| --- | --- | --- |
| `pack.schema.json` | 1 | `pack.toml`, including `[[pack.integrations]]` |
| `catalogue.schema.json` | 1 | `catalogue.toml` |
| `profile.schema.json` | 1 | profile TOML files |
| `skill.schema.json` | 1 | `SKILL.md` frontmatter and body |
| `skill-manifest.schema.json` | 1 | skill manifest files |
| `target-vocab.toml` | 1 | the adapter target names `pack.toml` may use |
| `catalogue-index.schema.json` | 2 | the `catalogue-index.json` that consumers read |
| `catalogue-manifest.schema.json` | 2 | the release archive manifest (new, D5) |
| `adapter.toml` | 3 | the adapter projection rules, with their own `[contract]` version |
| `adapter.schema.json` | 3 | the shape of `adapter.toml` |

**Edge cases.**

| Contract | Role | Rule applied |
| --- | --- | --- |
| `marketplace-entry.schema.json` | bundled | Host projection: the Claude marketplace entry. `catalogue verify` checks it, but only for the Claude plugin route |
| `plugin-manifest.schema.json`, `plugin-manifest.derived.schema.json` | bundled | Host projection: Claude `plugin.json` |
| `distribution-routes.toml` and its schema | bundled | Engine setting owned by RFC-0092 |
| `agent-plugin-extension-namespaces.toml` and its schema | bundled | Engine setting: this project's namespace allocations |
| `guide.schema.json` | bundled | Other record: only this repository's site tooling checks it (`tools/validate_guides.py`) |
| `jsonschema/knowledge-captured-observation.schema.json` | bundled | Other record: a work-loop record. Removing it from the bundle is its owner's call |
| `vendor/agent-plugins/1.0.0/*` | vendored | Upstream owns `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. The spec links there. A second copy under our host would give one schema two canonical homes |
| OKF schemas (`jsonschema/okf-*`) | not listed | Other record: knowledge projection (RFC-0087). Neither bundled nor published |
| All other `jsonschema/` and `delivery/` schemas | not listed | Other records: work-loop, workspace, work-intake and delivery |

**The `JOURNEY.md` gap.** The `JOURNEY.md` frontmatter format meets clause 1, and the CLI checks it (`catalogue_tooling/journey_validator.py`). It has no file under `contracts/`, and RFC-0076 D1 forbids a guide from being the normative source. So it is not a 0.1 member. The overview page links [`pack-journey-format.md`](../../guides/_shared/reference/pack-journey-format.md) as informative. A journey contract file under `contracts/` joins in a minor version.

**Manifest.** `contracts/catalogue-spec.toml` lists every bundled contract with one role: `member`, `bundled` or `vendored`. It also holds the append-only release table. Each release row records the version, its date, its adapter contract version, and a SHA-256 for every member file and every page source in its snapshot. A correction row names a released version and supersedes only that version's page-source digests. Three things read it:

- `sync_contract_inventory.py` writes `public-contracts.txt` from the `member` and `bundled` rows instead of from folder position.
- `check_contract_parity.py` requires every `member` and `bundled` row to have a byte-identical `_data/` copy.
- `tools/build-site.py` publishes only `member` rows, and links each `vendored` row to its upstream URL instead of publishing a copy. The `_data/vendor/` copies keep the identity check `test_distribution_route_contract.py` already runs.

The manifest itself stays in the repository and is not bundled. The CLI learns its specification version from its bundled member `$id`s (D3), so a release-table change never forces a package change. `contracts/README.md` groups its table by role from the same manifest.

### D2 — The home is a section of the docs site

The specification lives at `https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/`, inside the Starlight docs site.

- `tools/build-site.py` writes the pages into `docs-site/src/content/docs/spec/catalogue/` and the raw files into `docs-site/public/spec/catalogue/`. Both are generated and gitignored, as `docs-site/public/guides/` already is. Astro copies `public/` to the output under the docs base path, so the RFC-0089 D3 build order does not change.
- Starlight derives a page's route from its file path, and its default slugging is expected to drop the dot in `0.1` (not yet tested here). So each generated page sets an explicit `slug`, and a rendered-output check asserts that pages and raw files share the `<MAJOR.MINOR>/` path.
- `pages.yml` adds `contracts/**` to both its `push` and `pull_request` path filters. It already covers `docs-site/**`. So a pull request touching the specification runs the site build and its rendered-output checks before merge, and a merge redeploys the site.
- Narrative page sources are authored in `docs-site/spec-src/catalogue/`, outside the generated content folder. Neither that folder nor `contracts/` is in `packages/`, so a change there needs no package version bump.
- Build a Catalogue keeps its "Contract and schema reference" entry (RFC-0076 D9). S3 points the entry at `/docs/spec/catalogue/draft/`. S4, which creates `latest/`, repoints it there.
- Wave 6 is not reopened. It keeps its routes, its pages and RFC-0076 OQ4. If Wave 6 has shipped its own field-reference pages by S3, they stay where they are, and the spec pages link to them. Merging the two is Wave 6's choice.
- The marketing site stays free of schema pages (RFC-0076 D10). The `/evaluate/` page's open-formats and versioned-contracts claims link to the spec section instead of the `contracts/` folder.

### D3 — URL, version and `$id` schemes

**Host.** The existing site host, `eugenelim.github.io/agent-ready-repo`. The owner named it. It costs nothing, and it is the address adopters already reach.

**Paths.**

| Path under `/agent-ready-repo/docs/spec/catalogue/` | What it serves | Changes? |
| --- | --- | --- |
| `<MAJOR.MINOR>/` | Overview and member pages for one release, built from its snapshot | Content changes only through a correction row (D7). Layout and styling follow the live generator and site |
| `<MAJOR.MINOR>/<file>` | The exact released bytes, for example `0.1/pack.schema.json` | Never |
| `latest/` | Redirect pages to the newest release, and copies of its files | Moves on each release |
| `draft/` | Pages and files built from `contracts/` on `main` | Every merge |
| `index` | The version list with each version's date, adapter contract version, and a SHA-256 for every released file. Served from S3 on, with zero releases until S4 | Each release |

GitHub Pages serves static files and has no redirect setting, so a `latest/` JSON file is a byte copy whose `$id` names the versioned path. Tools pin the versioned path.

**Version line.** The set carries a semver `MAJOR.MINOR` version, starting at `0.1`. Members still change from wave to wave, and RFC-0003 reserves `1.0` for a stable contract. RFC-0003 § Spec versioning applies to the set as written for the adapter contract: `0.x` while breaking changes are expected, `1.0` when stable, and the same compatibility rules for readers.

- A compatible member change is a minor version. A breaking one is a major version, or a minor version while in `0.x`.
- There is no patch number. OpenAPI and CloudEvents keep the patch out of what tools match on for the same reason.
- `adapter.toml` keeps its own `[contract]` version on its own line. Packs keep declaring it in `[pack.adapter-contract]`. Each release row records which adapter contract version the release contains.
- The CLI version (agentbundle 0.53.1 on `main` at 2026-10-21) stays independent. Each CLI release adds the catalogue specification version to `agentbundle --version` and `agentbundle catalogue contracts list`. It reads that version from its bundled member `$id`s.

**`$id` rule.** Each member JSON Schema carries `"$id": "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/<MAJOR.MINOR>/<file>"` and a `$schema` keyword. `adapter.schema.json` gains both.

- In `contracts/`, all member `$id`s name one version. After a release, the first change to any member rewrites every member `$id` to the next version. A tool does the rewrite, and check 2 enforces it.
- An unreleased version's `$id` is a working name, not a promise. JSON Schema § 8.2.1 calls an `$id` "an identifier and not necessarily a network locator". No public URL serves a file under that name before release. The `draft/` copies are rewritten to `$id`s under `draft/`, so draft bytes never claim a future release's identity.
- A released `$id` never changes. A later version mints a new one. Moving from today's bare filenames to absolute `$id`s happens once, at the first release (S4).
- The CLI keeps loading schemas from `_data/` and fetches nothing. No member uses a cross-file `$ref`, so no current resolution path reads a member `$id`.

### D4 — No move on disk

Contracts stay where they are, and the D1 manifest does the separating.

A move to a folder such as `contracts/catalogue/` would:

- break 553 path references in 188 files at `3cc898b9`. The count is `git grep -E -o 'contracts/(pack|catalogue|profile|skill|skill-manifest|catalogue-index|adapter)\.schema\.json|contracts/adapter\.toml'`, which covers only the 8 core files;
- change the `_data/` copy paths, the parity gate and the inventory rule;
- break the `contracts/REGISTRY.md` back-pointers and the spec `Contract:` headers that `lint-spec-status.py` reads;
- break every `github.com/.../blob/main/contracts/...` link that RFC-0003 made canonical for v0.x.

Those links are public, so the move is a one-way door that buys only a folder name. The manifest gives adopters the separation, and the site gives them the address.

### D5 — A schema for `catalogue-manifest.json`

Add `contracts/catalogue-manifest.schema.json` as a member. It states exactly what the verifier accepts today, no more and no less.

- **From `CAT-V-ARC-011`:** `schema` is 1 or 2. `bundle`, `release` and `generated_at` are required strings. `files` and `packs` are required lists.
- **From `CAT-V-ARC-019`:** `files[]` items are `{path, sha256}` strings. `packs[]` items carry string `name` and `version`, with optional `path` and `digest`. `profiles[]` items are name strings or objects with a string `name`, and an object with a `digest` must have a `path`.
- **Proof both ways.** A contract test proves that every manifest `catalogue package` writes passes the schema, and that a schema-1 manifest and the older `packs[]` and `profiles[]` shapes pass too. A second test proves that each `CAT-V-ARC-011` and `CAT-V-ARC-019` failure case fails the schema.
- **What it proves.** The schema checks shape only. Nothing in the archive format proves who published an archive. The SHA-256 sidecar travels with the archive, so it proves only that the bytes arrived intact. The channel descriptor is unsigned and never reaches the disconnected host. Authenticity needs the sidecar, or a signature, obtained through a separate authenticated channel. This RFC adds neither. A schema-valid manifest is not evidence of origin.

### D6 — Generated field tables, short narrative pages

This RFC owns the spec pages and their generator, delivered in S3.

- **Generated.** Every member JSON Schema gets a page with a field table built from `type`, `required`, `enum`, `pattern`, `default` and `description`, plus a link to the raw file. The table repeats the schema and adds no meaning, so it needs no quality cut. TOML members get a generated page that renders the file and links its schema.
- **Narrative.** One overview page per version states what a catalogue must contain, how to validate it (`agentbundle catalogue lint`, `verify` and `package`), what the code-only checks do, and what changed since the previous version. Each member page may add a short block for purpose and examples. Narrative links to fields and never defines one. This applies RFC-0076 D1's rule that guides "do not define undocumented schema fields".
- **Wave 6.** RFC-0076 OQ4 still decides which `pack.toml` and `skill.schema.json` fields Wave 6 explains in its own narrative. Wave 6 may meet D9's field-reference line by linking to these pages.
- **Worked example.** The overview links the starter catalogue that `agentbundle catalogue init` writes (`_data/catalogue-scaffold/`). It is a catalogue the CLI accepts at that version.

### D7 — Drift checks

Four checks keep `contracts/`, the site and released CLIs in step. Checks 1 and 2, and the tree half of check 3, run in the build-check chain on every pull request. The rendered half of check 3 runs in `pages.yml`, on pull requests and in the deploy build. Check 4 runs in the tag-push run of `release-agentbundle.yml`, in a job that every publish job (`publish-pypi` and `publish-artifactory`) depends on.

1. **Manifest parity.** The existing parity gate reads the D1 manifest. Every `member` and `bundled` row has a byte-identical `_data/` copy, `public-contracts.txt` equals those rows, and no top-level contract except the manifest itself is left without a row.
2. **Version consistency.** All member `$id`s name one version, V. If member bytes equal the latest snapshot, V is the latest release. If they differ, V is the next version and has no snapshot yet. The tool that fixes a failure is named in the error.
3. **Append-only, immutable snapshots, anchored outside the commit.** Each release is committed under `contracts/releases/catalogue/<MAJOR.MINOR>/`. That path is outside the inventory's folder scope and outside the package. A snapshot holds the member files and a copy of the narrative page sources from `docs-site/spec-src/catalogue/` for that version. Released pages therefore rebuild from frozen content. The live generator and Starlight may still change their layout and styling, which is allowed; they may not change the words or the raw files.
   - The original release row records a SHA-256 for every member file. A later correction row may supersede page-source digests only, never a member digest. Every build checks member files against the original row, whatever corrections exist.
   - A check inside one commit cannot catch an edit that changes a file and its digest together. So the reference is something the pushed commit cannot rewrite. Pull-request runs use the base commit's release table and snapshots. S1's manifest starts with an empty release table, so every base commit has one. Push and `workflow_dispatch` runs on `main` use the currently deployed `index`, checked in the Pages build job before `upload-pages-artifact`. Every released row, path and member digest in the reference must still exist unchanged. Deleting or editing a row, deleting a snapshot, or dropping a released path from the built site fails against that reference, even when the pushed tree is consistent with itself.
   - The check fails closed. S3 deploys an `index` that lists zero releases, so from S3 on the deployed `index` always exists. A missing, unfetchable or 404 `index` fails the deploy. A deployed `index` with zero releases is the only "nothing released yet" state. It admits S4's first deploy, and any retry of it, because the anchor changes only when a deploy succeeds. A dispatch on any other ref skips this half, because it cannot deploy. The Pages deploy runs on any push to `main` without the build-check chain, so this check must live in the Pages job itself.
   - A rendered-output check fails if the built site lacks any released path or serves member bytes that differ from the original row.
   - An editorial fix to a released page edits that snapshot's page sources and appends a correction row with their new digests and a note. For each version, the newest correction row governs page-source digests, and the original row always governs member digests. "Latest release" means the highest version number with a release row. Correction rows never change it.
4. **Release gate.** At a CLI release, the gate reads V from the bundled member `$id`s. It fails unless the tagged commit holds a snapshot and a release row for V, the bundled member bytes equal that snapshot, and the deployed `index` already lists V with the same member digests. So a CLI never ships while the site fails to serve its version.

**How a release flows.**

1. Contract pull requests change members on `main`. With the first such change, the rewrite tool moves every member `$id` to the next version, V, and check 2 verifies it. `draft/` shows the result.
2. When V is ready, a release pull request adds the snapshot and the release row. It touches `contracts/` and `docs-site/spec-src/` only, so it needs no package version bump.
3. The merge runs `pages.yml`. Once its deploy job succeeds, the deployed `index` lists V.
4. A maintainer then pushes the `agentbundle-v*` tag, which passes check 4. A tag pushed before that deploy finishes fails check 4, safely.

A tag cut while `main` still has unreleased member changes fails check 4. That stops a CLI from shipping rules the site does not publish.

### D8 — Rollout

**At acceptance.** The acceptance pull request records this RFC's corrections in RFC-0003 and RFC-0076, as listed below. So no accepted body reads as current authority after a slice has changed it.

Each slice after that is one spec under `work-loop`. Only S4 is a one-way door.

| Slice | Delivers | Door | Unblocks |
| --- | --- | --- | --- |
| S1 | The D1 manifest, the inventory and parity from it, `contracts/README.md` grouped by role, and bundled-first loading for every contract load path (see below) | two-way | S2, S3 |
| S2 | `catalogue-manifest.schema.json`, its two contract tests, and the provenance correction in `catalogue-archive.md` (D5) | two-way (a new file) | S3 |
| S3 | The docs-site section at `draft/`, with generated and narrative pages, the build-site change, `contracts/**` added to both `pages.yml` path filters, explicit slugs, an `index` listing zero releases, and the Build a Catalogue link to `draft/` (D2, D6) | two-way | S4 |
| S4 | Release 0.1: absolute `$id`s, the first snapshot and release row, `latest/` and the repointed Build a Catalogue link, checks 2 to 4, and the CLI version report (D3, D7) | **one-way** | Wave 7 links |

**S1's load-path rule.** S1 lists every place `agentbundle` loads a contract, including `build/lint_packs.py` and `commands/pack_evals.py`. Each loads the bundled `_data/` copy. Reading `contracts/` from a source tree is allowed only when this repository's own build says so through a signal the catalogue tree cannot supply, such as the running package resolving to an editable checkout of this repository. A file inside the catalogue never counts as that signal.

S1, S2 and S4 change `packages/agentbundle/`. Each updates both `version.py` and `pyproject.toml`, as [`packages/AGENTS.md`](../../packages/AGENTS.md) requires. Each also carries an `Engine-Change-RFC: RFC-0109` commit trailer, which the engine-change gate in [`tools/AGENTS.md`](../../tools/AGENTS.md) requires.

### What this RFC amends

The acceptance pull request appends one entry to each RFC below. Their bodies are not edited.

- RFC-0076 has no correction section, so it gains `## Errata`.
- RFC-0003 already has a `## Amendments` section from before RFC-0055. RFC-0055 says Errata and Amendments never coexist, and its D5 leaves old sections as they are. So the entry is appended under RFC-0003's existing `## Amendments` heading.

**RFC-0003.**

- **§ The published spec**, "Working assumption: **option 1 for v0.x; promote to option 2 at v1.0**" (line 101). Superseded. The canonical home is the website path in D3. The GitHub file path stays the authored source but is no longer the canonical address. A sibling repository would not change the URLs, so the move at v1.0 is no longer assumed.
- **§ Unresolved questions**, item 1, "Spec hosting at v1.0" (line 397). Closed by D2 and D3.
- **§ Spec versioning** (heading at line 269). Extended. The semver rules now also govern the catalogue specification as a set. `adapter.toml`'s version continues as a member's own version. The rule that "the CLI's `--version` output names the spec version" now also covers the catalogue specification version.
- **§ Follow-on artifacts**, F-spec-publish (line 429). Partly superseded. Nothing moves, and D6's overview page replaces the `SPEC.md` overview. The licence choice that F-spec-publish leaves to the spec author is unchanged.

**RFC-0076.**

- **D1** authority model. Extended. Released `<MAJOR.MINOR>/<file>` paths and their `latest/` copies are byte projections of the member files, one tier below `contracts/` and beside `_data/`. `draft/` files are derived projections whose `$id`s are rewritten. Spec pages are guides under D1's existing rules. D1's rule against catalogue-local overrides now has a check in S1.
- **D9**, "Contract and schema reference (generated from contracts/ — Wave 6)" (line 492). Amended. The entry points at the published specification. Wave 6 keeps its other routes and OQ4.
- **D10**, "Versioned contracts (contracts/ directory, RFC-0003 standard)" (line 515) and "Links to technical evidence (docs-site, contracts/, agentbundle PyPI)" (line 522). Amended. Both link to the published specification instead of the `contracts/` folder.
- **D10**, "Do not turn the marketing site into raw schema documentation" (line 524). Unchanged and reaffirmed.
- **D10**, "Release integrity (mutation refusal, content digests — Wave 8, after D8 ships)" (line 520). Corrected, not amended. D8 shipped as Wave 5 on 2026-10-21 (PR #1587, agentbundle 0.53.0).

## Options considered

### Home (D2), along the axis "which surface serves it"

| Option | For | Against |
| --- | --- | --- |
| Do nothing: GitHub file paths stay canonical | No work | The intent's outcome fails. Nothing is versioned, and file views are not schema URLs |
| **Docs-site section** | Owns technical reference already. One build. MCP and Kubernetes do this | Spec and guides share a sidebar, so the IA needs care |
| Marketing site | One fewer hop from `/evaluate/` | RFC-0076 D10 forbids it, and the audiences differ |
| Dedicated spec site or sibling repository | Cleanest separation, the OpenAPI and Agent Plugins model | A second site, deploy and repository with one implementer. RFC-0003 already judged this premature |

### `$id` and version scheme (D3), along the axis "what a version names"

| Option | For | Against |
| --- | --- | --- |
| Do nothing: keep bare filenames | No churn | Not absolute, as the JSON Schema guidance recommends. Nothing to pin |
| **One version per set, all files under it** | One mental model, the Agent Plugins and JSON Schema shape | Every release rewrites every member `$id` |
| One version per schema, with a set manifest | Unchanged schemas keep their `$id` | Adopters must map set versions to schema versions. More paths |
| Date versions (`2026-10-21`), the MCP shape | Avoids confusion with adapter `0.18` and CLI `0.53` | RFC-0003 already chose semver for contracts, and this would split the rule |

A rewrite on each release is mechanical and checked. It costs less than a mapping every adopter must learn.

### Separation (D4)

The manifest dominates a move. Both separate the files, but only the move breaks public links. Do-nothing leaves membership positional, which is how `knowledge-captured-observation` reached the bundle.

## Trust analysis

- **Who can change what adopters fetch.** Anyone who can push to `main` redeploys the site, because `pages.yml` deploys on push without the build-check chain, and `main`'s branch protection does not bind administrators. Check 3 runs inside the Pages job against the deployed `index`, so a push that rewrites an already-deployed released file or digest fails the deploy. Two gaps remain. A version merged but not yet deployed is unprotected until its deploy lands, because a later push is checked against the older anchor. And `pages.yml` lives in the repository, so any `main` writer can change or skip check 3. Released bytes are therefore only as safe as write access to `main`. A push can also change `latest/` and `draft/`.
- **How adopters protect themselves.** The 0.1 overview tells adopters to:
  - pin a versioned URL, never `latest/` or `draft/`;
  - record each file's digest once, in their own repository, and never re-fetch the digest from the site, because the `index` comes from the same deploy as the files;
  - cross-check a digest against a source the site cannot change: the `_data/` copy inside the matching PyPI wheel, or the snapshot at the matching `agentbundle-v*` tag;
  - or vendor the file.
- **What the CLI trusts.** Nothing from the site. It reads `_data/` only and fetches no schema, so a tampered site cannot change what a CLI enforces.
- **Review.** A spec-stage security-reviewer pass ran on 2026-10-21. Its controls are in this section, D5, D7 check 3 and S1's load-path rule.
- **Archive verification.** D5 adds a schema and changes no verifier behaviour. Nothing in the archive format proves the publisher (D5). The guide that currently calls the sidecar and descriptor "the provenance evidence" is corrected in S2.

## Risks & what would make this wrong

- **The `github.io` host stops serving the URLs.** A repository rename, a move to an organisation, or a custom domain would change the address. The GitHub Pages docs fetched for the survey say a user site's custom domain covers its project sites. They do not say old `github.io` paths redirect. *Mitigation:* released `$id`s stay valid as identifiers either way, and adopters who pin digests or vendor files are unaffected. A new host would start a new `$id` line at the next version. *Wrong if* the owner expects a rename or domain move within a year. Then S4 should wait for it.
- **An adopter tool registered schemas by their bare-filename `$id`.** It would stop matching after S4. *Mitigation:* no member uses a cross-file `$ref`, no schema resolution path in the CLI reads `$id`, and the 0.1 overview names the change. *Falsified if* an adopter reports a broken `$ref`.
- **The tag gate blocks an urgent CLI fix.** A fix tagged while `main` holds unreleased member changes fails check 4. *Mitigation:* if the unreleased member changes are ready, cut the specification release first, in one pull request. If they are not ready, revert them on `main`, tag, and re-land them after. A version is never minted only to unblock a tag. *Wrong if* this blocks a CLI release more than once a quarter.
- **The membership line leaves out something the CLI checks.** Adopters would then fall back to `contracts/`, which is the intent's riskiest assumption. *Mitigation:* the validation below.
- **Generated pages read as thin.** Schema descriptions vary in quality. *Mitigation:* D6's narrative blocks.

## Evidence & prior art

The [survey](../product/research/catalogue-spec-publication-survey.md) covers ten platforms. The findings this RFC relies on:

- **Website, not file view** (finding 1, high). Nine of the ten surveyed platforms publish on a site they control, and CloudEvents publishes from GitHub release tags. MCP and Kubernetes do it inside their docs site. Basis for D2.
- **Immutable versioned paths, and `latest` as a human alias** (finding 2, high). MCP, Agent Plugins, OpenAPI and JSON Schema give each version its own path. JSON-Schema-Test-Suite and mike make `latest` a link. Basis for D3's path table.
- **Semver and date versions are both common** (finding 2, high). OpenAPI, Agent Plugins and CloudEvents use semver. MCP and JSON Schema use dates. D3 follows RFC-0003's existing semver choice.
- **No patch in what tools match** (finding 2, high). From OpenAPI and CloudEvents. Basis for `MAJOR.MINOR`.
- **`$id` is an identifier, absolute, and equal to the served URL where one is served** (finding 3, high). From JSON Schema core § 8.2.1 and § 8.2.3, Agent Plugins, and OpenAPI. Basis for the `$id` rule. The working-name rule for unreleased `$id`s rests on § 8.2.1 alone.
- **A published URL is permanent, and a new identity is minted rather than an old one moved** (finding 4, moderate). From SchemaStore, OpenAPI and Kubernetes. Basis for "a released `$id` never changes" and D4.
- **The spec version is independent of the implementation version** (finding 5, high). From MCP, CloudEvents, Dev Containers and Kubernetes. Basis for D3's three version lines.
- **Generated field reference plus narrative** (finding 6, moderate). From Kubernetes. Basis for D6. OpenAPI makes prose authoritative instead. This repository chose the schema side in RFC-0076 D1.
- **Keep few versions, and never touch a released one** (finding 8, moderate). From Docusaurus, mike and Kubernetes. Basis for cutting a version only when members change.

## Experiment / validation

- **Hypothesis.** An adopter can build and validate a catalogue from the published 0.1 specification without opening `contracts/`.
- **Measure.** After S3, one maintainer works from `draft/` alone. They scaffold a catalogue, add one pack, one skill and one profile, then run `agentbundle catalogue lint`, `verify` and `package`. They record each time they needed a file or rule that was not on the site.
- **Success.** Zero lookups outside the site, and every CLI error names a rule the site shows.
- **Failure.** Any lookup outside the site. Each one adds a member or a narrative block before S4. Two or more missing members reopen the D1 rule.
- **Mechanical proof.** A test runs every command that loads a contract, including `lint`, `verify`, `package`, `index` and pack evals, on the starter catalogue, and records every contract file the CLI loads. Each file must be a `member`, or appear in a fixed exclusion list where each entry names one of D1's three exclusion classes. Adding an exclusion needs a spec that cites D1. The test also fails if the CLI loads any contract from outside `_data/` when run outside this repository.

## Open questions

- **OQ1 — Where the spec section sits in the docs sidebar.** Should it be a sidebar tab of its own, or only an entry inside Build a Catalogue? **Recommended default:** an entry inside Build a Catalogue, with no new tab, so the stage rail in `docs-site/src/components/rail.ts` is untouched. Owner: eugenelim, who owns both the Wave 6 intent and this one. Decide by: approval of the S3 spec.

## Follow-on artifacts

- **Corrections:** the entries in § What this RFC amends, recorded in the acceptance pull request.
- **Specs:** one per slice, S1 to S4, under `docs/specs/`. Each names this RFC as its governance basis.
- **Intent updates:** `catalogue-specification-publication` records this RFC as its governing decision. `catalogue-wave7-marketing-evaluator` points its specification links at S4's URLs.
- **Guide:** S3's overview page is the adopter guide. No separate guide is needed.

## Acceptance criteria (for this RFC)

- [x] D1 to D8 reviewed and accepted by the Approver (2026-10-21).
- [x] The correction entries for RFC-0003 and RFC-0076 land in the acceptance pull request.
- [ ] OQ1 settled in the S3 spec.
- [ ] The S3 validation run is recorded with zero lookups outside the site, or the gaps are fixed before S4.

## Errata

- **2026-10-21, eugenelim (Approver) — S2 tightens one verifier check.** The verifier accepted any value Python treats as equal to 1 or 2 for the archive manifest's `schema` field, including the boolean `true`. The Approver chose not to publish a schema that admits a boolean there. `catalogue verify` now also rejects a boolean `schema` with CAT-V-ARC-011, and keeps accepting integer-valued numbers such as `1.0`, which draft 2020-12 treats as integers. The schema in D5 therefore states what the verifier accepts after this one change. This supersedes "states exactly what the verifier accepts today" in D5 and "D5 adds a schema and changes no verifier behaviour" in § Trust analysis, for that field only. Recorded in [`catalogue-manifest-schema`](../specs/catalogue-manifest-schema/spec.md).

- **2026-10-22, eugenelim (Approver) — OQ1 is settled, and the S3 validation run is withdrawn.** [`catalogue-spec-site`](../specs/catalogue-spec-site/spec.md) settles OQ1 with the default placement: an entry inside Build a Catalogue's "Contract and schema reference" group, with no new tab and `docs-site/src/components/rail.ts` untouched. The Approver withdrew the S3 validation run, so no maintainer walkthrough of `draft/` is run or recorded. S1's load-inventory roster test, `tests/roster/test_catalogue_spec_contract_loads.py`, stays as the mechanical proof. This supersedes four passages. First, the Risks mitigation "the validation below" (line 323). Second, § Experiment / validation (lines 340–345: Hypothesis, Measure, Success and Failure), which no longer applies. Its Mechanical proof bullet (line 346) stands, because S1 delivered it. Third and fourth, acceptance criteria items 3 and 4 (lines 363–364): item 3 is met by the S3 spec, and item 4 is withdrawn along with the run.
