# First-time reader and unattended-agent review

Scope: README and setup instructions only; no deployment, GPU operation, image
build, clock change, model download or production request was performed for this
rewrite. The public candidate remains GPU-unqualified. Steering remains **ON by
default, GLP-39 alpha 0.75, layers 1–39**, with explicit OFF on every rank available.

## Cold-read pass: missing knowledge found and supplied

Read in order: introduction → prerequisites → quick path → measurements/quality →
guided preparation → launch → readiness → text/image use → stop/resume/rollback →
troubleshooting. The linked setup guide was checked in its numbered order too.

| Gap found | Fix in the documents |
|---|---|
| Specialist terms were assumed. | Plain definitions cover tokens/context, workers/ranks, TP4, RoCE/QSFP/RDMA, GHCR, steering, prefill/decode, latency and the benchmark labels. |
| Machine roles and account/software requirements were implicit. | Separate build-host and per-node commands; an up-front checklist; vendor driver/toolkit handoff, version checks and utility-install commands. Historical versions are not called universal minimums. |
| Site-specific wiring and address choices looked inferable from examples. | Explicit owner-supplied input table, next/previous topology, local-port file, link/large-packet/GID checks; agents stop on missing values. |
| Template checks could mistake a comment for an unfilled value. | Fleet placeholder check ignores comment lines; actual unresolved values stop the procedure. |
| Shell checks could continue after an inverted grep failure. | Explicit stop-on-placeholder branches and Bash error/pipe handling; no bypassing failed checks. |
| No exact first-time download/conversion sequence or account boundary. | Isolated download CLI, pinned official revision, dry-run size check, converter/verifier commands and successful receipt checks. HLE is explicitly not needed to serve. |
| Disk reserve could be mistaken for the entire disk requirement. | Actual per-rank byte calculation, model-copy capacity check, runtime size/location commands and post-staging 160 + 32 GiB reserve check. Existing sessions are never deleted. |
| File distribution and post-copy verification were left to the reader. | Per-rank file/checksum lists, four-destination validation against the fleet file, same-recipe-commit check, resumable copy commands and destination hash verification. |
| A combined network configure/probe loop could stop before other nodes had addresses. | Separate apply and probe passes with an explicit all-node barrier; no manual line-picking or timing guess is needed. |
| Rank assignment and communication-test invocation were unspecified. | Exactly one hostname match writes the local rank; named, bounded existing ring correctness test with exact success summaries on all four nodes. |
| Sequential startup could time out while another node rehashed large assets. | Finish checksums first, launch all four within the connection deadline, then wait on rank 0. |
| The published image's historical launcher could silently leave steering OFF. | Every launch explicitly passes `--steering glp39`; documentation distinguishes this from new source-build defaults. |
| Running a container was conflated with a ready model. | Container state, bounded health wait, model/context JSON check, and real response parsing are separate checks. Container OOM status is not claimed to exclude GPU allocation errors. |
| Image example depended on an unexplained local file. | A self-contained standard-library PNG generator and request builder; decoded response and a clearly limited visual check. No benchmark result is claimed for this example. |
| Stopping, resuming and returning to an older release were unspecified. | All-rank stop/start, preserved sessions/assets, saved container/image IDs, name-collision checks, two-phase rollback, and explicit warning that a first install has no previous healthy version. |
| Failure notes offered checks without a recovery path. | Symptom/cause/action table; known-safe commands are explicit, while unknown kernel/hardware causes stop for vendor diagnosis rather than guessed mutations. |

## Verification

- Full recipe suite: **148/148 tests passed**, including **10 documentation tests**.
- Working-tree and reachable-history scrub: **zero forbidden-content findings**.
- `git diff --check`: passed.

`tests/test_reader_docs.py` checks shell syntax, compiles embedded Python examples,
resolves local links/anchors, requires per-step verification, exercises the image
and response examples with local fixtures, and verifies per-rank copy lists/hashes.
No documentation test contacts a serving endpoint or changes a host.

The complete README performance and quality block is retained **byte for byte**:
SHA256 `6a377451a396c606dc9da875142018797ec2687370dd2139ac17141c50a645c8`.
That includes the capped-condition line, every performance number, all measured
OFF/alpha-zero/ON labels, and the official HLE reference versus not-measured status.
The measurement files and benchmarks document are not changed in this rewrite.

The quick path states its prepared-input boundary; the guided path covers a fresh
installation. Hardware cabling, local network inputs and vendor-specific driver
installation remain explicit owner-provided prerequisites, not guessed automation.
The previously documented public-image qualification and full public-source build
pipeline gaps are not represented as closed by a documentation change.
