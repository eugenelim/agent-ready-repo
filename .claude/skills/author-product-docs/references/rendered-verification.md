# Rendered verification

Verification scope is proportionate to the change. A content-only edit and a
navigation restructure warrant different levels of checking.

## Scope by change type

### Content-only edits (no navigation or layout changes)

- Confirm the rendered page displays the new content correctly.
- Check that internal links in the changed file resolve.
- Verify code blocks and commands render without truncation.

### Navigation changes (new page, moved page, renamed slug)

All of the above, plus:
- Verify the new or moved page appears in the sidebar or index where expected.
- Verify old routes return a redirect or 404, not silently stale content.
- Check that cross-links from sibling pages pointing to this page still resolve.
- Confirm the page title and breadcrumb match the file's heading.

### Page-layout changes (new sections, restructured headings)

All of the above, plus:
- Confirm the heading hierarchy is valid (no h3 under h1, no skipped levels).
- Check anchor links resolve after heading changes.
- Verify the page renders without broken layout at standard viewport widths.

### Responsive behavior

Check at three viewport widths: mobile (~375px), tablet (~768px), desktop
(~1280px). Flag wrapping issues in tables, overflow in code blocks, and nav
items that disappear at narrow widths.

### Accessibility

- Confirm image alt text is present and describes the image, not the filename.
- Verify heading levels are not used for visual styling (h2 for emphasis is wrong).
- Check that link text is descriptive ("learn more" is not descriptive).

### Links

Before declaring a change ready, run the renderer's link checker or manually
verify that every new or changed link resolves. Do not write a link that has
never been checked.

### Source versus rendered drift

Generated pages (rendered from templates or data) must not be hand-edited.
When a rendered page is stale, update the source data or template. If you
cannot identify the source, state this explicitly rather than editing the
rendered output.

---

## What "claimed verification" means

A verification claim ("I have verified the rendered output") is only valid if
the renderer was actually run and the output was actually inspected. Do not
claim verification that did not happen. If the renderer is unavailable, state
that the verification was not performed and describe what would need to be run.
