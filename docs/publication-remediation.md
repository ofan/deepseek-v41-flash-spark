> Historical audit/remediation record. Current distribution state is in [completion-report.md](completion-report.md). Private-predecessor records below are provenance only, never acquisition instructions.

# Publication packaging remediation — 2026-11-11

## Scope and release boundary

A **new, private source-rebuilt runtime candidate** is distinct from the qualified production mirror. The original tag, manifest and production remain unchanged. No visibility setting, serving system, hardware host, routing configuration or pull request is changed by this work. The git repository stays private.

The original audit and all its historical findings are retained in [layer-audit.md](layer-audit.md). Deleting files in a later layer cannot make that original artifact safe: the older layer blobs remain downloadable. Its digest cannot be both unchanged and sanitized. The prior conditional release authorization named that original digest, not a source rebuild.

## Owner waiver and publication eligibility — 2026-11-11 23:58 EST

**Candidate audit CLEARED WITH OWNER WAIVERS.** Ryan waived exactly the 11 third-party binary files below: vendor build/assertion paths inside NVIDIA and GNU binaries are vendor artifacts present in public CUDA images, not operator data. Every adjudication is retained and marked **WAIVED**, with the prior REVIEW disposition, author, time, scope and reason in `publication-audit.json`. No raw finding was deleted and this is not represented as an independent publisher provenance verification. Operator findings are **0**; unresolved candidate findings are **0**; waived vendor files are **11**. The waiver applies only to the exact sanitized r4 digest, not the original production mirror.

The incomplete PyTorch/QEMU smoke remains a **serving-qualification note**, not a publication blocker. The candidate is **not GPU-qualified for serving**. Publication permission does not imply runtime acceptance or deployment permission.

### Historical distribution blocker — superseded by separate-package copy

At 2026-11-12T05:00:23Z the approved candidate and original mirror occupied one
private package. Package-wide visibility could not safely expose only the candidate.
`publication-visibility.json` preserves that dated evidence. The owner subsequently
authorized a separate distribution package; the digest-preserving copy is complete.
The **current** blocker is owner-authenticated web access for its visibility change,
not shared-package placement. See `public-release.json` and the completion report.
The protected original package remains private; no version was changed or deleted.

Official reference: [GitHub package access control and visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

## Fixed packaging defects

- Construct fresh layers with a runtime **allowlist**, not a descendant of the contaminated image. No original layer or build-history entry is inherited.
- Omit prior operational application trees, benchmark/evidence receipts, account homes, old launchers/profiles, caches, temporary build payloads and unrelated model-serving frameworks.
- Preserve the qualified frontend and native vision pack byte-for-byte. Include the authentic optional GLP-39 vector, locked by its published hash. No text checkpoint weights were downloaded or reconverted; text ranks/Engram/tokenizer remain externally supplied assets.
- Replace profile, launcher, working directory, environment, account data and labels with generic recipe-owned equivalents. Steering defaults **OFF**; vision is enabled on rank zero. Fleet addresses must be supplied by the operator, not baked into the image.
- Preserve dependency copyright/license notices, including the original runtime license and the declared PyTorch dependency closure in a supplemental layer. Add the generic ARM64 dynamic-loader link there; this is a packaging dependency, not an engine patch.
- Remove the contaminated mirror as the Dockerfile's default base. The all-in-one build script now requires a privacy-cleared sanitized-runtime receipt and uses that runtime's engine hash, rather than overwriting it with the blocked production executable.

## Why an engine rebuild was necessary

The deeper **binary** scan found **88 operator-home path occurrences** in the qualified engine executable, not just the filesystem/config. They occur in host read-only data and CUDA fatbins. A host debug-strip experiment left **88/88** occurrences. Therefore a flatten-and-delete-only plan would still disclose those strings.

Rebuilt the unchanged pinned engine source **b7c3eb5b12a030725bfb0186d27065bc6e376685** under generic `/src` and `/build` paths using the already installed CUDA13 ARM64 cross-builder. Source and sysroot mounts were read-only; the container had no network, GPU access or capabilities. No source edit or executable string patch was used. The rebuilt executable has **0 operator-home path occurrences**.

- Original qualified engine SHA256: `b12cbb69d30976d2a378f258fb2f75eee36da251ced1530f47ccea56993286b2`.
- Rebuilt engine SHA256: `9b4aadf1ed5a5890d5e201d1f304be4a5461657d54eddf7df8b0f21882f45659`.
- Preserved frontend SHA256: `860ec4f3a88c3b6833b88f03829728f537a498deee67cb540f9bd50ad72223f5`.
- Preserved vision SHA256: `b07abf470c4107ba3029fedb9de1fd8823a40041f99d0d278e536b06ed5bb446`.
- Optional GLP-39 SHA256: `9c66d47701e0ceb42c33906f2d3789c0f1f16b21e7d97185f20f7f3f09fbf5cf`.

**This changes the executable hash. Historical production identity, quality and performance results do not qualify the new executable/runtime.** CPU regressions and packaging smoke tests cannot replace full GPU acceptance. Do not deploy this candidate based on this report.

## Reproducible tooling

1. `scripts/rebuild-publication-engine.sh`: requires an explicitly selected local builder by image ID, reviewed sysroot/toolchain, clean pinned source checkout and new output directory. It builds without network or a GPU under generic container paths. The builder used here has ID `sha256:2b4f41127b7a33a50f42e03994b9ab3754dcbb132c23b0c5e914c06d6d8fc657`.
2. `scripts/assemble-runtime.py`: validates the original manifest and every source-layer hash, applies whiteouts, stages only selected runtime files under opaque numeric names (never archive paths), adds generic metadata/profile/launcher and writes a new OCI core. It never executes image code, authenticates, pushes, deploys or changes visibility. Supply the pinned fork's authentic engine NOTICE and the hash-verified vector explicitly.
3. `scripts/add-dependency-notice.py`: accepts only that fresh one-layer core; adds the retained source runtime license, generic ARM64 loader link and explicitly supplied declared Python dependency archives in a deterministic second layer. The dependency archives were read from a never-started local source container, not from a serving system. It is **not** a cleanup layer on the original image.
4. `scripts/audit-runtime.py`: validates the OCI blobs and scans every archive path/link plus all regular-file bytes except opaque model/tensor/vocabulary payloads. This includes binaries and large text; matches are reported as categories/offsets/hashes, never matched values. No member paths are extracted and no image code runs during scanning. No pattern finding is automatically treated as publication permission.
5. `scripts/build-image.sh`: refuses an uncleared runtime receipt; any subsequent all-in-one build is a local, unqualified candidate. Text asset preparation remains separately required.

## Host proof and remaining gates

- The rebuilt ARM64 GLP reader test passes against the authentic vector under QEMU: 39 directions, layers 1–39, alpha 0.75, six malformed-file refusals and environment contract checked.
- Rebuilt ARM64 fold/reduction regression under QEMU: **0 reference differences**, 798,720 fold values / 156 dot rows, full 5120-column coverage; alpha-zero finite identity checked. No GPU ran.
- Rebuilt ARM64 sampler endpoint regression passes all **16,777,216 bins** under QEMU.
- New archive/privacy regression tests exercise allowlisting, history exclusion, latest-file behavior, whiteouts, traversal, links, binary scanning and opaque payload boundaries.

Final artifact audit/readback and smoke-test status are recorded in `publication-runtime.json`, `publication-audit.json` and the completion report. No public or GPU-serving claim may be inferred from a locally built OCI artifact.

The owner has cleared the candidate audit and approved its exact digest for publication; distribution now awaits the separate package visibility change and anonymous readback. Separately, review/reproduce the local toolchain, complete the runtime smoke and run full four-rank GPU acceptance before serving use. A separate all-in-one text-weight bundle would need its own build/audit. No full text-weight bundle was built in this task.

## Candidate audit outcome — cleared by the owner waiver above

Candidate: `ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4`.

- Manifest: `sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`.
- Config: `sha256:97cfdaafc7d1b5e7e0cd0e1b3b7a2cf787e8948586732089c9a24a334379e1df`.
- Two fresh layer descriptors; **4,581,714,457 compressed bytes**. Zero original layer digests are retained. The large core was scanned completely; the final audit reuses that result only after rehashing the identical core blob, then scans the supplement and final config.
- **11,907 archive members**, **9,384 non-payload regular files**, **6,335,716,288 bytes** scanned. The vision tensor pack and authentic vector are the two opaque payloads; both have locked, verified hashes.
- Final config: **0 pattern findings**. No private-domain, tailnet-domain or internal-routing match remains in the scanned bytes. The rebuilt engine has no operator-home path match.
- **42 third-party files / 173 screening matches were flagged**: 106 home-path references, 24 credential-location references, 24 token/key-marker-shaped references, 19 address-shaped references. Every path, offset, category, match hash, layer digest and adjudication is in `publication-audit.json`. Bounded context review resolves **31 files as benign code/data patterns** and initially retained **11 files for vendor-provenance review**. All 11 are now WAIVED by Ryan as recorded above; the candidate audit is cleared. Historical raw matches remain available.

Review of bounded, redacted context identifies public code examples, protocol/crypto format strings and library self-test material, base64 font/Unicode-name coincidences, official package SBOM paths, and third-party build provenance/assertion paths. These are **not evidence of working credentials or a current deployment address**. In particular, key markers in a crypto parser and credential filename strings in a client library are not credential files. Some vendor build paths include user-like components and have not been independently matched against publisher artifacts. These were not automatically waived by the scanner. Ryan subsequently waived the 11 vendor files explicitly; this is clearance by owner ruling, not zero raw pattern matches. The original production image is not covered by that ruling.

Isolated smoke tests found that the initial pruning omitted `torchgen`, then the importable `torch.testing` API. The final supplement retains the declared CUDA/Python dependencies plus the NumPy/SymPy/PyTorch testing APIs (not their test suites). The earlier r3 private candidate is retained as a failed packaging iteration, not a release; its tag was not overwritten. No serving deployment occurred. Full GPU/image/quality/performance gates still have not run on the rebuilt artifact.

Ryan has supplied explicit adjudication and exact-digest publication approval. A separate package boundary has now been created without exposing the original mirror. Serving use additionally needs separately authorized full four-rank qualification. The old digest remains blocked and unchanged.

### Exact vendor-provenance set waived by Ryan

These are not asserted to contain working credentials. They retain user-like source/build-directory strings whose publisher provenance has not been independently established. All are in the fresh core layer; none is an inherited operational layer.

| Layer digest | File | Disposition |
|---|---|---|
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/lib/aarch64-linux-gnu/libksba.so.8.14.6` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_adv.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_engines_precompiled.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_engines_runtime_compiled.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_graph.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_heuristic.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib/libcudnn_ops.so.9` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/nvidia/cusparselt/lib/libcusparseLt.so.0` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/torch/lib/libnvpl_lapack_core.so.0` | WAIVED |
| `sha256:98fb19dceb88f5e70ffb4a2ecd2c4befdcd3da2dd711b2189d9d8122b29ecf97` | `usr/local/lib/python3.12/dist-packages/torch/lib/libnvpl_lapack_lp64_gomp.so.0` | WAIVED |

## Historical private registry proof

Owner-authenticated GHCR GET by final tag and digest hashes to the candidate manifest above; config GET matches its digest, and all three referenced blobs pass digest/size HEAD checks. The owner API reports the package **private**, the tagged version exists, and the git repository is **private**. The original production tag still hashes to `sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`. Receipt: `publication-transfer.json`. This is not a claim of an independent full multi-gigabyte registry pull. No visibility API was called and no anonymous-public-readback success is claimed.

## Final bounded runtime smoke — INCOMPLETE

The final r4 container ran off-serving under ARM64 QEMU, with no GPU/network, read-only rootfs, all capabilities dropped, a four-CPU/eight-GiB bound and one numerical-library thread. NumPy, PIL and safetensors imported. **PyTorch import did not finish within the 660-second deadline**; the wrapper stopped the task container and it was automatically removed. The wrapper finished after 690.271 seconds including bounded shutdown. No `complete_no_gpu` marker was observed, and later imports were not reached. This is an **incomplete smoke, not a pass** and not proof of another missing dependency or an engine fault. It does not replace native ARM64/GPU qualification. The initial missing-loader/API errors were separately addressed, but the final complete runtime import remains unproven. See `publication-verification.json`.

Final local checks: **75 offline recipe tests passed**, three rebuilt ARM64 CPU regressions returned exit0, and scrub/static checks passed as recorded in `recipe-verification.json`. Mechanical profile checks match engine/frontend hashes; all 61 original confirmed operational-path occurrences are absent from the fresh core namespace. The candidate audit is now cleared by the owner waiver; this historical verification did not change visibility; current distribution status is in the completion report. No deployment or visibility change occurred.

## Separate distribution boundary — 2026-11-12

The approved digest was copied without modification to the separate `ghcr.io/ofan/deepseek-v41-flash-spark-public` package. This removes the shared-package design conflict. Visibility remains private because no authenticated owner web session is available; no public readback is claimed. The original package and predecessor remain private and untouched. See `public-release.json` and the completion report.
