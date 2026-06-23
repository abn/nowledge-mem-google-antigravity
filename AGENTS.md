# Developer Agent Guidelines for `nowledge-mem-google-antigravity`

Welcome! This document outlines the project architecture, developer workflows, performance constraints, and UI guidelines for agents contributing to this repository.

---

## 1. Project Stack & Architecture

This plugin is a hybrid integration of the user's Nowledge Mem knowledge base and Google Antigravity:
* **Lifecycle Hooks**: Triggered before/after sessions and tool calls to inject context (Context Bundle / Working Memory) and save transcripts.
* **MCP Server Connection**: Exposes structured JSON tools (`nowledge-mem` server) for low-friction memory read/write operations.
* **Agent Skills**: Bundled markdown instructions (`skills/`) that teach agents when and how to search, distill, or checkpoint progress.

---

## 2. Hook Development Constraints

When modifying or adding hook scripts under `hooks/` and configuring them in `hooks.json`, adhere to the following rules:

* **POSIX Path Safety**: Do NOT use dynamic path variables (such as `${extensionPath}`) inside `hooks.json`. They are not supported by the Antigravity hook runner. Keep invocations generic and POSIX-compliant (e.g. `python3 hooks/session-start.py || python hooks/session-start.py || echo {}`).
* **Latency Optimization**: Spawning subprocesses adds significant overhead (~300-500ms).
  - Pre-invocation, pre-tool, and stop hooks must run quickly (<50ms).
  - In hook scripts, prefer direct HTTP requests to the Nowledge Mem server using python's native `urllib` module rather than spawning `nmem` CLI subprocesses.
* **Intent-Based Gating**: Preserve the auto-allow logic in `hooks/nmem-gate.py`.
  - It reads `transcript.jsonl` to scan for explicit user intent keywords (`save`, `remember`, `store`, etc.).
  - Safe memory writes with detected user intent should be auto-allowed (`"decision": "allow"`) to minimize user permission prompts, while destructive edits require a prompt (`"decision": "force_ask"`).
* **Space Auto-Detection Heuristics**: Automatically map workspace directories to Nowledge Mem spaces.
  - Heuristics must fall back gracefully to the `default` space.
  - Respect override environment variables (`NMEM_SPACE` or `NMEM_SPACE_ID`) if set.

---

## 3. Git Commit Standards

Maintain a clean, linear repository history by following these commit guidelines:

* **Conventional Commits**: Prefix all commit titles with Conventional Commit tags (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
* **Summary-Only Preference**: Prioritize terse, summary-only commit messages.
  - If adding a description summary, keep it human-friendly and high-level.
  - Avoid listing file-by-file code changes that are easily inferred from the commit diffs.

---

## 4. CI/CD & Validation

* Before staging or proposing any changes, always run the validation suite:
  ```bash
  npm run validate
  ```
* The linter (`scripts/validate-plugin.mjs`) checks:
  - That all required files (rules, skills, hooks, and release notes) are present.
  - That the version declared in `plugin.json` matches the version in `package.json` exactly.
  - That configuration files like `mcp_config.json` and `hooks.json` contain valid JSON structure.

---

## 5. Token Optimization Guidelines

Help agents minimize token usage and avoid bloating the conversation context:

* **Start Informed, Once**: Read the Context Bundle or Working Memory exactly once at the beginning of the session. Do not query them on every conversation turn.
* **Nowledge FS Priority**: Prioritize the unified path-first interface (MCP `mem_fs` tool or CLI `nmem fs`) for directory listings, grep-searching, and file actions.
* **Start Broad, Then Narrow**:
  1. Use `mem_fs` `recall` or `find` to retrieve file paths.
  2. Use `mem_fs` `stat` to check file sizes and metadata cheaply *before* loading bodies.
  3. Use `mem_fs` `cat` with `--line` and `--lines` (or paging limits/offsets for thread fetches) to load only the specific window of content needed.
* **Deduplication**: Query existing memories via `memory_search` before calling writes to prevent duplicate entries.
* **CLI/Hook-Based Thread Saving**: The `nmem-save-thread` skill is uniquely designed to use host-side CLI hooks (such as `hooks/session-end.py`) rather than MCP tools. This prevents the agent from loading large, multi-megabyte `transcript.jsonl` files into its context window and serializing them over MCP, optimizing token usage and eliminating context limits on long conversations.

---

## 6. Premium UI/UX & Feedback Loops

Avoid raw text chat loops for drafting, confirmation, and multi-choice selections. Leverage Antigravity's native rich interfaces:

* **Proceed Approvals (Artifacts)**:
  - For drafting distilled memories or session handoff summaries, write them to a structured Markdown artifact (e.g. `distilled_memories_draft.md` or `handoff_draft.md`) under `<appDataDir>/brain/<conversation-id>`.
  - Set `RequestFeedback: true` and `UserFacing: true` in the `ArtifactMetadata` to present the user with a single-click "Proceed" button.
* **Interactive Prompts (`ask_question`)**:
  - Use the native `ask_question` tool with `is_multi_select: true` when asking the user to choose from multiple options (such as selecting which suggested skills to install or which memories to save).
  - List recommended options first, prefixed with `(Recommended)`.
* **Visual Formatting**: Format all structured content using GitHub-style Alerts (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`), Markdown Tables, and Mermaid diagrams to represent graph relationships.

---

## 7. Skill Development Guidelines

When authoring or modifying skills under `skills/`, follow these principles:

* **File Location & Naming**: Each skill must be placed in its own folder under `skills/<skill-folder>/SKILL.md` (e.g. `skills/nmem-search-memory/SKILL.md`).
* **YAML Frontmatter Trigger Matching**: Every `SKILL.md` must start with a YAML frontmatter block containing:
  - `name`: Kebab-cased unique name matching the folder name.
  - `description`: A clear, third-person explanation of what behavior the skill teaches and when the agent should use it. This description is parsed by Antigravity at startup to dynamically discover and load relevant skills, so it must contain relevant keywords.
* **Primary and Fallback Interaction Paths**: Every skill that interacts with the `nmem` backend (whether reading working memory, searching, saving handoffs, or distilling memories) should define:
  1. A **Primary Interaction Mode**: Usually native MCP tools (or specialized helper scripts) to prevent terminal permission prompts and keep execution silent.
  2. A **CLI Fallback**: A documented fallback command using the `nmem` CLI to ensure the skill remains operational if MCP tools or APIs are disabled or unavailable.
* **Preferred Execution Hierarchy**: Document these paths clearly in a "Preferred Retrieval Hierarchy" or "Preferred Execution Hierarchy" section within the skill's `SKILL.md` file.
* **Outcome Feedback Footers**: Include the standard `<!-- nmem:skill-outcome-footer v1 -->` section at the bottom of the document. This teaches using agents to output `nmem-skill-used: <skill-name>` when applying the skill and instructs them to report deviations or failures using `report_skill_outcome` or the `nmem skills outcome` CLI fallback.
