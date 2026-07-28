# user-guide-diataxis — Deprecated

> **This pack is a deprecated compatibility shim.** It has no seeds and no
> authoring capability of its own. Install
> [`product-documentation`](../product-documentation/) directly for all new
> work.

## Migration

```
agentbundle install --pack product-documentation <catalogue>
```

The `author-product-docs` skill replaces `new-guide` and supports five modes:
create, revise, retrofit, audit, and verify. It is directory-agnostic — no
four-quadrant folder scaffold is installed.

## What changed

`user-guide-diataxis` 0.2.x installed a `docs/guides/` skeleton with four seed
READMEs (tutorials, how-to, reference, explanation) and the `new-guide` skill.

Version 0.3.0 is a shim only: it depends on `product-documentation`, has no
seeds, and provides a thin `new-guide` redirect that names `author-product-docs`
as the canonical skill.

## Important: install order

agentbundle does not auto-install this shim's dependencies. A bare:

```
agentbundle install --pack user-guide-diataxis <catalogue>
```

will fail with "install product-documentation first" if `product-documentation`
is not already present. Install `product-documentation` first:

```
agentbundle install --pack product-documentation <catalogue>
agentbundle install --pack user-guide-diataxis <catalogue>
```

For profile-based installs, both packs must appear in the profile.

---

→ [product-documentation guides](../../guides/product-documentation/)
