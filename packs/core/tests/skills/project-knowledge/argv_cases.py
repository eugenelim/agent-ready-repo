"""The § D6 case table, generated — not retyped from the spec table.

Regenerate with, from the repository root::

    python3 -c "
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location(
        'spike_argv_boundary_for_generation',
        'docs/specs/work-item-capture/notes/spike-argv-boundary.py',
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = module.rows
    "

Every row is `spike-argv-boundary.py`'s own ``(argv, reason_code, why)`` —
computed by running that derivation's ``validate`` function over its own
``CASES``, never hand-transcribed from
``docs/specs/work-item-capture/spec.md`` § D6's rendered table. A row whose
verdict changes here is a contract change to that spec's § D6, not a
fixture edit — regenerating this file from the spike must reproduce it
byte-for-byte.

This module is data only: no import of the spike, no import of pytest, so it
stays importable by another spec's suite (the promotion-handoff spec's
re-check criterion reads it) without reaching across a pack or a repository
boundary at test time.
"""
from __future__ import annotations

# (argv, expected_reason_code_or_None_for_admit, why_this_case_exists)
ARGV_CASES: list[tuple[object, str | None, str]] = [
    (['cat', 'src/a.py'], None, 'baseline admission'),  # noqa: E501
    (['wc', 'docs/x.md'], None, 'baseline admission'),  # noqa: E501
    (['ls', 'docs'], None, 'baseline admission'),  # noqa: E501
    (['grep', 'AKIA', 'src/a.py'], None, 'baseline admission, fixed-string pattern'),  # noqa: E501
    ('cat src/a.py', 'work_item_command_shape', 'R1: string command'),  # noqa: E501
    (['find', '.', '-delete'], 'work_item_command_option', 'R1 sec: find -delete destroyed a file'),  # noqa: E501
    (['find', 'd', '-maxdepth', '0', '-fprint', 'o'], 'work_item_command_option', 'R1 sec: find -fprint wrote a file'),  # noqa: E501
    (['git', 'log', '--output=o'], 'work_item_command_option', 'R1 sec: git --output wrote a file'),  # noqa: E501
    (['rg', '--pre', './pre.sh', 'q', 'a.txt'], 'work_item_command_option', 'R1 sec: rg --pre executed a script'),  # noqa: E501
    (['git', '-c', 'diff.external=tee p', 'diff'], 'work_item_command_option', 'R2 sec: git -c reached execution'),  # noqa: E501
    (['cat', '-n', 'src/a.py'], 'work_item_command_option', 'R4 adv 12: option on an ADMITTED tool — the only rows above use tools the allowlist refuses anyway, so scoping the option rule to non-allowlisted tools reproduced every verdict'),  # noqa: E501
    (['ls', '-la', 'docs'], 'work_item_command_option', "R4 adv 12: second admitted tool with an option, so the case is not one tool's quirk"),  # noqa: E501
    (['grep', '-i', 'x', 'docs'], 'work_item_command_option', "R4 adv 12: option ahead of grep's exempt pattern slot"),  # noqa: E501
    (['git', 'cat-file', 'blob', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'], 'work_item_command_tool', 'R2 sec: reads a deleted blob'),  # noqa: E501
    (['git', 'show', 'HEAD:docs/x.md'], 'work_item_command_tool', 'R2 sec: anchored read, now excluded'),  # noqa: E501
    (['cat', '.git/config'], 'work_item_command_path', 'R3 sec F3: credential disclosure'),  # noqa: E501
    (['cat', '.env'], 'work_item_command_path', 'R3 sec F3: untracked secret'),  # noqa: E501
    (['cat'], 'work_item_command_operand', 'R3 sec F4: blocks on stdin'),  # noqa: E501
    ([], 'work_item_command_size', 'R3 sec F4: argv[0] undefined'),  # noqa: E501
    (['grep', 'pattern'], 'work_item_command_operand', 'R3 sec F4: grep with no operand'),  # noqa: E501
    ([1, 2], 'work_item_command_shape', 'R3 sec F5: non-string elements'),  # noqa: E501
    ([None], 'work_item_command_shape', 'R3 sec F5: null element'),  # noqa: E501
    ([['cat']], 'work_item_command_shape', 'R3 sec F5: nested list'),  # noqa: E501
    (['grep', 'a*', 'docs'], 'work_item_command_charset', 'R3 sec F6: glob survives re-serialisation'),  # noqa: E501
    (['cat', "a' '-delete"], 'work_item_command_charset', 'R3 sec F6: quote-split survives wrapping'),  # noqa: E501
    (['cat', 'docs\\x.md'], 'work_item_command_charset', 'R3 sec F7: backslash, enforcers disagreed'),  # noqa: E501
    (['cat', '../etc/passwd'], 'work_item_command_path', 'traversal'),  # noqa: E501
    (['cat', '/etc/passwd'], 'work_item_command_path', 'absolute path'),  # noqa: E501
    (['cat', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'], 'work_item_command_size', 'element length'),  # noqa: E501
    (['cat', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'], 'work_item_command_size', 'element count'),  # noqa: E501
    (['cat', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'], 'work_item_command_size', 'aggregate length'),  # noqa: E501
    (['cat', 'a\nb'], 'work_item_command_charset', 'newline in element'),  # noqa: E501
    (['cat', 'a;b'], 'work_item_command_charset', 'shell metacharacter'),  # noqa: E501
    (['cat', '.ssh/id_rsa'], 'work_item_command_path', 'iter2: dotdir beyond .git'),  # noqa: E501
    (['cat', 'docs/.hidden'], 'work_item_command_path', 'iter2: dotfile in a subdir'),  # noqa: E501
    (['grep', 'foo.*', 'docs'], 'work_item_command_charset', 'iter2: BRE metachar in pattern'),  # noqa: E501
    (['cat', 'a b'], 'work_item_command_charset', 'iter2: space element'),  # noqa: E501
    (['cat', 'a"b'], 'work_item_command_charset', 'iter2: double quote'),  # noqa: E501
    (['cat', 'docs/a-b_c.py'], None, 'iter2: ordinary path must survive'),  # noqa: E501
    (['grep', 'TODO:fix', 'docs/x.md'], None, 'iter2: ordinary pattern must survive'),  # noqa: E501
    (['cat', 'src/a.py\n'], 'work_item_command_charset', 'R4 sec B1: TRAILING newline, $ admitted it'),  # noqa: E501
    (['grep', 'AKIA\n', 'src/a.py'], 'work_item_command_charset', 'R4 sec B1: trailing newline in a pattern'),  # noqa: E501
    (['grep', 'a', 'b\n'], 'work_item_command_charset', 'R4 sec B1: trailing newline in a later path'),  # noqa: E501
    (['grep', '.env', 'docs'], None, 'R4 sec N9: pattern is exempt from the dot rule'),  # noqa: E501
    (['grep', '../../etc/passwd', 'docs'], None, 'R4 sec C4: pattern exempt from repositoryPath'),  # noqa: E501
    (['cat', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 'work_item_command_size', 'R5 sec C6: pins count-before-type ordering'),  # noqa: E501
]
