# Vision recipe completion — 2026-11-11

## Verdict

Recipe documentation and fail-closed build scaffolding now target **current native-vision production**, engine **b7c3eb5**, not the retired sampler serving artifact. **GHCR staging is BLOCKED by source-registry blob connectivity.** Two digest-preserving copy attempts failed; neither published a package manifest. The repository remains PRIVATE. No visibility setting was changed. No Spark, production container, service or routing system was accessed or changed.

The recipe is not represented as a freshly built/qualified all-in-one image: production itself mounts the large text/Engram assets externally. The exact mirror and new all-in-one Dockerfile are explicitly distinguished throughout.

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

Intended PRIVATE destination:
`ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1`.

- Source manifest: **sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9** (raw bytes independently hashed).
- Config: **sha256:979ff212061ffe5d43ecd14e2c8a3d32d9cfceedf1b3e350008b7cdcf3226382**, **86,924 bytes**.
- **72 layers**, compressed descriptor sum **11,564,486,734 bytes** (~11.564GB; not the hundreds-of-GB external text model, nor unique transfer size/uncompressed footprint).
- Linux/ARM64. Read-only configuration inspection; no container ran. Source config/history scan found0 private-domain matches, but **this is not a complete layer-content/public-distribution audit**.
- Machine-readable facts: `production-manifest.json`.

## GHCR result and exact blocker

The owner credential was obtained through the existing secret manager and verified as the intended account. Registry auth stayed in an anonymous in-memory file descriptor inherited by the transfer process; no secret was printed or stored in a disk auth file. Copy used an immutable source digest and `--preserve-digests`. The second attempt enabled two bounded transport retries. No quota/size failure or digest mismatch was reported.

Both failures occurred while writing a destination blob after the source stream broke and the reconnect to the **source blob endpoint was refused**. The failing source blob digest was:

`sha256:2fe1bd723675049a1f5c52ea338ce521041685f0a9be654144096643d8cb07b8`.

Sanitized tool error (private network identifiers and ephemeral upload ID removed only):

```text
writing blob: Patch "https://ghcr.io/v2/ofan/deepseek-v41-flash-spark/blobs/upload/UPLOAD_ID": happened during read: unexpected EOF (while reconnecting: Get "https://SOURCE_REGISTRY/v2/library/pico-dsgx10/blobs/sha256:2fe1bd723675049a1f5c52ea338ce521041685f0a9be654144096643d8cb07b8": dial tcp SOURCE_ADDRESS:443: connect: connection refused)
```

Copy exit status **1** on both attempts. Owner-authenticated package lookup returned **404 before and after** each attempt. No completed package/destination manifest/digest is claimed. Partial blob upload traffic is not a published image. Full sanitized attempt times/errors and visibility status are retained in `ghcr-transfer.json`.

## Remaining private transfer steps

1. Restore source-registry connectivity from an authorized transfer host, including sustained reads of the named blob. Do not change serving systems to do this.
2. Re-read the immutable source tag/digest; confirm destination absent or already PRIVATE. Stop if an existing destination is public. Never mutate visibility.
3. Run an OCI-aware digest-preserving copy, using transient authentication. Generic command shape:

```sh
# SOURCE_IMAGE_AT_DIGEST is supplied out of band; no private endpoint is committed.
skopeo copy --preserve-digests "$SOURCE_IMAGE_AT_DIGEST" \
  docker://ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1
```

4. Verify the destination raw-manifest SHA256 equals the locked digest, config/layer digests/counts agree, ARM64 identity and owner-authenticated pull work, and the package is PRIVATE (new GHCR packages default private). If privacy cannot be verified, do not report success.
5. Update the transfer receipt/status only after proof. Linking inherited package source metadata to this private recipe is separate from copying bytes; do not rewrite image labels and still claim the original digest.

## Build work and residual gaps

Added compact-vision staging from the pinned public checkpoint/fork extractor, qualified-image artifact extraction, bounded optional authentic vector acquisition, vision-aware profile validation, rank0 native-encoder orchestration and offline regressions. Pinned the default runtime to the qualified image instead of inventing a public CUDA/PyTorch/RDMA substitute. Every step maps to recorded homeinfra or fork documentation in [build.md](build.md).

Remaining gaps are explicit:

1. Failed private registry transfer (above); no GHCR package exists yet.
2. Original cross-build native-input/sysroot/toolchain bundle is not published; exact binaries can be extracted once the qualified mirror exists. A fresh compile is not falsely promised byte-identical.
3. New all-in-one layout and public-source asset pipeline have not been executed end-to-end: acquire/verify official snapshot and authentic notices, convert/verify/reuse text assets, extract/verify compact vision, optional vector, build, size/SBOM/dependency audit and full-ring acceptance. The generic launcher has host tests only, not four-rank deployment acceptance.
4. Public-release license/layer-content review is still required. Neither repository nor package may be made public under this task.

The original scaffold report is retained as clearly superseded historical evidence. No model/vector download, engine compile, new container build, deployment or new inference was performed in this recipe-completion turn. The registry copy did transfer some image blobs before failing; it must not be described as zero image traffic.

## Verification

See `recipe-verification.json` for final offline unit-test counts, scrub result and static checks. These check the **recipe**, not the model gates. The final source commit/push and repository privacy check are reported in the turn result (avoiding self-referential commit hashes here).
