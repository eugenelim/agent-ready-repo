# Invocation contract

> **Updated for D-A and D-B.** Six flags were cut (`--profile`, `--quarto`,
> `--out`, `--replace-foreign-dir`, `--force-unlock`, `--from-index`) and two
> verbs added (`outline`, `templates`, plus `recipe write`). The verb list below
> predates that; treat [`open-decisions.md`](open-decisions.md) D-A and
> [`outline-and-templates.md`](outline-and-templates.md) as authoritative where
> they differ.

> Verbs, flags, exit codes, entry-point resolution.
> Part of [binder publishing architecture](README.md).

## Command and invocation contract

### Entry-point resolution

The skill has **no single install path**: at contract v0.17 the `skill` primitive
lands in `.claude/skills/`, the shared `.agents/skills/` home (codex, cursor,
gemini, copilot), and `.kiro/skills/`, at either scope. Worse, `author-a-skill.md`
rule 2 is linter-enforced and forbids a skill from referring to its own files by
an install-path prefix. So the contract is defined at two levels:

**Agent invocation (normative, and what `SKILL.md` contains).** Skill-relative,
exactly as `mermaid-renderer` does it — the agent's working directory is the skill
directory, and the *content* root is supplied explicitly:

```bash
python scripts/binder.py build binder.toml --root=/path/to/project
```

This is why `--root` exists. It is the mechanism that decouples "where the script
lives" from "what it operates on", and it is what makes the contract independent
of both the current shell and the adapter layout.

**Non-agent invocation (CI, `Makefile`, cron).** A caller outside an agent session
resolves the script path once, by either:

- exporting **`$BINDER_SCRIPT`** to the absolute path of `binder.py` and invoking
  `python "$BINDER_SCRIPT" …`; or
- consulting the per-adapter path table in `references/invocation.md`, which lists
  the locations the projection uses, across seven adapters and three scopes.

`references/invocation.md` is the single place those paths are written down, so
the skill body never carries a forbidden install-path prefix and CI never has to
guess. Examples below use `$BINDER_SCRIPT` for non-agent callers and
`scripts/binder.py` for agent callers.

### Verbs

Seven verbs in v1 (`sidecar init` makes eight in Phase 2), one entry point. Value
flags use `=` form throughout, per
`skill-script-conventions.md`.

```
python scripts/binder.py check     [--root=DIR] [--renderer=quarto] [--quarto=PATH]
python scripts/binder.py check     --published=DIR <recipe> [--root=DIR] [--param=K=V]...
python scripts/binder.py inventory <source-root>... [--root=DIR] [--json]
python scripts/binder.py resolve   <recipe> [--root=DIR] [--param=K=V]... [--out=PATH]
python scripts/binder.py build     <recipe> [--root=DIR] [--param=K=V]...
                                   [--from-index=PATH]
                                   [--profile=strict|trusted]
                                   [--keep-stage] [--no-wait] [--force-unlock]
                                   [--allow-unknown-fields] [--replace-foreign-dir]
python scripts/binder.py explain   <recipe-or-index> <content-id-or-path>
python scripts/binder.py clean     <binder-id> [--publication] [--toolchain] [--yes]
python scripts/binder.py clean     --stale [--yes]
python scripts/binder.py recipe write <recipe-path> [--root=DIR] [--editorial=DIR]
python scripts/binder.py install-quarto --consent=install-quarto-<version> [--version=V]
```

**`--from-index=PATH`** builds from an index the caller has already seen and
approved, instead of re-resolving. **A supplied index is untrusted input, not an authority.** It is a caller-owned
file that can be committed, and it carries `profile`, every `source-path`, and
`assets[]` — so invariant 3's `read_node_source` allowlist would be the attacker's
allowlist if the file were trusted. The check is therefore **re-resolution**:
`build` resolves the named recipe and requires the result to be byte-identical to
the supplied index. Invariant 21 makes that exact and cheap, and it preserves the
flag's purpose — the bytes match whenever nothing has changed, which is precisely
the "I already approved this" case. A mismatch is **exit 4**, naming the first
differing field. The `profile` in a supplied index is re-authorized against the
policy file like any other request; it never grants. This is what makes the resolve → review →
"proceed?" → build interaction honest: without it, `build` would re-resolve and
the user would have approved a possibly different index. Omitting the flag
re-resolves, which is the right default for an unattended run.

**Path resolution.** A relative `<recipe>` is resolved against `--root`, never
against the process working directory — because the agent's working directory is
the *skill* directory, so CWD-relative resolution would look for the recipe inside
the installed pack. An absolute `<recipe>` is used as given and must still resolve
beneath the content root.

`--out=PATH` is **confined**, not exempt. It must resolve beneath the workspace
directory, the publication directory, or the platform temp directory — which
covers the CI motivation (`/tmp`) without leaving an unbounded write primitive
reachable from the invocation string. Anything else is exit 6. An earlier draft
made it a deliberate exception; that contradicted the threat model's own rule
that "any control that a command-line flag can switch off is therefore not a
control", and controls 21 and 25a exist for precisely this class.

`check --published=DIR <recipe>` is the CI staleness gate, and the reason source
hashes are recorded at all. **It takes the recipe**, because the stamp deliberately
contains no source paths (D37) and the workspace index is gitignored and absent in
a fresh clone — so without a recipe there is nothing to tell the verb which files
to re-hash. The flow is:

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
6. Exit `0` on a match; exit `9` otherwise. The per-node `content-key`/`sha256`
   comparison then runs only to *explain* the mismatch — naming which documents
   changed, and which were added or removed.

An earlier draft gave the verb neither a recipe nor an index, which made exit 9
unreachable and left the SHA-256 field as the receipt theatre this design's own
rule forbids.

**`check --published` never probes the renderer.** It resolves and compares
hashes, both of which are Quarto-free, so it exits 0 or 9 regardless of whether
Quarto is present. That matters because *CI provisioning* puts the 236 MB
toolchain behind a path filter — the job asserting "the committed publication is
fresh" is exactly the one that should not pay for a renderer it never invokes.
Renderer-detection precedence applies only to `check` **without** `--published`,
and to `build`.

**`inventory` runs the same trust scan** as discovery — it reads source bodies and
hands the results to the editorial pass, which is the situation D29 exists to
cover. It does not fail the whole verb on one bad file, because an inventory that
dies on a single unsafe document is useless for triage: an unsafe candidate is
returned with `unsafe: true` and the violating construct named, so the editor can
route around it.

**At Level 0 it** returns, per candidate: normalized content-id, relative
path, size, first H1 if the document has one, diagram count, and that `unsafe`
flag. It does *not*
return `kind`, `status`, `subject`, or `producer` — those are Phase-2 metadata and
the verb says so in its output header rather than emitting empty fields. That is
enough for the editorial pass to choose what to read in full; the pass reads
bodies itself, which is why it is dispatched with `Read`/`Grep`/`Glob`.

**Consent is agent-mediated, not TTY-mediated.** An earlier draft made
`install-quarto` refuse a non-TTY stdin — which would have made rung 2 unreachable
on the pack's *primary* surface, since an agent invoking
`python scripts/binder.py …` as a subprocess always has non-TTY stdin. It would
also have stranded V4's PEP 668 fallback, which routes to rung 2 precisely when
`pip` is refused.

So consent is an explicit affirmative token:

```
python scripts/binder.py install-quarto --consent=install-quarto-1.10.18
```

**Rung 1 requires a *different* token.** Q13 establishes that `pip install
quarto-cli` executes a `setup.py` that downloads a 236 MB binary with no integrity
verification — functionally an unverified download-and-execute, differing from the
banned `curl … | bash` mainly in who runs the fetch. Ordering it first is a
deliberate availability judgment (it is the route that works in a locked-down
environment), but the user's affirmation should be to the integrity gap, not
merely to "install Quarto". So rung 1's token is:

```
python -m pip install --no-deps --user quarto-cli==1.10.18   # after --consent=install-quarto-unverified-1.10.18
```

and `SKILL.md` requires the agent to state, in the same breath as the size, that
this route does not verify what it downloads and that rung 2 does. The RFC may
reorder the rungs; what it should not do is leave the ordering implicit.

- The token embeds the pinned version and is **refused if it does not match** the
  version about to be installed, so it cannot be committed once and reused across
  upgrades.
- `SKILL.md` instructs the agent to obtain the human's consent — disclosing size,
  URL, and digest — *before* constructing the token. That instruction is a
  dispatch convention, not a mechanism, and is labelled as such.
- The token is **refused when `CI` is set**. This is a guard against an accidental
  install in a pipeline, **not** a control against a hostile one: a committed
  `Makefile` can run `env -u CI python scripts/binder.py install-quarto …`, and by
  this design's own rule an environment variable the invocation can unset is not a
  control. What actually bounds rung 2's blast radius is that it installs a
  **digest-verified** pinned artifact into a **caller-owned cache** and executes
  nothing else — which is the honest reason it is tolerable in a hostile
  repository, and it is recorded as a residual risk rather than a mechanism.

This trades a mechanism that could not work for one that can, and is honest that
the human-in-the-loop part is convention. `clean --yes` stays a plain flag:
deleting a directory the caller named is a different order of decision.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected internal error |
| 2 | Required dependency absent |
| 3 | Dependency present but unsupported version |
| 4 | Recipe validation error (schema, unknown field, not-yet-implemented key, version, cross-section constraint) |
| 5 | Resolution error (ambiguity, missing required, cycle, collision) |
| 6 | Security rejection (path escape, unsafe construct, unauthorized profile) |
| 7 | Renderer failure |
| 8 | Lock contention |
| 9 | Published output is stale (`check --published`) |
| 10 | Published output was built by a different pack version — rebuild recommended, not stale |
| 130 | Interrupted (SIGINT) |

Distinct codes for 4/5/6 let CI treat "the recipe is wrong" and "someone
committed a file with a `{{< env >}}` in it" as different alerts.

### Invocation examples

**Agent, user-scope install, unrelated directory with no Git and no configuration:**

```bash
python scripts/binder.py build binder.toml --root=/Users/dev/scratch/vendor-eval
# → /Users/dev/scratch/vendor-eval/build/binders/vendor-eval/index.html
```

**Agent, repository scope, named recipe, parameterized:**

```bash
python scripts/binder.py build binders/architecture-review.binder.toml \
  --root=/Users/dev/proj --param=subject=payments-migration
```

**Agent, resolve without rendering (no Quarto needed):**

```bash
python scripts/binder.py resolve binders/architecture-review.binder.toml \
  --root=/Users/dev/proj --param=subject=payments-migration --out=/tmp/index.json
```

**CI staleness gate (non-agent caller):**

```bash
export BINDER_SCRIPT="$HOME/.agents/skills/publish-binder/scripts/binder.py"
python "$BINDER_SCRIPT" check --published=docs/published/release-readiness \\
  binders/release-readiness.binder.toml --root="$PWD"
# exit 0 fresh · 9 stale
```

---
