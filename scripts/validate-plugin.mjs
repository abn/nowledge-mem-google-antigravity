import { readFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = path.join(pluginRoot, 'plugin.json');
const mcpConfigPath = path.join(pluginRoot, 'mcp_config.json');
const packageJsonPath = path.join(pluginRoot, 'package.json');

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

async function readJson(filePath) {
  const text = await readFile(filePath, 'utf8');
  return JSON.parse(text);
}

function assertString(value, label) {
  if (typeof value !== 'string' || value.trim() === '') {
    fail(`${label} must be a non-empty string`);
  }
}

async function main() {
  const manifest = await readJson(manifestPath);
  const mcpConfig = await readJson(mcpConfigPath);
  const packageJson = await readJson(packageJsonPath);
  const pluginDirName = path.basename(pluginRoot);

  assertString(manifest.name, 'manifest.name');
  assertString(manifest.version, 'manifest.version');
  assertString(manifest.description, 'manifest.description');

  if (manifest.name !== pluginDirName && pluginDirName !== 'nmem' && pluginDirName !== 'nowledge-mem') {
    fail(`manifest.name (${manifest.name}) must match directory name (or be "nmem" or "nowledge-mem"), but got "${pluginDirName}"`);
  }

  if (manifest.version !== packageJson.version) {
    fail(`manifest.version (${manifest.version}) must match package.json version (${packageJson.version})`);
  }

  const server = mcpConfig.mcpServers?.['nowledge-mem'];
  if (!server || typeof server !== 'object') {
    fail('mcp_config.json must define mcpServers.nowledge-mem');
  }
  if (server.serverUrl !== 'http://127.0.0.1:14242/mcp/') {
    fail('mcp_config.json nowledge-mem.serverUrl must point to the local Mem MCP endpoint');
  }
  if (server.headers?.APP !== 'Google Antigravity') {
    fail('mcp_config.json nowledge-mem.headers.APP must be "Google Antigravity"');
  }

  const requiredPaths = [
    'plugin.json',
    'mcp_config.json',
    'hooks.json',
    'package.json',
    'README.md',
    'CHANGELOG.md',
    'RELEASING.md',
    'rules/nowledge-mem.md',
    'hooks/session-start.py',
    'hooks/session-end.py',
    'hooks/nmem-gate.py',
    'hooks/nmem_status.py',
    'skills/nmem-read-working-memory/SKILL.md',
    'skills/nmem-search-memory/SKILL.md',
    'skills/nmem-distill-memory/SKILL.md',
    'skills/nmem-save-thread/SKILL.md',
    'skills/nmem-save-handoff/SKILL.md',
    'skills/nmem-status/SKILL.md',
    'skills/nmem-fs-explorer/SKILL.md',
    'skills/nmem-manage-skills/SKILL.md',
    'skills/nmem-manage-skills/scripts/manage_skills.py',
    'skills/nmem-propose-skill/SKILL.md',
    'skills/nmem-load-skill/SKILL.md',
    'skills/nmem-load-skill/scripts/load_skill.py',
    'scripts/validate-plugin.mjs',
    'scripts/package-plugin.mjs',
    'tests/test_hooks.py',
    `release-notes/${manifest.version}.md`
  ];

  for (const relPath of requiredPaths) {
    const absPath = path.join(pluginRoot, relPath);
    try {
      const text = await readFile(absPath, 'utf8');
      if (text.trim() === '') {
        fail(`${relPath} must not be empty`);
      }

      if (relPath === 'hooks.json') {
        const hooksConfig = JSON.parse(text);
        if (
          !hooksConfig ||
          typeof hooksConfig !== 'object' ||
          typeof hooksConfig['nowledge-mem-hooks'] !== 'object' ||
          hooksConfig['nowledge-mem-hooks'] === null ||
          Array.isArray(hooksConfig['nowledge-mem-hooks'])
        ) {
          fail('hooks.json must contain a top-level "nowledge-mem-hooks" object');
        }
      }
    } catch (error) {
      if (error instanceof SyntaxError) {
        fail(`${relPath} must contain valid JSON`);
      }
      fail(`missing required file: ${relPath}`);
    }
  }

  console.log('Validated Google Antigravity plugin manifest, config files, and required release files.');

  console.log('Running hooks unit test suite...');
  const testProc = spawnSync('python3', ['-m', 'unittest', 'discover', '-s', 'tests'], {
    cwd: pluginRoot,
    stdio: 'inherit'
  });
  if (testProc.status !== 0) {
    const testProcFallback = spawnSync('python', ['-m', 'unittest', 'discover', '-s', 'tests'], {
      cwd: pluginRoot,
      stdio: 'inherit'
    });
    if (testProcFallback.status !== 0) {
      fail('Hooks unit tests failed.');
    }
  }
  console.log('All hooks unit tests passed.');
}

await main();
