# DeepSeek-V4.1-Flash on four DGX Sparks

An **unofficial recipe for text and image input** with stock
[DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017),
the Pico engine and **4 × NVIDIA DGX Spark / GB10 (128 GB each), TP4**, on a
qualified direct ConnectX-7 RoCE ring. This is image understanding, not image generation.

**Publication is currently held:** the separate distribution package has been copied
and its digest verified with owner authentication, but its visibility is still private.
The pull command below is the intended public quick-start, **not yet anonymously usable**.
The repository also remains private until anonymous image readback and all publication
checks pass. See [publication status](docs/completion-report.md).

**Qualification:** the published-candidate bytes are a sanitized twin of the production
build: same engine source, byte-identical frontend and vision assets, but an engine
rebuilt under generic paths and a new runtime/launcher. **GPU serving qualification
of this candidate is pending.** Production itself runs a separate private exact mirror;
that mirror is neither distributed here nor required by these instructions.

## Quick-start — bring your own text assets

The distribution image contains the ARM64 runtime, engine, frontend, native vision pack
and optional authentic GLP-39 vector. **It does not contain the text rank files,
Engram shards or tokenizer.** There is no single-node or CPU serving mode for the full model.

1. Review [host/storage/fabric requirements](docs/setup-spark.md). Use four **idle**
   compatible nodes, not machines already serving a model.
2. Obtain the pinned official checkpoint and produce the lossless per-rank text assets
   using [the public-source asset preparation steps](docs/build.md#prepare-the-text-assets).
   This requires a separate CUDA build/conversion host and substantial local storage.
   Do not substitute another model or checkpoint revision.
3. Install Docker with NVIDIA Container Toolkit on each node, confirm GPU and native
   RDMA access, and create your own `fleet.conf` following [the fleet-file guide](docs/setup-spark.md#fleet-file).
   The addresses, devices and GID must describe **your** physical ring.
4. On **each** node, pull the identical digest-pinned image:

```sh
IMAGE=ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
docker pull --platform linux/arm64 "$IMAGE"
```

5. Stage that node's `rankN.dsw`, its two Engram shards, `engram_hashmap.bin`,
   `tokenizer.json` and checkpoint metadata under `/srv/pico/model`. Keep a writable
   `/srv/pico/spill` with **160 GiB spill capacity plus the 32 GiB engine free-space
   guard**, in addition to assets/image storage. Then run one rank on each node:

```sh
# Set RANK separately: 0, 1, 2, 3, exactly one per node.
RANK=0
# IMAGE must be the exact public-package reference above.
docker run --name pico --network host --gpus all \
  --device /dev/infiniband --ulimit memlock=-1:-1 --cap-add IPC_LOCK \
  --mount type=bind,src=/srv/pico/model,dst=/opt/package/model,readonly \
  --mount type=bind,src=/srv/pico/fleet.conf,dst=/etc/pico/fleet.conf,readonly \
  --mount type=bind,src=/srv/pico/spill,dst=/var/lib/pico \
  --tmpfs /run/pico:rw,nosuid,nodev,size=64m \
  "$IMAGE" --rank "$RANK" --fleet /etc/pico/fleet.conf --steering off
```

Start all four ranks as a coordinated ring; a rank waits for its peers. Only rank0
serves HTTP, on port **8888**. Host networking exposes that listener: firewall it and
put access controls/TLS in front before exposing it beyond a trusted network.
`/dev/infiniband` access and memory locking must match your site policy; do not replace
this with blanket privileged mode. These invocation examples have offline tests, **not
a completed four-rank runtime acceptance** of the sanitized image.

On rank0, after startup:

```sh
curl --fail http://127.0.0.1:8888/health
curl --fail http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"Hello."}],"max_tokens":32}'
```

For an image request use Chat Completions content parts, for example `text` plus
`image_url` with a PNG/JPEG/WEBP data URL. Public HTTP(S) image URLs are also accepted
subject to bounded fetching/SSRF validation. Streaming is supported. Rank0 serializes
native vision encoding; spans are broadcast and injected on **all four ranks**.
Image-bearing histories bypass prefix/session caching and are re-encoded each turn.
Up to 16 images and 1024 span rows/image are bounded by request/frame/pixel/queue limits.
No raw model placeholder text is needed. Audio/video and image generation are not offered.

## Optional GLP-39 — default OFF

The vector does not modify the checkpoint. To opt in, replace `--steering off` with
`--steering glp39` **on every rank**. Tested setting: alpha **0.75**, zero-based layers
**1–39**, spec-v1 post-layer per-stream projection. Credit: **msuiche**, MIT.
See [steering details](docs/steering.md). Do not mix steering settings within a ring.

## Recorded production benchmarks — not candidate measurements

| Measurement | Result |
|---|---:|
| Text prefill 32K | 8,951 tok/s |
| Text prefill 131K | 9,259 tok/s |
| Text prefill near 500K | 9,076 tok/s |
| Text prefill near 1M | 8,598 tok/s |
| Decode single stream | 88.772 tok/s |
| Image QA | 88/88 OFF + 88/88 GLP-39 |
| Text identity | 9/9 OFF + 9/9 alpha-zero, bit-identical |
| Slots / context | 16 / 1,048,576 tokens |

Source for every row: homeinfra evidence at `cf6e8b67c`,
`docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`.
[Benchmarks](docs/benchmarks.md) describes the method and historical comparisons.
These are reference production measurements, **not** performance/quality claims for
an unqualified rebuild, and not a hardware guarantee.

## Status, build and licenses

[Build and residual gaps](docs/build.md) · [Host setup](docs/setup-spark.md) ·
[Audit/qualification](docs/publication-remediation.md) · [Publication status](docs/completion-report.md)

MIT credit chain: **Andy Shu and Picom** (engine), **DeepSeek** (model/native vision),
**msuiche** (optional vector). Recipe is MIT; preserve [LICENSE](LICENSE),
[NOTICE](NOTICE), publisher notices and dependency licenses. Third-party runtime
components retain their own terms. **No affiliation with, sponsorship by or
endorsement from DeepSeek exists.** This is not an official DeepSeek or NVIDIA package.
