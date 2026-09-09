# Plan: install-to-ship-walkthrough

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** root [`AGENTS.md`](../../../AGENTS.md);
  [`docs/AGENTS.md`](../../AGENTS.md); [`web/AGENTS.md`](../../../web/AGENTS.md);
  [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md);
  [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) §§ 5b and *A spec directory
  freezes as a unit*; the Shipped
  [`documentation-entry-navigation`](../documentation-entry-navigation/spec.md)
  spec, which owns all four entry surfaces this slice edits.

## Approach

`guides/README.md` already carries six ordered paths under `## Follow a path`.
Rename that section to the walkthrough, lift the sixth path out of it so the
stage sequence is unambiguous, add a successor link to each of the first four
stages, and point three entry surfaces at the renamed heading.

The editorial change is larger than a rename: five stages gain or keep
prerequisite and first-value lines, four gain a successor link, one path moves to
its own section, and three entry surfaces gain a link. Existing guidance prose is
not rewritten.

**Spike, 2026-09-08 — anchor mechanism confirmed.** A throwaway build of the
unchanged tree (`tools/build-site.py`, then `npm run build --prefix web`, then
`npm run build --prefix docs-site`) emitted `build/docs/guides/index.html`
carrying `id="follow-a-path"` for the authored `## Follow a path` heading, and
`id="p1--adopt-the-catalogue--1-hour"` through
`id="p6--extend-the-catalogue--3-hours"` for the six stage headings. All three
commands exited 0. The durable record of that run — commands, exit codes, and
the observed heading/id pairs — is
[`notes/verification-ledger.md`](notes/verification-ledger.md); the session
scratch logs behind it are ephemeral and are not offered as auditable evidence.
The spike was not committed; `build/` is ignored by `.gitignore:66`.

## Constraints

- The marketing and documentation sites deploy under the `/agent-ready-repo`
  subpath. Marketing links must go through `withBase()`; origin-root paths fail.
- `web/` cleans repository `build/`, so it must build before `docs-site/` writes
  `build/docs/`. The canonical order is `tools/build-site.py`, then
  `npm run build --prefix web`, then `npm run build --prefix docs-site`
  (`docs-site/AGENTS.md` § Build).
- A site build in this worktree requires `npm ci` in both `web/` and
  `docs-site/`; a fresh worktree has neither `node_modules` tree.
- Two gates, not one. `tools/test_documentation_entry_links.py` runs under
  `make test` via the file list at `Makefile:584`.
  `web/src/test/rendered-output.test.ts` runs only under
  `npm test --prefix web` — no `make` target invokes it; CI reaches it through
  `.github/workflows/pages.yml:192`. Every task that adds a case to the web
  suite must run that command explicitly.
- `docs-site/src/content/docs/guides/` is generated. Edits go to `guides/`.
- From plan approval this pair is pinned in substance. Execution observations go
  to [`notes/verification-ledger.md`](notes/verification-ledger.md), never into
  this file (`docs/CONVENTIONS.md` § *A spec directory freezes as a unit*).

## Construction tests

**One altitude for the structural checks.** AC1–AC11 and AC13 all describe what
the *published site* shows a reader, so each is checked by reading emitted HTML
in `web/src/test/rendered-output.test.ts` — the only shipped suite that inspects
the consuming renderer. AC12 is not one of these: it is a set difference between
the recorded baseline and the emitted route list, run as a step in T5 rather
than as an assertion over one page.

It already resolves every surface these criteria name, which is what makes one
suite sufficient: `BUILD_ROOT` and `homePage` (`build/index.html`) reach the
marketing landing page for AC8, `DOCS_HOME` reaches the documentation home for
AC9, `DOCS_ROOT` reaches the getting-started page for AC10 and the guide hub for
AC1–AC7 and AC11, and its `walk(...)` helper enumerates emitted pages for AC12
and AC13. No new fixture, root, or helper is needed.

A source-altitude copy of these checks was designed and cut. It bought nothing
the rendered check does not already prove, and it could be satisfied by content
a reader never sees: the repository's source suite strips fenced code but not
HTML comments, so a walkthrough authored entirely inside `<!-- -->` would pass a
raw-source heading scan while rendering nothing. Emitted HTML has no such
escape.

`tools/test_documentation_entry_links.py` still runs and still owns
documentation-entry navigation generally; this slice adds no case to it, and
adds `InstallTerminal.astro` to no tuple. An earlier draft of this plan claimed
that adding the component to `MARKETING_SOURCES` would bring the marketing link
under existing fragment validation. That claim was false: `_check_site_route`
returns after resolving a docs route without checking the supplied fragment, and
fragment validation applies only to filesystem-relative links. The rendered
check covers the fragment instead.

Design notes the implementer cannot infer:

- The AC3 activity list is written into the test from the spec's enumerated
  eight. Reading it out of the page would make the check unable to fail.
- AC2's stage set is asserted as an ordered sequence of the stage headings inside
  the emitted walkthrough section. Because T2 moves the catalogue-extension path
  to its own sibling section, "the stages in this section" and "the five
  walkthrough stages" are the same set, so AC6's "every stage but the last"
  needs no hard-coded exception.
- AC6, AC8, AC9, and AC10 each need **one** assertion that binds an anchor's
  `href` and its text content together. Two independent assertions — a correct
  target somewhere on the page and the naming words somewhere on the page — pass
  on a page where they belong to different elements. AC6 additionally binds both
  to the stage being walked: stage *n*'s successor link must name and target
  stage *n+1*, not merely some stage.
- AC4 and AC5 are separate criteria over the same stage set, and neither is a
  label-presence check. AC4 parses each stage's prerequisite and requires it to
  resolve to `none` or to earlier stage names drawn from AC2's ordered set — a
  forward or invented reference fails. AC5 collects the five first-value strings
  and requires each non-empty and all five distinct. Presence of the labels
  alone would pass on placeholder text.
- AC12 compares set membership against `notes/route-baseline.txt`, never a
  count: a build that drops one route and adds another preserves the count. The
  baseline is a plain sorted list of 288 routes with no header or comment lines,
  so the comparison is a set difference over the file's lines and needs no
  parser.

## Durable-output map

| Spec durable output | Task | Evidence at closeout |
| --- | --- | --- |
| User-facing promise (`guides/README.md`) | T2 | AC1–AC7 cases in `web/src/test/rendered-output.test.ts` |
| Marketing entry | T3 | AC8 case in the same suite |
| Documentation-home entry | T4 | AC9 case in the same suite |
| Funnel continuity (getting-started) | T4 | AC10 case in the same suite |
| Interface compatibility | T1, T5 | `notes/route-baseline.txt` recorded at T1; membership comparison recorded in the ledger at T5 |
| Operations (execution observations) | T1, T5 | `notes/verification-ledger.md` |

## Design (LLD)

`Shape: mixed` — the surfaces are one guide document, two MDX pages, and one
Astro component. The `ui` sub-sections are thin because no component is
designed; the marketing change is one sentence inside an existing section.

### Design decisions

- **The walkthrough is the existing `## Follow a path` section, renamed** — not a
  new section beside it. A second ordered list of the same guides would give one
  fact two homes with nothing keeping them in sync.
- **The catalogue-extension path moves to its own sibling section.** This is what
  makes AC2 and AC5 checkable without an unstated exception: while it sits inside
  the walkthrough as a sixth `###` heading, no structural rule distinguishes a
  stage from a branch, and a successor link pointing into it would pass a naive
  "every stage but the last" check.
- **The eight activities map onto the existing five stages** rather than
  motivating new ones. Where a stage does not already name its activity, T2 adds
  the naming to that stage's prose.
- **Entry links carry the heading anchor**, not the bare hub URL, so a reader
  lands on the route rather than the top of the page.

### Behavior & rules

Renaming the heading changes its emitted id. Starlight's on-this-page navigation
and heading permalink are generated from the heading and follow it. No authored
page links to `#follow-a-path`, so the Boundaries § Ask first trigger does not
fire; an inbound authored link found before T2 lands reopens that decision.

### Failure, edge cases & resilience

- A reader arriving mid-walkthrough from search gets the stage's prerequisite
  line, which AC4 requires every stage to carry.
- The marketing link is cross-site. It resolves in the combined deployment and is
  audited by the rendered link check, which runs after both site builds.

### Dependencies & integration

No new dependency. `npm ci` in `web/` and `docs-site/` restores the pinned trees
already declared in their lockfiles.

## Tasks

### T1: record the accepted-base route set

- **Depends on:** none
- **Mode:** goal-based check
- **Implements:** the baseline AC12 compares against
- **Tests:** none authored; this task's output is a committed artifact.
- **Approach:** `npm ci` in both workspaces, then build in canonical order.
  Write the sorted list of emitted internal routes to
  `notes/route-baseline.txt` and commit it — `build/` is ignored and the web
  build cleans it, so an uncommitted build cannot serve as a baseline. Record
  the commands and their exit codes in `notes/verification-ledger.md`.

### T2: name the walkthrough and make its stages followable

- **Depends on:** T1
- **Mode:** goal-based check
- **Implements:** AC1–AC7, AC14
- **Tests:** eight cases in `web/src/test/rendered-output.test.ts`, over the
  emitted guide hub page. The ordered stage sequence and the activity list are
  written into the test; the prerequisite check resolves each stage's stated
  prerequisite against AC2's ordered stage names; the first-value check asserts
  presence and pairwise distinctness; the successor assertion walks the emitted
  stage headings and, for each stage, binds one anchor's text and target to the
  next stage; and the AC14 case asserts the relocated catalogue-extension
  section still links to all four guides it names.
- **Approach:** rename the section, then move the catalogue-extension path out
  to its own sibling section **whole** — heading, prerequisite line, all four
  numbered step links, first value, and ends-at line. Relocating the heading
  alone would leave an empty marker, which is what AC14 exists to catch. Then
  state what the route is and where it ends, ensure every stage carries a
  prerequisite and a first-value line, and add a successor link to each of the
  first four stages.

### T3: enter the walkthrough from the marketing landing page

- **Depends on:** T2
- **Mode:** goal-based check
- **Implements:** AC8
- **Tests:** one case in `web/src/test/rendered-output.test.ts` binding the
  anchor's `href` and text together on the emitted landing page.
- **Approach:** extend the existing `install__note` paragraph in
  `InstallTerminal.astro` with the named link, through `withBase()`. No new
  component; `web/src/pages/index.astro` is untouched.

### T4: enter the walkthrough from the documentation surfaces

- **Depends on:** T2
- **Mode:** goal-based check
- **Implements:** AC9, AC10
- **Tests:** two cases in `web/src/test/rendered-output.test.ts`, each binding
  `href` and text on the same anchor.
- **Approach:** add the featured entry above the outcome grid in `index.mdx`, and
  a first item in the getting-started `## Continue` list.

### T5: verify the generated route

- **Depends on:** T2, T3, T4
- **Mode:** goal-based check
- **Implements:** AC11, AC12, AC13
- **Tests:** cases in `web/src/test/rendered-output.test.ts` for the emitted
  heading id and for internal-link resolution on the three entry surfaces.
- **Approach:** rebuild in canonical order, then run four gates explicitly:
  `npm test --prefix web` for the suite carrying every case this slice adds (no
  `make` target invokes it); `make test` for the repository suite, which must
  stay green even though this slice adds no case to it;
  `npm run test:e2e:gate --prefix web`, the browser gate `web/AGENTS.md` names
  as essential, which must stay green — it visits the marketing routes, the docs
  home, and one nested guide, so it does not exercise the walkthrough anchors
  themselves; and `make site-link-check`. Then compute the set difference
  `notes/route-baseline.txt` minus the emitted route list and require it empty.
  Record every command, its exit code, and the difference result in
  `notes/verification-ledger.md`.

## Rollout

- **Delivery:** big bang, single PR. Fully reversible by reverting the commit; no
  state, no migration, no flag.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the site build order in § Constraints is the only
  ordering requirement.

## Risks

- **A check passes on a link no reader can see.** Partly retired: the standing
  cases read emitted HTML rather than source, so commented-out content cannot
  satisfy them. CSS-level concealment is **not** covered — the browser gate does
  not visit the guide hub or getting-started, and its marketing route set is
  another spec's ratified constant. `spec.md` § Testing Strategy records this as
  an accepted gap rather than a covered case.
- **The successor chain is asserted against a stage set that includes the
  catalogue-extension branch.** Retired by T2 moving that path out of the
  walkthrough section before the check is written.
- **A case lands in the web suite and no local gate runs it.** Retired by T5
  naming `npm test --prefix web` explicitly; `make test` does not reach it.
- **The walkthrough drifts from the paths it names.** The stage assertion is
  ordered and named rather than counted, so a path added later moves the check
  instead of silently passing.

## Changelog

- 2026-09-08 — Initial plan drafted from brief slice S1.
- 2026-09-08 — Revised against two independent spec-stage reviews (round 1).
  Split the entry-link checks into source and rendered altitudes; moved the
  catalogue-extension path out of the walkthrough so the stage set is
  unambiguous; replaced the scalar route count with a committed route-set
  baseline; added `notes/verification-ledger.md` as the home for execution
  observations; named the two distinct gate invocations; corrected the claim that
  the entry-link suite already covers `InstallTerminal.astro`.
- 2026-09-09 — Round 2. Six of ten findings were introduced by round-1 repairs,
  so this revision **reduces** rather than extends. The source-altitude copy of
  the structural checks is cut: every standing case now reads emitted HTML,
  which removes the HTML-comment escape the source suite has and removes the
  false claim that `MARKETING_SOURCES` membership validates a site link's
  fragment. Added the browser gate to T5 for computed visibility, which JSDOM
  cannot establish; stated AC5's per-stage binding; made `route-baseline.txt` a
  plain comment-free set and moved its provenance to the ledger; named the AC11
  comparison as an explicit set difference.
- 2026-09-09 — Round 3. Again a reducing revision. Split AC4's bundled
  prerequisite-and-payoff predicate into two criteria (13 criteria now, AC5
  onward renumbered); removed the AC10 escape hatch that would have let an
  unexpected emitted id be accommodated rather than fail; withdrew the claim
  that the browser gate covers walkthrough-link visibility, since its
  `DOCS_ROUTES` reaches only `/` and one nested guide and its `MARKETING_ROUTES`
  is another spec's ratified constant — CSS-level concealment is now a recorded
  accepted gap; gave every durable output a living owner instead of "this spec";
  moved test-placement machinery out of the spec's Boundaries; replaced the
  ledger's false slug rule with the four observed heading/id pairs.
- 2026-09-09 — Round 4 (final review round; four findings, none blocking).
  AC4 and AC5 were label-presence checks that placeholder text would satisfy, so
  AC4 now resolves each prerequisite against AC2's ordered stage names and AC5
  requires five present, pairwise-distinct first values. Added AC14, appended
  rather than renumbered so AC1-AC13 keep their identifiers, because relocating
  the catalogue-extension path could otherwise leave an empty heading that
  passes AC7. Corrected criterion references the AC4/AC5 split left stale in the
  ledger and the spec's assumptions. Dropped the spike's unresolvable
  `runs/spike/` log locator: the ledger is the durable record, and the scratch
  logs are not offered as auditable evidence.
- 2026-09-09 — Round 5 (owner-requested). One finding, nonmaterial: the
  owner-admitted-scope assumption still named AC9 after the round-3 renumbering
  moved the getting-started entry to AC10. Corrected as a cross-reference fix;
  no criterion, mechanism, boundary, or task changed. The reviewer found no
  delivery defect across AC1-AC14, the factual assertions, task dependencies,
  criterion coverage, gate reachability, or the route-baseline format.
