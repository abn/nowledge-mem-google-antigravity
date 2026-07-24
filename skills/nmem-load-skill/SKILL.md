---
name: nmem-load-skill
description: Search Nowledge Mem for skills matching a query and load or inject them on-demand into the current conversation turn or workspace. Triggered by /nmem-load-skill <query> or proactive task discovery.
---

# Nowledge Mem On-Demand Skill Loader

Dynamically discover, preview, and load compiled AI skills from Nowledge Mem into the active conversation turn or local workspace.

## Primary Entry Point

Use this skill when:
- The user runs `/nmem-load-skill <skill query>` or asks to "load skill <query>".
- Antigravity discovers an unhandled domain task (e.g. Makefile, RPM packaging, Docker, Flatpak, specialized database migrations) where a relevant skill exists on the Nowledge Mem server but is not yet active locally.

---

## Workflow

### Step 1: Search for Matching Skills
Run `load_skill.py search` to query Nowledge Mem for candidate or compiled skills matching the query:

```bash
python3 skills/nmem-load-skill/scripts/load_skill.py search "<skill query>"
```

The script returns JSON listing available matching skills with their `id`, `name`, `description`, `stage`, and relevance.

### Step 2: Present Preview & Selection
If multiple matching skills are returned, present the choices to the user before loading:
- Use `ask_question` to let the user select the desired skill.
- If a single skill clearly matches, present a brief summary of the skill name and description.

### Step 3: Fetch Skill Body
Retrieve the full skill body without altering the global activation state on the server:

```bash
python3 skills/nmem-load-skill/scripts/load_skill.py fetch "<skill_id>"
```

### Step 4: Load into Active Session

Select the appropriate loading mode based on user intent:

#### Mode A: Ephemeral Turn Injection (Zero-Restart)
When the user wants the skill loaded immediately for the current task without persisting files:
- Use the fetched skill markdown body directly within a contextual block in your response:
  ```markdown
  <dynamically_loaded_skill name="<skill-id>">
  <skill-body-content>
  </dynamically_loaded_skill>
  ```
- Proceed directly to follow the injected skill's instructions for the current turn.

#### Mode B: Persistent Workspace Installation
When the user asks to install the skill for future use in the current repository:
```bash
python3 skills/nmem-load-skill/scripts/load_skill.py install "<skill_id>" "<workspace-root>" [--ignore]
```
- Installs the file to `<workspace-root>/.agents/skills/<skill-name>/SKILL.md`.
- Appends `.agents/skills/<skill-name>/` to `<workspace-root>/.git/info/exclude` if `--ignore` is set.
- Notify the user once installed.
