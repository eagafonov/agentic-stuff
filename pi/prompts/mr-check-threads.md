---
description: Check and resolve addressed MR threads
---

Check the unresolved review threads on the MR we are working on, and resolve the ones that are addressed.
If no MR is clear from the conversation, ask for it and stop.

Use the `gitlab-explorer` skill (`gl.py`) for all GitLab calls.

1. List the MR threads with `discussions`.
2. For each unresolved thread, verify the fix against the code at the MR's current pushed head, not the
   thread state or the author's reply. Cite the commit and `file:line` that addresses it.
   Run targeted build/tests if the fix changes behaviour.
3. Classify each thread:
   - **addressed**: the fix is verified in the code
   - **not addressed**: no fix, or the fix is partial or wrong; say what is missing
   - **needs decision**: a design question or open discussion; leave it for me
4. Report a table: thread (note ID, `file:line`), summary, status, evidence, proposed reply.
   Wait for my approval before posting anything.
5. On approval, for each addressed thread, reply inside the existing thread (`reply <note_id>`, never a new
   diff note) citing the fix, with `--reaction robot`, then `resolve <note_id>`.
   Do not resolve threads that are not addressed or need a decision.

Never edit code, commit, or push as part of this prompt.
