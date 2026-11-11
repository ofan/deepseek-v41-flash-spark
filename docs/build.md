# Build the native-vision recipe

## Two different artifacts — do not confuse them

1. **Exact private production mirror**: `ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1@sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`. Same manifest/config/layers as the qualified production artifact, including its existing launcher/defaults. **Transfer failed; this reference is not published yet.** Its text rank/Engram assets are externally mounted. It is not an all-in-one model package.
2. **All-in-one bundle candidate**: the Dockerfile combines the qualified runtime/binaries, independently verified official stock rank files/Engram, compact vision pack, publisher preprocessing/ViT modules and optional GLP-39 into a **new** image. Its generic supervisor defaults steering OFF and vision ON. Adding assets/changing launcher changes the digest. **Not built or fleet-qualified in this task.**

No script builds on a Spark, deploys, changes a route or pushes an image automatically. Use an off-serving build host; TP4 model acceptance requires a separate compatible four-rank ring or a separately authorized window.

## Locked inputs

See `sources.lock.json` (full revisions/hashes):

- Engine AND frontend: `ofan/pico-dgx-ds4`, `feature/native-vision-20261108`, **b7c3eb5b12a030725bfb0186d27065bc6e376685**. This retains GLP, DSML, sampler, cache and native-vision fixes together. Do not substitute a contribution-only branch.
- Stock text and native vision weights: `deepseek-ai/DeepSeek-V4.1-Flash-1017`, revision **1bae0e1088993b9b82de08f59de5be5a34e42170**. Lossless layout conversion, no re-quantization, no training, no baked uncensoring.
- Compact vision: **266 BF16 tensors**, **970,536,960 payload bytes** (0.904 GiB rounded), pack SHA256 **b07abf470c4107ba3029fedb9de1fd8823a40041f99d0d278e536b06ed5bb446**. The pack contains tower + trained aligner + three learned delimiter vectors. The text rank files already contain the visual routing biases and need no vision-related reconversion.
- Optional authentic msuiche GLP-39: SHA256 **9c66d47701e0ceb42c33906f2d3789c0f1f16b21e7d97185f20f7f3f09fbf5cf**; tested alpha0.75/layers1–39. See [license/source](steering.md).

## 1. Fetch source, compile or reuse exact qualified binaries

```sh
bash scripts/fetch-sources.sh
# Off-serving ARM64 CUDA13 builder only; creates source-build candidate:
bash scripts/build-engine.sh
```

The source script checks clean pinned checkouts, builds CMake engine and locked Cargo frontend and copies upstream notices. Prerequisites are in [setup](setup-spark.md). A clean source build is **not guaranteed to reproduce qualified binary bytes**: production used a hash-preserving cross-relink with 13 preserved native inputs. The exact original input/sysroot/builder bundle is not published here. The validator rejects binaries other than:

- Engine `b12cbb69d30976d2a378f258fb2f75eee36da251ced1530f47ccea56993286b2`.
- Frontend `860ec4f3a88c3b6833b88f03829728f537a498deee67cb540f9bd50ad72223f5`.

**Scripted qualified-binary route once the mirror is available:**

```sh
bash scripts/stage-qualified.sh
```

This pulls the digest-pinned mirror on the build host, creates but **never starts** a disposable container, extracts `/opt/pico/dsgb10_rank`, `/opt/pico/dsfront` and `/opt/pico/vision/vision.safetensors` into ignored `bundle/`, checks their three qualified hashes and removes the never-started container. It refuses existing destination artifacts. This preserves qualified binaries instead of pretending a new compiler produced the same bytes. Source remains pinned for audit/rebuild.

**Manual step if using a new source build:** obtain the original qualified 13-input/linker/sysroot bundle and original relink procedure from its custodian, verify the native-input manifest/control binary, then link the changed model/Engram/server modules exactly as recorded. If unavailable, keep the source-build result separate and independently qualify it; do not edit the expected hashes to make it appear production-identical. No public download URL or builder digest is known, so none is invented.

## 2. Acquire the pinned official snapshot

Install the Hugging Face client on a build host and acquire the exact revision with your own authorized access:

```sh
hf download deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --local-dir work/checkpoint
```

This is an explicit large download, **not executed in this task**. Keep acquisition/verification receipts. Revision arguments in our converters assert provenance; they cannot cryptographically prove an arbitrary local directory came from that revision. Include original metadata and `inference/{vision.py,image_processor.py}`. Never print tokenizer contents or inference captures into a text-only model session.

## 3. Text rank files and Engram — only for a new standalone package

```sh
# Plan-only by default, no assets read or created:
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Add --execute only on the prepared off-serving converter host.
```

For each rank0–3 the script runs the pinned `dsw_convert`, every-byte `dsw_verify --threads 4` and `engram_pack`; then the pinned `make_hashmap_stdlib.py`. It preserves metadata and writes a file-hash receipt only after every command exits0. Review the verifier logs: require zero bad tensors and every-byte comparison, not load/CRC alone. Conversion timestamps can change full-file DSW hashes without changing tensor bytes.

If reusing already verified stock text ranks/Engram, **do not reconvert them just to add vision**. Stage the four DSW files, eight Engram shards, hash map, metadata and original authentic conversion receipt/logs. Then use:

```sh
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --reuse
# Add --execute only on the prepared build host; runs FOUR dsw_verify commands.
```

Reuse mode checks every original file hash, runs every-byte verification with the current pinned tools against the pinned checkpoint, retains the original conversion commit and receipt hash, and records the new verification commit separately. It does **not** rewrite rank/Engram files or relabel their converter lineage. Without authentic acquisition/conversion receipts, reconstruct provenance from the original verified logs and source acquisition records before using this path; a self-authored hash list alone does not prove official model identity.

## 4. Prepare compact vision (no text rank changes)

```sh
python3 scripts/prepare-vision.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Plan-only; add --execute on the prepared build host.
```

The wrapper verifies the fork revision, stages the checkpoint's exact `vision.py`, `image_processor.py` and config, plus the fork's `vision_encoder.py` / bounded `image_io.py`. If an exact pack was extracted by `stage-qualified.sh`, it verifies/reuses it. Otherwise it derives the **266-tensor inventory and raw headers** from the pre-obtained pinned snapshot and invokes the fork's existing **`tools/vision/extract_pack.py`**. That exporter fetches exact HTTP206 tensor ranges from the pinned publisher revision, without reconverting/downloading text tensor payloads. The wrapper requires the qualified **full-file pack SHA256**, writes a compact-only index and hashes every vision runtime file. No replacement encoder/projector or synthetic weights are permitted.

The public-source inventory wrapper has offline header/schema tests; its full ~1GiB extraction was **not executed here**. If it fails the qualified pack hash, stop; preserve logs and compare header ordering/serialization against the pinned exporter before claiming byte identity. The qualified-mirror extraction is the exact-byte fallback, **not a generated substitute**.

Canonical publisher attention is selected with `VISION_SDPA_OPT_IN=0`, serialized rank0 GPU encoding with `VISION_PRELOAD=1`. Do not enable the inherited optional SDPA reshape optimization without separate arithmetic/output acceptance. Image histories are fresh, no-base, no-KEEP, no prefix reuse. The engine broadcasts/injects image spans across all ranks, selects visual routing bias and masks Engram on span positions.

## 5. Optional authentic vector, notices and bundle validation

```sh
python3 scripts/fetch-vector.py             # show public URL/hash, no download
python3 scripts/fetch-vector.py --execute   # optional explicit download + exact hash
```

The public vector URL is hash-guarded even if its hosting branch changes. If access terms/authentication prevent download, obtain the exact publisher file manually and copy it to `bundle/vectors/glp39.gguf`, verify the SHA256 above and retain publisher notices. Never synthesize or silently replace it. Omit it entirely for a stock-only image; default steering stays OFF either way.

Required ignored bundle layout:

```text
bundle/
  bin/{dsgb10_rank,dsfront}
  notices/engine-NOTICE
  model/{config.json,tokenizer.json,rank0.dsw,rank1.dsw,rank2.dsw,rank3.dsw}
  model/engram-l{1,14}-r{0,1,2,3}of4.bin
  model/{engram_hashmap.bin,asset-hashes.json}
  vision/{vision.safetensors,config.json,model.safetensors.index.json}
  vision/{vision_encoder.py,image_io.py,asset-hashes.json}
  vision/inference/{vision.py,image_processor.py}
  vectors/glp39.gguf                       # optional
```

Copy authentic upstream engine NOTICE from the pinned source (`work/source/engine/NOTICE`); preserve all model, vector and dependency notices. Run:

```sh
python3 scripts/prepare-bundle.py
```

The validator checks qualified binaries, all rank/Engram/metadata receipt hashes, exact vision pack/runtime hashes, provenance, path traversal/symlinks and optional authentic vector. Only then does it generate `bundle/profile.json`. This proves internal artifact consistency, **not** truth of a forged acquisition/conversion receipt or model acceptance.

## 6. Build the NEW all-in-one candidate (no push)

```sh
bash scripts/build-image.sh
```

The default Dockerfile runtime base is the qualified private mirror **by immutable tag+digest**. This closes the arbitrary-runtime-selection gap **only when that mirror is actually available**; the present transfer blocker still prevents pulling it. It inherits production CUDA/RDMA/Python dependencies instead of inventing a supposedly equivalent public base. An alternate reviewed base must be pinned by digest and independently qualified for shared-library closure, ARM64/GB10, Python/PyTorch/Pillow/safetensors, licenses and runtime behavior.

The result is a **local** `2026.11.08-native-vision-bundle-candidate`. It includes all ranks and will be much larger than the 11.56GB compressed runtime/vision mirror. Full bundled compressed size, extraction/disk headroom and registry large-layer compatibility have not been measured. No image build or model download ran here.

Before release: extract actual profile/binaries/vision pack from the built image and compare hashes; inspect dynamic dependencies; retain SBOM/licenses; smoke-test the generic supervisor; then run all full-ring gates. Text SUBMIT layout must remain unchanged when no images are supplied. Image payload/slot lifecycle, cache isolation and bounded input rejection must be checked, not inferred from host tests.

## Provenance mapping to homeinfra

Reference branch `glp/pico-glp-steer-20261106`, current evidence commit **cf6e8b67c**. Evidence paths below are under `docs/operations/evidence/` unless explicitly `config/`.

| Recipe step | Recorded counterpart | What is / is not reproduced |
|---|---|---|
| Full source pin and binary guards | `config/pico-production/profile.json`; `pico-image-support-20261108/window-r2/REPORT.md` | Current engine/frontend b7c3eb5, retains all production fixes |
| Engine source compile / qualified extraction | `pico-image-support-20261108/window-r2/HOST-QUALIFICATION.md`, `host/` | Compile command supplied; original exact relink inputs not publicly packaged |
| Stock text conversion / every-byte verification | `pico-glp-promotion-20261107/README.md`; pinned engine README steps4–5 | Same tools; reused production text ranks need no vision rewrite |
| Exact compact vision and publisher code | `pico-image-support-20261108/window-r2/HOST-QUALIFICATION.md`; pinned fork `tools/vision/extract_pack.py` | Qualified pack hash enforced; public preparation wrapper added, full extraction not rerun |
| Optional vector | `pico-glp-upstream-prepare-20261107/README.md` | Exact published hash, default OFF in generic supervisor |
| Supervision / immutable packaging | `config/pico-vision-entrypoint.py`; `pico-image-support-20261108/window-r2/image/` | Generic new launcher/paths, distinct all-in-one layout; not an exact OCI rebuild |
| Qualified production gates | `pico-image-support-20261111/retrial-spark-only/REPORT.md` | Historical exact production artifact passed; new bundle still requires acceptance |

## Residual gaps

1. **GHCR transfer blocked**: source blob reconnect failed with connection refused on both attempts; no destination manifest/package published. Exact sanitized errors/receipt: [completion report](completion-report.md), `ghcr-transfer.json`. Remaining action: restore source-registry connectivity on the transfer/build host and rerun the digest-preserving private copy, then verify visibility and digest. No serving change is involved.
2. **Independent public-source byte-identical engine build is not turnkey**: the original 13 qualified native inputs/toolchain/sysroot are not distributed. The scripted exact-binary extraction requires the private mirror; otherwise obtain those inputs from their custodian or independently qualify a new build. No builder digest/download URL is invented.
3. **New all-in-one layout remains unexecuted/unqualified**: official snapshot acquisition, text conversion/verification, public compact extraction, optional vector acquisition, all-asset build, storage/SBOM/license closure and generic launcher/full-ring acceptance must actually run. Commands and fail-closed checks are supplied; test success here is **offline recipe verification only**. Snapshot origin and authentic notices still require operator review.
4. **Public distribution readiness is separate**: the exact inherited image preserves existing defaults, labels/history/layers; it is not a scrubbed public rebuild. Review all layer contents/dependency licenses and remove any nonpublishable material in a separately built image before any public-release decision. No visibility change is authorized here.
