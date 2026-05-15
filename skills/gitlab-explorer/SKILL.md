---
name: gitlab-explorer
description: Use when exploring a private GitLab instance - searching projects, listing merge requests, viewing commits, checking pipelines, or reviewing user activity. Requires python-gitlab module and GITLAB_URL/GITLAB_PRIVATE_TOKEN env vars.
---

# GitLab Explorer

Explore a private GitLab instance using `scripts/gl.py` (python-gitlab wrapper).

## Prerequisites

- `python-gitlab` module installed (`pip install python-gitlab`)
- Environment variables: `GITLAB_URL`, `GITLAB_PRIVATE_TOKEN`

## Quick Reference

Run all commands as `python3 <skill-dir>/scripts/gl.py <command>`.

| Command | Description |
|---------|-------------|
| `gl.py auth` | Verify authentication |
| `gl.py projects search <query>` | Search projects by name |
| `gl.py project <path> info` | Project details (JSON) |
| `gl.py project <path> mrs [--state STATE] [--author USER] [--assignee USER] [--reviewer USER] [--scope SCOPE]` | List merge requests |
| `gl.py project <path> mr <iid>` | MR details (JSON) |
| `gl.py project <path> mr <iid> changes` | MR file diff summary |
| `gl.py project <path> mr <iid> approvals` | MR approval status |
| `gl.py project <path> mr <iid> approve` | Approve MR |
| `gl.py project <path> mr <iid> unapprove` | Unapprove MR |
| `gl.py project <path> mr <iid> notes [--all]` | MR comments (excludes system notes by default) |
| `gl.py project <path> mr <iid> comment <body> [--file PATH --line N]` | Post MR comment (general or diff note) |
| `gl.py project <path> mr <iid> resolve <note_id>` | Resolve discussion containing the given note ID |
| `gl.py project <path> mr <iid> resolve --all` | Resolve all unresolved discussions |
| `gl.py project <path> mr <iid> update [--title TITLE] [--description DESC]` | Update MR title/description |
| `gl.py project <path> commits [--author X] [--since DATE] [--until DATE]` | List commits |
| `gl.py project <path> branches [--search PATTERN]` | List branches |
| `gl.py project <path> pipelines [--ref REF] [--status STATUS]` | List pipelines |
| `gl.py project <path> issues [--state STATE] [--labels L1,L2]` | List issues |
| `gl.py events [--after DATE] [--before DATE]` | User activity feed |
| `gl.py groups search <query>` | Search groups |
| `gl.py group <id> projects [--search QUERY]` | List group projects |

All date arguments use `YYYY-MM-DD` format. Most list commands accept `--limit N` (default 20).

Project `<path>` accepts `group/project-name` or numeric ID.

## Typical Workflows

### Check what I did today
```bash
gl.py events --after 2026-04-21 --limit 30
```

### Find a project and list open MRs
```bash
gl.py projects search "group"
gl.py project group/project-name mrs
```

### MRs assigned to me or where I'm reviewer
```bash
gl.py project group/project-name mrs --assignee myusername --state opened
gl.py project group/project-name mrs --reviewer myusername --state opened
```

### Review a specific MR
```bash
gl.py project group/project-name mr 258
gl.py project group/project-name mr 258 changes
gl.py project group/project-name mr 258 approvals
gl.py project group/project-name mr 258 notes
```

### Post a comment on an MR
```bash
# General comment
gl.py project group/project-name mr 258 comment "LGTM, minor nit on line 42"

# Diff note on a specific file and line
gl.py project group/project-name mr 258 comment "This could be simplified" --file src/main.go --line 55

# Multiline comment from stdin
echo "## Review Summary\n\nLooks good overall." | gl.py project group/project-name mr 258 comment -
```

### Resolve MR discussions
```bash
# Resolve the discussion containing note #12345
gl.py project group/project-name mr 258 resolve 12345

# Resolve all unresolved discussions at once
gl.py project group/project-name mr 258 resolve --all
```

### Update an MR
```bash
gl.py project group/project-name mr 258 update --title "New title"
gl.py project group/project-name mr 258 update --description "Updated description"
```

### Recent commits by author
```bash
gl.py project group/project-name commits --author "Eugene Agafonov" --since 2026-04-14
```

## Run `gl.py --help` for full usage details.
