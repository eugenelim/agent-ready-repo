# Artifact model

Defines the documentation artifacts this skill can create or update, their ownership boundaries, and when to create each. Each artifact lives where the repository keeps user-facing docs of that kind; see [`repository-ownership.md`](repository-ownership.md) for how to find that place.

## Artifact types

### README

The product's landing and discovery document.

**Owned by:** product maintainers. Authored and updated by this skill.
**Purpose:** say what the product is, who it is for, how to install it, and show a first runnable example, with links to deeper docs.
**Must not:** open with an inventory of commands, flags, or components. Must not repeat machine facts (version, dependencies) that a manifest states.
**Update when:** user-facing behavior changes, a major capability ships, or the README leads with implementation vocabulary instead of outcomes.

### Docs landing page

The entry page of the docs set.
**Purpose:** give a new reader one start-here path and route others by goal.
**Update when:** a guide is added or removed, or the recommended first step changes.

### Installation guide

**Purpose:** get the product running: prerequisites, one supported path, a check that it worked, upgrade, uninstall.
**Update when:** supported platforms, versions, or install commands change.

### Tutorial and quickstart

A learning-oriented artifact that guarantees a working result. A quickstart is the shortest tutorial: one path to one real result in minutes.
**Purpose:** take the reader from nothing to a small, verified success.
**Must not:** offer choices mid-way, or explain *why* without linking out.
**Update when:** the steps no longer produce the promised result.

### How-to guide

A task-oriented recipe for a competent reader with a named problem.
**Purpose:** solve one task. Cover the common path and realistic variations; link to reference for options.
**Must not:** reteach basics or list every option inline.
**Update when:** the procedure changes.

### Reference

Authoritative, complete description of the product surface: API, CLI commands, configuration, or skills. The surface decides the shape; see [`surface-discovery.md`](surface-discovery.md).
**Purpose:** answer "what exactly does this accept and do?" for a reader scanning for one fact.
**Must not:** editorialize or omit options because they are rarely used. Sibling entries share one structure.
**Update when:** any described parameter, output, or behavior changes, in the same change.

### Explanation

**Purpose:** give a mental model, trade-offs, and how components fit together, bounded by an "About <topic>" frame.
**Must not:** contain step-by-step procedures or have open-ended scope.
**Update when:** the design rationale changes.

### Troubleshooting

**Purpose:** map visible symptoms and exact error text to cause, confirmation, and fix.
**Update when:** an error message changes, or a new failure becomes common.

### Changelog and release notes

**Purpose:** tell readers what changed per release, newest first, grouped by change type.
**Update when:** each release.

### Migration guide

**Purpose:** a checklist for moving between two versions across a breaking change.
**Update when:** a release breaks compatibility.

### Contributing guide

**Purpose:** how to report bugs, set up development, run tests, and what contributions are wanted. Linked from the README.
**Update when:** the development workflow changes.

### Journey page

An optional start-to-finish narrative from the reader's first action to a meaningful outcome, one block per stage.
**Update when:** the primary flow changes end to end.

### Maintainer design record

Maintainer-facing architecture and design rationale.
**This skill does not author it by default.** It reads the record during audit and verify modes to cross-check product claims.

---

## Mandatory vs. conditional artifacts

| Artifact | Status |
|---|---|
| README | Mandatory |
| Docs landing page | Conditional: when the journey gap report shows several pages with no entry point |
| Installation guide | Conditional: when install needs more than the README's install section |
| Tutorial or quickstart | Conditional: when first success is partial or missing |
| How-to | Conditional: when a competent reader needs a named-problem recipe |
| Reference | Conditional: when the surface has interface detail to look up |
| Explanation | Conditional: when users need a mental model |
| Troubleshooting | Conditional: when readers hit errors the docs do not cover |
| Changelog and release notes | Conditional: when releases ship and none are recorded |
| Migration guide | Conditional: when a release breaks compatibility |
| Contributing guide | Conditional: when the product takes outside contributions |
| Journey page | Optional |

The journey gap report decides which conditional artifacts to create ([`docs-journey.md`](docs-journey.md)).

Default to ONE artifact. Do not create one of every kind because a framework has four quadrants.

---

## When to update entry surfaces

Update the README when:
- A new major capability changes the primary user job
- It leads with an inventory or implementation vocabulary
- The first runnable example changes

Update the docs landing page when:
- A guide is added or removed
- The recommended entry point changes

Update a journey page when:
- The primary flow changes end to end
- A stage no longer produces the described result
