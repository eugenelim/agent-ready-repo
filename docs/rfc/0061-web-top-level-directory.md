# RFC-0061: Add `web/` top-level directory

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-16
- **Date closed:** 2026-07-16
- **Decision weight:** standard
- **Related:** [platform-site spec](../specs/platform-site/spec.md), [platform-site plan](../specs/platform-site/plan.md); AGENTS.md § "Check before acting" ("Propose new top-level directories via RFC")

## Reviewer brief

- **Decision:** Approve `web/` as a new top-level directory — sibling to `site/` — housing the Astro marketing site, and accept the Node.js build dependency it carries.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - A new `web/` directory holds the Astro project (`package.json`, `astro.config.ts`, `src/`, `public/`).
  - The GitHub Pages build gains a Node.js step (`actions/setup-node` + `npm ci`/`npm run build`) that runs before the existing Python/MkDocs steps.
  - MkDocs `site_dir` moves from `built` to `../build/docs`; both builds emit into one `build/` artifact.
- **Affected surface:** repo structure (one new top-level dir), `.github/workflows/pages.yml`, `site/mkdocs.yml`. No pack (a *pack* is a bundled set of agent skills/subagents this repo ships to adopters), no published `agentbundle`/`credbroker` interface (the two pip packages the repo publishes), no adopter-facing primitive.
- **Stakes:** reversible — reverting the PR (which removes `web/`, restores `site_dir: built`, and reverts the Node build + upload-path steps in `pages.yml`) returns the repo to the prior MkDocs-only deploy.
- **Review focus:** (1) that a Node build toolchain for our own marketing site does not violate the charter's "not a framework that picks your tech stack" principle; (2) that a single-package (not root-monorepo) JS topology is the right call.
- **Not in scope:** homepage content/aesthetics (owned by the platform-site spec + design docs), adopter-facing tooling, any change to what packs prescribe.

## The ask

- **Recommendation (BLUF — bottom line up front):** Approve a new top-level `web/` directory for the Astro marketing site, built as a single npm package (`npm --prefix web`), deployed into the existing single GitHub Pages origin alongside MkDocs. This RFC exists solely to satisfy AGENTS.md's rule that new top-level directories are proposed via RFC before the first commit; the marketing site's content, aesthetics, and phasing are already defined in the [platform-site spec](../specs/platform-site/spec.md) (Status: Implementing; user-confirmed 2026-07-16).
- **Why now (SCQA — situation, complication, question):**
  - *Situation:* The repo documents itself through a MkDocs reference site in `site/`, served at the GitHub Pages root. (The repo is a *catalogue* — a curated library of agent packs — and this reference site is its current web surface.)
  - *Complication:* The platform-site spec adds a marketing anchor at `/` that MkDocs Material cannot express within its theme constraints (display-scale type, alternating dark/light bands, full-bleed sections, CSS-only interactive components). It requires a static-site generator with full template freedom — Astro — which needs a home in the repo.
  - *Question:* Where does the Astro project live, how is it built and deployed alongside MkDocs, and is its Node.js dependency acceptable?
- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | Where does the Astro marketing site live? | New top-level `web/`, sibling to `site/` | Mirrors the existing `site/` (MkDocs) and `packages/` (Python) sibling-per-toolchain pattern; keeps the JS toolchain self-contained | this review | Confirm the new top-level directory |
  | D2 | JS project topology? | Single package built via `npm --prefix web` | Only one JS package exists; a root monorepo workspace adds a root `package.json` and tooling for no present benefit | this review | Confirm single-package over root workspace |
  | D3 | Is the Node.js build dependency acceptable? | Yes — build-time only, for our own site | The charter's tech-stack neutrality governs what we *prescribe to adopters*, not our own build infra (which already picks Python/MkDocs) | this review | Rule that this does not breach the charter |

## Problem & goals

The platform-site spec establishes a marketing homepage as the catalogue's anchor. The design system it selects (Option B — "Alternating Conviction", the spec's name for a dark-hero / light-content / dark-closer band layout) demands surface control that MkDocs Material's theme does not offer: a dark full-bleed hero, alternating content bands, display-scale type, and CSS-only interactive components. Astro is the generator the spec selects; on acceptance, the SSG-selection trade-off and the one-Pages-deploy architecture are recorded in an ADR — Architecture Decision Record — so the cross-cutting toolchain choice has a durable home (see Follow-on artifacts). AGENTS.md § "Check before acting" requires: *"Propose new top-level directories via RFC. The structure is intentional."* This RFC is that proposal.

**Goals.**

- Give the Astro project an unambiguous, conventional home in the repo.
- Keep the JS toolchain isolated so it does not perturb the Python packages or the MkDocs build.
- Preserve one GitHub Pages deploy (Astro at `/`, MkDocs at `/docs/`) — no second origin.
- Keep the addition reversible.

**Non-goals.**

- *Restructuring `site/`.* MkDocs stays where it is; only its `site_dir` output target moves so both builds share one artifact.
- *A repo-wide JavaScript/monorepo posture.* This does not make the repo a JS monorepo; it adds one isolated JS package. If a second JS package ever appears, revisiting a root workspace is a separate decision.
- *Prescribing Astro (or any web framework) to adopters.* `web/` is this repo's own marketing surface, not a shipped primitive or template.

## Proposal

Add `web/` as a top-level directory, sibling to `site/`:

```
web/
├── astro.config.ts        # outDir: '../build'
├── package.json           # pinned Astro version; single package, no workspaces
├── package-lock.json
├── src/                   # components, pages, styles, content
└── public/
```

**Build & deploy pipeline (one Pages origin, one artifact).** Astro's `astro build` cleans its `outDir` on every run, so it must run *first*; MkDocs writes only into `build/docs/` *after* Astro has finished:

1. `actions/setup-node@v4` → `npm ci --prefix web` → `npm run build --prefix web` (emits Astro into `build/`).
2. Existing Python steps: `pip install` → `python tools/build-site.py` → `mkdocs build` (emits into `build/docs/` via `site_dir: ../build/docs`).
3. `actions/upload-pages-artifact` uploads `./build`; `actions/deploy-pages` deploys it (unchanged mechanism, new path).

**Config changes:** `site/mkdocs.yml` `site_dir: built` → `site_dir: ../build/docs`. The Astro version is pinned in `web/package.json` (not a floating range) to keep CI reproducible.

**Reversibility.** Revert the PR: deleting `web/`, restoring `site_dir: built`, and reverting the workflow returns the repo to the MkDocs-only deploy.

## Options considered

**Axis: where the marketing UI's toolchain lives relative to the existing repo structure** (a new top-level dir · under an existing top-level dir · a wholly separate origin), plus do-nothing. These exhaust the placement choices: a directory is either new-and-top-level, nested inside one of the existing top-level dirs (`site/` or `packages/`), or outside the repo entirely.

| Option | What it is | Trade-off | Recommended |
| --- | --- | --- | --- |
| **A. New top-level `web/`** | Astro in its own top-level dir, sibling to `site/` | + Matches the existing one-dir-per-toolchain pattern (`site/` MkDocs, `packages/` Python); clean isolation. − Requires this RFC (an intentional cost, not a real one). | ★ |
| B. Nest under `site/` (e.g. `site/web/`) | Astro inside the MkDocs directory | + No new top-level dir. − Conflates two independent toolchains and build lifecycles under one dir named for MkDocs; `site/` stops meaning "the docs site". | |
| C. Nest under `packages/` (e.g. `packages/web/`) | Astro inside the existing sub-projects dir | + No new top-level dir; `packages/` is the repo's literal sub-projects home. − `packages/` is by convention Python sub-projects (`agentbundle` and `credbroker` publish to PyPI; `_example` is the scaffold template) sharing one packaging/versioning discipline; a non-published static-site build artifact is a category mismatch that erodes what `packages/` means. | |
| D. Express marketing within MkDocs only (do-nothing on new tooling) | Push the marketing homepage into MkDocs Material overrides/CSS | + Zero new dependency. − Cannot achieve the specified design (full-bleed hero, alternating bands, display type, CSS-only components) within the theme; fails the spec. Cost of delay: the anchor page the spec is built around never ships. | |
| E. Separate repo / separate Pages deploy | Marketing site in its own repo and origin | + Total isolation. − Two deploys, split content ownership, cross-origin cross-links; the spec's Boundaries section explicitly forbids separate deployments. | |

**Prior art for A** — the repo already keeps one directory per toolchain: `site/` (MkDocs/Python) and `packages/` (Python distributions). A JS toolchain in its own `web/` is the same pattern, one level out. Astro's own docs recommend a dedicated project directory with `outDir` pointed wherever the host expects the artifact ([Astro configuration reference — `outDir`](https://docs.astro.build/en/reference/configuration-reference/#outdir)).

**On D2 (topology)** — sub-axis "how many JS packages does the build coordinate": single-package (`npm --prefix web`) vs. root npm workspace. npm's own guidance is that workspaces exist to manage *multiple* packages from one root ([npm workspaces docs](https://docs.npmjs.com/cli/v10/using-npm/workspaces)); with exactly one JS package, the single-package pattern is the simpler, prior-art-backed default. The plan already declines the root workspace for this reason.

## Risks & what would make this wrong

**Pre-mortem.**

- *MkDocs output wiped.* If MkDocs runs before Astro, `astro build`'s clean step deletes `build/docs/`. Mitigation: strict pipeline ordering (Astro first); the failure is loud (missing `/docs/` in the artifact) and caught on the first CI run.
- *Node version drift in CI.* First use of `actions/setup-node` for a build artifact. Mitigation: pin `node-version` in the workflow and the Astro version in `package.json`.
- *Scope creep into a JS monorepo.* Mitigation: Non-goal states this is one isolated package; a second JS package is a separate decision.

**Key assumptions (falsifiable).**

- Astro can emit into an arbitrary `outDir` (`../build`) without touching sibling output — *if false, the single-artifact model breaks.* (Confirmed below.)
- A build-time Node dependency for our own site does not breach the charter's tech-stack-neutrality principle — *if a reviewer reads the charter as governing our own build infra, this is wrong.* (Argued below.)

**Drawbacks.** A second language toolchain in CI (Node alongside Python) — more moving parts, a second dependency-update surface, longer CI. This is the real cost; it is accepted because the marketing anchor is a spec-defined deliverable and MkDocs cannot produce it.

## Evidence & prior art

- **Spike / de-risk result.** Riskiest assumption: a Node build dependency for our own marketing site violates the charter's *"Not a framework that picks your tech stack."* Resolved by reading the charter (`docs/CHARTER.md:43–46`): that principle scopes what the project *prescribes to adopters* ("the conventions are aware of architectural layers … but never of specific frameworks"), not the tooling we use to build our own artifacts. The repo already picks Python + MkDocs for `site/` without conflict. Astro in `web/` is the same class of choice — our own build infrastructure, not a shipped or prescribed primitive. Assumption does not hold against the RFC; no blocker.
- **Repo precedent.**
  - AGENTS.md § "Check before acting" mandates this RFC for the new top-level directory.
  - `site/` (MkDocs) and `packages/` (Python distributions) establish the one-directory-per-toolchain precedent A relies on.
  - `.github/workflows/pack-evals.yml:54` already runs `npm install -g @anthropic-ai/claude-code` in CI — Node is not new to CI; a Node-*built deploy artifact* (via `setup-node`) is the new part.
  - The [platform-site spec](../specs/platform-site/spec.md) (Status: Implementing; its Assumptions section records user confirmation 2026-07-16) already defines the marketing site, the Alternating Conviction aesthetic, the Astro-at-`/`-plus-MkDocs-at-`/docs/` architecture, and the build order — this RFC unblocks its Phase 1 build (tasks T2–T7 in the plan).
- **External prior art.**
  - [Astro configuration reference — `outDir`](https://docs.astro.build/en/reference/configuration-reference/#outdir) — Astro supports an arbitrary build output directory, confirming the `outDir: '../build'` single-artifact approach.
  - [npm workspaces documentation](https://docs.npmjs.com/cli/v10/using-npm/workspaces) — workspaces are for managing multiple packages from a root; a single package needs none, backing D2.

## Open questions

None. All three decisions carry recommendations grounded in repo precedent and the platform-site spec; the spike resolves the one live tension.

## Follow-on artifacts

On acceptance:

- **Spec:** [`docs/specs/platform-site/`](../specs/platform-site/) Phase 1 build (tasks T2–T7 in the plan) is unblocked.
- **ADR:** [ADR-0050](../adr/0050-astro-marketing-site-toolchain-and-deploy.md) records the cross-cutting toolchain + deploy decision — Astro chosen as the SSG (static-site generator), one GitHub Pages deploy with Astro at `/` and MkDocs at `/docs/`, and the Node.js/Astro build dependency this introduces. This is where a future maintainer asking "why Astro, and why is Node in CI?" looks; CONVENTIONS § 3 routes an accepted RFC's architectural decisions to an ADR, and AGENTS.md § "Check before acting" requires new dependencies recorded in an ADR (or the package's `AGENTS.md`) before they are added.
- **Dependency record:** create `web/AGENTS.md` when the Astro project is scaffolded (T2), naming the Node.js runtime + pinned Astro version, so the dependency is recorded in-package per the AGENTS.md convention — not left implicit in `package.json`.
- **Spec back-link:** add RFC-0061 to the platform-site spec's `Constrained by:` line (CONVENTIONS § 4 — specs cite the RFCs that constrain them).
- No `docs/CONVENTIONS.md` change — `web/` follows the existing one-dir-per-toolchain convention rather than adding a new one.
