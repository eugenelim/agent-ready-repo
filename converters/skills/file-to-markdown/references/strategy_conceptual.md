# Strategy: conceptual

The catch-all strategy for diagrams that don't fit architecture,
event-storm, process, or domain. Use it for mind maps, capability maps,
quadrant diagrams, sketches, and anything ad-hoc.

## What to extract from each tile

For every visible labelled shape:

- `type`: pick the most descriptive of `node`, `group`, `annotation`,
  `legend`, `connection`. Lowercase.
- `name`: the visible label.
- `description`: any inline text.
- `bbox_in_tile`: `{x, y, w, h}` if you can.
- `confidence`: standard scale.

## What NOT to extract

- Don't invent a more specific `type` than the diagram supports — if
  it's a sketch with unlabelled blobs, use `node`.
- Don't fabricate relationships you can't see.

## Output shape

```json
{
  "tile_id": "tile_W0_R0_C0",
  "elements": [
    {"type": "node", "name": "Onboarding",
     "bbox_in_tile": {"x": 100, "y": 80, "w": 160, "h": 60},
     "confidence": "medium"},
    {"type": "annotation", "name": "Q1 priority",
     "bbox_in_tile": {"x": 280, "y": 90, "w": 110, "h": 30},
     "confidence": "low"}
  ]
}
```

If `confidence` is mostly `low`, the resulting Markdown will carry
`requires-review: true` in its frontmatter — that's the correct
outcome for sketchy inputs, not a bug.
