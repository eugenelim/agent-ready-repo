# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to this file.
> Cursor, Codex, Gemini CLI, and Copilot also read it (via their own discovery rules).
>
> Keep this file under ~200 lines. If you're tempted to add to it, ask first whether
> the content belongs in `docs/`, `.claude/skills/`, or a subdirectory `AGENTS.md`.

## What this repo is

<!-- ONE sentence. Replace this. -->
A monorepo for `<project-name>` — a `<one-line description of what it does and for whom>`.

The detailed map of what lives where is in [`docs/architecture/overview.md`](docs/architecture/overview.md).
**Read it before exploring.** It will save you 20 minutes of grep.

## Keeping changes minimal

Code is a liability, not an asset; the same principle unifies *Add a flag only when a second caller actually needs to differ* (next bullet) and *Dependencies are forever* in [§ Check before acting](#check-before-acting).

Scope each change precisely to the request.

### Non-negotiables

- **Surface assumptions before building.** Name them in PLAN's trio.
  The declined-pattern register in the `work-loop` skill
  names temptations; assumptions are different — call them out separately.
- **Stop and ask when requirements conflict.** Use the Surface verb
  defined in the `work-loop` skill — emit a
  short description and wait.
- **Push back when warranted.** Not a yes-machine. Disagreement goes in
  the PR description, not in silence.
- **Prefer the boring, obvious solution.** Cleverness is expensive; see
  the declined-pattern register in the `work-loop` skill.
- **Touch only what you're asked to touch.** See the rest of this section.

- **Limit the diff to what the request requires — extra changes hide
  the real one from review.** If the request needs it — or would ship
  broken without it — it's in scope, even discoveries you make
  mid-implementation.
- **Add a flag or option only when a second caller actually needs to
  differ.** Today's one caller is enough to define the shape.
- **Add docstrings and types to code the change actually touches.**
  Leave nearby untouched code as it is.
- **Validate at boundaries the request crosses** (user input, external
  APIs). Trust internal callers and framework guarantees.
- **Inline a single-use operation.** Extract a helper once a second
  caller actually appears.

When you defer something out of this PR — unrelated find or same-area
cleanup — note it in the PR description with a one-line reason.

## Source of truth

For each kind of decision, there is exactly one place it lives:

| Question                                  | Where it lives                       |
| ----------------------------------------- | ------------------------------------ |
| What is this project, and what's in/out of scope? | `docs/CHARTER.md`             |
| Why did we choose X over Y?               | `docs/adr/`     (Architecture Decision Records) |
| What should we change, and how?           | `docs/rfc/`     (Request For Comments) |
| What exactly does this feature do?        | `docs/specs/<feature>/spec.md`       |
| How will we build it, step by step?       | `docs/specs/<feature>/plan.md`       |
| How is the code organized today?          | `docs/architecture/`                 |
| What is the product doing today?          | `docs/product/` (roadmap, changelog) |
| How do users use the product?             | `docs/guides/` (Diátaxis: tutorials, how-to, reference, explanation) |
| How do agents do `<repeating task>`?      | `.claude/skills/<task>/SKILL.md`     |

If you can't find the answer in one of these places, **the answer doesn't
exist yet** — ask, or open an RFC. Don't guess. Lifecycle and mechanics
(living vs. frozen, ADR vs. RFC, etc.) live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## How we work

For anything beyond a one-line edit, follow the **plan → execute → verify →
review** loop. The mechanics — verification modes, gate sequence, iteration
cap, capture-learnings, specialist-reviewer pass — live in the
`work-loop` skill. Load it before
non-trivial work; that is the canonical source for *how* the loop runs.
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#how-we-do-non-trivial-work)
covers the *why*. Commits follow Conventional Commits — format and footer
rules are in [`CONVENTIONS.md § Commits`](docs/CONVENTIONS.md#commits).

Specs are validation gates, not write-once docs. If implementation diverges
from the spec, update the spec in the same PR — drift is a bug.

For unattended/AFK work, the [Ralph harness](tools/RALPH.md) runs the loop
in fresh sessions. Read it first; Ralph fits *some* tasks, not most.

## Commands you'll need

<!-- Keep this short. Detailed command reference goes in docs/. -->

```bash
<install command>           # one-time setup
<test command>              # run tests for the package you're in
<test all command>          # run all tests (slow — usually CI's job)
<lint command>              # lint + format check
<build command>             # produce build artifacts
```

## Code style

We don't list style rules here — the linter does that job better than prose can.
Run `<lint command>` and follow what it tells you. If something is genuinely
ambiguous to a linter (naming, file organization, error handling philosophy),
it's covered in [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Agent workflows

Use the generated skill list below when a task matches a named workflow.
<!-- agent-skills:start -->
- **adapt-to-project** — Use this skill to walk the adopter through the four classes of post-install change (substitution, .upstream companion merges, discovery + restructuring, within-layout consolidation). Triggers after installing a pack (the install→adapt chain nudges via session-start hook) or any time `<repo>/.adapt-install-marker.toml` / `~/.agent-ready/.adapt-install-marker.toml` is on disk. Walks both scopes' state files for Tier-2 detection; class-1 substitution shells out to `agentbundle adapt`; classes 2–4 write files directly under the per-scope path-jail.
- **add-credentialed-skill** — Use this skill when the user wants to author a new credentialed primitive — a skill that calls an authenticated external API on behalf of the user. Triggers on "add a credentialed skill", "new credentialed primitive", "wire up `<service>` API access". The skill walks the author through picking the primitive class (credentialed-cli vs. mcp-server), copying the matching `### Variant:` from `assets/credentialed-skill-SKILL.md`, declaring the schema, and importing the loader. Do NOT use for skills that just shell out to an already-credentialed binary the user has on PATH — those are not credentialed primitives. See `docs/specs/skill-secrets/spec.md` for the full architecture.
- **api-contract** — Use when generating an OpenAPI 3.1 API contract from requirements, user stories, or domain models. Applies 138 RESTful API rules as hard constraints to produce complete, validated YAML specs ready for code gen, test gen, mocks, and SDKs. Activate for tasks involving API design, REST contract authoring, or OpenAPI spec creation.
- **bug-fix** — Use this skill when the user wants to fix a bug — a deviation between current behavior and intended behavior in code that already exists. Triggers on "fix bug", "fix this bug", "diagnose and fix", "investigate this regression", "this is broken". Do NOT use for new features (use `new-spec`) or for refactors that don't fix incorrect behavior.
- **example-credentialed-skill** — Reference skill — do NOT auto-load. Authoring a new credentialed primitive belongs in `add-credentialed-skill`; this directory ships only as a runnable worked example for adopters who explicitly ask to *see* one. The skill carries a no-op `scripts/cli.py` calling a fictional `example` API via `agent_ready.credentials`, the canonical `references/creds-schema.toml` declaring `API_TOKEN` (secret) and `BASE_URL` (non-secret sibling), and the verbatim `### Security rules (non-negotiable)` block the credentialed-CLI lint pins. Read it; do not invoke it from production code.
- **file-to-markdown** — Convert documents and images to Markdown. Documents (PDF, DOCX, PPTX, XLSX, XLS) go through Docling text extraction (`scripts/convert.py`); images (PNG, JPG, JPEG, TIFF, BMP, WEBP, GIF) go through a two-pass sliding-window vision pipeline whose tiling and reconciliation are deterministic (`scripts/split_image.py` and `scripts/reconcile.py`). The agent's job is the per-tile vision read; tile dedup and ordering are handled by the script.
- **markdown-to-html** — Convert a Markdown file to a self-contained, styled HTML page (sticky header, sidebar nav, syntax-highlighted code, callout boxes, Mermaid diagrams, print-ready). Use when the user asks to render, convert, or export a `.md` file as a shareable HTML document — not for slides, presentations, or pitch decks. Rendering is deterministic via `marked` + `highlight.js`; the agent only invokes the script.
- **msg-to-markdown** — Convert Outlook .msg email files to Markdown, preserving email headers (From, To, CC, Date), body content, and attachment metadata. Use when the user wants to convert, read, or process a .msg email file into Markdown format.
- **new-adr** — Use this skill when the user asks to create, write, draft, or open a new ADR (architecture decision record). Triggers on phrases like "new ADR", "write an ADR for…", "record this decision", "let's ADR this". Do NOT use for RFCs (use `new-rfc`) or feature specs (use `new-spec`).
- **new-guide** — Use this skill to draft a new user-facing guide under `docs/guides/<quadrant>/<slug>.md` following the Diátaxis framework. Triggers on "write a guide for X", "new tutorial", "new how-to". Picks the quadrant (tutorials/how-to/reference/explanation) and applies the per-quadrant template.
- **new-package** — Use this skill when the user wants to scaffold a new package in the monorepo's `packages/` directory. Triggers on "new package", "create a package called…", "add a library for…". Don't use for new top-level directories (those need an RFC) or for new apps (which go in `apps/`, not `packages/`).
- **new-rfc** — Use this skill when the user asks to propose, draft, or open an RFC (request for comments). Triggers on "RFC", "propose a change to…", "let's get input on…", "draft a proposal". Do NOT use for already-decided things (use `new-adr`) or single-feature specs (use `new-spec`).
- **new-spec** — Use this skill when the user wants to start a new feature with a spec, or wants to write a spec for something they're about to build. Triggers on "new spec", "write a spec for X", "let's spec this out", "start a feature for…". Spec-driven development; the spec drives implementation. Do NOT use for cross-cutting proposals (use `new-rfc`) or recording decisions (use `new-adr`).
- **update-conventions** — Use this skill when the user wants to change `docs/CONVENTIONS.md` or `docs/CHARTER.md`. Triggers on "let's change the convention for…", "update the rules", "amend the charter", "change our principles". Conventions and charter changes go through RFC review, not direct PR.
- **work-loop** — Use this skill whenever you're implementing a non-trivial change — a feature, a multi-file bug fix, a refactor, a migration, a framework or dependency upgrade, a schema or API change, performance work, an infrastructure or build-system edit, or anything spec-driven. It enforces the project's plan → execute → self-review → fix loop with mechanical gates (lint, typecheck, tests) and adversarial review. Default to this skill for any task larger than a one-line edit.
<!-- agent-skills:end -->

## Specialist subagents

`.claude/agents/` contains sharp, differentiable lenses for diff review,
plus the executor used by `work-loop`'s supervisor mode. Pick the
reviewers the diff actually warrants; don't run all three by default.

- `adversarial-reviewer` — spec /
  plan / implementation drift; missing edge cases; scope creep. Default
  reviewer; runs after gates pass.
- `security-reviewer` — OWASP Top
  10 (web + LLM Apps) and STRIDE lens. Use when the diff touches auth,
  secrets, user input, deserialization, file/network I/O, dependencies,
  or LLM/agent code. Complements SAST/SCA scanners; does not replace them.
- `quality-engineer` — testability,
  observability, reliability, and maintainability lens. Also drafts
  contract or construction tests on request.
- `implementer` — single-task executor;
  `work-loop` dispatches one per task in supervisor mode. Not a
  reviewer; not selected by hand.

## Check before acting

- **Get user confirmation for destructive commands** (`rm -rf`,
  `git push --force`, dropping database tables) before running them.
- **Route substantive `docs/CHARTER.md` edits through an RFC.** Trivial
  fixes (typos, broken links) are fine as normal PRs.
- **Record new dependencies in the package's `AGENTS.md` or an ADR**
  before adding them. Dependencies are forever.
- **Grep to verify a function exists** before importing it. Imports
  that "look right" but aren't waste the time of everyone who hits the
  broken build.
- **Propose new top-level directories via RFC.** The structure is
  intentional.

### Excuses we don't accept

Rationalizations the agent hits *before* the work-loop loads — when it's
deciding whether to load it at all. The in-loop set lives in
the `work-loop` skill's *Anti-patterns* section.

| Excuse | What to do instead |
| --- | --- |
| "Small enough to not bother loading the work-loop." | Load `work-loop` and write its trio anyway — three sentences. The discipline is the point, not the length. |
| "I don't need a spec, I understand the task." | If it touches more than one file, run `new-spec`. The spec exists to surface what you don't know you don't know. |
| "I'll grep the codebase as I go." | Verify APIs *before* you start writing, not while you're writing — same rigor as the *Grep to verify a function exists* bullet above. |
| "I'll match the surrounding code's pattern." | Check [Source of truth](#source-of-truth) first; local style may already conflict with the canonical convention. |

## When this file is wrong

Flag drift in your PR — don't silently work around it. AGENTS.md vs. reality
drift is the biggest cause of agent quality decay. Substantive changes to
this file go through RFC; small fixes are normal PRs.

---

*Generated from the [`agent-ready-repo`](https://github.com/) template. See [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) for the full conventions, or [`docs/architecture/overview.md`](docs/architecture/overview.md) to start exploring.*
> Working on this repo specifically? See [`AGENTS.local.md`](AGENTS.local.md).
