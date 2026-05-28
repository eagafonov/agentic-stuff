---
name: merge-request-review
description: Use when reviewing a GitLab merge request for code quality, correctness, and design issues before approving or requesting changes
---

# Merge Request Review

## Overview

Structured process for reviewing GitLab merge requests. Combines diff analysis with full-file context reading and related-code comparison to produce thorough, actionable reviews.

**Core principle:** Diffs show what changed; full files show whether the change makes sense in context. Always read both.

## When to Use

- Reviewing any GitLab merge request
- Asked to provide code review feedback on an MR
- Preparing review comments before approving or requesting changes

## Prerequisites

Load the **gitlab-explorer** skill before starting. It provides `gl.py` — the only tool used for all GitLab API calls in this process.

```
skill: gitlab-explorer   # read SKILL.md, note the gl.py path and invocation pattern
```

All `gl.py` commands below follow the form:
```bash
python3 <skill-dir>/scripts/gl.py project <project-id-or-path> ...
```

## Process

### Phase 1: Gather MR Metadata and Changed Files

Fetch in parallel (no dependencies between these calls) using `gl.py`:

```bash
# MR details: title, author, branches, status, description
python3 <gl.py> project <id> mr <iid>

# Changed file list: paths and change type (M/A/D/R)
python3 <gl.py> project <id> mr <iid> changes
```

Note: the correct subcommand for the file list is `changes`, **not** `files`.

This establishes scope before reading any code.

### Phase 2: Set Up Isolated Worktree

Check out the MR's source branch into a local worktree for full filesystem access.

**Why a worktree:** GitLab diffs only show changed hunks. A worktree gives access to complete files with surrounding context — essential for judging whether changes integrate correctly with existing code.

Use the `using-git-worktrees` skill if available, otherwise:

```bash
git fetch origin <source_branch>
git worktree add .worktrees/review-mr<iid> origin/<source_branch> --detach
```

### Phase 3: Fetch Diffs in Batches

While the worktree is being set up, fetch the full diff via `gl.py`:

```bash
# Full unified diff for all changed files
python3 <gl.py> project <id> mr <iid> changes --all
```

Process in parallel batches (3-5 files per batch). Separate batches by file type when practical:
- Core logic files (the substantive changes)
- Config/dependency files (package manifests, lock files, env templates)

Skip reading large generated files (lock files) in detail — scan for unexpected additions only.

### Phase 4: Read Full Files from Worktree

Read complete contents of all changed source files from the worktree. Focus on:
- **New files** — read entirely, these are the core of most MRs
- **Modified files** — read enough surrounding context to understand the change (not just the diff hunks)
- **Entry points and initialization code** — understand the call chain

### Phase 5: Read Related Unchanged Code

This is the step most reviewers skip and shouldn't.

Identify files that are architecturally related but not changed in this MR:
- **Analogous modules** — if the MR adds `otel_init.py`, read the existing `sentry_init.py` to judge pattern consistency
- **Callers/consumers** — code that will use the new/changed code
- **Shared utilities** — to spot duplication or missed reuse opportunities

### Phase 6: Search for What's Missing

Actively look for gaps:
- **Tests** — search for test files covering the changed modules. Absence is a finding.
- **Documentation** — check if new env vars, configs, or APIs are documented
- **Migration/upgrade concerns** — breaking changes, deprecations

### Phase 7: Clean Up Worktree

Remove the worktree after reading is complete:

```bash
git worktree remove .worktrees/review-mr<iid>
```

### Phase 8: Synthesize Review

Organize findings by severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| **Critical** | Bugs, security issues, data loss risk | Must fix before merge |
| **Important** | Design issues, fragility, non-standard patterns | Should fix, discuss if disagreed |
| **Minor** | Code style, duplication, missing tests | Nice to fix, not blocking |
| **Nit** | Naming, comments, cosmetic | Optional |

Structure the review:
1. **Summary** — what the MR does in 2-3 sentences
2. **Strengths** — what's done well (be specific, not flattering)
3. **Issues** — grouped by severity with file:line references
4. **Questions** — things that need clarification from the author
5. **Verdict** — approve / approve with suggestions / request changes

## Parallel I/O Strategy

Maximize concurrent API calls where there are no data dependencies:

```
Phase 1:  [MR details] + [changed file list]        <- parallel
Phase 2:  [create worktree]                          <- sequential (needs branch name from phase 1)
Phase 3:  [diff batch 1] + [diff batch 2]            <- parallel (during worktree setup)
Phase 4:  [read file 1] + [read file 2] + ...        <- parallel
Phase 5:  [read related file 1] + [read related 2]   <- parallel
```

## Common Mistakes

### Only reading diffs
Diffs without context miss integration problems. A function that looks correct in isolation may conflict with surrounding code.

### Skipping related unchanged files
Pattern consistency and duplication can only be judged by reading the code the MR is modeled after.

### Not searching for missing things
The absence of tests or documentation is as important as code quality issues.

### Severity inflation
Not every finding is critical. Over-severity erodes trust. Reserve "critical" for actual bugs and security issues.

### Reviewing generated files in detail
Lock files, compiled outputs, and auto-generated code should be scanned for unexpected entries, not read line-by-line.
