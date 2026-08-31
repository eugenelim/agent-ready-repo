# Manual QA — direct skill repository installation

Run against the built CLI on 2026-08-31, `agentbundle 0.41.0 (spec 0.18)`,
CPython 3.13.13, macOS arm64. Operator paths are redacted to `<SOURCES>`,
`<TARGET>`, and `<HOME>`.

**15 commands, 9 exiting 0 and 6 exiting 1.** Every command, its output, and its
exit code are in the transcript below.

## Command list and the criteria each exercises

| # | Command | Exit | Criteria |
|---|---|---|---|
| 1 | `--version` | 0 | — |
| 2 | `install <root-single> --dry-run` | 0 | AC25 no-write preview, AC19 capability block, AC20 verdict placement |
| 3 | `install <root-single> --yes` | 0 | AC15 measured bytes, AC19, AC22 receipt, AC12 state row |
| 4 | `install <collection>` (unselected) | 1 | AC8 selection refusal, candidate listing, recovery text |
| 5 | `install <collection> --skill summarise --yes` | 0 | AC8 explicit selection, AC24 category flattening |
| 6 | `install <collection> --skill nope --yes` | 1 | AC8 unknown-selection refusal |
| 7 | `install <root-level collection> --all-skills --yes` | 0 | E22 root collection, AC8 `--all-skills` |
| 8 | `install <direct-pack> --yes` | 0 | AC1 direct-pack shape, AC10 manifest profile |
| 9 | `install <root-single> --adapter codex --yes` | 0 | AC7 adapter honoured, AC12 recorded scope |
| 10 | `install <ambiguous roots> --yes` | 1 | AC1 ambiguity refusal |
| 11 | `install <nested envelopes> --yes` | 1 | AC1 nested-envelope refusal |
| 12 | `install <non-empty .gitkeep> --yes` | 1 | E22 placeholder emptiness guard |
| 13 | `install git+https://... --skill canvas-design` | 1 | AC20 remote requires `--yes` |
| 14 | `install git+https://... --skill canvas-design --yes` | 0 | AC3 revision pinning, AC5 bounds, AC6 link policy, AC37 transport |
| 15 | `validate <root-level collection> --format json` | 0 | AC7 `--format json`, AC21 envelope |

## Verified beyond the transcript

- **Dry run writes nothing.** `find` over the target after command 2: **0 files**.
- **AC26 sentinel sweep.** Fixed-string search over all recorded output:
  `0.0.0` — **0**, `+agentbundle` — **0**, `manifestless` — 6 (the permitted
  label). The sentinel appears only in `installed-version` inside the six state
  files, which is internal. A first pass reported one `0.0.0` hit; that was the
  sweep's own defect — an unescaped `.` matched `0f000` inside a digest.
- **AC19 projected payloads are non-executable.** The source ships
  `scripts/run.py` with the executable bit and the capability block reports it
  as `executable`; the installed file is mode `600`. The bit is reported, not
  applied.
- **Adapter targets.** `--adapter codex` wrote `.agents/skills/`, not
  `.claude/skills/`.

## Defects this session found

Manual QA earned its place again: two defects survived the full automated suite
and appeared only when the real CLI ran.

1. **A root-level collection was refused by the CLI.** `_has_direct_marker`
   gated on `SKILL.md`, `skills/`, and `.claude/skills/`, and a repository whose
   own root is the collection carries none of them — so E22's shape was admitted
   by classification and rejected by the command in front of it. The two halves
   did not join, which is the same failure shape the remote arm found earlier
   between acquisition and admission.
2. **The remote refusal message described behaviour the code did not have.** It
   said the admissibility summary "is printed either way", but the refusal
   happens before acquisition, so no summary exists. Correcting the message to
   point at `--dry-run` made it false a second time, because `--dry-run` was
   also refused without `--yes`. Rather than weaken the message, `--dry-run` is
   now exempt: it writes nothing and is the only way to read the summary for a
   remote source before consenting. Verified — the remote dry run prints the
   full plan and writes **0 files**.

## Not exercised

`upgrade`, `list-installed`, `show`, and `uninstall` for direct rows are not
built; AC4, AC7, AC9, AC22, and AC30 stay unticked for that reason. The receipt
prints an `uninstall --skill` line that the CLI does not yet accept, which is
recorded in `security-evidence.md` rather than hidden here.

## Transcript

```console
$ agentbundle --version
agentbundle 0.41.0 (spec 0.18)
[exit 0]

$ agentbundle install <SOURCES>/hello-world --output <TARGET>/t1 --dry-run
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: hello-world
  source:      <SOURCES>/hello-world
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: Grep, Read
  boundaries:  filesystem_read
  credentialed: False
  SKILL.md:    sha256-1:be1b7a19932139e511a22b9e7e0f7dfdc15d06bb4d574a8bfb6d5ec17561d3d9
    scripts/run.py  sha256-1:0ca9091eb4e31fb1ab24c8c5de92a08e4e5f402919f82ea3ca784f38534f03f3  executable
--- end publisher-supplied data ---

admissible—not safe

would install (dry run — nothing written):
  .claude/skills/hello-world/SKILL.md
  .claude/skills/hello-world/scripts/run.py
[exit 0]

# files written by that dry run: 0

$ agentbundle install <SOURCES>/hello-world --output <TARGET>/t1 --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: hello-world
  source:      <SOURCES>/hello-world
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: Grep, Read
  boundaries:  filesystem_read
  credentialed: False
  SKILL.md:    sha256-1:be1b7a19932139e511a22b9e7e0f7dfdc15d06bb4d574a8bfb6d5ec17561d3d9
    scripts/run.py  sha256-1:0ca9091eb4e31fb1ab24c8c5de92a08e4e5f402919f82ea3ca784f38534f03f3  executable
--- end publisher-supplied data ---

admissible—not safe

installed: hello-world
  kind:     manifestless
  source:   <SOURCES>/hello-world
  revision: —
  digest:   sha256-1:b488c01882edd089090055feb4228713430a3ad13fe9dcde0d02faa065622754
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill hello-world
[exit 0]

$ agentbundle install <SOURCES>/kit --output <TARGET>/t2
install: [CAT-D008] a collection source requires an explicit skill selection
  at: <SOURCES>/kit
  → Select explicitly: agentbundle install <SOURCES>/kit --skill expand  or  agentbundle install <SOURCES>/kit --all-skills

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
  expand — Lengthens text.
  summarise — Shortens text.
--- end publisher-supplied data ---

Select explicitly: agentbundle install <SOURCES>/kit --skill expand  or  agentbundle install <SOURCES>/kit --all-skills
[exit 1]

$ agentbundle install <SOURCES>/kit --output <TARGET>/t2 --skill summarise --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: summarise
  source:      <SOURCES>/kit
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: undeclared (unrestricted)
  boundaries:  —
  credentialed: —
  SKILL.md:    sha256-1:da357e3d967b584b0b39742c33b3f2f6572925936f4deb59c3eb2b92aaa1b658
--- end publisher-supplied data ---

admissible—not safe

installed: summarise
  kind:     manifestless
  source:   <SOURCES>/kit
  revision: —
  digest:   sha256-1:6f24165364a8e2f3b1312b987769b119077100b82871045eded7341f91fcdd34
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill summarise
[exit 0]

$ agentbundle install <SOURCES>/kit --output <TARGET>/t2 --skill nope --yes
install: [CAT-D008] --skill 'nope' is not in this source
  at: <SOURCES>/kit
  → Select explicitly: agentbundle install <SOURCES>/kit --skill expand  or  agentbundle install <SOURCES>/kit --all-skills

Select explicitly: agentbundle install <SOURCES>/kit --skill expand  or  agentbundle install <SOURCES>/kit --all-skills
[exit 1]

$ agentbundle install <SOURCES>/rootcol --output <TARGET>/t3 --all-skills --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: alt-text
  source:      <SOURCES>/rootcol
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: undeclared (unrestricted)
  boundaries:  —
  credentialed: —
  SKILL.md:    sha256-1:0d8c6d6e9174d9030697131007604a9fbfe94b6be65b6be4bf3c1dbbd83bfed8

skill: brand-yml
  source:      <SOURCES>/rootcol
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: undeclared (unrestricted)
  boundaries:  —
  credentialed: —
  SKILL.md:    sha256-1:61d7992b52556b96fdc336e408b5d662088466b0919c4d0428065acfe5384350
--- end publisher-supplied data ---

admissible—not safe

installed: alt-text
  kind:     manifestless
  source:   <SOURCES>/rootcol
  revision: —
  digest:   sha256-1:6f4c6f5ae63867450071213709541f04fd499f6324da8fee655de9c4354efac0
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill alt-text

installed: brand-yml
  kind:     manifestless
  source:   <SOURCES>/rootcol
  revision: —
  digest:   sha256-1:6f4c6f5ae63867450071213709541f04fd499f6324da8fee655de9c4354efac0
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill brand-yml
[exit 0]

$ agentbundle install <SOURCES>/dpack --output <TARGET>/t4 --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: one
  source:      <SOURCES>/dpack
  revision:    —
  scope:       repo
  adapter:     claude-code
  allowed-tools: undeclared (unrestricted)
  boundaries:  —
  credentialed: —
  SKILL.md:    sha256-1:f96b36abc7151e2fc5fdf92f166d6671734720710d98faa61e8597dd63534b3e
--- end publisher-supplied data ---

admissible—not safe

installed: one
  kind:     pack
  source:   <SOURCES>/dpack
  revision: —
  digest:   sha256-1:29d859c76f7d27cb0c6109753f60e93546660734a46371b34569083c17face03
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill one
[exit 0]

$ agentbundle install <SOURCES>/hello-world --output <TARGET>/t5 --adapter codex --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: hello-world
  source:      <SOURCES>/hello-world
  revision:    —
  scope:       repo
  adapter:     codex
  allowed-tools: Grep, Read
  boundaries:  filesystem_read
  credentialed: False
  SKILL.md:    sha256-1:be1b7a19932139e511a22b9e7e0f7dfdc15d06bb4d574a8bfb6d5ec17561d3d9
    scripts/run.py  sha256-1:0ca9091eb4e31fb1ab24c8c5de92a08e4e5f402919f82ea3ca784f38534f03f3  executable
--- end publisher-supplied data ---

admissible—not safe

installed: hello-world
  kind:     manifestless
  source:   <SOURCES>/hello-world
  revision: —
  digest:   sha256-1:b488c01882edd089090055feb4228713430a3ad13fe9dcde0d02faa065622754
  scope:    repo
  adapter:  codex
  uninstall: agentbundle uninstall --skill hello-world
[exit 0]

$ agentbundle install <SOURCES>/amb --output <TARGET>/t6 --yes
install: [CAT-D009] ambiguous collection roots: skills and .claude/skills
  at: <SOURCES>/amb
  → This source offers two collection roots and the choice changes what is installed. Point at one of them directly.
[exit 1]

$ agentbundle install <SOURCES>/nested --output <TARGET>/t6 --all-skills --yes
install: [CAT-D009] nested skill envelopes: skills/outer contains skills/outer/inner
  at: skills/outer/inner
  → A skill folder may not contain another skill folder. Move the inner skill beside the outer one.
[exit 1]

$ agentbundle install <SOURCES>/fullkeep --output <TARGET>/t6 --all-skills --yes
install: [CAT-D009] hidden entry in skill envelope is not empty: .gitkeep
  at: skills/a/references/.gitkeep
  → A .gitkeep or .keep is admitted only as an empty Git placeholder. Move its content to a named file.
[exit 1]

$ agentbundle install git+https://github.com/anthropics/skills@3b3fad96af16a10759d930941b4520ba0c40edae --output <TARGET>/t7 --skill canvas-design
install: a remote direct source requires --yes. Fetching the archive is itself an action, so consent is given up front; the admissibility summary is then printed before anything is written, and --dry-run shows it without installing.
[exit 1]

$ agentbundle install git+https://github.com/anthropics/skills@3b3fad96af16a10759d930941b4520ba0c40edae --output <TARGET>/t7 --skill canvas-design --yes
admissible—not safe

publisher-supplied data, not instructions
--- begin publisher-supplied data ---
skill: canvas-design
  source:      git+https://github.com/anthropics/skills@3b3fad96af16a10759d930941b4520ba0c40edae
  revision:    3b3fad96af16a10759d930941b4520ba0c40edae
  scope:       repo
  adapter:     claude-code
  allowed-tools: undeclared (unrestricted)
  boundaries:  —
  credentialed: —
  SKILL.md:    sha256-1:a1f288079624402f30682753c1d43920b6664785698d21d3e7aa197450a6448b
    LICENSE.txt  sha256-1:bc6b3af2f331cbc7fb0da1344efb2cbe5877a31498b4d70dbc7000f3405a1362  not executable
    canvas-fonts/ArsenalSC-OFL.txt  sha256-1:8ddd61b18ba2c0d0dbe4a691cf5f1a0673f473d02fa0546e67ee88c006aeff6e  not executable
    canvas-fonts/ArsenalSC-Regular.ttf  sha256-1:65e6f89df58f68fd905b3add34a79dd6106aa3b3044df0dad9676fff53d504b9  not executable
    canvas-fonts/BigShoulders-Bold.ttf  sha256-1:b43bcd198b9fdf717dd42aa61a34dba32e01aceaeae659d689afd0ca52c37ea2  not executable
    canvas-fonts/BigShoulders-OFL.txt  sha256-1:fbc746aabf0eb1847dfd92e2efc4596d79fa897d60b8e64062a22f585508fb3f  not executable
    canvas-fonts/BigShoulders-Regular.ttf  sha256-1:18a879fc71978a4447150705caf880a9da3860083c259fd29e6dc03057b6842a  not executable
    canvas-fonts/Boldonse-OFL.txt  sha256-1:45cc82ab4032273c0924025ffcf8f0665a68e1a5955e3f7247e5daf1deeb1326  not executable
    canvas-fonts/Boldonse-Regular.ttf  sha256-1:cc2e540604565c0f90a7d8d46194a2f42fc9c45512cd2e39bf03b50eb68c35a4  not executable
    canvas-fonts/BricolageGrotesque-Bold.ttf  sha256-1:a737b146fe0d77ffe8a86e3cd16700dd431d3b1e420d4fd80e142cd68a1cb50d  not executable
    canvas-fonts/BricolageGrotesque-OFL.txt  sha256-1:0e4f4eb8534bc66a76aca13dd19c1f9731b2008866b29ccff182b764649df9b4  not executable
    canvas-fonts/BricolageGrotesque-Regular.ttf  sha256-1:972a6d098c9867ae131d0ea99e221e63976b11a19d4b931c2c7ace525674e4f6  not executable
    canvas-fonts/CrimsonPro-Bold.ttf  sha256-1:48f191e38355c8db100eb3ce157c20f9302a3b9a37b44a660f77ecfce3986609  not executable
    canvas-fonts/CrimsonPro-Italic.ttf  sha256-1:52318db3526b644e6efa60be0b3ca5a50e40fbe8bd026c261e0aa206f0772267  not executable
    canvas-fonts/CrimsonPro-OFL.txt  sha256-1:35680d14547b6748b6f362a052a46d22764ce5eccf96e18b74f567bb2ee58114  not executable
    canvas-fonts/CrimsonPro-Regular.ttf  sha256-1:48fad08cb1917a7b2f2c6fe5135d6c07743a6663cf7631ec4481108aaf081422  not executable
    canvas-fonts/DMMono-OFL.txt  sha256-1:bfe7842fcb88323e2981e24710c25202677385a8c75fb6a87217b275a0247ae3  not executable
    canvas-fonts/DMMono-Regular.ttf  sha256-1:f98ada968dc3b6b2c08d3f5caaf266977df0bfe0929372b93df5a06cf2ace450  not executable
    canvas-fonts/EricaOne-OFL.txt  sha256-1:e0de629968b52255548d5fafcf30b24ff9edae0eda362380755a75816404d0fa  not executable
    canvas-fonts/EricaOne-Regular.ttf  sha256-1:db1d89e80e33a8a01beaaac7a85df582857d24a43f1e181461aa7ff5d701476a  not executable
    canvas-fonts/GeistMono-Bold.ttf  sha256-1:75c0828d5c1ee44b9ef9f4df577bf41595ec362e2ea3f1e558590c9e92c7949d  not executable
    canvas-fonts/GeistMono-OFL.txt  sha256-1:6a873c900f584109b13ae0aaf81d6e3cf0a68751a216b03f7b6c68d547057bb4  not executable
    canvas-fonts/GeistMono-Regular.ttf  sha256-1:a55c1b51cda4afeab9e471e7947b85a20f7c8831d7e6b1470c1b7fbdc0f0f15e  not executable
    canvas-fonts/Gloock-OFL.txt  sha256-1:c0a3f3125ac491ef3d1f09f401be4834c646562f647e44f2bcbc49f0466c656d  not executable
    canvas-fonts/Gloock-Regular.ttf  sha256-1:e86b4ce66dbd3f1f83eee8db99ec96e0da1128c3f53df0e9b3b7472025dfe960  not executable
    canvas-fonts/IBMPlexMono-Bold.ttf  sha256-1:dbd2a2fb024579438d6400a84e57579bfd2dbe67c306c8fd9fde92a61e4f2eea  not executable
    canvas-fonts/IBMPlexMono-OFL.txt  sha256-1:5294ce778857e1eb02e830b6ab06435537d38f43055327e73d03a2d4d57d5123  not executable
    canvas-fonts/IBMPlexMono-Regular.ttf  sha256-1:ab08018ccd276b79fb2c636bb95b9c543598f9d50505fe92506fcb4dae7810cd  not executable
    canvas-fonts/IBMPlexSerif-Bold.ttf  sha256-1:b8d294e9b5c5a0940f167c3ced0f7ef2e3f57082ca3ff096ef30e86e26c1c159  not executable
    canvas-fonts/IBMPlexSerif-BoldItalic.ttf  sha256-1:da64b75f4284f53e7b5c71fa190a35b8bf3494fe19f1804c81c3a53340bca570  not executable
    canvas-fonts/IBMPlexSerif-Italic.ttf  sha256-1:b11f1048745e715a55c9d837b3f10226ca3d78867b7db7251ddad8f98dcf0f38  not executable
    canvas-fonts/IBMPlexSerif-Regular.ttf  sha256-1:77cd233a2af8dc6b1022faea3bb3b01f3c75af68bcf530cb6aeb15982ff3dbb7  not executable
    canvas-fonts/InstrumentSans-Bold.ttf  sha256-1:444f85bf1c4b0e1ce1ca624f6be54bcd832207714ccaf4ea99ee531341683bdf  not executable
    canvas-fonts/InstrumentSans-BoldItalic.ttf  sha256-1:3762f6cef95d6039489ad5ba5787d4c30f17a1ad01e9ac3c816ed69692722a68  not executable
    canvas-fonts/InstrumentSans-Italic.ttf  sha256-1:78e85858e371b2cb4e18f617c10f0f937c0e12a0887ffee98555b24ed305b3a7  not executable
    canvas-fonts/InstrumentSans-OFL.txt  sha256-1:bf4dc6d13a8cccd4807133c77a1ee9619a16b92cb23322258725ab6731c2f6e5  not executable
    canvas-fonts/InstrumentSans-Regular.ttf  sha256-1:a22cb26e48fd79bcb01bf2fc92d36785474dce36d9c544ab0a8868c2657c4a87  not executable
    canvas-fonts/InstrumentSerif-Italic.ttf  sha256-1:9c86e4d5a47b50224a2463a9eca8535835257c8e85c470c2c6b454b1af6f046e  not executable
    canvas-fonts/InstrumentSerif-Regular.ttf  sha256-1:56ac3be03ac3ba283196b3e77850ab2ffcf56cfb6fd3212c5620109a972f8c99  not executable
    canvas-fonts/Italiana-OFL.txt  sha256-1:8373b11312ace78c4cec2e8f9f6aa9f2330601107dac7bcf899c6f2dbd40c5a5  not executable
    canvas-fonts/Italiana-Regular.ttf  sha256-1:15c4dd6ab8cf4a29ba8826f65edcbe2f6c266c557d34d081f25072dfd5605fd2  not executable
    canvas-fonts/JetBrainsMono-Bold.ttf  sha256-1:a2349098b9e45419e7bf0e2958d6c4937a049dded37387b08be725be4c7615f3  not executable
    canvas-fonts/JetBrainsMono-OFL.txt  sha256-1:a76abf002c49097d146e86740a3105a5d00450b1592e820a1109a8c5680cd697  not executable
    canvas-fonts/JetBrainsMono-Regular.ttf  sha256-1:b6b1ff4ddefe36d7f2a6174e1d001cab374e594519ee9049af028d577b64c5f5  not executable
    canvas-fonts/Jura-Light.ttf  sha256-1:c891a381df056b2c4dfe85841e911bf45da0890fa21a7b2692cbe5ea1f505e1e  not executable
    canvas-fonts/Jura-Medium.ttf  sha256-1:c72965cb732a92872643819fd1734128238583cc36b116313859137a51d3368a  not executable
    canvas-fonts/Jura-OFL.txt  sha256-1:eaf9bdb675f6d87e5feb88199ab3ea581d3bd2082f426e384fa9c394576d7260  not executable
    canvas-fonts/LibreBaskerville-OFL.txt  sha256-1:55959eef5b0c3b2e3c1c7631b8ff0f9447d75de20f29cfa7db5bcfb026763343  not executable
    canvas-fonts/LibreBaskerville-Regular.ttf  sha256-1:2101302538d9e88adb679031c04623e4578b5745e89566284fd2c508d79acae0  not executable
    canvas-fonts/Lora-Bold.ttf  sha256-1:7d74015e950c2fb66519c7295b8155621d22200ae2ca2a4c6b43ce3c490cac87  not executable
    canvas-fonts/Lora-BoldItalic.ttf  sha256-1:152f87e71f5ddb60d5c57ecd9132807c947e65c42977193c9164e7c5a6690081  not executable
    canvas-fonts/Lora-Italic.ttf  sha256-1:be627e595184e8afe521f08da0607eee613f1997d423bc8dadc5798995581377  not executable
    canvas-fonts/Lora-OFL.txt  sha256-1:62e37a82d3f1ef2a70712885fa8b3144b65fd144d8e748d6196b690a354d792c  not executable
    canvas-fonts/Lora-Regular.ttf  sha256-1:7ed00e7c9cdf16ab7e2fd2361fe45d4f0b61263cd60aae398b27b7ee08108827  not executable
    canvas-fonts/NationalPark-Bold.ttf  sha256-1:69ac4c301c4a7233c6e602d12a92c54d7967b575f4449951c45ce773f7acff53  not executable
    canvas-fonts/NationalPark-OFL.txt  sha256-1:81c6c71d83b5b45d7344f96df12bb4a2477a5b092a9144757ee1d0f50f855175  not executable
    canvas-fonts/NationalPark-Regular.ttf  sha256-1:a477338b7e18308d476650dfe31235ef86a883572665e56ffb5fb80f82009b58  not executable
    canvas-fonts/NothingYouCouldDo-OFL.txt  sha256-1:7c2a6970584ddad04919816163746f83b378078015899b18468b40f05e9ce128  not executable
    canvas-fonts/NothingYouCouldDo-Regular.ttf  sha256-1:d866f985896d3280f4fce72db7e17302c24a0c1fdb0699b6b5ed3af14f944d57  not executable
    canvas-fonts/Outfit-Bold.ttf  sha256-1:6654b93d21301ec61887d3cedd6c11d9df1b1dfb63f9cf45ac7995f6e2235ab1  not executable
    canvas-fonts/Outfit-OFL.txt  sha256-1:1945b62cd76da9a3051a1660dde72afaa64ffc2666d30e7a78356d651653ba2f  not executable
    canvas-fonts/Outfit-Regular.ttf  sha256-1:f24945365147c9e783e91d8649959b59be6b00c9ee4ecd2f6b33afbb2dd871fe  not executable
    canvas-fonts/PixelifySans-Medium.ttf  sha256-1:38397504f71c122b03d234ea6f55118e3d5bdbddffd82bedddbd7755d3b3be82  not executable
    canvas-fonts/PixelifySans-OFL.txt  sha256-1:7f54d1d9f1ae1ba9f2722f978145f90324fea34ca3c2304b3a29cfa96ac6037e  not executable
    canvas-fonts/PoiretOne-OFL.txt  sha256-1:2eaf541f7eb8b512e4c757a5212060abf5b6edfef230e9d7640bf736b315c33a  not executable
    canvas-fonts/PoiretOne-Regular.ttf  sha256-1:9cf265b139648b36b6c0afdfeb0bf27f7e66db9a16094bc40f644d8da05bc318  not executable
    canvas-fonts/RedHatMono-Bold.ttf  sha256-1:7ef48353f4be5ddb90f000f6fad48f2b62b3e8c27d9818d8d45ff46c201065e0  not executable
    canvas-fonts/RedHatMono-OFL.txt  sha256-1:435fbfb7e66988b2a06686a4cb966faec733f35d8fe100a1601573c27f3e0bb8  not executable
    canvas-fonts/RedHatMono-Regular.ttf  sha256-1:452fe826871b37539f5212b20c87cf30f82f58dd2741f1c96edd1dcbdc0db6b4  not executable
    canvas-fonts/Silkscreen-OFL.txt  sha256-1:6b849745119bbe85ec01fd080c9cd50234da9f52ac6e48b55d1a424a0c4d7ca9  not executable
    canvas-fonts/Silkscreen-Regular.ttf  sha256-1:49567408600809e25147e9225ac4f37f410e2df45a750696c45027531fb65f1b  not executable
    canvas-fonts/SmoochSans-Medium.ttf  sha256-1:dd76e6e77cce82f827a8654cd906e9ce58f3aaf78adda63c4a7f655b8ecb41f0  not executable
    canvas-fonts/SmoochSans-OFL.txt  sha256-1:74c9c4eb88e891483e1b7bc54780b452cbf4f4df66d4e71881d7569aa2130749  not executable
    canvas-fonts/Tektur-Medium.ttf  sha256-1:52bbe8c9b057b3d2da4eeace31a524b1ea26a1375ae34319cf6900ccc57a4c82  not executable
    canvas-fonts/Tektur-OFL.txt  sha256-1:3f1466cb5438f31782eeb6e895f3a655bc4d090e24263e331f555357d1cb734e  not executable
    canvas-fonts/Tektur-Regular.ttf  sha256-1:162e1b36c4718c5b051b36c971ad7e50d341944f35618f480422ebbe72988f98  not executable
    canvas-fonts/WorkSans-Bold.ttf  sha256-1:240d125fc9f8561363dc1ea3f513501253bd70942f41468f48f0b0cafb0c82e2  not executable
    canvas-fonts/WorkSans-BoldItalic.ttf  sha256-1:a5b2cad813df0aaa7d16621f2e93b5117c25e9bc788bc9a3ad218e9d6348ce34  not executable
    canvas-fonts/WorkSans-Italic.ttf  sha256-1:6b7f7002e0b0c8b261fe878658ef5551e3e59d9f6b609b04efb90dde1e2c1ada  not executable
    canvas-fonts/WorkSans-OFL.txt  sha256-1:ace8c22a3326318b54e67c3691857929634205533f454a70ef5a3473ddb2e2ba  not executable
    canvas-fonts/WorkSans-Regular.ttf  sha256-1:e67985a843df0d3cdee51a3d0f329eb1774a344ad9ff0c9ab923751f1577e2a4  not executable
    canvas-fonts/YoungSerif-OFL.txt  sha256-1:cdcb8039606b40a027a6d24586ec62d5fe29c701343d82a048c829cb28a3dd28  not executable
    canvas-fonts/YoungSerif-Regular.ttf  sha256-1:f8dc08f77abad753a00670af70756a8ace938e5c3f0b770f4f4c2071c4bd8fc6  not executable
--- end publisher-supplied data ---

admissible—not safe

installed: canvas-design
  kind:     manifestless
  source:   git+https://github.com/anthropics/skills@3b3fad96af16a10759d930941b4520ba0c40edae
  revision: 3b3fad96af16a10759d930941b4520ba0c40edae
  digest:   sha256-1:6119d84ae1c1a751210e7043f1aacc1b43788460d217a8862ae1dbc1cd6ebbaa
  scope:    repo
  adapter:  claude-code
  uninstall: agentbundle uninstall --skill canvas-design
[exit 0]

$ agentbundle validate <SOURCES>/rootcol --format json
{
  "agentbundle_version": "0.41.0",
  "catalogue_schema_version": 1,
  "command": "validate",
  "diagnostics": [],
  "ok": true,
  "operation": "direct",
  "schema_version": 1,
  "summary": {
    "selected_skills": [
      "alt-text",
      "brand-yml"
    ],
    "shape": "collection"
  }
}
[exit 0]
```
