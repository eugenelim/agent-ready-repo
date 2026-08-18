# Spec: Catalogue CI — Documentation Integration

- **Status:** Shipped
- **RFC:** ini-006 M2b
- **Author:** eugenelim

## Mode

Full — two risk triggers:

1. **Structural change** — new guide at `guides/_shared/how-to/create-external-catalogue.md`
   (new file in the adopter-facing guide tree).
2. **Public interface change** — `packages/agentbundle/README.md` is the PyPI README; any
   change to it is visible to every pip user of the package.

## Objective

The Catalogue CI Contract guide shipped in PR #794 at
`guides/_shared/reference/catalogue-ci-contract.md`. The surfaces that existed before that
PR — the curation pack guides, the enterprise distribution how-to, the top-level guides
index, and the PyPI README — don't reference it. Curation pack users (the primary external
catalogue audience) have no path from their existing entry points to CI guidance.

This spec stitches the contract guide into those surfaces, adds the missing adopter-facing
how-to for creating an external catalogue, and fixes a deprecated command in the PyPI README.

## Acceptance Criteria

- [x] AC1: `guides/README.md` includes the Catalogue CI Contract in the Shared guides
  reference list.

- [x] AC2: `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md` See also
  section links to the Catalogue CI Contract.

- [x] AC3: `guides/catalogue-curation/explanation/catalogue-operator-journey.md` publish
  section links to the Catalogue CI Contract.

- [x] AC4: `guides/catalogue-curation/README.md` links to the Catalogue CI Contract.

- [x] AC5: `packages/agentbundle/README.md` (PyPI README) no longer references
  `agentbundle package-catalogue` in the enterprise distribution section (deprecated command
  replaced with `agentbundle catalogue package --root … --bundle … --release … --channel …
  --output …`); the section links to the Catalogue CI Contract via
  `https://github.com/eugenelim/agent-ready-repo/blob/main/guides/_shared/reference/catalogue-ci-contract.md`
  (correct path — without the `docs/` prefix that existing broken links carry).

- [x] AC6: `guides/_shared/how-to/create-external-catalogue.md` exists with required guide
  frontmatter (title, summary, pack: _shared, kind: how-to, status: stable); it covers the
  create → self-host → lint → verify → CI pipeline path in the correct order (self-host
  generates `marketplace.json`, which `lint` requires at CAT-L002); it explicitly references
  `guides/_reference/catalogue-format.md` for the full `catalogue.toml` schema (not shown <!-- Moved 2026-08-18 by spec/guide-metadata-completion to `guides/_shared/reference/catalogue-format.md`; the public route is unchanged. -->
  inline, since the schema requires ~20 nested fields); it links to the Catalogue CI
  Contract for the publish phase.

- [x] AC7: `guides/_shared/README.md` How-to section lists the new
  `create-external-catalogue.md` guide.

- [x] AC8: All relative links across modified files resolve — verified by a script that
  resolves each `catalogue-ci-contract.md` relative reference against its source file's
  directory and asserts the target exists on disk. (build-site.py rewrites syntax; it does
  not verify cross-file body links, so an automated resolver is the only gate here.)

- [x] AC9: `python3 -m pytest tools/test_catalogue_tooling_docs.py tools/test_validate_guides.py -q`
  exits 0.

- [x] AC10: `python3 tools/build-site.py` exits 0 (site regenerated cleanly; no hand-edited
  generated outputs).

## Testing Strategy

| AC | Mode | Verification |
|----|------|-------------|
| AC1–AC5, AC7 | Goal-based | `grep` for the link target in the modified file |
| AC6 | Visual / manual QA | `grep` for frontmatter fields + CI link; manual: run `agentbundle catalogue lint/verify` commands from the guide against a scratch catalogue |
| AC8 | Goal-based | Inline Python resolver: resolve each relative link against its source file's dir, assert target exists |
| AC9 | Goal-based | `pytest` run |
| AC10 | Goal-based | `python3 tools/build-site.py` run |

## Boundaries

**In scope:**
- New adopter-facing how-to at `guides/_shared/how-to/create-external-catalogue.md`
- Link additions to `guides/README.md`, `guides/_shared/README.md`, configure-enterprise guide,
  curation pack operator journey, curation pack README
- PyPI README: deprecated command fix + CI pointer
- All internal link validation

**Out of scope:**
- `docs/guides/how-to/create-external-catalogue.md` — intentionally maintainer-only (verified
  by `test_catalogue_tooling_docs.py`; must not be moved or modified)
- `guides/_shared/reference/agentbundle.md` — already has an accurate 3-sentence CI section
  with link; expansion would duplicate the contract
- CI workflow examples or pipeline content in any guide
- `spec/catalogue-ci-export-boundary` — separate spec in the queue

## Structural gap decisions

**Gap 1 — adopter-facing external catalogue how-to:**
Create a companion at `guides/_shared/how-to/create-external-catalogue.md`. The internal guide
at `docs/guides/how-to/create-external-catalogue.md` is tested to exist by
`test_catalogue_tooling_docs.py` and must remain.

The companion uses the correct pipeline order:
1. Create layout (see `guides/_reference/catalogue-format.md` for full `catalogue.toml` schema — ~20 required fields across 5 nested tables; not shown inline)
2. Run `agentbundle catalogue self-host --root . --write` to generate `marketplace.json` (required by `catalogue lint` CAT-L002)
3. Lint: `agentbundle catalogue lint --root .`
4. Verify: `agentbundle catalogue verify --root .`
5. Publish via CI: link to catalogue-ci-contract.md

The internal guide's step order (lint before self-host) is incorrect for external catalogues
without a pre-existing `marketplace.json`. The companion corrects this.

Manual QA for AC6 uses this repo's own catalogue (which has a valid `catalogue.toml` and
pre-existing `marketplace.json`), not a from-scratch minimal scaffold.

**Gap 2 — curation pack CI mention:**
No new curation guide. Add a CI pointer in the existing operator journey's publish section
and in the curation pack README. A sentence and a link is enough; duplicating the contract
content is not the right move.

## Assumptions

1. `guides/_shared/how-to/` accepts new how-to files without build or governance ceremony
   (existing files confirm this).
2. `pack: _shared` and `kind: how-to` are valid frontmatter values for the new guide (confirmed
   from `contracts/guide.schema.json` — the new how-to will be the first frontmatter-bearing
   `_shared` how-to; existing how-tos have no frontmatter and get a migration warning from
   `validate_guides.py`, not an error).
3. `agentbundle package-catalogue` is deprecated and prints a warning; `agentbundle catalogue
   package` is the current canonical form (confirmed from `package_catalogue.py` docstring).
   The minimum version for the full documented surface (`catalogue package`, 18-step `verify`)
   is 0.22.x (current); the prerequisite in the new how-to will be pinned to `≥ 0.22.0`.
   (The `0.14.0` figure in the plan draft was unsourced and too low.)
4. `tools/build-site.py` picks up new `guides/_shared/how-to/*.md` files automatically by
   directory walk (confirmed from `test_build_site_routing.py` mirror logic).
5. `guides/README.md` is a Manual file (not projected) per `AGENTS.local.md`.

## Declined patterns

- **Expanding `agentbundle.md`'s CI section:** The 3-sentence summary + link is the right
  depth for a reference doc. More would duplicate the contract.
- **Adding CI workflow snippets to any guide:** The contract explicitly places workflow
  implementation on the org's CI system; adding examples would blur the responsibility
  boundary.
- **Creating a "Curation CI" guide:** The operator journey already has a publish section.
  A sentence pointing to the contract is the minimal correct addition.
- **Moving the internal how-to:** `test_catalogue_tooling_docs.py` asserts its location;
  moving it breaks a tested contract.
- **Updating the `docs/guides/how-to/create-external-catalogue.md` internal guide:** It is
  maintainer-facing by convention. Additions belong in the adopter-facing companion.
