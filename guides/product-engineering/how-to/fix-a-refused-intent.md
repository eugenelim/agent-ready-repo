---
title: "Fix a refused intent"
summary: Read the refusal, find the field it names, and apply the one remedy that clears it.
pack: product-engineering
kind: how-to
---

# Fix a refused intent

Two things check an intent's shape, and both name the field at fault. The
corpus check walks a directory of intents and exits non-zero. A cold shaping
review reads one intent and emits `MALFORMED(shape)`. This page takes each
refusal to its remedy.

:::note
**Diátaxis: how-to.** For what every field means and which tier it sits in, see
the reference *Intent fields, modes, and projection profiles*.
:::

## Run the check

The corpus check ships with the `work-intake` skill as
`intent_corpus_lint.py`. Point it at your intents directory:

```bash
python3 intent_corpus_lint.py --dir docs/product/intents --root .
```

It prints one progress line per intent on stdout and every refusal on stderr,
then exits.

| Exit | Meaning |
| --- | --- |
| `0` | every file read, every file conforms |
| `1` | at least one intent is non-conforming |
| `2` | a file could not be read, so the run proves nothing about it |

Exit `2` is deliberately not exit `1`. "No violations found" and "clean" are
different claims when a file would not open, and a check that reported an
unreadable corpus as clean would be worse than one that refused.

## Read the refusal

Every line is `<file>: <field>: <reason>`. The field is the fix's address.

## The refusals, and what clears each one

### A required field is absent

```text
FEAT-0001-missing-owner.md: Owner: required preamble field is absent
```

Four fields are required: `Owner`, `Slug`, `Level`, `Status`. Add the named one
to the preamble — the run of `- **Field:** value` lines above the first `## `
heading.

Declare the value; do not derive it. `Owner` in particular is not read from
commit history, because the person who last edited a file is often not the
person accountable for the outcome.

### A value is outside its set

```text
FEAT-0002-bad-status.md: Status: value 'Shipped' is outside Draft, Accepted,
Fulfilled, Withdrawn, Cancelled, and `Superseded by <slug>`
FEAT-0003-bad-kind.md: Kind: value 'objective' is outside outcome, opportunity
```

The reason lists the whole set, so the remedy is in the message. `Status` also
accepts `Superseded by <slug>`, where the slug names a live intent.

A near-miss is still a miss: `Shipped` is a spec status, not an intent status,
and lowercase `draft` is not `Draft`.

`Level` never appears here. Its set is open, so its value is never judged —
name an intervening altitude if your organization has one.

### A progress field carries the wrong shape

```text
FEAT-0004-bad-derisked.md: De-risked: value 'soon' is neither an ISO 8601 date
nor the literal `no`
FEAT-0005-bad-decomposed.md: Decomposed: value '2026-09-22 brief spec' is
neither the literal `no` nor an ISO 8601 date followed by exactly one terminus
```

`De-risked` and `Shaping-reviewed` each take a date or the literal `no`. A
date means the calendar form `YYYY-MM-DD`: the basic form `20260922`, a week
date, and an ordinal date are all refused.
`Decomposed` takes `no`, or a date plus **exactly one** terminus from
`children`, `brief`, `spec`, `direct-light`. Two termini is a refusal, and so
is a date with none.

If you have not reached that stage, delete the line. Absent is a legitimate
state and never fails a check — it means nobody recorded an answer, where `no`
means someone decided against it.

### The field name is retired

```text
FEAT-0006-retired-name.md: Authority: retired preamble field name
```

Six names are refused: `Type`, `Raised`, `Stage`, `Parent`, `Source`,
`Authority`. Rename to the replacement in the reference's field table —
`Authority` becomes `Governed by`, `Parent` becomes `Parent intent`.

Only the preamble is checked, so an `Authority:` line *below* the first heading
is untouched. There it is an attribution or a provenance token, not this field,
and renaming it would lose that distinction.

### The same field appears twice

```text
FEAT-0007-repeated.md: Governed by: preamble field appears more than once (2)
```

Merge the values onto one line. A preamble field ends at its newline, so a
second line is a second field rather than a continuation, and nothing decides
which of the two wins.

### A `direct-light` decomposition has no items

```text
FEAT-0008-empty-items.md: Decomposed: `direct-light` terminus carries no
checkbox item under `## Decomposition`
```

When `Decomposed` ends in `direct-light`, the work is executed directly rather
than handed to a child intent, a brief, or a spec — so this intent is the only
place the requested outcomes are written down. Add a `## Decomposition`
section with one checkbox item per outcome, each carrying text:

```markdown
## Decomposition

- [ ] Rename the retired field across the corpus
```

An empty item is refused too, for the same reason: a box with no text records
that something is owed without saying what.

The other three termini leave the section unread, because the child intent,
brief, or spec carries the detail instead.

### A supersession points at nothing

```text
FEAT-0009-ghost.md: Status: `Superseded by` slug 'a-ghost' matches no live
intent's `Slug:`
```

`Superseded by` takes the `Slug` of a **live** intent — the bet that replaced
this one. Fix the slug, or choose a different status: `Withdrawn` and
`Cancelled` both end an intent without naming a successor.

A retired artifact's slug does not answer this. A supersession says which bet
took over, and a retired file is not a bet.

### A tombstone is malformed

```text
FEAT-0010-tombstone.md: Reissued as: a tombstone carries exactly one of
`Reissued as:` or `Retired:`, and this one carries 0
FEAT-0010-tombstone.md: Tombstone: a tombstone carries exactly 3 fields, and
this one carries 2
```

A file whose preamble carries `Tombstone:` is checked as a tombstone instead of
a live intent. It carries exactly three fields: the `Slug` it had before
retirement, the `Tombstone` date, and exactly one of `Reissued as:` or
`Retired:`. Both is as wrong as neither, and a fourth field is refused.

### The shaping review says `MALFORMED(shape)`

The cold review reads one intent and reports conditions it can settle from the
text alone. `MALFORMED(shape)` means the preamble fails one of the rules above.
Run the corpus check on that file to learn which — the review names the
condition, the check names the field.

One exception: a preamble with no owner emits `MALFORMED(owner)` alone, and
every other condition stays silent. Fix the owner first, then re-run.

## A refusal that is not about your intent

Exit `2` with an `unreadable:` line means the check could not read something.
Two shapes, and they differ in how much of the run survives.

**One file could not be read.** It is not valid UTF-8, or it exceeds the size
bound:

```text
unreadable: FEAT-0011-binary.md: UnicodeDecodeError
intent-corpus-lint: 0 violation(s), 1 unreadable — 10 file(s), 9 live, 1 tombstone
```

The named file is skipped and every other file is still checked — the counts
show ten files routed. One unreadable file does not hide the rest.

**The directory itself could not be walked.** A link, rather than a regular
file, is the usual cause:

```text
unreadable: /path/to/intents: UnsafeContentError
intent-corpus-lint: 0 violation(s), 1 unreadable — 0 file(s), 0 live, 0 tombstone
```

Here the path is the directory, not a file, and the counts are all zero: the
walk stopped, so the run says nothing about any intent. Do not read this as a
clean corpus with one bad file. Replace the link with a regular file and re-run
before trusting anything else the run reported.

Either way the exit code stays non-zero until every file can be read.

## Check your work

Re-run the command. Exit `0` with `clean` in the summary line means every file
was read and every file conforms:

```text
intent-corpus-lint: clean — 150 file(s), 150 live, 0 tombstone
```

The counts are worth a glance. If the live and tombstone totals do not add up
to the file count, a file went unrouted, which is a defect in the check rather
than in your intent.
