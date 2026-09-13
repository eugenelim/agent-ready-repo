# AGENTS.md — `docs/product/`

Applies to `docs/product/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Editing the changelog: `/now/` needs nothing from you

The public `/now/` page is projected from the `### Highlights` blocks of
released sections in `changelog.md`. **Edit the changelog and stop there.**

`web/src/lib/now-highlights.generated.json` is generated, gitignored, and
rebuilt by every `npm run` script in `web/` and `docs-site/` that imports it, so
there is no second copy to keep in step and nothing to commit alongside your
edit. This replaced a rule that asked you to regenerate and commit the JSON in
the same change; a forgotten regeneration is how a stale `/now/` page reached
production, and the fix was to remove the step rather than to detect it later.

Write each highlight as a `-` bullet. The parser extracts only bullets, so a
paragraph is dropped silently — that is still true, and
`test_the_generator_projects_the_real_changelog_into_a_valid_payload` is what
catches a release whose highlights stop projecting.

To see your edit rendered, run `make site-build` and open `build/now/index.html`.

`changelog.md`'s own header owns how to write a highlight and which releases
owe one; [`packs/AGENTS.local.md`](../../packs/AGENTS.local.md) owns the pack
release pipeline that records that decision.
