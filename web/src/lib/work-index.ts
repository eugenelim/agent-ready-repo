import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

export interface WorkIndexFinding {
  readonly code: string;
  readonly nextAction: string;
}

export interface WorkIndexItem {
  readonly path: string;
  readonly summary: string;
  readonly dispatchable: boolean;
  readonly findings: readonly WorkIndexFinding[];
}

export interface WorkIndexInitiative {
  readonly slug: string;
  readonly name: string;
  readonly milestone: string;
  readonly active: readonly WorkIndexItem[];
  readonly ready: readonly WorkIndexItem[];
  readonly attention: readonly WorkIndexItem[];
}

export interface WorkIndexProjection {
  readonly schemaVersion: 1;
  readonly counts: Readonly<Record<WorkIndexCount, number>>;
  readonly initiatives: readonly WorkIndexInitiative[];
  readonly briefs: readonly { path: string; initiative: string }[];
  readonly shaping: readonly {
    slug: string;
    type: string;
    initiative: string;
    status?: string;
  }[];
  readonly backlog: readonly { slug?: string; path?: string; summary?: string; label?: string }[];
}

export type WorkIndexCount =
  | 'active'
  | 'ready'
  | 'attention'
  | 'briefs'
  | 'shaping'
  | 'backlog';

const countKeys: readonly WorkIndexCount[] = [
  'active',
  'ready',
  'attention',
  'briefs',
  'shaping',
  'backlog',
];

const safeExporterCode = /^work-index export failed: ([a-z0-9-]{1,96})$/;

type ExporterRunner = (
  file: string,
  args: readonly string[],
  options: {
    readonly cwd: string;
    readonly encoding: 'utf8';
    readonly maxBuffer: number;
    readonly timeout: number;
    readonly stdio: readonly ['ignore', 'pipe', 'pipe'];
  }
) => string;

class WorkIndexBuildError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'WorkIndexBuildError';
    this.stack = message;
  }
}

function safeExporterDiagnostic(error: unknown): string | undefined {
  if (typeof error !== 'object' || error === null || !('stderr' in error)) return undefined;
  const stderr = (error as { stderr?: unknown }).stderr;
  let diagnostic: string;
  if (typeof stderr === 'string') diagnostic = stderr;
  if (stderr instanceof Uint8Array) {
    if (stderr.byteLength > 1024) return undefined;
    diagnostic = Buffer.from(stderr).toString('utf8');
  } else if (typeof stderr !== 'string') {
    return undefined;
  }
  if (diagnostic.length > 1024) return undefined;
  return safeExporterCode.exec(diagnostic.trim())?.[1];
}

function abortBuild(error?: unknown): never {
  const detail = safeExporterDiagnostic(error) ?? 'canonical-status-unavailable';
  throw new WorkIndexBuildError(`Work-index build failed: ${detail}.`);
}

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('Work-index projection is malformed.');
  }
  return value as Record<string, unknown>;
}

function array(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error('Work-index projection is malformed.');
  return value;
}

function text(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Work-index projection is malformed.');
  return value;
}

function flag(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new Error('Work-index projection is malformed.');
  return value;
}

function optionalText(value: unknown): string | undefined {
  return value === undefined ? undefined : text(value);
}

function finding(value: unknown): WorkIndexFinding {
  const item = record(value);
  return {
    code: text(item.code),
    nextAction: text(item.nextAction),
  };
}

function workItem(value: unknown): WorkIndexItem {
  const item = record(value);
  return {
    path: text(item.path),
    summary: text(item.summary),
    dispatchable: flag(item.dispatchable),
    findings: array(item.findings).map(finding),
  };
}

/** Validate the small UI projection independently of the Python adapter. */
export function validateWorkIndexProjection(value: unknown): WorkIndexProjection {
  const projection = record(value);
  if (projection.schemaVersion !== 1) {
    throw new Error('Work-index projection uses an unsupported schema version.');
  }
  const rawCounts = record(projection.counts);
  const counts = Object.fromEntries(countKeys.map(key => {
    const count = rawCounts[key];
    if (!Number.isSafeInteger(count) || (count as number) < 0) {
      throw new Error('Work-index projection is malformed.');
    }
    return [key, count as number];
  })) as Record<WorkIndexCount, number>;

  return {
    schemaVersion: 1,
    counts,
    initiatives: array(projection.initiatives).map(value => {
      const initiative = record(value);
      return {
        slug: text(initiative.slug),
        name: text(initiative.name),
        milestone: text(initiative.milestone),
        active: array(initiative.active).map(workItem),
        ready: array(initiative.ready).map(workItem),
        attention: array(initiative.attention).map(workItem),
      };
    }),
    briefs: array(projection.briefs).map(value => {
      const brief = record(value);
      return { path: text(brief.path), initiative: text(brief.initiative) };
    }),
    shaping: array(projection.shaping).map(value => {
      const item = record(value);
      return {
        slug: text(item.slug),
        type: text(item.type),
        initiative: text(item.initiative),
        status: optionalText(item.status),
      };
    }),
    backlog: array(projection.backlog).map(value => {
      const item = record(value);
      const result = {
        slug: optionalText(item.slug),
        path: optionalText(item.path),
        summary: optionalText(item.summary),
        label: optionalText(item.label),
      };
      if (!result.slug && !result.path && !result.summary && !result.label) {
        throw new Error('Work-index projection is malformed.');
      }
      return result;
    }),
  };
}

function normalizeExporterProjection(value: unknown): unknown {
  const projection = record(value);
  return {
    schemaVersion: projection.schema_version,
    counts: projection.counts,
    initiatives: array(projection.initiatives).map(value => {
      const initiative = record(value);
      const normalizeItems = (items: unknown) => array(items).map(value => {
        const item = record(value);
        return {
          path: item.path,
          summary: item.summary,
          dispatchable: item.dispatchable,
          findings: array(item.findings).map(value => {
            const rawFinding = record(value);
            return { code: rawFinding.code, nextAction: rawFinding.next_action };
          }),
        };
      });
      return {
        slug: initiative.slug,
        name: initiative.name,
        milestone: initiative.milestone,
        active: normalizeItems(initiative.active),
        ready: normalizeItems(initiative.ready),
        attention: normalizeItems(initiative.attention),
      };
    }),
    briefs: projection.briefs,
    shaping: projection.shaping,
    backlog: projection.backlog,
  };
}

/** Run the confined build-time exporter and return validated page data. */
export function loadWorkIndex(runExporter: ExporterRunner = execFileSync): WorkIndexProjection {
  const repoRoot = resolve(process.cwd(), '..');
  const exporter = resolve(repoRoot, 'tools/export_work_index.py');
  let raw: string;
  try {
    raw = runExporter('python3', [exporter], {
      cwd: repoRoot,
      encoding: 'utf8',
      maxBuffer: 5 * 1024 * 1024,
      // The exporter owns the 20-second canonical-status deadline. Leave room
      // here for cold Python startup and its bounded process/pipe cleanup.
      timeout: 60_000,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (error) {
    return abortBuild(error);
  }

  try {
    return validateWorkIndexProjection(normalizeExporterProjection(JSON.parse(raw)));
  } catch {
    return abortBuild();
  }
}
