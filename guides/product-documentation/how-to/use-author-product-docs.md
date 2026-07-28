# How to create and maintain product documentation

**Use this when:** you need to create a new guide, improve an existing one, audit documentation for quality issues, or verify that docs match what actually ships.
**Pack required:** `product-documentation` installed.
**Result:** a documentation artifact grounded in canonical behavior — pack README, guide, journey, or audit report — at the right location for its audience.

The `author-product-docs` skill figures out what you need from your request. Tell it what you want to accomplish; it handles the rest.

## The five modes

| Say this | What happens |
|---|---|
| "Write a how-to for X" | Creates a new how-to guide at the right path |
| "Improve this README / guide" | Revises the existing artifact in place |
| "Connect these pages into a coherent flow" | Retrofits related guides around a journey |
| "Audit these docs for quality issues" | Produces evidence-based findings without editing |
| "Verify this guide against what ships" | Checks each claim against the canonical skill sources |

You do not need to name the mode. The skill infers it.

## Steps

### 1. Describe what you want

Just tell the agent what you're trying to accomplish. Examples that trigger the skill:

- "Create a getting-started tutorial for the credential-brokers pack"
- "The pack README leads with skill names — rewrite it to lead with outcomes"
- "Audit the desk-research guides and tell me what's out of date"
- "Does this guide match what the architect skill actually does?"

### 2. The skill inspects canonical sources

Before writing anything, the skill reads:
- The pack's `pack.toml` — actual scope, dependencies, install behavior
- The skill's `SKILL.md` — real modes, inputs, and outputs
- The current `README.md` or guide (for revise mode)

Product claims in the output are grounded in these sources. If a behavior can't be verified, the skill says so rather than inventing it.

### 3. The skill picks one artifact

The default is one artifact — the minimum useful thing for the request. It does not create four empty quadrant directories or sibling pages you didn't ask for.

For guide artifacts, it assigns a page kind from your reader's posture:
- On rails, wants a working result → tutorial
- Has a specific problem → how-to
- Scanning for a fact → reference
- Wants to understand why → explanation

You get: a draft at the right path, with a report of what was inspected, what was written, and what was not verified.

### 4. Confirm before the skill writes

For create mode, the skill shows you the planned artifact and its destination before writing. Confirm the kind and path; if something looks wrong, redirect here — it's the cheapest place to catch a mismatch.

### 5. Follow up

Common follow-ups after the first artifact:

- "Add a See also section linking to the related explanation"
- "Verify this how-to against what the skill actually does"
- "Create a guide index for this pack"

## Variations

**Retrofitting connected pages** — say "connect these docs" or "make the journey coherent." The skill maps the entry surfaces and related guides, identifies gaps, and proposes the minimum set of changes.

**Audit mode** — the skill produces findings without editing. You review; then ask for specific edits if you want them.

**Adopter repos** — the skill inspects your repo's guide structure rather than assuming any specific layout. It writes to where guides already live.

## Common mistakes

- **Picking the page kind by topic** — authentication is a topic; whether your reader is learning, solving a problem, looking up a fact, or understanding a design is the kind. The skill does this automatically from your description of the reader.
- **Expecting four pages** — ask for one guide; get one guide. Create siblings only when there is a reason.
- **Editing the rendered output** — the source files in `guides/` are canonical. Edits to `web/` or `docs-site/` output don't survive the next build.

## See also

- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — why the four kinds exist and when to use each
- [Product Documentation pack README](../../../packs/product-documentation/README.md) — install, scope, and what the pack ships
