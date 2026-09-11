# Spec: Catalogue install writes a layout section the skills read

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0040](../../rfc/0040-consolidated-pack-layout-config.md) — sets the
    append-if-exists / never-create / never-overwrite contract and the
    repo-relative anchoring rule; its erratum records the key rename and
    `architect`'s base
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/pack.schema.json` (modified — adds one optional key)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Installing a pack into a repository that keeps an `agentbundle-layout.toml`
adds the pack's default output location, and the pack's own skills find it.

The install-time append writes nothing for any pack in the catalogue. It reads a
manifest key no pack declares, and writes a section name no reader looks for.
Both halves close here, and the code that runs once the append is reachable
rebuilds the adopter's file from a single key and destroys the rest — so
preservation lands in the same change.

A pack declares which section owns its output:

```toml
[pack.layout.repo]
section    = "design"
output_dir = "docs/design"
```

At install, that becomes a section in the adopter's file:

```toml
[design]
output_dir = "docs/design"
```

The section is declared rather than derived from the pack name, because the
section name and the pack name are not the same thing and no function maps one
to the other — `experience-design` writes `[design]`, `desk-research` writes
`[research]`. Each pack's skills already document and read the section this
declares, so the install and the skill agree on the first try.

## Boundaries

### Always do

- Keep the append conditional: never create a file, never replace a section an
  adopter wrote.
- Leave the adopter's existing bytes untouched.
- Keep the per-scope write jail and the injection-safe string emission.
- Keep the two `pack.schema.json` copies byte-identical, moved together.

### Ask first

- Any change to a pack's default `output_dir` beyond `architect`'s. A default
  is an adopter-visible path.
- Any change to which section a pack declares. Each value matches what that
  pack's skills already read; changing one silently breaks them.

### Never do

- **No new top-level directory, module, or dependency.**
- Never rename a section in a skill body, reference doc, guide, or convention
  page. Moving the vocabulary onto pack names is separate, logged work.
- Never create a layout file that did not already exist, on any scope.

## Acceptance Criteria

- [ ] **AC1 — A declaring pack's default reaches an existing adopter file.**
  Installing a pack whose manifest declares both `section` and `output_dir` for
  the install scope, into a scope holding an `agentbundle-layout.toml`, appends
  a table named by `section` carrying `output_dir` set to the declared value.
  A pack missing either key for that scope appends nothing.

- [ ] **AC2 — Every other byte is unchanged.** Comments, blank lines, key
  order, quoting style, line endings, and every existing table and top-level
  value survive. After the append of AC1 the file equals the original bytes
  plus exactly the separator of AC3 and the appended table — stated as the
  complete result, so a no-op cannot satisfy it. The comparison is on bytes: a
  parsed comparison sees neither a lost comment nor a folded CRLF.

- [ ] **AC3 — The separator is the only added byte.** A file already ending in
  a newline gains none. A file ending without one gains exactly one, in the
  line-ending style the file already uses, or `\n` when it carries none.

- [ ] **AC4 — Three states refuse and report.** A file that cannot be decoded
  as UTF-8, a file that cannot be parsed, and a top-level name already taken by
  the declared section — whatever its type — each leave the file byte-identical
  and write the reason to stderr.

- [ ] **AC5 — An absent file stays absent, silently.** Installing into a scope
  with no `agentbundle-layout.toml` creates nothing and emits no diagnostic.
  This is the designed no-op on the majority of installs, not a refusal.

- [ ] **AC6 — Each pack declares the section its own skills read.** For every
  pack declaring `[pack.layout.<scope>]`, the declared `section` equals the
  section name that pack's shipped skill bodies and `references/agentbundle-layout.md`
  instruct a reader to look in. Both sides are derived from the repository.

- [ ] **AC7 — A repo-scope relative value resolves against the repository
  root.** `workspace_mcp.py` anchors a relative `output_dir` from the repo-scope
  file to the repository root, not to the process working directory. The test
  runs from a working directory other than the repository root, so an
  implementation that resolves against the process CWD fails.

- [ ] **AC8 — `architect` declares `docs/architecture`, and says so.** Its
  manifest names that base, and both of its `references/agentbundle-layout.md`
  files document the same value rather than `docs/design`.

- [ ] **AC9 — No shipped document claims the append drops content.** No
  `references/agentbundle-layout.md` states that the installer re-emits the file
  without preserving comments or off-schema keys. The file set is derived from
  the repository.

- [ ] **AC10 — The manifest schema admits `section` and still refuses an
  unknown key.** `pack.schema.json` accepts `section` inside
  `[pack.layout.repo]` and `[pack.layout.user]`, refuses a key it does not name,
  and its two copies are byte-equal.

- [ ] **AC11 — The emitted table is injection-safe.** A declared `section` or
  `output_dir` containing `"`, `]`, a newline, or `../` round-trips through
  `tomllib` as one string in one table, landing no additional TOML structure.

## Testing Strategy

- **The write behaviour (AC1, AC2, AC3, AC4, AC5):** TDD. Each fails on a
  different input — a wrong key, a wrong section name, a lost comment, a folded
  line ending, a file created that should not be, a diagnostic on a designed
  no-op.

- **The round trip (AC6):** goal-based check. Writer and readers disagreed on
  both the key and the section name for two releases with tests green on each
  side, because each was exercised against its own idea of the shape. The
  observation is that the manifest's declared section and the section the
  shipped skill reads are the same string, derived from both.

- **Path anchoring (AC7):** TDD. The failing input is a test run from a
  directory other than the repository root, which is what makes a CWD-anchored
  implementation red.

- **The documents (AC8, AC9):** goal-based checks over the repository-derived
  file set. They fail on different inputs — a wrong value in two files, a stale
  behavioural claim in six — so they need separate repairs.

- **The schema (AC10):** goal-based check. A manifest carrying `section`
  validates, one carrying an unknown sibling does not, and the copies compare
  equal; the shipped parity gate owns the last half.

- **Injection safety (AC11):** TDD, mutation-checked by removing the emitter
  call to confirm the control can still fail.

## Assumptions

- Technical: the installer reads `[pack.layout.<scope>].parent` and returns
  before writing when it is absent, while all five declaring packs write
  `output_dir` — so the append is inert for the whole catalogue (source:
  `packages/agentbundle/agentbundle/commands/install.py:3254-3261`;
  `packs/*/pack.toml`, read 2026-09-10)
- Technical: the installer writes a `[<pack_name>]` table, and no pack's skills
  read a section named for their pack — `experience-design`'s skills read
  `[design]`, `desk-research`'s read `[research]`, `architect`'s read
  `[architecture]`, `product-strategy`'s read `[strategy]`,
  `product-engineering`'s read `[product]` (source:
  `packs/*/.apm/skills/*/references/agentbundle-layout.md`, read 2026-09-10)
- Technical: skills resolve the layout file themselves by prose instruction and
  never call `workspace_mcp` — so the resolver's behaviour does not affect
  whether an installed default is found by the pack that wrote it (source:
  `packs/experience-design/.apm/skills/experience-status/SKILL.md:45-53`; grep
  for `workspace_mcp` across shipped `SKILL.md` returns none, 2026-09-11)
- Technical: the re-emit rebuilds the file from `(name, parent)` pairs, dropping
  every other key, every comment, and any section whose `parent` is not a
  string — and every real adopter file carries `output_dir` (source:
  `install.py:3286-3316`, read 2026-09-10)
- Technical: an occupied top-level name does not produce invalid TOML today —
  the occupant is silently dropped and the output parses. Executing the real
  function against `research = 1` and against `[[research]]` returned
  `["research"]\nparent = ".context/research"\n` in both cases (source: probe
  against `_append_layout_section`, 2026-09-11; output recorded in
  `notes/verification-ledger.md` at execution)
- Technical: a file that cannot be decoded as UTF-8 is caught today by the
  malformed branch because `read_text` sits inside the `try`, so a
  byte-preserving read must keep the decode inside that boundary (source: probe
  with a latin-1 comment, 2026-09-11; recorded in the ledger at execution)
- Technical: `read_text` folds CRLF and lone CR to LF, and
  `safety.write_jailed` accepts `bytes` directly, so a byte-preserving path
  needs no signature change (source: `install.py:3267`;
  `packages/agentbundle/agentbundle/safety.py:386`; CR-only probe, 2026-09-11)
- Technical: the absent-file branch returns silently by design, and installing
  into a repository with no layout file is the common case (source:
  `install.py:3250-3252`, read 2026-09-11)
- Technical: `workspace_mcp.py` resolves a configured value with
  `str(Path(raw).expanduser().resolve())`, anchoring a relative value to the
  process working directory rather than the repository root. The path is
  reachable today only through hand-authored config; writing a repo-relative
  default makes it the common case (source:
  `packages/agentbundle/agentbundle/workspace_mcp.py:1595`, read 2026-09-10)
- Technical: `contracts/pack.schema.json` sets `additionalProperties: false` on
  both layout scope sub-tables and refuses `section` today, so admitting it is
  a schema change; the two copies are byte-parity gated (source: schema read
  and `jsonschema` validation probe, 2026-09-10)
- Technical: two shipped assertions pin the data loss as correct (source:
  `packages/agentbundle/tests/unit/test_append_layout_section.py`,
  `test_reemit_drops_tampered_existing_parent`, read 2026-09-10)
- Technical: six `references/agentbundle-layout.md` files state the installer
  "does not preserve freeform comments or off-schema keys", which this change
  makes false (source: repository grep, 2026-09-11)
- Technical: both `architect` reference docs document `output_dir = "docs/design"`
  (source: `packs/architect/.apm/skills/architect-design/references/agentbundle-layout.md`,
  read 2026-09-11)
- Technical: the defect is unreached by this catalogue but not unreachable —
  the schema admits `parent` and `agentbundle install` accepts an external
  catalogue, so a third-party pack declaring it reaches the re-emit today
  (source: `contracts/pack.schema.json`; `install.py:516`, read 2026-09-10)
- Product: the installer writes the section each pack's skills already read;
  moving the vocabulary onto pack names is logged as separate work (source:
  user confirmation 2026-09-11)
- Product: `architect`'s base is `docs/architecture` (source: user confirmation
  2026-09-10)

## Durable outputs

| Role | Destination | Owner | Evidence | Closes when |
| --- | --- | --- | --- | --- |
| Current architecture | `docs/architecture/agentbundle.md` § 7.1 | eugenelim | The drift section describes both reader classes agreeing | The section describes what ships |
| User-facing promise | the `architect` and re-emit reference docs | eugenelim | Corrected value and no comment-loss claim | AC8, AC9 |
| Interface compatibility | `contracts/pack.schema.json` | eugenelim | Both copies byte-equal | AC10 |
| Release history | `docs/product/changelog.md` | eugenelim | An `agentbundle` entry and one per bumped pack | Released |

The decision rationale already landed: RFC-0040 and RFC-0067 carry errata
recording the key rename, the pack renames, and `architect`'s base. No further
decision record is owed, and no criterion here claims one.

## Follow-ons

- **Move the section vocabulary onto pack names.** Logged as a backlog entry.
  It reaches 23 `SKILL.md` bodies, the `references/agentbundle-layout.md` set,
  five `pack.toml` comment blocks, four `DESIGN.md`, `docs/CONVENTIONS.md` and
  its byte-parity twin, the guide corpus, the work-loop corpus fixtures, and
  `tools/test_live_demo_guide.py`, which asserts a literal section name. It must
  also settle `[product]`, which two item types share in `workspace_mcp.py`, and
  `[discovery]`, whose base is not `product-engineering`'s. Owner: eugenelim.
- **`workspace_mcp.py` resolves three of the five declaring packs.**
  `architect` has no item type and `strategy` keys on `[product]`. This spec
  does not touch it, because skills do not read through it. Owner: eugenelim.
- **Key drift in two shipped documents.** `packs/core/.apm/skills/workspace-status/references/agentbundle-layout.md`
  documents `[product]` with a `shaping` key, and
  `guides/product-engineering/reference/intent-fields-and-modes.md` documents
  reading `parent` — neither is `output_dir`. Owner: eugenelim.
- **Removing `parent` from `pack.schema.json`.** Nothing reads it after this,
  but removing a key an external manifest may carry is its own compatibility
  question. Owner: eugenelim.
