# Build and asset preparation

## Distribution artifact

Use only the digest-pinned sanitized runtime from
`ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`.
It includes runtime, engine, frontend, native vision assets and optional GLP-39;
**text rank/Engram/tokenizer assets must be prepared separately**. Publication is
held until anonymous readback succeeds; see [status](completion-report.md).

The sanitized twin uses unchanged engine source **b7c3eb5**, byte-identical production
frontend and vision assets, and a generic-path rebuilt engine. It is **not GPU-qualified**.
An older private predecessor is not a build input or download requirement.

## Prepare the text assets

Use an off-serving ARM64 CUDA13 conversion host, not an active serving node.
See [setup](setup-spark.md) for compiler and memory/storage requirements.

```sh
bash scripts/fetch-sources.sh
bash scripts/build-engine.sh
hf download deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --local-dir work/checkpoint
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Review the plan, then explicitly perform conversion:
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --execute
```

The source fetch pins `ofan/pico-dgx-ds4` to
`b7c3eb5b12a030725bfb0186d27065bc6e376685`. CMake builds converters, verifier and
Engram packer as well as the engine. The conversion wrapper runs, for ranks0–3:
`dsw_convert`, every-byte `dsw_verify --threads 4`, `engram_pack`, then the pinned
`make_hashmap_stdlib.py`. It writes `bundle/model/asset-hashes.json` only after all
commands succeed. Review `work/conversion-logs`: require zero bad tensors and
bytewise agreement, not just loading/CRC. No re-quantization or training is performed.
Retain authentic acquisition and license records; the revision argument alone does
not prove the origin of a local directory.

Per-node staging from `bundle/model`:

```text
rankN.dsw
engram-l1-rNof4.bin
engram-l14-rNof4.bin
engram_hashmap.bin
tokenizer.json
config.json
other original checkpoint metadata
```

Copy the matching rank and two shards plus common metadata into `/srv/pico/model`
on each node. Do not copy all ranks to every node unless deliberately provisioning
that extra storage. Preserve/verify file hashes after transfer. Vision addition does
not require rewriting already verified stock text ranks. The wrapper's `--reuse`
mode requires the authentic original conversion receipt and runs four fresh verifiers;
it does not overwrite text/Engram files or relabel their original lineage.

## Extract already packaged public runtime assets (optional)

```sh
bash scripts/stage-public-runtime.sh
```

This pulls only the public-package candidate, creates but never starts a temporary
container, extracts engine/frontend/vision/vector/notices, and verifies locked hashes.
It is for rebuild/staging, not needed to run the README command. It refuses existing
output artifacts. No private-image fallback exists. The legacy `stage-qualified.sh`
name forwards to this script and does **not** imply GPU qualification.

## Prepare native vision from public source (optional rebuild route)

```sh
python3 scripts/prepare-vision.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Review, then add --execute on the build host.
```

The wrapper stages publisher `inference/vision.py`, `image_processor.py` and config,
and fork `vision_encoder.py` / `image_io.py`. The pinned fork exporter reads exact
HTTP206 tensor ranges. Require the **266-tensor** compact pack, **970,536,960 BF16
payload bytes**, full-file hash
`b07abf470c4107ba3029fedb9de1fd8823a40041f99d0d278e536b06ed5bb446`.
A packaged exact pack is reusable. No synthetic weights or replacement projector.
The public extraction wrapper has offline tests but has not been run end to end here.
Keep canonical attention (`VISION_SDPA_OPT_IN=0`) and serialized preload/encoding.

## Optional vector

```sh
python3 scripts/fetch-vector.py           # show URL/hash only
python3 scripts/fetch-vector.py --execute # explicit authentic download
```

See [steering](steering.md) for source, MIT credit and full hash. It defaults OFF.
The public runtime already includes the authentic optional vector; no download is
required to enable its runtime flag. Git contains no model/vector payloads.

## Build a distinct all-in-one image (advanced, not required to run)

```sh
python3 scripts/prepare-bundle.py --publication-runtime docs/publication-runtime.json
bash scripts/build-image.sh
```

Required bundle tree: `bin/{dsgb10_rank,dsfront}`, `notices/engine-NOTICE`,
`model/` with all four ranks/eight shards/hashmap/metadata and authentic hash receipt,
`vision/` with the exact pack/publisher modules/fork helpers and its hash receipt,
and optionally `vectors/glp39.gguf`.
The validator enforces provenance, hashes, path safety and steering OFF; the Dockerfile
requires an explicit audit-cleared runtime base. Adding text assets changes the image
digest and disk footprint. The script builds locally only; it never pushes or deploys.
A new native engine compilation need not have the packaged engine's hash: do not edit
hash guards to call an unqualified binary production-identical.

## Source/provenance mapping

The retained provenance is homeinfra `cf6e8b67c`, under `docs/operations/evidence/`:

| Step | Source evidence / pinned implementation |
|---|---|
| Engine/frontend source | Fork `b7c3eb5`; `pico-image-support-20261108/window-r2/HOST-QUALIFICATION.md` |
| Text conversion and verification | Pinned `weights/{dsw_convert,dsw_verify}`, `engram_pack`, `make_hashmap_stdlib.py`; `pico-glp-promotion-20261107/README.md` |
| Compact native vision | Pinned `tools/vision/extract_pack.py`; same host-qualification report |
| Authentic optional vector | `pico-glp-upstream-prepare-20261107/README.md` |
| Production gates | `pico-image-support-20261111/retrial-spark-only/REPORT.md` |
| Sanitized rebuild, audit and owner waivers | Local [publication remediation](publication-remediation.md) and JSON receipts |

These evidence references are provenance, not private dependencies required to run
this recipe. Only the public-package artifact is a distribution input.

## Residual gaps

1. **Publication held:** separate package is uploaded but still private; owner-authenticated
   web access is needed to change visibility, followed by anonymous readback. Repository
   publication is gated on that result.
2. **Sanitized candidate GPU qualification pending.** The generic-path engine and runtime
   have host/QEMU tests, not completed four-rank model gates. The PyTorch import smoke
   timed out; this remains a qualification note, not an audit/publication blocker.
3. **Independent exact compiler reproduction is not turnkey.** The original native-input
   cross-toolchain/sysroot bundle is not publicly distributed. Native build commands are
   supplied, but byte-identical source rebuilding is not promised. Users can run the
   distributed candidate without rebuilding its engine.
4. **Full public-source asset pipeline / all-in-one image not executed end to end.**
   Snapshot acquisition, conversion, compact extraction, full bundle sizing/audit and
   full-ring acceptance require actual execution. The runtime-only quick-start does not
   claim to ship text weights or remove the need to prepare them.
