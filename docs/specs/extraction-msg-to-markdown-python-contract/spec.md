# Spec: extraction-msg-to-markdown-python-contract

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0058 (Open-Q2), ADR-0045 (capability-tiered document extraction — names "the shared output contract `msg-to-markdown` adopts"), ADR-0034 (no bundled per-vendor data / models), RFC-0007 (the converters pack `msg-to-markdown` ships in), **ADR-TBD** (the `.msg`-reader dependency + license decision — authored in plan T1; this header is updated with the minted number in the same PR)
- **Contract:** none — the output is a Markdown file with YAML frontmatter, not an API under `contracts/`. The frontmatter *is* a consumer-facing contract; its shape is the unified contract pinned by `extraction-tier0-and-output-contract` (the `contract-version` field is how consumers detect it) and re-asserted by the Acceptance Criteria below.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers fired: new dependency (a Python .msg
reader replacing the npm one); security boundary (parses untrusted .msg — an OLE2
compound file — plus attachment extraction to disk and untrusted MIME); structural
+ public-interface change (swaps the skill's runtime Node→Python and changes its
output shape to the unified contract). Implements the deferred slice named in
`extraction-tier0-and-output-contract` (backlog § extraction-tier0-and-output-contract)
and folds in the deferred richer-MIME item (backlog: extraction-tier0-eml-mime). -->

## Objective

A user in a locked-down or Node-less environment converts an Outlook `.msg`
email — and a MIME `.eml` email — to Markdown for an AI context layer using only
Python, and every conversion carries the same versioned **unified output
contract** (`contract-version`, `tier`, `source-file`, `content-type`,
`ingestion-date`, and the nested `ingestion-quality` block) that `file-to-markdown`
emits. The `msg-to-markdown` skill runs on Python — a permissive-licensed,
pure-Python `.msg` reader replaces the `@nicecode/msg-reader` npm package and the
Node runtime — and it emits the contract through the **same** frontmatter builder
`file-to-markdown` uses (`contract.py`), vendored into this skill by copy with a
byte-identical drift guard (drift *detected*, not structurally prevented — see AC2)
rather than a JavaScript reimplementation that would fork the contract. The
converted Markdown preserves what the Node converter preserved — subject, sender,
`To`/`CC`/`BCC` recipients, date, importance, the body (HTML reduced to Markdown or
plain text), and an attachments table — verified by a **content-parity check**
against the Node converter's output over a corpus of `.msg` fixtures, so the port
does not silently regress `.msg` parsing (MAPI properties, encodings, attachments).
Because a `.msg` is an untrusted OLE2 compound file, the skill enforces its **own**
resource ceiling around the reader, confines every attachment and output write, and
bounds embedded-message recursion; it makes no network call and loads no ML/OCR
model — a Tier-0 (no-ML) converter.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep source changes inside `packs/converters/.apm/skills/msg-to-markdown/`,
  plus the pack version files (`pack.toml`, `.claude-plugin/plugin.json`), the
  regenerated top-level `.claude-plugin/marketplace.json`, `docs/product/changelog.md`,
  and a **new ADR** recording the `.msg`-reader dependency choice + license
  rationale (the pack has no `AGENTS.md`, so a new dependency is recorded in an ADR
  per `AGENTS.md` § Check before acting). **Do not edit `file-to-markdown/` source** —
  see the vendoring bullet below.
- Emit the **unified output contract** through `file-to-markdown`'s shared builder
  (`contract.py.build_frontmatter`) — the same `contract-version`, `tier`
  (`0-no-ml`), `source-file`, `content-type`, `ingestion-date`, and nested
  `ingestion-quality.{extraction-confidence, requires-review}` shape. The extracted
  body (headers block, converted body, attachments table) sits **below** the leading
  `---`-fenced frontmatter, exactly as `file-to-markdown`'s document branch assembles it.
- **Vendor the two shared modules by copy + guard against drift.** Copy `contract.py`
  and `safe_io.py` **verbatim** from `file-to-markdown/scripts/` into
  `msg-to-markdown/scripts/` (there is no cross-skill shared-lib mechanism — each
  skill's `scripts/` project independently), and add a **byte-identical drift-guard
  test** asserting the two copies match the `file-to-markdown` originals. This
  *detects* drift (a tripwire in the suite), it does **not** structurally prevent it
  the way the floor's single imported module does — a deliberate, documented weakening
  accepted because no shared-lib mechanism exists (AC2). The **HTML→Markdown reducer**
  is `file-to-markdown`'s stdlib `html.parser` *technique* re-implemented as this
  skill's own module — **not** a byte-identical vendored copy — because its reducer is
  an inline nested class in `file-to-markdown/convert.py`, and extracting it would edit
  the shipped floor skill (out of scope).
- **Enforce the skill's own resource ceiling around the `.msg` reader, regardless of
  the reader's internal limits.** A `.msg` is an OLE2/CFBF file, **not** a zip, so
  `safe_io.py`'s zip-bomb guards do **not** cover it, and `check_input_size` gates
  input bytes only. The skill enforces a **cumulative-decompressed-output cap**, a
  **per-stream / RTF-decompressed (LZFu) byte cap**, and an **OLE2 stream/storage-count
  cap**, applied before/around full materialization, so a small `.msg` that declares or
  decompresses to gigabytes is refused (AC10).
- Select the `.msg` reader **pip-on-demand** (an early import-probe `cmd_check()` +
  a `PIP_INSTALL` constant that **pins a minimum version** + a `--check` verb returning
  exit 0 present / 2 absent), never auto-installed — mirroring `file-to-markdown`'s and
  the sibling `markdown-to-*` skills' optional-library pattern.
- Treat the `.msg` and `.eml` input as **untrusted**: enforce the coarse input-size
  ceiling before parse; confine the output `.md` write (realpath + path-component
  containment, via `safe_io.confine`); confine **every extracted-attachment write** to
  the extraction directory by reducing the stored filename to a basename via **both**
  `PurePosixPath` and `PureWindowsPath` (reject any name bearing either separator, an
  empty/`.`/`..` result, an absolute path, or a Windows drive/UNC prefix) **then**
  `safe_io.confine`; cap **embedded-message recursion** by depth and count; make **no
  network call**.
- Preserve the Node converter's extracted fields — subject, sender name+email,
  `To`/`CC`/`BCC` recipients, date, importance, HTML-or-plain body, and an
  attachments table (filename, size, type, inline flag) with the embedded-message
  note — and prove it with a **content-parity** test corpus (see Testing Strategy),
  documenting any field the chosen reader cannot surface as an allowed difference (AC3).
- Handle both `.msg` and `.eml` through **one internal email-render path** so the
  header block, body reduction, and attachments table are identical across formats;
  reduce an HTML body to Markdown with the skill's stdlib `html.parser` reducer, not a
  bespoke regex pass.

### Ask first

- **The `.msg`-reader dependency and its license.** The default is a **permissive**
  (BSD/MIT/Apache — clears the pack's `Apache-2.0 OR MIT` license) pure-Python reader:
  `msg-parser` (BSD-2-Clause, `olefile`-based) is the recommended pick, with
  `olefile` (BSD-2-Clause) + hand-rolled MAPI-property parsing as the fallback if
  `msg-parser`'s coverage or maintenance proves inadequate at EXECUTE. **`extract-msg`
  is excluded on license (GPL, copyleft).** Any deviation — including a copyleft
  dependency justified as pip-on-demand-only — is an escalation resolved in the ADR.
- Bumping the converters pack's **minor** version vs. patch (this adds capability +
  swaps a runtime, so minor is expected — confirm the number).
- **Removing or changing** the skill's `WROTE:` / `SUMMARY:` / `EXTRACTED:` / `SKIPPED:`
  stdout markers or the attachments-extraction sub-command invocation shape —
  downstream callers/scripts may parse them.
- **Confirm the pinned reader's OLE2/RTF behavior at EXECUTE** (contract-grounding):
  the skill's own resource wrap (above) is mandatory regardless, but confirm the pinned
  `msg-parser`/`olefile` versions' stream-read and RTF-decompression behavior so the
  wrap is placed correctly. Relaxing the skill's own wrap in favor of the reader's
  internal limits is **not** an option — it is a hard control (AC10).

### Never do

- Add an ML or OCR **model** dependency, reach Tier 2+/Tier 3, or introduce **any
  network egress** — this is a Tier-0 (no-ML) converter.
- Reimplement or fork the frontmatter builder in JavaScript, or hand-write the YAML
  frontmatter — the contract is emitted only through the vendored shared `contract.py`.
- Introduce a **new top-level directory** or a cross-skill shared-lib/module boundary
  — the builder is shared by vendored copy + drift guard, not by new structure.
- Keep the Node runtime, `scripts/convert.js`, `scripts/extract-attachments.js`, or
  the `@nicecode/msg-reader` / `msgreader` dependency once the Python port lands.
- Write an extracted attachment (or any output) to a path the extraction directory
  does not contain — no `extractall`, no joining an attachment's own filename into a
  path without the basename-reduction + confinement above (the traversal sink the Node
  script carried).
- **Parse an attachment's or a MIME part's payload as XML.** The skill *lists*
  attachments; it does not open their content. If any XML read is ever introduced it
  goes through `safe_io.parse_xml` (XXE-safe, DTD-refusing), never `lxml` /
  `xml.dom.minidom` / `xml.sax` at defaults.
- Add an `evals/` directory under `msg-to-markdown/` — the pack's carry-over gate
  hard-errors if `msg-to-markdown/evals` exists (`pack.toml` § pack.evals).
- Edit projected `.claude/` paths by hand — edit `packs/converters/.apm/` source and
  regenerate.

## Testing Strategy

- **Unified contract shape — TDD + goal-based.** A unit test asserts the emitted
  frontmatter carries every required key (`contract-version`, `tier`, `source-file`,
  `content-type`, `ingestion-date`, `extraction-confidence`, `requires-review`)
  through the shared builder; one end-to-end run of the documented invocation
  (`python scripts/convert.py <file.msg>`) greps the emitted frontmatter,
  `tier: "0-no-ml"`, and `content-type: "msg"`. (AC1, AC8)
- **Shared-builder drift guard — goal-based.** A test asserts `msg-to-markdown/scripts/contract.py`
  and `safe_io.py` are **byte-identical** to the `file-to-markdown` originals, so a
  future edit to one copy fails until both are synced. (AC2)
- **Content-parity vs. the Node converter — goal-based, corpus + one real sample.**
  Over a **generated** `.msg`/`.eml` corpus, the Python port's extracted content
  (subject, sender name+email, `To`/`CC`/`BCC`, date, importance, body text,
  attachment filenames+sizes+types, embedded-`.msg` detection) matches the Node
  converter's captured baseline; fields the chosen reader cannot surface (e.g. BCC)
  are asserted as *documented allowed differences*. Because a generated corpus can only
  bound **reader-vs-reader** regression (both readers may share a real-world MAPI blind
  spot), AC3 also carries **one numbered real-world `.msg` + one real-world `.eml`
  manual-verification artifact** with a recorded result. This is **field-semantic**
  parity, not byte-parity, and explicitly **not** a security-behavior baseline (the Node
  script is the insecure predecessor — it carried the traversal sink). (AC3)
- **`.msg` field extraction — TDD.** Unit tests on sender / recipients-by-type /
  date-resolution (delivery vs. submit vs. creation) / importance / HTML-vs-plain body
  selection, against small fixtures. (AC3, AC4)
- **HTML-body reduction — TDD.** A unit test asserts an HTML body is reduced to
  Markdown by the stdlib `html.parser` reducer (headings, bold/italic, links, lists,
  tables, entity unescaping), not a bespoke regex. (AC4)
- **`.eml` / richer MIME — TDD + goal-based E2E.** Unit tests on the multipart walk
  (preferred `text/plain` vs `text/html`), a nested `message/rfc822` part, and richer
  header mapping; one end-to-end `python scripts/convert.py <file.eml>` run asserting
  the body + `content-type: "eml"` frontmatter; plus a **cross-path frontmatter-parity**
  test — the same simple `.eml` routed through this skill and through
  `file-to-markdown`'s flat `.eml` route yields **identical contract frontmatter** (body
  differences are the intentional superset). (AC5)
- **Attachment-extraction confinement — TDD (security).** Attachments named `../evil`,
  an absolute path, a Windows drive/UNC path, an **empty name**, and a name bearing
  **either** separator are each reduced to a basename inside the extraction directory or
  refused — never written outside it; a `..`-traversal and a symlinked-extraction-dir
  escape are both refused. (AC6, AC9)
- **OLE2 / RTF resource bound — TDD (security).** A small `.msg` that declares/expands
  to an oversized cumulative output, an oversized single stream, an oversized
  LZFu-decompressed RTF body, or an excessive OLE2 stream/storage count is refused by
  the **skill's own** wrap (not the reader's internal limits) with an actionable error +
  `requires-review`. A test asserts `check_input_size` alone does **not** admit such a
  file. (AC10)
- **Output-path confinement — TDD (security).** The written `.md` path is confined by
  path-component containment; a `..`-traversal, a symlink escape, and the
  **sibling-prefix** case (`<root>-evil` vs root `<root>`) are refused. (AC9)
- **Embedded-recursion bound — TDD (security).** An embedded `.msg` / nested
  `message/rfc822` chain deeper than the pinned depth or wider than the pinned count is
  truncated with a surfaced note; the cumulative resource budget (AC10) spans the whole
  recursion, so many shallow-but-large embedded parts cannot bypass it. (AC7)
- **Frontmatter-injection safety — TDD (security).** A `.msg`/`.eml` whose subject or
  body contains `---`, newlines, and a `contract-version:` line produces frontmatter
  where the shared builder's values win, the closing `---` fence is intact, and the
  hostile text appears only in the body. (AC8)
- **No-ML / no-egress — goal-based.** A test/grep confirms the skill imports no
  Docling/OCR/vision model and makes no network call; `--check` reports the `.msg`
  reader present/absent with exit 0/2. (AC11)
- **Release hygiene — goal-based.** `pack.toml` / `plugin.json` / `marketplace.json`
  are version-consistent; `lint-packs`, `validate`, `build`, and `pytest` are green;
  a `docs/product/changelog.md` `[Unreleased]` entry records the change; the new ADR
  records the dependency + license + pinned versions; SKILL.md documents the Python
  invocation, the contract, and `.eml` support; no `msg-to-markdown/evals/` dir exists;
  no Node artifacts remain; `Constrained by:` carries the minted ADR number. (AC11, AC12)

## Acceptance Criteria

- [ ] **AC1 — Python runtime, unified contract via the shared builder.** `msg-to-markdown`
  runs on Python (`python scripts/convert.py <file.msg>`); its output carries the
  unified YAML frontmatter — at minimum `contract-version` (string), `tier`
  (`"0-no-ml"`), `source-file`, `content-type` (`"msg"` for `.msg`, `"eml"` for `.eml`),
  `ingestion-date`, `ingestion-quality.extraction-confidence` (`high|medium|low`), and
  `ingestion-quality.requires-review` (bool) — produced by `file-to-markdown`'s shared
  `contract.py.build_frontmatter`, not a JavaScript reimplementation or a hand-written
  block. The extracted body sits below the leading `---` fence.

- [ ] **AC2 — Shared builder is vendored by copy, with drift *detected* (not prevented).**
  `contract.py` and `safe_io.py` are vendored into `msg-to-markdown/scripts/` **verbatim**
  from `file-to-markdown/scripts/`, and a **drift-guard test** asserts the copies are
  byte-identical to the originals — so a future edit to either copy fails the suite until
  both are synced. This is a **deliberate weakening** of the floor spec's *structural*
  single-builder guarantee (one imported module, drift impossible): here there are two
  copies and a tripwire that detects drift after the fact, accepted because no cross-skill
  shared-lib mechanism exists. The HTML→Markdown reducer is **not** in the vendored set —
  it is this skill's own stdlib `html.parser` module (re-implementing the floor's
  technique), so the port touches **no** `file-to-markdown/` source.

- [ ] **AC3 — Content parity with the Node converter (no silent regression), reader-vs-reader
  bounded.** Over a generated `.msg`/`.eml` corpus, the Python port extracts the same
  **content** the Node converter did — subject, sender name+email, `To`/`CC` recipients,
  date, importance, body text (HTML-reduced or plain), and the attachments list
  (filename, size, type, inline flag) with embedded-`.msg` detection — verified against a
  captured Node baseline. `BCC` (and any other field the chosen reader cannot surface) is
  named as an **allowed, documented** parity difference, and its gap triggers the
  `olefile`+MAPI fallback or a documented degradation, so the gate has a defined green
  path. Parity is **field-semantic**, not byte-for-byte, and bounds reader-vs-reader
  regression only; **AC3 also carries a numbered real-world `.msg` + `.eml`
  manual-verification artifact** (recorded result) as the absolute-fidelity signal, since
  a generated corpus cannot catch a MAPI/encoding quirk it never emits.

- [ ] **AC4 — `.msg` parsing at Tier 0, no ML.** A `.msg` file is parsed by a
  permissive-licensed, pure-Python reader with no ML/OCR model and no network call;
  sender, recipients-by-type, the resolved date, importance, and the HTML-or-plain body
  (HTML reduced to Markdown via the skill's stdlib `html.parser` reducer) are extracted,
  and the output carries `tier: "0-no-ml"`.

- [ ] **AC5 — `.eml` / richer MIME support (fold-in), consistent with the floor route.**
  `msg-to-markdown` also converts a `.eml` (MIME) file — walking multipart bodies
  (preferred `text/plain` vs `text/html`), handling a nested `message/rfc822` part, and
  mapping the richer headers — through the **same** internal email-render path and the
  same unified contract. `file-to-markdown`'s existing flat `.eml` floor route is
  **unchanged**; this skill is the richer email specialist. The relationship is defined,
  not just "two implementations": for a shared simple `.eml` fixture the **contract
  frontmatter is identical across both paths**, and this skill's body/header output is a
  documented **superset** of the flat route's.

- [ ] **AC6 — Attachment extraction is confined.** The attachments sub-command
  (invocation form pinned in SKILL.md / the Interfaces design) writes each attachment
  under a path **contained** by the extraction directory: the stored filename is reduced
  to a basename via **both** `PurePosixPath` and `PureWindowsPath` and refused if it is
  empty, `.`/`..`, `..`-bearing, absolute, or a Windows drive/UNC path; the result is then
  `safe_io.confine`-checked; nothing is ever written outside the extraction directory.
  (Closes the Node `extract-attachments.js` traversal sink.) Tests cover `../evil`, an
  absolute path, a drive/UNC path, an empty name, and a both-separator name.

- [ ] **AC7 — Embedded-message recursion is bounded, by pinned numbers.** An embedded
  `.msg` / nested `message/rfc822` chain is followed only to a **pinned depth** and a
  **pinned total count** (concrete numbers in the code + SKILL.md, e.g. depth ≤ 3, total
  embedded parts ≤ a small N); beyond it the output surfaces a note and stops. The
  cumulative resource budget of AC10 spans the **whole** recursion (it does not reset per
  level), so many shallow-but-large embedded parts cannot bypass the ceiling.

- [ ] **AC8 — Extracted content cannot forge the contract.** Because the frontmatter is
  emitted through the shared builder, a subject/body containing `---`, newlines, or a
  `contract-version:` line is escaped/quoted so the builder's values win, the closing
  `---` fence stays intact, and the hostile text appears only in the body. A test drives
  a hostile `.msg`/`.eml` and asserts a frontmatter parser reads only the builder's
  leading block.

- [ ] **AC9 — Untrusted-input defenses.** Output-path and attachment writes are confined
  (realpath + path-component containment — `..`, symlink, and sibling-prefix cases
  refused); an input over the coarse size ceiling is refused before parse with an
  actionable error + `requires-review`; a malformed/truncated OLE2 `.msg` fails fast
  without an uncaught crash; no network call is made. The skill does **not** parse any
  attachment/MIME-part payload as XML; were an XML read introduced it would use
  `safe_io.parse_xml` (XXE-safe), never `lxml`/`minidom`/`sax` at defaults.

- [ ] **AC10 — OLE2/CFBF + RTF resource guard is the skill's own (not the reader's).**
  Because a `.msg` is an OLE2 compound file (the vendored `safe_io.py` zip-bomb guards do
  not apply, and `check_input_size` gates input bytes only), the skill enforces its **own**
  bounds around the reader: a **cumulative decompressed-output cap**, a **per-stream /
  LZFu-decompressed-RTF byte cap**, and an **OLE2 stream/storage-count cap**, applied
  before/around full materialization. A small `.msg` declaring or decompressing to
  gigabytes is refused with `requires-review` regardless of the (possibly absent) internal
  limits of the pinned, unmaintained reader. The cumulative decompressed-output cap is a
  **single running total threaded through the recursive embedded-message walk** —
  decremented across every embedded `.msg` / `message/rfc822` read, never re-initialized
  per reader invocation — so it composes with AC7's recursion bound (N shallow-but-large
  embedded parts cannot each pass a per-call cap while the aggregate blows the budget). A
  test proves `check_input_size` alone does not admit such a file, and a test proves the
  accumulator refuses an aggregate that no single embedded read exceeds.

- [ ] **AC11 — Tier-0 / no-ML / pip-on-demand with a pinned floor.** The skill imports no
  ML/OCR/vision model (asserted by a grep/import test) and makes no network call; the
  `.msg` reader is resolved pip-on-demand via a `--check` verb (exit 0 present / 2 absent)
  whose `PIP_INSTALL` hint **pins a minimum version**, never auto-installed. Because the
  reader is pip-on-demand in the *user's* environment — outside the repo lockfile and its
  SCA scanning — the ADR records the pinned `msg-parser`/`olefile` versions, names the
  SCA-invisibility as an accepted risk with the AC10 resource-wrap as the load-bearing
  compensating control, and records the maintenance-abandonment exit (the `olefile`+
  hand-rolled-MAPI fallback).

- [ ] **AC12 — Release hygiene + Node removal + docs.** The Node runtime and its files
  (`convert.js`, `extract-attachments.js`, the npm dependency) are removed; no
  `msg-to-markdown/evals/` directory exists; the converters pack version is bumped
  consistently across `pack.toml`, `.claude-plugin/plugin.json`, and the regenerated
  `.claude-plugin/marketplace.json`; `docs/product/changelog.md` records the change; a new
  ADR records the `.msg`-reader dependency + license decision and the spec's
  `Constrained by:` carries its minted number (updated in the same PR); SKILL.md documents
  the Python invocation, the tiers/contract, `.eml` support, the confined attachment
  extraction, and the carried edge-case prose; `lint-packs`, `validate`, `build`, and
  `pytest` are green.

## Assumptions

- Technical: the target skill is `msg-to-markdown` in the `converters` pack (v0.4.0),
  today a Node.js skill — `scripts/convert.js` + `scripts/extract-attachments.js` on
  `@nicecode/msg-reader` (fallback `msgreader`) — emitting a `# subject` + `| Field | Value |`
  header table + body + attachments table + embedded-`.msg` note, with `WROTE:` /
  `SUMMARY:` stdout markers. (source: repo read of `packs/converters/.apm/skills/msg-to-markdown/`
  + `pack.toml`, 2026-07-01.)
- Technical: `file-to-markdown`'s shared builder (`contract.py.build_frontmatter`) and
  `safe_io.py` (confine, SafeZip, size ceiling) live **only** in `file-to-markdown/scripts/`
  and are imported as sibling modules; there is **no cross-skill shared-lib mechanism**,
  so sharing across skills is by vendored copy + a drift-guard test. The HTML reducer is an
  **inline nested class** in `file-to-markdown/convert.py` (not an importable module), so it
  is re-implemented in `msg-to-markdown`, not vendored. (source: repo read + `find`,
  2026-07-01.)
- Technical: `file-to-markdown` already ships a **flat** stdlib `.eml` reader at Tier 0
  (floor spec AC7); the richer MIME handling (multipart, nested messages, richer headers)
  was explicitly deferred to this slice. (source: repo read of `convert.py._extract_eml`
  + `docs/backlog.md § extraction-tier0-eml-mime`, 2026-07-01.)
- Technical (security): the Node `extract-attachments.js` writes each attachment via
  `path.join(outDir, att.fileName)` using the attachment's attacker-controlled filename
  — a path-traversal sink the port must confine. A `.msg` is an OLE2/CFBF file, so the
  vendored zip-bomb guards do not cover it; MAPI `PidTagRtfCompressed` uses LZFu
  decompression whose output can dwarf the input — hence the skill's own OLE2/RTF resource
  wrap. (source: repo read of `scripts/extract-attachments.js:31` + `safe_io.py`, 2026-07-01.)
- Technical: `msg-to-markdown` is deliberately excluded from `pack.evals`; a build-check
  gate hard-errors if `msg-to-markdown/evals/` exists — the port adds no evals dir.
  (source: `packs/converters/pack.toml` § pack.evals, 2026-07-01.)
- Technical (license + maintenance): `extract-msg` is **GPL** (copyleft); `msg-parser` is
  **BSD-2-Clause** (`olefile`-based, pure-Python, no Windows deps, but last released
  1.2.0 in Dec 2019 — a maintenance risk for an untrusted-input parser); `olefile` is
  **BSD-2-Clause** and actively maintained. The pack license is `Apache-2.0 OR MIT`, and
  its dependency bar rejected copyleft (AGPL) before — so the default reader is permissive
  and `extract-msg` is excluded on license; the staleness is handled by the AC10 resource
  wrap + the `olefile`-fallback exit recorded in the ADR. (source: web search —
  pypi.org/project/{extract-msg,msg-parser,olefile}, github.com/vikramarsid/msg_parser,
  2026-07-01.)
- Process: governed by RFC-0058 (Open-Q2) and ADR-0045 (which names "the shared output
  contract `msg-to-markdown` adopts"); this is the deferred slice named in
  `extraction-tier0-and-output-contract`. A new dependency is recorded in a new ADR
  (authored in plan T1; the `converters` pack has no `AGENTS.md`), whose number backfills
  the spec `Constrained by:` in the same PR. Full mode. (source: `docs/rfc/0058-*.md`,
  `docs/adr/0045-*.md`, `AGENTS.md § Check before acting`, 2026-07-01.)
- Process: Node v26 is present in the dev environment, so the parity baseline can be
  captured by running the current `convert.js` at development time even though the shipped
  skill drops Node; no `.msg` fixtures exist in the repo, so the parity corpus is generated
  (synthetic `.msg`/`.eml`), backstopped by the AC3 real-world manual sample. (source:
  `node --version` probe + `find … -iname '*.msg'` (empty), 2026-07-01.)
- Product: the consumer is the same AI **context layer** as `file-to-markdown`; the driver
  is email→Markdown ingestion in locked-down / Node-less environments. (source: user
  confirmation 2026-07-01.)
