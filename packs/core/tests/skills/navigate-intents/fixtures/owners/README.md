# owners fixture

A corpus for the record-owner work: a product strategy, two capabilities with one
nested under the other, intents under each, a brief, and specs with open and closed
statuses. Every `Owner:` header form is present: plain, backticked, a value followed
by a comment, a value that is only a comment, an `Owner:` line inside a multi-line
comment, a second `Owner:` line, an `Owner:` line below the first `## ` line, one
owner in two letter-case and spacing variants, a non-ASCII capital letter, and an
absent line. Each capability's owner differs from the owners of the intents beneath
it, so context rows occur under "Full hierarchy", "By capability" and the roadmap.

Every value below is stated by hand from the spec's terms, never computed with the
code under test. The tables are machine-readable: a test splits each row on `|`,
trims each cell and removes one pair of surrounding backticks. A cell that holds a
string or a boolean is JSON. A cell that lists ids separates them with a comma and a
space; `-` means none. Hand-stated terms:

- **Owner key:** the owner with each run of spaces and tabs made one space, trimmed,
  and each letter A to Z made lower case. No other letter changes, so `Édith team`
  and `édith team` are two keys.
- **Owner label:** the `owner` of the node holding the key whose id is first in
  code-point order. For key `team two` that node is `capability:cap-nested`, which
  sorts before `intent:feat-d`, so the label keeps its two spaces. For key
  `owner-one` it is `brief:brief-n`, which sorts before `intent:strat-alpha`, so the
  label is `Owner-One`.
- **Name order:** display names compared in lower case: Alpha direction, Apple,
  Banana, Cherry, Damson, Elder, Fig, Grape, Nested, Top.
- **Open intents:** every intent except `intent:feat-b` (Fulfilled) and
  `intent:feat-e` (Withdrawn).
- **Matching record, Browse match, context row:** as the record-owners spec defines
  them. Under "Open", an intent is a Browse match only when it is open and matching.

## Owner table

`owner` is the raw value the derivation must return. The `form` column names the
AC-0001 case the record covers.

| Node id | Path | owner | form |
| --- | --- | --- | --- |
| `intent:strat-alpha` | `docs/product/intents/STRAT-0001-strat-alpha.md` | `"owner-one"` | plain |
| `capability:cap-top` | `docs/product/intents/CAP-0002-cap-top.md` | `"owner-two"` | backticked |
| `capability:cap-nested` | `docs/product/intents/CAP-0003-cap-nested.md` | `"Team  Two"` | repeated spaces, mixed case |
| `intent:feat-a` | `docs/product/intents/FEAT-0004-feat-a.md` | `"owner-three"` | value then comment |
| `intent:feat-b` | `docs/product/intents/FEAT-0005-feat-b.md` | `""` | only a comment |
| `intent:feat-c` | `docs/product/intents/FEAT-0006-feat-c.md` | `"owner-three"` | second `Owner:` line ignored |
| `intent:feat-d` | `docs/product/intents/FEAT-0007-feat-d.md` | `"TEAM TWO"` | same key as `Team  Two` |
| `intent:feat-e` | `docs/product/intents/FEAT-0008-feat-e.md` | `"Édith Team"` | non-ASCII capital |
| `outcome:feat-f` | `docs/product/intents/FEAT-0009-feat-f.md` | `""` | absent line |
| `intent:feat-orphan` | `docs/product/intents/FEAT-0010-feat-orphan.md` | `""` | line below the first `## ` |
| `brief:brief-n` | `docs/product/briefs/brief-n.md` | `"Owner-One"` | plain, label source |
| `spec:spec-open` | `docs/specs/spec-open/spec.md` | `""` | line inside a multi-line comment |
| `spec:spec-closed` | `docs/specs/spec-closed/spec.md` | `"owner-two"` | plain |

## Option list

The options of the Owner control over the whole-corpus export, in order. `key` is the
owner key; the "Any owner" and "No owner recorded" options hold none.

| Position | Option | key |
| --- | --- | --- |
| 1 | `Any owner` | `-` |
| 2 | `Owner-One` | `"owner-one"` |
| 3 | `owner-three` | `"owner-three"` |
| 4 | `owner-two` | `"owner-two"` |
| 5 | `Team  Two` | `"team two"` |
| 6 | `Édith Team` | `"Édith team"` |
| 7 | `No owner recorded` | `""` |

Position 6's key keeps its capital É, because only A to Z are lower-cased.

## Owner selector table

The intent ids `search` returns for the `owner` selector value, sorted by id. Only
intents are returned, so briefs and specs never appear.

| Value | Intent ids |
| --- | --- |
| `"owner-one"` | `intent:strat-alpha` |
| `"OWNER-ONE"` | `intent:strat-alpha` |
| `"  owner-one  "` | `intent:strat-alpha` |
| `"owner-three"` | `intent:feat-a`, `intent:feat-c` |
| `"owner-two"` | `capability:cap-top` |
| `"team two"` | `capability:cap-nested`, `intent:feat-d` |
| `"Team   TWO"` | `capability:cap-nested`, `intent:feat-d` |
| `"Édith Team"` | `intent:feat-e` |
| `"Édith team"` | `intent:feat-e` |
| `"édith team"` | `-` |
| `""` | `intent:feat-b`, `intent:feat-orphan`, `outcome:feat-f` |
| `"   "` | `intent:feat-b`, `intent:feat-orphan`, `outcome:feat-f` |
| `"owner-four"` | `-` |
| `"hidden-owner"` | `-` |
| `"late-owner"` | `-` |

## Non-owner selector table

One value each for the other `search` selectors, with the intent ids each returns,
sorted by id. `parentless` is true for an intent whose `Parent intent:` is `none`.

| Selector | Value | Intent ids |
| --- | --- | --- |
| `level` | `"capability"` | `capability:cap-nested`, `capability:cap-top` |
| `kind` | `"outcome"` | `outcome:feat-f` |
| `exact_status` | `"Withdrawn"` | `intent:feat-e` |
| `parentless` | `true` | `intent:feat-orphan`, `intent:strat-alpha` |
| `text` | `"apple"` | `intent:feat-a` |

## Browse expectations

"Browse all intents" over the whole-corpus export, one row per owner choice, Group
and Show choice. "Shown rows" lists every row link in display order, a parent before
its children, a "Hierarchy roots" or "Top-level capabilities" section before the
closed disclosure. "Context rows" is the subset of shown rows that are not Browse
matches. A tree is nested, so the hierarchy is: `intent:strat-alpha` holds
`outcome:feat-f` and `capability:cap-top`; `capability:cap-top` holds `intent:feat-a`,
`intent:feat-d` and `capability:cap-nested`; `intent:feat-d` holds `intent:feat-e`;
`capability:cap-nested` holds `intent:feat-b` and `intent:feat-c`; `intent:feat-orphan`
is its own root. Under "By capability", `capability:cap-top` holds `intent:feat-a`,
`intent:feat-d`, `intent:feat-e` and `capability:cap-nested`, `capability:cap-nested`
holds `intent:feat-b` and `intent:feat-c`, and `intent:strat-alpha`, `outcome:feat-f`
and `intent:feat-orphan` are in the closed disclosure "Not under a capability".

| Owner choice | Group | Show | Shown rows | Context rows |
| --- | --- | --- | --- | --- |
| `Owner-One` | Full hierarchy | All | `intent:strat-alpha` | `-` |
| `owner-three` | Full hierarchy | All | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-a`, `capability:cap-nested`, `intent:feat-c` | `intent:strat-alpha`, `capability:cap-top`, `capability:cap-nested` |
| `owner-two` | Full hierarchy | All | `intent:strat-alpha`, `capability:cap-top` | `intent:strat-alpha` |
| `Team  Two` | Full hierarchy | All | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-d`, `capability:cap-nested` | `intent:strat-alpha`, `capability:cap-top` |
| `Édith Team` | Full hierarchy | All | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-d`, `intent:feat-e` | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-d` |
| `No owner recorded` | Full hierarchy | All | `intent:strat-alpha`, `outcome:feat-f`, `capability:cap-top`, `capability:cap-nested`, `intent:feat-b`, `intent:feat-orphan` | `intent:strat-alpha`, `capability:cap-top`, `capability:cap-nested` |
| `Owner-One` | By capability | All | `intent:strat-alpha` | `-` |
| `owner-three` | By capability | All | `capability:cap-top`, `intent:feat-a`, `capability:cap-nested`, `intent:feat-c` | `capability:cap-top`, `capability:cap-nested` |
| `owner-two` | By capability | All | `capability:cap-top` | `-` |
| `Team  Two` | By capability | All | `capability:cap-top`, `intent:feat-d`, `capability:cap-nested` | `capability:cap-top` |
| `Édith Team` | By capability | All | `capability:cap-top`, `intent:feat-e` | `capability:cap-top` |
| `No owner recorded` | By capability | All | `capability:cap-top`, `capability:cap-nested`, `intent:feat-b`, `outcome:feat-f`, `intent:feat-orphan` | `capability:cap-top`, `capability:cap-nested` |
| `Owner-One` | Full hierarchy | Open | `intent:strat-alpha` | `-` |
| `owner-three` | Full hierarchy | Open | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-a`, `capability:cap-nested`, `intent:feat-c` | `intent:strat-alpha`, `capability:cap-top`, `capability:cap-nested` |
| `owner-two` | Full hierarchy | Open | `intent:strat-alpha`, `capability:cap-top` | `intent:strat-alpha` |
| `Team  Two` | Full hierarchy | Open | `intent:strat-alpha`, `capability:cap-top`, `intent:feat-d`, `capability:cap-nested` | `intent:strat-alpha`, `capability:cap-top` |
| `Édith Team` | Full hierarchy | Open | `-` | `-` |
| `No owner recorded` | Full hierarchy | Open | `intent:strat-alpha`, `outcome:feat-f`, `intent:feat-orphan` | `intent:strat-alpha` |

`intent:feat-e` is Withdrawn, so under "Open" the choice `Édith Team` shows no row. In
"By capability" with `No owner recorded`, `intent:strat-alpha` is not shown: it does not
match and nothing beneath it in that grouping does.

## Roadmap expectations

"How far along is each capability?" over the whole-corpus export. Both capabilities sit
in the section "Alpha direction", the display name of `intent:strat-alpha`, and
`capability:cap-nested` is nested under `capability:cap-top`. A capability is listed
when it is a matching record or a capability nested beneath it is listed.

| Owner choice | Sections | Listed capabilities | Context capabilities |
| --- | --- | --- | --- |
| `Owner-One` | `-` | `-` | `-` |
| `owner-three` | `-` | `-` | `-` |
| `owner-two` | `Alpha direction` | `capability:cap-top` | `-` |
| `Team  Two` | `Alpha direction` | `capability:cap-top`, `capability:cap-nested` | `capability:cap-top` |
| `Édith Team` | `-` | `-` | `-` |
| `No owner recorded` | `-` | `-` | `-` |

## Scoping

| Item | Value |
| --- | --- |
| Scoped capability | `capability:cap-nested` |
| Search text | `"feat"` |
| Empty scoped Browse choices | `Owner-One`, `owner-two` |

A `--from` export of `capability:cap-nested` holds that capability, `intent:feat-b`,
`intent:feat-c`, `brief:brief-n`, `spec:spec-open` and `spec:spec-closed`. Its Owner
control offers `Any owner`, `Owner-One`, `owner-three`, `owner-two`, `Team  Two` and
`No owner recorded`. `Owner-One` is held only by the brief and `owner-two` only by a
spec, so under either choice the scoped "Browse all intents" shows no row and the
scoped roadmap lists no capability.

The search text `feat` appears in the heading label "Feature:" of every feature and in
the slug of each; it matches no capability and no strategy. Under `Owner-One` and
`owner-two` nothing matches it, so those choices reach the empty search state.
