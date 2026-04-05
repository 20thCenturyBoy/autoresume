#!/bin/bash
# One-liner to install the autoresume wrapper to the user's PATH.
# Usage: source /path/to/plugins/autoresume/hooks/setup.sh

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
USER_BIN="$HOME/.local/bin"

mkdir -p "$USER_BIN"

# Symlink wrapper
ln -sf "$PLUGIN_DIR/bin/autoresume" "$USER_BIN/autoresume"
chmod +x "$PLUGIN_DIR/bin/autoresume"

# Add to PATH for this session
export PATH="$USER_BIN:$PATH"

# Persist to shell rc
for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$rc" ] && ! grep -q "$USER_BIN" "$rc" 2>/dev/null; then
        echo "" >> "$rc"
        echo 'export PATH="'"$USER_BIN"':$PATH"' >> "$rc"
    fi
done

echo ""
echo "✅  autoresume wrapper installed to $USER_BIN"
echo "    You can now run: autoresume claude"
