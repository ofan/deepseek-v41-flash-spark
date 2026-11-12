#!/usr/bin/env bash
# Explicit local candidate build only; no push, deploy or model download.
set -euo pipefail
cd "$(dirname "$0")/.."
receipt=${PUBLICATION_RUNTIME_RECEIPT:-docs/publication-runtime.json}
RUNTIME_BASE=$(python3 - "$receipt" <<'PY'
import json,re,sys
r=json.load(open(sys.argv[1]))
assert r['privacy_verdict']=='CLEAN' and r['unresolved_findings']==0, 'Runtime privacy gate not clear'
assert r['inherited_source_layers']==0, 'Historical layers are forbidden'
ref=r['image']+'@'+r['manifest_digest']
assert re.fullmatch(r'ghcr.io/ofan/deepseek-v41-flash-spark:[A-Za-z0-9_.-]+@sha256:[0-9a-f]{64}',ref)
print(ref)
PY
)
python3 scripts/prepare-bundle.py --publication-runtime "$receipt"
docker build --platform linux/arm64 --build-arg "RUNTIME_BASE=$RUNTIME_BASE" \
 -t ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.11-native-vision-bundle-candidate .
echo 'LOCAL unqualified candidate only. Requires full artifact audit and four-rank acceptance.'
