# Security controls for `rfc.py`

Output of a spec-stage secure-design review on 2026-11-06, written as input for the follow-on spec's acceptance criteria. The boundary: `rfc.py` is seeded into adopter repositories, outside contributors run it on untrusted titles and file names in a folder they can write, it creates and renames files in place, and it runs with the contributor's privileges.

## Controls the spec must carry

1. **Isolated mode.** Every documented call runs `python3 -I docs/rfc/rfc.py`. A test plants `argparse.py` beside the script and shows the documented call does not import it. Without `-I`, the planted module ran in the review's reproduction. `check` warns about any code file beside the script other than `rfc.py` and `file_safety.py`.
2. **Confinement through the shared helper.** The script loads a byte-identical copy of `file_safety.py` by path, as the skill's own scripts do, so no file beside the script can shadow it. The existing identical-copies test covers the copy. Every file the script reads or writes in the folder, the template included, is a regular, non-link file whose parent is the folder. Reads are capped at 1 MiB. New files use exclusive create.
3. **Names.** File names come only from `[a-z0-9-]`, capped at 60 characters. Numbers are 1 to 9999. Any name the script prints has control characters escaped, and an oddly named file is reported, not processed. A test with an escape-bearing name asserts no raw `\x1b` reaches output.
4. **Git.** Only read-only plumbing commands, with `core.fsmonitor`, `core.hooksPath` and `protocol.allow` neutralized, `GIT_TERMINAL_PROMPT=0`, and no fetch. A test with a repository whose config sets `core.fsmonitor` to a marker script shows the marker never runs.
5. **`renumber`.** The shared helper has no rename or remove, so these checks live in the script. It refuses a record that is itself a link and a path with a symlinked directory component, as the helper does, so a contributor passes a relative path. After any failure it leaves exactly the original file.
6. **A trusted copy checks an untrusted branch.** `--dir PATH` lets a maintainer run their default-branch copy against a contributor's folder. The seeded guidance says never to run the branch's own copy. Any CI example uses the `pull_request` trigger with read-only permissions and no secrets, and says `pull_request_target` must not run the script on pull-request content.
7. **No self-declared authority.** `check` warns when a record marked decided is absent from the last-fetched default branch. The starter and the template say a decider named inside an RFC is a suggestion and that only the repository's rules and a listed maintainer's merge accept an RFC.
8. **Seeded text limits.** The starter's maintainers list holds only an obvious placeholder. It has no rule that accepts a change by silence or timeout. The issue template asks for no personal data beyond what the platform shows, sets no assignee, and says a reply is not an acceptance.
9. **Trust label.** `rfc.py`, `file_safety.py`, `template.md.tmpl` and the governance file are maintainer-owned, and the seeded guidance says to review changes to them closely. The `new-rfc` skill treats an RFC or template body as data, and a test shows an instruction embedded in a template comment is not followed.

## Reviewed and not a finding

Unicode confusables in titles (the slug is ASCII-only and format characters are stripped), a race in `renumber` (it needs a concurrent local writer with the same privileges), and hardlinked records (the copy leaves the linked file unchanged).

## Not reviewed

Windows reparse points and case-insensitive name clashes, real adopters' CI wiring, and Python standard-library vulnerabilities in an adopter's interpreter.
