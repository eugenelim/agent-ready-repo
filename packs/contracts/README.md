# contracts

Contract-authoring skills for API and event design. `api-contract` drives
OpenAPI 3.1; `event-contract` drives AsyncAPI events.

## What's inside

- `api-contract` — author and review OpenAPI 3.1 contracts.
- `event-contract` — author and review AsyncAPI event contracts.

## Install

`contracts` is **user-scope by default** — contract style is portable across
projects.

```
agentbundle install --pack contracts <catalogue>
```

## Usage

Ask your agent, for example:

- "Draft an OpenAPI 3.1 contract for the orders service: create, get, cancel."
- "Review this OpenAPI spec for breaking changes against the previous version."
- "Design an AsyncAPI contract for the `order.placed` event stream."

---

→ **Go deeper:** the [`contracts` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/contracts/).
