#!/usr/bin/env bash
# Extract qualified artifacts on a BUILD HOST only. Never start the container.
set -euo pipefail
cd "$(dirname "$0")/.."
image='ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1@sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9'
for f in bundle/bin/dsgb10_rank bundle/bin/dsfront bundle/vision; do
 test ! -e "$f" || { echo "Refusing existing artifact: $f" >&2; exit 1; }
done
docker pull --platform linux/arm64 "$image"
cid=$(docker create --platform linux/arm64 --entrypoint /bin/true "$image")
trap 'docker rm "$cid" >/dev/null' EXIT
mkdir -p bundle/bin bundle/vision
# Paths from the production qualification's shipped-asset contract.
docker cp "$cid:/opt/pico/dsgb10_rank" bundle/bin/dsgb10_rank
docker cp "$cid:/opt/pico/dsfront" bundle/bin/dsfront
docker cp "$cid:/opt/pico/vision/vision.safetensors" bundle/vision/vision.safetensors
python3 - <<'PYVERIFY'
import hashlib,json
from pathlib import Path
lock=json.loads(Path('sources.lock.json').read_text())
for name,key in [('bin/dsgb10_rank','engine_binary_sha256'),('bin/dsfront','frontend_binary_sha256'),('vision/vision.safetensors','vision_pack_sha256')]:
 p=Path('bundle')/name
 h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 if h!=lock[key]:raise SystemExit('Qualified artifact hash mismatch: '+name)
print('Qualified binaries and compact pack verified. Container was never started.')
PYVERIFY
# Stage publisher modules and fork helpers with prepare-vision.py before bundling.
