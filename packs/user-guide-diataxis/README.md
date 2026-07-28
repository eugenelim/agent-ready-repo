# user-guide-diataxis (Deprecated)

> **This pack is deprecated.** Install [`product-documentation`](../product-documentation/README.md) directly.
>
> `user-guide-diataxis@0.3.0` installs `product-documentation` as a dependency, so if you have this pack installed you already have the new capability. The `new-guide` skill remains available as a compatibility shim — it activates on the same triggers and routes to `author-product-docs`.

## Migrating

Replace `user-guide-diataxis` with `product-documentation` in your install commands and profiles:

```bash
agentbundle install --pack product-documentation
```

The four-quadrant seed scaffold (`docs/guides/tutorials/`, `how-to/`, `reference/`, `explanation/`) is no longer installed. The `author-product-docs` skill inspects your repo's existing guide structure and writes to the appropriate location.

## What changed

- `new-guide` → `author-product-docs` (same triggers, five modes: create/revise/retrofit/audit/verify)
- No seed scaffold installed (Diátaxis is now a page contract, not a directory requirement)
- `core` dependency removed
- Available at `user` scope as well as `repo` scope (via the `product-documentation` dependency)

→ [Product Documentation pack](../product-documentation/README.md)
