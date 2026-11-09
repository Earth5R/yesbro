#!/bin/sh
# Commit the built paper and push it to main.
# If main moved during the build, rebase onto that tip and push once.
# Never force-push.
set -eu

git config user.name "yesbro-bot"
git config user.email "yesbro-bot@users.noreply.github.com"
git add -A
# Never publish a CNAME change from the build tree.
git restore --source=HEAD --staged --worktree -- CNAME || true
if git diff --cached --quiet; then
  echo "No site changes to commit"
  exit 0
fi
git commit -m "Yes Bro daily: $(TZ=Asia/Kolkata date +%F)"
if git push origin HEAD:main; then
  exit 0
fi
echo "Push rejected because main moved. Rebase onto origin/main and push once."
git fetch origin main
git rebase FETCH_HEAD
git push origin HEAD:main
