# Content brief artifact path resolution

The `content-design` skill writes its output artifact — the content brief — to a file path resolved through the three-tier layout contract established in RFC-0050 D6. This file documents the resolution order and the adopter-owned configuration key.

## Resolution order (config → default → discover-by-marker)

**Tier 1 — Config.** If the adopter's `agentbundle.toml` (or equivalent configuration file) contains an `[experience]` table with a `content_brief_dir` key, the skill writes the artifact to that directory:

```
[experience]
content_brief_dir = "path/to/your/content-briefs/"
```

**Tier 2 — Default.** If no config key is present, the skill writes to the default path:

```
docs/design/content/<slug>.md
```

where `<slug>` is a short kebab-case name for the surface (e.g. `landing-page`, `api-quickstart`, `onboarding-flow`).

**Tier 3 — Discover-by-marker.** If neither config nor default path resolves (the `docs/design/` directory does not exist in the repository), the skill discovers existing content briefs by the frontmatter marker `type: content-brief`. Any file in the repository containing this frontmatter field is treated as a content brief and may be referenced as a prior artifact.

## Frontmatter contract

Every content brief written by this skill includes the following frontmatter:

```
type: content-brief
surface-type: <acquisition | product-or-reference>
persona: <short persona name or pointer>
date: <YYYY-MM-DD>
```

The `type: content-brief` field is the discover-by-marker key. Do not omit it; without it the artifact cannot be found by Tier 3 resolution.

## Extension to the pack's marker set

`content-brief` extends the `experience` pack's existing discover-by-marker set alongside the aesthetic-direction artifact (`type: aesthetic-direction`). An adopter who stores both types in non-default locations can configure each independently via the `[experience]` table.
