# Strategy: event-storm

For event-storming boards (big-picture, design-level) and other
sticky-note-on-canvas diagrams.

## What to extract from each tile

For every sticky note in the tile, emit one element. Map color to type:

| Sticky color | `type` value |
|---|---|
| Orange | `event` |
| Blue | `command` |
| Yellow | `aggregate` |
| Lilac / purple | `policy` |
| Red / pink | `hot-spot` |
| Green | `read-model` |
| White / other | `external` |

Required fields:

- `type`: from the table above. Lowercase, exactly as listed.
- `name`: the visible text on the sticky.
- `bbox_in_tile`: `{x, y, w, h}` of the sticky inside the tile. Critical
  for event-storms — temporal sequence is reconstructed from spatial
  position by the reconciler.
- `confidence`: `high` if color is unambiguous and text is fully
  legible; `medium` if color is borderline; `low` if you can't tell
  the color from the lighting.

Optional:

- `description`: only if there's secondary text on the sticky (rare).
- `color_observed`: a hex or color name if the color is genuinely
  ambiguous (e.g., yellow-vs-orange under bad lighting). Goes into
  `extra` so reviewers can see it.

## What NOT to extract

- Don't reorder by perceived narrative. Just emit each sticky in tile
  order. The reconciler sorts by global x (left-to-right = temporal)
  for event-storming boards using the structural map's `layout` field.
- Don't dedupe across tiles. Same sticky seen in two tiles → emit
  twice; the reconciler collapses by `(type, name)`.

## Output shape

```json
{
  "tile_id": "tile_W0_R1_C2",
  "elements": [
    {"type": "event", "name": "OrderPlaced",
     "bbox_in_tile": {"x": 240, "y": 60, "w": 110, "h": 90},
     "confidence": "high"},
    {"type": "policy", "name": "Reserve inventory",
     "bbox_in_tile": {"x": 380, "y": 200, "w": 130, "h": 90},
     "confidence": "medium"}
  ]
}
```

## Structural map for the overview

When reading the overview image, populate:

```json
{
  "diagram_type": "event-storming-big-picture",
  "layout": "left-to-right",
  "summary": "<one-sentence narrative of the timeline>"
}
```

`layout: left-to-right` is what makes the reconciler sort events
along the timeline. Set `top-to-bottom` only if the board genuinely
flows vertically.
