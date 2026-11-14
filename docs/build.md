# Build from the included implementation

## Choose a route

1. **Run the public runtime:** prepare verified text assets, then follow the README.
   No engine download or private artifact is needed.
2. **Rebuild from source:** use `vendor/engine/`, compile on an off-serving ARM64
   CUDA13 host, prepare model/vision assets and assemble a **new unqualified image**.
   Source, base and patch series are in this repository. Native dependencies and
   publisher model assets are still external inputs, not vendored binaries.

Published runtime:
`ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`.
It contains runtime, engine, frontend, vision pack and authentic optional GLP-39,
**not text ranks, Engram shards or tokenizer**. Anonymous readback is recorded in
[completion status](completion-report.md). Four-rank GPU qualification is pending
for the sanitized public candidate and for any new source build.

## Included source and patches

`vendor/engine/` contains the engine, frontend, vision tools and two benchmark tools
at production **b7c3eb5b12a030725bfb0186d27065bc6e376685**, with deployment paths,
addresses and local reference names generalized. This is an implementation snapshot,
not the entire upstream operations/evidence repository. Each file has original and
sanitized hashes in `SOURCE.json`; `vendor/sanitization.json` discloses the categories.
The included fleet file is an intentionally incomplete generic template, supplied because CMake copies it beside the binaries; runtime still requires your own completed fleet file. No arithmetic change or parser protocol-literal rewrite is intended by sanitization.

`vendor/upstream/` contains the corresponding base implementation at **4e70b2ab**.
`patches/` contains four standalone feature patches (GLP steering, DSML parser,
sampler clamp, native vision) **plus one separate cache-fidelity prerequisite**.
They form an **ordered five-patch series**, not four independent patches against a
pristine base. The prerequisite preserves production's prompt/session repairs.
[Patch manifest and commit mapping](../patches/README.md).

```sh
python3 scripts/source_tree.py --verify vendor/engine
python3 scripts/verify-patches.py
bash scripts/fetch-sources.sh  # compatibility name: copies local source to work/source
bash scripts/build-engine.sh
```

Staging refuses existing destinations; select a new destination rather than overwriting
work. Building verifies the included manifest in both staged trees. Install the compiler,
CUDA13 and RDMA development prerequisites listed in [setup](setup-spark.md) first.
CMake builds the engine, converters/verifier and Engram packer; Cargo uses the included
lockfile. Rust crates must be available from their publishers or your reviewed cache.
The build writes `work/compiled/source-build.json` with source-manifest and binary hashes;
it is a provenance receipt, **not GPU acceptance or an exact-production binary claim**.

The optional `rebuild-publication-engine.sh` cross-build helper also consumes the
included source. Its exact original cross-builder/sysroot is not distributed; prefer
the documented native ARM64 route unless you supply and qualify your own toolchain.

## Prepare the text assets

On the separate build/conversion host, acquire the official checkpoint. No weights
are downloaded implicitly by build scripts. Use the publisher's Hugging Face CLI and
honor its acquisition/license terms:

```sh
hf download deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --local-dir work/checkpoint
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Review the printed plan, then explicitly execute:
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --execute
```

The wrapper uses the **in-repo staged implementation**, not an external fork. For
ranks0–3 it runs `dsw_convert`, every-byte `dsw_verify --threads 4`, `engram_pack`,
then `make_hashmap_stdlib.py`. Require zero bad tensors and bytewise agreement in
`work/conversion-logs`, not just loading/CRC. `bundle/model/asset-hashes.json` is
written only after successful commands. No re-quantization or training is performed.
Retain authentic snapshot provenance: a command-line revision alone cannot establish
where an arbitrary local directory came from.

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

Copy only the matching rank and two shards plus common metadata into `/srv/pico/model`
on each node; verify hashes after transfer. Existing verified text ranks do not need
rewriting for vision. `--reuse --execute` requires the original authentic conversion
receipt and runs fresh four-rank verifiers while preserving original conversion lineage.
Never discard existing verified assets just to rerun this recipe.

## Vision and optional steering assets

For **running the published image**, these are already packaged; no extra download
is needed. To extract packaged runtime assets without starting a container:

```sh
bash scripts/stage-public-runtime.sh
```

It stages engine/frontend/vision/vector/notices under `bundle/`, verifies locked
hashes and refuses existing output artifacts. No private fallback exists. The older
`stage-qualified.sh` alias does **not** imply GPU qualification.

For a **source rebuild**, prepare vision from the pinned official snapshot and
included tools instead:

```sh
python3 scripts/prepare-vision.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Review, then repeat with --execute.
python3 scripts/fetch-vector.py           # show authentic URL/hash only
python3 scripts/fetch-vector.py --execute # required for the default GLP-39 ON launch
```

Vision uses the included `tools/vision/extract_pack.py`, exact HTTP206 tensor ranges,
publisher `inference/vision.py`, `image_processor.py` and config, and included
`vision_encoder.py` / `image_io.py`. It requires the **266-tensor** pack,
**970,536,960 BF16 payload bytes**, full-file SHA256
`b07abf470c4107ba3029fedb9de1fd8823a40041f99d0d278e536b06ed5bb446`.
A pre-obtained exact pack can be reused; no synthetic encoder/projector is allowed.
Keep canonical attention (`VISION_SDPA_OPT_IN=0`) and serialized preload/encoding.
[GLP-39 source and MIT credit](steering.md); default ON, alpha 0.75, layers 1–39.
A vector-free bundle is only usable with explicit `--steering off` on every rank;
default ON fails startup if the authentic vector or its verified hash is missing.

## Assemble a new all-in-one image

Required `bundle/`: binaries, upstream notices, all four text ranks/eight Engram
shards/hashmap/metadata and their successful conversion receipt; vision files and
receipt; optionally authentic vector. This layout includes text weights and is
much larger than the published runtime-only image.

Using the packaged binaries, the extraction step above supplies `bundle/bin` and
notices. For a local source build, stage its actual outputs instead:

```sh
mkdir -p bundle/bin bundle/notices
cp work/compiled/bin/dsgb10_rank work/compiled/bin/dsfront bundle/bin/
cp work/compiled/notices/* bundle/notices/
SOURCE_BUILD_RECEIPT=work/compiled/source-build.json bash scripts/build-image.sh
```

Or, after extracting packaged binaries and preparing model/vision receipts:

```sh
bash scripts/build-image.sh
```

The validator checks actual binary hashes, source provenance, model/vision receipts,
paths and the GLP-39 ON default (alpha 0.75, layers 1–39). A local source receipt enables a **distinct local build**;
it does not weaken production locks or claim binary equivalence. The Dockerfile
inherits only the digest-pinned public audited runtime. A build does not push or
deploy. New binaries, changed assets or added layers require a new audit and full
four-rank acceptance before serving/publication. Do not run a local image under the
published candidate's tag/digest or relabel it qualified.

## Build-step provenance

| Local artifact / step | Recorded origin |
|---|---|
| `vendor/engine`, `SOURCE.json` | Production engine b7c3eb5, generalized deployment data only |
| `vendor/upstream` + `patches/series` | Pico base4e70b2ab + separate cache/GLP/parser/sampler/vision history |
| Lossless converter/verifier/Engram | Included `engine/weights`, `engine/engram`; historical `pico-glp-promotion-20261107/README.md` |
| Compact vision path | Included `tools/vision`; `pico-image-support-20261108/window-r2/HOST-QUALIFICATION.md` |
| Accepted production model gates | homeinfra cf6e8b67c, `pico-image-support-20261111/retrial-spark-only/REPORT.md` |
| Published runtime audit | Local `publication-audit.json`, `publication-remediation.md` and owner-adjudicated vendor findings |

Evidence references identify historical provenance; they are not private runtime
or build dependencies. No external engine checkout is required.

## Residual gaps

1. **Public sanitized candidate GPU qualification pending.** Same source/unchanged
   frontend and vision assets do not replace four-rank model acceptance of the new
   engine/runtime. The earlier incomplete PyTorch import smoke remains a qualification
   note, not a disclosure finding. No serving deployment is performed by this recipe.
2. **Full public-source pipeline not executed end to end here.** Acquisition, lossless
   conversion of this large checkpoint, extraction and all-in-one assembly must be
   executed/verified on a suitably provisioned build host. Offline tests do not prove
   that entire resource-intensive workflow or a stranger's fabric.
3. **Exact compiler reproduction is not promised.** Original cross-toolchain/sysroot
   inputs are not published. The native ARM64 build is supplied and source-verified,
   but binary hashes can differ. Qualify your resulting image rather than editing
   a guard to call it production-identical.
