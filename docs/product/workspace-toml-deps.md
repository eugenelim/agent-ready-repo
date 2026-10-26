# Dependency edges — header reference

A piece of work records that it waits for another by one line in its own file:
the `Depends on:` header. `workspace-status` reads that line and blocks the work
until each item it names is satisfied. The registry entry in `workspace.toml`
holds no edge: its `needs` stays `[]`.

The design is RFC-0106 D3. The receipt's carrier is recorded in the ADR that
supersedes ADR-0103 D6 in part. The guide
[`workspace-toml-schema.md`](../../guides/core/reference/workspace-toml-schema.md)
is the adopter-facing reference. `workspace.toml` in the repository root is the
lived example.

---

## Where the lines go

Both lines go in the preamble of the file the registry entry's `path` names
(a spec, brief, intent, or captured item). The preamble is every line before the
first `## ` heading, outside fenced blocks, with HTML comments hidden.

```markdown
- **Depends on:** spec:workspace-core, brief:platform-core
- **Dependency receipts:** spec:retired-delivery completion retired-42 completed release commit:0123456789abcdef0123456789abcdef01234567
```

---

## `Depends on:`

The line holds comma-separated items. Empty items are dropped. A line whose first
word is `none` adds no item. Each item is one of:

| Item | Meaning |
| --- | --- |
| `spec:<slug>` | the spec at `docs/specs/<slug>/spec.md` |
| `brief:<slug>` | the delivery brief whose `Slug:` is `<slug>` |
| `<intent kind>:<slug>` | the live intent of that kind with that `Slug:`; the kind is `intent`, `outcome`, `opportunity`, or `capability` |
| a captured-item path | a repository path such as `docs/product/design/payment-routing.md`; its kind comes from its registry entry, or from its own `Kind:` line when it has none |

A slug is one or more lowercase letters, digits, and hyphens, starting with a
letter or digit. A repository path to a spec, brief, or intent is not a
captured-item path: write the typed reference instead.

An item that is neither form, names more than one target, or is a captured item
with no kind gives an `invalid_dependency` finding, and the work is not
dispatchable. A wrapped line gives the same finding, so keep each line on one
line.

---

## `Dependency receipts:`

The line holds comma-separated receipts, each for an item of the same file, with
tokens separated by whitespace:

- `<reference> completion <delivery_id> <outcome> <completion_event> <evidence_ref>`
  settles a dependency whose delivery shipped and was then removed from the
  registry. The `outcome` is `completed`, `abandoned`, or `superseded`. A
  captured-item reference may not carry one.
- `<reference> coordination <remote_kind> <receipt_id> <accepted_revision>`
  pins a cross-repository dependency on a `brief:` reference. The brief holds the
  matching reviewed `toml coordination-receipts` block.

A second receipt for the same reference, or a receipt whose reference is not an
item of the same `Depends on:` line, gives `invalid_dependency`.

---

## What blocks

The satisfaction rules are unchanged from the registry form: a spec, brief, or
intent is satisfied at its terminal state, a defect when it is closed, and a
removed delivery by its valid completion receipt. Only the place the edge is read
from moved. A dependency cycle among non-cooled items gives `dependency_cycle`.
A cooled waiting item contributes no edge.

Agents read `workspace-status` output to decide what to work on next. They do not
enforce the graph themselves.

---

## Legacy `needs` is repair input only

Older registry entries carry `needs` as a string, a list of strings, or typed
records. No reader derives a dependency from them. An entry that still carries a
non-empty `needs` gets `unmigrated_needs` and is not dispatchable, whatever its
header says.

To move the edges:

1. Run `workspace-status repair-plan`. It writes `.workspace-repair-plan.json`
   with one `needs-to-header` operation for each waiting item, holding the
   header lines it will add. An edge the header cannot hold as the same edge
   becomes a manual finding that names the waiting path.
2. Read the plan and confirm that exact plan.
3. Run `workspace-status repair-apply`. It adds the lines, sets each migrated
   entry to `needs = []`, and compares the header edges read before and after
   the write with the registry edges. It exits non-zero when they differ.

A cooled waiting item gets a `needs-drop-cooled` operation instead: its edges
are dropped, because a cooled item contributes none. The full steps are in the
`workspace-status` skill's `references/mutate.md`.
