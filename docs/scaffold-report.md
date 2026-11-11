# Historical scaffold report (superseded)

This file records the **initial scaffold at 75f0448**, before native vision became production. It is retained as historical provenance only. Its sampler artifact, no-image statement, gaps and unexecuted push plan are **not current status**. See [completion report](completion-report.md), [current build](build.md) and [current benchmarks](benchmarks.md).

# Private recipe scaffold — 2026-11-11

## Verdict

Private source-package scaffold prepared for `ofan/deepseek-v41-flash-spark`. This is **not a built or published all-in-one model image**. Historical production engine/model/vector provenance is pinned; build and packaging gaps are explicit. No serving machine, Spark, proxy or production configuration was accessed or changed. No model/vector tensor payload was downloaded. No image build, layer download or container push occurred.

The shared homeinfra checkout was never switched or edited. Source documentation was read from branch `glp/pico-glp-steer-20261106`, snapshot `f2a0a4dbea07ac9bf94bb24d8605da8f43a9a099`, through a read-only extracted snapshot. No request payload, tokenizer contents or image-support artifact was read into the resumed session. Only reports/text documentation were used for recipe/benchmark content; other artifacts were inventoried by name and size.

## Manifest facts (read-only, freshly verified)

Source artifact: `pico-dsgx10:2026.11.08-sampler-open-unit-r1`.
The private source registry hostname is deliberately omitted from publishable repository content.

- Manifest digest: **`sha256:bc0d7b73ed1d6e5408f9707d613b5c7c8a42f7c23c07b061f8aadafa9f22b3bc`**.
- Config digest: **`sha256:187b53d50685f7e7b6ae65e7908b07e673315557ad8a2b042809b45554f68281`**.
- Media type: Docker distribution manifest v2.
- Layers: **68** descriptors.
- Compressed layer descriptor sum: **10,785,944,568 bytes** = **10.785944568 GB / 10.045194 GiB**.
- Config: **85,742 bytes**.
- Layers + config: **10,786,030,310 bytes**.
- Manifest JSON: **14,567 bytes**; descriptor sum + config + manifest: **10,786,044,877 bytes**.

Tag and digest reads independently returned the expected digest; the raw manifest bytes were hashed and matched. No layer or config blob was downloaded. These totals are descriptor sizes, not uncompressed storage, unique-layer transfer cost or the size of a future bundled model image. Machine-readable facts: `production-manifest.json`.

## GHCR push plan — not executed

Destination: **`ghcr.io/ofan/deepseek-v41-flash-spark`**, **PRIVATE package**, owned by `ofan`. Source: the versioned artifact and digest above at the privately configured source registry. No source registry address or credentials belong in this repository.

1. In a separately authorized transfer task, verify the source version tag still resolves to the pinned manifest digest. Verify the destination package is absent or already PRIVATE. **Do not change any visibility setting.** If an existing package is not PRIVATE, stop.
2. Confirm package/account storage quotas and transfer headroom. The **existing** image needs approximately **10.786 GB** of compressed referenced content before reuse; the all-in-one model image will be much larger and has **no measured size yet**.
3. Review the image configuration/history/layers for redistribution safety, embedded site metadata and all dependency licenses. A private mirror can preserve the exact digest only if manifest bytes/layers/config remain unchanged; any sanitization or bundling requires a new digest and fresh verification.
4. For an authorized **private historical-image mirror**, copy by **digest** with an OCI-aware registry tool preserving manifests, under a versioned historical tag. Confirm source/destination config, every layer digest, manifest digest and ARM64 runtime identity. This mirror alone is NOT the promised model-included package and must be labeled accordingly.
5. For the **actual all-in-one recipe release**, close `build.md` gaps, acquire/verify exact assets, assemble the one-image candidate off serving systems and record its new size/SBOM/digest. Prove the extracted profile matches shipped binaries, then complete fresh model/protocol/concurrency gates. Use a distinct immutable version tag; never overwrite the historical tag or digest claim.
6. Authenticate transiently with least-privilege permissions, push only under separate authorization, and immediately verify the package remains PRIVATE and that destination digests match the intended artifact. Associate it only with the private recipe repository. Do not enable public access, change visibility, or use a floating tag.
7. Record destination receipts and a private pull verification. For the bundled release, verify both steering-OFF default and explicit GLP-39 opt-in. Do not deploy as part of a registry transfer.

**Nothing was pushed to GHCR in this scaffold turn.** Repository creation/push is source publication only and is not container publication.

## Evidence sources for all benchmark figures

See the row-level table in `benchmarks.md`:

- `docs/operations/evidence/pico-token-corruption-20261108/`: sampler production 8,999 at 32K; 9,380 at 131K; 88.6 c1; OFF/zero identity; capability/needles 14/14; stability.
- `docs/operations/evidence/pico-session-cache-fix-20261106/`: reused historical comparison baselines 9,098.9 / 9,479.4 prefill; 82.2 / 155.0 / 259.5 decode c1/c4/c16; 16 slots and 1,048,576 context; session/spill limits. These values are the report's Prior Pico column, not the Fixed r5 column.
- `docs/operations/evidence/pico-glp-r4-window-20261106/`: exact 500,025 / 1,048,025 needles; 14/14 official vs 14/14 steered, delta 0; reused r5-comparator label.
- `docs/operations/evidence/pico-glp-promotion-20261107/`: full-spill promotion and retained exact needles.
- `docs/operations/evidence/pico-glp-upstream-prepare-20261107/`: vector full-file hash and 0-diff fold/reference arithmetic.

## Remaining gaps

The six release gaps in `build.md` are not hidden behind placeholder success: qualified cross-build/native object distribution, redistributable runtime dependency closure, full asset acquisition/conversion, the new one-image layout/size, real launcher/fabric validation, and fresh rebuilt-image acceptance. No end-to-end image reproducibility or deployment is claimed.

## Repository controls

The repository is created PRIVATE; no visibility-setting change is part of this work. Public-facing content uses generic paths, user-supplied fleet topology and the GHCR target only. License attribution is retained for Andy Shu, Picom, DeepSeek and msuiche. No personal access/contact data, infrastructure addresses, credentials, request captures or model payloads are included. Final commit, file inventory, tests, privacy verification and push receipts are reported in the turn result, avoiding a self-referential commit hash in this file.

## Host-only scaffold checks

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: **18/18 PASS**, zero failures.
- `python3 scripts/check-scrub.py`: **23 text files**, **0 forbidden-content matches**.
- `bash -n scripts/*.sh` (each script individually): **PASS**.
- Python AST parsing of every script and parsing of the source-lock/manifest JSON: **PASS**.
- Conversion plan-only CLI: **13 planned steps**, including **4** per-rank tensor verifications; no `work/` or `bundle/` assets created. Entrypoint/bundle-validator CLI help checks pass.
- `git diff --cached --check`: **PASS**.
- No model inference, converter execution, engine compilation, Docker build or runtime smoke is included in these scaffold tests.
