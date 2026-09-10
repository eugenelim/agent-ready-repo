# AGENTS.md — `docs/product/`

Applies to `docs/product/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Regenerate `/now/` with the changelog change

The public `/now/` page is projected from the `### Highlights` blocks of
released sections in `changelog.md`. When you add or edit one, regenerate the
projection in the same change and commit both files:

```bash
python3 tools/build-site.py --journeys-only   # writes web/src/lib/now-highlights.generated.json
python3 -m pytest tools/test_build_site_routing.py -k now -q
```

A changelog edit committed without the regenerated JSON fails
`test_the_committed_now_projection_matches_the_changelog_source` with
``web/src/lib/now-highlights.generated.json is stale — run `python3
tools/build-site.py --journeys-only` ``.

`changelog.md`'s own header owns how to write a highlight and which releases
owe one; [`packs/AGENTS.local.md`](../../packs/AGENTS.local.md) owns the pack
release pipeline that records that decision.
