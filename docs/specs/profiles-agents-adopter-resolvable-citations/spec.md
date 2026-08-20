# Spec: profiles-agents-adopter-resolvable-citations

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none. Instruction prose plus one generalized construction test; no
  schema, CLI, or behaviour change.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (no risk trigger fired). Checked each trigger explicitly.
Unfamiliar: no — the sibling file `packs/AGENTS.md` already solved this exact
problem and its guard is the artifact being generalized. Governance surface: no
— every obligation the file states survives with the same meaning; only the
route a reader takes to the schema changes. Structural / public-interface: no —
no new module, boundary, dependency, or CLI verb; `agentbundle catalogue
contracts show` already ships. Destructive: no. New dependency: no. -->

## Objective

`profiles/AGENTS.md:13` points an adopter at `../contracts/profile.schema.json`
as a Markdown hyperlink. `catalogue init` writes the scaffold, and the scaffold
ships `guides/ manifest.json packs/ profiles/ tests/` — no `contracts/`. So the
one place the file names the authority for profile validation is unreachable in
every adopter tree, and `profiles/AGENTS.md:31` points at
`tools/catalogue/sync_authoring_scaffold.py`, which no adopter has either.

Neither dangles in this repository, so nothing fails. The sibling `packs/AGENTS.md`
is already guarded against exactly this by
`test_packs_agents_md_cites_only_paths_it_ships`; that guard names one file
literally, which is why `profiles/AGENTS.md` drifted.

Success: an adopter reading the shipped `profiles/AGENTS.md` can reach the profile
schema with a command they have, still learns that the schema owns validation, and
the guard that would have caught this covers both files.

## Acceptance Criteria

- [x] **AC1 — the ownership statement survives, with a route that resolves in
  both trees.** `profiles/AGENTS.md` still states that the profile schema owns
  fields and semantic validation, and still states that profile TOML is the
  source and that profiles are scaffold sources not projected by `catalogue
  self-host`. It names the schema as `profile.schema.json` and routes the reader
  to it with `agentbundle catalogue contracts show profile.schema.json` — the
  installed CLI carries the schema as package data and this verb prints it.

- [x] **AC2 — no repo-only path survives in the shipped file.**
  `profiles/AGENTS.md` cites no path under `contracts/`, `tools/`, or `docs/`.
  The scaffold-sync obligation is not restated with a path; it keeps its
  canonical maintainer home in `AGENTS.local.md`, which already names `profiles/`
  by that route.

- [x] **AC3 — the guard covers both sync-paired instruction files.**
  `test_packs_agents_md_cites_only_paths_it_ships` is retained and delegates to
  `_assert_cites_only_shipped_paths`; a second
  `test_profiles_agents_md_cites_only_paths_it_ships` delegates to the same
  helper, preserving per-file failure isolation. The helper uses the same
  shipped-file set, rooted prefixes, placeholder exclusion, and
  `optional_by_design` exception for each file, with a bounded rooted-path token
  extraction that also recognizes bare paths, reference-style destinations, HTML
  `href` destinations, fragments, and nested directory citations.

- [x] **AC4 — the generalized guard is proven to fail.** Reintroducing the
  hyperlink `[`contracts/profile.schema.json`](../contracts/profile.schema.json)`
  into the scaffold copy of `profiles/AGENTS.md` makes the guard fail and name
  that path; restoring the corrected text by editing makes it pass. The same
  mutation is run for the `tools/` citation, and for one instance of each
  citation form the extraction recognizes — bare path, reference-style
  destination, HTML `href`, fragment-carrying path, and nested directory. Each
  mutation is injected alone, and the file is restored by editing to
  byte-identical content, never by `git checkout`.
  `test_packs_agents_md_cites_only_paths_it_ships` stays green throughout, which
  is what proves the two files fail independently.

- [x] **AC5 — both copies of the sync pair agree.**
  `tools/catalogue/sync_authoring_scaffold.py --check` exits 0, and
  `manifest.json` digests match, after the repo-root source is edited and the
  projection is rewritten by that script's `--write` mode. The scaffold copy is
  never hand-edited.

- [x] **AC6 — the release surfaces move together.** The change alters package
  data that ships in the wheel, so per the `packages/AGENTS.md` version-bump rule
  the package moves to the next free version, and every surface pinned to it
  moves with it: `pyproject.toml`, `agentbundle/version.py`,
  `packages/agentbundle/CHANGELOG.md`, `README-pypi.md` (`What's new in <v>`),
  the `### [agentbundle][<v>]` heading in `docs/product/changelog.md`, and the
  literal pin in `tests/roster/test_okf_catalogue_discovery.py`. The topmost
  `### [agentbundle][…]` heading equals the package version.

- [x] **AC7 — the decision record stops asserting what is no longer true.** The
  `packs-agents-normative-pointer` entry in `workspace.toml` states that
  `profiles/AGENTS.md` names `contracts/profile.schema.json` and that no test
  covers that file, and instructs that the assertion be extended "in the same
  change". All three claims are corrected to match the tree, the `packs/` half is
  left open with its `(a)`-vs-`(b)` decision intact, and the entry's stale
  150-line budget note is corrected to the 80-line cap the linter enforces.

## Boundaries

### Never do

- Never delete the ownership statement to make the link problem go away. AC5 of
  `docs/specs/contracts-readme-governance-sweep/spec.md` added this pointer so a
  reader could tell which artifact wins; that obligation is preserved and only
  its reachability changes.
- Never widen the guard to all scaffold-shipped Markdown. Measured on
  `b4dae24d`: `guides/_shared/reference/catalogue-authoring-standards.md` carries
  twelve such citations, which AC9 of
  `docs/specs/catalogue-wave1-contract-convergence/spec.md` deliberately admitted
  as plain-text contract names. A blanket guard reddens `make ci` and reverses a
  ratified decision.
- Never hand-edit `packages/agentbundle/agentbundle/_data/catalogue-scaffold/`.
- Never fix the same defect class in `packs/README.md`. `workspace.toml` records
  that entry as blocked with its reasoning; this spec does not reopen it.

## Assumptions

- The profile schema does not need to reach an adopter as a file. Verified:
  `agentbundle/catalogue_tooling/verify.py:422` loads it with
  `_load_bundled_json("profile.schema.json")` and
  `agentbundle/commands/profile.py:69-77` resolves it at
  `_data/profile.schema.json`, whose docstring states the profile schema "is
  internal and lives only" there. `_data/profile.schema.json` is byte-identical
  to `contracts/profile.schema.json`, is listed in `_data/public-contracts.txt`,
  and `agentbundle catalogue contracts show profile.schema.json` prints it. So an
  adopter validates with `agentbundle catalogue lint` / `verify` and reads the
  contract with `contracts show` — a `contracts/` copy is not required for either.
