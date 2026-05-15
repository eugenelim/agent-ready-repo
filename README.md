# agent-ready-repo

A repo template designed to be a place where AI coding agents can do their best work.

AI coding agents are getting good enough to do real engineering, and the work goes better when the repo is set up for them: a clear home for every kind of document, conventions that hold up as the project grows, and review steps that catch what agents typically miss. Most repos aren't built that way. This one is.

It fits any project — service, library, platform — and scales from solo developer up to a team of fifty without restructuring. For the thinking behind each piece, see [`docs/APPROACH.md`](docs/APPROACH.md).

---

**For evaluators**: below is the template scaffold an adopter inherits after running `bash tools/bootstrap.sh`. It shows the kinds of documents, conventions, and structure the template installs.

<!-- BOOTSTRAP_TEMPLATE_INTRO_END -->

# `<project-name>`

> One-line description of what this project does and who it's for.

## For humans

- **What this is:** see [`docs/CHARTER.md`](docs/CHARTER.md).
- **How users use it:** see [`docs/guides/`](docs/guides/) (Diátaxis-organized).
- **Where the product is heading:** see [`docs/product/roadmap.md`](docs/product/roadmap.md).
- **What changed recently:** see [`docs/product/changelog.md`](docs/product/changelog.md).
- **How the code is organized:** see [`docs/architecture/overview.md`](docs/architecture/overview.md).
- **How to contribute:** see [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## For agents (Claude Code, Cursor, Codex, Gemini CLI, Copilot)

Read [`AGENTS.md`](AGENTS.md) first. `CLAUDE.md` is a symlink to it. The
file is kept short on purpose — it points to deeper docs and skills that
load on demand.

## Quickstart

<!-- Replace with your project's actual install + run commands. -->

```bash
<install command>
<run command>
```

## Repository layout

```
.
├── AGENTS.md             # canonical agent context (read this first)
├── CLAUDE.md             # → AGENTS.md (symlink)
├── apps/                 # deployable applications        (delete if not used)
├── packages/             # shared libraries               (delete if not used)
├── tools/                # build, dev, ops tooling (incl. docs linter, Ralph harness)
├── docs/                 # all documentation
│   ├── CHARTER.md        # mission, scope, principles (one page)
│   ├── CONVENTIONS.md    # how we work in this repo
│   ├── adr/              # architecture decisions (frozen history)
│   ├── rfc/              # proposals (governance)
│   ├── specs/            # feature specs and plans (per-feature)
│   ├── architecture/     # current code structure (for contributors)
│   ├── product/          # roadmap, changelog (for maintainers)
│   ├── guides/           # user-facing docs (Diátaxis: tutorials/how-to/reference/explanation)
│   └── _templates/       # templates for adr / rfc / spec / plan
└── .claude/              # Claude Code skills, agents, commands
```

## License

<!--
This template is licensed under both MIT and Apache-2.0; you can pick either.
The default text below mirrors that. Keep it, change to a single license, or
replace entirely depending on what your derivative project chooses.
-->

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT License ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this project by you, as defined in the Apache-2.0 license,
shall be dual-licensed as above, without any additional terms or conditions.
