# Guide sidebar ordering remains stable when curated labels change

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/guide-metadata-completion sidebar decision](../../specs/guide-metadata-completion/spec.md)

## Outcome

Maintainers can adopt a curated guide title without unintentionally reordering the guide's sidebar kind bucket.

## Opportunity

`project_guide_sidebar` orders kind buckets by the resolved reader-visible label, making title adoption and sidebar order coupled.

## What this absorbs

### guide-sidebar-label-order-coupling

`tools/build-site.py:881` sorts with `bucket.sort(key=lambda r: (_guide_label(r, baseline).casefold(), r["slug"]))`. Kind-bucket ordering therefore still depends on the resolved reader-visible label, so adopting a curated title necessarily reorders its bucket.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
