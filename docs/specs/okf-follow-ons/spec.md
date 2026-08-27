# Spec: OKF follow-ons

- **Status:** Shipped
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0087, ADR-0093
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Catalogue maintainers can compile and discover shipped OKF knowledge without
letting untrusted concept metadata alter compiler-owned index structure, without
losing executable coverage of the repeated-compile determinism guard, and
without the architect pack failing discovery. Generated index metadata stays
bounded and deterministic, `OKF012` remains mutation-resistant, and both
affected packs ship internally consistent release metadata.

## Boundaries

### Always do

- Treat concept frontmatter as untrusted data before interpolating it into a
  compiler-owned Markdown index.
- Keep `OKF001`–`OKF012` closed and preserve the compiler's existing exit-code
  contract by escaping bounded display fields instead of adding a diagnostic.
- Verify the `OKF012` test by temporarily deleting the guard's distinguishing
  second render, observing the focused test fail, and restoring the guard.
- Bump and document `catalogue-curation` and `architect` independently because
  each pack owns its release surface.

### Ask first

- Ask before changing the confirmed 200-character input cap or the confirmed
  delimiter and newline escaping rules.
- Ask before changing the OKF profile, diagnostic registry, compiler process
  interface, or discovery schema.
- Ask before combining the two pack release units when that would prevent each
  pack change from remaining independently reviewable.

### Never do

- Never add a diagnostic code, dependency, module boundary, or top-level
  directory for these follow-ons.
- Never make the compiler write the authored OKF bundle root or manually edit a
  generated router projection.
- Never weaken the existing confined-read, confined-write, ownership, or
  deterministic-rendering boundaries to accommodate hostile metadata.

## Testing Strategy

- **Generated index isolation — TDD.** An exact-byte hostile-title fixture
  proves link syntax cannot add an index entry or change its canonical filename
  target. A separate exact generated-entry boundary test drives title, status,
  and a non-string type independently past the 200-input-character cap while
  carrying carriage returns, newlines, Markdown link delimiters, HTML/autolink
  delimiters, and backslashes, proving the common encoding contract is wired to
  all three interpolation points. A third exact-byte test covers AC1's
  destination clause from the path side, pinning the percent-encoded destination
  for a filename carrying an HTML character reference and for one carrying a
  space, so no source path can render an attacker-chosen `href`. The same
  exact-byte root-index assertion pins **entry order** by normalized source
  path: it places `concepts(root)[fake]` before `concepts0`, which a
  rendered-line-bytes key inverts, so it is the standing guard on the frozen
  predecessor AC11 ordering this change restores. Three further tests close the
  non-encodable-input class end to end. Display: a lone surrogate in `title`
  renders as a visible, escaped `\\uXXXX` sequence rather than raising
  `UnicodeEncodeError`, and re-rendering is byte-identical. Paths: a concept
  filename that is not valid UTF-8 is refused by the existing path gate, so it
  never reaches the scan or the sort and fails on the documented `OKF004` exit
  path. Frontmatter: a non-encodable `license`, `boundaries`, or nested
  `x-agentbundle` skill `description` is diagnosed `OKF003` instead of aborting
  the process on the manifest/digest path. All three reuse existing diagnostic
  codes, and non-ASCII values remain accepted throughout.
- **Predecessor spec restoration — goal-based check.** `AC3` is verified by two
  greps over `docs/specs/okf-authoring-projection/spec.md`: the
  fabricated-source-path clause is present in AC17, and
  `Two behaviours shipped narrower` is absent. No durable gate is added — the
  predecessor spec is frozen apart from this authorized restoration, so a
  standing check would guard a file nothing else is permitted to edit.
- **Repeated-compile guard — TDD plus mutation verification.** A focused unit
  test replaces `render_okf_bundle` with a two-result seam, asserts exit 2,
  exactly `OKF012`, and zero pack mutation, then is run once against a temporary
  `second = first` mutation to prove the test fails when the guard is removed.
- **Architect discovery and source-root semantics — manual CLI QA plus
  goal-based generated-output checks.** Production discovery and
  `agentbundle show architect --format json` succeed, the source root declares
  the same content licence as the other managed packs, compilation changes only
  compiler-owned output, and the managed-pack checker passes.
- **Release coupling and regression breadth — TDD plus goal-based checks.**
  Durable pack tests require pack/plugin parity for each release, and a
  repository roster test requires the matching topmost changelog heading for
  both; focused OKF suites and the repository CI chain pass with any
  environment-forced SAST or cleanup skips named exactly.

## Acceptance Criteria

- [x] **AC1:** `title`, `status`, and `type` are each converted to a string,
  capped at 200 input characters, and escaped before compiler-owned index
  interpolation. Each escape rule is stated as a **class**, not as a list of
  members; an enumeration is what let three members slip through review.
  Four classes are covered:
  - Every code point a reader can treat as a line break — the C0 controls, DEL,
    the C1 controls, and U+2028/U+2029 — rendered as a visible escape, so no
    value can look like more than one entry to either a CommonMark renderer or a
    `splitlines()` reader. The class matters rather than the separators alone:
    `\x1b` repaints a terminal below Markdown and `\x00` truncates a
    null-terminating reader.
  - Link and autolink structure (`\`, `[`, `]`, `(`, `)`, `<`, `>`).
  - Code-span and emphasis delimiters (`` ` ``, `*`, `_`).
  - Every GFM extended-autolink trigger, because GFM linkifies a bare `www.`
    host, a `scheme://` URL (`http`, `https` **and `ftp`**), and a bare
    `user@host.tld` address with no surrounding Markdown at all. Two mechanisms
    are used, and which one applies is decided by evidence rather than symmetry:
    - `www.` and `http`/`https`/`ftp` `://` are **escaped**. Escaping the single
      punctuation mark each needs is verified to defuse the trigger on both
      cmark-gfm and micromark, and leaves the text unchanged when rendered.
    - A bare address is **refused**, not escaped — by `OKF009` in frontmatter and
      by the path gate in a path component. cmark-gfm resolves character escapes
      into text before its autolink pass scans, so `ops\@evil.invalid` still
      renders a live `mailto:` link there and `ops&#64;evil.invalid` bypasses an
      escape the same way. Escaping an address would be inert against the
      extension while still corrupting an ordinary `a@b`.

  No display field can therefore emit an inline link, image, autolink, code
  span, or emphasis run, so the canonical filename remains the only `](…)` link
  target and every entry renders as exactly one entry. Frontmatter additionally
  refuses a reference outright: `OKF009` rejects any value containing
  `http://`, `https://`, `www.`, `mailto:`, or a bare address anywhere within it
  — RFC-0087 rejected runtime external fetch, so a URL in metadata is never
  dereferenced and has no supported function. Escaping covers the leg a refusal
  cannot reach: a **directory name** becomes display text in a
  `# OKF index: <name>` heading, where a refusal would instead deny an author a
  legal directory name.
  Concept **bodies** are deliberately not scanned: an organization-specific
  corpus may legitimately point a reader at an internal app or runbook for
  manual follow-up, and the body is where such a pointer belongs, since it
  reaches the agent on descent and is never fetched.

  Index link destinations are the concept's canonical filename with three
  classes percent-encoded. The encoded set in `_LINK_DESTINATION_UNSAFE` is the
  authority; this is a description of it, not a substitute:
  - *Structural* — C0/C1 controls, space, U+2028/U+2029, and `" ( ) < > \ |`.
    These break or escape a CommonMark destination. The separators are encoded
    here as well as in the display table so both legs of one rendered line agree
    on where that line ends.
  - *Reference-forming* — `&`, `#`, `;`, and `%`, because a renderer resolves
    character references *inside* a destination; leaving those literal is what
    lets a concept named `..&#x2F;..&#x2F;SKILL.md` render an attacker-chosen
    `href`, and `%` is encoded so an emitted escape is never read as a literal.
  - *RFC-3986-excluded* — `'`, `^`, `` ` ``, `{`, `}`. These are **not**
    security-relevant here: a link whose destination is `don't.md` already
    produced a working `href`.
    They are encoded for URL validity, and that knowingly trades literal
    fidelity for it — a legitimately named `don't-panic.md` is cited as
    `don%27t-panic.md`.

  Letters, digits, `- . _ ~`, `/`, `! $ + , = @ [ ]`, `:`, and all non-ASCII stay
  literal, so an ordinary destination remains a path the router's reader can
  open. `:` staying literal is safe only because the path gate rejects it in a
  path component; without that gate a concept named `javascript:alert(1).md`
  would yield a live scheme URL for any renderer that does not sanitize schemes,
  so a test pins the refusal and names the dependency. Encoding the whole path
  was tried and rejected twice: it turned a legitimate `café.md` into
  `caf%C3%A9.md` for no security gain.
- [x] **AC2:** A title-variant hostile fixture pins the complete generated
  `references/okf/concepts/index.md` bytes and proves no attacker-selected link
  or extra index entry is emitted.
- [x] **AC3:** `docs/specs/okf-authoring-projection/spec.md` AC17 again states
  that fabricated source paths remain data, and its temporary "Two behaviours
  shipped narrower" boundary paragraph is absent. This is the user-authorized
  exception to the frozen shipped-spec convention.
- [x] **AC4:** A focused `compile_pack` test makes the second
  `render_okf_bundle` call return different files, observes exit code 2 and
  diagnostics exactly `["OKF012"]`, and proves the selected pack is not
  mutated.
- [x] **AC5:** The AC4 test fails when the compiler is temporarily mutated to
  assign `second = first`, then passes again after the real guard is restored.
- [x] **AC6:** `packs/architect/okf/architecture-lenses/index.md` declares
  `license: "Apache-2.0 OR MIT"` and accurately describes the authored root as
  the compiler input rather than compiler-owned output; production OKF
  discovery and `agentbundle show architect --format json` succeed **against a
  locally-resolved catalogue**. That precondition is load-bearing: `show` has no
  `--catalogue` flag, so a bare invocation falls through to the packaged default
  and resolves the remote catalogue, where it exits 1 with the pre-fix
  `missing content license` — indistinguishable from the defect this closes.
  Re-verify with an editable install of this worktree, or by pointing the
  configured source at it; the durable artifact is the roster test, which drives
  `show.run` with this repository as the catalogue.
- [x] **AC7:** Recompiling architect updates only its compiler-owned outputs,
  and `python3 tools/check-okf-managed-packs.py` passes.
- [x] **AC8:** `catalogue-curation` is released as 0.4.3 and `architect` as
  0.15.3 with matching `pack.toml`, plugin metadata, and free-standing
  changelog entries. Each pack's own test asserts generic pack/plugin parity,
  and a repository roster test asserts the topmost matching changelog heading
  for both packs; no release test asserts a version literal. The changelog
  surface is asserted from `tests/roster/` rather than in-pack because
  `tools/lint-pack-test-boundary.py` forbids a pack test from reading above its
  own pack, and `docs/product/changelog.md` is repository-level.
- [x] **AC9:** Focused pack tests, spec-status lint, pack verification, and the
  repository CI chain pass; any SAST or cleanup-sensitive case unavailable in
  the managed profile is recorded as an explicit incomplete leg rather than a
  green local claim.

## Assumptions

- Technical: The shipped compiler interpolates untrusted `title`, `status`, and
  `type` values directly into generated Markdown index lines (source:
  `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py` and
  isolated exploit reproduction on 2026-08-25).
- Technical: The fixed diagnostic registry and existing exit-code contract
  reserve exactly `OKF001`–`OKF012` (source:
  `docs/specs/okf-authoring-projection/spec.md` AC6–AC7 and RFC-0087 D2).
- Technical: No test outside the compiler names `OKF012` before this work
  (source: repository `rg -n OKF012` check on 2026-08-25).
- Technical: Architect discovery fails because its authored bundle root omits
  a content licence, while core and the cost-engineering pilot declare
  `Apache-2.0 OR MIT` (source: production discovery probe and the three bundle
  root files on 2026-08-25).
- Product: The delivery scope is exactly the three PR #1130 follow-ons and
  their required release bookkeeping (source: user confirmation 2026-08-25).
- Product: Index display fields use a 200-character input cap, visible CR/LF
  escapes, and context-complete Markdown escaping; the spec shape is mixed
  (source: user confirmation 2026-08-25, extended by adjudicated secure-design
  review on 2026-08-26 to cover escape-control and HTML/autolink delimiters).
- Technical: `status` is not attacker-reachable — `OKF003` already rejects any
  value outside `{None, "Active", "Deprecated"}` — so `title` and `type` are the
  only live vectors; the `status` leg of AC1 proves the encoder is wired to all
  three interpolation points, not that a `status` threat was open (source:
  `okf_compiler.py` status allowlist, adjudicated review round 9).
- Technical: **The display-field escape set closes link-and-entry forgery and
  single-entry integrity, and the frontmatter gate keeps URLs out entirely.**
  Verified with micromark against both CommonMark and GFM: no metadata value can
  choose a link target, add an index entry, or add a heading — the shipped
  hostile fixture yields exactly one `href`, the canonical filename. Six display
  residuals found during review were closed rather than registered, on owner
  decision to widen the confirmed escape set. Three were closed by escaping the
  members a first pass named: the extra line separators, so a `splitlines()`
  reader and a CommonMark renderer agree on entry count; `` ` ``, `*`, and `_`,
  so a cross-field code span can no longer swallow an entry's own destination;
  and `OKF009` refusing a remote reference anywhere in a frontmatter value
  rather than only as a prefix.

  A later round showed why those three were not enough, and the remaining three
  are the correction. **Each rule is now stated and implemented as a class, not
  as a list.** (i) The member list of line separators omitted `\x1c`, `\x1d` and
  `\x1e` — code points `str.splitlines()` breaks on, reachable through a YAML
  `"\x1c"` escape — while the guard test iterated exactly the members the table
  already escaped, making it a positive control that could not detect an
  omission; the table and the test now both drive the whole C0/DEL/C1 range.
  (ii) The display table escaped U+2028/U+2029 while the destination encoder left
  them raw, so one rendered line escaped a separator in its link text and emitted
  it literally in its destination; both legs now cover the same range. (iii) The
  frontmatter refusal matched `mailto:` but not a bare `user@host.tld`, which GFM
  linkifies on its own, and no rule at all covered path-derived display text, so
  a directory named `www.internal.invalid` rendered a live link in its own
  heading; the predicate now covers bare addresses and `_index_display_value`
  neutralizes the escapable GFM autolink triggers. Escaping rather than refusing
  was the owner's choice for the path leg, so an author is denied no legal
  directory name. Widening the escape set changed no committed generated byte —
  measured across all 67 shipped OKF files in three corpora, zero display values
  or paths carry any control character, autolink trigger, colon, or `@` (source:
  owner decisions 2026-08-27 after adjudicated security review rounds 17 and 21).
- Technical: **The efficacy claim was first verified against the wrong renderer,
  and re-verifying against the right one changed the design.** Rounds 17–21
  verified escaping against micromark alone. micromark implements GFM
  autolink-literal as a tokenizer construct, so a character escape prevents the
  match; cmark-gfm — the renderer this output is actually read through —
  implements it as a post-pass over consolidated text, where `\.` has already
  become `.`. Re-running the sweep against cmark-gfm on 2026-08-27 found two
  things micromark had hidden, both now fixed: `ftp://` **is** an extended-autolink
  trigger there (micromark leaves it inert), and escaping a bare address is
  **inert** against the extension, so the address shape is refused instead of
  escaped. The scheme escapes were confirmed effective on both renderers.
  Verifying a rendering claim against one implementation is not sufficient
  evidence for this boundary.
- Technical: **The bare-address predicate is anchored on `@` for complexity, and
  bounded to what the renderer actually linkifies for precision.** Leading with
  the local part made `re.search` retry at every offset and backtrack a greedy
  class hunting for an absent `@`: 16 000 dotted characters cost 2.7s and the
  frontmatter cap is 65 536 bytes, so one value was roughly 44s of compiler CPU
  across up to 2 000 concepts. A one-character lookbehind makes it a single linear
  pass — 65 536 characters in 0.004s — and every repetition is bounded. The final
  label must end in a letter, which matches cmark-gfm exactly: it linkifies
  `x@y.z` and `a_b@c-d.io` but not `Rev@1.2`, `Deploy@v1.2` or `tag@10.0.0.1`.
  Matching more than the renderer would refuse a legal version string and fail an
  adopter's compile, so the predicate is pinned against the renderer in both
  directions (source: measured 2026-08-27, adversarial review round 22).
- Technical: **The confirmed escape set is knowingly wider than security
  requires in two places, and the descriptions now say so.** `'`, `^`,
  `` ` ``, `{`, `}` are percent-encoded in destinations for RFC-3986 validity,
  not safety — a link whose destination is `don't.md` already produced a working
  `href` — so a
  legitimately named `don't-panic.md` is cited as `don%27t-panic.md`. Intraword
  `_` is escaped although CommonMark never emphasises it, so `cost_model` renders
  as `cost\_model`. Both were left as shipped on owner decision; what changed is
  that the docstring, this AC, the adopter changelog, and the public authoring
  guide no longer claim such a filename "was already unusable as a literal
  destination", which was false (source: owner decision 2026-08-27 after
  adversarial review round 21).
- Process: **AC5's mutation result, recorded durably because the mutant is by
  design temporary.** On 2026-08-27, with the fix committed first so a
  `git checkout --` restore could not delete it, `okf_compiler.py`'s second
  `render_okf_bundle` call was replaced by `second = first`;
  `test_repeated_compile_mismatch_returns_okf012_without_mutation` then failed on
  **both** parameters (`extra-key` and `same-keys-different-bytes`), and passed
  again after restoration, with `git diff` clean on the compiler. The
  `same-keys-different-bytes` parameter is the one that kills a `files.keys()`
  comparison; the run therefore attests the parametrized test as shipped, not its
  pre-parametrize predecessor.
- Process: **The round-21 escape guards were mutation-proven in both
  directions**, 6/6 killed on 2026-08-27, again with the fix committed first: drop
  `\x1c`–`\x1f` from the control class; drop the line separators from the
  destination class; drop the bare-address autolink trigger; drop `_utf8_safe`
  from the diagnostic constructor; drop the bare-address alternation from the
  remote-reference predicate; and re-encode the whole path as the twice-rejected
  wholesale version. The last one is the *permitting* direction — it reddens
  `test_destination_encoding_permits_every_legitimate_filename_shape`, the check
  a suite proving only the blocking direction would have passed. Each mutation
  asserted its anchor matched exactly once before applying, so a stale anchor
  reports a failure rather than skipping green, and the harness verified the
  restore byte-for-byte.
- Process: **AC9's incomplete leg, recorded rather than claimed green.** SAST did
  not run in this environment: the local chain is invoked as `SKIP_SAST=1 make
  ci` because the managed profile does not provide the scanner. The
  `gate-sast` required check on the pull request is the authority for that leg,
  and no local claim substitutes for it. Dependency and container CVE scanning is
  likewise out of scope for this diff, which adds no dependency (source: managed
  profile constraint, 2026-08-27).
- Process: Editing the shipped predecessor spec is an explicit exception to
  `docs/CONVENTIONS.md`'s frozen-spec rule for the requested AC17 restoration
  (source: user confirmation 2026-08-25).
- Process: Each non-cosmetic pack change carries an independent patch version,
  matching plugin version, and free-standing changelog entry (source:
  `packs/AGENTS.md` and `packs/AGENTS.local.md`).
- Process: `plan.md`'s security NFR, AC8 test names, and T1 `Tests:` list were
  corrected in-phase after adjudicated review rounds 11 and 12. Landing them
  required an owner-authorized cohort re-seal, because `loop-engine` applies
  `schedule check-current` to every `CODE-*` transition except `done`, so any
  `plan.md` edit otherwise blocks the run. The re-seal reset
  `review_retry_count` and `current_wave_index`; the durable per-round review
  and adjudication artifacts under `.context/reviews/<run-id>/` remain the audit
  trail, and the underlying tooling conflict is registered as
  `cohort-seal-blocks-in-phase-plan-correction` (source: owner decision
  2026-08-27).
