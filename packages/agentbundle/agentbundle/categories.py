"""Default `categories` vocabulary for `pack.toml` (enriched-pack-manifest).

RFC-0031 D3 gives the pack catalogue a small, *soft* category vocabulary —
a publisher may declare a slug outside this set, and `agentbundle validate`
emits a warning (exit 0) rather than refusing. The vocabulary exists to
nudge consistency across the catalogue, not to gate it; a hard enum would
ossify the taxonomy and break packs whenever a new category is needed.

Keep this list and the documented set in
`docs/architecture/pack-layout.md` / the spec's AC in lockstep — it is the
single source of truth the validate command reads.
"""

from __future__ import annotations

# The ~16 default slugs (RFC-0031 D3). Soft: unknown slugs warn, never fail.
DEFAULT_CATEGORIES: frozenset[str] = frozenset(
    {
        "code-review",
        "testing",
        "documentation",
        "architecture",
        "security",
        "research",
        "product-management",
        "project-management",
        "integrations",
        "file-conversion",
        "api-design",
        "governance",
        "credentials",
        "devops",
        "data",
        "ai-agent",
    }
)


def unknown_categories(declared: object) -> list[str]:
    """Return declared category slugs that are not in the default vocabulary.

    Accepts the raw `[pack].categories` value (any type — defensive at the
    validation boundary): non-list inputs and non-string entries are
    ignored, so this never raises on a malformed manifest (the schema's
    type check owns that error path). Order is preserved and duplicates are
    de-duplicated, so the warning lists each unknown slug once.
    """
    if not isinstance(declared, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for entry in declared:
        if isinstance(entry, str) and entry not in DEFAULT_CATEGORIES:
            if entry not in seen:
                seen.add(entry)
                out.append(entry)
    return out
