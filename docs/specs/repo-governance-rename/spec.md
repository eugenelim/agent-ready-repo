# Spec: Rename governance-extras to repo-governance with an installer rename hint

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0110 (with its 2026-10-25 errata)
- **Brief:** brief:repo-governance-pack
- **Discovery:** none
- **Contract:** `contracts/renames/pack-renames.toml`, `contracts/renames/pack-renames.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->

## Outcome

An adopter who has `governance-extras` installed and runs agentbundle 0.57.0 or later against a catalogue that carries the rename learns that the pack is now `repo-governance`, gets the exact commands to move, and has nothing changed by the command that told them. This repository publishes the pack only as `repo-governance` 2.0.0, and the old name stays reserved so no other pack can take it.

## What Changes

- The pack moves from `packs/governance-extras/` to `packs/repo-governance/` at 2.0.0, with display name "Repository Governance".
- Its guides move from `guides/governance-extras/` to `guides/repo-governance/`.
- A catalogue-owned rename map, `contracts/renames/pack-renames.toml`, records `governance-extras` → `repo-governance`. Its schema is `contracts/renames/pack-renames.schema.json`. Neither file is a member of the catalogue specification, so `contracts/catalogue-spec.toml` and its released version are unchanged.
- `agentbundle install --pack`, `upgrade --pack` and `upgrade --all` print a rename hint where they print "not found" today. That covers `packages/agentbundle/agentbundle/commands/install.py` and `upgrade.py`.
- A lint refuses a pack whose name is an old name in the map, and a map target that is not a pack in the same catalogue.
- `packs/iac-terraform` requires `repo-governance ^2.0` at 0.2.0. `profiles/full-ceremony.toml` lists `repo-governance`.
- Every live surface that names the pack uses the new name. That covers build and site code, CI workflows, lints, tests, web pages, other packs' skills and live docs.
- agentbundle releases as 0.57.0. Its changelog and the `repo-governance` README carry the migration steps.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Adopters must learn the new name and the steps, including on CLIs older than 0.57.0 that print no hint | `packs/repo-governance/README.md` § migrating from governance-extras; `guides/repo-governance/` | pack owner | the README section carries the three steps verbatim | the README steps match the hint's steps for AC-0026's input, and the README tells readers to replace the adapter with their own |
| Interface compatibility | The rename map is a new published catalogue contract | `contracts/renames/pack-renames.toml`, `contracts/renames/pack-renames.schema.json`, `contracts/README.md` rows, `contracts/REGISTRY.md` row | catalogue maintainers | schema validation test; contract registry test | both files listed in `contracts/README.md` § Repository only, with no `catalogue-spec.toml` row |
| Maintainer procedure | A future rename must reuse the map rather than invent a path | `contracts/README.md` entry for `pack-renames.toml` | catalogue maintainers | the entry names how to add a rename | entry present |
| Release history | agentbundle, `repo-governance` and `iac-terraform` each release | `packages/agentbundle/CHANGELOG.md`; `docs/product/changelog.d/` fragments for all three packages | release owner | fragments pass `tools/changelog.py` validation | three fragments and the CHANGELOG entry exist |
| Current architecture | `docs/architecture/pack-layout.md` names the pack | that file | architecture owner | renamed | renamed |
| Decision rationale | Already recorded | RFC-0110 and its errata | — | — | none further |
| Reusable learning | none: the delivery teaches no fact a later author needs beyond the map entry above | — | — | — | — |

## Agent Rules

### Always do

- Classify each file that names `governance-extras` by RFC-0110 D3's live-versus-frozen status rule before editing it. A frozen file is never edited.
- Regenerate projections with `FORCE=1 make build-self` after any pack source change, and commit the result in the same change.
- Print every value in a hint step through the existing shell-quoting helper. Print a reporting source only when it is printable, and a recorded source only in credential-free form.
- End every commit that touches `packages/agentbundle/` with `Engine-Change-RFC: RFC-0110`, as `packages/AGENTS.local.md` § Engine-Change-RFC requirement asks.
- Read the map and each dependent's `pack.toml` only through `file_safety.read_confined_regular_file`, rooted at the reporting catalogue's root.

### Ask first

- Any change to install, upgrade or uninstall behaviour other than replacing the not-found output with the hint and showing it before `upgrade --pack`'s multi-adapter refusal (AC-0033).
- Adding an entry to the rename map other than `governance-extras` → `repo-governance`.
- Editing a file whose status under RFC-0110 D3's rule is unclear.

### Never do

- Install, upgrade or uninstall any pack as a side effect of printing the hint.
- Resolve, fetch or read any catalogue other than the reporting catalogue while building the hint.
- Add a new top-level directory, a new third-party dependency, or a new CLI subcommand or flag.
- Edit a frozen record, or rename the build-pipeline fixture pack under `packages/agentbundle/tests/build_pipeline/fixtures/packs/governance-extras/`.

## Testing Strategy

- **Hint selection, message text, source rendering and refusals (AC-0013, AC-0014, AC-0031, AC-0028, AC-0015, AC-0030, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0027):** TDD. Each is a pure function of the reporting catalogue, the requested name and the installed state, so unit tests pin it exactly.
- **Hint on each catalogue shape (AC-0009, AC-0010, AC-0011, AC-0012, AC-0023, AC-0033, AC-0034, AC-0035):** goal-based, as integration tests that run the real CLI. Local path runs unpatched. The release archive is built in the test with `agentbundle catalogue package` and served from a local HTTPS server whose throwaway certificate authority reaches the CLI through `AGENTBUNDLE_CA_BUNDLE`, so no code is patched. The git shape runs the real CLI with only the network download replaced by the same local tree, because a `git+https` source downloads exactly that tree.
- **Migration steps complete and the map ships (AC-0024, AC-0029, AC-0032, AC-0006):** goal-based, as an end-to-end test over a pre-rename catalogue fixture and an archive built from this repository.
- **The map and its guard (AC-0005, AC-0007, AC-0008):** TDD over fixture catalogues for the lint, and schema validation for the map.
- **The renamed pack, its dependents and completeness (AC-0001, AC-0002, AC-0003, AC-0004, AC-0025, AC-0026):** goal-based: parsed manifests, a profile install into an empty repository, a repository search compared to the exception set, a no-diff `FORCE=1 make build-self`, and a comparison of the CHANGELOG and README step commands with the hint's steps.

## Acceptance Criteria

Terms used below:

- **The reporting catalogue** is the catalogue the command resolved and found without the requested pack.
- **The map** is the file at the fixed path `contracts/renames/pack-renames.toml` under the reporting catalogue's root.
- **An unsafe character** is one that `escape_rendered_value` in `catalogue_tooling/diagnostics.py` renders as a `\uXXXX` escape.
- **A printable source** is a non-empty source with no unsafe character, no user-info and no query. Its fragment is empty, or, for an `archive+https` source only, exactly `sha256=` followed by 64 lowercase hexadecimal digits.
- **The credential-free form** of a source is that source with its user-info, query and fragment removed and its unsafe characters escaped.
- **Credential-bearing** describes a source that `canonicalize_source` in `config.py` rejects for user-info or for a credential term in a query key or the fragment.
- **No recorded source** means the recorded source is missing, empty, not text, or the legacy value `agent-ready-repo`.
- **Two sources differ** when the pack does not have no recorded source, and `canonicalize_source` does not return the same non-`None` value for its recorded source and for the reporting source.
- **A pack directory** in a catalogue is found as the installer's `_locate_pack` finds it: `packs/<name>` first, then `<name>` at the catalogue root. A name "is a pack in the catalogue" when one of those holds a `pack.toml`.
- **The installed state the hint reads** is the target repository's repo-scope state, whatever `--scope` the reporting command was given. `governance-extras`, `repo-governance` and `iac-terraform` each declare `allowed-scopes = ["repo"]`, so no other scope can hold them.
- **The target root** is the `--root` value given to `upgrade` or the `--output` value given to `install`, when one was given.
- **A dependent** is a pack in the installed state the hint reads whose `pack.toml` in the reporting catalogue declares a required dependency on the rename's target.
- **An adapter row** is one installed-state record of a pack for one adapter.
- **The not-found points** are `install --pack` and `upgrade --pack` reaching a pack missing from the reporting catalogue, and an `upgrade --all` row whose pack is missing. AC-0021, AC-0022, AC-0023 and AC-0027 govern those points. On the multi-adapter path of AC-0033, AC-0035 alone governs what is printed when no hint is.
- **A shipped adapter name** is one of the values the CLI's `--adapter` option accepts (`cli._shipped_adapters_choices`). An adapter value appears in the hint's text only when it is a shipped adapter name.
- **The placeholder** is the literal `<catalogue-source>`, printed unquoted.
- **The hint's layout** is, in order:
  1. the first line AC-0009 names;
  2. the line `Run these steps to move to it:`;
  3. sentences that qualify no single step: the AC-0018 sentence, then one AC-0030 notice of either kind per affected pack, ordered by raw installed name compared by code point;
  4. each step as a line `  <n>. <step>`, numbered from 1. Each step has one fixed word order, where bracketed parts appear only when they apply and every value passes through the shell-quoting helper:
     - `agentbundle uninstall --pack governance-extras --scope repo [--adapter <adapter>] [--root <target root>]`
     - `agentbundle install --pack repo-governance --scope repo [--adapter <adapter>] [--output <target root>] <source>`
     - `agentbundle upgrade --pack <dependent> --scope repo [--adapter <adapter>] [--root <target root>] <source>` Any sentence that qualifies the step sits on the lines directly above it: the AC-0028, AC-0016 or AC-0017 sentence first, then the placeholder sentence.
- **A step** is the command text after `<n>. ` on a step line.
- **The hint's text** is every line the hint builder returns, wherever it is printed: stderr, the `upgrade --all` table, and the `rename_hint` field of `--format json` output.

### The pack and its dependents

- [x] **AC-0001.** `packs/repo-governance/pack.toml` has `name = "repo-governance"`, `version = "2.0.0"` and `display_name = "Repository Governance"`; `packs/repo-governance/.claude-plugin/plugin.json` has version `2.0.0`; and `packs/governance-extras/` does not exist.
- [x] **AC-0002.** `packs/iac-terraform/pack.toml` is at version `0.2.0` and its required dependency reads `pack = "repo-governance"`, `version = "^2.0"`.
- [x] **AC-0003.** `agentbundle install --profile full-ceremony` against this repository's catalogue, into an empty repository, exits 0 and records `repo-governance` 2.0.0 as installed.
- [x] **AC-0004.** `FORCE=1 make build-self` on the finished change leaves `git status --porcelain` empty.

### The map

- [x] **AC-0005.** `contracts/renames/pack-renames.toml` contains exactly one rename, `governance-extras` → `repo-governance`, and validates against `contracts/renames/pack-renames.schema.json`. `contracts/catalogue-spec.toml` is byte-identical to its state before this change.
- [x] **AC-0006.** The archive that `agentbundle catalogue package` builds from this repository contains `contracts/renames/pack-renames.toml` byte-identical to the source file.
- [x] **AC-0007.** The repository lint fails on a fixture catalogue in which a pack is named after an old name in its map.
- [x] **AC-0008.** The repository lint fails on a fixture catalogue whose map names a target that is not a pack in that catalogue.
- [x] **AC-0027.** At the not-found points, the command prints the existing not-found message, no hint, and exits 1 when the map, or its `contracts/` or `contracts/renames/` directory, is any of: a symlink, a hard link, a non-regular file, or a map larger than 65,536 bytes. An `upgrade --all` row in that case reports `pack-not-found`.
- [x] **AC-0022.** At the not-found points, a map that cannot be read, decoded as UTF-8, parsed as TOML, or shape-checked produces no hint. This includes nesting deep enough to exhaust recursion, wrong-typed values, a missing key, a name failing `^[a-z0-9][a-z0-9-]*$`, and a target that is not a pack in the reporting catalogue as the term above defines. In each case the command prints the existing not-found message, writes no traceback, and exits 1. An `upgrade --all` row in that case reports `pack-not-found`.

### The hint

- [x] **AC-0009.** For each of `install --pack governance-extras` and `upgrade --pack governance-extras`, run on each of the local-path, release-archive and git catalogue shapes, two things hold. The reporting catalogue's map renames the pack, and `governance-extras` and `iac-terraform` are installed. Stderr's first line reads `<command>: pack 'governance-extras' was renamed to 'repo-governance'.`, where `<command>` is `install` or `upgrade`, and the rest of stderr follows the hint's layout. Its steps are exactly those AC-0013, AC-0014 and AC-0015 define for that shape's source, in that order. Its sentences are exactly those AC-0014, AC-0016, AC-0017, AC-0018, AC-0028 and AC-0030 require for the fixture. In this fixture, both packs were recorded from the reporting catalogue's own source. The exit code is 1.
- [x] **AC-0010.** In every run AC-0009, AC-0011, AC-0021, AC-0022, AC-0023, AC-0027, AC-0033, AC-0034 and AC-0035 describe, the installed-state files and every file under the target repository are byte-identical before and after the command.
- [x] **AC-0011.** `upgrade --all --scope repo` is run on each of the three catalogue shapes. `governance-extras` and `iac-terraform` are installed, and `governance-extras`'s recorded source is a catalogue carrying the map. The run does three things:
  - it reports that row's hint text in the table, and in a `rename_hint` array of strings present only on that row when run with `--format json --dry-run`;
  - it marks every other row that is not `skipped-direct` as `blocked`;
  - it exits 1.
- [x] **AC-0012.** `upgrade --all --scope repo`, run where `governance-extras` is installed with a recorded source that is a pre-rename release archive, upgrades that row from that archive as it does today, and prints no rename hint.
- [x] **AC-0013.** The hint prints `agentbundle uninstall --pack governance-extras --scope repo` when the installed state the hint reads holds `governance-extras`, and not at all when it does not. When it has more than one adapter row, the step is printed once per adapter row, carrying `--adapter <adapter>` in the layout's word order.
- [x] **AC-0014.** The hint always prints `agentbundle install --pack repo-governance --scope repo <source>` as a step. When `governance-extras` is installed, it prints the step once per adapter row of it, each carrying `--adapter <adapter>` in the layout's word order, so the new pack lands on the same hosts. When it is not installed, it prints the step once, carrying `--adapter <adapter>` only when the reporting `install` command was given `--adapter`, with that value. `<source>` is always the last word of a step. `<source>` is the reporting catalogue's source when that source is printable. Otherwise it is the placeholder. Every step that carries the placeholder, from this criterion or AC-0015, is introduced by the sentence `Edit this step to name a catalogue source before running it; leaving the source out sends this step to a different catalogue.`
- [x] **AC-0033.** `upgrade --pack governance-extras` with no `--adapter`, run where `governance-extras` has two adapter rows that both came from a catalogue and the reporting catalogue's map renames it, prints the hint with the per-adapter steps AC-0013 and AC-0014 define, instead of the existing "pass --adapter" refusal, and exits 1.
- [x] **AC-0034.** `upgrade --pack <pack>` with no `--adapter`, run where `<pack>` has two adapter rows and at least one of them is a direct install, prints today's multi-adapter refusal byte-identical, exits 1, and resolves no catalogue and makes no network request.
- [x] **AC-0035.** `upgrade --pack <pack>` with no `--adapter`, run where `<pack>` has two adapter rows that both came from a catalogue, prints today's multi-adapter refusal byte-identical and exits 1 whenever no hint is printed. That covers each of these inputs: `<pack>` is a pack in the reporting catalogue; the map does not rename `<pack>`; resolving or fetching the reporting catalogue fails; and each input AC-0021, AC-0022, AC-0023 and AC-0027 name.
- [x] **AC-0031.** Every step that carries the placeholder ends with the bare, unquoted word `<catalogue-source>`, and is rejected as a syntax error by `bash -n`, `zsh -n` and `sh -n`, so no shell runs it as written. The fixtures include the single-adapter and multi-adapter forms of the AC-0014 and AC-0015 steps.
- [x] **AC-0028.** When `governance-extras` is installed with a recorded source that differs from the reporting catalogue's source, or with no recorded source, the AC-0014 step is introduced by a sentence. That sentence calls the step a move between catalogues and names the recorded source in credential-free form, or states that the pack has no recorded source.
- [x] **AC-0015.** The hint prints one `agentbundle upgrade --pack <dependent> --scope repo <source>` step per dependent that AC-0030 leaves a step, and per adapter row of it. When the dependent has more than one adapter row, each step carries `--adapter <adapter>` in the layout's word order. `<source>` is rendered and placed as in AC-0014. It prints none when there is no dependent.
- [x] **AC-0030.** In this criterion, `<escaped-name>` is the installed name passed through `escape_rendered_value`, and `<target>` is the rename's target. For each installed pack other than the rename's old name, the builder checks the name against `^[a-z0-9][a-z0-9-]*$` before using it in a catalogue path. Each path component under the reporting catalogue's root, `packs` included, is tested without following links. Every such pack falls in exactly one case:
  - **Absent:** the name passes the check, every candidate pack directory and its parent is a real directory or absent, and no candidate holds anything at `pack.toml`. The pack is not a dependent, and the hint says nothing about it.
  - **Readable:** the name passes the check, every candidate pack directory and its parent is a real directory or absent, and the first candidate that holds an entry at `pack.toml` holds a regular file there with one link and at most 65,536 bytes. It decodes as UTF-8 and parses as TOML without exhausting recursion. The pack is a dependent when `pack.dependencies.required` is an array holding at least one table whose `pack` value is the string naming the rename's target. Any other structure, an entry's `catalogue` value included, is ignored. A dependent with any adapter row that names something other than a shipped adapter name gets no step for any of its adapter rows, and the hint adds the notice `Installed pack '<escaped-name>' has an adapter that is not a shipped adapter; upgrade it by hand.` instead.
  - **Unchecked:** every other case. That includes a name that fails the check; a link or non-directory at `packs` or at either candidate pack directory, whatever a later candidate holds; and, at `pack.toml`, a symlink, a hard link, a directory or other non-regular file, a file over 65,536 bytes, invalid UTF-8, invalid TOML, or nesting that exhausts recursion. The pack gets no step. The hint keeps all its other lines and adds the notice `Could not check installed pack '<escaped-name>' for a dependency on '<target>'.`.

  The command writes no traceback and exits 1.
- [x] **AC-0016.** When a dependent's recorded source differs from the reporting catalogue's source, its step is introduced by a sentence calling it a move between catalogues and naming that recorded source in credential-free form.
- [x] **AC-0017.** When a dependent has no recorded source, its step is introduced by a sentence stating that the pack has no recorded source.
- [x] **AC-0018.** When the reporting catalogue's source is credential-bearing, the hint states that `upgrade` cannot record that source, so each dependent keeps its old recorded source.
- [x] **AC-0019.** The hint's text contains no user-info, no query content, no fragment content other than an `archive+https` source's `sha256=` digest, and no unescaped unsafe character from any fixture source. The fixtures cover each of these, used both as the reporting source on the `archive+https` shape and as a recorded source:
  - a token as the user name;
  - `user:password@`;
  - `password=`, `secret=`, `sig=`, `md5=`, `verify=` and `Policy=` query keys;
  - a bare query segment with no `=`;
  - a `;`-joined pair such as `?a=1;token=x`;
  - a percent-encoded credential term, in a query key and in a fragment;
  - an upper-case credential key;
  - a source that carries credentials and also contains U+202E.
- [x] **AC-0020.** Every printed step that carries no placeholder is a shell command whose words `shlex.split` returns as intended for every fixture source and target root, including values with spaces, quotes, `$`, `;` and backticks.
- [x] **AC-0021.** At the not-found points, when the reporting catalogue's map is valid and renames the requested pack, and the reporting source is empty, contains an unsafe character or starts with `-`, or the target root contains an unsafe character or starts with `-`, or an adapter row of `governance-extras` names something other than a shipped adapter name, no hint is printed. `install --pack` and `upgrade --pack` print the existing not-found message, and the rest of stderr is exactly the refusal reason `<command>: the rename hint for '<old name>' is withheld because the catalogue source, target root or an installed adapter name cannot be printed safely.`, with only `<command>` (`install` or `upgrade`) and `<old name>` (the requested pack) filled in. Both commands exit 1. An `upgrade --all` row reports `pack-not-found` with no hint and no refusal reason. No file changes. The fixtures include U+202E, U+200B, U+2028, U+007F and a leading `-` in the source, U+000A, U+202E and a leading `-` in the target root, and the adapter keys `bogus`, `-x`, and keys carrying U+000A and U+202E, on `governance-extras`. When the map is absent or invalid, or does not rename the requested pack, an unsafe source or target root leaves today's not-found output byte-identical.
- [x] **AC-0023.** Building the hint reads no catalogue other than the reporting catalogue and makes no network request. When the map renames the requested pack only in another catalogue, the command at the not-found points prints the existing not-found message and no hint.

### Migration and completeness

- [x] **AC-0024.** A repository has `governance-extras` 1.0.3 and `iac-terraform` 0.1.12 installed, with `iac-terraform` recorded from a pre-rename release-archive fixture. The test runs the printed steps in order against the post-rename catalogue fixture. It adds `--yes` to each step to answer the confirmation prompt, and passes no `--force`. The results are:
  - each step exits 0;
  - the AC-0016 sentence was printed;
  - at the end, `repo-governance` 2.0.0 and `iac-terraform` 0.2.0 are installed and `governance-extras` is absent.
- [x] **AC-0032.** The AC-0024 run, with the post-rename catalogue served as an `archive+https` release archive over HTTPS, prints steps whose source is that `archive+https` source with its `#sha256=` fragment, and those steps complete with the same end state.
- [x] **AC-0029.** The AC-0024 run, with `iac-terraform` installed with no recorded source, ends in the same installed state and printed the AC-0017 sentence.
- [ ] **AC-0025.** `git grep -l governance-extras` on the finished change returns only paths in these categories:
  - files frozen under RFC-0110 D3's status rule;
  - the build-pipeline fixture under `packages/agentbundle/tests/build_pipeline/fixtures/packs/governance-extras/`, and files under `packages/agentbundle/tests/build_pipeline/` that load that fixture by name;
  - `docs/adr/README.md` and `docs/rfc/README.md`, where every matching line is the generated index row of a frozen record;
  - `workspace.toml` lines that register `docs/product/briefs/repo-governance-pack.md` or this spec;
  - evidence pinned to a recorded `baseline_commit`: `docs/product/research/plan-evolution-experiments/` and `tools/plan_evolution_workbench/fixtures/`;
  - digest-pinned golden fixtures whose tests forbid regeneration: `packs/core/tests/skills/work-loop/fixtures/corpus/001-recorded/plan.md`;
  - `docs/specs/workspace-retirement/inventory.toml`, where every matching line references the path of the frozen spec directory `docs/specs/governance-extras-without-core/`;
  - `contracts/renames/pack-renames.toml`;
  - the migration text in `packages/agentbundle/CHANGELOG.md`, the three changelog fragments and `packs/repo-governance/README.md`;
  - tests and fixtures of the hint, of the lint in AC-0007 and AC-0008, and of this criterion;
  - intents whose status is `Fulfilled`, and `docs/knowledge/observations/` journals;
  - `docs/product/briefs/repo-governance-pack.md` and `docs/specs/repo-governance-rename/`.
- [x] **AC-0026.** `packages/agentbundle/agentbundle/version.py` reads `0.57.0`. The step commands in `packages/agentbundle/CHANGELOG.md`'s `0.57.0` entry and in `packs/repo-governance/README.md` both equal the hint's steps for this input:
  - `governance-extras` installed at repo scope for the one adapter `claude-code`;
  - `iac-terraform` installed at repo scope for the one adapter `claude-code`;
  - the reporting source `git+https://github.com/eugenelim/agent-ready-repo`.

  Both texts also say, next to the steps, to replace `claude-code` with the adapter the reader's `governance-extras` is installed for.

## Follow-ons

none

## Assumptions

- Security: `upgrade --all` already prints each pack's recorded source in full, in the table's `SOURCE` column and in JSON `sources[].source` and `rows[].source` (`upgrade.py:1236-1250`, `:1319-1321`). A recorded presigned URL whose keys `canonicalize_source` accepts, such as `sig=`, therefore reaches stdout today. This spec leaves that output unchanged, so the gap stays open. It needs its own owner decision and change (settled by: the agentbundle owner).
- Security: the existing not-found line prints `catalogue at {catalogue_dir}` unescaped (`install.py:563`, `upgrade.py:1781`). A local-path source with an unsafe character therefore reaches stderr raw on that line, even though AC-0021's refusal reason omits it. This spec leaves the existing line unchanged, so the gap stays open (settled by: the agentbundle owner).
- Security: today's multi-adapter refusal prints each adapter key raw (`upgrade.py:1676-1683`). AC-0035 keeps that refusal byte-identical, so an installed-state adapter key with an unsafe character still reaches stderr raw on that path. This spec leaves it unchanged, so the gap stays open (settled by: the agentbundle owner).
- Technical: `upgrade --pack` refuses a pack installed at more than one scope before it resolves any catalogue (`upgrade.py:1585-1591`), and the hint reads only repo scope. Neither matters for this rename, because all three packs it touches allow only repo scope. A later rename of a pack installable at several scopes would need both decided (settled by: the spec for that rename).
