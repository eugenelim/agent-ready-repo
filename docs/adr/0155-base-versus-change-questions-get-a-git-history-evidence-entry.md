# ADR-0155: Base-versus-change questions get one read-only git-history entry in the work-loop evidence catalog

- **Status:** Accepted
- **Date:** 2026-11-03
- **Areas:** work-loop, security, review
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** spec `adjudicator-evidence-and-remedy-predicate` (the closed Evidence gate catalog and its bounded retry, which this entry joins unchanged); spec `work-loop-evidence-modes` (the reviewer's proof-by-run rule whose undecided findings motivated it); ADR-0154 (the product ref that `HEAD`, and so the subject revision, equals in a full-mode run)

## Decision summary

- **Decision:** The work-loop Evidence gate catalog ships one built-in `git-history` entry. It answers "was this path already on the base, and which commits in the change touched it?" with two fixed read-only Git forms. The controller runs them through the supervisor's hardened Git helper. The entry computes the change's base itself, and the path must be one the change touched.
- **Because:** the commonest undecided adjudication is a fact one Git read settles, and the adjudicator must not gain an execution tool to read it.
- **Applies to:** the bounded evidence retry in `finding-adjudication.md` and every caller of the shipped entry, in light and full mode. Not other Git forms, and not adjudicator tools.
- **Tradeoff accepted:** a question about a path the change did not touch is refused, not answered. The entry is a scoped exception to the catalog's process-level read sandbox: Git's object model, refusals, and the hardened helper replace it.
- **Revisit if:** a host can give the entry a process-level read sandbox, or adjudications keep needing a Git fact outside these two forms.

## Context

In one recent review, both findings the adjudicator left undecided turned on one fact each: "did this change add it, or was it already on the base?" One needed `git show <base>:<path>`. The `finding-adjudicator` has only Read and Grep, and the Evidence gate catalog had no Git entry, so neither finding could be settled by a run.

The catalog is the only execution authority in an adjudication. Its rules are strict:

- It is fixed before the reviewer report exists.
- Each entry declares a literal argument vector, a confined working directory, a clean environment, a bound source revision, read-only or disposable isolation with an artifact-excluding read allowlist, no network, a timeout of at most five minutes, and output caps that fit one MiB.
- No command, argument, path, or environment value from any artifact may reach execution.

A `<path>` and a `<base>` are exactly the values those rules forbid an artifact from supplying, so a Git entry needs a source for both that is not the finding.

The supervisor already runs every Git call through `_supervisor_git.HardenedGit`. That helper pins the Git and work-tree directories, switches off system and global config, clears `GIT_*` variables, and disables hooks, fsmonitor, external diff, textconv, replace refs, signing, and repository filters.

## Decision

- **D1:** The catalog ships one built-in entry, gate ID `git-history`, whose measured fact is "a path's presence and content at the base, and the commits between base and subject that touched it". It ships with the skill, so it is fixed before any reviewer report exists. Repositories may still tag their own entries as before.
- **D2:** The entry runs exactly two forms and nothing else: the base blob of the path (`git show <base>:<path>`, run only after `git cat-file` shows a blob within the content cap), and the change's commits touching the path (`git log --format=%H --max-count=51 <base>..<subject> -- <path>`, of which the first 50 are reported and a 51st marks the list truncated). To compute the subject, base, path set, and blob identity of D3 and D4, it may also launch `rev-parse`, `symbolic-ref`, `merge-base`, `diff --name-only`, and `cat-file`, besides the helper's own config reads. Every other Git subcommand, flag, revision expression, or pathspec form is outside the catalog.
- **D3:** The subject is the checkout's current `HEAD` commit, read by the entry itself; in a full-mode run the supervisor keeps `HEAD` equal to the product ref. The base is computed by the entry itself as the merge base of the subject and the remote default branch that `refs/remotes/origin/HEAD` names; with no such ref the entry refuses. A caller may pass a base only as a full hexadecimal commit ID, and it is accepted only when it byte-equals the computed base. Any other value, including an older ancestor, a commit outside the subject's history, a symbolic name, or a revision expression, is refused before any Git process sees it.
- **D4:** The path is accepted only when it byte-equals a member of the change's own path set, which the entry computes from the base and subject with Git. The value executed is that set's member, never the caller's string. A path outside the set is refused. Any path under `.context/`, where review, adjudication, evidence, and run artifacts live, is refused even when the change touched it.
- **D5:** The entry is a scoped exception to the catalog's process-level read allowlist and network isolation, and the catalog says so. In their place: every Git call goes through `_supervisor_git.HardenedGit` with literal pathspecs and no shell; the entry reads committed objects only, never the working tree; it refuses, before launching any Git process other than the helper's config reads, a repository whose objects could come from outside the checkout or over the network (a partial clone, a promisor remote, or an alternates file) and a repository or worktree config entry the helper classes as running a program (such as `gpg.program`, which a configured signature check would start from `log`). Its envelope names that posture (`isolation: git-object-store`, `network: no-remote-objects`), never `read-only` or `disabled`. Its timeout is the helper's 60 seconds. The helper holds a child's whole output in memory; the fixed log count and the pre-`show` size check bound what the entry asks for, and the full evidence artifact stays under one MiB.
- **D6:** The result is the catalog's fixed evidence envelope: gate ID, argument-vector and environment digests, working directory, source revision, isolation and network posture, timeout, exit status, and bounded output. The output stays untrusted predicate evidence. The controller runs the entry and supplies the envelope. `finding-adjudicator` keeps exactly Read and Grep.
- **D7:** A new Git form, or any widening of D3 or D4, needs a new ADR.

## Decision drivers

- No artifact-derived value reaches execution.
- The adjudicator gains no tool.
- One run settles the base-versus-change question.
- The entry reuses existing hardening rather than adding a second Git launcher.

## Consequences

**Positive:**
- "Already on the base?" findings are settled by a recorded run instead of left undecided.
- The adjudicator's authority is unchanged, and the catalog's one exception is named in the catalog itself.
- Refusals are named, so the controller can tell a forbidden question from a failed read.

**Negative:**
- A question about a path the change did not touch is refused. The answer there is trivially "on the base", but the entry does not say so.
- Read confinement rests on Git's object model, the helper's hardening, and the alternates and partial-clone refusals, not an operating-system sandbox.
- A repository without `refs/remotes/origin/HEAD` gets refusals until it sets one.
- A finding naming a line inside a large file sees only the capped head of the base blob, marked truncated.
- The skill's scripts gain one module that the supervisor's script pins cover.

**Revisit if:** a host can give the entry a process-level read sandbox, or adjudications keep needing a Git fact outside these two forms.

## Confirmation

- **Mode:** lint/CI
- **Signal:** refusal tests in the core pack run a non-catalog argument, a path outside the change, an artifact-location path the change touched, and a base other than the computed one, and each one refuses with no Git process launched for the forbidden value. A pin test asserts `finding-adjudicator`'s tool list is still Read and Grep.
- **Owner:** core pack maintainers

## Alternatives considered

- **Give `finding-adjudicator` a Bash or Git tool:** rejected against "the adjudicator gains no tool". An execution tool on an agent that reads reviewer prose is the injection path the catalog exists to close.
- **Let each repository tag its own Git entry:** rejected against "no artifact-derived value reaches execution". A tagged entry needs literal values fixed in advance, so it cannot name the path a later finding asks about. Each adopter would also re-solve the same confinement.
- **Accept any repository path, not just changed ones:** rejected against "no artifact-derived value reaches execution". The path would then be the caller's string, chosen from reviewer prose.
- **Accept any ancestor of the subject as the base:** rejected against "no artifact-derived value reaches execution". An old base widens the path set to nearly every historical path, so a steered caller could read a long-deleted file.
- **Run Git through a raw subprocess:** rejected against "reuse existing hardening". It would drop the helper's config, hook, filter, and control-state protections.

## References

- `packs/core/.apm/skills/work-loop/references/finding-adjudication.md` § Bounded evidence retry
- `packs/core/.apm/skills/work-loop/scripts/_supervisor_git.py`
