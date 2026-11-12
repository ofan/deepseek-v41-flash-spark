# Vision recipe completion — 2026-11-11

## Verdict

Recipe documentation and fail-closed build scaffolding now target **current native-vision production**, engine **b7c3eb5**, not the retired sampler serving artifact. **GHCR staging is complete: the private copy has the exact production manifest digest.** Two historical failed copies are retained in the receipt, followed by the diagnosed/resumed transfer and verified readback. The repository remains PRIVATE. No visibility setting was changed. No Spark, production container, service or routing system was accessed or changed.

The recipe is not represented as a freshly built/qualified all-in-one image: production itself mounts the large text/Engram assets externally. The exact mirror and new all-in-one Dockerfile are explicitly distinguished throughout.

## Layer-content publication audit — BLOCKED

The image is mirrored correctly but **must remain PRIVATE**. The follow-up [layer-content audit](layer-audit.md) indexed **72 layer descriptors / 68 unique layers**, scanned the authenticated image config (**1084 field/container entries, 199 history entries**) and bounded configuration text. It identified **61 file/directory occurrences across 9 layers** as publication blockers, plus separate unresolved screening candidates. Every finding is recorded with its exact layer digest, relative archive member and line references in `layer-audit.md` / `layer-audit.json`.

- Config: operator-home trial working directory/history; inherited operational and stale build/checkpoint metadata.
- Five historical `opt/pico/profile.json` versions: internal registry hostname, operator-home paths and rollback metadata. The final layer70 profile still contains these disclosures.
- Two `opt/pico/entrypoint.py` versions: fixed private-network frontend bind address. The layer69 version remains effective.
- Inherited vLLM operational scripts and b12x benchmark/evidence files: network literals and operator-home paths. An operator-named working-directory tree is also present.

**Ryan's conditional publication authorization was not exercised:** zero forbidden findings was required and that condition failed. No visibility change or anonymous-public-readback success is claimed. Final owner-authenticated readback confirms the package is still private and the manifest digest is unchanged; the git repository is also still private. No production, Spark or routing system was accessed. No image code was executed and no tensor/tokenizer member was opened.

A new, clean publication artifact must exclude old operational layers and use generic config/launcher/metadata. Overwriting or deleting a file in a later layer does not remove the older bytes. Sanitizing necessarily changes the digest. This audit did not rebuild, deploy or publish anything.

## Current qualification provenance

Homeinfra branch `glp/pico-glp-steer-20261106`, **cf6e8b67c8cb4c7a07dc52aaccf16f09fb39e774**:
`docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`.

- Prefill32K/131K/500K/1M: **8951 / 9259 / 9076 / 8598 tok/s**, rounded.
- Decode c1: **88.772 tok/s**.
- Identity: **9/9 OFF + 9/9 alpha-zero**, bit-identical including1M needle.
- Fixed image QA: **88/88 OFF + 88/88 GLP-39**; six-fixture repeat/stream/c1/c16 matrix.
- Protocol12 rounds: **0 leaks/errors**. Stability: **16/16**, **0 restarts/OOM/errors**.
- These are production evidence, **not new inference performed for recipe completion**.

[Benchmarks](benchmarks.md) gives a source for every figure and separates historical14/14 capability points from the current6/6 capability +2/2 needles.

## Registry manifest — freshly read, no serving access

Verified PRIVATE destination:
`ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1`.

- Source manifest: **sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9** (raw bytes independently hashed).
- Config: **sha256:979ff212061ffe5d43ecd14e2c8a3d32d9cfceedf1b3e350008b7cdcf3226382**, **86,924 bytes**.
- **72 layers**, compressed descriptor sum **11,564,486,734 bytes** (~11.564GB; not the hundreds-of-GB external text model, nor unique transfer size/uncompressed footprint).
- Linux/ARM64. Read-only configuration inspection; no container ran. The earlier config/history-only domain scan found0 private-domain matches; the later **layer-content audit found publication blockers**, including domains inside profiles. See the audit above; manifest integrity is not publication clearance.
- Machine-readable facts: `production-manifest.json`.

## GHCR transfer — resolved, digest and privacy verified

The transfer ran on an off-serving development host. DNS selected a tailnet TCP relay before the source registry ingress. Read-only inspection showed that relay's nginx container had a **32 MiB memory limit**, was **OOMKilled (exit 137) at 21:07:53 UTC**, and restarted at **21:08:18 UTC**. The second failed copy recorded its refused reconnect at **21:07:54 UTC**, inside that outage. Termination drops established blob streams; the listener is unavailable before restart. This was **TLS TCP stream passthrough with ssl_preread**, not HTTP response buffering. Registry and ingress did not restart. The first copy had the same transport signature, but its exact relay termination timestamp was not retained; it is not independently timestamp-proven.

**Fix:** the transfer client alone selected the directly routed registry ingress, retaining the original TLS hostname, SNI and certificate verification. An unauthenticated registry probe returned expected 401 with TLS verification 0; an authenticated exact 1 MiB byte range of the originally failing blob returned 206. No shared DNS, hosts, gateway, proxy, network or serving configuration was changed. The shared relay memory setting is unchanged; this is a scoped transfer-path fix, not a claim to repair the shared relay.

The resumable client caches opaque source blobs, downloads 64 MiB exact byte ranges, verifies full SHA256, HEAD-checks destination blobs and PATCH-uploads only missing work with offset recovery. GHCR explicitly rejected a 4,611,987-byte PATCH with 416 and message `the request body is too large and exceeds the maximum permissible limit of 4.00MiB`. Reducing PATCH chunks to **4 MiB maximum** fixed that client compatibility issue; completed blobs and verified local cache were reused rather than restarting the image transfer. Credentials remained only in memory; neither credentials nor upload session URLs were recorded.

**Verified result:**

- Destination: `ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1`.
- GET by tag **and** digest returned original raw-manifest bytes with SHA256 **`sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`**.
- All **69 unique config/layer blobs** passed digest/size HEAD checks (72 layer descriptors include duplicates). Config GET/hash verified Linux/ARM64 identity. Source config/layers/manifest were not rewritten.
- Owner-authenticated GitHub package lookup returned **200**, visibility **private**. No visibility setting was changed.
- Machine-readable timestamps, per-blob results, source/destination digest, diagnostics and historical failures: `ghcr-transfer.json`. Independent post-copy readback is retained there too.

The mirror preserves the original image bytes and existing metadata. It is not a rebuilt or newly qualified all-in-one bundle and does not embed externally mounted text assets. Public publication requires separate review; nothing was made public.

## Build work and residual gaps

Added compact-vision staging from the pinned public checkpoint/fork extractor, qualified-image artifact extraction, bounded optional authentic vector acquisition, vision-aware profile validation, rank0 native-encoder orchestration and offline regressions. Pinned the default runtime to the qualified image instead of inventing a public CUDA/PyTorch/RDMA substitute. Every step maps to recorded homeinfra or fork documentation in [build.md](build.md).

Remaining gaps are explicit:

The private transfer has no remaining blocker. Independent recipe gaps remain:

1. Original cross-build native-input/sysroot/toolchain bundle is not published; exact binaries can now be extracted from the qualified private mirror. A fresh compile is not falsely promised byte-identical.
2. New all-in-one layout and public-source asset pipeline have not been executed end-to-end: acquire/verify official snapshot and authentic notices, convert/verify/reuse text assets, extract/verify compact vision, optional vector, build, size/SBOM/dependency audit and full-ring acceptance. The generic launcher has host tests only, not four-rank deployment acceptance.
3. Layer-content review is now recorded and **BLOCKED**. Remove the exact findings in a separately built artifact, resolve remaining review candidates and complete dependency/license review before considering publication. Conditional package-only publication was authorized only for a clean audit; this artifact did not meet that condition. Repository visibility remains private.

The original scaffold report is retained as clearly superseded historical evidence. No model/vector download, engine compile, new container build, deployment or new inference was performed in this recipe-completion turn. The follow-up transfer copied the image successfully; it did not download external text weights, execute a container, or qualify a fresh bundle.

## Verification

See `recipe-verification.json` for final offline unit-test counts, scrub result and static checks. These check the **recipe**, not the model gates. The final source commit/push and repository privacy check are reported in the turn result (avoiding self-referential commit hashes here).
