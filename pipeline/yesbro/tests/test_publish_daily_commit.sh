#!/bin/sh
# The daily job pushes to main after a long build. A commit that lands on
# main during that build must be kept, and the paper commit replayed on top.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/../../.." && pwd)
SCRIPT="$ROOT/pipeline/yesbro/publish_daily_commit.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

git init --bare "$TMP/origin.git" >/dev/null
git --git-dir="$TMP/origin.git" symbolic-ref HEAD refs/heads/main
git clone "file://$TMP/origin.git" "$TMP/seed" >/dev/null
git -C "$TMP/seed" config user.email "seed@example.com"
git -C "$TMP/seed" config user.name "seed"
printf 'cron: "0 0 * * *"\n' > "$TMP/seed/daily.yml"
printf 'yesbrohq.com\n' > "$TMP/seed/CNAME"
printf 'Sunday\n' > "$TMP/seed/index.html"
git -C "$TMP/seed" add daily.yml CNAME index.html
git -C "$TMP/seed" commit -m "base" >/dev/null
git -C "$TMP/seed" branch -M main
git -C "$TMP/seed" push -u origin main >/dev/null

git clone --depth 1 "file://$TMP/origin.git" "$TMP/worker" >/dev/null

# Main gains the schedule change while the worker is building.
printf 'cron: "30 23 * * *"\n' > "$TMP/seed/daily.yml"
git -C "$TMP/seed" commit -am "schedule 05:00 IST" >/dev/null
git -C "$TMP/seed" push origin main >/dev/null

printf 'Monday 9 November 2026\n' > "$TMP/worker/index.html"
printf 'stolen.example\n' > "$TMP/worker/CNAME"
( cd "$TMP/worker" && sh "$SCRIPT" ) 

PAPER=$(git --git-dir="$TMP/origin.git" log -1 --format=%s main)
test "$PAPER" = "Yes Bro daily: $(TZ=Asia/Kolkata date +%F)"
test "$(git --git-dir="$TMP/origin.git" show main:index.html)" = "Monday 9 November 2026"
test "$(git --git-dir="$TMP/origin.git" show main:daily.yml)" = 'cron: "30 23 * * *"'
test "$(git --git-dir="$TMP/origin.git" show main:CNAME)" = "yesbrohq.com"
echo "rebase publish kept schedule, paper, and CNAME"

# A second run with nothing new does not add a commit.
BEFORE=$(git --git-dir="$TMP/origin.git" rev-parse main)
git clone "file://$TMP/origin.git" "$TMP/idle" >/dev/null
( cd "$TMP/idle" && sh "$SCRIPT" )
AFTER=$(git --git-dir="$TMP/origin.git" rev-parse main)
test "$BEFORE" = "$AFTER"
echo "empty publish does not push"
