---
title: "How to ship your organization's standard stack as a reusable pack"
summary: Package organizational architecture, conventions, and framework knowledge into a reusable pack and one-command profile.
pack: _shared
kind: how-to
---

# How to ship your organization's standard stack as a reusable pack

**Use this when:** You want every team in your organization to start from the same architecture, conventions, and internal framework knowledge, installed in one command.
**Prerequisites:** A forked catalogue your organization owns, your real stack documented, and a chosen pack name; see "Before you start".
**Result:** A distributable org-stack pack with organization-owned standards, optional root or scoped guidance deltas, framework-library skills, and a one-command profile install.

> "Help me package our backend standards as an organization-owned stack pack.
> Preserve the files we already use, and route backend-only commands from the
> backend subtree."

This guide is for a platform or tooling lead who wants every team in the
organization to start from the same golden path — your real reference
architecture, your conventions, and the agent knowledge of your internal
frameworks — installed in one command. You build that as an **org-stack pack**:
an ordinary pack composed entirely of primitives that already exist, distributed
from a fork of this catalogue that your organization owns outright.

It assumes you already know how packs and profiles install (see
[install a profile](install-a-profile.md)) and have authored a skill before
(see [author a skill](author-a-skill.md)). Nothing here adds new machinery —
you are composing seeds, framework-library skills, a profile, and the
editable-install path that already ship.

This walkthrough reads your existing standards and creates files in the
organization-owned catalogue fork. It does not rewrite an adopter repository.
Installation may preserve a colliding seed as a companion; the approval-gated
[adapt to project](../../core/how-to/adapt-to-project.md) workflow reconciles
that content afterward.

If you're standardizing one repository, you do not need a pack. Keep its
architecture and contribution sources where they already live and let
`adapt-to-project` route them from root or scoped `AGENTS.md`. A pack earns its
cost when two or more repositories share the same golden path.

## Before you start

You need:

- **A fork of this catalogue that your organization owns.** The org-stack model
  is a *detached* fork: your teams install from your clone, with no runtime or
  package dependency on the upstream catalogue. The
  [editable-install route](install-agentbundle-from-clone.md) is how that clone
  becomes the install source.
- **Your real stack written down somewhere** — the runtimes and platforms you
  deploy to, the load-bearing framework and library choices, where your
  verification tooling lives. You're going to bake this into a seed, so have it
  to hand.
- **A pack name.** This guide uses `acme-stack` for the pack and
  `acme-golden-path` for the profile throughout; substitute your own.

## Steps

1. **Create the pack skeleton.** A pack is a directory under `packs/`. Copy a
   first-party pack's layout as a starting point, then strip it down to the
   three things an org-stack pack carries — seeds, framework skills, and a
   manifest:

   ```
   packs/acme-stack/
   ├── pack.toml                       # the manifest
   ├── .apm/skills/                    # framework-library skills (step 3)
   └── seeds/                          # organization-owned standards (step 2)
       └── docs/standards/backend.md   # example; use your established path
   ```

   In `pack.toml`, declare the pack at **repo scope** and make it depend on your
   forked `core` — the org pack adds your stack on top of the core workflow, it
   doesn't replace it:

   ```toml
   [pack]
   name = "acme-stack"
   version = "0.1.0"
   description = "Acme's standard stack: reference architecture, conventions, and internal-framework skills."

   [pack.adapter-contract]
   version = "0.8"

   [pack.install]
   default-scope = "repo"
   allowed-scopes = ["repo"]

   [[pack.dependencies.required]]
   catalogue = "<catalogue>"
   pack = "core"
   version = "^0.1"
   ```

   Copy the full field set (licence, links, maintainers) from a first-party
   manifest like `packs/governance-extras/pack.toml` — the four tables above are
   the load-bearing ones: the scope this guide assumes, and the `core` dependency
   the profile in step 4 relies on.

   **Do not copy the `lint-seeds = true` line.** First-party scaffold packs
   carry it because their seeds must stay placeholder-shaped; yours ship the
   opposite — real instance content. Omitting the flag is what leaves your pack
   unenforced by `lint-catalogue-seeds`, by construction. Step 5 covers why this
   matters.

2. **Ship standards in the locations your organization owns.** Use the same
   paths and terminology that teams already recognize. A repository using
   `ARCHITECTURE.md`, `engineering/decisions/`, or
   `docs/standards/backend.md` does not need a duplicate
   `docs/architecture/reference.md`. When no equivalent architecture source
   exists, you may fill the core pack's reference template and adopt its path as
   an organization default.

   Whichever source you choose, record the coordinates the work-loop needs:

   - managed runtimes and deployment platforms;
   - load-bearing framework or library contracts, such as entrypoints, required
     base classes, annotations, factories, or registration paths;
   - verification tooling: build, test, lint, deploy, smoke, teardown, and test
     data commands where applicable.

   Contribute agent guidance according to scope:

   - **Repository-wide:** ship a small `seeds/AGENTS.md` delta that links the
     organization-owned sources. Do not copy the core scaffold. If installation
     preserves it as `AGENTS.upstream.md`, `adapt-to-project` proposes a
     selective merge into the existing conventional sections; it never uses raw
     concatenation.
   - **One stable subtree:** when every adopter uses the same subtree, ship a
     delta-only scoped `AGENTS.md` there with only the relevant development,
     build/test, and convention guidance. If repository layouts differ, do not
     guess the folder; let the doctor offer a scoped file after discovery.
   - **Existing contributor guidance:** link the repository's root
     `CONTRIBUTING.md` or equivalent. Put action-changing directory deltas in
     the relevant scoped `AGENTS.md`.

   Compatible links from core, the org pack, and the adopter fold into one
   section by concern even when their source headings differ. Conflicting
   sources stay attributed and require a maintainer decision.

3. **Add a framework-library skill for each internal framework.** This is the
   detect target the work-loop's EXECUTE contract-grounding gate looks for when
   an agent generates code against one of your frameworks. Without it, the agent
   confirms a symbol *exists* but has to guess its behavioral contract — the
   versioned signature, the required call order, the deprecation. With it, the
   agent consults and cites the real contract.

   Author one ordinary skill per framework under
   `packs/acme-stack/.apm/skills/<framework>/SKILL.md` — follow
   [author a skill](author-a-skill.md). The model auto-activates it by
   description-match, so write the `description` to fire on the names and tasks
   your framework actually shows up under:

   ```yaml
   ---
   name: acme-rpc
   description: >-
     Authoritative contract for Acme's internal acme-rpc framework. Use whenever
     generating, reviewing, or debugging code that imports acme_rpc — service
     definitions, the @rpc_method decorator, the AcmeService base class, the
     client retry contract. Covers the call-order and config-loading rules that
     a bare grep for a symbol won't reveal.
   ---
   ```

   Put the load-bearing contract in the body: the signatures, the call-order
   constraints, the version-specific behavior. Keep it to what an agent can't
   recover by reading the symbol — that's what earns the skill its place.

4. **Wire one-command install with a repo-scope profile.** A profile bundles the
   packs a team should install together, in dependency-first order. Create
   `profiles/acme-golden-path.toml` listing your forked `core` first, then your
   org pack:

   ```toml
   scope = "repo"
   description = "Acme's golden path: the core workflow plus Acme's standard stack."

   [[packs]]
   pack = "core"

   [[packs]]
   pack = "acme-stack"
   ```

   `core` first matters — `acme-stack` depends on it, and a profile installs in
   the order you list. Now a team gets the whole golden path with:

   ```bash
   agentbundle install --profile acme-golden-path <your-clone>
   ```

5. **Distribute from your own detached fork.** Your teams install from your
   clone, never from upstream. Two pieces make that clean:

   - **Blank the packaged default source** so a stray `agentbundle install` with
     no catalogue argument can't silently reach upstream. In your fork, blank the
     `source` value in
     `packages/agentbundle/agentbundle/_data/install-defaults.toml` (or delete
     the file). The explicit-argument, user-config, and editable-clone
     resolution layers still work — only the upstream fallback is gone.
   - **Use the editable install.** Each team clones your fork and runs
     `python -m pip install -e packages/agentbundle/` once (see
     [install from a clone](install-agentbundle-from-clone.md)). After that,
     `agentbundle` resolves the catalogue source to *their clone of your fork*,
     so the install command needs no catalogue argument:

     ```bash
     agentbundle install --profile acme-golden-path
     ```

   Because the fork is detached, an installed org pack has no upstream
   dependency. The cost is yours to own: pulling improvements from upstream is a
   deliberate re-sync of your fork, not an automatic update.

## Variations

Real rollouts branch. Cover the cases you're likely to hit:

- **A user-scope skill toolkit instead of a repo golden path:** if what you're
  standardizing is a *role's* portable skills rather than a repo's architecture,
  ship a user-scope pack and a user-scope profile (like `solution-architect`),
  not the repo-scope seeds shape above. Seeds are a repo-scope concern.
- **Multiple stacks under one org:** if teams run genuinely different stacks
  (a Go services stack and a data-platform stack, say), ship one org pack per
  stack and one profile per stack, rather than one pack that tries to cover
  both. A profile is cheap; an over-broad standards document that fits no team
  is not.
- **You only need framework skills, no architecture seed yet:** ship the
  `.apm/skills/<framework>/` skills and skip the `seeds/` directory entirely.
  The pack is still valid; add organization-owned standards when the golden
  path is real enough to hold a pull request to.

## Common pitfalls

- **The seed lint rejects your filled-in standards** — you copied
  `lint-seeds = true` from a first-party `pack.toml`. Delete that line.
  `lint-catalogue-seeds` enforces a placeholder-only contract, which is the
  inverse of what your pack ships; org packs opt out by simply not declaring the
  flag.
- **`acme-stack` installs before `core` and fails its dependency check** — your
  profile lists the packs in the wrong order, or omits `core`. List `core`
  first; a profile installs in declaration order.
- **`agentbundle install` reaches upstream instead of your fork** — you didn't
  blank `install-defaults.toml`, or you ran a snapshot `pip install` instead of
  the editable `-e` one. Re-check both pieces in step 5; the editable install is
  what makes the no-argument install resolve to your clone.
- **A framework skill never activates** — its `description` doesn't name what the
  reader's code or task actually looks like. The model selects skills by
  description-match; write the trigger in the vocabulary your framework appears
  under, not in abstractions.
- **Your filled-in seeds drift from your real stack** — the stack moves, the seed
  lies, and the work-loop grounds on stale coordinates. The preflight treats a
  recorded value as a *seed for* live oracle acquisition, not a replacement, so a
  contradiction surfaces as drift rather than silently misleading — but you still
  own keeping the seed honest.

## See also

- [How to install a curated set of packs in one command](install-a-profile.md) —
  the profile install your teams run.
- [How to install `agentbundle` from a clone](install-agentbundle-from-clone.md) —
  the editable-install path your detached fork distributes through.
- [How to author a skill](author-a-skill.md) — for the framework-library skills
  in step 3.
- [The pack catalogue](../explanation/pack-catalogue.md) — for *why* the
  catalogue is packs-and-profiles and what the two-scope model means.
