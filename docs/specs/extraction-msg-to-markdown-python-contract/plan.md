# Plan: extraction-msg-to-markdown-python-contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Rewrite `msg-to-markdown` as a Python skill that mirrors `file-to-markdown`'s
`convert.py` shape: an `ExtractResult`-style extraction feeding the **shared**
`contract.build_frontmatter` builder and a confined write. The change is a
runtime swap (Node → Python) plus an output-shape change (adopt the unified
contract), landed in dependency order:

1. **Record the dependency decision** in an ADR first — the `.msg` reader is a
   new dependency and the license bar (permissive; `extract-msg`/GPL excluded)
   plus the stale-parser maintenance risk are the load-bearing constraints, so
   they are settled before code. The ADR number backfills the spec header.
2. **Vendor the two shared modules** (`contract.py`, `safe_io.py`) byte-for-byte
   with a drift-guard test — this is what makes "one builder, drift detected"
   true across two skills absent a shared-lib mechanism. The HTML reducer is
   re-implemented in this skill (the floor's reducer is an inline class; extracting
   it would edit the shipped floor skill — out of scope), so nothing under
   `file-to-markdown/` is touched.
3. **Capture the Node parity baseline** while Node is still present (dev env has
   v26), over a generated `.msg`/`.eml` corpus + one real-world sample — the safety
   net that catches a silent `.msg`-parsing regression (reader-vs-reader) and, via
   the real sample, an absolute-fidelity miss the generator can't emit.
4. **Build the Python converter** (`.msg` first, then the `.eml`/MIME fold-in
   through the same render path), with the skill's **own OLE2/RTF resource wrap**
   around the reader, then the **confined** attachment extractor.
5. **Remove Node**, wire release hygiene, rewrite SKILL.md, backfill the ADR number.

The riskiest parts: (a) the `.msg` reader's field coverage and encoding fidelity
versus the Node reader (the parity gate + real sample prove it; BCC is a known
allowed-difference); (b) the untrusted-OLE2 resource surface — a `.msg` is not a
zip, so the vendored zip guards don't apply and the skill must bound OLE2 streams
and LZFu-RTF decompression itself; (c) the two security sinks the port must not
carry forward or reintroduce (attachment-filename traversal, unbounded
embedded-message recursion).

## Constraints

- **RFC-0058 (Open-Q2)** — recommended `msg-to-markdown` adopt the unified
  contract; this slice is the Python-port realization.
- **ADR-0045** — capability-tiered document extraction; explicitly names "the
  shared output contract `msg-to-markdown` adopts". This port is a Tier-0 (no-ML)
  converter under that doctrine.
- **ADR-0034** — no bundled per-vendor data / models; the `.msg` reader is a
  no-ML parser and stays pip-on-demand, not bundled.
- **RFC-0007** — the converters pack `msg-to-markdown` ships in (user-scope,
  no seeds/hooks).
- **`extraction-tier0-and-output-contract`** — the sibling spec that shipped the
  `contract.py` builder + `safe_io.py` this slice vendors; its AC1 single-builder
  property is *deliberately weakened* here (copy + detection, not one imported
  module), documented in spec AC2.
- **ADR-TBD** (authored in T1) records the `.msg`-reader dependency + license +
  pinned-version decision (the pack has no `AGENTS.md`); its number backfills the
  spec `Constrained by:` in the same PR.

## Construction tests

**Integration tests:** the content-parity harness (T7) spans the reader and the
render path — it runs the built Python converter over the whole corpus and diffs
extracted fields against the Node baseline, with BCC (and any other reader-gap
field) asserted as a documented allowed difference.
**Manual verification:** AC3's numbered real-world artifact — convert one real
`.msg` and one real `.eml` by hand and record the eyeballed result (the corpus is
synthetic; a real sample catches encoding/MAPI surprises the generator misses).

## Design (LLD)

Shape: **service**. Sub-sections: interfaces & contracts, data & schema, failure
& resilience, quality attributes. Stack: Python 3 stdlib + a permissive
pure-Python `.msg` reader, matching `file-to-markdown/scripts/convert.py`'s
conventions (module-level `import contract` / `import safe_io`, `ExtractResult`
NamedTuple, `assemble` → `write_output`).

### Design decisions
- **Vendor-copy the two shared modules + drift-guard test** (spec AC2) over merging
  `.msg` into `file-to-markdown` or building a shared-lib projection mechanism.
  Rejected: merging collapses a distinct skill (its attachment extraction +
  interactive email reporting) and trips the `msg-to-markdown`-excluded evals gate
  wiring; a shared-lib mechanism is new top-level structure (RFC-territory). Copy +
  guard is minimal and honors "port as its own slice" — but it is drift *detection*,
  a documented weakening of the floor's structural guarantee. The HTML reducer is
  **re-implemented** (not vendored) because the floor's is an inline class; vendoring
  it would force an out-of-scope edit to `file-to-markdown/convert.py`. Traces to:
  AC2 · (no `contracts/`).
- **Permissive `.msg` reader, `extract-msg` excluded on license** (spec AC4, AC11,
  and the "Ask first" dependency gate). Default `msg-parser` (BSD), fallback
  `olefile` (BSD) + hand-rolled MAPI. Recorded in the ADR with pinned versions.
  Traces to: AC4, AC11.
- **Skill-owned OLE2/RTF resource wrap** (spec AC10) rather than trusting the stale
  reader's internal limits — a `.msg` is CFBF, not a zip, so `safe_io`'s zip guards
  don't apply and `check_input_size` gates input bytes only. Traces to: AC10.
- **One internal email-render path for `.msg` and `.eml`** (spec AC5) so headers,
  body reduction, and attachments render identically; `.eml` uses stdlib `email`
  (multipart walk + `message/rfc822`); the contract frontmatter is identical to the
  floor's flat `.eml` route for a shared fixture. Traces to: AC4, AC5.

### Data & schema
- **Output frontmatter** = the unified contract (spec AC1): `contract-version`,
  `tier: "0-no-ml"`, `source-file`, `content-type` (`"msg"` | `"eml"`),
  `ingestion-date`, `ingestion-quality.{extraction-confidence, requires-review}`.
  Emitted only by the vendored `contract.build_frontmatter`.
- **Internal email model** — a small dataclass: `subject`, `sender(name,email)`,
  `recipients[](kind∈{to,cc,bcc}, name, email)`, `date`, `importance`,
  `body(kind∈{html,plain,none}, text)`, `attachments[](filename, size, ctype,
  inline, is_embedded_msg)`. Both readers populate it; the renderer consumes it.
  `bcc` may be empty when the reader can't surface it (AC3 allowed difference).
  Traces to: AC3, AC4, AC5.

### Interfaces & contracts
- CLI: `python scripts/convert.py <file.msg|file.eml> [...]`; `--check` (exit 0/2,
  `PIP_INSTALL` pins a minimum reader version); attachments extraction sub-command —
  **pinned invocation form** (a `--attachments <file>` verb on `convert.py`, or the
  preserved second script; whichever is chosen is documented in SKILL.md and is the
  shape the `EXTRACTED:`/`SKIPPED:` markers hang off, per spec "Ask first"). No
  `contracts/` file — the output contract is the frontmatter. Traces to: AC1, AC6,
  AC11, AC12.

### Failure, edge cases & resilience
- Size ceiling before parse; **skill-owned OLE2/RTF resource wrap** (cumulative
  decompressed cap + per-stream/LZFu-RTF cap + OLE2 stream/storage-count cap);
  malformed OLE2 → fail fast, no crash; embedded-message chain → pinned depth+count
  cap with a surfaced note and the cumulative budget spanning the whole recursion (a
  single running accumulator threaded through the walk, decremented per embedded read,
  never re-initialized per reader invocation — so AC7 and AC10 compose);
  sparse/empty body → `requires-review`. Attachment/output writes → basename-reduce
  (both path flavors) then `safe_io.confine`. Traces to: AC6, AC7, AC9, AC10.
- Edge cases carried from the Node SKILL.md prose (RTF-only body, TNEF/winmail,
  `cid:` inline images, quoted reply chains, `.ics` invites, encodings, distribution
  lists, sensitivity labels, receipts) stay documented in SKILL.md; the ones with a
  code path (RTF-only detection → note; inline flag; encoding fallback) get a test.

### Quality attributes (NFRs)
- **Security posture** (untrusted input): confinement, input ceiling, skill-owned
  OLE2/RTF bound, bounded recursion, no-XML-payload-parse boundary, injection-safe
  frontmatter (inherited from the vendored builder). No egress. Traces to: AC6, AC7,
  AC8, AC9, AC10.
- **No-ML / Tier-0**: no model import, asserted by test. Traces to: AC4, AC11.
- **Supply-chain**: pinned reader versions, pip-on-demand outside repo SCA, resource
  wrap as the compensating control, fallback exit — recorded in the ADR. Traces to:
  AC11.

### Dependencies & integration
- New: one permissive `.msg` reader (`msg-parser` default, pinned). Reused: stdlib
  `email`, `html.parser`; vendored `contract.py`/`safe_io.py`; a re-implemented HTML
  reducer. Removed: Node + npm reader. Traces to: AC4, AC5, AC11, AC12.

## Tasks

### T1: ADR records the `.msg`-reader dependency + license + version decision

**Depends on:** none

**Tests:**
- Goal-based: a new `docs/adr/NNNN-*.md` exists, Status Accepted, naming the chosen
  reader, its **pinned version**, its license (permissive), why `extract-msg` (GPL)
  is excluded, the pip-on-demand-outside-SCA accepted risk, the AC10 resource wrap as
  compensating control, and the `olefile`+MAPI abandonment exit. (spec AC11, AC12)

**Approach:**
- Author the ADR via the `new-adr` skill: decision = permissive pure-Python `.msg`
  reader (default `msg-parser` BSD / fallback `olefile`+MAPI), copyleft excluded,
  pip-on-demand via `--check` with a pinned minimum. Cite RFC-0058, ADR-0045, ADR-0034.
- Note the minted ADR number for the T8 spec-header backfill.

**Done when:** the ADR is Accepted and its number is recorded for backfill.

### T2: Vendor the two shared modules with a byte-identical drift guard

**Depends on:** none

**Tests:**
- Goal-based: a drift-guard test asserts `msg-to-markdown/scripts/contract.py` and
  `safe_io.py` are byte-identical to the `file-to-markdown` originals (read both,
  `assertEqual` on bytes). (spec AC2)

**Approach:**
- Copy `contract.py` and `safe_io.py` **verbatim** into `msg-to-markdown/scripts/`.
- Add the drift-guard test resolving both paths relative to the pack root.
- **Do not** touch `file-to-markdown/`; the HTML reducer is re-implemented in T4.

**Touches:** packs/converters/.apm/skills/msg-to-markdown/scripts/contract.py, packs/converters/.apm/skills/msg-to-markdown/scripts/safe_io.py, packs/converters/.apm/skills/msg-to-markdown/scripts/test_*.py

**Done when:** the drift-guard test passes and editing either copy fails it.

### T3: Capture the Node parity baseline over a generated corpus + one real sample

**Depends on:** none

**Tests:**
- Goal-based: a baseline artifact (extracted-fields JSON per fixture) is produced by
  running the current `convert.js` over the generated corpus; one real-world `.msg`
  and one real-world `.eml` are recorded as the AC3 absolute-fidelity artifact. (spec AC3)

**Approach:**
- Generate a small synthetic `.msg`/`.eml` corpus covering: plain body, HTML body,
  to/cc/bcc mix, an attachment, an inline `cid:` image, an embedded `.msg`,
  non-ASCII encoding, importance set.
- Run the existing Node `convert.js` (dev env Node v26) and record extracted fields
  (parse the `SUMMARY:` JSON + header/attachments table) as the baseline.
- Record the numbered real-world sample result (source noted; no PII committed).

**Done when:** a committed baseline covers every corpus fixture and the real-world
artifact is recorded.

### T4: Python `.msg` converter → unified contract, with the OLE2/RTF resource wrap

**Depends on:** T2

**Tests:**
- TDD: unit tests on sender / recipients-by-type / date-resolution / importance /
  body-selection extraction and the re-implemented HTML reducer. (spec AC3, AC4)
- TDD (security): the skill-owned OLE2/RTF wrap refuses a `.msg` that expands to an
  oversized cumulative output, an oversized stream, an oversized LZFu-RTF body, or an
  excessive OLE2 stream/storage count — and a test proves `check_input_size` alone
  does not admit it. (spec AC10)
- TDD (security): injection-safety on a hostile subject/body; malformed-OLE2
  fast-fail; no-model-import grep; `--check` 0/2 with a pinned-version hint. (spec
  AC8, AC9, AC11)
- Goal-based E2E: `python scripts/convert.py <fixture.msg>` emits `tier: "0-no-ml"`,
  `content-type: "msg"` frontmatter + the header/body/attachments Markdown. (spec AC1, AC4)

**Approach:**
- Build `convert.py` mirroring `file-to-markdown`'s shape: reader import-probe
  (`cmd_check` + version-pinned `PIP_INSTALL`), populate the internal email model,
  render header block + body (HTML→Markdown via the re-implemented stdlib reducer) +
  attachments table, `assemble` via `contract.build_frontmatter`, `write_output` via
  `safe_io.confine`.
- Wrap the reader call with the OLE2-stream / RTF-decompression / cumulative-output
  bounds (AC10); preserve the `WROTE:`/`SUMMARY:` markers.

**Touches:** packs/converters/.apm/skills/msg-to-markdown/scripts/convert.py, packs/converters/.apm/skills/msg-to-markdown/scripts/test_convert.py

**Done when:** all T4 tests are green and a `.msg` fixture round-trips to contracted Markdown.

### T5: `.eml` / richer MIME through the same render path

**Depends on:** T4

**Tests:**
- TDD: multipart body-preference (`text/plain` vs `text/html`), a nested
  `message/rfc822` part, richer header mapping. (spec AC5)
- TDD (security): embedded-message recursion pinned depth+count cap surfaces a note;
  the AC10 cumulative budget is a single accumulator threaded through the walk — a test
  proves an aggregate that no single embedded read exceeds is still refused. (spec AC7, AC10)
- Goal-based E2E: `python scripts/convert.py <fixture.eml>` emits `content-type: "eml"`
  + unified frontmatter. (spec AC5)
- Goal-based: **cross-path frontmatter parity** — the same simple `.eml` through this
  skill and through `file-to-markdown`'s flat route yields identical contract
  frontmatter; body/header differences are the documented superset. (spec AC5)

**Approach:**
- Add a stdlib-`email` reader that populates the same internal email model; route
  `.eml` through the shared renderer. Enforce the recursion cap + cumulative budget in
  the shared walk.
- Leave `file-to-markdown`'s flat `.eml` route untouched; document the two-altitude
  split (and the frontmatter-parity relationship) in both SKILL.md files.

**Touches:** packs/converters/.apm/skills/msg-to-markdown/scripts/convert.py, packs/converters/.apm/skills/msg-to-markdown/scripts/test_convert.py

**Done when:** `.eml` E2E + MIME unit tests + the cross-path parity test are green; the
flat floor route is unchanged.

### T6: Confined attachment extraction

**Depends on:** T4

**Tests:**
- TDD (security): attachments named `../evil`, an absolute path, a Windows drive/UNC
  path, an **empty name**, and a **both-separator** name each write inside the
  extraction dir (basename via `PurePosixPath` + `PureWindowsPath`) or are refused; a
  `..`-traversal and a symlinked-dir escape are refused. (spec AC6, AC9)
- Goal-based: the attachments sub-command (pinned invocation form) extracts a normal
  attachment and prints `EXTRACTED:`/`SKIPPED:`. (spec AC6)

**Approach:**
- Port `extract-attachments.js` to Python, reducing each stored filename to a basename
  via both path flavors, rejecting empty/`.`/`..`/absolute/drive/UNC, then
  `safe_io.confine(extraction_dir / name, extraction_dir)`; never join the raw name.

**Touches:** packs/converters/.apm/skills/msg-to-markdown/scripts/, packs/converters/.apm/skills/msg-to-markdown/scripts/test_*.py

**Done when:** the traversal tests are green and no write escapes the extraction dir.

### T7: Content-parity gate against the Node baseline

**Depends on:** T3, T4, T5, T6

**Tests:**
- Goal-based (integration): for every corpus fixture, the Python port's extracted
  fields equal the T3 Node baseline (subject, sender, to/cc, date, importance, body
  text, attachment filenames+sizes+types, embedded-`.msg` detection); **BCC and any
  other reader-gap field are asserted as documented allowed differences** (a BCC gap
  triggers the fallback or the documented degradation, so the gate is green by a
  defined path). (spec AC3)

**Approach:**
- Run the Python converter over the corpus, extract the same fields, diff against the
  baseline; encode allowed differences (BCC, date formatting) as explicit expectations
  with comments.

**Done when:** the parity gate is green across the corpus with allowed differences documented.

### T8: Remove Node, release hygiene, SKILL.md rewrite, ADR backfill

**Depends on:** T1, T4, T5, T6, T7

**Tests:**
- Goal-based: no `convert.js` / `extract-attachments.js` / npm-reader references
  remain; no `msg-to-markdown/evals/` dir; `pack.toml`/`plugin.json`/`marketplace.json`
  version-consistent; `docs/product/changelog.md` `[Unreleased]` entry present; the
  spec's `Constrained by:` carries the minted ADR number; `lint-packs`, `validate`,
  `build`, `pytest` green; SKILL.md documents the Python invocation, contract, `.eml`,
  the pinned attachment sub-command form, and confined extraction. (spec AC12)

**Approach:**
- Delete the Node scripts + npm prerequisite prose; rewrite SKILL.md; bump the pack
  minor version across the three files, regenerate `marketplace.json`
  (`make build-self`), add the changelog entry, backfill the ADR number into the spec.

**Touches:** packs/converters/.apm/skills/msg-to-markdown/*, packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md, docs/specs/extraction-msg-to-markdown-python-contract/spec.md

**Done when:** all gates green, no Node artifacts, docs + spec header current.

## Rollout

- **Delivery:** big-bang within the skill — the converters pack ships a new minor
  version; the skill's runtime changes Node→Python and its output gains frontmatter.
  Reversible by reverting the PR (no data migration, no published event).
- **Infrastructure:** none — no new infra, no network.
- **External-system integration:** the `.msg` reader is pip-on-demand in the *user's*
  environment (outside the repo lockfile/SCA, like `file-to-markdown`'s optional libs;
  the AC10 resource wrap is the compensating control for the invisibility); the user
  installs it via the version-pinned `--check` hint. Node is no longer required.
- **Deployment sequencing:** ADR (T1) before code; vendored modules + drift guard (T2)
  before the converter (T4) imports them; Node baseline (T3) captured before Node is
  removed (T8).

## Risks

- **`.msg` reader field/encoding coverage** falls short of the Node reader (e.g.
  RTF-only bodies, TNEF, exotic encodings, BCC). Mitigation: the T7 parity gate +
  AC3 real-world sample catch regressions; BCC is a pre-declared allowed difference;
  the `olefile`+hand-rolled-MAPI fallback is available if `msg-parser` is inadequate;
  RTF-only/TNEF degrade to a surfaced note as they do today.
- **`msg-parser` is stale (2019)** — a maintenance/security risk for an untrusted-input
  parser, invisible to the repo's SCA (pip-on-demand). Mitigation: the **skill-owned**
  OLE2/RTF resource wrap (AC10) is the load-bearing control (not the reader's internal
  limits); the ADR records the pinned version, the SCA-invisibility accepted risk, and
  the `olefile`-fallback exit.
- **Drift-guard brittleness** — the byte-identical test fails on any legitimate
  `file-to-markdown` edit until the copy is synced. This is intended (it *is* the
  drift-detection guarantee) but must be documented so a future editor knows to sync
  both; the spec is explicit that this is detection, not prevention.
- **Two `.eml` paths** (this skill's richer route + `file-to-markdown`'s flat floor)
  could confuse. Mitigation: the cross-path frontmatter-parity test pins their
  relationship; the two-altitude split is documented in both SKILL.md files.

## Changelog

- 2026-07-01: initial plan. Decisions locked with the owner: vendor-copy + drift guard
  (not merge / not shared-lib); permissive reader with `extract-msg`/GPL excluded;
  semantic content-parity (not byte-parity) over a generated corpus with a Node-v26
  baseline; `.eml`/MIME folded into this skill while `file-to-markdown`'s flat `.eml`
  floor route stays.
- 2026-07-01: revised per spec-stage adversarial + security review. (a) HTML reducer
  is **re-implemented** in this skill rather than vendored — the floor's reducer is an
  inline class, and vendoring it would edit the shipped floor skill (out of scope);
  vendored byte-identical set is now `contract.py` + `safe_io.py` only. (b) Added T4's
  **skill-owned OLE2/CFBF + LZFu-RTF resource wrap** (new spec AC10) — a `.msg` is not
  a zip, so the vendored zip-bomb guards don't apply and `check_input_size` is
  insufficient. (c) AC2 reworded to claim drift *detection*, not the floor's structural
  prevention. (d) BCC named as a pre-declared allowed parity difference with a defined
  fallback (T7). (e) Elevated the real-world `.msg`/`.eml` manual check to a numbered
  AC3 artifact (T3). (f) Added the cross-path `.eml` frontmatter-parity test (T5). (g)
  Attachment confinement pinned to basename-via-both-path-flavors + empty/`.`/`..`
  rejection (T6). (h) ADR number is TBD until T1, backfilled into the spec header in T8.
