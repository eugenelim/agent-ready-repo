# Spec: m1-governance-integration

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (governing — the M1 Workspace Foundation design, Batch 5 ACs, and the `workspace.toml` schema this batch surfaces)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineering team running RFC-0064's governance machinery gets three
integrated improvements that land in one PR. First, the `new-rfc` skill's
Accepted path gains a workspace queue-write step: when an RFC moves to Accepted
the skill prompts "Add implementation specs to `workspace.toml` queue?" —
letting the agent help queue the follow-on implementation work immediately,
without a separate manual edit. Second, four `docs/product/` subdirectory
cases are handled (three seeded, one intentionally left): `projects/` (project
index template), `findings/` (directory placeholder ahead of M3's register
population), and `initiatives/` (initiative brief template) are created; and
`shaping/` is deliberately left untouched (already contains M2 shaping
artifacts from Batch 2). This batch is the sole owner of
`initiatives/_template.md`; M2 implementation uses it, not re-creates it. Third, a reference doc documents the `workspace.toml`
dependency model in full — the inline `{path/slug, needs}` format, the
cross-queue and cross-type prefix notation, the cross-initiative prefix, the
display surface (`check-workspace`), and the deferral boundary — so any
agent or engineer can understand the coordination model without reading the
full RFC.

Success: an agent reaching the Accepted path of `new-rfc` is offered a queue
write; all four `docs/product/` subdirectory cases are handled (three
created, one intentionally left); the dependency model reference doc is
discoverable under `docs/product/` and links back to RFC-0064; and the orphaned
`spec/m1-shaping-seeds` queue entry is removed from `workspace.toml`.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Degrade the workspace write gracefully.** If `workspace.toml` is absent
  the Accepted-path prompt still appears; the TOML write is skipped with the
  literal note: "workspace.toml not found — add the entry manually when
  Batch 2 lands." This preserves behavior for any adopter who has not yet
  shipped Batch 2.
- **Preserve the existing Accepted-path behaviour.** The "After acceptance"
  section of `new-rfc` that lists follow-on ADRs, specs, and CONVENTIONS edits
  runs unchanged; the queue-write step is appended after, not substituted.
- **Seed files are minimal.** `_template.md` files contain the schema and
  guidance prose from CONVENTIONS.md §5b, not live project data. The
  `findings/` seed establishes the directory and its purpose; it does not
  pre-populate the register schema (that belongs to M3 per RFC-0064 M3 ACs).
  Seed files that exist (`docs/product/shaping/` already has two files) are
  left untouched.
- **Reference doc cites the RFC.** `workspace-toml-deps.md` links back to
  RFC-0064 as the authoritative source for D7 (dependency model) and D9
  (shaping-type prefixes).
- **Write spec body in present tense.** Retcon discipline — describe the
  capability as if it already works.

### Ask first

- **Changing the exact prompt text.** RFC-0064 specifies "Add implementation
  specs to `workspace.toml` queue?" verbatim; any rewording needs user
  sign-off.
- **Adding support for queue-entry types other than `{path, needs}` strings.**
  D7's inline object is `{path/slug, needs}`; extending this (e.g. adding a
  `type` field on work entries) is a schema change that requires an erratum to
  RFC-0064.
- **Placing the reference doc somewhere other than `docs/product/`.** The
  name and location are open within `docs/product/`; a location outside that
  tree needs explicit confirmation.
- **Removing any other `workspace.toml` queue entry beyond `m1-shaping-seeds`.**
  The removal of the pre-split `m1-shaping-seeds` entry is the only sanctioned
  `workspace.toml` edit in this PR; any further edits need user sign-off.

### Never do

- **Never modify the `workspace.toml` schema.** This batch only reads,
  appends to `[work].queue`, and removes the orphaned entry; no new sections
  or keys.
- **Never write to `workspace.toml` without user confirmation.** The Accepted
  path is interactive; the queue-write step is opt-in (the user answers the
  prompt). No silent auto-writes. The `m1-shaping-seeds` removal is the one
  exception — it is a queue cleanup, not a queue write, and it ships in the
  same PR as a deliberate collapse (per Assumptions below).
- **Never introduce a new top-level package, service, or runtime dependency.**
  All three deliverables are content changes (skill prose edits + markdown
  seed files); no new library, no new build step.
- **Never merge implementation with Batch 3 or Batch 4 changes.** This PR
  is independent of both. If a work-loop or receive-brief change appears in
  the same branch, split it out.
- **Never pre-populate `docs/product/findings/` with register entries.**
  Those belong to M3. The Batch 5 seed establishes the directory and purpose
  only; no column schema, no row data.

## Testing Strategy

All three deliverables are skill-prose or markdown content, so verification
is **goal-based** for the structural outputs and **manual QA** for the
end-to-end flow:

- **new-rfc skill content (goal-based):** `grep` the source skill file for
  the exact prompt text "Add implementation specs to `workspace.toml` queue?"
  and for the exact skip-note text "workspace.toml not found — add the entry
  manually when Batch 2 lands" (the literal skip-note deterministically
  confirms the absent-file branch exists).
- **Accepted-path end-to-end (manual QA):** invoke `new-rfc` on a test RFC
  stub and walk it to the Accepted state. Record four scenarios: (a) prompt
  appears and answering yes produces a valid `[work].queue` append in an
  existing `workspace.toml` with the target initiative section present;
  (b) with `workspace.toml` absent, the prompt appears and the literal skip
  note appears, no error; (c) with `workspace.toml` present but the target
  initiative section absent, the skill confirms the slug with the user and
  offers to create the section before appending — it does not silently skip
  and does not auto-create; (d) answering no to the prompt leaves
  `workspace.toml` unchanged and continues to the follow-on artifact list.
- **Seed files present (goal-based):** `find docs/product/projects
  docs/product/findings docs/product/initiatives -name "*.md"` and assert
  the expected files exist. `shaping/` is excluded (intentionally untouched).
- **Dependency model doc present (goal-based):** assert the reference doc
  exists under `docs/product/` and `grep` it for: the three cross-queue
  prefix forms (`work:`, `shape:`, `brief:`), the two shaping-type prefix
  forms (`research:`, `strategy:`), and `grep -E "ini-[0-9]{3}:work:"` for
  the cross-initiative prefix (matches the concrete worked example, not just
  the RFC filename which also contains `ini-`).
- **Orphaned queue entry removed (goal-based):** `grep workspace.toml` for
  `m1-shaping-seeds` exits non-zero (entry removed).
- **RFC-0064 amendments landed (goal-based):** read RFC-0064 and confirm
  (a) the Batch 5 table row no longer implies a `shaping/` seed; (b) the
  Batch 5 AC bullet (~line 407) matches the table row; (c) the M2.6 JIT table
  row (~line 115) reads as *using* the Batch 5-seeded `initiatives/_template.md`,
  not creating it; (d) the M2 acceptance criterion (~line 418,
  `- [ ] Initiative brief artifact + docs/product/initiatives/_template.md seed`)
  is updated to read as M2.6 *using* the Batch 5-seeded template;
  (e) the Bootstrap example queue (~line 324) no longer lists
  `"spec/m1-shaping-seeds"` (removed to match the collapsed single-spec
  Batch 5 delivery).

No TDD-mode tests are needed: there is no logic with a compressible invariant
(no parser, no data model, no algorithmic path). All verification is either
structural file presence or an observable prose contract.

## Acceptance Criteria

**AC1 — `new-rfc` Accepted-path workspace prompt**

- [x] The `new-rfc` skill's post-acceptance step (currently "After acceptance"
  in the skill body) is extended to prompt the user: "Add implementation specs
  to `workspace.toml` queue?" before presenting the follow-on artifact list.
- [x] If the user answers yes, the skill reads `["<initiative-slug>".work].queue`
  in the local `workspace.toml` and helps the user add entries in the
  `{path, needs}` format defined in RFC-0064 D7, then stages the file.
- [x] If `workspace.toml` is absent in the working directory, the prompt still
  appears; the TOML write is skipped with the literal note "workspace.toml not
  found — add the entry manually when Batch 2 lands"; no error or exception
  is raised.
- [x] If `workspace.toml` is present but the target initiative section
  (`["<slug>"]`) is absent, the skill asks the user to confirm the initiative
  slug and offers to create the section with an empty `[work].queue` before
  appending. It does not silently skip and does not auto-create without
  confirmation.
- [x] The existing "After acceptance" follow-on artifact list (ADRs, specs,
  CONVENTIONS edits) is preserved and runs as before; the queue-write step
  is additive.
- [x] `grep` of the source skill file confirms: the literal prompt string "Add
  implementation specs to `workspace.toml` queue?" is present; the literal
  skip-note "workspace.toml not found — add the entry manually when Batch 2
  lands" is present.

**AC2 — `docs/product/` artifact seeds + workspace.toml cleanup**

- [x] `docs/product/projects/_template.md` exists and contains: a frontmatter
  block (or markdown header block) with `outcome`, `appetite`, `milestone`,
  and `brief` fields per CONVENTIONS §5b's project definition; and brief
  instructional prose referencing `workspace.toml` as the queue coordination
  artifact.
- [x] `docs/product/findings/` exists and contains at least one seed file
  establishing the directory purpose (per CONVENTIONS §5b: "structured
  governance registers"), clearly marked as awaiting M3's register files
  (`rfc-candidates.md`, `roadmap-intents.md`). The seed contains **no** column
  schema and **no** register entries — those belong to M3.
- [x] `docs/product/initiatives/` exists and contains `_template.md` for an
  initiative brief, shaped for altitude-1 shaping artifacts (cross-repo,
  multi-quarter scope; links to `workspace.toml` initiative section;
  per CONVENTIONS §5b's initiative brief definition). This is the sole owner
  of `initiatives/_template.md`; M2.6 uses this file, it does not recreate it.
- [x] `docs/product/shaping/` is left untouched (already contains two files
  from Batch 2; no new files added here). The RFC Batch 5 "shaping artifact
  seeds" clause is intentionally a no-op: shaping artifacts are M2-produced
  via PE skills, not seeded by templates; the two existing files are the M2
  priors, not Batch 5 deliverables.
- [x] `workspace.toml` no longer contains the `"spec/m1-shaping-seeds"` queue
  entry — the pre-split entry is removed in the same PR because its work is
  collapsed into this spec.
- [x] All new files, the `workspace.toml` cleanup, the dependency model doc
  (AC3), and the RFC-0064 amendments (AC4) land in the same PR as AC1.

**AC3 — `workspace.toml` dependency model reference doc**

- [x] A reference doc exists at `docs/product/workspace-toml-deps.md` (or a
  clearly discoverable path under `docs/product/`) that documents:
  - The inline object format: a queue entry is a **string** (no deps) or an
    **inline object** `{path = "...", needs = "..."}` (with deps); `needs` is
    a string or a list of strings.
  - The three **cross-queue** prefix forms (for `[work]` queue deps):
    `"work:<path>"`, `"shape:<slug>"`, `"brief:<path>"`.
  - The two **shaping-type** prefix forms (for `[shaping_queue]` cross-type
    deps, per RFC-0064 D9): `"research:<slug>"`, `"strategy:<slug>"`.
  - The cross-initiative prefix: `"ini-NNN:work:<path>"`, with a worked
    example matching the multi-initiative example in RFC-0064 § Proposed design.
  - That `check-workspace` is the display surface — it reads the declared
    deps and surfaces ready/blocked/parallel candidates; agents do not
    enforce the DAG themselves.
  - That `work-loop` enforcement of the DAG is deferred to a post-M1
    milestone (per RFC-0064 D7), so the reference doc does not create a false
    expectation that `work-loop` enforces the DAG today.
- [x] `grep -E "ini-[0-9]{3}:work:"` of the doc matches (cross-initiative
  prefix present in the worked example, as specified in RFC-0064 § Proposed
  design); also `grep` confirms `work:`, `shape:`, `brief:`, `research:`, and
  `strategy:` are present.
- [x] The doc links to RFC-0064 as the authoritative source for D7 (dependency
  model) and D9 (shaping-type prefixes), and to `workspace.toml` as the living
  example.

**AC4 — RFC-0064 Draft amendments**

- [x] RFC-0064 Batch 5 table and AC wording no longer imply a shaping-directory
  seed (`docs/product/shaping/` is explicitly noted as intentionally untouched
  because shaping artifacts are PE-skill-produced, not templated).
- [x] RFC-0064 M2.6 JIT table row (~line 115) and M2 acceptance criterion
  (~line 418) are both updated to read as M2.6 *using* the Batch 5-seeded
  `initiatives/_template.md` rather than creating it; sole ownership of the
  seed is unambiguously this batch.
- [x] RFC-0064 Batch 5 AC bullet (~line 407) matches the amended Batch 5 table
  row (no shaping-directory seed implied).
- [x] RFC-0064 Bootstrap example queue (~line 324) no longer lists
  `"spec/m1-shaping-seeds"` — the entry is removed to match the collapsed
  single-spec Batch 5 delivery.

## Assumptions

- Technical: the `new-rfc` skill source lives in the governance-extras pack
  source path and is projected to `.claude/skills/new-rfc/SKILL.md`; edits
  go to the source, not the projected copy
  (source: `.claude/skills/new-rfc/SKILL.md` read 2026-07-18 — skill exists
  and has an "After acceptance" section with no workspace.toml step yet).
- Technical: `workspace.toml` exists in the repo root on `main` (Batch 2
  shipped; source: `workspace.toml` read 2026-07-18 — file present with full
  `["ini-002"]` section and a `"spec/m1-shaping-seeds"` queue entry to remove).
- Technical: `docs/product/shaping/` already contains two files
  (`ecosystem-overview.md`, `product-vision-INI-001.md`) committed in Batch 2;
  no new shaping seeds are needed in this batch
  (source: `ls docs/product/shaping/` 2026-07-18).
- Technical: `docs/product/findings/`, `docs/product/initiatives/`, and
  `docs/product/projects/` do not yet exist; all three are created by this batch
  (source: `ls docs/product/` 2026-07-18 — only `shaping/`, `journeys/`,
  `README.md`, `changelog.md`, `roadmap.md`, `release-checklist.md` present).
- Process: CONVENTIONS.md §5b already admits all five subdirectories
  (`projects/`, `shaping/`, `findings/`, `initiatives/`, `research/`) with
  their definitions — Batch 1 amendment is shipped
  (source: `docs/CONVENTIONS.md` lines 501–522, read 2026-07-18).
- Process: this batch is safe to ship after Batch 1; the `new-rfc` queue-write
  degrades gracefully if `workspace.toml` is absent, so Batch 2 is not a
  hard prerequisite (source: RFC-0064 Batch 5 notes — "safe to ship any time
  after Batch 1; `new-rfc` queue-write is a no-op until Batch 2 lands").
- Process: the spec slug `m1-governance-integration` matches the entry
  pre-seeded in `workspace.toml` `["ini-002".work].queue` (source:
  `workspace.toml` read 2026-07-18 — `"spec/m1-governance-integration"` present).
- Process: the `m1-shaping-seeds` workspace.toml entry is a pre-split from
  Batch 2 planning that is collapsed into this spec; removing it in the same
  PR is the correct resolution (source: user instruction 2026-07-18 — all
  three Batch 5 ACs belong to this single spec).
- Process: `docs/product/initiatives/_template.md` is the **sole** owner of
  this seed; RFC-0064 M2.6 uses the file produced here and does not recreate
  it (source: RFC-0064 M2 ACs, `rfc:418` — "Initiative brief artifact +
  `docs/product/initiatives/_template.md` seed"; read as M2 using a Batch 5
  seed, consistent with Batch 5 shipping before M2 begins).
- Process: the `findings/` seed does **not** include the register column schema;
  that schema is owned by M3 per RFC-0064 M3 ACs (`rfc:424–425` —
  `docs/product/findings/rfc-candidates.md` and `roadmap-intents.md` with the
  `| Problem | Source | Surfaced by | Date | Priority | Disposition |` schema);
  Batch 5 seeds the directory only (source: RFC-0064 M3 ACs, read 2026-07-18).
- Product: the exact prompt text ("Add implementation specs to `workspace.toml`
  queue?") is specified in RFC-0064 and must not be changed without an erratum
  (source: RFC-0064 Batch 5 AC, Batch 5 table "Accepted-RFC path prompts…").
- Product: the dependency model reference doc location is `docs/product/` to
  keep workspace-related reference material co-located with `workspace.toml`
  and the product layer (source: user confirmation 2026-07-18; RFC-0064 §
  Proposed design names the doc's content but not its exact path).
- Process: RFC-0064 Batch 5 AC wording and RFC line 115 (M2.6) must be
  amended in this PR's implementing branch (not deferred as optional erratum).
  RFC-0064 is `Status: Draft`, so direct body edits are valid per CONVENTIONS
  §3 (Frozen rules apply only to Accepted/Rejected RFCs); no RFC-0055 erratum
  ceremony is required. The amendments cover: (a) Batch 5 "shaping artifact
  seeds" — clarified to exclude `shaping/` (M2-produced artifacts, not seeds);
  (b) RFC line 115 (M2.6) — reworded to say M2.6 *uses* the
  `initiatives/_template.md` Batch 5 seeds rather than creates it. These
  amendments are the sole changes to the RFC in this PR; no architectural
  decision is re-opened.
- Product: the RFC Batch 5 "shaping artifact seeds" clause is a no-op in this
  spec: shaping artifacts (`docs/product/shaping/`) are produced by PE skills
  (M2 six-step sequence), not seeded by templates; the two files already
  committed there are M2 priors, not Batch 5 deliverables.
