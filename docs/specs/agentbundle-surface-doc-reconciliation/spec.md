# Spec: reconcile architecture docs with the agentbundle surface

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Contract:** none — prose corrections in `docs/architecture/` and one shipped
  explanation guide, plus one `workspace.toml` queue entry. No engine change, no
  CLI/API/schema surface touched.

Mode: light (no risk trigger fired)

Mode call: two deliverables land in one PR, but they are independent prose/queue
edits — not a multi-feature brief being decomposed into specs, and not
inter-dependent tasks. No other trigger fires: familiar territory, one author,
no security boundary, no structural or public-interface change, nothing
destructive, no new dependency.

## Objective

`docs/architecture/` describes an `agentbundle` that no longer exists: a v0.6 /
v0.14 adapter contract (it is v0.17), four adapters (every shipped one is
declared), a verb table that still lists a verb removed in 0.2.0 while omitting
most of what shipped since, and relative links that still point at the pre-ADR-0055 `docs/contracts/` and
`docs/guides/` trees. One shipped adopter guide carries the same stale contract
path.

Separately, a catalogue `search` verb is named as a gap in RFC-0031's diagnosis
but owned by nothing — no queue entry, no backlog slug, no spec. It needs to be
queued behind the index it would read, not implemented.

## Acceptance Criteria

**D1 — architecture drift**

- [x] **AC1 — contract currency.** Every *present-tense* "the contract is
      currently vN" claim in `docs/architecture/` reads v0.17 and attributes the
      bump to RFC-0052 (shared-prefix registry), the RFC that shipped it.
      Correctly-historical attributions ("added in v0.6 per RFC-0011",
      "`< 0.6` packs", "enriched-pack-manifest … v0.14") are left intact.
      Sites: `agentbundle.md` (contract-version paragraph, primitive bullet,
      user-scope bullet), `overview.md`, `pack-layout.md`, `pack-manifest.md`.
- [x] **AC2 — pack contract targets.** `agentbundle.md`'s claim that four named
      packs target v0.6 and four repo-only packs target v0.2 is replaced with a
      statement true of the tree (no pack targets either version today) and
      phrased without a total-coupled count or a pack-name enumeration that
      re-rots on the next pack.
- [x] **AC3 — adapter set.** `agentbundle.md`'s bundler-pipeline step 3 and the
      `list-targets` verb row name all eight shipped adapters
      (`claude-code`, `codex`, `copilot`, `cursor`, `gemini`, `kiro-ide`,
      `kiro-cli`, and `kiro` as the deprecated alias for `kiro-ide`) rather
      than four, and say `kiro` is the alias rather than dropping it.
- [x] **AC4 — verb table.** The verb table in `agentbundle.md` matches
      `agentbundle --help` from this tree: `creds` is gone, and `show`, `docs`,
      `package-catalogue`, `catalogue`, `lint`, `pack`, `pack-config`, `oplog`
      are present with descriptions derived from the CLI's own help/docstrings,
      not invented.
- [x] **AC5 — relative links resolve.** Every relative link in the
      `docs/architecture/` files this change touches resolves to a file that
      exists on disk, verified by resolving the path — not by grepping that the
      string changed.
- [x] **AC6 — shipped guide.** `guides/_shared/explanation/pack-catalogue.md`
      references `contracts/adapter.toml`, and the changelog question is answered
      with a recorded determination either way.
- [x] **AC7 — exclusions held.** `docs/adr/0055-*`, `docs/rfc/0008-*`,
      `docs/rfc/0010-*`, and
      `docs/specs/agentbundle-skill-spec-lint-and-evals/spec.md` are unmodified.
      An unfiltered post-edit re-grep for `../contracts/` and for `v0.6` / `v0.14`
      across `docs/` and `guides/` shows every remaining hit is one of these
      deliberate exclusions or a correct historical attribution.

**D2 — queue the `search` verb**

- [x] **AC8 — queued, not implemented.** `workspace.toml` gains exactly one
      `["ini-007".work].queue` entry for a local catalogue `search` verb. No
      code, no `docs/specs/` directory, and no second owner for it elsewhere —
      in particular no `[backlog].open` slug for `search`. No implementation.
- [x] **AC9 — gated on the index.** The entry declares
      `needs = "work:spec/catalogue-wave4-semantic-contracts-index"`, and its
      comment records the substrate dependency, that this is the local read
      surface only (hosted search stays a non-goal per RFC-0031 and ini-007),
      and that new-wave-vs-RFC-0031-follow-on is an open question for whoever
      picks it up.
- [x] **AC10 — blocked, not ready.** `workspace-status` reports the entry as
      blocked on Wave 4 rather than ready to start.

## Boundaries

Out of scope, and deliberately untouched:

- **Frozen governance.** `docs/adr/0055-*` (its `docs/contracts/` mentions *are*
  the record of the move), `docs/rfc/0008-*`, `docs/rfc/0010-*` (4 stale relative
  links there need an Approver-signed erratum, not a doc PR), and
  `docs/specs/agentbundle-skill-spec-lint-and-evals/spec.md:49` (shipped spec —
  historical record of what that spec touched).
- **Engine.** No change to `cli.py`, the adapters, or the contract. Two CLI-side
  drifts found while reading ground truth are surfaced in the PR description
  rather than fixed here: `list-targets`' own `--help` string still names only
  six targets (its *output* is correct), and `tools/repo/check_release_impact.py`
  still lists the pre-ADR-0055 `docs/contracts/` prefix instead of `contracts/`.
  Both were recorded in `[backlog].open` as
  `agentbundle-surface-doc-reconciliation-engine-stragglers`, and both were
  **resolved on 2026-08-16** by `spec/agentbundle-engine-stragglers` (agentbundle
  0.36.0): the help string now names all eight registry adapters with a drift test
  behind it, and the release-impact prefix is `contracts/`. That backlog entry is
  closed.
- **Implementing `search`.** D2 queues; it does not build.

## Verification

Goal-based throughout — this change ships prose and a TOML entry, and both are
verified by running the thing that reads them.

- `SKIP_SAST=1 make build-check` exits 0.
- A link resolver walks every relative link in each touched Markdown file and
  reports zero misses (path resolution, not string matching).
- `agentbundle --help` from this tree is diffed against the verb table by hand.
- `workspace-status` is run and its treatment of the new entry read from output.
- Unfiltered re-greps for `../contracts/`, `docs/contracts/`, `v0.6`, `v0.14`.

### Determination — no changelog entry for the guide fix (AC6)

`guides/_shared/explanation/pack-catalogue.md` gets no `[Unreleased]` line.
`docs/product/changelog.md` is release-scoped — every entry hangs off a package
or pack version — and this change bumps nothing: no verb, flag, exit code,
schema, or output structure moved. `tools/repo/check_release_impact.py`, the
gate that decides whether a diff owes a release, lists neither `guides/` nor
`docs/architecture/` as release-impacting. A stale path corrected in an
explanation page has no version to attach to.

## Tasks

1. **T1 — contract currency + pack targets** (AC1, AC2). `agentbundle.md`,
   `overview.md`, `pack-layout.md`, `pack-manifest.md`. Read each flagged line
   before editing; leave historical attributions alone.
2. **T2 — adapter set** (AC3). `agentbundle.md` step 3 prose + `list-targets` row.
3. **T3 — verb table** (AC4). Regenerate from `agentbundle --help` and each
   command module's docstring.
4. **T4 — relative links** (AC5). `../contracts/` → `../../contracts/` in
   `skill-and-pack-format.md`, `agentbundle.md`, `pack-manifest.md`,
   `pack-layout.md`. The `../guides/` set in the same tree is the same
   ADR-0055 defect and is fixed as a bundled ride-along (see PR description).
5. **T5 — shipped guide + changelog determination** (AC6).
   `guides/_shared/explanation/pack-catalogue.md:62`.
6. **T6 — queue entry** (AC8, AC9, AC10). `workspace.toml` `["ini-007".work].queue`.
7. **T7 — gates + unfiltered sweeps** (AC5, AC7, AC10).

## Assumptions

- **RFC-0052 shipped v0.17.** Grounded: the contract's own v0.17 note
  ("shared-prefix registry", cohort routing of `skill` to `.agents/skills/`)
  matches RFC-0052's index entry verbatim in substance, and no other RFC
  describes the bump.
- **`kiro` remains a shipped deprecated alias**, not a removal — the contract
  still declares `[adapter.kiro]`, so docs name it as an alias rather than
  dropping it.
