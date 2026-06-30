---
name: jira-explorer
description: Use when exploring a Jira instance - searching issues, viewing details, posting comments, transitioning status, or checking assigned work. Requires python-jira module and JIRA_URL/JIRA_API_TOKEN env vars.
---

# Jira Explorer

Explore a self-hosted Jira instance using `scripts/jr.py` (python-jira wrapper).

## Prerequisites

- `jira` module installed (`pip install jira`)
- Environment variables: `JIRA_URL` (or `JIRA_HOST`), `JIRA_API_TOKEN`

## Quick Reference

Run all commands as `python3 <skill-dir>/scripts/jr.py <command>`.

| Command | Description |
|---------|-------------|
| `jr.py auth` | Verify authentication |
| `jr.py myself [--limit N]` | Current user info + assigned issues |
| `jr.py search <JQL> [--limit N]` | Run JQL query |
| `jr.py create <PROJECT> --type <type> --summary <summary> [opts]` | Create a new issue |
| `jr.py issue <KEY>` | Issue details (JSON) |
| `jr.py issue <KEY> comments` | List issue comments |
| `jr.py issue <KEY> comment <body>` | Post a comment (use `-` for stdin) |
| `jr.py issue <KEY> transitions` | List available status transitions |
| `jr.py issue <KEY> transition <name>` | Move issue to new status |
| `jr.py issue <KEY> update <field=value>... [--json '{}']` | Update issue fields |

Issue `<KEY>` is the full issue key (e.g. `PROJ-123`).

Most list commands accept `--limit N` (default 20).

## Typical Workflows

### Check my assigned issues
```bash
jr.py myself
```

### Search for issues
```bash
jr.py search "project = PROJ AND status = 'In Progress'"
jr.py search "assignee = currentUser() AND updated >= -7d"
```

### View and comment on an issue
```bash
jr.py issue PROJ-123
jr.py issue PROJ-123 comments
jr.py issue PROJ-123 comment "Working on this now"

# Multiline comment from stdin
echo "## Summary\n\nDone." | jr.py issue PROJ-123 comment -
```

### Create an issue
```bash
# Simple bug
jr.py create PROJ --type Bug --summary "Login button not working"

# Full options
jr.py create PROJ --type Bug --summary "Title" --description "Details" \
  --priority "P1 - Should have" --assignee username --labels bug urgent

# Sub-task under parent
jr.py create PROJ --type Sub-task --summary "Sub-task title" --parent PROJ-100

# Description from stdin
echo "Detailed description" | jr.py create PROJ --type Task --summary "Title" --description -

# Extra fields via JSON
jr.py create PROJ --type Story --summary "Title" --json '{"customfield_10001": {"value": "A"}}'
```

### Transition an issue
```bash
# See available transitions first
jr.py issue PROJ-123 transitions

# Move to new status
jr.py issue PROJ-123 transition "In Progress"
jr.py issue PROJ-123 transition Done
```

### Update issue fields
```bash
# Simple field updates
jr.py issue PROJ-123 update summary="Updated title" priority=High

# Complex fields via JSON
jr.py issue PROJ-123 update --json '{"customfield_10001": {"value": "Option A"}}'

# Combine both
jr.py issue PROJ-123 update summary="New title" --json '{"labels": ["bug", "urgent"]}'
```

## Troubleshooting

If `auth` fails, report the error output to the user as-is. Do not attempt to inspect or enumerate environment variables.

## Run `jr.py --help` for full usage details.
