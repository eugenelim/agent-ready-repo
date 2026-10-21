# Spec: Packageable blank catalogue from `catalogue init`

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`catalogue-tooling-init`](../catalogue-tooling-init/spec.md) (a blank catalogue has zero installable packs) and [`catalogue-authoring-scaffold`](../catalogue-authoring-scaffold/spec.md) AC10 (`_`-prefixed directories are templates that packaging skips)
- **Amends:** [`catalogue-tooling-init`](../catalogue-tooling-init/spec.md) file-status table — `already-present` also covers a kept root `AGENTS.md` or `CLAUDE.md` whose content differs from the planned file (AC-0003)
- **Discovery:** none
- **Contract:** none — `catalogue init` output and the runtime archive have no schema file; the acceptance criteria pin the observable behaviour and the reference guides in Durable Outputs describe it.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

**Mode:** full. It changes a published interface: the files `agentbundle catalogue init`
writes and the diagnostics `agentbundle catalogue package` reports.

## Outcome

A catalogue author can run `catalogue init`, `catalogue verify --root`, `catalogue package`
and `catalogue verify --archive` on the fresh scaffold, in that order and with no hand
edits, and every command exits 0. A blank catalogue still has zero installable packs, so
its first release is an empty but valid archive.

## What Changes

- `catalogue init` generates a root `AGENTS.md` and a root `CLAUDE.md` import shim beside `catalogue.toml` (`catalogue_tooling/initialise.py`). `catalogue package` already ships a root `AGENTS.md`, and the archive verifier accepts it as the installable-catalogue marker.
- A target that already holds its own root `AGENTS.md` or `CLAUDE.md` keeps it: init reports the file `already-present` with the SHA-256 of the bytes on disk, and does not write it. For every other path `already-present` still means byte-identical.
- An invalid `[catalogue.package].include` entry makes `catalogue package` fail with a `CAT-PKG-001` diagnostic instead of an uncaught `ValueError`, and an entry naming a `_` template directory is invalid, so a template never ships (`catalogue_tooling/package.py`).
- The bundled scaffold (`_data/catalogue-scaffold/` and its `manifest.json`) is unchanged.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | the files init writes and the first-release path change | `guides/_shared/how-to/create-a-catalogue.md` § Create the catalogue | implementer | names the root `AGENTS.md` and says a fresh catalogue packages as an empty release | text matches AC-0001 and AC-0005 |
| Interface reference (init) | the scaffold file list and the keep-existing rule change | `guides/_shared/reference/catalogue-format.md` § Scaffold options | implementer | lists root `AGENTS.md` and `CLAUDE.md`, states that existing ones are kept and reported `already-present` with their on-disk hash | text matches AC-0001 and AC-0003 |
| Command reference (package) | the root marker and the include diagnostic | `docs/guides/reference/catalogue-commands.md` § `agentbundle catalogue package` | implementer | states that a runtime archive needs a root `AGENTS.md` and that a bad include entry reports `CAT-PKG-001` | text matches AC-0006 |
| Release history | a public CLI output changes | release `0.53.1`, moved together across `version.py`, `pyproject.toml`, `CHANGELOG.md` (entry carrying `Engine-Change-RFC: n/a — …`), `README-pypi.md` (`What's new in 0.53.1` first), a `docs/product/changelog.d/` fragment, and the pin in `tests/roster/test_okf_catalogue_discovery.py` | implementer | changelog entry names both fixes | `tests/roster/test_okf_catalogue_discovery.py` green |

## Agent Rules

### Always do

- Build the root `AGENTS.md` text from the validated catalogue `name` only; never interpolate `--display-name`, `--description` or `--owner-name` into it.
- Route the generated root files through the existing plan, conflict, staging, commit and rollback path in `initialise.py`.

### Ask first

- Scaffolding a real, non-`_` starter pack.
- Changing `_data/catalogue-scaffold/` or its `manifest.json`.
- Changing the self-hosted preset (`initialise_self_hosted.py`).

### Never do

- Add a dependency or a new source module under `packages/agentbundle/agentbundle/`; the engine change lives in `initialise.py` and `package.py`.
- Overwrite or edit an existing root `AGENTS.md` or `CLAUDE.md` in the target.
- Relax `verify_archive`'s marker check or the `_`-prefix packaging exclusion.

## Testing Strategy

- **Init writes and keeps the root files — TDD (AC-0001, AC-0002, AC-0003, AC-0004)** — `init_catalogue` on `tmp_path` targets gives exact files, bytes and file actions.
- **Blank catalogue packages and verifies — TDD, integration through the CLI (AC-0005)** — a subprocess run of the four commands on a fresh `tmp_path` target observes each exit code; this is the regression test for the defect.
- **Include diagnostic — TDD (AC-0006)** — `package_catalogue` on a fixture catalogue with a bad include entry returns a result, not an exception.
- **Adopter rehearsal — manual QA, end to end** — the four commands run from this worktree's code in a temporary directory outside the repository, with no hand edits.

## Acceptance Criteria

- [ ] **AC-0001.** `catalogue init` into a new directory creates a root `AGENTS.md` and a root `CLAUDE.md` whose bytes are exactly `@AGENTS.md\n`, and reports both with action `create`.
- [ ] **AC-0002.** The root `AGENTS.md` that init writes contains the catalogue's `name`, and its Markdown link targets are exactly `packs/AGENTS.md`, `profiles/AGENTS.md` and `guides/_shared/reference/catalogue-authoring-standards.md`.
- [ ] **AC-0003.** When the target already holds a regular, non-symlink root `AGENTS.md` or `CLAUDE.md` with any content, init exits 0, leaves that file's bytes unchanged, and reports it with action `already-present` and a `sha256` equal to the SHA-256 of that file's bytes.
- [ ] **AC-0004.** When the target's root `AGENTS.md` or `CLAUDE.md` is a symlink, init fails with `CAT-INIT-007` and writes no file.
- [ ] **AC-0005.** On a directory just created by `catalogue init <dir> --name <name>`, with no other change, `catalogue verify --root <dir>`, then `catalogue package --root <dir> --bundle <b> --release <r> --channel <c> --output <out>`, then `catalogue verify --archive <archive> --sha256-file <sidecar>` each exit 0, and the archive holds a root `AGENTS.md` and no member under `packs/_example/` or `profiles/_example/`.
- [ ] **AC-0006.** When `[catalogue.package].include` holds an entry that `catalogue package` rejects — one not under `packs/`, one that does not exist, one naming build residue, or one whose path has a `_`-prefixed directory directly under `packs/` — `catalogue package` exits 1 with a `CAT-PKG-001` diagnostic naming the entry, prints no traceback, and creates no file under `--output`.

## Follow-ons

none

## Assumptions

none
