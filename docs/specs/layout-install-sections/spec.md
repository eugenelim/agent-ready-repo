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

## The append is best-effort maintenance

One property governs every state below, and the criteria derive from it rather
than each deciding it again.

The append is optional maintenance on a file the adopter owns. It therefore
**never raises and never fails the install**: it returns, having either written
one table or written nothing, and the install's exit status and projected files
are the same either way. When it declines, it says so on stderr — except for
the three states that are the contract working, where a message would be noise
on the majority of installs.

This is scoped to the layout append alone. `_append_install_marker` shares its
call site and its `try`, and stays fatal: the marker is what uninstall and
`adapt` read, so a swallowed marker failure reports success while leaving no
record of the install.

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

- [ ] **AC3 — The separator is the only addition.** A file already ending in a
  line terminator gains none. A file ending without one gains exactly one
  terminator, matching the style the file already uses, or `\n` when it carries
  none. The appended table's own line terminators match that same style, so a
  CRLF file does not end in mixed endings. The admitted styles are LF and CRLF;
  a lone-CR file is refused under AC4 rather than appended to.

- [ ] **AC4 — Three error states refuse and report.** A file that cannot be
  decoded as UTF-8, a file that cannot be parsed, and a top-level name already
  taken by a scalar or an array of tables each leave the file byte-identical
  and write a reason to stderr naming the layout file's path and the section
  that was not written.

- [ ] **AC5 — Every designed no-op is silent.** Three states write nothing and
  emit no diagnostic: no `agentbundle-layout.toml` at the scope; the declared
  section already present as a table; a pack declaring neither or only one of
  `section` and `output_dir` for that scope. Each is the contract working — the
  first and third on the majority of installs, the second on every re-install
  of an already-configured pack — so a diagnostic there is noise, not
  reporting.

- [ ] **AC6 — Each declared section is one the pack itself documents.** For
  every pack declaring `[pack.layout.<scope>]`, the declared `section` appears
  as a documented section in at least one `references/agentbundle-layout.md`
  under that pack. Both sides derive from the repository, and the check asserts
  the size of the set it walked, so an enumeration that finds nothing fails
  rather than passes.

  The right-hand side is the sections documented by the skills that write *this
  pack's own output*, which excludes a section the pack only reads from another
  pack. Equality against every section a pack mentions is red on a correct
  implementation — `product-engineering` names three — but the unrestricted
  one-way form is too loose in the other direction: it would admit
  `section = "discovery"` alongside `output_dir = "docs/product"`, installing a
  default under a section whose consumers expect a different base.

- [ ] **AC7 — A relative value is anchored, or refused, per scope.** A relative
  `output_dir` in the repo-scope file resolves against the repository root, not
  the process working directory; the test asserts this from a working directory
  that is not the repository root, so a CWD-anchored implementation fails.

  A relative value in the user-scope file is not resolved, and the resolver
  reports it on stderr naming the file and the key — stdout being the MCP
  protocol channel. The criterion asserts that message, not the absence of a
  resolved path: `_read_scope` runs inside `contextlib.suppress(Exception)` and
  its caller catches broadly, so an implementation that raises produces exactly
  the byte-for-byte outcome of an unconfigured file, and a test asserting "the
  pattern is unchanged" passes while the adopter's configured vault is silently
  ignored. One fix that anchors both scopes to the repository root satisfies
  the first half and fails the second.

- [ ] **AC8 — `architect` declares `docs/architecture`, and says so.** Its
  manifest names that base, and both of its `references/agentbundle-layout.md`
  files document the same value rather than `docs/design`.

- [ ] **AC9 — The manifest schema admits `section` and still refuses an
  unknown key.** `pack.schema.json` accepts `section` inside
  `[pack.layout.repo]` and `[pack.layout.user]` and refuses a key it does not
  name. Byte-equality of the two copies is not restated here; the shipped
  contract-parity gate owns it.

- [ ] **AC10 — The emitted table is injection-safe.** A declared `section` or
  `output_dir` containing `"`, `]`, a newline, or `../` round-trips through
  `tomllib` as one string in one table, landing no additional TOML structure.

- [ ] **AC11 — A layout failure never fails the install; a marker failure still
  does.** When the layout append cannot write — read-only file, unwritable
  directory, or a path the write jail refuses — `agentbundle install` completes
  with its normal exit status and its projected files intact, and the reason is
  reported. A failure from `_append_install_marker`, which shares the same
  `try`, still exits non-zero. The two share one `except` today, so an
  implementation that relaxes it wholesale satisfies the first half and fails
  the second.

- [ ] **AC12 — The adopter's file keeps its permissions.** A layout file
  readable by the adopter's group or others has the same mode after an append
  as before it. The atomic replace must not hand the file the temporary file's
  private mode.

- [ ] **AC13 — A symlinked layout file is refused, not replaced.** When
  `agentbundle-layout.toml` is a symbolic link, the append writes nothing,
  reports why, and leaves the link itself intact — matching `workspace_mcp.py`,
  which already refuses to read one. It reports rather than raising, per the
  refusal contract above. An in-tree link is today replaced by a regular file,
  stranding what the adopter pointed it at; an out-of-tree link is already
  refused by the write jail, and that refusal becomes a report too.

- [ ] **AC14 — A declared `output_dir` is confined to its scope's root.** A
  value that resolves — after `~` expansion and symlink resolution — outside
  the repository at repo scope, or outside the user state root at user scope,
  is refused: nothing is written and the reason is reported. The criterion is
  on the resolved path, not on the absence of `..`, so an absolute path and a
  `~`-anchored path are both covered. This is RFC-0040's security contract for
  a catalogue-sourced value, and this change is what first carries one to a
  filesystem root.

- [ ] **AC15 — A declared `section` matches a bounded character class.** A
  `section` that is not `^[a-z0-9][a-z0-9-]*$` is refused at schema validation
  and again at the install site, which reports and writes nothing. `pack_name`
  already carries this check because it becomes a TOML key; `section` becomes a
  table header and a lookup key that every reader trusts, so it earns the same
  guard. Structural injection is closed by the emitter — this is the
  bell-rings-loud companion, and it also refuses a well-formed name carrying
  `/`, `.`, or a control character that no reader could match.

## Testing Strategy

- **The write behaviour (AC1, AC2, AC3, AC4, AC5):** TDD. Each fails on a
  different input — a wrong key, a wrong section name, a lost comment, a folded
  line ending, a file created that should not be, a diagnostic on a designed
  no-op.

- **The filesystem outcomes (AC11, AC12, AC13):** TDD. These are the states the
  change reaches for the first time, because the write has never executed. Each
  needs an observation the byte comparison cannot make — an exit status and a
  projected-file listing, a stat mode, and whether the path is still a link —
  so none of them can ride on AC2's assertion.

- **The declared section (AC6):** goal-based check. Writer and readers
  disagreed on both the key and the section name for two releases with tests
  green on each side, each exercised against its own idea of the shape. The
  observation is that a pack's declared section is one that pack's own
  documentation describes, with the walked set's size asserted so an empty
  enumeration fails.

- **Path anchoring (AC7):** TDD. Two failing inputs, not one: a repo-scope
  relative value observed from a working directory that is not the repository
  root, and a user-scope relative value that must not resolve silently. A fix
  that anchors both scopes alike passes the first and fails the second.

- **The documents (AC8, AC9):** goal-based checks over the repository-derived
  file set. They fail on different inputs — a wrong documented value, and a
  stale behavioural claim — so they need separate repairs.

- **The schema (AC9):** goal-based check. A manifest carrying `section`
  validates and one carrying an unknown sibling does not.

- **Injection safety (AC10):** TDD, mutation-checked by removing the emitter
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
- Technical: a set of `references/agentbundle-layout.md` files state the
  installer "does not preserve freeform comments or off-schema keys", which
  this change makes false. The set is derived at execution, not counted here
  (source: repository grep, 2026-09-11)
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
| Interface compatibility | `contracts/pack.schema.json` | eugenelim | Both copies byte-equal | AC9 |
| Release history | `docs/product/changelog.md` | eugenelim | An `agentbundle` entry and one per bumped pack | Released |

The decision rationale already landed: RFC-0040 and RFC-0067 carry errata
recording the key rename, the pack renames, and `architect`'s base. No further
decision record is owed, and no criterion here claims one.

## Follow-ons

- **Move the section vocabulary onto pack names.** Logged as a backlog entry.
  It reaches the skill bodies, the `references/agentbundle-layout.md` set, the
  `pack.toml` comment blocks, the `DESIGN.md` set, `docs/CONVENTIONS.md` and its
  byte-parity twin, the guide corpus, the work-loop corpus fixtures, and
  `tools/test_live_demo_guide.py`, which asserts a literal section name. The
  backlog entry carries the measured surface. It must
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
