---
description: Commit staged changes
argument-hint: "[commit-message hints]"
---
Inspect staged changes and commit. Ignore uncommitted changes. Generate a commit message describing the changes.
Use 'git commit' to commit the changes.
User-provided commit message hints: ${@:-none}
Treat the hints as requirements for the commit message (e.g. a hint like 'Prefix with Jira ticket FOOBAR-12345' means that ticket ID must appear in the commit subject).

When reviewing staged changes:
- Skip obvious/mechanical changes (renumbering sections, whitespace, formatting adjustments) that are a natural consequence of the primary change
- Focus the commit message on the substantive/intentional changes only
- If project has AGENTS.md with commit guidelines, follow them (scope, prefix conventions, etc.)
