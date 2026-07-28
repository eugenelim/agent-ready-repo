# Artifact model

Defines the documentation artifacts this skill can create or update, their ownership boundaries, and when to create each.

## Artifact types

### Pack README (`packs/<pack>/README.md`)

The pack's canonical landing and discovery document.

**Owned by:** pack maintainers. Authored and updated by this skill.  
**Purpose:** explain what the pack helps a user accomplish, its natural first request, major jobs, install and trust information, and links to deeper documentation.  
**Must not:** list skill names as the first thing the reader encounters. Must not include machine facts (version, scope, dependencies) that are already authoritative in `pack.toml`.  
**Update when:** the pack's user-facing behavior changes, new major capabilities ship, or the current README leads with implementation vocabulary instead of outcomes.

### Journey (`packs/<pack>/JOURNEY.md` — proposed optional)

The canonical first-value journey for the pack. Reserved for the optional first-value narrative: a start-to-finish sequence from the reader's opening request to their first meaningful outcome.

**Owned by:** pack maintainers. Authored by this skill when the journey convention is established.  
**Purpose:** walk a complete user flow — each stage has a user request, what the agent does, what the user gets, and the decision the user makes.  
**Must not:** describe internal skill mechanics in the main flow. Link out to how-to guides for variations.  
**Update when:** the primary user flow changes or the pack's first-value path is redefined.

### Tutorial (`guides/<pack>/tutorials/<slug>.md`)

A learning-oriented artifact for beginners. Guarantees a working result.

**Owned by:** guide authors. Authored by this skill.  
**Purpose:** take the reader from nothing to a small, verified success. Every step produces an observable result. The reader finishes with something real.  
**Must not:** offer choices mid-tutorial. Must not insert explanations of why without linking out.  
**Update when:** the described steps no longer produce the promised result.

### How-to guide (`guides/<pack>/how-to/<slug>.md`)

A task-oriented recipe for a competent reader with a specific problem.

**Owned by:** guide authors. Authored by this skill.  
**Purpose:** help the reader solve one specific named problem. Covers the common path and realistic variations. Links to reference for exhaustive options.  
**Must not:** reteach basics the reader already knows. Must not list every possible flag or option inline.  
**Update when:** the procedure for the task changes.

### Reference (`guides/<pack>/reference/<slug>.md`)

Authoritative, dry, complete description of interfaces, commands, schema fields, or configuration.

**Owned by:** guide authors. Authored by this skill.  
**Purpose:** answer "what exactly does this do / accept / return?" for a reader scanning for one fact.  
**Must not:** editorialize. Must not omit options because they are "rarely used." Must be consistent in structure across sibling entries.  
**Update when:** any described parameter, output, or behavior changes. A code change → reference update in the same PR is the rule.

### Explanation (`guides/<pack>/explanation/<slug>.md`)

Understanding-oriented discussion of why something works the way it does.

**Owned by:** guide authors. Authored by this skill.  
**Purpose:** give the reader a mental model. Cover trade-offs, design reasoning, and how components fit together. Bounded by an "About <topic>" frame.  
**Must not:** contain step-by-step procedures. Must not have open-ended scope.  
**Update when:** the design rationale changes, or the explanation contains outdated motivations.

### Guide index / landing (`guides/<pack>/README.md`)

Entry surface linking into the pack's guides.

**Owned by:** guide authors. Updated by this skill when the set of available guides changes materially.  
**Purpose:** orient the reader and route them to the right guide. Lists available guides by user goal, not by quadrant name.  
**Update when:** a new guide is added, an existing guide is removed, or the primary user goal changes.

### Maintainer DESIGN input (`packs/<pack>/DESIGN.md`)

Maintainer-facing design and architecture record.

**Owned by:** pack maintainers. Read by this skill for verified architecture claims.  
**This skill does not author DESIGN.md by default.** It reads DESIGN.md during audit and verify modes to cross-check product claims.

---

## Mandatory vs. conditional artifacts

| Artifact | Status |
|---|---|
| Pack README | Mandatory for every pack |
| Guide index (README) | Conditional — create when ≥2 guides exist |
| Tutorial | Conditional — when a beginner needs an on-rails path |
| How-to | Conditional — when a competent reader needs a named-problem recipe |
| Reference | Conditional — when there is interface detail to look up |
| Explanation | Conditional — when users need a mental model |
| Journey | Optional — reserved for the pack's first-value narrative |

Default to ONE artifact. Do not create all six because the Diátaxis framework has four quadrants.

---

## When to update entry surfaces

Update the pack README when:
- A new major capability ships that changes the primary user job
- The current README leads with skill names or implementation vocabulary
- The natural first request changes

Update a guide index when:
- A new guide is added that the index should link to
- An existing guide is removed
- The primary user goal changes enough to change the recommended entry point

Update a journey when:
- The primary user flow changes end-to-end
- A stage no longer produces the described result
