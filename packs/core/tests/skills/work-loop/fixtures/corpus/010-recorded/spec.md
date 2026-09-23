# Spec: binder-publishing-gate-propagation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [ADR-0073](../../adr/0073-zensical-as-the-v1-binder-renderer.md) — the v1 renderer decision the gate results bear on; unaffected by them, and this spec must not reopen it
- **Contract:** none — `binder-publishing` has no implementation, so no published interface changes here.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. Two conditional triggers were
checked and did NOT fire. (1) Governance/security boundary: the change records
measurements into a pre-RFC design tree and the `metadata.boundaries` set is
unchanged — Z5 confirms `network_fetch` stays dropped rather than reinstating it.
(2) Structural / public-interface: `invocation.md` is an unshipped design document
for a pack with no code, so there is no adopter-facing interface to change. This
was the close call and is recorded as such. Lean fill: Objective + Acceptance
Criteria + Boundaries + Testing Strategy + Assumptions — the last three earn their
place because one AC turns on a design call (which accessible-name mechanism
replaces the falsified one) and because the gate evidence is external to the
repository. -->

## Objective

`docs/architecture/binder-publishing/` carries three unrun verification gates —
**Z5** (does `zensical build` reach the network during a build), **Z6** (does
vendored Mermaid render in a browser with egress blocked), and **V6** (is an
agent's process working directory the skill directory). All three were **executed
2026-08-07**; the run and its controls are recorded in this spec's Testing
Strategy.

A reader of the tree should find each gate's result recorded with the same shape
Z1–Z4 use — finding, confidence, and what it changed — and should find **no
surviving claim that the gates falsified**. One gate falsified a specified
control: Z6 found that the accessible-name mechanism the design specifies is
destroyed at render time. Fixing that claim, and naming the reasoning it
supersedes rather than quietly editing it, is the substance of this change.

Success: the three gates read as run, every claim contingent on them is settled in
the direction the evidence points, and the tree stays internally consistent — the
property `README.md` asserts and the reason the tree is a tree.

## Boundaries

### Always do

- Record what the gate **measured**, not what it implies. A gate result is
  evidence; a design change that follows from it is a decision and gets a `D`-row.
- Name superseded reasoning explicitly, in the tree's established voice — the
  convention `zensical-adapter.md`'s header block and `decisions.md`'s
  *What the Z-gates changed after D40* table already set.
- State gate coverage honestly. V6 was measured on two of seven adapters; the
  other five must be named as unmeasured, with the reason.
- Keep every gate's fallback claim truthful. Where a fallback was itself verified
  (Z6's degradation), say so; where a replacement mechanism was verified, name it
  the way Z4b named the working font form.

### Ask first

- Reopening ADR-0073 or the renderer pin. Z6 **confirms** the vendoring mechanism
  works, so nothing here should touch the renderer decision — if the change starts
  to, stop.
- Widening the closed `markdown_extensions` allowlist. The replacement
  accessible-name mechanism was verified to need no new extension; if a later
  reading suggests otherwise, that is a decision to surface, not to make.

### Never do

- Report a gate as passed on a plausible reading of documentation. Every row added
  here traces to an executed run with a stated control.
- Delete the Quarto Q1–Q28 findings or the historical V-gate table. They are
  retained evidence for a future PDF adapter; only V6's row is live.
- Fix the `converters` bare-relative script-path defect that V6 surfaced. Different
  pack, different concern — it is recorded as a deferral, not bundled.

## Acceptance Criteria

- [x] **AC1 — Z5 is recorded as run and passed.** `verified-findings.md` carries a
  Z5 finding table in the Z1–Z4 shape and a Z5 row in the Z-gate status table
  reading **PASSED** with the date, and the row states the method's strength (no
  attempt made, not merely "succeeds offline").
- [x] **AC2 — every Z5-contingent claim is settled.**
  `security-profile.md` § *The subprocess* no longer says network access during the
  build is "Z5, unverified", and `editorial-model.md`'s `network_fetch` paragraph
  no longer says "Z5 is open". Both record the result, and `network_fetch` stays
  dropped from `metadata.boundaries`.
- [x] **AC3 — Z6 is recorded as run, split by what passed and what failed.**
  `verified-findings.md` carries a Z6 finding table and a Z6 status row recording
  that rendering with egress blocked **passed** and the accessible-name assertion
  **failed**, with the mechanism of the failure named
  (`replaceWith` onto a fresh `div`, plus a closed shadow root).
- [x] **AC4 — the falsified accessible-name claim is corrected everywhere it
  appears.** No file still asserts that the accessible name reaches the rendered
  SVG through the `<pre>`'s `attr_list` attributes. `rollout.md` §
  *Accessibility smoke checks* and `zensical-adapter.md` § *Vendoring Mermaid*
  carry the verified replacement, and the superseded reasoning is named rather
  than silently removed.
- [x] **AC5 — the replacement mechanism is a recorded decision.** `decisions.md`
  carries a new `D`-row for the accessible-name mechanism with its rationale and
  what it supersedes, and the Z-gate correction table gains the Z6 row.
- [x] **AC6 — V6 is answered, and the defensive specification is simplified.**
  `verified-findings.md`'s V6 row is updated in place with the answer (**no** — the
  CWD is the content root) and its adapter coverage. `overview.md` § content-root
  resolution and `invocation.md` § entry-point resolution no longer say `--root` is
  effectively required on the agent surface; both state what was measured, on which
  adapters, and what remains unmeasured.
- [x] **AC7 — the tree's own bookkeeping is current.** `rollout.md` no longer
  lists Z5/Z6/V6 among Phase 1's remaining gates or among the decisions required
  before implementation; U7 records its resolution; `history.md` records the round;
  `README.md`'s status line does not claim gates outstanding that are now closed.
- [x] **AC8 — repository gates pass.** `python3 tools/lint-ruff.py`,
  `SKIP_SAST=1 make build-check`, and
  `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` all exit 0, and
  `git status` is clean but for this change. (That last path is skill-relative, not
  repo-relative — which V6, one of the gates this spec records, is exactly about.)
- [x] **AC9 — a cold `design-reviewer` pass over the tree, scoped to gate
  propagation, returns no unaddressed finding.** Findings are dispositioned
  `apply` or `defer` per the loop's DECIDE rules, and both are recorded in
  `notes/review-2026-08-07.md` (AC12) so the pass leaves an artifact.
- [x] **AC10 — the two defects V6 surfaced outside this tree are captured, not
  fixed here.** The `converters` bare-relative script-path defect and the
  exit-code-2 collision are recorded in `workspace.toml [backlog].open` with
  cold-start-sufficient comments, and surfaced in the PR description.

- [x] **AC11 — the accessible-name replacement names the graphic, adds no lines,
  and its emitted values are allowlisted.** `decisions.md` D46 and
  `zensical-adapter.md` specify `attr_list` attributes on the fence's opening
  delimiter lifted into the Mermaid source by the theme, so the SVG itself carries
  `<title>`/`<desc>`; the per-file transformation table records the fence-annotation
  step as line-count-neutral; and both files carry the allowlist rule Z6h forces —
  an `attr_list` value containing `"` terminates the attribute and admits raw markup,
  and escaping double-encodes rather than fixing it.
- [x] **AC12 — the gate harness and the review record are committed.**
  `notes/harness/` holds the fixture generator, the socket tracer, the browser
  probes, the sandbox profiles, and the per-run JSON; `notes/gate-results-2026-08-07.md`
  holds the transcribed results; `notes/review-2026-08-07.md` holds both review
  passes' findings and dispositions. Phase 1 has to rebuild these gates as CI
  assertions, and prose is not a sufficient handoff.
## Testing strategy

**Verification mode: goal-based check** for every task. There is no code in this
change and none in the subject — `binder-publishing` is a design tree — so a unit
test would assert only that a string is present. The `Done when:` one-liners in
`plan.md` are greps over the tree plus the three repository gates.

**The gate runs themselves are the real-artifact exercise, and they are already
done.** Fixture, method, controls, and raw results are committed under
[`notes/`](notes/) — `gate-results-2026-08-07.md`, and in `harness/` the fixture
generator, the `PYTHONPATH`-injected socket tracer, the browser probes, the two
`sandbox-exec` profiles, the a11y theme shim, and the per-run JSON. Their substance
is *also* transcribed into `verified-findings.md`, which is the tree's own evidence
file: the notes are how Phase 1 rebuilds the gates, the tree is where a spec author
reads them.

What each gate rested on, since an AC that cites a gate is only as good as the
gate's controls:

| Gate | Instrument | Controls that had to pass first |
|---|---|---|
| Z5 | `sandbox-exec` `(deny network-outbound (with send-signal SIGKILL))`, plus a `PYTHONPATH`-injected socket tracer, plus output byte-comparison | trivial process survives (no false positive); IP-literal `connect` killed; DNS-based `urlopen` killed; tracer self-test logged a known request; unsandboxed control succeeded; local file IO still permitted |
| Z6 | headless Chromium, all non-`file://` requests aborted, DOM read via CDP `DOM.getDocument(pierce=True)`, name read from `Accessibility.getFullAXTree` | positive-control run (unvendored, egress allowed) logged the unpkg request **and** rendered — so both detectors were shown to work before the gate run was trusted |
| V6 | the real shipped `mermaid-renderer` skill's own documented Step 1, run with the skill actively loaded; and a live `codex exec` session | the same script invoked through the harness-supplied absolute base directory succeeded, isolating path resolution as the variable |

**Anchor-test sweep: clean.** No test hashes, snapshots, or counts the content of
any file this change edits (`grep` over `packages`, `tools` for content-hash and
line-count assertions against `docs/architecture` returned nothing).

**Not tested here, deliberately.** Z5 and Z6 become CI regression assertions in
`tests/skills/publish-binder/integration/` when the pack is implemented —
`rollout.md` already assigns that duty. Building the harness now would test a pack
that does not exist.

## Assumptions

1. **The transcribed fixture is the real emitted config.** `binder.py` does not
   exist, so "the real emitted `zensical.toml`" means the config block
   `zensical-adapter.md` § *Generated `zensical.toml`* specifies, transcribed
   byte-faithfully — the same standing assumption the Z1–Z4 run made and recorded.
   Surfaced because it is the one place this evidence is weaker than it will be
   once the adapter is written.
2. **Two adapters answering identically settles V6.** `claude-code` and `codex`
   were measured; both put the CWD at the session's project root, by the same
   mechanism. The design change this licenses is a *relaxation* — dropping a
   defensive requirement — and the self-realpath guard is retained, so an adapter
   that behaves differently degrades to the currently-specified behaviour rather
   than to a defect.
3. **`mermaid@11` resolving to 11.16.1 is representative.** The theme bundle
   requests the floating `mermaid@11` tag, so the vendored version is whatever that
   resolves to at vendoring time. The mechanism verified (a global `mermaid` set by
   the bundle's own last line) is a property of the esbuild-produced distribution,
   not of the patch version. The design now says the pack vendors a *pinned* version
   with a recorded digest, which removes the assumption at implementation time.
4. **The theme-side half of D46 is specified against measured browser behaviour,
   not against a documented contract.** Mermaid's `accTitle:`/`accDescr:` directives
   and the fact that a `MutationObserver` registered in `<head>` sees each fence
   before any mount are both verified here, but neither is a stability promise from
   Mermaid or from Zensical's bundle. This is the assumption D46 rests on, and it is
   the reason Z6 has regression duty rather than retiring green: a bundle change that
   moves the mount earlier, or a Mermaid release that renames the directives, breaks
   the name silently and leaves the diagram rendering fine.
