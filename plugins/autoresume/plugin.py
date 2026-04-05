#!/usr/bin/env python3
"""
Auto-Resume MCP Server (supplementary).

This provides proactive tools for Claude to check rate limit status
before starting long tasks. The main auto-resume mechanism is the
terminal wrapper in bin/autoresume — it handles rate limits reactively
with zero token cost.

Tools:
  check_rate_limit — see current API quota and reset times
"""

import asyncio
import json
import os
import sys
from http.client import HTTPSConnection


class RateLimitChecker:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def check(self):
        if not self.api_key:
            return {
                "limited": False,
                "retry_after": 0,
                "reset_at": "",
                "error": "No ANTHROPIC_API_KEY set",
            }

        try:
            conn = HTTPSConnection("api.anthropic.com", timeout=10)
            body = json.dumps(
                {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "."}],
                }
            )
            conn.request(
                "POST",
                "/v1/messages",
                body=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            resp = conn.getresponse()
            status = resp.status

            retry_after = int(resp.getheader("retry-after", 0))
            remaining = {
                "tokens_remaining": resp.getheader(
                    "anthropic-ratelimit-tokens-remaining", ""
                ),
                "requests_remaining": resp.getheader(
                    "anthropic-ratelimit-requests-remaining", ""
                ),
                "tokens_reset": resp.getheader(
                    "anthropic-ratelimit-tokens-reset", ""
                ),
                "requests_reset": resp.getheader(
                    "anthropic-ratelimit-requests-reset", ""
                ),
            }

            if status == 429:
                from datetime import datetime, timezone

                reset_at = ""
                if retry_after > 0:
                    ts = datetime.now(timezone.utc).timestamp() + retry_after
                    reset_at = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                return {
                    "limited": True,
                    "retry_after": retry_after if retry_after > 0 else 60,
                    "reset_at": reset_at,
                    "remaining": remaining,
                    "error": "Rate limit hit (HTTP 429)",
                }

            return {
                "limited": False,
                "retry_after": 0,
                "reset_at": "",
                "remaining": remaining,
                "error": "",
            }

        except Exception as e:
            return {
                "limited": False,
                "retry_after": 0,
                "reset_at": "",
                "error": str(e),
            }


async def run():
    checker = RateLimitChecker()
    loop = asyncio.get_event_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = req.get("method", "")
            msg_id = req.get("id")
            params = req.get("params", {})

            result = await handle(method, msg_id, params, checker)
            if result is not None:
                print(json.dumps(result), flush=True)

        except (KeyboardInterrupt, EOFError):
            break


async def handle(method, msg_id, params, checker):
    if method == "initialize":
        return ok(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "auto-resume-check", "version": "1.0.0"},
        })

    if method == "tools/list":
        return ok(msg_id, {
            "tools": [
                {
                    "name": "check_rate_limit",
                    "description": (
                        "Check if the Anthropic API is currently rate limited. "
                        "Returns remaining quota and exact reset time. "
                        "Use this proactively before starting a long task to "
                        "avoid hitting rate limits mid-work."
                    ),
                    "inputSchema": {"type": "object", "properties": {}},
                }
            ]
        })

    if method == "tools/call":
        name = params.get("name", "")
        if name == "check_rate_limit":
            r = checker.check()
            return ok(msg_id, {
                "content": [{"type": "text", "text": format_check(r)}]
            })

    if method in ("notifications/initialized",):
        return None

    if msg_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }
    return None


def ok(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def format_check(r):
    if r["error"] and not r["limited"]:
        return f"⚠️ {r['error']}"
    if r["limited"]:
        m, s = divmod(r["retry_after"], 60)
        w = f"{m}m {s}s" if m else f"{s}s"
        return (
            f"⚠️  RATE LIMIT ACTIVE\n"
            f"   Reset in: {w} (at {r.get('reset_at', 'calculating...')})\n"
            f"   Consider running `autoresume` instead of working directly."
        )
    rem = r.get("remaining", {})
    parts = ["✅ Rate limit clear"]
    if rem.get("tokens_remaining"):
        parts.append(f"tokens: {rem['tokens_remaining']}")
    if rem.get("requests_remaining"):
        parts.append(f"requests: {rem['requests_remaining']}")
    return "  ".join(parts)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        checker = RateLimitChecker()
        result = checker.check()
        print(format_check(result))
        sys.exit(1 if result.get("limited") else 0)
    else:
        asyncio.run(run())
