---
slug: catalogue-spec-site
title: "The catalogue specification on the docs site, at draft/ (RFC-0109 S3)"
status: Shipped
---

# Spec: The catalogue specification on the docs site, at draft/

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) D2, D3 (`draft/` path and `$id` rule), D6, D8 slice S3, OQ1, and its [errata](../../rfc/0109-catalogue-specification-publication.md#errata)
- **Contract:** none
- **Shape:** ui
- **Depends on:** spec:catalogue-manifest-schema

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

**Mode:** full. It adds a public site section and changes the docs build and the Pages workflow.

## Outcome

Adopters can read the catalogue specification on the docs site: one page per
member contract with its field table or rendered file, the raw file beside it,
and a short overview of what a catalogue must contain and how to check it. The
section shows the live `main` state at `/docs/spec/catalogue/draft/` and lists
no released versions yet.

## What Changes

- A generator writes the specification pages and raw files from the member rows of `contracts/catalogue-spec.toml` — `tools/catalogue_spec_site.py`, called by `tools/build-site.py`
- Narrative sources for the overview and member blocks — `docs-site/spec-src/catalogue/`
- A version index listing zero releases — page at `/docs/spec/catalogue/`, data at `/docs/spec/catalogue/index.json`
- The Build a Catalogue tab's "Contract and schema reference" group gains a first entry pointing at the draft section (RFC-0109 OQ1)
- `pages.yml` runs on `contracts/**` changes; a rendered-output check covers the section
- An RFC-0109 errata entry records the Approver's withdrawal of the S3 validation run

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Adopters read the specification here | the generated section; `docs-site/spec-src/catalogue/` | eugenelim | Rendered-output check green | Every member has a page and a raw file at `draft/` |
| Maintainer procedure | Maintainers must know where the pages come from | `docs-site/AGENTS.md` | eugenelim | Updated generated-content note | Note names the generator and `spec-src/` |
| Decision rationale | OQ1 and the withdrawn validation run | RFC-0109 `## Errata` | eugenelim | Errata entry | Entry present |

## Agent Rules

### Always do

- Generate the section from the manifest's `member` rows only. A member row added later must appear without a code change.
- Set an explicit `slug` on every generated page.
- Rewrite each draft JSON file's `$id` to `https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/draft/<file>`, and change no other byte. Copy TOML members byte for byte.
- Keep narrative text to purpose and links. Narrative never defines or restates a field; the generated table does.
- Keep generated outputs out of git, and honour `build-site.py --dry-run` and `--clean`.

### Ask first

- Adding a top-level docs tab, or changing `docs-site/src/components/rail.ts`.
- Moving or removing Wave 6's `reference/pack-toml` or `reference/skill-frontmatter` pages.

### Never do

- Publish a versioned path (`/docs/spec/catalogue/<MAJOR.MINOR>/`), a `latest/` path, or a release row. Those belong to S4.
- Change a contract file's bytes in `contracts/`.
- Add a third-party dependency or a new top-level directory.
- Publish a copy of a `vendored` or `bundled` row.

## Testing Strategy

- Generator behaviour (member set, slugs, `$id` rewrite, TOML rendering, index content, dry-run, clean): **TDD** in `tools/test_catalogue_spec_site.py`, against a fixture manifest and the real one.
- Navigation entry: **TDD** by extending `tools/test_build_a_catalogue_nav.py`.
- Workflow triggers: **TDD** by extending `tools/test-pages-workflow.py`'s required paths.
- The built site: **goal-based**, exercised by an **integration** check in `web/src/test/rendered-output.test.ts` against the real Astro build in `pages.yml`, and by `tools/check-rendered-site-links.py`.

## Acceptance Criteria

- [x] After `python tools/build-site.py`, every `member` row of `contracts/catalogue-spec.toml` has exactly one page source under `docs-site/src/content/docs/spec/catalogue/draft/` and one raw file at `docs-site/public/spec/catalogue/draft/<file name>`. No `bundled` or `vendored` row has either.
- [x] Each generated page source sets a `slug` of `spec/catalogue/draft/<page name>`, where the page name is the file name with dots replaced by hyphens, so no page route equals a raw file path.
- [x] Each draft JSON raw file is byte-identical to its `contracts/` source except for one span: the value of the existing top-level `"$id"` member is replaced by `https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/draft/<file name>`. A member without a top-level `$id` gains the line `  "$id": "<that URL>",` directly after its opening `{` line, and no other byte changes. Each TOML raw file is byte-identical to its source.
- [x] Each JSON member page carries the field table `tools/schema_field_reference.py` produces for that schema, and its narrative reference link, which the table's conditional-rules marker points at, targets the member's raw file. Each TOML member page shows the file's contents and links its raw file, and `adapter.toml`'s page links the `adapter.schema.json` page.
- [x] The `pack.schema.json` and `skill.schema.json` member pages link Wave 6's `reference/pack-toml` and `reference/skill-frontmatter` pages, which remain unchanged.
- [x] The draft overview page lists every member with its page and raw-file link; names `agentbundle catalogue lint`, `verify` and `package` as the checks; says which checks live only in code, naming the `CAT-V-ARC-*` archive checks and the `JOURNEY.md` validator; links the `JOURNEY.md` format guide as informative; links the starter catalogue `agentbundle catalogue init` writes; and states that `draft/` changes with every merge and is not a release.
- [x] `/docs/spec/catalogue/` lists zero released versions and links `draft/`. `/docs/spec/catalogue/index.json` is `{"releases": []}`.
- [x] Build a Catalogue's "Contract and schema reference" group lists "Catalogue specification (draft)" first, linking `spec/catalogue/draft`, and keeps its three existing entries. The tab set and `rail.ts` are unchanged.
- [x] `pages.yml` lists `contracts/**` and every new generator source in both its `push` and `pull_request` path filters, and `tools/test-pages-workflow.py` requires them.
- [x] A rendered-output check over the real build fails unless every member's page and raw file are served under `/agent-ready-repo/docs/spec/catalogue/draft/`, and every draft JSON raw file's `$id` names its own served URL.
- [x] `python tools/build-site.py --clean` deletes both generated spec trees before its pass regenerates them, so a stale file planted in either tree is gone afterwards and the section is present again. `--dry-run` writes nothing.
- [x] RFC-0109 gains an errata entry recording OQ1 as settled by this spec and the Approver's withdrawal of the S3 validation run.

## Follow-ons

- eugenelim: RFC-0109 S4 — release 0.1, absolute `$id`s, `latest/`, and drift checks 2–4.

## Assumptions

- Technical: Starlight's default slugging of dotted path segments is untested here — it would change only whether explicit slugs are needed, and they are set regardless (settled by: the first real build).
