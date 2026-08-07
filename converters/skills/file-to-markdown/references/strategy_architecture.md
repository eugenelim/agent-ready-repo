# Strategy: architecture

For C4-style architecture, deployment, network, and component diagrams.

## What to extract from each tile

For every shape that represents a component, capture:

- `type`: one of `component`, `boundary`, `actor`, `database`, `queue`,
  `external-system`, `annotation`. Lowercase.
- `name`: the visible label.
- `description`: any inline text describing the role (one line).
- `bbox_in_tile` (optional but recommended): `{x, y, w, h}` of the
  shape inside this tile, in pixels relative to the tile's top-left.
  The reconciler uses this to deduplicate shapes that span tile borders.
- `confidence`: `high` if the label is fully legible and the shape is
  not bisected at a tile edge; `medium` if partially clipped or
  partially obscured; `low` if you're guessing.

For every connector / arrow you can read entirely within the tile,
also emit:

- `type: "relationship"`
- `name`: the protocol or label (e.g. `HTTPS`, `gRPC`, `reads`,
  `publishes-to`); use `"unlabelled"` when there's no label.
- `description`: free-form, e.g. `"Auth Service → User DB"`. Put the
  source and target names in here so the reconciler can preserve them.
- `bbox_in_tile`: tight box around the connector if you can.

## What NOT to extract

- Don't infer relationships that span tile edges; the reconciler does
  cross-tile work, but only if you give it consistent endpoint names.
- Don't dedupe across tiles yourself — emit every observation. The
  reconciler collapses by `(type, name)` and by IoU.
- Don't invent a description if the diagram doesn't have one. Use
  empty string.

## Output shape

```json
{
  "tile_id": "tile_W0_R0_C0",
  "elements": [
    {"type": "component", "name": "Auth Service",
     "description": "Issues JWTs.",
     "bbox_in_tile": {"x": 100, "y": 50, "w": 200, "h": 100},
     "confidence": "high"},
    {"type": "relationship", "name": "HTTPS",
     "description": "Client → Auth Service",
     "bbox_in_tile": {"x": 60, "y": 80, "w": 40, "h": 20},
     "confidence": "medium"}
  ]
}
```
