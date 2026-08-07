# Review report — guides-sidebar-generation

Adversarial review: **Clean — ready to commit.**
Quality-engineer: findings raised and closed (see below).

Eleven rounds across spec and implementation. Spec-stage rounds found 22 issues;
implementation rounds found a further 30. Findings that changed the design
rather than the wording:

- `order` was already in use by four `atlassian` pages as a cross-kind,
  pack-level sequence. The planned pack→kind→order grouping would have
  scattered it one page per bucket.
- Filename-derived labels regress 90 of 119 existing sidebar labels, and 13
  pages carry a `title:` differing from their nav label — so the label chain had
  to resolve baseline first, not frontmatter first.
- `site.toml`'s `[[groups]]` cannot express `_shared` (39 pages), because
  `discover_packs()` skips underscore-prefixed slugs.
- `guides/_shared/<kind>/README.md` are guide-authoring templates, not adopter
  content, and were never in the pre-change sidebar.
- The tests documented the implementation rather than constraining it: two
  reviewers independently showed by mutation that deleting the eligibility rule
  or the duplicate-slug tie-break left the whole suite green.

Every guard added at REVIEW was verified by mutation — the reviewer reproduced
each independently and confirmed it kills exactly its named test.
