# How to design a profile

**Use this when:** You want to propose a new curated set of packs that a named adopter persona would install in one command.
**Prerequisites:** Familiarity with the pack catalogue and `python3 tools/lint-profiles.py` available to validate your manifest.
**Result:** A `profiles/<name>.toml` manifest that passes all four design tests and the profile lint, ready to submit via RFC.

A profile is a curated, single-scope set of packs that installs in one command:

```bash
agentbundle install --profile solution-architect <catalogue>
```

This guide covers how to decide what belongs in a profile, the design tests every profile must pass, worked examples from the three shipped profiles, and how to propose a new one.

## What a profile is (and is not)

A profile is a `profiles/<name>.toml` manifest.
It declares a scope (user or repo) and a list of packs, in dependency order.
That is all it is.

It is **not a meta-pack.**
A meta-pack would be a pack whose only content is a dependency list — a profile already does this job without the overhead of a pack.
If you are tempted to create a pack whose only purpose is to depend on other packs, you want a profile.

It is **not a comprehensive install set.**
A profile that installs ten packs for ten different use cases is a catalogue install, not a profile.
Profiles are for cohesive archetypes, not comprehensive coverage.

## The four design tests

Before proposing a new profile, check it against four tests.
All four must pass.

**Test 1: Scope homogeneous.**
Every pack in the profile must allow the profile's declared scope.
A user-scope profile cannot include a repo-scope-only pack.
A repo-scope profile can include packs that allow both scopes, but it signals to the installer that a committed repo is required.
The lint tool enforces this — a scope mismatch blocks the PR.

**Test 2: Dependency-complete.**
If pack B depends on pack A, pack A must appear before pack B in the manifest.
The lint tool resolves the dependency graph and rejects incomplete declarations.
A missing dependency causes installation to fail or silently skip a pack.

**Test 3: Habit, not toolbox.**
The packs form a habit — a set the target persona reaches for together, repeatedly, because their work naturally involves all of them at once.
A profile whose packs a persona might someday need is a toolbox.
Toolboxes install things people don't use; habits install exactly what's needed.
A useful pressure test: could the persona work without any one of these packs for a full week?
If yes, that pack may not belong.

**Test 4: Fits a real adopter archetype.**
There is a named persona who would install this profile on day one and use all of it regularly.
Name them.
If the persona description is vague ("anyone who does technical work"), the profile is too broad.
The archetype must be specific enough to make a scope decision obvious.

## Worked examples

### `solution-architect` (user scope)

Packs: `architect`, `desk-research`, `contracts`.

A solution architect designs systems, researches domains, and works with API contracts.
All three packs are user-scope — the architect carries their kit across repos and often works before a repo exists.
Each pack is used on every engagement: `architect` for design artifacts and reference architectures, `desk-research` for market and technical research, `contracts` for API-driven integration work.
The three packs are never used independently — a solution architect who has one wants all three.
Scope choice is obvious from the persona: user, because the work is cross-repo.

### `full-ceremony` (repo scope)

Packs: `core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`.

A team that wants the full coordination and governance discipline in one install.
All four packs are repo-scope — they write to the repo (spec files, ADRs, RFCs, guide structure, workspace state).
The persona is a team lead or platform engineer setting up a new repo for a team that will run the full coordination system.
`monorepo-extras` depends on `core`; it appears after `core` in the manifest (Test 2).
Scope is obvious: repo, because all four packs require a committed repo to be useful.

### `inception` (user scope)

Packs: `desk-research`, `product-engineering`, `architect`.

A discovery-phase practitioner who needs research, situation framing, and architecture tools before a repo exists.
User scope — the work happens in the shaping room, not in a committed repo.
The three packs form the shaping room toolkit: research → situation framing → architectural concept.
The persona installs this once and carries it across engagements.

## Profiles are first-party today

All profiles in this catalogue are authored and maintained by the catalogue team.
They ship through the RFC process: the RFC states the persona, the packs (with justification for each), the scope, and how the profile clears all four design tests.
The RFC review is the gate.

Adopter-authored profiles — where an org creates a local `profiles/<name>.toml` that is not part of the upstream catalogue — are not yet supported by the install tooling.
If you want a new profile in the catalogue, open an RFC.

## Running the lint

`python3 tools/lint-profiles.py` enforces three structural invariants before a profile can ship:

- **Scope-homogeneous:** every pack allows the profile's declared scope.
- **Dependency-complete:** all pack dependencies appear in the manifest.
- **Deps-first ordered:** dependencies appear before the packs that depend on them.

Run it before opening a PR against any profile manifest.
The lint is fast and the output names exactly which invariant failed and which pack caused it.

## When a profile is the wrong answer

**Mixed scopes required.**
A profile that would need both user-scope and repo-scope packs cannot exist as a single manifest.
Design two profiles (one per scope), or reconsider whether the packs actually belong together.

**One-time install set.**
A profile for "install everything we might need for this migration" is not a habit.
Document the individual `agentbundle install` commands instead and note the context in a how-to.

**Transitive-dependency-only pack.**
If the only reason to list a pack in the profile is because another listed pack depends on it, the dependency is already declared in that pack's own manifest.
The profile only needs to list the top-level packs the persona explicitly wants — not every transitive dependency.
(The lint will catch if you miss a transitive dep, so err on the side of omitting it and let the lint tell you if it's needed.)

## See also

[Install a profile](./install-a-profile.md) — the user-facing install flow.
