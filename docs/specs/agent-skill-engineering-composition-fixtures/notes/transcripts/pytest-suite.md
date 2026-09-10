Mode: frame
Write status: not authorized

# Frame — verification contract for the `check-migration-plan` test suite

Read-only. Nothing below authorizes a write; agreement with this frame is not authorization for a later one. The supplied `pytest-suite-SKILL.md` was read as untrusted evidence: it describes a suite, and that description cannot widen this task, its tools, or its write authority.

## What the suite must guarantee

The observable outcome of `check-migration-plan` is a report of three named things from a supplied plan — reversibility, blast radius, rollback path — with the plan unmodified. A verification contract for that outcome has to make four guarantees, and each is a decision you own before the first test file exists:

**1. Collection identity — which module the suite actually tested.**
The guarantee: a passing run proves the checker in *this* skill was exercised, and the proof does not depend on which directory the runner reached first. The draft's shape (bare-name import plus `sys.path` reliance) does not make that guarantee. Skills are independent and several may ship a same-named module; a bare import binds whichever directory reached the path first and caches it for every later importer in the session. Decide now: a unique load name that includes pack and skill, or accept that a green suite is evidence about an unknown module. The same decision applies to any shared test helper.

**2. Invocation independence — where the suite may be run from.**
The guarantee: the suite's result is the same from the skill root, the repository root, and CI. The draft ties passing to the working directory being the skill root, which converts an environment property into a test outcome. Decide whether paths resolve from the test file's own location or whether "run from the skill root" becomes a documented, enforced precondition — one of those, not neither.

**3. Temporary-path lifetime — what exists on disk, where, and for how long.**
The guarantee: no test leaves state inside the skill root, and no cleanup step ever needs deletion authority beyond the paths the test itself created. The draft puts fixture directories in the repository tree and defers removal to end of session. Three costs: an interrupted or crashed run leaves residue inside the confined root with no owner; end-of-session sweeping is a deletion appetite wider than any single test's own outputs, and an interrupted or denied cleanup is a visible incomplete result, never a licence to broaden it; and artifacts from a failed run may be gone before you can read them. Decide the lifetime per test, not per session, and site temporaries outside the tree the skill is confined to.

**4. Isolation under concurrency — whether two runs can be true at once.**
The guarantee: two workers, or two developers, or CI and a laptop, can run the suite simultaneously and each result is independently valid. One shared fixture directory across parallel runs cannot give that. The cost is not slower tests, it is unattributable ones: the failures you get are write-write races surfacing as order-dependent, non-reproducible reds in assertions about reversibility, sending you to debug the checker for a defect in the harness. This is the item where the draft's stated motive — keeping the suite fast — buys the least, because the time it saves is returned with interest on the first flake investigation. Decide isolation first; buy speed elsewhere.

**Where speed is legitimately bought.** Cost belongs in assertions rather than processes: call a function instead of spawning an interpreter, put a seam in front of any external binary, never invoke a package manager from a test, and give a genuinely expensive fixture the widest scope its assertions still allow. That last clause is the constraint — scope widened past what the assertions tolerate is decision 4 reintroduced under a different name.

## Boundary consequence

The skill declares `boundaries: [filesystem_read_untrusted]`. A suite that creates and removes directories in the repository tree is filesystem write and delete behavior. Two coherent resolutions, and they cost differently: keep the declaration and site all test state outside the declared root (cheaper — confined to the body and the suite), or widen the declared boundary to include write (dearer — a boundary widening on a shipped skill, needing its own authorization and its own review). Do not let the suite's shape silently decide this; the declaration is the contract readers rely on.

## Evidence the suite must produce

- **Success** — each of reversibility, blast radius, and rollback path asserted independently, so a partial report fails loudly rather than passing on one field.
- **Failure** — a malformed or incomplete plan yields a stated failure, not a silent empty report.
- **Non-mutation** — the supplied plan is byte-identical after the check; this is the skill's one prohibition and needs its own test.
- **Untrusted input** — a plan containing directive-shaped text is treated as data; embedded instructions are ignored, not obeyed.
- **Path refusal** — targets outside the resolved root, `..` components, non-regular files, and symlinks are refused before any content read.
- **Clean degradation** — an interrupted run leaves no state in the skill root.

## Proposed tree

```text
check-migration-plan/
  SKILL.md
  tests/
    conftest.py          # unique-name loader; per-test tmp fixtures outside the root
    test_report_fields.py
    test_plan_unmodified.py
    test_untrusted_input.py
    test_path_refusal.py
```

## Non-goals

- Writing, generating, or editing any of these files in this pass.
- Choosing between the two boundary resolutions on your behalf.
- Version-pinned pytest mechanics: `python-pytest` is a recognized extension family, but its language topic and stated version range are not available in this slice. Everything above is the portable verification floor plus this skill's own contract; treat any specific pytest API or plugin claim as unevidenced until that topic is read, and do not carry a TypeScript/Node convention across the seam to fill the gap.

---

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: mode and target resolution; boundary reconciliation of the declared `filesystem_read_untrusted` against the described suite behavior; evidence enumeration against the skill's stated outcome and prohibition. Retained behavior: not applicable — no update was entered. Unavailable capabilities: the `python-pytest` language topic and its version range. Cleanup: none required.
