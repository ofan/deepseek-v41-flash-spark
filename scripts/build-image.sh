#!/usr/bin/env bash
# Explicit local build only. Never pushes, deploys or downloads model weights.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${RUNTIME_BASE:?Supply a reviewed public ARM64 CUDA13/RDMA runtime base pinned by digest; see docs/build.md}"
[[ "$RUNTIME_BASE" == *@sha256:* ]] || { echo 'Runtime base must be digest-pinned' >&2; exit 1; }
python3 scripts/prepare-bundle.py
docker build --platform linux/arm64 --build-arg "RUNTIME_BASE=$RUNTIME_BASE" \
 -t ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-sampler-open-unit-r1-bundle-candidate .
echo 'LOCAL candidate only. Requires profile extraction and four-rank acceptance; nothing pushed.'
