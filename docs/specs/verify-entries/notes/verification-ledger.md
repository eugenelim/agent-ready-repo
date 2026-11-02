# Verification ledger: verify entries

Execution observations for this delivery. Paths are placeholders: `<checkout>` is the worktree root, `<scratch>` the `mktemp -d` directory a run created, and `<evidence-dir>` is `.context/verify/agentbundle-cli/<run-id>/`. `<ab>` is `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle`.

## Run r1 — drift found at run start

Driven at commit `b693f1ed070738f45ea5780fc5cf88876502db65` from `docs/VERIFICATION.md` as first written.

- `<ab> render <checkout>/packs/core --target codex --output <scratch>/render` exited 0 and wrote no files.
- Classification: doc drift. `agentbundle render` selects distribution recipes by target, and a direct-install adapter target such as `codex` selects none, as the command's own module docstring states. The entry's Drive and Evidence were corrected to render with no `--target` and to check `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md`. Grade: `blocked` — the run stopped at run start on doc drift. r2 is the retry.
- Observation for the CLI's owners, not part of this delivery: a render that selects no recipe exits 0 silently. A message naming the empty selection would have made the drift visible without reading the output tree.

## Run r2 — live-verified

Driven from the working tree on top of commit `b693f1ed070738f45ea5780fc5cf88876502db65`, with the corrected `docs/VERIFICATION.md` not yet committed, so no commit holds the tree it drove. Grade: `live-verified`. It carries no receipt; r4 is the recorded live run.

| Step | Command | Exit | Observed |
| --- | --- | --- | --- |
| Doctor | `<ab> --version` | 0 | `agentbundle 0.59.0 (spec 0.18, catalogue specification 0.1)` |
| Drive 1 | `<ab> render <checkout>/packs/core --output <scratch>/render` | 0 | `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md` present |
| Drive 2 | `git init -q <scratch>/repo` | 0 | empty repository created |
| Drive 3 | `<ab> install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo` | 0 | ready: `<scratch>/repo/.agentbundle-state.toml` present |
| Drive 4 | `<ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core` | 0 | no output: the install matches a fresh render |
| Cleanup | remove `<scratch>` by its recorded handle | 0 | `<scratch>` gone; `<evidence-dir>` still holds all step transcripts |

## Mutation proof

- **Invariant:** the install matches a fresh render of the pack.
- **Catching test:** the entry's evidence check, `<ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core` (`agentbundle diff`).
- **Exact mutation:** one line, `mutation-proof`, appended to `<scratch>/repo/.agents/skills/work-loop/SKILL.md` after Drive 4 in run r2. The deliberate break of the driven subject stands in for a revert to a pre-fix implementation, which a new entry does not have.
- **Expected failure:** `agentbundle diff` exits 1 and names `.agents/skills/work-loop/SKILL.md`.
- **Observed failure:** `agentbundle diff` printed `.agents/skills/work-loop/SKILL.md` and exited with exit 1.

## Run r3 — superseded

Driven at commit `abbb7dd3ba666c6f94bfa3bbab65b7c1b160f1b1` and graded `live-verified`, but its record ran `git init -q` where the entry says `git init` and did not show the Isolation step's `mktemp -d`. Run r4 replaces it.

## Run r4 — live-verified, as the entry is written

Driven at commit `3357364813e2318c977f1966d1002181067709fb`, which holds `docs/VERIFICATION.md` as driven; the working tree was clean. Grade: `live-verified`. Each command is the entry's own, in order, with its output and exit status. Paths are placeholders, `<ab>` is the entry's launch prefix, and the render listing's 399 lines under `apm/core/.apm/` (the skills, agents, and hooks tree) are omitted; every other output line is as printed.

```text
$ mktemp -d
<scratch>
exit=0
$ <ab> --version
agentbundle 0.59.0 (spec 0.18, catalogue specification 0.1)
exit=0
$ <ab> render <checkout>/packs/core --output <scratch>/render
agent-plugin: pack "core" excluded by dropped primitives ["adapter-root-bins","agent","command","hook-body","hook-wiring","kiro-ide-hook"]
apm/core/README.md
apm/core/apm.yml
apm/core/pack.toml
apm/core/seeds/.gitignore
apm/core/seeds/AGENTS.md
apm/core/seeds/AGENT_RULES.md
apm/core/seeds/_agents-footer.md
apm/core/seeds/docs/AGENTS.md
apm/core/seeds/docs/CHARTER.md
apm/core/seeds/docs/README.md
apm/core/seeds/docs/architecture/README.md
apm/core/seeds/docs/architecture/overview.md
apm/core/seeds/docs/knowledge/README.md
apm/core/seeds/docs/knowledge/patterns.jsonl
apm/core/seeds/docs/product/README.md
apm/core/seeds/docs/product/briefs/_template.md
apm/core/seeds/docs/product/changelog.md
apm/core/seeds/docs/product/roadmap.md
apm/core/seeds/docs/specs/README.md
apm/core/seeds/workspace.toml
claude-plugins/marketplace.json
exit=0
$ test -f <scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md
exit=0
$ git init <scratch>/repo
hint: Using 'master' as the name for the initial branch. This default branch name
hint: will change to "main" in Git 3.0. To configure the initial branch name
hint: to use in all of your new repositories, which will suppress this warning,
hint: call:
hint:
hint: 	git config --global init.defaultBranch <name>
hint:
hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
hint: 'development'. The just-created branch can be renamed via this command:
hint:
hint: 	git branch -m <name>
hint:
hint: Disable this message with "git config set advice.defaultBranchName false"
Initialized empty Git repository in <scratch>/repo/.git/
exit=0
$ <ab> install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo
warning: pack core ships 1 command that codex projects as 'dropped'; these primitives will not be installed. The compatible primitives (agents, hook-bodies, hook-wirings, and skills) will proceed.
install: delivered 15 seed(s) for pack core
Installed core for codex (repo).
  Skills → .agents/skills/ — also read by cursor, gemini, copilot.
  Hooks & subagents → .codex/ — codex only; install those adapters
  separately to get them there.
adapt: no .adapt-discovery.toml at repo root; markers left unresolved
installed: core @ repo via codex

Verify:   Run workspace-status and confirm your workspace.toml queue state is displayed.
Next:     Ask your agent to run adapt-to-project for a read-only readiness check; start a new session if the skill is unavailable.
exit=0
$ test -f <scratch>/repo/.agentbundle-state.toml
exit=0
$ <ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core
exit=0
$ rm -rf <scratch>
exit=0
$ test ! -e <scratch>
exit=0
$ test -s <evidence-dir>/transcript.txt
exit=0
```

- Observation for the CLI's owners, not part of this delivery: the omitted render listing includes 16 local bytecode files under `__pycache__/` directories, such as `apm/core/.apm/adapter-root-bins/__pycache__/intent_delivery_relations.cpython-314.pyc`, so a render from a working checkout can package untracked build residue.

## Receipts

Run r4:

```json
{
  "schema_version": 1,
  "receipt_id": "verify:agentbundle-cli:r4",
  "acceptance_fingerprint": "git:3357364813e2318c977f1966d1002181067709fb",
  "lineage": {"criterion_ref": "AC-0026"},
  "selector": {"term": "verify"},
  "freshness_mode": "exact-subject",
  "observation": {"type": "command-result"},
  "outcome": "live-verified",
  "producer": {"class": "verify-entry", "identity": "verify:agentbundle-cli"}
}
```
