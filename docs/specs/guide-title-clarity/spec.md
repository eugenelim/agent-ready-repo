# Spec: Guide title clarity

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** tech-site-completion
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

- [ ] `page-screen-contract.md` presents
  “Write a page or screen contract” as its canonical title.
- [ ] `run-an-audit.md` presents “Run a frontend audit” as its canonical
  title.
- [ ] `scaffold-a-component.md` presents
  “Scaffold a component from a screen brief” as its canonical title.
- [ ] `guides/iac-terraform/README.md` presents
  “Terraform and OpenTofu guides” as its canonical title.
- [ ] For each changed guide, the source H1, frontmatter title when present,
  generated page H1, browser/search title, and applicable sidebar label are
  coherent with the approved string.
- [ ] The existing five reviewed titles outside this four-file set do not
  change.
- [ ] Every pre-change route for the four guides still resolves and the
  combined rendered-link checker reports no broken page or fragment.
- [ ] A rendered-surface review finds no Major issue against “Precision
  authority” or the principle “Lead with the user's job; reveal the system
  second.”

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
