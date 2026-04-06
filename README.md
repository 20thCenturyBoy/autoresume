# autoresume

Terminal wrapper that automatically resumes [Claude Code](https://claude.ai/code) sessions when API rate limits are hit. Zero tokens wasted during detection or wait.

## Install

**One command in your terminal:**

```bash
curl -sSfL https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/plugins/autoresume/install.py | python3 -
```

That's it. The `autoresume` command is now available.

**Alternatively, from Claude Code:**

```
/plugin marketplace add 20thCenturyBoy/autoresume
/plugin install autoresume@20thCenturyBoy
```

Then run the one-liner above to install the wrapper.

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

```
User ──keystrokes──▶ [autoresume wrapper] ──stdin──▶ Claude
                       (monitors output)
User ◀──terminal─── [autoresume wrapper] ◀──stdout── Claude
                       (scans for 429/rate limit)
```

1. **Launches Claude** in a pseudo-terminal (so Claude runs normally)
2. **Relays I/O** bidirectionally between user and Claude
3. **Scans output** for rate limit patterns (429, "rate limit", etc.) — **0 tokens**
4. **Polls API** for exact reset time via `retry-after` header — **0 tokens** (429 response)
5. **Shows countdown** with live progress bar — **0 tokens** (local time + sleep)
6. **Confirms reset** — **0–1 tokens**
7. **Injects resume prompt** into Claude's stdin — **0 tokens** (fd write, like typing)
8. **Claude resumes** with full context — normal token usage (rate limit cleared)

**Total overhead during rate limit: 0–1 tokens.**

## Standalone Rate Limit Check

```bash
python plugin.py --check
```

## Uninstall

```bash
python3 -c "
from pathlib import Path
w = Path.home() / '.local/bin/autoresume'
if w.is_symlink() or w.exists(): w.unlink()
print('✅ Removed')
"
```

## Requirements

- Python 3.7+ (stdlib only, no pip install)
- Mac / Linux (uses `pty` for terminal emulation)
- Windows: works via subprocess pipes (some CLI differences possible)
- `ANTHROPIC_API_KEY` in environment (already required for Claude Code)
