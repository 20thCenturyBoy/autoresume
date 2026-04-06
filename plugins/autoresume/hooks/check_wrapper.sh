#!/bin/bash
# SessionStart hook: auto-installs the autoresume wrapper if not in PATH.
# On success: adds ~/.local/bin to PATH and prints a success message.
# On failure: prints manual install instructions so the user can fix it.

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WRAPPER_BIN="$PLUGIN_DIR/bin/autoresume"
USER_BIN="$HOME/.local/bin"
LINK="$USER_BIN/autoresume"

# ── Already installed? ──────────────────────────────────────────────────────
if command -v autoresume &>/dev/null; then
    exit 0
fi

# ── Source binary exists? ───────────────────────────────────────────────────
if [ ! -f "$WRAPPER_BIN" ]; then
    echo "⚠️  Autoresume wrapper source not found at: $WRAPPER_BIN"
    echo ""
    echo "The plugin files may be corrupted. Try reinstalling:"
    echo "  /plugin uninstall autoresume@20thCenturyBoy"
    echo "  /plugin install autoresume@20thCenturyBoy"
    exit 0
fi

_show_manual() {
    echo "⚠️  Could not auto-install the autoresume wrapper."
    echo ""
    echo "Install it manually by running this in your terminal:"
    echo "  source $PLUGIN_DIR/hooks/setup.sh"
    echo ""
    echo "Then use: autoresume claude"
}

# ── Attempt auto-install ────────────────────────────────────────────────────
mkdir -p "$USER_BIN" 2>/dev/null
if [ $? -ne 0 ]; then
    _show_manual
    exit 0
fi

# Remove stale symlink if present
if [ -L "$LINK" ]; then
    rm -f "$LINK" 2>/dev/null
fi

ln -sf "$WRAPPER_BIN" "$LINK" 2>/dev/null
if [ $? -ne 0 ] || [ ! -L "$LINK" ]; then
    _show_manual
    exit 0
fi

chmod +x "$WRAPPER_BIN" 2>/dev/null
chmod +x "$LINK" 2>/dev/null

# Add to PATH for this session via Claude's env file mechanism
if [ -n "$CLAUDE_ENV_FILE" ] && [ -f "$CLAUDE_ENV_FILE" ]; then
    echo "PATH=$USER_BIN:\$PATH" >> "$CLAUDE_ENV_FILE"
fi

echo "✅  autoresume wrapper auto-installed to $LINK"
echo "    You can now run: autoresume claude"
exit 0
