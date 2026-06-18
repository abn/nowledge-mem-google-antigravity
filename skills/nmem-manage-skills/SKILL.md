---
name: nmem-manage-skills
description: Install, update, or synchronize skills from Nowledge Mem into the local workspace directory under `.agents/skills/`. Use when the user asks to import, install, or update skills, or when recommending relevant skills for the workspace.
---

# Nowledge Mem Skill Manager

This skill allows the agent to list, suggest, and install skills from the user's Nowledge Mem knowledge base into the current project workspace.

## When to Use

- Use when the user asks to "install a skill", "update a skill", or "import skills from nmem".
- Use when setting up a new workspace to see what existing compiled procedures (ruling, check-lists, styling conventions) from Nowledge Mem would help this project.
- Use to keep local workspace skills in sync with updates on the Nowledge Mem server.

## Workspace Target

All skills installed via this pipeline are placed in:
`<workspace-root>/.agents/skills/<skill-folder>/SKILL.md`

## Workflow

### Step 1: Suggest and Analyze Relevance
To find out what skills might be relevant to the current workspace, run:
```bash
python3 skills/nmem-manage-skills/scripts/manage_skills.py suggest <workspace-root>
```
This script scans for Makefiles, workflow files, Flatpak/AetherPak configurations, and Git status to score and match skills on the server.

### Step 2: Prompt the User (Rich Interface)
Do not install skills silently. Once you have suggestions or a list of available skills, use the Antigravity `ask_question` tool to present them to the user.
* Provide multiple-choice options for the skills to install.
* Ask the user if the skill should be **committed to the repository** (standard track) or **kept local/user-specific** (ignored via Git exclude).

### Step 3: Install/Update the Skill
Run the install command:
```bash
python3 skills/nmem-manage-skills/scripts/manage_skills.py install <skill_id> <workspace-root> [--ignore]
```
* If the skill is in `candidate` stage, the script will automatically trigger compile and wait for it.
* It will download the body directly using `GET /skills/<id>?include_body=true` (which avoids modifying the global activation state on the server).
* If `--ignore` is specified, it automatically appends `.agents/skills/<skill-folder>/` to `<workspace-root>/.git/info/exclude`.

### Step 4: Verify
Verify that the files have been written under `<workspace-root>/.agents/skills/` and notify the user.
