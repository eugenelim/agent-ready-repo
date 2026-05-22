# RFC-0003: Adapter contract publication + reference CLI

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-21
- **Date closed:** 2026-05-22
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (defines
  the in-repo adapter contract this RFC publishes); [RFC-0002](0002-self-hosting.md)
  (validates the in-repo contract on every PR, strengthening the
  case for publishing). Depends on RFC-0001's F-spec + F-build
  landing first. This RFC replaces an earlier RFC-0003 plan
  ("Bundle Format Specification + CLI") which was scoped against
  the original RFC-0001 — most of that plan's contract-extraction
  work is now absorbed into RFC-0001's F-spec, leaving RFC-0003 to
  do publication and the CLI.

## Contents

- [Summary](#summary)
- [Motivation](#motivation)
- [Proposal](#proposal)
  - [The published spec](#the-published-spec)
  - [The reference CLI](#the-reference-cli)
  - [Conformance test suite](#conformance-test-suite)
  - [Spec versioning](#spec-versioning)
  - [Migration path](#migration-path)
- [Alternatives considered](#alternatives-considered)
- [Drawbacks](#drawbacks)
- [Unresolved questions](#unresolved-questions)
- [Follow-on artifacts](#follow-on-artifacts)

## Summary

Lift the per-IDE adapter contract from `docs/contracts/adapter.toml`
in this repo to a published open standard, with semantic versioning
and a conformance test suite. Ship a reference CLI — working name
`agentbundle` — that exposes the contract's executable form:
`validate <bundle>` checks a bundle's projection against the
contract; `render <bundle> --target <ide>` applies the contract to
produce per-tool output (the same logic as RFC-0001's build pipeline,
exposed as a command); `scaffold` drops the governance directory
tree into a target path (solves the brownfield-with-governance gap);
`list-targets` enumerates the adapters this CLI version supports.
The CLI is the spec's executable form. When the spec is
ambiguous, the CLI's behaviour is the tiebreaker. Other implementations
(APM upstream, future independent renderers) validate against the
conformance suite to claim compliance.

## Motivation

Three reasons to publish the contract separately from the bundle that
defined it:

**1. Other implementations need something to conform to.** APM's
adapters are in code with no published interface; Claude plugins are
single-tool; agentskills.io stops at the single-skill level. A
published per-IDE adapter contract gives APM upstream (or any future
renderer) a target to validate against. Without publication, the
contract is "the way *our* build pipeline happens to behave," which
is brittle as a standardization basis.

**2. A CLI is the spec's executable form.** Paper specs are useful as
documentation but brittle: readers interpret them differently. The
CLI disambiguates — when the spec is unclear, the reference CLI's
behaviour is the tiebreaker. This is the same pattern as
`terraform` for HCL, `helm` for Helm charts, `npm` for the npm
registry. The CLI ships *with* the spec, not before it; a CLI
without a spec is yet another installer.

**3. The CLI is our surface for adopter-side tooling.** The install
path goes through APM and Claude plugins (RFC-0001 settled this);
neither of those tools has a place for adopter-side commands like
"drop the governance scaffold into my repo," "adapt the just-
installed primitives to my project conventions in a CI script,"
or "diff the contract against my installed bundle." Our CLI is the
right home for those — it's complementary to the install routes,
not a replacement. The CLI's `adapt` subcommand in particular is
the scriptable counterpart to RFC-0001's `adapt-to-project` skill;
both are required under the catalogue-installer model where
the value proposition is "superpower any existing codebase, not
just fresh ones."

## Proposal

### The published spec

The adapter contract — currently at `docs/contracts/adapter.toml`
in this repo per RFC-0001's F-spec — moves to a publishable home with
versioning, a stable URL, and a license. Three hosting options:

1. **Stay in this repo, treat the path as canonical.** URL is
   `github.com/<org>/agent-ready-repo/blob/main/docs/contracts/adapter.toml`.
   Versioned by git tags on the repo.
2. **Sibling repo (`adapter-contract`).** Clean separation. URL is
   `github.com/<org>/adapter-contract/`. Releases independently of
   our bundle.
3. **Neutral org name (`agent-adapter-spec` or similar).** Signals
   "this is a standard, not our project." Requires governance setup
   we don't have yet.

Working assumption: **option 1 for v0.x; promote to option 2 at v1.0**
if outside implementations show up. Sibling-repo cost (cross-repo
issue tracking, separate CI, more discovery surface) doesn't pay off
until there's actually a second implementation to coordinate with.

The spec file itself stays TOML (RFC-0001's reasoning holds:
schema-definition artifact, typed scalars, comments, format-neutral
relative to APM and Claude). RFC-0001's `[contract]` table already
carries a `version = "0.1"` field; RFC-0003 ratifies that field as
the canonical spec version, readable by `agentbundle --version`
and the conformance suite.

### The reference CLI

**Name:** `agentbundle` (per the earlier RFC-0003 plan; revisit at
implementation if a better name surfaces).

**Subcommands** (all pack-aware where it makes sense):

- `agentbundle list-packs <catalogue-uri>` — Lists the packs
  published by a catalogue (one row per pack: name, version,
  description, dependencies). Adopters call this before deciding
  which packs to install.
- `agentbundle install --pack <pack-name> [--pack <pack-name>] <catalogue-uri>` —
  Constrained-network fallback installer (used when APM or
  Claude plugins aren't reachable). Installs the named packs into
  the adopter's repo per the Tier-2 fast-path in RFC-0001's
  adopter file safety contract: at any path where the adopter
  has a pre-existing file, write the pack's version alongside as
  `<filename>.upstream.<ext>` rather than clobbering, leaving
  the merge for `agentbundle adapt`. Cross-pack `seeds/`
  collisions follow the merge semantics from RFC-0002 (file-by-
  file merge, file-level collision = error).
- `agentbundle validate <pack-path>` — Reads the pack's adapter
  contract version, runs the conformance suite for that version,
  reports pass/fail per check. Exit 0 if clean, 1 if any check
  fails. Operates on a single pack.
- `agentbundle render <pack-path> --target <ide> [--output <dir>]` —
  Applies the contract against `<pack-path>`'s primitives to
  produce per-tool output for `<ide>`. This is RFC-0001's build
  pipeline exposed as a CLI command; same code, different surface.
  Pack-scoped — the CLI renders one pack at a time.
- `agentbundle scaffold [--output <dir>]` — Renders the
  `core` pack's `seeds/` content (docs/ tree with READMEs and
  spec/plan templates) into the target directory, plus the
  `seeds/` content of any other installed packs. Pre-existing
  files at any target path follow the same Tier-2 fast-path as
  `agentbundle install` — the pack's version drops alongside as
  `<filename>.upstream.<ext>` rather than clobbering; merge is
  deferred to `agentbundle adapt` or the LLM skill.
  Covers brownfield adopters who want our governance scaffolding
  in their existing repo (see RFC-0001's *Common adoption
  patterns* table).
- `agentbundle adapt [--packs <pack>,<pack>,...] [--values-from <file>] [--output <dir>]` —
  **Deterministic, non-LLM scriptable variant of the
  `adapt-to-project` skill from RFC-0001.** Pack-aware: operates
  only on the packs the adopter actually installed. Three
  responsibilities (each pack-scoped per the installed set):
  - **Substitute** the `<adapt:NAME>` markers in projected files
    using the values from `--values-from` (project name, install
    command, etc.).
  - **Surface upstream-companion files** — for every
    `<filename>.upstream.<ext>` left by install, write a
    `.adapt-pending.md` report listing the companion path and a
    one-line diff summary. The CLI variant does *not* attempt a
    deterministic merge — text-level merge of markdown sections is
    ambiguous enough (heading-anchored? line-anchored? where do
    moved sections land?) that any rule we pick would surprise
    some adopters. CI mode (`--ci`) writes the report and exits
    non-zero so the CI flags the pending companions for human
    review. The LLM skill variant handles the actual merge
    interactively; the CLI variant defers to the LLM run.
  - **Resolve discovery decisions from `.adapt-discovery.toml`**
    if present (the LLM skill writes this file with the adopter's
    accepted *and* declined discovery decisions); the CLI applies
    accepted ones deterministically and skips findings already
    marked declined so re-runs don't churn. *New* discovery
    (finding non-canonical content under different names) is
    LLM-only and isn't part of the CLI variant.
  The LLM skill variant (ships in the `core` pack, runs from
  Claude Code) is the headline case; this CLI variant covers CI
  environments and constrained-network adopters who need a
  deterministic apply step after the LLM session ran.
- `agentbundle list-targets` — Enumerates the adapters this CLI
  version knows about. Useful for adopters to confirm what they
  can render to.
- `agentbundle diff <pack-path>` — Re-renders the pack and diffs
  against on-disk projected output. Same logic as RFC-0002's `make
  build --check`, exposed as a CLI command for adopter-side use.
- `agentbundle init-state` — Hashes the just-installed projection
  files (post APM or Claude-plugin install) and writes them to
  `.agent-ready-state.toml`, enabling Tier-2 detection for adopters
  who installed via the upstream tools but want the catalogue's
  file-safety guarantees on subsequent adapt or update operations.
  Required only for APM/Claude-plugin install routes; CLI-installed
  state is initialised at install time.
- `agentbundle uninstall --pack <name>` — Removes Tier-1 files for
  the named pack (per the safety contract in RFC-0001); warns on
  Tier-2 (offers keep-or-remove-with-backup); never touches Tier-3.
  Updates `.agent-ready-state.toml`. Only valid against
  CLI-installed packs; APM/Claude-plugin packs uninstall via their
  native tools.
- `agentbundle upgrade --pack <name> [--skill <skill> | --agent <agent> | --hook <hook> | --seed <path>] [--to <version>]` —
  Per-pack upgrade with optional per-primitive granularity, per
  RFC-0001's *Upgrades — granularity* section. Without a per-
  primitive flag, the whole pack moves to `--to` (or the latest
  available version), applying the Tier-1 / Tier-2 safety
  contract. With a per-primitive flag, only that primitive's
  files move; the rest stay at the previously-installed version,
  and `.agent-ready-state.toml` records the mixed-version state.
  Subsequent whole-pack upgrades flag mixed state to the adopter
  before proceeding.

**What the CLI is *not*:**
- Not a competing primary installer. `claude /plugin install` and
  `apm install` remain the install routes for adopters in
  environments where those tools are available. `agentbundle install`
  exists *only* for constrained-network environments where neither
  works — the third install route named in RFC-0001's Distribution
  outputs table.
- Not a registry. Discovery happens through `marketplace.json` for
  Claude plugins and git URLs for APM. The CLI doesn't host a
  catalog.
- Not a manifest format. APM's `apm.yml` and Claude's `plugin.json`
  remain the manifests. The CLI consumes those.

**Distribution:** The corporate-network discipline from RFC-0001
(git-clone + git-pull only, no raw HTTP) constrains this. Three
plausible distribution paths:

1. **Python `zipapp` distributed via GitHub Releases**, fetched with
   `gh release download` (which goes through authenticated git
   access). Single executable, pure stdlib, no `pip install`. This
   is the most constrained-network-friendly path.
2. **`pip install agentbundle` through Artifactory.** Same friction
   as Copier in the original RFC-0001 — works through Artifactory +
   PAT, doesn't work in PAT-less environments.
3. **Homebrew formula** for Mac/Linux developers outside corporate
   networks. Doesn't satisfy the corporate constraint but earns its
   keep for personal use.

Working assumption: ship all three; the `zipapp` route is the
load-bearing one for the constrained-network case.

### Conformance test suite

The conformance suite is a directory of test fixtures, each fixture
being:

- A small input bundle (synthetic, ~3-5 primitives).
- An expected output tree per target adapter.
- A test runner that runs `agentbundle render` and asserts the
  output matches.

Other implementations claim conformance by running the suite and
publishing the results. The suite lives alongside the spec; its
version pins to the spec version.

Conformance has two tiers:
- **Schema conformance** — bundle's `adapter.toml` parses
  per the published schema. Mechanical, fast.
- **Semantic conformance** — bundle's projection matches the
  expected output for each target. Requires running the
  implementation against fixtures.

Both run via `agentbundle validate`; the `--strict` flag enables
semantic conformance.

### Spec versioning

**Semantic versioning.** `v0.x` while breaking changes are expected;
`v1.0` when the contract is considered stable.

When a CLI compiled against spec `v1.2` reads a bundle declaring
`v1.4`:
- **Same major version, newer minor** → forward-compat read-only:
  the CLI processes everything it understands, emits `[info]` for
  fields it doesn't recognize, no failure.
- **Same major version, older minor** → process normally; older
  bundles work on newer CLIs by definition.
- **Different major version** → refuse with a clear message naming
  the version mismatch. No silent partial behavior.

The CLI's `--version` output names the spec version it ships
against. Packs declare the spec version they conform to in their
`pack.toml` under `[pack.adapter-contract]` (`version = "0.1"`,
matching the value in `adapter.toml`'s `[contract]` table).

### Migration path

This repo's adapter contract — currently `docs/contracts/adapter.toml`
under RFC-0001's F-spec — becomes the published spec at `v0.1`. The
publication step is mechanical: tag the file's location, copy the
schema definition into a published artifact, update the CLI to read
spec version from the contract.

Per-pack `pack.toml` is the unified declaration; the build pipeline
derives per-tool fields from it:

```toml
# packs/core/pack.toml (excerpt)
[pack.adapter-contract]
version = "0.1"
```

```yaml
# Build-derived dist/apm/core/apm.yml (excerpt)
adapter-contract: "0.1"
```

```json
// Build-derived dist/claude-plugins/core/.claude-plugin/plugin.json (excerpt)
{ "adapter-contract": "0.1", ... }
```

Adopter-facing impact is zero — these fields are metadata that
tools that don't understand them ignore.

## Alternatives considered

**Alt 1 — Don't publish. Keep the contract internal.** Spec stays at
`docs/contracts/adapter.toml`; no versioning, no
conformance suite, no CLI. **Why not chosen:** the contract is the
only architectural artifact this template produces that isn't
already in APM or Claude plugins. Not publishing it gives up the
one contribution while keeping all the maintenance
cost.

**Alt 2 — Paper-only spec, no CLI.** Publish the contract as a doc;
skip the CLI. The earlier RFC-0003 plan called this "RFC-0003a."
**Why not chosen:** without a reference implementation, the spec is
brittle to interpretation. The CLI is what disambiguates corner
cases; building both at once keeps them honest with each other.
Cost is modest — the CLI is largely the build pipeline from
RFC-0001's F-build with a different command surface.

**Alt 3 — Contribute the contract to APM upstream as their adapter
format.** APM has the user base and the install routes; making our
contract APM's official adapter format would give it instant reach.
**Why not chosen:** unilaterally proposing a format to APM upstream
isn't ours to do — APM's governance is "technically collaborative
but governance-sparse" per the research, and there's no documented
RFC process for adding format conventions. We can *contribute* the
contract to APM once it's published independently; that's an
upstream-PR path, not an architectural one. Publishing first keeps
us non-dependent on APM's acceptance timeline.

**Alt 4 — One mega-RFC combining 0001 + 0002 + 0003.** Ship the
bundle, self-host, and publish the spec in a single RFC. **Why not
chosen:** the three steps are independently shippable and each has
a different audience. 0001 is for the maintainers (what does our
template look like); 0002 is for CI (drift detection mechanics);
0003 is for the broader ecosystem (here's a standard you can
implement against). Bundling them obscures the audience for each.

**Alt 5 — A different CLI name.** `agentbundle` is the working name
from the earlier RFC-0003 plan. Alternatives considered briefly:
`adapterctl`, `bundlespec`, `agentpkg`. **Why `agentbundle`:**
keeps continuity with the earlier RFC plan; the name signals "this
operates on agent bundles" without making the spec name load-bearing.
Settled at implementation time, not RFC-altitude.

## Drawbacks

**Publishing implies a stewardship commitment.** Once we tag the
spec `v0.1` and ship a CLI, downstream implementations may form
expectations about stability, backwards compatibility, and
support. Mitigation: `v0.x` framing is honest about pre-1.0
volatility; `v1.0` requires a deliberate readiness check.

**The conformance suite is real work.** Building fixtures,
writing the runner, maintaining them across spec versions — all
of this adds maintenance surface. Scope-tight version: ship the
suite with one fixture per target adapter (~5 fixtures total) at
`v0.1`; expand as edge cases surface.

**CLI distribution under corporate-network discipline is constrained.**
The `zipapp` + `gh release download` path works, but it's the
narrowest distribution method we use anywhere in the bundle stack.
Adopters in less-constrained environments may prefer
`pip install`; documenting all three paths adds complexity to
`USING_THIS_TEMPLATE.md`.

**`agentbundle` competes for namespace with APM and Claude plugins
in adopter mental models.** Adopters may wonder "do I install
agentbundle or apm or claude/plugin?" The answer is "all three for
different purposes" — but that's friction. Mitigation: clear docs
on the install-story page naming exactly when to use which.

**The CLI is new code in a domain where new tools die fast.** The
agent-tooling ecosystem is churning rapidly (APM is ~1 year old as
of 2026-05; Claude plugins newer still). Our CLI joins that churn.
If a clearly-better cross-tool CLI emerges, we revisit.

## Unresolved questions

1. **Spec hosting at v1.0.** Stay in this repo (option 1), sibling
   repo (option 2), or neutral org (option 3)? Working assumption:
   sibling repo when a second implementation shows up; this-repo
   until then. The decision can defer past `v0.1` ship.

2. **Conformance levels and badging.** Should we have a "verified
   conformant" badge implementations can earn by passing the
   suite, like Anthropic's "Verified" badge for Claude plugins?
   Working assumption: no badge at `v0.1`; revisit when the second
   implementation appears.

3. **CLI versus library split.** Is `agentbundle` the CLI surface
   over a `agentbundle.py` Python library that other tools can
   import? Working assumption: library-first, CLI as the documented
   surface; same code, two entry points. Defer the public-library-
   API question until a real importer surfaces.

4. **Distribution form priority.** `zipapp` first, then
   `pip install`, then Homebrew? Working assumption: yes, in that
   order. Settled by F-cli-dist implementation.

5. **Whether `agentbundle install` should grow into a unifying
   wrapper over APM and Claude plugins.** Body resolves *no* for
   v0.1 — `agentbundle install` is scoped to the constrained-network
   fallback case and explicitly doesn't compete with native install
   tools. Reopen if adopter feedback shows a real demand for a
   single unified install surface.

## Follow-on artifacts

If accepted, this RFC produces:

- **F-spec-publish.** Move `docs/contracts/adapter.toml`
  to the publication home (per the hosting decision in Unresolved
  Question 1), tag `v0.1`, write `SPEC.md` overview prose, license
  the spec under a permissive license (CC-BY-4.0 or similar — chosen
  by the spec author).
- **F-cli — `agentbundle` reference implementation.** Eleven
  subcommands (`list-packs`, `install`, `validate`, `render`,
  `scaffold`, `adapt`, `list-targets`, `diff`, `init-state`,
  `uninstall`, `upgrade`). Library-first; CLI as a documented
  surface over the library. Reuses RFC-0001's F-build code where
  possible. `install` is scoped to the constrained-network
  fallback case per the body; `init-state` and `uninstall` exist
  to give APM and Claude-plugin adopters access to the safety
  contract's Tier-2 guarantees; `upgrade` exposes the per-
  primitive granularity from RFC-0001's *Upgrades — granularity*
  section.
- **F-cli-dist — CLI distribution.** `zipapp` via GitHub Releases
  as primary; `pip install` and Homebrew as additional paths.
  Minimum Python: 3.11 (for stdlib `tomllib`); adopters on older
  runtimes get a clear refuse-and-explain message rather than
  silent failure.
- **F-conformance — Conformance test suite.** One fixture per
  target adapter at `v0.1`; runner exposed via `agentbundle
  validate --strict`.
- **F-version-decl — Pack conformance declaration.** Add a
  `[pack.adapter-contract]` table with `version = "0.1"` to
  per-pack `pack.toml`; document the convention. Build-pipeline
  generates derived `adapter-contract` fields in per-tool manifests
  (`apm.yml`, `plugin.json`) for downstream visibility.

The biggest of the three RFCs *under the old plan* — but
substantially smaller under the new RFC-0001/RFC-0002 shape because
the contract extraction is already done. The work that remains is
publication + CLI + conformance, all of which are well-scoped.

## Amendments

- 2026-05-22 (post-acceptance): adapter contract files relocated to
  `docs/contracts/`; this RFC's path references updated (the sibling-repo
  alternative name `adapter-contract`, the `[pack.adapter-contract]`
  TOML key, and the `adapter-contract: "0.1"` field name are concept
  identifiers and remain unchanged). Full rationale and the
  `CONVENTIONS.md:80` exception note live in
  [RFC-0001 § Amendments](0001-bundle-distribution-by-adapter-spec.md#amendments).
