#!/usr/bin/env python3
"""Check captured GitHub release inputs without granting execution authority."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from pathlib import Path
from types import ModuleType
from typing import Any


def load_admission() -> ModuleType:
    """Reuse sibling input guards without changing Python's import search path."""
    path = Path(__file__).resolve().with_name('release_admission.py')
    spec = importlib.util.spec_from_file_location(
        'release_engineering_release_loop_github_admission', path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('admission unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


admission = load_admission()
handoff = admission.handoff
Refusal = admission.Refusal
MANIFEST_LIMIT = handoff.MANIFEST_LIMIT
ARCHIVE_LIMIT = handoff.EVIDENCE_LIMIT

# Raw service responses stay open; owner controls and internal records do not.
CLOSED_FIELDS = {
    'controls': {
        'repository', 'repository_id', 'environment', 'release_branch', 'prepare_workflow',
        'deploy_workflow', 'deploy_job_workflow', 'agent', 'concurrency_group',
        'max_executions', 'budget_window_days', 'reconciled_runs', 'audit', 'cloud',
        'effects', 'isolation',
    },
    'binding': {
        'admission_sha256', 'candidate_sha256', 'target', 'repository', 'repository_id',
        'workflow_ref', 'workflow_sha', 'run_id', 'run_attempt', 'triggering_actor',
        'prepare_run_id', 'artifact_digest', 'approvals', 'approvals_response_sha256',
        'bound_at', 'marker', 'effects',
    },
    'decision': {'binding_sha256', 'binding', 'approvals_response', 'attempt_response'},
    'audit-receipt': {'Key', 'VersionId', 'ChecksumSHA256', 'ETag'},
    'ops': {'run_id', 'run_attempt', 'outcome', 'operations'},
}
INPUTS = {
    'readiness': ('controls', 'snapshot', 'deploy-workflow', 'deploy-job-workflow',
                  'prepare-workflow'),
    'bind': ('admission', 'controls', 'context', 'attempt', 'approvals', 'environment-settings',
             'prepare-run', 'prepare-artifacts', 'artifact-archive'),
    'budget': ('controls', 'listing'),
    'recheck': ('binding', 'decision', 'admission', 'controls', 'audit-receipt', 'audit-head',
                'audit-listing', 'live-snapshot', 'cloud-identity'),
    'reconcile': ('binding', 'controls', 'run', 'jobs', 'observed', 'audit-listing'),
    'summary': ('binding', 'decision', 'audit-receipt', 'audit-readback', 'audit-head',
                'observed', 'ops'),
}


class Unparsed(Exception):
    """Report unsupported workflow syntax without including its content."""

    def __init__(self) -> None:
        super().__init__('unparsed')


def closed(value: Any, names: set[str]) -> dict[str, Any]:
    """Reject unknown fields; command-specific validators require field values."""
    if not isinstance(value, dict) or not set(value) <= names:
        raise Refusal('unreadable-input', 'error')
    return value


def check_shape(value: Any, kind: str) -> None:
    """Check the closed portions of local records, leaving API responses inert."""
    if kind in CLOSED_FIELDS:
        closed(value, CLOSED_FIELDS[kind])
    if kind == 'controls':
        for name, names in {
            'agent': {'kind', 'slug', 'login'},
            'audit': {'kind', 'minimum_retention_days', 'decision_prefix', 'ops_prefix'},
            'cloud': {'provider', 'account_label', 'account_secret', 'role_secret',
                      'role_name', 'audience', 'allowed_actions'},
            'isolation': {'attested_by', 'classification'},
        }.items():
            if name in value:
                closed(value[name], names)
        if 'effects' in value:
            if not isinstance(value['effects'], list):
                raise Refusal('unreadable-input', 'error')
            for effect in value['effects']:
                closed(effect, {
                    'id', 'kind', 'resource', 'payload_component', 'max_payload_bytes',
                })
    elif kind == 'ops' and 'operations' in value:
        if not isinstance(value['operations'], list):
            raise Refusal('unreadable-input', 'error')
        for operation in value['operations']:
            closed(operation, {'effect_id', 'request_id', 'version_id'})
    elif kind == 'binding':
        if 'effects' in value:
            if not isinstance(value['effects'], list):
                raise Refusal('unreadable-input', 'error')
            for effect in value['effects']:
                closed(effect, {'id', 'payload_sha256'})
        if 'target' in value:
            closed(value['target'], {'environment', 'account'})
        if 'approvals' in value:
            if not isinstance(value['approvals'], list):
                raise Refusal('unreadable-input', 'error')
            for reviewer in value['approvals']:
                closed(reviewer, {'login', 'id', 'comment_sha256'})
    elif kind == 'decision' and 'binding' in value:
        check_shape(value['binding'], 'binding')
    elif kind == 'observed':
        if not isinstance(value, list):
            raise Refusal('unreadable-input', 'error')
        for effect in value:
            closed(effect, {'id', 'state', 'digest', 'marker', 'write_time', 'operation_id'})


def read_json(root: Path, locator: str, kind: str = '') -> Any:
    """Read one bounded strict JSON document without echoing supplied bytes."""
    try:
        value = handoff.parse_json(admission.read_manifest(root, locator))
        check_shape(value, kind)
        return value
    except Refusal:
        raise Refusal('unreadable-input', 'error') from None


def hash_archive(root: Path, locator: str) -> str:
    """Stream an archive's exact bytes for its digest; never open its members."""
    try:
        return admission.hash_evidence(root, locator)
    except Refusal:
        raise Refusal('unreadable-input', 'error') from None


def _line(text: str) -> tuple[str, int | None]:
    """Locate a block mapping separator and strip comments outside quotes."""
    quote = ''
    boundary = True
    separator = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            if char == '\\' and quote == '"':
                index += 2
                continue
            if char == quote:
                if quote == "'" and text[index:index + 2] == "''":
                    index += 2
                    continue
                quote = ''
        elif char in "\"'" and boundary:
            quote = char
            boundary = False
        elif char == '#' and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip(), separator
        elif char == ':' and (index + 1 == len(text) or text[index + 1].isspace()):
            if separator is None:
                separator = index
            boundary = True
        elif char in '[,':
            boundary = True
        elif boundary and not char.isspace():
            boundary = char == '-' and (index + 1 == len(text) or text[index + 1].isspace())
        index += 1
    if quote:
        raise Unparsed()
    return text.rstrip(), separator


def _flow(text: str) -> list[Any]:
    """Read one single-line flow sequence containing only scalars."""
    if not text.endswith(']'):
        raise Unparsed()
    inner = text[1:-1]
    if not inner.strip():
        return []
    parts = []
    start = 0
    quote = ''
    index = 0
    while index < len(inner):
        char = inner[index]
        if quote:
            if char == '\\' and quote == '"':
                index += 2
                continue
            if char == quote:
                if quote == "'" and inner[index:index + 2] == "''":
                    index += 2
                    continue
                quote = ''
        elif char in "\"'" and not inner[start:index].strip():
            quote = char
        elif char == ',':
            parts.append(inner[start:index].strip())
            start = index + 1
        index += 1
    if quote:
        raise Unparsed()
    last = inner[start:].strip()
    if last:
        parts.append(last)
    if any(not part for part in parts):
        raise Unparsed()
    result = [_scalar(part, flow=True) for part in parts]
    if len(result) > 1000:
        raise Unparsed()
    return result


def _double_quoted(text: str) -> str:
    """Decode YAML's single-line quoted escapes without evaluating any text."""
    if len(text) < 2 or not text.endswith('"'):
        raise Unparsed()
    escapes = {
        '0': '\0', 'a': '\a', 'b': '\b', 't': '\t', 'n': '\n', 'v': '\v',
        'f': '\f', 'r': '\r', 'e': '\x1b', ' ': ' ', '"': '"', '/': '/',
        '\\': '\\', 'N': '\x85', '_': '\xa0', 'L': '\u2028', 'P': '\u2029',
    }
    result = []
    index = 1
    while index < len(text) - 1:
        char = text[index]
        if char == '"':
            raise Unparsed()
        if char == '\\':
            index += 1
            if index >= len(text) - 1:
                raise Unparsed()
            char = text[index]
            if char in ('x', 'u', 'U'):
                width = {'x': 2, 'u': 4, 'U': 8}[char]
                digits = text[index + 1:index + 1 + width]
                if len(digits) != width or not re.fullmatch('[0-9a-fA-F]+', digits):
                    raise Unparsed()
                char = chr(int(digits, 16))
                index += width
            elif char in escapes:
                char = escapes[char]
            else:
                raise Unparsed()
        result.append(char)
        index += 1
    return ''.join(result)


def _scalar(text: str, *, key: bool = False, flow: bool = False) -> Any:
    """Decode scalars without interpreting expressions, tags or references."""
    text = text.strip()
    value: Any
    if not text:
        value = None
    elif text.startswith('"'):
        value = _double_quoted(text)
    elif text.startswith("'"):
        if len(text) < 2 or not text.endswith("'"):
            raise Unparsed()
        inner = text[1:-1]
        if "'" in inner.replace("''", ''):
            raise Unparsed()
        value = inner.replace("''", "'")
    elif text in ('[]', '{}') and not flow:
        value = [] if text == '[]' else {}
    elif text.startswith('[') and not flow and not key:
        value = _flow(text)
    elif (text[0] in '!&*[{|>%,]}@`' or text in ('---', '...', '<<')
          or re.search(r':(?:\s|$)', text) or (flow and any(c in text for c in '[],{}'))):
        raise Unparsed()
    elif text.lower() in ('true', 'false', 'null', '~'):
        value = {'true': True, 'false': False, 'null': None, '~': None}[text.lower()]
    elif re.fullmatch(r'-?(?:0|[1-9][0-9]*)', text):
        value = int(text)
    elif re.fullmatch(r'-?(?:0|[1-9][0-9]*)\.[0-9]+(?:[eE][+-]?[0-9]+)?', text):
        value = float(text)
    else:
        value = text
    if key and (not isinstance(value, str) or value == '<<'):
        raise Unparsed()
    handoff.bound_value(value)
    return value


def _block_scalar(lines: list[str], position: int, indent: int, style: str) -> tuple[str, int]:
    """Consume literal or folded content, preserving comments and relative indent."""
    content = []
    margin = None
    while position < len(lines):
        physical = lines[position]
        spaces = len(physical) - len(physical.lstrip(' '))
        if physical.strip():
            if spaces <= indent:
                break
            if margin is None:
                margin = spaces
            if spaces < margin:
                raise Unparsed()
        content.append(physical)
        position += 1
    margin = margin or indent + 1
    values = [line[margin:] if line.strip() else '' for line in content]
    if style.startswith('|'):
        value = '\n'.join(values)
        if values:
            value += '\n'
    else:
        pieces = []
        for index, line in enumerate(values):
            following = values[index + 1] if index + 1 < len(values) else None
            if following is None or not line or line.startswith((' ', '\t')):
                ending = '\n'
            elif not following:
                ending = ''
            elif following.startswith((' ', '\t')):
                ending = '\n'
            else:
                ending = ' '
            pieces.append(line + ending)
        value = ''.join(pieces)
    value = value.rstrip('\n')
    if not style.endswith('-') and any(values):
        value += '\n'
    return value, position


def read_workflow(raw: bytes) -> object:
    """Read a bounded workflow subset; unsupported syntax always raises Unparsed."""
    try:
        if len(raw) > MANIFEST_LIMIT:
            raise Unparsed()
        text = raw.decode('utf-8')
        if any(ord(char) < 32 and char not in '\t\r\n' for char in text):
            raise Unparsed()
        lines = [line.removesuffix('\r') for line in text.split('\n')]
        # Each sequence marker becomes a separate token, as in the candidate reader.
        records: list[tuple[int, str, int | None]] = []
        position = 0
        while position < len(lines):
            physical = lines[position]
            position += 1
            indent = len(physical) - len(physical.lstrip(' '))
            if physical[indent:].startswith('\t'):
                raise Unparsed()
            content, _ = _line(physical[indent:])
            if not content:
                continue
            if content in ('---', '...') or content.startswith('%'):
                raise Unparsed()
            block_indent = indent
            while content == '-' or content.startswith('- '):
                if indent > 64:
                    raise Unparsed()
                records.append((indent, '-', None))
                rest = content[1:]
                indent += 1 + len(rest) - len(rest.lstrip(' '))
                content = rest.lstrip(' ')
            if not content:
                continue
            content, separator = _line(content)
            tail = content[separator + 1:].strip() if separator is not None else content
            if tail in ('|', '|-', '>', '>-'):
                # A mapping in a sequence is logically indented after its marker.
                owner_indent = indent if separator is not None else block_indent
                value, position = _block_scalar(lines, position, owner_indent, tail)
                prefix = content[:separator + 1] + ' ' if separator is not None else ''
                content = prefix + json.dumps(value, ensure_ascii=False)
            records.append((indent, content, separator))
        cursor = 0

        def block(indent: int, depth: int) -> Any:
            """Consume each token once while enforcing depth and sequence limits."""
            nonlocal cursor
            if depth > 32:
                raise Unparsed()
            sequence = records[cursor][1] == '-'
            mapping = records[cursor][2] is not None
            if not sequence and not mapping:
                value = _scalar(records[cursor][1])
                cursor += 1
                return value
            result: Any = [] if sequence else {}
            while cursor < len(records) and records[cursor][0] == indent:
                _, content, separator = records[cursor]
                if sequence and content != '-':
                    break
                cursor += 1
                if sequence:
                    if len(result) >= 1000:
                        raise Unparsed()
                    child = None
                    if cursor < len(records) and records[cursor][0] > indent:
                        child = block(records[cursor][0], depth + 1)
                    result.append(child)
                else:
                    if separator is None:
                        raise Unparsed()
                    key = _scalar(content[:separator], key=True)
                    if key in result:
                        raise Unparsed()
                    tail = content[separator + 1:].strip()
                    if tail:
                        value = _scalar(tail)
                    elif cursor < len(records) and (
                        records[cursor][0] > indent
                        or records[cursor][0] == indent and records[cursor][1] == '-'
                    ):
                        value = block(records[cursor][0], depth + 1)
                    else:
                        value = None
                    result[key] = value
            return result

        if not records:
            return None
        if records[0][0] != 0:
            raise Unparsed()
        result = block(0, 1)
        if cursor != len(records):
            raise Unparsed()
        handoff.bound_value(result)
        return result
    except (Refusal, ValueError, UnicodeError, RecursionError):
        raise Unparsed() from None


# This table is the sole inventory of captured sources and their consumers.
SOURCE_CONTROLS = {
    'repository': ('credentials',),
    'environment': ('human-approval',),
    'branch_rules': ('trusted-execution',),
    'oidc_subject_template': ('credentials',),
    'agent_app': ('human-approval',),
    'iam_role': ('credentials', 'serialization', 'audit', 'isolation'),
    'iam_role_policies': ('credentials', 'audit', 'cost', 'isolation'),
    'audit_store': ('audit', 'credentials', 'isolation'),
    'target_policy': ('serialization', 'credentials', 'isolation'),
    'target_lifecycle': ('cost',),
}
WORKFLOW_CONTROLS = (
    'trusted-execution', 'candidate-binding', 'serialization', 'recovery-limits', 'isolation',
)
ERASURE_ACTIONS = (
    's3:BypassGovernanceRetention', 's3:PutObjectRetention', 's3:PutObjectLegalHold',
    's3:PutBucketObjectLockConfiguration', 's3:DeleteObject*', 's3:PutBucketVersioning',
    's3:PutLifecycleConfiguration',
)
ROLE_READS = {'iam:GetRole', 'iam:ListRolePolicies', 'iam:GetRolePolicy',
              'iam:ListAttachedRolePolicies'}
BUCKET_READS = {'s3:GetBucketVersioning', 's3:GetBucketObjectLockConfiguration',
                's3:GetLifecycleConfiguration', 's3:GetBucketPolicy'}
AUDIT_LIST_ACTIONS = {'s3:ListBucket', 's3:ListBucketVersions'}
OBJECT_READS = {'s3:GetObject', 's3:GetObjectVersion'}
# Object Lock fields of a decision version; allowed on the audit prefixes only.
AUDIT_OBJECT_READS = {'s3:GetObjectRetention'}
EFFECT_ACTIONS = OBJECT_READS | {'s3:PutObject', 's3:DeleteObject'}
DISPATCH_INPUTS = {'prepare_run_id', 'admission_sha256', 'pre_deploy_reviews'}


def _map(value: Any) -> dict[str, Any]:
    """Use only an object's expected fields, never instructions in other values."""
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    """Return an API list or an empty invalid value."""
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    """Accept an IAM scalar-or-list without silently discarding malformed entries."""
    items = value if isinstance(value, list) else [value]
    return items if items and all(isinstance(item, str) and item for item in items) else []


def _positive(value: Any, maximum: int | None = None) -> bool:
    """Reject booleans, missing bounds and nonpositive integers."""
    return type(value) is int and value > 0 and (maximum is None or value <= maximum)


def _document(value: Any) -> dict[str, Any]:
    """Decode a raw get-bucket-policy Policy string with the shared strict reader."""
    if isinstance(value, str):
        try:
            value = handoff.parse_json(value.encode('utf-8'))
        except (Refusal, UnicodeError):
            return {}
    return _map(value)


def _statements(value: Any) -> list[dict[str, Any]]:
    """Read an IAM Statement object or array, refusing malformed entries."""
    value = _document(value).get('Statement')
    values = [value] if isinstance(value, dict) else _list(value)
    return values if values and all(isinstance(item, dict) for item in values) else []


def _s3(value: Any) -> tuple[str, str, str]:
    """Split an S3 ARN or URI into its ARN, bucket ARN and object key."""
    if not isinstance(value, str):
        return '', '', ''
    if value.startswith('s3://'):
        value = 'arn:aws:s3:::' + value[5:]
    match = re.fullmatch(r'(arn:aws:s3:::[a-z0-9][a-z0-9.-]*)/(.+)', value)
    return (value, match[1], match[2]) if match else ('', '', '')


def _covers(pattern: str, resource: str) -> bool:
    """Prove resource coverage using only exact matches or a final wildcard."""
    return bool(resource) and (pattern == resource or pattern == '*' or (
        pattern.endswith('*') and not any(c in pattern[:-1] for c in '*?[')
        and resource.startswith(pattern[:-1])))


def _denies(policy: Any, action: str, resource: str, role: str = '') -> bool:
    """Require a universal deny, optionally excepting precisely one role ARN.

    Unknown policy operators or extra conditions cannot prove exclusion. A broad
    Allow cannot override this explicit deny under AWS policy evaluation.
    """
    for statement in _statements(_map(policy).get('Policy', policy)):
        if (statement.get('Effect') != 'Deny' or statement.get('Principal') != '*'
                or 'NotAction' in statement or 'NotResource' in statement):
            continue
        condition = statement.get('Condition', {})
        exceptions = [
            {operator: {'aws:PrincipalArn': role}}
            for operator in ('ArnNotEquals', 'StringNotEquals')
        ] if role else []
        if condition != {} and condition not in exceptions:
            continue
        if (any(fnmatchcase(action.lower(), pattern.lower())
                for pattern in _strings(statement.get('Action')))
                and any(_covers(pattern, resource)
                        for pattern in _strings(statement.get('Resource')))):
            return True
    return False


def _workflow_jobs(workflow: Any) -> list[dict[str, Any]]:
    """Read jobs without interpreting workflow expressions."""
    return [_map(job) for job in _map(_map(workflow).get('jobs')).values()]


def _single_job(workflow: Any) -> dict[str, Any]:
    """Select the unique protected job; more than one cannot satisfy binding."""
    jobs = _workflow_jobs(workflow)
    return jobs[0] if len(jobs) == 1 else {}


def _execution_codes(controls: dict[str, Any], snapshot: dict[str, Any],
                     workflows: dict[str, Any]) -> list[str]:
    """Check triggers, permissions, action pins and active branch rules."""
    codes = []
    for name in ('prepare', 'deploy', 'deploy-job'):
        workflow = _map(workflows.get(name))
        event = workflow.get('on')
        events = set(event) if isinstance(event, dict) else set(_strings(event))
        expected = 'workflow_call' if name == 'deploy-job' else 'workflow_dispatch'
        if events != {expected}:
            codes.append('untrusted-trigger')
        allowed = {'contents': 'read', 'actions': 'read'}
        if name != 'prepare':
            allowed['id-token'] = 'write'
        jobs = _workflow_jobs(workflow)
        if not jobs:
            codes.append('permissions-undeclared')
        for node in [workflow, *jobs]:
            permissions = node.get('permissions')
            if not isinstance(permissions, dict):
                codes.append('permissions-undeclared')
            elif any(key not in allowed or value not in ('none', allowed.get(key))
                     for key, value in permissions.items()):
                codes.append('permissions-broad')
        nodes = [workflow, *jobs, *(_map(step) for job in jobs
                                   for step in _list(job.get('steps')))]
        for node in nodes:
            if 'uses' in node:
                value = node['uses']
                if not isinstance(value, str) or not (
                    re.fullmatch(r'\./[^\s@]+', value)
                    or re.fullmatch(r'[\w.-]+/[\w./-]+@[0-9a-fA-F]{40}', value)
                    or re.fullmatch(r'docker://[^\s@]+@sha256:[0-9a-fA-F]{64}', value)
                ):
                    codes.append('unpinned-action')
            if node.get('secrets') == 'inherit':
                codes.append('secrets-inherited')
            if isinstance(node.get('run'), str) and '${{' in node['run']:
                codes.append('expression-in-run')
    caller = _single_job(workflows.get('deploy'))
    if (caller.get('uses') != './' + str(controls.get('deploy_job_workflow', ''))
            or not isinstance(caller.get('secrets'), dict) or not caller['secrets']
            or any(not isinstance(value, str) or not re.fullmatch(
                r'\$\{\{\s*secrets\.[A-Za-z_][A-Za-z0-9_]*\s*\}\}', value)
                   for value in _map(caller.get('secrets')).values())):
        codes.append('untrusted-trigger')
    rules = [_map(rule) for rule in _list(snapshot.get('branch_rules'))]
    kinds = {rule.get('type') for rule in rules if isinstance(rule.get('type'), str)}
    if not ({'deletion', 'non_fast_forward'} <= kinds and any(
        rule.get('type') == 'pull_request' and _positive(
            _map(rule.get('parameters')).get('required_approving_review_count')) for rule in rules
    )):
        codes.append('branch-unprotected')
    return codes


def _binding_codes(controls: dict[str, Any], workflows: dict[str, Any]) -> list[str]:
    """Require the binding chain before every declared mutation."""
    codes = []
    job = _single_job(workflows.get('deploy-job'))
    steps = [_map(step) for step in _list(job.get('steps'))]
    ids = [step.get('id') for step in steps]
    chain = ['verify-admission', 'bind', 'credentials', 'budget', 'audit', 'recheck']
    if any(ids.count(name) != 1 for name in chain):
        codes.append('binding-step-missing')
    positions = [ids.index(name) for name in chain if name in ids]
    mutations = [index for index, name in enumerate(ids)
                 if isinstance(name, str) and name.startswith('mutate-')]
    if positions != sorted(positions) or not mutations or any(
        index <= max(positions, default=-1)
        for index in mutations
    ) or any('if' in step for step in steps
             if step.get('id') in chain or str(step.get('id', '')).startswith('mutate-')):
        codes.append('binding-order')
    if any('continue-on-error' in step for step in steps
           if step.get('id') in chain or str(step.get('id', '')).startswith('mutate-')):
        codes.append('mutation-continues-on-error')
    environment = job.get('environment')
    if isinstance(environment, dict):
        environment = environment.get('name')
    if not controls.get('environment') or environment != controls['environment']:
        codes.append('environment-mismatch')
    dispatch = _map(_map(_map(workflows.get('deploy')).get('on')).get('workflow_dispatch'))
    call = _map(_map(_map(workflows.get('deploy-job')).get('on')).get('workflow_call'))
    expected = {name: '${{ inputs.' + name + ' }}' for name in DISPATCH_INPUTS}
    if (set(_map(dispatch.get('inputs'))) != DISPATCH_INPUTS
            or set(_map(call.get('inputs'))) != DISPATCH_INPUTS
            or _single_job(workflows.get('deploy')).get('with') != expected):
        codes.append('inputs-mismatch')
    return codes


def approval_codes(controls: dict[str, Any], environment: Any) -> list[str]:
    """Check the GitHub environment half of approval for readiness and bind."""
    codes = []
    settings = _map(environment)
    rules = [_map(rule) for rule in _list(settings.get('protection_rules'))
             if _map(rule).get('type') == 'required_reviewers']
    reviewers = [reviewer for rule in rules for reviewer in _list(rule.get('reviewers'))]
    if not reviewers or any(
        not _positive(_map(_map(reviewer).get('reviewer')).get('id'))
        or not isinstance(_map(_map(reviewer).get('reviewer')).get('login'), str)
        or not _map(_map(reviewer).get('reviewer')).get('login') for reviewer in reviewers
    ):
        codes.append('reviewers-missing')
    if any(_map(reviewer).get('type') != 'User' for reviewer in reviewers):
        codes.append('team-reviewer-unsupported')
    if not rules or any(rule.get('prevent_self_review') is not True for rule in rules):
        codes.append('self-review-allowed')
    if settings.get('can_admins_bypass') is not False:
        codes.append('admin-bypass')
    if _map(settings.get('deployment_branch_policy')).get('protected_branches') is not True:
        codes.append('branch-policy-open')
    agent = _map(controls.get('agent'))
    if agent.get('kind') != 'app':
        codes.append('agent-kind-unsupported')
    if any(_map(_map(reviewer).get('reviewer')).get('login') == agent.get('login')
           for reviewer in reviewers):
        codes.append('agent-is-reviewer')
    return codes


def _inline_statements(snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """Check list/get inline-policy completeness and reject managed policies.

    iam_role_policies combines raw PolicyNames, get-role-policy responses in
    Policies, and raw AttachedPolicies. Missing responses cannot prove scope.
    """
    bundle = _map(snapshot.get('iam_role_policies'))
    names = _strings(bundle.get('PolicyNames'))
    policies = _list(bundle.get('Policies'))
    statements = [statement for policy in policies
                  for statement in _statements(_map(policy).get('PolicyDocument'))]
    valid = (bool(names) and len(names) == len(set(names))
             and len(policies) == len(names)
             and all(isinstance(_map(policy).get('PolicyName'), str) for policy in policies)
             and {_map(policy).get('PolicyName') for policy in policies} == set(names)
             and all(_statements(_map(policy).get('PolicyDocument')) for policy in policies)
             and bundle.get('AttachedPolicies') == []
             and bundle.get('IsTruncated', False) is False and not bundle.get('Marker'))
    return statements, valid


def _listing_scoped(condition: Any, prefixes: list[str]) -> bool:
    """Limit bucket listing to the audit key spaces used for execution history."""
    for operator in ('StringEquals', 'StringLike'):
        fields = _map(_map(condition).get(operator))
        patterns = _strings(fields.get('s3:prefix'))
        if patterns and all(any(pattern.startswith(_s3(prefix)[2]) and _s3(prefix)[2]
                                for prefix in prefixes) for pattern in patterns):
            return True
    return False


def _effect_listing(resource: str, condition: Any, effects: set[str]) -> bool:
    """Allow listing an effect's bucket only for that effect's exact key.

    Without list permission S3 answers a missing key with 403, so teardown could
    not tell a deleted effect from a refused read.
    """
    keys = {_s3(effect)[2] for effect in effects if _s3(effect)[1] == resource}
    patterns = _strings(_map(_map(condition).get('StringEquals')).get('s3:prefix'))
    exact = set(_map(condition)) == {'StringEquals'}
    return bool(keys) and exact and bool(patterns) and set(patterns) <= keys


def _permission_codes(
    controls: dict[str, Any], snapshot: dict[str, Any],
) -> tuple[list[str], bool]:
    """Prove each action/resource pair stays inside the declared release scope."""
    codes = []
    cloud = _map(controls.get('cloud'))
    role = _map(_map(snapshot.get('iam_role')).get('Role')).get('Arn')
    effects = {_s3(_map(effect).get('resource'))[0] for effect in _list(controls.get('effects'))}
    audit = _map(controls.get('audit'))
    prefixes = [_s3(audit.get(name))[0] for name in ('decision_prefix', 'ops_prefix')]
    buckets = {_s3(resource)[1] for resource in [*effects, *prefixes]} - {''}
    audit_buckets = {_s3(prefix)[1] for prefix in prefixes} - {''}
    statements, complete = _inline_statements(snapshot)
    if not complete or cloud.get('provider') != 'aws':
        codes.append('permissions-exceed-allowlist')
    policies = [*_map(snapshot.get('target_policy')).values(),
                _map(snapshot.get('audit_store')).get('policy')]
    if any(statement.get('Effect') == 'Allow' for policy in policies
           for statement in _statements(_map(policy).get('Policy', policy))):
        codes.append('permissions-exceed-allowlist')
    allowed = _strings(cloud.get('allowed_actions'))
    for statement in statements:
        actions = _strings(statement.get('Action'))
        resources = _strings(statement.get('Resource'))
        if not actions or not resources or statement.get('Effect') != 'Allow' or any(
            name in statement for name in ('NotAction', 'NotResource', 'Principal', 'NotPrincipal')
        ):
            codes.append('permissions-exceed-allowlist')
        if any('*' in action or '?' in action for action in actions) or '*' in resources:
            codes.append('wildcard-permission')
        for action in actions:
            if action not in allowed:
                codes.append('permissions-exceed-allowlist')
            for resource in resources:
                in_scope = (
                    (action in EFFECT_ACTIONS and resource in effects and resource
                     and not any(c in resource for c in '*?['))
                    or (action in OBJECT_READS | AUDIT_OBJECT_READS | {'s3:PutObject'}
                        and resource in [prefix + '*' for prefix in prefixes if prefix])
                    or (action in BUCKET_READS and resource in buckets)
                    or (action in AUDIT_LIST_ACTIONS and resource in audit_buckets
                        and _listing_scoped(statement.get('Condition'), prefixes))
                    or (action in ROLE_READS and resource == role and role)
                    or (action == 's3:ListBucket' and _effect_listing(
                        resource, statement.get('Condition'), effects))
                )
                if not in_scope:
                    codes.append('permissions-exceed-allowlist')
    # Raw configuration must identify the same audit store; no captured label can widen it.
    if len(audit_buckets) != 1 or not all(prefixes) or prefixes[0] == prefixes[1]:
        codes.append('permissions-exceed-allowlist')
    return codes, not codes


def _credential_codes(controls: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    """Require a single exact OIDC trust statement and bounded role permissions."""
    codes, _ = _permission_codes(controls, snapshot)
    role = _map(_map(snapshot.get('iam_role')).get('Role'))
    statements = _statements(role.get('AssumeRolePolicyDocument'))
    statement = statements[0] if len(statements) == 1 else {}
    arn = role.get('Arn', '')
    match = re.fullmatch(r'arn:aws:iam::([0-9]{12}):role/(.+)', str(arn))
    provider = ('arn:aws:iam::' + match[1] + ':oidc-provider/'
                'token.actions.githubusercontent.com') if match else ''
    condition = _map(statement.get('Condition'))
    equals = _map(condition.get('StringEquals'))
    if (len(statements) != 1 or statement.get('Effect') != 'Allow'
            or _strings(statement.get('Action')) != ['sts:AssumeRoleWithWebIdentity']
            or statement.get('Principal') != {'Federated': provider} or not provider
            or role.get('RoleName') != _map(controls.get('cloud')).get('role_name')
            or not match or match[2].rsplit('/', 1)[-1] != role.get('RoleName')
            or set(condition) != {'StringEquals'}
            or any(key in statement for key in ('NotAction', 'NotPrincipal'))
            or equals.get('token.actions.githubusercontent.com:aud')
            != _map(controls.get('cloud')).get('audience')
            or not _map(controls.get('cloud')).get('audience')):
        codes.append('trust-open')
    repository = str(controls.get('repository', ''))
    parts = repository.split('/')
    owner_id = _map(_map(snapshot.get('repository')).get('owner')).get('id')
    suffix = (':environment:' + str(controls.get('environment', '')) + ':job_workflow_ref:'
              + repository + '/' + str(controls.get('deploy_job_workflow', ''))
              + '@refs/heads/' + str(controls.get('release_branch', '')))
    mutable = 'repo:' + repository + suffix
    immutable = ('repo:' + parts[0] + '@' + str(owner_id) + '/' + parts[-1] + '@'
                 + str(controls.get('repository_id')) + suffix) if len(parts) == 2 else ''
    subject = equals.get('token.actions.githubusercontent.com:sub')
    template = _map(snapshot.get('oidc_subject_template'))
    if (template.get('use_default') is not False
            or template.get('include_claim_keys') != ['repo', 'context', 'job_workflow_ref']
            # GitHub reports the subject's repository part, e.g. repo:owner@1/name@2.
            or template.get('sub_claim_prefix') not in (
                (immutable.split(':environment:')[0] if template.get('use_immutable_subject')
                 else 'repo:' + repository), None)):
        codes.append('subject-template-mismatch')
    if (subject not in (mutable, immutable) or not repository or not controls.get('environment')
            or not controls.get('deploy_job_workflow') or not controls.get('release_branch')
            or subject == immutable and not _positive(owner_id)
            or template.get('use_immutable_subject') is True and subject != immutable
            or template.get('use_immutable_subject') is False and subject != mutable):
        codes.append('trust-subject-mismatch')
    if (subject == mutable and (
        not _positive(controls.get('repository_id'))
        or equals.get('token.actions.githubusercontent.com:repository_id')
        != str(controls.get('repository_id'))
    )):
        codes.append('repository-id-unpinned')
    return codes


def _lifecycle_prefix(rule: dict[str, Any]) -> str | None:
    """Return an unconditional key prefix; unknown filters cannot prove cleanup."""
    if 'Filter' not in rule:
        return rule.get('Prefix', '') if isinstance(rule.get('Prefix', ''), str) else None
    selector = rule['Filter']
    if not isinstance(selector, dict) or not set(selector) <= {'Prefix'}:
        return None
    return selector.get('Prefix', '') if isinstance(selector.get('Prefix', ''), str) else None


def _audit_codes(controls: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    """Check retention and deny policies independently of caller permissions."""
    codes = []
    audit = _map(controls.get('audit'))
    if audit.get('kind') != 'aws-s3-object-lock':
        codes.append('audit-kind-unsupported')
    store = _map(snapshot.get('audit_store'))
    lock = _map(_map(store.get('object_lock')).get('ObjectLockConfiguration'))
    retention = _map(_map(lock.get('Rule')).get('DefaultRetention'))
    if (_map(store.get('versioning')).get('Status') != 'Enabled'
            or lock.get('ObjectLockEnabled') != 'Enabled'
            or retention.get('Mode') != 'COMPLIANCE'):
        codes.append('audit-not-immutable')
    minimum = audit.get('minimum_retention_days')
    window = controls.get('budget_window_days')
    days = retention.get('Days')
    if 'Days' not in retention and _positive(retention.get('Years')):
        # A calendar year always contains at least 365 days.
        days = retention['Years'] * 365
    if (not _positive(minimum) or not _positive(window) or not _positive(days)
            or days < max(minimum, window)):
        codes.append('audit-retention-short')
    prefixes = [_s3(audit.get(name)) for name in ('decision_prefix', 'ops_prefix')]
    lifecycle = _map(store.get('lifecycle'))
    if not isinstance(lifecycle.get('Rules'), list):
        codes.append('audit-history-expires')
    for value in _list(lifecycle.get('Rules')):
        rule = _map(value)
        if rule.get('Status') == 'Disabled':
            continue
        prefix = _lifecycle_prefix(rule)
        if any(key in rule for key in ('Expiration', 'Transitions', 'NoncurrentVersionExpiration',
                                       'NoncurrentVersionTransitions')) and (
            prefix is None or any(key.startswith(prefix) or prefix.startswith(key)
                                  for _, _, key in prefixes)
        ):
            codes.append('audit-history-expires')
    role = str(_map(_map(snapshot.get('iam_role')).get('Role')).get('Arn', ''))
    policy = store.get('policy')
    if not role or any(not arn or not _denies(policy, 's3:*', arn + '*', role)
                       for arn, _, _ in prefixes):
        codes.append('audit-writer-open')
    bucket = prefixes[0][1]
    object_actions = {'s3:BypassGovernanceRetention', 's3:PutObjectRetention',
                      's3:PutObjectLegalHold', 's3:DeleteObject*'}
    for action in ERASURE_ACTIONS:
        resources = [arn + '*' for arn, _, _ in prefixes] if action in object_actions else [bucket]
        if any(not _denies(policy, action, resource) for resource in resources):
            codes.append('audit-erasable')
    statements, _ = _inline_statements(snapshot)
    # Exact target deletion is needed for teardown; it cannot erase audit history.
    effect_resources = {_s3(_map(effect).get('resource'))[0]
                        for effect in _list(controls.get('effects'))}
    if any((fnmatchcase(banned.lower(), action.lower())
            or fnmatchcase(action.lower(), banned.lower()))
           and not (action == 's3:DeleteObject' and banned == 's3:DeleteObject*'
                    and _strings(statement.get('Resource'))
                    and all(resource in effect_resources and not any(c in resource for c in '*?[')
                            for resource in _strings(statement.get('Resource'))))
           for statement in statements for action in _strings(statement.get('Action'))
           for banned in ERASURE_ACTIONS):
        codes.append('audit-erasable')
    return codes


def _recovery_codes(controls: dict[str, Any], job: dict[str, Any]) -> list[str]:
    """Require finite retries and a teardown gated by the successful recheck."""
    codes = []
    if (not _positive(controls.get('max_executions'), 100)
            or not _positive(controls.get('budget_window_days'), 365)):
        codes.append('executions-unbounded')
    steps = [_map(step) for step in _list(job.get('steps'))]
    positions = [index for index, step in enumerate(steps) if step.get('id') == 'teardown']
    if len(positions) != 1:
        codes.append('teardown-missing')
    elif (steps[positions[0]].get('if') != "always() && steps.recheck.outcome == 'success'"
          or any(index >= positions[0] for index, step in enumerate(steps)
                 if str(step.get('id', '')).startswith('mutate-'))):
        codes.append('teardown-unguarded')
    effects = _list(controls.get('effects'))
    if not effects or any(not all(isinstance(_map(effect).get(key), str) and _map(effect)[key]
                                 for key in ('id', 'kind', 'resource', 'payload_component'))
                          for effect in effects):
        codes.append('effects-undeclared')
    if any(_map(effect).get('kind') != 'aws-s3-object' for effect in effects):
        codes.append('effect-kind-unsupported')
    return codes


def _expires(rules: list[dict[str, Any]], key: str, window: Any,
             field: str, days_field: str) -> bool:
    """Prove expiry of all matching objects without tag-dependent filters."""
    return _positive(window) and any(
        rule.get('Status') == 'Enabled' and (prefix := _lifecycle_prefix(rule)) is not None
        and key.startswith(prefix) and _positive(_map(rule.get(field)).get(days_field))
        and _map(rule.get(field))[days_field] <= window
        and not _map(rule.get(field)).get('NewerNoncurrentVersions') for rule in rules
    )


def _cost_codes(controls: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    """Require exact effects, bounded bytes and current/noncurrent expiry."""
    codes = []
    statements, _ = _inline_statements(snapshot)
    audit = _map(controls.get('audit'))
    audit_resources = {_s3(audit.get(name))[0] + '*' for name in ('decision_prefix', 'ops_prefix')}
    effects = [_map(effect) for effect in _list(controls.get('effects'))]
    exact = {_s3(effect.get('resource'))[0] for effect in effects}
    for statement in statements:
        for action in _strings(statement.get('Action')):
            if action in OBJECT_READS | BUCKET_READS | ROLE_READS | AUDIT_LIST_ACTIONS:
                continue
            resources = set(_strings(statement.get('Resource')))
            if action in AUDIT_OBJECT_READS and resources <= audit_resources:
                continue
            for resource in _strings(statement.get('Resource')):
                if not (action == 's3:PutObject' and resource in audit_resources) and (
                    action not in EFFECT_ACTIONS or resource not in exact
                    or any(char in resource for char in '*?[')
                ):
                    codes.append('effect-resource-open')
    window = controls.get('budget_window_days')
    targets = _map(snapshot.get('target_lifecycle'))
    for effect in effects:
        arn, bucket, key = _s3(effect.get('resource'))
        if effect.get('kind') != 'aws-s3-object' or not arn or any(c in arn for c in '*?['):
            codes.append('effect-resource-open')
        if not _positive(effect.get('max_payload_bytes')):
            codes.append('payload-unbounded')
        target = _map(targets.get(bucket.removeprefix('arn:aws:s3:::')))
        rules = [_map(rule) for rule in _list(_map(target.get('lifecycle')).get('Rules'))]
        versioning = _map(target.get('versioning')).get('Status')
        if (versioning not in ('Enabled', 'Suspended', None) or 'versioning' not in target
                or not _expires(rules, key, window, 'Expiration', 'Days')
                or versioning in ('Enabled', 'Suspended')
                and not _expires(rules, key, window,
                                 'NoncurrentVersionExpiration', 'NoncurrentDays')):
            codes.append('cleanup-unbounded')
    if not effects:
        codes.extend(['effect-resource-open', 'payload-unbounded', 'cleanup-unbounded'])
    return codes


def evaluate_readiness(controls: dict[str, Any], snapshot: dict[str, Any],
                       workflows: dict[str, Any]) -> dict[str, Any]:
    """Evaluate captured data without I/O or authority to change any control.

    workflows maps prepare, deploy and deploy-job to parsed reader results (None
    for unparsed). audit_store bundles raw versioning, object_lock, lifecycle
    and policy responses. target_policy maps bucket names to raw policy responses;
    target_lifecycle maps bucket names to raw versioning and lifecycle responses.
    Missing sources are tracked by SOURCE_CONTROLS, including for live rechecks.
    """
    controls, snapshot, workflows = _map(controls), _map(snapshot), _map(workflows)
    job = _single_job(workflows.get('deploy-job'))
    codes = {'trusted-execution': _execution_codes(controls, snapshot, workflows),
             'candidate-binding': _binding_codes(controls, workflows),
             'human-approval': approval_codes(controls, snapshot.get('environment')),
             'serialization': [], 'credentials': _credential_codes(controls, snapshot),
             'audit': _audit_codes(controls, snapshot),
             'recovery-limits': _recovery_codes(controls, job),
             'cost': _cost_codes(controls, snapshot), 'isolation': []}
    permissions = _map(_map(snapshot.get('agent_app')).get('permissions'))
    if (not isinstance(_map(snapshot.get('agent_app')).get('permissions'), dict)
        or _map(snapshot.get('agent_app')).get('slug') != _map(controls.get('agent')).get('slug')
        or not _map(controls.get('agent')).get('slug') or any(
        permissions.get(name) not in (None, 'none')
        for name in ('administration', 'environments', 'secrets', 'actions_variables', 'workflows')
    ) or permissions.get('contents') not in (None, 'none', 'read')):
        codes['human-approval'].append('agent-can-reconfigure')
    concurrency = _map(job.get('concurrency'))
    if (not controls.get('concurrency_group')
            or concurrency.get('group') != controls['concurrency_group']):
        codes['serialization'].append('concurrency-missing')
    if concurrency.get('cancel-in-progress') is not False:
        codes['serialization'].append('cancel-in-progress')
    role = str(_map(_map(snapshot.get('iam_role')).get('Role')).get('Arn', ''))
    policies = _map(snapshot.get('target_policy'))
    effects = [_map(effect) for effect in _list(controls.get('effects'))]
    if not effects or not role or any(
        not _denies(policies.get(_s3(effect.get('resource'))[1].removeprefix('arn:aws:s3:::')),
                    's3:*', _s3(effect.get('resource'))[0], role) for effect in effects
    ):
        codes['serialization'].append('writers-not-excluded')
    _, scoped = _permission_codes(controls, snapshot)
    if not scoped:
        codes['isolation'].append('role-reaches-beyond-effects')
    classification = _map(controls.get('isolation'))
    if (classification.get('classification') != 'non-production'
            or not isinstance(classification.get('attested_by'), str)
            or not classification['attested_by'].strip()):
        codes['isolation'].append('classification-unattested')
    for name in ('prepare', 'deploy', 'deploy-job'):
        for candidate in _workflow_jobs(workflows.get(name)):
            if (name == 'deploy' and candidate.get('uses')
                    == './' + str(controls.get('deploy_job_workflow', ''))):
                continue
            labels = _strings(candidate.get('runs-on'))
            if not labels or not all(re.fullmatch(r'(ubuntu|windows|macos)-[a-zA-Z0-9.-]+', label)
                                     for label in labels):
                codes['isolation'].append('self-hosted-runner')
    unavailable: dict[str, list[str]] = {name: [] for name in codes}
    for source, consumers in SOURCE_CONTROLS.items():
        shape = list if source == 'branch_rules' else dict
        if source not in snapshot or not isinstance(snapshot[source], shape):
            for name in consumers:
                unavailable[name].append('source-unavailable:' + source)
    for name in ('prepare', 'deploy', 'deploy-job'):
        if not isinstance(workflows.get(name), dict):
            consumers = (WORKFLOW_CONTROLS if name != 'prepare'
                         else ('trusted-execution', 'isolation'))
            for control in consumers:
                unavailable[control].append('workflow-unparsed:' + name)
    if 'audit-kind-unsupported' in codes['audit']:
        unavailable['audit'].append('audit-kind-unsupported')
    rows = [{'control': name,
             'status': 'unverified' if unavailable[name] else 'missing' if values else 'met',
             'codes': list(dict.fromkeys(unavailable[name] or values))}
            for name, values in codes.items()]
    ready = all(result['status'] == 'met' for result in rows)
    return {'status': 'ready' if ready else 'blocked', 'controls': rows,
            'blocked_mutations': [] if ready else ['deploy', 'teardown'],
            'unaffected': ['authoring', 'collection', 'admission', 'review'],
            'cost_bound': {'max_executions': controls.get('max_executions'),
                           'window_days': controls.get('budget_window_days'),
                           'per_execution': {'effect_requests': {
                               'write': 1, 'read': 1, 'delete': 1},
                                             'decision_writes': 1, 'ops_writes': 1},
                           'max_payload_bytes': {effect['id']: effect.get('max_payload_bytes')
                                                 for effect in effects
                                                 if isinstance(effect.get('id'), str)},
                           'budget_refusal_writes': 0}}


def _canonical(value: Any) -> bytes:
    """Serialize reproducible UTF-8 records including their final newline."""
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            + '\n').encode('utf-8')


def _run_number(value: Any) -> int:
    """Read positive API integers or decimal GitHub environment values."""
    if type(value) is int and value > 0:
        return value
    if isinstance(value, str) and re.fullmatch(r'[1-9][0-9]{0,19}', value):
        return int(value)
    raise Refusal('context-malformed', 'refused')


def _bound_approvals(controls: dict[str, Any], environment: dict[str, Any],
                     approvals: Any, attempt: dict[str, Any], marker: str) -> list[dict[str, Any]]:
    """Select independent required users whose comments name the whole digest."""
    relevant = [item for item in _list(approvals) if isinstance(item, dict) and any(
        _map(env).get('name') == controls['environment']
        and _map(env).get('id') == environment['id']
        for env in _list(item.get('environments'))
    )]
    if any(item.get('state') == 'rejected' for item in relevant):
        raise Refusal('approval-rejected', 'refused')
    approved = [item for item in relevant if item.get('state') == 'approved']
    if not approved:
        raise Refusal('approval-missing', 'refused')
    excluded = {attempt['triggering_actor']['login'].casefold(),
                controls['agent']['login'].casefold()}
    approved = [item for item in approved
                if admission.text(_map(item.get('user')).get('login'))
                and _positive(_map(item.get('user')).get('id'))]
    if not approved:
        raise Refusal('approval-missing', 'refused')
    independent = [item for item in approved if (
        item['user']['login'].casefold() not in excluded
        and _map(item.get('user')).get('id') != attempt['triggering_actor']['id']
    )]
    if not independent:
        raise Refusal('approval-self', 'refused')
    reviewers = [_map(_map(item).get('reviewer'))
                 for rule in environment['protection_rules']
                 if _map(rule).get('type') == 'required_reviewers'
                 for item in _list(rule.get('reviewers'))]
    required = [item for item in independent if _map(item.get('user')).get('type') == 'User'
                and any(_map(item.get('user')).get('id') == reviewer.get('id')
                        and _map(item.get('user')).get('login') == reviewer.get('login')
                        for reviewer in reviewers)]
    if not required:
        raise Refusal('approval-missing', 'refused')
    matches = [item for item in required if isinstance(item.get('comment'), str)
               and re.search(r'(?<![A-Za-z0-9_:-])' + re.escape(marker)
                             + r'(?![A-Za-z0-9_-])', item['comment'])]
    if not matches:
        raise Refusal('approval-unbound', 'refused')
    selected = {}
    for item in matches:
        user = item['user']
        selected[user['id']] = {'login': user['login'], 'id': user['id'],
                               'comment_sha256': admission.sha256(item['comment'].encode('utf-8'))}
    return sorted(selected.values(), key=lambda item: item['id'])


def bind(args: Any, root: Path, parsed: dict[str, Any],
         captured: dict[str, Any]) -> dict[str, Any]:
    """Verify admission, workflow provenance and this run's independent approval."""
    clock = admission.clock_time(None)
    try:
        if admission.verify(args.admission, root=root, now=clock)['status'] != 'current':
            raise Refusal('admission-stale', 'refused')
        admitted, record_raw = admission.read_record(root, args.admission)
        if record_raw != captured['admission']:
            raise Refusal('admission-stale', 'refused')
        candidate_raw = admission.read_manifest(root, admitted['candidate']['locator'])
        if admission.sha256(candidate_raw) != admitted['candidate']['sha256']:
            raise Refusal('admission-stale', 'refused')
        candidate = handoff.parse_yaml(candidate_raw)
    except Refusal:
        raise Refusal('admission-stale', 'refused') from None
    digest = admission.sha256(captured['admission']).removeprefix('sha256:')
    if args.expect_admission_sha256 != digest:
        raise Refusal('admission-digest-mismatch', 'refused')
    controls, context, attempt = (parsed[name] for name in ('controls', 'context', 'attempt'))
    if not all(isinstance(value, dict) for value in (controls, context, attempt)):
        raise Refusal('context-malformed', 'refused')
    names = ('GITHUB_REPOSITORY', 'GITHUB_REPOSITORY_ID', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT',
             'GITHUB_WORKFLOW_REF', 'GITHUB_WORKFLOW_SHA', 'GITHUB_REF', 'GITHUB_TRIGGERING_ACTOR',
             'environment')
    if (any(not admission.text(context.get(name)) for name in names)
            or not re.fullmatch(r'[0-9a-f]{40}', context['GITHUB_WORKFLOW_SHA'])
            or not admission.text(_map(controls.get('agent')).get('login'))
            or not isinstance(attempt.get('triggering_actor'), dict)
            or not admission.text(attempt['triggering_actor'].get('login'))):
        raise Refusal('context-malformed', 'refused')
    run_id = _run_number(context['GITHUB_RUN_ID'])
    run_attempt = _run_number(context['GITHUB_RUN_ATTEMPT'])
    repository_id = _run_number(context['GITHUB_REPOSITORY_ID'])
    if (_run_number(attempt.get('id')) != run_id
            or attempt['triggering_actor']['login'] != context['GITHUB_TRIGGERING_ACTOR']):
        raise Refusal('context-malformed', 'refused')
    _run_number(attempt['triggering_actor'].get('id'))
    if run_attempt != 1 or _run_number(attempt.get('run_attempt')) != 1:
        raise Refusal('rerun-refused', 'refused')
    if (admitted['target']['environment'] != context['environment']
            or admitted['target']['environment'] != controls.get('environment')
            or admitted['target']['account'] != _map(controls.get('cloud')).get('account_label')):
        raise Refusal('target-mismatch', 'refused')
    repository = _map(attempt.get('repository'))
    branch_ref = 'refs/heads/' + str(controls.get('release_branch', ''))
    workflow_ref = (str(controls.get('repository', '')) + '/'
                    + str(controls.get('deploy_workflow', '')) + '@' + branch_ref)
    if (context['GITHUB_REPOSITORY'] != controls.get('repository')
            or repository_id != controls.get('repository_id')
            or context['GITHUB_WORKFLOW_REF'] != workflow_ref
            or context['GITHUB_REF'] != branch_ref
            or attempt.get('path') != controls.get('deploy_workflow')
            or attempt.get('head_branch') != controls.get('release_branch')
            or attempt.get('head_sha') != context['GITHUB_WORKFLOW_SHA']
            or attempt.get('event') != 'workflow_dispatch'
            or repository.get('id') != repository_id
            or repository.get('full_name') != controls.get('repository')):
        raise Refusal('workflow-mismatch', 'refused')
    prepare = _map(parsed['prepare-run'])
    sources = _list(candidate.get('sources'))
    if (not _positive(prepare.get('id'))
            or _map(prepare.get('repository')).get('id') != repository_id
            or _map(prepare.get('repository')).get('full_name') != controls['repository']
            or prepare.get('path') != controls.get('prepare_workflow')
            or prepare.get('head_branch') != controls.get('release_branch')
            or prepare.get('event') != 'workflow_dispatch' or prepare.get('status') != 'completed'
            or prepare.get('conclusion') != 'success' or not sources
            or any(_map(source).get('revision') != prepare.get('head_sha') for source in sources)):
        raise Refusal('prepare-run-mismatch', 'refused')
    if prepare.get('head_sha') != context['GITHUB_WORKFLOW_SHA']:
        raise Refusal('workflow-mismatch', 'refused')
    listing = _map(parsed['prepare-artifacts'])
    artifacts = _list(listing.get('artifacts'))
    matches = [artifact for artifact in artifacts if isinstance(artifact, dict)
               and artifact.get('digest') == captured['artifact-archive']
               and artifact.get('expired') is False and _positive(artifact.get('id'))
               and _map(artifact.get('workflow_run')).get('id') == prepare['id']
               and _map(artifact.get('workflow_run')).get('repository_id') == repository_id
               and _map(artifact.get('workflow_run')).get('head_branch')
               == controls['release_branch']
               and _map(artifact.get('workflow_run')).get('head_sha') == prepare['head_sha']]
    if (type(listing.get('total_count')) is not int or listing['total_count'] != len(artifacts)
            or len(matches) != 1):
        raise Refusal('artifact-digest-mismatch', 'refused')
    environment = _map(parsed['environment-settings'])
    if (approval_codes(controls, environment) or environment.get('name') != controls['environment']
            or not _positive(environment.get('id'))):
        raise Refusal('protection-changed', 'refused')
    marker = 'admission:' + digest
    approvals = _bound_approvals(controls, environment, parsed['approvals'], attempt, marker)
    digests = _component_digests(candidate)
    effects = []
    for effect in controls.get('effects', []):
        if (not admission.text(effect.get('id'))
                or effect.get('payload_component') not in digests
                or any(item['id'] == effect['id'] for item in effects)):
            raise Refusal('context-malformed', 'refused')
        effects.append({'id': effect['id'],
                        'payload_sha256': digests[effect['payload_component']]})
    binding = {
        'admission_sha256': digest, 'candidate_sha256': admitted['candidate']['sha256'],
        'target': admitted['target'], 'repository': controls['repository'],
        'repository_id': repository_id, 'workflow_ref': workflow_ref,
        'workflow_sha': context['GITHUB_WORKFLOW_SHA'],
        'run_id': run_id, 'run_attempt': run_attempt,
        'triggering_actor': context['GITHUB_TRIGGERING_ACTOR'], 'prepare_run_id': prepare['id'],
        'artifact_digest': captured['artifact-archive'], 'approvals': approvals,
        'approvals_response_sha256': admission.sha256(captured['approvals']),
        'bound_at': clock, 'marker': marker, 'effects': effects,
    }
    raw = _canonical(binding)
    decision = _canonical({'binding_sha256': admission.sha256(raw), 'binding': binding,
                           'approvals_response': parsed['approvals'], 'attempt_response': attempt})
    if len(raw) > MANIFEST_LIMIT or len(decision) > MANIFEST_LIMIT:
        raise Refusal('unreadable-input', 'error')
    handoff.parse_json(decision)
    if not args.check:
        _publish_binding(root, args.output, args.decision_output, args.admission, raw, decision)
    return {'status': 'bound', 'issues': []}


def _publish_binding(root: Path, output: str, decision_output: str, source: str,
                     raw: bytes, decision: bytes) -> None:
    """Preflight both confined destinations and roll back our first file on failure."""
    if output == decision_output:
        raise Refusal('unreadable-input', 'error')
    with handoff.output_directory(root, output, source) as (directory, name, recheck), \
            handoff.output_directory(root, decision_output, source) as (other, other_name, check):
        handoff.save_candidate(directory, name, raw, recheck,
                               handoff.write_candidate, handoff.publish_candidate)
        identity = os.stat(name, dir_fd=directory, follow_symlinks=False)
        try:
            handoff.save_candidate(other, other_name, decision, check,
                                   handoff.write_candidate, handoff.publish_candidate)
        except (OSError, Refusal):
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                os.unlink(name, dir_fd=directory)
            raise


def _component_digests(candidate: dict[str, Any]) -> dict[str, str]:
    """Resolve supported components to the artifact digests pinned by admission."""
    evidence = {item['id']: item['sha256'] for item in candidate['evidence']}
    return {item['id']: evidence[
                item['artifact' if item['kind'] == 'oci-image' else 'plan_bundle']]
            for item in candidate['components']}


def _time(value: Any) -> datetime:
    """Read timezone-aware provider ISO timestamps without accepting local time."""
    if not isinstance(value, str):
        raise ValueError('timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone required')
    return result


def _audit_key_prefix(controls: dict[str, Any], kind: str) -> str:
    """Return the object-key part of a bucket-qualified audit prefix; listings and keys use it."""
    key = _s3(controls['audit'][kind + '_prefix'])[2]
    if not key:
        raise ValueError('audit prefix is not bucket-qualified')
    return key


def _decision_key(controls: dict[str, Any], binding: dict[str, Any],
                  kind: str = 'decision') -> str:
    """Derive the exact audit object key from owner controls and bound run identity."""
    return (_audit_key_prefix(controls, kind) + controls['environment'] + '/'
            + str(binding['run_id']) + '-' + str(binding['run_attempt']) + '.json')


def _versions(controls: dict[str, Any], listing: Any) -> list[dict[str, Any]]:
    """Validate a complete saved page stream and keep noncurrent object versions.

    Ops versions may carry a `record` containing the separately captured body.
    Continuation markers must chain; each prefix stream starts with empty markers
    and ends with an untruncated page.
    """
    try:
        if not isinstance(listing, list) or not listing:
            raise ValueError('pages required')
        required = {_audit_key_prefix(controls, kind) + controls['environment'] + '/'
                    for kind in ('decision', 'ops')}
        covered = set()
        active_prefix = ''
        versions = []
        seen = set()
        expected_markers = ('', '')
        for index, page in enumerate(listing):
            if (not isinstance(page, dict) or type(page.get('IsTruncated')) is not bool
                    or not isinstance(page.get('Versions', []), list)
                    or not isinstance(page.get('DeleteMarkers', []), list)):
                raise ValueError('malformed page')
            prefix = page.get('Prefix')
            if (not isinstance(prefix, str) or prefix not in required
                    or (expected_markers != ('', '') and prefix != active_prefix)):
                raise ValueError('wrong prefix')
            active_prefix = prefix
            markers = (page.get('KeyMarker', ''), page.get('VersionIdMarker', ''))
            if markers != expected_markers:
                raise ValueError('missing page')
            expected_markers = ('', '')
            if page['IsTruncated']:
                if not all(admission.text(page.get(name))
                           for name in ('NextKeyMarker', 'NextVersionIdMarker')):
                    raise ValueError('missing continuation markers')
                expected_markers = (page['NextKeyMarker'], page['NextVersionIdMarker'])
            if page['IsTruncated'] and index + 1 == len(listing):
                raise ValueError('missing continuation')
            if not page['IsTruncated']:
                covered.add(prefix)
            for item in page.get('Versions', []) + page.get('DeleteMarkers', []):
                if (not isinstance(item, dict) or not admission.text(item.get('Key'))
                        or not item['Key'].startswith(prefix)
                        or not admission.text(item.get('VersionId'))
                        or type(item.get('IsLatest')) is not bool):
                    raise ValueError('malformed version')
                _time(item.get('LastModified'))
                identity = (item['Key'], item['VersionId'])
                if identity in seen:
                    raise ValueError('duplicate version')
                seen.add(identity)
            versions.extend(page.get('Versions', []))
        if covered != required:
            raise ValueError('missing history stream')
        return versions
    except (ValueError, TypeError, KeyError):
        raise Refusal('listing-incomplete', 'refused') from None


def _decision_versions(controls: dict[str, Any], listing: Any,
                       now: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select all decisions for this environment and those in the inclusive window."""
    versions = _versions(controls, listing)
    try:
        maximum, days = controls['max_executions'], controls['budget_window_days']
        if (type(maximum) is not int or not 1 <= maximum <= 100
                or type(days) is not int or not 1 <= days <= 365):
            raise ValueError('invalid bounds')
        prefix = _audit_key_prefix(controls, 'decision') + controls['environment'] + '/'
        clock = _time(now)
        decisions = [item for item in versions if item['Key'].startswith(prefix)]
        if any(not re.fullmatch(r'[1-9][0-9]*-[1-9][0-9]*\.json', item['Key'][len(prefix):])
               for item in decisions):
            raise ValueError('invalid decision identity')
        current = [item for item in decisions
                   if clock - timedelta(days=days) <= _time(item['LastModified']) <= clock]
        if any(_time(item['LastModified']) > clock for item in decisions):
            raise ValueError('future decision')
        return decisions, current
    except (KeyError, TypeError, ValueError):
        raise Refusal('listing-incomplete', 'refused') from None


def _terminal_ops(value: Any, run_id: Any, attempt: Any,
                  effects: list[dict[str, Any]]) -> bool:
    """Require a matching terminal record with operation evidence for each effect."""
    if not isinstance(value, dict):
        return False
    check_shape(value, 'ops')
    if (value.get('run_id') != run_id or value.get('run_attempt') != attempt
            or value.get('outcome') not in ('no-mutation', 'mutated', 'torn-down', 'failed')
            or not isinstance(value.get('operations'), list)):
        return False
    operations = value['operations']
    if value['outcome'] == 'no-mutation':
        return not operations
    return (len(operations) == len(effects)
            and {item.get('effect_id') for item in operations} == {item['id'] for item in effects}
            and all(admission.text(item.get('request_id'))
                    and admission.text(item.get('version_id'))
                    for item in operations))


def budget(args: Any, parsed: dict[str, Any]) -> dict[str, Any]:
    """Count every decision version before writing and require reconciled history."""
    controls = parsed['controls']
    decisions, current = _decision_versions(controls, parsed['listing'], args.now)
    if len(current) >= controls['max_executions']:
        raise Refusal('execution-limit', 'refused')
    versions = _versions(controls, parsed['listing'])
    for item in decisions:
        name = item['Key'].rsplit('/', 1)[-1].removesuffix('.json')
        run_id, attempt = (int(part) for part in name.split('-'))
        if run_id in controls.get('reconciled_runs', []):
            continue
        key = _decision_key(controls, {'run_id': run_id, 'run_attempt': attempt}, 'ops')
        if not any(version['Key'] == key and _terminal_ops(
                version.get('record'), run_id, attempt, controls.get('effects', []))
                   for version in versions):
            raise Refusal('prior-unreconciled', 'refused')
    return {'status': 'available', 'executions_used': len(current),
            'executions_remaining': controls['max_executions'] - len(current), 'issues': []}


def _audit_matches(parsed: dict[str, Any], captured: dict[str, Any]) -> bool:
    """Bind exact decision bytes and run, plus owner controls when supplied."""
    try:
        binding, decision, receipt = (
            parsed[name] for name in ('binding', 'decision', 'audit-receipt'))
        controls = parsed.get('controls')
        checksum = base64.b64decode(receipt['ChecksumSHA256'], validate=True)
        return (checksum == hashlib.sha256(captured['decision']).digest()
                and admission.text(receipt.get('Key'))
                and admission.text(receipt.get('VersionId'))
                and decision['binding_sha256'] == admission.sha256(captured['binding'])
                and decision['binding'] == binding
                and _map(decision.get('attempt_response')).get('id') == binding['run_id']
                and _map(decision.get('attempt_response')).get('run_attempt')
                == binding['run_attempt']
                and (controls is None or (
                    receipt['Key'] == _decision_key(controls, binding)
                    and binding['repository'] == controls['repository']
                    and binding['repository_id'] == controls['repository_id']
                    and binding['target']['environment'] == controls['environment'])))
    except (KeyError, TypeError, ValueError):
        return False


def _protected_head(parsed: dict[str, Any], now: str) -> bool:
    """Confirm this receipt's immutable version still retains its bytes."""
    try:
        head, receipt = parsed['audit-head'], parsed['audit-receipt']
        return bool(head['VersionId'] == receipt['VersionId']
                    and head['ObjectLockMode'] == 'COMPLIANCE'
                    and _time(head['ObjectLockRetainUntilDate']) > _time(now)
                    and _time(head['LastModified']) <= _time(now)
                    and head.get('ChecksumSHA256') == receipt['ChecksumSHA256'])
    except (KeyError, TypeError, ValueError):
        return False


def recheck(args: Any, root: Path, parsed: dict[str, Any],
            captured: dict[str, Any]) -> dict[str, Any]:
    """Re-evaluate live controls and every exact-byte binding before mutation."""
    if not _audit_matches(parsed, captured):
        raise Refusal('binding-unaudited', 'refused')
    if not _protected_head(parsed, args.now):
        raise Refusal('audit-unprotected', 'refused')
    controls, binding = parsed['controls'], parsed['binding']
    workflows = {}
    for name in ('prepare', 'deploy', 'deploy-job'):
        locator = controls[name.replace('-job', '_job') + '_workflow']
        raw = admission.read_manifest(root, args.workflows_root + '/' + locator)
        try:
            workflows[name] = read_workflow(raw)
        except Unparsed:
            workflows[name] = None
    report = evaluate_readiness(controls, parsed['live-snapshot'], workflows)
    if report['status'] != 'ready':
        codes = list(dict.fromkeys(code for row in report['controls'] if row['status'] != 'met'
                                   for code in row['codes']))
        # Audit failures have their own refusal; retain other live row failures too.
        audit_failed = any(row['control'] == 'audit' and row['status'] != 'met'
                           for row in report['controls'])
        return {'status': 'refused', 'issues': [
            {'code': 'live-readiness-blocked', 'codes': codes},
            *([{'code': 'audit-unprotected'}] if audit_failed else [])]}
    try:
        if admission.verify(args.admission, root=root, now=args.now)['status'] != 'current':
            raise Refusal('admission-stale', 'refused')
        admitted, raw = admission.read_record(root, args.admission)
        if (raw != captured['admission']
                or admission.sha256(raw)[7:] != binding['admission_sha256']
                or admitted['candidate']['sha256'] != binding['candidate_sha256']
                or admitted['target'] != binding['target']):
            raise Refusal('admission-stale', 'refused')
        candidate_raw = admission.read_manifest(root, admitted['candidate']['locator'])
        if admission.sha256(candidate_raw) != binding['candidate_sha256']:
            raise Refusal('admission-stale', 'refused')
        digests = _component_digests(handoff.parse_yaml(candidate_raw))
    except Refusal:
        raise Refusal('admission-stale', 'refused') from None
    payloads = dict(pair.split('=', 1) for pair in args.payload)
    bound = {item['id']: item['payload_sha256'] for item in binding['effects']}
    effects = controls['effects']
    if (len(payloads) != len(args.payload) or set(payloads) != {effect['id'] for effect in effects}
            or set(bound) != set(payloads) or len(bound) != len(binding['effects'])):
        raise Refusal('payload-mismatch', 'refused')
    for effect in effects:
        locator = payloads[effect['id']]
        digest = hash_archive(root, locator)
        size = sum(len(chunk) for chunk in admission.bounded_chunks(root, locator, ARCHIVE_LIMIT))
        if (digest != digests.get(effect['payload_component']) or digest != bound[effect['id']]
                or size > effect['max_payload_bytes']):
            raise Refusal('payload-mismatch', 'refused')
    identity = parsed['cloud-identity']
    role = os.environ.get(args.expect_role_arn_env, '')
    account = os.environ.get(args.expect_account_env, '')
    match = re.fullmatch(r'arn:aws:iam::([0-9]{12}):role/(.+)', role)
    session = re.fullmatch(r'arn:aws:sts::([0-9]{12}):assumed-role/([^/]+)/([^/]+)',
                           str(identity.get('Arn', '')))
    if (args.expect_role_arn_env != controls['cloud']['role_secret']
            or args.expect_account_env != controls['cloud']['account_secret']
            or role != parsed['live-snapshot']['iam_role']['Role']['Arn']
            or not match or not session or match[1] != account or session[1] != account
            or match[2].rsplit('/', 1)[-1] != controls['cloud']['role_name']
            or session[2] != controls['cloud']['role_name']
            or identity.get('Account') != account):
        raise Refusal('cloud-identity-mismatch', 'refused')
    _, current = _decision_versions(controls, parsed['audit-listing'], args.now)
    if not any(item['Key'] == parsed['audit-receipt']['Key']
               and item['VersionId'] == parsed['audit-receipt']['VersionId'] for item in current):
        raise Refusal('binding-unaudited', 'refused')
    if len(current) > controls['max_executions']:
        raise Refusal('execution-limit', 'refused')
    return {'status': 'current', 'issues': []}


def _effect_states(binding: dict[str, Any], controls: dict[str, Any],
                   observed: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Classify only unique observations matching this binding's payload and marker."""
    bound = {item['id']: item['payload_sha256'] for item in binding.get('effects', [])}
    result = []
    for effect in controls['effects']:
        matches = [item for item in observed if item.get('id') == effect['id']]
        state = 'unknown'
        if len(matches) == 1 and effect['id'] in bound:
            observation = matches[0]
            if observation.get('state') == 'absent':
                state = 'absent'
            elif (observation.get('state') == 'present'
                  and observation.get('digest') == bound[effect['id']]
                  and observation.get('marker') == binding['marker']):
                state = 'applied'
        result.append({'id': effect['id'], 'state': state})
    return result


def _jobs_unstarted(response: Any, binding: dict[str, Any]) -> bool:
    """Require complete same-attempt jobs and explicit unstarted mutation evidence."""
    if not isinstance(response, dict):
        return False
    jobs = response.get('jobs')
    if (not isinstance(jobs, list) or not jobs
            or type(response.get('total_count')) is not int
            or response['total_count'] != len(jobs)):
        return False
    mutations = []
    for job in jobs:
        if (not isinstance(job, dict)
                or type(job.get('run_id')) is not int
                or type(job.get('run_attempt')) is not int
                or job['run_id'] != binding.get('run_id')
                or job['run_attempt'] != binding.get('run_attempt')
                or not isinstance(job.get('steps'), list)):
            return False
        for step in job['steps']:
            if not isinstance(step, dict) or not isinstance(step.get('name'), str):
                return False
            if step['name'].startswith('mutate-'):
                mutations.append(step)
    return bool(mutations) and all(
        (step.get('status') == 'queued' and step.get('conclusion') is None)
        or (step.get('status') == 'completed' and step.get('conclusion') == 'skipped')
        for step in mutations)


def reconcile(args: Any, parsed: dict[str, Any]) -> dict[str, Any]:
    """Report observed effects; permit retries only with terminal run and ops evidence."""
    binding, controls, run = (parsed[name] for name in ('binding', 'controls', 'run'))
    _, current = _decision_versions(
        controls, parsed['audit-listing'], admission.clock_time(None))
    states = _effect_states(binding, controls, parsed['observed'])
    report: dict[str, Any] = {'status': 'pause', 'effects': states, 'issues': []}
    if (run.get('id') != binding.get('run_id')
            or run.get('run_attempt') != binding.get('run_attempt')):
        report['issues'] = [{'code': 'run-mismatch'}]
    elif run.get('status') != 'completed':
        report['issues'] = [{'code': 'run-not-terminal'}]
    elif states and all(item['state'] == 'applied' for item in states):
        report['status'] = 'proceed-to-observe'
    elif not states or any(item['state'] != 'absent' for item in states):
        report['issues'] = [{'code': 'effect-unknown'}]
    else:
        if len(current) >= controls['max_executions']:
            report['issues'] = [{'code': 'execution-limit'}]
        else:
            no_mutation = _jobs_unstarted(parsed['jobs'], binding)
            if no_mutation or _terminal_ops(parsed.get('ops'), binding['run_id'],
                                             binding['run_attempt'], controls['effects']):
                report['status'] = 'retry-allowed'
            else:
                report['issues'] = [{'code': 'ops-missing'}]
    return report


def summary(args: Any, parsed: dict[str, Any], captured: dict[str, Any]) -> dict[str, Any]:
    """Confirm immutable audit bytes and return a non-authorizing completion receipt."""
    def unconfirmed() -> dict[str, Any]:
        """Return a safe, stable audit refusal without copying supplied diagnostics."""
        return {'status': 'audit-unconfirmed', 'issues': [{'code': 'audit-unconfirmed'}]}
    if (not _audit_matches(parsed, captured) or not _protected_head(parsed, args.now)
            or captured.get('audit-readback') != captured['decision']):
        return unconfirmed()
    binding, ops = (parsed[name] for name in ('binding', 'ops'))
    controls = parsed.get('controls', binding)
    states = _effect_states(binding, controls, parsed['observed'])
    try:
        for state in states:
            if state['state'] == 'applied':
                observation = next(item for item in parsed['observed']
                                   if item['id'] == state['id'])
                if (_time(parsed['audit-head']['LastModified'])
                        > _time(observation.get('write_time'))):
                    return unconfirmed()
    except (ValueError, TypeError):
        return unconfirmed()
    if not _terminal_ops(ops, binding['run_id'], binding['run_attempt'], controls['effects']):
        return unconfirmed()
    return {'status': 'audited', 'run_id': binding['run_id'],
            'run_attempt': binding['run_attempt'],
            'approval_reviewer_ids': [item['id'] for item in binding['approvals']],
            'audit_key': parsed['audit-receipt']['Key'],
            'audit_version_id': parsed['audit-receipt']['VersionId'],
            'operation_ids': [item['request_id'] for item in ops['operations']],
            'achieved_stage': ('deployed' if ops['outcome'] in ('mutated', 'torn-down')
                               else 'pre-deploy'),
            'cleanup_state': 'torn-down' if ops['outcome'] == 'torn-down' else 'retained',
            'issues': []}


def _output_path(root: Path, locator: str) -> None:
    """Validate a future output without creating a file in the command skeleton."""
    if (not locator or locator.startswith('/') or '\\' in locator
            or re.match(r'^[A-Za-z]:', locator)
            or any(part in ('', '.', '..') for part in locator.split('/'))):
        raise Refusal('unreadable-input', 'error')
    target = root / locator
    if target.exists() or target.is_symlink():
        admission.read_manifest(root, locator)
    else:
        canonical = root.resolve(strict=True)
        if not target.resolve().is_relative_to(canonical):
            raise Refusal('unreadable-input', 'error')
        current = canonical
        for part in locator.split('/')[:-1]:
            current = current / part
            if current.is_symlink() or not current.is_dir():
                raise Refusal('unreadable-input', 'error')


def main(argv: list[str] | None = None) -> int:
    """Validate confined inputs and evaluate the selected offline command."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = handoff.SafeParser(add_help=False, allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, inputs in INPUTS.items():
        command = commands.add_parser(name, add_help=False, allow_abbrev=False)
        command.add_argument('--root', required=True)
        for flag in inputs:
            command.add_argument('--' + flag, required=True)
        if name == 'summary':
            command.add_argument('--controls')
        if name == 'reconcile':
            command.add_argument('--ops')
        if name == 'bind':
            command.add_argument('--expect-admission-sha256', required=True)
            command.add_argument('--output', required=True)
            command.add_argument('--decision-output', required=True)
            command.add_argument('--check', action='store_true')
        if name == 'recheck':
            command.add_argument('--workflows-root', required=True)
            command.add_argument('--payload', action='append', default=[])
            command.add_argument('--expect-role-arn-env', required=True)
            command.add_argument('--expect-account-env', required=True)
        if name in ('budget', 'recheck', 'summary'):
            command.add_argument('--now', required=True)
    try:
        args = parser.parse_args(argv)
        root = Path(args.root)
        # Read every locator before semantic validation, so unsafe later inputs fail too.
        captured = {}
        optional_ops = ['ops'] if args.command == 'reconcile' and args.ops else []
        optional_controls = ['controls'] if args.command == 'summary' and args.controls else []
        for flag in (*INPUTS[args.command], *optional_ops, *optional_controls):
            locator = getattr(args, flag.replace('-', '_'))
            if flag == 'artifact-archive':
                captured[flag] = hash_archive(root, locator)
            else:
                try:
                    captured[flag] = admission.read_manifest(root, locator)
                except (Refusal, OSError):
                    if (args.command == 'summary' and flag == 'audit-readback'
                            and not (root / locator).exists()
                            and not (root / locator).is_symlink()):
                        _output_path(root, locator)
                        captured[flag] = None
                    else:
                        raise
        if args.command == 'bind':
            for locator in (args.output, args.decision_output):
                _output_path(root, locator)
        if args.command == 'recheck':
            # Workflow paths inside this directory are controls-owned, not yet evaluated.
            _output_path(root, args.workflows_root + '/.workflow-check')
            for pair in args.payload:
                effect, separator, locator = pair.partition('=')
                if not effect or not separator:
                    raise Refusal('usage', 'error')
                hash_archive(root, locator)
        parsed = {}
        for flag, raw in captured.items():
            if flag == 'artifact-archive' or flag == 'audit-readback':
                continue
            if flag.endswith('workflow'):
                try:
                    parsed[flag] = read_workflow(raw)
                except Unparsed:
                    parsed[flag] = None
            else:
                value = handoff.parse_json(raw)
                check_shape(value, flag)
                parsed[flag] = value
        if args.command == 'readiness':
            report = evaluate_readiness(parsed['controls'], parsed['snapshot'], {
                name: parsed[name + '-workflow'] for name in ('prepare', 'deploy', 'deploy-job')
            })
            print(json.dumps(report, separators=(',', ':')))
            return 0 if report['status'] == 'ready' else 1
        if args.command == 'bind':
            try:
                report = bind(args, root, parsed, captured)
            except Refusal as exc:
                if exc.status != 'refused':
                    raise
                report = {'status': 'refused', 'issues': [{'code': exc.code}]}
            print(json.dumps(report, separators=(',', ':')))
            return 0 if report['status'] == 'bound' else 1
        if args.command in ('budget', 'recheck', 'reconcile', 'summary'):
            try:
                if args.command == 'budget':
                    report = budget(args, parsed)
                elif args.command == 'recheck':
                    report = recheck(args, root, parsed, captured)
                elif args.command == 'reconcile':
                    report = reconcile(args, parsed)
                else:
                    report = summary(args, parsed, captured)
            except Refusal as exc:
                if exc.status != 'refused':
                    raise
                report = {'status': 'refused', 'issues': [{'code': exc.code}]}
            print(json.dumps(report, separators=(',', ':')))
            return 1 if report['status'] in ('refused', 'audit-unconfirmed') else 0
        code = 'usage'
    except Refusal as exc:
        code = 'usage' if exc.code == 'usage' else 'unreadable-input'
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError):
        code = 'unreadable-input'
    print(json.dumps({'status': 'error', 'issues': [{'code': code}]}, separators=(',', ':')))
    return 2


if __name__ == '__main__':
    sys.exit(main())
