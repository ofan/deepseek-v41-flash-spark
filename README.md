# DeepSeek V4.1 Flash on 4 DGX Sparks

Run **DeepSeek-V4.1-Flash-1017** on **4 × NVIDIA DGX Spark / GB10** with the
[Pico engine](https://github.com/Picom-code/pico-dgx-ds4), forked from
[blaesus/dsgb10](https://github.com/blaesus/dsgb10). It accepts text and images,
keeps up to **1,048,576 tokens** of conversation, and has **16 request slots**.
GB10 is the Spark's processor chip. A **token** is a small piece of text; the **context** is the text the model can use
for one request. A slot is space for one active request. Image support means
understanding an image, not generating one.

GLP-39 is **ON by default, alpha 0.75, layers 1–39**. A **steering vector** is a
file that changes selected internal model activations without rewriting its learned
weights (the numerical values learned during training). Alpha is the strength; layers are internal stages, counted from zero.
Use `--steering glp39` on **every rank**; `--steering off` on every rank is an
explicit opt-out. A rank is one worker: rank 0, 1, 2 or 3, each on its own Spark.

**Four-rank GPU serving qualification is pending for the public image.** It is the sanitized twin of the
production build: the same engine source, byte-identical frontend (the web request
handler) and vision assets (the model's image-reading files), but a rebuilt engine
under generic paths and a new launcher. Sanitized means installation-specific data was
removed or generalized. Production below means the reference serving deployment
that supplied the measurements; it does **not** mean your new installation. Those measurements do **not**
prove that this published image has passed a four-rank GPU serving run. GPU means
the processor doing model calculations. Production uses a separate private exact
mirror; public users do not need it. There is no claim of a turnkey or
byte-identical compiler reproduction. See [remaining build gaps](docs/build.md#residual-gaps).

## Prerequisites — before step 1

Have these in hand; an unattended agent must stop if any item is missing rather
than guess, delete files or change security settings to get past it.

- [ ] **Four Sparks**, each with a GB10 GPU, **128 GB unified memory** (shared CPU/GPU
  memory), and **ARM64 Linux** (the processor type reported as `aarch64`). There is
  no single-node, CPU-only (general-purpose processor) or ordinary-network-only mode for this full model.
- [ ] **Direct QSFP ring cabling**, with an approved port/address plan and recovery
  access to every node. QSFP is the high-speed cable connector family. A **RoCE ring**
  is the direct network loop used to transfer GPU memory between neighbors. Two
  independent paths run in each direction; the topology is **0 → 1 → 2 → 3 → 0**.
  Do not assume a physical connector maps to a particular device name.
- [ ] **Disk capacity on every node:** its actual rank and lookup-table files, the
  downloaded/unpacked image and temporary download space, **plus 160 GiB saved-session
  space and a 32 GiB free-space guard**. GiB is 1,073,741,824 bytes. Use local NVMe,
  the fast disk inside each machine. [Setup steps 5–6](docs/setup-spark.md#5-complete-the-fleet-file-and-copy-only-each-ranks-assets--build-host)
  calculate file bytes and check space; 192 GiB is a reserve, **not the total disk requirement**.
- [ ] **Installed host software and access:** NVIDIA DGX OS / Ubuntu, a supported
  NVIDIA driver, Docker (runs packaged programs), NVIDIA Container Toolkit (gives
  Docker GPU access), Bash, Python, Git, curl, rsync and RDMA utilities. RDMA means
  direct memory transfer over the ring. You need administrator permission and
  approved Docker access. The historical tested baseline is Ubuntu **24.04.4 LTS**,
  kernel **7.0.0-1019-nvidia-64k**, **65,536-byte pages**, driver **580.178.04**,
  ConnectX-7 firmware **28.45.4028**. The kernel is the operating system's core;
  pages are its memory blocks, a driver controls hardware, and firmware is software
  inside the network adapter. Do not downgrade blindly. Docker/toolkit versions
  were not pinned in that record; differing versions need local validation.
- [ ] **A separate non-serving ARM64 build/conversion host** with CUDA **13.0**,
  CMake **3.28+**, g++ **13.3 / C++20**, Python **3.12** and Rust (recorded Cargo
  **1.97**). These are the GPU toolkit and compilation tools. It needs space for
  both the official checkpoint and converted output at once; no fixed measured
  build-host disk minimum is claimed. Do not compile on a serving Spark.
- [ ] **Downloads and accounts:** network access to GitHub, GHCR and the official
  [DeepSeek checkpoint](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017).
  A checkpoint is the publisher's learned model files. GHCR means GitHub Container
  Registry, which hosts the public image; no GitHub login is needed to pull it.
  If Hugging Face requires an account or terms acceptance, arrange it before
  downloading. Pin checkpoint revision `1bae0e1088993b9b82de08f59de5be5a34e42170`.
  **HLE (Humanity's Last Exam, an optional quality test) access is not required for serving.**
- [ ] **Local inputs:** four distinct ranks, machine names, remote-copy destinations
  and the approved network plan. [Setup's input table](docs/setup-spark.md#before-step-1-collect-the-inputs)
  specifies them. The repository intentionally contains no usable site addresses.

The **public ARM64 runtime image** contains the engine, frontend, native image
files and authentic GLP-39 vector. **It does not contain the text rank files**,
Engram shards or tokenizer. Engram shards are pieces of the model's disk lookup
tables; a tokenizer converts text into tokens. Prepare these from the official
checkpoint using the included [source](vendor/engine) at **b7c3eb5** and
[ordered patches](patches); no external engine checkout is required.

## Quick path — prepared machines and verified model files

This is the complete **start and check** sequence for experienced owners and agents
who already completed setup steps 1–7 below. It is **not** a weight downloader or
an automatic network installer. On a fresh installation, take the full guided path
first. Required on each node: `/srv/pico/model/SHA256SUMS`, the model files it lists,
`/srv/pico/fleet.conf`, writable `/srv/pico/spill`, and `/srv/pico/rank` containing
its verified rank. An agent must not synthesize those inputs to make a check pass.

Run this Bash sequence on **each of the four nodes concurrently**, with launches
within 120 seconds of one another. Hash verification must already have completed
on all nodes, not run serially after the first rank starts:

```bash
set -euo pipefail
IMAGE=ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
docker pull --platform linux/arm64 "$IMAGE"
printf '%s\n' "$IMAGE" > /srv/pico/image.ref
IMAGE=$(cat /srv/pico/image.ref)
RANK=$(cat /srv/pico/rank)
case "$RANK" in 0|1|2|3) ;; *) echo 'STOP: invalid rank' >&2; exit 1;; esac
test -s /srv/pico/model/SHA256SUMS
if docker container inspect pico >/dev/null 2>&1; then
  echo 'STOP: container pico already exists; use the stop/rollback instructions' >&2
  exit 1
fi
docker run -d --name pico --network host --gpus all \
  --device /dev/infiniband --ulimit memlock=-1:-1 --cap-add IPC_LOCK \
  --mount type=bind,src=/srv/pico/model,dst=/opt/package/model,readonly \
  --mount type=bind,src=/srv/pico/fleet.conf,dst=/etc/pico/fleet.conf,readonly \
  --mount type=bind,src=/srv/pico/spill,dst=/var/lib/pico \
  --tmpfs /run/pico:rw,nosuid,nodev,size=64m \
  "$IMAGE" --rank "$RANK" --fleet /etc/pico/fleet.conf --steering glp39
test "$(docker inspect pico --format '{{.State.Running}} {{.RestartCount}} {{.State.OOMKilled}}')" = 'true 0 false'
if [ "$RANK" = 0 ]; then
  timeout 1800 bash -c 'until curl -fsS http://127.0.0.1:8888/health | grep -qx ok; do sleep 5; done'
  curl --fail-with-body --max-time 180 http://127.0.0.1:8888/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"Hello."}],"max_tokens":32}'
fi
```

**Verify:** each launch returns a container ID and the state test exits zero. Rank 0
returns health `ok` and a text response containing `choices`. A container being
running is not enough: wait for the health check and inspect a real answer. For
image use, stop, and rollback, see the corresponding guided steps below.

## Terms for reading the published measurements

- **Tensor parallel (TP4)** means splitting one model's calculations across four GPUs.
- **Prefill** is the work of reading the input before generating an answer.
- **Decode** is generating answer tokens; `tok/s` is tokens per second.
- A **stream** sends answer pieces as they are generated; concurrency is the number
  of requests running at once. Aggregate is their total, not each user's speed.
- A **prompt** is the input sent to the model; a **wave** is a group of requests
  launched together. Built-in prompts are the benchmark tool's existing examples.
- **Latency** is waiting time; first-token latency excludes the rest of the answer,
  while end-to-end time includes both waiting and generation. `K` means thousand;
  `1M` means roughly one million.
- A **graphics-clock cap** limits GPU calculation frequency; MHz is million cycles
  per second. `N/A` means no value was reported, not a zero setting.
- **Stock fidelity** asks whether an unchanged-model control and the patched engine
  return exactly the same tokens. Bit-identical means exactly the same recorded
  output; a needle check retrieves a fact placed inside a long input. Alpha-zero
  means steering strength zero, which is separate from the OFF switch.
- **HLE** (Humanity's Last Exam) is a standardized difficult-question benchmark;
  its text-only subset excludes image questions. A suite is a set of checks;
  **P5** is the local name of six serving checks, not an official benchmark.
- **HTTP** is the web request protocol, **JSON** its structured message format,
  and an adapter translates requests between programs. A model card is the
  publisher's model documentation. An **LLM scorer** is a language model used to
  grade answers. HTTP 403 means access was refused.

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

The selected standardized comparison is **HLE without tools, text-only subset**,
for which [DeepSeek's official model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/main/README.md)
reports **44.0%**. The recipe comparison is GLP-39 **ON, alpha 0.75**, layers 1–39.

| Benchmark | DeepSeek official | This recipe, GLP-39 ON | Recipe minus official |
|---|---:|---|---|
| HLE without tools, text-only | **44.0%** | **Not measured** | N/A |

**No recipe quality score or point delta is claimed.** Dataset access is resolved:
the pinned official revision was staged and verified locally at **2,158 text-only
questions** of 2,500. The run is stopped by a protocol difference, not by access.
Unchanged production caps output at **32,768 tokens**, while the official card
reports HLE at **at least 256K**. In diagnostic requests drawn from the official
question set at that cap, **5 of 9 produced no answer at all** because they reached
the 32,768-token limit first; the four that finished needed 19K-26K tokens. A capped
score would measure a shorter protocol, and the complete text-only set projects to
roughly **60 million output tokens, about six days of exclusive serving**. Neither a
partial subset nor a shortened-budget result is published as the HLE score. No
serving, clock or routing setting was changed.
[Official reference, dataset provenance and probe evidence](docs/benchmarks.md#standardized-quality-comparison--dataset-staged).

**Serving acceptance check:** GLP-39 scored **14/14** on the existing small local
suite: six capability checks, two long-context retrieval checks and six P5
capability checks. This checks serving correctness; it is **not HLE**, is not a
broad model-quality estimate, and cannot be compared numerically with 44.0%.
[Settings and per-check receipt](docs/benchmarks.md#local-serving-acceptance-2026-11-14).

## Requirements

The [up-front checklist](#prerequisites--before-step-1) and the
[full setup guide](docs/setup-spark.md) are required, not optional background.
The guide supplies the machine-specific input schema, software checks, network
checks, converter commands, per-rank copy commands and checksum checks. Do not
start a partial ring: all four ranks must use the same image, model revision,
fleet file and steering setting.

## Full guided path

Use Bash (`bash`) for these commands. A command exiting zero means it succeeded;
any nonzero exit means stop at that step. Run each block on the machine named in
its heading. `sudo` runs an administrator command; `ssh` runs a command on another
machine, and `rsync` copies files while retaining partial transfers for resumption.
Do not commit your local machine names, addresses or login information here.

### 1. Prepare the hosts and direct cables

Complete [setup steps 1–3](docs/setup-spark.md#1-check-the-installed-operating-system-and-tools--every-spark).
They contain the prerequisite installation links, utility-install commands,
physical next/previous port mapping, address input template and exact link tests.
All four nodes must be idle; first installation is not a live migration.

**Verify on each node:** `uname -m` prints `aarch64`; `rdma link show` shows each
selected link `ACTIVE` / `LINK_UP`; every documented large-packet ping has
`0% packet loss`. A management-network ping alone is not a ring test.

### 2. Prepare and copy the text model files

On the separate build host, complete [setup steps 4–5](docs/setup-spark.md#4-build-converters-and-prepare-verified-model-files--build-host-only).
These download the exact official revision, build the included converters, verify
all four conversions and copy only the correct rank/shards to each node.
No weights are downloaded by the launcher. Do not invent or substitute a vector.
The public image already supplies the authentic vector and native vision files.

**Verify on each node:**

```bash
cd /srv/pico/model
sha256sum -c SHA256SUMS
```

Every listed file must end `OK`, and exit status must be zero. A file existing or
a download completing is not sufficient. Keep the receipt used to make this list.

### 3. Pull the exact image and test the ring

Complete [setup steps 6–7](docs/setup-spark.md#6-pull-and-verify-the-runtime--every-spark).
They pull the exact public image, check GPU visibility and free disk, derive a
unique rank from the approved fleet file and run the existing `ring_test` program
on all four GPUs before any model is loaded. A digest is the content checksum
that fixes exactly which image is being used.

**Verify on each node:**

```bash
RANK=$(cat /srv/pico/rank)
grep -E "rank ${RANK}: passed;" /srv/pico/ring-test.log
```

Success is the node's own `rank N: passed;` summary plus a zero ring-test exit
status, not just a log file containing the word passed. Never skip the ring test
to work around a network error. Use step 7's bounded invocation, not the program's
long-running default battery.

## Use it — start, ask, stop and roll back

### 4. Start all four ranks

Run the following on **each node**. It returns immediately after creating a
background container; start all four within 120 seconds before waiting on rank 0.
Finish the model checksums on **all four** first; re-reading large weights during
sequential launches can leave the first rank waiting past its connection deadline. Do not copy `RANK=0`
to every machine: the previously verified `/srv/pico/rank` supplies its unique rank.
For an upgrade, first follow [save a rollback](#save-a-rollback-before-an-upgrade);
the command deliberately refuses to overwrite an existing `pico` container.

```bash
set -euo pipefail
IMAGE=$(cat /srv/pico/image.ref)
RANK=$(cat /srv/pico/rank)
case "$RANK" in 0|1|2|3) ;; *) echo 'STOP: invalid rank' >&2; exit 1;; esac
test -s /srv/pico/model/SHA256SUMS
if docker container inspect pico >/dev/null 2>&1; then
  echo 'STOP: container pico already exists; use the stop/rollback instructions' >&2
  exit 1
fi
docker run -d --name pico --network host --gpus all \
  --device /dev/infiniband --ulimit memlock=-1:-1 --cap-add IPC_LOCK \
  --mount type=bind,src=/srv/pico/model,dst=/opt/package/model,readonly \
  --mount type=bind,src=/srv/pico/fleet.conf,dst=/etc/pico/fleet.conf,readonly \
  --mount type=bind,src=/srv/pico/spill,dst=/var/lib/pico \
  --tmpfs /run/pico:rw,nosuid,nodev,size=64m \
  "$IMAGE" --rank "$RANK" --fleet /etc/pico/fleet.conf --steering glp39
```

The flags expose the GPU and RDMA devices, allow locked memory (memory the operating
system must not move to disk), and map the host's files to fixed container paths.
`readonly` prevents the container from changing model files. The temporary
`/run/pico` directory contains live sockets (local process connections), not saved
sessions. Port **8888** is the web interface, served **only by rank 0**. Host
networking means it uses the host's network directly. There is no authentication
or encrypted transport in this example: keep it on a trusted, firewalled network;
do not expose it to the internet. Do not use a blanket `--privileged` flag.

**Verify on each node:**

```bash
docker inspect pico --format '{{.State.Running}} {{.RestartCount}} {{.State.OOMKilled}}'
docker logs --tail 30 pico
```

The first command must print **`true 0 false`**: running, no restarts, no recorded container
out-of-memory kill. OOM means out of memory; this flag does not rule out a GPU
allocation error, so also inspect the logs. Logs must not show a child process
exiting or a fatal error. This is necessary but not sufficient; verify rank 0 next.

### 5. Wait for readiness — rank 0 only

```bash
set -euo pipefail
timeout 1800 bash -c 'until curl -fsS http://127.0.0.1:8888/health | grep -qx ok; do sleep 5; done'
curl --fail-with-body http://127.0.0.1:8888/health
curl --fail-with-body http://127.0.0.1:8888/v1/models > /srv/pico/models.json
python3 - <<'MODELS'
import json
from pathlib import Path
models = json.loads(Path('/srv/pico/models.json').read_text())['data']
model = next(m for m in models if m['id'] == 'deepseek-v4.1-flash')
assert model['max_model_len'] == 1048576
print('PASS: deepseek-v4.1-flash, context 1048576')
MODELS
```

**Verify:** health prints **`ok`**, and the model check prints its PASS line. The
wait has a 30-minute deadline, not an indefinite sleep. If it times out, inspect
all four nodes' logs and stop; do not call a half-started ring healthy.
`127.0.0.1` is this same machine, so run these requests on rank 0. The model ID is
exactly `deepseek-v4.1-flash`; aliases provided by other services are not needed.

### 6. Send a text request and read the answer — rank 0 only

```bash
set -euo pipefail
curl --fail-with-body --max-time 180 http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"Hello."}],"max_tokens":32}' \
  > /srv/pico/text-response.json
python3 - <<'ANSWER'
import json
from pathlib import Path
result = json.loads(Path('/srv/pico/text-response.json').read_text())
assert not result.get('error'), result.get('error')
message = result['choices'][0]['message']
text = message.get('content') or message.get('reasoning_content')
assert text, 'No text returned; inspect response and logs'
print(text)
print('PASS: text response received')
ANSWER
```

**Verify:** curl exits zero, the answer is printed, then `PASS: text response
received`. `max_tokens` bounds the answer length; a short answer can end before
the model completes a long explanation. The stored JSON also contains usage and
finish information. This is an example request, not a new benchmark prompt.

### 7. Send an image and read the answer — rank 0 only

No separate image download is needed for this example. Create a small plain red
PNG (a standard image file format), using only Python's built-in libraries. This
is a usage example, **not a measured vision benchmark or one of the 88 checks**.

```bash
python3 - <<'PNG'
import struct, zlib
from pathlib import Path
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
w = h = 64
pixels = (b'\0' + bytes((255, 0, 0)) * w) * h
image = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
image += chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')
Path('/srv/pico/example.png').write_bytes(image)
print('PASS: wrote /srv/pico/example.png (64 by 64 red image)')
PNG
python3 - <<'IMAGE'
import base64, json
from pathlib import Path
url = 'data:image/png;base64,' + base64.b64encode(Path('/srv/pico/example.png').read_bytes()).decode()
request = {'model':'deepseek-v4.1-flash','messages':[{'role':'user','content':[
    {'type':'text','text':'Describe this image.'},
    {'type':'image_url','image_url':{'url':url}}]}],'max_tokens':512}
Path('/srv/pico/image-request.json').write_text(json.dumps(request))
print('PASS: wrote image request')
IMAGE
curl --fail-with-body --max-time 300 http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' --data-binary @/srv/pico/image-request.json \
  > /srv/pico/image-response.json
python3 - <<'VISION'
import json
from pathlib import Path
result = json.loads(Path('/srv/pico/image-response.json').read_text())
assert not result.get('error'), result.get('error')
answer = result['choices'][0]['message'].get('content') or ''
assert answer, 'No final image answer; inspect response/finish reason before continuing'
print(answer)
assert 'red' in answer.lower(), 'Expected a description of the red image; inspect answer'
print('PASS: image answer mentions red')
VISION
```

**Verify:** image generation prints its PASS line, curl exits zero, and the final
answer describes the red image. The word check is only a simple example check,
not proof of broad vision quality. JSON includes both text and `image_url` parts;
base64 is a way to embed file bytes as text in that request. Small PNG, JPEG or
WEBP images can be sent this way; these are standard compressed image formats.
Bounded public HTTP(S) image URLs also work, but embedding bytes avoids download
permissions or remote-server failures. HTTPS is HTTP with encrypted transport.

For streaming, add `"stream":true` to the JSON and use `curl -N` to avoid holding
output in a client buffer. The response then arrives as **SSE** (server-sent events:
a series of `data:` lines), not a single JSON object; do not pass it to the single-
response parser above. Image conversations are re-encoded each turn and do not
reuse saved image-prefix computations. Rank 0 handles one image-encoding operation
at a time and shares the resulting numerical rows with all ranks. Limits include
16 images and 1024 rows per image, plus byte, pixel and queue bounds. No audio,
video, image-generation route or special raw model placeholders are required.

### 8. Stop, resume and roll back — all four nodes

To stop without deleting weights, the container or saved sessions, run on **all four**:

```bash
docker stop --time 120 pico
docker inspect pico --format '{{.State.Running}}'
```

**Verify:** every node prints **`false`**. Do not delete `/srv/pico/spill`: it holds
saved sessions. Requests running at stop time can be interrupted; stop during an
agreed idle window. Do not stop just one worker and expect the ring to serve.
To resume the **same** installation, run `docker start pico` on all four, then
repeat steps 5–7. `docker start` preserves its saved launch options and image.

#### Save a rollback before an upgrade

A rollback means returning to the exact previous tested installation, not pulling
a tag whose contents may have changed. For a first installation there is **no
previous serving version**; stopping is not the same as restoring a healthy server.
Before replacing an already tested `pico`, save it on every node as follows. This
is a future upgrade procedure, not an instruction to interrupt an existing service
just to follow this README.

```bash
set -euo pipefail
if docker container inspect pico-rollback >/dev/null 2>&1; then
  echo 'STOP: a rollback container already exists; review it, do not overwrite it' >&2
  exit 1
fi
docker inspect pico --format '{{.Image}}' > /srv/pico/rollback-image-id.txt
docker stop --time 120 pico
docker rename pico pico-rollback
docker inspect pico-rollback --format '{{.State.Running}}'
```

**Verify:** all four saved containers print `false`; their image IDs remain in
`/srv/pico/rollback-image-id.txt`. Keep their images and any incompatible old asset
versions until the new version is accepted. This upgrade must not overwrite their
model files. If a future release changes the saved-session format, require an
explicit compatibility/backup plan before upgrading; compatibility is not assumed.

To undo a failed replacement **when that saved rollback exists**, run the first
block on all four nodes before starting any old rank:

```bash
set -euo pipefail
docker inspect pico-rollback >/dev/null
if docker container inspect pico-candidate-stopped >/dev/null 2>&1; then
  echo 'STOP: inspect existing pico-candidate-stopped before reusing that name' >&2
  exit 1
fi
docker stop --time 120 pico
docker rename pico pico-candidate-stopped
docker rename pico-rollback pico
test "$(docker inspect pico --format '{{.Image}}')" = "$(cat /srv/pico/rollback-image-id.txt)"
```

Then run **`docker start pico` on every node**, and repeat the readiness and real
request checks in steps 5–7. **Verify:** health is `ok`, text and image requests
succeed, and image IDs match the saved record. If no new `pico` was created, skip
its stop/rename lines and just restore `pico-rollback` to `pico`; do not delete
containers, images, model data or session data as a recovery shortcut.

## Steering (ON by default)

Use **`--steering glp39` on every rank**; alpha is **0.75**, zero-based layers
**1–39**. To opt out explicitly, replace it with **`--steering off` on every rank**
when creating the containers, not merely in a later shell environment.
The pinned public image predates this recipe default; its embedded launcher defaults
to OFF when the flag is omitted. The explicit flag enables GLP-39 without changing
the immutable image. New builds use the in-repo ON default. The vector author is
**msuiche**, MIT. [Mechanics, provenance and tradeoffs](docs/steering.md).

## Troubleshooting

Stop at the failed step; do not keep restarting a broken ring. Run commands on the
node showing the problem unless the row says all four. Unknown causes require log
inspection, not a guessed host change.

| Symptom | Plain-language cause/check | Exact recovery action |
|---|---|---|
| Image pull denied or interrupted | Wrong image name/digest, no route, or full image disk. The artifact is public. | Set `IMAGE=$(cat /srv/pico/image.ref)` and run `docker pull --platform linux/arm64 "$IMAGE"` after checking `df -h` and registry reachability. If the reference file was never created, copy the exact value from the quick path first. Do not substitute a private image. |
| Container name already in use | A previous installation or stopped attempt already exists. | Run `docker inspect pico --format '{{.State.Running}} {{.Image}}'`; use step 8 to resume it or save a rollback. Do not remove it blindly. |
| Rank waits; health never becomes `ok` | A peer is absent or the direct network plan is wrong. | Run `docker ps -a --filter name=pico` and `docker logs --tail 100 pico` on all four; check their unique `/srv/pico/rank` values. Stop all four with `docker stop --time 120 pico`, correct the approved fleet/port input and repeat setup step 7, then run `docker start pico` on all four and recheck health. |
| File hash/profile mismatch | An incomplete copy, wrong revision or mixed binary/asset set. | Run `(cd /srv/pico/model && sha256sum -c SHA256SUMS)`; repeat setup step 5's `rsync` for the failed files, then rerun hashes. For packaged runtime mismatches, re-pull the pinned image; do not edit expected hashes. |
| GPU/RDMA permission or memory registration failure | The container cannot access the GPU/network device, or the kernel cannot register memory. | Repeat setup step 6's one-shot GPU check and `ibv_devinfo`; restore the documented device/memory-lock flags. For a kernel registration error, stop and use vendor kernel guidance; never add `--privileged` or change boot options speculatively. |
| Disk guard or allocation error | Model/image/session data left too little free space. | Run `df -B1 /srv/pico/model /srv/pico/spill`; add capacity or move unrelated data through a reviewed plan. Repeat setup step 6's storage check for a fresh install. Do not shrink the 160 GiB reserve or delete saved sessions. |
| Image request rejected or encoder exits | Unsupported/oversized input, full image queue, or missing encoder assets. | First use step 7's generated small PNG and inspect `docker logs --tail 100 pico` on rank 0. Wait for the queue to clear; use the bounded example request. If it still fails, stop and inspect the exact error rather than disabling image validation. |
| Slow first answer | Input length, other users or cached work affect waiting time. | Run one bounded example request with `curl --max-time` as above and inspect active load. Compare against the published first-token caveat, not decode speed alone; do not wipe sessions to force a speed result. |

## Unofficial and licensed

No affiliation with, sponsorship by or endorsement from **DeepSeek** exists.
This is not an official DeepSeek or NVIDIA package. MIT is the permissive license
used by this engine/model/vector line; retain its attribution and license text.
Credit: **Andy Shu and Picom** (engine), **DeepSeek** (model/native vision),
**msuiche** (vector), and ofan (recipe). Preserve [LICENSE](LICENSE), [NOTICE](NOTICE),
`licenses/` and included upstream notices; other dependencies retain their own licenses.
See [build instructions](docs/build.md), [measurement details](docs/benchmarks.md)
and [completion/qualification status](docs/completion-report.md) before adapting
this into an unattended service.
