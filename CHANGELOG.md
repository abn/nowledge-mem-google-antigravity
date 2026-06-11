# Changelog

All notable changes to the Nowledge Mem Google Antigravity plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-12

### Added
- Initial release of the `nowledge-mem-google-antigravity` plugin.
- Added `plugin.json`, `mcp_config.json`, and `hooks.json` mapping for Google Antigravity.
- Ported memory rules to `rules/nowledge-mem.md`.
- Implemented `PreInvocation` hook in `hooks/session-start.mjs` to inject Context Bundle / Working Memory startup briefings.
- Implemented `Stop` hook in `hooks/session-end.mjs` to extract conversation logs from `transcript.jsonl` and sync them into `nmem`.
- Implemented validation and packaging scripts (`scripts/validate-plugin.mjs`, `scripts/package-plugin.mjs`).
- Ported the 5 core memory skills: `distill-memory`, `read-working-memory`, `save-handoff`, `save-thread`, and `search-memory`.
