---
name: agentic-review
description: Use when performing an agentic MR review — cloning a repo, setting up a worktree, reviewing code, and posting findings to GitLab
---

# Agentic MR Review

## Overview

End-to-end procedure for performing code reviews of GitLab merge requests in an isolated, reproducible workspace. Covers repository checkout, worktree setup, review execution, and comment posting.

## When to Use

- Performing a full code review of a GitLab merge request
- Asked to review an MR given its URL or project/MR identifiers

## Prerequisites

Load these skills before starting:

- **gitlab-explorer** — provides `gl.py` for all GitLab API interactions
- **merge-request-review** — provides the structured review methodology (phases, severity levels, output format)

## Process

### Step 1: Identify the Project and MR

Extract from the MR URL or user input:
- **GitLab host** (e.g. `gitlab.com`, `gitlab.example.com`)
- **Project path** (e.g. `my-group/my-project`)
- **MR IID** (the merge request number)

### Step 2: Clone the Repository

**Always clone into the current working directory.** Do NOT look for existing clones outside the current folder.

```bash
git clone <repo-clone-url> <repo-dir>
```

The clone URL depends on the GitLab instance. Use SSH when available:
```bash
git clone ssh://git@<host>:<port>/<project-path>.git
# or for standard port:
git clone git@<host>:<project-path>.git
```

### Step 3: Set Up a Worktree for the Source Branch

```bash
cd <repo-dir>
git fetch origin <source_branch>
git worktree add ../.worktrees/review-mr<iid> origin/<source_branch> --detach
```

The worktree goes into `.worktrees/` as a sibling to the clone root. This keeps everything self-contained.

### Step 4: Perform the Review

Follow the **merge-request-review** skill process:
1. Gather MR metadata and changed files via `gl.py`
2. Fetch diffs in batches
3. Read full files from the worktree for context
4. Read related unchanged code
5. Search for what's missing (tests, docs, migrations)
6. Synthesize findings with severity levels

### Step 5: Present Findings to the User

Present the structured review (summary, strengths, issues, questions, verdict).

### Step 6: Ask Before Posting Comments

**NEVER post comments without explicit user consent.** After presenting findings, ask:

> Review complete. How would you like to post the findings as MR comments?
> 1. **Post all** — post every finding (critical, important, minor, nits)
> 2. **Critical/important only** — skip minor and nit findings
> 3. **Select specific** — I'll list the findings and you choose which ones to post
> 4. **Don't post** — skip posting

Wait for the user's choice before calling `gl.py … comment`.

**NEVER post the review summary/overview as an MR comment.** Only post individual findings (issues, questions). The summary is for the user only.

### Step 7: Clean Up

After the review is complete (and any comments posted), remove the worktree and optionally the clone:

```bash
cd <repo-dir>
git worktree remove ../.worktrees/review-mr<iid>
cd ..
rm -rf <repo-dir>
```

## Key Rules

| Rule | Rationale |
|------|-----------|
| Clone into CWD only | Reproducible, no stale state from prior reviews |
| Worktree in `.worktrees/` sibling dir | Keeps workspace self-contained |
| Always ask before posting | Reviewer controls what goes to GitLab |
| Never post summaries as comments | Summaries are for the human, not the MR thread |
| Use `gl.py` for all API calls | Single consistent interface to GitLab |

## Directory Layout After Setup

```
<cwd>/
├── <repo-dir>/          # fresh clone
└── .worktrees/
    └── review-mr<iid>/  # detached worktree at source branch
```
