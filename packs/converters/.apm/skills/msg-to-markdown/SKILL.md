---
name: msg-to-markdown
description: Convert Outlook .msg email files to Markdown, preserving email headers (From, To, CC, Date), body content, and attachment metadata. Use when the user wants to convert, read, or process a .msg email file into Markdown format.
---

# Outlook MSG to Markdown Converter

Convert Outlook `.msg` email files to clean, structured Markdown preserving headers, body, and attachment metadata.

## Prerequisites

The converter runs on Node.js and reads `.msg` files through an npm
package — `@nicecode/msg-reader` (preferred) or `msgreader` as an
alternative. `scripts/convert.js` uses whichever is installed. Install
the preferred one once:

```bash
npm install @nicecode/msg-reader
```

## Instructions

You are a document conversion agent. When the user provides a `.msg` file path via `$ARGUMENTS`, convert it to Markdown that captures the full email structure.

### Step 1: Verify the environment

Confirm Node.js and a reader package are available. From the skill's own
directory, check for either supported package (mirroring what
`convert.js` resolves):

```bash
node -e "try{require.resolve('@nicecode/msg-reader')}catch{require.resolve('msgreader')}"
```

- Exit 0 → at least one reader is installed; proceed to Step 2.
- Non-zero → neither is installed. Confirm `npm` is available
  (`npm --version`); if npm is missing, tell the user to install
  Node.js and stop. Otherwise tell the user to run the install command
  from Prerequisites (or, **with their consent**, run it once and
  re-verify). Don't install it silently.

### Step 2: Extract the email data

Run the conversion script, replacing `$ARGUMENTS` with the input file path:

```bash
node scripts/convert.js "$ARGUMENTS"
```

### Step 3: Extract attachments (if requested)

If the user asks to extract attachments, run the attachments script:

```bash
node scripts/extract-attachments.js "$ARGUMENTS"
```

### Step 4: Report the result

After conversion:

1. Show the user a summary: subject, sender, date, recipient count, body type (HTML vs plain text), and attachment count
2. If the email had an HTML body, mention that it was converted from HTML and some complex formatting (e.g., embedded CSS styles, conditional Outlook markup) may have been simplified
3. If there are attachments, list them and ask if the user wants them extracted to a folder
4. If there are embedded `.msg` files (forwarded emails), offer to recursively convert those too
5. Ask if they'd like adjustments:
   - Including or stripping email signature blocks
   - Extracting inline images
   - Converting the email into a more structured format (e.g., meeting notes template)
   - Batch-converting a folder of `.msg` files

### Input format

The user provides the argument as a file path, e.g.:

- `emails/important-update.msg`
- `./meeting-invite.msg`
- `/absolute/path/to/forwarded-chain.msg`

If the user provides a glob pattern like `emails/*.msg`, loop through each file and convert them individually.

### Edge cases to handle

- **RTF body**: Some older Outlook messages store the body only in RTF format (no HTML or plain text). If both `htmlBody` and `body` are empty, note that the email likely uses RTF-only encoding and suggest the user open it in Outlook to re-save as HTML, or install an RTF parser.
- **Winmail.dat / TNEF**: Some `.msg` files contain TNEF-encoded content. If the reader fails to parse, suggest the `node-tnef` package as an alternative.
- **Inline images**: Images referenced via `cid:` URLs in the HTML body are stored as attachments with a `contentId`. Flag these separately from regular attachments and note that the Markdown will show broken image references unless attachments are extracted.
- **Email chains / conversation threads**: The body may contain quoted replies. Look for patterns like `From:` headers mid-body, `>` prefixed lines, or `-----Original Message-----` dividers. Preserve these as nested blockquotes in the Markdown.
- **Calendar invites (.ics)**: If an attachment is a `.ics` file, mention it's a calendar invite and offer to parse the event details (date, time, location, attendees) into a structured Markdown section.
- **Character encoding**: `.msg` files may use various encodings. If the output contains garbled text, try reading string properties with different encodings (UTF-8, UTF-16LE, Windows-1252).
- **Distribution lists**: The To/CC fields may reference Outlook distribution lists rather than individual addresses. These may appear as display names without email addresses — preserve them as-is.
- **Sensitivity / classification labels**: Some corporate emails have sensitivity labels (Confidential, Internal, etc.). If present in the message properties, include them in the metadata table.
- **Read receipts / delivery receipts**: These are special message types. If the message class indicates a receipt rather than a normal email, format the output accordingly with the receipt metadata.
