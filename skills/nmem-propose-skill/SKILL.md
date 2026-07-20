---
name: nmem-propose-skill
description: Propose a new skill or submit a skill improvement to Nowledge Mem. Use this skill when the user asks you to create, teach, write, or save a skill, or when you identify an opportunity to propose an improvement to an existing skill's procedure.
---

# Propose Skill / Submit Improvement

Use this skill when the user asks you to write, create, teach, or save a Skill, or when you identify an opportunity to propose a concrete improvement to an existing skill's procedure.

## Good Candidates

- Procedures or guidelines you've refined in the session that would be valuable as reusable agent instructions.
- Additions of safety checks, gotchas, or release steps to existing skills.
- Custom checklists or orders of operations the user wants to codify.

## Workflow

### Step 1: Draft the Skill Submission
Determine whether the request is for a new skill or an improvement to an existing one.
- **For a New Skill**:
  - Determine a short human name for the skill (e.g., 'Release checklist' or 'RSpec Testing Suite').
  - Write a clear `purpose` string describing when to use it and what behavior it should teach.
  - Gather any evidence files or context (such as `memory_ids` from searches, `thread_ids` from conversations, or `source_ids` from library documents).
- **For a Skill Improvement**:
  - Locate the skill you consumed (e.g. from the trailing token of its folder or `/skills/<name>-<id>`).
  - Draft a specific `what` improvement description (1-2 sentences).

### Step 2: Show the Draft to the User (Rich UI/UX Review)
Do not submit or create the skill silently. Write the proposed draft to a user-facing artifact named `skill_draft.md` under `<appDataDir>/brain/<conversation-id>`.
- Set `RequestFeedback: true` and `UserFacing: true` in the `ArtifactMetadata` to present the user with a visual "Proceed" button.
- Format the draft using a premium layout:
  - Organize using GitHub-style Alerts (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`) to describe the skill's name and purpose.
  - Use markdown Tables to show the fields (e.g. Name, Purpose, Evidence).
  - Use Mermaid flowcharts (`mermaid` block) to visualize the skill's workflow/steps if appropriate.

### Step 3: Await Confirmation and Dispatch
1. Notify the user to review the drafted `skill_draft.md` artifact.
2. Wait for the user to click the "Proceed" button or give explicit approval in the conversation.
3. Once approved, dispatch the request.

## Preferred Execution Hierarchy

1. **Direct REST API Import (Primary - Most Reliable)**:
   - Run the proposal python script to upload the fully drafted skill markdown directly to Nowledge Mem:
     ```bash
     python3 skills/nmem-propose-skill/scripts/propose_skill.py <appDataDir>/brain/<conversation-id>/skill_draft.md
     ```
     This bypasses compile-queue failures by directly registering the complete structured procedure.
2. **MCP Tools (Fallback)**:
   - **For a new skill**: Call the `create_skill` tool with the drafted parameters (`name`, `purpose`, and optional `memory_ids`, `thread_ids`, `source_ids`).
   - **For a skill improvement**: Call the `propose_skill_improvement` tool with `skill_id` and the drafted `what` description.
3. **CLI Fallback (Only if python script and MCP are unavailable)**:
   - **For a new skill**:
     ```bash
     nmem skills create -y --name "<name>" --note "<purpose>" [--memory <id>] [--thread <id>] [--source <id>]
     ```
   - **For a skill improvement**:
     ```bash
     nmem skills refine <skill_id> "<what>"
     ```

Report whether the skill submission was successfully created or proposed.

---

<!-- nmem:skill-outcome-footer v1 -->
## Improving this skill

Nowledge Mem compiled this skill from the user's own experience. When you apply it, print one line so it keeps getting sharper (replace `<name>` with this skill's name from the frontmatter above):

    nmem-skill-used: nmem-propose-skill

If a step was wrong or missing, or it didn't work, also record that: call `report_skill_outcome` with `skill_id="nmem-propose-skill"`, `skill_version=1`, an `outcome` of `completed` / `completed_with_deviation` / `failed` / `abandoned`, and a one-line note on what was off. This is the user's own feedback loop, not telemetry.
(Or use CLI fallback: `nmem skills outcome nmem-propose-skill --version 1 --outcome <outcome> [--deviations "<note>" | --failure "<reason>"]`)
