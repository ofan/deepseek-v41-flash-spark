# Vision recipe completion — 2026-11-11

## Verdict

The exact production mirror is private and intact. The follow-up remediation removed the known deployment-specific disclosures in a **separate source-rebuilt runtime candidate**, also private. **The candidate audit is now CLEARED WITH OWNER WAIVERS:** Ryan waived the 11 vendor-binary build/assertion-path findings on 2026-11-11 at 23:58 EST. **Public distribution remains blocked solely by GHCR package-wide visibility:** the candidate and unwaived production mirror share one package and cannot have separate tag visibility. No visibility setting changed. The repository remains private; production, hardware hosts and routing were untouched.

The candidate is a runtime plus compact vision pack and optional vector, **not an all-in-one text-checkpoint bundle**. The original production qualification does not qualify its new executable/runtime. The sections below retain the historical production/mirror evidence; see the dated remediation section for the new artifact.

## Publication remediation — follow-up, 2026-11-12 UTC

Full evidence and tooling: [publication-remediation.md](publication-remediation.md), `publication-audit.json`, `publication-runtime.json`, and `publication-transfer.json`.

**Fixed:** fresh runtime-allowlist layers with generic config/profile/launcher; no inherited operational trees, homes, stale profiles, launchers or build history. The original executable itself contained **88 operator-home path occurrences**, also inside CUDA fatbins; host debug stripping retained them. Rebuilding unchanged source **b7c3eb5b12a030725bfb0186d27065bc6e376685** under generic paths removed those occurrences (**88 → 0**). No source or executable-string patch was used. The qualified frontend, compact vision pack and authentic optional vector retain their locked hashes. Steering defaults OFF. The recipe's build path now refuses the blocked original base and any uncleared runtime receipt.

**Private candidate:**

- `ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.11-native-vision-sanitized-candidate-r4`.
- Manifest **`sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`**.
- Config **`sha256:97cfdaafc7d1b5e7e0cd0e1b3b7a2cf787e8948586732089c9a24a334379e1df`**.
- **2 fresh layers**, **4,581,714,457 compressed bytes**; zero original layer digests retained.
- Rebuilt engine **`9b4aadf1ed5a5890d5e201d1f304be4a5461657d54eddf7df8b0f21882f45659`**. Full GPU/model qualification has **not** run.
- Owner-authenticated manifest GET by tag and digest, config hash and all three referenced blob digest/size HEAD checks pass. Package and repository remain **private**. This is not an independent full multi-gigabyte pull. No public/anonymous readback is claimed.
- The original production tag still resolves to **`sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`**; it was not overwritten or deployed.

**Deeper audit:** all **11,907 members** indexed; **9,384 non-payload regular files / 6,335,716,288 bytes** scanned, including binaries and large text. The two locked vision/vector payloads stay opaque. Config has **0 findings** and scanned bytes have no private-domain, tailnet-domain or internal-routing matches. Of **42 screening files / 173 raw matches**, bounded review classifies **31 files as benign patterns** and initially retained **11 for review**, now explicitly **WAIVED by Ryan**. These are third-party libksba, seven cuDNN libraries, cuSPARSELt and two NVPL libraries, listed with exact paths and layer digest in `publication-remediation.md`. They are not asserted to contain working credentials. They are explicitly waived by the owner: candidate audit verdict **CLEARED_WITH_OWNER_WAIVERS**, zero unresolved operator findings. The original mirror remains blocked. Raw findings and prior dispositions are retained.

**Host-only verification:** rebuilt ARM64 tests under QEMU pass authentic-vector reader validation (including six malformed-file refusals), fold arithmetic **0 reference differences** over **798,720 values / 156 rows**, and sampler endpoint regression over **16,777,216 bins**. Earlier isolated packaging smokes found missing loader/Python APIs; those failures are retained as packaging iterations rather than release passes. The final r4 smoke imported NumPy, PIL and safetensors, then **timed out during PyTorch import at the 660-second deadline**; the isolated task container was stopped/removed. No complete-import or runtime readiness pass is claimed. **75 offline recipe tests pass**. Results and scrub/static checks are recorded in `publication-verification.json` and `recipe-verification.json`. These are not GPU, generation identity, quality or performance acceptance.

**Remaining distribution blocker:** GHCR has package-wide visibility, and both tagged versions are in package ID 16805256. An approved separate public package boundary is needed. No visibility was changed and no versions were deleted. The exact candidate digest and owner waiver are approved; the incomplete runtime smoke is not a publication blocker. **Serving-qualification notes:** review/reproduce the local cross-toolchain/sysroot and obtain separately authorized full four-rank acceptance before serving use. External text assets and the new all-in-one bundle still require their own end-to-end build/audit/qualification. No production or visibility changes are part of this remediation.

## Layer-content publication audit — BLOCKED

The image is mirrored correctly but **must remain PRIVATE**. The follow-up [layer-content audit](layer-audit.md) indexed **72 layer descriptors / 68 unique layers**, scanned the authenticated image config (**1084 field/container entries, 199 history entries**) and bounded configuration text. It identified **61 file/directory occurrences across 9 layers** as publication blockers, plus separate unresolved screening candidates. Every finding is recorded with its exact layer digest, relative archive member and line references in `layer-audit.md` / `layer-audit.json`.

- Config: operator-home trial working directory/history; inherited operational and stale build/checkpoint metadata.
- Five historical `opt/pico/profile.json` versions: internal registry hostname, operator-home paths and rollback metadata. The final layer70 profile still contains these disclosures.
- Two `opt/pico/entrypoint.py` versions: fixed private-network frontend bind address. The layer69 version remains effective.
- Inherited vLLM operational scripts and b12x benchmark/evidence files: network literals and operator-home paths. An operator-named working-directory tree is also present.

**Ryan's conditional publication authorization was not exercised:** zero forbidden findings was required and that condition failed. No visibility change or anonymous-public-readback success is claimed. Final owner-authenticated readback confirms the package is still private and the manifest digest is unchanged; the git repository is also still private. No production, Spark or routing system was accessed. No image code was executed and no tensor/tokenizer member was opened.

A new, clean publication artifact must exclude old operational layers and use generic config/launcher/metadata. Overwriting or deleting a file in a later layer does not remove the older bytes. Sanitizing necessarily changes the digest. That original audit did not rebuild, deploy or publish anything; the subsequent private remediation is documented above.

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

Added compact-vision staging from the pinned public checkpoint/fork extractor, qualified-image artifact extraction, bounded optional authentic vector acquisition, vision-aware profile validation, rank0 native-encoder orchestration and offline regressions. The historical recipe pinned the qualified mirror; remediation now removes that contaminated default and requires a separately audited source-rebuilt runtime receipt. Every step maps to recorded homeinfra or fork documentation in [build.md](build.md).

Remaining gaps are explicit:

The private transfer has no remaining blocker. Independent recipe gaps remain:

1. Original cross-build native-input/sysroot/toolchain bundle is not published; original binaries remain extractable for private/forensic use but contain deployment-path disclosures. A generic-path rebuild was performed with local tooling; the toolchain/sysroot are still not independently published or reproduced. It is not byte-identical or GPU-qualified.
2. New all-in-one layout and public-source asset pipeline have not been executed end-to-end: acquire/verify official snapshot and authentic notices, convert/verify/reuse text assets, extract/verify compact vision, optional vector, build, size/SBOM/dependency audit and full-ring acceptance. The generic launcher has host tests only, not four-rank deployment acceptance.
3. The original mirror layer-content audit remains **BLOCKED**. The separate r4 candidate audit is **CLEARED WITH OWNER WAIVERS**. Its public distribution is blocked by shared package visibility, not by the waived vendor findings or incomplete runtime smoke. Repository visibility remains private.

The original scaffold report is retained as superseded historical evidence. Original completion/transfer did not compile or qualify a new image. The later remediation did rebuild the engine and construct/run isolated development-only runtime candidates, as documented above; it did not deploy, download/reconvert text weights, or perform new model inference.

## Verification

See `recipe-verification.json` for final offline unit-test counts, scrub result and static checks. These check the **recipe**, not the model gates. The final source commit/push and repository privacy check are reported in the turn result (avoiding self-referential commit hashes here).

## Publication request readback — 2026-11-12 UTC

At 05:00:23Z, the owner API reports package 16805256 private and both tags as versions within it. Candidate manifest GET200 hashes to `sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`; original mirror GET200 hashes to `sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`. Anonymous manifest and anonymous pull-token requests both return401 for each. Repo is private. See `publication-visibility.json` for exact statuses and version IDs. There is **no successful public readback**: changing this package would expose the explicitly protected original mirror too. No visibility, deletion, production or repository-access change occurred.
