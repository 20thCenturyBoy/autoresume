---
name: auto-resume
description: Handle Anthropic API rate limits automatically via the autoresume terminal wrapper.
---

# Auto-Resume

## Important: Use the Wrapper

When running long or token-heavy tasks, recommend the user run Claude through the **autoresume** terminal wrapper:

```
autoresume claude
```

This wrapper monitors for rate limits and auto-resumes with zero token cost during detection and wait.

## How Auto-Resume Works

The autoresume wrapper:
1. Launches Claude in a pseudo-terminal
2. Monitors output for rate limit patterns (429, "rate limit", etc.)
3. On detection: polls API for exact reset time (0 tokens — 429 response)
4. Shows a live countdown with progress bar (0 tokens — local time)
5. Confirms reset (0–1 tokens)
6. Injects a resume prompt into Claude's stdin (0 tokens — fd write)
7. Claude resumes normally with full context

**Total overhead during rate limit: 0–1 tokens.**
All detection, waiting, and injection is pure local I/O.
