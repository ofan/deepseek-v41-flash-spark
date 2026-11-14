# DeepSeek V4.1 Flash on 4 DGX Sparks

Run stock **DeepSeek-V4.1-Flash-1017** with the [Pico engine](https://github.com/Picom-code/pico-dgx-ds4), forked from
[blaesus/dsgb10](https://github.com/blaesus/dsgb10), on **4 × NVIDIA DGX Spark / GB10**:
**1,048,576-token context**, image input, 16 request slots, and lossless text weights.
The measured production stack prefills at **8,951 tok/s at 32K** and **8,598 tok/s near 1M**;
fresh bounded decode measurements are below. Optional GLP-39 activation steering is
**OFF by default**. This is image understanding, not image generation.

This repository includes the engine/frontend implementation, four feature patches
plus their cache-fidelity prerequisite, conversion/build scripts, a launcher and
provenance. Browse the [production implementation](vendor/engine) at **b7c3eb5**
and [ordered patch series](patches). The **public ARM64 runtime image** contains engine, frontend, native
vision assets and optional vector. **It does not contain the text rank files**,
Engram shards or tokenizer: prepare these from the official checkpoint first.

**Qualification matters:** the published image is the sanitized twin of the
production build: same engine source, byte-identical frontend and vision assets,
but an engine rebuilt under generic paths and a new runtime/launcher. Its **four-rank
GPU serving qualification is pending**. Measurements below are from production,
not from the public candidate. Production runs a separate private exact mirror;
you do not need that mirror to follow this recipe. No turnkey or byte-identical
compiler reproduction is claimed. See [build status and remaining gaps](docs/build.md#residual-gaps).

## Measured performance

Four GB10s, TP4, **2,200 MHz configured graphics-clock cap on every GPU**.
The GPUs report power limit **N/A**; no wattage cap is inferred. Fresh decode runs
on **2026-11-13**, steering GLP-39 alpha0.75, 256 output tokens per request:

**Benchmarks measured with every GPU capped at 2,200 MHz (graphics clock).**

| Concurrent streams | Prose decode tok/s | Code decode tok/s |
|---:|---:|---:|
| 1 | 72.297 | 73.187 |
| 4 | 107.232 | 161.501 |
| 8 | 156.079 | 261.548 |
| 16 | 236.405 | 320.541 |

Multi-stream numbers are **aggregate**, not per-user. These are one bounded wave
per cell, copies of the existing built-in prompt, on a shared live server. Decode
excludes first-token latency. In particular, prose at eight streams had **21.9–23.6 s
to first token** and only **58.594 tok/s end to end**. Do not read the decode table
as a latency guarantee or sustained-capacity result. All **58/58 requests succeeded**.
[Method, every request timing, end-to-end rates and GPU-cap receipt](docs/benchmarks.md#fresh-decode-battery-2026-11-13).

| Text prefill context | tok/s |
|---|---:|
| 32K | 8,951 |
| 131K | 9,259 |
| Near 500K | 9,076 |
| Near 1M | 8,598 |

Prefill numbers are retained from the accepted production re-trial, not remeasured
here. Evidence: homeinfra `cf6e8b67c`,
`docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`.
[Full benchmark provenance and limitations](docs/benchmarks.md).

- **Vision check:** the model answers questions about images, **88 of 88 correct**
  with steering off and **88 of 88** with GLP-39 on. Six known-answer images were
  tested across streaming, non-streaming, repeat and concurrency combinations;
  this is not 88 different images.
- **Stock fidelity:** with steering off, output matches the stock-model control
  token for token: **9 of 9 prompts bit-identical**, including a 1M-token needle;
  alpha-zero controls also passed 9/9. This matters because the patches do not
  change stock behavior on those tested prompts; it is not proof for every prompt.

Both checks come from the same accepted production re-trial evidence above.

## Quality

The target standardized comparison is **HLE without tools, text-only subset**,
for which [DeepSeek's official model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/main/README.md)
reports **44.0%**. The recipe comparison is GLP-39 **ON, alpha 0.75**, layers 1–39.

| Benchmark | DeepSeek official | This recipe, GLP-39 ON | Recipe minus official |
|---|---:|---|---|
| HLE without tools, text-only | **44.0%** | **Not measured** | N/A |

**No standardized recipe quality score or point delta is claimed yet.** The
available HLE evaluator is an offline DeepInfer engine launcher, not a client for
the live Pico API, and its dataset is not staged. Running that launcher unchanged
would measure a different engine, not this recipe. An HTTP-capable evaluation path
and the official dataset are needed before this table can contain a recipe score.
[Official scores, evaluator readiness and remaining work](docs/benchmarks.md#standardized-quality-comparison--not-run).

**Serving acceptance check:** GLP-39 scored **14/14** on the existing small local
suite: six capability checks, two long-context retrieval checks and six P5
capability checks. This checks serving correctness; it is **not HLE**, is not a
broad model-quality estimate, and cannot be compared numerically with 44.0%.
[Settings and per-check receipt](docs/benchmarks.md#local-serving-acceptance-2026-11-14).

## Requirements

- **4 × NVIDIA DGX Spark / GB10**, 128 GB unified memory each; ARM64 Linux with a
  compatible NVIDIA driver, Docker and NVIDIA Container Toolkit. There is no
  one-node, CPU or ordinary Ethernet-only mode for this full model.
- A **qualified direct ConnectX-7 RoCE ring**, correctly cabled and addressed for
  Pico's native verbs collectives, with memory locking and RDMA device access.
  This recipe does not create that fabric. See [host and fabric setup](docs/setup-spark.md).
- Local NVMe for each rank's model/Engram files, image storage and **160 GiB writable
  saved-session spill plus 32 GiB free-space guard per node**. Measure actual asset
  sizes before proceeding; a 128 GB host is not a 128 GB disk requirement.
- A separate off-serving ARM64 CUDA13 build/conversion host and enough workspace
  for the official checkpoint and converted output. Obtain the checkpoint at the
  pinned revision; model acquisition is a substantial download.

## Setup — use four idle nodes

### 1. Prepare hosts and the model

Follow [host preparation](docs/setup-spark.md), including NVIDIA's toolkit and RDMA
checks. Clone this repository on the **build host**, then use its included source:

```sh
git clone https://github.com/ofan/deepseek-v41-flash-spark.git
cd deepseek-v41-flash-spark
python3 scripts/verify-patches.py
bash scripts/fetch-sources.sh   # stages in-repo source; no external engine checkout
bash scripts/build-engine.sh   # off-serving ARM64 CUDA13 host only
```

Follow [asset preparation](docs/build.md#prepare-the-text-assets) to acquire the
pinned official snapshot and run all four lossless converters/verifiers. Do not
skip verification. On each serving node, create `/srv/pico/model` and stage **only
its rank** (`rankN.dsw`), its two `engram-l{1,14}-rNof4.bin` shards, and the common
hashmap, tokenizer and checkpoint metadata there. Verify hashes after copying.
The image supplies vision assets; no text reconversion is needed just to add vision
to already verified assets. Create `/srv/pico/spill` on suitably sized writable NVMe.

### 2. Configure your ring

Copy `examples/fleet.conf.example` to `/srv/pico/fleet.conf` on each node. Replace
**every `REPLACE_...` field** with your own devices, GID, peer names and link
addresses; it is not a runnable sample network. Follow the [fleet-file guide](docs/setup-spark.md#fleet-file).
Keep ranks, devices and topology consistent. Verify the idle ring with the included
engine's `ring_test` before loading the model. No recipe script configures hosts
or starts remote containers for you.

### 3. Pull the public image on every node

```sh
IMAGE=ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
docker pull --platform linux/arm64 "$IMAGE"
```

Anonymous manifest readback confirms that digest; no registry login is required.

### 4. Launch one rank per node

Set `IMAGE` as above and set **RANK to that node's unique value 0, 1, 2 or 3**.
Start all four as one coordinated ring; a rank waits for its peers.

```sh
RANK=0
# IMAGE must be the exact reference from step 3.
docker run --name pico --network host --gpus all \
  --device /dev/infiniband --ulimit memlock=-1:-1 --cap-add IPC_LOCK \
  --mount type=bind,src=/srv/pico/model,dst=/opt/package/model,readonly \
  --mount type=bind,src=/srv/pico/fleet.conf,dst=/etc/pico/fleet.conf,readonly \
  --mount type=bind,src=/srv/pico/spill,dst=/var/lib/pico \
  --tmpfs /run/pico:rw,nosuid,nodev,size=64m \
  "$IMAGE" --rank "$RANK" --fleet /etc/pico/fleet.conf --steering off
```

Keep these terminals or your own reviewed service supervision in place. Do not
mix builds or steering settings. The launcher stops the rank if a child exits;
it does not automatically repair or restart the ring. Only rank0 serves HTTP,
on **port 8888**. Host networking exposes the listener: firewall it and put
access control/TLS in front before use outside a trusted network. Do not replace
scoped GPU/RDMA/memory-lock permissions with blanket privileged mode.

### 5. Health check and first text request

On rank0 after startup:

```sh
curl --fail http://127.0.0.1:8888/health
curl --fail http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"Hello."}],"max_tokens":32}'
```

### 6. Send an image

Use Chat Completions `text` and `image_url` content parts. This example builds a
request from **your own** small PNG; use the resulting JSON with the same endpoint.
It is an API example, not a benchmark fixture or claimed QA run.

```sh
python3 - <<'PYIMAGE' > image-request.json
import base64, json
from pathlib import Path
url = 'data:image/png;base64,' + base64.b64encode(Path('example.png').read_bytes()).decode()
print(json.dumps({'model':'deepseek-v4.1-flash','messages':[{'role':'user','content':[
    {'type':'text','text':'Describe this image.'},
    {'type':'image_url','image_url':{'url':url}}]}],'max_tokens':128}))
PYIMAGE
curl --fail http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' --data-binary @image-request.json
```

PNG/JPEG/WEBP data URLs and bounded public HTTP(S) URLs are supported; use `stream:true`
for SSE. Image-bearing histories bypass prefix/session caches and re-encode each
turn. Rank0 serializes native encoding and broadcasts spans to **all four ranks**.
Limits include 16 images and 1024 span rows/image, plus request/frame/pixel/queue
bounds; a file extension alone is not input validation. No raw model placeholders,
audio/video or image-generation API is needed or offered.

## Optional steering

To opt in, replace `--steering off` with **`--steering glp39` on every rank**.
Tested setting: alpha **0.75**, zero-based layers **1–39**. It uses an authentic
runtime vector, not changed checkpoint weights. Credit **msuiche**, MIT.
[Mechanics, provenance and tradeoffs](docs/steering.md).

## Troubleshooting

| Symptom | Check before retrying |
|---|---|
| Cannot pull | Use the public package and exact tag+digest above; verify disk and registry reachability. No private-image fallback. |
| Rank waits / no HTTP | All four ranks must be running with matching files/settings; inspect each node's `docker logs pico`, cabling, HCA ports, GID and fleet keys. |
| Hash/profile error | Verify the copied assets and pinned revision. Do not bypass a hash guard or mix a local binary with the public profile. |
| GPU/RDMA permission error | Check NVIDIA toolkit, `nvidia-smi`, `/dev/infiniband`, memlock and the idle-ring test; do not grant blanket privilege. |
| Disk guard / allocation failure | Preserve 160 GiB spill plus the 32 GiB free guard and asset/image overhead on every rank. |
| Image rejected / encoder exits | Use a supported small image, inspect rank0 logs, verify vision assets and runtime, and distinguish input bounds from an encoder failure. |
| Slow first token | Prompt length, active traffic and caching matter. Decode tok/s alone excludes that delay; see the measured latency outlier. |

Read [build instructions](docs/build.md), [benchmarks and receipts](docs/benchmarks.md)
and [publication/qualification status](docs/completion-report.md) before adapting
this to an unattended service.

## Unofficial and licensed

No affiliation with, sponsorship by or endorsement from **DeepSeek** exists.
This is not an official DeepSeek or NVIDIA package. MIT credit chain: **Andy Shu
and Picom** (engine), **DeepSeek** (model/native vision), **msuiche** (optional
vector), and ofan (recipe). Preserve [LICENSE](LICENSE), [NOTICE](NOTICE),
`licenses/` and vendored upstream notices. Dependencies retain their own licenses.
