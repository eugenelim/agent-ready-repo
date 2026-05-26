# ER-diagram rubric — for `architect-review`

For critiquing a Mermaid `erDiagram` or other entity-relationship
notation.

> Note: intentionally duplicated content with `architect-diagram`'s
> ER guidance. Skill autonomy beats DRY at this scale.

## Universal

- [ ] **Renders.** Mermaid source parses.
- [ ] **Title or scope sentence** above the diagram names the
      domain.
- [ ] **Fits one screen.** ≤15 entities; split by sub-domain
      otherwise.

## Entities

- [ ] **Entity names match the system** in document mode (table or
      collection names verbatim).
- [ ] **Primary key marked** on every entity.
- [ ] **Foreign keys marked.**
- [ ] **Unique constraints** rendered where load-bearing for the
      design.
- [ ] **Attribute types consistent** — pick one convention (SQL
      types, language types, abstract types) and stay with it.

## Relationships

- [ ] **Cardinality at both ends** of every relationship. Half a
      cardinality is half a model.
- [ ] **Relationship labeled** with a verb-phrase. Bare lines
      fail. "places", "contains", "appears in".
- [ ] **Identifying vs. non-identifying** relationships
      distinguished (`--` vs. `..`) when it matters.

## What's *not* in scope

- [ ] **No implementation details.** Indexes, partition keys,
      storage parameters belong in the migration, not the diagram.
- [ ] **No every-column.** Show what matters for the design.

## Severity mapping (typical)

- 🟥 **Blocker** — Cardinality missing entirely; entity names
  fabricated in document mode; no PKs marked.
- 🟧 **Major** — One relationship unlabeled; types inconsistent;
  one FK missing.
- 🟨 **Minor** — Attribute order awkward; one entity over-detailed.
- ⚪ **Nit** — Naming case style, layout.
