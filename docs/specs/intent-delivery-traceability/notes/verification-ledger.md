# Verification ledger: intent delivery traceability

Execution observations and owner decisions for this delivery. Obligations stay
in `spec.md` and `plan.md`; this file records what execution and review found.

## 2026-10-04 — T1 confinement import probe

The plan's T1 kill condition asks whether the projected resolver can import
`agentbundle.catalogue_tooling.file_safety` in supported repo-scope execution.

- Observed on the maintainer workstation: `python3 -I -c "import
  agentbundle.catalogue_tooling.file_safety"` resolved from a pip-installed
  `agentbundle`, byte-identical to
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`.
- Not observed at the time: the pipx and zipapp routes that
  `guides/_shared/how-to/install-agentbundle-from-clone.md` documents as
  supported for `core`. Neither puts `agentbundle` on the interpreter that runs
  skill scripts.

## 2026-10-05 — Review round 1 outcome

Round 1 post-gates review (adversarial, security, quality, experience) found
that the import probe above did not cover every supported install route. On a
pipx- or zipapp-only install the resolver cannot import the helper, so both
consumers would fail closed on every run. The plan's kill condition therefore
holds: the plan is amended rather than the helper vendored ad hoc.

## 2026-10-05 — Owner decisions (eugenelim)

Recorded from the owner's answers in the implementing session.

1. **Confinement source.** The resolver uses a byte-identical `file_safety.py`
   co-located in `packs/core/.apm/adapter-root-bins/`, pinned to the blessed
   `agentbundle.catalogue_tooling.file_safety` by a parity test. This is the
   pattern close-work, work-intake, and work-loop already use. It replaces the
   direct `agentbundle` import.
2. **Closure policy for a broken spec reference.** When a spec's own delivery
   reference is ambiguous, malformed, unsafe, or names a missing target,
   close-work refuses closure of every feature that spec could belong to and
   names the `delivery-…` code, instead of dropping the spec from the
   descendant set.
3. **Wording.** The changelog and how-to keep per-consumer phrasing for
   delivery problem cases. Each phrasing must match what its own consumer
   checks; only statements found to be wrong are corrected.

## 2026-10-05 — Round 1 indeterminate adjudications, resolved by the owner

Three round-1 adjudications classified `invalid (indeterminate-present)`
because each held one question for the owner. Their sustained findings stand
as adjudicated; the decisions above settle the open entries:

- Experience reviewer finding 7 (one set of problem-case terms): settled by
  decision 3. No change beyond correcting inaccurate statements.
- Security reviewer finding 4 (close-work acting on partial data when a spec
  reference is broken): settled by decision 2. Becomes required work.
- Adversarial reviewer finding 5 (no evidence that a real projection was
  invoked): settled by the sustained quality-engineer finding 4, which requires
  a test against a real clean Core repo-scope projection.

## 2026-10-05 — Helper renamed to `_file_safety.py` (review revision)

The pre-EXECUTE adversarial review of the amendment (round 1, finding 6)
showed that a non-prefixed `.py` file in `adapter-root-bins/` is published as
a pack execution entry and claims a shared basename in `.agentbundle/bin/`.
The plan revision therefore names the co-located helper `_file_safety.py`, the
private-helper form other packs use. The owner's decision 1 is unchanged in
substance; the name is the controller's revision, pending the owner's
ratification at the next plan approval.

## 2026-10-05 — Owner decision 4: fix the two unsafe corpus links here (eugenelim)

Two specs carried a `Discovery:` markdown link of the form
`../../product/intents/<slug>.md`, which AC-0010 reports as
`delivery-reference-unsafe`: `docs/specs/capture-work-alias-removal/spec.md`
and `docs/specs/rendered-page-visual-inspection/spec.md`. Under AC-0020 those
two diagnostics would make close-work refuse closure of every `spec`-route
feature in this repository, 22 features including this one. The owner chose
to fix both links in this change. Each now reads `intent:<slug>`, naming the
same intent file the link pointed at.

- Observed after the fix: the resolver reports `complete: true` with no
  `delivery-reference-unsafe` diagnostic; `delivery-target-missing` fell from
  9 to 8 because `rendered-page-visual-inspection` now resolves to its spec.

## 2026-10-05 — Features still refused by their own delivery diagnostics

After owner decision 4, no spec or brief carries a delivery diagnostic of its
own, so AC-0020 refuses nothing in this corpus. Close-work still refuses a
feature whose own subject carries a delivery diagnostic (AC-0012). Observed on
the resolver run after commit `8ffa61de9`, ten features:

- `delivery-projection-mismatch`: `intent:cut-before-adding-solution-ladder`,
  `intent:work-item-capture-contract`.
- `delivery-target-missing`: `intent:cross-pack-experience-eval`,
  `intent:digital-product-guides-update`,
  `intent:product-engineering-shaping-doctrine`,
  `intent:product-strategy-adoption-doctrine`,
  `intent:tracker-native-value-before-adoption`,
  `intent:xd-design-system-foundations`, `intent:xd-ia-archetypes-objects`,
  `intent:xd-state-reviewer-doctrine`.

Repairing those mappings is a corpus edit outside this delivery.

## 2026-10-05 — Amended spec and plan approved (eugenelim)

The owner approved the amended spec and plan, which ratifies the private
`_file_safety.py` helper name. Tasks T1–T4 were delivered before the run
reset, in commits `a2b0f6140`, `336745737`, `d028d1b41`, and `ec7d1a605`; the
fresh run accounts for them against those commits rather than rebuilding them.

## 2026-10-06 — Post-build review: the repo-scope install never delivers the resolver

Observed by the adversarial and quality reviewers and confirmed in source:
`agentbundle install` delivers `adapter-root-bins/*.py` only at user scope,
to `~/.agentbundle/bin/` (`packages/agentbundle/agentbundle/commands/install.py`,
"Skipped at repo scope"), and Core installs only at repo scope. A real
`agentbundle install --pack core --scope repo` therefore leaves no
`.agentbundle/bin/`, and both consumers fail closed in every adopter
repository. This falsifies the plan's design decision that a repo-scope
adapter-root primitive reaches `<repository>/.agentbundle/bin/`; the
self-host projection was the only route that delivered it.

## 2026-10-06 — Owner decisions 5 and 6 (eugenelim)

5. **Resolver delivery.** Ship byte-identical copies of the resolver and its
   `_file_safety.py` helper inside each consuming skill's `scripts/` folder
   (close-work and work-loop), pinned to one source by parity tests. Each
   consumer runs its own copy. No agentbundle engine change.
6. **Release version.** `main` released Core `2.28.0` from another change, so
   this branch rebases onto `origin/main` and takes Core `2.29.0` everywhere it
   states its version.

These settle the two indeterminate entries in the 2026-10-06 post-gates
adjudications (`adversarial-reviewer` 1 and 4, `quality-engineer` 1).

## 2026-10-06 — T11 stub went green before T11 production code

The T11 stub (`test_ac0020_path_form_ambiguous_discovery_refuses_named_feature`)
earned its red on 2026-10-06 during planning, against the tree before T10.
T10 then made the resolver emit only canonical diagnostic targets, which
changed the snapshot this stub feeds to close-work; when T11 started, the stub
already passed. It was materialized byte-identical and kept as the AC-0020
path-form regression.

Run against close-work as it stood before T11, two of the 17 tests T11 added
in `test_closure_t11_vi.py` fail, and they are the two under-refusals the
post-build review found: an ambiguous `Discovery:` naming a `brief`-route
feature (`test_named_brief_route_feature_is_refused`), and an ambiguous
`Brief:` whose named briefs do not resolve
(`test_no_resolving_target_refuses_every_brief_route_feature`). The other 15
pass on that tree because T5–T10 already delivered the behaviour they pin.

## 2026-10-07 — Post-build review round 3: close-work reads brief parents itself

Observed by the adversarial reviewer and sustained on adjudication. To find the
feature behind each brief an ambiguous spec `Brief:` names, close-work reads
that brief's `Parent intent:` from its file, because the snapshot carries no
brief-to-intent link when the brief's only spec is the ambiguous one. That is a
second parser of a delivery field, against AC-0014 and T11's "from the snapshot
alone". It also keeps only the first `Parent intent:` value, so a feature
named by a second value is never refused. The same round found that the
round-2 repair refuses every `spec`-route feature on any broken spec `Brief:`,
which AC-0020 does not allow, and that the plan's `artifacts` definition no
longer matches the resolver.

## 2026-10-07 — Owner decision 7 (eugenelim)

7. **Brief-to-intent links.** The resolver reports, in the snapshot, every
   valid `Parent intent:` value of each brief that an ambiguous spec `Brief:`
   names. Close-work maps a named brief to its features from the snapshot
   alone and parses no delivery field. AC-0014 and T11 stay as written.

## 2026-10-07 — Completion evidence handoff

- **Delivery:** FEAT-0003, `docs/specs/intent-delivery-traceability/`, work-loop run `92bc8766-7fb1-4d67-b06a-3f5ffbf0e702`, branch `eugenelim/feat-0003`.
- **Accepted outcome and authority:** AC-0001–AC-0020 of the spec, approved by eugenelim on 2026-10-04 and amended with approval on 2026-10-05, 2026-10-06, and 2026-10-07 under owner decisions 1–7 above.
- **Implemented scope:** one canonical resolver (`packs/core/.apm/adapter-root-bins/intent_delivery_relations.py` with `_file_safety.py`), byte-identical copies run by `close-work` and `work-loop`, both consumers validating every snapshot record, AC-0020 refusal sets, and Core `2.29.0` records. Tasks T1–T14 are delivered.
- **Verification:** `make lint-ruff lint-mypy` exit 0; 895 targeted tests pass; `tools/check_closure_terminality_parity.py` exit 0; the shipped resolver on this repository returns a complete snapshot (46 relations, 31 classifications, 171 provenance records, 10 diagnostics); `lint-traceability.py` on this repository exits 0; `lint-spec-status.py` clean.
- **Durable outputs:** spec `Shipped`, plan `Done`, this ledger, the changelog entry `[core][2.29.0]`, the close-work how-to's delivery-code list, and the architecture page's resolver paragraphs, all repository-durable on this branch.
- **Non-goals and follow-ons:** `lint-brief-coverage.py` still reads `Brief:` itself; the ten features named under "Features still refused by their own delivery diagnostics" stay refused until their artifacts are repaired. Neither is required by the accepted intent, and no follow-on was created.
- **Unresolved obligations:** none in the accepted intent. Merge needs the owner's review.
- **Completion-event candidate:** merge of the pull request for `eugenelim/feat-0003`.
- **Authority facts:** this run wrote only repository files on this branch. It holds no closeout, disposition, or deletion authority; `close-work` owns those.

## 2026-10-07 — `main` released Core 2.29.0 from another change

After this delivery passed review at `ff170f0ad`, `main` gained eight commits
up to `9d39eae8b`. Two of them released Core: #1513 (`repository-exploration`)
released `2.29.0`, the version owner decision 6 assigned here, and #1515
(acceptance-authority shadow services) released `2.29.1`. This falsifies T13's
version. The branch was rebased
onto `origin/main` (`9d39eae8b`), which also moved the Makefile the plan-digest
pins read.

## 2026-10-07 — Owner decision 8 (eugenelim)

8. **Release version.** Rebase onto `origin/main` and take Core `2.30.0`
   everywhere this delivery states its version, superseding decision 6's
   `2.29.0`.

The version rule in `packs/AGENTS.md` bumps patch for changed content and minor
for new primitives. The owner reads this delivery's new resolver, which ships
as a script in two skills and changes what both consumers return, as a minor
change, as decision 6 already did. `tools/check-core-release.py --base
origin/main` therefore refuses with `version is 2.30.0, expected the patch
successor 2.29.2`; that check expects patch releases and runs in no CI workflow
or Makefile target.

## 2026-10-07 — Completion evidence handoff, superseding the earlier record

This record replaces the 2026-10-07 completion handoff above, which named Core
`2.29.0` before owner decision 8. Every field not listed here is unchanged.

- **Delivery:** work-loop run `a0cadd63-4cf6-47d4-8184-141c3ed2e371`, which replaced run `92bc8766-7fb1-4d67-b06a-3f5ffbf0e702` after an engine reset; branch `eugenelim/feat-0003`, rebased onto `origin/main` at `9d39eae8b`.
- **Implemented scope:** tasks T1–T15; this delivery releases Core `2.30.0`.
- **Durable outputs:** the changelog entry `[core][2.30.0]`; `main`'s `[core][2.29.0]` entry belongs to `repository-exploration`.
- **Pull request:** `pull-request-opened` — #1516 on 2026-10-07; merge awaits the owner's review.
