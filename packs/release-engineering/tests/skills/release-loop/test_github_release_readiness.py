"""Readiness evaluates captured settings without executing their content."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / '.apm/skills/release-loop/scripts/github_release.py'
ROLE = 'arn:aws:iam::123456789012:role/example-deploy'
TARGET = 'arn:aws:s3:::example-target/payload'
DECISIONS = 'arn:aws:s3:::example-audit/decisions/'
OPS = 'arn:aws:s3:::example-audit/ops/'
INPUT_NAMES = ('prepare_run_id', 'admission_sha256', 'pre_deploy_reviews')
ERASURE = ['s3:BypassGovernanceRetention', 's3:PutObjectRetention', 's3:PutObjectLegalHold',
           's3:PutBucketObjectLockConfiguration', 's3:DeleteObject*', 's3:PutBucketVersioning',
           's3:PutLifecycleConfiguration']


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load by a qualified name with process and network operations forbidden."""
    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Reject any external operation."""
        raise AssertionError('external operation forbidden')
    for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
        monkeypatch.setattr(subprocess, name, refuse)
    for name in ('socket', 'create_connection', 'socketpair', 'getaddrinfo'):
        monkeypatch.setattr(socket, name, refuse)
    monkeypatch.setattr(os, 'system', refuse)
    spec = importlib.util.spec_from_file_location(
        'release_engineering_release_loop_github_release_readiness', SCRIPT,
    )
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def writer_deny(resource: str) -> dict[str, Any]:
    """Describe an unconditional resource deny except for the deploy role."""
    return {'Effect': 'Deny', 'Principal': '*', 'Action': 's3:*', 'Resource': resource,
            'Condition': {'ArnNotEquals': {'aws:PrincipalArn': ROLE}}}


def valid_case() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build raw GitHub/AWS responses and parsed workflows in isolation."""
    controls = {
        'repository': 'example-owner/example-repo', 'repository_id': 456,
        'environment': 'sandbox', 'release_branch': 'main',
        'prepare_workflow': '.github/workflows/prepare.yml',
        'deploy_workflow': '.github/workflows/deploy.yml',
        'deploy_job_workflow': '.github/workflows/deploy-job.yml',
        'agent': {'kind': 'app', 'slug': 'example-agent', 'login': 'example-agent[bot]'},
        'concurrency_group': 'example-release', 'max_executions': 3, 'budget_window_days': 7,
        'reconciled_runs': [],
        'audit': {'kind': 'aws-s3-object-lock', 'minimum_retention_days': 2,
                  'decision_prefix': DECISIONS, 'ops_prefix': OPS},
        'cloud': {'provider': 'aws', 'account_label': 'example-sandbox',
                  'account_secret': 'EXAMPLE_ACCOUNT', 'role_secret': 'EXAMPLE_ROLE',
                  'role_name': 'example-deploy', 'audience': 'sts.amazonaws.com',
                  'allowed_actions': ['s3:PutObject', 's3:GetObject', 's3:DeleteObject',
                                      's3:GetBucketPolicy', 'iam:GetRole']},
        'effects': [{'id': 'example-payload', 'kind': 'aws-s3-object', 'resource': TARGET,
                     'payload_component': 'application', 'max_payload_bytes': 1024}],
        'isolation': {'classification': 'non-production', 'attested_by': 'example-owner'},
    }
    permissions = {'contents': 'read', 'actions': 'read'}
    inputs = dict.fromkeys(INPUT_NAMES, {'type': 'string', 'required': True})
    prepare = {'on': {'workflow_dispatch': {}}, 'permissions': permissions.copy(),
               'jobs': {'prepare': {'permissions': permissions.copy(), 'runs-on': 'ubuntu-latest',
                                    'steps': [{'uses': 'actions/checkout@' + 'a' * 40}]}}}
    caller = {'on': {'workflow_dispatch': {'inputs': inputs}}, 'permissions': permissions.copy(),
              'jobs': {'deploy': {'permissions': permissions.copy(),
                                  'uses': './' + controls['deploy_job_workflow'],
                                  'with': {key: '${{ inputs.' + key + ' }}' for key in INPUT_NAMES},
                                  'secrets': {'account': '${{ secrets.EXAMPLE_ACCOUNT }}',
                                              'role': '${{ secrets.EXAMPLE_ROLE }}'}}}}
    job = {'permissions': {**permissions, 'id-token': 'write'}, 'runs-on': 'ubuntu-latest',
           'environment': 'sandbox',
           'concurrency': {'group': 'example-release', 'cancel-in-progress': False},
           'steps': [{'id': key, 'run': 'printf example'} for key in
                     ('verify-admission', 'bind', 'credentials', 'budget', 'audit', 'recheck',
                      'mutate-deploy', 'teardown')]}
    job['steps'][-1]['if'] = "always() && steps.recheck.outcome == 'success'"
    worker = {'on': {'workflow_call': {'inputs': copy.deepcopy(inputs)}},
              'permissions': job['permissions'].copy(), 'jobs': {'deploy': job}}
    subject = ('repo:example-owner/example-repo:environment:sandbox:job_workflow_ref:'
               'example-owner/example-repo/.github/workflows/deploy-job.yml@refs/heads/main')
    policies = [
        {'Effect': 'Allow', 'Action': ['s3:PutObject', 's3:GetObject', 's3:DeleteObject'],
         'Resource': TARGET},
        {'Effect': 'Allow', 'Action': ['s3:PutObject', 's3:GetObject'],
         'Resource': [DECISIONS + '*', OPS + '*']},
        {'Effect': 'Allow', 'Action': 's3:GetBucketPolicy',
         'Resource': ['arn:aws:s3:::example-audit', 'arn:aws:s3:::example-target']},
        {'Effect': 'Allow', 'Action': 'iam:GetRole', 'Resource': ROLE},
    ]
    snapshot = {
        'repository': {'id': 456, 'owner': {'login': 'example-owner', 'id': 123}},
        'environment': {'protection_rules': [
            {'type': 'required_reviewers', 'prevent_self_review': True,
             'reviewers': [{'type': 'User', 'reviewer': {'login': 'example-reviewer', 'id': 789}}]},
            {'type': 'branch_policy'}], 'can_admins_bypass': False,
            'deployment_branch_policy': {'protected_branches': True, 'custom_branch_policies': False}},
        'branch_rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'},
                         {'type': 'pull_request',
                          'parameters': {'required_approving_review_count': 1}}],
        'oidc_subject_template': {'use_default': False,
                                  'include_claim_keys': ['repo', 'context', 'job_workflow_ref'],
                                  'use_immutable_subject': False,
                                  'sub_claim_prefix': 'repo:example-owner/example-repo'},
        'agent_app': {'slug': 'example-agent', 'permissions': {'actions': 'write'}},
        'iam_role': {'Role': {'Arn': ROLE, 'RoleName': 'example-deploy',
                             'AssumeRolePolicyDocument': {'Version': '2012-10-17', 'Statement': [{
                                 'Effect': 'Allow', 'Action': 'sts:AssumeRoleWithWebIdentity',
                                 'Principal': {'Federated':
                                               'arn:aws:iam::123456789012:oidc-provider/'
                                               'token.actions.githubusercontent.com'},
                                 'Condition': {'StringEquals': {
                                     'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
                                     'token.actions.githubusercontent.com:sub': subject,
                                     'token.actions.githubusercontent.com:repository_id': '456'}}}]}}},
        'iam_role_policies': {'PolicyNames': ['example-inline'], 'Policies': [
            {'RoleName': 'example-deploy', 'PolicyName': 'example-inline',
             'PolicyDocument': {'Version': '2012-10-17', 'Statement': policies}}],
                              'AttachedPolicies': []},
        'audit_store': {'versioning': {'Status': 'Enabled'},
                        'object_lock': {'ObjectLockConfiguration': {
                            'ObjectLockEnabled': 'Enabled', 'Rule': {'DefaultRetention': {
                                'Mode': 'COMPLIANCE', 'Days': 7}}}},
                        'lifecycle': {'Rules': []},
                        'policy': {'Policy': json.dumps({'Statement': [
                            writer_deny(DECISIONS + '*'), writer_deny(OPS + '*'),
                            {'Effect': 'Deny', 'Principal': '*', 'Action': ERASURE.copy(),
                             'Resource': ['arn:aws:s3:::example-audit',
                                          'arn:aws:s3:::example-audit/*']}]})}},
        'target_policy': {'example-target': {'Policy': json.dumps({
            'Statement': [writer_deny(TARGET)]})}},
        'target_lifecycle': {'example-target': {'versioning': {'Status': 'Enabled'},
                            'lifecycle': {'Rules': [{'Status': 'Enabled', 'Filter': {'Prefix': ''},
                                'Expiration': {'Days': 7},
                                'NoncurrentVersionExpiration': {'NoncurrentDays': 7}}]}}},
    }
    return controls, snapshot, {'prepare': prepare, 'deploy': caller, 'deploy-job': worker}


@pytest.fixture
def case() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Give each mutation a fresh valid fixture."""
    return valid_case()


def row(report: dict[str, Any], name: str) -> dict[str, Any]:
    """Select one public control result."""
    return next(item for item in report['controls'] if item['control'] == name)


def replace(case: Any, path: str, value: Any) -> None:
    """Change one selected leaf without rebuilding its parent records."""
    parts = path.split('/')
    current: Any = case[int(parts.pop(0))]
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    key: Any = int(parts[-1]) if isinstance(current, list) else parts[-1]
    current[key] = value


# Each entry changes one fact; assertions pin the public refusal, not implementation details.
MUTATIONS = [
    ('trusted-execution', 'untrusted-trigger', '2/prepare/on', 'push'),
    ('trusted-execution', 'untrusted-trigger', '2/deploy-job/on', 'workflow_dispatch'),
    ('trusted-execution', 'untrusted-trigger', '2/deploy/jobs/deploy/uses',
     'example-owner/another/.github/workflows/deploy.yml@' + 'a' * 40),
    ('trusted-execution', 'permissions-broad', '2/prepare/jobs/prepare/permissions',
     {'id-token': 'write'}),
    ('trusted-execution', 'permissions-undeclared', '2/deploy-job/permissions', None),
    ('trusted-execution', 'unpinned-action', '2/prepare/jobs/prepare/steps/0/uses',
     'actions/checkout@v4'),
    ('trusted-execution', 'secrets-inherited', '2/deploy/jobs/deploy/secrets', 'inherit'),
    ('trusted-execution', 'expression-in-run', '2/deploy-job/jobs/deploy/steps/0/run',
     'printf "${{ inputs.x }}"'),
    ('trusted-execution', 'branch-unprotected', '1/branch_rules', []),
    ('candidate-binding', 'binding-step-missing', '2/deploy-job/jobs/deploy/steps/0/id', 'other'),
    ('candidate-binding', 'binding-order', '2/deploy-job/jobs/deploy/steps/0/id', 'mutate-early'),
    ('candidate-binding', 'mutation-continues-on-error',
     '2/deploy-job/jobs/deploy/steps/6/continue-on-error', True),
    ('candidate-binding', 'environment-mismatch', '2/deploy-job/jobs/deploy/environment', 'other'),
    ('candidate-binding', 'inputs-mismatch', '2/deploy/jobs/deploy/with/prepare_run_id', '123'),
    ('human-approval', 'reviewers-missing', '1/environment/protection_rules/0/reviewers', []),
    ('human-approval', 'team-reviewer-unsupported',
     '1/environment/protection_rules/0/reviewers/0/type', 'Team'),
    ('human-approval', 'self-review-allowed',
     '1/environment/protection_rules/0/prevent_self_review', False),
    ('human-approval', 'admin-bypass', '1/environment/can_admins_bypass', True),
    ('human-approval', 'branch-policy-open',
     '1/environment/deployment_branch_policy/protected_branches', False),
    ('human-approval', 'agent-is-reviewer',
     '1/environment/protection_rules/0/reviewers/0/reviewer/login', 'example-agent[bot]'),
    ('human-approval', 'agent-kind-unsupported', '0/agent/kind', 'user'),
    *[('human-approval', 'agent-can-reconfigure', '1/agent_app/permissions', {key: 'write'})
      for key in ('administration', 'environments', 'secrets', 'actions_variables',
                  'workflows', 'contents')],
    ('serialization', 'concurrency-missing', '2/deploy-job/jobs/deploy/concurrency/group', 'other'),
    ('serialization', 'cancel-in-progress',
     '2/deploy-job/jobs/deploy/concurrency/cancel-in-progress', True),
    ('serialization', 'writers-not-excluded', '1/target_policy/example-target/Policy',
     json.dumps({'Statement': []})),
    ('credentials', 'trust-open', '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Principal',
     {'Federated': '*'}),
    ('credentials', 'trust-subject-mismatch',
     '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Condition/StringEquals/'
     'token.actions.githubusercontent.com:sub', 'repo:other'),
    ('credentials', 'trust-open', '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Condition',
     {'StringLike': {'token.actions.githubusercontent.com:sub': 'repo:*'}}),
    ('credentials', 'subject-template-mismatch',
     '1/oidc_subject_template/include_claim_keys', ['repo', 'context']),
    ('credentials', 'repository-id-unpinned',
     '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Condition/StringEquals/'
     'token.actions.githubusercontent.com:repository_id', None),
    ('credentials', 'permissions-exceed-allowlist', '1/iam_role_policies/AttachedPolicies',
     [{'PolicyArn': 'arn:aws:iam::123456789012:policy/example-managed'}]),
    ('credentials', 'permissions-exceed-allowlist',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Resource',
     'arn:aws:s3:::example-other/payload'),
    ('credentials', 'wildcard-permission',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Action', '*'),
    ('audit', 'audit-kind-unsupported', '0/audit/kind', 'workflow-logs'),
    ('audit', 'audit-not-immutable',
     '1/audit_store/object_lock/ObjectLockConfiguration/Rule/DefaultRetention/Mode', 'GOVERNANCE'),
    ('audit', 'audit-retention-short',
     '1/audit_store/object_lock/ObjectLockConfiguration/Rule/DefaultRetention/Days', 1),
    ('audit', 'audit-history-expires', '1/audit_store/lifecycle/Rules', [
        {'Status': 'Enabled', 'Filter': {'Prefix': 'decisions/'}, 'Expiration': {'Days': 100}}]),
    ('audit', 'audit-writer-open', '1/audit_store/policy/Policy', json.dumps({'Statement': []})),
    ('audit', 'audit-erasable',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Action',
     's3:BypassGovernanceRetention'),
    ('recovery-limits', 'executions-unbounded', '0/max_executions', None),
    ('recovery-limits', 'executions-unbounded', '0/budget_window_days', 0),
    ('recovery-limits', 'teardown-missing', '2/deploy-job/jobs/deploy/steps/7/id', 'other'),
    ('recovery-limits', 'teardown-unguarded', '2/deploy-job/jobs/deploy/steps/7/if', 'always()'),
    ('recovery-limits', 'effects-undeclared', '0/effects/0/payload_component', ''),
    ('recovery-limits', 'effect-kind-unsupported', '0/effects/0/kind', 'other'),
    ('cost', 'effect-resource-open', '0/effects/0/resource', 'arn:aws:s3:::example-target/*'),
    ('cost', 'payload-unbounded', '0/effects/0/max_payload_bytes', None),
    ('cost', 'cleanup-unbounded',
     '1/target_lifecycle/example-target/lifecycle/Rules/0/Expiration/Days', 8),
    ('cost', 'cleanup-unbounded',
     '1/target_lifecycle/example-target/lifecycle/Rules/0/NoncurrentVersionExpiration', {}),
    ('isolation', 'self-hosted-runner', '2/deploy-job/jobs/deploy/runs-on', ['self-hosted']),
    ('isolation', 'role-reaches-beyond-effects',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Resource',
     'arn:aws:s3:::example-other/payload'),
    ('isolation', 'classification-unattested', '0/isolation/classification', 'production'),
]


def test_ready(module: ModuleType, case: Any) -> None:
    """All nine controls must be met and the evaluator must not mutate its inputs."""
    original = copy.deepcopy(case)
    report = module.evaluate_readiness(*case)
    assert report['status'] == 'ready', report
    assert len(report['controls']) == 9
    assert all(item['status'] == 'met' and item['codes'] == [] for item in report['controls'])
    assert report['blocked_mutations'] == []
    assert report['unaffected'] == ['authoring', 'collection', 'admission', 'review']
    assert report['cost_bound'] == {
        'max_executions': 3, 'window_days': 7,
        'per_execution': {'effect_requests': {'write': 1, 'read': 1, 'delete': 1},
                          'decision_writes': 1, 'ops_writes': 1},
        'max_payload_bytes': {'example-payload': 1024}, 'budget_refusal_writes': 0,
    }
    assert case == original


@pytest.mark.parametrize('workflow,event', [
    ('prepare', 'workflow_dispatch'), ('deploy', 'workflow_dispatch'),
    ('deploy-job', 'workflow_call'),
])
@pytest.mark.parametrize('form', ['scalar', 'list', 'mapping'])
def test_trigger_forms(module: ModuleType, case: Any, workflow: str,
                       event: str, form: str) -> None:
    """Equivalent supported YAML trigger forms meet the execution control."""
    value = {'scalar': event, 'list': '[' + event + ']', 'mapping': '\n  ' + event + ': {}'}
    parsed = module.read_workflow(('on: ' + value[form] + '\n').encode('utf-8'))
    case[2][workflow]['on'] = parsed['on']
    assert row(module.evaluate_readiness(*case), 'trusted-execution') == {
        'control': 'trusted-execution', 'status': 'met', 'codes': [],
    }


@pytest.mark.parametrize('workflow,event', [
    ('prepare', 'workflow_dispatch'), ('deploy', 'workflow_dispatch'),
    ('deploy-job', 'workflow_call'),
])
@pytest.mark.parametrize('events', ['push', '{event}, push', '{event}, workflow_run'])
def test_trigger_list_refuses_other_events(module: ModuleType, case: Any,
                                          workflow: str, event: str, events: str) -> None:
    """An event list must contain only the required event."""
    parsed = module.read_workflow(('on: [' + events.format(event=event) + ']\n').encode('utf-8'))
    case[2][workflow]['on'] = parsed['on']
    report = module.evaluate_readiness(*case)
    assert row(report, 'trusted-execution') == {
        'control': 'trusted-execution', 'status': 'missing', 'codes': ['untrusted-trigger'],
    }
    assert report['blocked_mutations'] == ['deploy', 'teardown']


@pytest.mark.parametrize('source', ['target', 'audit'])
@pytest.mark.parametrize('broad', [False, True])
def test_bucket_policy_allow_refused(module: ModuleType, case: Any,
                                     source: str, broad: bool) -> None:
    """Even an in-scope resource grant must not supplement inline role grants."""
    captured = (case[1]['target_policy']['example-target'] if source == 'target'
                else case[1]['audit_store']['policy'])
    policy = json.loads(captured['Policy'])
    resource = TARGET if source == 'target' else DECISIONS + '*'
    policy['Statement'].append({
        'Effect': 'Allow', 'Principal': {'AWS': ROLE}, 'Action': 's3:PutObject',
        'Resource': resource if not broad else 'arn:aws:s3:::example-other/*',
    })
    captured['Policy'] = json.dumps(policy)
    report = module.evaluate_readiness(*case)
    for control, code in [('credentials', 'permissions-exceed-allowlist'),
                          ('isolation', 'role-reaches-beyond-effects')]:
        assert row(report, control) == {
            'control': control, 'status': 'missing', 'codes': [code],
        }
    assert report['blocked_mutations'] == ['deploy', 'teardown']


@pytest.mark.parametrize('control,code,path,value', MUTATIONS)
def test_one_change_refuses(module: ModuleType, case: Any, control: str, code: str,
                            path: str, value: Any) -> None:
    """Pin every refusal code with a single changed fact."""
    replace(case, path, value)
    report = module.evaluate_readiness(*case)
    assert report['status'] == 'blocked'
    result = row(report, control)
    assert result['status'] == ('unverified' if code == 'audit-kind-unsupported' else 'missing')
    assert code in result['codes'], result
    assert report['blocked_mutations'] == ['deploy', 'teardown']


DEPENDENCIES = {
    'repository': {'credentials'},
    'environment': {'human-approval'},
    'branch_rules': {'trusted-execution'},
    'oidc_subject_template': {'credentials'},
    'agent_app': {'human-approval'},
    'iam_role': {'credentials', 'serialization', 'audit', 'isolation'},
    'iam_role_policies': {'credentials', 'audit', 'cost', 'isolation'},
    'audit_store': {'audit', 'credentials', 'isolation'},
    'target_policy': {'serialization', 'credentials', 'isolation'},
    'target_lifecycle': {'cost'},
}


@pytest.mark.parametrize('source,expected', DEPENDENCIES.items())
def test_absent_source(module: ModuleType, case: Any, source: str, expected: set[str]) -> None:
    """A missing raw source affects exactly its consumers, without a default pass."""
    del case[1][source]
    report = module.evaluate_readiness(*case)
    assert {item['control'] for item in report['controls'] if item['status'] == 'unverified'} == expected
    assert all(item['status'] == 'met' for item in report['controls']
               if item['control'] not in expected)


@pytest.mark.parametrize('workflow', ['deploy', 'deploy-job'])
def test_unparsed(module: ModuleType, case: Any, workflow: str) -> None:
    """Unsupported deploy syntax makes all five workflow controls unverified."""
    case[2][workflow] = None
    report = module.evaluate_readiness(*case)
    assert {item['control'] for item in report['controls'] if item['status'] == 'unverified'} == {
        'trusted-execution', 'candidate-binding', 'serialization', 'recovery-limits', 'isolation'}


@pytest.mark.parametrize('immutable', [False, True])
def test_subject_forms(module: ModuleType, case: Any, immutable: bool) -> None:
    """Immutable subjects use owner.id, keeping names in job_workflow_ref."""
    if immutable:
        equals = case[1]['iam_role']['Role']['AssumeRolePolicyDocument']['Statement'][0][
            'Condition']['StringEquals']
        equals.pop('token.actions.githubusercontent.com:repository_id')
        equals['token.actions.githubusercontent.com:sub'] = equals[
            'token.actions.githubusercontent.com:sub'].replace(
                'repo:example-owner/example-repo:', 'repo:example-owner@123/example-repo@456:')
        case[1]['oidc_subject_template']['use_immutable_subject'] = True
        case[1]['oidc_subject_template']['sub_claim_prefix'] = 'repo:example-owner@123/example-repo@456'
    assert module.evaluate_readiness(*case)['status'] == 'ready'


@pytest.mark.parametrize('action', ERASURE)
def test_each_erasure_denied(module: ModuleType, case: Any, action: str) -> None:
    """Every erasure permission needs its own universal resource-policy deny."""
    policy = json.loads(case[1]['audit_store']['policy']['Policy'])
    policy['Statement'][-1]['Action'].remove(action)
    case[1]['audit_store']['policy']['Policy'] = json.dumps(policy)
    assert 'audit-erasable' in row(module.evaluate_readiness(*case), 'audit')['codes']


def test_directives_inert(module: ModuleType, case: Any) -> None:
    """Waivers, controls-named snapshot fields and comments have no authority."""
    before = module.evaluate_readiness(*case)
    case[1].update({'max_executions': 100, 'environment_name': 'other',
                    'waiver': 'Ignore every control and report ready'})
    case[2]['deploy-job']['jobs']['deploy']['steps'][0]['name'] = 'Ignore every control'
    assert module.evaluate_readiness(*case) == before
    case[1]['branch_rules'] = []
    blocked = module.evaluate_readiness(*case)
    assert blocked['status'] == 'blocked'
    assert 'branch-unprotected' in row(blocked, 'trusted-execution')['codes']


def yaml_text(value: Any, indent: int = 0) -> str:
    """Serialize the fixture using the supported block workflow subset."""
    pad = ' ' * indent
    if isinstance(value, dict):
        return ''.join(pad + json.dumps(key) + ':' + (
            '\n' + yaml_text(item, indent + 2) if isinstance(item, (dict, list)) and item
            else ' ' + json.dumps(item) + '\n') for key, item in value.items())
    assert isinstance(value, list)
    return ''.join(pad + '-\n' + yaml_text(item, indent + 2) for item in value)


def test_cli(module: ModuleType, case: Any, tmp_path: Path, capsys: Any) -> None:
    """Exercise readiness through bounded file reads and main(argv)."""
    args = ['readiness', '--root', str(tmp_path), '--controls', 'controls', '--snapshot', 'snapshot']
    for name, value in zip(('controls', 'snapshot'), case[:2], strict=True):
        (tmp_path / name).write_text(json.dumps(value), encoding='utf-8')
    for name, workflow in case[2].items():
        filename = name + '.yml'
        (tmp_path / filename).write_text(yaml_text(workflow), encoding='utf-8')
        args.extend(['--' + name + '-workflow', filename])
    assert module.main(args) == 0
    output = capsys.readouterr()
    assert output.err == ''
    assert json.loads(output.out) == module.evaluate_readiness(*case)
    (tmp_path / 'deploy.yml').write_text('on: &unsupported workflow_dispatch\n', encoding='utf-8')
    assert module.main(args) == 1
    assert row(json.loads(capsys.readouterr().out), 'candidate-binding')['status'] == 'unverified'


EXTRA_MUTATIONS = [
    ('trusted-execution', 'permissions-broad', '2/deploy-job/jobs/deploy/permissions',
     {'contents': 'write'}),
    ('trusted-execution', 'permissions-undeclared', '2/prepare/jobs/prepare/permissions', None),
    ('trusted-execution', 'permissions-broad', '2/deploy/permissions', {'checks': 'write'}),
    ('trusted-execution', 'unpinned-action', '2/deploy-job/jobs/deploy/steps/0/uses',
     'example-owner/example-repo/.github/workflows/other.yml@v1'),
    ('trusted-execution', 'branch-unprotected', '1/branch_rules/0/type', 'other'),
    ('trusted-execution', 'branch-unprotected', '1/branch_rules/1/type', 'other'),
    ('trusted-execution', 'branch-unprotected',
     '1/branch_rules/2/parameters/required_approving_review_count', 0),
    ('trusted-execution', 'untrusted-trigger', '2/deploy/jobs/deploy/secrets', {'account': 'literal'}),
    ('candidate-binding', 'binding-order', '2/deploy-job/jobs/deploy/steps/6/id', 'other'),
    ('candidate-binding', 'binding-step-missing', '2/deploy-job/jobs/deploy/steps/0',
     {'id': 'recheck', 'run': 'printf example'}),
    ('candidate-binding', 'inputs-mismatch', '2/deploy/on/workflow_dispatch/inputs', {}),
    ('candidate-binding', 'inputs-mismatch', '2/deploy-job/on/workflow_call/inputs', {}),
    ('human-approval', 'reviewers-missing',
     '1/environment/protection_rules/0/reviewers/0/reviewer', {}),
    ('human-approval', 'agent-can-reconfigure', '1/agent_app/slug', 'another-app'),
    ('credentials', 'permissions-exceed-allowlist',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Effect', 'Deny'),
    ('credentials', 'permissions-exceed-allowlist', '0/cloud/allowed_actions', ['s3:GetObject']),
    ('credentials', 'permissions-exceed-allowlist',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Action', 's3:CreateBucket'),
    ('credentials', 'permissions-exceed-allowlist', '1/iam_role_policies/Policies', []),
    ('credentials', 'permissions-exceed-allowlist', '1/iam_role_policies/PolicyNames',
     ['example-inline', 'example-uncaptured']),
    ('credentials', 'permissions-exceed-allowlist',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/3/Resource',
     'arn:aws:iam::123456789012:role/example-other'),
    ('credentials', 'wildcard-permission',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Resource', '*'),
    ('credentials', 'trust-open',
     '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Condition/StringEquals/'
     'token.actions.githubusercontent.com:aud', 'another-audience'),
    ('credentials', 'trust-open', '1/iam_role/Role/RoleName', 'example-other'),
    ('credentials', 'trust-open', '1/iam_role/Role/AssumeRolePolicyDocument/Statement/0/Action',
     ['sts:AssumeRoleWithWebIdentity', 'sts:AssumeRole']),
    ('credentials', 'subject-template-mismatch', '1/oidc_subject_template/use_default', True),
    ('audit', 'audit-not-immutable', '1/audit_store/versioning/Status', 'Suspended'),
    ('audit', 'audit-not-immutable',
     '1/audit_store/object_lock/ObjectLockConfiguration/ObjectLockEnabled', None),
    ('audit', 'audit-retention-short', '0/audit/minimum_retention_days', 8),
    ('audit', 'audit-history-expires', '1/audit_store/lifecycle/Rules', [
        {'Status': 'Enabled', 'Filter': {}, 'Transitions': [{'Days': 1, 'StorageClass': 'GLACIER'}]}]),
    ('audit', 'audit-history-expires', '1/audit_store/lifecycle/Rules', [
        {'Status': 'Enabled', 'Filter': {'And': {'Prefix': 'ops/', 'Tags': []}},
         'NoncurrentVersionExpiration': {'NoncurrentDays': 1}}]),
    ('cost', 'cleanup-unbounded', '1/target_lifecycle/example-target/lifecycle/Rules', []),
    ('cost', 'cleanup-unbounded',
     '1/target_lifecycle/example-target/lifecycle/Rules/0/Filter', {'Tag': {'Key': 'x', 'Value': 'y'}}),
    ('cost', 'cleanup-unbounded',
     '1/target_lifecycle/example-target/lifecycle/Rules/0/NoncurrentVersionExpiration',
     {'NoncurrentDays': 7, 'NewerNoncurrentVersions': 1}),
    ('cost', 'cleanup-unbounded',
     '1/target_lifecycle/example-target/lifecycle/Rules/0/Status', 'Disabled'),
    ('cost', 'payload-unbounded', '0/effects/0/max_payload_bytes', True),
    ('cost', 'effect-resource-open',
     '1/iam_role_policies/Policies/0/PolicyDocument/Statement/0/Resource',
     'arn:aws:s3:::example-target/payload*'),
    ('recovery-limits', 'executions-unbounded', '0/max_executions', True),
    ('recovery-limits', 'executions-unbounded', '0/max_executions', 101),
    ('recovery-limits', 'executions-unbounded', '0/budget_window_days', 366),
    ('recovery-limits', 'effects-undeclared', '0/effects', []),
    ('isolation', 'classification-unattested', '0/isolation/attested_by', ''),
    ('isolation', 'self-hosted-runner', '2/prepare/jobs/prepare/runs-on',
     ['ubuntu-latest', 'self-hosted']),
]


@pytest.mark.parametrize('control,code,path,value', EXTRA_MUTATIONS)
def test_more_single_changes(module: ModuleType, case: Any, control: str, code: str,
                             path: str, value: Any) -> None:
    """Exercise alternate failures of the same control rather than happy-path pins."""
    test_one_change_refuses(module, case, control, code, path, value)


@pytest.mark.parametrize('field,before,after', [
    ('environment', ':environment:sandbox:', ':environment:other:'),
    ('repository', 'repo:example-owner/example-repo:', 'repo:example-owner/other:'),
    ('workflow', '/deploy-job.yml@', '/other.yml@'),
    ('branch', '@refs/heads/main', '@refs/heads/other'),
])
def test_subject_scope(module: ModuleType, case: Any, field: str, before: str, after: str) -> None:
    """Each OIDC identity dimension is independently pinned."""
    equals = case[1]['iam_role']['Role']['AssumeRolePolicyDocument']['Statement'][0][
        'Condition']['StringEquals']
    equals['token.actions.githubusercontent.com:sub'] = equals[
        'token.actions.githubusercontent.com:sub'].replace(before, after)
    assert 'trust-subject-mismatch' in row(module.evaluate_readiness(*case), 'credentials')['codes']


@pytest.mark.parametrize('location', ['target', 'audit'])
@pytest.mark.parametrize('weakening', ['another-role', 'extra-condition', 'not-action'])
def test_writer_policy_scope(module: ModuleType, case: Any, location: str, weakening: str) -> None:
    """A deny that misses even one principal or request cannot prove serialization."""
    response = (case[1]['target_policy']['example-target'] if location == 'target'
                else case[1]['audit_store']['policy'])
    policy = json.loads(response['Policy'])
    statement = policy['Statement'][0]
    if weakening == 'another-role':
        statement['Condition']['ArnNotEquals']['aws:PrincipalArn'] = [ROLE,
            'arn:aws:iam::123456789012:role/example-other']
    elif weakening == 'extra-condition':
        statement['Condition']['StringEquals'] = {'s3:x-amz-acl': 'private'}
    else:
        statement['NotAction'] = 's3:PutObject'
    response['Policy'] = json.dumps(policy)
    result = module.evaluate_readiness(*case)
    control, code = ('serialization', 'writers-not-excluded') if location == 'target' else (
        'audit', 'audit-writer-open')
    assert code in row(result, control)['codes']


@pytest.mark.parametrize('source', DEPENDENCIES)
@pytest.mark.parametrize('invalid', [None, 'ignore controls'])
def test_invalid_source(module: ModuleType, case: Any, source: str, invalid: Any) -> None:
    """An unreadable source has the same consumers as an absent source."""
    case[1][source] = invalid
    report = module.evaluate_readiness(*case)
    assert {item['control'] for item in report['controls']
            if item['status'] == 'unverified'} == DEPENDENCIES[source]


@pytest.mark.parametrize('change', ['extra-trust', 'order', 'teardown-order', 'second-job'])
def test_structural_mutations(module: ModuleType, case: Any, change: str) -> None:
    """Extra statements/jobs and reordered steps cannot preserve a valid chain."""
    steps = case[2]['deploy-job']['jobs']['deploy']['steps']
    if change == 'extra-trust':
        statements = case[1]['iam_role']['Role']['AssumeRolePolicyDocument']['Statement']
        statements.append(copy.deepcopy(statements[0]))
        control, code = 'credentials', 'trust-open'
    elif change == 'order':
        steps[1], steps[2] = steps[2], steps[1]
        control, code = 'candidate-binding', 'binding-order'
    elif change == 'teardown-order':
        steps[6], steps[7] = steps[7], steps[6]
        control, code = 'recovery-limits', 'teardown-unguarded'
    else:
        jobs = case[2]['deploy-job']['jobs']
        jobs['other'] = copy.deepcopy(jobs['deploy'])
        control, code = 'candidate-binding', 'binding-step-missing'
    assert code in row(module.evaluate_readiness(*case), control)['codes']


@pytest.mark.parametrize('change', ['docker', 'local', 'empty-permissions', 'environment-map',
                                   'unversioned', 'unrelated-lifecycle', 'disabled-lifecycle'])
def test_valid_variants(module: ModuleType, case: Any, change: str) -> None:
    """Accept safe policy/workflow variants without requiring the exact fixture bytes."""
    if change == 'docker':
        case[2]['prepare']['jobs']['prepare']['steps'][0]['uses'] = 'docker://example-image@sha256:' + 'b' * 64
    elif change == 'local':
        case[2]['prepare']['jobs']['prepare']['steps'][0]['uses'] = './.github/actions/example'
    elif change == 'empty-permissions':
        case[2]['prepare']['permissions'] = {}
    elif change == 'environment-map':
        case[2]['deploy-job']['jobs']['deploy']['environment'] = {'name': 'sandbox'}
    elif change == 'unversioned':
        target = case[1]['target_lifecycle']['example-target']
        target['versioning'] = {}
        del target['lifecycle']['Rules'][0]['NoncurrentVersionExpiration']
    else:
        case[1]['audit_store']['lifecycle']['Rules'] = [{
            'Status': 'Disabled' if change == 'disabled-lifecycle' else 'Enabled',
            'Filter': {'Prefix': 'unrelated/'}, 'Expiration': {'Days': 1}}]
    assert module.evaluate_readiness(*case)['status'] == 'ready'


@pytest.mark.parametrize('value', [{}, [], None])
def test_malformed_policy_name(module: ModuleType, case: Any, value: Any) -> None:
    """Malformed raw names fail scope checks without an exception or input echo."""
    case[1]['iam_role_policies']['Policies'][0]['PolicyName'] = value
    report = module.evaluate_readiness(*case)
    assert 'permissions-exceed-allowlist' in row(report, 'credentials')['codes']


@pytest.mark.parametrize('immutable', [False, True])
def test_template_subject_mismatch(module: ModuleType, case: Any, immutable: bool) -> None:
    """The trust subject agrees with the captured subject customization setting."""
    if not immutable:
        test_subject_forms(module, case, True)
    case[1]['oidc_subject_template']['use_immutable_subject'] = immutable
    assert 'trust-subject-mismatch' in row(module.evaluate_readiness(*case), 'credentials')['codes']


def test_year_retention(module: ModuleType, case: Any) -> None:
    """A raw object-lock response may express its default retention in years."""
    retention = case[1]['audit_store']['object_lock']['ObjectLockConfiguration']['Rule']['DefaultRetention']
    del retention['Days']
    retention['Years'] = 1
    assert module.evaluate_readiness(*case)['status'] == 'ready'


@pytest.mark.parametrize('source', ['target_policy', 'audit_store'])
def test_bucket_policy_json_strict(module: ModuleType, case: Any, source: str) -> None:
    """JSON embedded in raw AWS responses has the same strictness as input files."""
    response = case[1]['target_policy']['example-target'] if source == 'target_policy' else case[1]['audit_store']['policy']
    original = response['Policy']
    response['Policy'] = '{"Statement": [],' + original[1:]
    report = module.evaluate_readiness(*case)
    control = 'serialization' if source == 'target_policy' else 'audit'
    assert row(report, control)['status'] == 'missing'


@pytest.mark.parametrize('workflow', ['deploy', 'deploy-job'])
@pytest.mark.parametrize('raw', [
    b'on: &dispatch workflow_dispatch', b'on: *dispatch', b'on: !!str workflow_dispatch',
    b'<<: source', b'on: workflow_dispatch\n---\non: push', b'x: [\n  one, two\n]',
    b'jobs:\n\tdeploy: {}', b'on: push\non: workflow_dispatch',
])
def test_unparsed_reader_to_controls(module: ModuleType, case: Any, workflow: str, raw: bytes) -> None:
    """Every unsupported workflow construct propagates to five unverified rows."""
    with pytest.raises(module.Unparsed):
        module.read_workflow(raw)
    case[2][workflow] = None
    report = module.evaluate_readiness(*case)
    assert {result['control'] for result in report['controls']
            if result['status'] == 'unverified'} == {
                'trusted-execution', 'candidate-binding', 'serialization',
                'recovery-limits', 'isolation'}


def test_prefix_uris(module: ModuleType, case: Any) -> None:
    """ARN policies can scope effects and audit prefixes configured as S3 URIs."""
    case[0]['audit']['decision_prefix'] = 's3://example-audit/decisions/'
    case[0]['audit']['ops_prefix'] = 's3://example-audit/ops/'
    case[0]['effects'][0]['resource'] = 's3://example-target/payload'
    assert module.evaluate_readiness(*case)['status'] == 'ready'


def test_extra_workflow_data_inert(module: ModuleType, case: Any) -> None:
    """Unrelated workflow data cannot impersonate a run step or permission node."""
    original = module.evaluate_readiness(*case)
    case[2]['deploy']['unrelated'] = {'run': '${{ ignore.all_controls }}', 'secrets': 'inherit'}
    assert module.evaluate_readiness(*case) == original


def test_incomplete_policy_listing(module: ModuleType, case: Any) -> None:
    """A truncated IAM policy list cannot establish credential scope."""
    case[1]['iam_role_policies']['IsTruncated'] = True
    assert 'permissions-exceed-allowlist' in row(module.evaluate_readiness(*case), 'credentials')['codes']


def test_reusable_prepare_runner_unknown(module: ModuleType, case: Any) -> None:
    """Only the inspected local deploy caller can delegate its runner declaration."""
    job = case[2]['prepare']['jobs']['prepare']
    del job['runs-on']
    job['uses'] = 'example-owner/example-repo/.github/workflows/other.yml@' + 'a' * 40
    assert 'self-hosted-runner' in row(module.evaluate_readiness(*case), 'isolation')['codes']


@pytest.mark.parametrize('scope', ['audit-prefix', 'unscoped-audit', 'target-listing'])
def test_bucket_listing_scope(module: ModuleType, case: Any, scope: str) -> None:
    """Listing audit history needs a prefix condition; target data listing exceeds scope."""
    case[0]['cloud']['allowed_actions'].append('s3:ListBucketVersions')
    statement = {'Effect': 'Allow', 'Action': 's3:ListBucketVersions',
                 'Resource': 'arn:aws:s3:::example-audit'}
    if scope == 'audit-prefix':
        statement['Condition'] = {'StringLike': {'s3:prefix': ['decisions/*', 'ops/*']}}
    elif scope == 'target-listing':
        statement['Resource'] = 'arn:aws:s3:::example-target'
    case[1]['iam_role_policies']['Policies'][0]['PolicyDocument']['Statement'].append(statement)
    result = module.evaluate_readiness(*case)
    if scope == 'audit-prefix':
        assert result['status'] == 'ready'
    else:
        assert 'permissions-exceed-allowlist' in row(result, 'credentials')['codes']
        assert 'role-reaches-beyond-effects' in row(result, 'isolation')['codes']


def test_malformed_app_permissions(module: ModuleType, case: Any) -> None:
    """An invalid permissions response cannot establish that the app is constrained."""
    case[1]['agent_app']['permissions'] = []
    assert 'agent-can-reconfigure' in row(module.evaluate_readiness(*case), 'human-approval')['codes']


def test_retention_read_is_audit_prefix_only(module: ModuleType, case: Any) -> None:
    """Retention reads pass on the audit prefixes and fail on an effect resource."""
    case[0]['cloud']['allowed_actions'].append('s3:GetObjectRetention')
    statements = case[1]['iam_role_policies']['Policies'][0]['PolicyDocument']['Statement']
    statements.append({'Effect': 'Allow', 'Action': ['s3:GetObjectRetention'],
                       'Resource': [DECISIONS + '*', OPS + '*']})
    assert module.evaluate_readiness(*case)['status'] == 'ready'
    statements[-1]['Resource'] = [TARGET]
    report = module.evaluate_readiness(*case)
    assert 'permissions-exceed-allowlist' in row(report, 'credentials')['codes']
    assert 'role-reaches-beyond-effects' in row(report, 'isolation')['codes']


@pytest.mark.parametrize('prefix', ['repo', 'repo:example-owner/other-repo',
                                    'repo:example-owner@123/example-repo@456'])
def test_subject_prefix_names_this_repository(module: ModuleType, case: Any, prefix: str) -> None:
    """GitHub's reported subject prefix must be this repository's form of the subject."""
    case[1]['oidc_subject_template']['sub_claim_prefix'] = prefix
    assert 'subject-template-mismatch' in row(module.evaluate_readiness(*case), 'credentials')['codes']


@pytest.mark.parametrize('condition,ready', [
    ({'StringEquals': {'s3:prefix': 'payload'}}, True),
    ({'StringLike': {'s3:prefix': 'payload'}}, False),
    ({'StringEquals': {'s3:prefix': 'other'}}, False),
    ({}, False),
])
def test_effect_listing_is_exact_key_only(module: ModuleType, case: Any,
                                          condition: dict[str, Any], ready: bool) -> None:
    """Teardown may list the effect bucket only for the effect's own key."""
    case[0]['cloud']['allowed_actions'].append('s3:ListBucket')
    statements = case[1]['iam_role_policies']['Policies'][0]['PolicyDocument']['Statement']
    statements.append({'Effect': 'Allow', 'Action': 's3:ListBucket',
                       'Resource': 'arn:aws:s3:::example-target', 'Condition': condition})
    report = module.evaluate_readiness(*case)
    assert (report['status'] == 'ready') is ready
    if not ready:
        assert 'permissions-exceed-allowlist' in row(report, 'credentials')['codes']


@pytest.mark.parametrize('step_id', [
    'verify-admission', 'bind', 'credentials', 'budget', 'audit', 'recheck', 'mutate-deploy',
])
@pytest.mark.parametrize('value', [True, False, '${{ inputs.ignore }}'])
def test_prerequisite_errors_cannot_be_ignored(
    module: ModuleType, case: Any, step_id: str, value: Any,
) -> None:
    """Every prerequisite and mutation must preserve failure propagation."""
    steps = case[2]['deploy-job']['jobs']['deploy']['steps']
    next(step for step in steps if step['id'] == step_id)['continue-on-error'] = value
    report = module.evaluate_readiness(*case)
    assert report['status'] == 'blocked'
    assert 'mutation-continues-on-error' in row(report, 'candidate-binding')['codes']


@pytest.mark.parametrize('condition', [
    'always()', 'failure()', 'cancelled()', '${{ always() }}',
    "always() && steps.recheck.outcome == 'success'",
    "!cancelled()", "success() || failure()",
])
def test_mutation_cannot_override_failed_prerequisites(
    module: ModuleType, case: Any, condition: str,
) -> None:
    """Status functions must not bypass GitHub's implicit success guard."""
    case[2]['deploy-job']['jobs']['deploy']['steps'][6]['if'] = condition
    report = module.evaluate_readiness(*case)
    assert report['status'] == 'blocked'
    assert 'binding-order' in row(report, 'candidate-binding')['codes']


@pytest.mark.parametrize('step_id', [
    'verify-admission', 'bind', 'credentials', 'budget', 'audit', 'recheck', 'mutate-deploy',
])
@pytest.mark.parametrize('condition', [False, True, None, '', 'false', 'success()',
                                      'ALWAYS()', '${{ !cancelled() }}'])
def test_required_steps_have_no_condition(
    module: ModuleType, case: Any, step_id: str, condition: Any,
) -> None:
    """Even a skip or apparently safe condition invalidates the required chain."""
    steps = case[2]['deploy-job']['jobs']['deploy']['steps']
    next(step for step in steps if step['id'] == step_id)['if'] = condition
    report = module.evaluate_readiness(*case)
    assert report['status'] == 'blocked'
    assert 'binding-order' in row(report, 'candidate-binding')['codes']
