# API reference

## `parse(text, strict=False)`

Parses `text` and returns a `Document`.

- `text`: the input string.
- `strict`: raise on malformed input when true.

## `Document`

A parsed result. Attributes: `nodes`, `source`.

<!-- TODO: document `Document.walk()`, `Document.to_dict()`, and the exceptions raised. -->
