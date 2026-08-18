# Spec: Guide title clarity

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0085](../../adr/0085-docs-rendering-is-site-local.md), [RFC-0089](../../rfc/0089-starlight-docs-boundary.md), [`docs-site-design-refresh/creative-direction.md`](../docs-site-design-refresh/creative-direction.md)
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Readers scanning guide pages, navigation, and search results see four specific,
task-oriented titles that name the actual outcome without generic wording or
internal shorthand. Routes remain stable, and title presentation follows the
platform site's precision-authority direction and the tech-site principle to
lead with the user's job.

## Boundaries

### Always do

- Apply the four approved title strings exactly.
- Keep each page H1, metadata title, and applicable navigation label coherent.
- Preserve every existing source path, generated route, alias, and inbound link.

### Ask first

- Change any of the five reviewed titles approved to remain as they are.
- Reword one of the four approved replacement strings.
- Change a navigation label independently from its approved page title.

### Never do

- Rename or move a guide file to make its title look cleaner.
- Fold the 125-page metadata backfill into this focused title change.
- Add a dependency, component, or new navigation destination.

## Testing Strategy

- Source and navigation consistency use TDD through the existing title linter
  and focused fixtures.
- Route preservation and emitted title behavior use goal-based full-site build
  assertions.
- The user-facing scan uses manual design review against the existing platform
  aesthetic direction and tech-site principles.

## Acceptance Criteria

- [x] **AC1** — `page-screen-contract.md` presents
  “Write a page or screen contract” as its canonical title.
- [x] **AC2** — `run-an-audit.md` presents “Run a frontend audit” as its canonical
  title.
- [x] **AC3** — `scaffold-a-component.md` presents
  “Scaffold a component from a screen brief” as its canonical title.
- [x] **AC4** — `guides/iac-terraform/README.md` presents
  “Terraform and OpenTofu guides” as its canonical title.
- [x] **AC5** — For each changed guide, the source H1, the frontmatter `title:` (the
  published canonical title — the build strips the body H1), the generated page
  H1, the browser/search title, and the sidebar ITEM label are coherent with the
  approved string. The `iac-terraform` sidebar GROUP label in `site.toml`
  (`IaC (Terraform)`) is deliberately unchanged: the approved decision names the
  page title, and changing a declared guide group is an “Ask first” boundary
  outside this spec.
- [x] **AC6** — Where a baseline label previously froze one of these titles, its
  `guide-nav-baseline.toml` entry is DELETED rather than relabelled, so the
  sidebar label resolves from the frontmatter title. Editing the label instead
  would make the pair guard tautological: `tools/test_build_site_sidebar.py`
  loads the same baseline file it compares against, so an edited label passes by
  construction and witnesses nothing.
- [x] **AC7** — The five reviewed titles outside this four-file set do not change,
  enumerated here because “the five” was previously recoverable only by git
  archaeology:
  - `guides/_shared/how-to/install-user-scope-pack-into-codex.md`
  - `guides/_shared/how-to/install-user-scope-pack-into-kiro.md`
  - `guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md`
  - `guides/frontend-engineering/reference/frontend-engineering.md`
  - `guides/governance-extras/how-to/new-adr.md`
- [x] **AC8** — The four retired strings — `Write a Page/Screen Contract`, `Run an Audit`,
  `Scaffold a Component`, `IaC (Terraform) guides` — appear in none of the four
  source files. They legitimately persist as provenance elsewhere and must not
  be scrubbed: `tools/test_build_site_sidebar.py`'s `RETIRED_STRINGS`, which is
  what enforces this criterion and therefore names all four;
  `docs/product/briefs/tech-site-completion.md:147-151` (the approved change
  list); this spec and its plan; `workspace.toml`;
  `tools/test_lint_guide_titles.py` fixtures; and `docs/product/changelog.md`
  with its docs mirror, whose release note quotes three of the four old titles
  beside their new ones — `IaC (Terraform) guides` is not among them, because
  the entry describes that change by naming the pack rather than the old title.
  Verification asserts absence in the four source files, not repository-wide
  absence.
- [x] **AC9** — `guides/frontend-engineering/README.md`'s link text for the three
  frontend-engineering pages matches their approved titles, so the pack's primary
  in-site entry point does not contradict them.
- [x] **AC10** — Every pre-change route for the four guides still resolves and the
  combined rendered-link checker reports no broken page or fragment.
- [x] **AC11** — A rendered-surface review finds no Major issue against the owning
  surface's aesthetic direction — `docs/specs/docs-site-design-refresh/creative-direction.md`'s
  dominant goal “Instrument-grade clarity” — or the tech-site principle “Lead
  with the user's job; reveal the system second.” NOT the marketing site's
  “Precision authority”: all four pages render only on `docs-site/`, and the
  brief's non-goals bar aligning the two surfaces. Severity uses the
  `frontend-engineering` skill's Blocker/Major/Minor/Note scale and is assigned
  by a human reviewer; the brief bars generated severity classifications.

## Assumptions

- Technical: the four old H1 strings still exist at their identified source
  paths (source: repository grep on 2026-08-17).
- Technical: navigation labels are pinned through
  `guide-nav-baseline.toml` where a guide participates in the sidebar
  (source: `tools/build-site.py` and `guide-nav-baseline.toml`).
- Product: the four replacement strings and five no-change decisions are exact
  (source: user confirmation 2026-08-17).
- Product: existing platform and docs aesthetic directions remain authoritative
  on their owning surfaces (source: user confirmation 2026-08-17).
- Process: title selection is judgment-led even though applying an approved
  string is mechanical (source:
  `docs/product/briefs/tech-site-completion.md`).
- Process: public routes and navigation contracts do not move (source:
  `docs/product/briefs/tech-site-completion.md`).
