#!/usr/bin/env bash
# Fetch code only. No weights, vectors or images. Refuse to alter an existing tree.
set -euo pipefail
cd "$(dirname "$0")/.."
root=${1:-work/source}
readarray -t pins < <(python3 - <<'PYLOCK'
import json
x=json.load(open('sources.lock.json'))
for key in ('engine_repository','engine_commit','frontend_commit'): print(x[key])
PYLOCK
)
for name in engine frontend; do
  dest="$root/$name"
  test ! -e "$dest" || { echo "Refusing existing destination: $dest" >&2; exit 1; }
done
for name in engine frontend; do
  revision=${pins[1]}; test "$name" != frontend || revision=${pins[2]}
  dest="$root/$name"
  mkdir -p "$dest"
  git -C "$dest" init -q
  git -C "$dest" remote add origin "${pins[0]}"
  git -C "$dest" fetch --depth 1 origin "$revision"
  git -C "$dest" checkout --detach FETCH_HEAD
  test "$(git -C "$dest" rev-parse HEAD)" = "$revision"
done
