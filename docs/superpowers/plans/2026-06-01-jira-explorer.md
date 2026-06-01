# Jira Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a minimalistic CLI tool (`jira.py`) for interacting with self-hosted Jira instances via Personal Access Token.

**Architecture:** Single Python file at `skills/jira-explorer/scripts/jira.py` using `python-jira` library. Argparse-based CLI with subcommands. SKILL.md documents usage for agents.

**Tech Stack:** Python 3.8+, `jira` (python-jira), argparse, json

---

## File Structure

| File | Responsibility |
|------|---------------|
| `skills/jira-explorer/scripts/jira.py` | CLI tool — all commands in one file |
| `skills/jira-explorer/SKILL.md` | Agent-facing documentation |

---

### Task 1: Scaffold and Authentication

**Files:**
- Create: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Create the script with auth scaffolding**

```python
#!/usr/bin/env python3
"""
Jira explorer CLI - thin wrapper around python-jira.

Authentication via environment variables:
  JIRA_URL        - Jira instance URL (e.g. https://jira.example.com)
  JIRA_API_TOKEN  - Personal Access Token (Data Center 8.14+)

Usage:
  jira.py auth                                      # Verify authentication
  jira.py myself [--limit N]                        # Current user + assigned issues
  jira.py search <JQL> [--limit N]                  # Run JQL query
  jira.py issue <KEY>                               # Issue details (JSON)
  jira.py issue <KEY> comments                      # List comments
  jira.py issue <KEY> comment <body>                # Post comment (use '-' for stdin)
  jira.py issue <KEY> transitions                   # List available transitions
  jira.py issue <KEY> transition <name>             # Move issue to new status
  jira.py issue <KEY> update <field=value>... [--json '{}']  # Update fields

Issue <KEY> is the full issue key (e.g. PROJ-123).
"""

import argparse
import json
import os
import sys

from jira import JIRA, JIRAError


def get_client():
    """Create authenticated Jira client from environment variables."""
    url = os.environ.get("JIRA_URL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not url or not token:
        print("Error: JIRA_URL and JIRA_API_TOKEN must be set", file=sys.stderr)
        sys.exit(1)
    return JIRA(server=url, token_auth=token)


def jprint(obj):
    """Print object as formatted JSON."""
    print(json.dumps(obj, indent=2, default=str))


def cmd_auth(args):
    """Verify authentication and print user info."""
    client = get_client()
    myself = client.myself()
    server_info = client.server_info()
    jprint({
        "username": myself.get("name", ""),
        "displayName": myself.get("displayName", ""),
        "emailAddress": myself.get("emailAddress", ""),
        "serverUrl": os.environ.get("JIRA_URL"),
        "serverVersion": server_info.get("version", ""),
        "serverTitle": server_info.get("serverTitle", ""),
    })


def main():
    parser = argparse.ArgumentParser(
        description="Jira Explorer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    # auth
    sub.add_parser("auth", help="Verify authentication")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "auth":
            cmd_auth(args)
    except JIRAError as e:
        print(f"Jira API error: {e.text or e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable and test manually**

```bash
chmod +x skills/jira-explorer/scripts/jira.py
python3 skills/jira-explorer/scripts/jira.py --help
```

Expected: help text prints with usage info and `auth` subcommand listed.

- [ ] **Step 3: Commit**

```bash
git add skills/jira-explorer/scripts/jira.py
git commit -m "feat(jira-explorer): scaffold CLI with auth command"
```

---

### Task 2: `myself` Command

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add `myself` command function**

Add after `cmd_auth`:

```python
def cmd_myself(args):
    """Show current user info and assigned issues."""
    client = get_client()
    myself = client.myself()
    username = myself.get("name", "")
    print(f"User: {username} ({myself.get('displayName', '')})")
    print(f"Email: {myself.get('emailAddress', '')}")
    print()

    jql = f"assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC"
    issues = client.search_issues(jql, maxResults=args.limit)
    print(f"Open issues assigned to me ({len(issues)}):")
    for issue in issues:
        key = issue.key
        status = str(issue.fields.status)
        summary = issue.fields.summary
        print(f"  {key:<12} {status:<16} {summary}")
```

- [ ] **Step 2: Register in argparse and dispatch**

Add to the subparsers section (after `auth`):

```python
    # myself
    myself_p = sub.add_parser("myself", help="Current user + assigned issues")
    myself_p.add_argument("--limit", type=int, default=20)
```

Add to the dispatch block:

```python
        elif args.command == "myself":
            cmd_myself(args)
```

- [ ] **Step 3: Test manually**

```bash
python3 skills/jira-explorer/scripts/jira.py myself --help
```

Expected: shows help with `--limit` option.

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add myself command"
```

---

### Task 3: `search` Command

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add `search` command function**

Add after `cmd_myself`:

```python
def cmd_search(args):
    """Run JQL query and display results."""
    client = get_client()
    issues = client.search_issues(args.jql, maxResults=args.limit)
    for issue in issues:
        key = issue.key
        status = str(issue.fields.status)
        assignee = str(issue.fields.assignee) if issue.fields.assignee else ""
        summary = issue.fields.summary
        print(f"{key:<12} {status:<16} {assignee:<20} {summary}")
```

- [ ] **Step 2: Register in argparse and dispatch**

Subparser:

```python
    # search
    search_p = sub.add_parser("search", help="Run JQL query")
    search_p.add_argument("jql", help="JQL query string")
    search_p.add_argument("--limit", type=int, default=20)
```

Dispatch:

```python
        elif args.command == "search":
            cmd_search(args)
```

- [ ] **Step 3: Test manually**

```bash
python3 skills/jira-explorer/scripts/jira.py search --help
```

Expected: shows help with `jql` positional arg and `--limit` option.

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add search command"
```

---

### Task 4: `issue` Detail Command

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add `issue` detail command function**

Add after `cmd_search`:

```python
def cmd_issue_detail(args):
    """Show issue details as JSON."""
    client = get_client()
    issue = client.issue(args.key)
    f = issue.fields
    jprint({
        "key": issue.key,
        "summary": f.summary,
        "status": str(f.status),
        "issueType": str(f.issuetype),
        "priority": str(f.priority) if f.priority else None,
        "assignee": str(f.assignee) if f.assignee else None,
        "reporter": str(f.reporter) if f.reporter else None,
        "labels": f.labels or [],
        "created": f.created,
        "updated": f.updated,
        "resolved": f.resolutiondate,
        "description": f.description,
    })
```

- [ ] **Step 2: Register in argparse and dispatch**

Subparser (the `issue` subcommand with its own sub-subcommands):

```python
    # issue <KEY> ...
    issue_p = sub.add_parser("issue", help="Issue operations")
    issue_p.add_argument("key", help="Issue key (e.g. PROJ-123)")
    issue_p.add_argument("subcmd", nargs="?", default=None,
                         choices=["comments", "comment", "transitions", "transition", "update"],
                         help="Sub-command")
    issue_p.add_argument("body", nargs="?", default=None,
                         help="Comment body or transition name (use '-' for stdin)")
    issue_p.add_argument("fields", nargs="*", default=[],
                         help="field=value pairs for update")
    issue_p.add_argument("--json", dest="json_fields", default=None,
                         help="JSON object for complex field updates")
    issue_p.add_argument("--limit", type=int, default=20)
```

Dispatch:

```python
        elif args.command == "issue":
            if args.subcmd is None:
                cmd_issue_detail(args)
```

- [ ] **Step 3: Test manually**

```bash
python3 skills/jira-explorer/scripts/jira.py issue --help
```

Expected: shows help with `key` argument and sub-commands listed.

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add issue detail command"
```

---

### Task 5: `issue <KEY> comments` and `issue <KEY> comment`

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add comments list function**

Add after `cmd_issue_detail`:

```python
def cmd_issue_comments(args):
    """List comments on an issue."""
    client = get_client()
    issue = client.issue(args.key)
    comments = client.comments(issue)
    if not comments:
        print("No comments.")
        return
    for c in comments:
        author = c.author.displayName if hasattr(c, "author") else "Unknown"
        created = c.created[:10] if c.created else ""
        print(f"--- #{c.id} {author} {created} ---")
        print(c.body)
        print()


def cmd_issue_comment(args):
    """Post a comment on an issue."""
    client = get_client()
    body = args.body
    if body == "-":
        body = sys.stdin.read()
    if not body:
        print("Error: comment body is required (pass text or '-' for stdin)", file=sys.stderr)
        sys.exit(1)
    client.add_comment(args.key, body)
    print(f"Comment added to {args.key}")
```

- [ ] **Step 2: Add dispatch for comments/comment**

Add inside the `elif args.command == "issue":` block:

```python
            elif args.subcmd == "comments":
                cmd_issue_comments(args)
            elif args.subcmd == "comment":
                cmd_issue_comment(args)
```

- [ ] **Step 3: Test manually**

```bash
python3 skills/jira-explorer/scripts/jira.py issue FAKE-1 comments
```

Expected: either shows comments or a Jira API error (confirming dispatch works).

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add issue comments and comment commands"
```

---

### Task 6: `issue <KEY> transitions` and `issue <KEY> transition`

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add transitions functions**

Add after `cmd_issue_comment`:

```python
def cmd_issue_transitions(args):
    """List available transitions for an issue."""
    client = get_client()
    transitions = client.transitions(args.key)
    for t in transitions:
        print(f"  {t['id']:<6} {t['name']}")


def cmd_issue_transition(args):
    """Transition an issue to a new status."""
    client = get_client()
    name = args.body
    if not name:
        print("Error: transition name is required", file=sys.stderr)
        sys.exit(1)

    transitions = client.transitions(args.key)
    # Case-insensitive match
    match = None
    for t in transitions:
        if t["name"].lower() == name.lower():
            match = t
            break

    if not match:
        print(f"Error: transition '{name}' not found. Available transitions:", file=sys.stderr)
        for t in transitions:
            print(f"  {t['id']:<6} {t['name']}", file=sys.stderr)
        sys.exit(1)

    client.transition_issue(args.key, match["id"])
    print(f"Transitioned {args.key} -> {match['name']}")
```

- [ ] **Step 2: Add dispatch**

Add inside the `elif args.command == "issue":` block:

```python
            elif args.subcmd == "transitions":
                cmd_issue_transitions(args)
            elif args.subcmd == "transition":
                cmd_issue_transition(args)
```

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add issue transitions commands"
```

---

### Task 7: `issue <KEY> update`

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

- [ ] **Step 1: Add update function**

Add after `cmd_issue_transition`:

```python
def cmd_issue_update(args):
    """Update issue fields."""
    client = get_client()
    fields = {}

    # Parse field=value positional args
    # args.body might be a field=value (first one captured there)
    all_fields_args = []
    if args.body and "=" in args.body:
        all_fields_args.append(args.body)
    all_fields_args.extend(args.fields)

    for pair in all_fields_args:
        if "=" not in pair:
            print(f"Error: invalid field format '{pair}', expected field=value", file=sys.stderr)
            sys.exit(1)
        key, value = pair.split("=", 1)
        fields[key] = value

    # Parse --json if provided
    if args.json_fields:
        try:
            json_data = json.loads(args.json_fields)
            fields.update(json_data)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    if not fields:
        print("Error: at least one field=value or --json is required", file=sys.stderr)
        sys.exit(1)

    issue = client.issue(args.key)
    issue.update(fields=fields)
    print(f"Updated {args.key}:")
    for k, v in fields.items():
        val_str = str(v)
        if len(val_str) > 80:
            val_str = val_str[:80] + "..."
        print(f"  {k} = {val_str}")
```

- [ ] **Step 2: Add dispatch**

Add inside the `elif args.command == "issue":` block:

```python
            elif args.subcmd == "update":
                cmd_issue_update(args)
```

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "feat(jira-explorer): add issue update command"
```

---

### Task 8: Argparse Refinement

**Files:**
- Modify: `skills/jira-explorer/scripts/jira.py`

The argparse for the `issue` subcommand uses a flat structure with `nargs="?"` for subcmd and body. This works but the `update` command needs to capture multiple positional `field=value` args. Let's verify the arg parsing handles all cases correctly.

- [ ] **Step 1: Refine the issue subparser to handle update fields**

Replace the `issue` subparser definition with a version that uses `parse_known_args` or adjust the positional handling. The current design uses `body` for both comment text AND transition name AND the first field=value pair. For `update`, remaining positional args go into `fields`. Verify this works by testing:

```bash
# These should all parse correctly:
python3 skills/jira-explorer/scripts/jira.py issue KEY
python3 skills/jira-explorer/scripts/jira.py issue KEY comments
python3 skills/jira-explorer/scripts/jira.py issue KEY comment "hello"
python3 skills/jira-explorer/scripts/jira.py issue KEY transition "In Progress"
python3 skills/jira-explorer/scripts/jira.py issue KEY update summary="new title" priority=High
python3 skills/jira-explorer/scripts/jira.py issue KEY update --json '{"summary":"test"}'
```

If parsing doesn't work cleanly with argparse (likely — mixing optional positionals with choices is fragile), switch to manual argv parsing for the `issue` command:

```python
def parse_issue_args(argv):
    """Parse issue sub-command args manually for flexibility."""
    if len(argv) < 1:
        return None

    key = argv[0]
    subcmd = argv[1] if len(argv) > 1 else None
    rest = argv[2:]

    return argparse.Namespace(
        command="issue",
        key=key,
        subcmd=subcmd,
        body=rest[0] if rest and subcmd in ("comment", "transition") else None,
        fields=rest if subcmd == "update" else [],
        json_fields=None,
        limit=20,
    )
```

Actually, the cleanest approach: keep argparse for top-level command routing, but for `issue` do manual parsing of `sys.argv` after the `issue` keyword. Here's the refined approach:

```python
def parse_issue_args(argv):
    """Parse issue subcommand arguments.

    argv is everything after 'issue' in sys.argv.
    """
    if not argv:
        print("Error: issue key is required", file=sys.stderr)
        sys.exit(1)

    key = argv[0]
    subcmd = argv[1] if len(argv) > 1 else None
    rest = argv[2:]

    ns = argparse.Namespace(command="issue", key=key, subcmd=subcmd, limit=20)

    if subcmd in ("comment", "transition"):
        ns.body = " ".join(rest) if rest else None
    elif subcmd == "update":
        # Separate --json from field=value pairs
        ns.json_fields = None
        ns.fields = []
        i = 0
        while i < len(rest):
            if rest[i] == "--json" and i + 1 < len(rest):
                ns.json_fields = rest[i + 1]
                i += 2
            else:
                ns.fields.append(rest[i])
                i += 1
        ns.body = None
    else:
        ns.body = None
        ns.fields = []
        ns.json_fields = None

    return ns
```

Then in `main()`, handle `issue` before argparse:

```python
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "issue":
        args = parse_issue_args(sys.argv[2:])
    else:
        # ... existing argparse for other commands ...
        args = parser.parse_args()
```

- [ ] **Step 2: Test all argument patterns**

```bash
python3 skills/jira-explorer/scripts/jira.py issue --help  # should still give useful info
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 comments
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 comment "test body"
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 transition "In Progress"
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 update summary="new" priority=High
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 update --json '{"summary":"x"}'
python3 skills/jira-explorer/scripts/jira.py issue PROJ-1 update summary="a" --json '{"priority":{"name":"High"}}'
```

Expected: no argparse errors — each parses to correct namespace. API errors are fine (no real server).

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "refactor(jira-explorer): use manual arg parsing for issue subcommand"
```

---

### Task 9: Write SKILL.md

**Files:**
- Create: `skills/jira-explorer/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: jira-explorer
description: Use when exploring a Jira instance - searching issues, viewing details, posting comments, transitioning status, or checking assigned work. Requires python-jira module and JIRA_URL/JIRA_API_TOKEN env vars.
---

# Jira Explorer

Explore a self-hosted Jira instance using `scripts/jira.py` (python-jira wrapper).

## Prerequisites

- `jira` module installed (`pip install jira`)
- Environment variables: `JIRA_URL`, `JIRA_API_TOKEN`

## Quick Reference

Run all commands as `python3 <skill-dir>/scripts/jira.py <command>`.

| Command | Description |
|---------|-------------|
| `jira.py auth` | Verify authentication |
| `jira.py myself [--limit N]` | Current user info + assigned issues |
| `jira.py search <JQL> [--limit N]` | Run JQL query |
| `jira.py issue <KEY>` | Issue details (JSON) |
| `jira.py issue <KEY> comments` | List issue comments |
| `jira.py issue <KEY> comment <body>` | Post a comment (use `-` for stdin) |
| `jira.py issue <KEY> transitions` | List available status transitions |
| `jira.py issue <KEY> transition <name>` | Move issue to new status |
| `jira.py issue <KEY> update <field=value>... [--json '{}']` | Update issue fields |

Issue `<KEY>` is the full issue key (e.g. `PROJ-123`).

Most list commands accept `--limit N` (default 20).

## Typical Workflows

### Check my assigned issues
```bash
jira.py myself
```

### Search for issues
```bash
jira.py search "project = PROJ AND status = 'In Progress'"
jira.py search "assignee = currentUser() AND updated >= -7d"
```

### View and comment on an issue
```bash
jira.py issue PROJ-123
jira.py issue PROJ-123 comments
jira.py issue PROJ-123 comment "Working on this now"

# Multiline comment from stdin
echo "## Summary\n\nDone." | jira.py issue PROJ-123 comment -
```

### Transition an issue
```bash
# See available transitions first
jira.py issue PROJ-123 transitions

# Move to new status
jira.py issue PROJ-123 transition "In Progress"
jira.py issue PROJ-123 transition Done
```

### Update issue fields
```bash
# Simple field updates
jira.py issue PROJ-123 update summary="Updated title" priority=High

# Complex fields via JSON
jira.py issue PROJ-123 update --json '{"customfield_10001": {"value": "Option A"}}'

# Combine both
jira.py issue PROJ-123 update summary="New title" --json '{"labels": ["bug", "urgent"]}'
```

## Run `jira.py --help` for full usage details.
```

- [ ] **Step 2: Commit**

```bash
git add skills/jira-explorer/SKILL.md
git commit -m "docs(jira-explorer): add SKILL.md"
```

---

### Task 10: Integration Test (Manual)

- [ ] **Step 1: Set environment variables and run full workflow**

```bash
export JIRA_URL="https://your-jira.example.com"
export JIRA_API_TOKEN="your-token-here"

python3 skills/jira-explorer/scripts/jira.py auth
python3 skills/jira-explorer/scripts/jira.py myself
python3 skills/jira-explorer/scripts/jira.py search "project = PROJ ORDER BY updated DESC" --limit 5
python3 skills/jira-explorer/scripts/jira.py issue PROJ-123
python3 skills/jira-explorer/scripts/jira.py issue PROJ-123 comments
python3 skills/jira-explorer/scripts/jira.py issue PROJ-123 transitions
```

- [ ] **Step 2: Verify error handling**

```bash
# Missing env vars
unset JIRA_API_TOKEN
python3 skills/jira-explorer/scripts/jira.py auth
# Expected: "Error: JIRA_URL and JIRA_API_TOKEN must be set"

# Bad token
export JIRA_API_TOKEN="invalid"
python3 skills/jira-explorer/scripts/jira.py auth
# Expected: Jira API error with auth failure message

# Invalid issue key
export JIRA_API_TOKEN="your-real-token"
python3 skills/jira-explorer/scripts/jira.py issue NONEXIST-999
# Expected: Jira API error
```

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -u
git commit -m "fix(jira-explorer): integration test fixes"
```
