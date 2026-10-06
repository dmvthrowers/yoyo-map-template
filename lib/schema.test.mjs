// Guards the database migrations against loosening privacy by accident: row level security on
// every table, no browser writes, no wide-open policies. Run: pnpm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';

const dir = new URL('../supabase/migrations/', import.meta.url);
const files = readdirSync(dir).filter((f) => f.endsWith('.sql')).sort();
const sql = files.map((f) => readFileSync(new URL(f, dir), 'utf8')).join('\n');
// Comments out, so notes in the SQL can't trip the checks.
const code = sql.replace(/--[^\n]*/g, '');

test('migration files are numbered, ordered and forward-only', () => {
  assert.ok(files.length > 0);
  for (const f of files) assert.match(f, /^\d{14}_\d{4}_[a-z0-9_]+\.sql$/, f);
  assert.deepEqual(files, [...files].sort());
});

test('every table in public has row level security enabled', () => {
  const tables = [...code.matchAll(/create table (?:if not exists )?public\.(\w+)/gi)].map((m) => m[1]);
  assert.ok(tables.length >= 10);
  for (const t of tables) {
    assert.match(code, new RegExp(`alter table public\\.${t}\\s+enable row level security`, 'i'), `${t} has no RLS`);
  }
});

test('browsers never get write access', () => {
  const grants = [...code.matchAll(/grant\s+([^;]*?)\s+on\s+[^;]*?\s+to\s+([^;]*);/gis)];
  for (const [, privs, roles] of grants) {
    if (/\b(anon|authenticated)\b/i.test(roles)) {
      assert.doesNotMatch(privs, /\b(insert|update|delete|truncate|all)\b/i, `browser grant: ${privs} to ${roles}`);
    }
  }
});

test('no policy lets browsers write, and open "using (true)" policies are read-only', () => {
  const policies = [...code.matchAll(/create policy\s+("[^"]+"|\w+)\s+on\s+public\.(\w+)([^;]*);/gis)];
  assert.ok(policies.length > 5);
  for (const [, name, table, rest] of policies) {
    if (/for\s+(insert|update|delete|all)\b/i.test(rest) && !/restrictive/i.test(rest)) {
      assert.fail(`policy ${name} on ${table} allows writes`);
    }
    if (/using\s*\(\s*true\s*\)/i.test(rest)) {
      assert.match(rest, /for\s+select/i, `policy ${name} on ${table} is open but not select-only`);
    }
  }
});

test('private tables have no browser policy or grant', () => {
  for (const t of ['parent_consents', 'verification_tokens', 'reports', 'audit_log', 'email_queue', 'email_send_log', 'email_daily_usage', 'geocode_cache']) {
    assert.doesNotMatch(code, new RegExp(`grant[^;]*on\\s+public\\.${t}\\b[^;]*to[^;]*\\b(anon|authenticated)\\b`, 'is'), `${t} granted to browsers`);
    assert.doesNotMatch(code, new RegExp(`create policy[^;]*on\\s+public\\.${t}\\s+(?!as restrictive)[^;]*to\\s+(anon|authenticated)`, 'is'), `${t} has a browser policy`);
  }
});

test('the map view runs with the caller\'s rights', () => {
  assert.match(code, /create view public\.map_entries with \(security_invoker = on\)/i);
});
