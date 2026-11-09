#!/bin/sh
# Backup schedule skips only when daily/archive/DATE.html is the published issue.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/../../.." && pwd)
CHECK="$ROOT/pipeline/yesbro/edition_published.sh"
SKIP="$ROOT/pipeline/yesbro/skip_published_edition.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/daily/archive"
date=2026-11-09
url="https://yesbrohq.com/daily/archive/$date.html"
printf '<link rel="canonical" href="%s">\n' "$url" > "$TMP/daily/archive/$date.html"

sh "$CHECK" "$TMP" "$date"
echo "canonical archive counts as published"

# The real Sunday issue written by publish.py, not a synthetic fixture.
sh "$CHECK" "$ROOT" "2026-11-08"
echo "committed daily/archive/2026-11-08.html counts as published"
if sh "$CHECK" "$ROOT" "2026-11-09"; then
  echo "9 Nov archive should not be on this checkout" >&2
  exit 1
fi
echo "9 Nov is not published on this checkout"

if sh "$CHECK" "$TMP" "2026-11-10"; then
  echo "missing archive was treated as published" >&2
  exit 1
fi
echo "missing archive is not published"

printf 'Sunday draft\n' > "$TMP/daily/archive/$date.html"
if sh "$CHECK" "$TMP" "$date"; then
  echo "file without the archive canonical was treated as published" >&2
  exit 1
fi
echo "undated file is not published"

printf '<link rel="canonical" href="https://yesbrohq.com/daily/archive/2026-11-08.html">\n' > "$TMP/daily/archive/$date.html"
if sh "$CHECK" "$TMP" "$date"; then
  echo "wrong-day canonical was treated as published" >&2
  exit 1
fi
echo "wrong canonical is not published"

: > "$TMP/daily/archive/$date.html"
if sh "$CHECK" "$TMP" "$date"; then
  echo "empty archive was treated as published" >&2
  exit 1
fi
echo "empty archive is not published"

printf '<link rel="canonical" href="%s">\n' "$url" > "$TMP/daily/archive/$date.html"
if [ "$(GITHUB_EVENT_NAME=workflow_dispatch GITHUB_WORKSPACE="$TMP" sh "$SKIP" | tail -n 1)" != "skip=false" ]; then
  echo "workflow_dispatch should always build" >&2
  exit 1
fi
echo "workflow_dispatch does not skip"

# schedule + published marker for the script's own IST date
today=$(TZ=Asia/Kolkata date +%F)
mkdir -p "$TMP/daily/archive"
printf '<link rel="canonical" href="https://yesbrohq.com/daily/archive/%s.html">\n' "$today" > "$TMP/daily/archive/$today.html"
got=$(GITHUB_EVENT_NAME=schedule GITHUB_WORKSPACE="$TMP" sh "$SKIP" | tail -n 1)
test "$got" = "skip=true"
echo "schedule skips when today's archive canonical is present"

rm -f "$TMP/daily/archive/$today.html"
got=$(GITHUB_EVENT_NAME=schedule GITHUB_WORKSPACE="$TMP" sh "$SKIP" | tail -n 1)
test "$got" = "skip=false"
echo "schedule builds when today's archive is absent"

# 05:00 IST is 23:30 UTC the previous UTC date. 06:30 IST is 01:00 UTC the same IST morning.
test "$(TZ=Asia/Kolkata date -d '2026-11-08 23:30 UTC' +%F)" = "2026-11-09"
test "$(TZ=Asia/Kolkata date -d '2026-11-08 23:30 UTC' +%H:%M)" = "05:00"
test "$(TZ=Asia/Kolkata date -d '2026-11-09 01:00 UTC' +%F)" = "2026-11-09"
test "$(TZ=Asia/Kolkata date -d '2026-11-09 01:00 UTC' +%H:%M)" = "06:30"
test "$(TZ=Asia/Kolkata date -d '2026-11-09 18:29 UTC' +%F)" = "2026-11-09"
test "$(TZ=Asia/Kolkata date -d '2026-11-09 18:30 UTC' +%F)" = "2026-11-10"
echo "05:00 IST and 06:30 IST stay on the same IST date"
