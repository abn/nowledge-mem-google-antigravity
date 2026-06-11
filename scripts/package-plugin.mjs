import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const distDir = path.join(pluginRoot, 'dist');
const archiveName = 'nowledge-mem-google-antigravity.tar.gz';
const archivePath = path.join(distDir, archiveName);
const stageDir = path.join(distDir, 'release-root');
const filesToShip = [
  'plugin.json',
  'mcp_config.json',
  'hooks.json',
  'package.json',
  'README.md',
  'CHANGELOG.md',
  'rules',
  'skills',
  'hooks'
];
const requiredArchiveEntries = new Set([
  './plugin.json',
  './mcp_config.json',
  './hooks.json',
  './package.json',
  './README.md',
  './CHANGELOG.md',
  './rules/nowledge-mem.md',
  './hooks/session-start.py',
  './hooks/session-end.py',
  './hooks/nmem-gate.py',
  './skills/nmem-read-working-memory/SKILL.md',
  './skills/nmem-search-memory/SKILL.md',
  './skills/nmem-distill-memory/SKILL.md',
  './skills/nmem-save-thread/SKILL.md',
  './skills/nmem-save-handoff/SKILL.md'
]);

function run(command, args, cwd = pluginRoot, options = {}) {
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', ...options });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  return result;
}

async function fileSha256(filePath) {
  const contents = await readFile(filePath);
  return createHash('sha256').update(contents).digest('hex');
}

function verifyArchive(filePath) {
  const result = spawnSync('tar', ['-tzf', filePath], {
    cwd: pluginRoot,
    encoding: 'utf8'
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }

  const rawEntries = result.stdout
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  const entries = new Set(
    rawEntries.map((line) => {
      if (line === '.') return './';
      return line.startsWith('./') ? line : `./${line}`;
    })
  );

  for (const entry of rawEntries) {
    const normalized = entry.startsWith('./') ? entry.slice(2) : entry;
    if (normalized === '._.' || normalized.startsWith('._') || normalized.includes('/._')) {
      console.error(`ERROR: release archive contains macOS metadata entry ${entry}`);
      process.exit(1);
    }
  }

  for (const requiredEntry of requiredArchiveEntries) {
    if (!entries.has(requiredEntry)) {
      console.error(`ERROR: release archive is missing ${requiredEntry}`);
      process.exit(1);
    }
  }
}

async function main() {
  run('node', ['scripts/validate-plugin.mjs']);

  await rm(distDir, { recursive: true, force: true });
  await mkdir(stageDir, { recursive: true });

  for (const relPath of filesToShip) {
    await cp(path.join(pluginRoot, relPath), path.join(stageDir, relPath), {
      recursive: true,
      force: true
    });
  }

  run('tar', ['-czf', archivePath, '-C', stageDir, '.'], pluginRoot, {
    env: {
      ...process.env,
      COPYFILE_DISABLE: '1'
    }
  });
  verifyArchive(archivePath);

  const checksum = await fileSha256(archivePath);
  await writeFile(
    path.join(distDir, `${archiveName}.sha256`),
    `${checksum}  ${archiveName}\n`,
    'utf8'
  );

  console.log(`Created ${archivePath}`);
  console.log(`Created ${path.join(distDir, `${archiveName}.sha256`)}`);
}

await main();
