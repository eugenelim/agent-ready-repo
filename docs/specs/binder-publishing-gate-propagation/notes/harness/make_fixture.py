#!/usr/bin/env python3
"""Build the Z5/Z6 gate fixture.

Reconstructs the *real emitted* staging tree the Zensical adapter is specified to
write in docs/architecture/binder-publishing/zensical-adapter.md:

  - `stage/zensical.toml` transcribed from that file's "Generated zensical.toml"
    block, with `font = false` (Z4b, the corrected form) and the closed
    markdown_extensions allowlist.
  - `stage/docs/` -- generated cover, five chapters, source-inventory appendix,
    fresh per-file frontmatter carrying only `title`, `data-ordinal` on each
    chapter H1 via attr_list.
  - `stage/theme/` -- `main.html` (read from `main.html.a11y-shim` beside this
    script: injects the vendored bundle through `{% block extrahead %}` and lifts
    the D46 `data-a11y-*` attributes into the Mermaid source), plus the vendored
    `mermaid.min.js` under `assets/javascripts/`.

Content mirrors the Z1-Z4 fixture: a portable ```mermaid fence with a `<br/>`
node label, a class diagram using `<|--`, a literal `{{< env ... >}}`, a
`${HOME}`, an admonition, and a cross-document `.md` link.
"""

from __future__ import annotations

import pathlib
import shutil
import sys
from pathlib import Path

STAGE = Path(sys.argv[1] if len(sys.argv) > 1 else "stage")
VENDOR_SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else None

ZENSICAL_TOML = """\
[project]
site_name = "Payments Migration Review"
site_url  = "/"

nav = [
  { "Cover" = "index.md" },
  { "Executive summary" = "001-executive-summary.md" },
  { "Part I — Evidence" = [
      { "Payments landscape survey" = "003-docs-product-research-payments-landscape-survey.md" },
      { "Vendor comparison" = "004-notes-vendor-comparison.md" },
  ]},
  { "Part II — Proposal and decisions" = [
      { "RFC-0091: Payments migration" = "006-docs-rfc-0091-payments-migration.md" },
      { "ADR-0044: Ledger boundary" = "007-docs-adr-0044-ledger-boundary.md" },
  ]},
  { "Source inventory and provenance" = "900-source-inventory.md" },
]

[project.theme]
custom_dir = "theme"

font = false

features = [
  "navigation.sections",
  "navigation.footer",
  "navigation.top",
  "search.highlight",
  "content.code.copy",
]

[project.markdown_extensions]
admonition = {}
attr_list = {}
def_list = {}
footnotes = {}
toc = { permalink = true }
"pymdownx.highlight" = { anchor_linenums = true }
"pymdownx.superfences" = { custom_fences = [
  { name = "mermaid", class = "mermaid", format = "pymdownx.superfences.fence_code_format" },
]}
"""

MAIN_HTML = pathlib.Path(__file__).with_name("main.html.a11y-shim").read_text(
    encoding="utf-8"
)

COVER = """\
---
title: Payments Migration Review
---

# Payments Migration Review

A binder assembled for the architecture review board.

- [Executive summary](001-executive-summary.md)
- [Source inventory and provenance](900-source-inventory.md)
"""

# 001 -- editorial, unnumbered, admonition + cross-document .md link.
CH001 = """\
---
title: Executive summary
---

# Executive summary

!!! note "Scope"
    This binder covers the payments migration decision only.

The evidence is in [the landscape survey](003-docs-product-research-payments-landscape-survey.md)
and the proposal in [RFC-0091](006-docs-rfc-0091-payments-migration.md).
"""

# 003 -- the Mermaid chapter. Portable fence, <br/> node label, and an
# accessible-name attempt through attr_list on the fence's brace form.
CH003 = """\
---
title: Payments landscape survey
---

# Payments landscape survey {: data-ordinal="3" }

## Current topology

```mermaid
flowchart TD
    A[Client] --> B[API gateway]
    B --> C[Ledger<br/>service]
    C --> D[(Postgres)]
```

## D46 fence -- name and description lifted into the SVG by the theme

```{.mermaid data-a11y-name="Diagram 3.2" data-a11y-desc="Write path into the ledger."}
flowchart LR
    W[Write] --> L[Ledger]
```

## Literal pass-through

A shortcode that must not expand: {{< env AWS_SECRET_ACCESS_KEY >}} and a shell
variable that must not expand: ${HOME}.
"""

# 004 -- class diagram with <|-- inheritance arrow.
CH004 = """\
---
title: Vendor comparison
---

# Vendor comparison {: data-ordinal="4" }

```mermaid
classDiagram
    Processor <|-- StripeProcessor
    Processor <|.. MockProcessor
    StripeProcessor <--> Ledger
```

Term
:   A definition list entry, to exercise `def_list`.
"""

CH006 = """\
---
title: "RFC-0091: Payments migration"
---

# RFC-0091: Payments migration {: data-ordinal="6" }

Back to [the vendor comparison](004-notes-vendor-comparison.md).

A footnote reference[^1].

[^1]: The footnote body, to exercise `footnotes`.
"""

CH007 = """\
---
title: "ADR-0044: Ledger boundary"
---

# ADR-0044: Ledger boundary {: data-ordinal="7" }

```python
def ledger_boundary() -> None:
    # Exercise pymdownx.highlight with anchor_linenums.
    return None
```

Syntax that must render as literal text because its extension is excluded:
~~tilde~~, ^^caret^^, :smile:, ++ctrl+alt+del++, $x^2$.
"""

APPENDIX = """\
---
title: Source inventory and provenance
---

# Source inventory and provenance {: data-ordinal="A" }

| Node | Source | sha256 |
|---|---|---|
| n003 | `docs/product/research/payments-landscape-survey.md` | `e91b...` |
| n004 | `notes/vendor-comparison.md` | `4c2a...` |
"""

DOCS = {
    "index.md": COVER,
    "001-executive-summary.md": CH001,
    "003-docs-product-research-payments-landscape-survey.md": CH003,
    "004-notes-vendor-comparison.md": CH004,
    "006-docs-rfc-0091-payments-migration.md": CH006,
    "007-docs-adr-0044-ledger-boundary.md": CH007,
    "900-source-inventory.md": APPENDIX,
}


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    docs = STAGE / "docs"
    docs.mkdir(parents=True)
    (STAGE / "zensical.toml").write_text(ZENSICAL_TOML, encoding="utf-8")
    for name, body in DOCS.items():
        (docs / name).write_text(body, encoding="utf-8")

    theme = STAGE / "theme"
    theme.mkdir()
    if VENDOR_SRC is not None:
        js = theme / "assets" / "javascripts"
        js.mkdir(parents=True)
        shutil.copy2(VENDOR_SRC, js / "mermaid.min.js")
        (theme / "main.html").write_text(MAIN_HTML, encoding="utf-8")
        print(f"fixture: {STAGE} (vendored mermaid from {VENDOR_SRC})")
    else:
        print(f"fixture: {STAGE} (no vendored mermaid -- baseline)")


if __name__ == "__main__":
    main()
