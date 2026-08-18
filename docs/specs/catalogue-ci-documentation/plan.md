# Plan: Catalogue CI — Documentation Integration

- **Status:** Drafting
- **Spec:** [spec.md](spec.md)

## Tasks

### T1 — Create `guides/_shared/how-to/create-external-catalogue.md`

**Depends on:** none

**Verification mode:** Visual / manual QA (new adopter-facing guide — frontmatter, links,
and documented command correctness must all be checked)

**Tests:**
- `guides/_shared/how-to/create-external-catalogue.md` exists
- `grep 'title:' guides/_shared/how-to/create-external-catalogue.md` returns non-empty
- `grep 'summary:' …` returns non-empty
- `grep 'pack: _shared' …` returns non-empty
- `grep 'kind: how-to' …` returns non-empty
- `grep 'catalogue-ci-contract' …` returns non-empty (link to CI contract present)
- `python3 -m pytest tools/test_validate_guides.py -q` exits 0 (guide passes schema check)
- `python3 tools/build-site.py` exits 0
- Manual: run `agentbundle catalogue lint --root .` and `agentbundle catalogue verify --root .`
  from this repo's root (complete `catalogue.toml` + pre-existing `marketplace.json`); confirm
  both exit 0 and match the commands as written in the guide

**Approach:**
Write the guide from scratch (not a copy of the internal doc). Audience: an engineer building
their first external catalogue. Cover:
1. Prerequisites (Python 3.11+, agentbundle ≥ 0.22.0)
2. Create the layout — show the directory shape; reference `guides/_reference/catalogue-format.md` <!-- Moved 2026-08-18 by spec/guide-metadata-completion to `guides/_shared/reference/catalogue-format.md`; the public route is unchanged. -->
   for the full `catalogue.toml` schema (required fields span ~20 nested keys across 5 tables;
   not shown inline — point to the format reference)
3. Run `agentbundle catalogue self-host --root . --write` to generate `marketplace.json`
   (lint requires this at CAT-L002)
4. Lint: `agentbundle catalogue lint --root .`
5. Verify: `agentbundle catalogue verify --root .`
6. Publish via CI: one sentence + link to catalogue-ci-contract.md

Keep it short. The CI contract and catalogue-format reference are the deep resources; this
guide is the entry path that orders the steps correctly.

For the manual QA step, run the documented commands against **this repo's own catalogue**
(which has a complete `catalogue.toml` and pre-existing `marketplace.json`), not a from-scratch
minimal scaffold. Confirm `lint` and `verify` exit 0 against the repo root.

---

### T2 — Update `guides/_shared/README.md`: add how-to entry

**Depends on:** T1

**Verification mode:** Goal-based check

**Tests:**
- `grep 'create-external-catalogue' guides/_shared/README.md` exits 0

**Approach:**
Add a bullet for the new guide in the How-to section, after the existing how-to entries.
One line: `- [Create an external catalogue](how-to/create-external-catalogue.md) — scaffold
a catalogue outside this repository, validate it, and publish it via CI.`

---

### T3 — Update `guides/README.md`: add CI contract to Shared guides section

**Depends on:** none

**Verification mode:** Goal-based check

**Tests:**
- `grep 'catalogue-ci-contract' guides/README.md` exits 0

**Approach:**
In the "Shared guides" section, add the CI contract to the Reference bullet list (alongside
agentbundle CLI, adapter support matrix, tracker vocabulary). One line.

---

### T4 — Update `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md`: add See also pointer

**Depends on:** none

**Verification mode:** Goal-based check

**Tests:**
- `grep 'catalogue-ci-contract' guides/_shared/how-to/configure-catalogue-enterprise-distribution.md` exits 0

**Approach:**
Add to the existing See also section:
`- [Catalogue CI contract](../reference/catalogue-ci-contract.md) — publication ordering,
exit codes, and responsibility boundaries for packaging and publishing from CI.`

---

### T5 — Update `guides/catalogue-curation/explanation/catalogue-operator-journey.md`: CI pointer in publish section

**Depends on:** none

**Verification mode:** Goal-based check

**Tests:**
- `grep 'catalogue-ci-contract\|CI contract' guides/catalogue-curation/explanation/catalogue-operator-journey.md` exits 0

**Approach:**
In the "Profile and publish" section, add a sentence framing the CI packaging path as a
distinct route from `export-catalogue` (not a gloss on it). `export-catalogue` produces a
redistributable fork; `agentbundle catalogue package` → Artifactory publish is the CI
release pipeline. Name the distinction, then link to the contract.

---

### T6 — Update `guides/catalogue-curation/README.md`: add CI pointer

**Depends on:** none

**Verification mode:** Goal-based check

**Tests:**
- `grep 'catalogue-ci-contract' guides/catalogue-curation/README.md` exits 0

**Approach:**
Add a reference to the Catalogue CI Contract in the relevant section (reference or related
links). One line or a short sentence.

---

### T7 — Update `packages/agentbundle/README.md`: fix deprecated command + add CI pointer

**Depends on:** none

**Verification mode:** Goal-based check

**Tests:**
- `grep 'agentbundle package-catalogue' packages/agentbundle/README.md` exits 1
  (deprecated command removed from enterprise distribution section)
- `grep 'catalogue-ci-contract\|Catalogue CI' packages/agentbundle/README.md` exits 0

**Approach:**
In the Enterprise distribution section:
1. Replace the `agentbundle package-catalogue` block with `agentbundle catalogue package`,
   keeping `--root` plus `--bundle`, `--release`, `--channel`, `--output`.
2. Add a one-line pointer using the correct GitHub URL (note: existing README links use a
   broken `docs/guides/_shared/...` prefix — the CI contract is at `guides/_shared/`, no
   `docs/` prefix):
   `https://github.com/eugenelim/agent-ready-repo/blob/main/guides/_shared/reference/catalogue-ci-contract.md`

---

### T8 — Validate all internal links across modified files

**Depends on:** T1, T2, T3, T4, T5, T6, T7

**Verification mode:** Goal-based check

**Tests:**
- Inline Python resolver (see Approach) exits 0 for all 6 relative links
- `python3 -m pytest tools/test_catalogue_tooling_docs.py tools/test_validate_guides.py -q`
  exits 0

**Approach:**
Write a short Python resolver that, for each (source_file, relative_link) pair, resolves
`source_file.parent / relative_link` and asserts the target exists. Run it inline; it is
not a permanent tool. Then verify:

For each modified file, verify the relative path to `catalogue-ci-contract.md` is correct:

| File | Correct relative path to CI contract |
|------|-------------------------------------|
| `guides/_shared/how-to/create-external-catalogue.md` | `../reference/catalogue-ci-contract.md` |
| `guides/_shared/README.md` | `reference/catalogue-ci-contract.md` |
| `guides/README.md` | `_shared/reference/catalogue-ci-contract.md` |
| `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md` | `../reference/catalogue-ci-contract.md` |
| `guides/catalogue-curation/explanation/catalogue-operator-journey.md` | `../../_shared/reference/catalogue-ci-contract.md` |
| `guides/catalogue-curation/README.md` | `../_shared/reference/catalogue-ci-contract.md` |
| `packages/agentbundle/README.md` | Full GitHub URL (PyPI README uses absolute URLs) |

Run `python3 tools/build-site.py` (or dry-run if available) to confirm clean regeneration.

---

## Pre-EXECUTE review gate

Per the work-loop spec/plan adversarial review trigger (structural change — new file in
`guides/_shared/how-to/`), run `adversarial-reviewer` on this spec + plan before EXECUTE.
Iterate to Clean before proceeding.
