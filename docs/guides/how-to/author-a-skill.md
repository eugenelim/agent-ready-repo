# How to author a skill

This guide collects the standards every skill in this catalogue follows
— the bundled packs and the skills you author in your own pack alike.
Some standards are checked by lint (called out inline, with the linter
as the authority); the rest are reviewer-enforced. It assumes you
already know what a skill is and when to add one
([`docs/CONVENTIONS.md`](../../CONVENTIONS.md) § Skills: you've done the
same multi-step thing three times, and you're not adding one
speculatively).

For the credential dimension — a skill that calls an authenticated API
or holds a token — read
[How to add a credentialed skill](add-a-credentialed-skill.md)
alongside this; that contract is separate and more specific.

## Before you start

You need a skill directory under `packs/<pack>/.apm/skills/<name>/` with
a `SKILL.md`, and — if it does real work — a `scripts/` helper.

## Frontmatter and description

Keep frontmatter to the keys the [agentskills.io](https://agentskills.io)
spec allows (`name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`) and put any project-specific data under the
`metadata:` escape hatch. The description is one sentence that names the
*trigger* ("Use when …"), not the implementation.

**The description must be a single-line scalar.** Folded/literal YAML
blocks (`>`, `|`) and continuation lines (an indented next line) parse as
valid YAML but break on some adapter targets — their downstream loaders
fail on a multi-line description even when the YAML itself is clean. For
the same reason, keep YAML structural characters out of an unquoted
value: a bare `: ` mid-description, a leading `#`/`&`/`*`/`[`, or
whitespace-then-`#` all change the parse. If you need any of those
characters, wrap the whole value in double quotes. Keep it under 1024
characters.

Don't memorize the exact rules from this page — run the linter, which is
the source of truth:

```bash
python3 tools/lint-skill-spec.py
python3 tools/lint-agent-artifacts.py
```

They check the key whitelist, description syntax, `allowed-tools` shape,
and `evals/`. (The CONVENTIONS rule applies: the linter does the style
job better than prose can.)

## Body structure

Use the section order the shipped skills share, so a reader always knows
where to look:

- `# <Skill> title` + a 2–3 sentence intro stating what it does **and
  what it doesn't**.
- `## When to Use` — the trigger conditions.
- `## Prerequisites` — tools, packages, sibling skills, credentials (see
  the tier ladder below).
- `## Instructions` / `## Procedure` — numbered steps with copy-paste
  commands. The agent *invokes* the script; it is not the script.
- `## Pitfalls` / `### Don't` — known failure modes and what not to do.
- `## Verification` — how the agent confirms it worked.

## Directory layout

A skill is a directory with `SKILL.md` plus four optional subdirectories
— and the linter (`tools/lint-skill-spec.py`) only blesses those four:

- `scripts/` — helper code the skill invokes (`python scripts/foo.py`).
  The skill body drives the script; it is not the script.
- `references/` — detailed material the agent loads **on demand**, not
  every time (schemas, per-branch strategies, long tables).
- `assets/` — templates and fixtures the skill copies or fills in
  (`assets/template.html`, `assets/state.json`).
- `evals/` — evaluation fixtures in the canonical
  `evals/evals.json` + `evals/files/<fixture>` layout.

Two rules the linter enforces, worth getting right the first time:

- **Keep files one level deep.** A reference to
  `scripts/a/b/c.py` warns — flatten it. (`evals/` keeps its own
  canonical nesting.)
- **Reference your own files skill-relative, sibling skills by name.**
  `scripts/foo.py` and `references/bar.md`, never
  `.claude/skills/<name>/...` or `packs/<pack>/.apm/skills/<name>/...`
  install-path prefixes; to point at another skill, name it
  (`the jira skill`), don't path into it.

Edit the **seed** under `packs/<pack>/.apm/skills/<name>/`, never the
projected copy under `.claude/skills/`; after any edit run
`make build-self` to regenerate the projection, then
`python3 tools/lint-skill-spec.py`.

## Progressive disclosure

`SKILL.md` is the always-loaded entry point; everything in `references/`
is pulled in only when the workflow reaches it. So keep `SKILL.md` lean
— the spec recommends under 500 lines, the linter warns past 500 and
errors past 1000 — and push depth into `references/` that the body links
to at the moment of need. `file-to-markdown` is the model: its body
routes to exactly one of five `references/strategy_*.md` files per run
("Pick one strategy and load its reference file … Do not load any other
strategy file unless you switch"), so the agent never carries four
irrelevant strategies in context. Reach for a reference file whenever a
section would otherwise bloat the body with detail only one branch
needs.

## Write scripts cross-platform

Skills run under every adapter and on every OS, including Windows, where
there's no guaranteed POSIX shell — PowerShell is the default and
git-bash may not be present. So:

- **New helper scripts are Python, not bash.** Invoke them as
  `python scripts/<name>.py` from the skill body — portable everywhere.
- **Detect tools with `shutil.which("<tool>")`, not `command -v`.**
  `command -v` is a POSIX-shell builtin that doesn't exist in PowerShell
  (`Get-Command` is the equivalent); a Python check resolves identically
  on macOS, Linux, and Windows.
- Prefer `pathlib`, `tempfile.gettempdir()`, and Python-level filtering
  over `grep`/`sed`/`find` and hardcoded `/tmp`. Declare an OS
  restriction only when the dependency is genuinely platform-bound.
- **Always pass `encoding="utf-8"`** to `read_text`/`write_text`/`open`
  for text. Windows defaults to CP1252 and silently corrupts non-ASCII
  Markdown/JSON/TOML otherwise.
- **`subprocess` uses list form, never `shell=True`,** and never shells
  out to `which`/`grep`/`find`/`sed`/`awk`/`make`/`bash` — use the
  Python equivalent.

## Dependencies: the three-tier policy

Any dependency outside the Python standard library — a CLI binary, a
pip/npm package, or a sibling skill — falls under one of three tiers.
**Tier 1 is mandatory and the default; Tier 2 is allowed but never the
default; Tier 3 is banned.**

**What counts as a dependency:** Python itself is the assumed runtime —
skills invoke `python scripts/...`, so a stdlib-only script declares
nothing. `pip`/`uv` ship with a Python install, so a pip-based Tier-2
install is low-risk (the manager is almost always there). `npm`/Node is
**not** a given — it's only present if the user installed Node — so an
npm-based skill detects `npm` (and Node) before relying on it, and a
Tier-2 npm install is gated on that detection. Prefer stdlib over a pip
dependency, and a pip dependency over an npm one, when you have the
choice.

### Tier 1 — declare, detect, fail clean (mandatory, default)

1. **Declare.** A `## Prerequisites` section names the tool, the minimum
   version if one matters, and the exact install command or link.
2. **Detect.** The first action of any workflow checks the dependency is
   present, before any real work — a `--check` verb on your helper
   script that uses `shutil.which("<tool>")` and exits `0` (present) /
   `2` (absent). (`shutil.which` finds *binaries*; probe a library
   package with an import / `require.resolve` instead — see the
   variations below.) Where a version floor matters, also parse
   `<tool> --version` and compare.
3. **Fail clean.** On absence, stop and emit a precise remediation
   string — the exact install command from `## Prerequisites`. Do not
   improvise around the missing tool (no hand-rolled fallback, no
   third-party web service).

[`mermaid-renderer`](../../../packs/converters/.apm/skills/mermaid-renderer/)
is the reference:

````markdown
## Prerequisites

The renderer shells out to `@mermaid-js/mermaid-cli`. Install once:

```bash
npm install -g @mermaid-js/mermaid-cli
```

### Step 1 — Verify `mmdc` is available

```bash
python scripts/render_mermaid.py --check
```

- Exit code 0 → `mmdc` is on `PATH`, proceed.
- Exit code 2 → not installed. Tell the user the install command above.
  Don't try to install it for them.
````

### Tier 2 — opt-in, gated, idempotent install (allowed, not default)

A skill may install a dependency for the user **only** when all of these
hold:

- the install is a **single, deterministic command**;
- it needs **no sudo / root**;
- it uses a package manager the user **demonstrably already has** —
  `uv`, `npm`, `pipx`, or `brew` *if detected* (detect the manager
  itself first; don't assume it).

When you install, the pattern is always **detect → install →
re-verify**, and you **pin the version** — never assume the install
succeeded:

```text
1. detect:    shutil.which("foo")  → present? done, no-op.
2. gate:      absent → ask the user; install only on explicit consent.
3. install:   npm install -g foo@1.2.3      (pinned, no sudo)
4. re-verify: shutil.which("foo")  → still absent? fail clean.
```

**Gated** means the user opts in: get explicit consent before installing
into their environment; don't install as a silent side effect of the
first run. **Idempotent** means re-running is safe — because you detect
first, an already-present dependency is a no-op.

### Tier 3 — banned

Never:

- **silently auto-install** anything (install without the user opting
  in);
- **assume sudo / root**, or run an install that needs it;
- **`curl … | bash`** (or any pipe-to-shell installer) without explicit
  consent;
- **assume PATH within the same session** — re-verify after an install
  rather than trusting that a just-installed binary is resolvable.

### Variations on Tier 1 detection

- **A pip/npm package, not a binary.** Probe presence with an import /
  `require.resolve`, not `shutil.which` (which finds binaries, not
  library packages); on absence, declare the install line and stop —
  [`file-to-markdown`](../../../packs/converters/.apm/skills/file-to-markdown/)
  is the detect-and-stop model. A skill that goes further and *installs*
  on consent is Tier 2, not Tier 1
  ([`markdown-to-html`](../../../packs/converters/.apm/skills/markdown-to-html/)).
- **A sibling skill.** Detect by invoking that skill's own `check` verb
  and reading its exit code; on failure, point the user at the sibling's
  setup rather than reaching into its internals
  ([`flow-metrics`](../../../packs/atlassian/.apm/skills/flow-metrics/),
  in the atlassian pack → `jira: check`).
- **A vendor CLI the user authenticated** (`gh`, `git`, `kubectl`).
  Presence detection still applies; the credential dimension is the
  `auth: cli` broker — see the credentialed-skill guide.

## What's enforced vs. recommended

Frontmatter and description rules are lint-enforced
(`tools/lint-skill-spec.py`, `tools/lint-agent-artifacts.py`);
credentialed-skill rules have their own lint. The body structure, the
cross-platform rules, and the three-tier dependency policy are
**reviewer-enforced conventions** — no gate checks them, so they live or
die in review. Hold the line there.

## See also

- [How to add a credentialed skill](add-a-credentialed-skill.md) — the
  separate contract for tokens, API auth, and the `auth: cli` broker.
- [`mermaid-renderer`](../../../packs/converters/.apm/skills/mermaid-renderer/)
  — the Tier-1 reference: `## Prerequisites` + a `shutil.which`
  `--check` verb + an explicit "don't auto-install" rule.
- [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) § Skills — when to add a
  skill at all (the three-times rule).
