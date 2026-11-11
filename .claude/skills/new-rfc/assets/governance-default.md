# Governance

<!-- Adopters: this file is yours. Change any section to match how your project
really works, then delete this note. Replace the maintainer handle below. -->

## Maintainers

- <maintainer-handle>

A maintainer can add another maintainer when the current maintainers agree.

## How decisions are made

Maintainers decide by consensus. Only a listed maintainer's merge accepts a change. If maintainers disagree, they keep talking until they agree. Where one maintainer holds the project alone, that maintainer decides.

## Suggesting a change

Anyone can suggest a change; you do not need write access. Pick the lightest route that fits:

1. **Not sure yet?** Open an issue or start a discussion. Maintainers will say which route below fits. This step is optional.
2. **Bug fix, small improvement, or easy to undo:** open a pull request from a fork.
3. **A decision already made that needs recording:** write a short decision record (an ADR) in `docs/adr/`.
4. **A change that needs agreement:** write an RFC (below).

## When to write an RFC

Write an RFC when the direction is still unresolved and more than one owner must agree, or when you want maintainers to review a proposal before anything is built. Always write one for a change to any of these four things:

- the project's charter: its mission, scope or foundational principles;
- maintainer authority, approval or the governance model, including this file;
- a security trust model;
- the withdrawal or breaking change of a stable, published compatibility promise.

One RFC proposes one change. If a proposal has parts that could be accepted separately, split it.

Start one with `python3 -I docs/rfc/rfc.py new "Short title"`. If you cannot run Python, copy `docs/rfc/template.md.tmpl` to `docs/rfc/XXXX-short-title.md` and a maintainer will number it. Then open a pull request. A fork is enough.

Maintainers: to check a contributor's branch, run your own copy of `rfc.py` from the default branch, never the one in their branch: `python3 -I docs/rfc/rfc.py --dir <their-checkout>/docs/rfc check`. These files are maintainer-owned: `rfc.py`, `file_safety.py`, `template.md.tmpl` and this file. A change to any of them needs close review. In CI, run `check` on the `pull_request` trigger with read-only permissions and no secrets, never on `pull_request_target`. The CI job must run the default-branch copy of `rfc.py` and read the pull request only through `--dir`; a copy taken from the pull request is the contributor's code.

Rules meant to bind AI agents belong in your project instructions (for example `AGENTS.md`), because agent skills do not read this file.

## How an RFC is decided

The maintainers decide, by consensus, on the pull request that adds the RFC. A decider named inside an RFC is only a suggestion: who may accept is set here. The outcome is recorded in the RFC's Status.
