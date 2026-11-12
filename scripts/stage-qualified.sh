#!/usr/bin/env bash
# Compatibility name only. This no longer retrieves any private/qualified mirror.
set -euo pipefail
echo 'Extracting sanitized public candidate, NOT a GPU-qualified production binary.' >&2
exec bash "$(dirname "$0")/stage-public-runtime.sh" "$@"
