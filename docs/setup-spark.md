# Prepare four Sparks, one step at a time

This guide prepares **your own idle machines**. It does not operate a remote group of machines.
Do not paste host-changing commands onto an already serving machine. Use Bash for
all command blocks: run `bash` first. Commands using `sudo` need your administrator's
approval. Stop on any failed verification; do not continue by removing a check.

## Words used in this guide

- A **GPU** is the processor that does the model's calculations; GB10 is the chip in a Spark.
- **ARM64**, reported as `aarch64`, is the processor type these binaries require.
- **Tensor parallel (TP4)** means splitting one model's calculations across all four GPUs.
- A **rank** is one of those four workers, numbered 0, 1, 2 and 3; a **node** is its machine.
- **QSFP** is the connector family used by the high-speed network cables.
- A **RoCE ring** is a direct loop of network links that lets the GPUs exchange memory without an ordinary network switch.
- **RDMA** is that direct memory transfer; **native verbs** are the low-level network operations Pico uses for it.
- A **network interface** is a named network connection; a **device** here is its RDMA adapter name.
- A **domain** is one of the two independent network paths used in each direction.
- A **CIDR** value is a network address followed by the number of bits identifying its network, written as an address and a suffix such as `/30`.
- A **GID index** selects an address entry on an RDMA device; **RoCEv2** is the address type required here.
- **MTU** is the largest network packet size allowed on a link, in bytes.
- **GHCR** is GitHub Container Registry, the service hosting the downloadable image.
- A **container image** is a packaged program; a **container** is a running instance of it.
- An image **digest** is a content checksum; pinning it prevents a tag change from changing what you run.
- The **engine** executes the model; the **frontend** translates web requests for it.
- A **subnet** is the group of addresses sharing one network link.
- A **checkpoint** is the publisher's model files; **weights** are the model's learned numerical values.
- An **Engram shard** is a rank's part of the model's on-disk lookup tables.
- A **tokenizer** turns text into the small pieces, called tokens, that the model processes.
- A **steering vector** is a file that changes selected internal activations without changing the checkpoint.
- **Alpha** sets steering strength; **layers 1–39** are the selected internal stages, counted from zero.
- A **hash** is a checksum used to detect a changed file; a **receipt** records expected hashes and source versions.
- **GiB** means 1,073,741,824 bytes; **NVMe** is the fast local disk used for model files and saved sessions.
- **Spill** is the saved-session disk area; it is not extra GPU memory.
- **Firmware** is software inside a network adapter; the **kernel** is the operating system's core, and a memory **page** is a fixed-size block it manages.
- **CUDA** is NVIDIA's GPU programming toolkit; **CMake**, **g++** and **Cargo** are build tools.
- **HTTP** is the web request protocol; an **endpoint** is a URL receiving those requests.

## Before step 1: collect the inputs

Have everything in the [README prerequisites](../README.md#prerequisites--before-step-1).
In particular, someone who can identify the physical ports must supply the following.
An unattended agent **must stop if any value is unknown**; it must not invent addresses,
choose a GID by position, change a boot setting, or treat the management connection
as a fabric port.

| Input | Required value |
|---|---|
| Machine order | Four distinct machines assigned ranks 0, 1, 2, 3; record each machine's exact `hostname` output. |
| Copy destinations | Four SSH login destinations, in rank order; SSH is encrypted remote command/file access. |
| Cabling | Direct QSFP connections for next/previous neighbors on both domains, mapped by the owner. |
| Local ports | Four interface names and four associated RDMA device names per machine. |
| Addresses | Each local port's CIDR, its neighbor's address, and one matching RoCEv2 GID index common to the selected devices on all machines. |
| Access | Administrator permission, working Docker access, internet access to GitHub/GHCR and the official checkpoint. |
| Storage | Empty first-install destinations with capacity for the actual files plus the reserves below; never delete existing assets to make this guide fit. |

The network plan is installation-specific and is **not distributed**. This guide
provides commands to apply and check an approved plan, not a fabricated plan.
The public image's **four-rank GPU serving qualification is pending**: successful
host checks below do not turn that into a qualification claim.

## 1. Check the installed operating system and tools — every Spark

Use NVIDIA's [DGX Spark software documentation](https://docs.nvidia.com/dgx/dgx-spark/)
to install or update the supported operating system and GPU driver **before** this
guide. Configure Docker with NVIDIA's [Container Toolkit instructions](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
Driver installation and any required reboot are a separate host-preparation task;
this guide does not replace vendor installation instructions with guessed packages.
Docker commands must work for your current account; do not bypass access failures
with a blanket privileged container.

```bash
set -euo pipefail
uname -m
. /etc/os-release; printf '%s\n' "$PRETTY_NAME"
uname -r
getconf PAGESIZE
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
docker version --format '{{.Server.Version}}'
docker info --format '{{json .Runtimes}}'
python3 --version
```

**Verify:** `uname -m` must print `aarch64`; the GPU must be GB10 and Docker must
return a server version without an access error. Docker's runtime list must contain
`nvidia`. Recorded compatibility baseline: NVIDIA DGX OS / Ubuntu **24.04.4 LTS**,
kernel **7.0.0-1019-nvidia-64k**, **65,536-byte pages**, driver **580.178.04**, and
ConnectX-7 firmware **28.45.4028**. These are historical tested versions, not a
requirement to downgrade a newer vendor-supported installation. No exact Docker
or Container Toolkit version was recorded, so no claim is made that an arbitrary
version is tested. If your versions differ, keep a record and qualify them locally.

Install the ordinary command-line utilities used below on Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv rsync openssh-client rdma-core ibverbs-utils nano
command -v git curl python3 rsync ibv_devinfo rdma
```

**Verify:** the last command prints a path for each of the six programs and exits
zero. Check that NVIDIA Container Toolkit installation succeeded by running the
image GPU check in step 6; the version checks alone do not test container access.

## 2. Create fixed directories and clone the recipe — build host and every Spark

The **build host** is a separate, non-serving ARM64 machine used to compile tools
and convert weights. It can use the same directory layout without being a rank.
The following commands refuse a second clone rather than overwriting your work.

```bash
sudo install -d -o "$(id -u)" -g "$(id -g)" /srv/pico /srv/pico/model /srv/pico/spill /srv/pico/tools
cd /srv/pico
test ! -e recipe
git clone https://github.com/ofan/deepseek-v41-flash-spark.git recipe
cd /srv/pico/recipe
python3 -B scripts/verify-patches.py
```

**Verify:** `git -C /srv/pico/recipe remote get-url origin` prints
`https://github.com/ofan/deepseek-v41-flash-spark.git`; the patch checker exits zero.
If `recipe` already exists, inspect `git -C /srv/pico/recipe status --short` and its
commit instead of cloning over it. Record one commit and use that same commit on
the build host and all four Sparks; do not update the recipe halfway through setup.

## 3. Cable, configure and check the ring — every Spark

Label the four machines **0 → 1 → 2 → 3 → 0**. In each of the two domains, connect
a rank's NEXT port to the next rank's PREV port. QSFP cable assembly/breakout details
depend on the hardware: use the owner's port map and supported cables, not an
assumed connector-to-device ordering. This is not the ordinary management network.

Identify your ports without changing them:

```bash
hostname
ip -br link
ip -br address
rdma link show
ibv_devinfo
```

**Verify:** match every physical cable to its interface and RDMA device; the selected
links must show `ACTIVE` / `LINK_UP`. Stop if any mapping is unknown. The firmware
version is shown by `ibv_devinfo` as `fw_ver`.

On each node, create `/srv/pico/ports.env` from this template and replace every
`REPLACE_...` value with the approved **local** input. `IF` is an interface name,
`CIDR` its address/prefix, `PEER` the neighbor's address. This file is local data,
not a file to commit to this public repository.

```bash
set -euo pipefail
test ! -e /srv/pico/ports.env
cat > /srv/pico/ports.env <<'PORTS'
NEXT_IF0=REPLACE_NEXT_IF0
NEXT_CIDR0=REPLACE_NEXT_CIDR0
NEXT_PEER0=REPLACE_NEXT_PEER0
NEXT_IF1=REPLACE_NEXT_IF1
NEXT_CIDR1=REPLACE_NEXT_CIDR1
NEXT_PEER1=REPLACE_NEXT_PEER1
PREV_IF0=REPLACE_PREV_IF0
PREV_CIDR0=REPLACE_PREV_CIDR0
PREV_PEER0=REPLACE_PREV_PEER0
PREV_IF1=REPLACE_PREV_IF1
PREV_CIDR1=REPLACE_PREV_CIDR1
PREV_PEER1=REPLACE_PREV_PEER1
PORTS
nano /srv/pico/ports.env
```

If `nano` is absent, use your editor or have your automation write this exact schema.
Review this shell input file before sourcing it: it must contain only assignments
you trust. **Do not run the next block over the only management connection if any
selected interface carries it.** Have console/recovery access. The changes below
last until reboot; after validation, use your vendor-supported network manager to
persist this same plan. Do not change the management interface or global network rules.

```bash
set -euo pipefail
if grep -n 'REPLACE_' /srv/pico/ports.env; then
  echo 'STOP: fill every local port input first' >&2; exit 1
fi
. /srv/pico/ports.env
for direction in NEXT PREV; do
  for domain in 0 1; do
    ifkey="${direction}_IF${domain}"; cidrkey="${direction}_CIDR${domain}"
    dev=${!ifkey}; cidr=${!cidrkey}
    sudo ip link set dev "$dev" mtu 9000 up
    sudo ip address replace "$cidr" dev "$dev"
  done
done
echo 'PASS: local port configuration commands completed'
```

**Verify:** the block prints its PASS line. **Complete this block on all four
nodes before the next block**: a neighbor not yet configured cannot answer. Then
check every link on each node:

```bash
set -euo pipefail
. /srv/pico/ports.env
for direction in NEXT PREV; do
  for domain in 0 1; do
    ifkey="${direction}_IF${domain}"; peerkey="${direction}_PEER${domain}"
    dev=${!ifkey}; peer=${!peerkey}
    ping -I "$dev" -c 3 -W 3 -M do -s 8972 "$peer"
  done
done
rdma link show
```

**Verify:** every ping reports
`0% packet loss` and every selected RDMA link reports `ACTIVE` / `LINK_UP`.
The ping size tests a 9000-byte IPv4 path. This alone does not prove GPU communication.

List address entries for the GID choice after addressing:

```bash
for port in /sys/class/infiniband/*/ports/1; do
  for gid in "$port"/gids/*; do
    idx=${gid##*/}
    printf '%s index=%s address=%s type=%s interface=%s\n' \
      "$port" "$idx" "$(cat "$gid")" \
      "$(cat "$port/gid_attrs/types/$idx")" \
      "$(cat "$port/gid_attrs/ndevs/$idx")"
  done
done
```

**Verify:** the chosen index has type `RoCE v2`, the planned interface and the
corresponding planned address on every chosen device. The four nodes must use the
same device names for NEXT/PREV in this engine's schema and a common GID index.
If they do not, stop and resolve that mismatch; do not copy a number from another
installation. Step 7 checks this with the actual engine network library.

## 4. Build converters and prepare verified model files — build host only

Keep the serving Sparks idle; no compiling or converting on a serving node.
Build prerequisites: **CUDA 13.0** at `/usr/local/cuda-13.0`, **CMake 3.28+**,
**g++ 13.3 / C++20**, **Python 3.12**, and a Rust toolchain (recorded Cargo **1.97**).
C++20 is the compiler language version. Install CUDA/Rust using their publishers'
ARM64 instructions before running this block; a different toolchain needs local
qualification, not a claim of exact production binary reproduction.

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libibverbs-dev pkg-config libssl-dev python3-venv git curl rsync openssh-client nano
/usr/local/cuda-13.0/bin/nvcc --version
cmake --version
g++ --version
cargo --version
cd /srv/pico/recipe
bash scripts/fetch-sources.sh
bash scripts/build-engine.sh
```

**Verify:** the version commands meet the requirements above. `fetch-sources.sh`
prints `Staged engine/frontend from pinned vendored source; no network fetch.`
The build prints `Source build complete.` followed by its qualification caveat;
`test -s /srv/pico/recipe/work/compiled/source-build.json` must exit zero.
The build stages engine source included in this repository; it does not fetch a
separate private fork. If `work/source` already exists, verify it rather than
running the first-time staging command again:
`python3 -B scripts/source_tree.py --verify work/source/engine`.

Download the official checkpoint. Hugging Face is the publisher's model download
service. The CLI (command-line interface) below is installed in an isolated Python environment so the
operating system Python is not changed. If the publisher requires an account,
accept its terms and use `work/download-env/bin/hf auth login` locally after installing the CLI; never paste credentials into
commands, documents or the repository. HLE (Humanity's Last Exam) is an optional quality test; its dataset access is
**not required for serving**.

```bash
cd /srv/pico/recipe
python3 -m venv work/download-env
work/download-env/bin/python -m pip install huggingface_hub
df -B1 /srv/pico/recipe
work/download-env/bin/hf download deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --dry-run
# Review the download size and disk budget before the real download.
work/download-env/bin/hf download deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --local-dir work/checkpoint
python3 -B scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170
python3 -B scripts/convert-assets.py --checkpoint work/checkpoint \
  --checkpoint-revision 1bae0e1088993b9b82de08f59de5be5a34e42170 --execute
```

**Verify:** download exits zero at that revision; conversion ends with
`All four ranks verified; conversion and Engram materialization complete. See work/conversion-logs.`
Then run:

```bash
cd /srv/pico/recipe
python3 - <<'CHECK'
import json
from pathlib import Path
r = json.loads(Path('bundle/model/asset-hashes.json').read_text())
assert r['revision'] == '1bae0e1088993b9b82de08f59de5be5a34e42170'
assert r['all_conversion_commands_exit_zero'] is True
assert r['all_verification_commands_exit_zero'] is True
for n in range(4):
    for name in (f'rank{n}.dsw', f'engram-l1-r{n}of4.bin', f'engram-l14-r{n}of4.bin'):
        assert name in r['sha256'], name
print('PASS: all four conversions and verifications complete')
CHECK
```

The converter refuses an existing output directory. Do not delete existing verified
weights to work around that protection: [reuse existing receipts](build.md#prepare-the-text-assets)
with `--reuse --execute`, or choose a new empty output with `--output` and consistently
substitute it below. Download, converted output and temporary files coexist; keep
space for all of them. There is no measured fixed build-host disk requirement in
this repository. Measure the actual download and conversion plan before allocating
space; do not equate the model's memory size with its disk size.

## 5. Complete the fleet file and copy only each rank's assets — build host

### Fleet file

```bash
set -euo pipefail
cd /srv/pico/recipe
test ! -e /srv/pico/fleet.conf
cp examples/fleet.conf.example /srv/pico/fleet.conf
nano /srv/pico/fleet.conf
```

The fleet file is the shared list of network and file locations. Replace **every**
`REPLACE_...` value. Use exactly one `KEY=value` per line, no quotes or spaces in
values; `#` starts a comment. This is not a runnable example network.

| Keys | What to enter |
|---|---|
| `NEXT_DEV0/1`, `PREV_DEV0/1` | RDMA device names, not interface names, from step 3; identical names across the ring. |
| `GID_INDEX` | The common RoCEv2 index verified in step 3. |
| `RANKr_NEXT_IP0/1`, `RANKr_PREV_IP0/1` | Rank r's **own** port addresses, without CIDR suffix, not its neighbor's addresses. |
| `RANKr_HOSTNAME` | That machine's exact `hostname` output; use it for local rank identification below. |
| `RANKr_NAME` | A unique plain label, for example `rank0`, `rank1`, `rank2`, `rank3`. |
| `RANKr_SSH` | Your remote login destination for that machine; the container launcher itself does not use SSH. |
| `RANKr_WEIGHTS/HASHMAP/ENGRAM/SPILL` | Keep the template's `/opt/package/model/...` and `/var/lib/pico` paths: these are paths **inside** the container. |
| `BIN_DIR/LOG_DIR/SERVICE_DIR/RING_LOCK` | Keep template values; native helper programs use them. |

Rank r's NEXT address and the next rank's PREV address (wrap from rank 3 to rank 0) must be on the same
subnet for each domain. TCP is the reliable network transport used to establish connections. Permit its
connection-establishment port **18620** (a service number, not a physical socket)
between ring peers and RoCE traffic on the direct links; do not open this port to
the internet. This recipe does not flush firewalls or configure an ordinary switch.

**Verify:** run the following; success is exactly `PASS: fleet fields filled`.
Step 7 is the authoritative parser/address/communication check, not this text check.

```bash
if grep -nE '^[^#]*REPLACE_' /srv/pico/fleet.conf; then
  echo 'STOP: fill every fleet field first' >&2; exit 1
fi
echo 'PASS: fleet fields filled'
```

### Deployment list and checksums

Create a private local list with exactly four lines: each is the SSH destination
for rank 0, 1, 2, 3 in order. Store it as `/srv/pico/nodes.txt`. Do not commit it.
The following copy loop uses it without guessing a machine's rank.

```bash
set -euo pipefail
nano /srv/pico/nodes.txt
cd /srv/pico/recipe
mkdir -p work/deploy
python3 - <<'LISTS'
import json
from pathlib import Path
receipt = json.loads(Path('bundle/model/asset-hashes.json').read_text())
for rank in range(4):
    names = [f'rank{rank}.dsw', f'engram-l1-r{rank}of4.bin',
             f'engram-l14-r{rank}of4.bin', 'engram_hashmap.bin']
    names += sorted(n for n in receipt['sha256'] if n.endswith('.json'))
    assert 'tokenizer.json' in names and 'config.json' in names
    assert all(Path(n).name == n for n in names)
    out = Path('work/deploy')
    (out / f'rank{rank}.files').write_text(''.join(n + '\n' for n in names))
    (out / f'rank{rank}.sha256').write_text(''.join(receipt['sha256'][n] + '  ' + n + '\n' for n in names))
    size = sum((Path('bundle/model') / n).stat().st_size for n in names)
    (out / f'rank{rank}.bytes').write_text(str(size) + '\n')
    print(f'rank {rank}: {size} asset bytes; reserve another {192 * 2**30} bytes after staging')
LISTS
python3 - <<'DESTINATIONS'
from pathlib import Path
nodes = Path('/srv/pico/nodes.txt').read_text().splitlines()
fleet = dict(line.split('=', 1) for line in Path('/srv/pico/fleet.conf').read_text().splitlines()
             if line and not line.startswith('#'))
assert len(nodes) == 4 and len(set(nodes)) == 4
assert all(nodes[n] == fleet[f'RANK{n}_SSH'] for n in range(4)), 'Copy list must match fleet ranks'
assert len({fleet[f'RANK{n}_HOSTNAME'] for n in range(4)}) == 4
assert all(n and not any(c.isspace() for c in n) and not n.startswith('-') and 'REPLACE_' not in n for n in nodes)
print('PASS: four distinct destinations match the fleet rank order')
DESTINATIONS
mapfile -t NODES < /srv/pico/nodes.txt
test "${#NODES[@]}" -eq 4
for RANK in 0 1 2 3; do
  NODE=${NODES[$RANK]}
  test -n "$NODE" && test "${NODE#-}" = "$NODE" && test "${NODE#*REPLACE_}" = "$NODE"
  ssh "$NODE" 'test -d /srv/pico/model && test -d /srv/pico/tools'
  test "$(ssh "$NODE" git -C /srv/pico/recipe rev-parse HEAD)" = "$(git rev-parse HEAD)"
  # Check capacity before copying; IMAGE will be pulled separately in step 6.
  BYTES=$(cat "work/deploy/rank${RANK}.bytes")
  ssh "$NODE" python3 - "$BYTES" <<'CAPACITY'
import shutil, sys
assert shutil.disk_usage('/srv/pico/model').free >= int(sys.argv[1]) + 192 * 2**30
print('PASS: model staging capacity')
CAPACITY
  rsync -a --partial --files-from="work/deploy/rank${RANK}.files" bundle/model/ "$NODE:/srv/pico/model/"
  rsync -a "work/deploy/rank${RANK}.sha256" "$NODE:/srv/pico/model/SHA256SUMS"
  rsync -a work/compiled/engine/comm/ring_test "$NODE:/srv/pico/tools/ring_test"
  rsync -a /srv/pico/fleet.conf "$NODE:/srv/pico/fleet.conf"
  ssh "$NODE" 'cd /srv/pico/model && sha256sum -c SHA256SUMS'
done
```

**Verify:** the copy loop also requires each clone to match the build-host commit.
If it does not, stop and check the local work before updating that clone; do not
force-update it. Every checksum line must end `OK`, all commands exit zero, and each node has
only its own large rank file and two Engram shards plus the common files. Keep the
original receipts on the build host. `rsync --partial` retains an interrupted copy
for resumption; do not interpret its partial file as verified. Rerun the checksums.

## 6. Pull and verify the runtime — every Spark

```bash
set -euo pipefail
IMAGE=ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4@sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
docker pull --platform linux/arm64 "$IMAGE"
printf '%s\n' "$IMAGE" > /srv/pico/image.ref
docker image inspect "$IMAGE" --format '{{.Architecture}} {{json .RepoDigests}}'
docker run --rm --gpus all --entrypoint nvidia-smi "$IMAGE" --query-gpu=name --format=csv,noheader
```

**Verify:** pull/inspect shows digest
`sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979`,
architecture `arm64`, and the one-shot GPU check prints `NVIDIA GB10`. No GHCR login
is required. That check does not load the model or qualify the vision encoder.

**Storage check after the pull and asset copy:** the model files and image already
occupy space. Leave **160 GiB** for saved sessions and at least **32 GiB** free beyond
that on each node. They are reserves in addition to assets, not the total disk size.
The next check assumes a fresh empty spill directory; if preserving sessions, count
their existing use as part of the 160 GiB budget instead of deleting them.

```bash
python3 - <<'SPACE'
import shutil
from pathlib import Path
model, spill = Path('/srv/pico/model'), Path('/srv/pico/spill')
assert model.stat().st_dev == spill.stat().st_dev, 'Different disks: calculate both budgets separately; stop here'
assert not any(spill.iterdir()), 'Existing sessions: preserve them and review remaining spill budget; stop here'
free = shutil.disk_usage(spill).free
assert free >= 192 * 2**30, 'Need 160 GiB session reserve plus 32 GiB guard after staging'
print('PASS: at least 192 GiB free after model and runtime staging')
SPACE
docker info --format '{{.DockerRootDir}}'
docker image inspect "$(cat /srv/pico/image.ref)" --format '{{.Size}}'
```

**Verify:** the script prints the PASS line. The last two commands identify Docker's
image-storage location and actual unpacked image size in bytes; if that directory
is on a separate filesystem, also check `df -B1` for that location. Size the disk
before downloading, including temporary pull space. There is no supported smaller
spill setting in this recipe. A full-session disk and a full Docker disk both block startup.

## 7. Verify GPU communication — all four, before model launch

On **each node**, save the rank selected by its hostname, then run the same test
within 120 seconds of the other nodes. Use four terminals, or an agent can start
four independent remote commands and wait for all four. Do not run it alongside a
model using the same GPU/ring. A maximum 300-second test deadline prevents waiting
indefinitely for an absent peer.

```bash
python3 - <<'RANK'
from pathlib import Path
import socket
items = {}
for line in Path('/srv/pico/fleet.conf').read_text().splitlines():
    line = line.split('#', 1)[0].strip()
    if line:
        key, value = line.split('=', 1)
        assert key not in items and value and 'REPLACE_' not in value
        items[key] = value
matches = [n for n in range(4) if items[f'RANK{n}_HOSTNAME'] == socket.gethostname()]
assert len(matches) == 1, 'Need exactly one hostname match; do not guess rank'
Path('/srv/pico/rank').write_text(str(matches[0]) + '\n')
print(f'PASS: this node is rank {matches[0]}')
RANK
set -o pipefail
RANK=$(cat /srv/pico/rank)
IMAGE=$(cat /srv/pico/image.ref)
if docker container inspect pico-ring-check >/dev/null 2>&1; then
  echo 'STOP: inspect existing pico-ring-check before repeating a test' >&2; exit 1
fi
timeout 300 docker run --rm --name pico-ring-check --network host --gpus all \
  --device /dev/infiniband --ulimit memlock=-1:-1 --cap-add IPC_LOCK \
  --mount type=bind,src=/srv/pico/fleet.conf,dst=/etc/pico/fleet.conf,readonly \
  --mount type=bind,src=/srv/pico/tools/ring_test,dst=/opt/check/ring_test,readonly \
  --entrypoint /opt/check/ring_test "$IMAGE" \
  --fleet /etc/pico/fleet.conf --rank "$RANK" correct | tee /srv/pico/ring-test.log
grep -E "rank ${RANK}: passed;" /srv/pico/ring-test.log
```

**Verify:** each test exits zero and its final summary contains `rank N: passed;`.
`correct` is an existing communication correctness test, not a speed or full-model
qualification. If a timeout leaves the check container, run `docker inspect pico-ring-check`
and `docker stop --time 10 pico-ring-check` on that node before retrying. Its
`--rm` flag removes it when stopped; never bulk-delete containers.
An RDMA registration error on the recorded kernel needed `kho=off` (a kernel boot
option); seek your vendor's kernel guidance, do not change boot options automatically.

## 8. Start and use the stack

Continue with [README guided step 4](../README.md#4-start-all-four-ranks).
Its launch, health, text, image, stop and rollback commands are the serving contract.
Keep **GLP-39 ON by default, alpha 0.75, layers 1–39**: explicitly pass
`--steering glp39` on every rank. Explicit `--steering off` on every rank is the
opt-out. The immutable published image predates the default change; its embedded
launcher omits steering unless the flag is given. New source builds default ON.

**Verify on every node:** `docker inspect pico --format '{{.State.Running}} {{.RestartCount}} {{.State.OOMKilled}}'`
must print `true 0 false`. On rank 0, `curl --fail http://127.0.0.1:8888/health`
must print `ok`; then run the README's real text and image checks. Do not treat
container status alone as serving proof.

## Optional tuning — not required commands for first launch

- **Graphics clock cap:** a maximum GPU calculation frequency. Production's recorded
  cap is **2,200 MHz**; its command is `sudo nvidia-smi -lgc 0,2200` on each node.
  Apply it only if you choose the same clock policy, with no competing controller;
  verify that the command reports successful locked-clock configuration. Current
  idle clock readings alone do not prove a lock. The report sampled roughly
  **2,190 MHz**; power limit was **N/A**, not a measured wattage cap.
  [Recorded clock evidence](benchmarks/2026-11-13-gpu-cap.json).
- **TCP**, the reliable network transport used for connection setup, had an optional
  management-network workaround: `net.ipv4.tcp_sack=0` disabled selective resend
  acknowledgments, and EEE (Energy Efficient Ethernet) was disabled on that interface.
  This was **not proven to eliminate receive misses**; do not apply it generally.
  Recorded optional values also included `net.mptcp.enabled=0` (disable multi-path
  TCP) and `net.ipv4.tcp_migrate_req=0` (do not move pending TCP requests).
- **Fabric packet handling:** recorded interface-scoped `arp_ignore / arp_announce /
  rp_filter` values were **1 / 2 / 2**. These control address replies and source-path
  validation. Do not set them globally without an approved network plan.
- Pico uses its own RDMA operations, not **NCCL** (NVIDIA's collective communication
  library). Settings for switched network congestion control are not a substitute
  for direct-link validation. No specific TCP buffer sizes are established here.

## Vision and session notes

The **vision tower** is the model component that turns images into numbers. Rank 0
runs it and shares the resulting **embedding spans** (rows of those numbers) with
all ranks. Keep `VISION_SDPA_OPT_IN=0` (the tested image calculation path) and
serialized encoding (one encoder operation at a time). BF16 is a 16-bit number
format: **0.904 GiB** counts only BF16 tower weights, not all runtime memory.
The historical six-fixture check passed **88/88 OFF and 88/88 GLP-39**; it does not
qualify a new runtime. Image-bearing conversations are re-encoded, not restored
from a saved image-prefix cache. A cache is previously computed work reused later.
Keep `/srv/pico/spill` intact when stopping or rolling back.

## Evidence sources and limits

These are provenance references, not files a public user must obtain to run:

- Homeinfra `hosts/spark1/README.md`, `hosts/spark3/README.md`: hardware and OS history.
- `spark-al-engr-20261106/result.md`, `before-diff.md`: kernel, pages, driver,
  clock policy and network history.
- `owen-4k-campaign-20261026.md`: bounded management-network workaround and its limits.
- `pico-session-cache-fix-20261106/README.md`: spill reserve and free-space guard.
- Homeinfra `cf6e8b67c`, `pico-image-support-20261111/retrial-spark-only/REPORT.md`:
  accepted production vision checks; see [benchmarks](benchmarks.md).

Public documentation and offline tests do not prove a stranger's cabling, kernel,
converted checkpoint or newly built runtime. Do not call the public candidate
GPU-qualified until it passes the four-rank serving checks on the target machines.
