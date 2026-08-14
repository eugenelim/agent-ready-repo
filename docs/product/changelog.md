# Changelog

All notable user-visible changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Maintenance: this file is updated in the same PR that introduces the
> change. CI will warn (configurable: block) when a PR touches code that
> changes user-visible behavior but does not touch this file.
>
> Entries can be drafted from conventional commits: `git log --oneline`
> filtered to `feat:` and `fix:` since the last tag is a starting point,
> not a finished product. Rewrite for users, not contributors. See the
> [Common Changelog guidance](https://common-changelog.org/) — the audience
> is humans who use the software, not humans who wrote it.


## [Unreleased]

### Changed

- **A live-demo guide now maps three roles through one coherent problem space.**
  Peer champions can run a 30-minute repository demonstration using Core's
  direct technical path, Core's structured enterprise handoff, or user-scoped
  Product Engineering shaping followed by a visible Core delivery handoff.
- **Published-site links are checked after rendering.** The complete marketing
  and technical-docs build now refuses publication when an internal page or
  fragment target is missing. Existing broken guide, pack, and component-demo
  targets have been repaired at their authored sources or owning projection
  rules.
- **Published guides no longer point at records you can't read.** Guide pages
  across the `_shared`, `core`, `atlassian`, `credential-brokers`,
  `governance-extras`, and `product-documentation` trees cited this
  repository's own decision records and specs, so those links went nowhere for
  anyone reading the published guides. The citations are gone and the
  surrounding explanation stays; generic guidance like "record an ADR",
  `<feature>` placeholders, and documented commands are untouched. References
  pointing readers at the retired `user-guide-diataxis` guide tree now point at
  `product-documentation`, which supersedes it.
- **Some guide sidebar labels changed.** Nineteen pages gained the frontmatter
  the guide site reads. For the sixteen that previously carried a shorter
  hand-written navigation label, the sidebar now shows the page's own title
  instead — "Adapt to Project" now reads "How to adapt a freshly installed pack
  to your project". No page moved and no link changed. No pack version changes.

### [agentbundle][0.35.1] — 2026-08-14

#### Fixed

- **An install now recovers when Python trusts no certificate authority at all.**
  A python.org macOS interpreter ships without a configured certificate store —
  until its `Install Certificates.command` runs it trusts zero authorities, and
  every HTTPS request fails whether or not your network inspects traffic. The
  previous release read this as a probable corporate proxy, which sent the first
  affected adopter after a cause that did not exist, and its recovery could not
  help because the administrator keychain holds private roots and cannot complete
  a public certificate chain. `agentbundle` now recognises an empty trust store,
  says so plainly, offers the one-command interpreter fix first, and repairs the
  case automatically on macOS by also reading Apple's root program. Nothing
  changes for an interpreter with a working store.

### [agentbundle][0.35.0] — 2026-08-14

#### Added

- **`agentbundle install` now recovers on corporate networks that inspect TLS.**
  On a network where a proxy re-signs HTTPS traffic with a private certificate
  authority, a catalogue fetch failed with
  `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`, because
  the authority is installed in the operating system's trust store and Python
  reads its own certificate file instead. On macOS, `agentbundle` now retries
  once against the administrator-controlled trust anchors the operating system
  already provides, and says so on stderr. Verification stays strict throughout:
  the retry adds trust anchors, never removes one, and no flag or variable
  disables verification. One caveat stated plainly: macOS lets an administrator
  mark a certificate *Never Trust*, and this fallback does not read those
  markings, so such a certificate is still used as an anchor — bounded to a
  keychain only an administrator can write. The login keychain is never read. Set
  `AGENTBUNDLE_NO_SYSTEM_TRUST=1` to opt out. Windows needs no fallback — Python already
  loads the Windows certificate store, honouring per-certificate trust settings —
  and Linux needs none provided the authority is installed in `/etc/ssl/certs`.
  A WSL distribution does not inherit the Windows store; install the authority
  into the distribution or set `AGENTBUNDLE_CA_BUNDLE`.
- **`AGENTBUNDLE_NO_SYSTEM_TRUST`** — opt out of the fallback above.

#### Fixed

- **`AGENTBUNDLE_CA_BUNDLE` now works on `git+https://` catalogue sources.** The
  reference documentation described it as covering HTTPS catalogue sources, but
  only the `catalogue+https://` and `archive+https://` paths read it — the
  `git+https://` path ignored it entirely, so adopters who followed the
  documentation still could not install. `SSL_CERT_FILE`, `SSL_CERT_DIR`, and
  `REQUESTS_CA_BUNDLE` are honoured there too, with `AGENTBUNDLE_CA_BUNDLE`
  taking precedence. Note the semantics differ by source form and this is now
  documented: `git+https://` *adds* your bundle to the default trust store,
  while `catalogue+https://` and `archive+https://` *replace* it.
- **A catalogue fetch can no longer hang indefinitely.** The request now carries
  an explicit 30-second timeout, so a proxy that accepts the connection and
  never answers fails instead of stalling.
- **A failed catalogue fetch explains what to do next.** The error previously
  surfaced only the raw OpenSSL string; it now names the probable cause and
  gives ordered troubleshooting steps.

#### Changed

- **Setting `AGENTBUNDLE_CA_BUNDLE` to a path that does not exist now fails a
  `git+https://` install that previously succeeded.** The variable was ignored
  on that path before, so a fleet-wide export pointing at a file absent on this
  host was harmless; it now raises before any connection is made. Unset it, or
  correct the path.

### [agentbundle][0.34.0] — 2026-08-12

#### Added

- **Bundled contracts are available offline from the CLI.**
  `agentbundle catalogue contracts list`, `show`, and `export` enumerate,
  inspect, or copy the exact public contracts shipped with the running version.
  Exported files are reference copies and do not change validation behavior.
- **New catalogues point authors to their next checks.** Successful plain
  `catalogue init` output now identifies the scaffolded authoring standards
  guide, bundled-contract discovery command, and catalogue verification. JSON
  output remains unchanged.

#### Changed

- **The authoring standards reference documents bundled contract inspection.**
  Section 12 records the offline commands and their read/write boundary, and the
  same section ships in the initialization scaffold.

### [core][2.5.9] — 2026-08-12

#### Changed

- **Work-loop captures more than speed improvements.** Its closeout review now
  asks whether a reusable learning would have improved correctness,
  reliability, security, determinism, operability, maintainability,
  efficiency, or independence from hidden context. Speed remains one signal,
  not the objective.
- **Repository knowledge has a lifecycle architecture.** Maintainers now have
  a concept-first reference for shared candidate capture, topic distillation,
  file-based canonical storage, explicit safe enquiry, freshness, and optional
  cross-project promotion. Normal session start continues to leave captured
  observations out of model context.

### [agentbundle][0.33.3] — 2026-08-12

#### Changed

- **AgentBundle and CredBroker Windows checks now run in parallel.** The
  AgentBundle compatibility command keeps the engine and pack portability
  checks, while CredBroker's package suite runs in its own Windows CI job. The
  existing aggregate check remains blocking on both suites.

#### Fixed

- **Self-host writes now work across checkout ownership boundaries.**
  `catalogue self-host --write` updates writable existing seed and adapter
  files without attempting owner-only timestamp or mode changes, preserving
  their inode, ownership, and mode. `--check` still reports mode drift that the
  writer cannot repair.

### [agentbundle][0.33.2] — 2026-08-12

#### Fixed

- **Workspace MCP status uses the canonical routing result.** The public MCP
  status surface now denies malformed workspace state with sanitized findings
  and exposes only canonical dispatchable queue work as ready.

### [core][2.5.8] — 2026-08-12

#### Changed

- **Workspace status now publishes canonical routing findings and receipt
  rules.** The workspace reference and status skill document every canonical
  finding, safe recovery action, cross-repository coordination receipt block,
  and invalid receipt recovery path.

#### Fixed

- **Workspace repair preserves structured queue entries when moving shipped
  work.** `repair-apply` now carries the retained inline TOML entry into
  `[work].shipped` instead of replacing it with a bare path, while keeping
  fingerprint, confinement, atomic write, and comment-preservation checks.

### [core][2.5.7] — 2026-08-11

#### Fixed

- **Core filesystem readers now fail closed on traversal and symlink escapes.**
  Spec-status and traceability checks confine repository-derived probes before
  use; work-loop state and pending-event JSON is bounded and read through a
  verified regular-file descriptor; event-log creation refuses links and
  identity changes and creates owner-only files; and knowledge appends use the
  shared no-follow state lock. Intentional operator-selected scan roots remain
  valid.

### [core][2.5.6] — 2026-08-11

#### Fixed

- **Core conventions no longer send adopters to catalogue-only files.** The
  credential-broker rule now states its four supported ids without linking to
  this catalogue's decision records, and maintainer hook guidance no longer
  points adopters to a README that is absent from the installed pack.

### [atlassian][0.8.3] — 2026-08-11

#### Fixed

- **Jira, Jira Align, Confluence Publisher, and Confluence Crawler now resolve
  installed scripts before interpreting exit codes.** Each skill confines and
  preflights its regular-file entry point under the installed skill directory,
  then launches it as one argument while keeping project-relative content paths
  unchanged. A missing or escaping script is reported as an installation or
  invocation failure instead of missing credentials. Headed Jira and Confluence
  SSO capture remains a command for the operator to run; automatic recovery
  remains headless.

### [figma][0.3.1] — 2026-08-11

#### Fixed

- **Figma script resolution can no longer masquerade as a credential or scope
  failure.** The skill validates and confines its installed `figma.py` before
  launch, uses an argument-safe resolved path, and reports entry-point failures
  without credential, token, re-authentication, or scope guidance.

### [linear][0.2.2] — 2026-08-11

#### Fixed

- **Linear now distinguishes an unavailable installed client from exit 2.** The
  primitive resolves and preflights `linear.py` before launch, preserving its
  existing credential behavior only for a script that actually ran. The pack
  also registers activation coverage for `linear`, `linear-brief-intake`, and
  `linear-brief-sync`, plus primitive behavior coverage for the corrected path.

### [converters][0.9.5] — 2026-08-11

#### Fixed

- **Mermaid Renderer and Markdown to HTML now launch their installed renderer
  entry points from project-root sessions.** Both skills use confined resolved
  paths, including eval and script-emitted usage surfaces. Missing scripts no
  longer produce false Mermaid CLI or Node-package guidance; the renderers'
  existing exit meanings and content-path behavior are unchanged.

### [credential-brokers][0.3.2] — 2026-08-10

#### Fixed

- **Concurrent first use of an SSO profile no longer fails spuriously on
  Windows.** The broker now establishes its fixed lock directory before
  validating the profile's lockfile path, so simultaneous first-use operations
  cannot make Windows path canonicalisation look like a confinement escape.
  Traversal and wrong-parent paths remain rejected before a lockfile is opened.

### [core][2.5.5] — 2026-08-10

#### Fixed

- **Workspace status now shows the complete repository backlog.**
  Both `status` and `reconcile` expose an ordered `repo_backlog.open` display
  contract, so legacy untyped build entries no longer disappear when the
  shaping guard's intentionally typed-only backlog is empty. The rendered
  Backlog section labels build and shaping work separately, preserves explicit
  dependencies and summaries, supports target path-based entries, and remains
  absent for an empty repository backlog.

### [atlassian][0.8.2] — 2026-08-10

#### Changed

- **Confluence SSO checks recover one unavailable stored session
  automatically.** `confluence-crawler --check` now verifies the stored
  cookie session, asks CredBroker to refresh its registered profile once when
  that specific session is unavailable, and verifies the refreshed session
  with one new probe. The disclosure states that recovery is headless, shows
  no browser window, and takes its destination from the registered profile.

  Permission, configuration, cookie-confinement, dependency, TLS, transport,
  timeout, and server failures never trigger recovery. Crawls and token-based
  authentication keep their existing behavior. When automatic recovery cannot
  proceed, the error tells the user which existing manual setup action to run.
### [core][2.5.1] — 2026-08-09

#### Changed

- **Core now publishes the target workspace index contract.**
  The workspace reference, starter seed, and initialization text describe the
  five-field target entry shape, lifecycle collections, source provenance,
  typed hard dependencies, legacy compatibility limits, path confinement, and
  strict JSON/TOML encoding expectations.

### Fixed

- **Concurrent SSO operations on one profile no longer corrupt its cookie jar.**
  Two agent turns touching the same profile at once — a `jira check` resolving
  cookies while a prior turn's recapture is still committing — could previously
  leave a jar assembled from both, or none at all. Each profile's store
  transition is now serialised behind an exclusive interprocess lock, so a
  reader always sees one whole jar.

  When a profile is busy, commands exit `6` and `credbroker` raises
  `SsoStoreContendedError` rather than waiting indefinitely or reporting a
  false expiry. Every wait is bounded well inside the caller's timeout.

### Changed

- **The Claude plugin marketplace now carries only packs you can install at
  user scope.** Claude plugins install into a global cache, not into your
  repository, so packs designed to live inside a repo — `core`,
  `governance-extras`, `iac-terraform`, `monorepo-extras`,
  `release-engineering`, `user-guide-diataxis` — are no longer offered there.
  Install them with `agentbundle install` instead; that is the route they were
  always built for. `catalogue-curation` makes seven: it was never published
  to the plugin branch, but it was still listed at the repository-root
  marketplace that `claude plugin marketplace add` resolves — a listing that
  could only ever fail to fetch. That entry is gone too.

  Already installed one as a plugin? Run
  `claude plugin uninstall <pack>@agent-ready-repo`, then install at repo scope
  with `agentbundle install`. Verified against Claude Code 2.1.223: once your
  client refreshes the marketplace, a delisted plugin shows as `failed to load`
  and `claude plugin update` refuses it. Until it refreshes, the cached copy
  keeps loading — so uninstall rather than wait.

  The pack pages and the catalogue on the site now show the plugin command only
  where it applies.

- **Every pack now says what it is *for* in its first sentence.** Pack
  descriptions are what you read in a marketplace browser while deciding whether
  to install, and ours had drifted into component inventories — `core` opened
  with a list of thirteen skill names, and the longest ran to 1122 characters
  against a 177-character median in the marketplace we are listed alongside.

  All 22 now lead with the job you accomplish: *"Supervised coding from brief to
  merged PR"*, *"Run Jira and Confluence from a conversation"*, *"Validate a
  release the way production will"*. Median length drops from 227 characters to
  188, the longest from 1122 to 263. Cross-pack references, internal file paths,
  and framework name-drops are gone; what each pack contains still follows, just
  after the point rather than instead of it.

  Nothing about a pack's behaviour changed, and no skill or agent description
  was touched — those drive activation and are a different contract. Five packs
  (`architect`, `contracts`, `core`, `experience-design`, `product-strategy`)
  also had descriptions that disagreed between their manifest and the
  marketplace listing; all three copies now match.

### Added

- **A written standard for pack descriptions.**
  `catalogue-authoring-standards.md` § 2 now says what a `[pack].description`
  is for — display copy a person reads while deciding whether to install — and
  names the anti-patterns that made ours drift: component-inventory openings,
  repo-insider vocabulary, cross-pack references, framework name-drops, and
  internal paths. It also separates this field from a *skill's* description,
  which the model reads to decide activation and where length is load-bearing.

  `tools/lint-pack-descriptions.py` backs it with a deliberately loose 800-char
  drift backstop — enough to stop another 1122-character entry, not enough to
  adjudicate style, because a length check cannot tell good copy from bad. It is
  a repository policy lint, not a packaged one: `pack.schema.json` and the
  packaged pack lint both run against *adopter* catalogues, so a rule in either
  would turn this catalogue's house style into someone else's build break.

## [core][2.5.5] — 2026-08-10

### Fixed

- **Concurrent work-loop mutations no longer lose an update during lock
  creation.** A contender could observe the live creator's lockfile after its
  exclusive creation but before its ownership record was written, mistake that
  fresh empty file for crash residue, and reclaim it immediately. Two writers
  could then enter one critical section; one would report success before
  discovering its lost lock, while the final state omitted an update. Fresh
  empty locks now remain occupied until the existing stale-recovery budget
  expires. Stale empty locks left by a crashed creator are still reclaimed, and
  no timeout or stale threshold changed.

- **The work-loop concurrency self-test now names its failing case in CI.** Its
  shell wrapper preserves the child suite's output, concurrency cases prove
  actual production-lock contention instead of scheduler timing, and
  hermeticity observes only each child's throwaway repository.

## [experience-design][2.0.1] — 2026-08-10

### Changed

- **All 20 experience-design skills now route natural requests at explicit
  discipline boundaries.** Each activation description names its design
  output and routes product strategy, product-engineering shaping, and routine
  frontend implementation away where applicable. The copy path now separates
  the brand register, surface content structure, acquisition-surface copy
  goals, and product UI strings without assigning one skill all four jobs.
- **Activation evidence and adopter pages use the same routing model.** Every
  skill gains a natural positive and an adjacent-discipline negative fixture.
  The pack page and guide home now lead with jobs and exits before the complete
  20-skill inventory, and the reference mirrors each skill's trigger, output,
  and nearest boundary.

## [architect][0.14.4] — 2026-08-09

### Changed

- Architect's pack-owned projection, rubric-parity, README, and install-command
  tests now travel with the pack instead of the `agentbundle` engine suite.

## [core][2.5.4] — 2026-08-09

### Changed

- Core's workspace-status, seed, README, and install-marker journey tests now
  travel with the pack that owns those behaviours.

## [catalogue-curation][0.2.4] — 2026-08-09

### Changed

- Catalogue-curation's removal and retained-content regressions now travel with
  the pack instead of the engine suite.

## [credential-brokers][0.3.1] — 2026-08-09

### Changed

- Credential-brokers now carries its own manifest, install, shim, floor, broker,
  guide, and vendored-source tests.

## [atlassian][0.8.1] — 2026-08-09

### Changed

- The flow-metrics upstream probe now travels with the Atlassian pack and runs
  from its skill-owned test directory.

## [product-engineering][0.13.4] — 2026-08-09

### Changed

- Product-engineering's README install-command regression now travels with the
  pack.

## [linear][0.2.1] — 2026-08-09

### Changed

- Linear's primitive tests now travel with the pack and run with its declared
  `httpx` test dependency.

## [agentbundle][0.30.1] — 2026-08-09

### Fixed

- **Catalogue verification now reports zero unclassified paths for this
  repository's current inventory without hiding future unknown files.**
  Repository-owned source, docs, profiles, and website trees are classified at
  stable ownership boundaries. Generated `.agentbundle/bin` and
  `.agentbundle/lib` files stay projected rather than excluded, and their drift
  now fails the self-host verifier path. Git filename enumeration is
  NUL-delimited with one-line escaped diagnostics. Special projection reads,
  writes, and orphan cleanup are no-follow; held-directory atomic writes defeat
  concurrent leaf-link swaps, and executable projections reject mode drift.

## [core][2.5.2] — 2026-08-09

### Changed

- **The source-of-truth convention now names the adapter-independent runtime
  projection rails.** Maintainers are directed to edit `adapter-root-bins` and
  `user-libs` upstreams instead of the generated `.agentbundle/` copies.

## [frontend-engineering][0.1.4] — 2026-08-08

### Added

- **Frontend Engineering now routes adopters by job before listing skills.**
  The pack page opens with create, retrofit, audit, and verify paths, each with
  the expected output, then links to a new canonical journey from page/screen
  contract through implementation, gates, evidence manifest, and independent
  frontend review.
- **Two new guides make frontend contracts and performance policy actionable.**
  The page/screen-contract how-to helps adopters choose a full contract, a
  proportional subset, or an explicit no-contract decision. The performance
  reference fixes p75 Core Web Vitals targets while keeping numeric asset
  ceilings project-specific and prioritized by surface type.

## [core][2.5.1] — 2026-08-08

### Changed

- **Bug investigations start from more of the language people actually use and
  stay evidence-led through exceptional cases.** The `bug-fix` skill now
  activates on root-cause requests, CI-only failures, intermittent or flaky
  behavior, and active production incidents without taking over new features,
  behavior-preserving refactors, postmortems, or skill maintenance.

  Multi-component failures are localized at their boundaries before the
  investigation narrows; a known-good path and backward data-flow trace feed
  the existing rival-hypothesis record. Asynchronous tests wait on a bounded
  real condition instead of sleeping. Three failed evidence-backed attempts
  stop patch stacking and surface an architectural discussion. External or
  timing failures can close without a false internal root-cause claim, while
  active harm permits labelled containment before analysis without presenting
  mitigation as the permanent fix. A production mutation requires confirmation
  of its exact action, scope, and blast radius unless already approved in the
  current turn; incident evidence is minimized and sensitive fields are redacted
  or sequestered. The early red regression test, minimum coherent diff,
  coverage-gap analysis, commit rationale, and tracker sync stay intact. The
  production-hotfix guide follows the same rule: containment is mitigation, and
  the permanent fix still returns to the red regression test.

## [core][2.3.1] — 2026-08-07

### Changed

- **Knowledge entries are no longer replayed into sessions automatically.**
  `session-start.py` printed every entry in `docs/knowledge/patterns.jsonl` to
  stdout, which Claude Code inserts into model context before the user's first
  prompt — and again on resume, clear, compaction and fork. Entries are captured
  by agents during the work-loop from material those loops encountered, so the
  hook turned one influenced session into a standing instruction for every
  session after it. The block is now rendered only when a caller passes
  `--show-knowledge`, which the wired hook does not; `tier: "invariant"`, which
  bypassed scope filtering and requested unconditional replay from inside the
  record itself, no longer grants anything. The adapt-to-project nudge is
  unaffected. If you relied on entries arriving at session start, render them
  deliberately with `session-start.py --show-knowledge [--scope <path>]`, or
  promote the durable ones into `AGENTS.md`, a skill, or an ADR — which is where
  guidance an agent must follow belongs.

- **Knowledge entries refuse control characters other than tab, and newline in `body`.**
  A hand-edited entry carrying `ESC`, `DEL`, a C1 character or a bare carriage
  return now fails `lint-knowledge.py`, where it previously passed — these are
  replayed verbatim into every session by the session-start hook, and a bare CR
  can overwrite a terminal line. Multi-line bodies and tabs are unaffected: a
  newline inside a JSON string is escaped on disk, so it never splits a JSONL
  line, and the hook indents multi-line bodies on purpose. A newline in `title`,
  `scope` or `source` *is* newly refused — the hook prints those on a single
  unindented line, where a newline forges an entry header — so fold it into the
  `body` or remove it. Also newly refused: a run of more than eight spaces or
  tabs in any field, which is how a payload is pushed off the side of a diff
  while still being replayed. If an entry trips any of these, rewrite the
  offending character out; there is no format migration.

  These rules guarantee that a reviewer sees what the model receives; they do
  not make replayed entries trusted. Entries are version-controlled and
  PR-reviewed, and that review remains the control.

### Security

- **The knowledge writer refuses invisible characters.** It rejected `Cc`
  controls only, so bidi overrides, the Unicode Tag block, and the variation
  selectors all passed — the last of those being 240 code points that encode
  arbitrary text at zero visual width. Since `session-start` replays every
  entry's title, scope and body verbatim into an agent's context (and a
  `tier: invariant` entry goes in regardless of scope), that was a durable
  prompt-injection channel invisible both in a diff and on screen. The rule is
  now Unicode's **Default_Ignorable_Code_Point** property, enumerated from
  `DerivedCoreProperties` rather than sampled by block. Sampling failed twice —
  `Cf` alone was bypassed by the variation selectors (`Mn`), and adding those
  was bypassed by the Mongolian free variation selectors, the same construct one
  block over. A total-volume budget sits beside the adjacency cap, since two
  joiners after every visible character never trip a run limit and still carry
  an arbitrary instruction. Both
  the writer and `lint-knowledge.py` enforce it from one shared predicate,
  because the file is hand-editable too. ZWJ, ZWNJ and the two emoji
  presentation selectors stay legal — they shape neighbouring characters — but a
  **run** of three or more adjacent zero-width characters is not, counting
  joiners and selectors together. Three is the threshold because real emoji cap
  at two adjacent (heart-on-fire is VS16 then ZWJ, as are the flag and
  bouncing-ball forms) while an alphabet needs many more; counting joiners alone
  left an alternating VS15/VS16 run invisible.

### Fixed

- **Concurrent appends no longer lose entries while reporting success.**
  Allocating `max(id) + 1` and then replacing the file is a read-modify-write;
  unlocked, six concurrent appends landed two entries and told all six callers
  their learning was recorded. The window is now serialized with a
  cross-platform lock. Note what makes it correct, since a first version got
  both halves wrong and did not exclude at all: a lock is broken only on
  evidence it is abandoned — its own age, never how long the waiter has waited,
  because a merely-slow holder still holds it — and it is released only if
  still owned, since a stale-breaker may have taken it over. The wait is
  bounded and reports rather than spinning on a lock it cannot remove.
- **Appending no longer narrows the knowledge file's permissions.**
  `mkstemp` creates `0600` and `os.replace` carried that onto the target, taking
  a committed world-readable file to owner-only. Git tracks only the exec bit,
  so it was invisible to review and CI. The target's mode is now preserved.
- **The knowledge linter cannot be hung by the input it exists to reject.** Its
  escape-detection pattern backtracked quadratically (measured 1.1s at 20k
  backslashes) and it runs unfiltered over a repo file in CI. Replaced with a
  non-backtracking pattern plus a line-length cap.
- **Status-regression detection now covers every verb that reads a pinned
  artifact**, not one of three. Normalizing the status token out of the hash
  removed the byte-compare that used to catch a spec regressing to `Draft`;
  the replacement assertion was only wired into `plan check-current`, so
  `approve-plan`'s already-approved branch and `schedule check-current` still
  passed such a spec.
- **Checkbox normalization is scoped by artifact.** It applied file-wide, so
  ticking a checkbox under a spec's `## Boundaries` — a `Never do` item,
  precisely the scope the pin protects — collided with the approved digest.
  A spec is now normalized inside its Acceptance Criteria section only; a plan,
  which has no such section and whose checkboxes are task progress, stays
  file-wide.
- **The hash-mismatch message no longer prescribes a recovery that fails.** It
  said to run `loop-cohort reset` and re-run the G-plan sequence, but that
  sequence has no `init` step, so `approve-plan` immediately refused; and it
  omitted that `loop-engine reset` must *not* be run. The five recovery steps
  are now spelled out in the message itself — an installed skill cannot point
  at this file, which adopters own as their own product's changelog.
- **The approval pin no longer breaks on the writes the loop itself mandates.**
  `loop-cohort approve-plan` pinned the raw bytes of `spec.md`, but `work-loop`
  requires writing `Status: Implementing` before any code and `Shipped` plus a
  ticked acceptance criterion at finish — so `plan check-current` went red one
  mandated step after approval, every run. `plan.md` had the same defect on a
  worse path: `schedule check-current` guards every `CODE-*` transition, so a
  plan `Status: Done` could wedge the state machine mid-EXECUTE. Both artifacts
  are now hashed through one canonical form that normalizes the preamble status
  *token* and checkbox bracket contents and nothing else. Substance stays
  pinned: acceptance-criterion text, task text, `Depends on:` edges, a
  `(deferred: <slug>)` annotation, a re-indented criterion, and any free text
  appended after the status token all still invalidate the baseline.

- **Knowledge entries have a writer, so the file stops drifting between
  encodings.** `docs/knowledge/patterns.jsonl` is line-delimited JSON, where
  both `\u2014` and a literal `—` are valid — so an author reaching for
  `json.dumps(entry)` (whose `ensure_ascii` defaults to `True`) silently changed
  the file's encoding while passing every gate, and for a non-BMP character
  emitted a surrogate pair that is not a valid TOML/YAML scalar downstream.
  `append-knowledge.py` now allocates the next id, writes raw UTF-8, confines
  its target, and lints the candidate before installing it, so a rejected entry
  never reaches the file. `lint-knowledge.py` rejects a `\uXXXX` escape for any
  character that should have been literal. Every C0 character bar tab (and a
  newline in `body`, which session-start indents) and every line
  separator (`U+0085`, `U+2028`, `U+2029`) is refused in **both** spellings:
  the literal form splits `str.splitlines()`, which is how the linter and
  `session-start` read the file, and the escaped form is worse — it survives
  the round trip intact, so it forges a line inside the block replayed into
  every session. The escape rule still exempts the three separators, but only
  so an entry carrying one gets a single clear error rather than two.
- **The knowledge-base guidance points at the privacy rule.** Capturing a
  learning is now a routine agent-authored commit into a permanent git
  artifact, and the author holds session context full of paths and identities,
  so all three authoring surfaces name `AGENTS.md` § Privacy alongside the
  encoding convention.

### Upgrading

A run already in flight when this lands carries a baseline pinned by the old
hash, which the new canonical form will not match. Recover with a **cohort-only**
reset — do not reset the engine, whose `plan-locked` transition is legal only
from `SPEC-PLAN-APPROVED`, so resetting it strands the run:

1. Restore `Status: Approved` in **both** `spec.md` and `plan.md`; `approve-plan`
   refuses unless both read `Approved`.
2. `loop-cohort reset <spec-dir>`, then `loop-cohort init <spec-dir> --run-id
   <run_id>`, taking `run_id` from `loop-engine status <spec-dir> --json`.
3. `loop-cohort approve-plan <spec-dir> --expect-run-id <run_id>`, then
   `loop-cohort schedule <spec-dir> --expect-run-id <run_id>`.
4. Restore the status you were on and continue.

Two things to know before you do it. Re-running `approve-plan` re-pins whatever
bytes are on disk — that is a re-approval in substance, so it is the plan
approver's call to re-affirm them, not something to self-serve. And the reset
returns `implementation_retry_count`, `review_round_count`, `review_retry_count`
and the recorded finding fingerprints to zero, so retry caps restart and stasis
detection loses its baseline.

## [core][2.3.0] — 2026-08-07

### Fixed

- **A nonexistent or non-directory `--root` no longer reports success.** `lint-spec-status` and
  `lint-traceability` accepted any path you gave them. Point either at a
  directory that does not exist and it scanned an empty tree and announced
  "spec metadata clean" — a green result that meant nothing. Both now refuse
  an unusable `--root` and name the offending path. A valid root, an omitted
  root, and a relative root all behave exactly as before.

- **A crafted `Contract:` header can no longer read files outside the repo.**
  `lint-spec-status` matched contract paths with a pattern that allowed `.` and
  `/`, so a spec file containing `- **Contract:** contracts/../../secret.json`
  made the linter read that file from outside the directory it was scanning and
  reveal, through which warning it printed, whether the file existed and roughly
  what it contained. A symlinked spec directory could escape the same way. Both
  are closed, and files are now size-capped before reading.

### Changed

- **Review fingerprints now use SHA-256** instead of SHA-1. These are internal
  markers used to notice when a review round returns the same findings twice;
  they are never shown to you. A run already in progress when you upgrade keeps
  working — its older markers stay valid.

- **Path arguments are validated where they enter.** The work-loop scripts
  already confined every file they read to within `--root`; that check now
  also happens at the point the argument is read. This is a legibility change
  for security scanners: the existing confinement runs across several
  functions, which taint analysers cannot follow, so scanners in adopter
  repositories reported path-traversal against code that was never vulnerable.
  No file the scripts would previously read is now out of reach.

  **Upgrade note:** an invocation that passed a nonexistent or non-directory
  `--root` used to exit 0 and now exits non-zero. If CI depends on that
  false pass, fix the path — the previous result was not a real check.

## [agentbundle][0.30.0] — 2026-08-08

### Changed

- **The wheel is about a fifth smaller, because it stops shipping the engine's
  own test suite.** It carried 45 test entries of 184 — a quarter of the
  uncompressed payload. The suite moved out of the importable package; the
  package itself did not move, so every import path except one is unchanged.

  The cause was not the obvious one. `setuptools`' package discovery defaults to
  PEP 420 namespace packages, so the tree was found whether or not it carried an
  `__init__.py` — deleting that marker would have removed exactly one entry of
  the forty-five.

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

- **`import agentbundle.build.tests` no longer resolves.** Nothing imported it;
  the module existed only to make a directory look like a package.

### Fixed

- **`build self --packs-dir <a fixture tree>` refuses again.** The
  destructive-write guard matched a fixed substring, so relocating the suite
  broke it silently and the command would have overwritten a working tree with
  fixture data. It now matches path components *and* the original substring, so
  it refuses strictly more than before.

- **`agentbundle catalogue self-host --write` now refuses a fixture packs
  path too.** That entry point takes its packs directory from
  `[catalogue.paths] packs` rather than a flag, and was never guarded — a
  catalogue pointing at a `tests/.../fixtures/` tree performed the same
  destructive overwrite. It now exits non-zero with a `CAT-SH-001`
  diagnostic, visible under `--format json`. This is a **new** refusal, not
  a restored one.

- **`catalogue init --preset self-hosted --tooling vendored` no longer copies
  test content into your repository.** The vendored copy is an install source —
  the command tells you to `pip install -e` it — so it is treated like the
  wheel. Your own packs and shared guides keep their tests, which is what
  catalogue archives are for.

  **Upgrade note:** if you vendored tooling from an earlier release, the engine
  tests, a stray `conftest.py`, and build residue (`__pycache__`,
  `.pytest_cache`, `*.egg-info`) are sitting in `.agentbundle/tooling/`. They
  are inert; deleting them is safe, and re-running `catalogue init` writes a
  clean copy — verified by running it, not inferred.

## [agentbundle][0.29.7] — 2026-08-06

### Changed

- **`catalogue init` stops handing you a `packs/AGENTS.md` full of dead links.**
  Six of its references pointed at files that exist only in the upstream
  catalogue, so the pack-authoring rules arrived without the means to follow
  them — including a test-layout rule credited to a linter you do not have.
  Every rule now stands on its own or points at a guide the scaffold ships, and
  a new gate fails the build if a future edit cites something unshipped.

## [credbroker][0.5.0] — 2026-08-06

### Added

- **Re-establish an expired SSO session from your own code.**
  `refresh_sso_session(profile)` re-captures without a human;
  `register_sso_session(...)` performs a first capture;
  `validate_sso_profile(profile)` is the shared grammar guard; and
  `derive_sso_destination(base_url, strategies=())` asks a resource server where
  it sends users to sign in (RFC 9728, then OIDC discovery, then an opt-in
  vendor probe). All four are additive.

  Derivation is an outbound fetch whose later targets come out of the server's
  own responses, so it is bounded hard: https-only at every hop, redirects not
  followed, a 5 s socket timeout under a 15 s budget, a 64 KiB body cap, strict
  TLS, no auth headers, and — for any hop that is not on your configured
  `base_url`'s origin — a refusal when the host resolves to loopback,
  link-local, RFC 1918 or another internal range.

  `refresh_sso_session` takes **only a profile**, deliberately: the signature is
  structurally incapable of forwarding a sign-in destination, so an automated
  caller cannot choose where the browser goes. `register_sso_session` is the sole
  function that accepts one.

- **New exception types**, so a caller can tell "your session expired" from
  "the broker failed": `SsoProfileNotRegisteredError` (subclasses the existing
  `SsoSessionUnavailableError`, so current handlers keep working),
  `SsoInteractionRequiredError`, `SsoRecaptureFailedError` and
  `SsoBrokerUnavailableError`.

### Changed

- **`load_sso_cookies` no longer hands your whole environment to the broker**,
  and no longer runs unbounded. It composes the child environment from an
  allowlist — so a spawned process cannot inherit an unrelated `*_API_TOKEN` —
  and applies a 30-second bound.

  **Behaviour change worth reading:** a timeout, a spawn failure, or an
  engine-internal error now raises `SsoBrokerUnavailableError` rather than
  `SsoSessionUnavailableError`. If your code retries or re-registers on the
  latter, a slow keychain no longer sends it down that path. Catch `SsoError` for
  the old blanket behaviour.

- `load_sso_cookies` validates the profile against the grammar before spawning.

## [credential-brokers][0.3.0] — 2026-08-06

### Changed

- **`sso-broker refresh` returns `4`, not `3`, when the profile was never
  registered.** A caller reading `3` as "not registered" was wrong: the engine
  returns it from a dozen distinct sites, including playwright being absent and
  a sign-in the operator did not finish. **If you read exit codes from this
  engine, re-read them.**

- **`sso-broker refresh` is now headless, and can return `5`.** It waits a
  bounded 20 seconds for a warm browser profile to complete the IdP flow
  unaided; if it cannot, it returns the new exit `5` instead of opening a
  window. **A `refresh` that used to prompt now fails fast** — by design: an
  unattended refresh must never leave a login page in front of whoever happens
  to be at the machine.

- **`sso-broker refresh` rejects every connection argument** (`--login-url`,
  `--success-url-pattern`, `--cookie-domain`, `--validation-endpoint`,
  `--session-filename`, `--ttl-hint-minutes`) with exit 3. Destinations come
  only from the stored profile.

- **`sso-broker register --ephemeral` changes where the session is captured.**
  Capture runs in a throwaway browser context which then *seeds*
  `browser-state/<profile>`, rather than capturing in that profile directly. A
  caller relying on `register` leaving a reusable profile now gets a seeded one.
  The verb's default is unchanged; `--ephemeral` is opt-in.

- **`profile` is validated and its store paths confined.** `register`,
  `get-cookies`, `test` and `refresh` refuse a name outside
  `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` or matching a Windows reserved device
  name. `rm` is exempt from the grammar so a profile registered under a
  now-invalid name stays deletable.

### Fixed

- **`get-cookies` served a stale cookie jar after every re-capture on macOS and
  Windows.** It materialised the jar only when the file was absent, while the
  primary store on those platforms is the OS keychain — so a successful refresh
  wrote to the keychain and the next read returned the pre-refresh file. Linux
  was unaffected (both surfaces are the same file there), which is why CI never
  caught it. The write is unconditional now, via a unique temp name per write.

## [atlassian][0.8.0] — 2026-08-06

### Added

- **`jira.py check` re-establishes an expired SSO session and retries, in one
  command.** No second step and no browser: the recapture is headless and takes
  no sign-in destination. If your identity-provider session has expired too,
  `check` stops with exit 2 and names the command to run — it never leaves a
  login page on screen.

- **`jira.py check --register`** captures a new session and completes the check
  in one command. It is the ordinary first run, and the only capture path that
  *attempts* to verify the sign-in destination against the instance — where the
  configured sign-in host is the instance host (SP-initiated SAML), that check
  short-circuits and confirms nothing. `scripts/setup_sso.py` remains for a
  scripted pre-bake and for the case where `--register` refuses.

### Changed

- **`--insecure` is honest on both auth paths.** On the token path **every
  subcommand** now warns whenever the flag fires, which they should always have
  done. On the SSO-cookie path it
  is inert — the session cookie is a bearer secret — and `check` says so rather
  than implying verification was disabled.

- **The SSO config loader rejects input it previously accepted**, in `jira` *and*
  `confluence-crawler`, which shares the file: a `profile` outside the broker
  grammar or supplied as a non-string, a non-integer `ttl_hint_minutes`, and any
  quote, backslash or control character in a `[sso]` string field. Control
  characters matter because URL parsing strips CR/LF before validation while the
  broker writes the value into a quoted TOML string.

- **`confluence-crawler`'s registration inherits the new spawn bounds** —
  timeout, whole-process-tree kill, and the environment allowlist — because
  `setup_sso.py` now calls `credbroker` instead of spawning the broker itself.

- **Both skills require `credbroker>=0.5.0`.** An older pinned install shadows
  the vendored floor; `check` on the SSO-cookie path detects it and exits 2 with
  the upgrade command.

- **Installing `atlassian` now requires the `credential-brokers` pack.** The
  install gate names the fix. Previously the install succeeded and failed at
  runtime with no remediation.

## [figma][0.3.0] — 2026-08-06

### Changed

- **Installing `figma` now requires the `credential-brokers` pack.** It ships a
  credentialed skill and has always depended on the broker layer; the dependency
  is now declared, so a missing broker is refused at install time with a named
  fix instead of failing at runtime. If you installed the library with `pip` but
  not the pack, the upgrade will refuse until you install the pack.

## [linear][0.2.0] — 2026-08-06

### Changed

- **Installing `linear` now requires the `credential-brokers` pack.** Same
  change, same reason, same upgrade-time refusal as `figma` above.
## [core][2.3.0] — 2026-08-07

### Fixed

- **Concurrent work-loop verbs no longer lose state silently.** Every verb that
  mutates `state.json` or `engine-state.json` wrote atomically but *decided*
  unguardedly, so two of them at once — a supervisor and a hand-run verb, or two
  agents in one workspace — overwrote each other with both callers exiting 0.
  Measured on the old code: two concurrent `record-attempt` calls lost an
  increment in 20 of 20 trials, so a retry cap could never fire; two concurrent
  `transition` calls were **both** admitted in 10 of 10 trials, where the second
  must fail `illegal transition`, leaving duplicate `(spec, seq)` records in the
  `.loop-run/events.jsonl` audit log; and six concurrent `init` calls all
  succeeded. Each verb now decides and writes while holding a lockfile beside
  the state file, so concurrent callers either both take effect or the loser is
  told why it did not.

- **A verb that cannot be sure its write landed now says so.** If a verb's lock
  is reclaimed while it is running, it exits non-zero naming the state file
  instead of reporting success — the one case where "it worked" would have been
  a lie.

### Changed

- Waiting for a busy state file is bounded and reported: a verb that cannot take
  the lock within 10 seconds refuses, naming the lock path and the process
  holding it. A lock left by a killed process is reclaimed automatically after
  **5 minutes**; to clear one sooner, delete the `.lock` file beside the state
  file it names. A lock path that is not a regular file (a stray directory or
  symlink) is refused immediately rather than waited on. Lockfiles and their
  reclaim residue are gitignored, including for new adopters.

## [agentbundle][0.29.5] — 2026-08-06

### Changed

- **`catalogue self-host --windows` can no longer report a pass it did not
  earn.** It runs the atlassian SSO suites from the packs' test trees now, and
  probes `credbroker` and `httpx` first. Both suites skip themselves at import
  when those are missing, and the step runner judges by exit code alone — so on
  a machine without them, both suites skipped silently and the step went green.
- Three suites whose subject was pack content moved out of the package's test
  tree to the packs that own them. A pack edit could otherwise turn the
  published package's suite red.

### Fixed

- **`catalogue package` stops shipping build residue.** If you had ever run the
  tests or an `npm install` in a skill before packaging, the archive carried the
  resulting `__pycache__`, `.pytest_cache` and `node_modules` — the deny-set
  meant to prevent it was never applied. 104 files on this catalogue. Your
  archives get smaller and match what the authoring standards say they contain.
  Packaging also no longer *fails* on a tree with a real `node_modules` in it —
  the symlink check refused its `.bin/` entries. No flag, verb, exit code, or
  schema changed.

## [architect][0.14.3] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

  For `architect-diagram` this also removes `scripts/` entirely — it held
  nothing but the fixture suite and its `.mmd` corpus.

## [atlassian][0.7.1] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

## [catalogue-curation][0.2.3] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

## [converters][0.9.4] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

  `msg-to-markdown`'s `## Scripts` list drops its test-material bullet, since
  those files are no longer in the skill.

## [credential-brokers][0.2.3] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

## [desk-research][1.1.4] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

  The `desk-research` skill body no longer cites a repository path for its
  closed cue tuples — that path did not exist in your tree.

## [figma][0.2.3] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

## [governance-extras][0.9.6] — 2026-08-06

### Changed

- **Tests no longer ship into your skills tree.** Projection adapters copy
  `.apm/skills/<skill>/` wholesale, so every test file this pack kept under
  `.apm/` was being written into your tree on install. They now live at
  `packs/<pack>/tests/`, which is never projected. Nothing you invoke changed —
  no skill, script, command, hook, reference or eval was removed, renamed, or
  edited. If you have an older install, the stale `test_*.py` files under your
  installed skills are safe to delete.

## [agentbundle][0.29.4] — 2026-08-06

### Changed

- **The package's test tree is catalogue-level only.** Suites whose subject was
  pack content — core's hook bodies, skill bodies and `work-loop` scripts, and
  the `product-documentation` pack check — moved to the owning pack's `tests/`
  tree. They tested pack content that happens to share a repository with the
  engine, so renaming a private helper in a pack could turn the published
  package's suite red. Engine tests that *use* a pack as fixture data (install,
  upgrade, projection, adapter parity) are unaffected: the distinction is
  subject, not mention. `README-pypi.md` gains the `tests/` tree and the
  three-boundary model. No flag, verb, exit code, schema, or output changed.

## [agentbundle][0.29.3] — 2026-08-05

Wording-only release. No flag, verb, exit code, schema, or output *structure*
changed — but the text an adopter reads changed almost everywhere, so it ships
as its own version rather than riding along with the next feature.

### Changed

- **Internal governance citations removed from every shipped surface.** The
  package previously carried `RFC-0NNN` / `ADR-0NNN` ordinals, internal
  acceptance-criterion labels (`AC7`, `AC22b`), and `docs/specs/<slug>` paths
  throughout. Those point at documents no adopter has — a dangling reference in
  the sdist, which ships source, and in the wheel. Each now states the rule
  directly instead of citing where it was decided: `# RFC-0052 D8: v0.3 state is
  hard-refused` became `# v0.3 state is hard-refused`. Roughly 2,700 occurrences
  across ~290 files. Specifically:

  - **`--help` output** for the root command and every subcommand — `install`,
    `upgrade`, `uninstall`, `catalogue`, `catalogue lint`, `init-state`,
    `reconcile`, `diff`.
  - **Runtime diagnostics**: `catalogue lint`'s three findings, the
    `init-state --migrate` message, `commands/install.py`'s short-circuit
    notice, and the workspace-mcp git errors.
  - **The bundled adapter contract** (`_data/adapter.toml`), whose comments are
    read from inside the wheel. Its per-version history was restructured from an
    RFC-keyed list into a version-keyed one; every declared value is unchanged
    and the file remains byte-identical to `contracts/adapter.toml`.
  - **Source comments and docstrings** across the engine, and the 46 files under
    `agentbundle/build/tests/` that land on disk on every `pip install`.
  - **`templates/install-marker.py`**, which projects into the adopter's own
    repo. Re-installing or upgrading will rewrite it with the new comments; the
    file's behaviour is unchanged, and the existing Tier-1/Tier-2 machinery
    handles it as it would any projected-file content change.

  IETF references are untouched — `RFC 9106` in the credential broker survives
  byte-identical. Ours are zero-padded four digits; IETF numbers never start
  with `0`.

### Fixed

- **`init-state --migrate` printed a stranded token.** The message read
  `Migration is greenfield D8) — reinstall…`, with an unmatched parenthesis.
  It now reads `Migration is greenfield — reinstall the pack(s) to regenerate
  state instead.`

- **`catalogue lint` contradicted itself on `patterns.jsonl`.** The refusal for
  a non-empty knowledge seed told the operator to "seed the file with a
  placeholder entry" — the exact thing it had just refused. It now says the file
  must carry no entries at seed time.

- **The codex `AGENTS.md` strip warning over-promised recovery.** It claimed the
  removed region was recoverable from git history; it now says that holds only
  if the file was committed.

### Added

- **A behavioural test for projection exclusion.** `_is_excluded`'s existing
  coverage only exercised the glob→regex translation against synthetic strings,
  so it stayed green if a caller stopped consulting the guard. The new test
  drives a real file at an excluded path through `run_self_host` and asserts it
  is absent from the unclassified-path enumeration.

## [credbroker][0.4.1] — 2026-08-05

Wording-only release; no library code changed. It exists so the corrected PyPI
project page and the swept docstrings actually reach installers.

### Changed

- **Internal governance citations removed from the shipped text.** The two
  design-doc links on the PyPI project page keep their working URLs and lose
  only the `RFC-00NN` prefixes from their link text, so the page reads for
  someone with no access to our numbering. Package docstrings and comments were
  swept on the same principle.
- **`RFC 9106` is deliberately retained** in `_vault.py` — that is the Argon2
  IETF specification, not one of ours, and it survives byte-identical.

## [agentbundle][0.29.2] — 2026-08-05

### Fixed

- **`self_host` — preferred-adapter respected**: `run_self_host` now restricts
  projection to the adapter named in `catalogue.toml`'s `preferred-adapter` field
  when that adapter is not in `SELF_HOST_ADAPTERS` (e.g. `kiro-ide`). Previously
  only `claude-code` and `codex` were ever projected, producing false drift for
  downstream repos using a different adapter.

- **`self_host` — shadow-clone and seed-copy paths use `shutil.copy`**: neither
  calls `os.utime`, fixing CI environments that restrict timestamp writes.
  `shutil.copy` (content + permissions, no timestamps) preserves source mode
  bits so the drift gate never false-positives on permission bits — `copyfile`
  would produce umask-derived mode on new files and cause spurious drift in
  strict-umask CI environments. Symlinked seeds are now dereferenced rather
  than copied as links (prior behavior was `follow_symlinks=False`).

- **`adapter_root_bins` — `shutil.copy2` replaced with `shutil.copyfile` +
  `os.chmod` guarded with `try/except OSError`**: the bin-projection path no
  longer calls `os.utime`; POSIX executable-bit setting is now best-effort so
  environments that restrict `chmod` do not abort the build.

- **`self_host` — Claude-specific artifacts omitted for non-claude-code repos**:
  `CLAUDE.md` and `.claude-plugin/marketplace.json` are no longer written (or
  drift-checked) when the effective adapter set does not include `claude-code`.
  Downstream repos with `preferred-adapter = "kiro-ide"` (or any adapter not in
  `SELF_HOST_ADAPTERS`) no longer accumulate Claude-specific files on `--write`
  and no longer see false drift on `--check`.

## [agentbundle][0.29.1] — 2026-08-05

### Fixed

- **`workspace_mcp._GitTools` — FSM mode guard**: `git_branch`, `git_commit`, and
  `git_push` are now blocked whenever `WORKSPACE_MCP_SPEC_PATH` is supplied —
  including when `WORKSPACE_MCP_DISPATCHED_ITEM` is also present (SPEC_PATH wins
  with a startup warning) and when the path fails containment validation
  (fail-closed: raw env var presence in `os.environ`, including an empty string,
  is the FSM trigger). Previously a stale harness supplying both vars, or an
  invalid SPEC_PATH, left FSM mode disabled and enabled git writes during a
  work-loop session. **Requires agentbundle >= 0.29.1** — updating the `core`
  pack alone does not deliver this fix.

- **`workspace_mcp._build_tools_list`**: refined git tool descriptions for
  harness clarity; `shaping[]` items marked informational-only in Stage 1.

## [core][2.2.1] — 2026-08-06

### Fixed

- **A failed fetch is no longer misreported as a wrong branch name.** The
  work-loop's base-freshness check classified *any* fetch failure whose stderr
  mentioned "remote ref" as "branch not found on remote" — and a remote URL
  containing that phrase is enough to trip it. The agent then went off to
  correct a `--target` that was never wrong, while the actual auth or network
  fault went unreported. Only git's own not-found wording now selects that
  message; everything else falls through to `check network/auth`. That wording
  is a gettext string, so every git subprocess the check runs now sets
  `LC_ALL=C` — on a git build with translation catalogues installed the match
  would otherwise never fire.
- **A dirty tree is told to commit, not to stash.** `refs/stash` is not a
  per-worktree ref, so every linked worktree of a repository shares one stash
  stack — work stashed in one worktree is visible, and poppable, from all the
  others. The check now recommends committing the work in progress on the
  current branch before rebasing, says why, and names the unwind
  (`git reset --soft HEAD~1`). The untracked/tracked distinction is kept: it
  selects between `git add -A` + commit and `git commit -a`. The suggested
  subject is `chore: wip`, so the command survives a `commit-msg` hook.
- **The unmerged-files message no longer implies committing is unavailable.**
  `git stash` refuses an unmerged index, but `git commit -a` succeeds and
  commits the conflict markers — and it is the command the sibling branch now
  recommends. The message names both.
- **An unreadable commit count fails closed.** When `git rev-list --count`
  exited 0 with output that was not a number, the count fell back to `0`, which
  the next line reported as "head is current" — the one answer this check must
  never give by accident. It now Surfaces instead.

### Changed

- **The pack no longer tells you to stash, anywhere.** Three surfaces still
  did, which left the guidance self-contradictory once the freshness check
  stopped. `work-loop`'s pre-existing-failure triage replaces the **stash-check**
  (`git stash -u && <gate> && git stash pop`) with a **worktree-check** —
  `git worktree add --detach`, run the gate there, remove it — which answers the
  same question without touching the shared stack; the dependency caveat and the
  commit-first fallback are named. `adapt-to-project`'s dirty-state escalation
  offers committing rather than "stash or commit".

## [core][2.2.0] — 2026-08-06

### Added

- **The knowledge-base linter ships with the pack.** `lint-knowledge.py` now
  lives beside the other `work-loop` scripts and projects into your tree at
  `<skills-dir>/work-loop/scripts/`. Its self-test stays in the catalogue. `docs/knowledge/patterns.jsonl`
  is seeded by this pack and appended to by the work-loop's Capture-learnings
  step, so the gate that validates it ships with it. Previously the linter was
  catalogue-local: the seeded README told adopters to run a script they had
  never been given.
- **`pre-pr.py` gates the knowledge base automatically.** The shipped hook
  finds `lint-knowledge.py` under whichever skills root your agent tool
  installed into and runs it over `docs/knowledge/patterns.jsonl` — nothing to
  wire by hand. Skipped cleanly when the file or the skill is absent.

  **Upgrading from 2.1.x:** this gate is new and strict — it rejects unknown
  keys as well as missing ones. If you added a field of your own to
  `patterns.jsonl`, the first `pre-pr.py` run after upgrading will fail on it.
  Fold the extra data into `body`, or drop the field.

### Fixed

- **`work-loop` § Capture learnings now states the knowledge-entry schema
  inline.** The step pointed at `docs/knowledge/patterns.jsonl` and deferred
  the shape to a second file, so entries were authored from memory and landed
  without the required `source` key. The six required keys — `id`, `kind`,
  `scope`, `title`, `body`, `source` — plus the optional `tier`, and a
  one-line example entry, are now written at the point of writing.
- **Verification is explicit at every surface.** `work-loop`,
  `docs/knowledge/README.md`, and its seed tell the writer to run the gate
  **unfiltered** and read its exit code. `<gate> | tail -2` returns *tail's*
  exit status — always 0 — and truncates the per-entry error lines, so a
  broken entry reads as clean locally and fails in CI. The general form is now
  a `work-loop` anti-pattern: never judge a gate through `tail` or `grep`.
- **A drift guard covers the guidance, not just the schema.** The linter's
  self-test now fails when any surface that tells a writer to author an entry
  omits a required key from its inline list, or carries an example that does
  not lint clean — the pack source, both projections, and the seeded README.

## [core][2.1.1] — 2026-08-04

### Added

- **Pack documentation**: added autonomous-dispatch section to `JOURNEY.md` and
  headless-mode pointer to `README.md`.

### Notes

- The workspace-mcp FSM git guard (blocking `git_branch`/`git_commit`/`git_push`
  in FSM mode) is delivered by **agentbundle 0.29.1**, not by this pack update.
  This pack's server wrapper imports whichever `agentbundle.workspace_mcp` is
  installed — update agentbundle to >= 0.29.1 to get the fix.

## [experience-design][2.0.0] — 2026-08-02

### Added

- **`copy-direction` skill added to the `experience-design` pack.** New skill for naming the copy direction for a specific marketing or acquisition surface — ranked copy goals grounded in stable referents (persona language, copy precedents, persuasion standards), plus copy arbitration rules for that surface. Copy twin of `creative-direction`: same 8-step interrogation rhythm applied to what a surface *says* rather than how it *looks*. Scope: per-surface acquisition copy positioning (hero headlines, above-fold narrative, taglines, announcement copy, onboarding copy voice). References: `tone-of-voice` brand-register doc as optional upstream anchor; writes `copy/<surface-slug>.md` with `type: copy-direction`. ([spec](../specs/xd-copy-direction/spec.md))

### Changed

- **`tone-of-voice` re-scoped to brand-level cross-surface register.** `tone-of-voice` now names the brand-level copy register — the cross-surface voice personality that all per-surface copy decisions reference — rather than per-surface acquisition copy positioning. Output path changed from `copy/<slug>.md` (per-surface slug) to `copy/brand-register.md` (stable brand-level doc). Per-surface acquisition copy positioning (hero headlines, above-fold narrative, taglines, announcement copy, onboarding copy voice) now belongs to the new `copy-direction` skill. The `content-design` and `ux-writing` boundary notes updated accordingly. ([spec](../specs/xd-copy-direction/spec.md))

## [product-engineering][0.13.3] — 2026-08-02

### Changed

- **`ux-writing` boundary note updated: onboarding copy voice routes to `copy-direction`.** The `ux-writing` skill's scope boundary note now routes per-surface marketing/acquisition copy voice — including onboarding copy voice — to `copy-direction` (experience-design pack) rather than `tone-of-voice`. The onboarding tri-point (`content-design` / `copy-direction` / `ux-writing`) is now explicit in the boundary note. ([spec](../specs/xd-copy-direction/spec.md))

## [core][2.1.0] — 2026-08-04

### Added

- **`workspace-mcp` Stage 1 — per-session MCP server.** New `agentbundle.workspace_mcp` module provides a per-session stdio MCP server exposing six tools: `workspace_status`, `elicit`, `git_status`, `git_branch`, `git_commit`, `git_push`. The event bridge polls `.loop-run/events.jsonl` and emits `_agentbundle.core/skill-state-change` and `_agentbundle.core/human-gate-pending` MCP notifications on FSM transitions. The `workspace-status` alias script is projected to `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py`. Requires Python 3.11+, stdlib only. ([spec](../specs/workspace-mcp/spec.md))

## [core][2.0.1] — 2026-08-02

### Added

- **`workspace-status` deterministic repair planning (Order 2B).** Two new subcommands —
  `repair-plan` and `repair-apply` — automate cleanup of stale Type 2 queue entries without
  manual `workspace.toml` editing. `repair-plan` runs a full reconciliation scan, builds a
  deterministic plan for all automatically-resolvable findings (Shipped → move to `[work].shipped`;
  Archived → remove from `[work].queue`), and writes a plan file with a SHA-256 fingerprint.
  `repair-apply` verifies the fingerprint, re-reads each spec's Status from disk at apply time,
  and writes atomically via `tempfile.mkstemp`. The `Approved` lifecycle invariant is preserved —
  Approved entries are never automatically touched. Type 1, Type 3, and `active`-list entries
  appear in `manual_findings` for human review. See SKILL.md §1b for the full two-step workflow.

## [core][1.0.4] — 2026-08-01

### Changed

- **`work-loop` Step 0 no longer scans the full portfolio for stale entries (Order 2A).**
  The stale-queue check — which read every `queue` and `active` spec.md to detect
  `Status: Shipped` drift on every `work-loop` invocation — is removed. `work-loop` now
  orients only (initiative, milestone, active spec, shaping guard). For exhaustive workspace
  integrity checks (stale entries, untracked live specs), run
  `workspace-status reconcile`. The same stale fixtures are still detected as Type 2 findings
  by `analyze()` — behavior moves, not disappears.

## [core][1.0.3] — 2026-08-01

### Added

- **`workspace-status` progressive read modes (Order 1B).** The `workspace-status` skill now
  exposes three explicit subcommands: `status` (bounded — Type 2 + 3 only, O(declared entries)),
  `reconcile` (exhaustive — Type 1 + 2 + 3, same as prior behavior), and `explain --item
  <selector>` (focused in-memory lookup for one item). `status` is now the default invocation in
  SKILL.md. JSON output gains `mode`, `scan.*`, and `reconciliation.{performed,complete,
  types_performed}` fields. Invoking without a subcommand still works as a `reconcile` alias
  with a deprecation warning on stderr.

## [core][2.0.2] — 2026-08-03

### Changed

- **work-loop** — doctrine additions and hardening to `SKILL.md`:
  - **Base freshness check** (new, before Step 0 ORIENT): run `python scripts/check-base-freshness.py` to fetch the merge target and check staleness. Exit 0: head is current. Exit 1: Surface — message includes the exact `git rebase` command to run. Handles single-remote auto-detect, explicit `--target REMOTE/BRANCH` for forks and stacked PRs, rebase-in-progress detection, detached HEAD, and SSH batch mode when no custom transport is configured.
  - `Surface` verb: recovery rung taxonomy added (steer / rerun / salvage in cost order) — every surface event must name the minimum viable rung.
  - Visual/manual QA: per-task UI check cadence — check after each task that modifies user-visible state, not just at finish.
  - DECIDE: execution-path check before routing any finding to `apply`.
  - DECIDE: scratch-note discipline — after routing each finding, save a one-liner to the IDE's native scratch; feeds Capture learnings.
  - Capture learnings: write the generalizable lesson; review scratch notes from DECIDE passes; promote to `docs/knowledge/patterns.jsonl` when generalisable.
  - Finish checklist: trust the running artifact, not the build exit code.
  - FIX items 2 and 3: shape-based split and own-fix adversarial verification.
- **work-loop evals** — two evals updated to require naming the minimum viable recovery rung.
- **`docs/knowledge/README.md`** — curation contract changed from append-only to living-doc: edit, remove, or promote entries as the codebase changes; git history is the record.
- **`docs/knowledge/patterns.jsonl`** — schema extended: optional `tier` field (`invariant` | `observation`, default `observation`); multi-glob `scope` (comma-separated). `tier: invariant` entries are injected unconditionally by session-start regardless of `--scope`.
- **`tools/lint-knowledge.py`** — validates `tier` and multi-glob `scope`; type-guards both fields against non-string values and explicit null; reports all errors on a line in one pass.
- **`tools/hooks/session-start.py`** — tier-aware injection and multi-glob scope matching.
- **`packs/AGENTS.md`** / **`packages/AGENTS.md`** — symlink-copy security rule added; both scopes covered.

## [core][2.0.0] — 2026-08-02

### Changed

- **loop-engine/loop-cohort** (breaking): Replaced the single `SPEC-PLAN-HUMAN-GATE` state and the combined `plan-approved` exit event with two separate human-wait states and a three-event approval sequence. Any `engine-state.json` parked at `SPEC-PLAN-HUMAN-GATE` from core 1.x will return "illegal transition" on every event after upgrade — reset with `loop-cohort reset` + `loop-engine reset` and re-init on the new sequence (spec.md and plan.md are preserved).
  - New states: `SPEC-HUMAN-GATE` (scope decision; spec approver writes `spec.md Status: Approved`), `PLAN-HUMAN-GATE` (build decision; plan approver writes `plan.md Status: Approved`), `SPEC-PLAN-APPROVED` (durable intermediate after both approvals).
  - New events: `spec-approved` (guard: spec.md Approved), `spec-rejected` → SPEC-PLAN-DRAFTING, `plan-locked` (replaces the old single-step plan-approved handoff; guard: spec Approved + schedule binding).
  - `plan-approved` now means "plan approver approved" and targets SPEC-PLAN-APPROVED; the old meaning (machine handoff to CODE-IMPLEMENTATION) is replaced by `plan-locked`.
  - `loop-cohort approve-plan` is now idempotent: same run ID + unchanged hashes = no-op; changed hash = refuse.
  - `check-spec-status.py` gains `--expect` and `--file` flags so the plan-approved guard can check plan.md independently. Path traversal fixed: `--file` is now confined to spec-dir.

## [governance-extras][0.9.5] — 2026-08-02

### Changed

- Updated core dependency constraint from `^1.0` to `^2.0`. No skill or agent changes.

## [iac-terraform][0.1.6] — 2026-08-02

### Changed

- Updated core dependency constraint from `^1.0` to `^2.0`. No skill or agent changes.

## [monorepo-extras][0.1.6] — 2026-08-02

### Changed

- Updated core dependency constraint from `^1.0` to `^2.0`. No skill or agent changes.

## [release-engineering][0.1.9] — 2026-08-02

### Changed

- Updated core dependency constraint from `^1.0` to `^2.0`. No skill or agent changes.

## [Unreleased]
### Added

- **58 guide pages that were published but unreachable now appear in the docs
  site navigation.** The sidebar was a hand-maintained list in
  `docs-site/astro.config.ts` carrying 119 entries against 177 navigable files,
  so adding a page and forgetting the config edit was the default outcome. It is
  now generated from the guides tree on every build — writing the file is all
  that navigation requires. Group labels and order are declared in `site.toml`'s
  new `[[guide_groups]]` table.

- **Guides can now be read as a sequence rather than a taxonomy.** A page's
  `order` frontmatter sorts it within its pack group *across* Diátaxis kinds, so
  a tutorial, a how-to and an explanation can form one reading path. The
  `iac-terraform` pack ships the first: a three-part explanation of how
  infrastructure work runs through the release loop.

### Changed

- **Diátaxis buckets now render in a consistent Tutorials → How-to → Reference →
  Explanation order** in every guide group. Bucket order previously varied by
  pack; 11 of 17 groups change. Page labels are unchanged — the pre-generation
  labels are frozen in `guide-nav-baseline.toml` so none regressed.

### Fixed

- **Installing a pack from the marketplace now delivers its skills, agents and
  commands.** Previously `claude plugin install <pack>@agent-ready-repo`
  reported success and installed an empty plugin — `claude plugin details`
  showed `Skills (0) Agents (0) Hooks (0)`. Two defects caused it. The
  marketplace entry used a `github` source with `branch` and `directory` keys,
  which Claude Code's `github` source does not support: both were silently
  dropped and the installer cloned the repository's default branch at its root.
  Entries now use a `git-subdir` source with an explicit clone URL, `path` and
  `ref`. Separately, components were published under `<pack>/.claude/`, but
  plugins load `skills/`, `agents/` and `commands/` from the plugin root; they
  are now published there. Verified against Claude Code 2.1.223: `core` reports
  Skills (13), Agents (4), Hooks (1). The install commands are unchanged.

  **If you already added this marketplace**, run
  `claude plugin marketplace update agent-ready-repo` and reinstall your packs —
  a cached catalogue keeps serving the old entries.

- **Marketplace entries are now validated in CI.** Nothing checked them before:
  the build strips `source` from `plugin.json` before validation, and the
  verifier inspected `marketplace.json` only for a stray `hooks` key. Both the
  published and the repo-root marketplace now validate every entry against a
  dedicated schema, so a malformed `source` fails the build instead of reaching
  adopters.


### Added

- **`work-loop` Phase-1 loop-infrastructure split (core 1.0.0 — major).** The work-loop
  tooling is split into two scripts with a hard boundary. `loop-engine.py` is a pure FSM
  phase tracker (read-only except `init`/`transition`/`reset`; owns `engine-state.json`)
  with two modes (`code`, 13 transitions; `spec-plan`, 5 transitions). `loop-cohort.py`
  is rewritten as the sole writer of `state.json`; new verbs include `identity`,
  `plan check-current [--require-schedule]`, `record-attempt`, `wave check`, `wave
  advance`, and `review inspect`. `check-spec-status.py` guards the `reviewers-clean`
  event in code mode. A `run_id` UUID generated at engine `init` is shared between both
  state files and verified on every mutating call via `--expect-run-id`. Phase-1 parallel
  verbs (`worktree`, `dispatch-decision`, `auto-parallel`) are disabled — they exit
  non-zero. The `pre-pr.py` enforcement hook now reads `engine-state.json` to skip the
  `check --phase review` cap check when the FSM is not in `CODE-REVIEW` (avoids false
  positives during `CODE-IMPLEMENTATION` and after `CODE-HUMAN-GATE`/`DONE`).
  **Breaking changes (version classification: major):** `worktree`
  subcommands are disabled (they exit non-zero). Dependent packs governance-extras (0.9.4), iac-terraform
  (0.1.5), monorepo-extras (0.1.5), and release-engineering (0.1.8) updated their core
  constraint from `^0.1` to `^1.0`.

- **governance-extras 0.9.4** — patch: updated core dependency constraint from `^0.1` to `^1.0` to track the core 1.0.0 major release. No skill or agent changes.

- **iac-terraform 0.1.5** — patch: updated core dependency constraint from `^0.1` to `^1.0` to track the core 1.0.0 major release. No skill or agent changes.

- **monorepo-extras 0.1.5** — patch: updated core dependency constraint from `^0.1` to `^1.0` to track the core 1.0.0 major release. No skill or agent changes.

- **release-engineering 0.1.8** — patch: updated core dependency constraint from `^0.1` to `^1.0` to track the core 1.0.0 major release. No skill or agent changes.

- **`agentbundle` 0.27.0 — `[[pack.integrations]]` convention**: packs can now
  declare optional cross-pack behavior seams in `pack.toml`. The new
  `[[pack.integrations]]` array (governed by `contracts/pack.schema.json`) carries
  ten fields: `id`, `pack`, `kind` (`input`/`augment`/`review`/`handoff`), `role`,
  `consumers`, `providers`, `when`, `purpose`, `fallback`, and an optional `version`
  semver range. `agentbundle catalogue verify` validates integration refs (uniqueness,
  primitive resolution, self-target prohibition, semver range grammar, provider
  presence when the target pack is in the same catalogue). `agentbundle show <pack>`
  surfaces declared integrations in table and JSON output. Five first-party integration
  entries ship across `packs/core` (two, targeting `frontend-engineering`) and
  `packs/governance-extras` (three, targeting `desk-research`, `product-engineering`,
  and `architect`).

- **`agentbundle` 0.26.1 — bundled schemas**: the wheel now bundles
  `guide.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`, and
  `target-vocab.toml` from the canonical `contracts/` source (plus corrected
  `profile.schema.json` annotations). Enables offline skill and guide validation
  without network access to the source catalogue.
- **Catalogue authoring standards hub**: `guides/_shared/reference/catalogue-authoring-standards.md`
  is now part of the init scaffold — a portable routing table to every authoritative
  contract and authoring guide, available in every `agentbundle catalogue init`
  output.
- **Contract parity gate**: `tools/catalogue/check_contract_parity.py` added to the
  `build-check` chain, verifying that every contract in `contracts/` is byte-identical
  to its `agentbundle/_data/` counterpart on every PR.
- **`agentbundle catalogue init --preset self-hosted`**: enterprise-derived catalogue
  initialization. Copies selected packs, profiles, and guides from a source catalogue;
  generates a new `catalogue.toml` with target identity fields; runs a fail-closed leak
  check. Two tooling modes: `external` (curation installed separately) and `vendored`
  (agentbundle source and curation copied into `.agentbundle/tooling/` for air-gapped
  deployments). Two identity modes: `white-label` (zero upstream trace) and `attributed`
  (upstream declared in designated surfaces only). Replaces the former `export-catalogue`
  skill.
- **`agentbundle catalogue package --flavor source`**: source-distribution packaging for
  self-hosted catalogues. Produces a versioned `catalogue-source-<release>.tar.gz` from a
  positive allowlist with per-file SHA-256 digests and a `self-hosted-source-manifest.json`.

### Changed

- **`catalogue-curation` pack 0.2.1**: `assimilate-primitive` lint gate updated from
  `lint-agent-artifacts` (deleted at v0.13.0) to `agentbundle catalogue verify`; stale
  `_Depends on core + governance-extras` footer removed (those deps were dropped in 0.2.0).

- **`catalogue-curation` pack 0.2.0**: `export-catalogue` skill removed (superseded by
  `agentbundle catalogue init --preset self-hosted`). Hard dependencies on `core` and
  `governance-extras` removed — the three remaining skills operate portably against the
  target catalogue's own contracts.

- **Atlassian pack — complete Product Documentation pilot (Phase 3).** The `atlassian` pack is now the first end-to-end pilot of the Product Documentation architecture. Six connected public surfaces ship together: a 17-step tutorial (whole-team backlog → story improvements → Jira writes → stand-up summary), a 7-task how-to, a skills reference covering all 11 skills, a system-model explanation, a retrofitted pack README, and a four-stage JOURNEY.md. All six surfaces share one canonical Team Atlas scenario (184 issues, canonical IDs APP-206/APP-219/API-104) and use the Phase 2A flat-source-path model with `slug:` frontmatter to preserve public URLs. `packs/atlassian/JOURNEY.md` is the pack-owned journey source; version stays at 0.7.0 (documentation-only; no skill content changed).
- **Pack-owned canonical journeys (Phase 2B).** Packs can now define their primary
  journey in `packs/<pack>/JOURNEY.md`, the canonical source that generates the
  central Astro content file. `tools/build-site.py --journeys-only` syncs pack-local
  journeys before the web build; `pages.yml` runs this step automatically in CI.
- **`lint-pack-journeys.py`** — new validator for `packs/*/JOURNEY.md` files;
  enforces `journey_id`, skill existence and count, state vocabulary, write-stage
  `You decide` requirement, dual-ownership detection, and duplicate ID detection.
- **State vocabulary** — nine machine-readable state values (`read-only`, `draft`,
  `proposed-write`, `confirmed-write`, `publish`, `destructive`, `no-action-required`,
  `decision-required`, `blocked`) with enforcement in `lint-pack-journeys.py`.
- **`product-documentation` pilot migration** — `packs/product-documentation/JOURNEY.md`
  is the first pack-owned journey. The central file is now generated from the pack source;
  the URL (`/journeys/product-documentation/`) is unchanged.
- **Maintainer how-to** at `guides/_shared/how-to/pack-journey-authoring.md` — covers
  when to add `JOURNEY.md`, the full frontmatter contract, stage contract, state
  vocabulary, skill validation, route preservation, installation exclusion, migration
  procedure, and dual-ownership rules.

## [core][1.0.2] — 2026-08-01

### Changed

- work-loop Step 0: remove "Exactly one →" sub-item from the Active spec bullet; add inline echo instruction so the orientation block surfaces "Beginning on `docs/specs/<slug>/spec.md`" alongside Initiative and Milestone output. Remove unreachable "Zero or multiple active items → stop after surfacing" bullet from the closing paragraph. Adds three evals covering Branch-1 (echo), Branch-2 (zero), and Branch-3 (multiple).

## [core][1.0.0] — 2026-07-31

### Added

- **`loop-engine.py`** — new Phase-1 FSM phase tracker for the work-loop. See `[Unreleased]` for full detail.

### Changed

- **`loop-cohort.py`** — Phase-1 rewrite with new verbs and split counter semantics. See `[Unreleased]`.

### Removed (breaking)

- **`worktree` subcommands** — disabled in Phase 1; all exit non-zero.

## [core][1.0.1] — 2026-07-31

### Changed

- **`work-loop` session-resumption table: `reviewers-clean` row consequence language.**
  The `reviewers-clean` row now explicitly names double-increment of `review_round_count`
  and overwrite of fingerprint audit history as consequences of replaying
  `review record --report` without authorization.

## [release-engineering][0.1.8] — 2026-07-31

### Changed

- Core dependency constraint updated from `^0.1` to `^1.0`.

## [monorepo-extras][0.1.5] — 2026-07-31

### Changed

- Core dependency constraint updated from `^0.1` to `^1.0`.

## [iac-terraform][0.1.5] — 2026-07-31

### Changed

- Core dependency constraint updated from `^0.1` to `^1.0`.

## [governance-extras][0.9.4] — 2026-07-31

### Changed

- Core dependency constraint updated from `^0.1` to `^1.0`.

## [product-documentation][0.1.0] — 2026-07-28

### Added

- **New pack: `product-documentation`.** Replaces `user-guide-diataxis` as the documentation authoring primitive. Installs the `author-product-docs` skill — a single entry point for five modes: **create** (new guide or README), **revise** (update an existing artifact), **retrofit** (reconnect a fragmented doc set to its Diátaxis contracts), **audit** (gap report with evidence and fix suggestions), and **verify** (checks that documentation claims match shipped behavior). Diátaxis governs what each page does for the reader, not which directories you must create. No four-quadrant seed scaffold is installed.

## [user-guide-diataxis][0.3.0] — 2026-07-28

### Changed

- **Deprecated.** `user-guide-diataxis` now depends on `product-documentation`; installing it still works and delivers `author-product-docs` as a result. The `new-guide` skill is a thin shim that routes to `author-product-docs`. Existing installs are unaffected. New projects should install `product-documentation` directly.

## [catalogue-curation][0.1.6] — 2026-07-28

### Changed

- **`export-catalogue` strip rules extended to subdirectories.** The strip list now uses `**/AGENTS.local.md` (was root-only `AGENTS.local.md`) and adds `**/README-pypi.md`, so forks produced by `export-catalogue` correctly exclude insider AGENTS context and PyPI-specific README files anywhere in the tree.

## [agentbundle][0.21.0] — 2026-07-28

### Added

- **Catalogue pack defaults**: catalogue operators can declare per-pack config defaults in
  `catalogue.toml` under `[pack-defaults.<pack>]`; these are baked in at publish time and
  merged with user config when a pack reads its settings.
- **Custom user directory**: `[catalogue] user-dir` overrides the default `~/.agentbundle`
  install root; the override persists in `state.toml` and is honoured by all CLI commands.
- **Pack config API**: `pack_dir` and `load_pack_config` in `agentbundle.config` for resolving
  per-pack directories and reading the three-layer config cascade from pack scripts.
- **Operation log API**: `write_entry` in `agentbundle.oplog` for appending JSONL operation
  records to `<pack_dir>/ops.jsonl` with atomic append semantics.
- **`agentbundle pack-config` CLI**: `get`, `set`, `show`, and `path` subcommands.
- **`agentbundle oplog` CLI**: `append`, `show`, and `clear` subcommands.

## [release-engineering][0.1.6] — 2026-07-27

### Added

- **Ephemeral environment qualification** (`release-loop` skill): outer-loop ephemeral
  environments must meet the L5 isolation floor (dedicated cloud account/project, or an
  L4/L4+ k8s namespace/vCluster that passes a three-dimension policy audit — prod
  reachability, data isolation, inter-env isolation). An environment below the floor is
  a consent-gate crossing; L4/L4+ qualifies only after the policy audit passes.
- **Polyrepo / value-stream topology** (`release-loop` skill): fleet manifest
  (`release-fleet.yaml`) schema, canonical e2e host repo definition (Must/Must-NOT rules),
  five-term harness-neutral deploy sequencing vocabulary (Component / Stage / Gate /
  Depends-on / Release manifest), and a collect-then-validate pre-deploy phase that
  runs RFC-0072 D6 provenance verification for every component before `infra-apply`.

## [core][0.15.5] — 2026-07-27

### Added

- **`fidelity-ladder` reference module** (`operational-safety/references/`): seven-level
  EXECUTE/QUALIFY reference (L0 in-memory fake through L6 staging) with per-level
  coverage, gaps, budget heuristics, the three-dimension outer-loop qualification test,
  and an isolation provability classification (self-evident / requires-policy-audit /
  programmatically-auditable). Companion to the existing `environment-isolation` REVIEW
  module; new module is constructive (how to choose / build), existing is audit (does it
  meet the bar).
- **Fidelity-ladder section** (`work-loop` skill): inner-loop budget heuristic (sub-5-min
  rule; L0–L1 always; L2–L3 ceiling for most services), seven-level summary table,
  cross-reference to `operational-safety/references/fidelity-ladder.md`, and a build-pack
  handoff note.

## [release-engineering][0.1.5] — 2026-07-27

### Added

- **Six new RFC-0072 doctrine sections in `release-loop/SKILL.md`.** Adds the G4
  handoff package schema (`release-handoff.yaml` — all mandatory fields), a four-phase
  deploy ordering protocol (infra-apply → service-deploy → smoke → canary), canary
  analysis defaults with four-outcome protocol (PROMOTE / ROLLBACK / PAUSE / HALT) and
  traffic steps 5%→25%→50%→100%, feature flag lifecycle (six states: created →
  deployed-off → enabled-pct → full-rollout → deprecated → removed), service vs. IaC
  rollback procedures, and SLSA L2 artifact provenance verification with cosign/keyless
  signing.
- **New `define-slo` skill.** Produces an OpenSLO v1 YAML document (`slos/<service>.yaml`)
  with an `error_budget_policy` block (halt_at / warn_at / postmortem_at / trailing_window).
  The release-loop PRR gate reads this artifact to resolve the `error-budget` field to one
  of four states: `not-defined`, `within-budget`, `warning: <N>% remaining`, or
  `exhausted: halt-releases`. Includes authoring-time query validation protocol and
  toolchain translation notes (Sloth, Pyrra, Nobl9, Datadog).
- **PRR error-budget paragraph updated.** Replaces the "supplied by a follow-on
  SLO-authoring capability (home provisional)" paragraph with the four-state resolution
  protocol referencing `define-slo`.

## [frontend-engineering][0.1.2] — 2026-07-27

### Changed

- **Output rendering directives added to `css-architecture`, `responsive-layout`, `token-architecture`.** Skills now declare rendering shape for inline output. No functional change.

## [core][0.15.4] — 2026-07-27

### Changed

- **Output rendering directive added to `init-project`.** Skill now declares rendering shape for inline output. No functional change.

## [user-guide-diataxis][0.2.1] — 2026-07-27

### Changed

- **Output rendering directives added to `new-guide`.** Skills now declare rendering shape for inline output. No functional change.

## [product-strategy][0.2.2] — 2026-07-27

### Changed

- **Output rendering directives added to `write-prfaq`, `define-content-strategy`, `run-bcg-matrix`, `run-swot`, `synthesize-stakeholder-research`, `define-ux-strategy`.** Skills now declare rendering shape for inline output. No functional change.

## [product-engineering][0.13.2] — 2026-07-27

### Changed

- **Output rendering directives added to `identify-opportunities`, `frame-intent`, `decompose-intent`, `diverge-solutions`, `voice-and-microcopy`, `frame-domain`, `lean-canvas`, `align-value-stream`.** Skills now declare rendering shape for inline output. No functional change.

## [linear][0.1.4] — 2026-07-27

### Changed

- **Output rendering directive added to `linear`.** Skill now declares rendering shape for inline output. No functional change.

## [frontend-engineering][0.1.1] — 2026-07-27

### Changed

- **Output rendering directives added to `fe-performance`, `component-contract`, `a11y-engineering`, `rendering-strategy`, `fe-status`.** Skills now declare rendering shape for inline output. No functional change.

## [figma][0.2.1] — 2026-07-27

### Changed

- **Output rendering directive added to `figma`.** Skill now declares rendering shape for inline output. No functional change.

## [experience-design][1.6.2] — 2026-07-27

### Changed

- **Output rendering directives added to `design-principles`, `informational-design`, `content-design`, `tone-of-voice`, `design-system`, `creative-direction`.** Skills now declare rendering shape for inline output. No functional change.

## [desk-research][1.1.3] — 2026-07-27

### Changed

- **Output rendering directives added to `decision-archaeology`, `desk-research`, `desk-research-project-start`, `build-outline`, `source-map`, `identify-perspectives`, `desk-research-project-check`.** Skills now declare rendering shape for inline output. No functional change.

## [contracts][0.3.5] — 2026-07-27

### Changed

- **Output rendering directives added to `api-contract`, `event-contract`.** Skills now declare rendering shape for inline output. No functional change.

## [catalogue-curation][0.1.4] — 2026-07-27

### Changed

- **Output rendering directives added to `assimilate-repo`, `propose-catalogue-pack`.** Skills now declare rendering shape for inline output. No functional change.

## [atlassian][0.6.2] — 2026-07-27

### Changed

- **Output rendering directives added to `confluence-crawler`, `jira-align`, `jira`.** Skills now declare rendering shape for inline output. No functional change.

## [core][0.15.3] — 2026-07-27

### Changed

- **Output rendering directives added to `work-loop`, `receive-brief`, `contract-acquisition`, `capture-work`, `author-brief`, `adapt-to-project`, `new-spec`, `bug-fix`.** Skills now declare rendering shape for inline output. No functional change.

## [frontend-engineering][0.1.0] — 2026-07-27

### Added

- **New standalone pack: `frontend-engineering` (0.1.0).** Promotes the `frontend-engineering` skill from core to a first-class pack. Ships nine skills: `frontend-engineering` (design pre-flight, craft rules, gates), `token-architecture`, `a11y-engineering`, `fe-performance`, `rendering-strategy`, `component-contract`, `responsive-layout`, `css-architecture`, and `fe-status`. Includes a `frontend-reviewer` diff-level subagent. Co-installs with `experience-design` for full genre routing.

## [agentbundle][0.20.0] — 2026-07-27

### Added

- **`agentbundle docs <pack>`** — read pack documentation from the catalogue
  source. `--list` enumerates available files; `<file>` displays a specific file
  by stem. Works across all source types.

- **`[pack.runtime-dependencies]` in pack schema** — declare external runtime
  dependencies per pack (ecosystem, package, version, optional, skills, install,
  note).

## [agentbundle][0.13.0] — 2026-07-26

### Added

- **`agentbundle catalogue lint` now covers profiles, seeds, first-value contract, and credentialed-skill conventions.** Four checks previously in standalone `tools/` scripts are now in the CLI: profile validation, seed blocklist enforcement, first-value contract completeness, and credentialed-skill AST inspection. Requires `pip install 'agentbundle[lint]'` for the AST pass.

- **`agentbundle catalogue lint --deep` runs the agentskills.io spec compliance pass on every `SKILL.md`.** Checks frontmatter key set, description length cap, name format, layout, and eval structure. Exits 2 with a clear message when PyYAML is absent.

- **`agentbundle catalogue verify` now runs agent-artifact lint (step 11) and plugin-manifest schema validation (step 13).** Step 11 validates projected skill/agent/command frontmatter; step 13 validates `plugin.json` against the bundled schema. Both require `pip install 'agentbundle[lint]'`.

- **`agentbundle pack evals run`** — new CLI command for pack activation evals. Runs Tier-A skill-activation evals via `claude --output-format stream-json`; writes results to a gitignored eval workspace. Report-only.

- **Windows cp1252/UTF-8 guards.** All scripts and subprocess calls now include UTF-8 reconfigure guards. Lazy `import asyncio` in credentialed scripts.

- **New `[lint]` optional dependency.** `pip install 'agentbundle[lint]'` pulls `pyyaml>=6.0`.

### Removed

- **Six standalone `tools/` linter scripts deleted.** `lint-agent-artifacts.py`, `lint-catalogue-seeds.py`, `lint-profiles.py`, `lint-first-value-contract.py`, `lint_credentialed_skills.py`, and `validate-claude-plugin-manifests.py` removed. All functionality preserved in `catalogue lint` and `catalogue verify`.

---

## [Unreleased]

### Changed

- **`jira-team-status` and `jira-story-triage` reframed for safe team-backlog orientation (atlassian pack 0.7.0).** Two readiness concepts are now explicitly distinct: *team readiness* (the default — scope + eligible open-work state + no known blocker + minimum definition) and *agent-execution readiness* (the five-question bar, activated only when the user explicitly asks for "agent-ready", "one-PR", or "coding-agent candidates"). The five-question bar is labeled an agent-execution readiness standard, not a universal team story quality standard. `jira-team-status` output starts with a header block (scope, coverage, Jira-not-changed confirmation, summary counts) before grouped sections — not a trailing summary line. Backlog items with insufficient definition go to **Needs story work** (renamed from "Needs detail") rather than silently to "Not ready". Pagination is now to completeness (Cloud cursor-based, Server offset-based), with an accurate coverage disclosure (`Complete — N items`, `Cap reached — N items`, `Permission-limited — N items accessible`) rather than a silent 100-item truncation. Stand-up summaries disclose when historical comparison is unavailable. `jira-story-triage` per-item output now includes: issue ID/title, readiness result, missing information, why that gap matters, proposed rewrite, proposed ACs, **unresolved human questions** (questions that must be answered by a human before improvement can proceed), expected readiness after draft, and Jira-not-changed confirmation. Write payloads show old values, proposed values, protected fields (status, assignee, sprint, priority, labels — never changed without explicit request), and total count before writing; partial failures report per-issue success/failure with a safe recovery path. Pack first-value starter-prompt changes from a personal assignment query to a team-oriented request. Deterministic and judgment evals (`evals.json`) added for both skills covering 16 fixture scenarios. ([spec](../specs/atlassian-jira-team-backlog-reframe/spec.md))

- **`voice-and-microcopy` renamed to `ux-writing` in the `product-engineering` pack (RFC-0066 D7 / spec: `ux-writing-rename`).** All operative references across `experience-design`, `product-strategy`, guides, and web content updated in the same PR. Alias-free clean retire per ADR-0038 precedent.

- **All output-producing skills now declare an `## Output rendering` section so agents know which output shape each skill emits (15 pack patch bumps).** ~70 skills across architect (0.14.1), atlassian (0.6.1), catalogue-curation (0.1.3), converters (0.9.2), core (0.15.1), desk-research (1.1.2), experience-design (1.6.1), github (0.1.2), governance-extras (0.9.1), iac-terraform (0.1.3), linear (0.1.3), monorepo-extras (0.1.4), product-engineering (0.13.1), product-strategy (0.2.1), and release-engineering (0.1.4) gained an `## Output rendering` section with the directive lines that match what each skill actually emits — Table, Status list, Severity list, Tree / hierarchy, Diagram / flow, Key–value, Code change, or Rationale / narrative — rather than loading the full catalog into every skill. The full directive catalog ships at `guides/_shared/reference/output-rendering.md`. Skills that write files, interact conversationally, or emit raw data streams for machine consumption carry no directive.

- **`workspace-status` renders its queues in predictable status-list and table shapes (core pack 0.15.0).** The skill now carries explicit rendering directives so its output is scannable and consistent across sessions. Ready to start, Blocked, Backlog, and signals render as status lists led by a glyph — `○` ready · `●` active · `⚠` blocked · `✓` shipped, glyph first, one item per line with any runnable command left intact. Active initiatives render as a Markdown table (with a right-aligned shipped count) when more than one is active, and as the one-line form otherwise. The brief queue renders as an aligned `label: value` list, and the Step 6b dependency graph prefers a fenced `mermaid` flowchart in chat while keeping the ASCII block as the terminal-only fallback. Findings registers stay full Markdown tables.

- **`workspace.toml` entries gain a `summary` field; `capture-work` writes it (core pack 0.15.0).** Queue, shaping, and `[backlog]` entries now carry a short `summary = "…"` label that `workspace-status` renders as the item's title — so rows read as a human-legible line instead of a bare slug, and the reader no longer has to scrape the first comment line for the backlog summary (it falls back to that only for un-migrated entries). `capture-work` writes the `summary` alongside the fuller cold-start comment; the entry schema is now `slug`/`path`, `needs`, `source`, `summary`, and (shaping-only) `type`. The live `workspace.toml` was migrated: all 58 backlog and 7 shaping entries got summaries, and the two completed initiatives' fully-shipped queues (367 lines of commented-out shipped-spec bodies) were collapsed to `queue = []`.

- **Initiatives can be marked completed when their last spec ships (core pack 0.15.0).** `workspace-status` skips `paused`/`closed` initiatives from the active surface, and its closeout check now fires at two moments: when an initiative's last item has shipped (elicits setting `status = "closed"`) and when exactly one unshipped item remains (flags that shipping it completes the initiative). `work-loop`'s done step, after moving the last spec to `[work].shipped`, elicits marking the initiative completed and writes `status = "closed"` in the same PR.

- **`list-installed` gains `--format json`, `--updates-only`, and `ahead` status (agentbundle 0.13.0).** `--format json` emits a stable JSON contract (`schema_version: 1`, per RFC-0072 D5) to stdout with all diagnostics on stderr — enables CI automation of upgrade decisions. `--updates-only` hides `up-to-date` rows from output while keeping the summary counts over the full pre-filter set. The command now resolves each row's recorded source catalogue independently (multi-source grouping), so a single source failure no longer suppresses rows from other sources. Status is now four-valued: `up-to-date`, `upgrade-available`, `ahead` (installed version is newer than catalogue), `unknown`; every `unknown` row includes a machine-readable reason code (`source-unknown`, `source-unavailable`, `malformed-catalogue`, `pack-not-found`, `incompatible-contract`, `adapter-no-longer-supported`, `unparseable-catalogue-version`, `unparseable-installed-version`). A conditional SOURCE column appears in table output when 2+ distinct sources are present. Rows sort by (scope, pack, adapter). ([spec](../specs/list-installed-update-status/spec.md))

- **`information-architecture` skill gains 12 page-archetype references, product-object mapping, card-use test, and attention + permission contracts (experience-design 1.3.0).** A new `references/page-archetypes.md` covers 12 surface types — marketing landing, onboarding, product workspace, dashboard/admin, transactional flow, pack/catalogue, journey, tutorial, task how-to, reference index, explanation, and multi-surface — each with 10 required fields (primary user, job, first-screen contract, primary action, expected result, next action, proof, read/write consequence, critical states, navigation behavior). Product-object mapping guidance names the five object roles (creates / receives / inspects / changes / approves) and the visual weight rule for each. A card-use test with non-card alternatives prevents card misuse. The attention contract (no-action / optional-progress / decision-required / blocked-pending) and read/write permission contract (read-only / draft / proposed-write / confirmed-write / destructive / undo-recovery) apply to every surface. The SKILL.md procedure gains two new steps — archetype identification and product-object mapping — before hierarchy design begins. A new IA how-to guide ships with a 12-archetype quick-reference table and a decision procedure. The experience-design journey page names archetype identification and product-object mapping as explicit steps. ([spec](../specs/xd-ia-archetypes-objects/spec.md))

- **`place-bet` skill requires four new fields: `thin-slice`, `first-success-event`, `specialist-lenses`, and `learning-contract` (product-engineering pack 0.13.0).** The thin-slice field enforces the four-criterion definition — one user, one real task, one meaningful result, one material failure and recovery, plus a named instrumentation event. `first-success-event` names what "adopted" looks like for one user 30 days out. `specialist-lenses` defaults to product, experience, architecture, safety. `learning-contract` requires signals, review cadence, and a pivot trigger. Three anti-patterns added: betting without a thin slice, first-success-free briefs, and blank learning contracts. ([spec](../specs/product-engineering-shaping-doctrine/spec.md))

- **`de-risk-intent` skill gains evidence ladder (product-engineering pack 0.13.0).** Assumptions are now classified on a five-level evidence ladder: `observed | supported | inferred | assumed | unknown`. Step 2 instructs testing from the lowest rung first — `unknown` before `assumed`, `assumed` before `inferred`. The `validation_hook` output template gains an `evidence_level` field. ([spec](../specs/product-engineering-shaping-doctrine/spec.md))

- **`jira-team-status` and `jira-story-triage` reshaped to activate from natural team language (atlassian pack 0.6.0).** Both skills now trigger from the words delivery leads and POs actually use — no need to name the skill. `jira-team-status` is a read-only status view organized by the dimensions people ask about (Ready to pull · In progress · Blocked · Unassigned · Needs detail, plus recently-changed and stale markers), answering "what can the team pick up next?", "what is blocked?", "what is sitting unassigned?", "what changed in this sprint?", and "team status for stand-up". "Ready to pull" is now a documented, team-overridable rule — in the selected scope + an eligible backlog state (default `statusCategory = "To Do"`) + no known blocker + meets the five-question readiness bar — and signals it can't read are labelled "needs confirmation" rather than asserted. `jira-story-triage` now explains *why* each item is not ready (which question failed and the specific gap, not a bare tier label) and can improve weak items — draft acceptance criteria, clarify the outcome — writing back via `update-issue` only after per-item approval. The write/improvement path moved from `jira-team-status` (now read-only by default, routing "shape this" to triage) into `jira-story-triage`. The five-question bar remains the shared engine; "agent-readiness / Tier A/B/C" is retired as the headline framing. ([spec](../specs/jira-activation-reframe/spec.md))

- **`new-guide` skill broadened to create or substantially revise guides (user-guide-diataxis 0.2.0).** The skill now triggers on rewrite, audit, simplify, and modernize requests in addition to new-guide creation — covering pack pages and journey pages alongside the four Diátaxis quadrants. The audience contract is replaced by a seven-field conversation contract (reader, job, natural_start, minimum_scope, first_result, write_boundary, next_request) as the gated checkpoint before any prose is drafted. Per-page-type contracts for all six surface types now live in a dedicated `references/page-contracts.md`. Three new reference files ship with the skill: `conversation-first.md` (sequencing rules), `page-contracts.md` (six surface contracts), and `usability-review.md` (pre-publish checklist). `clear-prose.md` gains a `## Conversation-first structure` section with eight page-level structural rules. Evals updated with revise/audit trigger cases and a conversation-first output-quality rubric. Key doctrine: *Diátaxis determines where information lives. User intent determines how readers enter it.* ([spec](../specs/new-guide-conversation-first/spec.md))

### Added

- **Story quality gate on `jira: create-issue` (atlassian pack 0.5.0).** The `jira` skill now runs a pre-create quality gate before every `create-issue` call: it detects the invocation repo via `git remote -v` ("Invocation repo" label), then checks the candidate story against the five-question actionability bar (self-contained change, reachable repo scope, binary ACs, no mid-flight decision, right-sized for one PR — Q5 added because Jira stories are a legacy capacity-allocation mechanism and oversized stories cannot be handed to a single agent or engineer). Six concrete checks with story-points as the primary Q5 signal. Gate fires on `create-issue` only; `update-issue` is unaffected. ([spec](../specs/jira-story-actionability/spec.md))

- **`jira-story-triage` skill (atlassian pack 0.5.0).** Audits a Jira backlog, sprint, or JQL-scoped set of stories for agent-readiness. Scores each story against the five-question actionability bar, applies a Blocked pre-check (image-only descriptions and discovery issuetypes short-circuit before Q1–Q5), classifies into Tier A (all five pass), B (exactly one named external gate fails), or C (any content failure or Q5 fail), then groups Tier A by complexity: Quick (≤ 2pts or ≤ 100 words), Standard (3–5pts), Involved (> 5pts). Read-only; composes `jira` for all reads. ([spec](../specs/jira-story-actionability/spec.md))

- **`jira-team-status` skill (atlassian pack 0.5.0).** Session-entry-point for sprint planning and daily coordination — modelled on the `workspace-status` pattern. Shows a scored sprint snapshot in four sections (§1 Agent-ready grouped by Quick/Standard/Involved, §2 Parallel batching candidates, §3 Gated, §4 Needs shaping), then offers a pick-up hand-off: Option A routes delivery to `jira-defect-flow` (bugs) or `new-spec` (tasks/stories); Option B shapes a blocked story collaboratively and calls `update-issue` once with explicit user consent. No reference to local workspace files or workspace.toml — completely separate from local queue management. ([spec](../specs/jira-story-actionability/spec.md))

### Changed

- **`capture-work` captures machine-readable dependencies for backlog items (core pack 0.13.7).** When a `[backlog]` entry's unblock condition is the completion of another tracked item (a `[backlog]` slug or a `[work]` spec) as a hard prerequisite, `capture-work` now adds the matching `needs` edge instead of recording the dependency in prose only — so `workspace-status` can resolve it. Disjunctive ("A or B"), untracked-target, and external ("credentials provisioned", "someone takes the PR") unblocks deliberately stay prose. The `workspace.toml` seed and `[backlog]` schema header now state the same rule.

### Added

- **First-value handoff block in `agentbundle install` (agentbundle 0.12.0).** A successful `agentbundle install` now prints a guidance block after the `installed:` line. Level B packs (non-technical audience, `level-b = true`) show four labelled lines — `Verify:`, `Try:`, `Expected:`, and optionally `Next:` — drawn from the pack's `[pack.first-value]` schema. Level A packs show `Verify:` only. Packs without `[pack.first-value]` are unchanged. Dry-run, upgrade, and profile-install paths are not affected. ([RFC-0064 Amendment #4](../rfc/0064-ini-001-ai-native-ecosystem.md) · [spec](../specs/agentbundle-first-value-handoff/spec.md))

- **`workspace.toml` seed (core pack 0.13.6).** `agentbundle install core` now
  delivers a minimal `workspace.toml` — schema comments and a `[backlog]` section
  — so the file exists from day one. Closes the gap where the installed
  CONVENTIONS.md references `workspace.toml [backlog].open` but install never
  created the file. The workspace-status "offer to initialise" path remains the
  upgrade tool for adding the full initiative schema. ([RFC-0069](../rfc/0069-workspace-toml-adopter-seeding.md))

- **Tracker intake guides — decision tree + vocabulary mapping table.** Adds two
  cross-cutting guides in `guides/_shared/`: `choose-a-tracker-integration.md`
  (decision table and per-tracker sections covering GitHub `github-brief-intake`,
  Linear `linear-brief-intake`, Jira `jira-brief-intake`, Jira Align
  `jira-align-brief-intake`, and the no-tracker `author-brief` path) and
  `tracker-vocabulary.md` (cross-tracker object-level mapping table + brief-intake
  skill routing table). P4 guide slice for the RFC-0064 tracker intake phase.
  ([spec](../specs/m5-tracker-guides/spec.md))

- **governance-extras 0.8.2 — first-session tutorial (preview-confirm write pilot).** Adds `guides/governance-extras/tutorials/governance-extras-first-session.md`: a step-by-step walkthrough of the `new-adr` preview-confirm write gate — decision framing, ADR content preview, target path preview, confirm/stop/revise, recovery, and next actions. Adds `tutorial` field to `[pack.first-value]` in `pack.toml`. Completes the `portfolio-first-run-pilot-governance-extras` pilot (RFC-0064 Amendment #4 preview-confirm write archetype).
- **`architect-first-session.md` first-session tutorial (architect pack 0.13.3).** First-value guided tutorial for the no-terminal architecture path; wires the `tutorial` pointer in the pack's first-value contract. Covers install verification, verbatim starter-prompt, expected-result (`docs/architecture/reference.md`), recovery, and next action. Pilot transcript confirms the path works via direct model reasoning (no skill required for the starter-prompt).

- **`jira-align-brief-intake` skill (atlassian pack 0.4.0).** Turns a Jira Align Feature into a product brief and shippable specs: fetches the Feature and its child stories, tasks, and defects via the `jira-align` skill, maps them onto a Shape B product brief using a configuration-guided field mapping reference (customised for org-specific workflow state names and Program Increment cadences), and hands off to `receive-brief` to elicit gaps, decompose, and build. 1-way intake only — never writes to Jira Align. Mirrors the `jira-brief-intake` choreography pattern for Jira Align's program-level delivery unit. ([RFC-0064 M5](../rfc/0064-ini-001-ai-native-ecosystem.md))
- **New `github` pack (v0.1.0) with `github-brief-intake` skill.** Pull a GitHub Milestone and its issues via the `gh` CLI, map them to a Shape B product brief (milestone title → Outcome draft; open and closed issues → `US-n (#NNN)` stories, closed issues annotated `[closed]`; milestone URL → `Epic:` provenance pointer), write the brief to `docs/product/briefs/<slug>.md`, and hand off to `receive-brief`. Three-way auth model: authenticated → proceed; unauthenticated + public repo → note posture and continue; unauthenticated + 404 → ambiguous message (private and nonexistent repos are indistinguishable). Graceful degradation when `receive-brief` is absent. Optional post-intake write-back (comment / label / close — never body edits). Ships with a Diátaxis how-to guide. ([spec](../specs/m5-github-brief-intake/spec.md))

- **`figma` pack (0.1.6) — first-run tutorial for the credentialed read-only archetype.** Adds `guides/figma/tutorials/figma-first-session.md`: a step-by-step tutorial for non-technical designers to reach their first visible result (page and frame structure from a Figma file they own). The tutorial covers `credential-brokers` prerequisite install, user-initiated credential setup via the `credential-setup` skill (token entered at the terminal `getpass` prompt, never in chat), connection verification via `figma check` + `figma whoami`, and the starter task. Corrects a factual error in the pack's `[pack.first-value]` `verification` field (workspace-listing was not a real capability; corrected to `check`/`whoami` path). Adds the `tutorial` field to `[pack.first-value]`, making the contract independently verifiable. ([spec](../specs/portfolio-first-run-pilot-figma/spec.md))

- **architect 0.14.0 — Stage-0 concept stop point + adopter front-door fixes.** `architect-design` now treats the Stage-0 concept as a valid stopping point: you can save the concept on its own (or stop at chat) without proceeding to the full design doc, and the skill ends with a Stage-0 completion receipt — either `Result: chat only; no file was created.` or the exact saved path and what it contains. The README leads with plain outcomes (shape a concept / draw a system / review an architecture) before internal vocabulary, adds a surface-aware route cue, corrects the install example to `agentbundle install --pack architect <catalogue>` (the bare `install architect` form the current parser rejects), and lists the correct adapter names. Adds a regression test locking the README's documented install commands to the live CLI parser. (RFC-0064 Amendment #4 adopter-persona mechanical fixes.)

- **figma 0.2.0 — render completion receipt + credential source-of-truth fix + front-door prerequisites.** Every `export-images` render now ends with a mandatory receipt: source frame, exact local output path, format, skipped/lower-fidelity warnings, and `No Figma changes made`. The SKILL's credential-resolver reference is corrected from the stale `credentials_shim` to the standalone `credbroker` library (matching the live client), and the shared pack-catalogue guide's stale `from agentbundle.credentials import …` line is corrected to `credbroker` for both `figma` and `atlassian`. The README leads with plain outcomes, states the precise remote consequence (no REST node edits; collaborator-visible comments that require confirmation), front-loads the Figma account / plan / token-scope / 403 conditions, and gives one authoritative setup sequence with `<catalogue>` explained. (RFC-0064 Amendment #4.)

- **governance-extras 0.9.0 — preview-confirm write gate + completion receipt for `new-adr` / `new-rfc`.** Both skills now resolve and display the repository root, detect a non-default ADR/RFC location, draft the content, and show a preview (identifier, status, target path, index path, content) that waits for explicit confirmation — no file is created and no index updated before you confirm. After writing, each returns a completion receipt (identifier, file path, index path, status, files changed, owner, next step). Identity fields no longer assume GitHub handles. The README leads with outcomes (record a decision / propose a change / change the rules) before the ADR/RFC acronyms, corrects the skill count (four skills, including `rfc-status`), states the repo-scope consequence (adds capabilities and files to the current project), and shows a `--dry-run` preview route. (RFC-0064 Amendment #4.)

### Fixed

- **Shared install/upgrade guides — removed the stale `--to <version>` flag.** The `agentbundle upgrade` verb no longer accepts `--to`; version selection is by pointing `<catalogue>` at a git ref. Corrected the flag out of `preview-install-or-upgrade`, `install-user-scope-pack-into-kiro`, `install-user-scope-pack-into-codex`, and the `file-safety-contract` explanation.

- **Invalid bare `agentbundle install <name>` forms corrected across the remaining packs.** The install verb requires `--pack`; the bare-positional form the current parser rejects was still documented in `linear` (0.1.2), `iac-terraform` (0.1.2), `product-strategy` (0.1.2), `product-engineering` (0.12.2 — including a two-pack-in-one-command line split into two invocations), and `release-engineering` (0.1.3) READMEs, plus the `catalogue-curation`, `desk-research`, `figma`, and `governance-extras` first-session tutorials. All now use `agentbundle install --pack <name> …`; the `desk-research` tutorial also drops the pre-rename `research` pack name. Follow-up to the RFC-0064 Amendment #4 adopter front-door fixes.

- **Claude plugin marketplace manifest now passes `claude plugin validate` (Claude Code 2.1.209).** Three generator defects caused 35 errors: (1) marketplace missing top-level `name` field, (2) plugin `author` emitted as a plain string instead of a `{name, email}` object, (3) plugin `source` field absent entirely. All three are fixed in the build pipeline (`derive_projectable_subset`, `_run_aggregate`, `_aggregate_marketplace`). The `.claude-plugin/marketplace.json` in the working tree now validates with 0 errors.

### Changed

- **RFC-0064 Amendment #4 — cross-pack first-value adoption overlay.** Records Level A/B pack obligations, a pilot-first rollout contract, and eight decisions governing non-technical pack onboarding. Adds five work queue entries (`spec/portfolio-pack-first-value-contract`, three pilot specs, `spec/agentbundle-first-value-handoff`) and two shaping entries to `workspace.toml`. Reconciles `spec/m2-frame-intent-jtbd` from queue to shipped. ([RFC-0064 Amendment #4](../rfc/0064-ini-001-ai-native-ecosystem.md))

- **`frame-intent` skill (product-engineering pack 0.12.0) — three-tier JTBD elicitation in step 5.** The Opportunity framing step now explicitly elicits a functional job, emotional job, social job, and struggling moment. The intent template's Opportunity section carries four corresponding optional sub-fields. Existing intents with free-form Opportunity prose remain valid without migration.

- **`workspace-status` skill (core pack 0.13.3) — Findings step shows inline tables.** When either `docs/product/findings/rfc-candidates.md` or `docs/product/findings/roadmap-intents.md` has data rows, `workspace-status` now prints both tables inline rather than a bare count. When both registers are empty, a single summary line is shown (`0 rfc candidates · 0 roadmap intents — both registers empty`) instead of silently omitting the section.

- **`work-loop` skill (core pack 0.13.5) — pre-existing failure capture + progressive disclosure.** Adds a "Pre-existing failure triage" step to GATES: when a gate fails on a file not in the diff, the loop captures it to `workspace.toml [backlog].open` as a `pre-existing-*` slug and treats it as a known-skip rather than going to FIX. Full schema in new `references/pre-flight-failures.md`. Also collapses the self-coverage gate section (~30 inline lines → 4-line summary + `references/self-coverage/protocol.md`) and removes the infra/deploy multi-artifact preflight paragraph (already covered by `references/infra-verification.md`).
- **`work-loop` skill (core pack 0.13.2) — experience-reviewer rendered-output clarification for web surfaces.** The `experience-reviewer` bullet in the REVIEW section now explicitly states that for web surfaces (HTML/CSS/JS), "rendered output" means the built site — run the build and describe key pages from the output; the code diff alone cannot serve as the rendered artifact for genre-rubric or cross-page consistency checks. Backlog item `work-loop-xd-rendered-output`.
- **Claude plugin install command updated to use marketplace format.** The documented install flow in `README.md` and the web catalogue now uses `claude plugin marketplace add eugenelim/agent-ready-repo` followed by `claude plugin install <pack>@agent-ready-repo`, replacing the deprecated repository-tree-URL form (`claude plugin install https://github.com/…/tree/claude-plugins-dist/<pack>`).

- **`check-workspace` renamed to `workspace-status` (core pack — clean retire, no alias).** The workspace-level cold-start orient skill is now invoked as `workspace-status`. All operative references swept in one PR. Adopters invoking `check-workspace` by name will receive a "skill not found" signal; update to `workspace-status`. The new description triggers cover all phrasing the old skill responded to, plus "workspace status", "where am I", "orient me", "session start". ([RFC-0067](../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md), [ADR-0054](../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md))

### Added

- **`linear` pack (0.1.0) — Linear integration: credentialed CLI + brief intake/sync.** New opt-in user-scope pack. Adds three skills: (1) `linear` — a credentialed GraphQL CLI for read-only access to Linear Issues and Projects (check, get-issue, get-project; Personal API Key via `credbroker`; paginated up to 250 issues; 429 Retry-After); (2) `linear-brief-intake` — maps a Linear Issue (with sub-issues) or Project onto a Shape B product brief, caps at 10 stories, hands off to `receive-brief`; (3) `linear-brief-sync` — delta catch-up for existing briefs: diffs Linear-sourced fields, presents section-level before/after for PE approval, refuses when Status is Executing. ([RFC-0068](../rfc/0068-linear-brief-intake-and-sync.md))
- **Pack first-value contract — all 17 packs (RFC-0064 Amendment #4).** Every pack now carries a `[pack.first-value]` section in `pack.toml` recording audience posture, verified surfaces, prerequisites, verification steps, and recovery steps. Level B packs (10 of 17) additionally carry a starter task, starter prompt, expected result, and next action for non-technical or mixed audiences. Two packs (`governance-extras`, `user-guide-diataxis`) include a `safety-gate` because their starter task writes a shared governance or structural record. `tools/lint-first-value-contract.py` enforces the contract at build time; `tools/build_gate_chain.py build-check` now includes the new gate.

- **`frontend-engineering` skill (core pack 0.13.1) — XD genre routing step (step 1b).** After naming the aesthetic reference (step 1), the `frontend-engineering` PLAN phase now routes to the matching XD discipline skill by surface type: `conversion-design` for marketing pages, `documentation-design` for docs/help, `analytical-design` for dashboards, `informational-design` for editorial pages, `interaction-design` for form flows and component state machines, `content-design` for content strategy. T2 conditional — experience-design pack detected by checking for `conversion-design` in available skills; absent pack records a named skip and proceeds to step 2. Backlog item `xd-genre-routing-frontend-engineering`.

- **`capture-work` skill (core) — classify-then-triage front-door for `workspace.toml`.** Replaces `queue-add`. Before writing, `capture-work` classifies each item as `[build]` (implement, fix, spec, refactor) or `[shape]` (research, strategy, design, signal) and surfaces that classification for confirmation. Build items route to the same destinations as `queue-add` (active initiative's `[work].queue` or `[backlog].open`), with all prior behaviors preserved: slug derivation + collision check, dependency inference from explicit language only, grouping (independent batch / atomic bundle), prioritization elicitation, escalation rubric, cold-start-sufficient comments, comment-preserving write, graceful degradation. Shaping items route to `[shaping_queue].backlog` (initiative-scoped) or `[backlog].open` with a `type` field (repo-level); `signal` items route to `[shaping_queue].active`. After writing, the skill offers a progressive capability-detected hand-off to the matching shaping skill if its pack is installed, or emits a named install hint if not. Triggers on "capture this", "add these to the queue", "capture these as queue items", "queue this up", "add this to the backlog". ([RFC-0064 Amendment #3](../rfc/0064-ini-001-ai-native-ecosystem.md))
- **`workspace-status` mode tags** — every item in the Ready-to-start and Backlog sections is now prefixed with its room: `[build]` (work queue items and untyped backlog entries), `[shape]` (shaping queue items and typed backlog entries), `[brief]` (brief queue items). The two-room model is immediately visible at session start.
- **`work-loop` orient-step guard** — step 0 now checks whether the argument slug matches a shaping entry in `[shaping_queue]` (active or backlog) or a typed `[backlog].open` entry. If matched, the skill emits a redirect naming the appropriate shaping skill and stops before PLAN. Prevents accidentally running `work-loop` on items that belong in the shaping room.

- **Verb taxonomy section in `guides/_shared/how-to/author-a-skill.md`.** A new `## Naming your skill` section (after `## Body structure`) documents the canonical five-verb taxonomy (`status`, `start`, `check`, `init`, `resume`) and the banned-label list (`arrive`, `orient`, `onboard`, `return`, `onboarding`) from ADR-0054. Pack authors now have a lookup table before naming a new skill.

- **`product-strategy` pack 0.1.0 — the strategy seat upstream of product engineering and experience design (RFC-0063, ADR-0053).** A new user-scope, pure-markdown pack with 9 skills across 3 pillars. **Pillar 1 — Market and competitive strategy:** `run-swot` (SWOT analysis → `swot-analysis.md`); `run-porters-five-forces` (industry structure analysis → `competitive-landscape.md`); `run-pestle-analysis` (macro-environment scan → `macro-environment.md`); `run-bcg-matrix` (portfolio position by quadrant → `portfolio-position.md`); `run-okr-cascade` (company → team OKR derivation + gap identification → `okr-cascade.md`; gaps routed as `{type = "strategy"}` entries to the active initiative's `["ini-NNN".shaping_queue].backlog` in `workspace.toml` for `frame-situation` (PE pack) to pick up); `write-prfaq` (altitude-0 press release + FAQ forcing function → `prfaq.md`); `synthesize-stakeholder-research` (consumes desk-research pack outputs → `stakeholder-synthesis.md`). **Pillar 2 — UX strategy:** `define-ux-strategy` (NN/g three-layer model + Jaime Levy four tenets + Gothelf/Seiden OKR-linked framing → `ux-strategy.md`). **Pillar 3 — Content strategy:** `define-content-strategy` (Halvorson quad: Purpose + Process + Structure + Governance → `content-strategy.md`). All artifacts resolve their write path through the `[product-strategy]` table of `agentbundle-layout.toml` (config → default `docs/product/shaping/` → discover-by-marker). Each skill ships trigger evals (`eval_queries.json`) and a Tier-4 LLM-judge eval (`evals.json`). The OKR-cascade → PE-pack cross-pack routing contract is documented in `packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md`; `workspace-status` routes `{type = "strategy"}` items to `frame-situation` (M2) or `frame-intent` as interim. Journey: `docs/product/journeys/product-strategist-sets-direction.md`.

- **`experience` pack 0.6.0 — surface-genre uplift: 9 canonical renames, 7 new skills.** The experience pack moves from 11 skills at 0.5.x to 18 skills at 0.6.0. **Nine skill renames** to canonical industry vocabulary (ADR-0052): `map-customer-journey` → `journey-mapping`, `blueprint-service` → `service-blueprint`, `map-screen-flow` → `user-flow`, `map-internal-process` → `process-mapping`, `aesthetic-direction` → `creative-direction`, `layout-and-information-architecture` → `information-architecture`, `design-critique` → `design-review`, `design-system-foundations` → `design-system`, `copy-direction` → `tone-of-voice`. **Seven new skills**: `design-principles` (Define-phase: NNGroup 4-step model, arbitration test, evidence-level carry-through); `conversion-design` (marketing surfaces: hero approach, above-fold spec, scroll story, social proof tier); `documentation-design` (docs surfaces: Diátaxis type map, navigation-at-scale strategies, TTFV target, machine-readability as design-phase decision); `analytical-design` (dashboard surfaces: domain-model-first, business-question anchoring, 3-tier widget hierarchy, Shneiderman's mantra, spatial layout grammar); `marketplace-design` (catalogue surfaces: card IA hierarchy, filter/facet architecture, comparison affordances, browse-first vs. search-first); `informational-design` (editorial surfaces: typography as primary design tool, F/Z-pattern calibration, editorial grid, "what's next" chain); `workspace-design` (productivity and agentic surfaces: context-persistence, session arc, collaboration state IA, agentic UI patterns). **Surface-genre contract**: `user-flow/assets/screen-brief-template.md` gains a `surface-genre:` frontmatter field; genre declared once in the brief propagates to all downstream skills. **Seven D5 extensions** across six existing skills: `journey-mapping` gains peak-moment identification and evidence-level elicitation; `interaction-design/references/pattern-families.md` adds 5 pattern families (wizard-and-stepper, data-table, destructive-action escalation, save-state, analytical-dashboard-widgets); `service-blueprint` gains evidence-of-service row and fail-point marking; `information-architecture` gains success-metric binding and genre routing; `design-review` gains design-principles integration chain and 6 genre-specific rubrics; `creative-direction` gains genre canonical reference tier for all 7 genres.

- **`rfc-status` skill added to governance-extras (0.7.0) — RFC landscape dashboard.** A new read-only skill scans `docs/rfc/*.md` and groups RFCs by lifecycle state (`Draft`, `Open`, `Final Comment Period`, `Accepted`, `Rejected`, `Withdrawn`, `Experimental`, `Superseded`); surfaces active RFCs by name and resolved RFCs by count. Also counts non-header rows in `docs/product/findings/rfc-candidates.md` and `docs/product/findings/roadmap-intents.md` and surfaces them as a findings summary. Useful at session start alongside `workspace-status`. Read-only — never creates or modifies RFC files.
- **`docs/product/findings/` registers seeded (RFC-0064 M3).** Two new governance registers: `rfc-candidates.md` (candidate RFCs surfaced by work-loop scope-deferrals or `frame-situation` escalations) and `roadmap-intents.md` (deferred roadmap items not yet shaped into specs). Both use the same five-column schema: `Problem | Source | Surfaced by | Date | Priority | Disposition`.
- **`workspace-status` surfaces findings count (core 0.13.0).** After resolving the queue DAG, `workspace-status` now surfaces a count line — "N rfc candidates · M roadmap intents" — from the findings registers when either count is non-zero. Omitted when both are zero or the files are absent.

### Changed

- **`experience-design` pack 1.1.0 — multi-surface audit protocol, 6-element above-fold spec, and surface-specific mobile paths.** Seven gaps identified by a UX audit benchmarked against Linear and Stardog (the skills got within-surface findings right but missed every cross-surface and surface-specific mobile finding — root cause: no multi-surface protocol and no surface-specific mobile path in the quality floor pass). **Multi-surface protocol (Gaps 1, 3):** `design-review` and `information-architecture` each gain a Step 0 surface inventory for multi-surface platforms; `design-review` genre routing and `experience-reviewer` both state that a marketing surface and a documentation surface require separate passes with a third cross-surface integration pass after. **Above-fold spec (Gap 2):** the marketing genre rubric item 2 now enumerates all six required above-fold elements (IC-first headline ≤10 words, conviction-building subheadline, outcome-language primary CTA, optional secondary CTA, adjacently-positioned proof signal, friction microcopy — absence of friction microcopy is a blocker when the primary CTA implies commitment) and adds a tone collision check between headline approach and subheadline register. **Cross-surface wayfinding (Gap 4):** `information-architecture` step 6 gains a cross-surface wayfinding check — the docs→marketing bridge must be present on every page (not just the footer or landing page) and its absence is a blocker finding. **Docs landing page hub structure (Gap 5):** documentation genre rubric item 3 now verifies the three hub jobs (Start Here entry point, four Diátaxis-typed entry points named by reader outcome, above-fold search) and flags the search-first requirement for >200-page sites. **Surface-specific mobile checklists (Gap 6):** `design-review` step 2 and `interaction-design` step 6 each gain surface-specific mobile priorities for marketing surfaces (above-fold CTA visibility on small-phone viewports, full-width drawer targets, grid overflow) and documentation surfaces (code block horizontal scroll, sidebar collapse, comfortable reading width). **Cross-surface copy voice continuity (Gap 7):** marketing genre rubric gains item 4 — register mismatch flags as minor; contradicted product claims flag as major; requires reading the docs landing page and one how-to page alongside the marketing surface.

- **`work-loop` deferred-items step prompts for findings registers (core 0.13.0).** After recording a deferred item in `docs/backlog.md`, the loop now prompts: "Does this look like an RFC candidate or a roadmap intent? If so, also add a row to `docs/product/findings/rfc-candidates.md` or `docs/product/findings/roadmap-intents.md`." The backlog anchor remains the primary durable record; the findings registers add governance visibility. Prompt skipped when neither file exists.

### Fixed

- **`new-rfc` session-fragmentation guard (governance-extras 0.8.0).** Generating specs or ADRs for an already-Accepted RFC in a follow-on session now re-surfaces the `workspace.toml` queue-write prompt for any `spec/<path>` entries absent from the active initiative's queue. Previously the prompt fired only when an RFC transitioned to Accepted within the current session; a follow-on session silently skipped it. The `new-rfc` trigger description is also extended to activate on "generate follow-on specs for RFC-NNNN" and similar phrasing, routing those sessions through the queue-write guard.

- **`desk-research-project-start` no longer silently falls back to `.context/research` (desk-research 1.1.0).** The pre-fix skill defaulted to `.context/research/` when no `agentbundle-layout.toml [research]` config was found — a gitignored scratch path that does not survive workspace resets or session boundaries. The fix removes this silent fallback and replaces it with two-branch elicitation: the agent asks whether to commit output to the repo (`docs/product/research/`) or to a personal workspace (user-supplied absolute path, e.g. an Obsidian vault). Elicitation writes the chosen path to the appropriate `agentbundle-layout.toml` so subsequent projects skip the prompt. The config key is renamed from `parent` to `output_dir`; resolution order is now user-scope first (personal vault wins across repos), then repo-scope, then elicitation.

- **`iac-terraform` pack (v0.1.0) — Terraform and OpenTofu IaC accelerator.** A new opt-in accelerator pack for generating and maintaining Terraform/OpenTofu infrastructure code. Two skills: `generate-iac` (8-stage generation loop from ADR gate through G4 handoff) and `reconcile-iac` (drift audit required before every follow-on change). Dual-engine — the engine-neutral HCL baseline runs unchanged on both Terraform ≥ 1.6 and OpenTofu ≥ 1.6 (the validation floor); the native S3 lockfile feature (`use_lockfile = true`) requires Terraform ≥ 1.11 or OpenTofu ≥ 1.7 and is configured separately in `backend.hcl`; OpenTofu-only features (state encryption, early variable eval) are opt-in via the `.tofu` override mechanism. Zero seeds, zero agents — the pack emits provider files and pipeline config into the adopter's repo via `generate-iac`, not via scaffold seeds. Validated providers in v1: AWS (both engines), GCP, and Databricks; Azure, Kubernetes workloads, edge/CDN/DNS, HashiCorp platform (Vault, HCP), data platforms, and observability vendors are experimental. Standards: terraform layout, networking, security/IAM, tagging, observability, OPA/Conftest policy-on-plan (Sentinel incompatible with OpenTofu — not supported). CI templates for GitHub Actions (reference), Azure DevOps and GitLab (experimental). G4 handoff artifact set: deploy-ready TF directory, pinned plan + digest, OPA/Conftest exit-0 evidence, Trivy/Checkov exit-0 evidence, reversibility classification per resource, and optional Infracost delta. Depends on `core >= 0.1` and `governance-extras >= 0.6`.
- **`governance-extras` 0.6.0 — governance-index template, extension-contract how-to, `new-adr` infra mode.** Three companion additions from RFC-0065 D16: (1) `seeds/governance/manifest.example.yaml` — the governance-index template (a domain → ADR/standard manifest loaded first by `generate-iac` Stage 0; tool-neutral, used by any governed repo); (2) `new-adr` skill gains infra mode (`mode: infra`), which loads a new reference (`references/infra-decisions.md`) with the seven IaC ADR topics and their framing questions — `state`, `layout`, `iam`, `tagging`, `networking`, `pipeline_auth`, `remediation`; (3) new how-to guides for the governance index and extension-contract conventions.
- **`architect-review` Proposal rubric gains an extension-contract check.** When a design doc introduces a plugin, hook, or customisation point, the Proposal rubric now checks that the extension contract is named, its shape is described, and what is stable vs unstable is stated.

- **`workspace-status` skill added to core pack (core 0.12.0, originally `check-workspace` — renamed in this release).** A new session-start skill reads the repo-level `workspace.toml` and surfaces ready-to-start items, blocked items with reason, parallel candidates, and active signals — all in one command. Resolves the dependency DAG across all queues and initiatives using `needs` prefix notation (`work:`, `shape:`, `research:`, `brief:`, and cross-initiative `ini-xxx:work:` prefixes). Surfaces `type = "signal"` entries as "active context" separately from actionable "ready to start" items; surfaces each shaping entry with the matching skill invocation for the installed packs. Offers to initialise `workspace.toml` when absent. Run `workspace-status` at every session start from Batch 2 onward.
- **`workspace.toml` committed to `main` as the repo-level declared-intent coordination artifact.** Pre-populated with the INI-002 (Platform Core) M1 bootstrap queue: three queues (`shaping_queue`, `brief_queue`, `work`) with all Batch 3–5 specs pre-seeded and their `needs` wiring in place. `spec/m1-workspace-core` is marked shipped (this PR). The `agentbundle-layout.toml [product]` table is documented in `workspace-status`'s reference file: `projects` and `shaping` paths are configurable; `briefs` stays pinned.

### Changed

- **`voice-and-microcopy` human-craft check gains vocabulary tells, an editorial methodology, and voice authenticity tests (product-engineering 0.11.0).** `human-craft-check.md` now covers three additional layers beyond its existing structural tells: a vocabulary-tell section (hollow verbs, inflated adjectives, abstract container nouns, hedging openers — each with a concrete replacement rule); a three-pass editorial methodology (vocabulary scan → delete the opening → specificity audit); and three voice authenticity tests (pub test, founder test, one-person test). Scoped to the same context as before — longer copy: onboarding text, feature descriptions, help text — not short UI strings.

### Added

- **`voice-and-microcopy` gains a human-craft structural-tell check (product-engineering 0.10.1).** A new reference file, `human-craft-check.md`, inlines six structural AI tells — treadmill effect, symmetrical lists, false precision, performative thoroughness, nice-nice wrap, subtext vacuum — and a four-question self-check for longer copy (onboarding text, feature descriptions, help text). The content checklist gains an eighth item, Human-crafted, that routes longer copy through this check. Self-contained within the pack; no cross-pack references.

### Changed

- **`architect-diagram` gains Mermaid layout guidance, ELK renderer docs, and an explanation guide (architect 0.12.0).** `mermaid-flowchart.md` gains three new sections: `## Edge routing — curve style` (the `curve: step` orthogonal-routing recommendation for architecture diagrams, with a full routing-value table), `## Layout control` (subgraph direction override, `inheritDir`, diagram-global spacing keys, the `subGraphTitleMargin` workaround, and label wrapping), and `## ELK renderer — for complex graphs` (Brandes-Köpf node-placement strategy, `mergeEdges`, `LINEAR_SEGMENTS` option, and a venue-caveat matrix). `mermaid-c4.md` gains `## Layout config` (`c4ShapeInRow`, `c4BoundaryInRow`, `UpdateLayoutConfig()` syntax, and a note that `Lay_*` direction directives are silently ignored). `mermaid-mindmap.md` gains `## Layout algorithms` (`cose-bilkent` vs `tidy-tree`, determinism trade-off, `maxNodeWidth`, `padding`). `## Common architecture pitfalls` in the flowchart reference adds three new entries: invisible links as a layout crutch, non-grammatical edge labels, and edge-label overlap. A new Diátaxis explanation guide (`guides/architect/explanation/architect-diagram-skill-design.md`) documents the design principles behind the skill — Sugiyama / dagre / ELK algorithm choices, direction defaults, Gestalt visual-encoding rationale, notation-routing logic, portability constraints, and the anti-pattern register. 16 `.mmd` fixture files covering all supported diagram types and a `pytest`-based validation harness (`scripts/test_fixtures.py` + `scripts/testdata/`) are added to the skill source.
- **`architect-diagram` gains portable Mermaid title, accessibility, and pipeline-orientation guidance (architect 0.11.0).** Three Mermaid-native additions to the skill's references: (1) `flowchart LR` is now explicitly the orientation for pipeline / ETL / CI-CD / data-flow diagrams (a decision-table row plus strengthened flowchart guidance); (2) the config-frontmatter `title:` is documented as the in-source diagram title (Mermaid ≥ 10.5), with the prose scope sentence kept as the always-portable baseline; (3) `accTitle` / `accDescr` are documented as the diagram's screen-reader alt text. The change also explicitly rejects three renderer-proprietary conventions (`:::external`, `label\|tech`, `%% title:`) that no-op or break in stock Mermaid (GitHub, Confluence, `mmdc`, and the repo's own renderers) — they contradict the skill's "survive enterprise wiki rendering" north star. Guidance only; no renderer or skill-contract change.

### Fixed

- **`aesthetic-direction` grounding reference now cites WCAG thresholds by name, not literal values (experience 0.4.1).** The Standards section of the grounding reference described contrast thresholds using specific ratio and point-size literals, which violated RFC-0033's portable-method rule. The section now refers to the named WCAG SC thresholds and the OS-level reduced-motion preference concept rather than reprinting the values table. No change to skill behavior — only the reference prose that informs the aesthetic-direction pass.

### Added

- **Platform marketing site — Phase 1 (Astro homepage).** A new Astro marketing
  site in `web/` (approved as a top-level directory by [RFC-0061](../rfc/0061-web-top-level-directory.md),
  toolchain recorded in [ADR-0050](../adr/0050-astro-marketing-site-toolchain-and-deploy.md))
  becomes the platform anchor at `/`, with the existing MkDocs reference docs
  co-deployed at `/docs/` from one GitHub Pages origin. The homepage ships all
  nine sections from the platform-site spec in the amber-gold Option B aesthetic
  (dark hero + stat strip, light content bands, dark closer); all interactions —
  install tabs, catalogue expand, mobile nav — are CSS-only (zero JavaScript) and
  the page passes `pa11y` WCAG 2.2 AA. The CI pipeline now builds Astro first,
  then MkDocs, into a single `build/` artifact.

- **`frontend-engineering` skill added to core pack (core 0.11.0).** The work-loop now loads
  inline craft rules — design pre-flight, HTML semantics, CSS token discipline,
  accessibility, state completeness, and verification commands — whenever a
  task's primary output is HTML, CSS, or JS. The design-intent pass is mandatory
  (not a recommendation) for that surface.

- **OWASP Agentic Skills Top 10 v1.0 compliance pass — all non-core packs.**
  All non-core packs audited and hardened against AST01–AST10. Three classes of changes:
  (1) AST05 — `research` skill now explicitly declares that fetched web content is untrusted
  data, never instructions;
  (2) AST06 — `confluence-crawler` and `jira` skills now declare the SSRF pre-flight host
  check the agent must run before invoking a user-supplied base URL (scripts validate scheme
  only; the agent verifies the host and rejects private-IP ranges and cloud-metadata endpoints);
  (3) AST10 — all non-credentialed skills that cross a security boundary now carry
  `metadata.boundaries` in their SKILL.md frontmatter (`network_fetch`, `filesystem_write`,
  `filesystem_read_untrusted`, `network_egress`, or `deploy_action`). The `assimilate-primitive`
  skill also gains an explicit AST01–AST10 security review step so any ingested primitive is
  checked before landing. Compliance record in `docs/architecture/security.md`.

- **New `agentic-skills` module in `security-checklists` — OWASP Agentic Skills Top 10 v1.0 coverage (core 0.10.0).**
  The `security-reviewer` now has control-altitude depth for the OWASP Agentic Skills Top 10
  v1.0 (AST01–AST10): malicious skill content (AST01), permission over-declaration (AST03),
  insecure metadata parsing (AST04), external reference pinning (AST05), isolation declaration
  (AST06), version drift (AST07), governance gaps (AST09), and cross-platform security metadata
  (AST10). AST02 (Supply Chain) defers to the existing `supply-chain` module; AST08 (Poor
  Scanning) is addressed by the three-bucket delegation legend. The module fires when a diff
  authors or modifies a skill file, parses skill metadata, builds a distribution package, or
  adds skill execution sandbox config. Accompanied by a new `docs/architecture/security.md`
  reference documenting all enforced security frameworks.

- **New `agentbundle show <pack>` command — a pack's skills and agents, derived live (agentbundle).**
  Answers "what does this pack contain?" by walking the pack's `.apm/` source tree on
  each call, printing its `pack.toml` metadata alongside the full, sorted skill and agent
  inventory. `--format json` emits a stable object (`name`, `version`, `description`,
  `skills`, `agents`, `source`) for scripts and agents. Nothing is persisted and no
  manifest is touched, so the answer can't drift from what the pack ships. When the
  catalogue can't be resolved, an *installed* pack still reports its inventory from the
  install-state files (`source: installed-state`); a not-installed pack errors and exits
  non-zero. Implements RFC-0060 / ADR-0049.

- **`design-critique` now includes a marketing clarity pass (experience 0.4.0).** A new
  fourth mode runs when the artifact has above-fold copy with a persuasion/conversion
  goal (landing pages, pack cards, product announcements — not settings screens or forms).
  It checks the tweet test (headline stands alone as a conviction statement), the
  five-second scan (above-fold answers what / who / should I care), and painkiller-first
  structure (copy leads with the reader's problem, not the author's feature list). Each
  finding maps to the violated criterion with a `marketing` source label and a 0–4
  severity using the existing frequency × impact × persistence rubric, where impact means
  conversion/persuasion cost.

- **`new-spec` now prompts for design-readiness on ui-shaped specs (core 0.9.0).** When
  `Shape: ui` is confirmed, a new step 4d checks whether a grounded aesthetic reference
  (`aesthetic-direction` output) exists before the Acceptance Criteria are written,
  offers to run `design-critique` on any existing affected surface, and requires at
  least one design-intent AC whose outcome is observable from the rendered surface —
  not derivable from code. If the experience pack is absent, it notes that in Assumptions
  and proceeds. This is the spec-authoring complement to `work-loop`'s pre-EXECUTE
  design-intent pass: both target the same failure mode (technically correct surfaces
  with no design sense) at different stages of the loop.

- **`work-loop` now includes a pre-EXECUTE design-intent pass and an `experience-reviewer`
  gate for user-facing surface diffs (core 0.8.0).** When a change produces a user-facing
  surface — a new page, a redesigned screen, a pack card, a docs page — the PLAN section
  now recommends running `aesthetic-direction` and/or `design-critique` before writing
  code (advisory in both light and full mode, analogous to "write the test first"). For
  full-mode user-facing surface diffs, `experience-reviewer` is added to the specialist
  reviewer roster alongside `security-reviewer` and `quality-engineer`: it receives the
  rendered output plus the grounded aesthetic reference and constraints, and runs with
  the standard select-or-note fallback when the experience pack is absent. Decision
  recorded in ADR-0047.

- **New `catalogue-curation` pack — the catalogue-operator's toolkit (opt-in, repo-scope).**
  Skills to grow and maintain an agent-skill catalogue: `propose-catalogue-pack`
  (stand up a new pack), `assimilate-primitive` / `assimilate-repo` (bring
  external skills/agents/hooks in — safely, and reshaped to the repo's craft,
  resumable via a ledger), and `export-catalogue` (produce a white-label or
  attributed derivative for another org or domain, with a fail-closed leak
  check). Ingested code runs the repo's own lints + SAST/SCA before it lands; a
  guard blocks any change to the `agentbundle` engine or credential brokers
  through the pack. Domain-agnostic — the same toolkit serves a non-SDLC
  catalogue. Requires `core` + `governance-extras`; not in any default profile.
  (RFC-0059, ADR-0048.)
- **`msg-to-markdown` is now a pure-Python skill that also reads `.eml`, and
  emits the unified output contract (converters 0.6.0).** The Outlook `.msg`
  converter is re-hosted from Node.js onto Python: `.msg` is read via `olefile` +
  first-party MAPI decoding (replacing the `msg-parser`/`extract-msg`/npm readers
  — see ADR-0046), and MIME `.eml` is now supported through the same render path
  (multipart bodies, nested `message/rfc822`, richer headers). Every conversion
  now carries the same versioned frontmatter contract (`contract-version`, `tier:
  0-no-ml`, `content-type`, `ingestion-quality`) that `file-to-markdown` emits, so
  email ingests into a context layer exactly like documents. It preserves headers
  (From/To/CC/**BCC**/Date/Importance), the body (HTML reduced to Markdown, or
  plain text), and an attachments table, and it **closes the attachment-extraction
  path-traversal sink** the old Node script carried (every write is basename-
  reduced and confined). No Node.js, no ML/OCR model, no network call.

- **`file-to-markdown` gains three opt-in higher-fidelity capabilities
  (converters 0.5.0).** All three are **off by default** — the default one command
  (`python scripts/convert.py "<file>"`) is unchanged. (1) **`--enrich`** turns on
  Docling's **local-model** enrichment on the Tier-2 path — formulas → LaTeX, code
  understanding, figure classification and captioning. It is local-model-only by
  construction (Docling's remote-services / remote-VLM path is never enabled), so
  enrichment can never become a hidden data-egress channel; enriched captions are
  treated as untrusted model output (inert body content, never instructions).
  (2) **`--chunk`** also writes Docling `HybridChunker` output (tokenizer-aware,
  structure-preserving chunks) to a `<basename>.chunks.jsonl` sidecar — one JSON
  record per chunk carrying the full contract field set — so an extraction can feed
  a retrieval store as chunks, not just a flat file (needs the
  `docling-core[chunking]` tokenizer extra, installed on demand). (3) **`--tier3`**
  assembles adopter-obtained managed-OCR text into the unified contract with
  `tier: "3-managed-api"` and `requires-review: true`. Tier 3 crosses a
  **data-egress boundary**, so it is **explicit-only and never auto-reached**, and
  the skill itself **makes no network call** — you run the approved vendor through
  your own transport, and the skill validates an egress declaration
  (`{endpoint-allowlist, residency-region}`), stamps the contract, and records the
  destination in provenance. See the skill's `references/tier3-managed-api.md` for
  the adopter controls (vendor retention/no-training, transport-binding, and
  redaction as your responsibility — documents are sent unmodified). No ML model or
  per-vendor data ships with the pack.

- **`file-to-markdown` reads scans and non-diagram images via agent-vision
  (converters 0.4.0).** The image branch gains a general **`text-table`**
  strategy for non-diagram content — a screenshot of prose, a table image, a
  form, a receipt, a scanned page — that emits Markdown prose and tables instead
  of forcing everything through the diagram extractor. For a scanned or
  image-only PDF (the case the Tier-0 floor flags `requires-review` and points at
  Tier 1), a new `scripts/rasterize_pdf.py` renders each page to an image, which
  the in-session model then reads. This is **Tier 1 (agent-vision)**: the
  already-running model reading a rendered image — *not* an installed OCR model.
  The read carries `tier: "1-agent-vision"` with an honest
  `extraction-confidence`/`requires-review` signal, treats all document text as
  **untrusted data** (transcribe, never obey — a prompt-injection defense), and,
  when the PDF has a digital text layer, is **cross-checked** against it to bound
  hallucination. The page rasterizer is `pdf2image` (MIT), installed on demand
  (`python scripts/rasterize_pdf.py --check`) and needing a system poppler; it is
  never auto-installed, and when it is absent the skill keeps the Tier-0 output
  and says so rather than crashing. Tier 1 adds **no new network egress from the
  skill** — though a cloud-hosted in-session model still receives the page
  content at its already-approved endpoint.
- **`file-to-markdown` gains a no-ML Tier-0 floor and a versioned output
  contract (converters 0.3.0).** Where Docling's ML models are banned or
  un-fetchable, `file-to-markdown` can now convert a digital PDF (via `pypdf`),
  Office files (`.docx`/`.xlsx`/`.pptx`, degrading to a stdlib path when the
  ordinary library is absent), and the everyday text formats (HTML, EPUB,
  CSV/TSV, OpenDocument, `.eml`) to Markdown using only pure-Python or standard-
  library parsers — no ML model, no network. Docling stays as the higher-
  fidelity Tier 2 for `.xls` and images. Every extraction, across both the
  document and image branches, now carries one versioned YAML frontmatter
  contract recording provenance and a quality signal (`contract-version`,
  `tier`, `extraction-confidence`, `requires-review`), so a scanned PDF that
  yields sparse text is flagged `requires-review` and pointed at an escalation
  tier instead of passing silently. The default invocation is unchanged
  (`python scripts/convert.py "<input-file>"`); the Tier-0 PDF/Office libraries
  install on demand (`python scripts/convert.py --check`), and untrusted input
  is parsed defensively (XXE-safe XML, decompression-bomb guards, output-path
  confinement, resource ceilings).

### Fixed

- **`file-to-markdown` image extraction no longer silently loses elements
  (converters 0.2.3).** The image reconciler used to collapse every element
  that shared a `(type, name)` into one before checking where it sat — so two
  genuinely distinct nodes with the same label (a second "Validate" step, a
  repeated "Queue") were merged into a single element with no warning, and
  elements the model saw but couldn't label were dropped entirely. The
  reconciler now clusters by position: same-named nodes that overlap across
  tiles still merge, but spatially distinct ones are kept as separate elements,
  and unlabeled elements are retained and shown as `(unlabeled)`. The document
  branch (`convert.py`) now fails with actionable guidance — naming
  password-protection/encryption and corruption as likely causes — instead of a
  bare stack trace, and the image branch warns (to stderr; stdout stays clean)
  when handed a multi-frame image (animated GIF, multi-page TIFF) that only its
  first frame is read.

### Added

- **`architect-diagram` now draws timeline, quadrant, and mindmap diagrams (architect 0.10.0).**
  The diagram skill routes three new intents to Mermaid: a **timeline** for
  roadmaps / chronologies / release history, a **quadrant** (`quadrantChart`)
  for 2×2 prioritization and positioning, and a **mindmap** for hierarchical
  decomposition — joining the existing C4 / sequence / state / ER / flowchart
  set. Each has its own on-demand syntax reference and rubric budget. Because
  the three are newer Mermaid grammars with uneven enterprise-wiki rendering,
  the skill offers them with the same rendering-support caveat it already
  applies to `architecture-beta` (with a table / bullet-list fallback), so
  flowchart and C4 stay the defaults. The diagram rubric also gains explicit
  per-type complexity budgets plus additive accent- and edge-count caps.
- **Docs now call out the catalogue and skill/pack format as first-class, and ship an `llms.txt`.**
  New `docs/architecture/catalogue.md` names what a catalogue *is* on disk (the
  `packs/` + `.claude-plugin/marketplace.json` markers), how `agentbundle`
  resolves one through its four-layer chain, and how to point it at your own —
  the starting point for standing up your own catalogue. New
  `docs/architecture/skill-and-pack-format.md` maps the format in three layers
  (the agentskills.io skill standard, the pack envelope, projection). A root
  `llms.txt` indexes the key docs so an agent can read the relevant pages
  instead of scanning the whole repo. The architecture and top-level READMEs
  route to both.
- **The `methodology` output shape for research (research 0.6.0).** Ask
  *"the best way to do / run / build / train X, end to end, for my situation"*
  and `/research` now answers with a **method, not a reading list** — a staged,
  contingency-adapted, maturity-aware, evidence-graded description of how the
  activity is done. The shape produces `<topic-slug>-methodology.md` (episodic) or
  `methodology.md` (project mode) from six sections, each grounded in a discipline:
  a SIPOC scope frame, a stage spine, **mandatory** contingency branches
  (which path *your* situation takes) and a **mandatory** maturity ladder
  (novice→expert, or crawl→walk→run for one-off deliverables), failure modes, and
  GRADE evidence tags. It defaults to `applied` depth, is slide-ready for
  `markdown-to-pptx` with no reshaping (sections at H1, stages at H2, no H3), and
  is fenced against `frame-domain` (product/MVP grounding) and
  `map-internal-process` (your own operations). Prompt-only — no new dependency,
  no runtime engine.
- **`agentbundle list-installed` — see what you actually have installed (CLI 0.10.0).**
  A new read-only command lists every installed `(pack, adapter)` row across the
  user and repo scope with its version and an `up-to-date` / `upgrade-available`
  / `unknown` status against the catalogue. The status check runs by default and
  degrades to `unknown` (never an error) when the catalogue can't be resolved;
  `--no-check` / `--offline` skips it for a fast, network-free listing; `--scope`
  filters to one scope; `--check-drift` adds a per-row count of files edited
  locally since install. Closes the gap where no command could report installed
  state — only what a *catalogue* offered.
- **The release loop — a new opt-in `release-engineering` pack (release-engineering 0.1.0).**
  Adds the SRE/ops **outer loop** above `work-loop`'s inner build loop: a
  **`release-lead`** agent (the outer-loop supervisor — a peer of `work-loop`'s
  supervisor and `discovery-lead`, **not** a `work-loop` mode) and a
  **`release-loop`** skill that deploys the integrated whole to an **ephemeral
  environment**, runs e2e, observes telemetry, feeds deployed findings back to the
  inner loop (no human relay), redeploys, and **iterates until the deployed whole
  converges** — then stops at the **human consent gate** for the prod ship (G5),
  surfaced as a **release-readiness record** to ratify rather than a bare
  go/no-go. Autonomy is carved by **minimum-regret**: the agent runs the inner and
  outer loops on reversible ephemeral envs unwatched; humans gate the irreversible
  exits (first real users or data, data migrations, spend over threshold,
  security/auth-boundary changes, anything irreversible, and prod). Convergence up
  to that gate is judged by **policy** (canary SLOs + e2e coverage of the changed
  surface + flake < 2%), with **DORA** as the health signal. The pack is
  **repo-scope** (co-located in the build repo where `core` is installed) and
  **reuses** `core`'s `operational-safety` modules + `quality-engineer` +
  `security-reviewer`, consuming the discovery sidecar by convention — **no new
  runtime engine and no new reviewer**. This completes the **company OS**: product
  (discovery) → engineering (build) → SRE/ops (release). *(Implements RFC-0049,
  now Accepted; ADR-0044 records the inner/outer split + the minimum-regret deploy
  carve; the `release-loop` spec is Shipped, all 15 ACs checked.)*

### Changed

- **Shipped skill content is now self-contained — internal RFC/ADR citations removed.**
  Skills, subagents, reference docs, and scripts across `core`, `governance-extras`,
  `atlassian`, `converters`, `research`, and `product-engineering` no longer cite the
  bundle's own governance artifacts (`RFC-00xx`, `ADR-00xx`, `docs/rfc/…`, spec
  task/AC numbers) as load-bearing references — each rule now reads on its own terms.
  Adopters install these skills without the bundle's `docs/` tree, so a dangling
  `RFC-00xx` pointer was an unresolvable reference; the rules are unchanged, only the
  provenance citations are gone. Real external standards (e.g. RFC-1918, RFC-9457) are
  left intact. Also: the `.claude/skills/` README inventory now matches the projected
  skill set, the scaffolded `docs/product/roadmap.md` is marked as a template, and the
  `work-loop` activation hook's docstring points at `tools/hooks/README.md` for wiring.
- **`agentbundle upgrade` reports honestly, and its multi-adapter refusal is
  actionable (CLI 0.10.0).** A same-version re-apply no longer prints
  `upgraded: X -> X`; it reads `re-applied: <pack> @ <scope> <version>
  (already current)`, or names the count of locally edited files kept as
  `.upstream` companions when there were edits — and an upfront notice before the
  confirm tells you how many edits will be preserved. The "pass --adapter"
  refusal (also in `diff` / `uninstall`) now lists each installed adapter **with
  its version**, e.g. `claude-code (0.9.0), codex (0.9.0)`, so the next command
  is obvious without a second lookup.
- **The traceability lint gains a root→leaf reachability pass (core 0.7.1).** On the
  authoritative sidecar graph, `work-loop`'s `lint-traceability.py` now flags every
  node that does not lie on a path from `root` to a leaf — a **`UNREACHABLE`
  (disconnected subtree)** finding, additive to and non-overlapping with the
  existing per-node orphan check. Where the presence check caught only the orphan
  *tip* of a broken branch, reachability catches the **whole** stranded subtree —
  the refinement the `discovery-loop` cascade backstop depends on (RFC-0053 AC34).
  A cross-repo reference resolved through the value-stream rollup is a clean
  terminus (a legitimately federated graph is never failed); an *unresolvable*
  cross-repo hop is surfaced informationally, **never silently counted as closed**
  (the sidecar is untrusted input — a fabricated edge must not green a stranded
  subtree). `UNREACHABLE` joins the `--strict` tier (exit 1); dangling edges and
  cycles stay hard in every mode. Reachability runs in sidecar mode only — a
  standalone derived graph is legitimately partial and multi-root. The
  `discovery-loop` skill's traceability seam is updated to record the dependency as
  met. *(Amends the `traceability-lint` spec; closes the
  `discovery-loop-traceability-reachability` backlog item and the RFC-0048
  § Amendments 2026-06-30 cross-spec gap.)*

### Added

- **The discovery-side producer skills now emit the traceability markers the
  structural-orphan lint reads (experience 0.3.0, product-engineering 0.10.0).**
  `map-screen-flow`'s per-screen brief carries a bold-body `- **Type:** screen-brief`;
  `map-customer-journey` records each frontstage action as a `- **Action:** <slug>`
  marker and `blueprint-service` each backstage service as a `- **Service:** <slug>`
  marker; `frame-intent`'s intent template gains an optional `- **Kind:**
  outcome|opportunity` field (beside the existing `Level:`), and `decompose-intent`
  carries `Kind:`/`Level:` onto decomposed child intents. `work-loop`'s
  `lint-traceability.py` recognizes each producer node **by marker, not path** —
  previously only `frame-domain` emitted markers, so a fail-closed traceability
  up-edge would have been load-bearing on markers that didn't exist. Three
  reconciliations ride along: **CONVENTIONS § 4** is corrected to describe the
  marker as the **bold-body field** the lint reads (it had said "frontmatter
  `type:`" — a factual erratum); the lint's **`recognize_screens` now recurses**
  (`core` 0.7.1 → 0.7.2) so a real nested per-screen brief
  (`screens/<slug>/<screen>.md`) is found, not only a flat one; and the
  **intent↔chain rung mapping** is documented in `product-engineering`'s
  `intent-model.md` (`Kind:` → outcome/opportunity rung, `Level: capability` →
  capability rung), landing the `recognize_ladder` docstring. (Closes the
  `discovery-loop-type-marker-producers` and `screen-brief-nested-path-glob`
  backlog items; RFC-0053 AC36 / DRIFT-G, RFC-0048 note 04 + § Amendments 2026-06-30.)

- **`new-rfc` now drafts RFCs that read from zero prior context and hands you
  decisions you can make in the chat message itself (governance-extras 0.5.0).**
  The skill glosses every project-coined term, acronym, and sibling-RFC
  back-reference in plain language on first use (inline, not a glossary), so a
  reviewer who hasn't read the related RFCs can still follow it; a new
  **cold-reader check** in the pre-handoff gate dispatches a context-denied
  subagent — given only the RFC text — to flag any jargon it can't resolve, so
  inherited vocabulary gets caught before a reviewer hits it cold. The
  research/de-risk handoff now presents each decision **self-contained** — the
  plain-language question, the concrete options with their trade-offs and the
  consequence of each, and a recommendation — so you can decide without opening a
  file. The how-to guide and the Tier-4 eval ride along.

- **The `product-engineering` pack gains the discovery loop — a `discovery-loop`
  skill, a `discovery-lead` agent, and two discovery reviewers (product-engineering
  0.9.0, implementing RFC-0053 / the `discovery-loop` spec).** The upstream loop
  turns a raw idea into a ratified, build-ready **decision brief**: it diverges
  across candidate product shapes (the new `explore-options` skill), converges the
  chosen one through a lens roster, pauses at three consent gates (G0 / G1.5 / G2),
  emits a **connected hypothesis** with validation hooks (the new `plan-validation`
  skill — *converged ≠ validated*), and hands off to `work-loop` at G3 — **with no
  new engine, scheduler, or service**. It ships as content: the agent + skills, a
  carried, versioned **sidecar-schema** reference, and a **plan-tree** template
  asset. `de-risk-intent` gains a validation-hook field and `decompose-intent` an
  optional ranking step. The two discovery reviewers
  (`discovery-threat-reviewer` / `discovery-reliability-reviewer`) are **distinct**
  from `work-loop`'s code reviewers, required at G2, degrading only in depth. A
  coordinator ADR (ADR-0043) records the no-engine, spike-confirmed shape, and a
  four-page Diátaxis guide set under `guides/product-engineering/` covers it.
  The discovery loop is the full-battery home of the self-coverage gate (RFC-0051),
  wired as its pre-G2 phase. *(Eval coverage for the three new skills is a tracked
  follow-up, matching the `frame-domain` precedent.)*
- **`new-spec` and the spec-metadata contract gain an optional `Discovery:` up-edge
  header + discovery-artifact `type:` markers (core 0.7.0, format-only — DRIFT-G).** A
  spec descended from an upstream discovery artifact records it in a `Discovery:`
  header (the discovery-side sibling of `Brief:`), the producer edge a traceability
  check walks; discovery-side artifacts carry a `type:` marker so a check finds them
  by marker, not path. Format only — no operating-model doctrine. This resolves
  RFC-0048 acceptance blocker #4; the traceability lint's `--strict` flip is
  sequenced after the header lands (warn-only until then).
- **The `work-loop` skill now carries the self-coverage gate as a thin, named
  phase (core 0.6.0, implementing RFC-0051 for the `work-loop` slice).** The loop
  doctrine now names its existing passes as the gate's steps (REVIEW *is* the
  fresh-context-adversarial step; the PLAN assumption trio + declined-pattern
  register *are* the pre-mortem hook; `Surface` + DECIDE's apply/defer routing
  *are* the resolve-vs-surface bones), and adds two net-new spec-time checks
  governed by the existing light/full mode — a **resolve-vs-surface disposition
  record** (every open item is resolved-with-referent or surfaced-with-reason) and
  a **conditional domain-grounding** check (fires only on an ungrounded
  load-bearing domain claim, else degrades). One new end-of-session-checklist
  refusal item makes the disposition record non-skippable. A self-contained
  `references/self-coverage/resolve-vs-surface.md` calibrates the
  resolve-vs-surface call. No new reviewer, no new pack, no `docs/CONVENTIONS.md`
  change, no second right-sizing knob; the heavy seven-module design-convergence
  battery stays `discovery-loop`'s, never bolted onto the build loop.
- **The `design-craft` pack grows up into the `experience` pack — the design/UX
  seat that carries the whole design thread from journey to realization
  (experience 0.2.0, implementing RFC-0050 D1–D10; the rename is bridged by the
  already-Accepted ADR-0038, frozen governance untouched).** `design-craft` is
  **renamed in place to `experience`** (dirs, manifests, guides dir, the
  catalogue rows, and the framework-agnosticism CI lint
  `lint-design-craft-agnostic.py → lint-experience-agnostic.py` retargeted to
  `packs/experience/`, env `DESIGN_CRAFT_ROOT → EXPERIENCE_ROOT`; the RFC-0033
  docstring citation and the `(design-craft-pack AC8)` CI step tag stay pinned;
  **no install-time alias**). The seat gains **five new pure-markdown skills**:
  the connective trio **`map-customer-journey`** (stages × actions / emotions /
  pains / opportunities, with a platform/surface axis), **`map-screen-flow`**
  (the journey's screens *sequenced* — transitions, error/edge flows, the
  per-screen state matrix, one per-screen brief per screen, a cross-brief
  consistency pass, and a **non-droppable whole-journey steel thread** that
  degrades from an MCP prototype to a text-only walk but never to nothing, plus
  an optional design-tool handover that is instructions-not-pixels), and
  **`blueprint-service`** (frontstage / line-of-visibility / backstage / support,
  the backstage column the slicing instrument handed to `architect` / `contracts`
  by-name); the inside-out **`map-internal-process`** (APQC L3→L4, as-is + to-be
  with a delta table, SIPOC, a mermaid swimlane, a pain/waste register); and the
  behavioral-pillar craft skill **`interaction-design`** (feedback & timing,
  input & forms, component state machines as mermaid `stateDiagram-v2`, purposeful
  motion honoring reduced-motion, navigation-as-behavior, gesture, cognitive-law
  fit — enriching the per-screen brief, owning no artifact). The three-part
  **`quality-floor`** (handle-all-states + accessibility + reduced-motion, now
  with `permission/denied` as an additional gated state) becomes the pack-shared
  floor every consuming skill defers to. **`aesthetic-direction`** now grounds
  each named goal in persona + precedent + standards + platform conventions and
  carries the surface axis; **`design-critique`** gains a **taste mode** while
  staying an interactive authoring-time skill. A forked-context **`experience-reviewer`**
  agent gives the design step an independent design-time review (grounded
  aesthetic reference + platform fit + cross-brief coherence + the full quality
  floor incl. accessibility) — the only independent a11y check between
  human-value-add gates; collision-hardened name + a design-time-only `description`
  cue (never code diffs, never architecture design docs). Artifact paths resolve
  through a new `[experience]` layout table (`parent = "docs/design"`,
  config → default → discover-by-marker). The five new skills join the pack's
  eval surface (trigger + Tier-4 judge). **Pure-markdown method + manifests + one
  CI-lint rename — no runtime, hook, validator, values table, or pixel comp**
  (RFC-0033 / ADR-0024 guardrails unchanged). User-scope-default: re-aggregates
  `marketplace.json`, not projected into this repo's tree.
- **`voice-and-microcopy` (in `product-engineering`) learns the screen flow
  (product-engineering 0.8.0, RFC-0050 D5).** When a `map-screen-flow` per-screen
  state matrix is present it writes copy **per screen × state**, keyed to the
  matrix; absent one it behaves as before (detect-and-degrade). The `experience`
  and `product-engineering` READMEs now cross-link, so the design seat reads as
  one even though the words live in PE.

- **A new `lint-traceability.py` work-loop script in the `core` pack mechanically
  checks that the product-team artifact chain holds together — `outcome →
  opportunity → capability → screen → action → service → contract → spec →
  component` — and flags every structural orphan (a node with no producer above
  it or no consumer below it), across repositories (core 0.5.0, implementing
  `docs/specs/traceability-lint`; RFC-0048 Decision 6, consuming the RFC-0053
  traceability slot).** It generalizes `receive-brief`'s brief↔spec coverage lint
  to the full nine-layer chain: it reads an authoritative sidecar
  `_state/traceability.json` when present (by convention + its `schema_version`
  stamp) or derives the edge set from local artifacts when absent, resolves each
  cross-repo edge endpoint to **local / satisfied-by-reference / unresolvable**
  (an unresolvable target is reported `unknown / not-yet-catalogued`, never a
  false orphan), and reports orphans informationally (exit 0) while failing hard
  (exit 1) on a dangling edge or a cycle. `--strict` additionally fails on any
  orphan for the convergence / CI gate. It is **structural only** — it never
  judges whether a node is parented to the *right* outcome (semantic scope-creep
  stays a human call). It no-ops cleanly in a repo with no discovery chain, runs
  stdlib-only, and projects to every adapter like `lint-spec-status.py`.

- **A new `frame-domain` skill in the `product-engineering` pack grounds a product
  in its real-world domain and bounds its MVP before any screen, service, or
  architecture is drawn (product-engineering 0.7.0, implementing RFC-0048
  Decision 4).** Run at the discovery loop's G1.5 Domain & MVP point or
  standalone, it produces **two typed artifacts** from one `research`-grounded
  pass: **Domain Framing** (`domain-framing.md`, `type: domain-framing`) — a
  real-world-activity half (how the activity is really done · best practice ·
  naive-design failure modes, grounded by wrapping `research` applied mode) plus a
  brownfield current-system half (reverse-engineered via `decision-archaeology` +
  architecture extraction, omitted with a note when greenfield); and **Scope
  Boundary** (`scope-boundary.md`, `type: scope-boundary`) — the MVP out-of-scope
  register, each excluded capability paired with its appetite reason, the
  scope-creep guard the brief inherits and refines at G3. Each artifact carries a
  stable marker and resolves its write path in three tiers (config → designed
  default → discover-by-marker); findings the wrapped research could not ground
  surface as named residual assumptions, never silent assertions; absent optional
  dependencies degrade cleanly rather than fail. Prompt-only (Charter Principle 3).

### Changed

- **The `new-rfc` skill now documents a convention for recording post-publication
  RFC corrections (governance-extras 0.4.0, implementing RFC-0055).** A published
  RFC's body is frozen, but it can still need a correction — a spec finds a gap, a
  later RFC reframes a decision. The skill now names two lifecycle-keyed sections
  for recording one *inside* the RFC: `## Errata` for a Frozen RFC
  (Accepted/Rejected) and `## Amendments` for an in-flight Open one. Corrections
  are append-only, and once a section accumulates (more than one entry, or any
  entry supersedes another) it splits into an optional two-layer structure — an
  authoritative *current state* layer over a dated *audit trail*, where the
  current-state layer wins on disagreement. The bundled `assets/rfc.md` template
  carries the same shape as a clearly-conditional commented scaffold, so it travels
  into every RFC an adopter drafts without being filled into empty sections.
  Forward-only — existing correction sections are untouched.
- **The `new-adr` skill now helps you isolate the decision before drafting, so
  ADRs stay lean (governance-extras 0.4.0).** Four guidance refinements, none of
  which changes the ADR template's sections or fields: (1) a "frame the decision
  before drafting" step that *offers, doesn't force* — it infers the frame when
  the decision is already crisp and walks a short decision frame (the decision in
  a sentence, the problem, the alternatives, the winning driver, the tradeoff,
  any prior ADR it amends) when the request arrives tangled; (2) stronger title
  discipline — the title *identifies* the decision rather than encoding the whole
  rationale; (3) a one-decision-wide push-back that routes an umbrella of three
  or more load-bearing sub-decisions to an RFC spawning smaller ADRs; (4)
  pointer-like metadata guidance — `Consulted`/`Related` are short reference
  lists, not prose. The behavioral evals gain matching usability assertions.
- **The `new-rfc` skill now sizes each RFC to its two humans — the author and
  the reviewer (governance-extras 0.4.0, implementing RFC-0054).** Four changes,
  the deferred half of the human-consumption work whose RFC-0014-clean half
  shipped in 0.3.2: (1) a `Decision weight: light | standard | heavy` header
  field that right-sizes research depth and the pre-handoff gate — an
  author-picked prose heuristic off `work-loop`'s risk triggers, defaulting to
  `standard`; (2) a top-of-doc `## Reviewer brief` orientation grid that gives a
  reviewer first-screen bearings above "The ask"; (3) "The ask" decisions
  rendered as a table (with a per-decision *reviewer action* column) instead of
  numbered prose; (4) a guided shape/intake step before research that asks
  framing questions when intent is vague and infers when it's already specified
  — offered, never forced. Weight-based right-sizing changes how much research
  and draft an RFC carries, never whether a mandated pre-handoff gate check runs.
- **The `new-rfc` skill now drafts more reviewer- and author-friendly RFCs
  (governance-extras 0.3.2).** Three refinements, none of which changes the
  answer-first template or the research→draft→gate flow: (1) the skill draws an
  explicit *body-as-argument* line — a section that changes the reviewer's
  decision stays in the RFC body, while proof-of-work (research transcripts,
  prior-art matrices, review logs) is summarized and its detail linked from the
  optional `NNNN-notes/` companion; (2) the pre-handoff gate runs the same checks
  but hands back a concise, reviewer-oriented *readiness summary* with the heavy
  proof linked rather than pasted; (3) RFC titles are kept short and identifying,
  with the fuller explanation living in "The ask" so the RFC index stays
  scannable.
- **One pack can now be installed for several adapters at the same scope, and
  the adapters that all read `.agents/skills/` share one skill copy
  (RFC-0052).** The `agentbundle` install identity is now the *footprint* — the
  set of file paths a `(pack, adapter, scope)` install writes, each with its
  content SHA — not the pack name. Installing `research` for `codex` after
  `claude-code` now succeeds (their trees are disjoint), and installing it for
  `cursor` after `codex` *shares* the existing `.agents/skills/` skill files
  instead of fighting over them. A genuine collision — the same path at
  different content, or two different packs claiming one path — is refused,
  naming the conflicting paths; `--force` keeps your copy as a `.upstream`
  companion. `uninstall`, `upgrade`, and `diff` gain an `--adapter`
  disambiguator (required only when a pack has more than one adapter row at the
  scope); `uninstall` removes a shared file only when its last owner goes.
  **Behaviour change:** cursor, gemini, and copilot now project the *skill*
  primitive to the shared `.agents/skills/` home (joining codex) instead of
  their native `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`; their
  agents/hooks/commands are unchanged. After an install that writes a shared
  skill, stderr names the other adapters that read it.
- **The install state file is now schema `v0.4` (`[pack.<name>.adapters.<adapter>]`).**
  Migration is greenfield: a pre-v0.4 state file is refused (on read and write)
  with a re-install prompt — there is no auto-converter, and existing installs
  re-install to regenerate state. Existing cursor/gemini/copilot installs may
  leave a now-unused `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`
  (or `.copilot/skills/`) tree behind; re-installing lands skills at the shared
  home.
- **The `work-loop`'s two reviewer routing tables now live in the depth-library
  skills they route into, not in `work-loop`'s `SKILL.md`.** The security
  boundary→module table moved into `security-checklists`'s Module index and the
  operational failure-mode→module table moved into `operational-safety`'s Module
  index; the `work-loop` `security-reviewer` and `quality-engineer` review steps
  now dispatch against those indexes. This removes the last copy-paste duplication
  between `work-loop` and the two depth libraries — the routing table and the
  modules it routes to can no longer drift apart — and trims `work-loop`'s
  `SKILL.md` further under its size cap. The routing *behavior* is unchanged:
  orchestrator-loaded (never subagent-self-discovered), loaded 1–3 / 1–N and
  never a flat march, with the reliability-vs-security carve and the
  infra-mandatory security pass intact.
- **`work-loop`'s `SKILL.md` moves more situational depth into on-demand
  `references/`.** Three blocks that only matter in a subset of loops were
  relocated out of the always-loaded `SKILL.md` body, each leaving a
  load-bearing trigger/contract one-liner inline: the **visual / manual-QA**
  verification-mode depth → new `references/verification-modes.md` (loaded when a
  task picks that mode); the **pre-EXECUTE review** depth (how the reviewer
  measures a structural change, the re-plan re-fire, the gate mechanism, the
  infra-mandatory secure-design detail) → new `references/pre-execute-review.md`
  (loaded when a trigger fires); and the **supervisor parallel-dispatch gate**
  detail → the existing `references/supervisor-mode.md` (it had been duplicated
  inline). No behavior change — the doctrine is identical, just disclosed
  progressively; `SKILL.md`'s body drops further under its size cap.

### Fixed

- **The `agentbundle` CLI now writes LF line endings on every platform.** Every
  generated text artifact — adapter projections (Kiro, Cursor, Codex, Gemini,
  Copilot), the composed `AGENTS.md`, the self-host tree, merged
  `.claude/settings.json`, hooks, and TOML/JSON config — is emitted with `\n`
  regardless of OS. Previously, running the CLI on Windows produced CRLF
  (Python's text-mode writers translate `\n`→`\r\n` there), so a repo populated
  on Windows drifted from one populated on macOS/Linux and polluted diffs with
  line-ending churn. All 24 text-mode writers now pass `newline="\n"`, a
  repo-root `.gitattributes` pins `* text=auto eol=lf` at the commit boundary,
  and an AST guard test fails CI if a future writer omits the kwarg.

### Added

- **The ADR *template* now offers three optional fields — a first-screen Decision
  summary, a named Revisit-if trigger, and a structured Confirmation
  (governance-extras 0.4.0, implementing RFC-0056).** Distinct from the track-1
  `new-adr` change above (which refined guidance and changed none of the
  template's sections or fields), this track-2 change adds template surface, all
  optional and lean-keyed: (1) a `## Decision summary` block before Context
  (Decision / Because / Applies to / Tradeoff accepted / Revisit if), offered once
  an ADR is long enough that the decision isn't on the first screen and skipped on
  a short one; (2) a named `Revisit if:` trigger whose canonical home is
  Consequences (so it survives deletion of the optional summary), with `stable —
  no foreseeable trigger` as a valid explicit value; (3) a `Mode` / `Signal` /
  `Owner` sub-structure for the existing Confirmation section, where an explicit
  `Mode: none` is preferred over silently dropping the section. None of the three
  is mandatory, the skill and how-to guide describe them in the offer-don't-force
  shape, and the behavioral evals gain three matching format-dependent assertions.
  Forward-only — no existing ADR is converted.
- **Guides for shaping a new engagement — product vision, product strategy, and
  the architecture concept.** Three new how-tos document the top of the shaping
  funnel that previously had no guide:
  [*Frame a product vision*](../guides/product-engineering/how-to/frame-a-product-vision.md)
  and [*Shape a product strategy*](../guides/product-engineering/how-to/shape-a-product-strategy.md)
  in the `product-engineering` pack (the two product altitudes of `frame-intent`,
  with their market-existence de-risk), and
  [*Shape an architecture concept*](../guides/architect/how-to/shape-an-architecture-concept.md)
  in the `architect` pack (the ≤½-page Stage-0 concept `architect-design` agrees
  before a full design doc). A new cross-pack explanation,
  [*Shaping a new engagement*](../guides/_shared/explanation/shaping-a-new-engagement.md),
  ties them together — how product intent and the architecture concept co-shape
  each other at engagement start — and the affected pack indexes and existing
  guides gain cross-links.
- **An optional grounding surface lets you record where you deploy and how you
  verify — in files you already own.** The `core` seed `AGENTS.md` "Commands
  you'll need" gains an **optional** infra/verification command block
  (`<deploy>` / `<smoke / verify-status>` / `<teardown>` / `<seed-test-data>`),
  and the `reference.md` golden-path slots now prompt for the managed-runtime /
  platform target, framework-/library-level contracts, and where verification
  tooling lives. The work-loop infra preflight reads these recorded coordinates
  **if present** and falls back to cold oracle discovery if absent — a repo that
  fills nothing runs exactly as before. Recorded values **seed** oracle
  acquisition, never replace it; a coordinate that contradicts the live oracle
  is surfaced as a drift signal. No new config file, and absence never fails the
  loop or any CI gate. `adapt-to-project` and `init-project` now optionally
  offer to record these coordinates.
- **A how-to for shipping your organization's standard stack as a reusable
  pack.** [*Ship your organization's standard stack as a reusable pack*](../guides/_shared/how-to/build-an-org-stack-pack.md)
  walks a platform lead through composing an org-stack pack from primitives that
  already exist — a filled-in `reference.md` seed (plus optional
  `CONVENTIONS.md` / `AGENTS.md` deltas), `.apm/skills/<framework>/` skills as
  the work-loop's framework-grounding detect target, and a repo-scope profile
  that installs the org's forked `core` first — distributed from a detached fork
  the organization owns via the editable-install path, with no upstream
  dependency. No new machinery. (RFC-0047 Decision 5, ADR-0037 D3.)
- **`architect` grounds the design phase in platform reality — a backed
  serverless workload-class lens plus two dual-consumed disciplines.** The
  `architect` pack gains **`lens-serverless.md`** (in both `architect-design`
  and `architect-review`), the cloud-agnostic serverless workload-class lens
  that fills the slot the well-architected rubric named but never backed. It
  carries five durable, concern-grouped concerns — execution & throughput
  limits + the **sync-vs-async gate**, cold-start & readiness, scale-to-zero
  economics / capacity floors / cost cliffs, statelessness & idempotency &
  delivery semantics, and private-serverless network reachability — applied
  across the whole serverless class (compute, data, search/analytics, event
  glue). Two cross-cutting disciplines ride the same routing axis: a
  **platform-contract grounding discipline** (`architect-design` grounds every
  load-bearing managed-service contract on a critical path in an authoritative
  source with stated confidence — never model memory — and `architect-review`
  **independently re-checks** it) and a **synchronous-path viability check**
  (sum worst-case latency across every hop, compare it to the binding
  front-door timeout, and force a sync-vs-async gate for a long-running
  operation — caught at design *and* re-checked at review). The lens stays
  cloud-agnostic; version-specific numbers route to curated platform skills. The
  agentic lens gains a one-line cross-reference into the gate. **No new skill,
  reviewer, or executable tooling, and no per-vendor numbers ship.** (RFC-0045,
  ADR-0035.)

- **`work-loop` grounds its infrastructure inner loop in the platform's real
  contract, not model memory.** A new `core` skill,
  **`infra-contract-acquisition`**, runs a tiered, tool-keyed protocol that
  acquires a stack's real contract from the deterministic oracles its own
  toolchain ships (`terraform validate` + `plan`, `cdk synth`, `pulumi
  preview`, CloudFormation change sets, `kubectl --dry-run=server` + a
  machine-readable schema slice), declares its oracle tier and confidence, and
  degrades honestly to a runtime probe when the toolchain ships no strong static
  oracle. `work-loop` gains an **EXECUTE contract-grounding gate** ("acquire the
  contract before you guess a flag, schema shape, field constraint, or
  packaging assumption" — the infra generalization of "grep to verify a function
  exists before importing it"). A new `operational-safety` module,
  **`cloud-implementation-craft`**, is inlined into the **implementer's EXECUTE
  brief** (least-privilege-but-sufficient permissions, eventual-consistency
  waits, timeout / cold-start / backoff, dependency ordering,
  terminal-failed-state, the managed-runtime packaging / entrypoint model, and
  externalized script configuration). The infra preflight gains a fifth artifact
  (a **durable credential session** — establish once, reuse), a
  **reusable-script corollary** (every live interaction goes through a reusable,
  idempotent, externally-parameterized script), **phased oracle fidelity** (the
  cheap early oracle is necessary, not sufficient), a **readiness-aware
  data-plane probe** (in-network-if-private, write → read-back, poll-with-backoff,
  self-teardown), and a **symptom→layer log playbook** for failure localization.
  Contract-conformance review rides the existing `quality-engineer`, which
  re-derives the contract independently from the oracles — **no new reviewer or
  agent**, and **no executable tooling or per-vendor data** ships. (RFC-0044,
  ADR-0034.)
- **`product-engineering` gains two product altitudes above `capability` — and
  `Level` is now decoupled from `Scale`.** You can shape a greenfield product
  concept (or a multi-feature bet) as a `product-vision` intent (the existence
  bet: why this product should exist, for whom, through what wedge) or a
  `product-strategy` intent (the path: central challenge, guiding policy,
  coherent actions, problem/segment sequence), instead of being forced into a
  `feature`. `Level` is now an **open recognized set**
  (`product-vision › product-strategy › capability › feature`); `Scale` only
  *suggests* a starting altitude you override in a word, and `frame-intent` asks
  the altitude for concept-shaped input. The product-existence bet is de-risked
  once at the top as `market-existence` (market desirability **and** viability),
  distinct from feature-level `desirability`. A sibling-spawn detector *offers*
  to frame a product parent when work won't reduce to one shippable slice, and a
  retroactive-parent affordance back-links orphaned siblings at an inferred
  altitude. Existing `capability` / `feature` intents stay valid — the change is
  additive.
- **`init-project` recognises an `intent` from `frame-intent` as a fourth
  discovery source.** When the `product-engineering` pack is installed, the
  `frame → de-risk → decompose` loop hands its leaf into `init-project`'s value
  gate as an optional upstream source, alongside `research`, a PRD, and a
  `receive-brief` brief.

### Changed

- **The catalogue's seed lint is now opt-in by construction and renamed
  `lint-catalogue-seeds`.** `tools/lint-seeds.py` becomes
  `tools/lint-catalogue-seeds.py` (the CI job, its path filters, the
  `pre-pr-catalogue.py` gate, and the `tools/hooks/README.md` reference are
  renamed in lockstep), and **all** of its checks — the anti-leak blocklist and
  the placeholder-shape checks — now run only on packs whose `pack.toml` carries
  `[pack].lint-seeds = true`. The four first-party scaffold packs (`core`,
  `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) carry the flag,
  so their seeds stay enforced exactly as before; any other pack — including an
  organization pack that intentionally ships filled-in *instance* content — omits
  the flag and is unenforced by construction, with no edit to the lint or any
  central pack list. The flag is catalogue-internal metadata and is not projected
  to `plugin.json` / `marketplace.json`. (RFC-0047 Decision 6 / ADR-0037 D4.)
- **The work-loop's EXECUTE contract-grounding gate now fires on unfamiliar
  frameworks and libraries, not just infrastructure.** Before generating code
  against an unfamiliar internal framework or third-party library whose contract
  (a versioned signature, a deprecation, a call-order or lifecycle constraint)
  the agent doesn't already hold, the gate routes to the **same tiered oracle
  protocol** in `contract-acquisition` (the skill formerly named
  `infra-contract-acquisition`, renamed now that it grounds both surfaces) that
  infra uses: **T0** detect the
  installed version (the contract is version-specific); **T1** run the type
  checker / compiler against the call site (`mypy`/`pyright`, `tsc --noEmit`,
  `go build`/`vet`, `cargo check`) plus extract the installed package's API
  surface — the deterministic signature oracle; **T2** consult a curated
  framework-library skill for the behavioral contract no type encodes (the
  supplied-not-bundled tier — detect-and-recommend, never bundled); **T3**
  versioned docs / changelog; and a **runtime invoke-and-observe probe**. It
  declares its oracle tier honestly — strong (typed / stub-equipped) → medium
  (untyped-but-introspectable) → weak (dynamic / C-extension → probe-primary) —
  and `references/oracle-table.md` gives the concrete commands per ecosystem
  (Python / TypeScript / Go / Rust / Java). The bare "grep to verify a symbol
  exists" rule confirmed existence but never the contract; this closes that gap.
  The optional doc-retrieval surface stays **Tier-1 detect-and-stop — never
  auto-installed**, retrieved docs are treated as untrusted data, and
  `quality-engineer` re-derives the cited software contract slice at REVIEW,
  symmetric with infra. No new skill, no bundled per-library data.
- **`agentbundle uninstall` gains `--dry-run` and `--yes`, and confirms before
  removing anything.** Previously `uninstall` deleted every bundle-owned (Tier-1)
  file immediately with no preview. It now classifies each recorded file
  (`remove` Tier-1 / `keep` Tier-2) and: `--dry-run` prints that plan and writes
  nothing; without `--dry-run` it asks before the first removal (`--yes` skips
  the prompt; a non-interactive stdin refuses rather than hanging). Adopter-edited
  files are still preserved exactly as before.
- **`agentbundle install --force` confirms before its destructive cleanup, and
  `install` offers to upgrade an already-installed pack.** `--force` now lists the
  paths it will remove (the pre-RFC-0012 dist-tree subtrees, or orphan files) and
  asks before deleting; `install` gains `--yes` to skip that prompt. Used purely
  as a cross-scope bypass (no deletion), `--force` is unchanged and never prompts.
  **Migration:** CI that runs the *deleting* form of `install --force`
  non-interactively must now add `--yes` (a non-TTY without `--yes` refuses rather
  than deleting unattended — mirroring `upgrade`). Separately, installing a pack
  already installed at the requested scope now offers to run `upgrade` instead of
  flatly refusing; `install --yes` runs it, and a non-interactive stdin keeps the
  old `use 'upgrade'` refusal.
- **`agentbundle reconcile` and `list-targets` drop their dead `--scope` flag.**
  `reconcile`'s `--scope` had a single legal value (`user`) equal to its default,
  and `list-targets`'s `--scope` was parsed but never read; both are removed, so
  passing `--scope` to either now reports `unknown flag for <verb>: --scope`.
  Default behaviour of both verbs is unchanged.

- **`agentbundle upgrade` no longer takes `--to`; it derives the version and
  confirms (breaking).** The upgrade target is now read from the catalogue you
  point at (its `pack.toml` `[pack] version`) instead of an operator-supplied
  `--to` that was never validated against the catalogue. The command shows
  `installed → target`, asks before writing (`--yes` skips the prompt; a
  non-interactive stdin refuses rather than hanging), names both versions in the
  recap, and says so when you're already current. To upgrade to a specific past
  version, point the catalogue at that git ref. See the agentbundle CHANGELOG
  for the full migration note.

### Added

- **Agentic security boundaries are now control-level checks in the
  `security-checklists` `llm-agent` module (core 0.4.13 → 0.4.14; architect
  0.8.0 → 0.8.1; RFC-0029 / ADR-0032).** The `llm-agent` module — the
  orchestrator-inlined depth the `security-reviewer` reasons from — gains three
  control-altitude checks for the agentic boundaries the well-architected overlay
  previously named only at design time: **execution isolation & blast radius**
  (the three confinement axes — filesystem scope, network egress, resource/time
  caps — distinct from authorization), **inter-agent identity/privilege
  propagation** (a sub-agent must not amplify the spawning request's authority),
  and **memory poisoning** (a write gate that trust-checks content before it is
  persisted, plus the read side). The module's Standards surface adds the **OWASP
  Top 10 for Agentic Applications:2026** (ASI02 / ASI03 / ASI05 / ASI06) and
  **OWASP LLM04** (Data & Model Poisoning), keeping the existing
  LLM01/02/03/05/06/10 surface and the module's delegation legend, spec-stage
  proactive-control, and established-helper-bypass sections intact. As the
  ride-along, the `architect` GenAI/agentic lens (`lens-genai-agentic.md`, both
  skill copies) drops its now-stale "these boundaries reach beyond the module's
  current checks" caveat — they route to a named `llm-agent` check like every
  other security-boundary concern.
- **Agentic well-architected overlay, applied at design time (architect
  0.7.1 → 0.8.0; ADR-0032 / RFC-0042).** Designing an agentic system — one
  that uses tools, takes autonomous action, or runs an agent loop — now gets
  the GenAI/agentic well-architected overlay **by construction**, not only when
  a reviewer later runs well-architected mode. `architect-design`'s Stage 0
  gains a **workload-class** routing axis alongside its provider axis: an
  agentic concept loads the shared `lens-genai-agentic.md` overlay (and, on a
  named cloud, the provider pillars too — the axes are orthogonal). The shared
  lens is reorganised into a **progressive, capability-tiered** taxonomy —
  Tier A (the LLM is on the path) → Tier B (the system acts) → Tier C (the
  agent persists or collaborates) — so a plain RAG/chat design applies only the
  baseline tier while a multi-agent system with spend authority applies all
  three. Tier B makes the trust triad first-class — **human oversight,
  intent verification, and auditable action trails** — alongside tool-use
  authorization, tool/MCP source provenance, output handling, execution
  isolation, and reliability under non-determinism; Tier C adds memory & context
  integrity, sub-agent provenance, and inter-agent identity/privilege
  propagation. Graduated autonomy is framed as engineering judgment bounded by
  irreversibility and blast radius, never a standards mandate. Design time and
  review time consume **one shared lens file**, so the two never diverge.
  Security-boundary concerns name the boundary at design altitude and route
  control-level verification to `security-reviewer` / `security-checklists`
  (`llm-agent`). Prose only — no new reviewer, skill, or tooling ships.
- **`operational-safety` reference library for infra/destructive work (core
  0.4.12 → 0.4.13; RFC-0041 P3 / ADR-0031).** Infrastructure and destructive
  operational work now gets a first-class operational-safety depth library — a
  new `operational-safety` skill of six failure-mode-keyed prose modules
  (`state-and-idempotency`, `blast-radius`, `environment-isolation`,
  `cost-and-teardown`, `drift-and-rollback`, `observability-and-smoke`),
  structurally identical to `security-checklists`. When the work-loop detects
  infra/destructive work, the orchestrator loads only the matching modules
  (1–N, never all six) and inlines them into the **existing `quality-engineer`**
  reviewer's brief — so idempotency, blast radius, environment isolation,
  cost/teardown, drift/rollback, and observability/smoke get reviewer depth
  with **no fourth reviewer** (ADR-0023). The split against `security-checklists`
  is clean: security config → `security-checklists` (`security-reviewer`);
  reliability/ops config → `operational-safety` (`quality-engineer`).
  `security-checklists`' `config-misconfig` also gains a URL-free, version-free
  deferred-authority pointer (CIS Benchmarks + the per-provider well-architected
  security guidance) noting the real per-provider depth lives in the
  self-updating scanner. Prose only — no executable code ships.
- **One consolidated, namespaced pack-output layout file — `agentbundle-layout.toml`
  (RFC-0040 / ADR-0030).** An adopter who wants to control where a pack's durable
  output lands now edits **one** namespaced file instead of a per-pack config.
  `agentbundle-layout.toml` carries one `[<pack>]` table per output-producing pack
  (`research`, `architect`, `product-engineering`), each with a single `parent`
  **base** under which the skill creates a topic-named folder per unit of work. Two
  locations resolve with clear precedence — a checked-in `./agentbundle-layout.toml`
  overrides a personal `~/.agentbundle/agentbundle-layout.toml`, per table. The file
  is **adopter-owned and never shipped**: it comes into being by hand, or an
  `agentbundle install` step **appends** a pack's default section to one that already
  exists (never creating it, never overwriting a section you wrote). Reading stays
  **prompt-only** (Charter Principle 3 — no engine, index, daemon, or watcher); each
  consumer confines the resolved path (realpath-resolve, reject `..`, surface the
  absolute path before the first write) and treats a repo-sourced out-of-tree
  `parent` as an Ask-first, untrusted-origin case. Each consuming pack ships a
  `references/agentbundle-layout.md` schema doc and a scope-keyed `[pack.layout]`
  manifest default; `pack.toml` gains the optional `[pack.layout]` table (adapter
  contract → v0.16). `architect` (0.6.1 → 0.7.0) and `product-engineering`
  (0.4.2 → 0.5.0) become consumers; `research` (0.4.0 → 0.5.0) migrates from the
  undistributed `research-layout.toml` by a **clean rename, no alias**.
- **Infra-aware `work-loop` — the loop can now drive an infrastructure inner
  loop end-to-end (`core` pack, bumped to `0.4.12`; RFC-0041 / ADR-0031).** The
  loop's verification modes previously assumed the verification mechanism
  already existed and assumed a fast, local, stateless, single-hop gate — so a
  cloud deploy stalled the agent and the human became a relay, pasting deploy
  errors back into the session by hand. Four doctrine additions close that gap,
  all prose (no executable tooling, no new reviewer, no new risk trigger): (P1)
  a **generalized verification-mechanism preflight** — picking a verification
  mode now obligates confirming its mechanism exists, and if not, building it is
  *task zero*; this is agnostic (a missing test runner or build command, not
  just an infra smoke check) and **universal across light and full mode**, with
  the infra mechanism enumerated as a multi-artifact set (verify-status +
  teardown + test-data/mock-user seeding + a provider-appropriate
  policy-as-code/CSPM scanner). (P2) a fourth **infra/deploy verification
  flavor** whose contract is a layered GATES sequence (static preflight →
  plan/preview → idempotent convergent apply → active end-to-end smoke →
  rollback), cross-linked to the plan's `## Rollout` section. (P4) an
  **agent-drives-verification** doctrine — the agent runs the deploy and reads
  real environment output itself, with the human-as-relay named as the
  anti-pattern and Claude Code background tasks / `asyncRewake` / `PreToolUse`
  as accelerant only. (P5) **mandatory infra security** — infra-flavored work
  non-skippably runs `security-reviewer` at both spec stage and on the diff,
  force-loading the infra-relevant `security-checklists` modules, paired with
  the P1 policy-as-code/CSPM scanner for per-provider depth.
- **Research project mode — a four-skill lifecycle for sustained investigations
  (`research` pack, bumped to `0.4.0`).** Alongside the existing depth axis
  (`/research` quick/standard/applied/deep), the pack gains a *lifecycle* axis
  for multi-week investigations that accumulate a corpus:
  `research-project-start` scaffolds a three-layer project folder (raw
  `sources/` → a `synthesis-matrix.md` + `memos.md` **digest** middle layer the
  pack previously lacked → a typed synthesis); `research-project-digest` clusters
  sources into emergent, constructed matrix columns; `research-project-synthesize`
  emits the typed verdict **and** a single-file, self-contained
  `<topic-slug>-brief.md` that governance can lift whole into an RFC; and
  `research-project-check` is a passive saturation stop-signal that reads the
  matrix by eye and recommends — it never advances the lifecycle. Projects live
  in scratch / out-of-repo by default (configurable via the `[research]` table
  of an adopter-created `agentbundle-layout.toml`); the corpus is never committed
  to the repo, only the distilled brief. Prompt-only by construction (no engine, index, or counter);
  the seven existing skills are reused as phase operations. RFCs may now carry an
  optional `docs/rfc/NNNN-notes/` companion folder for promoted research.
- **Pack activation evals (Tier A) — `tools/run-pack-evals.py` + `[pack.evals]`
  (RFC-0037 / ADR-0028).** A catalogue maintainer can now measure, repeatably
  and empirically, whether each covered skill *activates* on the prompts it
  should and stays quiet on the near-misses it shouldn't. Each covered skill
  ships `evals/eval_queries.json` (a flat `[{query, should_trigger}]` array);
  a pack's `pack.toml` `[pack.evals].skills` lists the covered skills; the
  runner projects the pack in isolation, runs each query through the headless
  `claude` detector, computes a `trigger_rate` over N runs, grades against a
  0.5 threshold, and writes a gitignored, iteration-numbered eval-workspace.
  It runs report-only in a scheduled `pack-evals.yml` workflow — never on the
  PR critical path — and the first cut covers the `core` and `converters`
  packs. `lint-skill-spec.py` now accepts and validates `eval_queries.json`
  and enforces `[pack.evals].skills` coverage. A second, **in-harness** mode
  (`run-pack-evals.py --mode in-harness`, RFC-0037 § Errata E2) extends the
  reach to **Kiro IDE** and interactive Claude Code where there is no `claude`
  CLI: the host agent dispatches a read-only sub-context per query and reports
  activation — a lower-fidelity (reported, not observed) proxy, labelled as such
  in the summary so it is never mistaken for the headless baseline. A
  **lightweight behavior/output check** (`--check behavior`, RFC-0037 § Errata
  E3) goes further where it's safe: the agent runs the skill in a confined
  per-eval working dir and the runner re-derives deterministic post-conditions
  (an `evals/evals.json` `expect` block — produced files, output substrings)
  plus attested assertions (`tier: B-lite`). And a report-only **LLM-judge**
  (`--mode judge`, RFC-0037 § Errata E4) grades the *quality* layer against the
  eval rubric, behind a **config-driven, multi-adapter** backend seam: built-in
  `claude-code` (same model) + `codex` (independent model/IDE), and adopters add
  their own — e.g. a `kiro-cli` headless judge — and pick the model purely by a
  `--judge-config` entry, no code change. The judge is judgment-only and
  fails closed on an unparseable verdict. The **full** Tier-B grading (pass-rate
  deltas, with/without-skill, train/validation, the human-feedback loop) stays a
  future RFC.
- **Per-prompt work-loop activation hook (`core` pack).** A new
  `work-loop-check` hook nudges the agent, on every prompt, to load the
  work-loop skill for non-trivial work — closing a gap where the loop was
  not reliably activated. It ships as a matched pair so it reaches both
  surfaces: a `UserPromptSubmit` hook-wiring + hook body for Claude Code
  (and Copilot / Cursor / Gemini / Codex), and a standalone `promptSubmit`
  `askAgent` `.kiro.hook` for Kiro IDE, which reads only `.kiro/hooks/`
  files and ignores hook-wiring. (`agentbundle validate core`'s info line
  now lists both core hook-wirings as not projecting to the Kiro CLI
  adapter — `session-start.toml` and `work-loop-check.toml` — since neither
  declares `attach-to-agent`; this is informational, not a refusal.)
- **Markdown → Office publishing skills (`converters` pack, RFC-0036).** Three new
  skills publish a Markdown artifact back out as a distribution-ready, on-brand
  Office file by **filling a user-provided template** at its existing fill-points —
  `markdown-to-docx` (Word, via `docxtpl`), `markdown-to-pptx` (PowerPoint, via
  `python-pptx`), and `markdown-to-xlsx` (Excel, via `openpyxl`). A designer's
  cover page, slide master, logo, and named cell regions survive because the skill
  fills the template rather than converting Markdown into a fresh document. Each
  detects a template, confirms or elicits one, and proceeds unbranded only on the
  user's explicit opt-out — it never invents a brand and never auto-installs its
  Tier-1 render library. This completes the pack's Office round-trip, which until
  now ran only inward (Office → Markdown). The `converters` pack is bumped to
  `0.2.0`. See
  [Publish Markdown as a branded Office file](../guides/converters/how-to/publish-markdown-to-office.md).
- **SSO web-session cookie auth for `jira` reads + `confluence-crawler` (atlassian
  pack, RFC-0035).** On an Atlassian Data Center instance behind corporate SSO
  where API tokens are blocked, both skills can now authenticate by a captured web
  session instead of a token: pre-bake `references/sso-config.toml`
  (`auth_default = "sso-cookie"`), run `python scripts/setup_sso.py` once to
  register the session, and reads work with no token. The session is resolved
  through the `credbroker` SSO resolver (new `load_sso_cookies`, credbroker 0.2.0)
  and the captured jar is confined to the declared `cookie_domains`; no
  `Authorization` header is sent and redirects are not followed (the session
  cookie never crosses to another host). Both skills keep a `creds` (token)
  fallback — token users with no SSO config see no change. Data Center reads only;
  writes are refused pending XSRF design; Cloud is unchanged. See
  [Authenticate Jira / Confluence with an SSO web session](../guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md).
- **`jira-brief-intake` skill (atlassian pack).** Turns a Jira epic — or a
  board / sprint / JQL selection of issues — into shippable specs for teams who
  plan kanban-style in Jira. It pulls the epic and its children via the `jira`
  skill, maps them onto a Shape B product brief (epic → Outcome, child issues →
  `US-n` user stories tagged with their Jira key, epic key → `Epic:` provenance
  pointer) at `docs/product/briefs/<slug>.md`, then hands off to the
  `receive-brief` skill to elicit any missing fields, decompose, and build. It
  is read-only against Jira and degrades gracefully — when `receive-brief` is
  not installed it inlines a decompose/execute instruction for the agent to act
  on directly. Pure choreography, mirroring `jira-defect-flow`.

### Changed

- **`architect-design` writes each design effort into its own per-effort folder**
  (`<parent>/<topic-slug>/`) instead of scanning for a loose-file home every run
  (RFC-0040). The previous `docs/design/`→`design/`→`architecture/`→`docs/`
  scan-then-elicit becomes the **default** when no `[architect]` layout section
  resolves. Additive — a folder around what was a file — and documented in the
  pack's `references/agentbundle-layout.md`.
- **`new-rfc` now surfaces the optional `NNNN-notes/` companion
  (`governance-extras` pack, bumped to `0.3.0`).** The skill and its RFC
  template point authors at the optional sibling `docs/rfc/NNNN-notes/` folder
  for promoted research — a distilled brief and supporting material summarized
  into *Evidence & prior art* and linked, rather than pasted into the RFC body.
  Pairs with the companion convention added to `docs/CONVENTIONS.md` § 3, and is
  the landing place for a `research`-pack project's `<topic-slug>-brief.md`.
- **The `work-loop` skill's Context hygiene section now covers output, not just
  input (`core` pack, bumped to `0.4.11`).** A new *Emit less, too* note adds two
  zero-cost habits to the existing window-management guidance: don't restate code,
  files, diffs, or tool output already in the conversation — reference them by path
  and line — and continue with the substance instead of narrating a tool call's
  success. It is framed as waste reduction, not terseness for its own sake: the
  rationale, edge cases, and findings prose that review and the human actually read
  stay in.
- **Research outputs are now named by topic and type (`research` pack, bumped
  to `0.3.0`).** Episodic `/research` artifacts are written as
  `<topic-slug>-<type>.md` (e.g. `oauth-pkce-survey.md`) instead of the generic
  `research.md`, so two investigations in one working directory no longer
  overwrite each other and a file's name says what it is — `survey`,
  `fact-check`, `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`, or
  `counterpoints`. The scoping skills (`source-map`, `build-outline`,
  `identify-perspectives`, `decision-archaeology`) gain the same
  `<topic-slug>-` prefix. Quick mode is unchanged (inline, no file). The former
  name `research.md` is retained as a recognised legacy alias for one release.
- **The `new-adr` skill and ADR template now follow MADR conventions
  (`governance-extras` pack, bumped to `0.2.0`).** The ADR template gains a
  `Rejected` status (a declined proposal is now kept as a record, not deleted)
  and two optional sections — **Decision drivers** (the criteria a choice was
  judged against) and **Confirmation** (how conformance with the decision will
  be verified). Frontmatter adopts MADR's decision-roles split: the `Deciders`
  field is renamed to **`Decision-makers`** and gains optional **`Consulted`**
  and **`Informed`** lines. The H1 title now names the problem *and* the chosen
  solution together (the `ADR-NNNN` ordinal prefix is unchanged), and the skill
  now carries the full post-acceptance lifecycle discipline inline (bidirectional
  supersession, `Deprecated`-vs-`Superseded`, backfilling). The decision stays
  first in the body (answer-first; no options-first reordering). **Breaking for
  the template only:** new ADRs use `Decision-makers`; existing ADRs keep
  `Deciders` and are not rewritten (ADRs are immutable).

- **`credential-setup` now gives a clear install hint instead of a traceback
  when `credbroker` is missing.** Running the setup script without the
  `credbroker` resolver installed prints a single line telling you how to
  install it from your repository checkout and exits cleanly (code `3`),
  rather than dumping a `ModuleNotFoundError` stack trace. A different import
  failure (a broken `credbroker` submodule, say) still surfaces unchanged.

### Fixed

- **Kiro custom agents now reach the bundle's skills — CLI and IDE (contract
  v0.15).** On both Kiro targets, only the **default** agent auto-discovers
  skills; a **custom** agent (`kiro --agent <name>`, including every headless
  `--no-interactive` run, or an IDE subagent) loaded **zero** skills unless it
  declared them in its `resources` field. Packs projected agents without that
  field, so agent-driven runs saw none of the catalogue's skills. Both the
  `kiro-cli` and `kiro-ide` adapters now inject a skill-resources glob
  (`skill://.kiro/skills/**/SKILL.md` and the `~/.kiro/skills/**/SKILL.md`
  user-scope twin) into every projected agent — CLI into the agent JSON, IDE
  into the `.md` YAML frontmatter (quoted, YAML-safe). An agent that declares
  its own `resources` keeps it; the deprecated `kiro` alias inherits the IDE
  behavior. Default-agent runs were already fine and are unaffected.
  (RFC-0022 erratum E4; kiro #6887/#6888/#4993.)
- **`agentbundle install --adapter kiro` now behaves exactly like `kiro-ide`.**
  The deprecated `kiro` alias (RFC-0022) was honored by `make build` but not by
  the install path, which still emitted `.json` agents and merged hook-wiring —
  the legacy behavior. Installing, upgrading, or uninstalling via `kiro` now
  projects `.md` agents and **drops** hook-wiring (the IDE shape), consistent
  with the build registry. The legacy `.json`-agents + hook-wiring-merge
  behavior is unchanged — it lives under the `kiro-cli` adapter. The dropped-
  primitives warning for `kiro` now names what is actually dropped (hook-wiring
  and commands). `state.adapter` still records the name you chose (`kiro` stays
  `kiro`), so the alias remains a working, named adapter. The `attach-to-agent`
  validation and path-confinement rails now also fire for `kiro-cli`, so a
  malformed or path-traversing wiring declaration is refused for the adapter
  that performs the merge.

### Added

- **Pack profiles — install a curated set of packs in one command (RFC-0034).**
  `agentbundle install --profile <name> <catalogue>` reads a first-party
  `profiles/<name>.toml` from the catalogue and installs its packs at the
  profile's single declared scope, in deps-first order, on one pinned adapter,
  with all preconditions checked before any write. `agentbundle list-profiles
  <catalogue>` lists the available profiles (id, scope, description). Two
  profiles ship: `solution-architect` (user scope → `architect` + `research` +
  `contracts`) and `full-ceremony` (repo scope → `core` + `governance-extras`
  + `user-guide-diataxis` + `monorepo-extras`). `--profile` is mutually
  exclusive with `--pack`, and `--scope` is rejected with it (a profile
  declares its own scope). Already-installed packs are skipped, not reinstalled;
  per-pack state rows record `install_route = "profile"`. No new state schema,
  no adapter-contract bump, no new install route — distribution hygiene over
  the existing single-pack install path.

- **New `inception` profile.** A user-scope toolkit for taking an idea from
  zero to a buildable repo — `research` + `product-engineering` + `architect`,
  installed once and carried across ventures. Install with `agentbundle install
  --profile inception <catalogue>`, then use as much of it as the venture
  warrants: architecture alone for a learning project, plus product shaping for
  a side project, plus research when sizing a market. The build loop itself
  stays the repo-scope `core` pack, installed into the new repo at bootstrap.

- **`design` joins the soft `categories` vocabulary.** `agentbundle validate`
  now recognizes `design` as a known pack category, so the `design-craft` pack
  (and any future design pack) declares it without a soft warning. The
  vocabulary is extensible by design (RFC-0031 D8) — this grows it by one slug,
  no RFC required, no behavior change for any other pack.

- **New `design-craft` pack for interaction/visual designers (design-craft
  0.1.0).** An opt-in, user-scope pack of four pure-markdown skills —
  `aesthetic-direction` (turn a vague vibe into named, ranked goals),
  `design-system-foundations` (derive a token/scale taxonomy from intent),
  `layout-and-information-architecture` (hierarchy, reading flow, wayfinding as
  concepts), and `design-critique` (severity-rated heuristic evaluation) —
  plus a shared `quality-floor` checklist (handle all states, accessibility
  floor, "motion communicates state, honor reduced-motion"). Designers author
  the upstream **design intent** the build consumes, the design-side twin of
  `product-engineering`'s product-intent seam. Every skill is strictly
  framework-agnostic: it points to the recognized standards (WCAG, the W3C
  Design Tokens interchange shape) and ships the method to *derive* values,
  never a stack or a values table — enforced by a pack-scoped agnosticism lint
  wired into CI. No hooks, no engine, no in-pack validator, no reviewer
  subagent. Installs across all seven adapters; user-scope by default.

- **`decompose-intent` records the decomposition decision (product-engineering
  0.4.1).** When a cut drops or replaces a branch — most often after an upward
  `de-risk-intent` kill bubbles up — there was no instruction to record *why* on
  the parent, so a parent intent read as if its tree were always this shape and a
  later reader re-litigated branches already ruled out. A new procedure step (and
  an optional "Decomposition decisions" log in the intent template) asks for the
  grouping rationale plus any dropped/replaced branch, pointing to the killed
  child's verdict. This mirrors the de-risk trail, which already records why a bet
  was tested the way it was; a line or two per decision, omit if the cut was
  obvious. No new fields are required and the artifact stays a template, not a
  schema. (Pure-markdown; dependency-contract paths between siblings and
  confidence in a bet were audited and already covered by the business-unit
  provider/consumer projection and the survive/kill verdict respectively — no
  change there.)

- **`architect` ships a forked-context `design-reviewer` subagent (architect
  0.6.0, RFC-0032).** A read-only sibling of the `architect-review` skill: the
  same genre-routed verdict critique and well-architected risk register, with
  the same severity and mechanical/judgment tags — but run in an isolated
  context that hasn't seen the authoring, so it can't mark its own homework. It
  is the *fresh-context (preferred)* rung of `architect-design`'s convergence
  loop (which previously had only an in-thread skill and a weaker cold-re-read
  floor); its tools are `Read, Grep, Glob`, so it flags and never rewrites the
  design. The `architect-review` skill is unchanged and the two coexist. The
  convergence loop stays a soft dependency — it degrades gracefully when the
  subagent isn't installed. ADR-0023 records that the charter's "three reviewers
  is the ceiling" scopes the core code-review lenses, not opt-in design-side
  review.

- **`work-loop` makes "run it as a real user" first-class for non-UI tools (core 0.4.9).**
  The manual-QA verification mode was framed almost entirely around UI rendering
  and UX flows; it now explicitly covers any artifact a user invokes — a CLI, a
  library's public API, an agent or skill, a service endpoint. The doctrine:
  when a change ships something a user invokes, verification includes exercising
  the real built artifact end-to-end through its documented happy path and
  recording what you observed (real stdout/exit code, returned value, file
  written, on-screen result), not internal state or a unit gate standing in for
  the real invocation. Framed harness-agnostic like the EXECUTE simplify pass —
  done by hand on any agent, with Claude Code's native `/verify` and `/run` as
  an optional accelerant. The DECIDE end-of-session checklist gains a line that
  refuses "done" until that end-to-end exercise has happened. Existing
  UI-specific guidance is preserved as the UI instantiation of the general rule.

- **`architect-diagram` learns deliberate visual encoding (architect 0.5.3).**
  A new `references/visual-encoding.md` turns scattered correctness rules into
  one design heuristic: when a diagram distinguishes more than one category of
  thing or relationship, map each visual channel (shape, grouping, position,
  edge style, marker) to meaning *by the data type it carries*, rather than
  decorating arbitrarily. It names which channels are robust across enterprise
  wiki renderers versus fragile (colour, opacity) — colour is reinforcement,
  never the sole carrier — and notes honestly that Mermaid can't size nodes, so
  magnitude goes in a label. Mermaid-only; no rendering-library code. The draft
  step in the skill now loads it when a diagram carries more than one
  dimension.

- **`quality-engineer` catches two more test/edge-case shapes (core 0.4.8).**
  The tautological-tests finding now also flags a test that asserts on the
  mock's own configured return value (it can never fail, so it pins nothing),
  and the edge-case enumeration adds `permission-denied` and
  `resource-exhausted` to the cases the reviewer checks for.

- **The `architect-design` NFR lens gains a performance-budget optimization
  discipline (architect 0.5.2).** The "Performance and scale" checklist now
  asks for a performance budget committed up front (a latency, throughput, or
  resource target stated as a testable claim), and adds an "earn each
  optimization against the budget" prompt: measure before optimizing (no
  optimizing an unmeasured hotspot), spend effort on the hotspot where most of
  the cost sits, and weigh each optimization's ongoing complexity cost against
  the gain it actually buys. Framework- and stack-agnostic — no profiler or
  tool names. The optimization discipline was previously absent; budget-setting
  itself stays cross-linked to the existing quality-attribute-scenarios
  guidance rather than restated.

- **The `product-engineering` pack gains a content layer — `voice-and-microcopy`
  (product-engineering 0.4.0).** A fifth pure-markdown skill that turns shaped
  product intent into the **words a user reads** in the UI — the angle the pack's
  intent-shaping habits (`frame-intent`, `de-risk-intent`, `decompose-intent`)
  deliberately left open. The adopter characterizes their product's **voice**
  along a few axes (humor / formality / respect / enthusiasm) and records it in a
  travelling voice-chart template, writes the recurring UI states — **error,
  empty, button, label** — from blame-free, actionable formulas (each with a
  before/after), and runs a **content checklist** before copy ships. Voice is
  constant, tone flexes by context (calm in errors, warm in success). Fully
  framework-agnostic and habits-shaped — no engine, no schema, `SKILL.md` under
  100 lines with depth in `references/`. Distinct from the
  `house-voice-writing-craft` clear-prose rules, which shape *documentation*
  prose, not product UI copy.
- **The `bug-fix` skill gains two debugging-discipline moves (core 0.4.6).**
  A new "list candidate causes, then falsify each" step sits between
  reproduction and the root-cause assertion — name 2-3 rival causes and rule
  each in or out with Expected / Actual / Verdict, so you don't fixate on the
  first plausible cause. And a "Why wasn't it caught?" question joins the
  root-cause set, so the regression test closes a *named* coverage gap rather
  than only pinning the observed input. Both are language- and
  framework-agnostic. The renumbering shifts `bug-fix`'s tracker-loopback
  step from 8 to 9; the atlassian `jira-defect-flow` skill's references to it
  are updated to match (atlassian 0.1.4).

- **Spec and guide authoring skills teach two doc-writing disciplines: retcon
  writing and context poisoning (core 0.4.7, user-guide-diataxis 0.1.4).**
  *Retcon writing* — `new-spec` and `new-guide` now instruct authors to write
  spec/guide bodies in the present tense, as if the feature already exists and
  always worked this way: no "will be implemented", no "previously X, now Y", no
  deprecation timelines, no version-stamped history in the body (decision history
  stays in ADRs and the changelog). The rule lands as a failure-mode bullet in
  `new-spec` step 4, a guide-voice anti-pattern in `new-guide` step 4, a reminder
  in the `new-spec` `spec.md` template, and a `clear-prose.md` checklist item;
  `plan.md` is exempt, since it keeps its own changelog. *Context poisoning* —
  `new-spec` now names the failure mode its single-source-of-truth / drift-is-a-bug
  discipline prevents (an agent loading a stale, duplicated, or self-contradicting
  doc and deciding wrong from it) in one canonical place, tying the
  one-canonical-home rule and the retcon body together as the two halves of the
  defense.

- **`work-loop` gains a "Scale with a tool, not turns" technique for large,
  repetitive tasks (core 0.4.5).** When a task spans many similar items —
  applying one change across N files, transforming a large set, auditing every
  module — the skill now points you at writing a small enumeration script backed
  by a resumable tracking file (`progress.jsonl` or a checklist with per-item
  `pending`/`done`/`failed` state), so an idempotent re-run skips finished items
  and the loop reliably reaches 100% completion instead of stalling when context
  turns over. A short headline lands in the EXECUTE phase; the full playbook —
  tracking-file schema, idempotency, when to shell out to the agent per item, and
  keep-vs-delete the tool — is a new on-demand reference,
  `references/scale-with-a-tool.md`.

- **The research pack learns to preserve irreducible ambiguity instead of
  always collapsing to one rated answer (research 0.2.0).** Four skills gain a
  first-class way to hold a question open when the honest output is not a single
  verdict: `/identify-perspectives` adds a **tension map** recording, per
  irreducible disagreement, the conditions under which each camp holds and what
  a forced resolution would destroy; `/devils-advocate` adds a **do-not-resolve
  verdict** for productive tensions where both sides are well-evidenced under
  different conditions, distinct from its confidence-downgrade; `/research` adds
  a first-class **known-unknowns / unknowables** gap section, distinct from
  rating a weak finding `[uncertain]`; and `/decision-archaeology` adds a
  **revival check** that flags a rejected alternative whose original rejection
  rationale no longer holds because a constraint changed. Each is additive — no
  existing schema field or downstream contract changes.

- **The rest of the catalogue-internal references are swept from shipped
  content (core 0.4.4, figma 0.1.3).** Following the first pass, the remaining
  `make build-*` build-target mentions, an internal RFC citation, and the "this
  catalogue" identity asides are removed from the work-loop and receive-brief
  skill scripts, the session-start hook, the `pre-pr` hook, and the
  adapt-to-project reference; figma's exit-code test drops a dangling internal-RFC
  comment. Comment, docstring, and prose only — no behavior change.
  (`credential-brokers`, which is frozen, is left for a separate pass.)

- **Shipped pack content sheds catalogue-internal references (core 0.4.3,
  atlassian 0.1.3).** The `conventions-check` command no longer instructs
  running this repo's own `tools/lint-*` scripts — which never install into an
  adopter tree — and is reframed as checks you (or your own linters) perform
  directly. The `jira` skill's error-handling guidance drops a `make
  build-self` remediation hint in favour of "reinstall the pack", and four
  shipped atlassian test scripts drop dangling internal-RFC comment citations.

- **`make build-self` no longer litters the tree with by-quadrant guide
  scaffolds.** Self-host projection skips `guides/**`: guides are
  repo-owned and reach adopters through install-time seed delivery, so a repo
  that organizes its guides by pack no longer gets untracked
  `guides/{tutorials,how-to,reference,explanation}/README.md` re-created
  on every build.

- **`new-guide` now coaches prose, not just structure (user-guide-diataxis
  0.1.3).** The skill ships a `clear-prose` checklist. It names the tells that
  make docs read machine-made (hedges, uniform sentence rhythm, em-dash
  overuse, throat-clearing openers, inflated verbs) and the habits that keep
  them human (one claim per sentence, concrete over abstract, strong verbs,
  omit needless words). The voice section points to it. An optional copyedit
  pass hands the draft to a read-only subagent when one is available.

- **A guide home for every pack, and real guides for the packs that lacked
  them (ADR-0020).** `guides/` is reorganized from flat Diátaxis quadrants
  to a per-pack hierarchy — `guides/<pack>/{tutorials,how-to,reference,explanation}/`
  for each pack, `guides/_shared/` for cross-cutting topics (install routes,
  the adapter support matrix, the catalogue model, authoring a skill). All 12
  packs now have a guide home reachable from `[pack.links].documentation` and a
  "go deeper →" link from the pack README, and the README catalogue points each
  pack at its guides. The seven previously-undocumented packs (`atlassian`,
  `contracts`, `converters`, `figma`, `governance-extras`, `monorepo-extras`,
  `user-guide-diataxis`) gained full Diátaxis guides; `architect` gained diagram
  and review how-tos; flow-heavy guides carry ASCII diagrams; and `core`'s
  explanation now leads with *why loop engineering*. The adopter-facing
  `user-guide-diataxis` seed scaffold stays organized by quadrant; the
  `new-guide` skill is layout-aware (user-guide-diataxis 0.1.2). Every pack's
  version is bumped for the new `documentation` link.

- **`architect-design` now consults the enterprise's own knowledge when the
  environment exposes a retrieval surface (architect pack 0.3.0).** A new
  progressive-disclosure reference (`knowledge-surfaces.md`) carries an 8-area
  MECE knowledge taxonomy — business domain, current landscape, interfaces,
  operational reality, constraints & standards, patterns, decisions, in-flight —
  plus a **harness-agnostic detection** mechanism that discovers a retrieval
  surface (an MCP knowledge tool, an internal CLI, an in-repo doc set) from the
  session itself, hardcoding no tool name. A single conditional procedure step
  loads the reference **only when a surface is detected**, and otherwise
  **degrades gracefully** — asks for the missing context, lowers confidence, and
  never fabricates landscape/standards/in-flight facts — reusing the existing
  compose-with-`research` framing. No knowledge server or RAG engine ships (out
  of charter); no registry, shared config, or cross-pack dependency.
  The `architect-review`, `architect-diagram`, and `product-engineering`
  siblings have all since shipped (see below) — the line is complete.

- **`architect-review` now checks that a design was grounded in the enterprise's
  own knowledge (architect pack 0.4.0).** The review-side counterpart of the
  `architect-design` awareness above: a duplicated, **verification-lens**
  `knowledge-surfaces.md` reuses the same 8-area MECE taxonomy as a checklist —
  *is this area's claim grounded?* — and one conditional procedure step flags any
  landscape / standards / in-flight / interface claim asserted as fact without
  grounding (no cited surface and no "unverified — confirm" marker), plus any
  available knowledge surface the design ignored. It **does not redesign** and
  **does not consult surfaces to author a better answer** — if an internal
  surface is reachable it may spot-check the claims (naming what it checked
  against, or "none"); if not, it flags them for the author to confirm rather
  than guessing, and never fabricates a "ground truth" to judge against.
  Harness-agnostic detection (no hardcoded tools, public web excluded); no
  registry, shared config, or cross-pack/cross-skill dependency. The
  `architect-diagram` and `product-engineering` siblings have since shipped (see
  below).

- **`architect-diagram` now consults the enterprise's own knowledge to draw an
  accurate as-is diagram (architect pack 0.5.0).** The third and final
  architect-skill sibling of the awareness above, with a deliberately different
  lens: in **document** and **update** mode only, when the as-is system
  integrates beyond the repo boundary and a retrieval surface is reachable, a
  duplicated **as-is-drawing-lens**
  `knowledge-surfaces.md` extends "read the repo" to "read the landscape" — so the
  boxes, arrows, and edge labels beyond the repo boundary are grounded from the
  **descriptive current-system facets** (current landscape, interfaces,
  operational reality — areas 2/3/4) instead of guessed. It reuses the same 8-area
  MECE canonical core (kept byte-identical across all three copies; only the
  trigger column, lens paragraph, and detection/degrade framing change) and one
  conditional procedure step. **Mode-scoped:** it does **not** fire in design mode
  (the user's hypothetical — fabrication is allowed-but-flagged) or review mode
  (routes to `architect-review`). Harness-agnostic detection (no hardcoded tools,
  public web excluded); three honesty rails recast for drawing — name what you
  drew from, leave an ungroundable node `<unnamed>` or ask rather than guess, flag
  a surface-derived edge the repo contradicts rather than drawing over it —
  strengthening the skill's standing never-fabricate-names discipline. No
  registry, shared config, or cross-pack/cross-skill dependency. `architect-design`
  and `architect-review` are unchanged. The new copy is **registered in
  `tools/lint-knowledge-surface-parity.py`** (the drift guard shipped alongside
  the `product-engineering` sibling, extended here + its self-test) so the
  canonical core is mechanically guarded. This **completes the
  knowledge-surface line** — all three architect skills plus the
  `product-engineering` sibling now ship it.

- **The `product-engineering` pack gains its business-unit cross-component layer
  (pack 0.2.0).** A product org whose work fans out across **many component
  repos** can now stand up a **value-stream meta-repo** — a coordinating repo with
  no app code — via a new pure-markdown skill, **`align-value-stream`**. It holds
  the cross-cutting artifacts a polyrepo has nowhere else to put: a **federated
  Backstage catalog** (Domain→System→Component→API, referencing each repo's own
  `catalog-info.yaml`, never re-authored), the **shared-contract authority**
  (referenced by `contract@version` with a read-only courier snapshot, never
  forked), the **C4/bounded-context architecture**, and a **cross-component
  delivery rollup**. At business-unit scale `decompose-intent` now **slices a
  feature intent per component** into one `core` brief per repo, each carrying an
  optional **`parent-intent:`** provenance pointer (the one additive, never-
  interpreted `core` brief field, distinct from `Epic:`), a versioned contract
  reference, and a `providesApi`/`consumesApi` role; each brief crosses into its
  component repo where `receive-brief` → `new-spec` → `work-loop` take over, and
  the meta-repo rolls up "delivered across **all** components?" The rollup is a
  **markdown snapshot** (absent-source rows show `unknown / not-yet-catalogued`,
  never silently delivered) — **no runtime hub, no live API, no validator, no new
  subagent**. The hard limits are stated honestly: **no atomic cross-repo commit,
  no shared release train, snapshot-not-live**. Habits, not infrastructure
  (RFC-0030 phase 2, ADR-0022).

- **`frame-intent` now consults the enterprise's own knowledge through a
  problem-framing lens when the environment exposes a retrieval surface
  (product-engineering pack 0.3.0).** The product-engineering counterpart of the
  `architect-design` awareness above — same mechanism, different lens. A new
  progressive-disclosure reference (`frame-intent/references/knowledge-surfaces.md`)
  carries a **strict four-area subset** of architect's taxonomy — business domain
  & meaning and in-flight & roadmap (both primary), current landscape
  (brownfield-only), and operational reality (light) — and **deliberately omits**
  the four solution-design areas (interfaces, standards, patterns, decisions) so
  framing stays in problem space. The same **harness-agnostic detection** (no
  hardcoded tool name) and three honesty rails apply; a single conditional step
  loads the reference **only when a surface is detected** and otherwise
  **degrades gracefully** — asks for the missing domain/in-flight context, lowers
  confidence into the intent's `Assumptions`, and never fabricates. The
  current-landscape area wires into `frame-intent`'s existing brownfield maturity
  gate. A shared-canonical-core anchor names the architect reference as canonical
  so the copies don't diverge. The detection audit home ("name what you detected,
  or 'none detected'") is pinned to a fixed slot in the intent template's
  `## Assumptions` and — symmetrically — in `architect-design`'s Stage-0
  `concept.md` (bumping the architect pack `0.4.1 → 0.4.2`). A new stdlib
  `tools/lint-knowledge-surface-parity.py` CI gate guards **every copy** of the
  shared taxonomy core — `architect-design` (canonical), `architect-review`, and
  `frame-intent` — against silent drift. No knowledge server or RAG engine, no
  registry, shared config, or cross-pack dependency.

- **`pack.toml` is now the rich source of truth for pack metadata, projected
  into every catalogue listing (adapter contract → 0.14).** Packs can declare
  `license`, `display_name`, `[[pack.maintainers]]`, `[pack.links]`
  (homepage/repository/documentation/changelog/issues/icon), `categories` and
  `keywords` (each capped at 5), an opaque `[pack.metadata.<tool>]` table, and a
  `readme` pointer — all optional, so packs that omit them build and validate
  exactly as before. The build projects the cleanly-mappable subset (author ←
  first maintainer, `category` ← first category, `displayName`, plus
  license/keywords/homepage/repository) — and each pack's `README.md` — into the
  claude-plugins and APM routes' `plugin.json` / aggregated `marketplace.json`
  entry, so a pack is described richly rather than with a single sentence.
  `categories` is a **soft vocabulary**: an unknown slug warns (exit 0), never
  fails. `agentbundle list-packs` renders a pack's canonical identity as
  `@<catalogue>/<pack>` when `[pack].catalogue` is set (declare-only — no
  resolution change). **All 12 shipped packs** now declare the enriched metadata
  and bump a patch version. (RFC-0031, ADR-0021; the per-pack guide-home
  `documentation` links and the `guides/` per-pack reorg land in a
  follow-on, ADR-0020.) As part of the same sweep, `product-engineering`'s
  intent/rollup templates moved from repo-scaffolding `seeds/` into the owning
  skills' `assets/` (so the pack carries no `seeds/` and stays user-scope).

- **A new opt-in `product-engineering` pack shapes product intent into the specs
  your delivery loop already builds (pack 0.1.0).** Three pure-markdown skills —
  `frame-intent`, `de-risk-intent`, `decompose-intent` — work a recursive,
  level-tagged `intent` (a capability intent and a feature intent are the same
  artifact at different levels; a PRD is a feature intent written as a document).
  Name an outcome and the opportunity behind it, de-risk the riskiest assumption
  against a **predeclared kill condition** under a choosable **prototype-approach**
  (`prototype-led` ↔ `validate-first`), then decompose to a shippable spec — at app
  scale the leaf *is* a `core` brief, so `receive-brief` → `new-spec` → `work-loop`
  take it from there with **no change to `core`**. One global **Scale** axis (app ↔
  business-unit) plus per-intent maturity / reversibility / prototype-approach flags;
  one-way tracker projection (Linear / Jira Align / none); habits, not infrastructure.
  v1 is app/solo + single-component; the business-unit cross-component value-stream
  layer is a later phase (RFC-0030, ADR-0019).

- **The `architect` pack designs *and* reviews cloud architecture to the
  well-architected standard, and the design skill now converges (architect pack
  0.2.0).** `architect-design` shapes a one-page **concept first**, makes the
  design **well-architected by construction** for the chosen provider — AWS /
  Azure / GCP, **primitives providers like Hetzner** (it names the capability
  gaps you must build yourself), or **local-first** (the local→production delta +
  graduation path) — and then runs a **convergence loop**: it obtains a review
  pass, **auto-resolves the mechanical findings** without asking, re-reviews, and
  **surfaces only the judgment calls** (tradeoffs, risk acceptances,
  low-confidence assumptions) to you as decisions. `architect-review` gains a
  **well-architected / lens mode** (security · FinOps · SRE · DR · data ·
  compliance · green concern-lenses, plus ML / **GenAI-agentic** / SaaS /
  serverless workload-class lenses) that emits a risk register with every finding
  tagged **mechanical / judgment** — the signal the design loop consumes. The
  loop is an enhancement when both skills are present and degrades to an embedded
  rubric self-check when it isn't; for genuinely novel domains the design takes a
  **leading-edge path** that composes with the `research` skill when available and
  degrades to flagged-novelty + lowered-confidence when absent. Pure-markdown, no
  subagents, no new pack; the loop is an in-conversation procedure with no script
  or state file. `architect-diagram` gains a `cloud-primitives` diagram vocab for
  parity with its AWS/Azure/GCP references.
- **The `security-reviewer` is stronger, current, and shifts left (core pack 0.4.0).**
  Security review is no longer only a late gate: on security-boundary work the
  `work-loop` now dispatches the reviewer in a **spec-stage secure-design mode**
  at the pre-EXECUTE step, asking whether each control is specified as an
  acceptance criterion *at the right depth* (confinement, not just traversal;
  a scheme/host allowlist, not "validate the URL"; broker-mediated secrets, not
  ad-hoc reads) — collapsing post-implementation round-trips into one design-time
  pass. The awareness stack is current — **OWASP Top 10:2025** (replacing the
  2021 list), ASVS 5.0, API Security Top 10:2023, OWASP LLM Top 10:2025, CWE
  Top 25 — and a **STRIDE + LINDDUN** open pass adds the privacy lens STRIDE
  blind-spots. Depth ships through a new **`security-checklists` skill**: ten
  boundary-keyed modules the orchestrator loads *per boundary the change
  crosses* and inlines into the reviewer's brief, so the lens is deep without
  bloating the prompt and travels to every adapter with **no contract change**.
  Tool-delegation is now language-agnostic (`npm audit` / `pip-audit` /
  `govulncheck` / `cargo audit` / Snyk / Semgrep / CodeQL) and fails honestly
  (`degraded: no scanner`) rather than silently skipping. A new **established-helper
  bypass** meta-check flags code that rolled its own where the repo has a blessed
  helper — customize the list via a light "blessed security tools/helpers" point
  in `AGENTS.md`. Complements, does not replace, the SAST/SCA scanners (ADR-0017).
  See RFC-0029 / ADR-0018.

- **The default quality floor is now higher by doctrine (core pack 0.3.0).**
  Agent output tends to clear a strict external static-analysis gate (a
  SonarQube quality profile, a CI-only coverage threshold) regardless of tech
  stack, without bundling any linter, shipping any threshold, or detecting the
  repo's shape. Three coordinated, stack-agnostic changes: (1) the
  `quality-engineer` reviewer gains four universal code-smell findings —
  bounded complexity (split what's *reducible*, complementing the existing
  comment-the-irreducible finding), nesting depth (idiom-appropriate
  flattening, not a mandated early `return`), duplicated production blocks past
  the rule-of-three (tests stay DAMP), and magic-literals/parameter-bloat
  (judgment-based, threshold-free) — plus a mutation-testing-mindset Test
  Design headline ("a test must be able to fail") as the Goodhart-safe stand-in
  for chasing a coverage number; (2) `work-loop` gains a **simplify pass** in
  EXECUTE/REVIEW that shrinks the diff before review — harness-agnostic
  doctrine, with Claude Code's `/simplify` an optional accelerant, never a
  dependency; and (3) light mode now **retains** the `quality-engineer` pass
  when the adopter declares in their `AGENTS.md` that the repo is judged by a
  strict external gate the local loop can't run (adopter-declared policy, not
  repo detection). Mode *mechanics* begin migrating out of `CONVENTIONS.md`
  into the `work-loop` skill as their single owner.

- **The repo now has a SAST/SCA gate** — `make sast` runs **Bandit** (Python pattern SAST),
  **pip-audit** (dependency/SCA), **Semgrep** (cross-cutting SAST, including custom `mode: taint`
  rules under `tools/semgrep/`), and a **CodeQL** code-scanning workflow (deep interprocedural
  taint — the open-source analogue of Snyk Code). The first three are chained into
  `make build-check` so every PR is scanned by the repo's own single native gate (locally and in
  `build-check.yml` CI); CodeQL runs as its own workflow. Bandit fails on medium-or-higher findings
  (tuning in `bandit.yaml`). The genuine findings surfaced were fixed in the same change: weak SHA-1
  digests marked `usedforsecurity=False`; the arXiv retriever upgraded to HTTPS; the `session-start`
  hook's env-var path overrides sanitized against directory traversal (a fix every adopter inherits);
  and the SSO broker's `test` verb now rejects non-`http(s)` URL schemes. A committed `.snyk` policy
  file is the Snyk-native suppression vehicle for the organisational scan. All four scanners are
  CI-only dev tools (`tools/requirements-sast.txt`) and are **never** added to a shipped package's
  runtime dependencies. See ADR-0017.

- **Gemini CLI is now a full-parity adapter** — `agentbundle install --adapter gemini` (repo or
  user scope) projects every catalogue primitive to Gemini CLI's native `.gemini/*` layout:
  skills → `.gemini/skills/`, subagents → `.gemini/agents/<name>.md` (the `tools:` allowlist is
  **kept** and name-mapped to Gemini's tool ids — `Read`→`read_file`, `Bash`→`run_shell_command`,
  … — and `model` maps tier-preserving to the Gemini 2.5 line), commands →
  `.gemini/commands/<name>.toml`, and hook bodies → `.gemini/hooks/` with the wiring + a managed
  `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge merged into `.gemini/settings.json` so the
  canonical `AGENTS.md` is read. Every pack admits `gemini` at both scopes. Previously Gemini CLI
  got nothing (it doesn't read `AGENTS.md` by default). Contract v0.12 → v0.13 (RFC-0027 /
  ADR-0016). Distribution-only.
- **Cursor can now install the `research` and `architect` packs** — both packs added `cursor`
  to their `allowed-adapters`, so `agentbundle install --pack research --adapter cursor` (and
  `--pack architect`) now projects their skills to `.cursor/skills/` — and, for `research`, the
  two retrieval subagents to `.cursor/agents/` with `readonly: true` — instead of refusing the
  install up front. The Cursor adapter shipped in the previous release, but no pack had opted
  in. (The credentialed packs are covered by the next entry.)
- **Credentialed packs can now install via Cursor and Copilot** — `atlassian`, `contracts`,
  `converters`, `figma`, and `credential-brokers` added `copilot` + `cursor` to their
  `allowed-adapters`, so a Cursor- or Copilot-based adopter can install them (and the SSO/token
  broker lands at `~/.agentbundle/bin/` as before — the broker delivery is adapter-independent).
  Previously these packs admitted only `claude-code`, `kiro-ide`, and `codex`. Recorded as an
  RFC-0013 § Errata decision; no contract change (both adapters already declare the
  `.agentbundle/` install prefix the broker needs).
- **`--dry-run` previews an install or upgrade without writing anything** —
  `agentbundle install --dry-run` and `agentbundle upgrade --dry-run` run the
  full read-only pre-flight, print a per-file plan to stdout (one
  `<action> <tier> <target>` line each — `create` / `overwrite` /
  `companion`, with Tier-2 lines naming the `.upstream.<ext>` companion the
  real run would drop), and exit 0 without touching the tree, state, or
  install marker. A present Tier-2 collision does not change the exit code;
  the preview is informational. `install --dry-run --force` is refused
  (`--force`'s destructive cleanup is incompatible with a read-only preview).
  The install preview covers the rendered adapter projection; it does not yet
  enumerate the governance seeds (`AGENTS.md`, `docs/CHARTER.md`,
  `docs/CONVENTIONS.md`) a real install also delivers. See the
  [preview how-to](../guides/_shared/how-to/preview-install-or-upgrade.md).

### Changed

- **`agentbundle upgrade` tells you when it keeps your edits** — when a
  projected file you edited since install collides with the new version
  (Tier-2), the upgrade preserves your file and drops the upstream version
  as a `<path>.upstream.<ext>` companion, exactly as before. It now also
  prints, on stderr after the upgrade commits, how many files were kept
  and the companion path of each — so you can find them and run
  `adapt-to-project` to merge. Parity with what `install` already reports;
  no change to the file-safety contract (the CLI still never clobbers or
  prompts). Per
  [RFC-0001 § Errata (2026-06-11)](../rfc/0001-bundle-distribution-by-adapter-spec.md#errata),
  which reconciles the original draft's unbuilt in-CLI Tier-2 prompt with
  this deterministic companion-drop design.

- **Leaner work-loop context use, same rigor** — the review reviewers
  (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`) now return
  only their distilled findings block (or `Clean — ready to commit.`), with no
  pre-findings methodology recap or process narration. The `work-loop` skill
  drops the full reviewer report from resident context once findings are
  recorded — the on-disk report plus `state.json` fingerprints are the durable
  record — and gains a `## Context hygiene` section with three context-saving
  levers (reference-read reduction, task-boundary compaction, narrowest-gate
  during FIX), each with a portable no-subagent floor, plus a "reduce, never
  lossily transform" guardrail. No verification surface changes: gates, the
  iterate-to-Clean loop, fingerprint stasis detection, the quality-engineer
  floor, and the iteration cap all behave exactly as before. See
  [`docs/specs/work-loop-context-hygiene/`](../specs/work-loop-context-hygiene/spec.md).

- **Codex receives full skill bodies** — the `skill` projection for the
  Codex adapter flips from `managed-block-inline` (one-line teasers
  in `AGENTS.md` between `<!-- agent-skills:start -->` /
  `<!-- agent-skills:end -->`) to `direct-directory`. Codex users now
  read `.agents/skills/<name>/SKILL.md` byte-equal to source — the
  same surface Claude Code and Kiro have always had. Per
  [RFC-0009 § Adapter contract change](../rfc/0009-codex-native-skills.md#adapter-contract-change).
  On the first install after upgrade, the adapter strips the
  legacy `<!-- agent-skills:start --> … <!-- agent-skills:end -->`
  region from any pre-existing `AGENTS.md` in place; outside-block
  content is preserved. The strip is destructive by design: hand-
  edited content *between* the delimiters is not migrated
  (RFC-0009 § Failure modes). The strip mechanism
  (`_strip_legacy_skill_block` + the retained `_splice_managed_block`
  helper) is kept for one minor release as the migration window
  (released N) and then removed in the release after (N+1).
  **Self-host mirrors Codex repo projection.** The self-host allow-list
  includes both `claude-code` and `codex`, so this repo now carries
  Codex's repo-scope projection alongside Claude Code: `.agents/skills/`
  for full skill bodies, `.codex/agents/` for subagent TOML, and
  `.codex/hooks.json` for hook wiring. `make build-check` enforces those
  paths the same way it enforces `.claude/`.

- **Uniform multi-pack entry point across `direct-directory` adapters**
  — `codex`, `claude-code`, and `kiro` all expose
  `project_packs(pack_paths, contract, output_root)` as the
  canonical orchestrator-facing surface. Single-pack `project()`
  is retained as a wrapper. Same-name skill collisions across
  packs resolve deterministic-last-wins by source-order.

- **Orphan-skill cleanup across `direct-directory` adapters** — after
  every multi-pack `project_packs(...)` call, the projected skill
  directory is swept: child directories whose names are not in the
  union of source skill names across the call's pack list are
  removed. Bound to the `skill` primitive only; symlinks are
  removed via `Path.unlink()` (never followed).

### Deprecated

- (nothing yet)

### Removed

- (nothing yet)

### Fixed

- (nothing yet)

### Security

- (nothing yet)

<!--
## [1.0.0] — YYYY-MM-DD

### Added
- Initial public release.

[Unreleased]: https://github.com/<org>/<repo>/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/<org>/<repo>/releases/tag/v1.0.0
-->
