---
title: "Catalogue authoring standards"
summary: "Routing table for every catalogue authoring standard: pack manifests, skill frontmatter, profile format, lint and verify commands, CI contract, and packaging."
pack: _shared
kind: reference
status: stable
---

# Catalogue authoring standards

Machine contracts in `contracts/` are normative. These guides explain how to use them.

Each section below names the authoritative contract and points to the guide that
explains it. When a guide and its contract disagree, the contract is right.

## Guide asides and quotations

Use a Starlight aside when a passage does work beyond the surrounding narrative.
Choose the type by what the reader needs to do with it:

| Type | Use it for |
| --- | --- |
| `note` | Scope, orientation, or background the reader must notice |
| `tip` | An optional technique that improves the result or route |
| `caution` | A pitfall, limitation, or recovery step with reversible consequences |
| `danger` | A risk of severe or irreversible harm |

Use only those four types. Keep the default visible title unless a specific title
helps the reader act. Put the complete guidance inside the directive:

```md
:::caution
Confirm the generated paths before replacing an existing projection.
:::
```

A blockquote has a different job: it preserves someone else's words or exact text
the reader must recognize, such as a prompt, transcript, sample response, or rubric
wording. Leave those passages as `>` blockquotes. Do not turn prose into a quotation
just to make it visually prominent, and do not turn genuine quoted wording into an
aside.

---

## 1. Catalogue manifest

**Contract:** `contracts/catalogue.schema.json`

- `guides/_shared/how-to/create-a-catalogue.md` — scaffold a new catalogue with
  `agentbundle catalogue init`.
- `guides/_shared/how-to/create-external-catalogue.md` — self-hosted or enterprise-deployed
  variant. (Available in the full guide library; not bundled in this scaffold.)

---

## 2. Pack manifest

**Contract:** `contracts/pack.schema.json`

The `pack.toml` file at the root of every pack. Required fields: `[pack]` with `name`
and `version`; `[pack.adapter-contract]` with `version`.

- [packs/README.md](../../../packs/README.md) — pack layout, versioning rules, lint commands.
- [packs/AGENTS.md](../../../packs/AGENTS.md) — agent-facing schema map and primary workflow.

### `[pack].description` — display copy

`[pack].description` is read by a **person** deciding whether to install: in a
marketplace browser, a catalogue listing, or CLI output. It is not read by the model.

That makes it a different artifact from a skill's or agent's `description`, which the
model reads to decide whether to **activate** the primitive. Length is load-bearing
there and shortening it degrades activation; per-target caps in
`contracts/target-vocab.toml` govern it. Do not carry habits from one to the other.

**Shape.** Open on the job the adopter accomplishes, in their words. Say what they
get. Then stop.

Beyond that, let the pack decide the shape. Some need one sentence:

> Write the OpenAPI or AsyncAPI contract before anyone writes a handler.

Others earn three:

> Ship it the way production will see it. Deploy to a throwaway environment, run
> the tests, read the telemetry, and go round again until it holds. Then it stops
> and asks, because the next step is the one you cannot undo.

**Do not run every description through one mould.** An earlier pass here applied a
single shape — verb-first sentence, then a comma-list of capabilities — to all
22 packs. The result measured as 20 of 22 at exactly two sentences, 14 with a
comma-list second sentence, four opening on the identical "Turn X into Y" frame.
Every fact was right and the set still read as machine-written, because uniform
rhythm and symmetrical construction are themselves the tell. Vary sentence count
and length to match what each pack actually is.

Reach for the concrete. A real thing the user says (`"convert this PDF to
Markdown"`), a real artifact (`a Google-style design doc`), or a real check
(`the empty state and the focus ring you forgot`) all beat an abstract capability
noun.

**Anti-patterns**, each of which has shipped here before:

| Anti-pattern | Instead |
| --- | --- |
| Opening with a component inventory (`Core: work-loop, new-spec, bug-fix, …`) | Lead with the outcome; the inventory belongs in the README |
| Repo-insider vocabulary (`forked-context`, `the grown-up successor to X`) | Words a first-time reader resolves without this repo |
| Cross-pack references (`co-installs with X`, `feeds Y's queue`) | Nothing that assumes another pack is known |
| Provenance name-drops (`(STORM, PRISMA, ACH, GRADE)`) | Name a framework only when the reader is buying it |
| Negative space (`no stack, no values tables, no pixel comps`) | Say what it does; the README can scope what it doesn't |
| Internal paths (`~/.agentbundle/bin/`) | Nothing an adopter cannot act on from a listing |

**Discoverability is carried elsewhere** — `[pack].keywords` and `[pack].categories`
— so prose does not need to be keyword-dense to stay findable.

There is no target-imposed length limit. `tools/lint-pack-descriptions.py` fails the
build past a deliberately loose backstop, which exists only to stop runaway drift (the
field once reached 1122 characters); it is not the quality bar. **This section is.** A
description inside the backstop can still be bad, and a length check cannot tell —
review against the shape and the table above.

---

## 3. Pack README standard

A pack README serves adopters, not contributors. It states the pack's intent and the
user journey it serves — not a skill inventory. See the `_example` pack for a template.

- [packs/_example/README.md](../../../packs/_example/README.md) — canonical example.

---

## 4. Pack layout

Three boundaries, each owned by a different thing:

- The **pack** is the ownership and test-execution boundary.
- `.apm/` is the **runtime export** boundary.
- A **skill** is the evaluation-fixture boundary.

```
packs/<pack>/
├── pack.toml
├── README.md
├── .apm/                          # runtime — projected into installed environments
│   └── skills/<skill>/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       ├── assets/
│       └── evals/                 # skill-local, projected with the skill
├── tests/                         # implementation verification — never projected
│   └── skills/<skill>/
└── seeds/                         # governance files projected to the repo root
```

Deterministic implementation tests live under `packs/<pack>/tests/`. Runtime
skill evals live under `.apm/skills/<skill>/evals/`. `[pack.evals].skills`
selects which skill-local activation evals the pack evaluator runs.

Primitive sources live under `.apm/` and are projected per adapter by `catalogue self-host`.

| Source directory | Primitive type |
|------------------|----------------|
| `.apm/skills/` | Skills |
| `.apm/agents/` | Subagents |
| `.apm/hooks/` | Hook bodies |
| `.apm/hook-wiring/` | Hook wiring |
| `.apm/commands/` | Commands |
| `.apm/shared-libs/` | Shared libraries |
| `.apm/skills/<skill>/evals/` | Activation and output-quality evals (projected with the skill) |

### Tests live with the pack, outside the payload they validate

Keep tests beside the pack they validate, but out of the runtime payload.
`.apm/` holds only files meant to participate in installation, projection, or
execution — so a test never belongs there, **even where the installer happens
to ignore its path**. Runtime separation is expressed by directory structure,
not by relying on an implicit exclusion that a future adapter may not honour.

```
packs/<pack>/tests/
├── skills/
│   └── <skill>/          # unit/, integration/, fixtures/ as the skill warrants
├── hooks/
├── pack/                 # manifest, metadata, projection
└── fixtures/
```

Tests should execute or import the real implementation under `.apm/`. Never
duplicate production code into the test tree.

### Tests versus evaluations

Two different questions, two homes.

| | `tests/` | `evals/` |
|---|---|---|
| Verifies | Deterministic software behaviour | Agent-level behaviour |
| Covers | Function output, parsing, exit status, CLI behaviour, error handling, projected install contents | Whether a skill activates, whether a near-miss avoids activation, whether output satisfies a rubric |
| Run by | pytest, Vitest, Go test, shell tooling | The eval runner |
| Lives at | `packs/<pack>/tests/` | `.apm/skills/<skill>/evals/` |

Evaluations do not replace unit or integration tests for scripts.

Evals are skill-local by design, not by accident. A fixture only means anything
next to the skill it exercises, so it belongs to the skill and is projected with
it — the adapters copy `.apm/skills/<skill>/` wholesale. That is why the `tests/`
rule is scoped to the `.apm/` boundary rather than "anything that isn't runtime":
`evals/` is runtime-adjacent content, a test suite is not. The linter enforces
this — it looks for `eval_queries.json` and `evals.json` under
`<skill>/evals/`, and requires one for every skill named in `[pack.evals].skills`.

A **diagnostic** may live under `.apm/` when it is an intentional runtime
feature users or agents invoke — `scripts/doctor.py`,
`scripts/check_environment.py`. Those are runtime commands, not test suites.

### Catalogue archives may carry tests; installers must not install them

A catalogue or source archive walks `packs/**`, so it carries a pack's
`pack.toml`, `README.md`, `.apm/**`, `seeds/**`, `tests/**`, `docs/**`,
`.claude-plugin/`, and pack-root markdown. Shipping tests in a source-oriented
archive supports downstream verification, auditing, security review, and
testing an extracted release.

Catalogue inclusion does not imply runtime installation. Installers and
projection adapters treat `.apm/` and `seeds/` as the projected surfaces, so
nothing outside those two — `tests/` included — reaches an installed
environment.

### Test dependencies are not runtime dependencies

A skill's runtime dependency declaration lists only what the installed skill
needs at run time. `pytest`, `hypothesis`, `vitest`, `eslint`,
`mypy`, `ruff` and friends belong in development configuration.

Fixtures under a pack's test tree ship in the archive, so they must carry no
credentials or private data, prefer synthetic data, stay modest in size, and
name their licence when sourced externally. Fuzzing corpora, generated output,
coverage reports, and caches are neither committed nor packaged.

The packager enforces the second half. It prunes these directory names at every
level of a pack, and never descends into them:

```
__pycache__  .pytest_cache  .mypy_cache  .ruff_cache  .tox
.hypothesis  htmlcov  node_modules  .venv  venv
```

plus `*.pyc`, `*.pyo`, `.DS_Store`, `coverage.xml`, and any `.coverage*` shard.
A directory you mean to ship must not be named one of those — the drop is
silent. Note this is matched by name at any depth, so it is deliberately *not*
the same list as the repository-root exclusions.

### Repository-root tests

A test concerning one pack stays inside that pack. Behaviour no single pack
owns — the catalogue system, packaging, shared projection machinery, profiles,
cross-pack interaction — belongs to the repository, not to a pack.

Where that lives is the repository's call. This catalogue splits it: behaviour
that exercises the engine keeps to the engine's own suite
(`packages/agentbundle/tests/`), while cross-pack *lints* — the ones that read
every pack's tree and belong to no pack — live with the repository's other
tooling. Neither is a root `tests/` tree; a catalogue that wants the separate
tree can add one. Don't create a top-level directory for a single test — the
ownership rule is what matters, not the path.

### One test process per skill

Run each skill's suite in its own process. This is a correctness requirement,
not a performance preference.

Skills are independent, so two of them may reasonably ship a `render.py`, and
their suites may both be called `test_render.py`. Collect them into one pytest
run and two things break: pytest refuses the duplicate test basenames outright
(`import file mismatch`), and if it did not, the first `render` module imported
would serve every suite that expects its own.

```
pytest packs/<pack>/tests/skills/<skill>/     # one invocation per skill
```

An invocation that spans two skill test directories is safe only while their
basenames happen not to collide — which is a property of today's contents, not
of the layout. Keep the invocations separate and the question never arises.

### Normative summary

- A pack **MUST** be the ownership boundary for its tests.
- Pack-specific tests **MUST** live under `packs/<pack>/tests/`.
- Ordinary tests **MUST NOT** live under `.apm/`.
- `.apm/` **MUST** contain only runtime or projectable content.
- Agent evaluations **MUST** live under `.apm/skills/<skill>/evals/` and stay
  distinct from implementation tests.
- Test dependencies **MUST NOT** be declared as runtime dependencies.
- Tests **MAY** be included in catalogue or source archives.
- Tests **MUST NOT** be projected into installed agent environments. Evals
  **are** projected, as a skill subdirectory — they are runtime-adjacent.
- Tests that no single pack owns **SHOULD** be kept out of pack test trees,
  wherever the repository chooses to put them.
- CI **SHOULD** exercise both the source implementation and the projected
  runtime artifact.

Release validation should therefore project the pack into a temporary agent
environment, smoke-test it there, and confirm the projection contains no
`tests/`, `__pycache__/`, `.pytest_cache/`, coverage output, or
`test-results/`.

---

## 5. Skill frontmatter and body

**Contract:** `contracts/skill.schema.json`

Every skill is a Markdown file with YAML frontmatter. Required frontmatter keys:
`title`, `description` (≤ 1024 characters), `kind`.

- `guides/_shared/how-to/author-a-skill.md` — frontmatter key list, body structure,
  naming rules, progressive-disclosure pattern, three-tier dependency policy, and eval
  coverage. (Available in the full guide library; not bundled in this scaffold.)

---

## 6. Skill body and progressive disclosure

Long skills use progressive disclosure: a brief required-reading summary at the top,
with detail sections the agent loads on demand. This keeps context usage bounded.

See `guides/_shared/how-to/author-a-skill.md` for the full pattern.

---

## 7. Profile format

**Contract:** `contracts/profile.schema.json`

A profile is a blessed combination of packs installed in a single command.

- [profiles/README.md](../../../profiles/README.md) — profile layout and authoring rules.
- [profiles/AGENTS.md](../../../profiles/AGENTS.md) — agent-facing schema map.
- `guides/_shared/how-to/design-a-profile.md` — step-by-step authoring guide. (Available
  in the full guide library; not bundled in this scaffold.)

---

## 8. Lint and verify commands

```bash
agentbundle catalogue lint --root .           # style and basic correctness
agentbundle catalogue verify --root .         # full validation (lint + schema + self-host drift)
agentbundle catalogue self-host --root . --check  # scaffold projection drift check
```

Run all three before opening a PR. The CI contract (section 9) details the exit codes.

---

## 9. CI contract

**Contract:** `contracts/catalogue-ci-contract.md` (in this scaffold)

Provider-neutral validation, packaging, publication, and evidence requirements for a
catalogue CI pipeline.

- [catalogue-ci-contract.md](catalogue-ci-contract.md) — exit codes, required steps,
  evidence manifest.

---

## 10. Package and publication

```bash
agentbundle catalogue package --root . --output dist/
```

Produces a distributable archive with a content manifest. See the CI contract (section 9)
for the full pipeline sequence.

---

## 11. Optional pack integrations

**Contract:** `contracts/pack.schema.json` (`[[pack.integrations]]` array)

A pack can declare optional behavior seams with other packs using the
`[[pack.integrations]]` array table in `pack.toml`. The entire array is
optional — packs without integrations remain fully valid and installable.

**The ten fields** (all fields in each entry are required except `version`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique kebab-case identifier within this pack |
| `pack` | string | yes | Name of the target pack |
| `kind` | string | yes | One of: `input`, `augment`, `review`, `handoff` |
| `role` | string | yes | Short user-facing label for this integration |
| `consumers` | string[] | yes | Type-qualified primitive refs in the declaring pack |
| `providers` | string[] | yes | Type-qualified primitive refs in the target pack |
| `when` | string | yes | Human-readable conditions under which this seam activates |
| `purpose` | string | yes | What the integration achieves when active |
| `fallback` | string | yes | What the consuming skill does when the target pack is absent |
| `version` | string | no | Semver range of the target pack version |

**The four `kind` values:**

- `input` — the target provides an artifact the declaring pack's skill reads
- `augment` — the target pack's skill is inlined into the consuming skill's workflow
- `review` — the target pack's agent or skill is invoked as a reviewer pass
- `handoff` — the consuming skill passes control to the target at a defined boundary

**What integrations are not:**

No auto-install (declaring an integration does not install the target pack), no
dependency closure (`[pack.dependencies]` owns hard requirements), no executable
`when` expressions (the `when` field is explanatory text only).

**The `fallback` requirement:**

Every integration must declare what the consuming skill does when the target is
absent. An agent reading the integration without the target installed needs to
know how to proceed.

**Lint and verify:**

```bash
agentbundle catalogue verify --root .
```

Primitive refs (e.g., `"skill:work-loop"`) are validated against the declaring
and target packs' `.apm/` directories. An absent target pack does not fail
verification — the check is portable across catalogues that may not include
every optional pack.

---

## 12. Bundled contract inspection

List, inspect, or export the contracts bundled with the running AgentBundle version
without network access:

```bash
agentbundle catalogue contracts list
agentbundle catalogue contracts show <name>
agentbundle catalogue contracts export --output <dir>
```

`list` and `show` are read-only. `export` writes one regular file per listed contract
to the selected directory. These are reference copies only. They do not override the
contracts used for validation by this agentbundle version.

---

## Journey format

A `JOURNEY.md` describes the outcome a pack helps someone reach. Put it beside
`pack.toml` at `packs/<pack-name>/JOURNEY.md`. The file is optional: catalogues and
packs created before this convention remain valid, and their generated index contains
an empty `journeys` array.

The YAML frontmatter is the machine-readable contract. The Markdown body is for
readers; the index command does not extract structured data from it.

### Required frontmatter

```yaml
---
journey_id: catalogue-authoring
pack: example-pack
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: Build a catalogue pack that passes its published contracts.
contract:
  useItWhen: You need to add or revise a catalogue pack.
  youProvide: The intended outcome, scope, and pack contents.
  youReceive: A validated pack with clear author and adopter documentation.
  yourDecisions:
    - Which adapters and installation scopes the pack supports.
---
```

Use these fields:

- `journey_id`: a string that is unique within the catalogue.
- `pack`: the exact pack name from `pack.toml`.
- `start_state` and `end_state`: one of `read-only`, `proposed-write`, or
  `confirmed-write`.
- `scope`: `repo` or `user`.
- `tagline`: a plain-language summary of at most 120 characters.
- `contract`: a closed object with one optional member. `useItWhen`,
  `youProvide`, and `youReceive` are strings; `yourDecisions` is an array of
  strings. `decisionGateIds` is optional and, when present, is an array of
  `humanGates[].id` strings in the order a reader meets those decisions; it
  carries identifiers only, never adopter-facing wording. Packs authored before
  it existed stay valid, because `yourDecisions` remains required.

Malformed YAML, a missing required field, or a field with the wrong type stops index
generation before any output is replaced.

### Optional frontmatter

The following fields add richer discovery information without changing the required
contract:

- `prerequisitePacks`: pack-name strings.
- `whatChanges`: a reader-facing description.
- `skills`: objects with `name`, `description`, and `humanTouches`.
- `humanGates`: gate objects with `id`, `label`, `trigger`, `duration`,
  `whatToCheck`, `whatGoodLooksLike`, `whatBadLooksLike`, and `consequence`;
  `globalGate` is optional.
- `typicalSession`: an object with `agentTurns`, `humanTouches`, and
  `wallClockMinutes`.
- `docsUrl` and `packUrl`: documentation links.
- `relatedJourneys`: other journey identifiers.
- `effects`: external effects declared by the author.

Each `effects` entry is a closed object with string fields `kind` and `description`:

```yaml
effects:
  - kind: file-write
    description: Writes generated files after the user confirms the destination.
```

Effects describe externally observable outcomes such as writing files, using a
network service, or publishing an artifact. Do not infer them from pack structure,
and do not list internal computation as an effect.

### Reader-facing body

The first body element after frontmatter must be an **Arrival trigger** quick-reference
table that maps activation phrases to outcomes. Follow it with these sections:

1. `Orient`: explain how the user establishes the starting context for a session.
2. `Primary workflow`: use numbered steps. Every step names what the user says or does,
   what the agent produces, any human decision required, and the resulting state.
3. `Persist and collaborate`: explain how state is carried between sessions or handed
   off; a brief statement is enough when the pack has no multi-session state.
4. `Next steps`: suggest follow-on journeys named by `relatedJourneys` frontmatter.

Explain the outcome and choices in product language. Avoid repository-maintainer
commands, publication machinery, or internal decision records; adopters should not
need the catalogue's own development environment to understand a journey.

The generated journey data conforms to the machine contract at
`contracts/catalogue-index.schema.json`.

### Generate the neutral index

Run this from a catalogue checkout:

```console
agentbundle catalogue index . --dry-run
agentbundle catalogue index . --output catalogue-index.json
```

The dry run parses every present `JOURNEY.md`, builds the index in memory, validates it,
and writes nothing. The second command publishes the validated JSON atomically. Add
`--format json` when another tool needs the command result as one JSON document.

### Migrating an existing pack

You do not need to add placeholder journeys to old packs. Add `JOURNEY.md` when the pack
has a real end-to-end outcome to describe, then start with the required frontmatter and
the arrival table and body sections above. Keep `pack` equal to the manifest name and
choose states from the documented enums. Verify the complete catalogue with a dry run
before publishing its index.
