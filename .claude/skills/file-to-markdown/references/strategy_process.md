# Strategy: process

For process flow, swimlane, BPMN-lite, and similar step-and-decision
diagrams.

## What to extract from each tile

- `type`: `step`, `decision`, `start`, `end`, `actor`, `swimlane`,
  `annotation`. Lowercase.
- `name`: the visible label (the action verb for steps,
  the question for decisions).
- `description`: any longer-form text inside the shape; empty otherwise.
- `bbox_in_tile`: `{x, y, w, h}`. Used by the reconciler to dedup and
  to reconstruct sequence order.
- `confidence`: `high | medium | low` per the standard scale.

For arrows whose label is readable in this tile:

- `type: "transition"`
- `name`: the branch label (`yes`, `no`, `escalate`, etc.) or
  `"unlabelled"` when there's no label.
- `description`: `"<source step> → <target step>"`.
- `bbox_in_tile`: tight box if possible.

## What NOT to extract

- Don't try to figure out the global step order from a single tile.
  The reconciler sorts by reading order (top-to-bottom, then
  left-to-right) using the structural map's `layout` hint.
- Don't combine a decision and its branches into one element.
- Don't invent `start` / `end` markers if the diagram doesn't show them
  — leave the chain open.

## Output shape

```json
{
  "tile_id": "tile_W0_R0_C0",
  "elements": [
    {"type": "step", "name": "Fetch order",
     "bbox_in_tile": {"x": 40, "y": 60, "w": 180, "h": 80},
     "confidence": "high"},
    {"type": "decision", "name": "Inventory available?",
     "bbox_in_tile": {"x": 260, "y": 60, "w": 200, "h": 100},
     "confidence": "high"},
    {"type": "transition", "name": "yes",
     "description": "Inventory available? → Reserve",
     "bbox_in_tile": {"x": 460, "y": 90, "w": 50, "h": 30},
     "confidence": "medium"}
  ]
}
```
