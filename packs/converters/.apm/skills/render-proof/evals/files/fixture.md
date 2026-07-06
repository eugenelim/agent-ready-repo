# Render Proof Fixture

This document exercises every GFM atomic element required by the render-proof spec.

## Typography

This paragraph contains **bold text**, *italic text*, `inline code`, and a [hyperlink](https://example.com).

Combined styling: ***bold and italic*** text side by side.

## Lists

### Ordered list

1. First item
2. Second item
3. Third item

### Unordered list

- Alpha entry
- Beta entry
- Gamma entry

### Task list

- [ ] Unchecked task — pending
- [x] Checked task — done
- [ ] Another pending item

## Code blocks

### Python

```python
def greet(name):
    """Return a greeting string."""
    return f"Hello, {name}!"

result = greet("world")
print(result)
```

### Bash

```bash
#!/bin/bash
set -euo pipefail

echo "Render proof fixture"
find . -name "*.md" | head -5
```

## Table

| Column A | Column B | Column C |
|---|---|---|
| Row 1 A  | Row 1 B  | Row 1 C  |
| Row 2 A  | Row 2 B  | Row 2 C  |
| Row 3 A  | Row 3 B  | Row 3 C  |

## Blockquote

> This is a blockquote paragraph.
> It spans multiple lines and demonstrates
> the blockquote left-border styling.
>
> A second paragraph inside the same blockquote.

## Heading levels

### h3 Heading

Content under the h3 heading level.

#### h4 Heading

Content under the h4 heading level, displayed in small caps.

---

End of render-proof fixture.
