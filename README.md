# autoresume

Terminal wrapper that automatically resumes [Claude Code](https://claude.ai/code) sessions when API rate limits are hit. Zero tokens wasted during detection or wait.

## Install

```bash
curl -sSfL https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/plugins/autoresume/install.py | python3 -
```

## Use

Instead of `claude`, run `autoresume claude`:

```bash
autoresume claude
autoresume claude "refactor the auth module"
autoresume claude --dangerously-skip-approval
```

Works exactly like `claude` — but when a rate limit hits, it handles it automatically.

## What You See

When rate limited:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  RATE LIMIT HIT
   Waiting: 2m 14s (resets at 14:37:22)
   🔄 Will auto-resume with:
      "Please continue exactly where you left off..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ [████████░░░░░░░░░░░░░░░░░░] 35% (1m 28s remaining)
```

When cleared:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ RATE LIMIT RESET — Resuming session now
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Claude then continues exactly where it stopped. No context lost.

## How It Works

1. **Launches Claude** in a pseudo-terminal
2. **Relays I/O** bidirectionally between user and Claude
3. **Scans output** for rate limit patterns (429, "rate limit", etc.) — **0 tokens**
4. **Polls API** for exact reset time via `retry-after` header — **0 tokens** (429 response)
5. **Shows countdown** with live progress bar — **0 tokens** (local time + sleep)
6. **Confirms reset** — **0–1 tokens**
7. **Injects resume prompt** into Claude's stdin — **0 tokens** (fd write, like typing)
8. **Claude resumes** with full context — normal token usage (rate limit cleared)

**Total overhead during rate limit: 0–1 tokens.**

## Uninstall

```bash
rm -f ~/.local/bin/autoresume
```

## Requirements

- Python 3.7+ (stdlib only, no pip install)
- Mac / Linux
- `ANTHROPIC_API_KEY` in environment (already required for Claude Code)
