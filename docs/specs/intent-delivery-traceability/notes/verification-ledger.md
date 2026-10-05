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
