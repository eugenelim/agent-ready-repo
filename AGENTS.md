# AGENTS.md

> **This is the canonical agent context file.** `CLAUDE.md` is a symlink to this file.
> Cursor, Codex, and Copilot also read it (via their own discovery rules); Gemini CLI
> reads it via the `context.fileName` bridge the `gemini` adapter writes to `.gemini/settings.json`.
>
> Keep this file under ~200 lines. If you're tempted to add to it, ask first whether
> the content belongs in `docs/`, a skill, or a subdirectory `AGENTS.md`.

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
  Leave nearby untouched code as it is — except under the
  bundled-fixes carve-out defined in the `work-loop` skill (same-area,
  same-concern, mechanical ride-alongs only; surplus still goes to
  follow-up).
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
| How do agents do `<repeating task>`?      | A skill file (`SKILL.md` with frontmatter); your IDE handles discovery |

If you can't find the answer in one of these places, **the answer doesn't
exist yet** — ask, or open an RFC. Don't guess. Lifecycle and mechanics
(living vs. frozen, ADR vs. RFC, etc.) live in
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## How we work

Skip `work-loop` only when a repository change is cosmetic, tightly local,
behavior-preserving, and obviously verifiable — a one-line authentication,
migration, production-config, or public-interface change is not trivial. For
every other repository change, use `work-loop` and follow its plan → execute →
verify → review loop. The skill is the canonical source for verification modes,
gate order, iteration limits, learning capture, and specialist-reviewer routing.
[`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#how-we-do-non-trivial-work)
covers the *why*. Commits follow Conventional Commits — format and footer
rules are in [`CONVENTIONS.md § Commits`](docs/CONVENTIONS.md#commits).

`work-loop` runs in **light mode** by default — a lean inline spec, a
single bounded adversarial pass, no state machine — and escalates to
**full mode** when the work trips a risk trigger:

<!-- risk-triggers:start — canonical wording lives here; copied verbatim
     into AGENTS.md, packs/core/seeds/AGENTS.md, and docs/CONVENTIONS.md.
     Keep all four byte-identical (grep-equality is an acceptance
     criterion of the work-loop-light-mode spec). -->
**Risk triggers — any one routes the work to full mode:**

- **Unfamiliar** — territory you don't know well.
- **Multi-person** — more than one person builds or reviews it.
- **Multi-feature or dependent tasks** — it decomposes a multi-feature
  brief, or its tasks depend on one another.
- **Compliance, governance, or security boundary** — it touches a
  compliance or governance surface, or a security boundary (auth,
  secrets, user input, deserialization, file or network I/O).
- **Structural or public-interface change** — it changes structure (a new
  module, layer, or boundary) or a public or published interface.
- **Destructive or irreversible operation** — it deletes data,
  force-pushes, drops tables, or otherwise can't be cleanly undone.
- **New dependency** — it adds a dependency.

No trigger fires → **light mode**.
<!-- risk-triggers:end -->

What each mode trims (and what full mode runs) lives in the `work-loop`
skill — the canonical source for *how* the loop runs.

Specs are validation gates, not write-once docs. If implementation diverges
from the spec, update the spec in the same PR — drift is a bug.

For unattended/AFK work, some agents offer a fresh-session-per-iteration
mode driven from files. Use your agent's native facility; it fits *some*
tasks, not most — the work-loop skill covers when it's the right tool.

## Commands you'll need

<!-- Keep this short. Detailed command reference goes in docs/. -->

```bash
pip install -e packages/agentbundle 'packages/credbroker[crypto]' ruff mypy pytest  # one-time
pip install -r tools/requirements.txt          # jsonschema, pyyaml — one-time
python3 -m pytest packages/<pkg>/tests/ -q    # test the package you're editing
make lint-ruff                                 # lint + format
make build-self                               # sync projected files after touching packs/
make build-check                              # agentbundle verify + repo policy gates + SAST
SKIP_SAST=1 make build-check                 # same, minus SAST (fast; for non-SAST changes)
make ci                                       # full local CI: build-check + lint + test (Linux/macOS)
```

## Code style

We don't list style rules here — the linter does that job better than prose can.
Run `python3 tools/lint-ruff.py` and follow what it tells you. If something is genuinely
ambiguous to a linter (naming, file organization, error handling philosophy),
it's covered in [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Agent workflows

Use the generated skill list below when a task matches a named workflow.

## Specialist subagents

Specialist subagents — where your tool supports them — provide sharp,
differentiable lenses for diff review, plus the executor used by
`work-loop`'s supervisor mode. Pick the reviewers the diff actually
warrants; don't run all three by default.

- `adversarial-reviewer` — spec /
  plan / implementation drift; missing edge cases; scope creep. Default
  reviewer; runs after gates pass.
- `security-reviewer` — multi-framework (OWASP 2025, ASVS, STRIDE +
  LINDDUN) lens, run at spec stage and on the diff. Use when the change
  touches auth, secrets, user input, deserialization, file/network I/O,
  dependencies, or LLM/agent code. Complements SAST/SCA scanners; does not
  replace them. **Blessed security helpers** (customize per repo): list your
  sanctioned helpers per boundary — secrets broker, path-confinement,
  SSRF-guarded fetch client — so it flags rolled-its-own bypass; absent a
  list it infers from the codebase.
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
| "Low-risk, so I'll skip the work-loop." | Load `work-loop` and write its trio anyway — light mode is lean, not absent. The discipline is the point, not the length. |
| "I don't need a spec, I understand the task." | Light mode still writes a lean inline spec; if any risk trigger fires, run full `new-spec` first. The spec exists to surface what you don't know you don't know. |
| "I'll grep the codebase as I go." | Verify APIs *before* you start writing, not while you're writing — same rigor as the *Grep to verify a function exists* bullet above. |
| "I'll match the surrounding code's pattern." | Check [Source of truth](#source-of-truth) first; local style may already conflict with the canonical convention. |

## Privacy

**Never commit personal information to any file in this repo.** This includes:
- Real names, email addresses, usernames, or account identifiers
- Org-specific domains, subdomains, or employer hostnames
- AAD/UUID identifiers tied to real people
- Device names, profile paths, or user-specific filesystem paths
- Names of personal service providers or platforms that identify account relationships

Use generic placeholders everywhere: `user@example.com`, `colleague@example.com`,
`Example User`, `https://mail.yourorg.com/`, `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`,
`example-service`, `[service type]`.

**This rule covers all git artifacts** — code, comments, docs, specs, commit messages,
PR titles, PR bodies, and PR comments are permanent record. Never use real service or
vendor names as examples; use `example-service` or `[service type]` instead. When
authoring governance docs (ADRs, RFCs, specs), GitHub handles used for author/decider
fields are not PII — they are public project identifiers. Do not infer from session context.

## Guide trees

| Tree | Audience | Ships? |
|---|---|---|
| `docs/guides/` | Repo maintainers — internal tooling, CLI workflows, repo how-tos. | No |
| `guides/` | Adopters — `guides/_shared/{quadrant}/`; pack-specific in `guides/<pack>/{quadrant}/`. | Yes |

New user-facing guides → `guides/_shared/how-to/` (or the owning pack's subtree).
New maintainer guides → `docs/guides/`. The `author-product-docs` skill routes by audience automatically.

## AGENTS.md line caps

CI enforces: root `AGENTS.md` ≤ 250 lines; subdirectory `AGENTS.md` ≤ 150 lines. Exceeding the cap
blocks CI. Length equals token cost.

## New tool scripts: Python, not bash

New additions to `tools/` must be pure-stdlib Python (`.py`). Existing `.sh` files stay; the rule
applies forward. Path triggers in `.github/workflows/docs.yml` must match `python3 <script>`.

## When this file is wrong

Flag drift in your PR — don't silently work around it. AGENTS.md vs. reality
drift is the biggest cause of agent quality decay. Substantive changes to
this file go through RFC; small fixes are normal PRs.

> Working on this repo specifically? See [`AGENTS.local.md`](AGENTS.local.md).
