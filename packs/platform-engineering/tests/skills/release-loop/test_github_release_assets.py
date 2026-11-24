"""Exercise the shipped GitHub workflows through the real bounded reader."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PACK = Path(__file__).resolve().parents[3]
ASSETS = Path(__file__).resolve().parents[3] / '.apm/skills/release-loop/assets/github-actions'


def load(name: str, path: Path) -> ModuleType:
    """Load a pack-local module without changing the module search path."""
    spec = importlib.util.spec_from_file_location('release_engineering_release_loop_' + name, path)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def setup_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, list[str]]:
    """Reuse the readiness fixture and forbid processes and network access."""
    helper = load('assets_fixture', Path(__file__).with_name('test_github_release_readiness.py'))
    module = load('assets_script', PACK / '.apm/skills/release-loop/scripts/github_release.py')

    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Fail if a pure check tries an external operation."""
        raise AssertionError('external operation forbidden')

    for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
        monkeypatch.setattr(helper.subprocess, name, refuse)
    for name in ('socket', 'create_connection', 'socketpair', 'getaddrinfo'):
        monkeypatch.setattr(helper.socket, name, refuse)
    monkeypatch.setattr(helper.os, 'system', refuse)
    controls = json.loads((ASSETS / 'controls.example.json').read_text().replace(
        '__TARGET_BUCKET__', 'example-release-target').replace(
        '__AUDIT_BUCKET__', 'example-release-audit').replace('__ROLE_NAME__', 'example-deploy'))
    _, snapshot, _ = helper.valid_case()
    raw = json.dumps(snapshot)
    for old, new in [('example-target/payload', 'example-release-target/releases/current.json'),
                     ('example-target', 'example-release-target'),
                     ('example-audit', 'example-release-audit'),
                     ('deploy-job.yml', 'release-deploy-job.yml')]:
        raw = raw.replace(old, new)
    snapshot = json.loads(raw)
    snapshot['iam_role_policies']['Policies'][0]['PolicyDocument']['Statement'].append({
        'Effect': 'Allow', 'Action': 's3:GetObjectRetention',
        'Resource': controls['audit']['decision_prefix'] + '*',
    })
    (tmp_path / 'controls.json').write_text(json.dumps(controls))
    (tmp_path / 'snapshot.json').write_text(json.dumps(snapshot))
    args = ['readiness', '--root', str(tmp_path), '--controls', 'controls.json',
            '--snapshot', 'snapshot.json']
    for name, source in (('prepare', ASSETS / 'release-prepare.example.yml'),
                         ('deploy', ASSETS / 'release-deploy.example.yml'),
                         ('deploy-job', ASSETS / 'release-deploy-job.example.yml')):
        filename = source.name
        shutil.copyfile(source, tmp_path / filename)
        args.extend(['--' + name + '-workflow', filename])
    return module, args


def test_example_ready(setup_case: Any, capsys: Any) -> None:
    """All readiness rows meet the real examples without rewriting their bytes."""
    module, args = setup_case
    code = module.main(args)
    report = json.loads(capsys.readouterr().out)
    assert code == 0, report
    assert report['status'] == 'ready'
    assert all(row['status'] == 'met' for row in report['controls'])
    assert report['blocked_mutations'] == []


def test_workflow_contract(setup_case: Any) -> None:
    """Pin executable safety details beyond the readiness reader's structural checks."""
    module, _ = setup_case
    sources = {'prepare': (ASSETS / 'release-prepare.example.yml').read_bytes(),
               'deploy': (ASSETS / 'release-deploy.example.yml').read_bytes(),
               'deploy-job': (ASSETS / 'release-deploy-job.example.yml').read_bytes()}
    workflows = {name: module.read_workflow(raw) for name, raw in sources.items()}
    for workflow in workflows.values():
        for job in workflow['jobs'].values():
            for step in job.get('steps', []):
                assert '${{' not in step.get('run', '')
                if 'uses' in step:
                    assert re.fullmatch(r'actions/(checkout|upload-artifact)@[0-9a-f]{40}', step['uses'])
    prepare = workflows['prepare']['jobs']['prepare']
    assert 'environment' not in prepare
    assert 'id-token' not in prepare['permissions']
    assert sum('actions/upload-artifact@' in step.get('uses', '') for step in prepare['steps']) == 1
    job = workflows['deploy-job']['jobs']['deploy']
    steps = {step.get('id'): step for step in job['steps']}
    assert '60000' in steps['verify-admission']['run']
    assert 'check-stage --stage pre-deploy' in steps['verify-admission']['run']
    assert 'release_admission.py verify' in steps['verify-admission']['run']
    for name in ('teardown', 'summary'):
        assert steps[name]['if'] == "always() && steps.recheck.outcome == 'success'"
    assert steps['ops']['if'] == "always() && steps.audit.outcome == 'success'"
    text = (ASSETS / 'release-deploy-job.example.yml').read_text()
    assert 'python3 -m zipfile' in text
    assert 'assume-role-with-web-identity' in text
    assert '::add-mask::' in text
    assert '--checksum-algorithm SHA256' in text
    assert '--metadata "marker=$MARKER"' in text
    assert 'list-object-versions' in text
    for line in text.splitlines():
        if 'aws s3api ' in line:
            assert '--expected-bucket-owner "$RELEASE_CLOUD_ACCOUNT"' in line
    for name in ('RELEASE_ROLE_ARN', 'RELEASE_CLOUD_ACCOUNT', 'RELEASE_TARGET_BUCKET', 'RELEASE_AUDIT_BUCKET'):
        assert 'secrets.' + name in text


def test_placeholders_only() -> None:
    """Assets contain only synthetic cloud identifiers and portable guidance."""
    for path in ASSETS.iterdir():
        text = path.read_text()
        assert set(re.findall(r'(?<![0-9])[0-9]{12}(?![0-9])', text)) <= {'123456789012'}
        assert not re.search(r'\b(?:ADR|RFC|AC)-[0-9]+|docs/specs/', text)
    controls = json.loads((ASSETS / 'controls.example.json').read_text())
    assert controls['effects'][0]['resource'] == 'arn:aws:s3:::__TARGET_BUCKET__/releases/current.json'
    assert controls['effects'][0]['payload_component'] == 'app'


def test_step_names_match_ids(setup_case: Any) -> None:
    """The jobs API reports step names, so reconcile finds mutate- steps only by name."""
    module, _ = setup_case
    raw = (ASSETS / 'release-deploy-job.example.yml').read_bytes()
    steps = module.read_workflow(raw)['jobs']['deploy']['steps']
    named = [step for step in steps if 'id' in step]
    assert named and all(step.get('name') == step['id'] for step in named)


def test_native_listing_capture(setup_case: Any, tmp_path: Path,
                                monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    """Execute the shipped page assembly and ops enrichment against native pages."""
    module, _ = setup_case
    workflow = module.read_workflow((ASSETS / 'release-deploy-job.example.yml').read_bytes())
    steps = {step['id']: step for step in workflow['jobs']['deploy']['steps'] if 'id' in step}
    monkeypatch.chdir(tmp_path)
    pages_dir = tmp_path / 'work/pages'
    pages_dir.mkdir(parents=True)
    pages = [
        {'KeyMarker': '', 'VersionIdMarker': '', 'NextKeyMarker': 'decisions/example',
         'NextVersionIdMarker': 'example-1', 'IsTruncated': True,
         'Versions': [{'Key': 'decisions/example', 'VersionId': str(i)} for i in range(1000)],
         'DeleteMarkers': []},
        {'KeyMarker': 'decisions/example', 'VersionIdMarker': 'example-1',
         'IsTruncated': False, 'Versions': [{'Key': 'decisions/example', 'VersionId': str(i)}
                                          for i in range(1000, 2000)], 'DeleteMarkers': []},
        {'IsTruncated': False, 'Versions': [
            {'Key': 'ops/sandbox/42-1.json', 'VersionId': str(i)} for i in range(500)],
         'DeleteMarkers': [{'Key': 'ops/sandbox/old.json', 'VersionId': 'example-deleted'}]},
    ]
    for index, page in enumerate(pages):
        (pages_dir / f'{index}.json').write_text(json.dumps(page))
    native_bytes = [path.read_bytes() for path in sorted(pages_dir.iterdir())]
    for name in ('budget', 'recheck'):
        source = steps[name]['run']
        snippet = source.split('python3 - "$count" <<\'PY\'\n', 1)[1].split('\nPY', 1)[0]
        monkeypatch.setattr(sys, 'argv', ['capture', '3'])
        exec(compile(snippet, '<page-assembly>', 'exec'), {})
        assert json.loads((tmp_path / 'work/listing.json').read_bytes()) == pages
    source = steps['budget']['run']
    snippet = source.split("python3 - <<'PY' > work/ops-versions.tsv\n", 1)[1].split('\nPY', 1)[0]
    controls = json.loads((ASSETS / 'controls.example.json').read_bytes())
    (tmp_path / 'work/controls.json').write_text(json.dumps(controls))
    exec(compile(snippet, '<ops-selection>', 'exec'), {})
    selected = capsys.readouterr().out.splitlines()
    assert len(selected) == 500
    assert selected[-1] == 'ops/sandbox/42-1.json\t499'
    snippet = source.split('KEY="$key" VERSION="$version" python3 - <<\'PY\'\n', 1)[1].split('\nPY', 1)[0]
    monkeypatch.setenv('KEY', 'ops/sandbox/42-1.json')
    monkeypatch.setenv('VERSION', '499')
    record = {'run_id': 42, 'run_attempt': 1, 'outcome': 'no-mutation', 'operations': []}
    (tmp_path / 'work/prior-ops.json').write_text(json.dumps(record))
    exec(compile(snippet, '<ops-enrichment>', 'exec'), {})
    enriched = json.loads((tmp_path / 'work/listing.json').read_bytes())
    pages[-1]['Versions'][-1]['record'] = record
    assert enriched == pages
    assert [path.read_bytes() for path in sorted(pages_dir.iterdir())] == native_bytes


@pytest.mark.parametrize('source_name', ['workflow', 'capture'])
@pytest.mark.parametrize('change', ['none', 'unresolved', 'invalid-json'])
def test_rendered_controls(setup_case: Any, tmp_path: Path,
                           monkeypatch: pytest.MonkeyPatch, source_name: str, change: str) -> None:
    """Both real recipes render private names locally and refuse unusable templates."""
    module, _ = setup_case
    workflow = module.read_workflow((ASSETS / 'release-deploy-job.example.yml').read_bytes())
    steps = {step['id']: step for step in workflow['jobs']['deploy']['steps'] if 'id' in step}
    source = (steps['verify-admission']['run'] if source_name == 'workflow' else
              (ASSETS.parent.parent / 'references/github-actions.md').read_text())
    snippet = source.split("python3 - <<'CONTROLS'\n", 1)[1].split('\nCONTROLS', 1)[0]
    template = (ASSETS / 'controls.example.json').read_text()
    if change == 'unresolved':
        template = template.replace('__TARGET_BUCKET__', '__UNKNOWN_BUCKET__')
    elif change == 'invalid-json':
        template += 'invalid'
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'work').mkdir(exist_ok=True)
    output = tmp_path / 'work/controls.json'
    output.unlink(missing_ok=True)
    (tmp_path / 'release-controls.template.json').write_text(template)
    monkeypatch.setenv('RELEASE_TARGET_BUCKET', 'example-private-target')
    monkeypatch.setenv('RELEASE_AUDIT_BUCKET', 'example-private-audit')
    monkeypatch.setenv('RELEASE_ROLE_ARN', 'arn:aws:iam::123456789012:role/ci/example-private-role')
    if change != 'none':
        with pytest.raises(ValueError):
            exec(compile(snippet, '<controls-render>', 'exec'), {})
        assert not output.exists()
        return
    exec(compile(snippet, '<controls-render>', 'exec'), {})
    controls = json.loads(output.read_bytes())
    assert controls['cloud']['role_name'] == 'example-private-role'
    assert controls['audit']['decision_prefix'] == 'arn:aws:s3:::example-private-audit/decisions/'
    assert controls['audit']['ops_prefix'] == 'arn:aws:s3:::example-private-audit/ops/'
    assert controls['effects'][0]['resource'] == 'arn:aws:s3:::example-private-target/releases/current.json'
    assert '__' not in output.read_text()


def test_empty_native_capture_to_budget(setup_case: Any, tmp_path: Path,
                                       monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    """The shipped capture preserves omitted arrays and bootstraps a fresh audit store."""
    module, _ = setup_case
    workflow = module.read_workflow((ASSETS / 'release-deploy-job.example.yml').read_bytes())
    budget_step = next(step for step in workflow['jobs']['deploy']['steps']
                       if step.get('id') == 'budget')
    snippet = budget_step['run'].split("python3 - \"$count\" <<'PY'\n", 1)[1].split('\nPY', 1)[0]
    monkeypatch.chdir(tmp_path)
    pages = tmp_path / 'work/pages'
    pages.mkdir(parents=True)
    for index, prefix in enumerate(('decisions/sandbox/', 'ops/sandbox/')):
        (pages / f'{index}.json').write_text(json.dumps({
            'Prefix': prefix, 'IsTruncated': False, 'KeyMarker': '', 'VersionIdMarker': '',
            'MaxKeys': 1000,
        }))
    monkeypatch.setattr(sys, 'argv', ['capture', '2'])
    exec(compile(snippet, '<empty-page-assembly>', 'exec'), {})
    assert module.main(['budget', '--root', str(tmp_path), '--controls', 'controls.json',
                        '--listing', 'work/listing.json', '--now', '2026-01-01T12:30:00Z']) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['status'] == 'available' and report['executions_used'] == 0
