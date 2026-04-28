---
description: Update last commit message based on changes
argument-hint: "[hint]"
---
Check changes since the last commit and amend the commit message based on those changes. Use 'git diff HEAD^..HEAD' to get the changes. Preserve Gerrit's "Change-Id:" line if it exists. Do not add a Change-Id: line if it does not exist.

Hint/reason for the commit message (use if provided, ignore if empty): $@
