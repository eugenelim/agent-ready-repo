# ADR-0008: Contract authoring integrates via an agnostic, convention-first seam (not a core merge); contracts live in a repo-level tree

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-05-31
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0017 (pluggable API-contract standards + spec-driven contract seam); `pluggable-api-standards` spec (Stage 1, shipped); `spec-contract-seam` spec (Stage 2); ADR-0007 (doc-drift lint as a work-loop skill script)

## Context

`new-spec` (in the always-installed `core` pack) authors `spec.md` + `plan.md`
as a pair, with no gap to author an API contract between them; the `api-contract`
authoring skill lives in the user-scope-default `contracts` pack. The two were
decoupled islands, a contract had no canonical home or lifecycle, and the
spec→contract→plan chain only fired if a human strung it by hand (RFC-0017
diagnosis). RFC-0017 is Accepted and asks how to wire contract authoring into the
spec loop and give contracts a durable, traceable home **without breaking the
"compose around `core`, packs don't import each other" model** — and while
keeping `core` the agnostic, always-installed base that imposes REST on no one.

Three invariants constrain the answer (`docs/architecture/overview.md`): packs
don't import each other's code; `core` is repo-only while `contracts` is
user-scope default; `core` is the agnostic base.

## Decision

> We integrate contract authoring into `new-spec` through an **agnostic,
> convention-first seam**, not by merging `contracts` into `core`; and contracts
> live in a **repo-level `contracts/<type>/` tree**, discovered by location
> convention with a capability-name lookup that degrades gracefully.

Specifically:

1. **Separate pack + agnostic seam (not a merge).** `api-contract` stays in
   `contracts`. `core`'s `new-spec` gains a conditional step anchored on the
   *location convention* and the contract *type*; `core` imports no code from
   `contracts`. Folding `contracts` into `core` is rejected — it would be the
   first cross-pack code import, force `contracts` to repo-only, and impose REST
   on every adopter.
2. **Repo-level contract tree.** Contracts live at the repo root under
   `contracts/<type>/` (`openapi`, `asyncapi`, `proto`, …) — a single
   source of truth many specs can create and modify over time, not per-feature
   files under `docs/specs/<feature>/`. This is a new top-level directory,
   authorized by RFC-0017.
3. **Convention-first, two-layer discovery.** *Artifact* discovery is by the
   `contracts/<type>/` location convention (the load-bearing anchor — needs no
   installed skill). *Capability* discovery derives the expected authoring-skill
   name from the contract type and checks the agent's runtime skill roster; if
   present it delegates authoring, if absent it falls back to a direct file-edit
   and a runtime note. The type→skill map is an explicit table living
   **consumer-side in `core`'s seam** (the only surface visible regardless of the
   `contracts` pack's install scope or a bring-your-own skill), not in any pack
   manifest. So a missing authoring skill degrades *enforcement*, never the
   *integration*.

## Consequences

**Positive:**
- The pack model holds — convention-coupling, not import-coupling; `core` stays
  agnostic and dependency-free.
- Contracts gain a durable home and bidirectional spec↔contract traceability
  (forward `Contract:` header; backward `x-spec` / `contracts/REGISTRY.md`),
  kept honest by an in-repo warn-only lint.
- The integration is robust to a missing or renamed authoring skill (the
  contract still lands in its conventional, linked, traceable place).

**Negative:**
- A new top-level directory and two new conventions (folder layout, traceability)
  for adopters to learn; "contracts" now names three surfaces (the pack,
  `docs/contracts/`, and repo-root `contracts/`) — disambiguated by path.

**Neutral / to revisit:**
- v1 covers OpenAPI/REST only; other contract types (AsyncAPI, proto, …) plug in
  as new `contracts/<type>/` rows + roster entries without re-touching `core`.
- A runtime multi-standard resolver remains deferred (RFC-0017 Open Q1).

## Alternatives considered

- **Merge `contracts` into `core`** — discoverable, but breaks the three
  invariants above. Rejected.
- **Pure roster name-lookup (no location convention)** — makes a cross-pack name
  load-bearing on `core`'s critical path. Rejected for convention-first.
- **Pure location convention (no roster lookup)** — loses standard-enforcement
  when a skill *is* installed. Rejected; the hybrid keeps enforcement
  opportunistic.
- **Contracts in the spec folder / a separate contracts repo** — ties a contract
  to one feature, or breaks the in-repo spec↔contract drift gate. Rejected for
  the repo-level tree.

## References

- RFC-0017 — Decisions D1 (separate pack + agnostic seam), D7 (convention-first
  discovery), D8 (repo-level tree), D9 (lifecycle + traceability).
- `docs/specs/spec-contract-seam/spec.md` — the Stage 2 implementation contract.
