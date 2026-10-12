#!/usr/bin/env bash
# Copy the skill and watch list into Hermes.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.hermes/skills/research/competitor-intel ~/.hermes/competitor-intel/state
cp "$here/skills/competitor-intel/SKILL.md" ~/.hermes/skills/research/competitor-intel/
cp "$here/watchlist.json" "$here/schemas.json" ~/.hermes/competitor-intel/
echo "Installed. Next: hermes cron create \"0 9 * * 1\" \"Run the weekly competitor intel check by following the competitor-intel skill.\" --name competitor-intel --skill competitor-intel --deliver local"
