#!/usr/bin/env python3
"""
Tests for the autoresume wrapper.

Runs with: python3 tests/test_autoresume.py
No external dependencies — stdlib only.
"""

import importlib.machinery
import importlib.util
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT = os.path.join(os.path.dirname(__file__), "..")
BIN = os.path.join(ROOT, "bin", "autoresume")


def load(path):
    spec = importlib.util.spec_from_file_location(
        path, path,
        loader=importlib.machinery.SourceFileLoader(path, path),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wrapper = load(BIN)


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
        }.get(h, d)

        with patch.object(wrapper, "HTTPSConnection", return_value=MagicMock(
            getresponse=MagicMock(return_value=mock_resp)
        )):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, retry_after, reset_at = wrapper.check_rate_limit()

        self.assertTrue(limited)
        self.assertEqual(retry_after, 134)
        self.assertTrue(reset_at)

    def test_200_mocked(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.getheader.side_effect = lambda h, d="": d

        with patch.object(wrapper, "HTTPSConnection", return_value=MagicMock(
            getresponse=MagicMock(return_value=mock_resp)
        )):
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

        with patch.object(wrapper, "HTTPSConnection", return_value=MagicMock(
            getresponse=MagicMock(return_value=mock_resp)
        )):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                limited, retry_after, _ = wrapper.check_rate_limit()

        self.assertTrue(limited)
        self.assertEqual(retry_after, wrapper.DEFAULT_WAIT)


# ═══════════════════════════════════════════════════════════
# Test 3: Integration / structure
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
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "bin", "autoresume")))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "install.py")))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "README.md")))

    def test_readme_has_install_command(self):
        with open(os.path.join(ROOT, "README.md")) as f:
            content = f.read()
        self.assertIn("curl", content)
        self.assertIn("install.py", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
