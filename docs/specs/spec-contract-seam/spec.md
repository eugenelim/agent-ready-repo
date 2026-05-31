# Spec: spec-contract-seam

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0017

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Wire contract authoring into the spec loop, and give contracts a durable home.
Today `new-spec` authors `spec.md` + `plan.md` with no gap to author an API
contract between them, and a contract has no canonical location or lifecycle.
This is **Stage 2** of RFC-0017 (Stage 1, `pluggable-api-standards`, shipped).

For a feature that exposes an interface surface, `new-spec` gains a
**conditional, contract-type-agnostic seam**: detect the surface and its type
(REST/OpenAPI, events/AsyncAPI, RPC/proto, GraphQL, schemas — the seam routes
*any* type, not just REST), locate or create the contract at its conventional
path (`contracts/<type>/`), **delegate authoring to the type's skill if one is
installed — else fall back to a direct file-edit and note the absence**, link it
from the spec via a `Contract:` header, and point the plan's construction tests
at it. v1 bundles only the OpenAPI authoring skill (`api-contract`); every other
type — events included — still routes to `contracts/<type>/` and degrades to a
direct-edit + note. Contracts become **long-lived,
repo-level, single-source-of-truth** artifacts that many specs can create and
modify over time, with **bidirectional spec↔contract traceability** (forward
`Contract:` header; backward `x-spec` extension or `REGISTRY.md`) kept honest
by an in-repo lint.

The integration is **convention-first**: the location convention
(`contracts/<type>/`) is the load-bearing anchor; the type→skill roster lookup
only selects the authoring skill and **degrades gracefully** when absent. `core`
gains none of this as a code dependency on `contracts`.

**This catalogue repo ships the *mechanism* — it authors no contracts of its
own** (it has no API surface). The seam, the lint, the `adapt` relocation, the
conventions, and the ADR ship to adopters and **no-op here**; the repo-root
`contracts/` tree is *authorized* by RFC-0017 but **not created** here (Decision
1, confirmed by author).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit **source**, never a projection: core skills under
  `packs/core/.apm/skills/{new-spec,work-loop,adapt-to-project}/…` and the
  CONVENTIONS **seed** `packs/core/seeds/docs/CONVENTIONS.md` (top-level
  `docs/CONVENTIONS.md` is its byte-identical projection). Then `make build-self`;
  run **both** lint surfaces (`make lint-packs` and the projected-artifact lint
  `tools/lint-agent-artifacts.py` / `pre-pr`) — `core` **is** projected.
- Keep the seam **conditional and graceful**: a non-API feature runs the
  existing spec→plan path untouched; a missing authoring skill degrades to a
  direct file-edit + a note and **never blocks** (D5/D7).
- Keep the integration **convention-first**: the `contracts/<type>/` location
  convention is the anchor; the type→skill roster match is an enhancement, never
  on the critical path (D7).
- Keep the seam **contract-type-agnostic**: every type (events/AsyncAPI, proto,
  GraphQL, schemas) routes to `contracts/<type>/` and degrades the same way REST
  does; the only type-specific thing v1 ships is the OpenAPI authoring *skill*.
- Keep adopter-facing **skill** content free of **catalogue RFC numbers** —
  adopters don't have our RFCs; put provenance in the ADR + spec (governance).
  Real external standards (IETF RFC 9457, etc.) are fine.
- Record the **RFC-0017 gate** for the CONVENTIONS amendment in **ADR-0008 + this
  spec** (catalogue governance) — keep the adopter-facing CONVENTIONS **seed**
  placeholder-shaped (no catalogue RFC number; `lint-seeds` forbids it). Keep the
  `adapt` anti-pattern carve-out **narrow** (only the authorized `contracts/`
  root).

### Ask first

- Adding any type→skill row beyond `openapi → api-contract` (other contract
  types are deferred — D4).
- Making the traceability lint a **hard/fail-closed** gate rather than the
  warn-only shape RFC-0016's dangling-ref invariant uses.
- Materializing an actual `contracts/` directory in this repo (default: no).

### Never do

- Create an empty repo-root `contracts/` tree in **this** repo — convention
  only here (Decision 1).
- Make `core` import from or depend on `contracts` (compose-around-core
  invariant, `docs/architecture/overview.md`).
- Ship a **non-OpenAPI authoring skill or its rules** (v1 bundles only
  `api-contract`/OpenAPI; D4). The seam **routing** every type to
  `contracts/<type>/` and degrading is *in scope* — building a non-OpenAPI
  authoring *engine* is the deferred follow-on. No runtime multi-standard
  resolver (RFC-0017 Open Q1).
- Put a **catalogue RFC number** in adopter-facing skill content (it ships to
  adopters who don't have our RFCs); provenance goes in the ADR + spec.
- Relax the `adapt` "never add a new top-level directory" rule into a general
  license — the carve-out names the RFC-authorized `contracts/` root **only**.
- Add a **new standalone lint script** for traceability — extend
  `lint-spec-status.py` (Decision 2).
- Add a new third-party dependency.

## Testing Strategy

- **Seam presence & shape** (the conditional step, the `Contract:` header, the
  capability map) — *goal-based check.* Grep the skill body and template for the
  step, the header field, and the `openapi → api-contract` row + degrade rule.
  *Why:* skill prose is verified by structural presence, not a unit test.
- **Seam behaviour** (detect → locate/create → delegate-or-degrade → link →
  point plan tests; non-API path untouched) — *manual QA.* Reason through an API
  feature and a non-API feature against the skill body. *Why:* the behaviour is
  agent-executed prose; the contract is "the skill says the right thing."
- **Traceability lint invariant** — *TDD.* It is a pure function over files
  (parse `Contract:` headers + `x-spec`/`REGISTRY.md` back-refs, check
  agreement). *Why:* real logic with a compressible invariant; red-green covers
  agreement / forward-without-backward / no-contracts-no-op.
- **`adapt` Class 3 relocation + anti-pattern carve-out** — *goal-based + manual
  QA.* Grep the branch and the carve-out; read the carve-out to confirm it is
  narrow, not a general license.
- **CONVENTIONS amendment + ADR** — *goal-based.* Sections present, RFC-0017
  cited as the gate, no empty `contracts/` dir created.
- **Projection** — *goal-based.* `make build-self` clean; both lint surfaces
  green; projected `.claude/skills/{new-spec,adapt-to-project}` reflect the
  edits.

## Acceptance Criteria

- [x] `new-spec/SKILL.md` carries a **conditional contract step between step 4
  (fill spec) and step 5 (fill plan)**: detect an interface surface + its type
  (auto-detected, confirmed with the user), locate or create the contract at
  `contracts/<type>/`, delegate to the type's authoring skill if present in the
  roster else direct-edit + note, link via the `Contract:` header, and point the
  plan's construction tests at the contract. A non-API feature runs the existing
  path untouched.
- [x] `new-spec/assets/spec.md` carries a `Contract:` header field — the literal
  token `- **Contract:**` — alongside `Plan:` / `Constrained by:`. This exact
  token is the shared contract between the seam (writes it) and the traceability
  invariant (parses it).
- [x] `new-spec/references/contract-types.md` is the consumer-side,
  **type-agnostic** registry — a table mapping every known contract type to its
  `contracts/<type>/` location and authoring skill: `openapi → api-contract`
  (bundled), and the other types (events/`asyncapi`, `proto`, `graphql`,
  `jsonschema`, `jsonrpc`, `mcp`) to their location with **no bundled skill**
  (degrade to direct-edit + note). The seam routes *any* type, events included;
  the runtime-note degrade rule is documented.
- [x] The seam is **convention-first**: the skill body states the
  `contracts/<type>/` location is the anchor and that a missing authoring skill
  degrades to a direct file-edit + a note, never blocking.
- [x] **Adopter-ready skill content:** the seam's adopter-facing skill content
  (the 4b step, `contract-types.md`) and the `adapt` contract carve-out carry
  **no catalogue RFC numbers** (adopters don't have our RFCs) — RFC-0017
  provenance lives in ADR-0008 + this spec. Real external standards (e.g. IETF
  RFC 9457) are unaffected. (`RFC-0017` no longer appears anywhere under
  `packs/`.)
- [x] The CONVENTIONS **seed** `packs/core/seeds/docs/CONVENTIONS.md` (source of
  truth; top-level `docs/CONVENTIONS.md` is its projection) records the repo-level
  `contracts/<type>/` tree, the per-domain kebab-case naming + versioning
  (`info.version` + parallel-file for a breaking major), and bidirectional
  spec↔contract traceability — in **adopter-generic / placeholder shape** (no
  catalogue-specific RFC number, so `lint-seeds` passes), and projects cleanly via
  `build-self`. The **RFC-0017 gate** for this convention is recorded in
  **ADR-0008** and this spec (catalogue governance), not the adopter-facing seed.
  **No empty `contracts/` directory is created in this repo.**
- [x] Bidirectional traceability is specified: forward via the spec `Contract:`
  header; backward via an `x-spec` vendor extension (OpenAPI/AsyncAPI) with
  `contracts/REGISTRY.md` as the fallback for extensionless formats.
- [x] `lint-spec-status.py` gains a **traceability invariant** checking
  forward/backward agreement (the `- **Contract:**` spec header ↔
  `x-spec`/`REGISTRY.md` back-ref) that **no-ops when no `contracts/` tree
  exists**, is **warn-only** (mirrors RFC-0016 invariant (iii)'s deferred
  warn-only shape — finding lands on stderr, `returncode == 0`), and runs through
  the existing `make build-check`.
- [x] The traceability invariant has construction tests (TDD) over **tempdir
  fixtures** (build spec+contract trees under `tmp_path`, invoke `--root <dir>`
  per the existing `test-lint-spec-status.py` `write_spec` pattern — no real
  `contracts/` tree in this repo): agreement passes (no finding); a forward ref
  with no backward ref warns (stderr, `returncode == 0`); no `contracts/` tree
  no-ops; an extensionless format resolves via `REGISTRY.md`.
- [x] `adapt-to-project/SKILL.md` Class 3 gains a **contract-relocation branch**:
  walk for contracts in non-canonical locations (`api/openapi.yaml`,
  `swagger.json`, top-level `proto/`, `schemas/`), propose per-finding relocation
  into `contracts/<type>/`, repo-scope only, with downstream-path rewriting
  explicitly out of scope.
- [x] `adapt-to-project/SKILL.md`'s compound anti-pattern bullet "Never add a new
  top-level directory **or a new package**" is amended with a **narrow carve-out**
  for the RFC-0017-authorized `contracts/` root specifically (not a general
  license); the **"or a new package" clause stays byte-identical**; absent the
  carve-out, Class 3 relocates only into an existing tree.
- [x] A new **ADR (0008)** records the decisions — separate pack + agnostic
  convention-first seam (not a merge); repo-level contract tree; the
  capability-name convention — **and its row is added to `docs/adr/README.md`**.
- [x] `core` imports no code from `contracts` (convention-coupling only).
- [x] `make build-self` re-projects cleanly and both lint surfaces pass.
- [x] No new contract type/authoring skill, no runtime resolver, no new
  dependency, and no empty `contracts/` directory in this repo (Stage-2
  boundary).

## Assumptions

- Process: RFC-0017 Accepted; this is Stage 2, depending on the now-shipped
  Stage 1 (`pluggable-api-standards`, PR #196) (source: `docs/rfc/0017…md`; git).
- Technical: the seam inserts between `new-spec` step 4 and step 5; the
  `Contract:` header lands in `new-spec/assets/spec.md` alongside `Plan:` /
  `Constrained by:` (source: `packs/core/.apm/skills/new-spec/SKILL.md:120,138`
  + assets header read).
- Technical: capability discovery reuses the **step-6 roster pattern** ("subagent
  matching … absence is a note, not a blocker") (source: `new-spec/SKILL.md`
  step 6 — cited by step number since T2's step-insertion shifts line numbers).
- Technical: the anti-pattern to carve is `adapt-to-project/SKILL.md:280`; Class
  3 is at `:203` (source: repo read).
- Technical: `core` is projected by `build-self`, so the skill edits engage
  both lint surfaces — unlike Stage 1's user-scope `contracts` pack (source:
  `self_host.py` `SELF_HOST_PACKS`).
- Technical: `docs/contracts/` (adapter schemas) and the `contracts` pack both
  exist; repo-root `contracts/` is greenfield; the catalogue has no API contract
  of its own (source: `ls` + `git ls-files`).
- Technical: RFC-0016's doc-drift gate is `lint-spec-status.py` run in
  `make build-check` — the model and host for the traceability invariant
  (source: Makefile + repo read).
- Process: CONVENTIONS changes are RFC-gated; RFC-0017 is the gate (source:
  `update-conventions` skill + RFC-0017 Follow-on artifacts).
- Decision: no empty `contracts/` tree created in this repo — convention only
  (source: confirmed by author 2026-05-31).
- Decision: the traceability lint extends `lint-spec-status.py`, not a new
  script (source: confirmed by author 2026-05-31).
- Decision: Stage 2 is one spec; the CONVENTIONS amendment + ADR are plan tasks
  within it (source: confirmed by author 2026-05-31).
- Decision: the type→skill capability map is a markdown table in a `new-spec`
  reference file, one row `openapi → api-contract` (source: confirmed by author
  2026-05-31).
