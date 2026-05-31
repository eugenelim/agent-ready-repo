# Plan: spec-contract-seam

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Five coherent PRs, governance-first. **T1** lays the foundation — the
CONVENTIONS amendment (the `contracts/<type>/` layout, naming/versioning,
traceability) + the ADR — so the seam, the lint, and the `adapt` branch all
reference a settled convention. **T2** adds the `new-spec` seam (the conditional
step, the `Contract:` header, the capability map). **T3** adds the traceability
invariant to `lint-spec-status.py` — the only piece with real logic (TDD). **T4**
adds the `adapt` Class 3 relocation branch + the narrow anti-pattern carve-out.
**T5** integrates — projects via `build-self`, runs both lint surfaces, flips
status.

Most of this is **agent-read skill prose + governance docs**: verification is
structural (grep) + manual QA, except the lint invariant which is genuine
testable logic. The riskiest part is **the lint no-opping cleanly in this repo**
(no `contracts/` tree) so `make build-check` stays green — and keeping the
`adapt` carve-out narrow. Because `core` is projected, every skill edit must go
through `build-self` and clear the projected-artifact lint.

Two dogfood notes: (a) this spec has **no** API surface, so the seam's "non-API
feature → existing path untouched" branch applies — no `Contract:` header on
this spec; (b) editing `new-spec` does not affect this in-flight spec (the seam
is for *future* API specs).

## Constraints

- **RFC-0017** — D5 (seam), D7 (convention-first discovery), D8 (`contracts/<type>/`
  tree + the anti-pattern reconciliation), D9 (lifecycle + traceability). Stage 2
  of the staged implementation (D6), depends on shipped Stage 1.
- **RFC-0016 / ADR-0007** — the doc-drift lint (`lint-spec-status.py`, run in
  `make build-check`) is the model and host for the traceability invariant.
- `docs/architecture/overview.md` — no `core` → `contracts` code import.
- CONVENTIONS changes are RFC-gated; RFC-0017 is the gate.

## Construction tests

Per-task tests live under **Tasks**. The cross-cutting concern is that the new
traceability invariant **no-ops cleanly in this repo** (no `contracts/` tree),
so `make build-check` stays green (verified in T3 and again in T5).

**Integration tests:** the lint invariant's no-contracts no-op path (T3) doubles
as the integration guard for this repo.
**Manual verification:** reason the seam through one API and one non-API feature
(T2).

## Tasks

### T1: Governance foundation — CONVENTIONS amendment + ADR

**Depends on:** none

**Touches:** `packs/core/seeds/docs/CONVENTIONS.md` (the **source** seed —
verified byte-identical to the projected top-level `docs/CONVENTIONS.md`),
`docs/adr/0008-*.md`, `docs/adr/README.md` (register row)

**Tests:** (goal-based)
- The CONVENTIONS **seed** has a section documenting the repo-level
  `contracts/<type>/` tree, the per-domain kebab-case naming + versioning
  (`info.version` + parallel-file for a breaking major), and bidirectional
  spec↔contract traceability, **citing RFC-0017** as the gate. Verifies the
  CONVENTIONS AC.
- `docs/adr/0008-*.md` exists (0007 is the current max), Status Accepted,
  recording: separate pack + agnostic convention-first seam (not a merge),
  repo-level contract tree, capability-name convention; **and its row is present
  in `docs/adr/README.md`**. Verifies the ADR AC.
- `git status` shows **no** `contracts/` directory created. Verifies the
  no-empty-tree AC.

**Approach:**
- Edit the **seed** `packs/core/seeds/docs/CONVENTIONS.md` (NOT the top-level —
  it is the projection); the top-level refreshes via `build-self` in T5.
- Write `docs/adr/0008-…md` (cite RFC-0017; cross-link `pluggable-api-standards`
  + this spec). ADRs are not seed-projected — top-level `docs/adr/` is source.
- Do **not** create `contracts/`.

**Done when:** the convention section (in the seed) + ADR-0008 are present and
RFC-0017-gated, with no `contracts/` directory.

### T2: The `new-spec` seam (conditional step + `Contract:` header + capability map)

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/.apm/skills/new-spec/assets/spec.md`,
`packs/core/.apm/skills/new-spec/references/contract-types.md`

**Tests:** (goal-based + manual QA)
- Grep `new-spec/SKILL.md` for a conditional contract step positioned between
  step 4 and step 5, naming: detect-and-confirm, locate/create at
  `contracts/<type>/`, delegate-if-roster-else-direct-edit+note, link via
  `Contract:`, point plan tests at the contract, and "non-API → untouched."
  Verifies the seam AC + convention-first AC.
- `new-spec/assets/spec.md` has the literal `- **Contract:**` header field
  alongside `Plan:` / `Constrained by:` — the exact token T3's invariant parses.
  Verifies the header AC.
- `new-spec/references/contract-types.md` has the `openapi → api-contract` row +
  the runtime-note degrade rule. Verifies the capability-map AC.
- (Manual QA) reason the seam through an API feature (authors into
  `contracts/openapi/`, links it) and a non-API feature (existing path
  untouched). Verifies the seam-behaviour Testing-Strategy mode.

**Approach:**
- Insert the conditional step in `SKILL.md` labelled **`4b`** (preserves the
  existing step 5–8 numbering, so cross-references to "step 6" etc. stay valid).
- Add the literal `- **Contract:**` field to `assets/spec.md` (commented like the
  others) — this exact token is what T3 parses; keep them in lockstep.
- Write `references/contract-types.md` (one-row `openapi → api-contract` table +
  degrade/runtime-note rule + the D7 "roster is the one surface visible
  regardless of scope" rationale, briefly).

**Done when:** the three greps pass and the manual-QA reasoning holds.

### T3: Traceability invariant in `lint-spec-status.py` (TDD)

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`,
`packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py` (the existing
sibling test, verified present)

**Tests:** (TDD — **tempdir fixtures** built under `tmp_path`, invoked via the
documented `python …/lint-spec-status.py --root <tmpdir>` subprocess, mirroring
the existing `test-lint-spec-status.py` `write_spec` pattern; no real `contracts/`
tree in this repo. **Warn-only:** findings land on **stderr with
`returncode == 0`**, matching invariant (iii).)
- **Agreement passes:** fixture spec with `- **Contract:** contracts/openapi/orders.yaml`
  + that file carrying an `x-spec` back-ref to the spec → no finding,
  `returncode == 0`.
- **Forward-without-backward warns:** `Contract:` names a contract lacking the
  back-ref → warning on stderr, `returncode == 0` (not a hard fail).
- **No-contracts no-op:** fixture tree with no `contracts/` directory → no
  traceability output (this repo's real state; guards `build-check` green).
- **Extensionless format:** a `proto`/`graphql` fixture contract resolves its
  back-ref via `contracts/REGISTRY.md`. Verifies the traceability-invariant ACs.

**Approach:**
- Add a traceability invariant function (pure: takes parsed `- **Contract:**`
  headers + scans `contracts/**` for `x-spec` / `REGISTRY.md`), wired into the
  existing invariant loop and `make build-check`, as **warn-only** — mirroring
  invariant (iii)'s deferred warn-only shape (`lint-spec-status.py`); elevation to
  hard is Ask-first.
- No new script, no new dependency (stdlib + the existing frontmatter parse).

**Done when:** the four tests are green and `make build-check` stays green in
this repo (no-op path).

### T4: `adapt` Class 3 contract-relocation + narrow anti-pattern carve-out

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/adapt-to-project/SKILL.md`

**Tests:** (goal-based + manual QA)
- Grep Class 3 for a contract-relocation branch naming the non-canonical sources
  (`api/openapi.yaml`, `swagger.json`, top-level `proto/`, `schemas/`), per-finding
  relocation into `contracts/<type>/`, **repo-scope only**, with downstream-path
  rewriting **out of scope**. Verifies the Class 3 AC.
- Grep the anti-pattern register for the **narrow carve-out** naming the
  RFC-0017-authorized `contracts/` root specifically, with the "absent it,
  relocate only into an existing tree" fallback; and assert the **"or a new
  package" clause survives byte-identical**. Verifies the carve-out AC.
- (Manual QA) read the carve-out to confirm it does not become a general license
  to invent directories.

**Approach:**
- Add the relocation branch under Class 3 (model it on the existing
  `DESIGN.md → docs/CHARTER.md` restructure).
- Amend the compound bullet `:280` ("Never add a new top-level directory **or a
  new package**") with the narrow `contracts/`-only exception; the **package
  clause must remain byte-identical** (the edit is surgical, directory-half only).

**Done when:** both greps pass and the carve-out reads as narrow.

### T5: Integration — projection, gates, status

**Depends on:** T1, T2, T3, T4

**Touches:** projected `.claude/skills/{new-spec,adapt-to-project,work-loop}/…`,
`docs/specs/spec-contract-seam/{spec,plan}.md`, `docs/specs/README.md`

**Tests:** (goal-based)
- `make build-self` exits clean; projected `.claude/skills/new-spec`,
  `.claude/skills/adapt-to-project`, **and `.claude/skills/work-loop/scripts/
  lint-spec-status.py`** (T3 edits work-loop source, which projects to every
  adapter) reflect the edits; `make lint-packs` and the projected-artifact lint
  (`tools/lint-agent-artifacts.py` / `pre-pr`) both pass; `make build-check`
  exit 0. Verifies the projection AC.
- `git status` shows no `contracts/` directory and no `core`→`contracts` import.
  Verifies the Stage-2-boundary AC + the no-code-dependency AC.
- (At ship) spec → Shipped with all ACs `[x]`, plan → Done, README synced
  (per "set final status in the implementing PR").

**Approach:**
- `make build-self`; verify with `git status` / `git ls-files` on the projected
  skill paths (watch for projection-only-edit reverts).
- Run both lint surfaces; flip statuses in the shipping PR.

**Done when:** all gates green, projection clean, statuses flipped, boundary
intact.

## Rollout

Ships as core skill + governance edits (no pack version bump — `core` is
versioned by `^0.1` caret-minor, unaffected by skill-body edits). Adopters get
the seam, the lint, the conventions, and the `adapt` relocation on next
`build-self` / install. Fully reversible — revert the PRs. The behaviour is
inert in this repo (no contracts authored here).

## Risks

- **Traceability lint false-fires or fails to no-op** in a repo with no
  `contracts/` → `build-check` red here. → the no-contracts no-op test (T3) is
  the explicit guard.
- **Anti-pattern carve-out read as a general license** → wording pinned narrow
  (T4) + manual-QA read.
- **`new-spec` seam bloats the skill body** → keep the step concise; push detail
  into `references/contract-types.md`.
- **CONVENTIONS seed vs. top-level source-of-truth confusion** → confirm which is
  source before editing (T1), then `build-self` (T5); watch for projection-only
  reverts ([[feedback_build_self_undoes_projection_only_edits]]).
- **Editing `core` skills regresses projected artifacts** → both lint surfaces
  guard (T5).

## Changelog

- 2026-05-31: initial plan. Governance-first 5-task breakdown. Decisions per
  RFC-0017 + author confirmation 2026-05-31: no empty `contracts/` tree in this
  repo; traceability lint extends `lint-spec-status.py` (no new script); one spec
  with CONVENTIONS + ADR as tasks; capability map is a one-row markdown table in
  `new-spec/references/`.
