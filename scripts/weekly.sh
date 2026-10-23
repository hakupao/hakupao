#!/bin/bash
# Weekly refresh of the README "Last week" block, run by launchd (launchd/com.hakupao.profile-weekly.plist).
# Commits and pushes only README.md, and only when the block changed.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd "$(dirname "$0")/.."

echo "== $(date '+%F %T')"
git pull --ff-only --quiet
/usr/bin/python3 scripts/weekly.py
if git diff --quiet -- README.md; then
  echo "no change"
  exit 0
fi
git add README.md
git commit --quiet -m "chore: weekly update $(date +%G-W%V)"
git push --quiet
echo "pushed"
