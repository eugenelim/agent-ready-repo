# Guide sidebar ordering remains stable when curated labels change

- **Slug:** `guide-sidebar-label-ordering`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [guide publishing and sidebar contract](../../architecture/site-publishing.md#1-authored-content-is-projected-never-edited-in-place)

## Disposition — withdrawn 2026-11-05, decided: not worth doing now

the kind-bucket sort at `tools/build-site.py` (`bucket.sort(key=...label.casefold()...)`) is the accepted behavior of `spec/guide-metadata-completion`, which measured and approved the reorder from adopting curated titles (125 labels, 10 buckets; [historical acceptance](https://github.com/eugenelim/agent-ready-repo/blob/7bdd03da0a93a35883ef1d32a121ec361b99211d/docs/specs/guide-metadata-completion/spec.md)). If a fixed order is wanted later, add the optional `order` frontmatter field in a new intent.

## Outcome

Maintainers can adopt a curated guide title without unintentionally reordering the guide's sidebar kind bucket.

## Opportunity

`project_guide_sidebar` orders kind buckets by the resolved reader-visible label, making title adoption and sidebar order coupled.

## What this absorbs

### guide-sidebar-label-order-coupling

`project_guide_sidebar` in `tools/build-site.py` sorts with `bucket.sort(key=lambda r: (_guide_label(r, baseline).casefold(), r["slug"]))`. Kind-bucket ordering therefore still depends on the resolved reader-visible label, so adopting a curated title necessarily reorders its bucket.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
