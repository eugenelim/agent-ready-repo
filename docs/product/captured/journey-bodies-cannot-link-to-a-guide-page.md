# Journey bodies cannot link to a guide page

- **Status:** Open
- **Kind:** defect

## Summary

packs/core/JOURNEY.md:300 is a live 404 on the published site because sync_pack_journeys copies journey bodies verbatim and a Markdown body link is not base-qualified the way docsUrl is; it is the only guide link across 20 JOURNEY.md files, so packs have no working way to link a guide page, and the rendered-site link audit did not cover the journeys route
