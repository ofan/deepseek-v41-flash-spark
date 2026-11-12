# OCI layer-content publication audit — 2026-11-11

## Verdict: BLOCKED — keep the image package private

**The exact staged digest is not clean for publication. No visibility flip was performed.** The owner authorized publication only after zero forbidden findings in config and every layer. That condition fails. The git repository remains private, and no production or Spark system was accessed.

Image: `ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1`.
Manifest: `sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9`.
Config: `sha256:979ff212061ffe5d43ecd14e2c8a3d32d9cfceedf1b3e350008b7cdcf3226382`.

**Coverage:** all **72 layer descriptors / 68 unique layer blobs** were indexed. All blobs were SHA256-verified against an owner-authenticated GHCR manifest; authenticated config GET/hash verified the config. Digest-verified local mirror blobs were reused; missing blobs were fetched read-only from GHCR. Config traversal inspected **1084 fields/container nodes** and **199 history entries**. No container was started.

## Method and evidence boundaries

- Streamed each compressed layer with the tar reader; recorded archive member names, types, sizes and link metadata locally. No archive members were extracted onto the filesystem. No tensor, weight or tokenizer member was opened or interpreted; archive traversal necessarily passes their compressed bytes.
- Scanned UTF-8 configuration, launchers, scripts and other plausible small text up to **512 KiB per member**. A second pass covered extensionless/dotfile/build metadata in application and home/cache trees. Profiles and entrypoints were checked at every historical layer occurrence, not merely in the merged filesystem.
- Matching covers private-domain names, nonpublic/tailnet addresses, operator-home paths, credential-path patterns, credential/token shapes, secret assignments, email and proxy-internal references. Values are not reproduced: findings retain field/path/line, file hash and match hash. Archive paths below are exact relative member names; image-root leading slashes are omitted. Config field pointers are exact; sensitive field values are intentionally omitted.
- Machine-readable `layer-audit.json` preserves **every screening flag**, per-layer counts/index hashes, confirmed findings, unresolved candidates and excluded large-text file names/sizes. Full filename-only local indexes have recorded hashes; they are not copied wholesale into Git.
- **REVIEW is not clearance.** Upstream library code, public author/license contacts, documentation address examples and dummy credential fixtures can trigger matches; those are distinguished from confirmed deployment disclosures rather than being claimed as live credentials. Large text, binary contents and nested package archives were not generally inspected. This is a bounded publication-content audit, not a malware/CVE or exhaustive binary-secret scan.

## Config verdict: BLOCKED

| Surface | Result |
|---|---|
| Env (27 entries) | No live credential confirmed. `HF_REVISION` is stale baked-checkpoint provenance and must not be presented as the current stock revision. Other CUDA/toolchain/build URLs are public dependency metadata. |
| Labels | Inherited operational campaign/site/status/engine/checkpoint labels remain; several are stale. See exact field names in the JSON receipt. Public NVIDIA maintainer/license attribution is not treated as private operator data. |
| Entrypoint | `python3 /opt/pico/entrypoint.py`; launcher content findings are listed by layer below. |
| Cmd / exposed ports | Neither field is present. |
| User / working directory | User is explicitly `root`; not a credential disclosure. WorkingDir embeds an operator-specific trial home path: publication blocker. |
| History (199 entries) | Operator trial path retained at history indices **180 and 186**. Generic upstream application-user creation at index46 and upstream maintainer attribution at index10 are separate screening candidates, not claimed private credentials. |
| Remaining fields | Architecture/OS/creation time/rootfs identifiers and every remaining scalar/container were traversed; full field inventory and matching results are retained in the JSON receipt. |

No live credential/token value is confirmed by this audit. That is **not** a claim that opaque binaries, nested archives or excluded files contain no secrets. The proven domain/address/home-path findings already fail the authorization gate.

## Confirmed layer/file publication blockers

All rows below must be removed or replaced in a separately rebuilt publication candidate; later-layer deletion does not remove earlier bytes. Inherited vLLM/b12x scripts/evidence are not asserted to describe the current fleet. Their concrete operator/network literals and unnecessary operational payload are still not clean under the requested publication policy.

| # | Layer | Layer digest | Exact archive member | Finding / lines |
|---:|---:|---|---|---|
| 1 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/serve-ds4-flash-dspark-tp2-rdma.sh` | home-path, internal-or-tailnet-ip; lines 7, 9, 11, 12 |
| 2 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/serve-ds4-flash-dspark-tp4-rdma.sh` | home-path, internal-or-tailnet-ip; lines 7, 10, 12, 14, 15, 16, 17 |
| 3 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/serve-glm53-flash-nvfp4-tp2-rdma.sh` | home-path, internal-or-tailnet-ip; lines 8, 10, 13, 14 |
| 4 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/serve-glm53-nvfp4-tp4-rdma.sh` | home-path, internal-or-tailnet-ip; lines 8, 9, 11, 14, 15, 16, 17 |
| 5 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/serve-qwen38-flash-next-nvfp4-tp2-rdma.sh` | home-path, internal-or-tailnet-ip; lines 8, 9, 12, 13 |
| 6 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/scripts/spark-switch-network.md` | internal-or-tailnet-ip; lines 9, 10, 11, 12, 14, 15, 17, 18, 19, 22, 23, 65 |
| 7 | 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | `opt/spark-ds41f/candidate/vllm/serve-ds4-flash-spark.sh` | internal-or-tailnet-ip; lines 123, 125 |
| 8 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/measure.py` | home-path; lines 17 |
| 9 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/receipt.json` | home-path; lines 9, 10, 11, 12, 36, 38, 40, 88, 90, 92, 130, 132, 136, 142, 149, 155, 195, 197, 207, 214, 220, 260, 262, 272, 279, 285, 321, 323, 333, 340, 346, 398 |
| 10 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp2_candidate.jsonl` | home-path; lines 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 |
| 11 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp2_candidate_profile.json` | home-path; lines 7, 12 |
| 12 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_candidate.jsonl` | home-path; lines 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 |
| 13 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_candidate_profile.json` | home-path; lines 7, 12, 17, 22 |
| 14 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_control.jsonl` | home-path; lines 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 |
| 15 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_control_profile.json` | home-path; lines 7, 12, 17, 22 |
| 16 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_initial_partial.jsonl` | home-path; lines 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| 17 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/benchmarks/evidence/qsa_stable_selection/tp4_initial_partial_profile.json` | home-path; lines 7, 12, 17, 22 |
| 18 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/docs/evidence/kda_prefill/README.md` | home-path; lines 11 |
| 19 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/docs/evidence/nvfp4_split/20260910-rtxpro6000-maxq-production-graphs.json` | home-path; lines 6, 21, 22, 23, 24 |
| 20 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/docs/evidence/nvfp4_split/README.md` | home-path; lines 5, 7, 8, 18, 19 |
| 21 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/docs/evidence/rocenante/20260902-4spark-bf16-standalone.json` | internal-or-tailnet-ip; lines 8 |
| 22 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/docs/evidence/rocenante/20260903-4spark-bf16-standalone-00280f2.json` | internal-or-tailnet-ip; lines 8 |
| 23 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/csf/beta-integration.md` | internal-or-tailnet-ip; lines 58 |
| 24 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/acceptance_revision.json` | home-path; lines 8 |
| 25 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/basic_functionality.json` | home-path; lines 4 |
| 26 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/ced_prefill.json` | home-path; lines 17, 102, 107, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198 |
| 27 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/commands.json` | home-path; lines 3, 30, 49, 68, 72, 73, 76, 78, 81, 86, 89, 91, 93, 96, 109, 110, 113, 115, 117, 140, 141, 144, 146, 149, 154, 157, 159, 161, 164, 165, 168, 170, 174, 177, 178, 181, 183, 185, 190, 213, 233 |
| 28 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/gpu_contention.json` | home-path; lines 13 |
| 29 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/kernel_pass_01.json` | home-path; lines 94, 101, 107 |
| 30 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/native_execution.json` | home-path; lines 79, 84, 91, 98, 105, 112, 119, 126, 133 |
| 31 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/native_kv_allocation_fix.json` | home-path; lines 146, 147, 153, 160, 167, 175, 177, 193, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253 |
| 32 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/numerical_promotion_audit.json` | home-path; lines 67 |
| 33 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/package_verification.json` | home-path; lines 29, 36 |
| 34 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/performance_summary.json` | home-path; lines 231 |
| 35 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/ple_comparison.json` | home-path; lines 60 |
| 36 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/profile_optimization.json` | home-path; lines 10, 11, 88, 93, 173, 174, 175, 392, 401, 594, 603, 606, 611, 969, 978, 981, 986, 1207, 1216, 1219, 1224, 1394, 1395, 1412, 1415, 1420 |
| 37 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/qualification.json` | home-path; lines 23, 25, 30, 32, 69, 114, 127, 128, 137, 145, 150, 155, 160, 165, 170 |
| 38 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/ram_engram.json` | home-path; lines 6, 7, 11, 53, 268, 269, 270, 271, 272, 273, 274 |
| 39 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/reference_results.json` | home-path; lines 4, 6 |
| 40 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/source_manifest.json` | home-path; lines 5, 6 |
| 41 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/startup_workspace_fix.json` | home-path; lines 4, 29, 30, 46, 47, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 70 |
| 42 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/structural_optimization.json` | home-path; lines 6, 7, 385, 386, 391, 396, 402, 407, 413, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 516, 517, 518 |
| 43 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/tp4_ssd_latency.json` | home-path; lines 328, 329 |
| 44 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/tp4_ssd_native_execution.json` | home-path; lines 150, 210, 270, 330 |
| 45 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/deepseek_v41/tp4_ssd_progress.json` | home-path; lines 73 |
| 46 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/deepseek_wo_layout/results.json` | internal-or-tailnet-ip; lines 250, 288, 326, 364, 402, 440, 478, 516, 554, 592, 1309, 1347, 1385, 1423, 1461, 1499, 1537, 1575, 1613, 1651 |
| 47 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/deepseek_wo_packed_a/projection-traces.json` | internal-or-tailnet-ip; lines 1818, 1871, 1924, 1977, 2030, 3882, 3935, 3988, 4041, 4094, 5948, 6011, 6074, 6137, 6200 |
| 48 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/deepseek_wo_packed_a/results.json` | internal-or-tailnet-ip; lines 253, 291, 329, 367, 405, 443, 481, 519, 557, 595, 1315, 1353, 1391, 1429, 1467, 1505, 1543, 1581, 1619, 1657 |
| 49 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/moe_overlap_tuning/results.json` | internal-or-tailnet-ip; lines 253, 291, 329, 367, 405, 443, 481, 519, 557, 595, 1318, 1356, 1394, 1432, 1470, 1508, 1546, 1584, 1622, 1660 |
| 50 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/qwen_mxfp8_capacity/README.md` | internal-or-tailnet-ip; lines 102, 110 |
| 51 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/qwen_mxfp8_capacity/results.json` | internal-or-tailnet-ip; lines 252, 290, 328, 366, 404, 442, 480, 518, 556, 594, 1290, 1328, 1366, 1404, 1442, 1480, 1518, 1556, 1594, 1632, 2328, 2366, 2404, 2442, 2480, 2518, 2556, 2594, 2632, 2670 |
| 52 | 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | `opt/spark-ds41f/candidate/b12x/validation/serving/w4a8_resident_grid/results.json` | internal-or-tailnet-ip; lines 250, 288, 326, 364, 402, 440, 478, 516, 554, 592, 1312, 1350, 1388, 1426, 1464, 1502, 1540, 1578, 1616, 1654 |
| 53 | 60 | `sha256:f0d7f495588972696e6deb7b96ffc78965a3fe65f05744a5383726a578c92f2d` | `opt/pico/entrypoint.py` | internal-or-tailnet-ip; lines 28 |
| 54 | 60 | `sha256:f0d7f495588972696e6deb7b96ffc78965a3fe65f05744a5383726a578c92f2d` | `opt/pico/profile.json` | home-path, internal-domain; lines 7, 8, 70 |
| 55 | 61 | `sha256:18450e24dd36d46e258e989d95061ac24047868062c536a099a32b0cb24d53c9` | `home/ofan` | operator-home-directory; lines directory header |
| 56 | 61 | `sha256:18450e24dd36d46e258e989d95061ac24047868062c536a099a32b0cb24d53c9` | `home/ofan/pico-dsgx10-trial-20261105` | operator-home-directory; lines directory header |
| 57 | 63 | `sha256:b1b7e7ee31b16228faeb5c7bd7ecd2ae0aa650dac8972331fbb55db7b7065400` | `opt/pico/profile.json` | home-path, internal-domain; lines 7, 8, 70 |
| 58 | 66 | `sha256:bf673d8084247ce84b8203992eec7eaf2d90e20a68df71e388e3d8e42486904b` | `opt/pico/profile.json` | home-path, internal-domain; lines 7, 8, 90, 91 |
| 59 | 68 | `sha256:1d19b88f3ec74f3e71a5b5fec74130aabfecd36ef7e7df31728b584d01b4c203` | `opt/pico/profile.json` | home-path, internal-domain; lines 7, 8, 90, 91 |
| 60 | 69 | `sha256:2fc1ea083420922dbdbfd13f28ea20ffeff32389216c0fca72d4f765df206ce4` | `opt/pico/entrypoint.py` | internal-or-tailnet-ip; lines 29 |
| 61 | 70 | `sha256:29205c64c9f3507ec497b01f546cd3005f99c933922aef13ec6fa23e21447151` | `opt/pico/profile.json` | home-path, internal-domain; lines 7, 8, 90, 91 |

### Profile fields and what survives in the final filesystem

- **Layers60 and63:** `opt/pico/profile.json` fields `stock_checkpoint`, `trial_directory`, `image` (lines7,8,70). The image field contains an internal registry hostname.
- **Layers66,68,70:** same path, fields `stock_checkpoint`, `trial_directory`, `rollback.image`, `rollback.checkpoint` (lines7,8,90,91). `rollback.evidence` also points into the operational evidence tree (line92).
- **Layers60 and69:** `opt/pico/entrypoint.py` has a hard-coded private-network frontend listen address at lines28 and29 respectively. Public wildcard binding and loopback encoder binding are not classified as private-network leaks.
- **Layer61:** two operator-home trial directory headers remain.
- No subsequent layer replaces the profile after layer70, and no subsequent entrypoint replacement removes the layer69 address (layer72 changes other code). These are **current merged-filesystem leaks as well as historical-layer leaks**.
- There are no packaged operator SSH/cloud credential files confirmed. An empty root SSH directory, credential-named Python modules, generic authentication API variables, public license emails and dummy/test key markers are **screening candidates**, not proof of working secrets. All candidates remain visible in the JSON receipt; REVIEW rows are not silently cleared.

## Per-layer verdict

NO_FINDING_IN_SCOPE means no match within the bounded method, not general security clearance. REVIEW means a pattern/path/size-bound candidate remains; BLOCKED means an individually identified publication blocker above. Duplicate layer descriptors reference the same indexed bytes.

| # | Digest | Members | Primary text files | Supplement text files | Verdict |
|---:|---|---:|---:|---:|---|
| 1 | `sha256:752e689d935166fd0ae29b6775e31873ff882f7aefe8b0dde2eaad65c352bbfa` | 3440 | 240 | 5 | REVIEW |
| 2 | `sha256:933a394735d306a327b0f43198651b2beea2e35f4252ca836f938ff7213a8831` | 799 | 32 | 0 | REVIEW |
| 3 | `sha256:2fe1bd723675049a1f5c52ea338ce521041685f0a9be654144096643d8cb07b8` | 94 | 7 | 0 | NO_FINDING_IN_SCOPE |
| 4 | `sha256:c19f63f75df4d7fb51a310436b2772c04280c2748a88798925034b57235b4376` | 3 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 5 | `sha256:8897307e3a1e092f291d7c7b66c5a1a1e3f3a2918d41bd4043882ed44aa988a2` | 1 | 1 | 0 | REVIEW |
| 6 | `sha256:5814fbc68c3d4f237baf21fefd9b6e3afcdd3642d4be14f3fe307184e29c0769` | 1 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 7 | `sha256:9fd8b15f808c9a10d3e7a48dcfa7f7b7f694ffdca45831d4001a6060d6709b7a` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 8 | `sha256:e8ec7b8ca0e8354bb12c2b34586e50a09c3811b7b617a6993c90d30193dd9d6f` | 13371 | 3162 | 4 | REVIEW |
| 9 | `sha256:a9a98605605944ad2667c0e309fa656f794db8b50df62c6a1f8c6907b57608dd` | 6911 | 103 | 0 | REVIEW |
| 10 | `sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1` | 0 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 11 | `sha256:afc7de054f80ab9f86db3c00eff3b4a729a0749968b5b156c57d3930554d25f9` | 56 | 3 | 2 | REVIEW |
| 12 | `sha256:586d73e6d46732224b056fa85bb16ff8f88af98079b13ce4e67ac15212dd0a44` | 4 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 13 | `sha256:bdbf38d915092dd9cd03648ef15dc61f4504cc7cb681e44969e29994a7f2c50f` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 14 | `sha256:56d48059aa7f59e08ac4ea37baf1dec8dbd3747e7285141ffbea5a3c559a2aee` | 19 | 12 | 3 | REVIEW |
| 15 | `sha256:4b817686e30621d224f0a5f1a9c8af5a370bf230f9fdda13459effaa546c6e1e` | 4 | 1 | 0 | REVIEW |
| 16 | `sha256:4b817686e30621d224f0a5f1a9c8af5a370bf230f9fdda13459effaa546c6e1e` | 4 | 1 | 0 | REVIEW; duplicate of 15 |
| 17 | `sha256:00b6238efac7fed5135f8e95b6732d8b401091849cf5567409b458a1ac2c8bb0` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 18 | `sha256:0ab851bc6aa866eeea801d8f9e637b0fe9100ea3219693831746cce7e040b31a` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 19 | `sha256:34b91c34795d746ab45f3cbb3f4fb25932d0b010f823568ea8b553cd8ff66d16` | 138258 | 21046 | 1 | REVIEW |
| 20 | `sha256:26f21ec9a6012bb8bc5911b4ee02504d91126b5254eca2767579cf54621ce830` | 1832 | 3 | 0 | NO_FINDING_IN_SCOPE |
| 21 | `sha256:dfa9eb74e8321429193884cc27dce353c0b50111614e911641bef9badefc5296` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 22 | `sha256:1a165c07d4aaf7bad5a73b1bd707d7d860caca5c2497d994df54bb98b9e23b94` | 54 | 2 | 0 | NO_FINDING_IN_SCOPE |
| 23 | `sha256:7e5fa8ec4663ceee8f6906e92f663d0551005bcc1961f171f6be0172b81bd3fb` | 8345 | 5240 | 0 | REVIEW |
| 24 | `sha256:87f518048f7b447cfb28df5e5f5e68dbab68c3a30255794e6388978306f1e9f5` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 25 | `sha256:d03a2befe5bafaf1dd40bb49a33496e5795dccb4adba85bd2a2da4947c59b206` | 2 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 26 | `sha256:b1e9f342078b69488dde00bc06477dc856c94ffac53a245fb9c662c887a4b35c` | 5645 | 3287 | 1 | REVIEW |
| 27 | `sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1` | 0 | 0 | 0 | NO_FINDING_IN_SCOPE; duplicate of 10 |
| 28 | `sha256:479eed21c7386b26786c44620ec9084349354116e6fb30b011a3cd79d2843639` | 2 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 29 | `sha256:63fdd9c1aa614acbd9727dc2b8d95a3dd0cb2affd65d6dc4346f42f147ea0136` | 61 | 19 | 0 | NO_FINDING_IN_SCOPE |
| 30 | `sha256:c91841bb6cc73ebb12a917b6cf98a6befbfceffc3c6b942850bb7bd60b56088a` | 334 | 215 | 0 | REVIEW |
| 31 | `sha256:848f8e0b44ff98c7d93d21c76a1014e382bc3f15f1295f754ea4c2e64ebeb9ed` | 153 | 138 | 0 | REVIEW |
| 32 | `sha256:cb9f7b59991bd210621bfda9c80713f494243a0b5c78372feed940b2d54245cc` | 2 | 1 | 0 | REVIEW |
| 33 | `sha256:c1b560f902d50cfbf45013317be94b45604b9b286f2e62e28841348ec1525052` | 8154 | 2748 | 0 | REVIEW |
| 34 | `sha256:8cb64f32e012bd82433ae52712a41eb8484e3f59a5715f8abc99541508c3e178` | 1 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 35 | `sha256:74f06ebca97c21b34a9ca367a115388d1f78311ff4b05e4aaefe70b543b0bee4` | 2 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 36 | `sha256:c213be1c43352faf845570a9b78eadc3295ab4388e808904a0c198a012191940` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 37 | `sha256:0b0e1fb3584df51c2aee6ba457e150ef38c45cd15d2f764585a6e2bf35bc3196` | 3 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 38 | `sha256:deb18564216813d0ba30a7eaa1a23f6ffb0c95f27383b397478b56b8484f35e9` | 8719 | 6851 | 7644 | BLOCKED |
| 39 | `sha256:417339a4c8e1cb57059455edf555e3a7b76b9c313dcbed79a789ad8c6da103a9` | 1508 | 1328 | 1355 | BLOCKED |
| 40 | `sha256:1f17e6bc6b7d2000cb16d17772a9e12590d565c3ad3658a89b5392d5a36c5f59` | 6 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 41 | `sha256:299e24ecda1f1d6ea2c6404bfb8821d830ad7f9648f2e48e4fb0b1d7d38cdbfd` | 6 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 42 | `sha256:b55656e8de2d5a9e1e543b072536a2a54a8a63d417c8ec64b27787b23f2f7cdb` | 7 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 43 | `sha256:de000329441e7bd23c99a7adcd9037fa87dd31463fc4552c33385218be635016` | 5 | 0 | 1 | NO_FINDING_IN_SCOPE |
| 44 | `sha256:f3220070b442f005cb57362f620b7aa403479f3ee723aa861c7b310a83758d82` | 13 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 45 | `sha256:d7ce1a90f4c765749f894650f1350a4c5c9a0828889c88e8c53974858daa78c3` | 103 | 8 | 0 | NO_FINDING_IN_SCOPE |
| 46 | `sha256:3725bc3a6708a8e8861b28169ba201bd2e3e1e4ac4ed26d20095bd64249cf3a2` | 2 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 47 | `sha256:567353710001d103f0eb781792b877bdf8a2f0966fe3cb791493c899d8dee2f3` | 5394 | 208 | 1975 | REVIEW |
| 48 | `sha256:87c1968b47e7e04d60d3bae182bb3c875515f0f883161b0af1f84f0e088d6a14` | 2791 | 1322 | 538 | REVIEW |
| 49 | `sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1` | 0 | 0 | 0 | NO_FINDING_IN_SCOPE; duplicate of 10 |
| 50 | `sha256:0582c2b9ee640420c207518a4bd923e8a83be56e934f575cefdcad22646f3d6d` | 3780 | 0 | 0 | REVIEW |
| 51 | `sha256:622c9bd573eecc7619983a4c7bc9b5be63dcaadd087145b0c8f6ccb55bc89d57` | 5891 | 1314 | 0 | REVIEW |
| 52 | `sha256:c93016be5758e16111e76b04d6b6fb0275c5a1e61775f00d853f1be08dbe0ad8` | 1 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 53 | `sha256:a53d35c866790f3e77ade7525abba3b6e2a0ce8b86504242be543f0aca4b9eea` | 125 | 47 | 0 | REVIEW |
| 54 | `sha256:f4f89b596971df8fe917f3cfb2e112951b6c261e8ec254ad532dbc5be0b579a3` | 5 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 55 | `sha256:78e23c2e91dd353a9d5247142becd5d118a1aa0df0a9147a9399d3b8441ee486` | 127 | 47 | 0 | REVIEW |
| 56 | `sha256:d77e0caf4819bb023f621461932e29cf5d8ccc2bcff3a13e22a6a52f03a18b6a` | 5 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 57 | `sha256:aa8ef2a3446b6ac43eb8d97f2e39a5f1fb06e9b806187c8f6d3d66562d6f017d` | 1 | 0 | 0 | NO_FINDING_IN_SCOPE |
| 58 | `sha256:8990be26ae46d5b8147a7371ff1389d4d1608c22e5d7349385882426427ae08a` | 10 | 1 | 0 | NO_FINDING_IN_SCOPE |
| 59 | `sha256:aa820736e977321cb611b479f0529609b3757f1932c6c1269ca685ee4f4b4df7` | 4 | 0 | 0 | REVIEW |
| 60 | `sha256:f0d7f495588972696e6deb7b96ffc78965a3fe65f05744a5383726a578c92f2d` | 5 | 3 | 3 | BLOCKED |
| 61 | `sha256:18450e24dd36d46e258e989d95061ac24047868062c536a099a32b0cb24d53c9` | 3 | 0 | 0 | BLOCKED |
| 62 | `sha256:05c3c728a54ed9e5a99b9dc5646b1ad5973d69a03f9060ef2904103964a5ce7a` | 3 | 0 | 0 | REVIEW |
| 63 | `sha256:b1b7e7ee31b16228faeb5c7bd7ecd2ae0aa650dac8972331fbb55db7b7065400` | 3 | 1 | 1 | BLOCKED |
| 64 | `sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1` | 0 | 0 | 0 | NO_FINDING_IN_SCOPE; duplicate of 10 |
| 65 | `sha256:44ce64f8f30c937df3feb9db7f742abbd8f43b1881c906c13daa4b3817231415` | 3 | 0 | 0 | REVIEW |
| 66 | `sha256:bf673d8084247ce84b8203992eec7eaf2d90e20a68df71e388e3d8e42486904b` | 3 | 1 | 1 | BLOCKED |
| 67 | `sha256:9b41be06408125fa997b38d224569ac6cc1718370870f47a5348c38702437b34` | 3 | 0 | 0 | REVIEW |
| 68 | `sha256:1d19b88f3ec74f3e71a5b5fec74130aabfecd36ef7e7df31728b584d01b4c203` | 3 | 1 | 1 | BLOCKED |
| 69 | `sha256:2fc1ea083420922dbdbfd13f28ea20ffeff32389216c0fca72d4f765df206ce4` | 5 | 1 | 1 | BLOCKED |
| 70 | `sha256:29205c64c9f3507ec497b01f546cd3005f99c933922aef13ec6fa23e21447151` | 3 | 1 | 1 | BLOCKED |
| 71 | `sha256:d71466cd7b1ce6df92880be8ef50d7bb5227e770b0675adeed284872470d54ce` | 13 | 5 | 5 | REVIEW |
| 72 | `sha256:5627c9073e8208f5e54983e2fc98ecfd8c3ae855e0f135221f79903716c08fd9` | 5 | 2 | 2 | NO_FINDING_IN_SCOPE |

## Publication decision and next safe step

**No flip. No anonymous-public-readback success is claimed.** The package and git repository are owner-authenticated PRIVATE at audit close. Only read-only registry/API calls were used. The production digest is unchanged.

An unchanged manifest digest cannot be sanitized: config and every historical layer are content-addressed. Build a **new public-distribution artifact** from a clean runtime base, copy only the required engine/frontend/vision/runtime assets, supply a generic profile/launcher without embedded site paths or network addresses, discard inherited operational source/evidence/caches, and replace stale labels/history. Do not rely on an upper-layer whiteout or overwrite. Preserve notices and complete separate dependency/license review. Then audit **the new digest** and obtain publication authorization applicable to that candidate. No rebuild or deployment was performed here.

## Verification

See `layer-audit.json` for coverage/match receipts and `recipe-verification.json` for offline recipe tests and scrub. The audit files intentionally contain no secret values, internal domain/address literals, or raw generation/tokenizer/tensor data.
