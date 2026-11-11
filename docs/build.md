# Build recipe and provenance map

## Scope and honest reproducibility boundary

Pinned engine: `ofan/pico-dgx-ds4` at **`d04020cc1193364e042314a2ad8e0b8e6bccc46e`**. Pinned production frontend source: **`5559a1a611cf25af27e509d179c62bdc7b4f31fd`** from the same fork. Source subdirectory: `ds41f-4xgx10-switchless`. Keep all GLP, serving/cache, DSML and sampler fixes; do not substitute one standalone contribution branch for the production lineage.

Model: `deepseek-ai/DeepSeek-V4.1-Flash-1017` at **`1bae0e1088993b9b82de08f59de5be5a34e42170`**. Conversion changes storage layout, **not quantization or tensor values**. The public default is GLP OFF; optional GLP-39 is checked independently.

The Dockerfile packages verified inputs into a **new all-in-one candidate**. It does not recreate the historical OCI digest: that image used inherited runtime layers and separately supplied model assets. Nor is an arbitrary clean compilation promised to reproduce the qualified production binary: the original release used a hash-guarded relink with preserved native r5 inputs. A release must close the gaps below, not label a successful compile as exact reproduction.

## Sequence (commands supplied, not executed in this scaffold turn)

### 1. Fetch pinned code only

```sh
bash scripts/fetch-sources.sh
```

This obtains separate read-only-by-convention engine/frontend source checkouts under ignored `work/source/`; existing destinations are refused. No weights, vectors or images are fetched.

### 2. Compile on an off-serving ARM64 CUDA build machine

```sh
bash scripts/build-engine.sh
```

This mirrors the pinned engine's CMake + locked Cargo commands, producing a **source-build candidate** in `work/compiled/`. Production byte identity is a separate step. The production engine binary SHA256 is `644b40acac23cc7d0455723eff5370ecb88d9d30f9b5ab2c1d82b3a773dfebe9`; frontend SHA256 is `530d6c2512eeccbe50d7826ede5b2a1c93428998c273112a7eaa20a656173eb4`. `prepare-bundle.py` refuses any other binaries. Do not bypass that check to make a fresh compilation appear qualified.

For the historical cross-build, use the qualified aarch64 cross toolchain, preserve the 13 native r5 linker inputs, verify their committed hash manifest, reconstruct r5's control binary **first**, then link only the updated model archive. The baseline control must match `6eb1b00cd14a5f280b021d230047aeed5be04cf61d1fa142d1244b91c8145c85`. Those native inputs/toolchain are **not shipped in this scaffold**; therefore the exact cross-relink is a named release gap rather than a fabricated runnable command.

### 3. Obtain the official checkpoint separately

Use the Hugging Face client against the exact locked model/revision into `work/checkpoint`, with your own authorized access where needed. Do not use the uncensored community checkpoint, a moving main revision, the retired sparse conversion staging format or a tokenizer from another model. The input snapshot must include all tensors needed to materialize the Engram tables.

**No download command runs automatically. No weights were downloaded to prepare this repository.** The converter's revision option is an assertion of acquisition provenance, not a cryptographic substitute for pinning and verifying the downloaded snapshot.

### 4. Convert all ranks and materialize Engram

First inspect the plan (default; no tensor I/O or GPU execution):

```sh
python3 scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
# Only on an appropriate off-serving conversion host, add --execute.
```

The executable sequence mirrors the pinned engine documentation:

- `dsw_convert --ckpt CHECKPOINT --rank R --out rankR.dsw`, for ranks 0–3.
- `dsw_verify --ckpt CHECKPOINT --file rankR.dsw --threads 4`, every rank. Require every byte verified, zero bad tensors, not just a successful load or CRC.
- `engram_pack CHECKPOINT OUTPUT R`, two shards for each rank.
- `make_hashmap_stdlib.py CHECKPOINT OUTPUT/engram_hashmap.bin`, shared map.
- Preserve the matching config/tokenizer metadata; record hashes and converter logs. The script never prints or includes tokenizer contents in documentation.

The original rollout reused already-materialized Engram data and eventually removed the full source snapshot. A new standalone package must materialize those tables from the full pinned checkpoint or obtain independently verified equivalents. Whole-file DSW hashes vary with the converter's creation timestamp; the tensor-byte verifier, not an expectation of identical creation headers, establishes conversion equivalence.

### 5. Stage qualified binaries, notices and optional vector

Expected ignored build context:

```text
bundle/
  bin/dsgb10_rank
  bin/dsfront
  notices/engine-NOTICE
  model/config.json
  model/tokenizer.json
  model/rank0.dsw ... rank3.dsw
  model/engram-l1-r0of4.bin ... engram-l1-r3of4.bin
  model/engram-l14-r0of4.bin ... engram-l14-r3of4.bin
  model/engram_hashmap.bin
  model/asset-hashes.json
  vectors/glp39.gguf                  # optional
```

Supply the authentic upstream NOTICE and retain dependency notices. Obtain the optional vector from [msuiche](steering.md), verify its tested SHA256 and honor any access terms. No synthetic direction or automatic fallback is acceptable.

```sh
python3 scripts/prepare-bundle.py
```

The validator requires the **qualified production binary hashes**, all four rank files, all eight Engram shards, matching metadata/receipt hashes, engine notice, and the authentic vector hash if present. It generates `bundle/profile.json` only after validation. Asset receipts bind outputs to their conversion run; independent checkpoint acquisition proof and review of the verifier logs remain release requirements.

### 6. Assemble one immutable candidate, locally

Choose a licensed **public ARM64 CUDA 13 / RDMA runtime**, with all the qualified binaries' shared dependencies, pinned by digest. No default is invented for this unresolved runtime dependency.

```sh
RUNTIME_BASE=PUBLIC_RUNTIME_IMAGE_AT_DIGEST bash scripts/build-image.sh
```

The script builds a local `ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-sampler-open-unit-r1-bundle-candidate`; it **never pushes**. Extract the resulting profile and binaries and prove their hashes match before a future serving trial. Verify ELF architecture, dynamic library closure, CUDA compatibility, authentic notices and SBOM. Keep all four rank assets in this same image; select the rank at runtime.

## Mapping to homeinfra

Source reference: `glp/pico-glp-steer-20261106` at `f2a0a4dbea07ac9bf94bb24d8605da8f43a9a099`.

| Public build step | Homeinfra counterpart | Boundary |
|---|---|---|
| Pin full production engine/frontend | `config/pico-production/profile.json`; `pico-token-corruption-20261108/README.md` | Full production lineage, not standalone PR branches |
| Preserve r5 server/cache fixes; add GLP arithmetic | `config/pico-glp-steer/{source-contract.json,restore-r5-base.patch,glp-on-r5.patch}` | Use committed fork source instead of applying local patch files |
| Compile updated model / sampler | `pico-glp-steer-20261106/build/`; `pico-token-corruption-20261108/build-models.sh` | Generic native source-build commands supplied; exact cross builder missing |
| Hash-check 13 native inputs, reproduce r5, relink | `config/pico-glp-steer/relink-preserving-r5.sh`; `pico-session-cache-fix-20261106/native-input-sha256.json` | Recorded control/relink procedure, qualified inputs not redistributed |
| Convert official stock; verify all tensors | `pico-glp-promotion-20261107/README.md`; `pico-glp-r4-window-20261106/README.md` | Same converter/verifier, full pinned checkpoint rather than retired sparse staging |
| Produce Engram tables / map | Inherited assets described in promotion README; pinned engine README steps 4–5 | New package materializes the previously external tables |
| Include optional authentic GLP-39 | `pico-glp-upstream-prepare-20261107/README.md` | Exact tested full-file SHA256; default OFF |
| Profile-guarded supervision and packaging | `recipes/pico-dsgx10/{Dockerfile,entrypoint.py}`; `pico-token-corruption-20261108/image/` | New generic paths/all-in-one layout, no inherited site configuration |
| Qualify and publish | Sampler `README.md`, fresh qualification | Re-run gates for the new packaging; historical results are not new acceptance |

All shortened `pico-*` evidence paths in this table are under `docs/operations/evidence/`. Reports/text docs were read; other recipe/source artifacts were inventoried by filename and size only under the session safety restriction. Thus this is a faithful **documented workflow scaffold**, not an executed end-to-end build or an independent audit of every original script byte.

## Gaps before a reproducible release

1. **Exact native build input distribution / cross-toolchain lock.** The qualified 13-input manifest/control relink is described, but its original object/library/sysroot bundle and builder image digest are not supplied. A clean compile may differ and is rejected by the qualified packaging validator until resolved or independently requalified.
2. **Public runtime-base dependency and license closure.** Select and pin a redistributable ARM64 CUDA 13 / RDMA base; prove every dynamic dependency and preserve dependency notices/SBOM. No private base image is referenced in this scaffold.
3. **Large asset materialization.** Download/verify the pinned checkpoint, run the supplied conversions and every-byte verification, materialize/hash Engram, and obtain/verify the optional vector. None occurred in this turn.
4. **One-image redesign is not byte-identical production reproduction.** Existing production layers do not bundle the large model data. Adding all ranks, generic paths and public-default-OFF supervision produces a new digest. Full package compressed size, extraction/disk cost and registry large-layer support remain unmeasured.
5. **Generated launcher / package acceptance.** The new supervisor is host-unit-tested scaffolding, not a tested four-rank launcher. Validate CLI compatibility, rank/device mapping, GID selection, NVMe spill/guard and access-control integration before a trial.
6. **Fresh rebuilt-image gates.** OFF/alpha-zero identity, capability/needles, protocol, throughput and 16-stream stability must be rerun on the immutable candidate. No production system or Spark was touched here.
