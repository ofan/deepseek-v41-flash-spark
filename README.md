# DeepSeek-V4.1-Flash on four DGX Sparks

> Publication is blocked for the exact production mirror. A separate source-rebuilt runtime candidate and privacy audit are documented in [publication remediation](docs/publication-remediation.md). Neither that candidate nor the all-in-one bundle is a new GPU-qualified production release. The repository/package remain private.

An **unofficial recipe** for stock [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) with **native image input**, on **4 × NVIDIA DGX Spark / GB10**, TP4. There is **no affiliation with, sponsorship by, or endorsement from DeepSeek**. Engine work builds on Andy Shu's engine and Picom's Pico fork.

## Current qualified stack

Version **2026.11.08-native-vision-trial-r1**, fork engine **b7c3eb5**, stock 1017 at the locked revision. The production qualification passed text identity **9/9 OFF + 9/9 alpha-zero**, fixed image QA **88/88 OFF + 88/88 GLP-39**, protocol **zero leaks**, and stability **16/16**, zero restarts/OOM. These are recorded production results, not tests rerun for this repository. See [benchmarks and evidence](docs/benchmarks.md).

- Native 32-layer vision tower, trained aligner and delimiters: exact **266-tensor**, **970,536,960-byte BF16 payload** pack. Image spans are injected into every TP rank; the model weights are not retuned.
- Patched Pico engine, hardened DSML output handling, sampler open-interval clamp, retained-session/SSD fixes.
- Optional **msuiche GLP-39** runtime vector: **recipe default OFF**, tested opt-in alpha **0.75**, zero-based layers **1–39**. Production measurements use GLP-39 unless marked OFF.
- **16 active slots**, **1,048,576-token context**, 3 GiB saved-session RAM and **160 GiB SSD spill per rank**, plus a **32 GiB** disk guard. Four ranks are required; one Spark cannot stage the complete model.

## Package status and contents

The repository contains the pinned source/build/conversion recipe, vision-asset preparation, hash-guarded generic supervisor, optional vector acquisition, licenses, tests and benchmark provenance. **No model/vector tensor payloads are stored in Git.**

The verified private image mirror is:

```text
ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1
sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9
```

**The private GHCR mirror is published and verified byte-identical by manifest readback.** Owner-authenticated lookup confirms PRIVATE visibility. See [completion report](docs/completion-report.md) for the transfer diagnosis and receipt. The existing production OCI contains binaries/runtime/vision pack but **mounts text rank files and Engram separately**. Mirroring that digest does not bundle the hundreds of GB of text assets. The Dockerfile here can assemble those assets into a **distinct all-in-one candidate**, not the production digest. That layout has not been built or fleet-qualified; its residual gaps are explicit in [build documentation](docs/build.md#residual-gaps).

## Quick-start shape (remaining build gaps apply)

1. Review [optional host setup](docs/setup-spark.md), qualify your four-node native-verbs RoCE ring and reserve actual NVMe capacity. Build **off serving machines**.
2. Follow [build steps](docs/build.md): fetch exact fork code; obtain the pinned official checkpoint; convert and verify text ranks/Engram or reuse verified existing assets; prepare the exact compact vision pack and publisher modules; optionally fetch authentic GLP-39.
3. Stage hash-qualified binaries, validate the bundle, then build a **new** immutable ARM64 image. The contaminated production mirror is forbidden as the publication base; a separately audited sanitized runtime receipt is required. The current candidate remains blocked, so this build gate stops before Docker. No script deploys or pushes automatically.
4. Supply your own fleet file, GPU/RDMA access and local writable spill. Every node runs the same image with a different rank (0–3). Rank0 starts the serialized local vision encoder and HTTP frontend.

```sh
# Invocation inside the NEW bundled image, not the production mirror's launcher:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf
# Optional steering, consistently on every rank:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf --steering glp39
```

The default enables native image input and leaves steering OFF. `--no-vision` disables the image side path. Fleet asset keys point to `/opt/package/model/rankN.dsw`, `/opt/package/model/engram_hashmap.bin` and `/opt/package/model/`. Configure your own devices/addresses/GID. Keep the endpoint behind your own access controls.

## Image requests

The direct frontend accepts OpenAI-compatible **Chat Completions** with ordered `text` and `image_url` content parts. `image_url.url` may be a PNG/JPEG/WEBP data URL or a permitted public HTTP(S) URL. Both streaming and non-streaming are supported. Up to **16 images**, **1024 span rows per image**, with request/frame/pixel/queue bounds and SSRF checks. Images are encoded on rank0 using the checkpoint's native ViT/aligner and broadcast to all ranks. Image-bearing histories intentionally bypass prefix/session caching and are re-encoded each turn. Generated text attends to the resulting image-conditioned KV normally.

This is **image input**, not image generation. Video, audio and raw Responses image parts are not a direct-engine API promise; clients must use the supported Chat format. A missing encoder returns bounded errors for image requests without changing text inference. Do not send internal placeholder tokens as user text.

## Documentation and credits

[Benchmarks](docs/benchmarks.md) · [Setup](docs/setup-spark.md) · [Steering](docs/steering.md) · [Build](docs/build.md) · [Completion/transfer report](docs/completion-report.md)

Recipe: MIT. Engine: MIT, Andy Shu and Picom. Model/native vision weights: MIT, DeepSeek. Optional vector: MIT per msuiche's published model-card metadata. Preserve notices; see [LICENSE](LICENSE), [NOTICE](NOTICE) and `licenses/`. Runtime dependencies retain their own licenses. Repo/package visibility stays private; publication is a separate decision.
