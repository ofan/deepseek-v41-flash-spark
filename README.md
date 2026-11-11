# DeepSeek-V4.1-Flash on four DGX Sparks

An **unofficial recipe scaffold** for stock [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) on **4 × NVIDIA DGX Spark / GB10**, tensor parallelism 4. There is **no affiliation with, sponsorship by, or endorsement from DeepSeek**. Engine work builds on Andy Shu's engine and Picom's Pico fork.

## Package contents

- Pinned patched Pico engine source, including retained-session fixes, hardened DSML output handling and the sampler open-interval clamp.
- Stock 1017 weights converted losslessly to Pico rank files, plus per-rank disk-backed Engram tables.
- Optional **msuiche GLP-39** spec-v1 direction file. **Public default: steering OFF.** Enabling it is a runtime choice; the model weights are not modified.
- A single-image packaging Dockerfile, bounded supervisor, conversion scripts, build-step mapping, benchmark provenance and optional host-setup notes.

**Status:** the source lineage and measurements are production-proven; this newly scaffolded, all-in-one image is **not built, published or qualified yet**. The recorded production OCI image supplied its large model assets separately. Bundling them and making steering OFF the public default changes the image/configuration; it cannot preserve the historical production digest. See [build gaps](docs/build.md#gaps-before-a-reproducible-release).

The text-serving profile is **16 slots**, each with a **1,048,576-token context**, 3 GiB saved-session RAM and 160 GiB SSD spill per rank; keep an additional 32 GiB disk guard. These settings and their evidence are in [benchmarks](docs/benchmarks.md). This package does not claim image-input support.

## Quick-start shape (future release; not a published image)

1. Read [optional Spark setup](docs/setup-spark.md). Arrange a qualified four-node RoCE ring and local NVMe; do not assume arbitrary four-node Ethernet is equivalent.
2. Follow [the pinned source/build/conversion sequence](docs/build.md) **off serving machines**. Obtain the model at the locked revision and the authentic optional vector; run the verification steps. No weights are stored in this Git repository.
3. Resolve the documented runtime-base and qualified-build-input gaps, then assemble one immutable ARM64 image containing all four rank assets. The intended package is `ghcr.io/ofan/deepseek-v41-flash-spark`, **PRIVATE**. There is no current pullable release.
4. Supply your own fleet configuration using the engine's documented keys. Every node runs the **same image**, with a different rank (0–3), the same fleet file, GPU/RDMA access and a writable 160 GiB spill allocation. The supervisor starts the HTTP frontend only on rank 0.

```sh
# Invocation shape INSIDE the future image, not an executable deployment command:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf --steering off
# Optional, on every rank:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf --steering glp39
```

The fleet file must use `/opt/package/model/rankN.dsw`, `/opt/package/model/engram_hashmap.bin`, and `/opt/package/model/` for the corresponding rank's Engram shards. Configure your own devices, link addresses and GID index. Keep the HTTP listener behind your own access controls; this scaffold intentionally contains no credentials or credential paths.

5. Qualify identity, capability, long-context retrieval, concurrent streams, output protocol and throughput before adopting a rebuilt image. Do not infer release qualification from a successful source compilation.

## Documentation

- [Benchmark figures and evidence](docs/benchmarks.md)
- [Optional host setup](docs/setup-spark.md)
- [Optional GLP steering](docs/steering.md)
- [Build steps, provenance mapping and gaps](docs/build.md)
- [Scaffold report and private GHCR push plan](docs/scaffold-report.md)

## License and credits

Recipe code: MIT. Engine line: MIT, Andy Shu and Picom. Model weights: MIT, DeepSeek. Steering vector: MIT per msuiche's published model-card metadata. Preserve upstream notices and licenses; see [LICENSE](LICENSE), [NOTICE](NOTICE), and `licenses/`. CUDA, system libraries and other runtime dependencies retain their own licenses.
