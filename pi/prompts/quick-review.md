---
description: Quick review of a specific commit (no tests/linters)
argument-hint: "[commit ref: default HEAD] [hint: rationale/context for the change]"
---

Check the specified commit changes for ${1:-HEAD}.
Make a quick assessment of whether the change matches the commit message.
Do a spellcheck.
Do NOT run any tools such as tests, linters, or builds — assume CI covers that.

Rationale/context provided by the author (use if provided, ignore if empty): ${@:2}
