#!/usr/bin/env bash
# Compatibility command: stage reviewed in-repository source, never fetch a fork.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/source_tree.py --stage "${1:-work/source}"
