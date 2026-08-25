# Brief: Make the public technology sites reviewably complete

- **Slug:** `tech-site-completion`
- **Received:** 2026-08-17
- **Owner:** Platform Core (`ini-002`)
- **Status:** Shipped

## Outcome

People evaluating, adopting, and using the catalogue can move coherently across
the marketing site, documentation, published guides, catalogue pages, and
journeys without broken contracts, unexplained visual divergence, incomplete
content, or quality checks that exist only as manual knowledge. Maintainers have
one canonical programme map that records what remains, what is already shipped,
what has been superseded, and how every accepted slice will be proved through
emitted-site behavior.

## Success metrics

- Every registered site-related legacy item has one durable disposition:
  materialized, merged into a named canonical owner, retained with an explicit
  trigger, or closed with provenance.
- Both sites build in the required order and all agreed link, fragment,
  rendered-output, contrast, accessibility, responsive, and construction-test
  gates pass against emitted output.
- Every in-scope guide and priority journey satisfies its approved metadata,
  content, orientation, and navigation contract.
- The programme reaches zero unresolved product, design, content, governance,
  sequencing, or technical decisions before implementation is declared
  complete.

## Scope / Non-goals

**In scope:**

- The marketing site under `web/` and Starlight documentation under
  `docs-site/`.
- Published adopter guides under `guides/`.
- Catalogue and journey pages rendered by either site.
- Site generation, build ordering, rendered-output tests, link and fragment
  checks, contrast and accessibility checks, responsive evidence, deployment
  workflows, and their CI gates.
- The governance, durable design rules, content decisions, and sequencing
  needed to close the registered debt listed below.

**Non-goals:**

- New product capabilities, routes, navigation destinations, or dependency
  additions beyond the approved replacement of public `/work/` with released-
  outcome `/now/`.
- Aligning the docs palette with the marketing palette or replacing pinned
  Starlight behavior.
- Reopening shipped SEO, sitemap, canonical, robots, npm-SCA, or superseded
  site-shell work without contradictory repository evidence.
- Treating framework-owned behavior or speculative ideas as defects without a
  demonstrated user outcome.
- Absorbing doctrine, profile, distribution, or portfolio work that already has
  a separate registered owner.
- Implementation in the shaping and persistence session.

## Appetite

A bounded programme of eight ordered completion waves, not a redesign quarter.
Work that requires a new dependency, another route or navigation change,
palette unification, or feature expansion leaves this programme unless an
approved amendment explicitly changes the boundary.

## Rabbit holes

- Do not force the two sites to share CSS, component implementations, or color
  tokens merely to make them look alike.
- Do not generate human summaries, titles, journey transcripts, severity
  classifications, or credibility claims.
- Do not infer journey anchors by normalizing display text; use canonical IDs.
- Do not enable screenshot-writing or tautological browser tests as required CI
  merely because they already exist.
- Do not rewrite frozen shipped-spec bodies; use the canonical supersession
  annotation mechanism.
- Do not duplicate the historical problem/fix briefs from `workspace.toml` in
  derived specs; reference the registered slug and this brief's disposition.
- Do not name the external visual reference in tracked files or Git artifacts.

## Instrumentation

- Full `workspace-status reconcile` output before materialization and after the
  programme's lifecycle transactions.
- Generator, rendered-output, link/fragment, guide metadata, catalogue, and
  contrast test results in CI.
- Deterministic browser evidence across the approved route, theme, and viewport
  matrix, plus a recorded physical-device release check.
- Print audit evidence for representative landing, guide, code-heavy, aside,
  and long-table pages.

## Completion definition

The technology sites are complete when all of the following are true:

1. Every relevant legacy item is materialized, merged with a named owner,
   retained with an explicit trigger, or closed with provenance.
2. The shipped Starlight architecture is ratified and the stale frozen Phase 4b
   reference is annotated without rewriting its body.
3. Durable site principles are committed in the design-principles artifact;
   docs palette separation and pinned framework contracts remain intact.
4. Existing routes and navigation contracts are preserved except for the
   approved removal of public `/work/` and addition of `/now/`.
5. Every agreed public guide has reviewed metadata or an explicit non-content
   exception, and all nine reviewed guide-title decisions are applied.
6. Priority journeys have reviewed output evidence, useful eyebrows, stable
   gate IDs, and valid decision-chip anchors.
7. Shared chrome uses consistent destination language without forcing
   identical rendering or replacing Starlight-native controls.
8. Both sites build in the required order; combined links and fragments,
   rendered-output contracts, contrast, the seven registered construction
   tests, and the approved browser suite are CI-gated.
9. Tap targets, overflow, responsive behavior, accessibility, and print
   behavior pass an accepted emitted-site baseline or have narrowly scoped
   follow-up fixes.
10. Physical-device review remains an explicit manual release check.
11. No dependency, route move beyond catalogue-format source ownership with
    route compatibility, palette unification, speculative illustration system,
    or feature surface beyond approved `/now/` is introduced.
12. No accepted programme decision remains unresolved.

## Approved decision log

1. The programme slug is `tech-site-completion` and its initiative is
   `ini-002`.
2. The appetite is four bounded implementation waves, not a redesign quarter.
3. The completion definition above is the acceptance boundary.
4. Durable principles are:
   - lead with the user's job; reveal the system second;
   - put verifiable evidence beside every meaningful claim;
   - keep users oriented through stable names, paths, and destinations; and
   - preserve each surface's reading mode while maintaining one product
     identity.
5. Shared chrome shares information architecture and destination vocabulary,
   not CSS or component implementations. Marketing keeps its route contract;
   docs may add a thin product-orientation band while retaining Starlight title,
   search, theme control, and sidebar. Footers share destination taxonomy but
   keep renderer-specific appearance. The internal Docs destination does not
   use external-link treatment.
6. Every rendered public guide requires reviewed `title`, `summary`, `pack`,
   and `kind`, except explicitly declared structural or non-content Markdown.
   Titles default to the current H1, summaries are human-written, pack follows
   ownership, and kind follows actual page purpose.
7. Keep five reviewed current guide titles. Apply these four changes:
   - `Write a Page/Screen Contract` to `Write a page or screen contract`;
   - `Run an Audit` to `Run a frontend audit`;
   - `Scaffold a Component` to
     `Scaffold a component from a screen brief`; and
   - `IaC (Terraform) guides` to `Terraform and OpenTofu guides`.
8. Journey data stores canonical `decisionGateIds`, renders chip labels from
   canonical gate definitions, and gives gate cards stable DOM IDs. Display
   text is not an identifier.
9. Currently designated priority journeys require human-reviewed output
   transcripts and outcome-led eyebrows; neither is generated.
10. Tap targets use WCAG 2.2 classification with recorded legitimate inline and
    framework exemptions; only demonstrated non-exempt failures are fixed.
11. The deterministic browser gate covers 360, 375, 390, 414, and 1440 widths
    in both themes, permits at most the accepted 1px subpixel overflow
    tolerance, and requires zero serious or critical axe findings. Screenshot
    capture remains optional evidence and does not write tracked files in CI.
12. Print behavior is audited first. Framework/browser defaults are accepted if
    pages remain legible and navigation-only elements do not corrupt content;
    otherwise only demonstrated failures receive minimal print CSS.
13. Social proof remains research and does not block completion unless a
    stable, sourceable, owned signal is found. Close it as stale if none exists.
14. Rehype plugin unit tests use Node's built-in runner under the existing Node
    24 contract; no dependency is added.
15. Required CI gains the registered seven construction tests and docs contrast
    check. The deterministic Playwright subset follows after its route and
    exemption contract is materialized.
16. Materialize the Starlight ratification RFC and annotate the frozen Phase 4b
    spec; do not rewrite shipped bodies.
17. Keep the twelve adjacent-owner items outside this programme.
18. At the decision gate this brief remained Draft. Canonical intake and
    `receive-brief` subsequently owned its Ready transition, decomposition,
    and lifecycle registration after the review pause.
19. Public `/work/` is removed outright with no redirect. `/now/` is the
    independently shippable replacement, publishes only released changelog
    `Highlights`, and launches with all meaningful released highlights from the
    seven calendar days ending on launch day, inclusive.
20. Now drafting may be AI-assisted from implementation diff and verification
    evidence inside the normal development lifecycle; ordinary PR review owns
    acceptance, Unreleased content never publishes, and no model runs in CI,
    release automation, or site generation.
21. The shared destination order is How it works, Use cases, Catalogue, Now,
    Docs, and Try the build loop. Docs product orientation remains distinct
    from Starlight documentation navigation; destination data is shared but
    renderer presentation and state are not.
22. The 34 journey IDs, labels, three priority editorials, invocation
    convention, and emitted evidence contract are fixed in the owning spec.
    Pack versions and plugin descriptions stay unchanged because installed
    functional behavior does not change.
23. Browser and print measurement remains implementation evidence, not an open
    shaping decision. The final shaping record contains zero measured passes,
    failures, or exemptions and prohibits speculative remediation.
24. Detailed shaping replaces decision 2's four-wave sequencing granularity
    with the eight ordered completion waves below. The programme appetite stays
    bounded; the added stages make dependencies and evidence gates explicit
    rather than expanding scope.
25. Decision 13's close-stale condition is met: repository dogfooding is not
    third-party proof, and no durable permissioned, sourceable, owned signal
    exists. Reopen only when a named owner can maintain source, freshness,
    verification, presentation boundaries, and removal.

## Registered debt dispositions

Historical problem statements, proposed fixes, review headers, and vintages
remain preserved in their original `workspace.toml` comment blocks. Open
membership remains for the two explicitly retained research items and for the
satisfied `starlight-migration-rfc` compatibility pointer required by the
frozen-spec lint contract. The other legacy entries were replaced by their
approved canonical targets on 2026-08-17 without flattening their provenance.
The table below records the approved disposition.

| Registered slug | Disposition | Canonical target or trigger | Mechanicality |
| --- | --- | --- | --- |
| `guide-summary-backfill` | merge | `guide-metadata-completion` | mixed |
| `site-shared-chrome-band` | shape | after site principles | judgment-led |
| `guide-title-wording-review` | ship | independently shippable title review | judgment-led |
| `rehype-plugin-unit-tests` | ship | after built-in runner contract | mechanical-after-decision |
| `docs-tap-target-audit` | shape | audit before fixes | judgment-led |
| `site-design-principles` | ship | durable design-principles artifact | judgment-led |
| `docs-site-print-styles` | research | six-route print audit; close stale or shape narrowly from evidence | judgment-led |
| `web-docs-link-check-gate` | close-stale | shipped rendered-site link checker | mechanical-now |
| `phase4b-docsurl-instruction-stale` | ship | frozen-spec status annotation | mechanical-now |
| `site-social-proof-band` | close-stale | no durable owned external signal; reopen only with owner/freshness contract | judgment-led |
| `site-mobile-responsiveness` | merge | `site-browser-quality-gate` | mixed |
| `journey-good-output-transcripts` | merge | `journey-page-completion` | judgment-led |
| `journey-hero-descriptive-eyebrow` | merge | `journey-page-completion` | judgment-led |
| `journey-decision-chip-gate-anchors` | merge | `journey-page-completion` | mixed |
| `starlight-migration-rfc` | ship | ratifying RFC | judgment-led |
| `catalogue-site-tests-absent-from-ci` | ship | required CI construction-test group | mechanical-now |

## Newly discovered contract gaps

| Proposed identifier | Disposition | Mechanicality |
| --- | --- | --- |
| `site-link-check-contract-docs` | merge with rendered-link closure | mechanical-now |
| `docs-site-vestigial-token-copy` | ship | mechanical-now |
| `docs-contrast-ci-gate` | ship | mechanical-now after gate placement |
| `site-browser-quality-gate` | shape | mixed |
| `journey-template-priority-id-drift` | merge into journey completion | mechanical-now |
| `site-now-surface` | ship | mixed after released-highlight decisions |

The orphan historical rendered-link comment block is register hygiene, not a
separate product item; preserve its provenance when the stale membership is
resolved.

## Reserved adjacent owners

The following registered work affects a site, journey, or guide but retains its
own authority and verification contract:

- `product-strategy-adoption-doctrine`
- `product-engineering-shaping-doctrine`
- `xd-design-system-foundations`
- `xd-ia-archetypes-objects`
- `xd-state-reviewer-doctrine`
- `cross-pack-experience-eval`
- `digital-product-guides-update`
- `digital-experience-contract-pe-journey-xref`
- `digital-product-profile`
- `role-journey-agent-swarm-section`
- `catalogue-package-guides`
- `portfolio-outcome-entry-surfaces`

These are retained, not duplicated or blocked by this brief. Their owning
artifacts decide their open product and technical questions.

## Dependency and sequencing map

| Wave | Contents | Dependency |
| --- | --- | --- |
| 1. Rebaseline | Fresh `main`; reconcile Type 1/2/3; reconfirm inventory, routes, projections, and emitted baselines | Mechanical PRs merged |
| 2. Contracts and deterministic test foundations | Guide exception validator; journey ID/label validation; shared-destination validation/projection; browser scaffolding | Wave 1 |
| 3. Content and canonical sources | Six guide batches; canonical journey migration and priority copy; released Now projection and launch content | Wave 2 |
| 4. Renderer consumption | Regenerate journey copies; label/fragment behavior; add Now; adapt both shared-chrome renderers together | Wave 3 |
| 5. Emitted construction verification | Metadata, IDs, copies, routes, aliases, links, fragments, and shared destinations after marketing-first/docs-second build | Wave 4 |
| 6. Measured browser and print audit | Full matrix; tap geometry; axe; overflow; focus; keyboard; fragments; framework controls; six print representatives | Wave 5 and exposed runtimes |
| 7. Conditional remediation | Smallest fixes for demonstrated defects; new specs only for independently shippable outcomes | Wave 6 evidence |
| 8. Completion review | Full reconciliation, spec/plan review, evidence audit, lifecycle status, and physical-device record | All preceding waves |

No implementation spec becomes Shipped merely because shaping is complete.

## Verification contract

Every derived implementation plan must test emitted behavior, not merely source
shape. At minimum it must preserve the build order (`web/` first,
`docs-site/` second), run the combined page and fragment checker after both
builds, prove guide and journey metadata in generated pages, exercise both docs
themes, preserve all routes/navigation except the approved Work-to-Now change,
and record any framework or manual exception explicitly. Construction tests
must demonstrate a failure on a
seeded broken case rather than assert only that a source pattern exists.

## Spec map

The confirmed cut contains nine independently shippable slices. Status is
derived from each linked spec by the `receive-brief` coverage lint. All nine
spec and plan contracts received explicit human approval on 2026-08-17 and
were registered in the workspace work queue at approval; each slice moves to the
shipped list as it lands.

**Closed 2026-08-25.** All nine slices are `Shipped`. The two print-related debt
entries this programme registered are settled with provenance, satisfying
completion item 1: `print-audit-page-break-quality` was measured on human review
of the regenerated representative PDFs and closed; `print-chrome-paint-inventory`
is retired won't-do, because four probe generations failed and the question it
would answer is a legibility preference the owning audit's decision rule bars
from producing print rules. Both are in `workspace.toml [backlog].closed`.

Completion item 9 is met through its "narrowly scoped follow-up fixes" clause:
that human review found one print defect — the docs footer's navigation printing,
producing a navigation-only final page on four of five documentation routes —
which is owned by `spec/docs-site-print-chrome-suppression` rather than by this
brief. Completion item 10 is met as written: physical-device review *remains* an
explicit manual release check, and
[`docs/guides/how-to/verify-a-site-release.md`](../../guides/how-to/verify-a-site-release.md)
records it as **Blocked** with a named owner. Closing this brief does not
discharge that check.

| Spec | Status |
| --- | --- |
| `site-contract-provenance-cleanup` | Shipped |
| `site-ci-contract-closure` | Shipped |
| `docs-site-build-contract-hardening` | Shipped |
| `guide-title-clarity` | Shipped |
| `guide-metadata-completion` | Shipped |
| `journey-page-completion` | Shipped |
| `site-now-surface` | Shipped |
| `site-shared-chrome` | Shipped |
| `site-browser-quality-gate` | Shipped |

## Design artifacts

- `docs/product/journeys/team-evaluates-and-adopts.md`
- `docs/product/journeys/catalogue-engineer.md`
- `docs/product/findings/`
- `docs/design/principles/tech-site.md`

## Governance artifacts

- `docs/rfc/0089-starlight-docs-boundary.md` — Accepted; records the sibling
  Starlight project, renderer-autonomy, and ordered single-artifact boundaries.
- `docs/adr/0085-docs-rendering-is-site-local.md` — Accepted; owns the partial
  supersession of ADR-0055's token-sharing rationale.

## Source authority

- **Mode:** repo-origin
- **Locator:** `workspace.toml#repo_backlog.open` plus the shipped specs,
  generation contracts, site instructions, workflows, and tests reconciled at
  intake
- **Revision:** `7da8b07571e44fe5d6052f0efca7952484e173c8`
- **Decision confirmation:** all twenty-five decisions approved on 2026-08-17
