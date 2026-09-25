---
title: "Fix a refused intent"
summary: Read the refusal, find the field it names, and apply the one remedy that clears it.
pack: product-engineering
kind: how-to
---

# Fix a refused intent

Two things check an intent's shape, and they neither tell you the same amount
nor cover the same rules. The corpus check walks a directory of intents, exits
non-zero, and names the field at fault — every message quoted on this page is
one of its, and the rules decided over the whole corpus are its alone. A cold
shaping review reads one intent against the packet it was handed and emits a
token per failed condition, of which `MALFORMED(shape)` is the preamble one; a
missing owner emits `MALFORMED(owner)` alone and suppresses the rest. A token
names the condition, never the field or the rule, so a returned token tells you
to run the check, not which message to read. This page takes each
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

Four fields are always required: `Owner`, `Slug`, `Level`, `Status`. Two more,
`Accepted:` and `Fulfilled:`, are required only for certain `Status` values —
*A status requires a record, or forbids one* below covers those. Add the named
field to the preamble — the run of `- **Field:** value` lines above the first
`## ` heading.

Declare the value; do not derive it. `Owner` in particular is not read from
commit history, because the person who last edited a file is often not the
person accountable for the outcome.

### A value is outside its set

```text
FEAT-0002-bad-status.md: Status: value 'Shipped' is outside Draft, Accepted,
Fulfilled, Withdrawn, Cancelled, Superseded
FEAT-0003-bad-kind.md: Kind: value 'objective' is outside outcome, opportunity
```

The reason lists the whole set, so the remedy is in the message. Every `Status`
value is one bare word; the supersession pointer is a field of its own, covered
below.

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
`Authority`. The reference's field table gives each one its answer, and they
are not all renames. `Authority` becomes `Governed by`, `Parent` becomes
`Parent intent`, `Stage` becomes `Status`, and `Type` becomes `Kind`. The other
two move rather than rename: `Source` becomes a `## Source` body section, and
`Raised` becomes `De-risked` or `Shaping-reviewed` if it recorded a dated
fact — or is deleted if it recorded nothing the contract keeps.

Only the preamble is checked, so an `Authority:` line *below* the first heading
is untouched. There it is an attribution or a provenance token, not this field,
and renaming it would lose that distinction.

### The same field appears twice

```text
FEAT-0007-repeated.md: Governed by: preamble field appears more than once (2)
```

Merge the values onto one line, keeping both:

```markdown
- **Governed by:** the first value, the second value
```

Nothing is dropped, because nothing decides which of the two lines would have
won. A preamble field ends at its newline, so a second line is a second field
rather than a continuation.

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

### A supersession is missing half of itself

Supersession is two fields, not one value. `Status: Superseded` says this bet
was replaced; `Superseded by:` says what replaced it. Neither is meaningful
alone, so each is refused without the other.

```text
FEAT-0009-orphan.md: Superseded by: `Status: Superseded` carries no
`Superseded by:` field naming the intent that replaced this bet
FEAT-0010-stranded.md: Superseded by: field is present beside `Status: Draft`,
and only `Status: Superseded` carries a supersession pointer
```

For the first, add the field. For the second, decide which half was wrong: if
the bet really was replaced, set `Status: Superseded`; if it was not, delete the
pointer. A pointer left behind after a status moved on is the usual cause.

A line whose value is only a comment counts as absent, so a template's
`- **Superseded by:** <!-- ... -->` does not satisfy the first message.

### A supersession points at nothing

```text
FEAT-0011-ghost.md: Superseded by: slug 'a-ghost' matches no intent this
pointer may resolve to: the target must be live and not itself `Superseded`
```

`Superseded by:` takes the `Slug` of a **live** intent — the bet that replaced
this one. Fix the slug, or choose a different status: `Withdrawn` and
`Cancelled` both end an intent without naming a successor.

A retired artifact's slug does not answer this. A supersession says which bet
took over, and a retired file is not a bet. Neither does an intent that is
itself `Superseded`: the pointer resolves one hop, so a chain has to be
re-pointed rather than followed. That is the whole rule — the target must be in
the live corpus and must not itself be `Superseded`. No other status is checked,
so a pointer at a `Cancelled` or `Withdrawn` intent resolves, and whether that
reads sensibly is a judgement the check leaves to you.

### A ratification or fulfilment record carries no evidence

```text
FEAT-0012-bare.md: Accepted: value '2026-09-20' is not an ISO 8601 date
followed by evidence text
FEAT-0013-comma.md: Fulfilled: '2026-09-20,' is not an ISO 8601 date
```

`Accepted:` and `Fulfilled:` each take a date, a space, then text. A date alone
is refused on purpose: these records exist to carry the reasoning, and a date
carries none. The check asks only that text is present — write what justifies
the claim, who decided and on what evidence, because that is the whole point of
the field.

The second message is the one that surprises people. The date is the text up to
the first space, so a comma written straight after it lands *inside* the date
token. Move the punctuation, or drop it:
`2026-09-20 by you, on an independent review`.

Unlike `De-risked:` and `Shaping-reviewed:`, the literal `no` is not accepted
here. An intent that was never ratified omits the field rather than denying it.

### A status requires a record, or forbids one

```text
FEAT-0014-closed.md: Accepted: status `Fulfilled` requires an `Accepted:` record
FEAT-0014-closed.md: Fulfilled: status `Fulfilled` requires a `Fulfilled:` record
FEAT-0015-open.md: Accepted: status `Draft` carries an `Accepted:` record; `Draft` means open
```

A status that claims the work was delivered has to carry the records that
authorise it, and a status that claims nothing yet must not. Which applies is
decided by `Status` alone:

| `Status` | `Accepted:` | `Fulfilled:` |
| --- | --- | --- |
| `Draft` | refused | refused |
| `Accepted` | optional | refused |
| `Fulfilled` | **required** | **required** |
| `Cancelled` | **required** | refused |
| `Withdrawn` | optional | refused |
| `Superseded` | neither required nor refused | neither required nor refused |

To clear a *requires* refusal, add the named record. To clear a *carries*
refusal, either delete the record or move `Status` to the state that earned it —
the message names which state you are in and why it disagrees.

`Withdrawn` is the exception worth knowing: it never needs `Accepted:`, because
abandoning a bet nobody ratified needs no ratification. `Cancelled` does need
it — cancelling says the work was ratified and then stopped.

**Write the record in the preamble, not the body.** A `- **Accepted:** …` line
below the first `## ` heading is read as absent, so you get a *requires* refusal
while looking straight at a line that appears to supply it. If the message
insists a record is missing and you can see it, check which side of the first
heading it sits on.

### A tombstone is malformed

```text
FEAT-0010-tombstone.md: Reissued as: a tombstone carries exactly one of
`Reissued as:` or `Retired:`, and this one carries 0
FEAT-0010-tombstone.md: Tombstone: a tombstone carries exactly 3 fields, and
this one carries 2
```

A file whose preamble carries `Tombstone:` is checked as a tombstone instead of
a live intent. It carries exactly three fields and no others — a fourth is
refused, and both edges at once is as wrong as neither:

```markdown
# Retired: work-item capture and disposition

- **Slug:** `work-item-capture-and-disposition`
- **Tombstone:** 2026-09-22
- **Reissued as:** CAP-0007-work-item-capture-and-disposition.md
```

`Slug` is the one the artifact had before retirement, unchanged. `Tombstone`
carries the retirement date. Use `Reissued as:` with the path the artifact
moved to when it still exists somewhere, and `Retired:` with a short reason
when it does not:

```markdown
- **Retired:** the bet was withdrawn before any work started
```

The check counts the fields and notices whether each carries a value, but it
does not judge the values' format — so a malformed date passes it. Write the
date the way every other date in an intent is written.

### The shaping review says `MALFORMED(shape)`

The cold review reads one intent and reports conditions it can settle from the
packet it was given. `MALFORMED(shape)` means the preamble failed that
condition — it does not say which rule, and it may also mean the packet could
not settle it, because an unsettled condition fails closed.

So run the corpus check over the directory and read the line for that file.
That is what names the field and the rule; the token only says where to look.
The check takes a directory rather than a single file, so there is nothing to
narrow.

**The two do not cover the same rules, so the check may say nothing.** A
supersession pair split across `Status` and `Superseded by:`, and a pointer
that resolves nowhere, are decided over the whole corpus — the review never
sees them, and `MALFORMED(shape)` is not how they surface. The reverse also
holds: a shape token with no corpus line behind it means the review's packet,
not your intent, is what could not settle the condition.

One exception: a preamble with no owner emits `MALFORMED(owner)` alone, and
every other condition stays silent. Fix the owner first, then re-run.

## A refusal that is not about your intent

Exit `2` with an `unreadable:` line means the check could not read something.
Two shapes, and they differ in how much of the run survives.

**One file could not be read.** It is not valid UTF-8, or it is larger than
one megabyte, which is the bound the check reads up to. An intent is prose, so
either usually means the file is not the intent you think it is — a binary
committed under the wrong name, or generated output. Open it and confirm before
changing anything; the repair is to fix the encoding or move the file out of the
directory, not to raise a limit.

```text
unreadable: FEAT-0005-binary.md: UnicodeDecodeError
intent-corpus-lint: 0 violation(s), 1 unreadable — 5 entries, 3 live, 1 tombstone, 1 unreadable
```

The named file is skipped and every other file is still checked — three live
intents and one tombstone were validated. One unreadable file does not hide the
rest.

**The directory could not be walked.** A link somewhere in it is the usual
cause — either the directory itself or an entry inside it. Size is the next
most likely: the walk refuses a tree deeper than eight levels, or one holding
more than ten thousand files or fifty thousand entries. Any other read failure
surfaces the same way, a permission error among them. The message names the
directory in every case, so it does not say which entry, which bound, or which
error is at fault — the exception name after the colon is the clue:

```text
unreadable: /path/to/intents: UnsafeContentError
intent-corpus-lint: 0 violation(s), 1 unreadable — 1 entry, 0 live, 0 tombstone, 1 unreadable
```

Here the path is the directory, not a file, and nothing was validated: the one
entry accounted for is the directory itself, and the walk stopped, so the run
says nothing about any intent. Do not read this as a
clean corpus with one bad file. List the directory and read the exception
name. `UnsafeContentError` means a link or a bound: replace the link with a
regular file, or question an intents directory large enough to hit a bound
rather than working around it. An `OSError` or `PermissionError` means the
entry could not be opened at all. Re-run before trusting anything else the run
reported.

Either way the exit code stays non-zero until every file can be read.

## Check your work

Re-run the command. Exit `0` with `clean` in the summary line means every file
was read and every file conforms:

```text
intent-corpus-lint: clean — 150 entries, 150 live, 0 tombstone, 0 unreadable
```

The counts are worth a glance. Live plus tombstone plus unreadable should
equal the entry count. If they do not, a file went unmentioned, which is a
defect in the check rather than in your intent — report it rather than editing
an intent to satisfy it.
