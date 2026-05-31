# Contract types → authoring skills

The `new-spec` seam (step 4b) uses this map to pick the authoring skill for a
detected contract type. It lives **consumer-side, in `core`** — the only surface
visible regardless of where (or whether) the authoring pack is installed: a
user-scope `contracts` skill and a hand-dropped bring-your-own skill both appear
in the runtime roster by name, so the match key is the **skill name in the
roster**, not a pack manifest.

| Contract type | Conventional location | Authoring skill (roster name) |
| --- | --- | --- |
| openapi (REST) | `contracts/openapi/` | `api-contract` |

## How it's used

Derive the type from the detected interface surface, look up the expected skill
name here, and check your available-skills roster:

- **Skill present** → invoke it. It authors/modifies the contract against the
  active API standard, so the standard's compatibility rules catch breaking
  changes on an update.
- **Skill absent** → author the contract by **direct file-edit** and emit a
  runtime note: *"expected `<skill>` for type `<type>` not found — authored
  without rule-enforcement."* The contract still lands in its conventional,
  linked, traceable place. The integration does not break; only enforcement
  degrades.

This is an **explicit table, not a naming algorithm**, so the legacy name
`api-contract` (which authors OpenAPI) is absorbed without a rename, and a
bring-your-own skill is wired in by adding one row
(`graphql → my-graphql-contract`) — a repo-scope edit needing no pack. Detection
of a rename or absence is a **runtime note** at authoring time, not a build-time
lint: nothing `core` can read at build time sees a user-scope or BYO skill.

> **v1 ships one row (OpenAPI).** Other contract types — AsyncAPI, proto,
> GraphQL, JSON-Schema, JSON-RPC, MCP — plug in as new rows + new
> `contracts/<type>/` locations without re-touching `core` (RFC-0017 D4 / D7).
