# Copy-direction artifact path resolution

The `copy-direction` skill writes its output artifact — the copy-direction doc — to a file path resolved through the three-tier layout contract established in RFC-0050 D6. This file documents the resolution order and the adopter-owned configuration key.

## Resolution order (config → default → discover-by-marker)

**Tier 1 — Config.** If the adopter's `agentbundle.toml` (or equivalent configuration file) contains an `[experience]` table with a `copy_direction_dir` key, the skill writes the artifact to that directory:

```
[experience]
copy_direction_dir = "path/to/your/copy-direction-docs/"
```

**Tier 2 — Default.** If no config key is present, the skill writes to the default path:

```
docs/design/copy/<slug>.md
```

where `<slug>` is a short kebab-case name for the surface (e.g. `landing-page`, `product-launch`, `onboarding`).

**Tier 3 — Discover-by-marker.** If neither config nor default path resolves (the `docs/design/` directory does not exist in the repository), the skill discovers existing copy-direction docs by the frontmatter marker `type: copy-direction`. Any file in the repository containing this frontmatter field is treated as a copy-direction doc and may be referenced as a prior artifact.

## Frontmatter contract

Every copy-direction doc written by this skill includes the following frontmatter:

```
type: copy-direction
surface: <marketing/acquisition | onboarding | announcement | other>
persona: <short persona name or pointer>
date: <YYYY-MM-DD>
```

The `type: copy-direction` field is the discover-by-marker key. Do not omit it; without it the artifact cannot be found by Tier 3 resolution.

## Extension to the pack's marker set

`copy-direction` extends the `experience` pack's existing discover-by-marker set alongside `content-brief` (from `content-design`). An adopter who stores both types in non-default locations can configure each independently via the `[experience]` table.
