#!/usr/bin/env bash
# Source-build candidate, OFF serving machines. Not a byte-identical release claim.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$(pwd)
source_root=${1:-$root/work/source}
output=${2:-$root/work/compiled}
source_root=$(realpath "$source_root")
mkdir -p "$output"; output=$(realpath "$output")
test "$(uname -m)" = aarch64 || {
 echo 'Native recipe requires an off-serving ARM64 CUDA build host. Qualified x86 cross-toolchain is a release gap.' >&2; exit 1;
}
readarray -t pins < <(python3 - <<'PYLOCK'
import json
x=json.load(open('sources.lock.json'))
for k in ('engine_commit','frontend_commit','source_directory'): print(x[k])
PYLOCK
)
python3 "$root/scripts/source_tree.py" --verify "$source_root/engine"
python3 "$root/scripts/source_tree.py" --verify "$source_root/frontend"
engine="$source_root/engine/${pins[2]}/engine"
front="$source_root/frontend/${pins[2]}/frontend"
cmake -S "$engine" -B "$output/engine" -DCMAKE_BUILD_TYPE=Release
cmake --build "$output/engine" --target dsgb10_rank dsw_convert dsw_verify engram_pack ring_test -j "${BUILD_JOBS:-4}"
(cd "$front" && cargo build --locked --release -j "${BUILD_JOBS:-4}" --target-dir "$output/frontend")
mkdir -p "$output/bin" "$output/notices"
install -m755 "$output/engine/server/dsgb10_rank" "$output/bin/dsgb10_rank"
install -m755 "$output/frontend/release/dsfront" "$output/bin/dsfront"
cp "$source_root/engine/LICENSE" "$output/notices/engine-LICENSE"
cp "$source_root/engine/NOTICE" "$output/notices/engine-NOTICE"
sha256sum "$output/bin/dsgb10_rank" "$output/bin/dsfront"
python3 - "$output" <<'RECEIPT'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1]);manifest=Path('vendor/engine/SOURCE.json')
lock=json.loads(Path('sources.lock.json').read_text())
row={'source_commit':lock['engine_commit'],'source_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
     'engine_binary_sha256':hashlib.sha256((out/'bin/dsgb10_rank').read_bytes()).hexdigest(),
     'frontend_binary_sha256':hashlib.sha256((out/'bin/dsfront').read_bytes()).hexdigest(),
     'qualification':'LOCAL SOURCE BUILD; GPU qualification and layer-content audit required before release'}
(out/'source-build.json').write_text(json.dumps(row,indent=2)+'\n')
RECEIPT
echo 'Source build complete. Compare against sources.lock.json; a mismatch is NOT a qualified production binary.'
