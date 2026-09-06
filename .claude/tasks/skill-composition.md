# Task: Build Modular Skill Architecture

**Created:** 2026-01-28
**Status:** Planned

## Goal

Create modular skills that can be composed together, with `/weekly-checklist` orchestrating calls to specialized skills.

## Architecture

```
/weekly-checklist (orchestrator)
├── Financial > Banking & Credit (inline)
├── Professional > Digital & Physical Logistics
│   ├── /career-log  ← invoke via Skill tool
│   ├── /weekly-email ← invoke via Skill tool (replaces Uncle Arlo)
│   └── Calendar, Roadmap (inline)
├── Professional > Social & Communications (inline)
└── Recreational > Multimedia (inline)
```

## Skills to Build

### 1. /career-log

Analyze work and update Career Log spreadsheet.

**Capabilities:**
- Query Google Calendar via MCP for meetings attended
- Search Gmail for accomplishments, sent items
- Query Jira for tickets worked on
- Analyze patterns and summarize accomplishments
- Format entries (date, comments columns)
- Append to Career Log spreadsheet via Google Sheets MCP

**MCP servers used:**
- google-workspace (Calendar, Gmail, Sheets)
- mcp-atlassian-local (Jira)

### 2. /weekly-email

Generate RHEL 11 status email (replace Uncle Arlo Gemini gem).

**Capabilities:**
- Pull data from calendar, email, Jira, Acquacotta tracking spreadsheet
- Analyze Core Platform Pod activity
- Generate draft email following "RHEL 11 Status" format
- Highlight team accomplishments, call out people by name
- Create Gmail draft via MCP

**MCP servers used:**
- google-workspace (Calendar, Gmail, Drive, Sheets)
- mcp-atlassian-local (Jira)

### 3. Update /weekly-checklist

Modify to invoke sub-skills:
```markdown
### Career Log Item

When you reach the Career Log item, invoke the `/career-log` skill:
- Use the Skill tool with skill: "career-log"
- Wait for that skill to complete
- Then continue with the weekly checklist workflow
```

## Implementation Order

1. Build `/career-log` standalone, test it
2. Build `/weekly-email` standalone, test it
3. Wire both into `/weekly-checklist`
4. Test full orchestrated workflow

## Notes

- Skills can't directly call skills, but skill instructions can tell Claude to use the Skill tool
- Claude acts as intermediary executing the instructions
- Each sub-skill should work independently for debugging/testing
