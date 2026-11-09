#!/usr/bin/env bash
# Install the twscrape CLI from this fork (editable, so `git pull` updates it)
# and link the x-search skill into Claude Code.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SRC="$REPO/claude-skill/x-search"
SKILL_DST="$HOME/.claude/skills/x-search"

if ! command -v uv >/dev/null; then
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

uv tool install --force --editable --python 3.12 "$REPO"

mkdir -p "$HOME/.claude/skills"
if [ -e "$SKILL_DST" ] && [ ! -L "$SKILL_DST" ]; then
  echo "$SKILL_DST exists and is not a symlink; move it away and rerun." >&2
  exit 1
fi
ln -sfn "$SKILL_SRC" "$SKILL_DST"
chmod +x "$SKILL_SRC/x.py"

echo "Installed twscrape and the x-search skill."
echo "Next: log in at https://x.com in Chrome, then run  ~/.claude/skills/x-search/x.py login"
