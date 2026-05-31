# Contract types → location and authoring skill

The `new-spec` seam (step 4b) is **contract-type-agnostic**. It uses this map to
(a) place a detected contract at its canonical location and (b) pick the
authoring skill for that type. The map lives **consumer-side, in `core`** — the
only surface visible regardless of where (or whether) an authoring pack is
installed: an authoring skill appears in the runtime roster by name, so the match
key is the **roster skill name**, not a pack manifest.

| Contract type | Conventional location | Authoring skill (roster name) |
| --- | --- | --- |
| openapi (REST API) | `contracts/openapi/` | `api-contract` |
| asyncapi (events) | `contracts/asyncapi/` | — (none bundled; direct-edit + note) |
| proto (gRPC) | `contracts/proto/` | — |
| graphql | `contracts/graphql/` | — |
| jsonschema | `contracts/jsonschema/` | — |
| jsonrpc | `contracts/jsonrpc/` | — |
| mcp | `contracts/mcp/` | — |

## How the seam uses it

1. **Locate.** Every type maps to a `contracts/<type>/` location, so the seam
   places *any* detected contract — events included — in its canonical spot, even
   when no authoring skill exists for that type.
2. **Author.** Look up the type's authoring skill and check your available-skills
   roster:
   - **Skill present** (today: `api-contract` for `openapi`) → invoke it. It
     authors/modifies the contract against the active standard, so the standard's
     compatibility rules catch breaking changes on an update.
   - **Skill absent** (today: every non-OpenAPI type, e.g. events) → author by
     **direct file-edit** and emit a note: *"no authoring skill for type
     `<type>` — authored without rule-enforcement."* Produce a serviceable file
     for YAML-shaped types (AsyncAPI, JSON Schema); a **stub + note** for formats
     you can't reliably hand-author unaided (proto, GraphQL). The contract still
     lands in its conventional, linked, traceable place — the integration never
     breaks; only enforcement degrades.

This is an **explicit table, not a naming algorithm**: a bring-your-own authoring
skill is wired in by filling a row's skill column (e.g. `asyncapi →
my-event-contract`) — a repo-scope edit needing no pack. Detection of a missing or
renamed skill is a **runtime note** at authoring time, not a build-time check
(nothing `core` reads at build time sees a user-scope or bring-your-own skill).

> A new contract type is added by appending a row (its `contracts/<type>/`
> location, and an authoring-skill name once one exists). The seam itself needs
> no change — it routes by this table.
