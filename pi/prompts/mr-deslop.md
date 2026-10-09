---
description: Review an MR for AI comment slop and diff-restating commit messages, and post findings as review comments
argument-hint: "<MR URL>"
---

# MR Deslop Review

Focused MR review with two passes: comment slop and commit messages. Review only —
never edit the MR's code. Findings are posted as MR comments after explicit approval.

## Skills

Load and follow these skills:
- **gitlab-explorer** — `gl.py` for all GitLab API calls (resolve `<gl.py>` from the skill directory)
- **deslopify-comments** — slop patterns, keep rules, and ambiguity rule for classifying comments
- **agentic-review** — clone/worktree setup, posting procedure, cleanup

## Step 1 — Setup

Parse the GitLab project path and MR IID from `$1`. If no MR URL was given, ask for it and stop.

Follow the `agentic-review` skill: clone the repo into the current working directory,
fetch the source branch, and create the worktree at `.worktrees/review-mr<iid>`
(detached at `origin/<source_branch>`).

Gather via `gl.py`:
- MR details (title, description, source/target branch) — `project <path> mr <iid>`
- Changed file list — `project <path> mr <iid> changes`
- MR commits — `git log --reverse origin/<target_branch>..origin/<source_branch>`

## Step 2 — Scope

Comment findings are limited to comment lines the MR **added or modified**
(diff `origin/<target_branch>...origin/<source_branch>`, added lines only).

Pre-existing slop on unchanged lines of touched files is NOT a finding — list it in a
separate "Follow-up candidates" section of the report.

## Step 3 — Comment-slop pass

Apply the `deslopify-comments` skill rules to every added/modified comment line in
every changed file (skip vendored/generated/binary files). Classify each comment:
keep / rewrite / delete, per the skill's slop patterns (change-history narration,
restating the code, section-divider theatre, conversational/apologetic, tutorial
padding, redundant docstrings).

Read full files from the worktree so classification judges whether the comment adds
information the code cannot state — a diff hunk alone cannot show this.

Respect the skill's ambiguity rule: a comment that might encode unverifiable knowledge
(business rule, vendor quirk, measurement) is kept and listed as a question, never
flagged for deletion.

## Step 4 — Commit-message audit

For each commit in the MR, flag the commit message if it:
- merely restates the diff hunk-by-hunk or line-by-line, or
- narrates mechanical side effects (renumbering, whitespace, formatting) as if they
  were the point of the change.

A good message must state:
1. the issue being fixed,
2. the root cause,
3. a high-level description of the fix.

For each flagged commit, suggest a rewritten message as feedback only — never rewrite
history, never push. Subject style: match the repo's existing history
(`<scope>: <imperative summary>` / `FOOBAR-XXXXX: ...` / Conventional Commits).

Claims in a commit body must be verifiable — challenge anything you cannot confirm
against the diff or the worktree.

## Step 5 — Report and post

Structure:

1. **Summary** — what the MR does, 2-3 sentences (for the user only, never posted)
2. **Style — comment slop** — one finding per comment: `file:line`, quoted comment,
   slop pattern, proposed action (delete, or suggested rewrite text)
3. **Process — commit messages** — one finding per flagged commit, with the suggested
   rewritten message
4. **Questions** — kept-but-suspicious comments needing author input
5. **Follow-up candidates** — pre-existing slop on unchanged lines

State explicitly "No findings" for any pass that came up empty.

Then follow the `agentic-review` skill's posting procedure:
- ask which findings to post (all / critical-important only / select / none) and wait
- comment-slop findings: inline diff notes anchored to the exact `file:line`,
  tagged with the `:robot:` reaction; if the anchor line is not a valid diff position,
  re-anchor to the nearest changed line and reference the original line in the note
- commit-message findings: a single general MR note (they have no diff anchor),
  `:robot:`-tagged
- never post the summary as a comment

After posting, confirm with a compact per-file table of the posted notes
(file, line, note ID, finding).

## Step 6 — Cleanup

```bash
git worktree remove ../.worktrees/review-mr<iid>
cd ..
rm -rf <repo-dir>
```
