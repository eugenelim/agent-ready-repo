# Amendment 008 — remove the dot-component rule

**Authorised by:** eugenelim, 2026-09-21
**Tier:** contract — removes a § D6 rule, `AC-0065`, and case rows.
**Against:** approved_spec_hash 67ea736e

## Why it goes

**It is a filename-convention denylist, which is the documented antipattern
for path security.** OWASP's path-traversal guidance is accept-known-good,
not reject-known-bad: badness is easier to vary than goodness is to define.
Secret-detection tools in practice match content patterns and entropy, not
filenames — Gitleaks does not look for dotfiles.

**It does not decide the class it names.** A dot prefix is POSIX-only and
most of the secrets it aims at are not dotted: `credentials.json`, `id_rsa`,
`config/prod.env`, `secrets.yml`. It catches `.env` and misses the rest, and
§ D6 already had to disclose that as an accepted residual.

**It contributes nothing to confinement**, verified by running the
derivation. In the argv path slots — the stored-path members —
`/etc/passwd` and `../../etc/passwd` are refused by the re-anchored
`repositoryPath` rule and `a\b` by the character class, all without the dot
rule. (In `grep`'s pattern slot, which is not a stored path, those first
two are admitted with or without it; and in `verification_route.path`,
`a\b` folds to `a/b` and is admitted. Neither is a confinement the dot rule
ever supplied.) `.env` and `.ssh/id_rsa` are *inside the repository* — the
rule was never confining, it was guessing at disclosure.

**It is the one denylist in an allowlist design.** The four-tool allowlist,
the positive character class and the positive path pattern are all shaped
the way the guidance prescribes. This rule was shaped the other way.

## Provenance, recorded because it explains the cost

The parent intent delegates "the trust boundary on a stored command …
confinement", and confinement is fully delivered without this rule. It never
asked for disclosure control over in-repository files. The rule was added
mid-session in reaction to a review finding — a `.git/`-only predicate
admitted `["cat", ".env"]` — and the reaction was to widen the predicate
rather than to ask whether the predicate belonged. It then generated a
residual, a wrong ownership routing to the sibling's obligation 1, a
disclosure paragraph, a gap-list entry and two further review rounds.

## What changes

- § D6 drops the dot-component bullet and its "what it does not reach"
  residual paragraph. One sentence replaces them: the argv rules confine
  paths to the repository and do not decide whether a file is sensitive.
- `AC-0065` is removed, with its Testing Strategy row and scenario.
- **Erratum, 2026-09-21.** `AC-0058` was also removed, two rounds later. It
  required "a component beginning `.`" to be refused at write time — the same
  rule under different words, which is why three sweeps for
  "dot-leading"/"dot-component" all missed it. It was found by mapping every
  criterion to a case-table row and noticing that `AC-0058` was the one row
  with no code and no row behind it. **The mechanism:** a text sweep finds
  the phrasing you already know; mapping criteria to their evidence finds a
  criterion whose evidence no longer exists. The second is what caught it.
- The derivation drops its dot cases; the § D6 case table is regenerated
  from the spike, so the row count moves and the table stays byte-pinned to
  what the script emits.
- The validator drops `_refuse_dot_leading_component` and its call sites.
- The validator's dot test goes with it, and `argv_cases.py` is regenerated
  from the spike rather than hand-edited: 46 rows to 44.
- The gap list in `docs/architecture/security.md` keeps a residual but
  restates it. It no longer discloses the *limits of a partial rule*; it
  discloses the plain fact that the argv rules confine to the repository
  and do not classify sensitivity, so `credentials.json`, `keys/id_rsa`,
  `config/prod.env` and `.env` alike are admitted. The admitted set grew by
  exactly the dot-leading names — in the case table, two rows flipped to
  admit (`["cat", ".git/config"]`, `["cat", ".env"]`) and two were deleted
  (`["cat", ".ssh/id_rsa"]`, `["cat", "docs/.hidden"]`) — while the
  **disclosed risk class** did not
  change, because the rule was never a credential control. The residual is
  also restored to **unowned**: an earlier draft of this amendment routed it
  to the promotion-handoff spec's obligation 1, which round 4 had already
  refuted — that obligation refuses a path resolving *outside* the
  repository, and an in-repository file never does.

## What does not change

Confinement. `repositoryPath` re-anchored on `\Z`, the character class, the
four-tool allowlist, the no-options rule, the arity and size bounds and the
kind-agnostic binding all stand, and the remaining case rows reproduce.

An in-repository file with a sensitive name is now plainly out of scope
rather than partially covered, which is the honest state. It has **no
owner**: the sibling spec's post-resolution confinement obligation refuses a
path resolving *outside* the repository, and an in-repository file never
does, which is why round 4 withdrew that routing. Naming an owner here
would reinstate it.
