---
name: nmem-thread-save
description: Save the real Google Antigravity session to Nowledge Mem only when the user explicitly asks. This uses Antigravity's transcript-backed importer rather than a summary-only fallback. Triggered by /nmem-thread-save.
---

# Save Thread

Only use this skill when the user explicitly asks to save the session, persist the thread, or store the actual conversation.

## Contract

`nmem-save-thread` means saving the real conversation messages.

Use the plugin's `hooks/session-end.py` script for that path, which parses the `transcript.jsonl` file and imports it using `nmem t import`.

Use `nmem-save-handoff` instead only when the user wants a lightweight resumable summary rather than the full session.

## Workflow

1. Write a concise 1-2 sentence summary.
2. Locate the plugin's `hooks/session-end.py` script (typically under the workspace `.agents/plugins/nowledge-mem-google-antigravity/` or the global `~/.gemini/config/plugins/nowledge-mem-google-antigravity/` folder).
3. Read the `conversationId` and `transcriptPath` from your active context. The `transcriptPath` is typically `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`.
4. Run the script by passing the metadata as a JSON payload on `stdin`:
   ```bash
   echo '{"conversationId": "YOUR_CONVERSATION_ID", "transcriptPath": "PATH_TO_TRANSCRIPT_JSONL"}' | python3 /path/to/plugin/hooks/session-end.py
   ```
5. Report whether the thread was created or updated and how many messages were stored.

Never claim a checkpoint summary is a thread save. Never auto-save without an explicit user request.
