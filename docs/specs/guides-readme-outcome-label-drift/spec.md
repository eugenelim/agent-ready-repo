# Spec: guides-readme-outcome-label-drift

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — light mode, single task
- **Contract:** none. One documentation table cell; no schema, code, or
  behaviour change.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (no risk trigger fired). Checked the published-interface
trigger explicitly: it does NOT fire. `guides/` ships to adopters, but this
restores a label to the value the canonical map already publishes on every
other surface — it removes a divergence rather than introducing one. -->

## Objective

`tools/test_catalogue_navigation.py::test_markdown_entry_points_keep_canonical_outcome_labels`
fails on a clean `origin/main`, so `make ci` is red for everyone. The test
asserts every canonical outcome title appears verbatim in each markdown entry
point; `guides/README.md` carries `Start, remember, build, and review software`
where the canonical map says `Build and review software`.

Success: the two sides agree again, `make ci`'s catalogue-navigation leg is
green, and the capability #958 was describing survives.

## Which side is canonical

The navigation source, `web/src/lib/catalogue-navigation.ts`. Three independent
reasons:

1. **It says so, and the wiring backs it.** Its own header calls it the
   "Canonical outcome and role routes"; `PackCatalogue.astro` and
   `catalogue/index.astro` import it rather than restating it, and
   `test_marketing_surfaces_import_the_canonical_map` fails if either declares
   its own list. The markdown entry points are aligned consumers — the test
   docstring calls them "authored for their medium".
2. **The drift is one-sided.** `Start, remember, build, and review software`
   occurs exactly once repo-wide (`guides/README.md:11`). #958
   (`feat(core): add canonical work-intake routing`) reworded that one cell and
   left the source, `docs-site/src/content/docs/index.mdx`, and both marketing
   surfaces on the canonical wording. One consumer moved; the source did not.
3. **Register.** Every other title names an outcome the reader wants — *Decide
   what to build*, *Document what ships*, *Provision and release safely*. The
   README's column header is `I need to…`, and "I need to start, remember,
   build, and review software" enumerates the pack's verbs instead of naming
   the job. Work intake is part of building, not a fourth peer outcome.

So `guides/README.md` is realigned to the source, not the reverse.

## Acceptance Criteria

- [x] **AC1 — the title cell matches the canonical map.**
  `guides/README.md`'s third outcome row reads `**Build and review software**`,
  byte-identical to `catalogue-navigation.ts`'s `build` outcome `title`.

- [x] **AC2 — #958's actual contribution survives.** The row's *description*
  cell keeps `[`core`](core/) to route work into a durable artifact and
  supervised loop`. Work-intake routing is a fact about what `core` does; it
  belongs in the cell that describes the pack, not in the outcome label. Only
  the title cell changes.

- [x] **AC3 — the assertion is untouched.** No edit to
  `tools/test_catalogue_navigation.py`, and no edit to
  `web/src/lib/catalogue-navigation.ts` or
  `docs-site/src/content/docs/index.mdx`. The gate is not moved to meet the
  code.

- [x] **AC4 — the full navigation contract passes.**
  `python3 -m pytest tools/test_catalogue_navigation.py -q` reports 4 passed —
  not just the one previously-failing case, since the pack-membership and
  role-route cases read the same source.

- [x] **AC5 — the pack-link contract still holds.**
  `python3 tools/check-guide-index.py` exits 0. It verifies every active pack
  has a guide-home link in this file; the edited row carries three of them.

- [x] **AC6 — the backlog entry is dispositioned.**
  `pre-existing-guides-readme-outcome-label-drift` is removed from
  `workspace.toml [backlog].open`, and the known-skip paragraph in
  `docs/specs/bandit-nosec-comment-hygiene/spec.md` is left alone — it is a
  Shipped spec recording what was true when it shipped.

## Boundaries

### Never do

- Never weaken or delete the assertion. The test caught a real divergence
  between a published label and its source; that is the test working.
- Never edit the canonical map to match the consumer. That inverts the
  direction the whole navigation contract is built around.
- Never touch the other five outcome rows, the role list, or the flagship
  paragraph below the table.

## Testing Strategy

Goal-based check — the failing gate is the test:

- `python3 -m pytest tools/test_catalogue_navigation.py -q` → 4 passed
  (currently 1 failed, 3 passed).
- `python3 tools/check-guide-index.py` → exit 0.
- `SKIP_SAST=1 make build-check` → the repo policy gates that read `guides/`.

## Assumptions

- #958 intended to advertise work-intake routing, not to rename the outcome.
  Supported by the diff: it changed the title and description cells of one row
  in one file, in a PR whose subject is `add canonical work-intake routing`,
  and touched no navigation source. Had a rename been intended, the canonical
  map and the docs-site LinkCard were the files to edit.

## Declined

- **Promoting #958's wording to canonical.** It would change the marketing
  homepage, the catalogue page, and the docs-site featured LinkCard for a label
  that names the pack's mechanism rather than the reader's outcome. A bigger
  diff, on the surface adopters see first, to publish the worse of the two
  strings.
- **A new lint that pins markdown labels to the source automatically.**
  `test_markdown_entry_points_keep_canonical_outcome_labels` already is that
  lint. It fired correctly and was skipped, not missing.
- **Fixing the known-skip paragraph in the `bandit-nosec-comment-hygiene`
  spec.** That spec is Shipped; its § Known skip is an accurate record of the
  tree it shipped against. Editing it would rewrite history to describe a
  present that spec never saw.
