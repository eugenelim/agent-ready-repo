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

## Status has one home

A slice's or artifact's status has exactly one home: the table or generated
projection that owns it. Link to that home instead of restating the status in
prose—not in a sibling brief, not in the parent intent, and not in the owning
brief's preamble. A delivery brief's coverage map owns spec status through its
`Status` column; `author-delivery-brief` owns the coverage and its rollups.
Registered spec membership in `workspace.toml` is the confirmation evidence
surfaced in that map, so a confirmed slice without a registered entry leaves
the parent brief with no execution evidence. A slice's `Gating` cell owns its
gating, and a brief's `- **Status:**` line owns its lifecycle state.

Reasoning about a dependency is not the same as asserting its state. An
argument for why one slice must wait for another is content and belongs where
the argument is. “U2 is unconfirmed”, “D1 shipped on 2026-09-04”, and “brief X
is Executing” are status statements and belong only in the owning home.

An obligation on a sibling is discharged by changing that sibling's own cell
or amendment record. Nothing re-reads the prose that recorded the obligation,
so record it once where the sibling owns it and link there.

Nothing mechanically catches a restated status. It has no owner and nothing
re-checks it, so it goes stale silently while reading as current.
