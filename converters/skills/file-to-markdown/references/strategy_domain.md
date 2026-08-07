# Strategy: domain

For domain models, ER diagrams, class diagrams, and aggregate maps.

## What to extract from each tile

- `type`: `entity`, `aggregate`, `value-object`, `boundary`,
  `relationship`. Lowercase.
- `name`: the entity / class name (TitleCase usually).
- `description`: free-form notes like attribute lists, e.g.
  `"id, email, created_at"`. Keep it on one line; the reconciler
  preserves it verbatim.
- `bbox_in_tile`: `{x, y, w, h}` of the entity box in the tile.
- `confidence`: standard scale.

For relationship lines:

- `type: "relationship"`
- `name`: cardinality + name when present, e.g. `"1..N owns"`,
  `"N:M tagged-with"`. Use `"unlabelled"` if no label.
- `description`: `"<source entity> → <target entity>"`.
- `bbox_in_tile`: of the line if you can capture it.

## What NOT to extract

- Don't expand attributes into separate elements. Keep them on the
  parent entity's `description`.
- Don't infer aggregate boundaries from styling alone if the diagram
  doesn't draw them explicitly.

## Output shape

```json
{
  "tile_id": "tile_W0_R0_C0",
  "elements": [
    {"type": "entity", "name": "Order",
     "description": "id, customer_id, placed_at, status",
     "bbox_in_tile": {"x": 60, "y": 60, "w": 220, "h": 140},
     "confidence": "high"},
    {"type": "relationship", "name": "1..N has",
     "description": "Order → OrderLine",
     "bbox_in_tile": {"x": 280, "y": 100, "w": 60, "h": 30},
     "confidence": "medium"}
  ]
}
```
