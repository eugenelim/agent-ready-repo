# Manual QA: repository context anchoring

## T1 — scaffold parity

- Root and seed use the same four minimum concepts: project overview,
  development workflow, build/test commands, and coding conventions.
- Root retains `Documentation` because eight distinct authoritative source
  classes need routing. The seed explains the trigger without emitting the
  heading into an adopter file.
- Root retains `Security considerations` because this repository declares
  privacy rules, credential and filesystem helpers, and the outbound-HTTP gap.
- Root retains `Scoped instructions` because several real subtrees change the
  commands or ownership rules that apply. The seed makes this conditional.
- Root omits `Repository structure`; its project overview links the existing
  ownership map instead. The seed architecture asset asks only for area,
  responsibility, and change guidance and tells adopters to delete it when it
  would duplicate existing sources.
- The organization-stack how-to remains one external how-to page. It now starts
  with a natural-language backend example, distinguishes reads from catalogue
  writes, preserves organization-owned paths, and describes root/scoped deltas
  without adding another documentation artifact.

## T2 — doctor proposals

- Minimum/no-`AGENTS.md` case: the doctor reports missing routing, recommends
  only the four populated minimum topics, and stops at a proposal until each
  write is approved. It does not instantiate the optional architecture asset.
- Rich/custom-layout case: the doctor retains root `DESIGN.md` and an external
  contributor link, labels the unreachable external content unavailable, and
  offers a scoped delta only for the backend subtree. No source is relocated or
  copied into a core-pack path.
- The 19-case golden-eval matrix gives every scenario a repository-shaped
  prompt, observable expected output, and four review assertions. It covers the
  two proposal shapes plus evidence authority, authoring anchors, focused
  review, selective companion reconciliation, all 25 instruction/data
  authority combinations, and all six outside-root read/write path cases.

## T3 — task plans

- Structural example: `Repository anchors: DESIGN.md;
  src/tasks/ExampleTask.java; src/test/...; uncertainty — registration differs`.
  This is bounded to one explicit source, one implementation, its tests, and a
  named uncertainty.
- Non-structural example: `Repository anchors: none — non-structural`.
- Existing plans without the field remain valid and expose only a review-time
  assurance gap when the work is structural.

## T4 — focused review

- Positive structural case emits exactly: “This proposal introduces X. A
  mapped repository source or canonical production example uses Y for the same
  responsibility. Confirm or justify the deviation.” It requests confirmation
  or rationale and does not prescribe the replacement.
- Cosmetic difference and one-neighbor cases emit no idiom-delta finding. They
  are explicitly excluded from rule inference, along with product-scope
  expansion and core-layout enforcement.
- Review independently opens production examples only for convergent,
  tentative, contradictory, unavailable, or outcome-critical evidence; strong
  explicit/framework-owned citations bound the inspection unless contradicted
  by the diff.

## T5 — final scope

- Final diff audit confirms the implementation stays within repository
  anchoring. It does not change installer code, companion creation/delivery,
  marker behavior, hook wiring, activation diagnostics, `.codex/**`, or Codex
  projection tests. `adapt-to-project` consumes an existing
  `AGENTS.upstream.md` only as doctor input; deterministic creation of that
  companion remains unchanged.
- Canonical source and adopter-facing changes are exactly: root `AGENTS.md`;
  `docs/{CONVENTIONS.md,architecture/overview.md,product/changelog.md}`; the
  repository-context spec, plan, comparison matrix, and this record;
  `guides/_shared/how-to/build-an-org-stack-pack.md`;
  `guides/architect/{README.md,tutorials/architect-first-session.md}`;
  `guides/core/how-to/adapt-to-project.md`; core seed
  `AGENTS.md`, `docs/CONVENTIONS.md`, `docs/architecture/overview.md`, and
  `docs/product/changelog.md`; canonical core `adapt-to-project`, `new-spec`,
  `work-loop`, `contract-acquisition`, `operational-safety`, adversarial, and
  quality-reviewer sources/assets/evals; and canonical architect
  `architect-design` source/evals plus its README.
- Verification and release-only changes are exactly: the repository-context
  fixture matrix and its core/architect tests; the seed-lint implementation and
  unit test; core and architect pack/plugin manifests; the catalogue
  marketplace architect version; agentbundle version, pyproject, changelog, and
  PyPI README; and the generated site highlights file. The matching `.agents`
  and `.claude` core projections contain byte-identical copies of the changed
  canonical skills, references, evals, and reviewer definitions.
- The corrected targeted command—including the new seed-lint construction
  test—passes 53/53. It uses unique work-loop and architect test filenames;
  the originally planned duplicate `test_repository_anchors.py` basenames were
  corrected after pytest proved they collide in the shared interpreter. A wider
  unchanged lint-suite test cannot remove an empty pytest directory because
  macOS returns `EPERM`. `make lint-ruff`,
  `make lint-mypy`, guide validation, AGENTS progressive-disclosure lint,
  spec-status lint, and deep catalogue lint passed. Projection comparison found
  no content differences for common `.apm`/`.agents`/`.claude` files.
- Security review found and closed an asymmetry in repository-anchor consumers:
  `architect-design`, `new-spec`, and `work-loop` now reject outside-root local
  anchors and treat non-`AGENTS.md` repository/external material as attributed
  evidence that cannot widen authority. `adapt-to-project` and
  `architect-design` now declare their filesystem/network security boundaries;
  targeted tests pin both the prose controls and metadata.
- Full catalogue verification, self-host write, and `make build-check` reach
  cleanup of unchanged provenance-bearing fixture directories and fail when
  macOS denies removal. The same result occurs in a fresh `/private/tmp` clone
  with `COPYFILE_DISABLE=1`; `make site-build` completes documentation
  generation but Astro hits the same environment class while renaming a Vite
  temporary directory. On 2026-08-23 the owner approved a narrow verification
  deferral and asked Claude to retry these gates in its supported environment
  before merging. If that runtime has the same restriction, the approved
  replacement evidence is the targeted tests, ordinary lints, deep catalogue
  lint, projection parity, and clean reviewers recorded here. The implementation
  does not special-case generic linters or cleanup logic to hide the gap.
- Merge sequencing with the independent Codex/install session is limited to
  adjacent core seed content and shared release metadata. That session should
  rebase after the canonical seed and pack-version changes, then regenerate and
  verify its own Codex/install projections and tests. This change deliberately
  contains no `.codex/**` write to pre-empt that work.
- Final adversarial, security, and whole-spec quality re-reviews each returned
  `Clean — ready to commit.` after the security controls, behavioral goldens,
  test-path correction, and approved gate deferral were applied.

## T6 — deferred gates, retried in a supported environment

The environment deferral recorded under T5 was **not** used. On 2026-08-23 the
three gates that could not finish under the managed runtime — `catalogue
verify`, `catalogue self-host --write`, and `SKIP_SAST=1 make build-check` —
all ran to completion here with no `EPERM`. Running them, plus the wider test
suites CI runs, found six real defects that the deferral had concealed. Each is
fixed in this change; none was waived.

1. **Release-surface pins were not moved.** `tests/roster/`'s two
   release-synchronization tests hard-pin the previous core and `agentbundle`
   versions, so the version bump left them red. Both pins now name the shipped
   versions.
2. **A pack test reached above its owning pack.** The seed contract file
   asserted against this checkout's root `AGENTS.md`, root
   `docs/architecture/overview.md`, and an adopter-facing how-to. Rule
   `pack-tests-stay-in-pack` rejects that climb. The repository-level half moved
   to `tests/roster/test_repository_context_root_guidance.py`; the seed half
   stays pack-owned and now anchors at its own pack root. `tests/conformance/`
   is the wrong home — its portability lint rejects any reach into `docs/`.
3. **Two new suite directories had no runner.** `contract-acquisition` and
   `architect-design` were discovered rather than declared, which rule
   `every-suite-dir-has-a-runner` treats as unrun by default. Both are now named
   in the `Makefile` test target.
4. **A roster slice pinned the old Class-3 heading.**
   `tests/roster/test_adapt_reference_architecture.py` anchors on
   `**Reference-architecture harvest.**`, which this change renamed to
   `**Optional reference-architecture enrichment.**`. The guard failed loudly
   with "update this slice", which is the behavior it was designed for. The
   slice now follows the rename.
5. **The same slice asserted a canonical destination.** It required
   `docs/architecture/reference.md` inside the subsection — exactly the fixed
   destination this change removes. It now asserts the new contract instead:
   the shipped template is an optional starting point and the adopter chooses
   the location.
6. **A seed link inventory was pinned exactly.**
   `test_installed_agents_guidance_has_no_dangling_relative_links` asserted the
   seed `AGENTS.md` links both `docs/CONVENTIONS.md` and
   `docs/architecture/overview.md`. The architecture link is gone by design —
   that section is conditional and the seed tells adopters to delete the file
   when it duplicates a source they already have. Core still ships the file, and
   that assertion is retained.

Defects 4-6 sit outside the spec's targeted suite, in tests owned by other
features. That is the general lesson: a targeted suite cannot see the contracts
other suites pinned against the prose this change rewrote.

The version surface also moved: `main` released architect `0.15.0` while this
change was in review, so the architect bump is `0.15.1`, not the `0.14.6`
planned against the older base.
