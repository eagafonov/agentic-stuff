---
description: Commit staged changes
---
Inspect staged changes and commit. Ignore uncommitted changes. Generate a commit message describing the changes.
Use 'git commit' to commit the changes.
If parameters are provided, treat them as hints for the commit message (e.g. 'csc Prefix with Jira ticket DRIVE-12345' should include that ticket ID in the commit subject).

When reviewing staged changes:
- Skip obvious/mechanical changes (renumbering sections, whitespace, formatting adjustments) that are a natural consequence of the primary change
- Focus the commit message on the substantive/intentional changes only
