# The file-safety contract

When you install a pack from this catalogue, the install verb writes
files into your repo — `AGENTS.md`, `docs/CHARTER.md`, skill
directories, hooks. If you've already edited any of those files (or
the upgrade you're running has new content for them), what happens?

The short answer: **your edits are never silently overwritten**. This
page explains the long answer — what mechanism makes the guarantee
hold, how it differs by install route, and where the contract is
authoritative.

## The three tiers

The catalogue models every path in your repo as one of three tiers:

- **Tier-1** — files the catalogue writes and considers its own. The
  pack's seeds and projections. On install, these can be written
  freely; on upgrade, they're replaced *if* the on-disk content
  matches what the catalogue last wrote (i.e. you haven't edited it).
- **Tier-2** — files the catalogue wrote and you subsequently edited.
  The CLI tracks this by hashing every projected file at install time
  into `.agentbundle-state.toml`; on upgrade, a hash mismatch means
  Tier-2.
- **Tier-3** — files outside the pack's projected paths. Your source
  code, your own `docs/<thing>.md` that no pack ships, your
  `.gitignore`, your CI config. The catalogue never reads, writes, or
  even acknowledges these.

The guarantee in one sentence: **the install and upgrade verbs touch
Tier-1 only.** Tier-2 collisions land as companions; Tier-3 files are
invisible.

## What the catalogue actually does on collision

### First-install collision (CLI route)

If `agentbundle install` would write `AGENTS.md` and you already have
one, it drops `AGENTS.upstream.md` next to yours and leaves your
`AGENTS.md` alone. The `adapt-to-project` skill picks up these
companions and proposes a merge per file — accept, edit, skip, or
decline.

### Upgrade collision (after CLI install or `agentbundle init-state`)

The CLI records a SHA-256 of every projected file in
`.agentbundle-state.toml` at install time. On the next
`agentbundle upgrade --pack <name> --to <version> <catalogue>`, any
file whose content diverged since install (Tier-2) gets a
`*.upstream.<ext>` companion dropped next to it; your edited file is
left alone and the CLI continues without prompting. The merge UI lives
in the `adapt-to-project` skill, which you re-invoke after the upgrade
to walk the new companions one at a time. RFC-0001 specifies a richer
in-CLI prompt with a `<path>.pre-update.bak` overwrite path; v0.1
ships the companion-drop only.

### Tier-3 (everything else)

Untouched on install and on upgrade — including files in directories
the catalogue *does* write to but at sibling paths the catalogue
doesn't claim (your `docs/your-decisions.md` next to the pack's
`docs/architecture/overview.md`, for instance).

## Scope of the guarantee — by install route

The contract binds the `agentbundle` CLI's install path and the
`adapt-to-project` skill. APM (`apm install`) and Claude Code plugins
(`/plugin install`) are governed by *those tools'* native file-handling
semantics; the catalogue cannot intercept them.

The three routes differ:

| Route | Install-time safety | Upgrade-time safety |
| --- | --- | --- |
| `agentbundle install` (CLI) | Companion drop on Tier-2 collision. | Companion drop on Tier-2 divergence (`.agentbundle-state.toml` is the baseline). |
| `apm install` | APM's own conflict rules apply (it compiles straight to the working tree). | Same — unless you ran `agentbundle init-state` once after the install, which hashes the just-installed files. From that point forward the catalogue contract applies. |
| `/plugin install` (Claude Code) | Install-time collisions don't arise (plugins install into a Claude-managed cache, not your working tree). | Re-emerge only if you copy the cached files into your tree by hand — in which case run `agentbundle init-state` first if you want catalogue-level safety on subsequent upgrades. |

If you installed via APM or a Claude plugin and want the catalogue's
upgrade-safety guarantee, the one-time gesture is:

```bash
agentbundle init-state
```

This walks the projected paths the catalogue knows about and hashes
each into `.agentbundle-state.toml`. After that, `agentbundle upgrade`
behaves identically across all three install routes.

## Seeds, by install route

The Tier model above applies to **seeds** (`AGENTS.md`, `docs/CHARTER.md`,
governance docs) the same as to projected primitives — but *which route lands
them in your working tree* differs, and this is the same CLI-vs-cache split as
above:

- **CLI route** (`agentbundle install`) writes the seeds directly into your
  repo (repo root and `docs/`) with the first-install companion behaviour
  described above, and records them in `.agentbundle-state.toml`.
- **APM and Claude-plugin routes** ship the seeds *inside* the installed
  artifact (the APM package / the Claude-managed plugin cache), but do not
  place repo-root governance docs in your working tree — the plugin cache and
  APM HookIntegrator project primitives, not seeds, and the install-marker
  `SessionStart` hook writes only the marker. To land the seeds, run
  `agentbundle install` or `agentbundle scaffold --pack <name> --output .` (the
  `agentbundle` CLI those routes already need on PATH).

A session-time auto-copy of seeds out of the plugin cache would cross the "the
catalogue cannot intercept APM/plugins" line above; it is deliberately not done.
See [RFC-0001 § Errata](../../rfc/0001-bundle-distribution-by-adapter-spec.md#errata).

## Why this exists

The simplest alternative would have been: overwrite Tier-1 files on
install, ask the adopter to put `AGENTS.md` and `docs/CHARTER.md` into
`.gitignore` if they want to edit, and let `git diff` handle the rest.
We rejected that because the files the catalogue ships are
*deliberately* the ones adopters need to edit — `AGENTS.md` is the
project's agent context; `docs/CHARTER.md` is the project's own
mission statement. Asking an adopter to gitignore those is asking them
not to use the catalogue's most load-bearing seeds.

Tier-2 + companions are the design that lets the catalogue ship
opinionated seeds *and* respect adopter edits — both, not either-or.
The cost is a slightly more involved merge step (the
`adapt-to-project` skill), which is worth it because the alternative
(silent overwrite) destroys trust on the first upgrade.

## Where the contract is authoritative

This page is *explanation* — it tells you what to expect and why. The
authoritative source for the contract's exact behaviour is the RFC
that specified it:

[**RFC-0001 § Adopter file safety contract**](../../rfc/0001-bundle-distribution-by-adapter-spec.md#adopter-file-safety-contract)

If this page and RFC-0001 disagree, RFC-0001 wins and this page is the
bug.

## Related

- [How to adapt a freshly-installed pack](../how-to/adapt-to-project.md) — the skill that walks `*.upstream.<ext>` companions.
- [How to upgrade an installed pack](../how-to/upgrade-packs.md) — the verb that produces upgrade-time companions.
- [`docs/CONVENTIONS.md` § Pack source-of-truth split](../../CONVENTIONS.md#pack-source-of-truth-split) — the internal mirror of the Tier model, for contributors.
