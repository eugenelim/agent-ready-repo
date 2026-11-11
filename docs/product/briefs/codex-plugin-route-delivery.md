# Brief: the catalogue emits a native Codex plugin package and marketplace

- **Slug:** `codex-plugin-route-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner, **on owner authority over the last review round**. Five independent delivery-brief reviews followed the correction of slice C1. The fifth returned `Findings` with two concerns and a nit, which were fixed afterwards and not independently re-reviewed; the owner took the gate on that, and this line is the record of it. `author-delivery-brief` otherwise requires a revision-bound `Clean`. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** [`FEAT-0022-codex-plugin-route.md`](../intents/FEAT-0022-codex-plugin-route.md), under [RFC-0092](../../rfc/0092-first-class-distribution-routes.md) and the [distribution-routes programme](distribution-routes-programme.md), Phase 3
- **Parent intent:** intent:codex-plugin-route

## Outcome

From the same catalogue source as the Claude marketplace, the build emits a native Codex plugin package and marketplace manifest. Claude and Codex publication are checked against one literal roster that agrees with the shared user-scope eligibility rule in `tools/pack_scope.py`, and a commit that touches none of a given publisher's trigger inputs does not schedule that publisher.

## Success metrics

- The Codex package and manifest are byte-stable across two builds and match golden fixtures.
- The Codex route's support claim stays components-only and `documentation-verified`.
- A change touching none of a publisher's declared trigger inputs (its entry in the C1 publisher list) does not trigger that publisher, proved by a path-filter test.

## Scope / Non-goals

In scope: the Codex route as a contract entry, package and marketplace emission, hook translation, the trigger-parity check across publishers, trigger suppression for the Codex publisher, and the publisher branch control.

Out of scope: adaptation or seed claims, widening user-scope eligibility, and any live Codex install check.

## Constraints / Appetite

Four slices. Hard predecessors: [FEAT-0020](../intents/FEAT-0020-distribution-route-set-opening.md) (a route is a contract entry) and [FEAT-0021](../intents/FEAT-0021-canonical-mcp-install-parity.md) (MCP, which the route claims). Slice C1 touches only the roster lint and its tests, and may ship first. C4 creates the Codex publish workflow under its own governance record. [ADR-0079](../../adr/0079-executable-plugin-branch-publisher-identity.md) decides only that a dedicated GitHub App may update `claude-plugins-dist`; the Codex publisher branch needs its own record. Owner: eugenelim. Default: a new ADR for the Codex publisher branch identity, drafted by an agent before C4 and accepted by the owner; it is C4's gate. The route stays components-only: FEAT-0021 is a predecessor because the route's capability map must carry an `mcp` row, recorded `dropped`. A pack declaring MCP is refused for the Codex route until a documented MCP path is recorded.

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| C1 | Extend the roster parity check (`tools/lint-plugin-roster.py`) from one hard-wired publisher workflow to a declared list of publishers, each naming its workflow file and job inputs. The user-scope eligibility rule is already one shared helper in `tools/pack_scope.py`, and a workflow path filter cannot read a file, so no new contract file is extracted. Alone it has one entry (Claude); C4 adds Codex. | `tools/lint-plugin-roster.py`, tests | Mutation cases: a synthetic publisher whose filter omits a rostered pack's path fails, and one that lists a path outside its expected inputs fails | None. Independent. |
| C2 | Codex route contract entry, package and marketplace manifest emission, vendored schema with provenance | `contracts/`, `build/` | Golden fixtures, offline schema validation, determinism and path-containment fixtures; a roster check that the emitted Codex marketplace manifest lists exactly the rostered packs (the existing check compares the roster only with the Claude marketplace) | After FEAT-0020 and FEAT-0021 |
| C3 | Hook translation with a semantic-compatibility record; refuse a pack whose required hook semantic cannot be kept | route projector | Fixtures per hook event: preserved, dropped-with-diagnostic, refused | After C2 |
| C4 | Create the Codex publish workflow, added to the C1 publisher list so its trigger paths are checked against the roster, with a fixed publisher branch and ref control | `.github/workflows` (new file), tests | Workflow posture test pins the trigger paths, branch name, and ref; a posture mutation for an unrelated path | After C1, C2, C3, and the Accepted governance record for the Codex publisher branch (a new ADR for the Codex publisher branch identity) |

## Assumptions / Risks

- **Riskiest assumption:** the route can stay components-only unless plugin root, persistent data, enablement, and consent prerequisites are documented. De-risk by vendoring the documented schema and making any gap a build diagnostic.
- Publisher and build-contract changes stay eligible trigger inputs, so marketplace output cannot go stale.

## Ready gaps (Draft only)

None open.

## Rabbit holes

- Do not widen user-scope eligibility to make the rule shared.
- Do not claim `runtime-verified` from documentation.

## Manual residue (named, non-blocking)

- A real Codex install and enable check, recorded once in the runtime-verification record from [FEAT-0024](../intents/FEAT-0024-claude-manifest-migration-support-claims.md). The route ships without it.

## Spec map

| Spec | Status |
| --- | --- |
| publisher-trigger-parity | Draft |

## Provenance

Derived from FEAT-0022 and the programme brief's Phase 3 row.
