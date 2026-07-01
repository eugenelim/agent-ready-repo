---
name: msg-to-markdown
description: Convert Outlook .msg and MIME .eml email files to Markdown with a versioned output contract, preserving headers (From, To, CC, BCC, Date, Importance), the body (HTML reduced to Markdown, or plain text), and an attachments table. Use when the user wants to convert, read, or process a .msg or .eml email into Markdown, or extract its attachments.
---

# Email (.msg / .eml) to Markdown Converter

Convert Outlook `.msg` and MIME `.eml` email into clean, structured Markdown at
**Tier 0 (no ML)**, preserving headers, body, and attachment metadata. Every
output carries the same versioned **unified output contract** (YAML frontmatter:
`contract-version`, `tier`, `source-file`, `content-type`, `ingestion-date`, and a
nested `ingestion-quality` block) that `file-to-markdown` emits, so a downstream
context layer ingests email exactly as it ingests documents.

This is a pure-Python skill. `.msg` is read via `olefile` + first-party MAPI
decoding; `.eml` via the Python stdlib. No Node.js, no ML/OCR model, no network
call. (See ADR-0046 for the reader decision.)

## Prerequisites

`.eml` conversion needs only the Python standard library. `.msg` conversion needs
**`olefile`** (BSD-2-Clause), resolved pip-on-demand — never auto-installed. Check
and install:

```bash
python scripts/convert.py --check          # exit 0 = present, 2 = absent
python -m pip install 'olefile>=0.47'       # if absent
```

## Instructions

When the user provides an email file path, convert it to Markdown that captures
the full email structure.

### Step 1: Verify the environment

For a `.msg` file, run `python scripts/convert.py --check`. Exit 0 → proceed. Exit
2 → tell the user to install `olefile` (command above), or run it once **with
their consent**; don't install it silently. `.eml` needs no check.

### Step 2: Convert

```bash
python scripts/convert.py "<path>"          # .msg or .eml; more than one path is fine
```

It writes `<basename>.md` next to the input (confined to the input's directory)
and prints:

- `WROTE: <path>` — the Markdown file
- `SUMMARY: <json>` — subject, from, to, date, body type, attachment/recipient counts
- `WARNING: …` — printed when the output is flagged `requires-review`

### Step 3: Extract attachments (if requested)

```bash
python scripts/convert.py --attachments "<path>"
```

Each attachment is written into `<basename>_attachments/` **confined** to that
directory: the stored filename is reduced to a basename (a traversal name like
`../evil` becomes `evil`; an absolute, drive, UNC, empty, or `.`/`..` name is
refused) and re-checked against the directory. Prints `EXTRACTED: <path>` or
`SKIPPED: <reason>` per attachment. Embedded messages have no flat byte stream and
are skipped (convert them by running this skill on the parent again, or on an
exported copy).

### Step 4: Report the result

1. Show the user a summary: subject, sender, date, recipient count, body type
   (HTML vs plain), and attachment count (from the `SUMMARY:` line).
2. If the body was HTML, mention it was reduced to Markdown and some complex
   formatting (embedded CSS, conditional Outlook markup) may have been simplified.
3. If there are attachments, list them and offer to extract them (Step 3).
4. If there are embedded messages (forwarded emails), the output carries a note;
   offer to convert them too.
5. Offer adjustments: stripping signature blocks, extracting inline images, a
   meeting-notes template, or batch-converting a folder (loop over each file).

## Output contract

The leading `---`-fenced block is the unified contract; the extracted body sits
below it. `tier` is always `0-no-ml`; `content-type` is `msg` or `eml`.
`ingestion-quality.requires-review` is `true` (and `extraction-confidence` `low`)
when the input was refused (oversized / malformed / resource-capped) or the body
is RTF-only. Because the frontmatter is emitted through the shared builder, hostile
subject/body content cannot forge or truncate it.

## Security & limits

`.msg`/`.eml` input is treated as untrusted. The skill enforces its **own**
resource ceilings around the reader (a `.msg` is an OLE2/CFBF file, not a zip, so
the zip-bomb guards do not apply): a per-stream byte cap that distrusts the
declared size, an OLE2 stream/storage-count cap, a cumulative-output budget, and a
`PidTagRtfCompressed` LZFu **declared-size** cap (RTF is never decompressed).
Embedded-message recursion is bounded to a **depth of 3** and a **total of 20**
(`MAX_EMBED_DEPTH` / `MAX_EMBED_COUNT` in `mapi.py`); beyond it the output surfaces
a note. Malformed input fails soft to `requires-review`, never a crash. No
attachment or MIME-part payload is parsed as XML.

## Edge cases to handle

- **RTF-only body**: some older messages store the body only in compressed RTF.
  This Tier-0 converter does **not** decompress RTF; it surfaces a note and flags
  `requires-review`. Suggest opening in Outlook and re-saving as HTML/plain text.
- **Winmail.dat / TNEF**: TNEF-encoded content is not decoded; it appears as an
  attachment. Note it and suggest a dedicated TNEF tool if the user needs it.
- **Inline images**: images referenced via `cid:` are attachments with a content
  ID; they are flagged `(inline)` in the attachments table. Markdown shows broken
  image references unless the attachments are extracted.
- **Email chains / quoted replies**: the body may contain quoted replies
  (`-----Original Message-----`, `>`-prefixed lines). They are preserved as body text.
- **Calendar invites (.ics)**: a `.ics` attachment is listed; offer to parse the
  event details into a structured section if the user wants.
- **Character encoding**: `.msg` string properties are UTF-16LE (or codepage);
  decoding is non-raising, so malformed text degrades rather than crashing.
- **Distribution lists**: To/CC may reference display names without addresses;
  they are preserved as-is.
- **Sensitivity labels / receipts**: not specially parsed; the message class and
  any surfaced properties appear in the output as-is.

## Scripts

- `scripts/convert.py` — the CLI (convert, `--attachments`, `--check`).
- `scripts/mapi.py` — bounded `olefile`-based MAPI reader (the resource wrap).
- `scripts/html_md.py` — HTML → Markdown reducer (stdlib `html.parser`).
- `scripts/contract.py`, `scripts/safe_io.py` — **vendored verbatim** from
  `file-to-markdown` (a drift-guard test keeps them byte-identical; edit the
  originals, then re-sync — do not edit these copies).
- `scripts/msg_fixtures.py`, `scripts/test_*.py`, `scripts/testdata/` — the test
  corpus generator, tests, and the independent-reader (Node `msgreader`) oracle
  baseline.

## Relationship to `file-to-markdown`

`file-to-markdown` ships a **flat** `.eml` reader at Tier 0 (headers + preferred
body). This skill is the **richer email specialist**: it also reads `.msg`, walks
multipart bodies and nested `message/rfc822` parts, maps richer headers, and lists
attachments — but for a shared simple `.eml` the **contract frontmatter is
identical** across both (a test pins this); this skill's body/header output is a
documented superset. `file-to-markdown`'s flat route is unchanged.
