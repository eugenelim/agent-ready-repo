# Correct frozen records through a licensed errata mechanism

- **Status:** Draft
- **Level:** feature

## Outcome

Maintainers can add dated, additive corrections to frozen ADRs and related frozen records without rewriting historical bodies.

## Opportunity

The repository freezes ADR bodies and only licenses `## Errata` for RFCs, leaving known false references and discharged-deferral pointers without a permitted correction shape.

## What this absorbs

### adr-errata-convention

- **Authority:** [spec/pack-test-boundary-remaining-packs](../../specs/pack-test-boundary-remaining-packs/spec.md)
- ADRs have no errata mechanism. `docs/CONVENTIONS.md` freezes the body, and the shipped `new-adr` template says only the Status line moves, while `## Errata` is RFC-scoped in `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`.
- ADR-0071 names deleted `packs/core/tests/pack/test-runtime-boundary.py` at line 74 and says a migration is partial when it is complete. Two other frozen records have the same staleness.
- Extend the errata convention to ADRs by amending `new-adr`'s `SKILL.md` and template plus `docs/CONVENTIONS.md`, bumping governance-extras, and filing the ADR-0071 erratum.
- This is a governance change and needs its own PR.
- **Unblocks when:** picked up.

### distribution-adapters-lifecycle-class

- **Authority:** [spec/frozen-doc-supersession-annotations](../../specs/frozen-doc-supersession-annotations/spec.md)
- `docs/specs/distribution-adapters/spec.md` is now explicitly `Shipped` with a Status-line supersession annotation. Commit `5fd1b93b2` (`docs(specs): annotate the frozen documents that relied on a superseded decision (#987)`) made that annotation.
- The original premise that its lifecycle remains undecided is stale. The document remains demonstrably maintained because adapter PRs amend its Changelog and projection table.

### pack-js-ci-workflow

- **Authority:** [spec/pack-test-boundary-remaining-packs](../../specs/pack-test-boundary-remaining-packs/spec.md)
- **Authority:** [ADR-0083](../../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md)
- SECOND CONCRETE INSTANCE, 2026-08-18 (`spec/npm-dependabot-wiring`): ADR-0083's comparison table at line 72 and deferred-items list at line 201 name `npm-dependabot-wiring` as deferred to the repo owner. That item shipped and its `[backlog].open` entry was deleted, so both references resolve to nothing.
- `docs/specs/npm-sca-gate/spec.md` at lines 203 and 263 carries the same two references and is frozen. Unlike ADR-0071's deleted-file falsehood, these record a resolved deferral that was true at the time; decide whether discharged deferrals need annotation or only false claims do. Either pointer update is cheap once a licensed shape exists.
- No CI covers JavaScript living in a pack. `web/` and `docs-site/` are covered by `pages.yml` and `pack-evals.yml`, which run npm and ship committed lockfiles. `packs/converters/.apm/skills/render-proof/` and `packs/converters/.apm/skills/markdown-to-html/` each have dependencies, no lockfile, and no workflow.
- The three suites under `packs/converters/tests/skills/render-proof/` have never run in CI. All three pass locally after `npm install` in the skill. `security.test.js` covers `validateInputPath` and `validateOutputPath` path confinement, which nothing else asserts.
- Deliver a pack-skills JavaScript workflow with setup-node, `npm ci` per skill `package.json`, and the suites; committed lockfiles for both skills; and `npm audit`. Neither package has a supply-chain gate today. `render-proof` declares nine floating-caret dependencies, including `dompurify`, which its sanitizer assertions test.
- Remove the two render-proof entries from `_NO_RUNNER` in `tools/lint-pack-test-boundary.py`; the lint intentionally fails on a stale exemption.
- agentbundle 0.29.5 already fixed packaging: both archive flavours prune `node_modules` and cache directories, and `catalogue package` no longer aborts on real `node_modules` whose `.bin/` contains symlinks. The cost remains: integration tests `shutil.copytree` the whole `packs/` tree into temporary directories, so about 10k installed files still slow that suite by an order of magnitude. Scope installs to a CI job that does not run those tests, or make `copytree` prune too.
- **Unblocks when:** picked up; read this record first.

## Assumptions

- The lifecycle premise changed: `distribution-adapters` is explicitly Shipped with a Status-line annotation, not undecided.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
