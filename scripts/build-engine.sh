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
test "$(git -C "$source_root/engine" rev-parse HEAD)" = "${pins[0]}"
test "$(git -C "$source_root/frontend" rev-parse HEAD)" = "${pins[1]}"
test -z "$(git -C "$source_root/engine" status --porcelain)"
test -z "$(git -C "$source_root/frontend" status --porcelain)"
engine="$source_root/engine/${pins[2]}/engine"
front="$source_root/frontend/${pins[2]}/frontend"
cmake -S "$engine" -B "$output/engine" -DCMAKE_BUILD_TYPE=Release
cmake --build "$output/engine" -j "${BUILD_JOBS:-4}"
(cd "$front" && cargo build --locked --release -j "${BUILD_JOBS:-4}" --target-dir "$output/frontend")
mkdir -p "$output/bin" "$output/notices"
install -m755 "$output/engine/server/dsgb10_rank" "$output/bin/dsgb10_rank"
install -m755 "$output/frontend/release/dsfront" "$output/bin/dsfront"
cp "$source_root/engine/LICENSE" "$output/notices/engine-LICENSE"
cp "$source_root/engine/NOTICE" "$output/notices/engine-NOTICE"
sha256sum "$output/bin/dsgb10_rank" "$output/bin/dsfront"
echo 'Source build complete. Compare against sources.lock.json; a mismatch is NOT a qualified production binary.'
