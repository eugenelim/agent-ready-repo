# Spec: catalogue-wave8-readme-contributing

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D1–D4](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Gated on:** [catalogue-wave1-contract-convergence](../catalogue-wave1-contract-convergence/spec.md) (Shipped)
- **Shape:** docs only (no engine change)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (public interface: README.md and CONTRIBUTING.md are public-facing documents;
structural: adds a named section to README.md)

## Objective

Wave 1 shipped the contract authority model (D1), schema sync (D2),
`contracts/README.md` completeness (D3), and the portable authoring hub (D4). It
also replaced the "fork it as your own" language in `README.md` § "The catalogue"
and `docs-site/src/content/docs/index.mdx`, and added the `agentbundle catalogue init`
entry point.

Wave 8 completes the README/CONTRIBUTING convergence on top of that foundation:

1. **"Evaluate or build a catalogue" subsection** — README.md § "The catalogue"
   gains a named subsection that gives evaluators a clear entry point to the D4
   authoring hub and gives builders the `agentbundle catalogue init` path. Currently
   those two audiences share one undifferentiated paragraph with no evaluate anchor.

2. **Fork language verification** — README.md and CONTRIBUTING.md are confirmed
   clean. No further fork/clone-to-adopt language remains beyond what Wave 1
   removed. (One instance in `docs/architecture/catalogue.md` is a maintainer-facing
   architecture doc and is deferred as out of scope for this wave.)

3. **Pack table currency** — the curated flagship subset table in README.md is
   verified against `pack.toml description` fields. A note is added directing
   readers to `agentbundle list-packs` for the full catalogue. (Decision: curated
   subset over generated; automated generation would require build-pipeline coupling
   that does not exist today.)

4. **CONTRIBUTING authoring rules** — CONTRIBUTING.md gains a pointer to the D4
   authoring hub (`guides/_shared/reference/catalogue-authoring-standards.md`), an
   updated "Where to find authoritative information" table, and a navigational note
   for the Wave 2 `[[pack.integrations]]` convention (shipped in Wave 2 / 0.27.0).

After this wave, a cold reader arriving at README.md or CONTRIBUTING.md finds a
consistent path to the authoring hub, the machine contracts, and the Wave 2
integration convention (Wave 2 shipped; the note uses present tense). No engine
change is required; this wave touches documentation only.

## Boundaries

### Always do

- Verify `SKIP_SAST=1 make build-check` exits 0 before committing.
- Verify `grep "fork it as your own" README.md CONTRIBUTING.md` returns empty.
- Keep root AGENTS.md ≤ 250 lines and packs/AGENTS.md ≤ 150 lines.
- Keep the `[[pack.integrations]]` note in CONTRIBUTING navigational — Wave 2 has
  shipped (0.27.0); the note states the convention is live and points to the authoring
  hub for the full contract spec. Do not describe the schema in CONTRIBUTING.
- Use the exact link path `guides/_shared/reference/catalogue-authoring-standards.md`
  in both README.md and CONTRIBUTING.md (relative from the repo root).

### Ask first

- Adding any pack to or removing any pack from the README.md flagship subset table,
  beyond correcting a stale description for a pack that is already listed.
- Changing the pack table to generated output rather than a hand-maintained curated
  subset (requires build tooling decision; not in this wave).
- Any CONTRIBUTING.md change beyond the three targeted additions: authoring hub
  pointer, updated "Where to find authoritative information" table, and integration
  authoring rule.

### Never do

- Touch `agentbundle/_data/` — no engine change in this wave.
- Edit projected outputs under `.claude-code/`, `.cursor/`, `.kiro/`, etc.
  directly — edit `.apm/` sources, then run `make build-self`.
- Cite RFC, ADR, or spec paths in any content that ships to catalogue adopters.
- Exceed the AGENTS.md line caps (root ≤ 250, packs/ ≤ 150).

## Testing Strategy

- **README evaluate subsection (AC1–AC2):** grep confirms heading
  "Evaluate or build a catalogue" present in README.md; grep confirms link to
  `guides/_shared/reference/catalogue-authoring-standards.md` present in README.md.
- **No stale fork language (AC3, AC9):** `! grep -q "fork it as your own" README.md`
  and `! grep -q "fork it as your own" CONTRIBUTING.md` both exit 0 (no matches).
- **Pack table note (AC4):** grep for the distinctive caption text (e.g., "Full catalogue:"
  or `agentbundle list-packs`) within the `## The catalogue` section boundary — not a
  whole-file grep (Quick Start at line 48 already contains `agentbundle list-packs` and
  would produce a false-positive on a whole-file search).
- **Pack descriptions currency (AC5):** visual/manual QA — each listed pack's
  one-line description in the README.md table is derived from or consistent with the
  `description` field in that pack's `pack.toml`. Stale descriptions are corrected.
- **CONTRIBUTING authoring hub pointer (AC6):** grep for `catalogue-authoring-standards.md`
  within the "Adding a new pack" section only (lines between `## Three contribution lanes`
  / `### Adding a new pack` and the next `###` heading) — not a whole-file grep.
- **CONTRIBUTING where-to-find table (AC7):** grep for a table row that contains both
  the question-column text (e.g., "Catalogue authoring" or "authoring standards") and
  `catalogue-authoring-standards.md` in the same line, scoped to the "Where to find
  authoritative information" table section.
- **CONTRIBUTING integration authoring rule (AC8):** grep confirms
  `pack.integrations` present in CONTRIBUTING.md's "Adding a new pack" section.
- **Regression build-check (AC9):** `SKIP_SAST=1 make build-check` exits 0.
- **Line count (AC10–AC11):** `wc -l AGENTS.md` ≤ 250; `wc -l packs/AGENTS.md`
  ≤ 150.

## Acceptance Criteria

### Phase A — README.md: "Evaluate or build a catalogue" subsection

- [ ] AC1: README.md § "The catalogue" contains a subsection
  `### Evaluate or build a catalogue`. The subsection includes at minimum:
  (a) an evaluate path — one sentence and a link to
  `guides/_shared/reference/catalogue-authoring-standards.md` as the entry
  point for readers deciding whether to adopt or build from the catalogue;
  (b) a build path — the `agentbundle catalogue init` command and a link to
  `guides/_shared/how-to/create-a-catalogue.md`. The existing last paragraph
  of "The catalogue" section (the `catalogue init` paragraph shipped by Wave 1)
  is absorbed into or replaced by this subsection so it is not duplicated.
- [ ] AC2: The subsection heading `### Evaluate or build a catalogue` produces
  an anchor that is reachable via the README navigation link strip at the top of
  the file (or the navigation link strip is updated to include it). Either the
  existing `[The Catalogue](#the-catalogue)` link covers it, or a new link is
  added — either is acceptable; do not add a link that does not resolve.

### Phase B — README.md: Fork language and pack table

- [ ] AC3: `! grep -q "fork it as your own" README.md` exits 0 (no matches).
  No other adopt-by-forking phrase is present in README.md.
- [ ] AC4: The pack table in README.md includes a note or caption (e.g.,
  `> Full catalogue: run \`agentbundle list-packs\`` or equivalent) directing
  readers to `agentbundle list-packs` for the complete catalogue, positioned
  before or after the table but not as an inline table cell.
- [ ] AC5: Each pack row's short description in the README.md table is verified
  against its `pack.toml` `description` field. Descriptions that have drifted
  are corrected; descriptions that remain current are left unchanged. If no
  descriptions have drifted, AC5 is satisfied by the verification note in the PR
  description.

### Phase C — CONTRIBUTING.md: Portable authoring rules and integration authoring rule

- [ ] AC6: CONTRIBUTING.md "Adding a new pack" section contains a pointer to
  `guides/_shared/reference/catalogue-authoring-standards.md` as the portable
  authoring standards hub. This pointer may be added as a step 0 or step 2 note;
  it must be clearly reachable from the new-pack lane.
- [ ] AC7: CONTRIBUTING.md "Where to find authoritative information" table
  contains a new row for portable catalogue authoring standards pointing to
  `guides/_shared/reference/catalogue-authoring-standards.md`. The row's
  question column may read "Catalogue authoring standards and contracts" or
  equivalent.
- [ ] AC8: CONTRIBUTING.md "Adding a new pack" section contains a note for optional
  cross-pack composition: if the pack declares optional composition with other packs,
  add `[[pack.integrations]]` entries to `pack.toml`. The note must state that the
  `[[pack.integrations]]` convention shipped with Wave 2 (0.27.0) and point to the
  authoring hub for the full contract spec. The note must not define new schema; it is
  navigational only.
- [ ] AC9: `! grep -q "fork it as your own" CONTRIBUTING.md` exits 0 (no matches).

### Regression

- [ ] AC10: `SKIP_SAST=1 make build-check` exits 0.
- [ ] AC11: `wc -l AGENTS.md` ≤ 250 (CI enforces; verify after any edit).
- [ ] AC12: `wc -l packs/AGENTS.md` ≤ 150 (CI enforces; verify after any edit).

## Assumptions

- **Technical:** `guides/_shared/reference/catalogue-authoring-standards.md`
  exists (shipped in Wave 1 — verified at spec time).
- **Technical:** `guides/_shared/how-to/create-a-catalogue.md` exists
  (verified at spec time; Wave 1 uses it as the redirect target for the old
  `docs/architecture/catalogue.md` link).
- **Technical:** No CI step today enforces README pack-table currency; the
  table is hand-maintained. This wave verifies descriptions against `pack.toml`
  manually and notes findings in the PR.
- **Technical:** The curated flagship subset decision: the packs directory
  contains operator/tooling packs (`catalogue-curation`, `user-guide-diataxis`)
  and ecosystem-specific integrations (`iac-terraform`, `linear`, `github`,
  `frontend-engineering`) that are not appropriate for the main README audience.
  The existing 13-pack table is the right curated set; this wave verifies it
  rather than expanding it. `agentbundle list-packs` is the canonical full list.
- **Deferred:** `docs/architecture/catalogue.md` line 101 uses "fork this
  catalogue" in its "Stand up your own catalogue" section. This is an internal
  maintainer-facing architecture doc, not a public adopter path. Tracked as a
  follow-on cleanup outside Wave 8 scope.
- **Deferred:** The `/evaluate/` marketing page (RFC-0076 D10, Wave 7) is not
  a prerequisite. The README "Evaluate or build a catalogue" subsection links to
  the D4 authoring hub as the interim evaluate entry point. When Wave 7 ships,
  a forward-link to `/evaluate/` may be added in Wave 9's closeout.
- **Historical context:** `[[pack.integrations]]` shipped with Wave 2 (0.27.0).
  CONTRIBUTING carries a navigational note pointing to the authoring hub for the full
  contract spec. The note uses present tense ("shipped in Wave 2") not a future-reference.
