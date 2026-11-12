# Optional DGX Spark host preparation

**Optional guidance, not an installer.** This repository does not configure hosts. Apply site-specific tuning only after reviewing vendor documentation and arranging a recovery window. Do not execute these examples on a serving machine merely to follow this README.

## Hardware and OS baseline

Target four GB10 systems with 128 GB unified memory each, ARM64 Linux and local NVMe, joined by a qualified ConnectX-7 RoCE fabric. Host documentation records NVIDIA DGX OS / Ubuntu 24.04.4 LTS, aarch64. The later fleet qualification records **kernel 7.0.0-1019-nvidia-64k**, **65,536-byte pages**, **driver 580.178.04** and CX-7 firmware **28.45.4028**. Those are historical compatibility facts, not an instruction to downgrade or cross-flash another vendor's firmware. Validate the exact kernel, driver, RDMA devices and page size as a set.

Build requirements from the pinned Pico serving documentation: CUDA **13.0**, CMake **3.28+**, g++ **13.3 / C++20**, rdma-core / libibverbs development libraries, Python **3.12**, and a locked Rust toolchain (documented Cargo **1.97**). All builds should run on an appropriate **off-serving build host**. This package does not install compilers on serving nodes.

## Optional GPU clock cap

The recorded fleet uses a **2,200 MHz maximum graphics clock**, command shape:

```sh
# Administrative example, NOT run by any script in this recipe:
sudo nvidia-smi -lgc 0,2200
```

A single persistent policy owns the cap; do not stack competing clock controllers. The report sampled roughly 2,190 MHz while the advertised maximum remained higher. Monitor thermals/power and re-qualify throughput after changing clock policy; a cap is not a guarantee of constant frequency.

## Optional TCP / management NIC tuning

The documented management-NIC mitigation persisted `net.ipv4.tcp_sack=0` and disabled EEE on the matching management NIC. It was **not proven to eliminate receive misses**. Do not copy this exception onto every network without diagnosing the NIC; disabling SACK can hurt ordinary TCP workloads. The later optional baseline persisted `net.mptcp.enabled=0` and retained `net.ipv4.tcp_migrate_req=0`.

No TCP buffer-size values are published here: the allowed report-only evidence does not establish a particular buffer tuning requirement for Pico. Preserve local management reachability, firewalling and recovery access; do not flush system network rules or change MTU on the management interface as a side effect.

## RoCE / fabric tuning

The accepted topology is a **direct four-node ring**, not a switched NCCL deployment. The recorded physical fabric interfaces were UP with **MTU 9000**; `arp_ignore / arp_announce / rp_filter` were **1 / 2 / 2**. Validate those controls' interface scopes for your own addressing plan rather than applying blanket global sysctls.

Pico uses **native verbs**, not NCCL environment settings, for production collectives. Select the real RDMA devices and the **RoCEv2 GID index that matches your own link addresses**; do not copy a numeric GID from a different host. Populate all NEXT/PREV links consistently in your fleet file. Do not transpose switch-specific QoS/ECN settings onto a switchless ring.

Before model launch, verify neighbor connectivity, jumbo MTU end to end, all HCA ports ACTIVE, stable link/error counters and Pico's own ring/collective correctness check. These checks are necessary but not a replacement for model acceptance.

## Native vision operating profile

The reference production vision build uses the stock checkpoint's own tower on rank0 and broadcasts image spans to all four ranks. Reserve additional rank0 encoder/activation memory; **0.904 GiB** is only BF16 weight payload, not the peak memory budget. Keep the canonical attention path (`VISION_SDPA_OPT_IN=0`) and serialized image encoder. Six-fixture QA passed **88/88 OFF and 88/88 GLP-39** on the qualified production image; this is not a claim that any new all-in-one layout is qualified.

## Storage / operating profile

Retain per-rank model and Engram assets, **160 GiB** writable saved-session spill and the **32 GiB** free-space guard. Spill is for saved-session snapshots, not a reduction of active KV capacity. An image carrying all four ranks will have a very different disk footprint from the production runtime/vision image with external text assets. Measure actual storage before any future deployment.

## Provenance (generic facts only)

Homeinfra branch `glp/pico-glp-steer-20261106`:

- `hosts/spark1/README.md` and `hosts/spark3/README.md`: GB10, memory and Ubuntu/DGX OS baseline. Their old service descriptions are not used as serving authority.
- `docs/operations/evidence/spark-al-engr-20261106/result.md` and `before-diff.md`: qualified kernel/pages/driver, clock policy, optional TCP controls, MTU and native-verbs ring.
- `docs/operations/owen-4k-campaign-20261026.md`, Bounded management-NIC change: SACK/EEE mitigation and its limitations.
- `docs/operations/evidence/pico-session-cache-fix-20261106/README.md`: spill and free-space guard.
- Pinned engine `ds41f-4xgx10-switchless/README.md`: compiler/runtime prerequisites and fleet-file keys.

These documents describe the declarative fleet configuration without publishing fleet addresses, device identities, access instructions or credentials. No host was inspected or changed to finish this recipe.

Current-serving authority: homeinfra `cf6e8b67c`, `docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`. The older host facts above remain historical compatibility evidence, not a fresh host audit.


## Fleet file

The engine at the pinned source revision reads strict `KEY=value` lines and `#`
comments; no quoted values or spaces. Unknown/repeated keys are refused. Use
`examples/fleet.conf.example` as an intentionally incomplete template: replace every
`REPLACE_...` value with your own devices, GID and link addresses before launching.
It is not a ready-to-run network configuration. No site addresses are shipped.

- `NEXT_DEV0/1`, `PREV_DEV0/1`: local HCA ports on the two PCI domains, with NEXT
  connected to the next rank and PREV to the previous rank; same device names across
  the four nodes are assumed by this schema.
- `GID_INDEX`: RoCEv2 index matching those physical link addresses on every device.
- `RANKr_NEXT_IP0/1`, `RANKr_PREV_IP0/1`: each rank's own link addresses. The initial
  TCP ring handshake uses PREV_IP0 and port18620; permit only ring peers.
- `RANKr_HOSTNAME`, `RANKr_NAME`, `RANKr_SSH`: local names/log labels and source-script
  SSH destinations. The recipe container launcher explicitly supplies rank and does
  not start remote hosts over SSH.
- `RANKr_WEIGHTS/HASHMAP/ENGRAM/SPILL`: container-visible asset and spill locations;
  launcher flags override these with the README's fixed model/spill paths.
- `BIN_DIR/LOG_DIR/SERVICE_DIR/RING_LOCK`: paths used by native helper scripts.

Validate cabling, links, device registration and the pinned engine's `ring_test` on
an idle ring before loading the model. On the recorded kernel, `kho=off` was needed
for RDMA memory registration; confirm with your vendor/kernel rather than copying
boot changes blindly. Never run the upstream example's host-specific fleet unchanged.
The public runtime is not GPU-qualified; benchmark results in [benchmarks](benchmarks.md)
refer to the qualified predecessor, not your hardware or this rebuilt candidate.
