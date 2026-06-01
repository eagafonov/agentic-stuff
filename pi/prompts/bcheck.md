---
description: Check beads issues against current codebase
argument-hint: "[optional: filter like P1, P2, or specific issue IDs]"
---
You are the agent to check beads issue completion.
Go through open beads issues and check if each issue is resolved in the code on the current branch.

Report each issue with one of these statuses:
- ✅ Fixed — clear indication the issue is fixed in the code
- ❌ Present — the issue is clearly still present in the code
- ⚠️ Inconclusive — code significantly updated, needs deeper inspection

Present results as a table with: issue id, issue title, check status.

NEVER try to fix any issue. NEVER change the code. NEVER close issues automatically — ask which ones to close.

Filter/scope (use if provided, ignore if empty): $@
