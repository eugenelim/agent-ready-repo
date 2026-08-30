# agentbundle changelog

All notable changes to the `agentbundle` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

## [0.40.3] — 2026-08-29

### Changed

- Catalogue validation now checks the bounded agent-reviewer declaration and
  projects its least-privilege posture across supported adapters.

## [0.40.2] — 2026-08-28

### Changed

- Catalogue seed lint now admits the core pack's bounded rule router,
  cognitive-load topic, and scoped docs guidance while it keeps rejecting
  undeclared seed paths.

## [0.40.1] — 2026-08-28

### Changed

- Workspace MCP brief lifecycle metadata now invokes the canonical
  `author-delivery-brief` owner. Existing workspace kinds, queues, and artifact
  paths are unchanged.

### Security

- The packaged `workspace-status` runtime now rejects a queue locator that
  carries an embedded credential, token, or absolute local path, matching the
  minimization contract the Core pack applies at intake.

## [0.40.0] — 2026-08-25

### Added

- Default catalogue builds now emit deterministic Agent Plugins 1.0.0 packages
  for skills-only packs under `agent-plugins/<pack>/`. Root manifests validate
  offline against an immutable vendored schema; privacy-minimal author data,
  strict portable identities, complete exclusion diagnostics, and confined
  skill projection fail closed before route output changes.
- A closed reverse-domain extension allocation contract reserves the Kiro and
  Copilot namespaces and requires active, versioned schemas before extension
  manifest or file content can enter a portable package.

### Changed

- The explicit distribution-route contract is version 0.2 and declares the
  additive `agent-plugin` route alongside unchanged APM and Claude routes.

## [0.39.4] — 2026-08-24

### Fixed

- Codex projections now retain the default shell tool for agents that declare
  `Read`, `Grep`, or `Glob`, while keeping those agents in a read-only sandbox.
  This restores local file reading and search for the shipped design,
  desk-research, experience, frontend, and discovery reviewers that do not
  separately declare `Bash`; write and web capabilities remain controlled by
  their own source declarations.
- Kiro IDE and CLI projections now treat an explicit empty agent `resources`
  list as a no-resource opt-out: default skill-resource globs are suppressed and
  the empty consumer field is omitted.

### Added

- Portable no-skill opt-out for agent sources: Claude Code's own `skills: []`
  now suppresses Kiro's default skill-resource injection, so the intent is
  expressed in the portable frontmatter schema rather than in Kiro's
  consumer-native `resources` field. `skills` is admitted to the agent
  frontmatter allowlist; `resources` deliberately is not, because the
  Claude Code agent projection is a byte copy and would carry it verbatim into
  `.claude/agents/`.

### Changed

- **Breaking for Kiro agent sources.** The Kiro IDE and CLI agent projectors now
  bound the field set they emit (`name`, `description`, `model`, `tools`,
  `resources`, and `prompt` on the CLI) instead of passing unmapped source
  frontmatter through verbatim. Any other key — a Claude Code field Kiro cannot
  read such as `permissionMode`, `memory`, or `maxTurns`, or an IDE-only key
  such as `hooks` that makes the CLI loader silently drop the agent — is now
  dropped, with one `kiro: dropping … agent field` line on stderr per key as the
  migration signal. Pack authors who relied on the documented pass-through
  should check their build log.
- A non-empty `skills` list on an agent source is now a hard build failure:
  turning a skill name into a `skill://` URI needs templating the
  frontmatter-mapping grammar cannot express, so the build stops rather than
  emitting an unresolvable resource entry.
## [0.39.3] — 2026-08-23

### Changed

- The bundled workspace-status engine recognizes reviewed legacy work-intake
  migrations, validates durable operation digests, and refuses linked or
  aliased workspace input before projecting exact legacy bytes.

## [0.39.2] — 2026-08-23

### Changed

- Level A packs may declare an optional post-install next action. When present,
  `agentbundle install` prints it after the verification step; Level B packs
  still require one, and packs that omit it keep their existing output.

## [0.39.1] — 2026-08-23

### Changed

- Catalogue seed lint now requires architecture-overview templates to map
  repository areas to responsibilities and change guidance, preventing generic
  example directory trees from passing as adopter-ready context.

## [0.39.0] — 2026-08-21

### Added

- The bundled public-contract inventory now exposes
  `distribution-routes.toml` and its closed schema. The Phase 0 declaration
  names the APM and Claude-plugin package layouts, manifest and marketplace
  projectors, nine-primitive capability maps, admission policies, and lifecycle
  trigger.

### Changed

- Catalogue builds resolve APM and Claude package recipes through explicit,
  schema-validated route identities before writing output. Unsafe or
  inconsistent route declarations fail closed; existing APM and Claude package
  trees remain byte-for-byte unchanged.
- Package-route fields no longer live in the direct-install adapter contract.
  Direct `agentbundle install` behavior, adapter paths, scopes, seeds, and
  marker identity are unchanged.

## [0.38.6] — 2026-08-20

### Fixed

- The bundled profile-authoring instructions now direct catalogue authors to
  the packaged profile schema through a command available in initialized
  catalogues, rather than a repository-only path.

## [0.38.5] — 2026-08-20

### Changed

- The bundled catalogue authoring scaffold's `packs/AGENTS.md` and authoring
  standard state how to write pack tests that survive a shared interpreter:
  load a skill's modules under a name that includes its pack and skill rather
  than putting `scripts/` on `sys.path`, and keep a suite's cost in assertions
  rather than processes. No engine behaviour changed; the package data moves
  because those two repository files are its sources.

### Fixed

- Local-scope install and uninstall reuse each structural `git rev-parse`
  answer for the duration of one command, dropping the cache at the command
  boundary. Measured on the engine unit suite: git child processes fell from
  176 to 59.

- `catalogue init --preset self-hosted` and both archive flavours no longer
  copy a repository-only conformance test into an adopter's catalogue. The
  shipped set is now derived from `tests/conformance/` in one place, so the
  manifest that plain init reads and the directory that self-hosted init copies
  cannot describe different sets.

## [0.38.4] — 2026-08-20

### Changed

- The bundled catalogue authoring scaffold carries restored instruction rules in
  `packs/AGENTS.md` and `profiles/AGENTS.md`. No engine behaviour changed; the
  package data moves because those two repository files are its sources.

## [0.38.3] — 2026-08-19

### Changed

- **The `workspace_status` MCP result now includes safe tracker-refresh
  availability facts.** Callers can read origin mode, active profile, compared
  and accepted revisions, unresolved conflict state, and explicit or unknown
  refresh/write-back availability. The response does not expose field
  ownership, decisions, receipts, or approver identities.

## [0.38.2] — 2026-08-19

### Added

- **Optional journey decision-gate identifiers.** `JOURNEY.md` may list ordered
  `contract.decisionGateIds` from `humanGates[].id`; labels remain reader-facing,
  `yourDecisions` remains required, and existing packs stay valid unedited. This
  shipped after the 0.38.1 tag and reaches PyPI here for the first time.

### Changed

- **Leaner bundled authoring scaffold.** `packs/AGENTS.md` and
  `profiles/AGENTS.md` are shorter and restructured, so `agentbundle catalogue
  init` starts catalogues with leaner instructions. No CLI verb, flag, or output
  format changed.

## [0.38.1] — 2026-08-18

### Fixed

- **The Windows compatibility suite now verifies declared knowledge bundles.**
  It ran the adopter-facing pre-PR hook, which carries no knowledge-bundle gate,
  so no Windows runner invoked the compiler. The suite now re-renders every
  declared bundle and compares the result against the committed tree, so a
  Windows-only encoding, path, or ordering difference fails there rather than
  reaching main. Managed *writes* remain unavailable on Windows by design — they
  require directory-descriptor-confined operations the platform does not offer —
  so the Windows stage verifies committed output rather than producing it.

## [0.38.0] — 2026-08-17

### Added

- **`agentbundle show <pack> --format json` now carries pre-release rich
  catalogue discovery metadata.** Live catalogue responses include three
  additive fields: `pack_metadata` for the pack allowlist, `skill_metadata` for
  live Skill activation metadata, and `knowledge` for declared OKF 0.2 bundles.
  Installed-state fallback preserves the existing inventory-only behavior and
  emits those three fields as `null` because install state cannot prove them.
- **`agentbundle catalogue index` publishes a deterministic, neutral catalogue
  index.** It reads confined catalogue, pack, profile, and optional journey
  metadata; validates the assembled document against the bundled public schema;
  and writes through the package's no-follow atomic writer. Dry-run and
  structured JSON result modes are available for automation.
- **`catalogue-index.schema.json` is now a bundled public contract.** The closed
  schema covers catalogue identity, pack content and execution inventory,
  journeys, declared effects, forward and inverse integrations, profiles, and
  content-addressable pack digests.

### Changed

- **Catalogue journey authoring now has a published convention.** The bundled
  authoring reference defines required and optional frontmatter, external-effect
  declarations, reader-facing body sections, migration guidance, and index
  verification commands. Existing packs without a journey remain valid.

### Unchanged

- The discovery experiment does not add OKF metadata to `list-packs`,
  marketplace output, `catalogue-index.json`, or installed state. Human-readable
  `show` output keeps its existing table contract.
- Release commits for this feature must carry the trailer
  `Engine-Change-RFC: RFC-0087`.

## [0.37.2] — 2026-08-17

### Added

- **`catalogue verify` now performs all 19 advertised checks.** It validates
  profile schemas and references, dependency ranges and cycles, adapter
  compatibility, generated-output drift, pack metadata, and skill evaluation
  manifests. Generated-output comparison is confined to the `claude-plugins/`
  and `apm/` projection roots, and linked inputs are refused before reading.

### Changed

- **Dependency ranges now use one npm-compatible grammar across verify, lint,
  and install.** Caret, tilde, comparator, compound, and prerelease forms agree;
  below `1.0.0`, caret ranges retain normal semver compatibility.
- **Repository-specific leak checks moved out of the portable verifier** and
  into the repository-local build gate.

### Fixed

- **Malformed catalogue configuration now returns a bounded, redacted
  diagnostic.** Verifier help and adopter documentation also consistently
  describe the 19-step pipeline.

## [0.37.1] — 2026-08-16

### Changed

- **New catalogue scaffolds now document the guide callout contract.** The
  bundled authoring standards distinguish exact quoted wording from typed
  Starlight asides and define when to use `note`, `tip`, `caution`, or `danger`.
  Existing catalogues are unchanged until they refresh their scaffolded
  authoring reference.

## [0.37.0] — 2026-08-16

### Changed

- **`install --scope local` now refuses three cases it used to accept.** Local
  scope promises to leave no trace: files are git-invisible via an exclude
  block, and uninstall restores the tree exactly. Each case below is one where
  that promise cannot be kept, so the install stops **before writing anything**.
  All three are `--force`-immune — `--force` cannot make a deletion reversible.

  - **A target already tracked by git.** Writing over it makes the file dirty
    while the exclude block claims it is invisible, and uninstall would delete a
    file the repository owns.
  - **A target that exists, untracked, owned by no agentbundle install.**
    Identical content does not grant ownership: uninstall would delete a file
    this tool never created.
  - **A projected path already owned by a repo-scope pack**, including a
    *different* pack. The existing mutual exclusion only caught the same pack at
    both scopes; two different packs colliding on one path slipped through, and
    the second install silently took ownership of the first's file.

  Reinstalling over files this tool owns is unaffected — the guard keys on
  ownership, not on the file merely existing.

## [0.36.2] — 2026-08-16

### Fixed

- **Security: one planted file could wedge every state-mutating command at
  100% CPU.** A *dangling symlink* at `<state>.lock` made
  `os.open(O_CREAT|O_EXCL)` fail with `FileExistsError` while `Path.stat()`
  followed the link and raised `FileNotFoundError` — and that handler looped
  with neither a deadline check nor a sleep. The timeout therefore never fired:
  confirmed against the shipped package at 98% CPU, still spinning well past a
  2-second budget. Any writable directory holding a state file was enough.

  Four hardening items, ported from the work-loop skill's sibling lock (kept a
  separate module deliberately — the two guard different files for different
  consumers):

  - **Every** retry path now checks the deadline and sleeps.
  - The examine step uses `os.lstat`, which does not follow links, and refuses
    any lock path that is not a regular file. New `StateLockUnusable` (an
    `OSError`, like `StateLockTimeout`) says so immediately rather than waiting
    out a timeout that cannot succeed — waiting cannot make a symlink acquirable,
    and telling an operator to retry would be advice that never works.
  - Release keys on inode identity **and** a per-hold uuid4 token, so a hold
    whose lock was reclaimed mid-body no longer unlinks its *successor's* live
    lockfile on the way out. Inode identity alone is not enough: ext4 and tmpfs
    reuse inode numbers aggressively.
  - A mismatched reclaim restores the displaced file with `os.link` rather than
    `rename`. `rename` silently replaces its destination, so a third process
    that took the momentarily-free path would have its lockfile deleted and two
    holders admitted; `link` fails closed instead.

## [0.36.1] — 2026-08-16

### Fixed

- **Security: a pack can no longer smuggle a file from outside itself onto an
  adopter's disk.** Two independently-safe layers composed into a hole. The six
  direct-directory adapters carried six copies of a symlink policy that had
  drifted into two rules — four dropped every symlink, two dropped only symlinks
  with *absolute* targets and kept relative ones. "Absolute symlinks always
  escape the tree" is true and incomplete: `../../../../etc/passwd` escapes just
  as well and needs no leading slash. A preserved link was then read *through*
  by the install walker, which materialised the target's bytes under a relpath
  that looked entirely innocent.

  Both halves are closed. One policy now lives in
  `build/projections/direct_directory.py` and every adapter uses it, and
  `_collect_tree` skips symlinked entries rather than reading through them.

  **No behaviour change for real packs:** no pack in the catalogue ships a
  symlink, and `lint_packs` rejects any that tries, so the only source of one is
  an untrusted catalogue — which is the case this protects against.

  The build's `.apm` and `seeds` copytrees still pass `symlinks=True`, and that
  stays: preserving a link there is *safe* precisely because nothing reads the
  target at that layer. The defect was the composition, not either layer.
## [0.36.0] — 2026-08-16

### Fixed

- **`catalogue lint` now actually checks pack manifests** — the linter half of
  the fix 0.35.3 made to `catalogue verify`. `_check_plugin_json` and
  `_check_name_version_parity` looked for the manifest at `<pack>/plugin.json`
  while every pack keeps it at `<pack>/.claude-plugin/plugin.json`, so
  CAT-L007 (manifest parses), CAT-L008 (manifest has `name` and `version`) and
  CAT-L009 (`pack.toml` and `plugin.json` agree) had never fired against a real
  pack. All three now read the real path.

  The manifest location is now stated once, in
  `catalogue_tooling/manifest.py`, and imported by both the linter and the
  verifier — the two copies of that path are what let them disagree for as long
  as they did.

  **Upgrading:** three error diagnostics that could never fire are now live, so
  a catalogue that passed `agentbundle catalogue lint` on 0.35.3 may report
  CAT-L007, CAT-L008, or CAT-L009 on 0.36.0. Each points at a real defect. All
  22 packs in this repo's catalogue pass unchanged.

- **The `list-targets` help text named six adapters when there were eight.**
  `agentbundle list-targets --help` omitted `cursor` and `gemini`, and spelled
  the others in a form the verb does not print. The text now matches the
  registry, and a test fails if the two drift apart again.

- **Gate G's release-impact check no longer watches a deleted directory.** Its
  path table listed `docs/contracts/`, removed by ADR-0055, and omitted the
  `contracts/` tree that replaced it. Contract changes still tripped the gate
  through their packaged twins, so nothing escaped in practice — but a contract
  file without a twin (`catalogue.schema.json`, `guide.schema.json`) would
  have.

### Added

- **`catalogue init --format json` now emits `next_steps`.** The self-hosted
  init verb already returned the field; the plain one printed the same guidance
  to the terminal and left it out of the JSON, so an automation consumer got
  next steps from one verb and not the other. Both now carry it, and the
  terminal output is rendered from the same list rather than a second copy.

- The bundled public contract inventory now includes
  `knowledge-captured-observation.schema.json`, the strict producer handoff
  contract used by the core pack's project-knowledge capture flow.

### Changed

- **BREAKING — `render_packs_to_dir()` now requires an `aggregate_scope`
  argument.** It hard-coded `"catalogue"`, so rendering a repo-only subset
  through this helper printed the catalogue's exclusion notices where the
  single-pack helper stays silent. The parameter is required and has no
  default, matching `run_recipe()`: a default is what lets a caller inherit the
  wrong disclosure policy without noticing. Pass `"catalogue"` to keep the old
  behaviour, or `"single-pack"` when rendering a subset. The function had no
  callers in this repository.
## [0.35.3] — 2026-08-15

### Fixed

- **`catalogue verify` now actually checks pack manifests.** Steps 4 and 5
  looked for the manifest at `<pack>/plugin.json`, but every pack — in this
  repo and in a scaffolded catalogue — keeps it at
  `<pack>/.claude-plugin/plugin.json`. The probes missed on every pack and
  skipped it, so CAT-V-004 (manifest parses) and CAT-V-005 (pack.toml and
  plugin.json agree on name and version) had never fired: a `pack.toml` version
  bump without the matching `plugin.json` bump passed verify silently. Both
  steps now read the real path, and a `plugin.json` at the pack root is reported
  as misplaced rather than skipped. A pack with no manifest at all stays clean —
  verify runs against adopter catalogues, and requiring one would fail every
  manifest-less pack.

  **Upgrading:** two error diagnostics that could never fire are now live, so a
  catalogue that passed `agentbundle catalogue verify` on 0.35.2 may report
  CAT-V-004 or CAT-V-005 on 0.35.3. Both point at a real defect — a manifest
  that is misplaced or unparseable, or a `pack.toml` and `plugin.json` that
  disagree on name or version. Released as a patch, not a minor: the next minor
  is reserved for the rest of `spec/catalogue-verifier-correctness` and Wave 4,
  which are pinned to the same number.

## [0.35.2] — 2026-08-14

### Fixed

- **The certificate-setup command in the trust-failure message is now
  copy-pasteable.** It printed a literal `Python 3.x` placeholder, so the one
  audience that sees this message — an adopter whose interpreter trusts nothing —
  had to know to substitute their own version before the command would run. It
  now carries the running interpreter's actual version, and is omitted entirely
  when the script does not exist, so a non-python.org build gets the portable
  `SSL_CERT_FILE` advice instead of a command that would fail.

## [0.35.1] — 2026-08-14

### Fixed

- **Installing on Windows no longer fails with "seeking backwards is not
  allowed".** A catalogue carries symlinks (`CLAUDE.md` → `AGENTS.md`). Windows
  refuses to create them without Developer Mode or the `SeCreateSymbolicLink`
  privilege, so `tarfile` falls back to copying the link target — which means
  re-reading an archive member that the forward-only stream had already passed.
  The archive is now buffered to a seekable temporary file before extraction, so
  the fallback works and the link is materialised as a copy of its target. macOS
  and Linux were never affected, because `os.symlink` succeeds there. Nothing to
  do with certificates, despite arriving in the same reports.

- **An install now recovers when Python trusts no certificate authority at all.**
  A python.org macOS interpreter ships without a configured certificate store:
  until its `Install Certificates.command` runs, it trusts **zero** authorities
  and every HTTPS request fails. 0.35.0 reported this as a probable
  TLS-inspecting proxy, which was misleading — the first field report was not
  intercepted at all — and its fallback could not repair it, because the
  administrator keychain holds private roots and cannot complete a public chain.
  `agentbundle` now detects an empty trust store, names it as its own cause with
  the interpreter-level fix as the first troubleshooting step, and repairs it on
  macOS by reading Apple's root program alongside the administrator keychain.
  With a working trust store nothing changes: Apple's root program stays unread,
  exactly as before.

## [0.35.0] — 2026-08-13

### Added

- **Corporate-network trust for `git+https://` catalogue sources.** On a network
  that inspects TLS, a proxy re-signs HTTPS traffic with a private certificate
  authority your IT team installs in the operating system's trust store. Python
  does not read that store on macOS, so a catalogue fetch failed with
  `CERTIFICATE_VERIFY_FAILED` and nothing actionable to do about it. When
  verification fails, `agentbundle` now retries once against the administrator
  keychain (`/Library/Keychains/System.keychain`) and reports on stderr that it
  did so. Verification stays strict: the retry adds trust anchors, never removes
  one, and no flag or environment variable disables verification. One caveat:
  macOS lets an administrator mark a certificate *Never Trust*, and this
  fallback does not read those markings, so such a certificate is still used as
  an anchor — bounded to a keychain only an administrator can write. Your login
  keychain is never read, because it is writable without administrator rights.
- **`AGENTBUNDLE_NO_SYSTEM_TRUST`** — set to any non-empty value to disable that
  fallback and see the underlying verification error.

Windows needs no fallback: Python already loads the Windows `CA` and `ROOT`
stores and honours each certificate's trust settings. Linux needs none once the
authority is installed in `/etc/ssl/certs`. A WSL distribution does **not**
inherit the Windows certificate store, so install the authority into the
distribution or set `AGENTBUNDLE_CA_BUNDLE`.

### Fixed

- **`AGENTBUNDLE_CA_BUNDLE` now works on `git+https://` sources.** The reference
  documentation described it as covering HTTPS catalogue sources, but only the
  `catalogue+https://` and `archive+https://` paths read it — `git+https://`
  ignored it entirely, so adopters who followed the documentation still could not
  install. `SSL_CERT_FILE`, `SSL_CERT_DIR`, and `REQUESTS_CA_BUNDLE` are honoured
  there too, with `AGENTBUNDLE_CA_BUNDLE` taking precedence, then `SSL_CERT_FILE`,
  then `REQUESTS_CA_BUNDLE`. Note the semantics differ by source form and this is
  now documented: on `git+https://` your bundle is **added** to the default trust
  store, so a bundle holding only a private authority still verifies the
  `github.com` → `codeload.github.com` redirect; on the other two forms it
  **replaces** the store, pinning verification to your own authority.
- **A catalogue fetch can no longer hang indefinitely.** The request carries an
  explicit 30-second timeout, matching the HTTPS catalogue paths, so a proxy that
  accepts the connection and never answers fails instead of stalling.
- **A failed catalogue fetch explains what to do next.** The error previously
  surfaced only the raw OpenSSL string; it now names the probable cause and gives
  ordered troubleshooting steps, including that different Python interpreters do
  not share a certificate store — and that creating a virtualenv does not change
  trust, since a virtualenv inherits its base interpreter's store unchanged.

### Changed

- **Setting `AGENTBUNDLE_CA_BUNDLE` to a path that does not exist now fails a
  `git+https://` install that previously succeeded.** The variable was ignored on
  that path before, so a fleet-wide export pointing at a file absent on this host
  was harmless. Unset it, or correct the path.

## [0.34.0] — 2026-08-12

### Added

- `agentbundle catalogue contracts list`, `show`, and `export` expose the exact
  public contracts bundled with the running AgentBundle version without network
  access. Exported files are reference copies and cannot override runtime
  validation contracts.
- Successful plain `catalogue init` output now points adopters to the scaffolded
  authoring standards guide, bundled-contract discovery, and catalogue
  verification. The JSON result schema is unchanged.

### Changed

- The scaffolded authoring standards reference now documents offline bundled
  contract inspection and the read/write boundary of each command.

## [0.33.3] — 2026-08-12

### Changed

- The Windows compatibility command now owns AgentBundle and pack portability
  checks. This repository runs CredBroker's package suite in a separate,
  parallel Windows CI job; the existing aggregate check remains blocking on
  both suites.

### Fixed

- `catalogue self-host --write` now updates writable existing seed and adapter
  files in place without attempting owner-only timestamp or mode changes. This
  supports checkouts whose files are owned by a different user while preserving
  their inode, ownership, and mode; modification time advances naturally when
  content changes, and `--check` still reports mode drift that the writer cannot
  repair. Safe rollback is bounded to projected files no larger than 64 MiB;
  write-only files retain content-write compatibility but cannot be restored if
  their write fails after truncation.

## [0.33.2] — 2026-08-12

### Fixed

- **Workspace MCP status now consumes canonical routing eligibility.** Ready
  work is limited to dispatchable canonical queue specs, blocked entries carry
  stable findings, and malformed workspace state fails closed without leaking
  raw exception text or absolute paths. Trusted-mode package installs retain a
  byte-identical engine fallback when no repository projection is available.

## [0.33.1] — 2026-08-12

### Fixed

- The self-host classifier now recognizes the repository-owned top-level
  `tests/` tree, so catalogue verification no longer reports conformance,
  roster, or fixture paths as unclassified.

## [0.33.0] — 2026-08-11

### Changed

- **BREAKING — local catalogue sources now require a root `catalogue.toml`
  and literal root `packs/` directory.** The former `packs/` plus
  `.claude-plugin/marketplace.json` identity is no longer accepted. Add a valid
  `catalogue.toml` before upgrading; installable archive layouts are unchanged.
- `catalogue lint` and `catalogue verify` now reject source roots without
  `catalogue.toml`. A Claude marketplace is required only when the effective
  self-host adapters include `claude-code`, so Kiro-only catalogues may omit
  Claude-specific project artifacts.

## [0.32.0] — 2026-08-10

### Added

- **Claude-plugin installs now compile safe pack-authored command hooks into
  native plugin hooks.** Hook bodies project under the plugin root, the
  synthetic install marker remains first, and marketplace descriptions disclose
  each authored event, matcher, timeout, interpreter, and body path before
  installation.

### Changed

- **Claude-shaped hook wiring is validated at pack ingress.** Publication is
  limited to a pinned event set, four interpreters, exact two-token commands,
  confined regular hook-body files, bounded timeouts and fan-out, and literal
  matcher alternations. Direct-route output for valid wiring is unchanged.
- The adapter contract is now **v0.18**, adding the Claude-plugin-specific
  hook-body target and hook-wiring projection mode.

## [0.31.1] — 2026-08-10

### Added

- **Catalogue conformance tests now ship with every scaffolded or packaged
  catalogue.** The portable rule suite is separate from this repository's
  roster assertions and is materialised by both bare and self-hosted init.

### Fixed

- **The complete, self-contained engine test suite is restored to the source
  distribution.** The release gate now validates tar members before extraction,
  then collects and executes the extracted suite with dependency and skip
  integrity checks. Wheels, zipapps, and vendored engines remain test-free.

## [0.31.0] — 2026-08-10

### Changed

- **BREAKING — `build.main.run_recipe` requires `aggregate_scope`.** It is
  keyword-only with no default, so an out-of-repo caller gets a `TypeError` at
  call time rather than silently inheriting catalogue semantics. Whether a
  pack skipped on the plugin route is announced depends on which mode ran — a
  catalogue build names every exclusion, a single-pack render stays silent so
  a successful `agentbundle install --pack <repo-only>` does not print a route
  refusal — and that is the caller's fact, not something the recipe can infer.
- **BREAKING — `agentbundle build --recipe marketplace --pack <X>` exits 1.**
  Aggregate recipes read the whole dist tree, so a pack filter on one was
  always meaningless; it previously succeeded and produced a marketplace whose
  contents ignored the flag.
- **BREAKING — the Claude-plugin route now publishes only packs that permit a
  user-scope install.** A Claude plugin's code lives in the adopter's global
  cache and `claude plugin install` defaults to `--scope user`, so a pack
  declaring `[pack.install] allowed-scopes = ["repo"]` was being offered an
  install its own declaration forbids. Six packs leave the marketplace: `core`,
  `governance-extras`, `iac-terraform`, `monorepo-extras`,
  `release-engineering`, `user-guide-diataxis`. `catalogue-curation` makes
  seven: it was already excluded from the published branch, but was still
  listed at the repo root, and that entry goes too.

  **If you installed any of them as a plugin**, uninstall first —
  `claude plugin uninstall <pack>@agent-ready-repo` — then install at repo
  scope with `agentbundle install --pack <name> …`.

  Observed against Claude Code 2.1.223, **after a marketplace refresh**: a
  delisted plugin reports `Status: ✘ failed to load` in `claude plugin list`,
  and `claude plugin update` refuses it. Until your client refreshes
  (`claude plugin marketplace update <marketplace>`), the cached copy keeps
  loading and its hooks keep running — so uninstall rather than wait for the
  refresh. The enablement entry survives until you do, and uninstalling also
  avoids two unrelated copies of the pack's skills once you reinstall at repo
  scope.

- **An existing dist-tree install of a repo-only pack leaves an orphaned
  `claude-plugins/<pack>/` tree.** The filter sits in `render_pack`, so
  `--emit-install-routes` no longer writes that subtree. Verified by running a
  real upgrade — both a re-apply and a genuine version bump — the previously
  installed files are **not** deleted: they stay on disk and stay listed in
  `.agentbundle-state.toml`, because `upgrade` adds rendered relpaths to state
  and never prunes ones the render dropped. Nothing breaks; you are left with a
  directory nothing maintains. Remove it by hand if you want it gone.

- **A catalogue whose packs declare different `[pack.links] repository` values
  now fails the build.** The marketplace envelope's `name` and `owner` were
  derived from the *first* surviving entry's `source.url`, so a filtered set
  could silently re-key the marketplace to whichever pack sorted first. Every
  surviving entry must now agree, and disagreement exits non-zero naming both
  identities. Remedy: align `[pack.links] repository` across your packs.

- **Engine behaviour change for self-hosting adopters.** The same predicate
  applies on `run_self_host`, so a pack in *your* catalogue that resolves
  repo-only no longer appears in the `.claude-plugin/marketplace.json` your
  build writes. The resolver gates on `[pack.adapter-contract].version`, not
  `[pack.install]` — a pack declaring `allowed-scopes` with no contract version
  resolves `["repo"]` and will be filtered. Each exclusion prints a named line.
  A catalogue whose packs are *all* repo-scoped writes an empty marketplace and
  warns — that is a valid state, not a defect, and your build still succeeds.

## [0.30.1] — 2026-08-09

### Fixed

- **`catalogue verify` no longer reports this repository's owned source and
  documentation as unclassified.** The self-host classifier now recognizes
  the repository's package, profile, site, documentation, and root-config
  ownership boundaries while preserving informational notices for genuinely
  unknown paths. Git filenames are read losslessly with NUL delimiters.
- **Special `.agentbundle/` projections now participate in every self-host
  dry-run.** Generated broker executables and the vendored `credbroker` floor
  are classified from their projection enumerators and drift makes catalogue
  verifier step 15 fail. Executable drift checks no longer follow target
  symlinks and now enforce the projected `0o755` POSIX mode. Both special rails
  replace rejected target symlinks with held-directory atomic writes during
  regeneration without modifying their referents, even under a concurrent
  leaf swap; ancestor, read, and orphan operations are no-follow as well.

## [0.30.0] — 2026-08-08

### Changed

- **The wheel no longer ships the engine's test suite.** It carried 45 test
  entries of 184; the wheel is now roughly a fifth smaller compressed, a quarter
  uncompressed. The tests moved out of the importable package to
  `packages/agentbundle/tests/build_pipeline/` — the package itself did not
  move, and every import path except one is unchanged.

  The mechanism was not what it looked like: `[tool.setuptools.packages.find]`
  defaults to `namespaces = true`, so the tree was discovered as a PEP 420
  namespace package regardless of its `__init__.py`. Deleting that marker would
  have removed exactly one entry of the forty-five.

- **`ALLOW_FIXTURE_PACKS` now requires an explicit `1`, `true`, or `yes`.**
  It previously bypassed the self-host fixture guard on *any* non-empty
  value, so `ALLOW_FIXTURE_PACKS=0` disarmed a destructive-write control
  while reading as "off" — and stayed disarmed for every later invocation
  in that shell or CI job. If you set it to anything else, the guard now
  refuses.

### Removed

- **The source distribution no longer carries the build-pipeline test suite.**
  0.29.8's sdist held 45 of them; 0.30.0 holds none. They sat inside the
  importable package, so setuptools swept them in; from their new home they
  need an explicit `MANIFEST.in` graft, which lands with the catalogue
  carve-out. Eight top-level `tests/test*.py` modules still ship — the default
  sdist glob reaches those — and they do run (20 passed, 47 skipped from an
  installed sdist), without `tests/conftest.py`'s autouse
  `HOME`/`XDG_CONFIG_HOME` isolation. That last part is not new: a
  `tests/test*.py` glob never matched `conftest.py`, so 0.29.8's sdist
  shipped those eight the same way. What this release removes is the
  build-pipeline suite. Build from a git checkout until the graft ships.

- **`import agentbundle.build.tests` no longer resolves.** Nothing in this
  package or its consumers imported it; the module existed only to make the
  directory a package.

### Fixed

- **`build self --packs-dir <a fixture tree>` refuses again.** The
  destructive-write guard tested whether `"tests/fixtures/"` appeared in the
  path as a substring. With the suite relocated those two segments are no longer
  adjacent, so the guard failed *open* — the command would have overwritten a
  working tree with fixture data. It now refuses on path components **or** the
  original substring, so it refuses strictly more than before: the relocated
  `tests/build_pipeline/fixtures/` shape is caught, and adjacent forms like
  `mytests/fixtures/` keep the refusal they had. `my-tests/fixtures-backup/` is
  still allowed through, which is what the original trailing slash protected.

- **`agentbundle catalogue self-host --write` now refuses a fixture packs
  path too.** That entry point takes its packs directory from
  `[catalogue.paths] packs` rather than a flag, and was never guarded — a
  catalogue pointing at a `tests/.../fixtures/` tree performed the same
  destructive overwrite. It now exits non-zero with a `CAT-SH-001`
  diagnostic, visible under `--format json`. This is a **new** refusal, not
  a restored one.

- **`catalogue init --preset self-hosted --tooling vendored` no longer copies
  test content into an adopter's tree.** The vendored copy is an install source
  — the command tells you to `pip install -e` it — so it is treated like the
  wheel. The adopter's own packs and shared guides keep their tests, which is
  what catalogue archives are for.

## [0.29.8] — 2026-08-07

### Fixed

- **Packs installed with `claude plugin install` now complete their install.**
  The bundled install-marker script decided whether you had opted a pack in by
  reading `enabledPlugins` from your Claude Code settings, and expected a JSON
  array. Current clients write an object keyed by `name@marketplace` — so the
  script read every settings file as "not opted in", wrote no marker, and exited
  quietly. Two things silently did nothing as a result: the hand-off that offers
  to adapt a freshly installed pack to your repository, and the `allowed-scopes`
  check that refuses to install a repo-only pack at user scope. Both work now.
  The array form older clients wrote is still accepted.

- **A pack of the same name from another marketplace no longer counts as this
  one.** The identifier match compared only the part before the `@`, so
  `core@some-other-marketplace` in your settings satisfied a check for our
  `core`. Qualified identifiers now have to agree on the marketplace too.

- **A hostile or oversized settings file can no longer hang or crash the
  script.** The 1 MiB limit is applied to the read itself rather than measured
  after the whole file is in memory, non-regular paths (a FIFO, a symlink to a
  device) are refused rather than opened, and undecodable bytes fall through as
  "not opted in" instead of raising.

## [0.29.7] — 2026-08-06

### Changed

- **The scaffold's `packs/AGENTS.md` no longer cites paths it does not ship.**
  `catalogue init` writes this file into your repository, where six of its
  references pointed at files that exist only in the upstream catalogue — a
  test-boundary rule attributed to a linter you were never given, a shape
  document you cannot open, two JSON Schemas by repository path rather than by
  the `agentbundle catalogue lint` that validates against them, and two links to
  an authoring guide outside the shipped guide set. Each rule now stands on its
  own or points at `guides/_shared/reference/catalogue-authoring-standards.md`,
  which the scaffold does ship. A new projection assertion walks every path the
  shipped copy cites and fails when one is missing, so the class cannot recur.

- `catalogue self-host --check --windows` runs the atlassian pack's
  `test_check_sso_login.py` in the existing jira step rather than a second
  process for the same skill directory.

## [0.29.6] — 2026-08-06

### Fixed

- **Marketplace entries emit a resolvable plugin source.**
  `derive_projectable_subset` produced a `github` source carrying `branch` and
  `directory`; Claude Code's `github` source supports neither, so both were
  silently dropped and the installer cloned the repository's default branch at
  its root — every published plugin installed empty. Entries now emit a
  `git-subdir` source (`url`, `path`, and one of `ref`/`sha`). The GitHub URL
  matcher is HTTPS-only and raises on an `http://` repository link rather than
  upgrading it silently. The dist marketplace envelope now derives its
  `name`/`owner` from `source.url`, since `git-subdir` carries no `repo`.

- **Claude-plugin components project to the plugin root.** The claude-plugins
  route emitted `<pack>/.claude/{skills,agents,commands}`, but plugins load
  those directories from the plugin root. A route-scoped `plugin-target-path`
  on the claude-code projection entries moves them for that recipe only; the
  repo- and user-scope install routes are unchanged. Hook wiring stays at
  `.claude/settings.local.json`.

- **`catalogue verify` validates marketplace entries.** Step 13 previously
  checked `marketplace.json` for a stray `hooks` key and nothing else — a
  plugin `source` reached adopters unvalidated. It now validates every
  `plugins[]` entry in both the dist and repo-root marketplaces against the new
  bundled `marketplace-entry.schema.json`, and fails closed with a diagnostic
  when a schema cannot be resolved instead of silently skipping the step.

- **Contract `target-path` values are confined.** An absolute or `..`-bearing
  `target-path` escaped the output root on join, and the orphan sweep resolves
  the same value — so an escaped target became the root of a `rmtree`. The
  adapter now canonicalises and prefix-checks before writing.

### Added

- `marketplace-entry.schema.json` ships in the wheel alongside the other
  bundled contracts.

## [0.29.5] - 2026-08-06

### Changed

- `catalogue self-host --windows` runs the atlassian SSO suites from the packs'
  test trees rather than the skills' `scripts/` directories, and probes
  `credbroker` and `httpx` before doing so. Both suites `importorskip` at module
  scope and the step runner judges by return code alone, so without the probe a
  machine missing either dependency skipped both suites and reported pass.
- Three suites whose subject was pack content left the package's own test tree
  for the owning pack: the desk-research retriever-conformance and
  project-start elicitation checks, and the credential-setup skill-body check.
  A pack edit could otherwise turn the published package's suite red. Engine
  tests that use a pack as fixture data are unaffected — the distinction is
  subject, not mention.

### Fixed

- **`catalogue package` no longer puts build residue in the archive.** Both
  flavours walk `packs/**` recursively, and the deny-set that was meant to stop
  this was referenced nowhere — so `__pycache__` from any `pytest` run, and
  `node_modules` from any `npm install` in a skill that ships a `package.json`,
  were collected verbatim. On this repository that is 104 files. The walks now
  prune `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`,
  `node_modules`, `.venv`, `venv` and `htmlcov` at every level, plus stray
  `.pyc`/`.pyo`, `.DS_Store` and `.coverage` files.

  Validation was fixed alongside collection. The symlink check walked the same
  trees and refused the first symlink anywhere, and a real `node_modules/.bin/`
  is entirely symlinks — so pruning collection alone would have left
  `catalogue package` aborting on exactly the tree it was meant to handle. The
  pack-discovery step no longer treats a `packs/__pycache__/` as a pack either.

  The old set could not simply be applied: it also listed `.git`, `tools`,
  `packages` and `dist`, which are *repository-root* names already excluded by
  the include allowlist. Pruning those at every level would have dropped real
  content — `packs/monorepo-extras/seeds/packages/` is exactly that case, and
  there is a regression test for it.

No flag, verb, exit code, or schema changed. Archive *contents* do change: an
archive built from a tree that has been tested or npm-installed is now smaller,
and matches what `catalogue-authoring-standards.md` § 4 has always told adopters
it contains.

## [0.29.4] — 2026-08-06

### Changed

- **Pack-content tests no longer live in this package's test tree.** Every
  suite whose *subject* was pack content — core's hook bodies, skill bodies and
  `work-loop` scripts, plus the `product-documentation` pack check — moved to
  the owning pack's `tests/` tree. They were never testing `agentbundle`;
  they were testing pack content that happens to sit in the same repository, so
  renaming a private helper in the core pack could turn this package's suite
  red. `packages/agentbundle/tests/` is now catalogue-level only: the engine,
  the CLI, projection, packaging, and schema. Tests that *use* a pack as fixture
  data — install, upgrade, projection, adapter parity — are unaffected and stay;
  the distinction is subject, not mention.
- **`self_host_windows.py`** points the hook parity-net step at
  `packs/core/tests/hooks/` and runs it from the repo root rather than the
  package directory.
- **`README-pypi.md`** documents the pack layout's `tests/` tree and the
  three boundaries — pack owns tests, `.apm/` is the runtime export boundary,
  a skill owns its eval fixtures.

No flag, verb, exit code, schema, or output changed. The installed runtime
surface is identical; only where this repository keeps its tests moved.

## [0.29.3] — 2026-08-05

### Changed

- Wording-only release: internal governance citations removed from every shipped
  surface (`--help` output, runtime diagnostics, source comments). No flag, verb,
  exit code, schema, or output structure changed. See the repo changelog for the
  full breakdown.

## [0.29.2] — 2026-08-05

### Fixed

- **`self_host` — preferred-adapter respected**: `run_self_host` now restricts
  projection to the adapter named in `catalogue.toml`'s `preferred-adapter` field
  when that adapter is not in `SELF_HOST_ADAPTERS` (e.g. `kiro-ide`). Previously
  only `claude-code` and `codex` were ever projected, producing false drift for
  downstream repos using a different adapter.

- **`self_host` — Claude-specific artifacts omitted for non-claude-code repos**:
  `CLAUDE.md` and `.claude-plugin/marketplace.json` are no longer written (or
  drift-checked) when the effective adapter set does not include `claude-code`.
  Downstream repos with `preferred-adapter = "kiro-ide"` (or any adapter not in
  `SELF_HOST_ADAPTERS`) no longer accumulate Claude-specific files.

- **`self_host` — shadow-clone and seed-copy paths use `shutil.copy`**: neither
  calls `os.utime`, fixing CI environments that restrict timestamp writes.
  `shutil.copy` (content + permissions, no timestamps) preserves source mode bits
  so the drift gate never false-positives on permission bits in strict-umask CI.

- **`adapter_root_bins` — `shutil.copy2` replaced with `shutil.copyfile` +
  `os.chmod` guarded with `contextlib.suppress(OSError)`**: the bin-projection
  path no longer calls `os.utime`; POSIX executable-bit setting is now
  best-effort so environments that restrict `chmod` do not abort the build.

## [0.29.1]

### Fixed

- **`workspace_mcp._GitTools` — FSM mode guard**: `git_branch`, `git_commit`, and
  `git_push` are now blocked whenever `WORKSPACE_MCP_SPEC_PATH` is supplied —
  including when `WORKSPACE_MCP_DISPATCHED_ITEM` is also present (both-vars
  configuration, unsupported; SPEC_PATH wins with a startup warning), and when
  the path fails `repo_root` containment validation (fail-closed: raw env var
  presence in `os.environ` — including an empty string — is the FSM trigger, not
  the post-validation value). Previously, a stale harness supplying both vars, or
  an invalid SPEC_PATH, left `_fsm_mode=False`, enabling git writes during a
  work-loop session. A new `_fsm_mode` flag drives the guard.

- **`workspace_mcp._build_tools_list`** — refined git tool descriptions for
  harness clarity. `git_status`, `git_branch`, `git_commit`, and `git_push` open
  with "Use this instead of running 'git X' directly" and name the specific bypass
  risk each guard prevents. `git_commit` description states that pre-staged files
  outside the output paths cause a hard refusal; unstaged files are silently
  excluded. `git_push` description clarifies that a resumed dispatched session may
  inherit a pre-locked branch (no `git_branch()` call required). `git_branch`
  example updated to a non-FSM type (`shape`); added note that the tool is
  unavailable in FSM/work-loop sessions.

- **`workspace_status` tool description**: added `available`, `required_pack`, and
  `unmet_needs` eligibility fields so agents know not to dispatch items where
  `available: false` or `unmet_needs` is non-empty.

- **`README-pypi.md`**: marked `python3 -m agentbundle.workspace_mcp` as
  trusted-checkout-only; noted Stage 2 isolated spawn mode (`python3 -I -m ...`).

## [0.28.1]

### Fixed

- **`workspace_mcp._build_tools_list`**: rewrote all six tool descriptions and added
  `description` fields to every parameter schema — descriptions previously used
  internal jargon ("DAG-resolved", "FSM state", "control plane", "output_pattern",
  "session-bound") with no parameter docs; now self-contained for harness authors
  who have not read the design doc. `workspace_status` description names every
  response field. `elicit` documents all three parameters and the return shape.
  `git_branch`, `git_commit`, and `git_push` document constraints (once-per-session,
  discovery-mode unavailability, work-loop ownership) inline.

## [0.28.0]

Engine-Change-RFC: RFC-0078

### Added

- **`agentbundle.workspace_mcp`**: new per-session MCP server (Stage 1, RFC-0078).
  Provides `workspace_status`, `elicit`, `git_status`, `git_branch`, `git_commit`,
  and `git_push` tools over MCP stdio. Entry point: `python3 -m agentbundle.workspace_mcp`.
  - `_LIFECYCLE_MANIFEST`: embedded 7-type lifecycle metadata (`work`, `research`, `shape`,
    `design`, `strategy`, `signal`, `brief`) with dispatch skill, output pattern, gate flag,
    and required pack per type.
  - `DEFAULT_SESSION_INSTRUCTION`: 6-rule session instruction constant readable at
    `agentbundle.workspace_mcp.DEFAULT_SESSION_INSTRUCTION`.
  - `_EventBridge`: daemon thread; 200 ms poll of `.loop-run/events.jsonl`; byte-offset +
    inode tracking; seq deduplication; HUMAN-GATE state detection.
  - `_WorkspaceStatusTool`: calls `analyze_bounded(autonomous_dispatch=True)`; pack-presence
    filter (6 roots); slug safety guard (`_SAFE_SLUG_RE`); FSM state fields merged from
    `_EventBridge` (spike (c) poll-based fallback).
  - `_ElicitTool`: `elicitation/create` path + response-file fallback (O_EXCL 0600, 300 s
    poll); never advertises `elicitation` in `ServerCapabilities`.
  - `_GitTools`: `git_branch` (check-ref-format); `git_commit` (output_pattern intersection;
    `--` separator); `git_push` (two-sided branch check); discovery-mode guard.
  - 1 MiB frame-size cap; malformed JSON and unknown request_id discarded without
    dropping the connection.

- **`workspace_status_engine.analyze_bounded`**: `autonomous_dispatch: bool = False` parameter
  propagated through `classify_entries` → `is_need_satisfied`. When `True`, `shape:` absent
  from both active and backlog is unsatisfied; `research:` absent from backlog as type
  `"research"` is unsatisfied. Default `False` preserves existing human-session semantics.

- **`loop-engine` events.jsonl outbox protocol**: `cmd_init` creates `.loop-run/` + empty
  `events.jsonl` + `.gitignore` entry; `cmd_transition` writes `events.pending` → atomically
  writes `engine-state.json` → appends `events.jsonl` → deletes pending (graceful degradation).
  `_recover_pending()` replays or discards stale `events.pending` at init and transition.

- **Core-pack alias script**: `workspace_mcp_server.py` one-line delegation in
  `packs/core/.apm/skills/workspace-status/scripts/` projected to `.agents/` and `.claude/`.

### Fixed (post-review)

- **`_WorkspaceStatusTool`**: `entry.path` (format `"spec/<slug>"`) changed to `entry.slug`
  in ready/blocked work-queue slug check — prevents all work items being silently dropped
  because `_SAFE_SLUG_RE` rejects the `/` in the path prefix.
- **`_ElicitTool._call_via_elicitation`**: removed redundant `with self._write_lock:` wrapper
  (deadlock — `_write` acquires the same non-reentrant lock internally; CWE-833).
- **`_ElicitTool._call_via_elicitation`**: bounded `_ELICIT_POLL_TIMEOUT` (300 s) wait
  prevents a client that never responds from holding the thread indefinitely.
- **`_GitTools`**: added `self._git_lock = threading.Lock()` to serialize all mutating git
  calls; prevents `index.lock` collisions and TOCTOU races on `_session_branch`.
- **`_GitTools._resolve_output_pattern`**: `ini_slug` and `slug` from
  `WORKSPACE_MCP_DISPATCHED_ITEM` validated via `_is_safe_slug` — defense in depth against
  a crafted env var widening the commit output_pattern.
- **`_read_frame`**: frame-size cap now counts encoded UTF-8 bytes (`len(ch.encode("utf-8"))`)
  not characters — 1 MiB multi-byte characters previously undercounted.
- **Stub tests** (`test_workspace_mcp_*.py`, `test_loop_engine_events_jsonl.py`,
  `test_workspace_status_engine_autonomous.py`, `test_adapter_permissions_projection.py`):
  converted from `assert False  # STUB:` to `pytest.skip("STUB: ...")` — stubs are now
  skipped (exit 0) rather than failing. `B011` removed from `pyproject.toml` per-file-ignores.

AC17/AC18 (`permissions.allow` projection) are deferred to
`(deferred: workspace-mcp-permissions-projection-contract)` — a follow-on RFC will add
the adapter contract mode for additive array merging.

## [0.27.3]

### Changed

- **Scaffold sync**: `packs/AGENTS.md` updated to record `tomlkit==0.15.1` as an optional
  dependency of the `workspace-status` skill; `_data/catalogue-scaffold/` projection synced.

## [0.27.2]

### Fixed

- **Self-host orphan sweep deleting externally installed skills** (`build/adapters/claude_code.py`,
  `build/adapters/kiro.py`, `build/adapters/codex.py`): `catalogue self-host --write` (and
  `--force`) now preserves skill directories that are recorded in `.agentbundle-state.toml` —
  i.e. skills installed by `agentbundle install` from an external catalogue. Previously,
  `_sweep_skill_orphans` built its `expected_names` set solely from the packs passed to
  `project_packs`; any skill whose name was not in that set was silently deleted with
  `shutil.rmtree`. The fix reads the repo-root state file and adds every skill-directory name
  it finds there to `expected_names` before the sweep runs. Absent, legacy-schema, or
  malformed state files degrade gracefully to the pre-fix behavior (empty protection set;
  no error). All three adapters (claude_code, kiro, codex) are fixed with the same
  `_installed_skill_names` helper. Also copies `.agentbundle-state.toml` into
  the shadow tree in `_clone_target_subtree` (`build/self_host.py`) so that
  `--check` / dry-run produces consistent results with `--write` (without this,
  the sweep deleted installed skills from the shadow and reported false drift).

## [0.27.1]

### Added

- **workspace-status projection tests** (`build/tests/test_workspace_status_projection.py`):
  - `SourceInvariantTests`: verifies both CLI and engine scripts exist in the pack source.
  - `AdapterProjectionTests`: exercises all shipped adapters via subTest loop; uses rglob
    for adapter-agnostic scripts/ discovery (AC9).
  - `RealTreeProjectionTests`: asserts both scripts present in the self-hosted projection.
  - `EndToEndCLITests`: installed CLI exits 0, emits `schema_version: 1` against real repo.

## [0.26.0]

### Added

- **Self-hosted init — Phase 2 deferred ACs** (`catalogue_tooling/initialise_self_hosted.py`):
  - `SelfHostedSource` dataclass (name, display_name, release, archive_uri, sha256, revision);
    `resolve_source()` validates source for the requested tooling mode.
  - Vendored mode now refuses a source missing `packages/agentbundle/` with a clear
    diagnostic (B3 AC3).
  - Identity transform applied in-memory before writing; leak check runs in a tmpdir
    so no files are written on violation (B5).
  - Reuses `classify_conflicts`, `atomic_write`, `commit_files`, `rollback` from
    `initialise.py`; owned files (from prior run) overwrite without conflict (B5).
  - Vendored mode writes `[catalogue.tooling]` section (pack-roots, self-host-packs,
    adapters) to the generated `catalogue.toml` (B6).
  - Source containing `packs/catalogue-curation/.apm/skills/export-catalogue/` is
    refused with a diagnostic (B7 AC5).
  - External mode `next_steps` emits one `agentbundle install catalogue-curation` command
    per adapter (B7 AC2 — library-level planning, no subprocess).
  - `SelfHostOwnershipState` bumped to schema version 2: per-path sha256, adapter list,
    managed_target_path, source_pack_identity, source_root_kind (B9).
  - Re-run removes stale owned paths with sha256 guard (skip user-modified files) and
    path confinement (B9 AC2/3).
  - `SelfHostedInitResult.to_dict()` extended with preset, tooling_mode, attribution_mode,
    selected_packs, selected_profiles, selected_adapters, field_collection_mode,
    identity_replacements, leak_scan_result (B12).
- **Source manifest in tar** (`catalogue_tooling/package.py`): `self-hosted-source-manifest.json`
  is now included as a tar member (in addition to the sidecar), plus `packs` inventory and
  `archive_generation_policy_version: "1"` fields (B4 AC).
- **Source archive install refusal** (`catalogue_tooling/archive.py`, `commands/install.py`):
  `verify_archive()` and the `agentbundle install` resolution path both refuse archives
  whose members include `self-hosted-source-manifest.json` with a clear "wrong kind"
  diagnostic (B4 AC6 / B4 AC; install path Blocker fix).
- Public aliases `atomic_write`, `commit_files`, `rollback` added to
  `catalogue_tooling/initialise.py` for use by sibling modules.

### Changed

- `SelfHostOwnershipState.schema_version` promoted from `"1"` to `"2"`; migration from
  schema-1 state files is handled transparently (sha256=None entries skipped on removal).
- Vendored mode source validation is now a hard failure (`ok=False`) when
  `packages/agentbundle/` is absent, rather than a soft diagnostic.

## [0.25.0]

### Added

- **`agentbundle catalogue init --preset self-hosted`**: new enterprise-derived
  catalogue initialization. Accepts `--source`, `--tooling external|vendored`,
  `--attribution white-label|attributed`, `--guides none|selected`, `--pack` (repeatable),
  `--adapter` (repeatable), `--profile` (repeatable), `--repository-url`, `--owner-email`.
  Copies selected packs, profiles, and guides from a source catalogue; generates a new
  `catalogue.toml` with target identity; runs a fail-closed leak check using
  `identity.verify()`. Vendored mode copies agentbundle source and catalogue-curation
  into `.agentbundle/tooling/` for air-gapped deployments. Writes
  `.agentbundle/self-host-state.json` to track managed files.
  (`commands/catalogue_init.py`, `catalogue_tooling/initialise_self_hosted.py`,
  `catalogue_tooling/identity.py`)
- **`agentbundle catalogue package --flavor source`**: new source-distribution flavor
  for self-hosted catalogues. Produces a `catalogue-source-<release>.tar.gz` from a
  positive allowlist (catalogue.toml, packs/, profiles/, guides/_shared/,
  .claude-plugin/marketplace.json, legal files). Emits a `self-hosted-source-manifest.json`
  with `kind = agentbundle-self-hosted-source`, per-file SHA-256 digests, and provenance
  fields.
  (`commands/catalogue_package.py`, `catalogue_tooling/package.py`)
- **`catalogue_tooling.identity`**: new module migrated from
  `catalogue-curation/export-catalogue` scripts. Public API:
  `verify(target, anchors, *, mode, attribution_paths)` and
  `check_ci_boundary(target)`. Used by the self-hosted init engine.
  (`catalogue_tooling/identity.py`)

### Changed

- **`catalogue-curation` pack 0.2.0**: removed `export-catalogue` skill (superseded by
  `agentbundle catalogue init --preset self-hosted`). Removed hard dependencies on
  `core` and `governance-extras` — the pack's three skills now operate portably against
  the target catalogue's own contracts.

## [0.24.0]

### Added

- **`agentbundle catalogue init [TARGET]`**: new subcommand that scaffolds a
  plain AgentBundle catalogue directory. Writes `catalogue.toml`, an empty
  `.claude-plugin/marketplace.json`, the full pack/profile authoring scaffold
  (README, AGENTS, `_example/` templates), and the CI contract reference guide.
  Additive and idempotent — never overwrites existing files. Dry-run mode
  (`--dry-run`) shows the plan without touching the filesystem. All flags:
  `--name`, `--display-name`, `--description`, `--owner-name`,
  `--preferred-adapter`, `--dry-run`, `--format`.
  (`cli.py`, `commands/catalogue_init.py`, `catalogue_tooling/initialise.py`,
  `catalogue_tooling/toml_emit.py`)
- **`catalogue.toml` schema v1 relaxations**: `catalogue.paths.contracts`,
  `distribution.agentbundle.install-defaults-output`, and
  `distribution.agentbundle.default-source` are now optional. Catalogues
  without these fields are valid. Existing catalogues that have them are
  unchanged. (`_data/catalogue.schema.json`, `catalogue_tooling/config.py`)
- **`[catalogue.owner]` table**: new optional TOML table with a required `name`
  field. Loaded into `CatalogueConfig.owner` as `CatalogueOwner`. Absent when
  the key is not in `catalogue.toml`. (`catalogue_tooling/config.py`,
  `catalogue_tooling/results.py`)
- **Scaffold path-safety API** (`scaffold.py`): `validate_manifest_paths()`,
  `list_files_with_hashes()`, `verify_hashes_detailed()`, `find_unexpected_files()`
  — extended public API for the init engine.
- **`sync-defaults` no-op guard**: when
  `distribution.agentbundle.install-defaults-output` is absent, `check_defaults()`
  and `write_defaults()` return `ok=True` with an INFO diagnostic instead of
  failing. (`catalogue_tooling/defaults.py`)
- **Catalogue CI contract guide in scaffold**: `guides/_shared/reference/catalogue-ci-contract.md`
  is now included in the bundled scaffold and copied by `catalogue init`.
- **How-to guide**: `guides/_shared/how-to/create-a-catalogue.md`.

### Changed

- **`_build_archive` → `_write_archive`** (`catalogue_tooling/package.py`): the archive builder
  now streams the compressed output directly to the staged file on disk instead of
  materialising the full content in an `io.BytesIO` buffer first. The SHA-256 is then computed
  over the smaller compressed file. All determinism guarantees are preserved (sorted members,
  normalised metadata, zeroed gzip mtime, `GNU_FORMAT`). No change to archive contents, sidecar,
  or channel descriptor.

### Added

- **`agentbundle catalogue self-host --check --windows`**: new `--windows` flag on the `self-host` subcommand. When combined with `--check`, runs the Windows-portability compat suite (`catalogue_tooling/self_host_windows.py`) — bundler build, self-host drift gates, path-sensitive and encoding-sensitive pytest steps — instead of the standard drift-only check. Rejected with exit 2 if used without `--check`. Drives the `build-check-windows` CI job, replacing its 20-step inline YAML. (`cli.py`, `commands/catalogue_self_host.py`, `catalogue_tooling/self_host_windows.py`)
- **`AGENTBUNDLE_CA_BUNDLE` environment variable** (`https_catalogue.py`): when set to a path,
  `_build_opener` loads a custom PEM CA bundle into an `ssl.SSLContext` and passes it to
  `HTTPSHandler`. Raises `CatalogueError` with a clear message if the path does not exist.
  When the variable is absent, behavior is unchanged. Enables HTTPS catalogue sources behind
  a corporate or self-signed CA without modifying the system trust store.
- **Exact provenance fields on `PackState`** (`artifact_uri`, `archive_sha256`, `source_revision`):
  after `agentbundle install` or `agentbundle upgrade` from a `catalogue+https://` or
  `archive+https://` source, `.agentbundle-state.toml` now records the resolved archive URL,
  the verified SHA-256 digest, and the optional `source_revision` from the channel descriptor.
  Operators can correlate any installed pack row to a specific archive artifact for audit or
  incident response. Local-directory installs leave all three fields absent. Existing state
  files that predate this change are read without error; the missing fields default to `None`.
  (`config.py`, `https_catalogue.py`, `commands/install.py`, `commands/upgrade.py`)
- **Provenance exposed in `list-installed --format json`**: the three new fields appear on each
  row as `artifact_uri`, `archive_sha256`, and `source_revision` (null when absent).
  (`commands/list_installed.py`)
- **Documentation: source-resolution chain and env vars** (`guides/_shared/reference/agentbundle.md`):
  added "Catalogue source resolution" section (five-layer table derived from `source_defaults.py`)
  and "Environment variables" section covering `AGENTBUNDLE_HTTP_BEARER_TOKEN`,
  `AGENTBUNDLE_CA_BUNDLE`, `AGENTBUNDLE_NO_REMOTE`, `HTTPS_PROXY`, and `NO_PROXY`.
  Updated `docs/architecture/catalogue.md` to document the five-layer chain with Layer 3
  (Artifactory bootstrap); updated `docs/guides/reference/catalogue-toml.md` to replace the
  stale `[catalogue.packaging]` section with `[catalogue.package]` and add the missing
  `[distribution.agentbundle.artifactory]` section.

## [0.22.1] — 2026-07-28

### Added

- **`channel` field in `catalogue.toml`** (`distribution.agentbundle.artifactory`): the
  `channel` field is now required when `enabled = true`. `load_catalogue_config` validates
  it against the same safe-segment regex used for `repository` and `bundle`, and stores it
  in `ArtifactoryConfig.channel`. `compile_defaults` now emits the actual channel value
  instead of an empty string, so generated `install-defaults.toml` files contain the
  correct channel and Artifactory-sourced installs resolve successfully.
- **`AGENTBUNDLE_NO_REMOTE` environment variable** (`source_defaults.py`): when set to any
  truthy value, `resolve_default_source` skips the Artifactory org bootstrap (Layer 3) and
  editable-install detection (Layer 4), falling through directly to the packaged default
  (Layer 5). Useful for offline and air-gapped deployments.
- **`catalogue.schema.json`**: added `channel` as an optional string property in the
  `artifactory` object block; `additionalProperties: false` now permits the field without
  breaking `enabled = false` configs.

### Fixed

- `compile_defaults` no longer emits `channel = ""` when Artifactory is enabled. The
  previous hardcoded empty value made every Artifactory-enabled install-defaults.toml
  unusable at runtime.

### Changed

- **`agentbundle catalogue package`** now honours `catalogue.package.include`
  and `catalogue.package.required` from `catalogue.toml`. When `include` is
  non-empty, only those pack directories are archived (non-pack dirs such as
  `profiles/`, `contracts/`, and `.claude-plugin/` are always included). When
  `required` is set, it replaces the default `LICENSE-APACHE` / `LICENSE-MIT`
  constraint; absent or empty `required` preserves existing behavior.
  Path-traversal entries in `include` are rejected before any filesystem access.
  (`catalogue_tooling/package.py`, `catalogue_tooling/config.py`,
  `_data/catalogue.schema.json`, `contracts/catalogue.schema.json`)

### Documentation

- **`docs/guides/how-to/enterprise-app-store.md`**: corrected the archive output path
  (`dist/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`) and the
  channel descriptor path (`channels/<channel>.json`); added a `[distribution.agentbundle.artifactory]`
  configuration example with `channel = "stable"`; added an environment variable reference
  table covering `AGENTBUNDLE_HTTP_BEARER_TOKEN`, `AGENTBUNDLE_NO_REMOTE`, and
  `AGENTBUNDLE_CA_BUNDLE` (upcoming).

## [0.21.1] — 2026-07-28

### Fixed

- **Windows path validation** (`catalogue_tooling/build.py`). `_validate_recipe_path`
  now recognises Unix-style absolute paths (e.g. `/etc/foo.toml`) on Windows, where
  `Path.is_absolute()` returns `False` for drive-relative paths. An explicit
  `startswith("/")` guard rejects them with the correct "absolute" error on all platforms.

## [0.21.0] — 2026-07-28

### Added

- **Catalogue pack defaults** (`catalogue.toml`): a `[pack-defaults.<pack-name>]` table now lets
  catalogue operators declare default config values for any pack they distribute. These are baked
  into `_data/install-defaults.toml` by `agentbundle catalogue self-host --write` and merged with
  user config at runtime so every `load_pack_config` call resolves the three-layer cascade
  (pack-source defaults → operator defaults → user config).
- **Custom user directory** (`catalogue.toml`): `[catalogue] user-dir = "~/custom/path"` overrides
  the default `~/.agentbundle` root for the entire catalogue; `agentbundle install` persists the
  override as `user-root` in `state.toml` and every subsequent `pack_dir` call honours it.
- **Pack config API** (`agentbundle.config`): `pack_dir(pack_name)` resolves the user-scope
  directory for a pack; `load_pack_config(pack_name)` returns the merged three-layer config dict.
  Both honour any custom `user-root` stored in `state.toml`.
- **Operation log** (`agentbundle.oplog`): `write_entry(pack_name, action, src, ...)` appends a
  JSONL record to `<pack_dir>/ops.jsonl` using `O_CREAT|O_APPEND` (POSIX) or the state-file
  mutex (Windows). Each entry is bounded to 4096 bytes; oversized extras are silently truncated
  with a `"_truncated": true` marker.
- **`agentbundle pack-config` CLI**: `get <pack> <key>`, `set <pack> <key> <value>`,
  `show <pack>`, and `path <pack>` subcommands for reading and writing pack config entries.
- **`agentbundle oplog` CLI**: `append <pack>`, `show <pack>`, and `clear <pack>` subcommands
  for managing the per-pack operation log.

## [0.20.3] — 2026-07-27

### Changed

- **Ruff + mypy CI gates.** `build-check.yml` and `build-check-windows.yml` now
  run `ruff check` and `mypy` on every push and pull request. Ruff enforces
  style, imports, common-bug, and pathlib rules (E, W, F, I, UP, B, SIM, C4,
  PIE, RET, PTH). Mypy type-checks the two typed packages
  (`agentbundle`, `credbroker`) with strict import discipline.

### Fixed

- **Internal type annotations.** `commands/upgrade.py` now uses precise
  `Path | None` and `UserConfig | None` parameter types (was `object`),
  eliminating all mypy errors in that module. Other catalogue-tooling modules
  (`build.py`, `verify.py`, `lint.py`) carry targeted `# type: ignore`
  suppressions for dynamic module attributes and YAML duck-typing that mypy
  cannot resolve at import time.
- **Ruff violations.** All PTH, B904, SIM, UP, RET, and C4 rule violations
  across internal scripts are resolved — `os.*` calls replaced with
  `pathlib.Path` equivalents, exception re-raises carry `from exc`, and
  ternaries replace equivalent if/else blocks where they simplify reading.

## [0.20.2] — 2026-07-27

### Fixed

- **Seeds-lint symlink hardening.** `catalogue lint` with `lint-seeds = true`
  now uses `os.walk(followlinks=False)` instead of `Path.rglob("*")` for the
  seeds walk. On Python 3.11/3.12, `rglob` traverses into symlinked
  directories and reads their contents; `os.walk` with `followlinks=False`
  does not, closing a traversal gap for packs that ship a symlinked directory
  under `seeds/`.
- **`sso-broker.py` Windows console hardening.** The broker script
  (`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`) now
  reconfigures stdout and stderr to UTF-8 inside the file-path-invocation
  bootstrap gate, matching the fix applied to the other credentialed CLIs in
  0.20.1. Without this, em-dash messages on a Windows cp1252 console raised
  `UnicodeEncodeError` before the script could run.

## [0.20.1] — 2026-07-27

### Fixed

- **Windows portability.** The CLI entry point now reconfigures stdout/stderr to
  UTF-8 with `backslashreplace` at startup, preventing `UnicodeEncodeError` on
  Windows consoles (cp1252) when output includes non-ASCII characters (⚠, →).
- **Windows sandbox isolation in tests.** The test suite's autouse fixture now
  sets `USERPROFILE` alongside `HOME`, ensuring `scope.resolve_user_root()` uses
  the sandbox on Windows (where `Path("~").expanduser()` reads `USERPROFILE`).
- **Editable-install detection on Windows.** `url2pathname` can return a path
  with a spurious leading `/` before the drive letter (e.g. `/C:\repo`); that
  prefix is now stripped before constructing the `Path`.
- **NTFS reparse-point safety.** `is_symlink()` calls in the pack-floor install
  and seed-delivery paths are now wrapped in `try/except OSError`, skipping the
  entry conservatively when the reparse point cannot be interrogated.

## [0.20.0] — 2026-07-27

### Added

- **`agentbundle docs <pack>`** — new CLI verb that reads pack documentation
  from `packs/<pack>/docs/` in the catalogue source. Supports `--list` to
  enumerate available files and an optional `<file>` positional to display a
  specific file by stem. Works across all four source types (local path, editable
  install, git+https, Artifactory archive). Markdown rendered as plain text with
  ANSI bold headings on a TTY.

- **`[pack.runtime-dependencies]` in pack schema.** New array under `[pack]`
  for declaring external runtime dependencies (pip packages, npm modules, etc.)
  required by a pack's skills. Each entry carries `ecosystem` (required, one of
  pypi/npm/cargo/go/homebrew/apt/system), `package` (required), `version`,
  `optional`, `skills`, `install`, and `note`.

## [0.19.0] — 2026-07-27

Supersedes the accidental research-branch 0.18.0 PyPI publish. Contains all
features from 0.13.0 through 0.18.0 plus the ini-005 catalogue-tooling surface
introduced in 0.13.0.

## [0.13.0] — 2026-07-26

### Added

- **`agentbundle catalogue lint` now covers profiles, seeds, first-value contract, and credentialed-skill conventions.** Four checks previously scattered across standalone `tools/` scripts are now built into the CLI: profile key validation (`_check_profiles`); catalogue-seed blocklist enforcement — no `agent-ready-repo` strings, RFC/K-series identifiers, or internal-spec names leak into adopter seeds (`_check_seeds`); first-value contract completeness for Level-A and Level-B packs (`_check_first_value`); credentialed-skill AST inspection — argv-ban, canonical shim detection, dotfile guard (`_check_credentialed_skills`). Requires `pip install 'agentbundle[lint]'` for the credentialed-skill AST pass.

- **`agentbundle catalogue lint --deep` runs the agentskills.io spec compliance pass on every `SKILL.md`.** Checks frontmatter key set, description length cap (1024 chars), kebab-case name, blessed subdirectory layout, eval structure, and path reference hygiene. Exits 2 with a clear message when PyYAML is not installed; exits 0 without `--deep` regardless of PyYAML.

- **`agentbundle catalogue verify` now runs agent-artifact lint (step 11) and plugin-manifest schema validation (step 13).** Step 11 (`_step_agent_artifacts`) validates `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, and `.claude/commands/*.md` frontmatter and enforces the APM-skill leak guard. Step 13 (`_step_plugin_manifests`) validates every generated `*.claude-plugin/plugin.json` against the bundled schema. Both require `pip install 'agentbundle[lint]'`; absent PyYAML, step 11 returns a single advisory diagnostic and step 13 is a no-op.

- **`agentbundle pack evals run`** — new CLI command porting the pack activation-eval runner into the CLI. Runs Tier-A skill-activation evals using `claude --output-format stream-json --verbose --allowed-tools Skill`; reads `[pack.evals].skills` from `pack.toml`; writes per-run results to a gitignored eval workspace. Report-only: an eval miss is not a non-zero exit.

- **`upgrade --all` sentinel fix.** Packs installed before source-provenance tracking was added stored `source = "agent-ready-repo"` in state. The fix covers both `None` and `"agent-ready-repo"` absent cases so pre-provenance installs resolve through the configured default source and upgrade normally.

- **Windows cp1252/UTF-8 guards.** All `.apm/` scripts and CLI subprocess calls now include `sys.stdout.reconfigure(encoding="utf-8", errors="strict")` / `sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")` and `encoding="utf-8"` on `subprocess.run` calls. Lazy `import asyncio` in credentialed scripts.

- **New `[lint]` optional dependency.** `pip install 'agentbundle[lint]'` pulls `pyyaml>=6.0` for deep linting. Zero-dependency adopters who don't use `--deep` or verify are unaffected.

### Removed

- **Six standalone `tools/` scripts deleted.** `tools/lint-agent-artifacts.py`, `tools/lint-catalogue-seeds.py`, `tools/lint-profiles.py`, `tools/lint-first-value-contract.py`, `tools/lint_credentialed_skills.py`, and `tools/validate-claude-plugin-manifests.py` — plus their self-tests and the `tools/lint-credentialed-skills.sh` wrapper — are removed. All functionality is preserved in `catalogue lint` and `catalogue verify` with identical error codes and message strings.

## [0.12.1] — 2026-07-23

### Changed

- **`install --dry-run` now previews governance seed files alongside the
  projected adapter files.** Seeds (AGENTS.md, docs/CHARTER.md,
  CONVENTIONS.md, and companions) are classified read-only and included in
  the plan output — `create tier-1`, `companion tier-2`, or skipped — so
  the dry-run is a complete picture of what a real install would write, not
  just the adapter projection.
- **`assert_projection_jailed` centralises the two-step path-jail check.**
  A new read-only helper in `agentbundle/safety.py` unifies the root-escape
  (`assert_under`) and prefix-match checks that were duplicated across
  `install.py` Step 8, `upgrade.py`'s dry-run probe, and `write_jailed`'s
  inline prefix block. All three call sites now route through it.
- **`upgrade` probes all projected paths before any write.**
  The non-dry-run upgrade path gains the same probe-all-before-write
  pre-flight that `install`'s Step 8 uses: a prefix-jail violation now aborts
  with zero files written, rather than failing mid-loop after some writes.

## [0.11.1] — 2026-07-16

### Fixed

- **`install` without `--adapter` now targets the auto-resolved adapter when
  handing off to `upgrade`.** Installing a pack already present for multiple
  adapters at a scope (e.g. `claude-code` and `codex`) without specifying
  `--adapter` triggered upgrade's "pass `--adapter` to pick one" disambiguator,
  even though install's probe had already selected the right row. The offered
  upgrade now forwards the auto-resolved adapter, matching the behavior when
  `--adapter` is explicit.

## [0.11.0] — 2026-07-03

### Added

- **New `agentbundle show <pack>` command — a pack's skills and agents, derived
  live.** Answers "what does this pack contain?" by walking the pack's `.apm/`
  source tree on each call, printing its `pack.toml` metadata alongside the full,
  sorted skill and agent inventory. `--format json` emits a stable object
  (`name`, `version`, `description`, `skills`, `agents`, `source`) for scripts and
  agents. Nothing is persisted and no manifest is touched, so the answer can't
  drift from what the pack ships. When the catalogue can't be resolved, an
  *installed* pack still reports its inventory from the install-state files
  (`source: installed-state`, recovered across both scopes and every adapter row);
  a not-installed pack errors and exits non-zero. Implements RFC-0060 / ADR-0049.

## [0.10.2] — 2026-06-30

### Fixed

- **`install --adapter X` now carries that adapter through when it hands off to
  `upgrade`.** Installing a pack that is already present, with `--adapter`
  specified, offers to upgrade instead — but the hand-off dropped the adapter,
  so a pack installed for more than one adapter at that scope hit upgrade's
  "pass `--adapter` to pick one" disambiguator even though you had just passed
  it. The offered upgrade now targets the adapter you named.

## [0.10.1] — 2026-06-30

### Fixed

- **The "no catalogue source" error no longer sends you to a `--catalogue` flag
  that doesn't exist.** The catalogue is a trailing positional argument; when no
  source resolves, the recovery text now reads "pass a catalogue argument …" so
  following it actually works.

## [0.10.0] — 2026-06-30

_Backfilled: 0.10.0 shipped (tag `agentbundle-v0.10.0`) without a changelog
entry; recorded here for the history._

### Added

- **`agentbundle list-installed` — a read-only view of what's actually installed.**
  Lists every installed `(pack, adapter)` row across the user and repo scope with
  its version and an `up-to-date` / `upgrade-available` / `unknown` status against
  the catalogue; the check degrades to `unknown` (never an error) when the
  catalogue can't be resolved. `--no-check` / `--offline` skips it, `--scope`
  filters to one scope, and `--check-drift` adds a per-row count of files edited
  locally since install (#468).

### Changed

- **Upgrade messaging now reports per-adapter versions and distinguishes a
  re-applied install from a genuine upgrade**, and flags local drift from the
  installed baseline (#468).

## [0.9.0] — 2026-06-26

### Changed

- **Install identity is now the content-addressed *footprint*, not the pack
  name — one pack can be installed for several adapters at one scope, and the
  `.agents/skills/` cohort shares one skill copy (RFC-0052 / ADR-0039+0040).**
  The state file is keyed `[pack.<name>.adapters.<adapter>]` (schema **v0.4**).
  Installing `research` for `codex` after `claude-code` now succeeds (disjoint
  trees); installing it for `cursor` after `codex` co-owns the shared
  `.agents/skills/` files instead of rewriting them. A genuine collision — the
  same path at different content, or two different packs claiming one path — is
  refused, naming the conflicting paths; `--force` keeps your copy as a
  `.upstream` companion. `uninstall`, `upgrade`, and `diff` gain an `--adapter`
  disambiguator (required only when a pack has more than one adapter row at the
  scope); `uninstall` removes a shared file only when its last owner goes. After
  an install that writes a shared skill, stderr names the other adapters that
  read it.
- **cursor, gemini, and copilot now project the `skill` primitive to the shared
  `.agents/skills/` home (joining codex)** instead of their native
  `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`. Their
  agents/hooks/commands are unchanged. Adapter contract bumped to **v0.17** with
  a `[contract.shared-prefixes]` registry.

### Breaking

- **State schema migration is greenfield (no auto-converter).** A pre-v0.4
  state file is refused on read *and* write with a re-install prompt; mixed
  CLI versions across CI/local can no longer silently mis-read state. Existing
  cursor/gemini/copilot installs may leave a now-unused native skills tree
  behind — re-install to land skills at the shared home.

## [0.8.0] — 2026-06-25

### Added

- **The `catalogue` argument is now optional on `install`, `upgrade`,
  `list-packs`, and `list-profiles` (RFC-0046 + RFC-0047).** When omitted, the
  source resolves through a four-layer, first-match-wins chain: an explicit
  `catalogue` positional › your `config set source` value › an editable clone
  (`pip install -e`, detected via PEP 610 and walked up to the catalogue root,
  bounded by the enclosing `.git` repo) › a packaged default
  (`git+https://github.com/eugenelim/agent-ready-repo`). So a public user runs
  `agentbundle install --pack core` (or `agentbundle list-packs`) with no URL,
  and a gateway-bound editable fork defaults to its own clone — with no
  repo-committed source and no cwd fall-back (a code-provenance boundary). All
  four verbs share one resolver, so a bare query on an editable fork resolves to
  the local clone (never silently fetching upstream). New `source` user config
  key (`config set/get/unset source`). Layer-4 integrity-pinning (pin `main` to a
  SHA + verify the archive digest) is a named follow-on.

### Changed

- **`agentbundle list-packs` and `list-profiles` word-wrap the DESCRIPTION
  column to fit the terminal.** On an interactive terminal whose width the
  table would overflow, the long description column wraps to the leftover
  width — every physical line stays within the terminal, continuation lines
  align under the column, and the columns that follow it (DEPENDENCIES) stay on
  the row's first line. When stdout is **not** a terminal (piped or
  redirected), output is unchanged: full content-width columns, untruncated, so
  `grep`/`awk`/`cut` still see stable columns — the convention `gh`, `git`, and
  `ls` follow. Both commands now share one terminal-aware table renderer.

## [0.7.0] — 2026-06-24

### Changed

- **`agentbundle uninstall` gains `--dry-run` and `--yes`, and confirms before
  removing.** It classifies each recorded file into `remove` (Tier-1, bundle-
  owned) or `keep` (Tier-2, adopter-edited): `--dry-run` prints that plan and
  writes nothing (no removal, no hook-wiring unproject, no state change);
  otherwise it confirms before the first `os.remove` (`--yes` skips; a non-TTY
  stdin refuses rather than blocking). The execution acts on the previewed
  classification without re-hashing, so the bytes a dry-run / prompt shows are
  exactly the bytes removed. Tier-2 preservation is unchanged.
- **`agentbundle install --force` confirms before its destructive cleanup; new
  `--yes`.** When `--force` would delete on-disk paths, it lists the deletion
  unit — the dist-tree subtree roots (`claude-plugins/<pack>`, `apm/<pack>`) or
  the orphan files — and confirms before deleting; the whole destructive block
  (rmtree + state-row drop + state-file rewrite) is gated atomically, so a
  decline mutates nothing. `--yes` skips the prompt; a non-TTY without `--yes`
  refuses with zero deletions. `--force` used only as a cross-scope bypass (no
  deletion) is unchanged and never prompts. **Migration:** CI using the deleting
  form of `install --force` must add `--yes`.
- **`agentbundle install` offers to upgrade an already-installed pack.** Instead
  of flatly refusing with `use 'upgrade'`, installing a pack already present at
  the requested scope now offers (on a TTY) to run `upgrade` against the same
  catalogue/scope; `install --yes` runs it without prompting. A non-interactive
  stdin without `--yes`, and `install --dry-run`, keep the historical refusal.
- **`agentbundle reconcile` and `list-targets` drop their dead `--scope` flag.**
  `reconcile --scope` had a single legal value (`user`) equal to its default, and
  `list-targets --scope` was parsed but never read. Both are removed; passing
  `--scope` to either now reports `unknown flag for <verb>: --scope`. Default
  behaviour is unchanged.

- **`agentbundle upgrade` no longer takes `--to` (breaking).** The upgrade
  target is now derived from the resolved catalogue's `pack.toml` `[pack]
  version` — the catalogue is the single source of truth, and there is no
  version-history store to select from (`--to` was `required` but never
  validated against the catalogue's actual version). The command shows
  `installed → target`, asks before writing, and the success recap names both
  versions (`upgraded: <pack> @ <scope> <from> -> <to>`). When the installed
  version already equals the target, it says so and offers to re-apply.
  Migration: drop `--to <version>`; add `--yes` for non-interactive / CI use.
  To move to a specific past version, point the catalogue at that git ref.

### Added

- **`agentbundle upgrade --yes`** skips the confirmation prompt for
  non-interactive use; without it, a non-TTY stdin refuses (with guidance to
  pass `--yes`) rather than blocking on a prompt.

### Fixed

- **`agentbundle upgrade` rejects two per-primitive flags at once.** The
  `--skill` / `--agent` / `--hook` / `--seed` / `--command` flags are now a
  mutually-exclusive group; previously passing two silently upgraded only the
  first.

## [0.6.0] — 2026-06-20

### Fixed

- **Kiro custom agents now reach the bundle's skills — CLI and IDE** (RFC-0022
  erratum E4; adapter contract v0.15). On both Kiro targets, only the *default*
  agent auto-discovers skills; a *custom* agent (`kiro --agent <name>`, every
  headless `--no-interactive` run, or an IDE subagent) loaded **zero** skills
  unless it declared them in its `resources` field (kiro #6887/#6888/#4993). The
  `kiro-cli` and `kiro-ide` agent projections now inject a skill-resources glob
  (`skill://.kiro/skills/**/SKILL.md` plus the `~/.kiro/skills/**/SKILL.md`
  user-scope twin) into every projected agent — CLI into the agent JSON, IDE
  into the `.md` YAML frontmatter (quoted, YAML-safe). An agent that declares
  its own `resources` keeps it; the deprecated `kiro` alias inherits the IDE
  behavior. Default-agent runs were already fine and are unaffected.

### Added

- **`inject-resources` adapter-contract field** (contract v0.15). A typed,
  optional array on an adapter's agent projection entry that injects a fixed
  `resources` list into every projected agent. Currently used by the two Kiro
  adapters for skill reachability (above).

## [0.5.0] — 2026-06-16

### Added

- **Curated install profiles — `install --profile <name>` and `list-profiles`**
  (RFC-0034). A profile is a first-party `profiles/<name>.toml` at a catalogue
  root naming a single-scope, deps-first set of packs an adopter installs in
  one command. `agentbundle install --profile <name> <catalogue>` pins one
  scope and one adapter for the whole batch, runs the full read-only pre-flight
  for every pack before writing any, then installs each in authored order;
  `agentbundle list-profiles <catalogue>` browses what a catalogue offers.
  Adds zero primitives and zero adapter-contract surface — the CLI reads the
  manifest, the catalogue carries it.

### Fixed

- **`agentbundle install --adapter kiro` now behaves exactly like `kiro-ide`**
  (RFC-0022 alias parity). The `kiro` → `kiro-ide` alias is now canonicalized
  at every install-path decision site, not just the build registry.
- **`--version` reports the package version.** `CLI_VERSION` had drifted to
  `0.1.0` and was printed by `agentbundle --version` regardless of the released
  version; it now tracks the package version (`0.5.0`).

## [0.4.0] — 2026-06-14

### Added

- **`pack.toml` is the rich source of truth for pack metadata** (RFC-0031,
  adapter contract v0.14). A pack may now declare `license`,
  `[[pack.maintainers]]`, `[pack.links]`, `categories`, `keywords`, a `readme`
  pointer, and a `[pack.metadata.<tool>]` escape hatch. The build projects the
  cleanly-mappable subset — plus the pack's `README.md` — into each
  distribution route's manifest (`plugin.json` / `marketplace.json` entry), so
  a catalogue describes each pack richly instead of with one sentence. **All new
  fields are optional**; packs pinned below contract v0.14 are unaffected.
- **Soft `categories` vocabulary** — `agentbundle validate` recognizes a
  default set of category slugs and emits a **warning (exit 0)**, never an
  error, on an unknown slug. The vocabulary is extensible by design (RFC-0031
  D8); `design` is included for the `design-craft` pack.
- **`list-packs` surfaces the enriched metadata** so a catalogue is browsable
  by more than name and a one-line description.

### Changed

- **Pack and plugin-manifest JSON schemas accept the optional enriched fields**
  (the `additionalProperties: false` gate on both manifest schemas was relaxed
  for the projectable metadata subset).

### Fixed

- **`build-self` no longer emits untracked per-quadrant guide READMEs.** The
  self-host projection skips `guides/**` (adopters still receive guide
  scaffolds via seed delivery).

## [0.3.1] — 2026-06-12

### Changed

- **README rewritten for adoption** — quick start, a common-commands
  reference, and the "npm for your coding agent" framing; the PyPI summary
  now matches.
- **Static-analysis annotations** carried in from the repo's SAST gate
  (ADR-0017): `# nosec B310` on the constant-base GitHub-archive fetch and
  `usedforsecurity=False` on the non-security finding-ID digest. No runtime
  behaviour change.

## [0.3.0] — 2026-06-12

### Added

- **Cursor full-parity distribution adapter** (RFC-0026) — projects all
  primitives for both install scopes via the single-writer
  `.cursor/` model.
- **Gemini CLI full-parity distribution adapter** (RFC-0027) — keeps and
  maps tools, projects a tier model map, supports the
  `gemini-command-toml` mode, and bridges `AGENTS.md` through the
  single-writer `.gemini/settings.json`.
- **`--dry-run` for `install` and `upgrade`** — preview the projection
  without writing any files.
- **Upgrade surfaces Tier-2 companion-drops** — `upgrade` now reports the
  `.upstream` companion files that an adopter must reconcile by hand.
- **credbroker install-time user-scope delivery rail** — the build
  pipeline vendors `credbroker` to `.agentbundle/lib` (drift-gated) and
  consumer bootstraps append the `~/.agentbundle/lib` floor at lowest
  precedence (new `user_libs` module).

### Changed

- **Copilot adapter projects skills as first-class `SKILL.md`** and
  corrects the web-tool documentation (adapter contract v0.12).
- **Codex adapter projects agent model and tool config** into the
  generated agent TOML.
- **Pack admittance** — credentialed packs admit the `copilot` and
  `cursor` adapters (RFC-0013 erratum); `research` and `architect` opt
  into the `cursor` adapter.

### Removed

- **Retired the shared-libs shim projection.** Credentialed skills now
  `import credbroker` from the user-scope lib floor instead of a
  build-projected shim.

## [0.2.0] — 2026-05-26

### Removed (breaking)

- `agentbundle.credentials` — the public loader module (`load_credentials`,
  `Credentials`, `CredentialsMissingError`, `Tier2HardFailError`,
  `parse_env_file`, `EnvParseError`).
- `agentbundle.creds` — the entire subpackage (`loader`, `exceptions`,
  `_keychain_macos`, `_credman_windows`), including the schema parser
  `_parse_schema` and the `CredsSchema` / `KeyDef` dataclasses.
- `agentbundle creds` CLI subcommand and its four verbs (`setup`,
  `check`, `where`, `rm`).

### Migration recipe (RFC-0013 § 9)

Out-of-tree credentialed skills that previously imported the loader
from `agentbundle.credentials` must change four things to migrate to
0.2.0. None of the four are optional; missing one leaves the import
unresolvable.

**1. Add four frontmatter declarations** to the skill's `SKILL.md`
(nested under the `metadata:` escape hatch):

```yaml
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds                       # selects the build-projected shim broker
  namespace: <your-namespace>       # matches your creds-schema.toml
  keys: ["<KEY>"]                   # the secret keys this skill resolves
```

The build pipeline reads `auth: creds` to decide which skills receive
the projected shim. Without that line the projection doesn't fire.

**2. Change the import line** in each script that resolves
credentials:

```python
# Before (0.1.x)
from agentbundle.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

# After (0.2.0)
from .credentials_shim import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)
```

**3. Run `make build-self`** in the catalogue's clone (or invoke
`agentbundle install --pack credential-brokers --scope user .` if
you install via the CLI). This materialises the three shim files —
`credentials_shim.py`, `_keychain_macos.py`, `_credman_windows.py`
— into your skill's `scripts/` directory. Without this step the
relative import resolves to nothing and you get
`ModuleNotFoundError`.

**4. Replace `agentbundle creds setup <namespace>` invocations** in
docs and error messages with the `credential-setup` skill — shipped
by the `credential-brokers` pack at user scope. Authors invoke it
from their agent's skill loader instead of from the shell. There is
no longer an `agentbundle creds` CLI verb.

Verification: invoke the consumer skill's own `check` verb (or
equivalent low-stakes call). The shim walks Tier 1 → 2 → 3 the same
way the prior loader did and surfaces the same exceptions; no
behavioural delta.

### Adopter pin policy

Pin to `agentbundle < 0.2` in your dependency manifest until you have
completed the migration above. The pre-0.2 minor (`0.1.0`) is the
intended rollback target; that release ships from the `agentbundle-v0.1.0`
git tag and is published from the same release workflow this PR
amends. Adopters who cannot migrate immediately should stay on
`agentbundle < 0.2` until they have shipped the four-step recipe.

If no `agentbundle-v0.1.0` tag exists on the upstream remote at the
time you read this changelog, the rollback target has not yet been
published — open a release issue against the catalogue requesting
one before bumping any production pin.

### Why this is breaking inside the 0.x window

Per RFC-0013 § *Drawbacks* — the migration removes a public surface
that one or more out-of-tree consumers may depend on. The deprecation
window inside 0.x is the prior minor (0.1.0) staying available on
PyPI; the migration recipe above is mechanical (one import-line
change per consumer); and the new shim is byte-equivalent (per
spec § AC6) to the prior loader's behaviour. No behavioural change.

## [0.1.0] — pre-0.2.0

The `agentbundle` build / install / adapt CLI and the
`agentbundle.credentials` public loader surface. See `docs/CHARTER.md`
and `docs/specs/skill-secrets/spec.md` for the historical scope.
