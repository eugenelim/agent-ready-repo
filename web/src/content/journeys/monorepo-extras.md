---
pack: monorepo-extras
scope: repo
tagline: "Package scaffolding for monorepos."
prerequisitePacks: []
whatChanges: "After installing monorepo-extras, adding a new package to your monorepo runs through `new-package` — a structured scaffold that produces the correct directory layout, AGENTS.md, build configuration, and test wiring in one step. The alternative is doing it by hand from a peer package, which consistently misses the build system wiring."
skills:
  - name: new-package
    description: "Scaffolds a new package in a monorepo with the correct structure, AGENTS.md, and build configuration — wired to the project's existing conventions."
    humanTouches: 1
humanGates:
  - id: G-review
    globalGate: "G4"
    label: "Review the scaffolded package before first commit"
    trigger: "After new-package produces the package skeleton"
    duration: "5–10 minutes"
    whatToCheck:
      - "Is the package name and directory slug correct — consistent with the naming convention of existing packages?"
      - "Is the AGENTS.md populated with the package's actual purpose, commands, and any known gotchas — not the template placeholder text?"
      - "Is the build configuration wired correctly — does `npm run build` or the project's equivalent command work from the package root?"
      - "Are the test command and test directory correct — not pointing to a parent package's test suite?"
    whatGoodLooksLike: "A package that builds from its own root, has a meaningful AGENTS.md, and follows the naming and layout conventions of the existing packages in the monorepo."
    whatBadLooksLike: "A package whose AGENTS.md still reads 'TODO: describe this package.' Or a package whose test command runs the wrong test suite because the `jest.config.js` points to the wrong root. These are the two most common post-scaffold defects."
    consequence: "A scaffold that passes the G-review gate and then fails the first real build is the most expensive outcome — you've committed structural debt to the repo. The review gate is five minutes; fixing structural wiring after the first three PRs have extended the scaffolded pattern is much more expensive."
typicalSession:
  agentTurns: "3–5"
  humanTouches: 1
  wallClockMinutes: "10–20"
docsUrl: /docs/guides/monorepo-extras/
packUrl: /packs/monorepo-extras/
relatedJourneys:
  - core
  - governance-extras
---

## Stage 1 — Name the package and describe its role

You decide to add a new package to the monorepo and describe its purpose. The agent activates `new-package`, asks for the package name and a brief description, and checks whether any existing packages in the repo serve as the closest structural analogue.

**You:** Name the package precisely — using the project's naming convention (kebab-case, domain-qualified, etc.). Describe the package's role in one sentence: what it does and who uses it. If the agent suggests looking at an existing package as a template, confirm whether that package is actually the right model or just the closest match.

---

## Stage 2 — Scaffold and wire

The agent produces the package skeleton: directory structure, `package.json` (or equivalent), `AGENTS.md`, build configuration, and test directory. It populates the AGENTS.md with the package name, a description, and the correct build and test commands.

**You:** Review the scaffolded package at the G-review gate. The two things most likely to be wrong: the AGENTS.md still has placeholder text, and the test command points to the wrong root. Both are easy to catch and easy to fix at this gate; neither is easy to fix after other packages have extended the scaffolded pattern.

---

## Stage 3 — First commit and CI verification

After the review gate passes, the agent commits the scaffold, pushes the branch, and verifies that CI runs the new package's tests correctly.

**You:** Watch the CI run complete. If the new package's tests don't appear in the CI output, the test wiring is incomplete — the CI configuration doesn't know about the new package. Add the explicit CI step if needed. The most common cause: the CI config uses a hard-coded list of packages rather than a glob.
