// Versioned frontend checks + immutable build snapshot. Never executes model TEST.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, readdirSync, copyFileSync, existsSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'apps/web'); const base = path.join(root, 'artifacts/manifests/phase33');
const name = process.argv[2]; if (!name || !/^[a-z0-9_-]+$/.test(name)) throw new Error('Choose a new evidence name');
const digest = file => createHash('sha256').update(readFileSync(file)).digest('hex');
const relative = file => path.relative(root, file).split(path.sep).join('/');
const ref = file => ({ path: relative(file), sha256: digest(file), size_bytes: readFileSync(file).length });
function files(folder) { return readdirSync(folder, { withFileTypes: true }).flatMap(entry => entry.isDirectory() ? files(path.join(folder, entry.name)) : [path.join(folder, entry.name)]); }
function once(file, value) { writeFileSync(file, JSON.stringify(value, null, 2) + '\n', { flag: 'wx' }); }
const inputs = [...files(path.join(web, 'src')), ...files(path.join(web, 'tests/v3')),
  ...['package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts', 'vitest.v3.config.ts', 'playwright.v3.config.ts', 'eslint.config.mjs', 'index.html'].map(n => path.join(web, n))];
const source = inputs.sort().map(ref);
const sourceHash = createHash('sha256').update(JSON.stringify(source)).digest('hex');
if (existsSync(path.join(base, name + '_checks.json'))) throw new Error('Evidence exists; do not overwrite');
for (const file of inputs.filter(file => /src[\\/]v3/.test(file) && !/\.test\./.test(file))) {
 const text = readFileSync(file, 'utf8');
 if (/sk-[A-Za-z0-9]{24,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(text)) throw new Error('Potential secret pattern in scoped active UI source');
}
const npm = path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js');
const env = { ...process.env, PHASE33_EVIDENCE: name + '_unit', DEBUG_PRINT_LIMIT: '400',
  npm_config_cache: path.join(root, '.local/npm-cache') };
const records = [];
for (const action of ['lint', 'type-check', 'test:coverage', 'test:legacy', 'build']) {
 const result = spawnSync(process.execPath, [npm, 'run', action], { cwd: web, env, encoding: 'utf8', maxBuffer: 16 * 1024 ** 2, windowsHide: true });
 const log = path.join(base, name + '_' + action.replaceAll(':', '_') + '.log');
 writeFileSync(log, result.stdout + result.stderr, { flag: 'wx' });
 records.push({ action, status: result.status, log: ref(log) });
 if (result.status !== 0) { console.error(JSON.stringify({ action, status: result.status, log: relative(log) })); process.exit(1); }
 console.log(action + ' PASS');
}
const audit = spawnSync(process.execPath, [npm, 'audit', '--json', '--registry=https://registry.npmjs.org'], { cwd: web, env, encoding: 'utf8', maxBuffer: 16 * 1024 ** 2, windowsHide: true });
let advisory; try { advisory = JSON.parse(audit.stdout); } catch { throw new Error('npm audit unavailable; not a clean security result'); }
const auditFile = path.join(base, name + '_npm_audit.json'); once(auditFile, advisory);
if (audit.status !== 0 || advisory.metadata?.vulnerabilities?.total !== 0) throw new Error('Dependency audit not clean; inspect saved evidence, no auto-fix');
const destination = path.join(root, 'dist/phase33', 'web-preview-' + name);
if (existsSync(destination)) throw new Error('Immutable preview exists');
const output = [];
for (const file of files(path.join(web, 'dist'))) {
 const target = path.join(destination, path.relative(path.join(web, 'dist'), file));
 mkdirSync(path.dirname(target), { recursive: true }); copyFileSync(file, target); output.push(ref(target));
}
for (const row of source) if (digest(path.join(root, row.path)) !== row.sha256) throw new Error('Source changed during checks');
const lock = JSON.parse(readFileSync(path.join(web, 'package-lock.json')));
const versions = Object.fromEntries(['react', 'react-dom', 'react-router-dom', 'vite', 'vitest', '@playwright/test', 'eslint', 'typescript'].map(key => [key, lock.packages['node_modules/' + key].version]));
once(path.join(base, name + '_checks.json'), { status: 'PASS', source, source_sha256: sourceHash,
 node: process.version, versions, records, build_outputs: output, npm_audit: ref(auditFile),
 scoped_secret_patterns: 0, secret_scan_scope: 'Active V3 UI only, not Git history',
 preview_api_origin: process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:5000',
 cloud_deployed: false, historical_test_evaluation_executed: false, models_retrained: 0 });
console.log(JSON.stringify({ status: 'PASS', source_sha256: sourceHash, build_files: output.length }));
