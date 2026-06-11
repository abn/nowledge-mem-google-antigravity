# Nowledge Mem -- Google Antigravity Plugin

> Bring your Nowledge Mem knowledge base into Google Antigravity with persistent context, memory rules, and agent skills.

This package is the **Google Antigravity-native product surface** for Nowledge Mem.

It is deliberately **hybrid**:

- Google Antigravity loads memory rules plus lifecycle hooks for Context Bundle / Working Memory startup context and session capture
- the plugin exposes local Nowledge Mem MCP tools for lower-friction retrieval and memory writes
- bundled skills teach Antigravity when to recall, distill, save threads, and create handoff summaries
- Antigravity can still call `nmem` directly whenever it needs a more flexible path

The recommended setup is simple and stable: Google Antigravity on top, MCP for direct retrieval tools, and `nmem` for hooks, thread save, remote auth, and command fallback.

## Requirements

- [Google Antigravity 2.0](https://antigravity.google)
- [Nowledge Mem](https://mem.nowledge.co) running locally, or a reachable remote Nowledge Mem server
- `nmem` CLI in your `PATH`

If Nowledge Mem is already running on the same machine through the desktop app, install the bundled CLI from **Settings -> Preferences -> Developer Tools -> Install CLI**. That gives Antigravity direct access to the local Mem instance.

Verify connection:

```bash
nmem status
```

For the default same-machine setup, `nmem status` should show `http://127.0.0.1:14242 (default)`.

## Install

For local development or a repository checkout install, you can link the plugin folder to one of the locations scanned by Antigravity:

### Option 1: Workspace Level (Active workspace only)

Place or symlink the plugin folder inside `.agents/plugins/` (or `_agents/plugins/`) at the root of your opened workspace:

```bash
mkdir -p .agents/plugins
ln -s /path/to/nowledge-mem-google-antigravity .agents/plugins/
```

### Option 2: Global Level (All workspaces)

Place or symlink the plugin folder inside `~/.gemini/config/plugins/` in your user home directory:

```bash
mkdir -p ~/.gemini/config/plugins
ln -s /path/to/nowledge-mem-google-antigravity ~/.gemini/config/plugins/
```

Alternatively, you can clone the repository directly into your global plugins directory:

```bash
git clone https://github.com/nowledge-co/nowledge-mem-google-antigravity.git ~/.gemini/config/plugins/nowledge-mem
```

Restart Google Antigravity after linking or cloning.

Release packaging notes live in [`RELEASING.md`](./RELEASING.md).

## What You Get

**Automatic lifecycle hooks**

- **PreInvocation Hook**: Automatically loads Context Bundle when available, with Working Memory as the lightweight fallback, and injects it as situational context at the start of the session.
- **Stop Hook**: Automatically imports the conversation messages from Antigravity's `transcript.jsonl` log into Nowledge Mem under the current conversation ID when execution completes.

**Bundled MCP**

- Local same-machine installs expose `nowledge-mem` MCP tools at `http://127.0.0.1:14242/mcp/` automatically.
- Antigravity `mcp_config.json` can override the same `nowledge-mem` server name for remote Mem or a custom local endpoint.

**Persistent context rules**

- `rules/nowledge-mem.md` tells Antigravity how to route recall across Context Bundle, Working Memory, distilled memories, conversation threads, and handoff summaries.

**Agent skills**

- `read-working-memory`
- `search-memory`
- `distill-memory`
- `save-thread`
- `save-handoff`

## Local vs Remote

By default, both `nmem` and the bundled MCP server point to the local Mem server at `http://127.0.0.1:14242`.

For remote Mem, run:

```bash
nmem config client set url https://mem.example.com
nmem config client set api-key nmem_your_key
```

`nmem` loads connection settings with this priority:

- `--api-url` flag
- `NMEM_API_URL` / `NMEM_API_KEY`
- `~/.nowledge-mem/config.json`
- defaults

If you need a temporary override for one session, launch Antigravity from a shell where `NMEM_API_URL` and `NMEM_API_KEY` are exported.

For MCP tools in remote mode, generate the host config:

```bash
nmem config mcp show --host google-antigravity
```

Paste the generated JSON into Antigravity's custom MCP config (`~/.gemini/config/mcp_config.json` or modified raw via the MCP Store).

## Direct `nmem` Use Is Always Allowed

The bundled skills are convenience paths, not a cage. Antigravity should freely compose direct `nmem` commands when that is clearer or more flexible.

Examples:

```bash
nmem --json wm read
nmem --json m search "auth token rotation" --mode deep --importance 0.7
nmem --json m search "auth token rotation" --mode deep --importance 0.7 --space "Research Agent"
nmem --json m add "JWT refresh failures came from clock skew between the gateway and API nodes." -t "JWT refresh failures traced to clock skew" -i 0.9 --unit-type learning -l auth -l backend -s google-antigravity
nmem status
```

## Thread Save vs Handoff

Antigravity supports two separate save paths:

- **Thread Save** (`save-thread` skill): Imports the **real session messages** into Nowledge Mem. The Stop hook performs this import automatically at the end of the session, but the skill is available for manual mid-session triggers.
- **Handoff Save** (`save-handoff` skill): Creates a **compact resumable handoff summary** with Goal, Decisions, Files, Risks, and Next. Use this when you want a lightweight restart point rather than the full transcript.

Use `distill-memory` for durable atomic knowledge, `save-thread` for the full session, and `save-handoff` for a resumable handoff.

## Links

- [Documentation](https://mem.nowledge.co/docs/integrations/google-antigravity)
- [Nowledge Mem](https://mem.nowledge.co)
- [Discord](https://nowled.ge/discord)
- [GitHub](https://github.com/nowledge-co/nowledge-mem-google-antigravity)
