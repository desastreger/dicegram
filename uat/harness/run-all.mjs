// Run every spec in specs/ and print one summary table.
//
//   node run-all.mjs                 # all specs
//   node run-all.mjs layout typing   # only specs matching these substrings
//   HEADED=1 node run-all.mjs        # watch the browser work
//
// Exit code is the number of failed checks, so CI can gate on it.

import { readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.DICEGRAM_BASE ?? 'http://localhost:5173';

// Fail fast with a useful message rather than 6 identical timeouts.
const probe = await fetch(BASE).catch(() => null);
if (!probe?.ok) {
  console.error(`\x1b[31m✗\x1b[0m ${BASE} is not responding — start it with scripts/dev-up`);
  process.exit(1);
}

const filters = process.argv.slice(2);
const specs = readdirSync(join(HERE, 'specs'))
  .filter((f) => f.endsWith('.mjs'))
  .filter((f) => !filters.length || filters.some((s) => f.includes(s)))
  .sort();

if (!specs.length) {
  console.error(`no specs matched ${filters.join(', ')}`);
  process.exit(1);
}

const run = (file) =>
  new Promise((resolve) => {
    const p = spawn(process.execPath, [join(HERE, 'specs', file)], {
      stdio: ['ignore', 'inherit', 'inherit'],
      env: process.env,
    });
    p.on('close', (code) => resolve({ file, code: code ?? 1 }));
  });

const results = [];
for (const file of specs) results.push(await run(file));

const pad = Math.max(...results.map((r) => r.file.length));
console.log(`\n\x1b[1m${'─'.repeat(pad + 14)}\x1b[0m`);
for (const { file, code } of results) {
  const label = code === 0 ? '\x1b[32mPASS\x1b[0m' : `\x1b[31mFAIL(${code})\x1b[0m`;
  console.log(`${file.padEnd(pad)}  ${label}`);
}
const failed = results.filter((r) => r.code !== 0);
console.log(`\x1b[1m${'─'.repeat(pad + 14)}\x1b[0m`);
console.log(`${results.length - failed.length}/${results.length} specs green`);
console.log(`screenshots → uat/harness/shots/`);

process.exit(failed.length);
