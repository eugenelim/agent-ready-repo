# How to create a Lean Canvas for an initiative

**Use this when:** You have a committed bet (and optionally a capability map) and need to produce a shareable, version-controlled initiative brief through structured elicitation.
**Prerequisites:** `product-engineering` pack installed; a committed bet from `place-bet` and capability map from `map-capabilities` are recommended for pre-population, though the skill runs standalone without them.
**Result:** A `docs/product/initiatives/<ini-slug>.md` initiative brief with a `## Value Proposition` section and a `workspace.toml` entry suggestion, ready to commit and share with stakeholders.

Use the `lean-canvas` skill when you need to produce a shareable, version-
controlled initiative brief through a structured elicitation. The skill
adapts the Lean Canvas for internal initiatives — replacing startup vocabulary
with initiative-appropriate labels — and writes one file:
`docs/product/initiatives/<ini-slug>.md`.

## When to use this skill

**After steps 5 and 6 of the PE shaping sequence (recommended)**

If you have run `place-bet` (step 5) and `map-capabilities` (step 6), the
skill will find your upstream shaping artifacts and pre-populate several Lean
Canvas fields. You confirm or override each pre-filled value rather than
answering from scratch. This is the fastest path to a complete initiative brief.

**As a standalone elicitation**

You can run `lean-canvas` without any upstream shaping artifacts. The skill
runs in full-elicitation mode — it asks each field interactively. The produced
file is identical; you supply the answers rather than confirming pre-fills.
Use this path when you are starting a new initiative brief and earlier shaping
steps have not run yet, or when the initiative is not following the standard
shaping sequence.

## Choosing between simple and full mode

The skill presents both options when it starts. Pick based on what the
initiative actually needs captured.

**Simple mode (5 boxes) — the default**

Covers the core hypothesis: Problem, Unique Value Proposition, Solution,
Customer Segments, Key Metrics. Sufficient for most initiatives — when you
know your channels, cost profile, and strategic backing but do not need them
formally documented yet, simple mode produces a complete, usable brief.

**Full mode (9 boxes)**

Adds Channels, Value Created, Cost Estimate, and Organizational Buy-In. Use
full mode when your initiative needs to explicitly document how adopters
discover and adopt the tooling (Channels), what quantified organizational
benefit it delivers (Value Created), what resources it will consume (Cost
Estimate), or what strategic backing makes it hard to de-prioritize
(Organizational Buy-In). These are common for cross-team initiatives with
significant infrastructure investment or formal steering-committee review.

## Running the skill

1. **Start the skill.** Say "lean canvas" or "initiative brief" or
   "canvas this initiative" in your PE session, or invoke `lean-canvas` by
   name.

2. **Provide the initiative slug.** The skill asks for the initiative slug
   (e.g. `ini-003`). It uses this for the output path
   (`docs/product/initiatives/ini-003.md`) and for locating your shaping
   artifacts (`<output_dir>/shaping/ini-003/`).

3. **Choose a mode.** The skill presents simple and full with one-sentence
   descriptions. Confirm your choice. The mode is locked at this point —
   it does not change during elicitation.

4. **Confirm or fill each field.** If upstream artifacts exist, the skill
   pre-populates derivable fields and presents them for your confirmation
   or override. For fields without a pre-fill, the skill asks interactively.
   Any field you cannot answer yet is marked "TBD — `<one-line reason>`"
   in the produced file — never left blank.

5. **Review the resolved write path.** The skill surfaces the absolute path
   it will write to before writing. Confirm it is correct.

6. **File is written.** One file is created:
   `docs/product/initiatives/<ini-slug>.md`. It contains all template
   sections plus a `## Value Proposition` section (the Lean Canvas output)
   inserted before `## Scope`.

## Reviewing the Value Proposition output

The `## Value Proposition` section is the initiative's problem-solution-value
story. It is inserted before `## Scope` so the core hypothesis is visible on
first scroll. Review it as you would review a hypothesis:

- Is the **Problem** specific enough to falsify?
- Does the **Unique Value Proposition** make a testable claim?
- Do the **Key Metrics** give you an observable signal within the
  initiative's appetite?

If any field is marked TBD, treat it as an open assumption — schedule time to
fill it before the initiative brief is shared with stakeholders.

## Linking workspace.toml and sharing

After writing the file, the skill suggests a `workspace.toml` entry for the
initiative. Add it to the `["ini-NNN"]` section in `workspace.toml`; this
makes the initiative visible to `workspace-status` and the work queue.

To share the initiative brief with your team, commit the file to version
control and link it from the initiative's `workspace.toml` section. The
produced file is plain Markdown — it renders in GitHub, GitLab, and most
document tools without conversion.
