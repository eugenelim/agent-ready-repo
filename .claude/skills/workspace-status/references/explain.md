# Explain — investigate one item

Load this when the chosen mode is `explain`. It answers questions about a
single item; it never surveys the queue.

**`explain`** — pass a slug or `spec/` path to get the item's current classification, dependencies, blocking needs, and which downstream items would become unblocked if this item shipped. Lookup is restricted to **active initiatives' work queues** (queue/active/shipped); shaping items and items in paused or closed initiatives return `selector_status: "not_found"`.

## Closeout orientation

For closeout orientation, project only current pause, closeout blockers,
all-specs-shipped initiative eligibility, cooling-context visibility, and the next
action to invoke `close-work`. Never infer semantic freshness, choose a disposition,
confirm authority, distil content, record a closeout result, compact coordination,
remove an entry, or delete. A paused item remains visible as paused.
