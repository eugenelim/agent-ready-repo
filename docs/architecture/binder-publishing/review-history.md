# Review history (non-normative)

> Part of [binder publishing architecture](README.md).

## Review-convergence summary

*Populated by the mandatory cold `design-reviewer` convergence loop. The design is
not complete until a fresh reviewer returns an unqualified verdict with zero
actionable findings.*

> **This section is historical and non-normative.** It records what changed and
> why, for a future maintainer asking whether a decision was considered. Where it
> disagrees with the body of the document — because a later round superseded an
> earlier fix — **the body governs**.

| Round | Verdict | Blockers | Majors | Minors | Nits |
|---|---|---|---|---|---|
| 1 | MAJOR REWRITE | 5 | 11 | 15 | 0 |
| 2 | MAJOR REWRITE | 5 | 12 | 20 | 0 |
| 3 | MAJOR REWRITE | 3 | 10 | 17 | 2 |
| 4 | MAJOR REWRITE | 3 | 11 | 11 | 2 |
| 5 | MAJOR REWRITE | 3 | 10 | 14 | 4 |
| 6 | **SHIP WITH CHANGES** | 2 | 10 | 10 | 2 |
| 7 | *pending* | | | | |

### Consequential changes made through review

**Round 1** — all 31 findings resolved. The five that changed the design rather
than its wording:

1. **Shortcode handling was self-contradictory** (specified as *escape* in the
   adapter and *reject* in the diagnostics) **and the escape mechanism was
   invented.** Now one behaviour selected by `[policy] shortcodes`, defaulting to
   `reject`, with `escape` using Quarto's documented brace-tripling — added as a
   verified finding (Q18).
2. **`line-offset` as a scalar was provably wrong** — the document's own worked
   example disproved it, since five of eight transformation steps change line
   counts. Replaced with a `line-map` breakpoint array, and the worked example now
   shows the map.
3. **The trust lattice was bypassable by `--profile trusted`**, which mattered
   because the invocation string is repository content in the stated threat model.
   `--profile` now *activates* an existing grant and never creates one; the
   user policy file is the sole grant authority; and CI has a named mechanism.
   (Round 2 tightened this further — see below.)
4. **Environment scrubbing was a denylist** that passed `AWS_SECRET_ACCESS_KEY` —
   the design's own exfiltration example — straight through. Inverted to an
   explicit allowlist.
5. **Three claims were load-bearing but unverified.** Q10a (Mermaid under
   execution-off), Q19 (render-time network), and Q20 (fenced divs under
   `-raw_attribute`) are now marked UNVERIFIED and gated by V1–V3, each with a
   named fallback and a required CI test.

Also changed in substance: `Q10a` separated from `Q10` because the original
conflated an extension-API statement with a YAML-key claim; entry-point resolution
defined (`--root=` plus `$BINDER_SCRIPT` and a per-adapter table in
`references/`, since the skill has no single install path and the linter forbids
install-path prefixes); a second lock added on the publication directory with
`id`-uniqueness and collision validation; cross-section `before`/`after`
disambiguated to a hard error with warning W3 deleted from all four places it
appeared; a not-yet-implemented key class added so a Phase-0 build rejects a
Phase-2 `select` explicitly; Mermaid captions rebound from fence ordinal to
deterministic label with a `fence-sha256` drift warning; raw-HTML Mermaid labels
now rejected at every profile; the editorial subagent's tool set specified as
`Read`/`Grep`/`Glob` so "cannot render" is mechanical rather than asserted; all
four Charter principles assessed and the `converters`-versus-new-pack question
answered against the RFC-0036 precedent; and the current-state analysis corrected
after reading `_append_layout_section`, which reads `[pack.layout.<scope>].parent`
rather than `output_dir` and therefore no-ops for all five sibling packs.

---

**Round 2** — all 37 findings resolved. The five that changed the design rather
than its wording:

1. **The "renderer-neutral" index was not renderer-neutral.** It carried
   `staged-path` (a `.qmd` filename), `line-map` (breakpoints produced by the
   Quarto transformer), and `links[].rewritten` (pandoc anchor syntax) — and
   `resolve`, which runs without Quarto, could not have produced any of them. Split
   into `binder-index.json` (public, neutral) and an adapter-owned
   `renderer-plan.json`, with **invariant 22**: `build` writes no index field.
2. **`check --published` read a file that was never published**, making exit 9
   unreachable and cutting one of the two consumers that justify recording source
   hashes at all. Staging step 14 writes a stamp into `_output/` (round 3 replaced
   the index-copy this round proposed).
3. **The core had an unguarded YAML injection surface.** `binder.toml` is
   caller-owned content and TOML basic strings carry `\n`, so
   `title = "X\nfilters:\n  - evil.lua"` reached top-level `_quarto.yml` keys —
   around the adapter allowlist rather than through it. Added control-character
   validation plus a safe scalar emitter, and, separately, the **label resolution
   order** that Level 0 previously left undefined.
4. **The trust lattice still had two open channels.** `--quarto=./tools/quarto`
   from a committed `Makefile` executed attacker code, and `$BINDER_POLICY_FILE`
   let the same `Makefile` self-grant `trusted` by writing a policy file outside
   the content root. The binary path is now refused beneath the content root
   (control 25a) and `$BINDER_POLICY_FILE` is **removed** — a knob an attacker can
   turn is worse than no knob. What the lattice does and does not defend is now
   stated plainly.
5. **Caption binding was ordinal binding with an extra step.** Labels are derived
   from the ordinal, so inserting a diagram silently rebound every later caption —
   the exact failure D14 opens by describing, protected only by a *warning*.
   Captions are now verified by fence content hash (round 3 moved this to Phase 2
   and settled the exit code at 7).

Also changed in substance: the Quarto floor lowered from an asserted `>=1.8.0` to
the tested `>=1.10.0`, with widening defined as a procedure over the gate matrix;
the three gates collapsed onto **one fixture that is the real generated
`_quarto.yml`**, since testing the keys in isolation verified a configuration the
pack never emits; `EXDEV` handled with a validation-time device check and a
cross-device copy path; the trust scan moved into the resolver so a standalone
`resolve` cannot derive index fields from unscanned content; a third lock added on
the toolchain cache and automatic stale-lock breaking dropped as non-portable; the
`id`-uniqueness scan set defined and the `clean` claim downgraded to match;
`[[appendices]] sections` added so source artifacts can reach an appendix at all;
`--allow-diagram-errors` cut as unimplementable as described; scan exclusions now
warned with an override key; `[params]` given a closed substitution surface;
`binder sidecar init` added so Level 1 is reachable without hand-writing one file
per artifact; a module decomposition and a named v1 cut-line stated; the subagent
tool set relabelled a **dispatch convention** rather than "mechanical", with the
load-bearing guarantee moved into `binder.py`; heading shift clamped at H6;
`escape` made idempotent; `[[pack.runtime-dependencies]]` declared; `quarto check`
dropped from the detection path as unverified and slow; and the unresolved
questions renumbered with a recommendation on each.

**Changed by the user, mid-review:** the install ladder was reordered around
**`pip`**, because `uv` and `pipx` are unavailable or disallowed in many corporate
environments. This also removed a fabricated flag — `uv tool install` has **no
`--no-deps`** (verified against uv 0.11.33; it offers `--excludes`, which takes a
requirements file), whereas `pip install --no-deps` is real. Recorded as Q21/Q22.

---

**Round 3** — all 32 findings resolved. The reviewer's framing was that the *write
side* had not had the adversarial attention the *read side* got, and that was
correct; all three blockers were writes.

1. **Publication replacement could `rmtree` an arbitrary user directory.** With
   `publication-dir = "~/Sites"` — the design's own cross-device example — the
   first build renamed the user's site aside and deleted it. Replacement now
   requires the target to be absent, empty, or stamped as ours, with
   `--replace-foreign-dir` for the caller who means it (round 4 routed that flag
   through the trust lattice — a bare flag was itself repository-controllable).
2. **The published index disclosed more than the design claimed.** "Publishing it
   leaks nothing" was false: the index carries exclusion *reasons* ("superseded by
   RFC-0091"), unresolved gaps ("security assessment … no artifact matched"), every
   source path, and recipe line references — shipped by default to review boards,
   clients, and vendors. Publications now carry a minimal `binder-stamp.json`
   holding only what `check --published` reads.
3. **The confinement root was specified two incompatible ways.** "Confined to the
   content root" in one section, "must resolve beneath a declared source root" in
   the error example — and since `source-roots` is optional, the second reading
   made the Level-0 minimal recipe and the clean-directory fixture resolve
   nothing. Settled: **the content root is the confinement boundary; `source-roots`
   bounds selector scanning only and defaults to `["."]`**.

Also changed in substance: the scanner's rule set split into a **core-owned floor**
(unsafe in any Markdown renderer) and **adapter-declared rules** (shortcodes, raw
pandoc blocks, Mermaid directives), so a core module no longer enforces Quarto
syntax while claiming neutrality; `--out` confined to workspace / publication /
temp instead of being an exemption; `inventory` brought under the same scan with a
per-candidate `unsafe` flag rather than a whole-verb failure; the `contracts/`
mirror **dropped** after reading `contracts/README.md` and RFC-0076 D1/D2 — that
directory is the canonical authored source with a byte-parity gate against the
CLI's `_data/`, so mirroring a pack-payload schema there would have inverted the
authority and pulled a binder schema into the CLI bundle; RFC-0036's *dependency-
weight* precedent (PDF rejected because "LibreOffice headless — a heavy system
dependency") answered directly rather than only its placement axis; the publish
lock and trash sibling declared as the two entries written outside the publication
directory, with parent writability checked at validation; the cross-device check
walking to the nearest existing ancestor; `clean --stale` added for workspaces
orphaned by pack upgrades; `role = "appendix"` removed from the enum as a second
placement mechanism; the `[params]` `"REQUIRED"` sentinel replaced by a `required`
key that does not make a literal string unrepresentable; and the `alt` check
restated as attribute-present rather than non-empty, since a source `![](x.png)`
gives the compiler nothing to invent.

**Cut from v1, not deferred quietly.** The reviewer observed that the cut-line
protected every optional mechanism. `[[sections.items.figures]]` with its
`fence-sha256` protocol and `--if-stale` both moved to Phase 2 — which leaves
`check --published` as the **single** consumer of source hashes and removes a
circular justification, since `--if-stale` was a feature this document invented to
justify a field it also invented.

**Verified against the shipped policy, and corrected against it.** Tier 2's manager
enumeration is `uv`, `npm`, `pipx`, `brew` — **`pip` is not in it**, so the claim
that rung 1 "fully satisfies the shipped Tier-2 definition" was wrong. Both rungs
now state their deviation, and U5 asks for one amendment covering both, with
adding `pip` to the enumeration as the part that actually matters. `pip` is
detected via `importlib.util.find_spec`, not assumed.

**Two more fabricated-command near-misses caught.** `pip install --require-hashes
<spec>` does not work — pip reads hashes only from a requirements file — and the
correct form plus the real sdist hash
(`20b8b672…101571`) are now recorded as Q23, obtained by running the command
rather than recalling it. PEP 668 externally-managed interpreters are a real
failure mode for `--user`, recorded as Q24 and gated by the new **V4**, which
asserts the printed command works verbatim on macOS, Linux-with-PEP-668, and
Windows and that `shutil.which` finds the binary afterwards.

---

**Round 4** — all 27 findings resolved. The write side stayed the weak axis, and
two of the three blockers were controls this document had asserted as absolute
while leaving a channel open.

1. **`--replace-foreign-dir` was a bare flag**, and the threat model says in its
   own words that a control a flag can switch off is not a control. Combined with
   `publication-dir` being settable to an absolute path from a committed
   `agentbundle-layout.toml`, repository content could pick the directory *and*
   the flag that deletes it. Both are now **grants in the user policy file**; the
   flag activates one and never creates one.
2. **Emitted strings bypassed the scanner.** The scanner reads source bodies, but
   `binder.title`, section and part titles, node labels, and source-H1-derived
   titles all reach the renderer's metadata — so `title = "{{< env
   AWS_SECRET_ACCESS_KEY >}}"` falsified control 10's "no configuration passes a
   shortcode through unescaped". The emitted-string validator now rejects
   shortcode and interpolation syntax as well as control characters, and Q25/V5
   record that the underlying renderer behaviour is unverified rather than
   assuming it.
3. **The contract-publication decision was stated three ways.** Round 3 dropped
   the `contracts/` mirror with reasons; Phase 0 and the compatibility table still
   described it. Both corrected — a spec author following Phase 0 would have
   inverted RFC-0076 D1's authority model.

Also changed in substance: invariant 3's enforcement restated at the strength it
holds — the adapter *does* read sources and *is* given `content-root`, so the
mechanical claim is a single `read_node_source(node)` accessor that rejects any
path not in the index, not "it was never given the means"; an **Index surface**
table added with per-node-type required/optional and a two-way forward-compat
rule, since a public contract specified only by example cannot be implemented
against; the stamp's `content-id` replaced by `sha256(content-id)`, closing the
last of the four disclosures round 3 named; the write allowlist restated as a
closed seven-item list after the old three-item version was found to exclude
writes the design itself specifies; consent moved from a TTY test to a
version-matched token, because the pack's primary surface is an agent subprocess
where a TTY test would make rung 2 unreachable; the content-key extended to
include the resolved trust profile, so a strict and a trusted build of one recipe
no longer share a workspace; a **CI provisioning** subsection naming the workflow
file, the pytest path, the Quarto setup step, the path filter, and the 236 MB
per-job cost; `required-params` lifted out of `[params]`, where it had
reintroduced one level down the exact unrepresentability it was added to fix;
`publication-dir` settled to one statement; the worked scenario given a **Path A0**
that is actually v1, with the selector and overlay paths labelled Phase 2 and
Phase 3; control 25a widened to every probe including a `PATH` hit; a Python 3.11
floor declared and detected; V1's fallback corrected to "this reopens D3" after the
named route turned out to require the npm dependency *Portability* forbids; and
the round summaries marked non-normative, since ~200 lines of history had begun
carrying superseded claims.

**Corrected against the shipped guide, in my own disfavour.** Round 3 claimed
`pip` was absent from Tier 2's manager enumeration and therefore that rung 1
deviated. The bullet list omits it, but the section that governs it says
plainly: *"`pip`/`uv` ship with a Python install, so a pip-based Tier-2 install is
low-risk (the manager is almost always there)."* Rung 1 was already sanctioned.
U5 now asks for one amendment (the digest-verified binary fetch) plus an editorial
fix to the bullet list, and the "no conforming install route at all" fallback
language is gone.

---

**Round 5** — all 31 findings resolved. The three blockers were each a mechanism
specified two ways or specified in a form that could not run.

1. **`check --published` had no input.** The verb took neither a recipe nor an
   index; D37 had removed source paths from the stamp and the workspace index is
   gitignored, so nothing identified which files to re-hash. Exit 9 was
   unreachable and D13's single-consumer justification for source hashes
   collapsed with it. The signature is now
   `check --published=DIR <recipe>`, with the comparison flow specified step by
   step — including that a *changed node set* is stale even when every shared
   document is unchanged.
2. **The execution control was stated two incompatible ways.** The scanner's core
   floor listed executable-cell fences as always-rejected while staging step 5
   neutralized them and control 7 called neutralization "the real execution
   control" — and staging step 4 *creates* a `{mermaid}` executable cell, so
   "reject all" could not be literally true either. Settled: the floor rejects
   notebooks only; fences are **neutralized in staging** with `{mermaid}` the one
   exception, and the scanner warns rather than failing.
3. **The provenance appendix republished what the stamp had removed.** D32 and
   D37 stripped source paths and gaps out of the publication; a
   compiler-generated source-inventory appendix, on by default, rendered both
   back in human-readable form. It is now opt-in, with a closed field list that
   may never include a source path, an exclusion reason, or an unresolved gap.

Also changed in substance: the alternatives comparison **split into two axes** —
architecture and renderer-under-architecture-1 — because a single table let
Quarto inherit credit the neutral index and the renderer-agnostic scanner earn,
and because the split bounds D3's revisit condition to Axis B alone; V1's
worst-case branch replaced with its actual mechanism (Q9 engine auto-binding, and
whether the bound engine demands Jupyter); asset path rewriting and collision
handling specified as transformation step 7b with a `renderer-plan.json` mapping,
after the flat stage root was found to break every relative image reference; the
cross-device `.incoming-` directory added to the closed write allowlist it had
been violating; `build --from-index` added to the verb table, since the normative
sequence used a flag the contract did not define; the `CI`-set consent refusal
downgraded from "mechanism" to "guard against accident", with the honest bound
(digest verification plus a caller-owned cache) stated instead; the H6-clamp
record moved from the index to `renderer-plan.json`, where invariant 22 requires it;
content-root rules 2–4 scoped to exclude the case where the working directory *is*
the installed pack, which is the pack's primary surface; `node-id` stability
restated to match invariant 21; `figures[]` moved out of the v1 index as the same
circularity D13 removed for `--if-stale`; `source-roots` and
`scan-exclusions-override` re-marked Phase 2 with a warning, since both bound
selector scanning only; the schema URL given a version-suffixed filename and a
release tag instead of `main`; `PATH` entries resolving beneath the content root
stripped from the child environment as control 26a; `content-root: "."` explained
as an out-of-band anchor; the frontmatter `boundaries` key corrected to sit under
`metadata:` per `skill-and-pack-format.md`; and the RFC-0036 rebuttal rewritten
after the precedent turned out to carry a **third** on-point axis (its Axis A
rejected converter-owned structure — answered by the binder model owning structure
and handing it to the adapter, which is the inverse pattern).

---

**Round 6** — verdict moved to **SHIP WITH CHANGES**. All 24 findings resolved,
and one of them changed the design more than any single finding in the previous
five rounds — because it told the author to stop writing about a gate and run it.

1. **The scanner's position was specified three ways** — the component diagram put
   `SCAN` inside the adapter subgraph downstream of the index, D29 put it at the
   end of discovery, and Phase 0 shipped `resolve` and `inventory` without it. The
   diagram is redrawn, the scanner's core floor moves into Phase 0, and the false
   sentence claiming the trust-boundary diagram showed the ordering is gone.
2. **V1 was run rather than deferred**, and the results are now in the Q-table:
   - **Q10a is CONFIRMED.** Mermaid renders under `engine: markdown` *and*
     `execute: enabled: false`; the diagram handler is genuinely independent of
     the execution engine. The renderer decision no longer rests on an inference.
   - **Q26 is new, and it removed a security layer.** Quarto's diagram handler
     emits its output *as raw HTML*, so `from: markdown-raw_html` — which this
     design used as the second layer behind the scanner — **escapes the emitted
     `<pre class="mermaid">` and destroys every diagram**, inside an otherwise
     perfectly numbered figure. Bisection isolated it: `-raw_attribute-raw_tex`
     renders, `-raw_html` does not. The emitted string is now
     `markdown-raw_attribute-raw_tex`, and the design states plainly that **the
     scanner is the only raw-HTML control** rather than implying redundancy it
     cannot have.
   - **Q20 is CONFIRMED.** Callouts and attributed spans survive every `from:`
     variant; the plain-label fallback is not needed.
   - **Q24 passes on macOS.** The printed rung-1 command produced a working
     `~/.local/bin/quarto` reporting 1.10.18.
   - **Q27 is new, from V2b.** The rendered HTML carries zero absolute references,
     but the stock Bootstrap CSS `@import`s **Source Sans Pro from Google Fonts** —
     so a published binder phones out from the reader's browser. The shipped
     `binder.scss` must override the font stack, and V2b now asserts zero
     `https://` anywhere in `_output/`, CSS included.

Also changed in substance: **text encoding, BOM, and line-ending normalization**
specified, since four normative guarantees silently depended on them and none was
stated; `check --published` freed from renderer detection, because the CI job that
checks freshness is exactly the one that should not provision 236 MB; the stamp
given `index-sha256` so a reorder or a renamed section is detected — the previous
set-and-content comparison reported such a binder fresh; `--allow-unknown-fields`
barred from `[policy]`/`[trust]` tables, where a discarded *tightening* is a
relaxation performed by a flag; U5's refusal consequence corrected to name PEP 668
interpreters as a segment with no in-pack route, making it a blocking dependency
rather than an optional ask; a **distinct consent token** for rung 1 so the user
affirms the integrity gap rather than merely "install Quarto"; **prompt injection
into the editorial pass added to the threat model** as control 31, with the three
structural bounds that make it survivable named; the agent-CWD assumption demoted
to a gated assumption (V6) with defensive behaviour specified both ways; the
trusted profile's `from:` string written down; three-digit staged numbering and
node-ids made consistent across every example; and the developer-workstation route
to a `trusted` grant documented alongside the CI one.

### Findings intentionally not adopted

**Round 1, finding 13 — "demote rung 1 or route it as a policy amendment."**
Adopted in the second form rather than the first, and with a change to the
ordering the finding did not request: the digest-verified managed install is
**offered after `pip`** until the Tier-2 amendment lands (U5), rather than removed. The
governing constraint is that `author-a-skill.md`'s Tier-2 definition is shipped
policy and this design does not get to overrule it silently; the reason for
keeping rung 1 present is that Q13 establishes the conforming route is
*measurably less safe*, and hiding that from the user to satisfy a policy the
policy's own authors have not yet considered would be the wrong trade. The prompt
states the integrity difference so the choice is informed.

No other round-1 finding was declined.



**Round 2, finding 4 — the `$BINDER_POLICY_FILE` decision.** The reviewer offered
two resolutions: restrict grant authority to `~/.agentbundle/binder-policy.toml`
with CI overriding `$HOME`, or keep the variable and re-word the claims to admit
the environment is part of the invocation surface. **Neither was adopted as
offered.** The variable is removed, and CI provisions the one file the tool reads
rather than overriding `$HOME` — because "write the file" requires control of
runner provisioning while "point at a different file" requires only control of the
build command, and those are the two trust levels the lattice exists to separate.
The reviewer's second option is adopted *as documentation*: *What this model
defends, and what it does not* now states that an adversary controlling the
process environment can defeat the lattice, and that nothing at this layer could
prevent it.

No other round-2 finding was declined.

---

**Round 6 — no finding was declined.** Both blockers, ten majors, ten minors, and
two nits were adopted. Blocker 2 was adopted in the strongest available form: it
asked for V1 to be run before the RFC, and running it confirmed Q10a, produced
Q26, and produced Q27 — so the finding's real value was not the check it named but
the two it did not.

**Round 5 — no finding was declined.** All three blockers, ten majors, fourteen
minors, and four nits were adopted. Two were adopted in a stronger form: finding
9's `CI`-refusal was not merely reworded but replaced with the argument that
actually bounds rung 2 (digest verification into a caller-owned cache), and
finding 3's opt-in appendix gained a closed field list and an integration
assertion rather than only a default change.

**Round 4 — no finding was declined.** All three blockers, eleven majors, eleven
minors, and two nits were adopted. One was adopted in a different form than
offered: finding M5 proposed keeping the CI posture by refusing the consent token
when `CI` is set *or* dropping the CI claim; the design does the former, because
pipeline provisioning is already specified and a token refused on `CI` is a
mechanism rather than a convention.

**Round 3 — no finding was declined.** All three blockers, ten majors, seventeen
minors, and two nits were adopted. Two were adopted in a stronger form than
offered: finding B3 proposed publishing a reduced index, and the design instead
publishes a purpose-built stamp so the reduction cannot drift back; finding M7
proposed moving caption binding to Phase 2, and the design also moved `--if-stale`,
because leaving it would have preserved the circular hash justification the
finding was really about.
