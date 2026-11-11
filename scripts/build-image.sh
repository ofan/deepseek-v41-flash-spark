#!/usr/bin/env bash
# Explicit local build only. Never pushes, deploys or downloads model weights.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${RUNTIME_BASE:=ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1@sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9}"
[[ "$RUNTIME_BASE" == *@sha256:* ]] || { echo 'Runtime base must be digest-pinned' >&2; exit 1; }
python3 scripts/prepare-bundle.py
docker build --platform linux/arm64 --build-arg "RUNTIME_BASE=$RUNTIME_BASE" \
 -t ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-bundle-candidate .
echo 'LOCAL candidate only. Requires profile extraction and four-rank acceptance; nothing pushed.'
