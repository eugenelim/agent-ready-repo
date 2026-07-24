# Voice chart: <product name>

> **This is a template, not a schema.** It shows the *shape* of a product's voice
> chart — where the product sits on a few voice axes, how its tone flexes by
> context, and the words it prefers. Copy it to `docs/product/voice/<slug>.md` and
> fill in what you have; an empty field is a prompt, not an error. Characterize the
> voice once and **reuse this chart** across features — don't re-derive it per
> screen. Keep only the rows that earn their place.

- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Product:** `<what this voice belongs to>`

## Voice axes

<!-- Place the product on each axis — not always the middle. Justify in one line
from who the user is and what they came to do, and write one real sample line in
that voice. Add or drop an axis if the product needs it. See
references/voice-axes.md. -->

| Axis | Position (one end ↔ other) | Why | Sample line |
| --- | --- | --- | --- |
| Humor | `<serious ↔ playful>` | <one line> | <a real string> |
| Formality | `<formal ↔ casual>` | <one line> | <a real string> |
| Respect | `<deferential ↔ irreverent>` | <one line> | <a real string> |
| Enthusiasm | `<calm ↔ enthusiastic>` | <one line> | <a real string> |

## Tone flex by context

<!-- Voice is constant; tone flexes for the user's emotional state. The higher the
stress, the closer the tone moves to plain and calm — even for a playful product. -->

| Context | Tone |
| --- | --- |
| Success / celebration | <warmest the voice allows> |
| Routine action | <the default voice> |
| Error / failure | <calm, plain, blame-free> |
| Destructive / high-stakes confirm | <most serious; no wit> |
| Waiting / loading | <brief, reassuring> |

## Terminology

<!-- One concept, one word, everywhere. Preferred term + what to avoid, so the same
thing reads the same way on every screen. -->

| Concept | Use | Avoid |
| --- | --- | --- |
| <e.g. the container a user works in> | `<workspace>` | `<project, board>` |
| | | |

## Do / don't (optional)

<!-- A few sample strings that capture the voice in action — the fastest way for
the next writer to match it. -->

- ✅ <a line that nails the voice>
- ❌ <a line that misses it, and why>
