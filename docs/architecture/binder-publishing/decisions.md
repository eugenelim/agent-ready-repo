# Decision log

> Part of [binder publishing architecture](README.md).

## Decision log

| # | Decision | Rationale | Revisit if |
|---|---|---|---|
| D1 | Renderer-independent compiler with a neutral resolved index | Only shape where a producing pack participates with `tomllib` alone | The ecosystem seam goes unused for a year — then option 2 is cheaper |
| D2 | `binder-index.json` is a public versioned contract | Invariant 3 gives it a second consumer by definition | Never |
| D3 | ~~Quarto Book as first renderer~~ — **SUPERSEDED BY D40**. Retained as the reasoning a future PDF adapter inherits | Verified fit on structure, navigation, search, theming, Mermaid; no viable Python-native alternative without a plugin surface | Binary weight blocks adoption, or gate V1 fails in its worst form → reopen MkDocs/Zensical |
| D4 | One skill, all script verbs; no second skill | Self-containment forbids cross-skill imports and bars `shared-libs/` for skill code | U11 resolves the other way |
| D5 | Editorial pass is a reference, not a shipped agent; dispatched subagent restricted to `Read`/`Grep`/`Glob` | Skill wins 4 of 6 decision properties; withholding `Bash` is what makes "cannot render" mechanical | Measured context pressure justifies a named agent |
| D6 | Editor-generated prose in separate files, referenced by path | Reviewable in a diff; TOML should not hold paragraphs | Never |
| D7 | Trust is a separate lattice, and **the resolved policy file is the sole grant authority** | A recipe *and an invocation string* are both repository content in the threat model | Never |
| D8 | A separate `trusted` profile exists, with a non-overridable floor | Without it, teams with legitimate raw HTML abandon the pack or demand a blanket escape hatch | The floor proves insufficient |
| D9 | Shortcodes rejected by default; `escape` uses Quarto's verified brace-tripling | Q11 — `{{< env >}}` exfiltrates secrets with execution disabled; Q18 gives the verified escape | Quarto ships a documented global shortcode-disable option |
| D10 | Frontmatter discarded and rebuilt, not filtered | Allowlist by construction survives new Quarto keys; a denylist does not | Never |
| D11 | Non-mermaid executable fences neutralized — the real execution control | Survives a change in engine-binding behaviour, and V1 may force dropping the YAML keys | Never |
| D12 | No prose-parsing of `**Status:**` markers | A parser without a specification constrains every producer; sidecars solve it explicitly | A specified Markdown metadata convention is ratified |
| D13 | Source SHA-256 in the index and the published stamp; no timestamps, run IDs, or host names | **One** consumer, and it is the CI contract: `check --published`. An earlier draft also named `--if-stale`, which this design itself invents — justifying a field by a feature added to justify it is the circularity the anti-receipt-theatre rule targets, so `--if-stale` moved to Phase 2 and the justification now rests on the gate alone | `check --published` is cut |
| D14 | Required items may not be selectors; **captions are verified by fence content hash, and a mismatch is an error** | A silent wrong-binding in a board-approved packet is the worst failure available. Binding by position — directly by ordinal, or by a label *derived* from the ordinal, which is the same thing — is that failure; only a content hash actually detects it, and only an error actually stops it | Never |
| D15 | Unknown fields are a hard error; not-yet-implemented keys are their own class | A silently-ignored `weigth = 10` is bad; a silently-ignored `select` is worse | Never |
| D16 | Tier-1 detection mandatory; consented install offered; Homebrew excluded | Tier-2 forbids sudo; the cask is a `.pkg` (Q15) | Quarto ships a no-admin macOS route |
| D17 | **`pip` is rung 1**; the digest-verified managed install is rung 2, pending a Tier-2 policy amendment | `pip` ships with the Python the skill already requires, and `uv`/`pipx` are absent or disallowed in many corporate environments — so `pip` is both the most available route and the only fully policy-conforming one. Q13 still makes rung 2 the safer one, which is why it stays offered | U5 resolves |
| D18 | Toolchain cache in the platform cache dir, not `~/.agentbundle/` | 236 MB of third-party binary is not a scope-fenced primitive artifact | — |
| D19 | Link-out as the only v1 site boundary | Smallest clean seam; the index makes deeper integration additive | The site needs to host binders |
| D20 | Near-atomic publication via two renames, with a cross-device copy path detected at validation | Portable to Windows; `os.replace` raises `EXDEV` across filesystems and a configurable publication root makes that a normal case, not an edge one; claiming atomicity would be false | An adopter needs live-serving guarantees |
| D21 | TOML is the only human-authored form; JSON accepted from machine producers; only TOML written | `json` is stdlib everywhere, a TOML *writer* is not; one human format preserved | — |
| D22 | Index is byte-reproducible (invariant 21) | Makes CI diffing possible and ceremonial fields structurally impossible | — |
| D23 | `line-map` is a breakpoint array, not a scalar offset, **and it lives in `renderer-plan.json`** | Five of eight transformation steps change line counts, so a scalar is provably wrong; and a line map over `.qmd` files is a Quarto artifact, so it cannot sit in a renderer-neutral contract | Never |
| D24 | Three locks — workspace, publication directory, toolchain cache — plus `id`-uniqueness and publication-collision validation over a defined scan set; no automatic stale-lock breaking | Each lock guards a resource the others do not: the workspace lock does not protect a publication directory two recipes can share, and neither protects a 236 MB extraction two builds can race. Automatic breaking would need PID liveness, which is POSIX-only and unsafe under PID reuse | — |
| D25 | Child process environment built from an allowlist, not filtered | A denylist leaves `AWS_SECRET_ACCESS_KEY` in the child env, which is the exact Q11 exfiltration target | Never |
| D26 | Every claim the design leans on is either sourced or gated, **and the gates that decide the renderer are run before the RFC, not after** | Unverified claims would otherwise sit invisibly under load-bearing decisions — and running V1 proved the point, since it confirmed Q10a *and* produced Q26, which removed a security layer the design had claimed | — |
| D27 | **Two artifacts: a neutral `binder-index.json` and an adapter-owned `renderer-plan.json`** (invariant 22) | A "renderer-neutral" index carrying `.qmd` paths, pandoc anchors, and a transformer line map is a Quarto file with a neutral name — and `resolve` could not write those fields at all, since it runs without Quarto | A second renderer needs a field the index genuinely lacks |
| D28 | Every string emitted into YAML is control-character-validated **and** passes through a safe scalar emitter | `binder.toml` is caller-owned content and TOML strings carry `\n`, so an unguarded `title` reaches top-level `_quarto.yml` keys — going around the adapter allowlist rather than through it | Never |
| D29 | The trust scan runs at the end of **discovery**, not only before staging | `resolve` is a standalone verb that derives index fields from source bodies and writes a published artifact; a scan that only guards staging never runs for anyone who does not call `build` | Never |
| D30 | Grant authority is exactly `~/.agentbundle/binder-policy.toml`; no `$BINDER_POLICY_FILE`, and `--quarto` may not resolve beneath the content root | An environment variable and a CLI flag are both the invocation string, which is repository content; a knob an attacker can turn is worse than no knob | The environment itself becomes a trust boundary we can enforce |
| D31 | The declared Quarto range equals the tested range (`>=1.10.0,<1.11.0`), widened only by running the gates against a candidate | A floor asserted from documentation for versions no gate exercises is the same unverified-claim class Q10a was split out for | — |
| D32 | **Publications carry `binder-stamp.json`, never the index**; replacement requires the target to be absent, empty, or stamped as ours | The index discloses exclusion reasons, unresolved gaps, and source paths into an artifact that goes to boards, clients, and vendors; and an unguarded replace deletes `~/Sites` on first build. Both are write-side failures in a document that had scrutinised only reads | A consumer needs the full index published, in which case it is copied deliberately |
| D33 | **The content root is the confinement boundary; `source-roots` bounds selector scanning only** and defaults to `["."]` | An explicit `path` must work with no `source-roots` declared, or the Level-0 minimal recipe and the clean-directory fixture both resolve nothing | Never — Level 0 is the primary path |
| D34 | The scanner is core-owned **machinery** with a core floor plus **adapter-declared rules** | A core module rejecting `{{<` is enforcing Quarto syntax while claiming neutrality; splitting the rule set keeps D29's reason (scan before the index exists) without the leakage invariant 13 forbids | A second renderer's rules cannot be expressed declaratively |
| D35 | `--replace-foreign-dir` and an out-of-root `publication-dir` are **grants in the user policy file**, not flags | Both are reachable from repository content — a committed `Makefile` and a committed `agentbundle-layout.toml` — and the threat model's own rule is that a control a flag can switch off is not a control. Together they reached `rmtree` on any path | Never |
| D36 | Emitted strings (recipe- *and* source-derived) are validated against `{{<`, `{{{<`, `${` as well as control characters | The scanner reads bodies; titles bypass it, so `title = "{{< env … >}}"` was an unscanned path into the renderer that falsified control 10's absoluteness | Never |
| D37 | The stamp records `sha256(content-id)`, not the content-id | A path list in an artifact sent to vendors and boards discloses which internal documents exist; the staleness contract needs only equality, which a hash provides | A consumer needs human-readable node identity in a publication |
| D38 | Consent is an explicit version-matched token, not a TTY test | The pack's primary surface is an agent subprocess with non-TTY stdin, so a TTY test would have made rung 2 and the PEP 668 fallback unreachable exactly where they are needed | A harness offers a real consent channel |

---

## Post-review decisions

These two reshaped the design after eight review rounds and are the authority
where any earlier row disagrees.

| # | Decision | Rationale | Supersedes |
|---|---|---|---|
| D39 | **Collapse the trust surface rather than route it.** Cut the `trusted` profile, `binder-policy.toml` at every tier, and six flags (`--profile`, `--quarto`, `--out`, `--replace-foreign-dir`, `--force-unlock`, `--from-index`). Strict-only, no grants. | Five review rounds each found a *different* unrouted surface, and each was answered with another lattice rule. A router that must wrap nine surfaces is evidence the surface is too large. The pack does not need to support every combination — a caller wanting arbitrary renderer configuration should drive the renderer directly. | D7, D8, D30, D35 |
| D40 | **Zensical replaces Quarto as the v1 renderer**, established by spike rather than by paper comparison. | 12.2 MB pip wheel against a 236 MB external CLI — and more decisively, Zensical reads portable ` ```mermaid ` fences directly and does not interpret `{{< … >}}`, which deletes the Mermaid staging transformation *and* the shortcode attack surface. Both existed only to work around Quarto. Takes the install ladder, consent tokens, digest verification, PEP 668 handling and the toolchain cache with it. | D3, D9, D11 (partly), D16, D17, D18, D31 |

**Retained as Quarto-adapter evidence, not live design:** D9 (shortcode escaping),
D16–D18 (the install ladder), D31 (version-range procedure). A future PDF adapter
goes through Quarto and inherits all of them.
