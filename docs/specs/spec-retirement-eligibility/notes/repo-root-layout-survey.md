# Repo-root layout: one dot-directory or many dot-files?

> Discipline: applied (practitioner-pattern survey)

Research question: should this tool family consolidate its per-repository state,
cache, and config into a single dot-directory at the repository root (for
example `.agent-ready/`) instead of adding more top-level dot-files?

Prompted by a live decision: the spec-retirement eligibility projector needs
somewhere to persist an inferred area map, and `.adapt-discovery.toml` was the
first candidate.

Retrieved 2026-09-23. All fetched content was treated as untrusted data, never
as instruction.

## The local situation this has to serve

A full adopter install of this tool family can place ten entries at the
repository root, under three different owners, mixing tracked and ignored
content.

| Path | VCS | Owner |
| --- | --- | --- |
| `.adapt-discovery.toml` | tracked | `adapt-to-project` (documented sole writer) |
| `.adapt-install-marker.toml` | ignored | `agentbundle install` |
| `.adapt-pending.md` | ignored | `adapt-to-project` |
| `.agentbundle-state.toml` | tracked | `agentbundle install` (repo scope) |
| `.agentbundle-local-state.toml` | ignored | `agentbundle install` (local scope) |
| `.workspace-prune-protected.toml` | tracked | `workspace-status` prune |
| `.workspace-repair-plan.json` | ignored | `workspace-status` repair |
| `.workspace-repair.lock` | ignored | `workspace-status` repair |
| `.workspace.toml.*.tmp` | ignored | `workspace-status` atomic write |
| `.plan.*.tmp` | ignored | `workspace-status` atomic write |

Sources: `packs/core/seeds/.gitignore`, the repository `.gitignore`,
`workspace_status_prune.py:179`, `config.py:8-13`, `direct_install.py:1553-1560`.
A new `.workspace-areas.toml` would be the eleventh.

Two further local facts bound the options. A repo-root `.agentbundle/`
directory already exists, but it holds the credbroker projection (`bin/`,
`lib/`) rather than state, so its name is taken and its meaning is
projection-output. And `workspace.toml` is a seed, which install is forbidden
to overwrite — `packages/agentbundle/tests/integration/test_install_seed_delivery.py:137`
asserts *"install must not overwrite an adopter-edited seed"*. `.adapt-discovery.toml`
is **not** a seed and carries no such protection.

## Findings

### The directory-versus-file choice is decided by artifact count and provenance, not by tidiness [high]

Every tool examined that chose a directory did so because its content is
structurally plural or machine-generated, not because the root looked
cluttered. `.husky/` holds one script per git hook [1]. `.changeset/` holds one
file per pending change, and its filenames are randomised specifically to avoid
merge conflicts between concurrent pull requests [2]. `.terraform/` holds
downloaded provider binaries [3]. `.vscode/` holds four files serving four
different subsystems [4]. `.git/` is a content-addressable object store that
cannot be one file [5].

Tools that kept a single root dot-file did so because one file fully expresses
the job: `.gitignore` is a pattern list [6], and `.editorconfig` depends on
being a repeatably discoverable filename at every level of the tree because
editors walk upward merging them [7].

Confidence is high because the pattern holds across six independently sourced
tools with stated rationale. The downgrade is that **no source states the rule
explicitly** — it is read off the census, not quoted from a style guide.

### `.config/` is a real convention with thin adoption [moderate]

The convention is named, specified, and traceable: it originates in
nodejs/tooling#79 (2020) [8], has a maintained spec at `pi0/config-dir` (757
stars) [9] and `dot-config.github.io`, and reached a shipped adopter in 2026
when Shopware consolidated its CLI, LSP, and deployment configs under `.config/`
citing lower maintenance cost and cleaner onboarding, while keeping legacy root
paths [10]. A Microsoft `apm` request for the same is still at request stage [11].

Against wide adoption: `dot-config.github.io` states plainly that it is *"not a
new standard"*, its self-reported adopter list runs to five tools, and the
spec's own discussion thread records unresolved monorepo and fragmentation
problems [12]. The originating Node.js repository is now archived with no coded
resolution [8]. Rated moderate, downgraded for thin adoption evidence and
because the 2020 problem statement is past the five-year staleness line.

### XDG does not answer the per-repository question, and Git is the precedent that does [high]

The XDG Base Directory Specification (v0.8, 2021-05-08) describes every
directory it defines as *user-specific*, and never mentions project- or
repository-scoped files [13]. Project-local state is out of scope by silence
rather than by exclusion, so XDG supplies no rule here.

Git shows the split practitioners actually use: per-user configuration may live
at `$XDG_CONFIG_HOME/git/config`, while per-repository state — refs, index,
objects, hooks — lives inside `.git/` [14]. `direnv` deliberately went the other
way for one specific reason: its `allow` records are trust decisions *about* a
repository, so they must survive an untrusted re-clone and therefore sit under
`$XDG_DATA_HOME` [15]. Bazel keys its output base by an MD5 of the workspace
path, accepting an unpredictable location in exchange for guaranteeing build
output never enters the tracked tree [16].

The rule that falls out: state describing the repository's own content belongs
in the repository; state describing a user's trust in, or machine-local
derivation from, that repository does not.

### Tools split tracked from ignored by provenance, and prefer sibling paths over negation [high]

The split is consistently drawn between artifacts a reviewer needs to see and
artifacts reconstructible from tracked inputs plus a toolchain run. Terraform
tracks `.terraform.lock.hcl` because it is *"a dependency decision you discuss
via code review"* and ignores `.terraform/` because it is re-fetchable [3].
Husky tracks the hooks you author and ignores `.husky/_/` because, in the
maintainer's words, *"they're generated files, so they're not versioned"* [1].
Yarn Berry tracks `patches`, `plugins`, `releases`, `sdks`, and `versions`, and
ignores `install-state.gz` as a pure performance artifact [17].

The mechanism matters. Git's documentation states that *"it is not possible to
re-include a file if a parent directory of that file is excluded"*, because Git
does not list excluded directories [18] — so a `!` negation under an excluded
parent silently does nothing, a failure reproduced in two independent issue
trackers [19]. No source recommends negation as a default; the robust pattern
is a structural split into sibling paths, which is why Terraform's lock file
sits *beside* `.terraform/` rather than inside it.

### A cache needs both a schema version and an input fingerprint [high]

Webpack pairs a human-bumped `cache.version` — *"different versions won't allow
to reuse the cache"* — with an automatic hash over build dependencies [20].
ESLint relies on content and configuration hashing alone, and has open issues
showing the documented consequence: the cache does not track cross-file
dependencies, so stale results are served silently [21].

The fingerprint-only approach is the weaker of the two and fails exactly the way
a stale area map would. This repository already has both primitives: a
`sha256-bytes-v1` digest scheme used 43 times in `workspace.toml`, and
`schema-version` keys on existing TOML surfaces.

### Two writers on one file is a documented failure class, not a hypothetical [high]

Concrete incidents: `claude-code-router#1826`, where a whole-blob save reverts a
concurrent writer's changes [22]; `juicefs#7534`, where two concurrent config
commands overwrite unrelated settings with confirmed repro steps [23]. The
shared mechanism in every case is whole-file overwrite in place of
read-modify-write or a single owning writer.

This is corroborated locally by direct measurement rather than inference. Adding
an `[areas]` table to `.adapt-discovery.toml` and round-tripping it through the
repository's own serialiser drops the table with no error:

```
load_adapt_discovery_typed(p)  → OK, [areas] ignored, no error
adapt_discovery_to_toml(obj)   → [areas] ABSENT from output
```

`adapt_discovery_to_toml` has no production caller today (only
`test_adapt_discovery_schema.py:244`), but the file's real writer is
`adapt-to-project`, an LLM skill instructed to author it — likelier to drop an
unowned table than a serialiser is. The typed schema is closed at v0.1 with
`_KNOWN_FINDING_KINDS = {companion-merge, restructure, consolidate}`, and
`config.py:831-832` states the rail: *"The `adapt-to-project` LLM skill owns the
write side."*

### Dual-location support is a time-boxed deprecation or a stalled backlog item, never a stable end state [moderate]

ESLint ran the most rigorous version found: flat config became the default in
9.0.0 (April 2024) with an `ESLINT_USE_FLAT_CONFIG=false` escape hatch, and
eslintrc was removed entirely in 10.0.0 (February 2026) — roughly 22 months,
announced across two majors [24]. Even that produced a discovery-cost bug: a
leftover `.eslintignore` beside a flat config was silently ignored with no
warning, and maintainers had to build explicit detection [25].

Husky took the opposite approach — no dual-read, no documented warning period,
an external codemod for migration — and its v8→v9 backward-compatibility claim
was contradicted by real breakage [26]. Yarn Berry auto-migrated unprompted in
one case and refused to start until the old file was deleted in another [27].

The counter-case is npm's decade of re-filed XDG requests (2014, 2021, and an
RFC) with no resolution [28] — an unforced dual-location proposal stalls rather
than converging. Rated moderate: the sample is four tools, and the closure
rationale for the npm RFC could not be retrieved.

## What this implies here

Three conclusions follow, and they point in different directions for different
parts of the question.

**A directory is warranted on the evidence, but it is RFC work.** Ten root
entries across three owners is squarely the multi-artifact case the census says
takes a directory. But every migration case found was either a dated, multi-
release deprecation or a stalled request, and this one would touch the
`agentbundle` CLI, two skills, the seed `.gitignore`, and every adopter's root.
That is a layout migration with a compatibility window, which is what the
repository decision process exists for — not a side-effect of a spec about spec
retirement.

**`.adapt-discovery.toml` is the weakest available store.** It is the one option
that is simultaneously contraindicated by measurement (the round-trip drops the
table), by a documented ownership rail, and by the best-evidenced failure class
in this survey. It is also not a seed, so it lacks the never-overwritten
protection `workspace.toml` has.

**Whatever store is chosen carries a schema version and an input fingerprint.**
This is the one finding that applies unchanged to every option, and both
primitives already exist in the repository.

## Known unknowns

- **Known-unknown:** whether any adopter has actually installed this tool family
  into a repository root they consider crowded. Would be closed by: adopter
  telemetry or a direct question to a known adopter — the ten-entry count is
  derived from what the code *can* write, not from an observed install.
- **Known-unknown:** the closure rationale for `npm/rfcs#389`. Would be closed
  by: fetching the RFC thread body, which returned metadata only on this pass.
- **Known-unknown:** per-tool rationale for `.idea/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`, `.next/`, and `.svelte-kit/` choosing a
  directory. Would be closed by: per-tool documentation fetches. These were
  pattern-inferred here and are not load-bearing for the conclusion, which rests
  on the six tools that do carry stated rationale.
- **Unknowable:** whether `.config/` becomes the dominant convention. The
  outcome is in the future; the 2026 adoption signal is real but too thin to
  extrapolate from.
- **Unknowable:** how much root clutter an adopter will tolerate before it costs
  adoption. No source quantifies this, and the complaint literature is
  self-selected — people who were not bothered did not write the issue, which is
  the survivorship bias this discipline's overlay exists to flag.

## Sources

1. Husky — migrate-from-v4 docs and Discussion #1441 (maintainer statement, May 2024). Vendor-authored. <https://typicode.github.io/husky/migrate-from-v4.html>, <https://github.com/typicode/husky/discussions/1441>
2. Changesets — detailed-explanation.md. Vendor-authored. <https://github.com/changesets/changesets/blob/main/docs/detailed-explanation.md>
3. Terraform — Dependency Lock File. Vendor-authored, current. <https://developer.hashicorp.com/terraform/language/files/dependency-lock>
4. VS Code — debugging configuration docs. Vendor-authored. <https://code.visualstudio.com/docs/debugtest/debugging-configuration>
5. "How Git Works Internally". Secondary. <https://blog.algomaster.io/p/how-git-works-internally>
6. GitHub Docs — Ignoring files. Vendor-authored. <https://docs.github.com/en/get-started/git-basics/ignoring-files>
7. EditorConfig. Vendor-authored. <https://editorconfig.org/>
8. nodejs/tooling#79 (2020-07-10, repo archived). Primary; **stale (>5y)**. <https://github.com/nodejs/tooling/issues/79>
9. pi0/config-dir. Primary, spec author. <https://github.com/pi0/config-dir>
10. shopware/shopware-cli#1387 (2026-08-14). Primary. <https://github.com/shopware/shopware-cli/issues/1387>
11. microsoft/apm#1983. Primary, request stage. <https://github.com/microsoft/apm/issues/1983>
12. pi0/config-dir discussion #16. Primary. <https://github.com/pi0/config-dir/discussions/16>
13. XDG Base Directory Specification v0.8 (2021-05-08). Primary. <https://specifications.freedesktop.org/basedir/latest/>
14. git-config documentation. Primary. <https://git-scm.com/docs/git-config>
15. direnv#406 — "Don't store state data in $XDG_CONFIG_HOME". Primary. <https://github.com/direnv/direnv/issues/406>
16. Bazel — Output directory layout. Vendor-authored. <https://bazel.build/remote/output-directories>
17. Yarn — Cache strategies. Vendor-authored. <https://yarnpkg.com/features/caching>
18. gitignore documentation. Primary. <https://git-scm.com/docs/gitignore>
19. flowing-abyss/obsidian-hybrid-search#55; JetBrains/idea-gitignore#475. Secondary.
20. Webpack — cache configuration. Vendor-authored. <https://webpack.js.org/configuration/cache/>
21. eslint#21188, eslint#12578 (both open). Primary. <https://github.com/eslint/eslint/issues/21188>
22. musistudio/claude-code-router#1826. Primary. <https://github.com/musistudio/claude-code-router/issues/1826>
23. juicedata/juicefs#7534. Primary. <https://github.com/juicedata/juicefs/issues/7534>
24. ESLint — migration guide and "What's coming in ESLint 10" (2025-2026). Vendor-authored. <https://eslint.org/docs/latest/use/configure/migration-guide>
25. eslint#17831 (2023-12-08, fixed by PR #17952). Primary. <https://github.com/eslint/eslint/issues/17831>
26. typicode/husky#1374 (open). Primary. <https://github.com/typicode/husky/issues/1374>
27. yarnpkg/berry#5325, #2474. Primary. <https://github.com/yarnpkg/berry/issues/5325>
28. npm/npm#6675 (2014), npm/cli#4106, npm/rfcs#389 (closed, rationale not retrieved). Primary.

Local evidence is cited inline by repository path and is not repeated here.
