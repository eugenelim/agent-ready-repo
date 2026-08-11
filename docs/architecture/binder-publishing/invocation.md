# Invocation contract

> **This file publishes the complete verb table.** Verbs, flags, exit codes,
> entry-point resolution. Where [`outline-and-templates.md`](outline-and-templates.md)
> describes what `outline` and `templates` *do*, their signatures are here — one
> place, so a CI author reads one file.
>
> Written against D-A (strict-only, six flags cut) and D-B (Zensical). Part of
> [binder publishing architecture](README.md).

## Entry-point resolution

The skill has **no single install path**: at contract v0.17 the `skill` primitive
lands in `.claude/skills/`, the shared `.agents/skills/` home (codex, cursor,
gemini, copilot), and `.kiro/skills/`, at either scope. Worse, `author-a-skill.md`
rule 2 is linter-enforced and forbids a skill from referring to its own files by
an install-path prefix. So the contract is defined at two levels:

**Agent invocation (normative, and what `SKILL.md` contains).** The harness or
installer supplies `<skill-dir>`, the directory containing the active
`SKILL.md`. The caller canonicalizes that directory, its `scripts/` child, and
the expected entry point; requires the resolved entry to be a regular file that
remains beneath the canonical `scripts/` directory; and only then launches it.
The current project root remains the content working directory:

```text
["<python>", "<skill-dir>/scripts/binder.py", "build", "binder.toml", "--root=/path/to/project"]
```

The argument-vector form is canonical. A shell-string-only adapter must quote
the resolved entry point with its platform's literal form or refuse when the
path cannot be represented safely. A missing, non-file, resolution-error, or
escaping entry stops before interpreter launch with a bounded installation or
invocation diagnostic; it is not interpreted as a script exit code.

`--root` remains the mechanism that decouples where the script lives from what
it operates on. The installed entry point comes from `<skill-dir>`; content
paths still resolve from the project root or the explicit `--root` value.

> **Gate V6 answered this, and the answer is no.** The agent's working directory
> is **not** the skill directory — measured 2026-08-07 on `claude-code` and
> `codex`, both of which run a script with the CWD of the session's project root.
> That is the content root, so rule 4 of content-root resolution does the work and
> **`--root` is not required** on the agent surface.
>
> It stays in every example above, because *not required* and *not wanted* are
> different: an explicit root is what makes the invocation reproducible outside the
> session that produced it, and it is the only form a `Makefile` or CI step should
> use. `binder.py` still resolves its own realpath and skips content-root inference
> when its CWD is beneath the installed pack, exiting 4 with the message naming
> `--root` — retained for the adapters V6 could not measure.
> [`overview.md`](overview.md#what-repository-scope-means-outside-git) carries the
> full four-rule resolution order and the coverage caveat;
> [`verified-findings.md`](verified-findings.md) carries the measurement.
>
> **What V6 found corrected the caller contract.** Bare-relative skill commands
> resolve against the project root, not the skill directory. CPython then exits
> **2** before the script starts, which collides with the user-action band used
> by credentialed clients and Mermaid Renderer; Node exits **1** with
> `MODULE_NOT_FOUND`. Atlassian, Figma, Linear, Mermaid Renderer, and Markdown to
> HTML now resolve and preflight their installed entry point before launch, so
> neither runtime result can masquerade as missing credentials or dependencies.
>
> **`binder.py` cannot close the collision from inside.** The interpreter exits
> before its first line runs. The preflight above therefore belongs to the
> caller and precedes every exit-code table. Once the entry point actually runs,
> its published exit meanings remain unchanged.

**Non-agent invocation (CI, `Makefile`, cron).** A caller outside an agent session
resolves the script path once, by either:

- exporting **`$BINDER_SCRIPT`** to the absolute path of `binder.py` and invoking
  `python "$BINDER_SCRIPT" …`; or
- consulting the per-adapter path table in `references/invocation.md`, which lists
  the locations the projection uses, across seven adapters and three scopes.

`references/invocation.md` is the single place those paths are written down, so
the skill body never carries a forbidden install-path prefix and CI never has to
guess. Examples below use `$BINDER_SCRIPT` for non-agent callers and the
resolved `<skill-dir>/scripts/binder.py` form for agent callers.

---

## Verbs

**Nine verbs in v1** (`sidecar init` makes ten in Phase 2), one entry point. Value
flags use `=` form throughout, per `skill-script-conventions.md`.

```
python '<skill-dir>/scripts/binder.py' outline   <dir>... [--root=DIR] [--depth=N]
python '<skill-dir>/scripts/binder.py' templates [<name>] [--root=DIR]
python '<skill-dir>/scripts/binder.py' check     [--root=DIR]
python '<skill-dir>/scripts/binder.py' check     --published=DIR <recipe> [--root=DIR] [--param=K=V]...
python '<skill-dir>/scripts/binder.py' inventory <source-root>... [--root=DIR] [--json]
python '<skill-dir>/scripts/binder.py' resolve   <recipe> [--root=DIR] [--param=K=V]...
                                   [--allow-unknown-fields]
python '<skill-dir>/scripts/binder.py' build     <recipe> [--root=DIR] [--param=K=V]...
                                   [--keep-stage] [--no-wait] [--allow-unknown-fields]
python '<skill-dir>/scripts/binder.py' explain   <recipe-or-index> <content-id-or-path> [--root=DIR]
python '<skill-dir>/scripts/binder.py' recipe write <name> [--root=DIR]
python '<skill-dir>/scripts/binder.py' clean     <binder-id> [--publication] [--yes]
python '<skill-dir>/scripts/binder.py' clean     --stale [--yes]
```

### The complete flag surface

That is the whole surface. Stating it as a closed list is the point — D-A's claim
is that the surface is small enough not to need a router, and a claim like that is
only checkable against an enumeration.

| Flag | Verbs | Nature |
|---|---|---|
| `--root=DIR` | all | Selects the content root. **The only flag that selects the confinement boundary**, and the only one that needs a rule — see [`security-profile.md`](security-profile.md). |
| `--param=K=V` | `check --published`, `resolve`, `build` | Parameter substitution, confined to the closed key list in [`binder-recipe.md`](binder-recipe.md). Cannot name a path or reach `[policy]`. |
| `--published=DIR` | `check` | Names the publication to compare against. **Read-only** — it is a path, but never a write target. |
| `--json` | `inventory` | Output format. |
| `--depth=N` | `outline` | Directory depth at which the draft collapses sections. Default 2. |
| `--keep-stage` | `build` | Retains the staging directory for inspection. |
| `--no-wait` | `build` | Exit 8 immediately on lock contention rather than waiting 60 s. |
| `--allow-unknown-fields` | `build`, `resolve`, `check --published` | Downgrades the unknown-field error to a warning for forward compatibility with a newer producer. Never applies inside `[policy]`, and never downgrades the not-yet-implemented class. |
| `--publication`, `--stale`, `--yes` | `clean` | Scope and confirmation. |

**`--editorial=DIR` is cut**, and it was the last one hiding. D41 says no verb
takes a caller-named write destination; `recipe write` still had one. It was also
unreachable as specified — the write set admits only the editorial directory
beneath `recipes_dir`, so any other value was exit 6 and the flag could only name
what would have been derived. `recipe write <name>` now derives
`<recipes_dir>/<name>.binder.toml` and `<recipes_dir>/editorial/<slug>.md`. See
[`outline-and-templates.md`](outline-and-templates.md#3-recipe-write--the-editorial-write-path).

### The six cut flags, and where their job went

D-A cut these. They are listed because a reader arriving from an earlier draft, a
committed `Makefile`, or a stale CI job needs to know they are gone rather than
renamed.

| Cut | Where the job went |
|---|---|
| `--profile=strict\|trusted` | Nowhere. Strict is the only profile and there is no way to relax it. |
| `--quarto=PATH`, `$BINDER_QUARTO` | Nowhere. D-B made the renderer a module of the running interpreter (`sys.executable -m zensical`), so there is no binary to locate and no path to poison. |
| `--out=PATH` | `resolve` writes to the workspace and prints its path; CI reads it there. `outline` prints its draft to stdout; `templates <name>` writes to a derived path in `recipes_dir`. **No verb takes a caller-named destination.** |
| `--replace-foreign-dir` | Nowhere. A publication directory that is not ours is exit 4; the caller empties it themselves. |
| `--force-unlock` | `clean --stale`. Deleting state deliberately is a different act from being handed a flag that breaks another process's lock. |
| `--from-index=PATH` | Nowhere. `build` always resolves. Invariant 21 means identical inputs give a byte-identical index, so "the thing I approved" is still what gets built — which was the flag's only real purpose, obtained for free. |

There is no `install-quarto` verb. There is no install verb at all: the renderer
is one pinned pip package and the ladder is a single command, in
[`zensical-adapter.md`](zensical-adapter.md).

**Every destination is derived, not supplied.** That is the property D-A was
actually reaching for, and it is stronger than routing `--out` through a lattice
would have been: there is no unbounded write primitive reachable from the
invocation string because there is no caller-named write target anywhere in the
contract.

### Path resolution

A relative `<recipe>` is resolved against the **resolved content root**, never
against the process working directory. An absolute `<recipe>` is used as given and
must still resolve beneath the content root.

**The reason is no longer the one this file used to give.** It said CWD-relative
resolution would look inside the installed pack, *because the agent's working
directory is the skill directory* — which V6 measured as false. The rule survives
its premise: CWD-relative resolution happens to be correct on both adapters V6
measured and would be wrong on any adapter that runs a script from the installed
pack, and **a resolution rule must not depend on which adapter is driving it.**
Anchoring to the resolved root is the same told-not-asked relationship the `nav`
and the read accessor have.

---

## `check --published` — the CI staleness gate

```
python '<skill-dir>/scripts/binder.py' check --published=DIR <recipe> [--root=DIR] [--param=K=V]...
```

This is the reason source hashes are recorded at all. **It takes the recipe**,
because the stamp deliberately contains no source paths (D37) and the workspace
index is gitignored and absent in a fresh clone — so without a recipe there is
nothing to tell the verb which files to re-hash. The flow is:

1. Resolve `<recipe>` — the same resolution `build` would do, no renderer needed.
2. For each resolved node, compute `sha256(content-id)` and the content hash.
3. Read `DIR/binder-stamp.json` and compare the two node sets.
4. Compare the stamp's `pack-version` first. The index is additive-only, so a new
   optional field changes its bytes on every pack upgrade — comparing hashes
   naively would make one upgrade fail `check --published` across every committed
   publication in every repository, with no source change and no way to tell
   "sources drifted" from "the compiler's emission drifted". A version mismatch is
   therefore **exit 10, `rebuild-recommended`**, distinct from stale.
5. Then compare `index-sha256`. The index is byte-reproducible (invariant 21) and
   carries no paths, so hashing it discloses nothing and catches everything —
   including a reorder, a renamed section, an item moved into a part, or a changed
   `label`, none of which alter the node set or any content hash but all of which
   make the publication no longer match its recipe.
6. Exit `0` on a match; exit `9` otherwise. The per-node `id-sha256`/`sha256`
   comparison then runs only to *explain* the mismatch — naming which documents
   changed, and which were added or removed.

> **`id-sha256`, not "content-key".** The workspace directory name is the
> *content-key* ([`runtime.md`](runtime.md)); the per-node hash of a content-id is
> `id-sha256` ([`resolved-index.md`](resolved-index.md)). One word for two
> unrelated hashes is how a reader ends up looking for the wrong one.

An earlier draft gave the verb neither a recipe nor an index, which made exit 9
unreachable and left the SHA-256 field as the receipt theatre this design's own
rule forbids.

**`check --published` never touches the renderer.** It resolves and compares
hashes, both of which are renderer-free, so it exits 0 or 9 whether or not
`zensical` is installed. Under Quarto this mattered a great deal — it kept a 236 MB
toolchain out of the freshness job. Under D-B the saving is a 12.2 MB pip install,
so the property is now a tidiness argument rather than a cost argument, and the
design says so rather than inheriting the old justification.

---

## `outline`, `templates`, and `inventory`

**`outline` is read-only and writes nothing.** It prints a draft recipe to stdout;
the caller — an agent with `Write`, a human with a shell redirect — decides where
it lands. An earlier draft gave it `--out=PATH`, which D-A cut along with every
other caller-named destination. Making the verb purely read-only is what its own
documentation already claimed.

**`templates` has a derived destination.** `templates` with no argument lists what
is discoverable; `templates <name>` copies that template to
`<recipes_dir>/<name>.binder.toml`, refusing an existing path. The destination is
computed from `recipes_dir` and the template name, so nothing in the invocation
string picks it.

**`inventory` runs the same trust scan** as discovery — it reads source bodies and
hands the results to the editorial pass, which is the situation D29 exists to
cover. It does not fail the whole verb on one bad file, because an inventory that
dies on a single unsafe document is useless for triage: an unsafe candidate is
returned with `unsafe: true` and the violating construct named, so the editor can
route around it.

**At Level 0 it** returns, per candidate: normalized content-id, relative path,
size, first H1 if the document has one, diagram count, and that `unsafe` flag. It
does *not* return `kind`, `status`, `subject`, or `producer` — those are Phase-2
metadata and the verb says so in its output header rather than emitting empty
fields. That is enough for the editorial pass to choose what to read in full; the
pass reads bodies itself, which is why it is dispatched with `Read`/`Grep`/`Glob`.

---

## Consent

**`clean --yes` is the only consent flag, and it is a plain flag.** Deleting a
directory the caller named is an ordinary confirmation, not a trust decision.

Everything that previously needed a consent *token* — the version-matched
`--consent=install-quarto-<version>`, its distinct rung-1 variant, and the
argument about whether any of it was a mechanism or a convention — went with the
236 MB download that motivated it. The renderer install is one `pip install` the
user runs, and the skill's part in it is to detect, ask, and re-verify. See
[`zensical-adapter.md`](zensical-adapter.md).

**The `CI` guard survives.** The skill still declines to install when `CI` is set,
because an unattended pipeline should provision its own dependencies rather than
have a skill do it mid-run. It is nearly free and
[`zensical-adapter.md`](zensical-adapter.md) bounds it honestly: a guard
against an accidental install, **not** a control against a hostile pipeline, which
could unset the variable. What went is the *token*, not the check.

That is a substantial simplification and it is worth naming why it was available:
the consent machinery existed because the pack was going to fetch and execute a
third-party binary. It never was a good mechanism — round 6 downgraded the `CI`
refusal to "a guard against accident" for exactly the reason D-A generalises. D-B
removed the thing it was guarding.

---

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected internal error |
| 2 | Renderer not installed |
| 3 | Renderer present but not the pinned version |
| 11 | Python older than 3.11 — a *different* remedy from 2, and the reason it is a different code |
| 4 | Recipe validation error (schema, unknown field, not-yet-implemented key, version, cross-section constraint, foreign publication directory) |
| 5 | Resolution error (ambiguity, missing required, cycle, collision) |
| 6 | Security rejection (path escape, unsafe construct, refused content root, non-Markdown node read, write outside the write set) |
| 7 | Renderer failure (including a `nav` target that was never staged, and a `--strict` build reporting issues) |
| 8 | Lock contention |
| 9 | Published output is stale (`check --published`) |
| 10 | Published output was built by a different pack version — rebuild recommended, not stale |
| 130 | Interrupted (SIGINT) |

Distinct codes for 4/5/6 let CI treat "the recipe is wrong", "the recipe cannot be
resolved", and "someone committed a file with a `<script>` in it" as different
alerts.

**Exit 6 no longer includes "unauthorized profile".** There is no profile to
authorize. What remains under 6 is path and write confinement — the refusal-grade
rules, which are the ones that were doing the work all along.

---

## Invocation examples

**Agent, user-scope install, unrelated directory with no Git and no configuration:**

```bash
python '<skill-dir>/scripts/binder.py' build binder.toml --root=/Users/dev/scratch/vendor-eval
# → /Users/dev/scratch/vendor-eval/build/binders/vendor-eval/index.html
```

**Agent, repository scope, named recipe, parameterized:**

```bash
python '<skill-dir>/scripts/binder.py' build binders/architecture-review.binder.toml \
  --root=/Users/dev/proj --param=subject=payments-migration
```

**Agent, resolve without rendering (no renderer needed):**

```bash
python '<skill-dir>/scripts/binder.py' resolve binders/architecture-review.binder.toml \
  --root=/Users/dev/proj --param=subject=payments-migration
# → .binder-work/architecture-review/8f3a91c2/binder-index.json   (path printed)
```

**Agent, draft a first recipe from a folder:**

```bash
python '<skill-dir>/scripts/binder.py' outline docs/ --root=/Users/dev/proj > binders/draft.binder.toml
```

**CI staleness gate (non-agent caller):**

```bash
export BINDER_SCRIPT="$HOME/.agents/skills/publish-binder/scripts/binder.py"
python "$BINDER_SCRIPT" check --published=docs/published/release-readiness \
  binders/release-readiness.binder.toml --root="$PWD"
# exit 0 fresh · 9 stale · 10 rebuild recommended
```

---
