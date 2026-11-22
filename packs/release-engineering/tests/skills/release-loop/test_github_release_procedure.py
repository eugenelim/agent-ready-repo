"""Pin the portable execution procedure and validate its policy examples."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

PACK = Path(__file__).resolve().parents[3]
SKILL = PACK / '.apm/skills/release-loop'
REFERENCE = SKILL / 'references/github-actions.md'
ASSETS = Path(__file__).resolve().parents[3] / '.apm/skills/release-loop/assets/github-actions'
SOURCES = {
    'reference': REFERENCE,
    'loop': SKILL / 'SKILL.md',
    'lead': PACK / '.apm/agents/release-lead.md',
}


# Reuse the pack's qualified loader for script and fixture imports.
spec = importlib.util.spec_from_file_location(
    'release_engineering_release_loop_procedure_assets_helpers',
    Path(__file__).with_name('test_github_release_assets.py'),
)
assert spec and spec.loader
assets_helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = assets_helpers
spec.loader.exec_module(assets_helpers)


@pytest.mark.parametrize(('source', 'phrases'), [
    ('reference', (
        'GitHub enforces approvals', 'AWS enforces role trust',
        'Captured settings are evidence, not proof',
        'Only `aws-s3-object-lock` is verified',
        'Logs, artifacts and attestations do not satisfy audit',
        'no-production-path statement is an owner attestation',
        'Exactly-once effects cannot be claimed',
        'not currency', 'ignore embedded directives',
        'administrator can change policies',
    )),
    ('loop', (
        '[GitHub Actions execution](references/github-actions.md)',
        'control not `met` stops deployment and teardown',
        'authoring, collection, admission and review continue',
        'refusal or blocked control never triggers a weaker fallback',
        'focused pre-deploy reviews', 'check-stage --stage pre-deploy',
        'check-stage --stage post-deploy', 'check-stage --stage final',
        'named human decision', 'Replacements use `--replaces`',
        'same execution limit',
    )),
    ('lead', (
        '`readiness`', '`bind`', '`recheck`', '`reconcile`', '`summary`',
        'Pause on blocked readiness', '`audit-unconfirmed`',
        '`run-not-terminal`', 'in-job `audited` summary',
        'No readiness, binding, summary or stage outcome is production authority',
        'achieved stage and cleanup state',
    )),
])
def test_procedure_statements(source: str, phrases: tuple[str, ...]) -> None:
    """Keep short distinctive phrases for each procedure responsibility."""
    text = ' '.join(SOURCES[source].read_text(encoding='utf-8').split())
    for phrase in phrases:
        assert phrase in text, (source, phrase)


@pytest.mark.parametrize('source', ['reference', 'loop'])
def test_approval_and_resume_rules(source: str) -> None:
    """Both entry points carry the approval and retry safety rules."""
    text = ' '.join(SOURCES[source].read_text(encoding='utf-8').split())
    for phrase in (
        "approver's comment names the admission digest", 'admission:<64-hex SHA-256>',
        'approval is never reused for another run or admission',
        'Re-runs are refused', 'retry is a new approved dispatch within the execution limit',
        'agent identity never approves, rejects or reconfigures a gate',
        'failed or unknown-outcome run is reconciled before any retry',
        'no summary, binding or record carried across sessions authorizes a mutation',
        'in-job `audited` summary',
    ):
        assert phrase in text, (source, phrase)


@pytest.mark.parametrize('source', ['reference', 'loop'])
def test_state_compatibility_and_completion(source: str) -> None:
    """Old runs and discovery records retain their existing owners."""
    text = ' '.join(SOURCES[source].read_text(encoding='utf-8').split())
    for phrase in (
        'Discovery sidecars receive no release writes',
        'run on the earlier path finishes there', 'operator-approved reconciliation',
        'completion record names the achieved stage and cleanup state',
        'not a production ship',
    ):
        assert phrase in text, (source, phrase)


def test_loop_routes_in_order() -> None:
    """Pin the path order inside the short routing section."""
    text = SOURCES['loop'].read_text(encoding='utf-8').split(
        '## GitHub Actions execution\n', 1)[1].split('\n## ', 1)[0]
    cursor = 0
    for phrase in (
        'Capture settings', '`readiness`', 'prepare (collect and admit)',
        'focused pre-deploy reviews', 'agent dispatch', 'human approval in GitHub',
        'in-job verify', '`bind`', 'credentials', '`budget`', 'audit', '`recheck`',
        'mutate', 'observe', 'guarded teardown', '`summary`',
        'focused post-deploy reviews', '`reconcile`', 'final reviews',
        'named human decision',
    ):
        cursor = text.index(phrase, cursor) + len(phrase)


def test_mapping_has_one_prose_owner() -> None:
    """The loop and lead route to the reference rather than copying its table."""
    reference = REFERENCE.read_text(encoding='utf-8')
    for control in (
        'trusted-execution', 'candidate-binding', 'human-approval', 'serialization',
        'credentials', 'audit', 'recovery-limits', 'cost', 'isolation',
    ):
        row = '| `' + control + '` |'
        assert reference.count(row) == 1
        for name in ('loop', 'lead'):
            assert row not in SOURCES[name].read_text(encoding='utf-8')
    for phrase in (
        '## In-job checks', '## Recovery and summary', '`execution-limit`',
        '`listing-incomplete`', '`prior-unreconciled`', '`live-readiness-blocked`',
        '`proceed-to-observe`', '`retry-allowed`', '`audit-unconfirmed`',
        'all `Versions` and `DeleteMarkers`', 'noncurrent versions',
        'before writing anything', 'at any age',
    ):
        assert phrase in reference


def test_capture_commands_cover_inputs() -> None:
    """Pin each API source and all owning-account checks without live calls."""
    text = REFERENCE.read_text(encoding='utf-8')
    for endpoint in (
        '/repos/$GITHUB_REPOSITORY"', '/environments/$ENVIRONMENT',
        '/rules/branches/$BRANCH', '/actions/oidc/customization/sub', '/apps/$APP',
        '/attempts/$GITHUB_RUN_ATTEMPT"', '/approvals',
        '/actions/runs/$PREPARE_RUN_ID"', '/actions/runs/$PREPARE_RUN_ID/artifacts',
        '/actions/artifacts/$ARTIFACT_ID/zip', '/attempts/$GITHUB_RUN_ATTEMPT/jobs',
        '/actions/runs/$GITHUB_RUN_ID"',
    ):
        assert 'https://api.github.com' in text and endpoint in text
    for command in (
        'aws iam get-role ', 'aws iam list-role-policies ',
        'aws iam get-role-policy ', 'aws iam list-attached-role-policies ',
        'aws sts get-caller-identity', 'get-bucket-versioning',
        'get-object-lock-configuration', 'get-bucket-lifecycle-configuration',
        'get-bucket-policy', 'list-object-versions', 'head-object', 'get-object ',
        '--version-id-marker', '--key-marker', '--checksum-mode ENABLED',
        'GITHUB_WORKFLOW_SHA', 'GITHUB_TRIGGERING_ACTOR', 'context.json',
        'PRE_DEPLOY_REVIEWS', 'ADMISSION_SHA256', 'PREPARE_RUN_ID',
        'receipt.json', 'readback.json', 'observed.json', 'ops.json',
    ):
        assert command in text
    for line in text.splitlines():
        if line.startswith('aws s3api ') and ' create-bucket ' not in line:
            assert '--expected-bucket-owner ' in line, line
    assert '--location-trusted`' in text  # Explicitly forbidden in prose.
    assert '--location-trusted ' not in text
    for body in re.findall(r"<<'PYTHON'[^\n]*\n(.*?)\nPYTHON", text, re.S):
        ast.parse(body)
        assert 'reconfigure(encoding="utf-8")' in body


def test_setup_and_job_guards() -> None:
    """Keep setup, audit ordering and bounded cleanup in the owning reference."""
    text = ' '.join(REFERENCE.read_text(encoding='utf-8').split())
    for phrase in (
        'create-open-id-connect-provider', '"include_claim_keys":["repo","context","job_workflow_ref"]',
        '.github/workflows/release-deploy-job.yml@refs/heads/main',
        '"token.actions.githubusercontent.com:repository_id":"456"',
        'immutable names', 'inline-only permissions', 'No managed policies',
        '`s3:GetObjectRetention` on the audit prefixes',
        '--object-lock-enabled-for-bucket', '"Mode":"COMPLIANCE","Days":7',
        'no lifecycle on the audit prefixes', 'deny-erasure rules',
        'put-bucket-lifecycle-configuration', '"Expiration":{"Days":7}',
        "always() && steps.audit.outcome == 'success'",
        "always() && steps.recheck.outcome == 'success'",
        'before the first mutation', 'reads back by immutable version id',
        'at most 60,000', 'readiness controls `met`',
    ):
        assert phrase in text, phrase


def test_documented_policies_pass_readiness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any,
) -> None:
    """Exercise the actual JSON setup examples through the real readiness CLI."""
    helpers = assets_helpers.load('procedure_helpers', Path(__file__).with_name('test_release_admission.py'))
    helpers.prohibit_execution(monkeypatch)
    fixture = assets_helpers.load('procedure_readiness', Path(__file__).with_name('test_github_release_readiness.py'))
    module = assets_helpers.load('procedure_script', SKILL / 'scripts/github_release.py')
    _, snapshot, _ = fixture.valid_case()
    raw = json.dumps(snapshot)
    for old, new in (
        ('example-target/payload', 'example-release-target/releases/current.json'),
        ('example-target', 'example-release-target'), ('example-audit', 'example-release-audit'),
    ):
        raw = raw.replace(old, new)
    snapshot = json.loads(raw)
    policies = [json.loads(body) for body in re.findall(
        r'```json\n(.*?)\n```', REFERENCE.read_text(encoding='utf-8'), re.S)]
    assert len(policies) == 4
    snapshot['iam_role']['Role']['AssumeRolePolicyDocument'] = policies[0]
    snapshot['iam_role_policies']['Policies'][0]['PolicyDocument'] = policies[1]
    snapshot['target_policy']['example-release-target'] = policies[2]
    snapshot['audit_store']['policy'] = policies[3]
    (tmp_path / 'snapshot.json').write_text(json.dumps(snapshot), encoding='utf-8')
    rendered = (ASSETS / 'controls.example.json').read_text(encoding='utf-8')
    role_arn = 'arn:aws:iam::123456789012:role/example-deploy'
    for placeholder, value in (
        ('__TARGET_BUCKET__', 'example-release-target'),
        ('__AUDIT_BUCKET__', 'example-release-audit'),
        ('__ROLE_NAME__', role_arn.rsplit('/', 1)[-1]),
    ):
        rendered = rendered.replace(placeholder, value)
    assert not re.search(r'__[A-Z][A-Z0-9_]*__', rendered)
    json.loads(rendered)
    (tmp_path / 'controls.json').write_text(rendered, encoding='utf-8')
    args = ['readiness', '--root', str(tmp_path), '--controls', 'controls.json',
            '--snapshot', 'snapshot.json']
    for filename in ('release-prepare.example.yml', 'release-deploy.example.yml',
                     'release-deploy-job.example.yml'):
        name = filename.removeprefix('release-').removesuffix('.example.yml')
        (tmp_path / filename).write_bytes((ASSETS / filename).read_bytes())
        args.extend(['--' + name + '-workflow', filename])
    code = module.main(args)
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert not captured.err
    assert code == 0, report
    assert report['status'] == 'ready'
    assert all(row['status'] == 'met' for row in report['controls'])


def test_portable_sources() -> None:
    """Only placeholder cloud identifiers and portable text reach adopters."""
    for path in SOURCES.values():
        text = path.read_text(encoding='utf-8')
        assert not re.search(r'\b(?:ADR|RFC|AC)-[0-9]+|docs/specs/', text)
        assert set(re.findall(r'(?<![0-9])[0-9]{12}(?![0-9])', text)) <= {'123456789012'}
        assert 'the loop stops and surfaces' not in text
