# Spec: guides-readme-outcome-label-drift

- **Status:** Shipped (its deferral `catalogue-site-tests-absent-from-ci` was closed by [`build-check-coverage-gaps`](../build-check-coverage-gaps/spec.md), so that register anchor no longer resolves; not a supersession — every decision here stands)
- **Owner:** eugenelim
- **Plan:** none — light mode, single task
- **Contract:** none. One documentation table cell; no schema, code, or
  behaviour change.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light. Routed by AGENTS.md § How we work's cosmetic/tightly-local
carve-out: one table cell, behaviour-preserving, verified by a named test that
already exists. Not by an exception to the published-interface trigger — that
trigger is stated unconditionally and `guides/` is shipped adopter copy this
diff changes visibly, so claiming it "does not fire" would be inventing an
exception the trigger list does not contain. -->

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

1. **A test contract binds the markdown surfaces to it.** The binding authority
   is `tools/test_catalogue_navigation.py` (added by #927), which names
   `NAVIGATION_SOURCE` and asserts its titles appear in both
   `MARKDOWN_SURFACES`. Its docstring frames the split: the marketing surfaces
   "import one outcome map", while the markdown entry points "remain authored
   for their medium, so this test keeps their labels aligned". Aligned to what
   is not symmetric — the map is the source, the markdown is the consumer.

   Note the source's own header is narrower than this and cannot carry the
   argument alone: it reads "Canonical outcome and role routes **for the
   marketing site**", and its second paragraph binds only "those two entry
   surfaces". It claims no authority over the adopter-facing `guides/` tree.
   The test does.
2. **The drift is one-sided.** `Start, remember, build, and review software`
   occurred exactly once repo-wide before this change (`guides/README.md:11`);
   after it, only this spec quotes the string. #958
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

- [x] **AC4 — the full navigation contract passes**, not just the
  previously-failing case: § Testing Strategy's pytest run reports zero
  failures across every case in the file, since the pack-membership and
  role-route cases read the same source.

- [x] **AC5 — the pack-link contract still holds.** § Testing Strategy's
  `check-guide-index.py` run exits 0. It verifies every active pack has a
  guide-home link in this file; the edited row carries three of them.

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
- Never touch the other six outcome rows, the role list, or the flagship
  paragraph below the table.

## Testing Strategy

Goal-based check — the failing gate is the test:

- `python3 -m pytest tools/test_catalogue_navigation.py -q` → zero failures
  (was 1 failed, 3 passed).
- `python3 tools/check-guide-index.py` → exit 0.
- `SKIP_SAST=1 make build-check` → the repo policy gates that read `guides/`.
- `SKIP_SAST=1 make ci` → exit 0, which is the claim this PR actually makes.

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
  lint, and it is correct. What it is not is *enforced*: it is named only at
  `Makefile:349`, inside `make test`, and appears in no workflow under
  `.github/workflows/`. So it never ran on #958's PR — which is why that PR
  merged green and left `main` red for everyone who ran `make ci` locally. A
  second copy of the same lint would inherit the same gap; wiring is the fix,
  and it is deferred below rather than half-done here.
- **Wiring the test into `build-check.yml` in this PR.** The gap is not one
  test: 7 of the 13 files on `Makefile:349` are a run step in no workflow
  (`test_validate_guides`, `test_check_guide_index`, `test_catalogue_navigation`,
  `test_documentation_entry_links`, `test_build_site_link_rewrites`,
  `test_check_rendered_site_links`, `test_build_site_routing`). Wiring one and
  leaving six would read as coverage that is not there, and every added step
  needs a `lint-ci-parity` disposition. Deferred as
  `catalogue-site-tests-absent-from-ci` so the recurrence risk is registered
  rather than lost with the entry this PR closes.

  Counted per-file across all of `.github/workflows/`. Two traps, both of which
  produced a wrong count on the first pass: `test_check_rendered_site_links`
  appears in `pages.yml` only as a `paths:` trigger, never as a run step; and
  `test_catalogue_tooling_rewire` / `_docs` *are* run, by Gate F of
  `catalogue-tooling-ci-gates.yml`, so they are not in the list — though that
  workflow's `paths-ignore` covers `docs/**`, `guides/**`, `docs-site/**` and
  `web/**`, so it does not gate doc-surface PRs either.
- **Appending a resolution line to the `bandit-nosec-comment-hygiene` spec's
  § Known skip**, which points at the register entry this PR removes. That
  spec is Frozen (`docs/CONVENTIONS.md` § Document lifecycle: "Status fields
  can change …, bodies cannot"), and appending to a body is a body edit however
  additive it reads. The legal mechanism for annotating a frozen spec is
  exactly what `frozen-spec-supersession-convention` is deciding; pre-empting
  it with a one-off body edit here would prejudge that decision. Deferred, with
  that spec named as a caller once the convention lands.
