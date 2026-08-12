---
description: Deslopify code comments in files touched by a commit, commit range, or pending changes
argument-hint: "[staged|unstaged|dirty|commit ref or range (default HEAD)] [stage|commit|keep (default keep)]"
---

Load and follow the `deslopify-comments` skill.

Target: `${1:-HEAD}` — one of:
- `staged` / `--staged` / `--cached` / `index` — files currently staged in the index
- `unstaged` / `worktree` — files modified in the working tree but not staged
- `dirty` / `all` — union of staged and unstaged files
- a single commit ref (`HEAD`, `abc1234`)
- a range (`main..HEAD`, `abc1234..def5678`, `HEAD~3..HEAD`)

## Step 1 — Resolve the file list

```bash
git diff --cached --name-only --diff-filter=d                  # staged
git diff --name-only --diff-filter=d                           # unstaged
git diff HEAD --name-only --diff-filter=d                      # dirty (staged + unstaged)
git diff --name-only --diff-filter=d ${1:-HEAD}^..${1:-HEAD}   # single commit
git diff --name-only --diff-filter=d ${1:-HEAD}                # if it is a range
```

Pick the correct form for the argument given. If it contains `..` treat it as a range.
For a root commit with no parent, fall back to `git show --name-only --diff-filter=d`.
Untracked files are not included unless the caller explicitly asks for them.

If the resolved list is empty, say so and stop — do not silently fall back to `HEAD`.

Filter out: deleted files, binary files, vendored/generated paths, lock files,
and files with no comment syntax.

Report the resolved file list before editing.

## Step 2 — Deslopify

Apply the `deslopify-comments` skill to each file. Comments only.
Do NOT build, compile, lint, or test — assume the code is valid and correct.

## Step 3 — Staging / committing

Second argument `${2:-keep}` controls this:
- `keep` (default) — leave edits in the working tree, unstaged and uncommitted
- `stage` — `git add` the modified files, do not commit
- `commit` — stage and commit with a message like
  `chore: deslopify comments in <scope>` (no attribution/co-author trailers)

If the argument is absent or unrecognized, use `keep` and state that clearly.

**When the target was `staged` or `dirty`**: `keep` leaves each file split into a staged
(original) part and an unstaged (deslopified) part. Usually not what the caller wants, so:
- state explicitly that the comment edits sit unstaged on top of the staged content
- recommend `stage` to fold them back into the index
- for `stage`, `git add` exactly the files you edited — never `git add -A`
- for `commit` with a `staged`/`dirty` target, warn that the pre-existing staged changes
  would be committed too, and ask before committing

## Step 4 — Report

Output the skill's report format (per-file counts, notable rewrites,
kept-but-suspicious comments, code smells noticed but not fixed).
