# Jira Explorer Skill — Design Spec

## Overview

A minimalistic CLI tool (`jira.py`) for interacting with self-hosted Jira instances, following the same pattern as the existing `gitlab-explorer` skill. Single Python file, PAT authentication via environment variables, agent-friendly output.

## Structure

```
skills/jira-explorer/
├── SKILL.md
└── scripts/
    └── jira.py
```

## Dependencies

- Python 3.8+
- `jira` (python-jira) — `pip install jira`

## Environment Variables

| Variable   | Required | Description                                      |
|------------|----------|--------------------------------------------------|
| `JIRA_URL` | yes      | Jira instance URL (e.g. `https://jira.example.com`) |
| `JIRA_API_TOKEN` | yes      | Personal Access Token (Data Center 8.14+)        |

## Commands

| Command | Description |
|---------|-------------|
| `jira.py auth` | Verify authentication, print current user info |
| `jira.py myself` | Current user details + issues assigned to me |
| `jira.py search <JQL> [--limit N]` | Run JQL query, tabular results |
| `jira.py issue <KEY>` | Issue details as JSON |
| `jira.py issue <KEY> comments` | List comments |
| `jira.py issue <KEY> comment <body>` | Post comment (use `-` for stdin) |
| `jira.py issue <KEY> transitions` | List available status transitions |
| `jira.py issue <KEY> transition <name>` | Move issue to new status |
| `jira.py issue <KEY> update <field=value>... [--json '{}']` | Update issue fields |

### Command Details

#### `auth`

Connects to Jira, prints:
- Username and display name
- Server URL
- Server version info (if available)

#### `myself`

Prints current user info, then lists issues assigned to the authenticated user (open issues, ordered by updated date, default limit 20).

#### `search <JQL>`

Runs arbitrary JQL. Output: one line per issue — `KEY  STATUS  ASSIGNEE  SUMMARY`. Accepts `--limit N` (default 20).

#### `issue <KEY>`

Prints JSON with: key, summary, status, assignee, reporter, priority, labels, issue type, created, updated, resolved, description.

#### `issue <KEY> comments`

Lists comments chronologically. Each comment:
```
--- #<id> <author> <date> ---
<body>
```

#### `issue <KEY> comment <body>`

Posts a comment. If body is `-`, reads from stdin.

#### `issue <KEY> transitions`

Lists available transitions as: `ID  NAME`. Useful before calling `transition`.

#### `issue <KEY> transition <name>`

Transitions the issue. Matches transition name case-insensitively. If no match found, prints available transitions and exits with error.

#### `issue <KEY> update <field=value>... [--json '{}']`

Updates issue fields. Two modes:

1. **Positional `field=value` pairs** — split on first `=`. Field name is the Jira field ID or common name (summary, priority, labels, etc.). Value is a string.
2. **`--json` flag** — accepts raw JSON object, merged into fields dict. For complex/custom fields with nested structure.

Both can be combined in one call. JSON fields override positional if same key appears in both.

## Authentication

```python
from jira import JIRA

def get_client():
    url = os.environ.get("JIRA_URL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not url or not token:
        print("Error: JIRA_URL and JIRA_API_TOKEN must be set", file=sys.stderr)
        sys.exit(1)
    return JIRA(server=url, token_auth=token)
```

## Output Conventions

- **List commands** (`search`, `myself` issues, `transitions`): columnar, one item per line, human-readable
- **Detail commands** (`issue <KEY>`, `auth`): formatted JSON via `json.dumps(..., indent=2)`
- **Comments**: header line with metadata + body text (matches gitlab-explorer pattern)
- **Mutations** (`comment`, `transition`, `update`): confirmation message with key details
- **ASCII only** -- no emojis, no Unicode check marks/crosses, no special symbols in output

## Error Handling

- Missing env vars -- clear message naming the variables needed
- Authentication failure -- print error, suggest checking token validity
- HTTP/API errors -- print Jira's error response text
- Invalid transition name -- print available transitions in error output
- Invalid field names in update -- print Jira's field-level error messages

## SKILL.md Content

The SKILL.md will:
- State prerequisites (python-jira, env vars)
- Provide quick reference table of all commands
- Show typical workflows (check my issues, search and update, transition workflow)
- Note that `<KEY>` is the full issue key like `PROJ-123`

## Non-Goals

- No board/sprint management
- No issue creation (can be added later)
- No attachment handling
- No webhook/automation support
- No caching or offline mode
