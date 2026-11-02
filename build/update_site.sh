#!/usr/bin/env bash
# Rebuild site/ from data/inventory.json (+ any photos in data/photos/) and the build kit.
# Usage: build/update_site.sh YYYY-MM-DD
set -euo pipefail
cd "$(dirname "$0")/.."
DAY="${1:?date YYYY-MM-DD}"
WORK="$(mktemp -d)"
cp -r build/* "$WORK/"
mkdir -p "$WORK/img" "$WORK/data/photos"
cp site/img/* "$WORK/img/" 2>/dev/null || true
cp build/static/* "$WORK/img/"
cp data/inventory.json "$WORK/data/"
cp data/photos/* "$WORK/data/photos/" 2>/dev/null || true
( cd "$WORK" && python3 build_site.py "$DAY" )
cp "$WORK/index.html" site/index.html
cp "$WORK"/img/* site/img/
rm -rf "$WORK"
