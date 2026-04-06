#!/usr/bin/env python3
"""
One-line installer for the autoresume wrapper.

Install:
    curl -sSfL https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/install.py | python3 -
"""

import os
import subprocess
import tempfile
from pathlib import Path


def install():
    # Clone repo to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/20thCenturyBoy/autoresume.git", tmpdir],
            capture_output=True, check=True
        )
        wrapper_src = Path(tmpdir) / "bin" / "autoresume"

    if not wrapper_src.exists():
        print("❌  Wrapper not found in repo.")
        return

    user_bin = Path.home() / ".local" / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)

    link = user_bin / "autoresume"
    if link.is_symlink() or link.exists():
        link.unlink()

    # Copy (not symlink) so it works independently of the repo
    import shutil
    shutil.copy2(wrapper_src, link)
    os.chmod(link, 0o755)

    # Persist to shell rc
    path_entry = str(user_bin.resolve())
    shell = os.environ.get("SHELL", "")
    for rc_name in (".zshrc", ".bashrc", ".bash_profile"):
        rc = Path.home() / rc_name
        if rc.exists() and path_entry not in rc.read_text():
            with open(rc, "a") as f:
                f.write(f'\nexport PATH="{path_entry}:$PATH"\n')

    print()
    print("✅  autoresume installed to", link)
    print("    Run: autoresume claude")


if __name__ == "__main__":
    install()
