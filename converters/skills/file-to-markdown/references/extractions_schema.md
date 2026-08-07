# Extractions JSON schema

This is the file the agent writes after reading the overview and each
detail tile. The reconciler consumes it; you do not need to handle
deduplication or sorting in this file.

## Top-level shape

```json
{
  "structural_map": {
    "diagram_type": "<string from the overview pass>",
    "layout": "left-to-right | top-to-bottom | radial | unspecified",
    "summary": "<one or two sentences, optional>"
  },
  "tiles": [
    { "tile_id": "<basename of tile png, with or without extension>",
      "elements": [ /* see per-strategy reference */ ] },
    ...
  ]
}
```

## Per-tile element fields

| Field | Required | Notes |
|---|---|---|
| `type` | yes | Strategy-specific (see the matching strategy ref). Lowercase. |
| `name` | yes | Visible label. The reconciler dedupes on `(type, normalized_name)`. |
| `description` | no | Free-form, single line. Empty string if absent. |
| `bbox_in_tile` | recommended | `{x, y, w, h}` in pixels relative to the tile's top-left. Used for spatial dedup; without it the reconciler falls back to name-only matching. |
| `confidence` | yes | `high` / `medium` / `low`. The frontmatter's `extraction-confidence` field aggregates these. |

Any extra fields you include (e.g. `color_observed` on event-storm
stickies) flow into the merged JSON's `extra` block.

## Tile identifiers

`tile_id` may be:

- the bare basename, e.g. `tile_W0_R0_C0`
- the filename, e.g. `tile_W0_R0_C0.png`

Both resolve to the same record in the manifest. Pick one and stay
consistent within a single extractions file.

## What the reconciler does for you

- Translates `bbox_in_tile` to global source-image coordinates.
- Collapses elements that share `(type, normalized_name)` across tiles.
- Within the same `type`, merges elements whose global bboxes have
  IoU ≥ 0.5; if the names differ, the higher-confidence record wins
  and the loser becomes an entry in `ambiguities`.
- Sorts canonical elements by the structural map's `layout`.
- Emits a Markdown file with YAML frontmatter following the
  ingestion-quality schema.
