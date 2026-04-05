#!/usr/bin/env python3
"""
Installer for the Auto-Resume plugin.

Installs the `autoresume` wrapper script to a user-accessible location.

Usage:
    python install.py              # install
    python install.py --uninstall  # remove
"""

import os
import sys
from pathlib import Path


def install():
    plugin_dir = Path(__file__).parent.resolve()
    bin_dir = plugin_dir / "bin"

    # ── Step 1: Install the wrapper ──────────────────────────────────────

    # Preferred: symlink to a directory in PATH
    user_bin = Path.home() / ".local" / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)

    wrapper_src = bin_dir / "autoresume"
    wrapper_dst = user_bin / "autoresume"

    if wrapper_dst.exists() or wrapper_dst.is_symlink():
        wrapper_dst.unlink()
    wrapper_dst.symlink_to(wrapper_src.resolve())

    # Ensure user's ~/.local/bin is in PATH (warn if not)
    shell_rc = _find_shell_rc()
    path_entry = str(user_bin.resolve())
    if shell_rc and path_entry not in os.environ.get("PATH", ""):
        _ensure_path_in_rc(shell_rc, path_entry)

    # ── Done ─────────────────────────────────────────────────────────────

    print()
    print("━" * 60)
    print("✅  Auto-Resume Installed")
    print("━" * 60)
    print()
    print("   The `autoresume` command is now available.")
    print()
    print("   Usage:")
    print("     autoresume claude")
    print('     autoresume claude "refactor auth"')
    print()
    print("   The supplementary MCP server is also registered for")
    print("   proactive rate limit checks inside Claude sessions.")
    print()
    print("━" * 60)


def uninstall():
    user_bin = Path.home() / ".local" / "bin"
    wrapper = user_bin / "autoresume"

    if wrapper.exists() or wrapper.is_symlink():
        wrapper.unlink()

    print()
    print("✅  Auto-Resume removed.")
    print()


def _find_shell_rc():
    """Find the user's shell config file."""
    shell = os.environ.get("SHELL", "")
    candidates = []

    if "zsh" in shell:
        candidates = [".zshrc"]
    elif "bash" in shell:
        candidates = [".bashrc", ".bash_profile"]
    else:
        candidates = [".zshrc", ".bashrc", ".bash_profile"]

    for name in candidates:
        p = Path.home() / name
        if p.exists():
            return p
    return None


def _ensure_path_in_rc(rc_path: Path, path_entry: str):
    """Add PATH entry to shell rc if not already present."""
    try:
        content = rc_path.read_text()
    except IOError:
        return

    if path_entry in content:
        return

    with open(rc_path, "a") as f:
        f.write(f'\nexport PATH="{path_entry}:$PATH"\n')


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall()
    else:
        install()
