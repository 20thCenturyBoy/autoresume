#!/usr/bin/env python3
"""
One-line installer for the autoresume wrapper.

Install:
    curl -sSfL https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/install.py | python3 -
"""

import os
from pathlib import Path


def install():
    # Determine paths
    script_dir = Path(__file__).parent.resolve() if __file__ != "<stdin>" else None
    bin_dir = script_dir / "bin" if script_dir else None

    # If running from stdin (curl pipe), use the GitHub raw path
    if bin_dir is None or not bin_dir.exists():
        # We're being piped — clone to a temp location
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["git", "clone", "--depth", "1",
                 "https://github.com/20thCenturyBoy/autoresume.git", tmpdir],
                capture_output=True, check=True
            )
            bin_dir = Path(tmpdir) / "plugins" / "autoresume" / "bin"

    wrapper_src = bin_dir / "autoresume"
    if not wrapper_src.exists():
        print("❌  Wrapper binary not found in repo.")
        print("    Try: git clone https://github.com/20thCenturyBoy/autoresume.git")
        return

    user_bin = Path.home() / ".local" / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)

    link = user_bin / "autoresume"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(wrapper_src.resolve())

    os.chmod(wrapper_src, 0o755)

    # Add to PATH for this session
    path_entry = str(user_bin.resolve())
    if path_entry not in os.environ.get("PATH", ""):
        shell = os.environ.get("SHELL", "")
        rc = None
        if "zsh" in shell:
            rc = Path.home() / ".zshrc"
        elif "bash" in shell:
            rc = Path.home() / ".bashrc"
        if rc and rc.exists() and path_entry not in rc.read_text():
            with open(rc, "a") as f:
                f.write(f'\nexport PATH="{path_entry}:$PATH"\n')

    print()
    print("✅  autoresume installed to", link)
    print("    Run: autoresume claude")


if __name__ == "__main__":
    install()
