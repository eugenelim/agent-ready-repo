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

### Repository-root tests

A test concerning one pack stays inside that pack. Behaviour no single pack
owns — the catalogue system, packaging, shared projection machinery, profiles,
cross-pack interaction — belongs to the repository, not to a pack.

Where that lives is the repository's call. This catalogue keeps it in the
engine's own suite (`packages/agentbundle/tests/`) rather than a root `tests/`
tree; a catalogue that wants the separate tree can add one. Don't create a
top-level directory for a single test — the ownership rule is what matters,
not the path.

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

## Journey format

> **Not yet available.** Wave 4 of the catalogue-contracts initiative will define the
> journey format and its contract. This section will be filled in when that wave ships.
