# Spec: consolidated-pack-layout

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0040, ADR-0030, ADR-0029 (the `research-layout.toml` this generalises), ADR-0021 (`pack.toml` source of truth — home for `[pack.layout]`), RFC-0035 (namespaced adopter-editable TOML + shipped-placeholder delivery), RFC-0038 (forward-only migration — considered, found not to apply)
- **Brief:** none
- **Contract:** none under `contracts/<type>/` — the manifest extension is the `pack.schema.json` change (`[pack.layout]`), validated by `validate_pack_metadata`, not a `contracts/<type>/` API file; the `agentbundle-layout.toml` file contract itself is a prompt-only convention carried in the consumer skill bodies and their `references/agentbundle-layout.md` schema docs
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who wants to control where a pack's durable output lands edits **one
namespaced file** — `agentbundle-layout.toml` — instead of learning a per-pack
config for each of the three output-producing packs. The file carries one
`[<pack>]` table per consumer (`research`, `architect`, `product-engineering`),
each with a single `parent` key naming a **base directory** under which the skill
creates a topic-named folder per unit of work. Two locations resolve with clear
precedence — a checked-in `./agentbundle-layout.toml` overrides a personal
`~/.agentbundle/agentbundle-layout.toml`, per table — so a team can commit
repo-wide config while an individual keeps a default across repos. The file is
**adopter-owned and never shipped**: it comes into being by hand, by skill
elicitation on consent, or by an installer **append-if-exists** step that never
creates it from nothing and never overwrites a section an adopter already wrote.

Reading the file stays a **prompt-only habit** (Charter Principle 3): a skill body
reads it, anchors `parent` by the file's own location, resolves to the full
absolute path, and **surfaces that path before the first write** — there is no
runtime engine, index, daemon, or watcher anywhere. The repo-root layer
overriding the user layer crosses a real trust boundary (a cloned untrusted repo
can carry a hostile `parent`), so each consumer confines the resolved path,
rejects `..` escapes, realpath-resolves symlinks, and treats a repo-sourced
out-of-tree `parent` as an Ask-first deviation. This consolidates the
research-only `research-layout.toml` (undistributed, so a **clean rename with no
alias**) into a contract where the next consumer is a table, not a migration.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Resolve each consumer's output base in this order, **in the skill body**:
  read `agentbundle-layout.toml` — the **repo-root file's `[<pack>]` table
  first, else the user-profile file's** — to get `parent`; **anchor it by the
  file's location** (a repo-root value is repo-root-relative, a user-profile
  value must be absolute); fall back to the **pack's own default** base; then
  **elicit** if neither resolves.
- **Resolve to the full absolute path** (realpath, `~`-expanded, `..` rejected)
  and **surface it to the adopter before the first write**, then create the
  topic-named work folder under it.
- Create a **topic-named child folder per unit of work** using each pack's own
  naming convention: `research` → `<parent>/<YYYY-MM-DD>-<topic-slug>/`
  (unchanged); `architect` → `<parent>/<topic-slug>/` (new — was a loose file);
  `product-engineering` → file-per-slug under `<parent>/{intents,rollups}/` (the
  deliberate exception — single per-slug files handed downstream, not a folder).
- Keep the installer's `_append_layout_section` step **append-if-exists,
  never-create, never-overwrite**: only when a layout file already exists at the
  install scope's location, ensure `[<pack>]` is present — appending the pack's
  default if missing, leaving an existing section untouched.
- Source the appended default from the pack's **scope-keyed `[pack.layout]`
  manifest table** (`[pack.layout.repo]` / `[pack.layout.user]`, both optional), so
  the appended default matches the target file's anchor: repo-relative for the repo
  file; absolute / `~`-anchored for the user file. When a pack has **no sensible
  absolute user-scope default** (true for all three current consumers, whose output
  is per-repo), it **omits `[pack.layout.user]` entirely** — the user-scope append is
  then a **no-op**, and the commented-placeholder shape appears only in the
  `references/agentbundle-layout.md` schema doc as adopter guidance, never as
  installer-emitted output (this keeps every installer-written line on the
  injection-safe `config._emit_basic_string` path; a comment line has no such
  serialiser and would be a net-new emit shape with no `_append_install_marker`
  precedent).
- Serialise every pack-sourced string in the append through the existing
  injection-safe `config._emit_basic_string` and write via the path-jailed atomic
  `safety.write_jailed`.
- Ship each consuming pack a **`references/agentbundle-layout.md` schema doc** (a
  normal projected pack file) documenting its `[<pack>]` section: the `parent`
  key, the default base, the per-unit folder shape, and the posture.
- Add `agentbundle-layout.toml` to **this repo's** `.gitignore` alongside the
  existing `.adapt-install-marker.toml` entry.

### Ask first

- Writing under a **repo-root-sourced `parent` that resolves outside the repo
  tree**, or under any `parent` whose resolution required following a symlink out
  of the intended root — confirm the resolved absolute path with the adopter
  first (the untrusted-origin case).
- Any **further change to a consumer's output shape** beyond the file→folder
  generalisation this spec authorises for `architect` (e.g. relocating
  `product-engineering`'s briefs, or changing the topic-folder naming grammar).
- Adding a **fourth consumer**, a `[core]` table, or relocating `receive-brief` /
  `decompose-intent`'s `docs/product/briefs/` output — that is an RFC-0040
  non-goal and routes through a later RFC.

### Never do

- **No runtime reader, engine, index, daemon, or watcher** that reads
  `agentbundle-layout.toml` while a skill operates — reading is prompt-only
  (Charter Principle 3). The **only** code that touches the file is the
  install-time append step.
- The installer **never creates** the file when absent and **never overwrites**
  an existing `[<pack>]` section.
- **Never ship `agentbundle-layout.toml` as a projected artifact** and never place
  it under `packs/` — the active file is adopter-owned. The shipped artifacts are
  the `references/agentbundle-layout.md` schema doc and the within-pack
  `[pack.layout]` default.
- **Never follow a `..`-escaping or symlinked `parent` out of the intended root
  silently** — reject `..`, realpath-resolve, and surface the resolved path.
- **No legacy `research-layout.toml` alias** — it is a clean rename (the file is
  undistributed; there is nothing in the wild to be compatible with).
- **No new dependency, no new top-level directory, no new module boundary** — the
  three skills change in place, the installer step is peer to the existing
  install-marker upsert, and `[pack.layout]` is one additive optional manifest
  table.

## Testing Strategy

The prompt-only boundary makes the consumer-side controls **prose rails in skill
bodies**, not code — so the first three security criteria are **goal-based /
manual-QA by construction, not unit tests** (RFC-0040 § Risks). The installer
append is real code and is **TDD**.

- **File contract & resolution order (AC1–AC4):** goal-based check — `rg` greps
  against the three consumer SKILL.md bodies and their `references/agentbundle-layout.md`
  docs assert the two-location read, repo-overrides-user-per-table, the
  anchor-by-location rule, the pack-default fallback, the elicit tail, and the
  resolve-and-surface-before-write step.
- **Per-unit topic-folder shape (AC2, AC6, AC7):** goal-based check — `rg`
  confirms each body documents its folder grammar (`<YYYY-MM-DD>-<topic-slug>/`,
  `<topic-slug>/`, file-per-slug), and one manual-QA smoke (below) exhibits it.
- **Security rails (AC13–AC15):** goal-based / manual-QA — `rg` confirms each
  consumer body carries the realpath / reject-`..` / surface-before-write /
  repo-sourced-out-of-tree-is-Ask-first rail prose. These clauses are **net-new to
  all three bodies, including `research`**: `research-project-start`'s existing
  rail carries only an Ask-first-for-the-committed-tree deviation, *not*
  `..`-rejection or realpath — so the grep targets newly-added prose, not
  assumed-present prose. The AC16 smoke exercises a hostile repo-root `parent` and
  confirms the skill surfaces and asks rather than writing silently. There is no
  unit test here by design — the reader is a prompt; a prompt-only realpath/`..`
  rail is moreover **advisory** (a model may surface a lexical path without
  resolving a symlink), so the AC16 behavioural smoke is the only enforcing check
  and an unresolved-symlink escape is an accepted residual of the prompt-only
  boundary.
- **Installer append (AC9–AC11):** TDD — construction tests round-trip a
  `[pack.layout]` default containing `"`, `]`, newline, and `../` through
  `config._emit_basic_string` + `tomllib` (injection-safety); a **never-overwrite**
  test guards an existing `[<pack>]` section against clobber; a **never-create**
  test confirms no write when the file is absent; a **scope-keyed-selection** test
  confirms the repo append uses the repo-relative default and the user append the
  absolute / placeholder default; a **user-scope-write-succeeds** test exercises
  the `root=<home>` / `.agentbundle/` jail contract against a real
  `allowed-prefixes.user` list; and a **re-emit type-validation** test feeds a
  tampered existing `parent` (`42`, `["x"]`) and asserts it is dropped/coerced,
  not crashed on.
- **Manifest extension (AC10):** goal-based — `validate_pack_metadata` accepts a
  `pack.toml` carrying `[pack.layout]` (with `.repo`/`.user` sub-tables) and
  rejects a malformed one; the manifest schema/contract version field is bumped
  and asserted. **Run the full `agentbundle` package pytest by hand** — a contract
  bump trips lexical version-compare bugs and stale assertions in CI-ungated test
  roots (repo memory).
- **Migration (AC5, AC17):** goal-based — `rg` confirms no `research-layout.toml`
  reference remains in any skill body, guide, or changelog (only the RFC/ADR and
  historical changelog entries name it); `research` is bumped 0.4.0 → 0.5.0.
- **Version bumps + changelog (AC18):** goal-based grep on each touched pack's
  `pack.toml` + `plugin.json` version and the `docs/product/changelog.md`
  `[Unreleased]` entry.
- **One observable smoke (AC16):** visual / manual QA — with a hand-written
  repo-root `agentbundle-layout.toml`, run one consumer (`architect` or
  `research`) end-to-end and confirm the resolved absolute path is surfaced and
  the topic folder lands under `parent`; run `agentbundle install <pack>` against
  an existing layout file and confirm `[<pack>]` is appended (never overwritten;
  never created when the file is absent). Recorded in the implementing PR.

## Acceptance Criteria

- [x] **AC1 — One namespaced file, two locations, repo overrides user per table.**
  `agentbundle-layout.toml` carries one `[<pack>]` table per consumer, each with a
  single `parent` key. A skill reads the **repo-root `./agentbundle-layout.toml`**
  `[<pack>]` table if present, else the **user-profile
  `~/.agentbundle/agentbundle-layout.toml`** table; when both define `[<pack>]` the
  repo file's table is used whole and a table present only in the user file
  survives. Verification: `rg` against the three consumer SKILL.md bodies + their
  `references/agentbundle-layout.md` docs names both locations and the
  repo-overrides-user-per-table rule.

- [x] **AC2 — `parent` is a base; each unit of work gets its own topic-named
  folder.** `parent` is the directory the pack writes *under*, never the leaf the
  work lands *in*. Per-pack folder shape: `research` → `<parent>/<YYYY-MM-DD>-<topic-slug>/`;
  `architect` → `<parent>/<topic-slug>/`; `product-engineering` → file-per-slug
  under `<parent>/{intents,rollups}/`. Verification: `rg` confirms each body and
  its schema doc state the pack's folder shape and that `parent` is a base.

- [x] **AC3 — `parent` is anchored by the layout file's own location.** A
  **repo-root** file's `parent` is **repo-root-relative** (an absolute value is
  permitted but warned as non-portable); a **user-profile** file's `parent` **must
  be an explicit absolute path** (`~`-anchored ok) and a relative value there is an
  Ask-first deviation, never a silent resolve against the ambient cwd.
  Verification: `rg` against each consumer body + schema doc documents both anchor
  rules.

- [x] **AC4 — Resolve to, and surface, the full absolute path before the first
  write.** Regardless of anchor, each consumer resolves `parent` to a full absolute
  path (realpath, `~`-expanded, `..` rejected) and **surfaces that path to the
  adopter before creating the work folder**. The `..` rejection and realpath
  happen **after** anchoring, so a relative repo-file value that escapes via `..`
  (e.g. `parent = "../../etc"`) is caught regardless of which file supplied it —
  anchoring never blesses a `..`-bearing relative value as in-tree. Verification:
  `rg` against each consumer body names the resolve-then-surface-then-write order
  and the reject-`..`-after-anchoring invariant.

- [x] **AC5 — `research` migrates by a clean rename, no alias.**
  `research-layout.toml`'s top-level `parent` becomes the `[research]` table's
  `parent` in `agentbundle-layout.toml`; `research-project-start`'s body and the
  research reference / how-to / tutorial guides are updated to name the new file
  and table; **no legacy `research-layout.toml` alias is retained**. Verification:
  `rg` against `research-project-start/SKILL.md` and the research guides names
  `agentbundle-layout.toml` + `[research]` and the RFC-0038-alias-not-applied
  reasoning; AC17 confirms the old name is gone.

- [x] **AC6 — `architect` is a consumer, with a per-effort folder.**
  `architect-design` reads the `[architect]` table and writes each design effort
  into its own `<parent>/<topic-slug>/` folder (the design doc, diagrams, notes)
  instead of scanning for a loose-file home every run; its existing
  scan-then-elicit (`docs/design/`→`design/`→`architecture/`→`docs/`) becomes the
  **default** when no `[architect]` section resolves. Verification: `rg` against
  `architect-design/SKILL.md` names the `[architect]` read, the per-effort folder,
  and the scan-then-elicit default; the `references/agentbundle-layout.md` doc
  documents the folder shape and the file→folder shift.

- [x] **AC7 — `product-engineering` is a consumer, file-per-slug.** `frame-intent`
  and `align-value-stream` read the `[product-engineering]` table and write
  `<parent>/intents/<slug>.md` and `<parent>/rollups/<slug>.md` (default
  `parent = docs/product`); a per-topic *folder* is deliberately **not** used
  (single per-slug files handed downstream). `decompose-intent`'s
  `docs/product/briefs/<slug>.md` output stays **pinned** (RFC-0040 non-goal — the
  brief is the hand-off to core's `receive-brief`). Verification: `rg` against
  `frame-intent` + `align-value-stream` SKILL.md names the `[product-engineering]`
  read and the file-per-slug shape; `rg` confirms `decompose-intent` still pins
  `docs/product/briefs/`.

- [x] **AC8 — Each consumer ships a `references/agentbundle-layout.md` schema
  doc.** A normal projected pack file in each of the three packs documents that
  pack's `[<pack>]` section — `parent`, the default base, the per-unit folder
  shape, and the posture (committed-docs vs out-of-repo). The skill body reads it
  to both parse an existing section and scaffold a correct one. Verification: the
  three files exist under `packs/{research,architect,product-engineering}/.apm/skills/<skill>/references/agentbundle-layout.md`
  and each names its pack's `parent`, default, and folder shape.

- [x] **AC9 — Installer `_append_layout_section`: append-if-exists, never-create,
  never-overwrite.** `agentbundle install <pack>` gains an `_append_layout_section`
  step (modelled on `_append_install_marker`), called from the Step-11 per-scope
  loop: *if* a layout file exists at the install scope's location, ensure
  `[<pack>]` is present — append the pack's default if missing, never overwrite an
  existing section; **do not** create the file when absent. Verification:
  never-overwrite + never-create construction tests (Testing Strategy) pass; `rg`
  confirms the Step-11 loop calls the new step per scope.

- [x] **AC10 — Scope-keyed `[pack.layout]` manifest extension + validator +
  version bump.** `pack.toml` gains an optional `[pack.layout]` table with optional
  `.repo` / `.user` sub-tables (declaring the section inline or pointing at a
  within-pack `agentbundle-layout.toml` template); `pack.schema.json` accepts it
  and `validate_pack_metadata` validates it; the install scope selects which
  sub-table sources the appended default. **A pack may declare only `.repo`** (the
  three current consumers do, since their output is per-repo and they have no
  sensible absolute user default); a scope whose sub-table is absent **appends
  nothing** (no-op). The governing manifest / contract version field is the
  `adapter.toml` `[contract] version` (direct precedent: the enriched-pack-manifest
  manifest extension bumped it); it is bumped per the repo's contract-bump
  discipline. The additive optional `[pack.layout]` property leaves the stale
  `pack.schema.json` install-gate enum and each pack's `[pack.adapter-contract]
  version` untouched (the runtime version gate is major-only).
  Verification: `validate_pack_metadata` accepts a `[pack.layout]`-carrying
  `pack.toml` and rejects a malformed one; the version bump is asserted; the full
  `agentbundle` package pytest is run by hand (contract-bump traps).

- [x] **AC11 — The append is injection-safe, path-jailed, and re-emit-safe.**
  Every pack-sourced string the append writes passes through
  `config._emit_basic_string`, and the write goes through `safety.write_jailed`
  with the jail contract **modelled exactly on `_append_install_marker`** (the
  blessed precedent), not re-derived: at **repo scope** `root=<repo>`, top-level
  `relpath="agentbundle-layout.toml"`, `scope="repo"`, `allowed_prefixes=None`
  (the prefix check is skipped for a top-level repo file); at **user scope**
  `root=<home>`, `relpath=".agentbundle/agentbundle-layout.toml"`, `scope="user"`,
  `allowed_prefixes` = the adapter's `allowed-prefixes.user` list (which carries
  `.agentbundle/`), resolved via `safety.user_state_path`. A bare `relpath` under
  `root=~/.agentbundle` is **rejected** — `write_jailed` requires each prefix to
  end in `/` and matches by `startswith`, so the user file must be addressed
  relative to `<home>` and sit under the `.agentbundle/` prefix (the foot-gun the
  `_append_install_marker` shape already avoids). Because the append **reads an
  adopter-owned (possibly hand-edited) file and re-emits it**, it must also
  **type-validate each existing `[<pack>]` / `parent` it round-trips** — dropping
  or coercing a non-`str` `parent` before re-emission, exactly as
  `_append_install_marker` hardened its parsed fields. Verification: a
  construction test round-trips a `[pack.layout]` default containing `"`, `]`,
  newline, and `../` through `_emit_basic_string` + `tomllib`, asserting the
  parsed `parent` is intact, the emitted TOML is well-formed, and the parsed
  document contains **exactly one `[<pack>]` table** (a smuggled `\n[evil]\n`
  header did not materialise); a test that the **user-scope write succeeds**
  against a real `allowed-prefixes.user` list (not merely that the `TypeError`
  fires when the list is omitted); a **re-emit type-validation** test feeding a
  tampered existing section (`parent = 42`, `parent = ["x"]`) asserts it is
  dropped/coerced, not crashed on; a **symlink-target fails-closed** test confirms
  that when the layout *file path itself* is a symlink escaping `root`,
  `write_jailed`'s `assert_under` realpath-resolve raises `PathJailError` (the append
  fails closed, never following the link); plus the never-overwrite / never-create
  tests of AC9. **Scope note:** the append validates the *type* of a re-read `parent`
  (str-vs-non-str, mirroring `_append_install_marker`) and serialises it
  injection-safely, but it deliberately does **not** validate `parent`'s *path
  semantics* — a hostile `parent = "../../etc"` round-trips intact and well-formed,
  because confining the resolved `parent` value is wholly the prompt-only reader's
  job (AC13–AC15), not the path-jailed *file* write's. *(RFC-0040 spec-stage security
  AC 4.)*

- [x] **AC12 — Reading is prompt-only; no engine creeps in.** No consumer ships a
  script, daemon, index, counter, or any runtime code that reads
  `agentbundle-layout.toml`; resolution lives in the skill body. The only code
  touching the file is the install-time append. Verification: the three consumer
  skill directories contain no `scripts/` that read or resolve the layout file
  (`find … \( -name '*.py' -o -name '*.sh' \)` returns nothing layout-reading);
  `rg` confirms each body frames resolution as prompt-driven.

- [x] **AC13 — Confinement + `..` rejection + surface-before-write (security).**
  Each consumer confines the resolved `parent` + work folder to the pack's intended
  root, rejects `..` escapes, and surfaces the resolved absolute path before the
  first write. Verification: goal-based / manual-QA — `rg` confirms the rail prose
  in each body; the AC16 smoke confirms a `..`-containing `parent` is rejected and
  the resolved path surfaced. *(RFC-0040 spec-stage security AC 1.)*

- [x] **AC14 — Realpath resolution makes symlinks visible (security).** The
  resolved path is realpath-resolved so a symlinked `parent` or ancestor is visible
  and not silently followed out of tree. Verification: goal-based / manual-QA —
  `rg` confirms each body specifies realpath resolution; the AC16 smoke confirms a
  symlinked `parent` surfaces its real target before any write. *(RFC-0040
  spec-stage security AC 2.)*

- [x] **AC15 — Repo-root-sourced out-of-tree `parent` is untrusted-origin
  (security).** A `parent` taken from the repo-root file that resolves outside the
  repo tree is treated as untrusted-origin and **confirmed before writing** (the
  cloned-untrusted-repo case); the user-profile file is foot-gun-only (adopter is
  the author). This trust posture is the **reader's** (AC13–AC15); the install-time
  append still type-validates the user file's re-read `parent` per AC11 regardless of
  scope, so the two ACs do not contradict on who trusts the user file. Verification: goal-based / manual-QA — `rg` confirms the
  untrusted-origin Ask-first rail in each body; the AC16 smoke exercises a hostile
  repo-root `parent` (e.g. an absolute `~/.ssh`, or a relative `../../<outside>`
  that escapes the repo via `..`) and confirms the skill asks rather than writing.
  *(RFC-0040 spec-stage security AC 3.)*

- [x] **AC16 — One observable smoke project.** A real end-to-end run of one
  consumer with a hand-written repo-root `agentbundle-layout.toml` produces the
  topic-named folder under the resolved `parent` and surfaces the absolute path;
  a hostile/out-of-tree `parent` triggers the Ask-first confirmation; and
  `agentbundle install <pack>` against an existing layout file appends `[<pack>]`
  (never overwrites an existing section; never creates the file when absent).
  Verification: manual QA — the implementing PR records the produced tree, the
  surfaced path, the Ask-first prompt, and the append/never-overwrite/never-create
  outcomes (self-report is not sufficient; the files are the signal).

- [x] **AC17 — `.gitignore` housekeeping (this repo only).**
  `agentbundle-layout.toml` is added to this repo's `.gitignore` alongside
  `.adapt-install-marker.toml`, so a contributor exercising a consumer skill in the
  catalogue does not trip the self-host drift gate; adopters ship **no** gitignore
  rule. Verification: `rg -F 'agentbundle-layout.toml' .gitignore` returns a hit in
  the install-time-scratch section, and `rg` finds no surviving `research-layout.toml`
  reference **on a live consumer surface** — the three skill bodies and the
  `docs/guides/research/**` guides. The old name legitimately survives in **historical
  record**, which the sweep exempts: this spec/plan and its RFC-0040 / ADR-0030; the
  **frozen** `docs/specs/research-project-mode/` spec & plan and that spec's row in the
  living `docs/specs/README.md` index (CONVENTIONS forbids editing a frozen spec's
  body — it is historical description of what that spec shipped); and historical
  `docs/product/changelog.md` entries.

- [x] **AC18 — Pack version bumps + changelog.** `research` is bumped 0.4.0 →
  0.5.0; `architect` and `product-engineering` get the appropriate next bump for a
  new-consumer + (architect) behaviour-change; each pack's `pack.toml` and
  `plugin.json` move together; `docs/product/changelog.md` `[Unreleased]` records
  the consolidation (renaming the `research-layout.toml` mention) under the
  appropriate `### Added` / `### Changed` sections. Verification: goal-based grep on
  the versions and the changelog entry.

## Assumptions

- Technical: the three consumer skills live at
  `packs/{research,architect,product-engineering}/.apm/skills/<name>/SKILL.md` and
  project to `.claude/skills/…`; this spec PR authors governance docs only and
  edits **no** skill body — the body/installer/manifest changes are the implementing
  PR (source: directory listing 2026-06-22; RFC-0040 § Follow-on artifacts).
- Technical: `research-project-start` already reads `research-layout.toml` at two
  locations prompt-only today (`SKILL.md` § "Where the project lives", lines
  83–109), so the two-location namespaced read is a same-shape increment, not new
  capability; the `..`-rejection / realpath / surface-before-write security rails
  (AC13–AC15), however, are **net-new to all three bodies including `research`** —
  the existing rail lacks them (source:
  `packs/research/.apm/skills/research-project-start/SKILL.md`).
- Technical: the installer append reuses `_append_install_marker`'s upsert pattern
  (`packages/agentbundle/agentbundle/commands/install.py`, called from the Step-11
  per-scope loop), the injection-safe `config._emit_basic_string`
  (`config.py:383`), and the path-jailed atomic `safety.write_jailed`
  (`safety.py:264`) as-is (source: code survey 2026-06-22; RFC-0040 § Evidence).
- Technical: `[pack.layout]` is added to `pack.schema.json` (validated by
  `validate_pack_metadata`); the exact schema/contract version field that a
  manifest extension bumps is settled as the first step of the manifest task, since
  the contract-bump traps (lexical version-compare; CI-ungated test roots) demand
  the full package pytest be run by hand (source: RFC-0040 § Risks; repo memory
  "Contract-bump test traps").
- Technical: `research-layout.toml` is undistributed — `research 0.4.0` (commit
  2026-06-22) landed after `agentbundle-v0.6.0` (2026-06-21) — so a clean rename
  with no alias is correct; if a release cuts between this spec and the
  implementing PR that includes `research 0.4.0`, the migration reverts to a
  one-release alias (source: RFC-0040 § Key assumptions / Decision 8).
- Technical: the active `agentbundle-layout.toml` is adopter-created and never
  shipped into a projected path (it would trip the self-host drift gate); the
  shipped artifacts are the `references/agentbundle-layout.md` schema doc and the
  within-pack `[pack.layout]` default (source: RFC-0040 § "schema doc vs the file";
  RFC-0035 `references/sso-config.toml` precedent).
- Process: RFC-0040 + ADR-0030 are Accepted; this spec wires **three** consumers in
  one implementing spec by the Approver's explicit call (source: RFC-0040 § Follow-on
  artifacts / Decision 1).
- Process: the security control is prose-enforced acceptance criteria, not a code
  jail, because the reader is prompt-only (Charter Principle 3 forecloses a code
  path-validator in the skill body); verification of AC13–AC15 is goal-based /
  manual-QA by construction (source: RFC-0040 § Risks pre-mortem + § Follow-on
  security ACs).
- Product: `architect` and `product-engineering` are genuine relocation needs (the
  Approver confirms it), not a build-the-seam hedge: architect's every-run
  re-elicit can't scale to a platform's many architecture topics, and
  product-engineering's hardcoded `docs/product/` blocks adopters who file product
  docs elsewhere; the contract degrades gracefully if demand is softer (source:
  RFC-0040 § Key assumptions, Approver-confirmed).
