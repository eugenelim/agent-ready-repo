# A consumer pack proves user-scope hook support in a live installation

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0005 First consumer](../../rfc/0005-user-scope-hook-support.md)
- **Authority:** [spec/user-scope-hooks AC3](../../specs/user-scope-hooks/spec.md)

## Outcome

A maintained consumer pack declares a user-scope hook and proves that the hook fires through a live install transcript.

## Opportunity

`spec/user-scope-hooks` is Shipped, but fixture packs measure correctness and no pack contains a hook or hook-wiring source, so no real user-scope hook-bearing consumer exists; Rail B, the user-scope hook-wiring merge story, remains blocked.

## What this absorbs

### user-scope-hooks-first-consumer

The first user-scope hook-bearing consumer pack remains deferred under RFC-0005 § First consumer. Author or designate a consumer pack declaring `allowed-scopes = ["user"]` and wire a hook at user scope. Confirm that the hook fires through a live install transcript. `CONTRIBUTING.md:61` says, “If you claim `user` scope, justify it.” Unblocks when: a pack maintainer wants to ship a user-scope hook.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
