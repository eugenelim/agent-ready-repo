# Craft checklist — shape the target state, don't just reformat

"Migrate to convention" means bring the primitive up to this repo's
skill-authoring **craft** — the canonical rules are the repo's *Authoring
skills* conventions. This checklist is the applied form for an assimilated
skill. It runs in **Phase 2**, only after the raw content has been judged safe.

## Activation + no collision
- Rewrite the `description` **terse and activation-optimized** — natural operator
  phrasing should trigger it; state what it's for and, if near a sibling, a
  `Do NOT use for … (use X)` disambiguator.
- **Collision-check against every existing skill's description.** If the new
  surface overlaps an existing skill, surface it — name the colliding skill and
  the overlap — rather than landing two skills that fight for activation.

## Progressive disclosure with deterministic scripts
- Keep `SKILL.md` a terse procedure. Move detailed rules/catalogues to
  `references/`, and repeatable mechanical steps to deterministic `scripts/`.
- Reshape the ingested primitive to this — do not copy a monolithic body whole.

## Fresh-context / human-consumable
- Gloss coined terms on first use, inline — the skill must read standalone for a
  cold reader who hasn't seen the source project.

## Guided, not flooding
- In-skill decision points become **offered choices with prepared context**, not
  a bare question dumped on the user or a wall of options.
- When migration itself needs an operator judgment (destination pack, naming,
  bundle-split, a collision), present *what you found + the options + your
  recommendation* — guide the decision, don't flood it.

## Anti-patterns
- Run the [anti-pattern catalogue](anti-patterns.md) — steer or reject scripts
  that trigger primitives, misused agents, and flooding "skills".

A primitive that can't be brought to this bar is a **reject**, with the specific
craft rule it fails named.
