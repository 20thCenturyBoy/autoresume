#!/usr/bin/env python3
"""
One-line installer for the autoresume wrapper.

Install:
    curl -sSfL https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/install.py | python3 -
"""

import os
import ssl
import sys
from pathlib import Path
from urllib.request import urlopen, Request

WRAPPER_URL = "https://raw.githubusercontent.com/20thCenturyBoy/autoresume/main/bin/autoresume"


def install():
    user_bin = Path.home() / ".local" / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)

    dest = user_bin / "autoresume"

    # Download wrapper
    print("Downloading autoresume...")
    try:
        resp = urlopen(Request(WRAPPER_URL), timeout=15)
        content = resp.read()
    except Exception as e:
        print(f"❌  Failed to download: {e}")
        print("    Try: git clone https://github.com/20thCenturyBoy/autoresume.git")
        return

    if resp.status != 200:
        print(f"❌  Download failed (HTTP {resp.status})")
        return

    # Write
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    dest.write_bytes(content)
    os.chmod(dest, 0o755)

    # Persist to shell rc
    path_entry = str(user_bin.resolve())
    for rc_name in (".zshrc", ".bashrc", ".bash_profile"):
        rc = Path.home() / rc_name
        if rc.exists() and path_entry not in rc.read_text():
            with open(rc, "a") as f:
                f.write(f'\nexport PATH="{path_entry}:$PATH"\n')

    print()
    print("✅  autoresume installed to", dest)
    print("    Run: autoresume claude")


if __name__ == "__main__":
    install()
