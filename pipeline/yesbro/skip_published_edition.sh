#!/bin/sh
# Backup schedule runs skip the build when today's IST Daily is already on main.
# workflow_dispatch (manual and the external 05:00 IST cron) always builds.
set -eu

event=${GITHUB_EVENT_NAME:-workflow_dispatch}
root=${GITHUB_WORKSPACE:-.}
date=$(TZ=Asia/Kolkata date +%F)
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

skip=false
if [ "$event" = "schedule" ] && sh "$here/edition_published.sh" "$root" "$date"; then
  skip=true
  echo "Backup schedule: daily/archive/$date.html is already on main. Skipping the build."
else
  if [ "$event" = "schedule" ]; then
    echo "Backup schedule: daily/archive/$date.html is not a published Daily issue. Building."
  else
    echo "Event $event always builds (IST date would be $date)."
  fi
fi

echo "skip=$skip"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "skip=$skip" >> "$GITHUB_OUTPUT"
fi
