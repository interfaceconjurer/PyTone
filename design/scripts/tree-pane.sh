#!/bin/bash
# Live project tree: redraws every 3 seconds so it tracks changes.
root="$(cd "$(dirname "$0")/../.." && pwd)"
while true; do
  out=$(python3 "$root/design/scripts/tree.py" "$root" --depth 4 2>&1)
  clear
  printf '%s\n' "$out"
  sleep 3
done
