# Surface discovery

What a product is decides which reference pages it needs and how to check them.
Find the surface from the repository before you choose an artifact. A repository
can ship more than one surface — a library with a CLI, or an app with a public
API. Document each surface the reader touches, and lead with the one the
README's first example uses. If the README has no example, lead with the surface
the install instructions or the docs landing page start with.

Each section names four things:

- **Evidence:** what in the repository reveals the surface.
- **Canonical sources:** what to read before writing a claim about it.
- **Reference artifact:** the look-up page this surface needs.
- **Verification:** the check that proves the docs match what ships.

These are not page templates. Page shape comes from
[`page-contracts.md`](page-contracts.md); this file only tells you where the
truth lives and how to test it.

When no section fits, say which evidence you found, name the closest surface,
and ask once before drafting.

## Library or SDK

Evidence: a package manifest (`pyproject.toml`, `package.json` with `main` or
`exports`, `Cargo.toml`, `go.mod`, a `.gemspec`, a `.csproj`), public export
lists (`__all__`, `pub` items, index barrels), and typed signatures.

Canonical sources: the public API in source, its docstrings or doc comments,
the examples directory, and the package's version and supported runtimes in
the manifest.

Reference artifact: API reference generated from doc comments where the
repository already generates it; a hand-written reference page only for what
the generator does not cover. Each entry states inputs, return value, errors,
and one example.

Verification: run the examples. Use the repository's doc-test runner when one
exists (Python `doctest`, Sphinx doctest, `cargo test` for rustdoc, a Markdown
code-block test); otherwise run each snippet once and record the output.

## CLI

Evidence: an argument-parser definition (argparse, click, typer, clap, cobra,
commander, yargs), a `bin` entry in `package.json`, `[project.scripts]` in
`pyproject.toml`, a `cmd/` or `bin/` directory, or a man page source.

Canonical sources: the parser definitions — they are the truth for commands,
flags, defaults, and exit codes — plus the help text they produce.

Reference artifact: a command reference with one entry per command or
subcommand: synopsis, flags with defaults, exit codes, and an example. Help
output leads with examples, and every subcommand answers `--help`.

Verification: run `<tool> --help` and `<tool> <subcommand> --help` and compare
them with the reference. Run every documented example command in a scratch
directory and record the exit code.

When help text is hand-written separately from the parser, the parser is the
truth and a mismatch is a finding.

## HTTP or RPC API

Evidence: an OpenAPI, AsyncAPI, GraphQL, or `.proto` file; route definitions
(decorators, router files, controller classes); an API gateway configuration.

Canonical sources: the contract file first, then the route handlers for
behavior the contract does not state — auth, error bodies, rate limits,
pagination, idempotency.

Reference artifact: one entry per endpoint or method — request, response,
errors, auth scope, and limits — generated from the contract where the
repository already generates it. A separate page covers authentication, errors,
and pagination once, so endpoint entries can link to it.

Verification: compare every documented endpoint, field, and status code with
the contract file. Where a test or mock server exists, run one documented
request against it and record the response.

## App (web, desktop, or mobile)

Evidence: a UI route or page tree, an app manifest (`Info.plist`,
`AndroidManifest.xml`, an Electron or Tauri config, a web app manifest), an
end-to-end test suite, and UI string or translation files.

Canonical sources: the screens and flows in source, the UI strings as users see
them, and the end-to-end tests, which show the supported paths.

Reference artifact: task-based help for the core flows; a settings reference
when the app has settings a user changes. Use the exact UI labels from the
string files.

Verification: walk each documented task in the running app or its end-to-end
test and record where the steps diverge. Use a screenshot only where the image
is the instruction, and mark each one with the release it was taken from.

## Service

Evidence: a `Dockerfile`, Helm chart, Terraform or other deploy files, a config
schema (JSON Schema, a typed settings class), environment-variable reads, health
or readiness endpoints, and alert rules.

Canonical sources: the config schema and its defaults, the environment
variables the code reads, the deploy files, and the health endpoints.

Reference artifact: a configuration reference — every setting with its type,
default, and effect — plus an install or deploy guide. Operator runbooks for
incidents are maintainer material; route them to the repository's internal
docs, not the user guides.

Verification: compare every documented setting and default with the schema and
the code that reads it. Where a local run is possible, start the service with
the documented minimal config and record the health check.

## Plugin or extension

Evidence: an extension manifest with a contribution block — a VS Code
`package.json` `contributes` section, a browser extension `manifest.json`, a
plugin descriptor for a host application, or a package that a host framework
loads by configuration.

Canonical sources: the manifest's declared commands, settings, permissions, and
activation rules, and the host's version range.

Reference artifact: one entry per contributed command and setting, plus the
permissions the plugin asks for and why.

Verification: compare the reference with the manifest's contribution block,
entry by entry. Install the plugin in the host where possible and run one
documented command.

## Framework or extension points

Evidence: documented extension base classes, interfaces, or protocols; the
registration or loader code that finds user modules; config keys that load user
modules or npm or pip plugins; scaffolding commands. This covers products whose
users write code that the product loads or calls — framework modules, routes,
workflows, hooks, admin widgets — and a library's public extension points such
as custom transports, auth classes, event hooks, and middleware.

Canonical sources: the interface or base-class definitions, the loader and
registration code, and the default configuration that names what loads.

Reference artifact: one entry per extension point — its contract (interface),
when it is called in the lifecycle, how to register it, and a minimal example.

Verification: compare each entry with the interface definitions and the
loader or registration code. Run the minimal example where a host can load it.

## Agent-context pack

Evidence: a pack or plugin manifest for an agent host (`pack.toml`,
`.claude-plugin/plugin.json`), `SKILL.md` files, agent definitions, commands,
or hooks. Count it only when the pack ships to users (a published manifest or
install docs). Agent files that guide the repository's own maintainers are
maintainer material, not a product surface.

Canonical sources: the manifest for machine facts (name, version, scope,
dependencies), each `SKILL.md` for modes, inputs, outputs, and what it reads or
writes, and any journey file the pack keeps.

Reference artifact: the README's starter prompts plus a skill reference — each
skill's purpose, the request that starts it, what it reads, what it may change,
and the decisions it leaves to the user. Machine facts stay in the manifest.

Verification: read each skill's source before stating what it does. Where
possible, start a session with the pack installed and send the README's first
starter prompt; record whether the expected skill activates.
