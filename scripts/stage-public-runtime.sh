#!/usr/bin/env bash
# Extract audited candidate assets on a BUILD HOST. Never start the container.
set -euo pipefail
cd "$(dirname "$0")/.."
image='ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979'
for f in bundle/bin/dsgb10_rank bundle/bin/dsfront bundle/vision bundle/vectors bundle/notices; do
 test ! -e "$f" || { echo "Refusing existing artifact: $f" >&2; exit 1; }
done
docker pull --platform linux/arm64 "$image"
cid=$(docker create --platform linux/arm64 --entrypoint /bin/true "$image")
trap 'docker rm "$cid" >/dev/null' EXIT
mkdir -p bundle/bin
docker cp "$cid:/opt/package/bin/dsgb10_rank" bundle/bin/dsgb10_rank
docker cp "$cid:/opt/package/bin/dsfront" bundle/bin/dsfront
docker cp "$cid:/opt/package/vision" bundle/vision
docker cp "$cid:/opt/package/vectors" bundle/vectors
docker cp "$cid:/opt/package/notices" bundle/notices
python3 - <<'VERIFY'
import hashlib,json
from pathlib import Path
lock=json.loads(Path('sources.lock.json').read_text())
for name,key in [('bin/dsgb10_rank','engine_binary_sha256'),('bin/dsfront','frontend_binary_sha256'),('vision/vision.safetensors','vision_pack_sha256'),('vectors/glp39.gguf','optional_glp39_sha256')]:
 p=Path('bundle')/name
 if hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=lock[key]:
  raise SystemExit('Published artifact hash mismatch: '+name)
print('Candidate assets verified. Container never started; GPU qualification pending.')
VERIFY
