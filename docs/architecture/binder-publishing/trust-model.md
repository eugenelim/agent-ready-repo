# Trust model

> **Rewritten for D-A and D-B.** The previous version was a four-tier authority
> lattice routing nine input surfaces. Both decisions deleted most of it.

## The model, in one sentence

> **Everything outside the installed pack is untrusted, the profile is strict,
> and there is no way to relax it.**

That is the whole trust model. There is no policy file, no grant, no `trusted`
profile, no origin classification, and no authority tiers — because with nothing
to grant, there is nothing for an authority to decide.

## How it got this small

Five review rounds each found a *different* unrouted input surface — `--profile`,
`$BINDER_POLICY_FILE`, `--quarto`, `--replace-foreign-dir`, `publication-dir`,
`--out`, `--root`, `--from-index`, `--force-unlock`. Each round, the response was
to route one more surface through the lattice.

**That was the wrong response.** A router that must wrap nine surfaces is evidence
the surface is too large, not that the router is incomplete. A caller who wants an
arbitrary renderer configuration is outside this pack's scope and should drive the
renderer directly — the pack does not need to support every combination.

So the surfaces were cut instead (D-A), and then the renderer change (D-B) cut
two more attack surfaces outright. What survived:

| Surface | Kept? | Why |
|---|---|---|
| `--root=<path>` | **Keep** | The one flag that earns its place: it decouples "where the script lives" from "what it operates on", which is what makes the contract survive seven adapter layouts |
| `--keep-stage`, `--no-wait`, `--yes`, `--allow-unknown-fields` | Keep | None reaches a path or a policy |
| `--profile` / the `trusted` profile | **Cut** | Strict-only |
| `binder-policy.toml`, all tiers | **Cut** | Nothing left to grant |
| `--quarto`, `$BINDER_QUARTO` | **Cut** | Also moot under D-B — the renderer is a pip package, not a discovered binary |
| `--out` | **Cut** | `resolve` writes to the workspace; CI reads it there |
| `--replace-foreign-dir` | **Cut** | Refuse to replace a directory that is not ours; the caller can empty it |
| `--force-unlock` | **Cut** | `clean` handles stale state |
| `--from-index` | **Cut** | `build` always resolves; invariant 21 means identical inputs give an identical index, so "the thing I approved" is still what gets built |
| Absolute `publication-dir` | **Cut** | Confined beneath the content root, no exception |
| `[policy] shortcodes` | **Cut** | Moot under D-B — Zensical does not interpret `{{< … >}}` |

## `--root` — the one surface that needs a rule

It is kept because it is necessary, and it needs a rule because it selects the
boundary every path control is measured against.

- **Refusal list, always on.** A resolved content root that is the user home, a
  filesystem root, or an ancestor of `~/.agentbundle/` or the pack itself is exit 6.
- **Every node read is extension-checked** — `*.md`, `*.markdown`, `*.mmd` —
  explicit paths included. Without this, `path = ".aws/credentials"` beneath a
  permitted root would publish a secret.
- **Everything is confined beneath the resolved root** by realpath +
  path-*component* containment, so `root-evil` is rejected against `root`.

This is refusal-grade, not lattice-grade, and the design says so rather than
implying otherwise. A user who deliberately points the tool at a directory gets
what they pointed it at; the rules stop the paths that could only be abuse.

## What D-B deleted

The Zensical spike removed two entire control areas, because both existed only to
work around Quarto:

- **Shortcode neutralization.** Q11 — `{{< env AWS_SECRET_ACCESS_KEY >}}`
  exfiltrating a secret with execution fully disabled — is a *Quarto* behaviour.
  The spike confirmed Zensical passes the sequence through as literal text. The
  design's single most load-bearing security control, and the `[policy] shortcodes`
  key that governed it, are both gone.
- **The reader-toggle layer.** `from: markdown-raw_html` was Quarto's second layer
  behind the scanner, and Q26 showed it destroys Mermaid output anyway. Not
  applicable to Zensical.

What remains is in [`security-profile.md`](security-profile.md): path confinement,
frontmatter rebuild, raw-HTML rejection, remote-resource rejection, asset
allowlisting, resource ceilings, and the write set. All of it is
renderer-independent, which is the property that made it survive a renderer change.

## What this model defends, and what it does not

**It defends against repository content and the invocation string** — source
Markdown, recipes, committed config, and committed `Makefile`s. There is no
mechanism by which any of them can widen what the scanner accepts, because no such
mechanism exists for anything.

**It does not defend against a compromised build environment.** An adversary who
controls the process can replace `python`. Naming this is the point: repository
content and build environment are genuinely different trust levels in CI and in
`git clone`, which is why the confinement rules are worth having, not because they
are a sandbox.

**It does not claim skill scanning is runtime sandboxing**, and the subagent tool
restriction in the editorial pass is a **dispatch convention** interpreted by an
orchestrating model, not a mechanism. The load-bearing guarantee there is write
confinement in the script, which holds however the editor is run.

## The cost, stated

A team whose repository legitimately contains raw HTML in prose cannot publish
those files without editing or excluding them. That is exactly what the `trusted`
profile was designed for, and cutting it is a real loss.

It is accepted for v1 because the corpus gate will say empirically how often it
bites; because `<br/>` in Mermaid labels — the case that actually appeared in the
first real corpus — is verified to work under strict; and because **a profile
added later on evidence is a better profile than one designed against a
hypothetical.** If the corpus gate shows raw HTML is common in real binder
sources, that is the moment to design the relaxation, with data.
