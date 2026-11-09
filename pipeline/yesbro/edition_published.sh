#!/bin/sh
# Exit 0 when main already contains a finished Yes Bro Daily issue for DATE.
# publish.py writes daily/archive/DATE.html only after that issue is built,
# and the workflow commits it only when the pipeline exits 0.
# The canonical URL inside the file is the proof it is that archive page,
# not an empty or mis-dated file that happens to use the same name.
set -eu

root=${1:?site root}
date=${2:?YYYY-MM-DD}

case "$date" in
  [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
  *)
    echo "invalid edition date: $date" >&2
    exit 2
    ;;
esac

marker="$root/daily/archive/$date.html"
url="https://yesbrohq.com/daily/archive/$date.html"
if [ ! -f "$marker" ]; then
  exit 1
fi
grep -F -q "rel=\"canonical\" href=\"$url\"" "$marker"
