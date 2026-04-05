#!/bin/bash
# SessionStart hook: checks if the autoresume wrapper is installed.
# If not, tells the user how to install it and where the wrapper lives.

WRAPPER="autoresume"
PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if command -v "$WRAPPER" &>/dev/null; then
    # Already installed — nothing to do
    exit 0
fi

# Not installed — output context for Claude to display
cat <<EOF
{"additionalContext":"⚠️  The autoresume wrapper is NOT in your PATH.

To use auto-resume (which handles rate limits automatically),
run this ONE command in your terminal:

  source $PLUGIN_DIR/hooks/setup.sh

This symlinks the wrapper to ~/.local/bin/ and adds it to your PATH.
After that, use \`autoresume claude\` instead of \`claude\`."}
EOF
exit 0
