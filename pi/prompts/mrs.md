---
description: Check open MRs for approvals across multiple gitlab epos
argument-hint: "[my|review|all]"
---

# Check Open Merge Requests

Check open MRs across multiple repositories using the `gitlab-explorer` skill and present results as tables.

**Skill:** Load `gitlab-explorer` skill and use its `gl.py` script (resolve the script path from the skill directory: `<skill-dir>/scripts/gl.py`).

**GitLab username:** Use the value of the `GITLAB_USERNAME` environment variable (resolve it at runtime via `$GITLAB_USERNAME`).

## Scope

Argument `$1` controls what to check (default: `all`):
- `my` — Only my authored MRs
- `review` — Only MRs where I need to review (authored by others)
- `all` — Both tables

## Repositories to Check

Discover the list of repositories (as `group/project` paths) using these sources (in priority order):

1. **`gitlab-projects.md`** — look for this file in the current working directory
2. **`git remote -v`** — if no project list file is found, extract the GitLab project path from the remote URL:
   - SSH: `origin	git@gitlab.example.com:group/project.git` → `group/project`
   - HTTPS: `origin	https://gitlab.example.com/group/project.git` → `group/project`

Parse the project list before proceeding. If only one project is found (from git remote), use that single project.

## Procedure

### Table 1: My Open MRs (authored by me)

For each repo above, run:
```bash
python3 <skill-dir>/scripts/gl.py project <group/project> mrs --author $GITLAB_USERNAME --state opened --limit 10
```

For each MR found, get approval status:
```bash
python3 <skill-dir>/scripts/gl.py project <group/project> mr <iid> approvals
```

Present as table titled "My Open MRs":

| MR | Repo | Title | Draft | Approved by | Approvals needed |
|----|------|-------|-------|-------------|-----------------|

- MR column: `!IID`
- Draft: yes/no (check if title starts with "Draft:")
- Approved by: list of usernames from approvals, or "none"
- Approvals needed: `approvals_left` from approvals response

### Table 2: MRs Where I'm Assignee or Reviewer (authored by others)

For each repo above, run TWO queries and merge results (dedup by MR iid):
```bash
python3 <skill-dir>/scripts/gl.py project <group/project> mrs --assignee $GITLAB_USERNAME --state opened --limit 10
python3 <skill-dir>/scripts/gl.py project <group/project> mrs --reviewer $GITLAB_USERNAME --state opened --limit 10
```

Filter results to include only MRs where author is NOT `$GITLAB_USERNAME`.

Present as table titled "MRs Where I'm Assignee or Reviewer":

| MR | Repo | Title | Author | My role |
|----|------|-------|--------|---------|

- MR column: `!IID`
- My role: assignee, reviewer, or both (based on which query returned it)

## Batching

- Run queries for all repos in parallel (batch bash calls)
- Process approval checks only for my MRs (Table 1)
- If a repo has no open MRs, skip it silently

## Output Format

- Use markdown tables
- If either table has no results, state "No open MRs found"
- Sort by repo name within each table
