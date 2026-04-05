#!/usr/bin/env python3
"""
Tests for the autoresume wrapper.

Runs with: python3 tests/test_autoresume.py
No external dependencies — uses only stdlib (unittest, unittest.mock).
"""

import importlib.machinery
import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# ── Load modules by file path ────────────────────────────────────────────────

ROOT = os.path.join(os.path.dirname(__file__), "..")
PLUGIN = os.path.join(ROOT, "plugins", "autoresume")


def load(path):
    spec = importlib.util.spec_from_file_location(
        path, path,
        loader=importlib.machinery.SourceFileLoader(path, path),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wrapper = load(os.path.join(PLUGIN, "bin", "autoresume"))
plugin = load(os.path.join(PLUGIN, "plugin.py"))
installer = load(os.path.join(PLUGIN, "install.py"))


# ═══════════════════════════════════════════════════════════
# Test 1: OutputScanner
# ═══════════════════════════════════════════════════════════

class TestOutputScanner(unittest.TestCase):

    def setUp(self):
        self.s = wrapper.OutputScanner()

    def test_429(self):
        self.s.feed(b"HTTP error 429 Too Many Requests")
        self.assertTrue(self.s.triggered)

    def test_rate_limit_text(self):
        self.s.feed(b"Error: rate limit exceeded")
        self.assertTrue(self.s.triggered)

    def test_rate_limited(self):
        self.s.feed(b"Status: rate_limited")
        self.assertTrue(self.s.triggered)

    def test_too_many_requests(self):
        self.s.feed(b"Too many requests, slow down")
        self.assertTrue(self.s.triggered)

    def test_ratelimit_error(self):
        self.s.feed(b"RateLimitError: quota exceeded")
        self.assertTrue(self.s.triggered)

    def test_case_insensitive(self):
        self.s.feed(b"RATE LIMIT EXCEEDED")
        self.assertTrue(self.s.triggered)

    def test_normal_output(self):
        self.s.feed(b"I'll help you refactor auth.")
        self.assertFalse(self.s.triggered)

    def test_split_chunks(self):
        self.s.feed(b"HTTP error ")
        self.s.feed(b"429 Too Many Requests")
        self.assertTrue(self.s.triggered)

    def test_once_only(self):
        self.s.feed(b"429")
        self.assertTrue(self.s.triggered)
        self.s.buffer = b""
        self.assertFalse(self.s.feed(b"more"))

    def test_buffer_roll(self):
        self.s.feed(b"X" * 2048)
        self.assertFalse(self.s.triggered)
        self.s.feed(b"429")
        self.assertTrue(self.s.triggered)


# ═══════════════════════════════════════════════════════════
# Test 2: Rate limit checker
# ═══════════════════════════════════════════════════════════

class TestWrapperCheck(unittest.TestCase):

    def test_no_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            limited, _, _ = wrapper.check_rate_limit()
        self.assertFalse(limited)

    def test_429_mocked(self):
        mock_resp = MagicMock()
        mock_resp.status = 429
        mock_resp.getheader.side_effect = lambda h, d="": {
            "retry-after": "134",
            "anthropic-ratelimit-tokens-remaining": "0",
        }.get(h, d)

        mock_conn = MagicMock()
        mock_conn.return_value.getresponse.return_value = mock_resp

        with patch.object(wrapper, "HTTPSConnection", mock_conn):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, retry_after, reset_at = wrapper.check_rate_limit()

        self.assertTrue(limited)
        self.assertEqual(retry_after, 134)
        self.assertTrue(reset_at)

    def test_200_mocked(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.getheader.side_effect = lambda h, d="": d

        mock_conn = MagicMock()
        mock_conn.return_value.getresponse.return_value = mock_resp

        with patch.object(wrapper, "HTTPSConnection", mock_conn):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, retry_after, _ = wrapper.check_rate_limit()

        self.assertFalse(limited)
        self.assertEqual(retry_after, 0)

    def test_error_failsafe(self):
        with patch.object(wrapper, "HTTPSConnection", side_effect=Exception("no net")):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, _, _ = wrapper.check_rate_limit()
        self.assertFalse(limited)

    def test_default_fallback(self):
        mock_resp = MagicMock()
        mock_resp.status = 429
        mock_resp.getheader.side_effect = lambda h, d="": d

        mock_conn = MagicMock()
        mock_conn.return_value.getresponse.return_value = mock_resp

        with patch.object(wrapper, "HTTPSConnection", mock_conn):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, retry_after, _ = wrapper.check_rate_limit()

        self.assertTrue(limited)
        self.assertEqual(retry_after, wrapper.DEFAULT_WAIT)


# ═══════════════════════════════════════════════════════════
# Test 3: Plugin MCP server (formatting helpers only)
# ═══════════════════════════════════════════════════════════

class TestMCPPlugin(unittest.TestCase):

    def test_ok_helper(self):
        r = plugin.ok(42, {"x": 1})
        self.assertEqual(r["jsonrpc"], "2.0")
        self.assertEqual(r["id"], 42)
        self.assertEqual(r["result"]["x"], 1)

    def test_format_limited(self):
        r = {"limited": True, "retry_after": 120, "reset_at": "14:37:22",
             "remaining": {}, "error": "Rate limit hit"}
        text = plugin.format_check(r)
        self.assertIn("RATE LIMIT", text)
        self.assertIn("2m 0s", text)

    def test_format_clear(self):
        r = {"limited": False, "retry_after": 0, "reset_at": "",
             "remaining": {}, "error": ""}
        text = plugin.format_check(r)
        self.assertIn("clear", text.lower())


# ═══════════════════════════════════════════════════════════
# Test 4: Integration / display / structure
# ═══════════════════════════════════════════════════════════

class TestIntegration(unittest.TestCase):

    def test_scanner_realistic(self):
        s = wrapper.OutputScanner()
        s.feed(b"I'm refactoring auth...")
        self.assertFalse(s.triggered)
        s.feed(b"\nError: 429 Too Many Requests\nrate limit exceeded\n")
        self.assertTrue(s.triggered)

    def test_resume_prompt(self):
        p = wrapper.RESUME_PROMPT
        self.assertIn("continue", p.lower())
        self.assertIn("resume", p.lower())

    def test_display_functions(self):
        wrapper.show_rate_limit_banner("2m 14s", "14:37:22")
        wrapper.show_countdown(50.0, 67)
        wrapper.show_reset_clear()
        wrapper.show_max_retries(10)

    def test_files_exist(self):
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "bin", "autoresume")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "plugin.py")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "install.py")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "skills", "autoresume", "SKILL.md")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "hooks", "hooks.json")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "hooks", "check_wrapper.sh")))
        self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "hooks", "setup.sh")))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "README.md")))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
        self.assertFalse(os.path.isfile(os.path.join(PLUGIN, ".mcp.json")))

    def test_plugin_json_valid(self):
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")) as f:
            d = json.load(f)
        self.assertEqual(d["name"], "auto-resume")
        self.assertIn("skills", d)
        self.assertIn("hooks", d)

    def test_marketplace_json_valid(self):
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as f:
            d = json.load(f)
        self.assertEqual(d["name"], "20thCenturyBoy")
        self.assertIn("plugins", d)
        self.assertEqual(d["plugins"][0]["name"], "autoresume")


if __name__ == "__main__":
    unittest.main(verbosity=2)
