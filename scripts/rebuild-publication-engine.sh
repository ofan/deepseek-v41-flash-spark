#!/usr/bin/env bash
# Local off-serving cross build. No network, GPU, image push or serving action.
set -euo pipefail
cd "$(dirname "$0")/.."
SOURCE_CHECKOUT=${SOURCE_CHECKOUT:-vendor/engine}
: "${CROSS_BUILDER:?Set the locally available cross-builder by sha256 image ID}"
: "${ARM_SYSROOT:?Set the reviewed ARM64 CUDA13/RDMA sysroot}"
: "${TOOLCHAIN_FILE:?Set the reviewed CMake cross-toolchain file}"
: "${BUILD_OUTPUT:?Set a new build output directory}"
[[ "$CROSS_BUILDER" =~ ^sha256:[0-9a-f]{64}$ ]] || exit 1
pin=$(python3 -c 'import json; print(json.load(open("sources.lock.json"))["engine_commit"])')
python3 scripts/source_tree.py --verify "$SOURCE_CHECKOUT"
mkdir -m755 "$BUILD_OUTPUT"
source_root=$(realpath "$SOURCE_CHECKOUT/ds41f-4xgx10-switchless")
docker run --rm --user "$(id -u):$(id -g)" --network none --cap-drop ALL \
 --security-opt no-new-privileges --entrypoint /bin/bash \
 -v "$source_root:/src:ro" -v "$(realpath "$ARM_SYSROOT"):/sysroot:ro" \
 -v "$(realpath "$TOOLCHAIN_FILE"):/toolchain.cmake:ro" \
 -v "$(realpath "$BUILD_OUTPUT"):/build" "$CROSS_BUILDER" -lc \
 'cmake -S /src/engine -B /build -DCMAKE_TOOLCHAIN_FILE=/toolchain.cmake -DCMAKE_BUILD_TYPE=Release -DCUDAToolkit_ROOT=/sysroot/cuda -DCUDA_CUDART=/sysroot/cuda/lib64/libcudart.so && cmake --build /build --target dsgb10_rank glp_test glp_math_test sample_rng_test -j4'
echo 'Rebuilt from generic paths. New binary hash requires a new profile and GPU acceptance.'
