"""Confined offline inputs and the bounded GitHub Actions workflow language."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / '.apm/skills/release-loop/scripts/github_release.py'
FILES = {
    'readiness': ['controls', 'snapshot', 'deploy-workflow', 'deploy-job-workflow', 'prepare-workflow'],
    'bind': ['admission', 'controls', 'context', 'attempt', 'approvals', 'environment-settings',
             'prepare-run', 'prepare-artifacts', 'artifact-archive'],
    'budget': ['controls', 'listing'],
    'recheck': ['binding', 'decision', 'admission', 'controls', 'audit-receipt', 'audit-head',
                'audit-listing', 'live-snapshot', 'cloud-identity'],
    'reconcile': ['binding', 'controls', 'run', 'jobs', 'observed', 'audit-listing', 'ops'],
    'summary': ['binding', 'decision', 'audit-receipt', 'audit-readback', 'audit-head', 'observed', 'ops'],
}


def load_script() -> ModuleType:
    """Load the shipped module without changing Python's search path."""
    assert SCRIPT.is_file(), 'the workflow reader must be shipped'
    spec = importlib.util.spec_from_file_location('release_engineering_release_loop_github_release', SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Forbid all network and process operations during in-process cases."""
    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Fail at the external execution seam."""
        raise AssertionError('external operation forbidden')
    for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
        monkeypatch.setattr(subprocess, name, refuse)
    for name in ('socket', 'create_connection', 'socketpair', 'getaddrinfo'):
        monkeypatch.setattr(socket, name, refuse)
    monkeypatch.setattr(os, 'system', refuse)
    return load_script()


def argv(root: Path, command: str, flag: str = '', locator: str = '') -> list[str]:
    """Make minimal captured files; replace only the selected file argument."""
    args = [command, '--root', str(root)]
    for name in FILES[command]:
        path = root / name
        if not path.exists():
            path.write_bytes(b'[]' if name == 'observed' else b'{}')
        args += ['--' + name, locator if flag == name else name]
    if command == 'bind':
        args += ['--expect-admission-sha256', 'a' * 64, '--output', 'binding-out',
                 '--decision-output', 'decision-out']
    if command == 'recheck':
        (root / 'payload').write_bytes(b'example')
        args += ['--workflows-root', 'checkout', '--payload', 'effect=payload',
                 '--expect-role-arn-env', 'EXAMPLE_ROLE', '--expect-account-env', 'EXAMPLE_ACCOUNT']
        (root / 'checkout').mkdir(exist_ok=True)
    if command in ('budget', 'recheck', 'summary'):
        args += ['--now', '2026-01-01T00:00:00Z']
    return args


def invoke(module: ModuleType, args: list[str], capsys: Any) -> tuple[int, dict[str, Any]]:
    """Require one safe JSON object and no diagnostic spill to stderr."""
    code = module.main(args)
    out = capsys.readouterr()
    assert out.err == ''
    result = json.loads(out.out)
    assert isinstance(result, dict)
    assert 'private-input' not in out.out
    assert 'DO-NOT-ECHO' not in out.out
    return code, result


FILE_CASES = [(command, flag) for command, flags in FILES.items() for flag in flags]


@pytest.mark.parametrize('command,flag', FILE_CASES)
@pytest.mark.parametrize('kind', ['absolute', 'drive', 'backslash', 'dot', 'parent', 'empty',
                                  'symlink', 'hardlink', 'fifo', 'oversize', 'swap'])
def test_confinement(
    module: ModuleType, tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch,
    command: str, flag: str, kind: str,
) -> None:
    """Every file input reaches confinement before any semantic check."""
    args = argv(tmp_path, command)
    path = tmp_path / 'private-input'
    path.write_bytes(b'DO-NOT-ECHO')
    locator = 'private-input'
    if kind in ('absolute', 'drive', 'backslash', 'dot', 'parent', 'empty'):
        locator = {'absolute': str(path), 'drive': 'C:private-input',
                   'backslash': 'dir\\private-input', 'dot': './private-input',
                   'parent': '../private-input', 'empty': 'dir//private-input'}[kind]
    elif kind == 'symlink':
        (tmp_path / 'link').symlink_to(path)
        locator = 'link'
    elif kind == 'hardlink':
        os.link(path, tmp_path / 'linked')
    elif kind == 'fifo':
        path.unlink()
        os.mkfifo(path)
    elif kind == 'oversize':
        with path.open('wb') as stream:
            stream.truncate(module.ARCHIVE_LIMIT + 1 if flag == 'artifact-archive' else 1_048_577)
    else:
        original = os.read
        changed = False

        def swapped(fd: int, count: int) -> bytes:
            """Replace the directory entry after its descriptor has opened."""
            nonlocal changed
            if not changed and os.fstat(fd).st_ino == path.stat().st_ino:
                changed = True
                path.rename(tmp_path / 'original')
                path.write_bytes(b'DO-NOT-ECHO replacement')
            return original(fd, count)
        monkeypatch.setattr(os, 'read', swapped)
    args[args.index('--' + flag) + 1] = locator
    code, result = invoke(module, args, capsys)
    assert code == 2
    assert result['issues'] == [{'code': 'unreadable-input'}]


@pytest.mark.parametrize('command,flag', [pair for pair in FILE_CASES if 'workflow' not in pair[1]
                                         and pair[1] not in ('artifact-archive', 'audit-readback')])
@pytest.mark.parametrize('raw', [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                               b'{"x":-Infinity}', b'{"x":1e9999}', b'[' * 33 + b'0' + b']' * 33,
                               b'\xff', b'{"x":"\\ud800"}', b' ' * 1_048_577])
def test_strict_json(
    module: ModuleType, tmp_path: Path, capsys: Any, command: str, flag: str, raw: bytes,
) -> None:
    """Every JSON argument refuses ambiguous, non-finite or unbounded data."""
    args = argv(tmp_path, command)
    (tmp_path / flag).write_bytes(raw)
    code, result = invoke(module, args, capsys)
    assert code == 2
    assert result['issues'] == [{'code': 'unreadable-input'}]


@pytest.mark.parametrize('kind,value', [
    ('controls', {'extra': 'DO-NOT-ECHO'}),
    ('controls', {'agent': {'extra': 1}}), ('controls', {'audit': {'extra': 1}}),
    ('controls', {'cloud': {'extra': 1}}), ('controls', {'effects': [{'extra': 1}]}),
    ('controls', {'isolation': {'extra': 1}}),
    ('binding', {'extra': 1}), ('binding', {'target': {'extra': 1}}),
    ('binding', {'approvals': [{'extra': 1}]}),
    ('audit-receipt', {'extra': 1}), ('observed', [{'extra': 1}]),
    ('ops', {'extra': 1}), ('decision', {'extra': 1}),
])
def test_closed_shapes(module: ModuleType, tmp_path: Path, capsys: Any, kind: str, value: Any) -> None:
    """Unknown fields cannot extend owner controls or internal records."""
    command = next(command for command, flags in FILES.items() if kind in flags)
    args = argv(tmp_path, command)
    (tmp_path / kind).write_text(json.dumps(value), encoding='utf-8')
    assert invoke(module, args, capsys)[1]['issues'] == [{'code': 'unreadable-input'}]


def test_archive_hash_only(module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Archive bytes are hashed without interpreting or extracting members."""
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr('../escape', 'DO-NOT-ECHO')
    raw = data.getvalue()
    (tmp_path / 'archive').write_bytes(raw)

    def refuse(*args: Any, **kwargs: Any) -> Any:
        """An archive reader is unnecessary for a digest."""
        raise AssertionError('archive inspection forbidden')
    monkeypatch.setattr(zipfile, 'ZipFile', refuse)
    assert module.hash_archive(tmp_path, 'archive') == 'sha256:' + hashlib.sha256(raw).hexdigest()
    assert sorted(path.name for path in tmp_path.iterdir()) == ['archive']


@pytest.mark.parametrize('value', [
    {'text': 'DO-NOT-ECHO é [ { ] }', 'flag': True, 'number': 1.5},
    {'repository': 'example/project', 'agent': {'kind': 'app', 'slug': 'example-app'}},
    [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],
])
def test_valid_json(module: ModuleType, tmp_path: Path, value: Any) -> None:
    """The shared parser preserves valid values, including the depth boundary."""
    (tmp_path / 'input').write_bytes(json.dumps(value, ensure_ascii=False).encode())
    assert module.read_json(tmp_path, 'input') == value


def test_workflow_supported(module: ModuleType) -> None:
    """Block containers, scalars, comments and expressions retain their meaning."""
    raw = b'''# header
on: workflow_dispatch
permissions: {}
jobs:
  deploy:
    runs-on: [ubuntu-latest, "windows-latest", 'macos-latest'] # list
    enabled: true
    absent: null
    steps:
      - id: bind
        env:
          INPUT: ${{ inputs.x }}
        run: |-
          echo "hello: # literal"
          # not a comment
      - run: >
          first
          second
      - name: 'It''s ready'
        run: "echo \\u00e9"
    empty: []
'''
    assert module.read_workflow(raw) == {
        'on': 'workflow_dispatch', 'permissions': {}, 'jobs': {'deploy': {
            'runs-on': ['ubuntu-latest', 'windows-latest', 'macos-latest'],
            'enabled': True, 'absent': None,
            'steps': [{'id': 'bind', 'env': {'INPUT': '${{ inputs.x }}'},
                       'run': 'echo "hello: # literal"\n# not a comment'},
                      {'run': 'first second\n'}, {'name': "It's ready", 'run': 'echo é'}],
            'empty': [],
        }},
    }


@pytest.mark.parametrize('raw', [
    b'on: &dispatch workflow_dispatch', b'on: *dispatch', b'on: !!str workflow_dispatch',
    b'<<: {}', b'a: 1\na: 2', b'a: 1\n---\nb: 2', b'---\na: 1', b'a: 1\n...',
    b'a: [one,\n  two]', b'a: {one: two}', b'a:\n\tb: 1', b'a: [*alias]',
    b'a: [one, &anchor two]', b'a: [one, [two]]', b'a: "unterminated',
    b'a: |+\n  x', b'a: [one,,two]', b'a:\n  x: 1\n  x: 2', b'\xff',
    b'a: 1\n  b: 2', b'a: ["x" trailing]', b'a: "\\ud800"',
    b'a:\n' + b' ' * 1_048_576,
    b''.join(b'  ' * i + b'a:\n' for i in range(33)),
])
def test_workflow_unparsed(module: ModuleType, raw: bytes) -> None:
    """Unsupported or ambiguous workflow syntax has a single safe outcome."""
    with pytest.raises(module.Unparsed, match='^unparsed$'):
        module.read_workflow(raw)


@pytest.mark.parametrize('indicator,expected', [('|', 'a\nb\n'), ('|-', 'a\nb'),
                                                ('>', 'a b\n'), ('>-', 'a b')])
def test_block_styles(module: ModuleType, indicator: str, expected: str) -> None:
    """Literal and folded scalar trailing-newline rules differ as declared."""
    assert module.read_workflow(f'run: {indicator}\n  a\n  b\n'.encode()) == {'run': expected}


def test_scalar_edges(module: ModuleType) -> None:
    """Quoted commas and comment markers do not split flow values."""
    assert module.read_workflow(b'''x: ['a,b', "a#b", '${{ x }}', 'it''s', 1, false, null]
''') == {'x': ['a,b', 'a#b', '${{ x }}', "it's", 1, False, None]}


def test_quoted_escapes(module: ModuleType) -> None:
    """YAML quoted strings accept Unicode and YAML-specific escape sequences."""
    assert module.read_workflow(br'x: "\x41\u0042\U00000043\e\_"') == {
        'x': 'ABC\x1b\xa0',
    }


def test_indentless_sequence(module: ModuleType) -> None:
    """A block sequence may align with its owning mapping key."""
    assert module.read_workflow(b'steps:\n- run: example\nname: deploy\n') == {
        'steps': [{'run': 'example'}], 'name': 'deploy',
    }


def test_literal_content_tabs(module: ModuleType) -> None:
    """A tab after the block's space indentation is literal shell content."""
    assert module.read_workflow(b'run: |-\n  \tprintf example\n') == {
        'run': '\tprintf example',
    }


@pytest.mark.parametrize('raw,expected', [
    (b'run: >-\n  a\n\n  b\n', 'a\nb'),
    (b'run: >-\n  a\n    indented\n  b\n', 'a\n  indented\nb'),
    (b'run: |-\n  a\n\n  b\n\n', 'a\n\nb'),
    (b'run: |\r\n  a\r\n  b\r\n', 'a\nb\n'),
])
def test_block_whitespace(module: ModuleType, raw: bytes, expected: str) -> None:
    """Blank lines, relative indentation and CRLF preserve shell text."""
    assert module.read_workflow(raw) == {'run': expected}


@pytest.mark.parametrize('flag', ['output', 'decision-output'])
@pytest.mark.parametrize('kind', ['absolute', 'parent', 'dot', 'backslash', 'drive',
                                  'symlink', 'hardlink', 'fifo', 'oversize', 'swap'])
def test_output_confinement(
    module: ModuleType, tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch,
    flag: str, kind: str,
) -> None:
    """Even skeleton output arguments must pass the same path refusal checks."""
    test_confinement(module, tmp_path, capsys, monkeypatch, 'bind', flag, kind)


@pytest.mark.parametrize('kind', ['absolute', 'parent', 'dot', 'backslash', 'drive',
                                  'symlink', 'hardlink', 'fifo', 'oversize', 'swap'])
def test_payload_confinement(
    module: ModuleType, tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    """Payload locators are independently confined rather than treated as opaque argv."""
    args = argv(tmp_path, 'recheck')
    path = tmp_path / 'private-input'
    path.write_bytes(b'DO-NOT-ECHO')
    locator = '../private-input' if kind == 'parent' else 'private-input'
    if kind == 'absolute':
        locator = str(path)
    elif kind in ('dot', 'backslash', 'drive'):
        locator = {'dot': './private-input', 'backslash': 'x\\private-input',
                   'drive': 'C:private-input'}[kind]
    elif kind == 'symlink':
        (tmp_path / 'link').symlink_to(path)
        locator = 'link'
    elif kind == 'hardlink':
        os.link(path, tmp_path / 'linked')
    elif kind == 'fifo':
        path.unlink()
        os.mkfifo(path)
    elif kind == 'oversize':
        with path.open('wb') as stream:
            stream.truncate(module.ARCHIVE_LIMIT + 1)
    elif kind == 'swap':
        original = os.read
        changed = False

        def swapped(fd: int, count: int) -> bytes:
            """Change a payload entry while its old descriptor is pinned."""
            nonlocal changed
            if not changed and os.fstat(fd).st_ino == path.stat().st_ino:
                changed = True
                path.rename(tmp_path / 'original')
                path.write_bytes(b'replacement')
            return original(fd, count)

        monkeypatch.setattr(os, 'read', swapped)
    args[args.index('--payload') + 1] = 'effect=' + locator
    assert invoke(module, args, capsys)[1]['issues'] == [{'code': 'unreadable-input'}]


def test_cli_utf8(tmp_path: Path) -> None:
    """The real entrypoint emits one JSON object even under an ASCII locale."""
    result = subprocess.run([sys.executable, str(SCRIPT), 'DO-NOT-ECHO-é'],
                            env={**os.environ, 'PYTHONIOENCODING': 'ascii', 'PYTHONUTF8': '0'},
                            capture_output=True, check=False)
    assert result.returncode == 2
    assert result.stderr == b''
    assert json.loads(result.stdout)['issues'] == [{'code': 'usage'}]
    assert b'DO-NOT-ECHO' not in result.stdout


def test_stream_setup(module: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both streams are configured before any JSON is printed."""
    class Stream(io.StringIO):
        """Require UTF-8 configuration before accepting output."""
        configured = False

        def reconfigure(self, *, encoding: str) -> None:
            """Record the requested stream encoding."""
            assert encoding == 'utf-8'
            self.configured = True

        def write(self, value: str) -> int:
            """Reject output before both streams have been configured."""
            assert stdout.configured and stderr.configured
            return super().write(value)
    stdout, stderr = Stream(), Stream()
    monkeypatch.setattr(sys, 'stdout', stdout)
    monkeypatch.setattr(sys, 'stderr', stderr)
    assert module.main(['DO-NOT-ECHO']) == 2
    assert json.loads(stdout.getvalue())['status'] == 'error'
    assert stderr.getvalue() == ''
